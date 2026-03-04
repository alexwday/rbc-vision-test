"""
Process/Procedure Document test generator.

Creates a complex procedure document with flowcharts, swim lanes,
decision points, and step-by-step instructions alongside diagrams.
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
TEXT_COLOR = (30, 30, 30)
HEADER_BG = (45, 55, 72)
HEADER_TEXT = (255, 255, 255)
LANE_COLORS = [(232, 245, 253), (253, 245, 230), (232, 253, 240), (250, 232, 250)]
PROCESS_BOX = (66, 133, 244)
DECISION_BOX = (251, 188, 4)
START_END_BOX = (52, 168, 83)
CONNECTOR_COLOR = (100, 100, 100)
WARNING_BG = (255, 243, 224)
WARNING_BORDER = (255, 152, 0)
NOTE_BG = (227, 242, 253)
NOTE_BORDER = (33, 150, 243)


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
    angle = rng.uniform(-0.3, 0.3) * intensity
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")
    left = (rotated.width - image.width) // 2
    top = (rotated.height - image.height) // 2
    cropped = rotated.crop((left, top, left + image.width, top + image.height))

    noise = Image.effect_noise(image.size, int(4 * intensity))
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    blended = Image.blend(cropped, noise_rgb, 0.025 * intensity)
    return ImageEnhance.Contrast(blended).enhance(0.96 + rng.random() * 0.06)


def _draw_header(draw: ImageDraw.ImageDraw, doc_id: str, version: str, effective: str) -> int:
    """Draw document control header."""
    draw.rectangle((0, 0, PAGE_WIDTH, 90), fill=HEADER_BG)

    title_font = _load_font(28, bold=True)
    meta_font = _load_font(14)

    draw.text((MARGIN, 20), "Client Onboarding Procedure", font=title_font, fill=HEADER_TEXT)

    # Document metadata right side
    info_x = PAGE_WIDTH - MARGIN - 250
    draw.text((info_x, 15), f"Document ID: {doc_id}", font=meta_font, fill=HEADER_TEXT)
    draw.text((info_x, 35), f"Version: {version}", font=meta_font, fill=HEADER_TEXT)
    draw.text((info_x, 55), f"Effective: {effective}", font=meta_font, fill=HEADER_TEXT)

    # Classification banner
    draw.rectangle((MARGIN, 95, PAGE_WIDTH - MARGIN, 115), fill=(255, 235, 235), outline=(200, 100, 100))
    class_font = _load_font(12, bold=True)
    draw.text((MARGIN + 10, 97), "INTERNAL USE ONLY - DO NOT DISTRIBUTE", font=class_font, fill=(180, 50, 50))

    return 130


def _draw_footer(draw: ImageDraw.ImageDraw, page: int, total: int) -> None:
    """Draw footer with page number and revision info."""
    footer_font = _load_font(12)
    y = PAGE_HEIGHT - 50

    draw.line((MARGIN, y - 5, PAGE_WIDTH - MARGIN, y - 5), fill=(200, 200, 200), width=1)

    draw.text((MARGIN, y), "Owner: Operations Department | Review Cycle: Annual | Next Review: 2025-Q4", font=footer_font, fill=(120, 120, 120))
    draw.text((PAGE_WIDTH - MARGIN - 100, y), f"Page {page} of {total}", font=footer_font, fill=(120, 120, 120))


def _draw_box(draw: ImageDraw.ImageDraw, center: Tuple[int, int], size: Tuple[int, int], text: str, box_type: str, font: ImageFont.FreeTypeFont) -> None:
    """Draw a process box (rectangle), decision (diamond), or terminal (rounded)."""
    cx, cy = center
    w, h = size

    if box_type == "process":
        draw.rectangle((cx - w//2, cy - h//2, cx + w//2, cy + h//2), fill=PROCESS_BOX, outline=(40, 80, 150), width=2)
        text_color = (255, 255, 255)
    elif box_type == "decision":
        # Diamond shape
        points = [(cx, cy - h//2), (cx + w//2, cy), (cx, cy + h//2), (cx - w//2, cy)]
        draw.polygon(points, fill=DECISION_BOX, outline=(200, 150, 0), width=2)
        text_color = TEXT_COLOR
    elif box_type == "terminal":
        # Rounded rectangle (stadium shape)
        r = h // 2
        draw.ellipse((cx - w//2, cy - h//2, cx - w//2 + h, cy + h//2), fill=START_END_BOX)
        draw.ellipse((cx + w//2 - h, cy - h//2, cx + w//2, cy + h//2), fill=START_END_BOX)
        draw.rectangle((cx - w//2 + r, cy - h//2, cx + w//2 - r, cy + h//2), fill=START_END_BOX)
        text_color = (255, 255, 255)
    else:
        draw.rectangle((cx - w//2, cy - h//2, cx + w//2, cy + h//2), fill=(200, 200, 200))
        text_color = TEXT_COLOR

    # Center text (wrap if needed)
    lines = text.split('\n')
    line_height = font.size + 4
    total_height = len(lines) * line_height
    start_y = cy - total_height // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text((cx - text_w // 2, start_y + i * line_height), line, font=font, fill=text_color)


def _draw_arrow(draw: ImageDraw.ImageDraw, start: Tuple[int, int], end: Tuple[int, int], label: str = "", font: ImageFont.FreeTypeFont = None) -> None:
    """Draw an arrow with optional label."""
    draw.line((start, end), fill=CONNECTOR_COLOR, width=2)

    # Arrowhead
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx*dx + dy*dy)
    if length > 0:
        ux, uy = dx / length, dy / length
        # Arrow wings
        wing_len = 12
        wing_angle = 0.5
        wx1 = end[0] - wing_len * (ux * math.cos(wing_angle) - uy * math.sin(wing_angle))
        wy1 = end[1] - wing_len * (uy * math.cos(wing_angle) + ux * math.sin(wing_angle))
        wx2 = end[0] - wing_len * (ux * math.cos(-wing_angle) - uy * math.sin(-wing_angle))
        wy2 = end[1] - wing_len * (uy * math.cos(-wing_angle) + ux * math.sin(-wing_angle))
        draw.polygon([(end[0], end[1]), (wx1, wy1), (wx2, wy2)], fill=CONNECTOR_COLOR)

    if label and font:
        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2
        bbox = draw.textbbox((0, 0), label, font=font)
        # Background for label
        padding = 3
        draw.rectangle((mid_x - padding, mid_y - padding, mid_x + bbox[2] - bbox[0] + padding, mid_y + bbox[3] - bbox[1] + padding), fill=BACKGROUND)
        draw.text((mid_x, mid_y), label, font=font, fill=CONNECTOR_COLOR)


def _draw_swim_lane_flowchart(draw: ImageDraw.ImageDraw, top: int) -> int:
    """Draw a complex swim lane flowchart."""
    lanes = ["Client", "Relationship\nManager", "Compliance", "Operations"]
    lane_height = 380
    lane_width = (PAGE_WIDTH - 2 * MARGIN - 100) // len(lanes)
    label_width = 100

    chart_left = MARGIN + label_width
    chart_top = top

    # Draw lane backgrounds and labels
    for i, lane in enumerate(lanes):
        x = chart_left + i * lane_width
        draw.rectangle((x, chart_top, x + lane_width, chart_top + lane_height), fill=LANE_COLORS[i], outline=(180, 180, 180))

        # Vertical label on left
        label_font = _load_font(14, bold=True)
        lines = lane.split('\n')
        for j, line in enumerate(lines):
            draw.text((MARGIN + 10, chart_top + 10 + j * 18), line, font=label_font, fill=TEXT_COLOR)

    # Lane divider lines
    for i in range(len(lanes) + 1):
        x = chart_left + i * lane_width
        draw.line((x, chart_top, x, chart_top + lane_height), fill=(150, 150, 150), width=1)

    box_font = _load_font(11)
    label_font = _load_font(10)

    # Flowchart elements positions (lane_index, y_offset)
    # Lane centers
    def lane_center(idx):
        return chart_left + idx * lane_width + lane_width // 2

    y_positions = [chart_top + 50, chart_top + 130, chart_top + 210, chart_top + 290, chart_top + 370]

    # Start
    _draw_box(draw, (lane_center(0), y_positions[0]), (100, 40), "Start", "terminal", box_font)

    # Submit application
    _draw_box(draw, (lane_center(0), y_positions[1]), (120, 50), "Submit\nApplication", "process", box_font)
    _draw_arrow(draw, (lane_center(0), y_positions[0] + 20), (lane_center(0), y_positions[1] - 25))

    # Initial review
    _draw_box(draw, (lane_center(1), y_positions[1]), (120, 50), "Initial\nReview", "process", box_font)
    _draw_arrow(draw, (lane_center(0) + 60, y_positions[1]), (lane_center(1) - 60, y_positions[1]))

    # KYC Check decision
    _draw_box(draw, (lane_center(2), y_positions[1]), (110, 70), "KYC\nComplete?", "decision", box_font)
    _draw_arrow(draw, (lane_center(1) + 60, y_positions[1]), (lane_center(2) - 55, y_positions[1]))

    # Request more info (No path)
    _draw_box(draw, (lane_center(1), y_positions[2]), (120, 50), "Request\nMore Info", "process", box_font)
    _draw_arrow(draw, (lane_center(2), y_positions[1] + 35), (lane_center(2), y_positions[2]), "No", label_font)
    _draw_arrow(draw, (lane_center(2) - 55, y_positions[2]), (lane_center(1) + 60, y_positions[2]))
    # Loop back
    _draw_arrow(draw, (lane_center(1), y_positions[2] - 25), (lane_center(1), y_positions[1] + 25))

    # Risk assessment (Yes path)
    _draw_box(draw, (lane_center(2), y_positions[2]), (120, 50), "Risk\nAssessment", "process", box_font)
    _draw_arrow(draw, (lane_center(2) + 55, y_positions[1]), (lane_center(2) + 55, y_positions[2] - 25), "Yes", label_font)

    # Approval decision
    _draw_box(draw, (lane_center(2), y_positions[3]), (100, 70), "Approved?", "decision", box_font)
    _draw_arrow(draw, (lane_center(2), y_positions[2] + 25), (lane_center(2), y_positions[3] - 35))

    # Reject (No)
    _draw_box(draw, (lane_center(1), y_positions[3]), (100, 50), "Notify\nRejection", "process", box_font)
    _draw_arrow(draw, (lane_center(2) - 50, y_positions[3]), (lane_center(1) + 50, y_positions[3]), "No", label_font)

    # Setup account (Yes)
    _draw_box(draw, (lane_center(3), y_positions[3]), (120, 50), "Setup\nAccount", "process", box_font)
    _draw_arrow(draw, (lane_center(2) + 50, y_positions[3]), (lane_center(3) - 60, y_positions[3]), "Yes", label_font)

    # End states
    _draw_box(draw, (lane_center(1), y_positions[4] - 20), (80, 35), "End", "terminal", box_font)
    _draw_arrow(draw, (lane_center(1), y_positions[3] + 25), (lane_center(1), y_positions[4] - 38))

    _draw_box(draw, (lane_center(3), y_positions[4] - 20), (100, 35), "Complete", "terminal", box_font)
    _draw_arrow(draw, (lane_center(3), y_positions[3] + 25), (lane_center(3), y_positions[4] - 38))

    return chart_top + lane_height + 20


def _draw_procedure_steps(draw: ImageDraw.ImageDraw, top: int) -> int:
    """Draw numbered procedure steps with sub-steps."""
    title_font = _load_font(18, bold=True)
    step_font = _load_font(14, bold=True)
    body_font = _load_font(13)

    draw.text((MARGIN, top), "Detailed Procedure Steps", font=title_font, fill=TEXT_COLOR)

    steps = [
        ("1.", "Client Submission", [
            "1.1 Client completes Form CL-001 (Client Information Form)",
            "1.2 Required documents: Government ID, Proof of Address, Source of Funds",
            "1.3 Submit via secure portal or in-branch with RM assistance",
        ]),
        ("2.", "Initial Review (RM)", [
            "2.1 Verify form completeness within 1 business day",
            "2.2 Check document validity and legibility",
            "2.3 If incomplete, request additional information via Form CL-002",
            "    Note: Maximum 2 follow-up requests before escalation",
        ]),
        ("3.", "KYC/AML Compliance Check", [
            "3.1 Run automated screening against sanctions lists (OFAC, UN, EU)",
            "3.2 Perform Enhanced Due Diligence (EDD) if risk score > 70",
            "3.3 Document all findings in compliance system (Ref: POL-AML-003)",
            "3.4 Escalate PEP matches to Compliance Manager immediately",
        ]),
        ("4.", "Risk Assessment & Approval", [
            "4.1 Calculate client risk rating per Risk Matrix (Appendix B)",
            "4.2 Low/Medium risk: RM approval sufficient",
            "4.3 High risk: Requires Compliance Manager sign-off",
            "4.4 Record decision with rationale in audit trail",
        ]),
        ("5.", "Account Setup (Operations)", [
            "5.1 Create client profile in core banking system",
            "5.2 Generate account numbers and credentials",
            "5.3 Send welcome package within 2 business days",
            "5.4 Schedule 30-day follow-up call with RM",
        ]),
    ]

    y_cursor = top + 35

    for num, title, substeps in steps:
        draw.text((MARGIN, y_cursor), f"{num} {title}", font=step_font, fill=TEXT_COLOR)
        y_cursor += 24

        for substep in substeps:
            indent = MARGIN + 30 if not substep.startswith("    ") else MARGIN + 50
            text = substep.strip()
            draw.text((indent, y_cursor), text, font=body_font, fill=TEXT_COLOR)
            y_cursor += 20

        y_cursor += 8

    return y_cursor


def _draw_callout_boxes(draw: ImageDraw.ImageDraw, top: int) -> int:
    """Draw warning and note callout boxes."""
    box_width = (PAGE_WIDTH - 2 * MARGIN - 30) // 2

    # Warning box
    warning_top = top
    draw.rectangle((MARGIN, warning_top, MARGIN + box_width, warning_top + 100), fill=WARNING_BG, outline=WARNING_BORDER, width=2)

    warn_font = _load_font(14, bold=True)
    body_font = _load_font(12)

    draw.text((MARGIN + 10, warning_top + 8), "⚠ WARNING", font=warn_font, fill=(200, 100, 0))
    warning_text = [
        "Do NOT proceed with account opening if:",
        "• Client refuses to provide required documents",
        "• Sanctions screening returns positive match",
        "• Source of funds cannot be verified",
    ]
    y = warning_top + 30
    for line in warning_text:
        draw.text((MARGIN + 10, y), line, font=body_font, fill=TEXT_COLOR)
        y += 17

    # Note box
    note_left = MARGIN + box_width + 30
    draw.rectangle((note_left, warning_top, note_left + box_width, warning_top + 100), fill=NOTE_BG, outline=NOTE_BORDER, width=2)

    draw.text((note_left + 10, warning_top + 8), "📋 CROSS-REFERENCES", font=warn_font, fill=(30, 100, 180))
    note_text = [
        "• POL-AML-003: Anti-Money Laundering Policy",
        "• POL-KYC-001: Know Your Customer Standards",
        "• FORM-CL-001: Client Information Form",
        "• FORM-CL-002: Information Request Form",
    ]
    y = warning_top + 30
    for line in note_text:
        draw.text((note_left + 10, y), line, font=body_font, fill=TEXT_COLOR)
        y += 17

    return top + 120


def generate_procedure_document(
    output_dir: Path,
    expected_dir: Path,
    seed: int = 4096,
) -> Dict[str, Path]:
    """Generate a procedure document with flowcharts and steps."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(page)

    y_cursor = _draw_header(draw, "PROC-ONB-001", "3.2", "2024-01-15")

    # Section title
    section_font = _load_font(20, bold=True)
    draw.text((MARGIN, y_cursor), "1. Process Flow Overview", font=section_font, fill=TEXT_COLOR)
    y_cursor += 35

    y_cursor = _draw_swim_lane_flowchart(draw, y_cursor)

    draw.text((MARGIN, y_cursor), "2. Procedure Details", font=section_font, fill=TEXT_COLOR)
    y_cursor += 35

    y_cursor = _draw_procedure_steps(draw, y_cursor)

    y_cursor = _draw_callout_boxes(draw, y_cursor + 10)

    _draw_footer(draw, 1, 1)

    degraded = _apply_degradation(page, rng, 0.7)

    pdf_path = output_dir / "procedure_document.pdf"
    _save_pdf([degraded], pdf_path)

    expected_text = _build_expected_text()
    expected_md = expected_dir / "procedure_document_expected.md"
    expected_json = expected_dir / "procedure_document_expected.json"

    expected_md.write_text(expected_text, encoding="utf-8")
    expected_json.write_text(_build_expected_metadata(expected_text), encoding="utf-8")

    return {
        "pdf": pdf_path,
        "expected_markdown": expected_md,
        "expected_metadata": expected_json,
    }


def _build_expected_text() -> str:
    return """# Client Onboarding Procedure

Document ID: PROC-ONB-001
Version: 3.2
Effective: 2024-01-15

**INTERNAL USE ONLY - DO NOT DISTRIBUTE**

## 1. Process Flow Overview

### Swim Lane Flowchart

| Client | Relationship Manager | Compliance | Operations |
|--------|---------------------|------------|------------|

**Flow:**
1. Start (Client)
2. Submit Application (Client)
3. Initial Review (Relationship Manager)
4. KYC Complete? (Compliance) - Decision
   - No → Request More Info (RM) → loop back to Initial Review
   - Yes → Risk Assessment (Compliance)
5. Approved? (Compliance) - Decision
   - No → Notify Rejection (RM) → End
   - Yes → Setup Account (Operations) → Complete

## 2. Procedure Details

### 1. Client Submission
1.1 Client completes Form CL-001 (Client Information Form)
1.2 Required documents: Government ID, Proof of Address, Source of Funds
1.3 Submit via secure portal or in-branch with RM assistance

### 2. Initial Review (RM)
2.1 Verify form completeness within 1 business day
2.2 Check document validity and legibility
2.3 If incomplete, request additional information via Form CL-002
    Note: Maximum 2 follow-up requests before escalation

### 3. KYC/AML Compliance Check
3.1 Run automated screening against sanctions lists (OFAC, UN, EU)
3.2 Perform Enhanced Due Diligence (EDD) if risk score > 70
3.3 Document all findings in compliance system (Ref: POL-AML-003)
3.4 Escalate PEP matches to Compliance Manager immediately

### 4. Risk Assessment & Approval
4.1 Calculate client risk rating per Risk Matrix (Appendix B)
4.2 Low/Medium risk: RM approval sufficient
4.3 High risk: Requires Compliance Manager sign-off
4.4 Record decision with rationale in audit trail

### 5. Account Setup (Operations)
5.1 Create client profile in core banking system
5.2 Generate account numbers and credentials
5.3 Send welcome package within 2 business days
5.4 Schedule 30-day follow-up call with RM

## Callouts

### ⚠ WARNING
Do NOT proceed with account opening if:
- Client refuses to provide required documents
- Sanctions screening returns positive match
- Source of funds cannot be verified

### 📋 CROSS-REFERENCES
- POL-AML-003: Anti-Money Laundering Policy
- POL-KYC-001: Know Your Customer Standards
- FORM-CL-001: Client Information Form
- FORM-CL-002: Information Request Form

---
Owner: Operations Department | Review Cycle: Annual | Next Review: 2025-Q4
Page 1 of 1
"""


def _build_expected_metadata(expected_text: str) -> str:
    metadata = {
        "document": "procedure_document",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "critical_values": {
            "document_id": "PROC-ONB-001",
            "version": "3.2",
            "effective_date": "2024-01-15",
            "policy_reference": "POL-AML-003",
            "form_reference": "CL-001",
            "risk_threshold": "70",
        },
    }
    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    result = generate_procedure_document(base / "source", base / "expected")
    print("Generated procedure document:")
    for k, v in result.items():
        print(f"  {k}: {v}")
