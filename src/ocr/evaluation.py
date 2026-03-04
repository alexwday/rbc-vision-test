"""
Evaluation helpers for OCR outputs.

Provides Levenshtein-based CER/WER metrics and critical value extraction checks.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Sequence

logger = logging.getLogger(__name__)


def levenshtein_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    """Compute Levenshtein distance between two token sequences."""
    if not reference:
        return len(hypothesis)
    if not hypothesis:
        return len(reference)

    previous_row = list(range(len(hypothesis) + 1))

    for i, ref_token in enumerate(reference, start=1):
        current_row = [i]
        for j, hyp_token in enumerate(hypothesis, start=1):
            insertion = current_row[j - 1] + 1
            deletion = previous_row[j] + 1
            substitution = previous_row[j - 1] + (0 if ref_token == hyp_token else 1)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row

    return previous_row[-1]


def character_error_rate(expected: str, actual: str) -> float:
    """Calculate Character Error Rate (CER)."""
    total_characters = len(expected)
    if total_characters == 0:
        return 0.0
    edits = levenshtein_distance(list(expected), list(actual))
    return edits / total_characters


def word_error_rate(expected: str, actual: str) -> float:
    """Calculate Word Error Rate (WER)."""
    expected_words = expected.split()
    actual_words = actual.split()
    total_words = len(expected_words)
    if total_words == 0:
        return 0.0
    edits = levenshtein_distance(expected_words, actual_words)
    return edits / total_words


def check_critical_values(expected_values: Dict[str, Any], actual_text: str) -> Dict[str, bool]:
    """Check if expected critical values are present exactly in the OCR output."""
    matches: Dict[str, bool] = {}
    for key, value in expected_values.items():
        if isinstance(value, list):
            # For list values, check if all items are present
            matches[key] = all(str(item) in actual_text for item in value)
        else:
            matches[key] = str(value) in actual_text
    return matches


def evaluate_text(
    expected_text: str,
    actual_text: str,
    critical_values: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Evaluate OCR output against expected text."""
    char_edits = levenshtein_distance(list(expected_text), list(actual_text))
    word_edits = levenshtein_distance(expected_text.split(), actual_text.split())

    results: Dict[str, Any] = {
        "character_error_rate": character_error_rate(expected_text, actual_text),
        "word_error_rate": word_error_rate(expected_text, actual_text),
        "character_edits": char_edits,
        "word_edits": word_edits,
        "total_characters": len(expected_text),
        "total_words": len(expected_text.split()),
    }

    if critical_values:
        matches = check_critical_values(critical_values, actual_text)
        results["critical_values"] = matches
        results["critical_values_matched"] = all(matches.values()) if matches else True

    return results
