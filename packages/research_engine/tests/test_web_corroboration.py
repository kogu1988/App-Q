"""GRUP 9 — Web Corroboration dayanıklılık ve güvenilirlik testleri.

Korunan değerler:
1. Dayanıklılık: SearXNG kapalıyken rapor üretimi **çökmemeli**.
2. Güvenilirlik: Arama sonuç vermezse **uydurma kaynak üretilmemeli**;
   boş liste + metodolojik uyarı dönmeli.
3. Metadata: Gerçek sonuçlarda domain ve doğrulama işareti dolu olmalı.
"""
from __future__ import annotations

import pytest

from packages.research_engine.analytics import corroborate_findings
from packages.research_engine.tests.helpers import make_finding

VALID_RELEVANCE = {"high", "medium", "low"}

# Uydurma kurum/kaynak adları rapora ASLA girmemeli
FABRICATED_MARKERS = ("TÜAD", "Statista", "Deloitte", "TÜBİSAD", "McKinsey")


@pytest.fixture()
def search_disabled(monkeypatch):
    """SearXNG erişilemez senaryosu."""
    import packages.research_engine.search as search_module

    monkeypatch.setattr(search_module, "search_retriever", None, raising=False)
    return search_module


@pytest.fixture()
def search_with_results(monkeypatch):
    """Kontrollü sonuç döndüren sahte retriever."""
    import packages.research_engine.search as search_module

    class _FakeRetriever:
        def search(self, query: str, limit: int = 5):
            return [
                {
                    "title": f"Kaynak {i}",
                    "url": f"https://example{i}.com/makale",
                    "content": "fiyatlandırma kullanıcı pazar araştırması önemli",
                }
                for i in range(1, 6)
            ]

    monkeypatch.setattr(search_module, "search_retriever", _FakeRetriever(), raising=False)
    return search_module


def _findings(count: int = 2):
    return [
        make_finding(title=f"Bulgu {i}", summary=f"Özet {i}", category="pricing")
        for i in range(count)
    ]


def test_9_1_does_not_crash_when_search_unavailable(search_disabled):
    """Arama motoru yoksa bile fonksiyon çökmemeli ve liste dönmeli."""
    result = corroborate_findings(_findings(), "Test Araştırması", "pricing")

    assert isinstance(result, list)


def test_9_2_no_fabricated_sources_when_search_unavailable(search_disabled):
    """Arama yoksa uydurma kurum/sayı içeren kanıt ÜRETİLMEMELİ."""
    result = corroborate_findings(_findings(), "Test Araştırması", "pricing")

    assert result == [], "Arama yokken dış kanıt üretilmemeli"
    blob = " ".join(f"{i.source_title} {i.snippet} {i.source_url}" for i in result)
    assert not any(marker in blob for marker in FABRICATED_MARKERS), blob[:300]


def test_9_3_degrades_with_note_when_search_unavailable(search_disabled):
    """Arama yoksa rapora metodolojik uyarı düşülmeli."""
    notes: list[str] = []
    corroborate_findings(_findings(), "Test Araştırması", "pricing", degradation_notes=notes)

    assert notes, "Degradasyon notu eklenmeli"
    assert any("Harici kanıt" in n for n in notes)


def test_9_4_at_most_three_sources_per_finding(search_with_results):
    """Her bulgu için en fazla 3 kaynak dönmeli."""
    result = corroborate_findings(_findings(2), "Test Araştırması", "pricing")

    per_finding: dict[str, int] = {}
    for item in result:
        per_finding[item.finding_title] = per_finding.get(item.finding_title, 0) + 1

    assert per_finding, "Sonuç bekleniyordu"
    for title, count in per_finding.items():
        assert count <= 3, f"{title}: {count} kaynak"


def test_9_5_relevance_is_within_enum(search_with_results):
    """Relevance değeri high/medium/low olmalı."""
    result = corroborate_findings(_findings(2), "Test Araştırması", "pricing")

    assert result, "Sonuç bekleniyordu"
    for item in result:
        assert item.relevance in VALID_RELEVANCE, item.relevance


def test_9_6_confidence_boost_is_bounded(search_with_results):
    """Güven artışı 0.0–0.15 aralığında kalmalı (aşırı iyimserlik engeli)."""
    result = corroborate_findings(_findings(2), "Test Araştırması", "pricing")

    assert result, "Sonuç bekleniyordu"
    for item in result:
        assert 0.0 <= item.confidence_boost <= 0.15, item.confidence_boost


def test_9_7_real_sources_carry_metadata(search_with_results):
    """Gerçek sonuçlarda domain dolu ve doğrulanmış işaretli olmalı."""
    result = corroborate_findings(_findings(1), "Test Araştırması", "pricing")

    assert result, "Sonuç bekleniyordu"
    for item in result:
        assert item.source_domain, "Kaynak domain boş olmamalı"
        assert item.is_verified is True


def test_9_8_empty_findings_is_safe(search_disabled):
    """Boş bulgu listesi boş liste döndürmeli."""
    assert corroborate_findings([], "Test Araştırması", "pricing") == []
