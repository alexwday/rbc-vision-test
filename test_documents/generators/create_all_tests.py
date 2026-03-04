"""
Generate all OCR test documents and expected outputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .generate_financial import generate_financial_report
from .generate_form import generate_application_form
from .generate_technical import generate_technical_document
from .generate_shareholder_report import generate_shareholder_report
from .generate_procedure import generate_procedure_document
from .generate_guidelines import generate_guidelines_document


def generate_all_tests(
    output_dir: Path | None = None,
    expected_dir: Path | None = None,
) -> List[Dict[str, Path]]:
    """Generate all test PDFs and expected files."""
    base_dir = Path(__file__).resolve().parent.parent
    output_directory = output_dir or base_dir / "source"
    expected_directory = expected_dir or base_dir / "expected"

    generators = [
        # Original basic tests
        generate_financial_report,
        generate_application_form,
        generate_technical_document,
        # New complex tests matching real use cases
        generate_shareholder_report,      # Complex tables, charts, footnotes
        generate_procedure_document,       # Flowcharts, swim lanes, procedures
        generate_guidelines_document,      # Multi-level lists, checkboxes, policy tables
    ]

    results: List[Dict[str, Path]] = []
    for generator in generators:
        results.append(generator(output_directory, expected_directory))
    return results


if __name__ == "__main__":
    generated = generate_all_tests()
    print("Generated OCR test documents:")
    for item in generated:
        for key, value in item.items():
            print(f"- {key}: {value}")
