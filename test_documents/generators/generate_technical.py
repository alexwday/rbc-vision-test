"""
Technical document test generator.

Creates a page mixing math expressions, code, multilingual text, and a simple
flowchart to stress OCR handling of varied content.
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
BACKGROUND = (248, 248, 250)
TEXT_COLOR = (25, 25, 25)


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
    angle = rng.uniform(-0.8, 0.8)
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")
    left = (rotated.width - image.width) // 2
    top = (rotated.height - image.height) // 2
    cropped = rotated.crop((left, top, left + image.width, top + image.height))

    noise = Image.effect_noise(image.size, 5)
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    blended = Image.blend(cropped, noise_rgb, 0.04)
    return ImageEnhance.Contrast(blended).enhance(0.9 + rng.random() * 0.18)


def _draw_flowchart(draw: ImageDraw.ImageDraw, origin: Tuple[int, int], font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> None:
    """Draw a simple flowchart with arrows."""
    x, y = origin
    box_size = (220, 70)
    spacing = 140
    steps = ["Input", "Parse", "Transform", "Output"]

    for idx, label in enumerate(steps):
        box_x = x + idx * spacing
        box_y = y
        draw.rectangle(
            (box_x, box_y, box_x + box_size[0], box_y + box_size[1]),
            outline=TEXT_COLOR,
            width=3,
        )
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_x = box_x + (box_size[0] - (text_bbox[2] - text_bbox[0])) / 2
        text_y = box_y + (box_size[1] - (text_bbox[3] - text_bbox[1])) / 2
        draw.text((text_x, text_y), label, font=font, fill=TEXT_COLOR)

        if idx < len(steps) - 1:
            arrow_x_start = box_x + box_size[0]
            arrow_y = box_y + box_size[1] / 2
            arrow_x_end = arrow_x_start + (spacing - box_size[0])
            draw.line((arrow_x_start, arrow_y, arrow_x_end, arrow_y), fill=TEXT_COLOR, width=3)
            draw.polygon(
                [
                    (arrow_x_end, arrow_y),
                    (arrow_x_end - 12, arrow_y - 8),
                    (arrow_x_end - 12, arrow_y + 8),
                ],
                fill=TEXT_COLOR,
            )


def generate_technical_document(
    output_dir: Path,
    expected_dir: Path,
    seed: int = 128,
) -> Dict[str, Path]:
    """Generate the technical document PDF and expected outputs."""
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", PAGE_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(44, bold=True)
    header_font = _load_font(28, bold=True)
    body_font = _load_font(26)
    code_font = _load_font(24)

    draw.text((MARGIN, MARGIN), "Technical Research Notes", font=title_font, fill=TEXT_COLOR)

    # Equations
    equations = [
        "E = mc²",
        "∫₀¹ x² dx = 1/3",
        "Σ (α + β + γ) = Δ",
    ]
    eq_top = MARGIN + 80
    draw.text((MARGIN, eq_top), "Equations", font=header_font, fill=TEXT_COLOR)
    for idx, eq in enumerate(equations):
        draw.text((MARGIN + 10, eq_top + 40 + idx * 34), f"- {eq}", font=body_font, fill=TEXT_COLOR)

    # Code block
    code_lines = [
        "def fibonacci(n):",
        "    if n <= 1:",
        "        return n",
        "    return fibonacci(n-1) + fibonacci(n-2)",
    ]
    code_top = eq_top + 160
    draw.text((MARGIN, code_top), "Python Example", font=header_font, fill=TEXT_COLOR)
    code_box_top = code_top + 40
    for idx, line in enumerate(code_lines):
        draw.text((MARGIN + 20, code_box_top + idx * 32), line, font=code_font, fill=TEXT_COLOR)

    # Multilingual text
    language_lines = [
        "English: The pipeline orchestrates OCR across multi-page documents.",
        "Français: Le système conserve la structure et les caractères accentués.",
        "日本語: 日本語のサンプルテキストです。",
        "العربية: العربية نظام بسيط لمعالجة النص.",
    ]
    lang_top = code_box_top + 160
    draw.text((MARGIN, lang_top), "Multilingual Notes", font=header_font, fill=TEXT_COLOR)
    for idx, line in enumerate(language_lines):
        draw.text((MARGIN + 10, lang_top + 40 + idx * 32), f"- {line}", font=body_font, fill=TEXT_COLOR)

    # Flowchart
    flow_top = lang_top + 200
    draw.text((MARGIN, flow_top), "Flowchart", font=header_font, fill=TEXT_COLOR)
    _draw_flowchart(draw, origin=(MARGIN + 10, flow_top + 50), font=body_font)

    degraded = _apply_degradation(image, rng)

    pdf_path = output_dir / "technical_document.pdf"
    _save_pdf(degraded, pdf_path)

    expected_text = build_expected_text(equations, code_lines, language_lines)
    expected_md_path = expected_dir / "technical_document_expected.md"
    expected_json_path = expected_dir / "technical_document_expected.json"

    expected_md_path.write_text(expected_text, encoding="utf-8")
    expected_json_path.write_text(build_expected_metadata(expected_text), encoding="utf-8")

    return {
        "pdf": pdf_path,
        "expected_markdown": expected_md_path,
        "expected_metadata": expected_json_path,
    }


def build_expected_text(
    equations: List[str],
    code_lines: List[str],
    language_lines: List[str],
) -> str:
    lines = [
        "# Technical Research Notes",
        "",
        "## Equations",
    ]
    for eq in equations:
        lines.append(f"- {eq}")

    lines.extend(
        [
            "",
            "## Python Example",
            "```python",
            *code_lines,
            "```",
            "",
            "## Multilingual Notes",
        ]
    )
    for line in language_lines:
        lines.append(f"- {line}")

    lines.extend(
        [
            "",
            "## Flowchart",
            "Input -> Parse -> Transform -> Output",
        ]
    )

    return "\n".join(lines)


def build_expected_metadata(expected_text: str) -> str:
    import json

    metadata = {
        "document": "technical_document",
        "character_count": len(expected_text),
        "word_count": len(expected_text.split()),
        "critical_values": {
            "equation_energy": "E = mc²",
            "integral": "∫₀¹ x² dx = 1/3",
            "flowchart": "Input -> Parse -> Transform -> Output",
        },
    }
    return json.dumps(metadata, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    output_directory = base_dir / "source"
    expected_directory = base_dir / "expected"
    result = generate_technical_document(output_directory, expected_directory)
    print("Generated technical document:")
    for key, value in result.items():
        print(f"- {key}: {value}")
