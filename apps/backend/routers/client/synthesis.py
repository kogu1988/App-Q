"""Sentez raporu endpoint'i ve uygulamasi (R6-2)."""
import json
import logging
import os
from dataclasses import asdict
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from packages.research_engine.analytics import synthesize_report
from packages.research_engine.database import (
    archive_study,
    atomic_increment_simulation_count,
    check_simulation_limit,
    check_token_budget,
    count_chat_messages,
    count_user_non_ab_simulations,
    create_research_job,
    delete_study,
    delete_user_data,
    export_user_data,
    get_client_by_username,
    get_current_username,
    get_finding_detail,
    get_findings,
    get_research_job,
    list_studies,
    load_study_payload,
    record_token_usage,
    register_client_if_new,
    save_feedback,
    save_findings,
    save_study,
    upgrade_client_plan,
)
from packages.research_engine.db_vectors import get_personas_pool, save_persona_to_pool
from packages.research_engine.intake import process_intake_chat
from packages.research_engine.plan_config import (
    get_max_personas,
    get_min_plan_for_feature,
    get_plan_config,
    has_feature,
)
from packages.research_engine.privacy import PrivacyMasker, PrivacyResearchModelWrapper
from packages.research_engine.providers import get_model_provider
from packages.research_engine.workflow import (
    build_research_plan,
    generate_personas,
    run_interviews_batch,
    run_interviews_stream,
)

from ._deps import (
    _DELETE_CONFIRM_TOKEN,
    FollowUpRequest,
    _build_persona_tolerant,
    _effective_plan,
    _enforce_token_budget,
    _record_usage,
    _require_delete_confirmation,
    _require_feature,
    _resolve_plan,
    is_trial_expired,
    limiter,
    logger,
)
from ._schemas import (
    BriefRequest,
    FeedbackCreate,
    GeneratePersonasRequest,
    IntakeChatRequest,
    PersonaCreate,
    PersonaSearch,
    RegisterRequest,
    ResearchRequest,
    StudioSimulationRequest,
    StudyPayload,
    SynthesizeRequest,
    UpgradePlanRequest,
)

router = APIRouter()

@router.post("/synthesize")
def synthesize(request: SynthesizeRequest, x_username: str | None = Depends(get_current_username)):
    try:
        return _synthesize_impl(request, x_username)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("synthesize hata: %s", e, exc_info=True)
        raise HTTPException(status_code=422, detail=f"Sentez verisi eksik veya hatalı: {str(e)[:200]}")


def _synthesize_impl(request, x_username: str | None):
    from packages.research_engine.models import (
        ClarifyingQuestion,
        InterviewTurn,
        Persona,
        PersonaInterview,
        ResearchBrief,
        ResearchPlan,
    )

    plan_type, _ = _resolve_plan(x_username)

    # B2B modu Pro+ gerektirir
    if request.brief.get("b2b_mode"):
        _require_feature(plan_type, "b2b_mode")

    # brief → ResearchBrief (eksik alanlara varsayılan)
    bd = request.brief
    r_brief = ResearchBrief(
        title=bd.get("title") or "Araştırma",
        market=bd.get("market") or "Türkiye",
        category=bd.get("category") or "Genel",
        idea=bd.get("context") or bd.get("idea") or "",
        target_users=bd.get("target_users") or [],
        questions=bd.get("questions") or [],
        competitors=bd.get("competitors") or [],
        expected_price=bd.get("expected_price"),
        sales_channel=bd.get("sales_channel"),
        success_metric=bd.get("success_metric"),
        variant_a=bd.get("variant_a"),
        variant_b=bd.get("variant_b"),
        respondent_types=bd.get("respondent_types") or [],
        discovery_channels=bd.get("discovery_channels") or [],
    )

    # plan → ResearchPlan (eksik alanlara varsayılan)
    pd = request.plan or {}
    r_plan = ResearchPlan(
        objective=pd.get("objective") or f"{r_brief.title} fikrinin pazar potansiyelini test etmek",
        assumptions=pd.get("assumptions") or [],
        clarifying_questions=[
            ClarifyingQuestion(id=cq.get("id", f"cq_{i}"), question=cq.get("question", ""), reason=cq.get("reason", ""), priority=cq.get("priority", "medium"))
            for i, cq in enumerate(pd.get("clarifying_questions") or [])
        ],
        interview_questions=pd.get("interview_questions") or [],
        recommended_panel_size=pd.get("recommended_panel_size") or len(request.interviews) or 5,
        interview_script=[],
        ses_quota=pd.get("ses_quota") or {},
    )

    # PersonaInterview icindeki nested dict'leri dogru objelere cevir (eksik alanlara varsayılan)
    raw_interviews = []
    for i in request.interviews:
        raw_turns = i.get("turns", [])
        turns = []
        for t in raw_turns:
            turns.append(InterviewTurn(
                question=t.get("question", ""),
                answer=t.get("answer", ""),
                tags=t.get("tags") or [],
                model_id=t.get("model_id"),
                quality_flags=t.get("quality_flags") or [],
                is_probe=bool(t.get("is_probe", False)),
            ))
        raw_persona = i.get("persona", {})
        if isinstance(raw_persona, dict):
            persona = _build_persona_tolerant(raw_persona)
        else:
            persona = raw_persona
        pi = PersonaInterview(
            persona=persona,
            turns=turns,
            consistency_notes=i.get("consistency_notes", []),
        )
        raw_interviews.append(pi)
    p_interviews = raw_interviews

    # personas listesi varsa ilet (van_westendorp ve brand_health için gerekli)
    personas_raw = getattr(request, "personas", None) or []
    r_personas = [_build_persona_tolerant(p) for p in personas_raw] if personas_raw else [
        iv.persona for iv in p_interviews
    ]

    report = synthesize_report(
        brief=r_brief,
        plan=r_plan,
        personas=r_personas,
        interviews=p_interviews,
    )

    # ── Plan gate (gelir koruması) ──
    # brand_health (Pro+) ve SES cross-tab (Flex+) ücretli analizlerdir;
    # plan yetersizse rapor çıktısından çıkarılır (markdown ve JSON dahil).
    from dataclasses import replace as _dc_replace

    gated: dict = {}
    if not has_feature(plan_type, "brand_health"):
        gated["brand_health"] = None
    if not has_feature(plan_type, "ses_crosstab"):
        gated["ses_cross_tab"] = []
    if gated:
        report = _dc_replace(report, **gated)

    # ── Rapor zenginleştirme (DeepSeek Pro, kanıta bağlı anlatım) ──
    # Algoritmik raporu, YALNIZCA mevcut bulgular/kanıtlar üzerinden yazılmış
    # yönetici anlatımı + stratejik önerilerle zenginleştirir. Hata/eksiklikte
    # rapor olduğu gibi kalır (graceful degradation).
    if os.getenv("REPORT_ENRICH_ENABLED", "true").lower() in {"1", "true", "yes"}:
        try:
            from packages.research_engine.analytics import enrich_report_narrative
            _enrich_model = get_model_provider("pro", user_id=(x_username or "").strip() or "anonymous", effort="max")
            _narrative, _recs = enrich_report_narrative(report, _enrich_model)
            if _narrative:
                report = _dc_replace(
                    report,
                    executive_narrative=_narrative,
                    strategic_recommendations=_recs,
                )
        except Exception as e:
            logger.warning("Rapor zenginleştirme atlandı: %s", e)

    from dataclasses import asdict
    report_dict = asdict(report)

    # Tam markdown raporu üret (PDF/HTML export + frontend gösterimi için)
    try:
        from packages.research_engine.reporting import render_markdown
        report_dict["report_markdown"] = render_markdown(report)
    except Exception as e:
        logger.warning(f"report_markdown üretilemedi: {e}")
        report_dict["report_markdown"] = "\n".join(f"- {i}" for i in report.executive_summary)

    # ── P3-1: Kalite skoru (rapor oluşturulunca hesapla ve kalıcılaştır) ──
    # Frontend bunu study metadata'sına yazar; aksi halde listede 0/N-A kalıyordu.
    try:
        from packages.research_engine.quality import compute_research_quality

        _q = compute_research_quality(report_dict)
        report_dict["quality_score"] = int(_q.get("overall_score", 0))
        report_dict["quality_grade"] = {
            "green": "A", "yellow": "B", "red": "C",
        }.get(str(_q.get("grade", "")), "B")
    except Exception as e:
        logger.warning(f"Kalite skoru hesaplanamadı: {e}")

    # ── HTML raporu (PDF/export + web gösterimi) ──
    try:
        from packages.research_engine.reporting import render_report_html

        report_dict["report_html"] = render_report_html(
            report_dict, report_dict.get("report_markdown", "")
        )
    except Exception as e:
        logger.warning(f"report_html üretilemedi: {e}")

    # Sprint 3 — Ürün KPI event'i
    try:
        from packages.research_engine.database import record_product_event

        _sid = ""
        try:
            _meta = getattr(request, "metadata", None) or {}
            _sid = str(_meta.get("id", "") or "")
        except Exception:
            _sid = ""
        record_product_event("report_synthesized", username=x_username, study_id=_sid)
    except Exception:
        logger.debug("report_synthesized event'i kaydedilemedi.", exc_info=True)

    return report_dict
