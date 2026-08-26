"""PDF generation from markdown research reports.

Uses xhtml2pdf (Pisa) to convert styled HTML into PDF bytes.
No external process or GUI toolkit required — pure Python.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Inline CSS for the PDF ────────────────────────────────────────────────────
from pathlib import Path

# Load CSS stylesheet relative to this file
_CSS_PATH = Path(__file__).parent / "pdf_report.css"

try:
    if _CSS_PATH.exists():
        _CSS = _CSS_PATH.read_text(encoding="utf-8")
    else:
        logger.warning("Central PDF report CSS not found at %s. Falling back to in-memory styles.", _CSS_PATH)
        _CSS = ""
except Exception as e:
    logger.error("Failed to load central PDF CSS stylesheet: %s. Using default.", e)
    _CSS = ""

# In case the file is missing or failed, define fallback styles
if not _CSS:
    _CSS = """
@font-face {
    font-family: "DejaVu Sans";
    src: url("fonts/DejaVuSans.ttf");
}
@font-face {
    font-family: "DejaVu Sans";
    font-weight: bold;
    src: url("fonts/DejaVuSans-Bold.ttf");
}
@font-face {
    font-family: "DejaVu Sans Mono";
    src: url("fonts/DejaVuSansMono.ttf");
}
@page {
    margin: 2cm 2.5cm;
    size: A4;
}

body {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 10pt;
    color: #1a1a2e;
    line-height: 1.6;
}

h1 {
    font-size: 22pt;
    color: #003c33;
    border-bottom: 2px solid #003c33;
    padding-bottom: 6pt;
    margin-top: 24pt;
    margin-bottom: 12pt;
}

h2 {
    font-size: 15pt;
    color: #003c33;
    border-bottom: 1px solid #d0d0d0;
    padding-bottom: 4pt;
    margin-top: 18pt;
    margin-bottom: 8pt;
}

h3 {
    font-size: 12pt;
    color: #1a1a2e;
    margin-top: 12pt;
    margin-bottom: 6pt;
}

p {
    margin: 0 0 8pt 0;
}

ul, ol {
    margin: 4pt 0 8pt 20pt;
    padding: 0;
}

li {
    margin-bottom: 3pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
    font-size: 9pt;
}

th {
    background-color: #003c33;
    color: #ffffff;
    padding: 5pt 8pt;
    text-align: left;
    font-weight: bold;
}

td {
    padding: 4pt 8pt;
    border-bottom: 1px solid #e0e0e0;
}

tr:nth-child(even) td {
    background-color: #f5f5f5;
}

code {
    background-color: #f0f0f0;
    border-radius: 2pt;
    padding: 1pt 3pt;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 8.5pt;
}

pre {
    background-color: #f0f0f0;
    border-left: 3pt solid #003c33;
    padding: 8pt;
    margin: 8pt 0;
}

blockquote {
    border-left: 3pt solid #ff7759;
    margin: 8pt 0;
    padding: 4pt 12pt;
    background-color: #fffaf8;
    color: #555555;
}

.report-header {
    background-color: #003c33;
    color: #ffffff;
    padding: 20pt 24pt;
    margin-bottom: 24pt;
}

.report-header-title {
    font-size: 20pt;
    font-weight: bold;
    color: #ffffff;
    margin: 0 0 6pt 0;
}

.report-header-sub {
    color: #cccccc;
    font-size: 9pt;
    margin: 0;
}
"""


# ── Türkçe karakterleri destekleyen Unicode font (DejaVu) kaydı ─────────────
import os

_FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _link_callback(uri: str, rel: str) -> str:
    """CSS @font-face src URL'lerini konteyner içindeki TTF dosyalarına çevirir."""
    if uri.startswith("fonts/"):
        path = os.path.join(_FONT_DIR, os.path.basename(uri))
        if os.path.exists(path):
            return path
    return uri


def horizontal_bar_chart(title: str, items: list[tuple[str, int]], color: str = "#003c33") -> str:
    """Pillow ile basit yatay bar grafiği üretir; base64 PNG döndürür (PDF'e gömülür)."""
    import base64 as _b64
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return ""

    _font_path = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
    try:
        _font_title = ImageFont.truetype(_font_path, 18)
        _font_label = ImageFont.truetype(_font_path, 14)
    except Exception:
        _font_title = _font_label = ImageFont.load_default()

    _width, _bar_h, _gap = 720, 26, 10
    _height = 70 + len(items) * (_bar_h + _gap)
    _img = Image.new("RGB", (_width, _height), "#ffffff")
    _d = ImageDraw.Draw(_img)
    _d.text((24, 14), title, fill="#17171c", font=_font_title)

    _max_v = max((v for _, v in items), default=1) or 1
    _bar_x = 200
    _bar_max = _width - _bar_x - 70
    _y = 54
    for label, v in items:
        _d.text((24, _y + 5), label, fill="#212121", font=_font_label)
        _w = int(_bar_max * v / _max_v) if v > 0 else 2
        _d.rectangle([_bar_x, _y, _bar_x + _w, _y + _bar_h], fill=color)
        _d.text((_bar_x + _w + 8, _y + 5), str(v), fill="#616161", font=_font_label)
        _y += _bar_h + _gap

    _buf = io.BytesIO()
    _img.save(_buf, format="PNG")
    return _b64.b64encode(_buf.getvalue()).decode("ascii")


def generate_pdf_from_markdown(
    markdown_text: str,
    title: str = "Clarere Research Report",
    study_id: Optional[str] = None,
    brand_name: str = "Clarere",
    charts: Optional[list[tuple[str, str]]] = None,
) -> Optional[bytes]:
    """
    Convert a markdown research report to PDF bytes.

    Args:
        markdown_text: Full markdown content of the report.
        title: Human-readable title shown in the PDF header.
        study_id: Optional study ID shown in the header subtitle.

    Returns:
        PDF as bytes, or None if conversion fails.
    """
    try:
        import markdown as md_lib
        from xhtml2pdf import pisa
    except ImportError:
        logger.error(
            "markdown veya xhtml2pdf kurulu değil. Run: pip install -r requirements.txt"
        )
        return None

    # 1. Markdown → HTML body
    body_html = md_lib.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )

    # 2. Build header block
    subtitle = f"Rapor ID: {study_id}" if study_id else (f"{brand_name} AI Arastirma Platformu" if brand_name else "Pazar Arastirma Raporu")
    header_html = f"""
    <div class="report-header">
        <p class="report-header-title">{title}</p>
        <p class="report-header-sub">{subtitle}</p>
    </div>
    """

    # 2b. Grafik bölümleri (Pillow ile üretilen PNG'ler, base64 olarak gömülür)
    chart_html = ""
    if charts:
        for _cap, _b64 in charts:
            if _b64:
                chart_html += (
                    '<div style="margin: 12pt 0; text-align: center;">'
                    f'<img src="data:image/png;base64,{_b64}" width="480"/>'
                    f'<p style="font-size: 8pt; color: #616161; margin-top: 3pt;">{_cap}</p>'
                    "</div>"
                )

    # 3. Full HTML document
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8"/>
<style>
{_CSS}
</style>
</head>
<body>
{header_html}
{chart_html}
{body_html}
</body>
</html>"""

    # 4. HTML → PDF via xhtml2pdf (Pisa)
    output = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html,
        dest=output,
        encoding="utf-8",
        link_callback=_link_callback,
    )

    if pisa_status.err:
        logger.error("PDF generation failed with pisa errors: %s", pisa_status.err)
        return None

    return output.getvalue()
