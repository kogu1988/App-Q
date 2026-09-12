"""Production hazırlığı testleri — KVKK, e-posta servisi, Paddle iptali.

Bu testler gerçek DB/LLM/ağ çağrısı YAPMAZ; yalnızca env-gated davranış ve
girdi doğrulaması kontrol edilir.
"""
from __future__ import annotations

import pytest


# ── KVKK: hesap silme onayı ──

def test_delete_confirmation_rejects_empty():
    from fastapi import HTTPException

    from apps.backend.routers.client import _require_delete_confirmation

    with pytest.raises(HTTPException) as exc:
        _require_delete_confirmation("")
    assert exc.value.status_code == 400


def test_delete_confirmation_rejects_wrong_value():
    from fastapi import HTTPException

    from apps.backend.routers.client import _require_delete_confirmation

    for value in ["sil", "yes", "confirm", "DELETE ME", "DELETE!"]:
        with pytest.raises(HTTPException):
            _require_delete_confirmation(value)


def test_delete_confirmation_accepts_token_case_insensitively():
    from apps.backend.routers.client import _require_delete_confirmation

    assert _require_delete_confirmation("DELETE") is None
    assert _require_delete_confirmation("delete") is None
    assert _require_delete_confirmation("  Delete  ") is None


# ── E-posta servisi (Resend) — env yoksa fail-safe ──

def test_email_service_disabled_without_key(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)

    from packages.research_engine import email_service

    assert email_service.is_configured() is False
    assert email_service.send_email("a@example.com", "Konu", "<p>gövde</p>") is False
    assert email_service.notify_contact_form("Ali", "ali@example.com", "Merhaba") is False


def test_email_service_configured_flag(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")

    from packages.research_engine.email_service import is_configured

    assert is_configured() is True


# ── Paddle abonelik iptali — anahtar yoksa güvenli ──

def test_paddle_cancel_without_key_is_safe(monkeypatch):
    monkeypatch.delenv("PADDLE_API_KEY", raising=False)

    from packages.research_engine.paddle_webhooks import cancel_paddle_subscription

    assert cancel_paddle_subscription("") is False
    assert cancel_paddle_subscription("sub_01abc") is False


# ── P0-1 Aşama 2: async araştırma job'ı ──

def test_build_brief_prefers_intake_brief():
    from packages.research_engine.research_runner import build_brief

    brief = build_brief(
        {
            "title": "Payload Başlık",
            "category": "genel",
            "context": "payload context",
            "intake_brief": {
                "title": "Defne Başlık",
                "context": "defne context",
                "target_users": ["kobi"],
            },
        }
    )
    assert brief.title == "Defne Başlık"
    assert brief.idea == "defne context"
    assert brief.target_users == ["kobi"]


def test_build_brief_falls_back_to_payload():
    from packages.research_engine.research_runner import build_brief

    brief = build_brief({"title": "T", "context": "C", "category": "x"})
    assert brief.title == "T"
    assert brief.idea == "C"
    assert brief.target_users == []


def test_research_job_task_is_registered():
    from packages.research_engine.jobs import run_research_job

    assert run_research_job.name == "clarere.run_research_job"
