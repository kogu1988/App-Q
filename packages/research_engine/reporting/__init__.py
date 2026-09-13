"""Rapor render katmani (refactor R7-9).

Eski reporting.py dosyasi markdown/html olarak ayrildi; import yollari
degismesin diye isimler buradan yeniden disa verilir.
"""
from ._html_utils import count_by, html_list, html_table
from .html import render_report_html
from .markdown import (
    _SENTENCE_SPLIT_RE,
    _clip,
    _g,
    render_markdown,
    suggest_follow_up_question,
)
