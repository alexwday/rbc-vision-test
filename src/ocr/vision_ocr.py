"""
Vision OCR wrapper using GPT-4.1 (or configured vision model).

Builds vision chat prompts with images encoded as base64 strings and delegates
calls to the shared LLM connector.
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Sequence, Tuple, Union

from PIL import Image

from src.config import config
from src.llm import UsageDetails, execute_llm_call

from .pdf_processor import images_to_base64

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a precise document OCR system. Extract all visible text from the image \
and reproduce it as clean Markdown. Follow these rules exactly:

- Preserve document hierarchy using Markdown headings (#, ##, ###).
- Render tables with Markdown pipe syntax (| col | col |). Preserve every number exactly.
- Represent checkboxes as [x] (checked) or [ ] (unchecked).
- Use bullet (- ) and numbered (1. ) lists as they appear.
- Preserve **bold** and *italic* formatting where visible.
- Mark any unreadable section with [illegible].
- Output ONLY the extracted text. Do not add commentary, summaries, or interpretation.
"""

DEFAULT_MAX_TOKENS = 8192


def _normalize_detail(detail: str) -> str:
    """Clamp detail to allowed values for vision requests."""
    allowed = {"low", "high", "auto"}
    return detail if detail in allowed else "high"


def run_ocr_on_images(
    token: str,
    images: Sequence[Union[Image.Image, str]],
    document_type: str = "document",
    detail: str = "high",
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Tuple[str, UsageDetails]:
    """Run OCR on one or more images and return markdown text plus usage details.

    Args:
        token: OAuth token or API key for the vision model.
        images: Sequence of PIL images or base64-encoded strings.
        document_type: Hint about the document content (unused in direct OCR mode).
        detail: Vision detail level (low|high|auto).
        max_tokens: Response token budget.
    """
    if not images:
        raise ValueError("At least one image is required for OCR")

    if isinstance(images[0], Image.Image):
        base64_images: List[str] = images_to_base64(images)  # type: ignore[arg-type]
    else:
        base64_images = [str(img) for img in images]

    user_text = "Extract all text from this image as markdown."
    if document_type and document_type != "document":
        user_text += f" This is a page from a {document_type}."

    user_content = [
        {
            "type": "text",
            "text": user_text,
        }
    ]

    vision_detail = _normalize_detail(detail)

    for base64_image in base64_images:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": vision_detail,
                },
            }
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    logger.info("Running OCR for %d image(s) with detail=%s", len(base64_images), vision_detail)

    response, usage = execute_llm_call(
        oauth_token=token,
        model=config.VISION_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0,
    )

    content = response.choices[0].message.content
    text_content = content if isinstance(content, str) else str(content)

    return text_content, usage
