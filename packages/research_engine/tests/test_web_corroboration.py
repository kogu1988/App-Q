"""GRUP 9 — Web Corroboration Graceful Degradation testleri.

Korunan değer: Dayanıklılık. SearXNG kapalıyken rapor üretimi **çökmemeli**;
mock referanslara düşerek devam etmeli.
"""
from __future__ import annotations

import pytest

from packages.research_engine.analytics import corroborate_findings
from packages.research_engine.tests.helpers import make_finding

VALID_RELEVANCE = {"high", "medium", "low"}


@pytest.fixture()
def search_disabled(monkeypatch):
    """SearXNG erişilemez senaryosu — fallback (mock) yolunu zorlar."""
    import packages.research_engine.search as search_module

    monkeypatch.setattr(search_module, "search_retriever", None, raising=False)
    return search_module


def _findings(count: int = 2):
    return [
        make_finding(title=f"Bulgu {i}", summary=f"Özet {i}", category="pricing")
        for i in range(count)
    ]


def test_9_1_falls_back_when_search_unavailable(search_disabled):
    """Arama motoru yoksa bile liste dönmeli (çökme yok)."""
    result = corroborate_findings(_findings(), "Test Araştırması", "pricing")

    assert isinstance(result, list)


def test_9_2_fallback_sources_are_reference_labeled(search_disabled):
    """Fallback kaynakları tanınmış referans kurumlarla etiketlenmeli."""
    result = corroborate_findings(_findings(1), "Test Araştırması", "pricing")

    if not result:
        pytest.skip("Fallback kaynağı üretilmedi")

    blob = " ".join(
        f"{item.source_title} {item.snippet} {item.source_url}" for item in result
    )
    assert any(marker in blob for marker in ("TÜAD", "TUIK", "TÜİK", "Statista")), blob[:300]


def test_9_3_at_most_three_sources_per_finding(search_disabled):
    """Her bulgu için en fazla 3 kaynak dönmeli."""
    findings = _findings(2)
    result = corroborate_findings(findings, "Test Araştırması", "pricing")

    per_finding: dict[str, int] = {}
    for item in result:
        per_finding[item.finding_title] = per_finding.get(item.finding_title, 0) + 1

    for title, count in per_finding.items():
        assert count <= 3, f"{title}: {count} kaynak"


def test_9_4_relevance_is_within_enum(search_disabled):
    """Relevance değeri high/medium/low olmalı."""
    result = corroborate_findings(_findings(2), "Test Araştırması", "pricing")

    for item in result:
        assert item.relevance in VALID_RELEVANCE, item.relevance


def test_9_5_confidence_boost_is_bounded(search_disabled):
    """Güven artışı 0.0–0.15 aralığında kalmalı (aşırı iyimserlik engeli)."""
    result = corroborate_findings(_findings(2), "Test Araştırması", "pricing")

    for item in result:
        assert 0.0 <= item.confidence_boost <= 0.15, item.confidence_boost


def test_9_6_empty_findings_is_safe(search_disabled):
    """Boş bulgu listesi boş liste döndürmeli."""
    assert corroborate_findings([], "Test Araştırması", "pricing") == []
