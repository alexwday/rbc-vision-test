"""
Complex Layout Document Generator.

Creates a document with challenging layout features:
- Multi-column text
- Tables with merged cells
- Sidebars and callout boxes
- Headers/footers
- Footnotes
- Mixed formatting

Generates BOTH:
1. Image-based PDF (for vision OCR testing)
2. Digital text PDF (for text extraction comparison)
"""

from __future__ import annotations

import io
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import img2pdf
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

PAGE_WIDTH = 1700
PAGE_HEIGHT = 2200
MARGIN = 80
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
ACCENT_COLOR = (0, 82, 147)
SIDEBAR_BG = (240, 248, 255)
CALLOUT_BG = (255, 250, 230)
TABLE_HEADER_BG = (0, 82, 147)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Word wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def generate_complex_layout_image(output_path: Path, seed: int = 42) -> Dict:
    """Generate a complex layout document as an image-based PDF."""
    rng = random.Random(seed)

    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Fonts
    title_font = _load_font(36, bold=True)
    heading_font = _load_font(22, bold=True)
    subheading_font = _load_font(16, bold=True)
    body_font = _load_font(14)
    small_font = _load_font(12)
    tiny_font = _load_font(10)

    y = MARGIN

    # === HEADER ===
    draw.rectangle((0, 0, PAGE_WIDTH, 80), fill=ACCENT_COLOR)
    draw.text((MARGIN, 20), "QUARTERLY INVESTMENT REVIEW", font=title_font, fill=(255, 255, 255))
    draw.text((PAGE_WIDTH - MARGIN - 200, 30), "Q4 2024 Report", font=body_font, fill=(255, 255, 255))
    y = 100

    # === TWO-COLUMN LAYOUT ===
    col_width = (PAGE_WIDTH - 3 * MARGIN) // 2
    left_col_x = MARGIN
    right_col_x = MARGIN * 2 + col_width

    # Left column - Executive Summary
    draw.text((left_col_x, y), "Executive Summary", font=heading_font, fill=ACCENT_COLOR)
    y_left = y + 35

    summary_text = (
        "The fourth quarter demonstrated resilient portfolio performance despite elevated market volatility. "
        "Total returns reached 8.7% for the quarter, outperforming the benchmark by 120 basis points. "
        "Fixed income allocations provided stability while equity positions captured upside momentum in "
        "technology and healthcare sectors. Risk-adjusted metrics remained favorable with a Sharpe ratio of 1.42."
    )

    lines = _wrap_text(draw, summary_text, body_font, col_width - 20)
    for line in lines:
        draw.text((left_col_x, y_left), line, font=body_font, fill=TEXT_COLOR)
        y_left += 20

    y_left += 15

    # Key Metrics Box
    draw.rectangle((left_col_x, y_left, left_col_x + col_width, y_left + 140), fill=SIDEBAR_BG, outline=ACCENT_COLOR, width=2)
    draw.text((left_col_x + 15, y_left + 10), "Key Performance Metrics", font=subheading_font, fill=ACCENT_COLOR)

    metrics = [
        ("Total Return (QTD)", "8.7%"),
        ("Benchmark Return", "7.5%"),
        ("Alpha Generated", "+1.2%"),
        ("Sharpe Ratio", "1.42"),
        ("Max Drawdown", "-3.2%"),
    ]

    metric_y = y_left + 40
    for label, value in metrics:
        draw.text((left_col_x + 20, metric_y), label + ":", font=small_font, fill=TEXT_COLOR)
        draw.text((left_col_x + col_width - 80, metric_y), value, font=_load_font(12, bold=True), fill=ACCENT_COLOR)
        metric_y += 20

    y_left = y_left + 155

    # Right column - starts at same y as left
    y_right = y + 35

    # Sidebar callout box
    draw.rectangle((right_col_x, y_right, right_col_x + col_width, y_right + 100), fill=CALLOUT_BG, outline=(200, 150, 50), width=2)
    draw.text((right_col_x + 15, y_right + 10), "⚠ Market Alert", font=subheading_font, fill=(180, 100, 0))

    alert_text = "Fed policy uncertainty and geopolitical tensions warrant continued defensive positioning in Q1 2025."
    alert_lines = _wrap_text(draw, alert_text, small_font, col_width - 40)
    alert_y = y_right + 40
    for line in alert_lines:
        draw.text((right_col_x + 15, alert_y), line, font=small_font, fill=TEXT_COLOR)
        alert_y += 16

    y_right = y_right + 115

    # Asset Allocation section
    draw.text((right_col_x, y_right), "Asset Allocation", font=heading_font, fill=ACCENT_COLOR)
    y_right += 35

    # Mini allocation table
    alloc_data = [
        ("Asset Class", "Weight", "Change"),
        ("US Equities", "45.0%", "+2.0%"),
        ("Int'l Equities", "15.0%", "-1.5%"),
        ("Fixed Income", "30.0%", "+0.5%"),
        ("Alternatives", "7.5%", "-0.5%"),
        ("Cash", "2.5%", "-0.5%"),
    ]

    cell_widths = [col_width * 0.45, col_width * 0.275, col_width * 0.275]
    row_height = 25

    for i, row in enumerate(alloc_data):
        cell_x = right_col_x
        bg = TABLE_HEADER_BG if i == 0 else (BG_COLOR if i % 2 == 0 else (245, 247, 250))
        text_col = (255, 255, 255) if i == 0 else TEXT_COLOR

        for j, (cell, width) in enumerate(zip(row, cell_widths)):
            draw.rectangle((cell_x, y_right, cell_x + width, y_right + row_height), fill=bg, outline=(200, 200, 200))
            font = _load_font(11, bold=(i == 0))
            draw.text((cell_x + 8, y_right + 5), cell, font=font, fill=text_col)
            cell_x += width
        y_right += row_height

    y_right += 20

    # === FULL WIDTH TABLE ===
    table_y = max(y_left, y_right) + 20
    draw.text((MARGIN, table_y), "Sector Performance Analysis", font=heading_font, fill=ACCENT_COLOR)
    table_y += 35

    # Complex table with merged header
    table_width = PAGE_WIDTH - 2 * MARGIN

    # Level 1 header (merged cells)
    headers_l1 = [("Sector", 1), ("Q4 Performance", 3), ("Risk Metrics", 2), ("Outlook", 1)]
    headers_l2 = ["", "Return", "vs Bench", "Contrib.", "Vol", "Beta", "Rating"]

    col_w = table_width // 7
    row_h = 28

    # Draw Level 1 headers
    x = MARGIN
    for label, span in headers_l1:
        w = col_w * span
        if label:
            draw.rectangle((x, table_y, x + w, table_y + row_h), fill=ACCENT_COLOR)
            bbox = draw.textbbox((0, 0), label, font=small_font)
            text_x = x + (w - (bbox[2] - bbox[0])) // 2
            draw.text((text_x, table_y + 6), label, font=_load_font(12, bold=True), fill=(255, 255, 255))
        x += w

    table_y += row_h

    # Draw Level 2 headers
    x = MARGIN
    for header in headers_l2:
        draw.rectangle((x, table_y, x + col_w, table_y + row_h), fill=(220, 230, 240), outline=(180, 180, 180))
        if header:
            draw.text((x + 8, table_y + 6), header, font=_load_font(11, bold=True), fill=TEXT_COLOR)
        x += col_w

    table_y += row_h

    # Data rows
    sector_data = [
        ("Technology", "+12.4%", "+3.2%", "+2.1%", "18.5%", "1.25", "OW"),
        ("Healthcare", "+9.8%", "+1.5%", "+1.4%", "14.2%", "0.95", "OW"),
        ("Financials", "+7.2%", "-0.3%", "+0.9%", "16.8%", "1.15", "N"),
        ("Energy", "+5.1%", "-2.4%", "+0.4%", "22.3%", "1.35", "UW"),
        ("Consumer Disc.", "+6.8%", "-0.7%", "+0.6%", "15.9%", "1.10", "N"),
        ("Industrials", "+8.1%", "+0.6%", "+0.8%", "14.5%", "1.05", "OW"),
    ]

    for i, row in enumerate(sector_data):
        x = MARGIN
        bg = BG_COLOR if i % 2 == 0 else (248, 250, 252)
        for j, cell in enumerate(row):
            draw.rectangle((x, table_y, x + col_w, table_y + row_h), fill=bg, outline=(200, 200, 200))

            # Color coding for performance
            color = TEXT_COLOR
            if j in [1, 2, 3] and cell.startswith("+"):
                color = (0, 130, 0)
            elif j in [1, 2, 3] and cell.startswith("-"):
                color = (180, 0, 0)
            elif j == 6:
                color = ACCENT_COLOR if cell == "OW" else ((180, 0, 0) if cell == "UW" else TEXT_COLOR)

            draw.text((x + 8, table_y + 6), cell, font=small_font, fill=color)
            x += col_w
        table_y += row_h

    table_y += 25

    # === FOOTNOTES ===
    draw.line((MARGIN, table_y, MARGIN + 300, table_y), fill=(180, 180, 180), width=1)
    table_y += 10

    footnotes = [
        "¹ Returns shown are net of fees. Past performance is not indicative of future results.",
        "² OW = Overweight, N = Neutral, UW = Underweight relative to benchmark.",
        "³ Risk metrics calculated using 36-month rolling window.",
    ]

    for note in footnotes:
        draw.text((MARGIN, table_y), note, font=tiny_font, fill=(100, 100, 100))
        table_y += 14

    # === FOOTER ===
    footer_y = PAGE_HEIGHT - 50
    draw.line((MARGIN, footer_y - 10, PAGE_WIDTH - MARGIN, footer_y - 10), fill=(200, 200, 200), width=1)
    draw.text((MARGIN, footer_y), "CONFIDENTIAL - For authorized recipients only", font=tiny_font, fill=(150, 150, 150))
    draw.text((PAGE_WIDTH - MARGIN - 100, footer_y), "Page 1 of 1", font=tiny_font, fill=(150, 150, 150))

    # Save as image-based PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    pdf_bytes = img2pdf.convert(buffer.getvalue())

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    # Also save the raw image for inspection
    image_path = output_path.with_suffix(".png")
    image.save(image_path)

    return {
        "pdf": output_path,
        "image": image_path,
        "type": "image-based",
    }


def generate_complex_layout_digital(output_path: Path) -> Dict:
    """Generate the same layout as a digital text PDF using ReportLab."""
    from reportlab.platypus import Flowable

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#005293'),
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#005293'),
        spaceBefore=15,
        spaceAfter=10,
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
    )

    story = []

    # Title
    story.append(Paragraph("QUARTERLY INVESTMENT REVIEW - Q4 2024", title_style))
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary = (
        "The fourth quarter demonstrated resilient portfolio performance despite elevated market volatility. "
        "Total returns reached 8.7% for the quarter, outperforming the benchmark by 120 basis points. "
        "Fixed income allocations provided stability while equity positions captured upside momentum in "
        "technology and healthcare sectors. Risk-adjusted metrics remained favorable with a Sharpe ratio of 1.42."
    )
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 10))

    # Key Metrics Table
    story.append(Paragraph("Key Performance Metrics", heading_style))

    metrics_data = [
        ["Metric", "Value"],
        ["Total Return (QTD)", "8.7%"],
        ["Benchmark Return", "7.5%"],
        ["Alpha Generated", "+1.2%"],
        ["Sharpe Ratio", "1.42"],
        ["Max Drawdown", "-3.2%"],
    ]

    metrics_table = Table(metrics_data, colWidths=[200, 100])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005293')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7fa')]),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 20))

    # Asset Allocation
    story.append(Paragraph("Asset Allocation", heading_style))

    alloc_data = [
        ["Asset Class", "Weight", "Change"],
        ["US Equities", "45.0%", "+2.0%"],
        ["Int'l Equities", "15.0%", "-1.5%"],
        ["Fixed Income", "30.0%", "+0.5%"],
        ["Alternatives", "7.5%", "-0.5%"],
        ["Cash", "2.5%", "-0.5%"],
    ]

    alloc_table = Table(alloc_data, colWidths=[150, 80, 80])
    alloc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005293')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7fa')]),
    ]))
    story.append(alloc_table)
    story.append(Spacer(1, 20))

    # Sector Performance
    story.append(Paragraph("Sector Performance Analysis", heading_style))

    sector_data = [
        ["Sector", "Return", "vs Bench", "Contrib.", "Vol", "Beta", "Rating"],
        ["Technology", "+12.4%", "+3.2%", "+2.1%", "18.5%", "1.25", "OW"],
        ["Healthcare", "+9.8%", "+1.5%", "+1.4%", "14.2%", "0.95", "OW"],
        ["Financials", "+7.2%", "-0.3%", "+0.9%", "16.8%", "1.15", "N"],
        ["Energy", "+5.1%", "-2.4%", "+0.4%", "22.3%", "1.35", "UW"],
        ["Consumer Disc.", "+6.8%", "-0.7%", "+0.6%", "15.9%", "1.10", "N"],
        ["Industrials", "+8.1%", "+0.6%", "+0.8%", "14.5%", "1.05", "OW"],
    ]

    sector_table = Table(sector_data, colWidths=[90, 60, 60, 55, 50, 45, 50])
    sector_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005293')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafe')]),
    ]))
    story.append(sector_table)
    story.append(Spacer(1, 15))

    # Footnotes
    footnote_style = ParagraphStyle(
        'Footnote',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
    )

    footnotes = [
        "¹ Returns shown are net of fees. Past performance is not indicative of future results.",
        "² OW = Overweight, N = Neutral, UW = Underweight relative to benchmark.",
        "³ Risk metrics calculated using 36-month rolling window.",
    ]

    for note in footnotes:
        story.append(Paragraph(note, footnote_style))

    doc.build(story)

    return {
        "pdf": output_path,
        "type": "digital-text",
    }


def build_expected_markdown() -> str:
    """Build expected markdown output for evaluation."""
    return """# QUARTERLY INVESTMENT REVIEW - Q4 2024

## Executive Summary

The fourth quarter demonstrated resilient portfolio performance despite elevated market volatility. Total returns reached 8.7% for the quarter, outperforming the benchmark by 120 basis points. Fixed income allocations provided stability while equity positions captured upside momentum in technology and healthcare sectors. Risk-adjusted metrics remained favorable with a Sharpe ratio of 1.42.

## Key Performance Metrics

| Metric | Value |
|--------|-------|
| Total Return (QTD) | 8.7% |
| Benchmark Return | 7.5% |
| Alpha Generated | +1.2% |
| Sharpe Ratio | 1.42 |
| Max Drawdown | -3.2% |

## Asset Allocation

| Asset Class | Weight | Change |
|-------------|--------|--------|
| US Equities | 45.0% | +2.0% |
| Int'l Equities | 15.0% | -1.5% |
| Fixed Income | 30.0% | +0.5% |
| Alternatives | 7.5% | -0.5% |
| Cash | 2.5% | -0.5% |

## Sector Performance Analysis

| Sector | Return | vs Bench | Contrib. | Vol | Beta | Rating |
|--------|--------|----------|----------|-----|------|--------|
| Technology | +12.4% | +3.2% | +2.1% | 18.5% | 1.25 | OW |
| Healthcare | +9.8% | +1.5% | +1.4% | 14.2% | 0.95 | OW |
| Financials | +7.2% | -0.3% | +0.9% | 16.8% | 1.15 | N |
| Energy | +5.1% | -2.4% | +0.4% | 22.3% | 1.35 | UW |
| Consumer Disc. | +6.8% | -0.7% | +0.6% | 15.9% | 1.10 | N |
| Industrials | +8.1% | +0.6% | +0.8% | 14.5% | 1.05 | OW |

## Notes

¹ Returns shown are net of fees. Past performance is not indicative of future results.
² OW = Overweight, N = Neutral, UW = Underweight relative to benchmark.
³ Risk metrics calculated using 36-month rolling window.

---
CONFIDENTIAL - For authorized recipients only
Page 1 of 1
"""


def build_expected_metadata(expected_text: str) -> str:
    """Build JSON metadata for evaluation."""
    metadata = {
        "document": "complex_layout",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "critical_values": {
            "total_return": "8.7%",
            "benchmark_return": "7.5%",
            "sharpe_ratio": "1.42",
            "tech_return": "+12.4%",
            "energy_return": "+5.1%",
            "us_equities_weight": "45.0%",
        },
    }
    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    source_dir = base_dir / "source"
    expected_dir = base_dir / "expected"

    # Generate both versions
    image_result = generate_complex_layout_image(source_dir / "complex_layout_image.pdf")
    digital_result = generate_complex_layout_digital(source_dir / "complex_layout_digital.pdf")

    # Generate expected output
    expected_text = build_expected_markdown()
    (expected_dir / "complex_layout_expected.md").write_text(expected_text, encoding="utf-8")
    (expected_dir / "complex_layout_expected.json").write_text(build_expected_metadata(expected_text), encoding="utf-8")

    print("Generated complex layout documents:")
    print(f"  Image-based PDF: {image_result['pdf']}")
    print(f"  Image preview: {image_result['image']}")
    print(f"  Digital text PDF: {digital_result['pdf']}")
