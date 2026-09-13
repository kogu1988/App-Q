"""P0 blocker düzeltmeleri için birim testleri.

Kapsam:
  - Paddle webhook imza doğrulaması (P0-2)
  - Paddle price → plan eşlemesi tutarlılığı
  - Token fiyatlandırma hesabı (P0-6)
  - JWT secret production guard (P0-3)
  - Admin API guard (P0-4)
  - LLM kullanım birikimi (P0-6)
  - Süre bütçesi aşımında boş mülakat üretimi (P0-5)

Bu testler gerçek LLM/DB çağrısı YAPMAZ.
"""
from __future__ import annotations

import hashlib
import hmac
import time

import pytest


# ── P0-2: Paddle imza doğrulama ──

def _sign(body: bytes, secret: str, ts: int | None = None) -> str:
    ts = ts if ts is not None else int(time.time())
    digest = hmac.new(secret.encode(), str(ts).encode() + b":" + body, hashlib.sha256).hexdigest()
    return f"ts={ts};h1={digest}"


def test_paddle_signature_valid():
    from packages.research_engine.paddle_webhooks import verify_paddle_signature

    body = b'{"event_type":"subscription.created"}'
    secret = "pdl_ntfset_test"
    assert verify_paddle_signature(body, _sign(body, secret), secret) is True


def test_paddle_signature_tampered_body_rejected():
    from packages.research_engine.paddle_webhooks import verify_paddle_signature

    body = b'{"a":1}'
    secret = "s3cret"
    header = _sign(body, secret)
    assert verify_paddle_signature(b'{"a": 1}', header, secret) is False


def test_paddle_signature_old_timestamp_rejected():
    from packages.research_engine.paddle_webhooks import verify_paddle_signature

    body = b"{}"
    secret = "s3cret"
    old_ts = int(time.time()) - 60
    assert verify_paddle_signature(body, _sign(body, secret, old_ts), secret) is False


def test_paddle_signature_missing_or_empty_rejected():
    from packages.research_engine.paddle_webhooks import verify_paddle_signature

    assert verify_paddle_signature(b"{}", "", "s3cret") is False
    assert verify_paddle_signature(b"{}", "ts=1", "s3cret") is False
    assert verify_paddle_signature(b"{}", "ts=1;h1=abc", "") is False


def test_paddle_signature_malformed_timestamp():
    from packages.research_engine.paddle_webhooks import verify_paddle_signature

    assert verify_paddle_signature(b"{}", "ts=abc;h1=deadbeef", "s3cret") is False


# ── P0-2: price → plan eşlemesi ──

def test_paddle_price_map_matches_plan_config(monkeypatch):
    from packages.research_engine.paddle_config import plan_for_price
    from packages.research_engine.plan_config import PLAN_CONFIG

    monkeypatch.setenv("PADDLE_PRICE_FLEX", "pri_flex")
    monkeypatch.setenv("PADDLE_PRICE_STARTER_MONTHLY", "pri_starter_m")
    monkeypatch.setenv("PADDLE_PRICE_STARTER_ANNUAL", "pri_starter_a")
    monkeypatch.setenv("PADDLE_PRICE_PRO_MONTHLY", "pri_pro_m")
    monkeypatch.setenv("PADDLE_PRICE_PRO_ANNUAL", "pri_pro_a")

    expected = {
        "pri_flex": ("Flex", "one_time"),
        "pri_starter_m": ("Starter", "monthly"),
        "pri_starter_a": ("Starter", "annual"),
        "pri_pro_m": ("Pro", "monthly"),
        "pri_pro_a": ("Pro", "annual"),
    }
    for price_id, mapping in expected.items():
        assert plan_for_price(price_id) == mapping
        # Eşlenen plan adı PLAN_CONFIG ile birebir olmalı
        assert mapping[0] in PLAN_CONFIG


def test_paddle_price_for_plan_roundtrip(monkeypatch):
    from packages.research_engine.paddle_config import price_for_plan

    monkeypatch.setenv("PADDLE_PRICE_PRO_MONTHLY", "pri_x")
    assert price_for_plan("Pro", "monthly") == "pri_x"
    assert price_for_plan("Pro", "annual") is None
    assert price_for_plan("Bilinmeyen", "monthly") is None


# ── P0-6: token fiyatlandırma ──

def test_calculate_cost_uses_cache_hit_discount():
    from packages.research_engine import pricing_table

    pricing_table.MODEL_PRICING["__test_model__"] = {
        "input": 1.0,        # 1 USD / 1M
        "output": 2.0,
        "cache_hit": 0.1,    # indirimli
    }
    # 1M input (hepsi miss) + 1M output
    assert pricing_table.calculate_cost("__test_model__", 1_000_000, 1_000_000) == pytest.approx(3.0)
    # 1M prompt'un 800k'sı cache-hit, 200k miss + 0 output
    cost = pricing_table.calculate_cost(
        "__test_model__", prompt_tokens=1_000_000, completion_tokens=0, cache_hit_tokens=800_000
    )
    assert cost == pytest.approx(0.2 * 1.0 + 0.8 * 0.1)


def test_calculate_cost_unknown_model_is_zero_safe():
    from packages.research_engine.pricing_table import calculate_cost

    assert calculate_cost("bilinmeyen-model", 1_000_000, 1_000_000) == 0.0


def test_active_flash_model_has_pricing_entry():
    """Aktif Flash model adı (deepseek-flash) fiyat tablosunda bulunmalı.

    Regresyon: tablo yalnızca emekli `deepseek-v4-flash` adını taşıyordu → admin
    maliyet paneli Flash çağrıları için $0 gösteriyordu.
    """
    from packages.research_engine.pricing_table import MODEL_PRICING

    assert "deepseek-flash" in MODEL_PRICING
    assert MODEL_PRICING["deepseek-flash"] is MODEL_PRICING["deepseek-v4-flash"]


# ── P0-3: JWT secret guard ──

def test_jwt_secret_production_requires_env(monkeypatch):
    from packages.research_engine.jwt_utils import get_jwt_secret

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("ADMIN_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        get_jwt_secret()


def test_jwt_secret_production_rejects_short_secret(monkeypatch):
    from packages.research_engine.jwt_utils import get_jwt_secret

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "kisa")
    with pytest.raises(RuntimeError):
        get_jwt_secret()


def test_jwt_secret_production_accepts_long_secret(monkeypatch):
    from packages.research_engine.jwt_utils import get_jwt_secret

    secret = "x" * 48
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", secret)
    assert get_jwt_secret() == secret


def test_jwt_secret_dev_fallback_never_used_in_production(monkeypatch):
    from packages.research_engine import jwt_utils

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("ADMIN_SECRET_KEY", raising=False)
    assert jwt_utils.get_jwt_secret() == jwt_utils._DEV_FALLBACK


# ── P0-4: Admin guard ──

class _FakeClient:
    host = "127.0.0.1"


class _FakeRequest:
    client = _FakeClient()


def test_admin_guard_production_without_key_blocks(monkeypatch):
    from fastapi import HTTPException

    from apps.backend.routers.admin import require_admin

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ADMIN_SECRET_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        require_admin(_FakeRequest(), x_admin_key="")
    assert exc.value.status_code == 503


def test_admin_guard_wrong_key_forbidden(monkeypatch):
    from fastapi import HTTPException

    from apps.backend.routers.admin import require_admin

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ADMIN_SECRET_KEY", "correct-key")
    with pytest.raises(HTTPException) as exc:
        require_admin(_FakeRequest(), x_admin_key="wrong-key")
    assert exc.value.status_code == 403


def test_admin_guard_correct_key_allows(monkeypatch):
    from apps.backend.routers.admin import require_admin

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ADMIN_SECRET_KEY", "correct-key")
    assert require_admin(_FakeRequest(), x_admin_key="correct-key") is None


def test_admin_guard_dev_without_key_warns_only(monkeypatch):
    from apps.backend.routers.admin import require_admin

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("ADMIN_SECRET_KEY", raising=False)
    assert require_admin(_FakeRequest(), x_admin_key="") is None


# ── P0-6: LLM kullanım birikimi ──

class _Usage:
    prompt_tokens = 100
    completion_tokens = 50
    total_tokens = 150
    prompt_cache_hit_tokens = 20
    prompt_cache_miss_tokens = 80


class _Resp:
    usage = _Usage()


def test_provider_cumulative_usage_accumulates(monkeypatch):
    from packages.research_engine.providers import DeepSeekResearchModel

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    model = DeepSeekResearchModel(model_id="deepseek-v4-flash")
    model._capture_usage(_Resp())
    model._capture_usage(_Resp())

    assert model.last_usage["total_tokens"] == 150
    assert model.cumulative_usage["total_tokens"] == 300
    assert model.cumulative_usage["prompt_cache_hit_tokens"] == 40


# ── P0-5: süre bütçesi → boş mülakat ──

def test_skipped_interview_marks_unanswered():
    from packages.research_engine.models import (
        InterviewQuestion,
        Persona,
    )
    from packages.research_engine.workflow import _skipped_interview

    persona = Persona(
        id="p1",
        name="Test",
        age=30,
        city="İstanbul",
        segment="genel",
        stance="Mainstream",
        price_sensitivity=5,
        digital_confidence=5,
        context="Test bağlamı",
        goals=[],
        objections=[],
        knowledge_boundary="genel tüketici",
        role_title="Tüketici",
        bio="",
        ses_group="C1",
    )
    script = [
        InterviewQuestion(id="q1", label="PAIN", question="Soru 1?", reason="test"),
        InterviewQuestion(id="q2", label="PRICE", question="Soru 2?", reason="test"),
    ]

    interview = _skipped_interview(persona, script)
    assert len(interview.turns) == 2
    assert all(t.answer == "[Yanıt alınamadı]" for t in interview.turns)
    assert all("timeout" in t.quality_flags for t in interview.turns)


# ── P0-2: abonelik durumu → efektif plan ──

def test_effective_plan_status_mapping():
    from apps.backend.routers.client import _effective_plan

    assert _effective_plan({"plan_type": "Pro", "subscription_status": "active"}) == "Pro"
    assert _effective_plan({"plan_type": "Pro", "subscription_status": "trialing"}) == "Pro"
    # past_due → erişim korunur
    assert _effective_plan({"plan_type": "Pro", "subscription_status": "past_due"}) == "Pro"
    # paused / canceled → Free
    assert _effective_plan({"plan_type": "Pro", "subscription_status": "paused"}) == "Free"
    assert _effective_plan({"plan_type": "Pro", "subscription_status": "canceled"}) == "Free"
    # Abonelik yok (eski kullanıcı) → plan_type korunur
    assert _effective_plan({"plan_type": "Starter"}) == "Starter"
