"""
Quarterly Shareholder Report test document generator.

Creates a complex financial report mimicking a bank's quarterly shareholder report
with multi-level tables, charts, footnotes, headers/footers, and dense layouts.
"""

from __future__ import annotations

import io
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple

import img2pdf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

PAGE_WIDTH = 1700
PAGE_HEIGHT = 2200
MARGIN = 60
BACKGROUND = (255, 255, 255)
TEXT_COLOR = (20, 20, 20)
HEADER_BG = (0, 51, 102)  # Dark blue bank header
HEADER_TEXT = (255, 255, 255)
TABLE_HEADER_BG = (230, 235, 240)
TABLE_ALT_ROW = (245, 247, 250)
ACCENT_COLOR = (0, 102, 153)
FOOTNOTE_COLOR = (80, 80, 80)
WATERMARK_COLOR = (240, 240, 240)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


def _save_pdf(images: List[Image.Image], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    png_bytes = []
    for img in images:
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="PNG")
        png_bytes.append(buffer.getvalue())
    pdf_bytes = img2pdf.convert(png_bytes)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)


def _apply_degradation(image: Image.Image, rng: random.Random, intensity: float = 1.0) -> Image.Image:
    angle = rng.uniform(-0.4, 0.4) * intensity
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")
    left = (rotated.width - image.width) // 2
    top = (rotated.height - image.height) // 2
    cropped = rotated.crop((left, top, left + image.width, top + image.height))

    noise = Image.effect_noise(image.size, int(3 * intensity))
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    blended = Image.blend(cropped, noise_rgb, 0.03 * intensity)

    contrast = ImageEnhance.Contrast(blended).enhance(0.95 + rng.random() * 0.08)
    return contrast


def _draw_watermark(image: Image.Image, text: str) -> None:
    """Draw diagonal watermark across image."""
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(120, bold=True)

    # Rotate and tile the watermark
    for y in range(0, image.height, 400):
        for x in range(-200, image.width, 600):
            draw.text((x, y), text, font=font, fill=(200, 200, 200, 40))

    rotated = overlay.rotate(30, resample=Image.BICUBIC, expand=False)
    image.paste(rotated, (0, 0), rotated)


def _draw_header(draw: ImageDraw.ImageDraw, image: Image.Image, page_num: int, total_pages: int) -> int:
    """Draw page header with bank branding. Returns Y position after header."""
    # Header background
    draw.rectangle((0, 0, PAGE_WIDTH, 100), fill=HEADER_BG)

    title_font = _load_font(32, bold=True)
    subtitle_font = _load_font(20)

    draw.text((MARGIN, 25), "ROYAL COMMONWEALTH BANK", font=title_font, fill=HEADER_TEXT)
    draw.text((MARGIN, 65), "Q4 2024 Quarterly Report to Shareholders", font=subtitle_font, fill=HEADER_TEXT)

    # Page number right-aligned
    page_text = f"Page {page_num} of {total_pages}"
    page_bbox = draw.textbbox((0, 0), page_text, font=subtitle_font)
    draw.text((PAGE_WIDTH - MARGIN - (page_bbox[2] - page_bbox[0]), 65), page_text, font=subtitle_font, fill=HEADER_TEXT)

    # Date
    draw.text((PAGE_WIDTH - MARGIN - 200, 25), "December 31, 2024", font=subtitle_font, fill=HEADER_TEXT)

    return 120


def _draw_footer(draw: ImageDraw.ImageDraw, page_num: int) -> None:
    """Draw page footer with legal disclaimer."""
    footer_font = _load_font(14)
    footer_y = PAGE_HEIGHT - 60

    draw.line((MARGIN, footer_y - 10, PAGE_WIDTH - MARGIN, footer_y - 10), fill=(180, 180, 180), width=1)

    disclaimer = "This report contains forward-looking statements. Past performance does not guarantee future results. See notes for important disclosures."
    draw.text((MARGIN, footer_y), disclaimer, font=footer_font, fill=FOOTNOTE_COLOR)

    # Confidential marking
    draw.text((PAGE_WIDTH - MARGIN - 200, footer_y + 20), "CONFIDENTIAL", font=_load_font(12, bold=True), fill=(150, 50, 50))


def _draw_complex_table(
    draw: ImageDraw.ImageDraw,
    top_left: Tuple[int, int],
    table_data: Dict,
) -> int:
    """Draw a complex financial table with multi-level headers and merged cells."""
    x0, y0 = top_left

    header_font = _load_font(16, bold=True)
    subheader_font = _load_font(14, bold=True)
    cell_font = _load_font(14)
    small_font = _load_font(12)

    # Column widths
    col_widths = [180, 90, 90, 90, 90, 90, 90, 90, 90, 100]
    row_height = 32
    header_height = 28

    total_width = sum(col_widths)

    # Level 1 headers (grouped)
    level1_headers = [
        ("", 1),
        ("Current Quarter", 3),
        ("Year-to-Date", 3),
        ("Prior Year", 2),
        ("", 1),
    ]

    # Level 2 headers
    level2_headers = ["Metric", "Q4 2024", "Q3 2024", "Change", "2024 YTD", "2023 YTD", "Change", "Q4 2023", "Change", "Notes"]

    # Draw level 1 headers
    current_x = x0
    for header, span in level1_headers:
        width = sum(col_widths[sum(s for _, s in level1_headers[:level1_headers.index((header, span))]): sum(s for _, s in level1_headers[:level1_headers.index((header, span))]) + span])
        if header:
            draw.rectangle((current_x, y0, current_x + width, y0 + header_height), fill=HEADER_BG)
            text_bbox = draw.textbbox((0, 0), header, font=subheader_font)
            text_x = current_x + (width - (text_bbox[2] - text_bbox[0])) // 2
            draw.text((text_x, y0 + 5), header, font=subheader_font, fill=HEADER_TEXT)
        current_x += width

    # Draw level 2 headers
    y1 = y0 + header_height
    current_x = x0
    for i, header in enumerate(level2_headers):
        draw.rectangle((current_x, y1, current_x + col_widths[i], y1 + header_height), fill=TABLE_HEADER_BG)
        draw.rectangle((current_x, y1, current_x + col_widths[i], y1 + header_height), outline=(180, 180, 180))

        text_bbox = draw.textbbox((0, 0), header, font=small_font)
        text_x = current_x + (col_widths[i] - (text_bbox[2] - text_bbox[0])) // 2
        draw.text((text_x, y1 + 6), header, font=small_font, fill=TEXT_COLOR)
        current_x += col_widths[i]

    # Table rows with data
    rows = [
        # Section header (merged across all columns)
        {"type": "section", "text": "Revenue"},
        {"type": "data", "values": ["Net Interest Income", "$2,847M", "$2,756M", "+3.3%", "$11,234M", "$10,456M", "+7.4%", "$2,654M", "+7.3%", "1,2"]},
        {"type": "data", "values": ["Non-Interest Income", "$1,234M", "$1,189M", "+3.8%", "$4,821M", "$4,234M", "+13.9%", "$1,098M", "+12.4%", "3"]},
        {"type": "subtotal", "values": ["Total Revenue", "$4,081M", "$3,945M", "+3.4%", "$16,055M", "$14,690M", "+9.3%", "$3,752M", "+8.8%", ""]},

        {"type": "section", "text": "Expenses"},
        {"type": "data", "values": ["Salaries & Benefits", "($1,245M)", "($1,198M)", "+3.9%", "($4,834M)", "($4,523M)", "+6.9%", "($1,156M)", "+7.7%", ""]},
        {"type": "data", "values": ["Technology & Ops", "($456M)", "($423M)", "+7.8%", "($1,756M)", "($1,534M)", "+14.5%", "($398M)", "+14.6%", "4"]},
        {"type": "data", "values": ["Other Operating", "($312M)", "($298M)", "+4.7%", "($1,198M)", "($1,087M)", "+10.2%", "($287M)", "+8.7%", ""]},
        {"type": "subtotal", "values": ["Total Expenses", "($2,013M)", "($1,919M)", "+4.9%", "($7,788M)", "($7,144M)", "+9.0%", "($1,841M)", "+9.3%", ""]},

        {"type": "section", "text": "Profitability"},
        {"type": "data", "values": ["Pre-Tax Income", "$2,068M", "$2,026M", "+2.1%", "$8,267M", "$7,546M", "+9.6%", "$1,911M", "+8.2%", ""]},
        {"type": "data", "values": ["Income Tax", "($517M)", "($507M)", "+2.0%", "($2,067M)", "($1,887M)", "+9.5%", "($478M)", "+8.2%", "5"]},
        {"type": "total", "values": ["Net Income", "$1,551M", "$1,519M", "+2.1%", "$6,200M", "$5,659M", "+9.6%", "$1,433M", "+8.2%", ""]},

        {"type": "spacer"},
        {"type": "section", "text": "Key Ratios"},
        {"type": "data", "values": ["Return on Equity", "14.2%", "13.9%", "+30bp", "14.1%", "13.2%", "+90bp", "13.5%", "+70bp", "6"]},
        {"type": "data", "values": ["Efficiency Ratio", "49.3%", "48.6%", "+70bp", "48.5%", "48.6%", "-10bp", "49.1%", "+20bp", ""]},
        {"type": "data", "values": ["CET1 Capital Ratio", "12.8%", "12.5%", "+30bp", "12.8%", "12.1%", "+70bp", "12.1%", "+70bp", "7"]},
    ]

    y_cursor = y1 + header_height

    for row in rows:
        if row["type"] == "spacer":
            y_cursor += 10
            continue
        elif row["type"] == "section":
            # Section header spans all columns
            draw.rectangle((x0, y_cursor, x0 + total_width, y_cursor + row_height), fill=(220, 225, 230))
            draw.text((x0 + 10, y_cursor + 8), row["text"], font=header_font, fill=ACCENT_COLOR)
            y_cursor += row_height
        else:
            bg_color = BACKGROUND if rows.index(row) % 2 == 0 else TABLE_ALT_ROW
            if row["type"] == "subtotal":
                bg_color = (235, 240, 245)
            elif row["type"] == "total":
                bg_color = (200, 220, 235)

            draw.rectangle((x0, y_cursor, x0 + total_width, y_cursor + row_height), fill=bg_color)

            current_x = x0
            for i, value in enumerate(row["values"]):
                draw.rectangle((current_x, y_cursor, current_x + col_widths[i], y_cursor + row_height), outline=(200, 200, 200))

                font = header_font if row["type"] in ("subtotal", "total") and i == 0 else cell_font
                if i == 0:
                    # Left-align metric names
                    indent = 20 if row["type"] == "data" else 10
                    draw.text((current_x + indent, y_cursor + 8), value, font=font, fill=TEXT_COLOR)
                else:
                    # Center-align values
                    text_bbox = draw.textbbox((0, 0), value, font=cell_font)
                    text_x = current_x + (col_widths[i] - (text_bbox[2] - text_bbox[0])) // 2

                    # Color negative changes red, positive green
                    color = TEXT_COLOR
                    if "+" in value and "%" in value:
                        color = (0, 120, 0)
                    elif value.startswith("(") or value.startswith("-"):
                        color = (180, 0, 0)

                    draw.text((text_x, y_cursor + 8), value, font=cell_font, fill=color)

                current_x += col_widths[i]

            y_cursor += row_height

    # Border around entire table
    draw.rectangle((x0, y0, x0 + total_width, y_cursor), outline=(100, 100, 100), width=2)

    return y_cursor + 20


def _draw_chart_area(draw: ImageDraw.ImageDraw, top_left: Tuple[int, int], width: int, height: int) -> int:
    """Draw a simulated bar chart with labels."""
    x0, y0 = top_left

    title_font = _load_font(18, bold=True)
    label_font = _load_font(12)
    value_font = _load_font(11)

    # Chart title
    draw.text((x0, y0), "Quarterly Net Income Trend ($ Millions)", font=title_font, fill=TEXT_COLOR)

    chart_top = y0 + 35
    chart_height = height - 70
    chart_width = width - 80

    # Y-axis
    draw.line((x0 + 50, chart_top, x0 + 50, chart_top + chart_height), fill=TEXT_COLOR, width=2)
    # X-axis
    draw.line((x0 + 50, chart_top + chart_height, x0 + 50 + chart_width, chart_top + chart_height), fill=TEXT_COLOR, width=2)

    # Y-axis labels
    y_labels = ["2,000", "1,500", "1,000", "500", "0"]
    for i, label in enumerate(y_labels):
        y_pos = chart_top + (i * chart_height // 4)
        draw.text((x0 + 5, y_pos - 6), label, font=value_font, fill=FOOTNOTE_COLOR)
        draw.line((x0 + 48, y_pos, x0 + 52, y_pos), fill=TEXT_COLOR, width=1)
        # Grid line
        draw.line((x0 + 52, y_pos, x0 + 50 + chart_width, y_pos), fill=(220, 220, 220), width=1)

    # Bars
    quarters = ["Q1'23", "Q2'23", "Q3'23", "Q4'23", "Q1'24", "Q2'24", "Q3'24", "Q4'24"]
    values = [1345, 1412, 1398, 1433, 1478, 1534, 1519, 1551]
    bar_width = (chart_width - 40) // len(quarters)

    for i, (quarter, value) in enumerate(zip(quarters, values)):
        bar_height = int((value / 2000) * chart_height)
        bar_x = x0 + 60 + i * bar_width
        bar_y = chart_top + chart_height - bar_height

        color = ACCENT_COLOR if "24" in quarter else (150, 180, 200)
        draw.rectangle((bar_x, bar_y, bar_x + bar_width - 10, chart_top + chart_height), fill=color)

        # Value on top of bar
        draw.text((bar_x + 5, bar_y - 15), str(value), font=value_font, fill=TEXT_COLOR)

        # X-axis label
        draw.text((bar_x + 5, chart_top + chart_height + 5), quarter, font=label_font, fill=TEXT_COLOR)

    # Legend
    legend_y = y0 + 10
    draw.rectangle((x0 + width - 180, legend_y, x0 + width - 165, legend_y + 12), fill=ACCENT_COLOR)
    draw.text((x0 + width - 160, legend_y - 2), "2024", font=label_font, fill=TEXT_COLOR)
    draw.rectangle((x0 + width - 100, legend_y, x0 + width - 85, legend_y + 12), fill=(150, 180, 200))
    draw.text((x0 + width - 80, legend_y - 2), "2023", font=label_font, fill=TEXT_COLOR)

    return y0 + height


def _draw_footnotes(draw: ImageDraw.ImageDraw, top: int, footnotes: List[Tuple[str, str]]) -> int:
    """Draw dense footnotes section."""
    font = _load_font(11)
    superscript_font = _load_font(9)

    draw.text((MARGIN, top), "Notes:", font=_load_font(14, bold=True), fill=TEXT_COLOR)

    y_cursor = top + 25
    col_width = (PAGE_WIDTH - 2 * MARGIN) // 2

    for i, (marker, text) in enumerate(footnotes):
        col = i % 2
        row = i // 2
        x = MARGIN + col * col_width
        y = y_cursor + row * 18

        # Superscript marker
        draw.text((x, y - 3), marker, font=superscript_font, fill=ACCENT_COLOR)
        draw.text((x + 12, y), text, font=font, fill=FOOTNOTE_COLOR)

    return y_cursor + (len(footnotes) // 2 + 1) * 18 + 10


def _draw_executive_summary(draw: ImageDraw.ImageDraw, top: int) -> int:
    """Draw executive summary with paragraph text and inline footnote references."""
    title_font = _load_font(20, bold=True)
    body_font = _load_font(15)

    draw.text((MARGIN, top), "Executive Summary", font=title_font, fill=ACCENT_COLOR)

    paragraphs = [
        "Royal Commonwealth Bank delivered strong fourth quarter results with net income of $1,551 million, "
        "up 8.2% year-over-year and 2.1% quarter-over-quarter.^1 Total revenue reached $4,081 million driven by "
        "robust growth in both net interest income (+7.3% YoY) and non-interest income (+12.4% YoY).^2",

        "The efficiency ratio of 49.3% reflects continued investment in technology modernization initiatives "
        "while maintaining disciplined expense management.^4 Our CET1 capital ratio strengthened to 12.8%, "
        "providing substantial buffer above regulatory minimums.^7",

        "Year-to-date net income of $6,200 million represents a 9.6% increase over prior year, with return "
        "on equity improving 90 basis points to 14.1%.^6 Management remains focused on sustainable growth "
        "while prudently managing risk in an evolving economic environment.",
    ]

    y_cursor = top + 35
    line_height = 22
    max_width = PAGE_WIDTH - 2 * MARGIN

    for para in paragraphs:
        # Simple word wrap
        words = para.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=body_font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        for line in lines:
            draw.text((MARGIN, y_cursor), line, font=body_font, fill=TEXT_COLOR)
            y_cursor += line_height

        y_cursor += 10  # Paragraph spacing

    return y_cursor + 10


def generate_shareholder_report(
    output_dir: Path,
    expected_dir: Path,
    seed: int = 2024,
) -> Dict[str, Path]:
    """Generate a multi-page quarterly shareholder report."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    pages = []

    # Page 1: Executive summary and financial highlights table
    page1 = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BACKGROUND)
    draw1 = ImageDraw.Draw(page1)

    y_cursor = _draw_header(draw1, page1, 1, 2)
    y_cursor = _draw_executive_summary(draw1, y_cursor)

    draw1.text((MARGIN, y_cursor), "Financial Highlights", font=_load_font(20, bold=True), fill=ACCENT_COLOR)
    y_cursor += 35

    y_cursor = _draw_complex_table(draw1, (MARGIN, y_cursor), {})

    _draw_footer(draw1, 1)
    _draw_watermark(page1, "DRAFT")
    pages.append(_apply_degradation(page1, rng, 0.8))

    # Page 2: Charts and additional footnotes
    page2 = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BACKGROUND)
    draw2 = ImageDraw.Draw(page2)

    y_cursor = _draw_header(draw2, page2, 2, 2)

    draw2.text((MARGIN, y_cursor), "Performance Trends", font=_load_font(20, bold=True), fill=ACCENT_COLOR)
    y_cursor += 35

    y_cursor = _draw_chart_area(draw2, (MARGIN, y_cursor), PAGE_WIDTH - 2 * MARGIN, 350)

    y_cursor += 30

    footnotes = [
        ("1", "Net income attributable to common shareholders."),
        ("2", "Includes trading gains of $234M in Q4 2024."),
        ("3", "Non-interest income includes wealth management fees."),
        ("4", "Technology spend includes $89M one-time modernization costs."),
        ("5", "Effective tax rate of 25.0% reflects jurisdictional mix."),
        ("6", "ROE calculated using average common equity."),
        ("7", "CET1 ratio under Basel III standardized approach."),
        ("8", "Prior period figures restated for comparability."),
    ]

    y_cursor = _draw_footnotes(draw2, y_cursor, footnotes)

    # Additional dense text block
    draw2.text((MARGIN, y_cursor + 20), "Risk Factors and Forward-Looking Statements", font=_load_font(16, bold=True), fill=TEXT_COLOR)

    risk_text = (
        "This report contains forward-looking statements within the meaning of applicable securities laws. "
        "Such statements involve risks and uncertainties that may cause actual results to differ materially "
        "from those set forth in these statements. Factors that could cause such differences include: changes "
        "in interest rates and monetary policy; credit quality deterioration; regulatory changes; competitive "
        "pressures; economic conditions; technological disruption; cybersecurity threats; and other factors "
        "described in our Annual Report. We undertake no obligation to update forward-looking statements."
    )

    body_font = _load_font(12)
    words = risk_text.split()
    lines = []
    current_line = []
    max_width = PAGE_WIDTH - 2 * MARGIN

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw2.textbbox((0, 0), test_line, font=body_font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_text = y_cursor + 45
    for line in lines:
        draw2.text((MARGIN, y_text), line, font=body_font, fill=FOOTNOTE_COLOR)
        y_text += 16

    _draw_footer(draw2, 2)
    _draw_watermark(page2, "DRAFT")
    pages.append(_apply_degradation(page2, rng, 0.8))

    # Save PDF
    pdf_path = output_dir / "shareholder_report.pdf"
    _save_pdf(pages, pdf_path)

    # Generate expected outputs
    expected_text = _build_expected_text()
    expected_md_path = expected_dir / "shareholder_report_expected.md"
    expected_json_path = expected_dir / "shareholder_report_expected.json"

    expected_md_path.write_text(expected_text, encoding="utf-8")
    expected_json_path.write_text(_build_expected_metadata(expected_text), encoding="utf-8")

    return {
        "pdf": pdf_path,
        "expected_markdown": expected_md_path,
        "expected_metadata": expected_json_path,
    }


def _build_expected_text() -> str:
    """Construct expected markdown output."""
    return """# ROYAL COMMONWEALTH BANK
## Q4 2024 Quarterly Report to Shareholders
Date: December 31, 2024

## Executive Summary

Royal Commonwealth Bank delivered strong fourth quarter results with net income of $1,551 million, up 8.2% year-over-year and 2.1% quarter-over-quarter.^1 Total revenue reached $4,081 million driven by robust growth in both net interest income (+7.3% YoY) and non-interest income (+12.4% YoY).^2

The efficiency ratio of 49.3% reflects continued investment in technology modernization initiatives while maintaining disciplined expense management.^4 Our CET1 capital ratio strengthened to 12.8%, providing substantial buffer above regulatory minimums.^7

Year-to-date net income of $6,200 million represents a 9.6% increase over prior year, with return on equity improving 90 basis points to 14.1%.^6 Management remains focused on sustainable growth while prudently managing risk in an evolving economic environment.

## Financial Highlights

### Revenue

| Metric | Q4 2024 | Q3 2024 | Change | 2024 YTD | 2023 YTD | Change | Q4 2023 | Change | Notes |
|--------|---------|---------|--------|----------|----------|--------|---------|--------|-------|
| Net Interest Income | $2,847M | $2,756M | +3.3% | $11,234M | $10,456M | +7.4% | $2,654M | +7.3% | 1,2 |
| Non-Interest Income | $1,234M | $1,189M | +3.8% | $4,821M | $4,234M | +13.9% | $1,098M | +12.4% | 3 |
| **Total Revenue** | **$4,081M** | **$3,945M** | **+3.4%** | **$16,055M** | **$14,690M** | **+9.3%** | **$3,752M** | **+8.8%** | |

### Expenses

| Metric | Q4 2024 | Q3 2024 | Change | 2024 YTD | 2023 YTD | Change | Q4 2023 | Change | Notes |
|--------|---------|---------|--------|----------|----------|--------|---------|--------|-------|
| Salaries & Benefits | ($1,245M) | ($1,198M) | +3.9% | ($4,834M) | ($4,523M) | +6.9% | ($1,156M) | +7.7% | |
| Technology & Ops | ($456M) | ($423M) | +7.8% | ($1,756M) | ($1,534M) | +14.5% | ($398M) | +14.6% | 4 |
| Other Operating | ($312M) | ($298M) | +4.7% | ($1,198M) | ($1,087M) | +10.2% | ($287M) | +8.7% | |
| **Total Expenses** | **($2,013M)** | **($1,919M)** | **+4.9%** | **($7,788M)** | **($7,144M)** | **+9.0%** | **($1,841M)** | **+9.3%** | |

### Profitability

| Metric | Q4 2024 | Q3 2024 | Change | 2024 YTD | 2023 YTD | Change | Q4 2023 | Change | Notes |
|--------|---------|---------|--------|----------|----------|--------|---------|--------|-------|
| Pre-Tax Income | $2,068M | $2,026M | +2.1% | $8,267M | $7,546M | +9.6% | $1,911M | +8.2% | |
| Income Tax | ($517M) | ($507M) | +2.0% | ($2,067M) | ($1,887M) | +9.5% | ($478M) | +8.2% | 5 |
| **Net Income** | **$1,551M** | **$1,519M** | **+2.1%** | **$6,200M** | **$5,659M** | **+9.6%** | **$1,433M** | **+8.2%** | |

### Key Ratios

| Metric | Q4 2024 | Q3 2024 | Change | 2024 YTD | 2023 YTD | Change | Q4 2023 | Change | Notes |
|--------|---------|---------|--------|----------|----------|--------|---------|--------|-------|
| Return on Equity | 14.2% | 13.9% | +30bp | 14.1% | 13.2% | +90bp | 13.5% | +70bp | 6 |
| Efficiency Ratio | 49.3% | 48.6% | +70bp | 48.5% | 48.6% | -10bp | 49.1% | +20bp | |
| CET1 Capital Ratio | 12.8% | 12.5% | +30bp | 12.8% | 12.1% | +70bp | 12.1% | +70bp | 7 |

## Performance Trends

[Bar Chart: Quarterly Net Income Trend ($ Millions)]
- Q1'23: 1345
- Q2'23: 1412
- Q3'23: 1398
- Q4'23: 1433
- Q1'24: 1478
- Q2'24: 1534
- Q3'24: 1519
- Q4'24: 1551

## Notes

1. Net income attributable to common shareholders.
2. Includes trading gains of $234M in Q4 2024.
3. Non-interest income includes wealth management fees.
4. Technology spend includes $89M one-time modernization costs.
5. Effective tax rate of 25.0% reflects jurisdictional mix.
6. ROE calculated using average common equity.
7. CET1 ratio under Basel III standardized approach.
8. Prior period figures restated for comparability.

## Risk Factors and Forward-Looking Statements

This report contains forward-looking statements within the meaning of applicable securities laws. Such statements involve risks and uncertainties that may cause actual results to differ materially from those set forth in these statements. Factors that could cause such differences include: changes in interest rates and monetary policy; credit quality deterioration; regulatory changes; competitive pressures; economic conditions; technological disruption; cybersecurity threats; and other factors described in our Annual Report. We undertake no obligation to update forward-looking statements.

---
Page 1 of 2 | Page 2 of 2
CONFIDENTIAL
"""


def _build_expected_metadata(expected_text: str) -> str:
    """Return JSON metadata for evaluation."""
    metadata = {
        "document": "shareholder_report",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "pages": 2,
        "critical_values": {
            "net_income_q4": "$1,551M",
            "total_revenue_q4": "$4,081M",
            "yoy_net_income_change": "+8.2%",
            "cet1_ratio": "12.8%",
            "roe": "14.1%",
            "ytd_net_income": "$6,200M",
            "efficiency_ratio": "49.3%",
        },
    }
    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    result = generate_shareholder_report(base_dir / "source", base_dir / "expected")
    print("Generated shareholder report:")
    for key, value in result.items():
        print(f"  {key}: {value}")
