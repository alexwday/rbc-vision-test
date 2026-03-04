#!/usr/bin/env python3
"""
Run DeepSeek-OCR-2 on test documents for comparison with GPT-4.1.

Uses the mlx_vlm library with DeepSeek-OCR-2-bf16 model (Apple Silicon optimized).
"""

import json
import sys
import time
from pathlib import Path

from pdf2image import convert_from_path
from mlx_vlm import load, generate
from mlx_vlm.utils import load_config

# Import evaluation from our project
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.ocr.evaluation import evaluate_text


# DeepSeek-OCR-2 model
MODEL_PATH = "mlx-community/DeepSeek-OCR-2-bf16"


class DeepSeekOCR:
    """Simple wrapper for DeepSeek-OCR-2."""

    def __init__(self):
        self.model = None
        self.processor = None

    def load(self):
        print(f"Loading model: {MODEL_PATH}")
        self.model, self.processor = load(MODEL_PATH, trust_remote_code=True)
        print("Model loaded.")

    def ocr(self, image_path: str, max_tokens: int = 4000) -> str:
        prompt = "<image>\nExtract all text from this document."
        result = generate(
            self.model,
            self.processor,
            prompt,
            [image_path],
            verbose=False,
            max_tokens=max_tokens,
        )
        if hasattr(result, "text"):
            return result.text
        return str(result)


def run_deepseek_ocr():
    """Run DeepSeek-OCR-2 on all test documents."""
    # Initialize model
    model = DeepSeekOCR()
    model.load()

    # Paths
    source_dir = Path(__file__).parent.parent / "test_documents" / "source"
    expected_dir = Path(__file__).parent.parent / "test_documents" / "expected"
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Temp dir for page images
    temp_dir = results_dir / "temp_pages"
    temp_dir.mkdir(exist_ok=True)

    # Find all test PDFs
    pdf_files = sorted(source_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in test_documents/source/")
        return

    print(f"\nProcessing {len(pdf_files)} documents with DeepSeek-OCR-2...\n")

    results = []

    for pdf_path in pdf_files:
        doc_name = pdf_path.stem
        print(f"Processing {doc_name}...")

        # Convert PDF to images
        start_time = time.time()
        images = convert_from_path(str(pdf_path), dpi=150)

        # OCR each page
        page_texts = []
        for i, image in enumerate(images):
            # Save temp image
            temp_image_path = temp_dir / f"{doc_name}_page_{i+1}.png"
            image.save(temp_image_path)

            # Run OCR
            page_text = model.ocr(str(temp_image_path))
            page_texts.append(f"## Page {i+1}\n{page_text}")

        ocr_text = "\n\n".join(page_texts)
        elapsed = time.time() - start_time

        # Save OCR output
        ocr_output_path = results_dir / f"{doc_name}_deepseek_ocr.md"
        ocr_output_path.write_text(ocr_text, encoding="utf-8")

        # Load expected text and metadata
        expected_md_path = expected_dir / f"{doc_name}_expected.md"
        expected_json_path = expected_dir / f"{doc_name}_expected.json"

        if expected_md_path.exists():
            expected_text = expected_md_path.read_text(encoding="utf-8")

            # Load critical values if available
            critical_values = None
            if expected_json_path.exists():
                metadata = json.loads(expected_json_path.read_text(encoding="utf-8"))
                critical_values = metadata.get("critical_values")

            # Evaluate
            metrics = evaluate_text(expected_text, ocr_text, critical_values)

            result = {
                "document": doc_name,
                "model": "DeepSeek-OCR-2-bf16",
                "time_seconds": round(elapsed, 2),
                "pages": len(images),
                "metrics": metrics,
            }
            results.append(result)

            # Save individual result
            result_path = results_dir / f"{doc_name}_deepseek_result.json"
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

            print(f"  CER: {metrics['character_error_rate']:.4f}, WER: {metrics['word_error_rate']:.4f}, Time: {elapsed:.1f}s")
        else:
            print(f"  Warning: No expected output found for {doc_name}")

    # Print summary
    print("\n" + "=" * 60)
    print("DeepSeek-OCR-2 Results Summary")
    print("=" * 60)

    for r in results:
        m = r["metrics"]
        cv_status = "✓" if m.get("critical_values_matched", True) else "✗"
        print(f"  {r['document']}: CER={m['character_error_rate']:.4f}, WER={m['word_error_rate']:.4f} {cv_status}")

    print("\nResults saved to:", results_dir)

    # Clean up temp images
    for f in temp_dir.glob("*.png"):
        f.unlink()
    temp_dir.rmdir()


if __name__ == "__main__":
    run_deepseek_ocr()
