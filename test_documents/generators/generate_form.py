"""
Application form test document generator.

Simulates a filled form with mixed checked/unchecked boxes, handwriting-style
entries, a signature block, and an approval stamp.
"""

from __future__ import annotations

import io
import random
from pathlib import Path
from typing import Dict, List, Tuple

import img2pdf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

PAGE_SIZE = (1700, 2200)
MARGIN = 80
BACKGROUND = (252, 250, 247)
TEXT_COLOR = (28, 28, 28)
CHECK_COLOR = (20, 90, 40)
STAMP_COLOR = (175, 30, 30)


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


def _save_pdf(image: Image.Image, output_path: Path) -> None:
    image_rgb = image.convert("RGB")
    buffer = io.BytesIO()
    image_rgb.save(buffer, format="PNG")
    pdf_bytes = img2pdf.convert(buffer.getvalue())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)


def _apply_degradation(image: Image.Image, rng: random.Random) -> Image.Image:
    angle = rng.uniform(-0.6, 0.6)
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")

    left = (rotated.width - image.width) // 2
    top = (rotated.height - image.height) // 2
    cropped = rotated.crop((left, top, left + image.width, top + image.height))

    noise = Image.effect_noise(image.size, 6)
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    blended = Image.blend(cropped, noise_rgb, 0.05)

    return ImageEnhance.Contrast(blended).enhance(0.92 + rng.random() * 0.15)


def _char_width(font: ImageFont.FreeTypeFont | ImageFont.ImageFont, char: str) -> float:
    bbox = font.getbbox(char)
    return bbox[2] - bbox[0]


def _draw_handwriting(
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    rng: random.Random,
    jitter: float = 1.5,
    fill: Tuple[int, int, int] = TEXT_COLOR,
) -> None:
    """Render text with small jitter to mimic handwriting."""
    x, y = position
    for char in text:
        dx = rng.uniform(-jitter, jitter)
        dy = rng.uniform(-jitter, jitter)
        draw.text((x + dx, y + dy), char, font=font, fill=fill)
        x += _char_width(font, char) + 0.2


def _draw_checkbox(
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    label: str,
    checked: bool,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    box_size = 26
    x, y = position
    draw.rectangle((x, y, x + box_size, y + box_size), outline=TEXT_COLOR, width=2)
    if checked:
        draw.line((x + 5, y + 12, x + 12, y + 20), fill=CHECK_COLOR, width=3)
        draw.line((x + 12, y + 20, x + 22, y + 6), fill=CHECK_COLOR, width=3)
    draw.text((x + box_size + 10, y - 2), label, font=font, fill=TEXT_COLOR)


def _draw_stamp(base_image: Image.Image, center: Tuple[int, int], text: str) -> None:
    """Draw a circular approval stamp with rotated text."""
    stamp_size = 220
    stamp = Image.new("RGBA", (stamp_size, stamp_size), (0, 0, 0, 0))
    stamp_draw = ImageDraw.Draw(stamp)
    stamp_draw.ellipse((4, 4, stamp_size - 4, stamp_size - 4), outline=STAMP_COLOR, width=6)
    stamp_draw.ellipse((22, 22, stamp_size - 22, stamp_size - 22), outline=STAMP_COLOR, width=3)

    font = _load_font(42, bold=True)
    text_image = Image.new("RGBA", stamp.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_image)
    text_bbox = text_draw.textbbox((0, 0), text, font=font)
    text_pos = (
        (stamp_size - (text_bbox[2] - text_bbox[0])) / 2,
        (stamp_size - (text_bbox[3] - text_bbox[1])) / 2,
    )
    text_draw.text(text_pos, text, font=font, fill=STAMP_COLOR)
    rotated_text = text_image.rotate(-18, resample=Image.BICUBIC, expand=False)
    stamp.alpha_composite(rotated_text)

    x = center[0] - stamp_size // 2
    y = center[1] - stamp_size // 2
    base_image.paste(stamp, (x, y), stamp)


def generate_application_form(
    output_dir: Path,
    expected_dir: Path,
    seed: int = 84,
) -> Dict[str, Path]:
    """Generate the application form PDF and expected outputs."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", PAGE_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(46, bold=True)
    label_font = _load_font(26, bold=True)
    value_font = _load_font(26)
    handwriting_font = _load_font(28)
    small_font = _load_font(22)

    draw.text((MARGIN, MARGIN), "Client Application Form", font=title_font, fill=TEXT_COLOR)

    fields = [
        ("Applicant Name", "Alexandra Day"),
        ("Address", "1450 Maple Street"),
        ("City", "Vancouver, BC"),
        ("Email", "alex.day@example.com"),
        ("Phone", "(604) 555-1289"),
        ("Department", "Analytics & Insights"),
    ]

    y_cursor = MARGIN + 70
    for label, value in fields:
        draw.text((MARGIN, y_cursor), f"{label}:", font=label_font, fill=TEXT_COLOR)
        _draw_handwriting(draw, (MARGIN + 280, y_cursor - 4), value, handwriting_font, rng)
        y_cursor += 52

    draw.text((MARGIN, y_cursor + 10), "Preferred Contact Method", font=label_font, fill=TEXT_COLOR)
    _draw_checkbox(draw, (MARGIN + 10, y_cursor + 55), "Email", True, small_font)
    _draw_checkbox(draw, (MARGIN + 200, y_cursor + 55), "Phone", False, small_font)
    _draw_checkbox(draw, (MARGIN + 400, y_cursor + 55), "Weekly Newsletter", True, small_font)

    y_cursor += 140
    draw.text((MARGIN, y_cursor), "Program Selection", font=label_font, fill=TEXT_COLOR)
    _draw_checkbox(draw, (MARGIN + 10, y_cursor + 50), "Data Residency Waiver", True, small_font)
    _draw_checkbox(draw, (MARGIN + 300, y_cursor + 50), "Security Review Required", False, small_font)

    y_cursor += 150
    draw.text((MARGIN, y_cursor), "Signature", font=label_font, fill=TEXT_COLOR)
    signature_text = "Alex Day"
    _draw_handwriting(draw, (MARGIN + 180, y_cursor - 6), signature_text, handwriting_font, rng, jitter=2.2)
    draw.line((MARGIN + 170, y_cursor + 35, MARGIN + 520, y_cursor + 35), fill=TEXT_COLOR, width=2)

    draw.text((MARGIN, y_cursor + 70), "Date", font=label_font, fill=TEXT_COLOR)
    _draw_handwriting(draw, (MARGIN + 180, y_cursor + 64), "2024-07-15", handwriting_font, rng, jitter=1.2)
    draw.line((MARGIN + 170, y_cursor + 105, MARGIN + 360, y_cursor + 105), fill=TEXT_COLOR, width=2)

    _draw_stamp(image, center=(PAGE_SIZE[0] - 260, y_cursor - 20), text="APPROVED")

    degraded = _apply_degradation(image, rng)

    pdf_path = output_dir / "application_form.pdf"
    _save_pdf(degraded, pdf_path)

    expected_text = build_expected_text(fields)
    expected_md_path = expected_dir / "application_form_expected.md"
    expected_json_path = expected_dir / "application_form_expected.json"

    expected_md_path.write_text(expected_text, encoding="utf-8")
    expected_json_path.write_text(build_expected_metadata(expected_text), encoding="utf-8")

    return {
        "pdf": pdf_path,
        "expected_markdown": expected_md_path,
        "expected_metadata": expected_json_path,
    }


def build_expected_text(fields: List[Tuple[str, str]]) -> str:
    lines = [
        "# Client Application Form",
        "",
        "## Applicant Details",
    ]
    for label, value in fields:
        lines.append(f"- {label}: {value}")

    lines.extend(
        [
            "",
            "## Preferences",
            "- [x] Email",
            "- [ ] Phone",
            "- [x] Weekly Newsletter",
            "",
            "## Program Selection",
            "- [x] Data Residency Waiver",
            "- [ ] Security Review Required",
            "",
            "## Signature",
            "Signature: Alex Day",
            "Date: 2024-07-15",
            "Stamp: APPROVED",
        ]
    )

    return "\n".join(lines)


def build_expected_metadata(expected_text: str) -> str:
    import json

    metadata = {
        "document": "application_form",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "critical_values": {
            "applicant_name": "Alexandra Day",
            "email": "alex.day@example.com",
            "stamp": "APPROVED",
        },
    }
    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    output_directory = base_dir / "source"
    expected_directory = base_dir / "expected"
    result = generate_application_form(output_directory, expected_directory)
    print("Generated application form:")
    for key, value in result.items():
        print(f"- {key}: {value}")
