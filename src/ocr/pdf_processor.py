"""
PDF Processing utilities for OCR workflows.

Converts PDF files into page images suitable for OCR. Provides helpers to
return PIL images or base64-encoded strings for direct inclusion in vision
requests.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Iterable, List

from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)

_DEFAULT_DPI = 300


def _image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Encode a PIL image to a base64 string."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pdf_to_images(pdf_path: Path | str, dpi: int = _DEFAULT_DPI) -> List[Image.Image]:
    """Convert a PDF to a list of PIL images.

    Args:
        pdf_path: Path to the PDF file.
        dpi: Render DPI for conversion (default 300 for OCR quality).

    Returns:
        List of PIL Image objects, one per page.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    logger.info("Converting PDF '%s' to images at %sdpi", path.name, dpi)
    images = convert_from_path(str(path), dpi=dpi, fmt="png")

    converted = [img.convert("RGB") for img in images]
    logger.info("Converted %d page(s) from %s", len(converted), path.name)
    return converted


def pdf_to_base64_images(pdf_path: Path | str, dpi: int = _DEFAULT_DPI) -> List[str]:
    """Convert PDF pages to base64-encoded PNG strings."""
    images = pdf_to_images(pdf_path, dpi=dpi)
    return [_image_to_base64(img) for img in images]


def images_to_base64(images: Iterable[Image.Image], format: str = "PNG") -> List[str]:
    """Encode a collection of PIL images to base64 strings."""
    return [_image_to_base64(img, format=format) for img in images]
