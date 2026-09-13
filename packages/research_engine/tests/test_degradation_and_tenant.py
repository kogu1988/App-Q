"""Regresyon testleri: Celery'de RLS tenant bağlamı + sessiz degradasyon sinyali."""
from __future__ import annotations

import packages.research_engine.search as search_mod
from packages.research_engine import analytics, gateway
from packages.research_engine.database import get_current_username
from packages.research_engine.models import Finding


# ── 1) Celery'de tenant bağlamı (async çalışma görünürlüğü) ──

def test_bind_tenant_context_sets_username():
    gateway.bind_tenant_context("pro")
    assert get_current_username() == "pro"


def test_bind_tenant_context_handles_none():
    gateway.bind_tenant_context(None)
    assert get_current_username() == ""


# ── 2) Harici kanıt doğrulaması yapılamazsa degradasyon notu ──

def _finding() -> Finding:
    return Finding(
        title="Fiyat hassasiyeti",
        category="pricing",
        summary="Kullanıcılar fiyata duyarlı",
        confidence=0.6,
        evidence=[],
        implication="Fiyat esnekliği sağlanmalı.",
    )


def test_degradation_note_added_when_search_unavailable(monkeypatch):
    # SearXNG yok → uydurma kaynak ÜRETİLMEZ; boş sonuç + metodolojik uyarı dönmeli.
    monkeypatch.setattr(search_mod, "search_retriever", None)

    notes: list[str] = []
    result = analytics.corroborate_findings(
        [_finding()], "Test", "genel", degradation_notes=notes
    )

    assert result == [], "arama yokken dış kanıt üretilmemeli (uydurma yasak)"
    assert any("Harici kanıt" in note for note in notes), notes


def test_no_degradation_note_when_search_works(monkeypatch):
    class _FakeRetriever:
        def search(self, query: str, limit: int = 5):
            return [{"title": "Kaynak", "url": "http://x", "content": "fiyat hassasiyeti yüksek"}]

    monkeypatch.setattr(search_mod, "search_retriever", _FakeRetriever())

    notes: list[str] = []
    analytics.corroborate_findings([_finding()], "Test", "genel", degradation_notes=notes)

    assert notes == []
