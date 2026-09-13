"""Plan, persona uretimi, senkron/job arastirma ve mülakat akisi (R6-2)."""
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

@router.post("/plan")
def create_plan(request: BriefRequest, x_username: str | None = Depends(get_current_username)):
    plan_type, _ = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

    if plan_type == "Free" and request.questions:
        raise HTTPException(
            status_code=403,
            detail="Free planda özel mülakat sorusu eklenemez. Lütfen planınızı yükseltin."
        )

    if request.category.lower() in ("ab_test", "a/b test", "ab test"):
        _require_feature(plan_type, "ab_test")

    from packages.research_engine.models import ResearchBrief
    brief = ResearchBrief(
        title=request.title,
        market="Türkiye",
        category=request.category,
        idea=request.context,
        target_users=request.target_users,
        questions=request.questions,
        competitors=request.competitors,
        expected_price=request.expected_price,
        sales_channel=request.sales_channel,
        success_metric=request.success_metric,
        variant_a=request.variant_a,
        variant_b=request.variant_b,
        discovery_channels=request.discovery_channels,
        respondent_types=request.respondent_types,
    )
    from dataclasses import replace

    from packages.research_engine.providers import get_model_provider
    from packages.research_engine.reframing import apply_input_reframing

    plan = build_research_plan(brief)

    # Reframing katmanı ile sübjektif girdileri nesnelleştir (Sycophancy Mitigation)
    try:
        model = get_model_provider("flash", user_id=x_username or "", effort="low")
        reframed = apply_input_reframing(brief, model)

        new_objective = reframed.get("objective_product_context", plan.objective)
        new_questions = reframed.get("primary_research_questions", plan.interview_questions)

        plan = replace(plan, objective=new_objective, interview_questions=new_questions)
    except Exception as e:
        print(f"Reframing katmanı başarısız: {e}")

    return plan

@router.post("/personas/generate")
def generate_personas_from_plan(request: GeneratePersonasRequest, x_username: str | None = Depends(get_current_username)):
    plan_type, _ = _resolve_plan(x_username)
    from packages.research_engine.models import ResearchBrief

    # plan dict'ten sadece objective'yi al (ResearchPlan nested dataclass sorununu önler)
    plan_dict = request.plan
    plan_objective = plan_dict.get("objective") or ""

    # ResearchBrief'i brief dict'ten kur (fallback: plan objective)
    brief_data = request.brief
    brief = ResearchBrief(
        title=brief_data.get("title") or "Araştırma",
        market=brief_data.get("market") or "Türkiye",
        category=brief_data.get("category") or "Genel",
        idea=brief_data.get("context") or brief_data.get("idea") or plan_objective or "",
        target_users=brief_data.get("target_users") or [],
        questions=brief_data.get("questions") or [],
        competitors=brief_data.get("competitors") or [],
        expected_price=brief_data.get("expected_price"),
        sales_channel=brief_data.get("sales_channel"),
        success_metric=brief_data.get("success_metric"),
        respondent_types=brief_data.get("respondent_types") or [],
        discovery_channels=brief_data.get("discovery_channels") or [],
    )

    max_p = get_max_personas(plan_type)
    personas = generate_personas(brief)
    personas = personas[:max_p]
    from dataclasses import asdict
    return {"personas": [asdict(p) for p in personas]}


@router.post("/research")
def run_full_research(request: ResearchRequest, x_username: str | None = Depends(get_current_username)):
    """
    Adım 2 — Birleşik Araştırma (senkron): Plan + Persona + Mülakat.
    Uzun sürebilir (~30-60 sn); production'da `/research/jobs` (async) tercih edilir.
    Model: deepseek-v4-flash (hızlı/ucuz).
    """
    plan_type, _ = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

    _enforce_token_budget(x_username, plan_type)

    # ── Kota kontrolü (async `/research/jobs` ile PARİTE) ──
    # NOT: `execute_research` sayacı yalnızca SONDA artırır; burada önceden kontrol
    # edilmezse senkron yol (async 503 olunca frontend'in fallback'i) kotayı atlar.
    can_run, used, max_s = check_simulation_limit(x_username) if x_username else (True, 0, 0)
    if not can_run:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "QUOTA_EXCEEDED",
                "used": used,
                "limit": max_s,
                "message": f"Aylık araştırma limitine ulaştınız ({used}/{max_s}). Planınızı yükseltin.",
            },
        )

    from packages.research_engine.research_runner import execute_research
    return execute_research(request.model_dump(), x_username or "", plan_type)


@router.post("/research/jobs", status_code=202)
def start_research_job(request: ResearchRequest, x_username: str | None = Depends(get_current_username)):
    """Async araştırma: Celery kuyruğuna ekler ve 202 + job_id döner.

    Durum sorgusu: `GET /api/client/research/jobs/{job_id}`.
    Kuyruk kullanılamıyorsa 503 `ASYNC_UNAVAILABLE` → istemci senkron `/research`'e düşer.
    """
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")

    plan_type, _ = _resolve_plan(x_username)
    client = get_client_by_username(x_username)
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

    _enforce_token_budget(x_username, plan_type)

    can_run, used, max_s = check_simulation_limit(x_username)
    if not can_run:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "QUOTA_EXCEEDED",
                "used": used,
                "limit": max_s,
                "message": f"Aylık araştırma limitine ulaştınız ({used}/{max_s}). Planınızı yükseltin.",
            },
        )

    job_id = f"job_{uuid4().hex}"
    create_research_job(job_id, x_username)

    try:
        from packages.research_engine.jobs import run_research_job

        run_research_job.delay(job_id, request.model_dump(), x_username, plan_type)
    except Exception:
        logger.warning("Celery kuyruğuna eklenemedi — istemci senkron moda düşmeli.", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ASYNC_UNAVAILABLE",
                "message": "Arka plan işleyicisi şu an kullanılamıyor.",
            },
        )

    return {"job_id": job_id, "status": "queued"}


@router.get("/research/jobs/{job_id}")
def get_research_job_status(job_id: str, x_username: str | None = Depends(get_current_username)):
    """Async araştırma durumu: queued | running | completed | failed."""
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")

    job = get_research_job(job_id)
    if not job or job.get("username") != x_username:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")

    response: dict = {
        "job_id": job_id,
        "status": job.get("status"),
        "progress": job.get("progress", 0),
    }
    if job.get("status") == "completed":
        response["result"] = job.get("result")
    elif job.get("status") == "failed":
        response["error"] = job.get("error") or "Araştırma başarısız oldu."
    return response

@router.post("/interviews/stream")
@limiter.limit("30/minute")
def stream_interviews(request: Request, body: dict, x_username: str | None = Depends(get_current_username)):
    plan_dict = body.get("plan")
    personas_list = body.get("personas")
    brief_dict = body.get("brief", {})

    if not plan_dict or not personas_list:
        raise HTTPException(status_code=400, detail="Plan veya persona bilgisi eksik.")

    plan_type, _ = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

    _require_feature(plan_type, "streaming")
    _enforce_token_budget(x_username, plan_type)

    from packages.research_engine.models import Persona, ResearchBrief, ResearchPlan
    plan = ResearchPlan(**plan_dict)
    personas = [Persona(**p) for p in personas_list]
    personas = personas[:get_max_personas(plan_type)]

    # Reconstruct brief for interview context
    brief = ResearchBrief(
        title=brief_dict.get("title", "Araştırma"),
        market=brief_dict.get("market", "Türkiye"),
        category=brief_dict.get("category", "Genel"),
        idea=brief_dict.get("context") or brief_dict.get("idea", ""),
        target_users=brief_dict.get("target_users", []),
        questions=brief_dict.get("questions", []),
        competitors=brief_dict.get("competitors", []),
        expected_price=brief_dict.get("expected_price"),
        sales_channel=brief_dict.get("sales_channel"),
        success_metric=brief_dict.get("success_metric"),
        variant_a=brief_dict.get("variant_a"),
        variant_b=brief_dict.get("variant_b"),
        respondent_types=brief_dict.get("respondent_types", []),
        discovery_channels=brief_dict.get("discovery_channels", []),
    )

    # Wrap model with PrivacyMasker — PII (telefon/e-posta/TC) LLM'e gitmeden maskelenir.
    # Rakip marka maskelemesi opsiyoneldir (varsayılan KAPALI): kamuya açık marka adları
    # KVKK kapsamında değildir ve maskelenince analiz kalitesi düşer.
    base_model = get_model_provider("flash", user_id=x_username or "", effort="high")
    _mask_brands = os.getenv("PII_MASK_COMPETITORS", "false").lower() in {"1", "true", "yes"}
    custom_keywords = brief_dict.get("competitors", []) if _mask_brands else []
    masker = PrivacyMasker(custom_keywords=custom_keywords)
    model = PrivacyResearchModelWrapper(base_model, masker)

    def _serialize(obj):
        """Safely serialize dataclass or dict objects to JSON-compatible dict."""
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        if hasattr(obj, "dict"):  # Pydantic fallback
            return obj.dict()
        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        return obj

    def event_generator():
        collected_interviews = []
        try:
            for event_type, payload in run_interviews_stream(brief, personas, model, plan.interview_script):
                payload_dict = _serialize(payload)

                if event_type == "persona_end" and "interview" in payload_dict:
                    collected_interviews.append(payload_dict["interview"])

                yield f"data: {json.dumps({'type': event_type, 'payload': payload_dict}, ensure_ascii=False)}\n\n"

            # Stream tamamlandı — atomik kota artırma
            yield f"data: {json.dumps({'type': 'done', 'interviews': collected_interviews}, ensure_ascii=False)}\n\n"
            if x_username:
                try:
                    success, used, max_s = atomic_increment_simulation_count(x_username)
                    if not success:
                        logger.warning(
                            "Quota exceeded at increment for %s (used=%s max=%s)",
                            x_username, used, max_s
                        )
                except Exception:
                    logger.error(
                        "Simulation count increment failed for %s",
                        x_username,
                        exc_info=True,
                    )
        finally:
            _record_usage(x_username, model, "interview")
            model.free_memory()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
