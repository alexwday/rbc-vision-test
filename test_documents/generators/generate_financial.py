"""
Financial report test document generator.

Creates a lightly degraded financial report image and converts it to a
non-searchable PDF for OCR testing. Also writes ground-truth markdown and
metadata for evaluation.
"""

from __future__ import annotations

import io
import random
import textwrap
from pathlib import Path
from typing import Dict, List, Tuple

import img2pdf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

PAGE_SIZE = (1700, 2200)
MARGIN = 80
BACKGROUND = (250, 248, 245)
TEXT_COLOR = (30, 30, 30)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Best-effort font loader with fallbacks."""
    font_candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _save_pdf(image: Image.Image, output_path: Path) -> None:
    """Save a PIL image as a non-searchable PDF using img2pdf."""
    image_rgb = image.convert("RGB")
    buffer = io.BytesIO()
    image_rgb.save(buffer, format="PNG")
    pdf_bytes = img2pdf.convert(buffer.getvalue())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)


def _apply_degradation(image: Image.Image, rng: random.Random) -> Image.Image:
    """Add slight rotation, noise, and contrast variation."""
    angle = rng.uniform(0.5, 1.0)
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")

    # Center-crop back to the original page size
    left = (rotated.width - image.width) // 2
    top = (rotated.height - image.height) // 2
    cropped = rotated.crop((left, top, left + image.width, top + image.height))

    noise_layer = Image.effect_noise(image.size, 4)
    noise_rgb = Image.merge("RGB", (noise_layer, noise_layer, noise_layer))
    blended = Image.blend(cropped, noise_rgb, 0.04)

    contrast = ImageEnhance.Contrast(blended).enhance(0.9 + rng.random() * 0.2)
    return contrast


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    box: Tuple[int, int, int, int],
    fill: Tuple[int, int, int],
) -> None:
    """Draw text centered inside the provided box."""
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    x0, y0, x1, y1 = box
    x = x0 + (x1 - x0 - text_w) / 2
    y = y0 + (y1 - y0 - text_h) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _render_table(
    draw: ImageDraw.ImageDraw,
    top_left: Tuple[int, int],
    headers: List[str],
    rows: List[List[str]],
    cell_width: int,
    cell_height: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    merge_rows: List[int],
    background_color: Tuple[int, int, int],
) -> None:
    """Draw a table with optional merged first two columns on selected rows."""
    rows_count = len(rows) + 1
    cols_count = len(headers)
    x0, y0 = top_left

    # Grid lines
    for r in range(rows_count + 1):
        y = y0 + r * cell_height
        draw.line((x0, y, x0 + cols_count * cell_width, y), fill=TEXT_COLOR, width=2)
    for c in range(cols_count + 1):
        x = x0 + c * cell_width
        draw.line((x, y0, x, y0 + rows_count * cell_height), fill=TEXT_COLOR, width=2)

    # Merge lines for specified rows (remove the dividing line between first two columns)
    for row_idx in merge_rows:
        y_start = y0 + (row_idx + 1) * cell_height
        y_end = y_start + cell_height
        divider_x = x0 + cell_width
        draw.line((divider_x, y_start + 2, divider_x, y_end - 2), fill=background_color, width=6)

    # Header row
    for col_idx, header in enumerate(headers):
        cell_box = (
            x0 + col_idx * cell_width,
            y0,
            x0 + (col_idx + 1) * cell_width,
            y0 + cell_height,
        )
        _draw_centered_text(draw, header, font, cell_box, TEXT_COLOR)

    # Data rows
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            if row_idx in merge_rows and col_idx == 1:
                continue  # merged into column 0

            span = 2 if row_idx in merge_rows and col_idx == 0 else 1
            cell_left = x0 + col_idx * cell_width
            cell_box = (
                cell_left,
                y0 + (row_idx + 1) * cell_height,
                cell_left + span * cell_width,
                y0 + (row_idx + 2) * cell_height,
            )
            _draw_centered_text(draw, value, font, cell_box, TEXT_COLOR)


def _wrap_text(text: str, width: int) -> List[str]:
    """Wrap text to fit a column."""
    wrapped = textwrap.wrap(text, width=width)
    return wrapped if wrapped else [text]


def generate_financial_report(
    output_dir: Path,
    expected_dir: Path,
    seed: int = 42,
) -> Dict[str, Path]:
    """Generate the financial report PDF and expected outputs."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", PAGE_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(48, bold=True)
    header_font = _load_font(28, bold=True)
    body_font = _load_font(22)
    small_font = _load_font(18)

    # Header
    draw.text((MARGIN, MARGIN), "Northwind Analytics", font=header_font, fill=TEXT_COLOR)
    draw.text((PAGE_SIZE[0] - 450, MARGIN), "Date: June 30, 2024", font=body_font, fill=TEXT_COLOR)
    draw.text((MARGIN, MARGIN + 60), "Q2 Financial Performance Report", font=title_font, fill=TEXT_COLOR)

    # Executive summary columns
    summary_top = MARGIN + 140
    col_width = (PAGE_SIZE[0] - 2 * MARGIN - 40) // 2
    summary_a = (
        "Revenue strengthened with consistent quarterly growth; "
        "operating expenses remained controlled with incremental hiring."
    )
    summary_b = (
        "Cash position stable; investments prioritized toward analytics platforms "
        "and client experience modernization."
    )

    draw.text((MARGIN, summary_top - 20), "Executive Summary", font=header_font, fill=TEXT_COLOR)

    for idx, text in enumerate((summary_a, summary_b)):
        lines = _wrap_text(text, width=45)
        x = MARGIN + idx * (col_width + 40)
        y = summary_top + 10
        for line in lines:
            draw.text((x, y), line, font=body_font, fill=TEXT_COLOR)
            y += body_font.size + 6

    # Financial table
    headers = ["", "Q1", "Q2", "Q3", "Q4", "YoY %", "Target", "Variance"]
    rows = [
        ["Net Revenue (merged)", "", "$1,234.56", "$1,498.10", "$1,612.00", "12.5%", "$1,650.00", "$55.50"],
        ["COGS (merged)", "", "($345.00)", "($390.25)", "($410.10)", "(8.0%)", "($420.00)", "$-10.75"],
        ["Operating Expense", "$245.50", "$252.10", "$260.00", "$268.75", "4.1%", "($265.00)", "$-3.75"],
        ["EBITDA", "$643.06", "$855.75", "$941.90", "$1,005.95", "9.4%", "$980.00", "$25.95"],
        ["Net Income", "$410.12", "$522.80", "$575.60", "$610.45", "7.5%", "$590.00", "$20.45"],
    ]

    table_top = summary_top + 140
    cell_width = 175
    cell_height = 70
    _render_table(
        draw,
        top_left=(MARGIN, table_top),
        headers=headers,
        rows=rows,
        cell_width=cell_width,
        cell_height=cell_height,
        font=body_font,
        merge_rows=[0, 1],
        background_color=BACKGROUND,
    )

    # Footnotes with superscripts
    foot_top = table_top + (len(rows) + 2) * cell_height
    draw.text((MARGIN, foot_top), "Notes", font=header_font, fill=TEXT_COLOR)
    note_lines = [
        ("1", "Performance excludes one-time restructuring charges."),
        ("2", "Values presented in USD; negative numbers shown in parentheses."),
    ]
    y_cursor = foot_top + 40
    for marker, text in note_lines:
        draw.text((MARGIN, y_cursor - 6), marker, font=small_font, fill=TEXT_COLOR)
        draw.text((MARGIN + 18, y_cursor), text, font=body_font, fill=TEXT_COLOR)
        y_cursor += body_font.size + 6

    degraded = _apply_degradation(image, rng)

    pdf_path = output_dir / "financial_report.pdf"
    _save_pdf(degraded, pdf_path)

    expected_text = build_expected_text(headers, rows, summary_a, summary_b, note_lines)
    expected_md_path = expected_dir / "financial_report_expected.md"
    expected_json_path = expected_dir / "financial_report_expected.json"

    expected_md_path.write_text(expected_text, encoding="utf-8")
    expected_json_path.write_text(
        build_expected_metadata(expected_text),
        encoding="utf-8",
    )

    return {
        "pdf": pdf_path,
        "expected_markdown": expected_md_path,
        "expected_metadata": expected_json_path,
    }


def build_expected_text(
    headers: List[str],
    rows: List[List[str]],
    summary_a: str,
    summary_b: str,
    notes: List[Tuple[str, str]],
) -> str:
    """Construct markdown that mirrors the rendered document."""
    lines = [
        "# Northwind Analytics - Q2 Financial Performance Report",
        "Date: June 30, 2024",
        "",
        "## Executive Summary",
        "**Column A**",
        f"- {summary_a}",
        "**Column B**",
        f"- {summary_b}",
        "",
        "## Financial Table",
    ]

    header_row = "| " + " | ".join(headers) + " |"
    divider_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    lines.append(header_row)
    lines.append(divider_row)

    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("## Footnotes")
    for marker, text in notes:
        lines.append(f"{marker} {text}")

    return "\n".join(lines)


def build_expected_metadata(expected_text: str) -> str:
    """Return JSON metadata for the expected document."""
    import json

    metadata = {
        "document": "financial_report",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "critical_values": {
            "net_revenue_q4": "$1,612.00",
            "yoy_growth": "12.5%",
            "cogs_q4": "($410.10)",
        },
    }
    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    output_directory = base_dir / "source"
    expected_directory = base_dir / "expected"
    result = generate_financial_report(output_directory, expected_directory)
    print("Generated financial report:")
    for key, value in result.items():
        print(f"- {key}: {value}")
