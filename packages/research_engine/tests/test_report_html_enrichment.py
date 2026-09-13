"""HTML/PDF export, rapor zenginleştirme bölümlerini (Yönetici Anlatımı +
Stratejik Öneriler) içermeli."""
from __future__ import annotations

from packages.research_engine.reporting import render_report_html


def test_html_includes_narrative_and_strategic_recommendations():
    report_json = {
        "executive_summary": ["Kısa özet maddesi."],
        "executive_narrative": "Kanıta bağlı yönetici anlatımı metni.",
        "strategic_recommendations": ["Öneri bir", "Öneri iki"],
    }

    html = render_report_html(report_json, "# Markdown")

    assert "Kanıta bağlı yönetici anlatımı metni." in html
    assert "Stratejik Öneriler" in html
    assert "Öneri bir" in html
    assert "Öneri iki" in html


def test_html_omits_blocks_when_enrichment_absent():
    html = render_report_html({"executive_summary": ["özet"]}, "# md")

    assert "Stratejik Öneriler" not in html


def test_html_renders_degradation_notes():
    html = render_report_html(
        {"degradation_notes": ["Harici kanıt doğrulaması yapılamadı"]}, "# md"
    )

    assert "Metodolojik Uyarılar" in html
    assert "Harici kanıt doğrulaması yapılamadı" in html
