"""
Generate a self-contained HTML report with side-by-side PDF page images
and OCR text for visual comparison.
"""

from __future__ import annotations

import base64
import io
import html as html_mod
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

logger = logging.getLogger(__name__)

MAX_IMAGE_WIDTH = 800
JPEG_QUALITY = 85


@dataclass
class DocumentResult:
    """Collected results for one PDF document."""

    name: str
    page_images: List[Image.Image]
    page_texts: List[str]
    metrics: Dict = field(default_factory=dict)
    usage: List[dict] = field(default_factory=list)


def _image_to_base64(img: Image.Image) -> str:
    """Downscale and encode a PIL image as a base64 JPEG data URI."""
    w, h = img.size
    if w > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / w
        img = img.resize((MAX_IMAGE_WIDTH, int(h * ratio)), Image.LANCZOS)

    if img.mode == "RGBA":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _metric_color(value: Optional[float], thresholds: tuple = (0.05, 0.15)) -> str:
    """Return a CSS color based on error rate thresholds."""
    if value is None:
        return "#888"
    if value <= thresholds[0]:
        return "#2ecc71"  # green
    if value <= thresholds[1]:
        return "#f39c12"  # orange
    return "#e74c3c"  # red


def _fmt_metric(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def generate_html_report(
    results: List[DocumentResult],
    system_prompt: str,
    output_path: Path | str,
    model_name: str = "",
) -> Path:
    """Write a self-contained HTML report to *output_path*.

    Returns the resolved output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    parts: List[str] = []
    parts.append(_html_head(timestamp, model_name))
    parts.append(_system_prompt_section(system_prompt))

    for doc in results:
        parts.append(_document_section(doc))

    parts.append("</div></body></html>")

    output_path.write_text("\n".join(parts), encoding="utf-8")
    logger.info("HTML report written to %s", output_path)
    return output_path


# ── HTML building helpers ────────────────────────────────────────────────


def _html_head(timestamp: str, model_name: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OCR Test Report</title>
<style>
  :root {{ --bg: #0d1117; --card: #161b22; --border: #30363d; --text: #c9d1d9;
           --heading: #e6edf3; --accent: #58a6ff; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
          background: var(--bg); color: var(--text); line-height: 1.5; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
  header {{ margin-bottom: 32px; }}
  header h1 {{ color: var(--heading); font-size: 1.75rem; margin-bottom: 4px; }}
  header .meta {{ font-size: 0.85rem; color: #8b949e; }}
  .prompt-block {{ background: #0d1117; border: 1px solid var(--border);
                   border-radius: 6px; padding: 16px; margin-bottom: 32px;
                   overflow-x: auto; }}
  .prompt-block h2 {{ color: var(--accent); font-size: 1rem; margin-bottom: 8px; }}
  .prompt-block pre {{ white-space: pre-wrap; font-size: 0.82rem; color: #8b949e; }}
  .doc-card {{ background: var(--card); border: 1px solid var(--border);
               border-radius: 8px; margin-bottom: 32px; overflow: hidden; }}
  .doc-header {{ padding: 16px 20px; border-bottom: 1px solid var(--border);
                 display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
  .doc-header h2 {{ color: var(--heading); font-size: 1.15rem; }}
  .metric {{ font-size: 0.85rem; font-weight: 600; padding: 2px 10px;
             border-radius: 12px; background: #21262d; }}
  .page-grid {{ display: grid; grid-template-columns: 1fr 1fr; }}
  .page-grid .col-label {{ font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
                           letter-spacing: 0.05em; color: #8b949e; padding: 8px 16px;
                           border-bottom: 1px solid var(--border); }}
  .page-grid .col-label:first-child {{ border-right: 1px solid var(--border); }}
  .page-img {{ padding: 12px; border-right: 1px solid var(--border);
               display: flex; justify-content: center; align-items: flex-start;
               background: #0d1117; }}
  .page-img img {{ max-width: 100%; height: auto; border-radius: 4px; }}
  .page-text {{ padding: 12px 16px; overflow: auto; max-height: 800px; }}
  .page-text pre {{ white-space: pre-wrap; word-break: break-word;
                    font-size: 0.82rem; line-height: 1.6; }}
  .page-divider {{ grid-column: 1 / -1; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">
<header>
  <h1>OCR Test Report</h1>
  <div class="meta">{html_mod.escape(timestamp)}{(' &middot; ' + html_mod.escape(model_name)) if model_name else ''}</div>
</header>"""


def _system_prompt_section(system_prompt: str) -> str:
    return f"""\
<div class="prompt-block">
  <h2>System Prompt</h2>
  <pre>{html_mod.escape(system_prompt)}</pre>
</div>"""


def _document_section(doc: DocumentResult) -> str:
    cer = doc.metrics.get("character_error_rate")
    wer = doc.metrics.get("word_error_rate")

    header = f"""\
<div class="doc-card">
  <div class="doc-header">
    <h2>{html_mod.escape(doc.name)}</h2>
    <span class="metric" style="color:{_metric_color(cer)}">CER {_fmt_metric(cer)}</span>
    <span class="metric" style="color:{_metric_color(wer)}">WER {_fmt_metric(wer)}</span>
  </div>"""

    pages: List[str] = []
    for i, (img, text) in enumerate(zip(doc.page_images, doc.page_texts)):
        data_uri = _image_to_base64(img)
        page_num = i + 1
        if i > 0:
            pages.append('<div class="page-divider"></div>')
        pages.append(f"""\
  <div class="page-grid">
    <div class="col-label">Page {page_num} — PDF Image</div>
    <div class="col-label">Page {page_num} — OCR Output</div>
    <div class="page-img"><img src="{data_uri}" alt="Page {page_num}"></div>
    <div class="page-text"><pre>{html_mod.escape(text)}</pre></div>
  </div>""")

    return header + "\n".join(pages) + "\n</div>"
