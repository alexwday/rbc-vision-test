"""
Compliance Guidelines Document test generator.

Creates a guideline document with multi-level numbered sections,
checkbox requirement lists, definition tables, and policy boxes.
"""

from __future__ import annotations

import io
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import img2pdf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

PAGE_WIDTH = 1700
PAGE_HEIGHT = 2200
MARGIN = 60
BACKGROUND = (255, 255, 255)
TEXT_COLOR = (25, 25, 25)
HEADER_BG = (30, 60, 90)
HEADER_TEXT = (255, 255, 255)
SECTION_BG = (240, 245, 250)
MANDATORY_COLOR = (200, 30, 30)
OPTIONAL_COLOR = (80, 80, 80)
POLICY_BG = (255, 250, 230)
POLICY_BORDER = (200, 150, 50)
TABLE_HEADER_BG = (220, 230, 240)
TABLE_ALT = (248, 250, 252)
CHECK_COLOR = (30, 130, 30)


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


def _save_pdf(images: List[Image.Image], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    buffers = []
    for img in images:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        buffers.append(buf.getvalue())
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(buffers))


def _apply_degradation(image: Image.Image, rng: random.Random, intensity: float = 1.0) -> Image.Image:
    angle = rng.uniform(-0.35, 0.35) * intensity
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")
    left = (rotated.width - image.width) // 2
    top = (rotated.height - image.height) // 2
    cropped = rotated.crop((left, top, left + image.width, top + image.height))

    noise = Image.effect_noise(image.size, int(3 * intensity))
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    blended = Image.blend(cropped, noise_rgb, 0.02 * intensity)
    return ImageEnhance.Contrast(blended).enhance(0.97 + rng.random() * 0.05)


def _draw_header(draw: ImageDraw.ImageDraw) -> int:
    """Draw document header with control info."""
    draw.rectangle((0, 0, PAGE_WIDTH, 85), fill=HEADER_BG)

    title_font = _load_font(26, bold=True)
    meta_font = _load_font(12)

    draw.text((MARGIN, 15), "Data Classification & Handling Guidelines", font=title_font, fill=HEADER_TEXT)
    draw.text((MARGIN, 50), "Policy ID: POL-SEC-007  |  Classification: Internal  |  Owner: Information Security", font=meta_font, fill=HEADER_TEXT)

    # Version box
    ver_x = PAGE_WIDTH - MARGIN - 180
    draw.rectangle((ver_x, 10, ver_x + 170, 75), fill=(50, 80, 110), outline=HEADER_TEXT)
    draw.text((ver_x + 10, 15), "Version: 4.1", font=meta_font, fill=HEADER_TEXT)
    draw.text((ver_x + 10, 32), "Effective: 2024-03-01", font=meta_font, fill=HEADER_TEXT)
    draw.text((ver_x + 10, 49), "Supersedes: 3.5", font=meta_font, fill=HEADER_TEXT)

    return 100


def _draw_footer(draw: ImageDraw.ImageDraw, page: int, total: int) -> None:
    """Draw footer."""
    font = _load_font(11)
    y = PAGE_HEIGHT - 45

    draw.line((MARGIN, y - 8, PAGE_WIDTH - MARGIN, y - 8), fill=(180, 180, 180), width=1)
    draw.text((MARGIN, y), "Confidential - Internal Use Only | Unauthorized distribution prohibited", font=font, fill=(120, 120, 120))
    draw.text((PAGE_WIDTH - MARGIN - 80, y), f"Page {page} of {total}", font=font, fill=(120, 120, 120))


def _draw_section_header(draw: ImageDraw.ImageDraw, y: int, number: str, title: str) -> int:
    """Draw a section header with background."""
    font = _load_font(18, bold=True)

    draw.rectangle((MARGIN, y, PAGE_WIDTH - MARGIN, y + 32), fill=SECTION_BG)
    draw.text((MARGIN + 10, y + 6), f"{number}  {title}", font=font, fill=TEXT_COLOR)

    return y + 40


def _draw_checkbox(draw: ImageDraw.ImageDraw, pos: Tuple[int, int], checked: bool, label: str, font: ImageFont.FreeTypeFont, mandatory: bool = False) -> int:
    """Draw a checkbox with label. Returns width used."""
    x, y = pos
    box_size = 18

    # Draw box
    draw.rectangle((x, y, x + box_size, y + box_size), outline=TEXT_COLOR, width=2)

    if checked:
        # Draw checkmark
        draw.line((x + 4, y + 9, x + 8, y + 14), fill=CHECK_COLOR, width=3)
        draw.line((x + 8, y + 14, x + 15, y + 4), fill=CHECK_COLOR, width=3)

    # Label with mandatory indicator
    label_x = x + box_size + 8
    if mandatory:
        draw.text((label_x, y - 1), label, font=font, fill=TEXT_COLOR)
        req_font = _load_font(10, bold=True)
        label_bbox = draw.textbbox((0, 0), label, font=font)
        draw.text((label_x + label_bbox[2] - label_bbox[0] + 5, y + 2), "(Required)", font=req_font, fill=MANDATORY_COLOR)
    else:
        draw.text((label_x, y - 1), label, font=font, fill=TEXT_COLOR)

    return box_size + 8


def _draw_definition_table(draw: ImageDraw.ImageDraw, top: int, definitions: List[Tuple[str, str, str]]) -> int:
    """Draw a definition/lookup table."""
    col_widths = [200, 150, PAGE_WIDTH - 2 * MARGIN - 360]
    row_height = 45
    headers = ["Classification", "Label", "Description & Handling Requirements"]

    x0 = MARGIN
    y0 = top

    # Header row
    header_font = _load_font(13, bold=True)
    cell_font = _load_font(12)

    current_x = x0
    for i, header in enumerate(headers):
        draw.rectangle((current_x, y0, current_x + col_widths[i], y0 + 30), fill=TABLE_HEADER_BG, outline=(180, 180, 180))
        draw.text((current_x + 8, y0 + 7), header, font=header_font, fill=TEXT_COLOR)
        current_x += col_widths[i]

    y_cursor = y0 + 30

    for idx, (classification, label, description) in enumerate(definitions):
        bg = BACKGROUND if idx % 2 == 0 else TABLE_ALT
        row_h = row_height if len(description) < 80 else row_height + 20

        current_x = x0
        for i, value in enumerate([classification, label, description]):
            draw.rectangle((current_x, y_cursor, current_x + col_widths[i], y_cursor + row_h), fill=bg, outline=(200, 200, 200))

            # Word wrap for description column
            if i == 2 and len(value) > 50:
                words = value.split()
                lines = []
                current_line = []
                for word in words:
                    test = " ".join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test, font=cell_font)
                    if bbox[2] - bbox[0] < col_widths[i] - 16:
                        current_line.append(word)
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(" ".join(current_line))

                for j, line in enumerate(lines[:3]):  # Max 3 lines
                    draw.text((current_x + 8, y_cursor + 5 + j * 16), line, font=cell_font, fill=TEXT_COLOR)
            else:
                font = _load_font(12, bold=True) if i == 0 else cell_font
                color = MANDATORY_COLOR if classification == "Restricted" and i == 0 else TEXT_COLOR
                draw.text((current_x + 8, y_cursor + (row_h - 16) // 2), value, font=font, fill=color)

            current_x += col_widths[i]

        y_cursor += row_h

    return y_cursor + 15


def _draw_policy_box(draw: ImageDraw.ImageDraw, top: int, title: str, content: List[str]) -> int:
    """Draw a highlighted policy statement box."""
    box_height = 30 + len(content) * 20

    draw.rectangle((MARGIN, top, PAGE_WIDTH - MARGIN, top + box_height), fill=POLICY_BG, outline=POLICY_BORDER, width=2)

    title_font = _load_font(14, bold=True)
    content_font = _load_font(12)

    draw.text((MARGIN + 15, top + 8), title, font=title_font, fill=(150, 100, 0))

    y = top + 32
    for line in content:
        draw.text((MARGIN + 15, y), line, font=content_font, fill=TEXT_COLOR)
        y += 20

    return top + box_height + 15


def _draw_numbered_section(draw: ImageDraw.ImageDraw, top: int, items: List[Tuple[str, str, List[Tuple[str, str]]]]) -> int:
    """Draw multi-level numbered list."""
    section_font = _load_font(14, bold=True)
    subsection_font = _load_font(13)
    item_font = _load_font(12)

    y = top

    for section_num, section_title, subitems in items:
        draw.text((MARGIN, y), f"{section_num}  {section_title}", font=section_font, fill=TEXT_COLOR)
        y += 26

        for sub_num, sub_text in subitems:
            indent = MARGIN + 25
            draw.text((indent, y), sub_num, font=subsection_font, fill=TEXT_COLOR)
            draw.text((indent + 45, y), sub_text, font=item_font, fill=TEXT_COLOR)
            y += 22

        y += 10

    return y


def _draw_two_column_requirements(draw: ImageDraw.ImageDraw, top: int) -> int:
    """Draw requirements in two columns with checkboxes."""
    col_width = (PAGE_WIDTH - 2 * MARGIN - 40) // 2
    font = _load_font(12)

    title_font = _load_font(14, bold=True)
    draw.text((MARGIN, top), "Mandatory Requirements", font=title_font, fill=MANDATORY_COLOR)
    draw.text((MARGIN + col_width + 40, top), "Optional Enhancements", font=title_font, fill=OPTIONAL_COLOR)

    mandatory = [
        ("Encrypt data at rest using AES-256", True),
        ("Encrypt data in transit using TLS 1.2+", True),
        ("Implement access logging", True),
        ("Quarterly access reviews", True),
        ("Annual security training", True),
        ("Incident response plan", True),
    ]

    optional = [
        ("Hardware security modules (HSM)", False),
        ("Data loss prevention (DLP) tools", True),
        ("Advanced threat protection", False),
        ("Behavioral analytics", False),
        ("Zero-trust architecture", True),
        ("Automated compliance scanning", True),
    ]

    y_cursor = top + 28

    for i, ((m_label, m_checked), (o_label, o_checked)) in enumerate(zip(mandatory, optional)):
        _draw_checkbox(draw, (MARGIN, y_cursor), m_checked, m_label, font, mandatory=True)
        _draw_checkbox(draw, (MARGIN + col_width + 40, y_cursor), o_checked, o_label, font, mandatory=False)
        y_cursor += 28

    return y_cursor + 10


def generate_guidelines_document(
    output_dir: Path,
    expected_dir: Path,
    seed: int = 8192,
) -> Dict[str, Path]:
    """Generate a compliance guidelines document."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(page)

    y_cursor = _draw_header(draw)

    # Section 1: Purpose and Scope
    y_cursor = _draw_section_header(draw, y_cursor, "1", "Purpose and Scope")

    purpose_items = [
        ("1.1", "Purpose", [
            ("1.1.1", "Define data classification levels and handling requirements"),
            ("1.1.2", "Establish accountability for data protection"),
            ("1.1.3", "Ensure regulatory compliance (GDPR, CCPA, SOX)"),
        ]),
        ("1.2", "Scope", [
            ("1.2.1", "Applies to all employees, contractors, and third parties"),
            ("1.2.2", "Covers all data formats: electronic, paper, verbal"),
            ("1.2.3", "Includes data at rest, in transit, and in use"),
        ]),
    ]
    y_cursor = _draw_numbered_section(draw, y_cursor, purpose_items)

    # Section 2: Classification Levels
    y_cursor = _draw_section_header(draw, y_cursor, "2", "Data Classification Levels")

    definitions = [
        ("Public", "GREEN", "Information approved for public release. No restrictions on distribution."),
        ("Internal", "YELLOW", "Business information for internal use. Share only with employees who need it."),
        ("Confidential", "ORANGE", "Sensitive business data. Requires encryption and access controls. NDA required for third parties."),
        ("Restricted", "RED", "Highly sensitive data (PII, financial, health). Strictest controls. Encryption mandatory. Access logged and audited."),
    ]
    y_cursor = _draw_definition_table(draw, y_cursor, definitions)

    # Policy box
    y_cursor = _draw_policy_box(draw, y_cursor, "⚠ KEY POLICY STATEMENT", [
        "All data must be classified at creation. Unclassified data defaults to CONFIDENTIAL.",
        "Data owners are responsible for accurate classification and periodic review.",
        "Violations may result in disciplinary action up to and including termination.",
    ])

    # Section 3: Requirements
    y_cursor = _draw_section_header(draw, y_cursor, "3", "Security Requirements Checklist")
    y_cursor = _draw_two_column_requirements(draw, y_cursor)

    # Section 4: Additional guidelines
    y_cursor = _draw_section_header(draw, y_cursor, "4", "Handling Procedures")

    handling_items = [
        ("4.1", "Storage", [
            ("4.1.1", "Restricted data: encrypted storage only (approved systems list in Appendix A)"),
            ("4.1.2", "Confidential data: secure file shares with access controls"),
            ("4.1.3", "Retention per Records Management Policy (POL-REC-002)"),
        ]),
        ("4.2", "Transmission", [
            ("4.2.1", "Email: use encryption for Confidential and above"),
            ("4.2.2", "File transfer: SFTP or approved secure platforms only"),
            ("4.2.3", "No sensitive data via instant messaging or SMS"),
        ]),
        ("4.3", "Disposal", [
            ("4.3.1", "Electronic: secure deletion using approved tools"),
            ("4.3.2", "Paper: cross-cut shredding for Confidential and above"),
            ("4.3.3", "Media: physical destruction with certificate"),
        ]),
    ]
    y_cursor = _draw_numbered_section(draw, y_cursor, handling_items)

    _draw_footer(draw, 1, 1)

    degraded = _apply_degradation(page, rng, 0.7)

    pdf_path = output_dir / "guidelines_document.pdf"
    _save_pdf([degraded], pdf_path)

    expected_text = _build_expected_text()
    expected_md = expected_dir / "guidelines_document_expected.md"
    expected_json = expected_dir / "guidelines_document_expected.json"

    expected_md.write_text(expected_text, encoding="utf-8")
    expected_json.write_text(_build_expected_metadata(expected_text), encoding="utf-8")

    return {
        "pdf": pdf_path,
        "expected_markdown": expected_md,
        "expected_metadata": expected_json,
    }


def _build_expected_text() -> str:
    return """# Data Classification & Handling Guidelines

Policy ID: POL-SEC-007 | Classification: Internal | Owner: Information Security
Version: 4.1 | Effective: 2024-03-01 | Supersedes: 3.5

## 1. Purpose and Scope

### 1.1 Purpose
1.1.1 Define data classification levels and handling requirements
1.1.2 Establish accountability for data protection
1.1.3 Ensure regulatory compliance (GDPR, CCPA, SOX)

### 1.2 Scope
1.2.1 Applies to all employees, contractors, and third parties
1.2.2 Covers all data formats: electronic, paper, verbal
1.2.3 Includes data at rest, in transit, and in use

## 2. Data Classification Levels

| Classification | Label | Description & Handling Requirements |
|---------------|-------|-------------------------------------|
| Public | GREEN | Information approved for public release. No restrictions on distribution. |
| Internal | YELLOW | Business information for internal use. Share only with employees who need it. |
| Confidential | ORANGE | Sensitive business data. Requires encryption and access controls. NDA required for third parties. |
| Restricted | RED | Highly sensitive data (PII, financial, health). Strictest controls. Encryption mandatory. Access logged and audited. |

### ⚠ KEY POLICY STATEMENT
- All data must be classified at creation. Unclassified data defaults to CONFIDENTIAL.
- Data owners are responsible for accurate classification and periodic review.
- Violations may result in disciplinary action up to and including termination.

## 3. Security Requirements Checklist

### Mandatory Requirements
- [x] Encrypt data at rest using AES-256 (Required)
- [x] Encrypt data in transit using TLS 1.2+ (Required)
- [x] Implement access logging (Required)
- [x] Quarterly access reviews (Required)
- [x] Annual security training (Required)
- [x] Incident response plan (Required)

### Optional Enhancements
- [ ] Hardware security modules (HSM)
- [x] Data loss prevention (DLP) tools
- [ ] Advanced threat protection
- [ ] Behavioral analytics
- [x] Zero-trust architecture
- [x] Automated compliance scanning

## 4. Handling Procedures

### 4.1 Storage
4.1.1 Restricted data: encrypted storage only (approved systems list in Appendix A)
4.1.2 Confidential data: secure file shares with access controls
4.1.3 Retention per Records Management Policy (POL-REC-002)

### 4.2 Transmission
4.2.1 Email: use encryption for Confidential and above
4.2.2 File transfer: SFTP or approved secure platforms only
4.2.3 No sensitive data via instant messaging or SMS

### 4.3 Disposal
4.3.1 Electronic: secure deletion using approved tools
4.3.2 Paper: cross-cut shredding for Confidential and above
4.3.3 Media: physical destruction with certificate

---
Confidential - Internal Use Only | Unauthorized distribution prohibited
Page 1 of 1
"""


def _build_expected_metadata(expected_text: str) -> str:
    metadata = {
        "document": "guidelines_document",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "critical_values": {
            "policy_id": "POL-SEC-007",
            "version": "4.1",
            "effective_date": "2024-03-01",
            "encryption_standard": "AES-256",
            "tls_version": "TLS 1.2+",
            "related_policy": "POL-REC-002",
            "classification_levels": ["Public", "Internal", "Confidential", "Restricted"],
        },
    }
    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    result = generate_guidelines_document(base / "source", base / "expected")
    print("Generated guidelines document:")
    for k, v in result.items():
        print(f"  {k}: {v}")
