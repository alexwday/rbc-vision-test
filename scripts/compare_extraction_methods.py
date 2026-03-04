#!/usr/bin/env python3
"""
Compare extraction methods with optimized settings:

1. pymupdf4llm - best-in-class PDF text extraction for digital PDFs
2. DeepSeek-OCR-2 - vision-based OCR for image PDFs

Opens results side-by-side for comparison.
"""

import subprocess
import time
from pathlib import Path

from pdf2image import convert_from_path
from mlx_vlm import load, generate

# Import pymupdf4llm
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


# Paths
BASE_DIR = Path(__file__).parent.parent
SOURCE_DIR = BASE_DIR / "test_documents" / "source"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# DeepSeek-OCR-2 model
MODEL_PATH = "mlx-community/DeepSeek-OCR-2-bf16"


class DeepSeekOCR:
    """DeepSeek-OCR-2 wrapper with proper chat template formatting."""

    def __init__(self):
        self.model = None
        self.processor = None

    def load(self):
        print("Loading DeepSeek-OCR-2 model...")
        self.model, self.processor = load(MODEL_PATH, trust_remote_code=True)
        print("Model loaded.")

    def extract(self, image_path: str, max_tokens: int = 4000) -> str:
        """Extract text from image using proper chat template."""
        # Use chat template to format properly - this avoids artifacts
        messages = [
            {"role": "user", "content": "<image>\nExtract all text from this document."}
        ]
        prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)

        result = generate(
            self.model,
            self.processor,
            prompt,
            [image_path],
            verbose=False,
            max_tokens=max_tokens,
            temp=0.0,  # Deterministic output
        )

        if hasattr(result, "text"):
            return result.text
        return str(result)


def extract_with_pymupdf4llm(pdf_path: Path) -> str:
    """Extract markdown from PDF using pymupdf4llm."""
    if not PYMUPDF4LLM_AVAILABLE:
        return "ERROR: pymupdf4llm not installed"

    # Use pymupdf4llm with optimal settings
    md_text = pymupdf4llm.to_markdown(
        str(pdf_path),
        show_progress=False,
        page_chunks=False,  # Single output
    )

    return md_text


def extract_with_deepseek(model: DeepSeekOCR, pdf_path: Path, temp_dir: Path) -> str:
    """Extract from PDF using DeepSeek-OCR-2, processing page by page."""
    # Convert PDF to images at good resolution
    images = convert_from_path(str(pdf_path), dpi=200)

    page_texts = []
    for i, image in enumerate(images):
        # Save temp image
        temp_path = temp_dir / f"temp_page_{i+1}.png"
        image.save(temp_path)

        # Extract text
        text = model.extract(str(temp_path))

        # Add page header only for multi-page docs
        if len(images) > 1:
            page_texts.append(f"--- Page {i+1} ---\n\n{text.strip()}")
        else:
            page_texts.append(text.strip())

        # Clean up
        temp_path.unlink()

    return "\n\n".join(page_texts)


def main():
    print("=" * 70)
    print("PDF Extraction Method Comparison")
    print("=" * 70)
    print(f"pymupdf4llm available: {PYMUPDF4LLM_AVAILABLE}")
    print()

    # File paths
    image_pdf = SOURCE_DIR / "complex_layout_image.pdf"
    digital_pdf = SOURCE_DIR / "complex_layout_digital.pdf"

    if not image_pdf.exists() or not digital_pdf.exists():
        print("Error: Test documents not found. Run generate_complex_layout.py first.")
        return

    # Create temp directory
    temp_dir = RESULTS_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)

    # Initialize DeepSeek model
    model = DeepSeekOCR()
    model.load()

    results = {}

    # === DIGITAL PDF EXTRACTION ===
    print("\n" + "=" * 70)
    print("DIGITAL PDF EXTRACTION (selectable text)")
    print("=" * 70)

    # 1. pymupdf4llm on digital PDF
    print("\n[1/3] pymupdf4llm on DIGITAL PDF...")
    start = time.time()
    result1 = extract_with_pymupdf4llm(digital_pdf)
    time1 = time.time() - start
    results["pymupdf4llm_digital"] = result1
    print(f"     Done in {time1:.2f}s ({len(result1)} chars)")

    # === IMAGE PDF EXTRACTION ===
    print("\n" + "=" * 70)
    print("IMAGE PDF EXTRACTION (scanned/image-based)")
    print("=" * 70)

    # 2. DeepSeek on image PDF
    print("\n[2/3] DeepSeek-OCR-2 on IMAGE PDF...")
    start = time.time()
    result2 = extract_with_deepseek(model, image_pdf, temp_dir)
    time2 = time.time() - start
    results["deepseek_image"] = result2
    print(f"     Done in {time2:.2f}s ({len(result2)} chars)")

    # 3. DeepSeek on digital PDF (for comparison)
    print("\n[3/3] DeepSeek-OCR-2 on DIGITAL PDF (comparison)...")
    start = time.time()
    result3 = extract_with_deepseek(model, digital_pdf, temp_dir)
    time3 = time.time() - start
    results["deepseek_digital"] = result3
    print(f"     Done in {time3:.2f}s ({len(result3)} chars)")

    # Clean up temp dir
    try:
        temp_dir.rmdir()
    except:
        pass

    # Save results
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    output_files = []
    for name, content in results.items():
        output_path = RESULTS_DIR / f"compare_{name}.md"
        output_path.write_text(content, encoding="utf-8")
        output_files.append(output_path)
        print(f"Saved: {output_path.name}")

    # Print summary table
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Method':<45} {'Time':>8} {'Chars':>8}")
    print("-" * 70)
    print(f"{'pymupdf4llm (digital PDF)':<45} {time1:>7.2f}s {len(result1):>8}")
    print(f"{'DeepSeek-OCR-2 (image PDF)':<45} {time2:>7.2f}s {len(result2):>8}")
    print(f"{'DeepSeek-OCR-2 (digital PDF)':<45} {time3:>7.2f}s {len(result3):>8}")

    # Open files for comparison
    print("\n" + "=" * 70)
    print("Opening results for side-by-side comparison...")
    print("=" * 70)

    # Open the image preview
    image_preview = SOURCE_DIR / "complex_layout_image.png"
    if image_preview.exists():
        subprocess.run(["open", str(image_preview)])

    # Open expected output
    expected_path = BASE_DIR / "test_documents" / "expected" / "complex_layout_expected.md"
    if expected_path.exists():
        subprocess.run(["open", str(expected_path)])

    # Open the comparison files
    for f in output_files:
        subprocess.run(["open", str(f)])

    print("\nOpened files for comparison:")
    print(f"  - Original image: {image_preview.name}")
    print(f"  - Expected: complex_layout_expected.md")
    for f in output_files:
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
