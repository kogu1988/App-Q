"""Adversarial denetim REJECT etse bile kullanılabilir bir rapor üretilmeli.

Önceden max döngü sonunda `final_report` "Reddedilen Rapor (Revizyon Gerekiyor)"
placeholder'ına düşüyordu → async çalışma kullanıcıya boş çıktı veriyordu.
"""
from __future__ import annotations

import asyncio

from packages.research_engine.nodes import synthesis as syn


class _FakePro:
    def __init__(self, decision: str) -> None:
        self._decision = decision

    def generate(self, system: str, prompt: str, response_format=None, max_tokens=None) -> str:
        return self._decision


def _state():
    return {
        "extracted_themes": [
            {
                "title": "Fiyat hassasiyeti",
                "prevalence": 50.0,
                "evidence_chain": [{"quote": "Aylık 300 lira yüksek", "persona_id": "p1"}],
            }
        ],
        "adversarial_loops_count": 0,
    }


def _run(monkeypatch, decision: str) -> dict:
    monkeypatch.setattr(syn, "get_model_provider", lambda *a, **k: _FakePro(decision))
    monkeypatch.setattr(syn, "publish_live_status", lambda *a, **k: None)
    return asyncio.run(syn.adversarial_quality_audit_node(_state()))


def test_rejected_audit_still_emits_usable_report(monkeypatch):
    out = _run(monkeypatch, "REJECT")

    assert out["is_rejected"] is True
    assert "Fiyat hassasiyeti" in out["final_report"]
    assert "Revizyon Gerekiyor" not in out["final_report"]
    assert "saha doğrulaması" in out["final_report"]


def test_approved_audit_emits_report_without_warning(monkeypatch):
    out = _run(monkeypatch, "APPROVE")

    assert out["is_rejected"] is False
    assert "Fiyat hassasiyeti" in out["final_report"]
    assert "saha doğrulaması" not in out["final_report"]
