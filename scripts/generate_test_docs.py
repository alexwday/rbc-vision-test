#!/usr/bin/env python3
"""
Generate all OCR test documents and expected outputs.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_documents.generators.create_all_tests import generate_all_tests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    base_dir = Path(__file__).parent.parent / "test_documents"
    source_dir = base_dir / "source"
    expected_dir = base_dir / "expected"

    logger.info("Generating OCR test documents...")
    try:
        results = generate_all_tests(source_dir, expected_dir)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to generate test documents: %s", exc)
        return 1

    print("Generated OCR test documents:")
    for result in results:
        print(f"- PDF: {result['pdf']}")
        print(f"  Expected markdown: {result['expected_markdown']}")
        print(f"  Expected metadata: {result['expected_metadata']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
