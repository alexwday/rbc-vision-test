#!/usr/bin/env python3
"""
Run OCR pipeline on generated PDFs and evaluate CER/WER.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.oauth import fetch_oauth_token
from src.rbc_security import configure_rbc_security_certs
from src.ocr.document_processor import process_pdf_document
from src.ocr.evaluation import evaluate_text
from src.ocr.html_report import DocumentResult, generate_html_report
from src.ocr.vision_ocr import SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TEST_SOURCE_DIR = Path(__file__).parent.parent / "test_documents" / "source"
EXPECTED_DIR = Path(__file__).parent.parent / "test_documents" / "expected"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def _load_expected(stem: str) -> Tuple[str, Dict]:
    """Load expected markdown and metadata for a document stem."""
    md_path = EXPECTED_DIR / f"{stem}_expected.md"
    json_path = EXPECTED_DIR / f"{stem}_expected.json"

    expected_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    metadata = {}
    if json_path.exists():
        metadata = json.loads(json_path.read_text(encoding="utf-8"))

    return expected_text, metadata


def _save_results(stem: str, ocr_text: str, metrics: Dict, usage: list) -> None:
    """Persist OCR output and metrics to the results directory."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_md = RESULTS_DIR / f"{stem}_ocr.md"
    output_md.write_text(ocr_text, encoding="utf-8")

    result_json = RESULTS_DIR / f"{stem}_result.json"
    payload = {
        "document": stem,
        "metrics": metrics,
        "usage": usage,
    }
    result_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_for_pdf(pdf_path: Path, token: str, detail: str) -> Dict:
    """Run OCR on a single PDF and evaluate it."""
    logger.info("Processing %s", pdf_path.name)
    ocr_output, usage, images, page_texts = process_pdf_document(
        token=token,
        pdf_path=pdf_path,
        document_type=pdf_path.stem.replace("_", " "),
        detail=detail,
    )

    expected_text, metadata = _load_expected(pdf_path.stem)
    metrics: Dict
    if expected_text:
        metrics = evaluate_text(expected_text, ocr_output, metadata.get("critical_values"))
    else:
        metrics = {}
        logger.warning("Expected text not found for %s; metrics skipped", pdf_path.stem)

    _save_results(pdf_path.stem, ocr_output, metrics, usage)

    return {
        "document": pdf_path.name,
        "metrics": metrics,
        "usage": usage,
        "images": images,
        "page_texts": page_texts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OCR tests against generated PDFs")
    parser.add_argument("--detail", choices=["low", "high", "auto"], default="high", help="Vision detail level")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Configuring RBC security (if available)")
    configure_rbc_security_certs()

    try:
        token, auth_info = fetch_oauth_token()
        logger.info("Authentication method: %s", auth_info.get("method"))
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to fetch authentication token: %s", exc)
        return 1

    pdf_files = sorted(TEST_SOURCE_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in test_documents/source/. Run scripts/generate_test_docs.py first.")
        return 1

    logger.info("Using model %s at %s", config.VISION_MODEL, config.BASE_URL)

    summary = []
    for pdf_path in pdf_files:
        summary.append(run_for_pdf(pdf_path, token, args.detail))

    print("\nOCR Test Results")
    for item in summary:
        metrics = item["metrics"]
        cer = metrics.get("character_error_rate")
        wer = metrics.get("word_error_rate")
        cer_display = f"{cer:.4f}" if cer is not None else "n/a"
        wer_display = f"{wer:.4f}" if wer is not None else "n/a"
        print(f"- {item['document']}: CER={cer_display}, WER={wer_display}")

    # Generate HTML side-by-side report
    doc_results = [
        DocumentResult(
            name=item["document"],
            page_images=item["images"],
            page_texts=item["page_texts"],
            metrics=item["metrics"],
            usage=item["usage"],
        )
        for item in summary
    ]
    report_path = generate_html_report(
        results=doc_results,
        system_prompt=SYSTEM_PROMPT,
        output_path=RESULTS_DIR / "ocr_report.html",
        model_name=config.VISION_MODEL,
    )
    print(f"HTML report: {report_path}")

    print(f"\nOutputs saved to: {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
