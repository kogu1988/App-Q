"""Araştırma yürütücüsünün ortak çekirdeği.

Hem senkron `/research` endpoint'i hem Celery job'ı bu fonksiyonu kullanır —
böylece davranış tek yerde tanımlı kalır (P0-1 Aşama 2).
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Callable

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int], None] | None


def _report_progress(on_progress: ProgressCallback, value: int) -> None:
    if not on_progress:
        return
    try:
        on_progress(value)
    except Exception:
        logger.debug("İlerleme bildirimi başarısız (%%%s)", value, exc_info=True)


def build_brief(payload: dict):
    """İstek payload'ından (intake_brief öncelikli) ResearchBrief kurar."""
    from .models import ResearchBrief

    brief_data = payload.get("intake_brief") or {}
    return ResearchBrief(
        title=brief_data.get("title") or payload.get("title") or "Araştırma",
        market="Türkiye",
        category=payload.get("category") or "genel",
        idea=brief_data.get("context") or brief_data.get("idea") or payload.get("context") or "",
        target_users=brief_data.get("target_users") or payload.get("target_users") or [],
        questions=brief_data.get("questions") or payload.get("questions") or [],
        competitors=brief_data.get("competitors") or payload.get("competitors") or [],
        expected_price=brief_data.get("expected_price") or payload.get("expected_price"),
        sales_channel=brief_data.get("sales_channel") or payload.get("sales_channel"),
        success_metric=brief_data.get("success_metric") or payload.get("success_metric"),
        respondent_types=brief_data.get("respondent_types") or payload.get("respondent_types") or [],
        discovery_channels=brief_data.get("discovery_channels") or payload.get("discovery_channels") or [],
    )


def execute_research(
    payload: dict,
    username: str,
    plan_type: str,
    on_progress: ProgressCallback = None,
) -> dict:
    """Plan + persona + batch mülakat akışını çalıştırır ve serileştirilmiş sonuç döner.

    Yan etkiler: persona havuzuna kayıt, token muhasebesi, atomik kota artışı.
    """
    from .db_vectors import save_persona_to_pool
    from .plan_config import get_max_personas
    from .providers import get_model_provider
    from .workflow import build_research_plan, generate_personas, run_interviews_batch

    _report_progress(on_progress, 5)
    brief = build_brief(payload)
    model = get_model_provider("flash", user_id=username or "", effort="high")

    # 1) Plan
    plan = build_research_plan(brief)
    _report_progress(on_progress, 15)

    # 2) Persona
    personas = generate_personas(brief)
    personas = personas[: get_max_personas(plan_type)]
    _report_progress(on_progress, 30)

    # 3) Batch mülakat
    interviews = run_interviews_batch(brief, personas, model, plan.interview_script)
    _report_progress(on_progress, 85)

    # 4) Token muhasebesi (fail-safe)
    try:
        from .database import record_token_usage

        record_token_usage(
            username=username or "",
            model_id=getattr(model, "model_id", "") or "",
            operation="interview",
            usage=getattr(model, "cumulative_usage", None) or getattr(model, "last_usage", None) or {},
        )
    except Exception:
        logger.debug("Token kullanımı kaydedilemedi.", exc_info=True)

    # 5) Personaları havuza kaydet (tekrar kullanım için) — kritik değil
    for persona in personas:
        try:
            persona_dict = asdict(persona)
            persona_dict["created_by"] = username or "anonymous"
            persona_dict["is_global"] = True
            save_persona_to_pool(persona_dict, embedding=None)
        except Exception:
            logger.debug("Persona havuza kaydedilemedi.", exc_info=True)

    # 6) Atomik kota artırma
    if username:
        try:
            from .database import atomic_increment_simulation_count

            atomic_increment_simulation_count(username)
        except Exception:
            logger.warning("Simülasyon sayacı artırılamadı (user=%s)", username, exc_info=True)

    _report_progress(on_progress, 95)
    return {
        "plan": asdict(plan),
        "personas": [asdict(p) for p in personas],
        "interviews": [asdict(iv) for iv in interviews],
    }
