"""GRUP 5 — Plan Feature Gate Enforcement testleri.

Korunan değer: Gelir koruması. `plan_config.py` SSOT'u doğru olsa bile endpoint
katmanında uygulanmazsa ücretli özellikler bedava dağılır.

Bu test grubu, denetimde bulunan **gelir sızıntısını** (brand_health ve ses_crosstab
hiçbir endpoint'te gate'lenmiyordu) kalıcı olarak engeller.
"""
from __future__ import annotations

import pathlib
import re

import pytest
from fastapi import HTTPException

from apps.backend.routers.client import (
    SynthesizeRequest,
    _require_feature,
    _synthesize_impl,
    research_chat,
)
from packages.research_engine.plan_config import (
    FEATURE_MIN_PLAN,
    PLAN_CONFIG,
    get_plan_config,
    get_max_personas,
)

_ROUTER_FILES = [
    pathlib.Path("apps/backend/routers/client.py"),
    pathlib.Path("apps/backend/routers/admin.py"),
]

# Endpoint katmanında `_require_feature`/`has_feature` ile kapısı olan özellikler
ENFORCED_AT_API = {"streaming", "pdf_export", "ab_test", "b2b_mode", "ses_crosstab", "brand_health"}

# Raporlama katmanında (plan_config.get_brand_name) uygulanan özellik
ENFORCED_ELSEWHERE = {"white_label"}

# Admin API'si X-Admin-Key ile korunuyor → operatör özellikleri ayrıca plan-kapılı değil
ADMIN_PROTECTED = {"custom_personas", "fine_tuning_export", "audit_log", "multi_user"}

# Free planda zaten açık olduğu için kapı gerekmez
FREE_TIER = {"adversarial", "rfi"}


def _source() -> str:
    return "\n".join(f.read_text(encoding="utf-8") for f in _ROUTER_FILES)


def _is_enforced(feature: str) -> bool:
    pattern = re.compile(
        r"(_require_feature|has_feature|get_brand_name)\(\s*[^,)]*,\s*[\"']" + re.escape(feature) + r"[\"']"
    )
    return bool(pattern.search(_source()))


# ── 5.1–5.3 Temel gate davranışı ──

def test_5_1_closed_feature_raises_403():
    """Free planda ücretli özellik 403 üretmeli."""
    with pytest.raises(HTTPException) as exc:
        _require_feature("Free", "pdf_export")
    assert exc.value.status_code == 403


def test_5_2_forbidden_body_carries_plan_gate_code():
    """403 gövdesi PLAN_GATE kodunu ve gerekli planı taşımalı (frontend upgrade CTA)."""
    with pytest.raises(HTTPException) as exc:
        _require_feature("Free", "b2b_mode")

    detail = exc.value.detail
    assert detail["code"] == "PLAN_GATE"
    assert detail["feature"] == "b2b_mode"
    assert detail["required_plan"] == "Pro"
    assert detail["current_plan"] == "Free"


def test_5_3_open_feature_does_not_raise():
    """Plan özelliği içeriyorsa hata fırlatılmamalı."""
    assert _require_feature("Pro", "pdf_export") is None
    assert _require_feature("Enterprise", "brand_health") is None


# ── 5.4 Her ücretli özellik bir katmanda kapılı olmalı ──

def test_5_4_every_paid_feature_is_gated_somewhere():
    """FEATURE_MIN_PLAN'daki her özellik bir katmanda kapılı olmalı; kapısız olan yok."""
    for feature in FEATURE_MIN_PLAN:
        enforced = _is_enforced(feature)
        allowed_elsewhere = (
            feature in ENFORCED_ELSEWHERE or feature in ADMIN_PROTECTED or feature in FREE_TIER
        )
        assert enforced or allowed_elsewhere, (
            f"'{feature}' hiçbir katmanda kapılı değil — gelir sızıntısı riski"
        )


def test_5_5_api_enforced_features_are_actually_gated():
    """API katmanında kapılı olması gereken özellikler gerçekten kapılı olmalı."""
    for feature in ENFORCED_AT_API:
        assert _is_enforced(feature), f"{feature} endpoint katmanında kapılı değil"


def test_5_6_unknown_plan_falls_back_to_free():
    """Bilinmeyen plan adı Free konfigürasyonuna düşmeli (fail-safe)."""
    assert get_plan_config("Hacker") == PLAN_CONFIG["Free"]


def test_5_7_persona_limit_is_defined_and_runner_applies_it():
    """max_personas plan sınırı tanımlı ve araştırma yürütücüsünde uygulanıyor olmalı."""
    assert get_max_personas("Free") == 10
    assert get_max_personas("Enterprise") > get_max_personas("Pro")

    runner = pathlib.Path("packages/research_engine/research_runner.py").read_text(encoding="utf-8")
    assert "get_max_personas(plan_type)" in runner, "persona sınırı runner'da uygulanmıyor"


def test_5_8_copilot_is_blocked_on_free_plan():
    """Research Copilot Free planda 403 dönmeli (DB'ye gitmeden)."""
    with pytest.raises(HTTPException) as exc:
        research_chat("study_x", {"question": "Neden reddettiler?"}, None, None)
    assert exc.value.status_code == 403


# ── 5.9 Ücretli analizler rapordan çıkarılır (gelir sızıntısı regresyonu) ──

def test_5_9_free_report_excludes_paid_analyses():
    """Free planda brand_health ve SES cross-tab rapora dahil edilmemeli."""
    request = SynthesizeRequest(
        interviews=[
            {
                "persona": {"name": "Ali", "stance": "Mainstream"},
                "turns": [{"question": "Q", "answer": "A", "tags": ["pricing"]}],
            }
        ],
        plan={},
        brief={"title": "Test", "context": "Test fikri", "competitors": ["Rakip"]},
    )

    report = _synthesize_impl(request, None)  # x_username=None → Free plan

    assert report["brand_health"] is None
    assert report["ses_cross_tab"] == []


# ── 5.10 Senkron araştırma yolu da kota uygular (gelir sızıntısı regresyonu) ──

def test_5_10_sync_research_enforces_quota():
    """Senkron `/research`, async `/research/jobs` ile AYNI kota kontrolünü yapmalı.

    Regresyon: `execute_research` sayacı yalnızca SONDA artırıyordu; senkron yol
    (async 503 olunca frontend fallback'i) kotayı atlayıp Free kullanıcıya sınırsız
    araştırma izni veriyordu.
    """
    source = pathlib.Path("apps/backend/routers/client.py").read_text(encoding="utf-8")
    idx = source.index("def run_full_research")
    body = source[idx: idx + 2500]

    assert "check_simulation_limit" in body, "senkron /research kota kontrolü içermeli"
    assert "QUOTA_EXCEEDED" in body, "kota aşımı QUOTA_EXCEEDED döndürmeli"
