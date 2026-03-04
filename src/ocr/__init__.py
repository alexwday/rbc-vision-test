"""OCR utilities and pipeline components."""

from .document_processor import process_pdf_document
from .evaluation import (
    character_error_rate,
    check_critical_values,
    evaluate_text,
    levenshtein_distance,
    word_error_rate,
)
from .pdf_processor import pdf_to_base64_images, pdf_to_images
from .vision_ocr import run_ocr_on_images

__all__ = [
    "character_error_rate",
    "check_critical_values",
    "evaluate_text",
    "levenshtein_distance",
    "pdf_to_base64_images",
    "pdf_to_images",
    "process_pdf_document",
    "run_ocr_on_images",
    "word_error_rate",
]
