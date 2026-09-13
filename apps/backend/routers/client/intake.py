"""Persona havuzu, studio simulasyonu ve Defne intake (R6-1)."""
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

@router.get("/personas")
def list_personas():
    return get_personas_pool()

@router.post("/personas")
def create_persona(persona: PersonaCreate):
    save_persona_to_pool(
        name=persona.name,
        age=persona.age,
        city=persona.city,
        segment=persona.segment,
        stance=persona.stance,
        price_sensitivity=persona.price_sensitivity,
        digital_confidence=persona.digital_confidence,
        context=persona.context,
        goals=persona.goals,
        objections=persona.objections,
        knowledge_boundary=persona.knowledge_boundary,
        country_code=persona.country_code,
        origin_country=persona.origin_country,
        role_title=persona.role_title,
        bio=persona.bio,
        attributes=persona.attributes,
        traits=persona.traits,
        created_by=persona.created_by,
        is_global=persona.is_global,
        b2b_role=persona.b2b_role,
        industry=persona.industry,
        company_size=persona.company_size,
        b2b_company_type=persona.b2b_company_type,
        b2b_decision_maker=persona.b2b_decision_maker
    )
    return {"status": "success"}

@router.post("/studio/simulate")
@limiter.limit("20/minute")
async def trigger_studio_simulation(request: Request, data: StudioSimulationRequest, x_username: str | None = Depends(get_current_username)):
    """
    Research Studio: Tek turlu simülasyon başlatma endpoint'i.
    Gateway üzerinden geçip doğrudan Celery kuyruğuna aktarır.
    """
    try:
        from packages.research_engine.database import get_db
        from packages.research_engine.gateway import ResearchInflowGateway
        from packages.research_engine.plan_config import get_plan_config

        # get_db bağlamını gateway'e sunuyoruz
        gateway = ResearchInflowGateway(db_session=get_db)
        username = x_username or "anonymous"

        plan_type, _ = _resolve_plan(username)
        plan_config = get_plan_config(plan_type)
        max_loops = plan_config.get("max_adversarial_loops", 1)

        result = await gateway.trigger_simulation_triage(
            username=username,
            brief=data.brief,
            category=data.category,
            pricing=data.pricing,
            panel_roles=data.panel_roles,
            max_adversarial_loops=max_loops
        )
        return result
    except Exception:
        logger.error("studio_simulation error for user=%s", x_username, exc_info=True)
        raise HTTPException(status_code=500, detail="Simülasyon kuyruğa alınırken hata oluştu.")

@router.get("/studio/status/{task_id}")
def get_studio_simulation_status(task_id: str, x_username: str | None = Depends(get_current_username)):
    """
    Celery task durumunu döner. Frontend polling için kullanılır.
    """
    from celery.result import AsyncResult

    from packages.research_engine.celery_app import celery_app

    try:
        task = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": task.status,  # PENDING, STARTED, SUCCESS, FAILURE
        }

        if task.status == "SUCCESS":
            response["result"] = task.result
        elif task.status == "FAILURE":
            response["error"] = str(task.info)

        return response
    except Exception as e:
        logger.error(f"Error fetching task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Görev durumu sorgulanamadı. Lütfen tekrar deneyin.")

@router.post("/studio/match-personas")
@limiter.limit("20/minute")
def match_personas(request: Request, data: dict, x_username: str | None = Depends(get_current_username)):
    """
    Brief'e (veya idea'ya) uygun veritabanındaki hazır personaları eşleştirip önerir.
    Kullanıcıya 'hangi persona grubundan kaç tane istersiniz' diye sormak için kullanılır.
    """
    try:
        import json
        import re

        from packages.research_engine.providers import get_model_provider

        all_personas = get_personas_pool()
        if not all_personas:
            return {"matched_roles": []}

        brief_text = json.dumps(data, ensure_ascii=False)

        # Basit LLM eşleştirmesi: Havuzdaki rolleri verip en uygun 5 tanesini seçtiriyoruz.
        roles_context = "\n".join([f"- {p['role_title']}: {p['bio']}" for p in all_personas[:20]]) # İlk 20'yi alalım şimdilik

        system = "Sen bir pazar araştırma uzmanısın. Görevin, verilen proje fikrine en uygun hedef kitle profillerini (rolleri) listeden seçmektir."
        prompt = (
            f"Proje Fikri:\n{brief_text}\n\n"
            f"Mevcut Persona Rolleri:\n{roles_context}\n\n"
            "Yukarıdaki listeden bu proje için en uygun 4-5 rolü seç. SADECE aşağıdaki gibi JSON dizisi döndür, başka hiçbir metin ekleme:\n"
            '[\n  {"role": "Rol Adı", "why": "Bu projeye neden uygun?"}\n]'
        )

        model = get_model_provider("flash", user_id=x_username or "", effort="low")
        text = model.generate(system, prompt)
        _record_usage(x_username, model, "match")

        # JSON parse (fallback safety)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)

        try:
            matched = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            matched = []
        # For each matched role, find 1-2 sample personas from the pool to return for UI
        for m in matched:
            role_name = m.get("role", "")
            samples = [p for p in all_personas if p.get("role_title") == role_name or role_name in p.get("segment", "")]
            if not samples:
                samples = []
            m["samples"] = samples[:2]

        return {"matched_roles": matched}
    except Exception as e:
        logger.error(f"match-personas error: {e}")
        raise HTTPException(status_code=500, detail="Persona eşleştirme sırasında bir hata oluştu.")

@router.post("/intake")
@limiter.limit("20/minute")
def intake_chat(request: Request, data: IntakeChatRequest, x_username: str | None = Depends(get_current_username)):
    try:
        from packages.research_engine.database import get_system_config
        plan_type, _ = _resolve_plan(x_username)
        _enforce_token_budget(x_username, plan_type)
        model = get_model_provider("flash", user_id=(x_username or "").strip() or "anonymous", effort="low")
        # wizard_prompt DB'den okunur — admin panelinden kod deploy'u olmadan güncellenebilir
        try:
            config = get_system_config()
            db_wizard_prompt = config.get("wizard_prompt", "")
        except Exception:
            db_wizard_prompt = ""
        result = process_intake_chat(
            current_brief=data.current_brief,
            chat_history=data.chat_history,
            user_message=data.user_message,
            model=model,
            app_mode=data.app_mode,
            wizard_prompt=db_wizard_prompt,
        )
        _record_usage(x_username, model, "intake")
        return result
    except HTTPException:
        raise  # plan/kota hatalarını (403/429) 503'e dönüştürme
    except Exception as e:
        logger.error("intake_chat error for user=%s: %s", getattr(data, 'user_message', '')[:40], e, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Yapay Zeka servisi geçici olarak yoğun. Hata: {str(e)[:100]}")
