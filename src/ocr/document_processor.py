"""
Document orchestration for multi-page OCR.

Converts PDFs to images, sends each page through the vision OCR, and
combines page results into a single markdown output.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from .pdf_processor import pdf_to_images
from .vision_ocr import run_ocr_on_images

logger = logging.getLogger(__name__)


def process_pdf_document(
    token: str,
    pdf_path: Path | str,
    document_type: str = "document",
    detail: str = "high",
) -> Tuple[str, List[dict], List[Image.Image], List[str]]:
    """Process a PDF through OCR and combine page outputs.

    Returns:
        combined_text: All pages joined with ``## Page N`` headers.
        usage_details: Per-page token usage dicts.
        images: PIL page images (for downstream reporting).
        page_texts: Raw per-page OCR text (without the ``## Page N`` prefix).
    """
    images = pdf_to_images(pdf_path)
    logger.info("Processing %d page(s) from %s", len(images), pdf_path)

    page_outputs: List[str] = []
    page_texts: List[str] = []
    usage_details: List[dict] = []

    for index, image in enumerate(images, start=1):
        page_hint = f"{document_type} - page {index}"
        page_text, usage = run_ocr_on_images(
            token=token,
            images=[image],
            document_type=page_hint,
            detail=detail,
        )

        page_texts.append(page_text)
        page_outputs.append(f"## Page {index}\n{page_text}")

        page_usage: dict = {"page": index}
        if usage:
            page_usage.update(usage)
        usage_details.append(page_usage)

    combined_text = "\n\n".join(page_outputs)
    return combined_text, usage_details, images, page_texts
