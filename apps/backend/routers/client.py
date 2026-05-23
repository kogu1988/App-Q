from fastapi import APIRouter, HTTPException, Response, Query, Header, Request
import logging
from pydantic import BaseModel
from typing import Optional, List, Any
from fastapi.responses import StreamingResponse
from packages.research_engine.workflow import build_research_plan, generate_personas, run_interviews_stream
from packages.research_engine.analytics import synthesize_report
from packages.research_engine.database import (
    list_studies, load_study_payload, save_study, get_personas_pool, save_persona_to_pool,
    archive_study, save_feedback, get_client_by_username,
    upgrade_client_plan, check_simulation_limit, register_client_if_new,
    increment_simulation_count, atomic_increment_simulation_count
)
from packages.research_engine.intake import process_intake_chat
from packages.research_engine.providers import get_model_provider
from packages.research_engine.plan_config import get_plan_config, has_feature, get_max_personas, get_min_plan_for_feature
from slowapi import Limiter
from slowapi.util import get_remote_address
import json

logger = logging.getLogger(__name__)

# Limiter, main.py'deki app.state.limiter ile uyumlu
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


def _resolve_plan(x_username: str | None) -> tuple[str, dict]:
    """Header'dan username al, plan tipini ve config'ini döner. Kullanıcı bulunamazsa Free plan uygular."""
    plan_type = "Free"
    if x_username:
        client = get_client_by_username(x_username)
        if client:
            plan_type = client.get("plan_type", "Free")
    return plan_type, get_plan_config(plan_type)


def _require_feature(plan_type: str, feature: str) -> None:
    """Özellik plan'da yoksa HTTP 403 fırlatır."""
    if not has_feature(plan_type, feature):
        min_plan = get_min_plan_for_feature(feature)
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PLAN_GATE",
                "feature": feature,
                "current_plan": plan_type,
                "required_plan": min_plan,
                "message": "Bu özellik güncel planınızda bulunmuyor.",
            },
        )

class IntakeChatRequest(BaseModel):
    current_brief: dict = {}
    chat_history: List[dict] = []
    user_message: str
    app_mode: str = "research"  # "research" | "ab_test"


class GeneratePersonasRequest(BaseModel):
    plan: dict


class SynthesizeRequest(BaseModel):
    interviews: List[dict]
    plan: dict
    brief: dict = {}

class BriefRequest(BaseModel):
    category: str
    title: str
    context: str
    brand: str
    budget: str
    target_users: list[str] = []
    competitors: list[str] = []
    expected_price: str | None = None
    sales_channel: str | None = None
    success_metric: str | None = None
    variant_a: str | None = None
    variant_b: str | None = None
    questions: list[str] = []
    discovery_channels: list[str] = []

class StudyPayload(BaseModel):
    metadata: dict
    payload: dict

class PersonaCreate(BaseModel):
    name: str
    age: int
    city: str
    segment: str
    stance: str
    price_sensitivity: int
    digital_confidence: int
    context: str
    goals: str
    objections: str
    knowledge_boundary: str
    country_code: str
    origin_country: str
    role_title: str
    bio: str
    attributes: str
    traits: str
    created_by: str = "system"
    is_global: bool = True
    b2b_role: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    b2b_company_type: Optional[str] = None
    b2b_decision_maker: bool = False

class FeedbackCreate(BaseModel):
    username: str = "anonymous"
    study_id: str
    item_type: str
    item_id: str
    vote: int
    comment: str = ""


class UpgradePlanRequest(BaseModel):
    new_plan: str
    billing_cycle: str = "monthly"  # "monthly" | "annual"


class RegisterRequest(BaseModel):
    username: str
    email: str = ""
    new_plan: str = ""          # İsteğe bağlı: register sonrası bu plana yükselt
    billing_cycle: str = "monthly"

@router.get("/me")
@limiter.limit("60/minute")
async def get_me(request: Request, x_username: str | None = Header(default=None)):
    """Mevcut kullanıcının plan bilgisini döner."""
    plan_type, config = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None

    period_simulations = 0
    billing_cycle = "monthly"
    period_start = None
    if client:
        _, used, _ = check_simulation_limit(x_username) if x_username else (True, 0, 0)
        period_simulations = client.get("period_simulations", 0)
        billing_cycle = client.get("billing_cycle") or "monthly"
        period_start = client.get("period_start")

    return {
        "username": x_username or "anonymous",
        "plan_type": plan_type,
        "billing_cycle": billing_cycle,
        "period_start": period_start,
        "limits": {
            "max_personas": config["max_personas"],
            "max_simulations": config["max_simulations"],
        },
        "features": {k: v for k, v in config.items() if isinstance(v, bool)},
        "total_simulations": client.get("total_simulations", 0) if client else 0,
        "period_simulations": period_simulations,
    }


@router.post("/upgrade-plan")
async def upgrade_plan(req: UpgradePlanRequest, x_username: str | None = Header(default=None)):
    """Kayıtlı kullanıcının planını yükseltir ve dönem sayacını sıfırlar."""
    if not x_username:
        raise HTTPException(status_code=401, detail="X-Username header gerekli.")

    valid_plans = ["Free", "Starter", "Pro", "Enterprise"]
    if req.new_plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Geçersiz plan: {req.new_plan}")
    if req.billing_cycle not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing_cycle 'monthly' veya 'annual' olmalı.")

    upgrade_client_plan(x_username, req.new_plan, req.billing_cycle)
    _, config = _resolve_plan(x_username)
    return {
        "success": True,
        "username": x_username,
        "new_plan": req.new_plan,
        "billing_cycle": req.billing_cycle,
        "message": f"Plan başarıyla {req.new_plan} olarak güncellendi. Dönem sayacı sıfırlandı.",
        "new_limits": {
            "max_simulations": config["max_simulations"],
            "max_personas": config["max_personas"],
        },
    }


@router.post("/register")
@limiter.limit("10/minute")
async def register(request: Request, req: RegisterRequest):
    """Yeni kullanıcı kaydı: yoksa Free planla oluşturur, varsa mevcut planı döner.
    İsteğe bağlı: new_plan verilmişse kayıt sonrası planı yükseltir."""
    username = (req.username or "").strip()
    if not username or len(username) < 2 or len(username) > 20:
        raise HTTPException(status_code=400, detail="Kullanıcı adı 2-20 karakter arasında olmalı.")
    if not username.isalnum() and not all(c.isalnum() or c in "-_" for c in username):
        raise HTTPException(status_code=400, detail="Kullanıcı adı sadece harf, rakam, - ve _ içerebilir.")

    client, created = register_client_if_new(username, req.email)

    # İsteğe bağlı plan yükseltme
    if req.new_plan and req.new_plan in ["Starter", "Pro", "Enterprise"]:
        upgrade_client_plan(username, req.new_plan, req.billing_cycle)
        client["plan_type"] = req.new_plan

    return {
        "username": username,
        "plan_type": client.get("plan_type", "Free"),
        "created": created,
        "message": "Kayıt tamamlandı." if created else "Hoş geldiniz, mevcut hesabınıza devam ediliyor.",
    }

@router.get("/studies")
async def get_studies(include_archived: bool = Query(False)):
    return list_studies(include_archived=include_archived)

@router.get("/studies/{study_id}")
async def get_study(study_id: str):
    return load_study_payload(study_id, include_pdf=False)

@router.get("/studies/{study_id}/pdf")
async def download_study_pdf(study_id: str, x_username: str | None = Header(default=None)):
    plan_type, _ = _resolve_plan(x_username)
    _require_feature(plan_type, "pdf_export")
    payload = load_study_payload(study_id, include_pdf=True)
    pdf_data = payload.get("report_pdf")
    if not pdf_data:
        raise HTTPException(status_code=404, detail="PDF has not been generated for this study yet.")
    
    # Ensure memoryview/bytes conversion
    if isinstance(pdf_data, memoryview):
        pdf_data = pdf_data.tobytes()
    elif not isinstance(pdf_data, bytes):
        pdf_data = bytes(pdf_data)

    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=AppQ-Report-{study_id}.pdf",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.put("/studies/{study_id}/archive")
async def archive_study_endpoint(study_id: str):
    archive_study(study_id)
    return {"status": "success"}

@router.post("/feedback")
async def submit_feedback(data: FeedbackCreate):
    save_feedback(data.username, data.study_id, data.item_type, data.item_id, data.vote, data.comment)
    return {"status": "success"}

@router.post("/studies")
async def create_or_update_study(data: StudyPayload):
    save_study(data.metadata, data.payload)
    return {"status": "success", "id": data.metadata.get("id")}

@router.get("/personas")
async def list_personas():
    return get_personas_pool()

@router.post("/personas")
async def create_persona(persona: PersonaCreate):
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

@router.post("/plan")
async def create_plan(request: BriefRequest, x_username: str | None = Header(default=None)):
    plan_type, _ = _resolve_plan(x_username)
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
    )
    plan = build_research_plan(brief)
    return plan

@router.post("/personas/generate")
async def generate_personas_from_plan(request: GeneratePersonasRequest, x_username: str | None = Header(default=None)):
    plan_type, _ = _resolve_plan(x_username)
    from packages.research_engine.models import ResearchPlan
    plan = ResearchPlan(**request.plan)
    # Panel boyutunu plan limitine göre kırp
    max_p = get_max_personas(plan_type)
    if hasattr(plan, "panel_size") and plan.panel_size > max_p:
        plan.panel_size = max_p
    personas = generate_personas(plan)
    personas = personas[:max_p]
    return {"personas": [p.dict() for p in personas]}

@router.post("/interviews/stream")
@limiter.limit("5/minute")
async def stream_interviews(request: Request, body: dict, x_username: str | None = Header(default=None)):
    plan_dict = body.get("plan")
    personas_list = body.get("personas")

    if not plan_dict or not personas_list:
        raise HTTPException(status_code=400, detail="Missing plan or personas")

    plan_type, _ = _resolve_plan(x_username)
    _require_feature(plan_type, "streaming")

    from packages.research_engine.models import ResearchPlan, Persona
    plan = ResearchPlan(**plan_dict)
    personas = [Persona(**p) for p in personas_list]
    personas = personas[:get_max_personas(plan_type)]

    def event_generator():
        for chunk in run_interviews_stream(plan, personas):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        # Stream tamamlandı — atomik kota artırma
        if x_username:
            try:
                success, used, max_s = atomic_increment_simulation_count(x_username)
                if not success:
                    # Kota stream bitmeden doldu (par.el istek senaryosu)
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

    return StreamingResponse(event_generator(), media_type="text/event-stream")
    
@router.post("/synthesize")
async def synthesize(request: SynthesizeRequest, x_username: str | None = Header(default=None)):
    plan_type, _ = _resolve_plan(x_username)

    # B2B modu Pro+ gerektirir
    if request.brief.get("b2b_mode"):
        _require_feature(plan_type, "b2b_mode")

    from packages.research_engine.models import PersonaInterview, ResearchPlan
    p_interviews = [PersonaInterview(**i) for i in request.interviews]
    r_plan = ResearchPlan(**request.plan)
    report = synthesize_report(p_interviews, r_plan)
    return report.dict()

@router.post("/intake")
@limiter.limit("20/minute")
async def intake_chat(request: Request, data: IntakeChatRequest):
    """
    Defne (araştırma sihirbazı ajanı) ile sohbet endpoint'i.
    process_intake_chat() kullanarak brief'i adım adım doldurur.
    """
    try:
        model = get_model_provider()
        result = process_intake_chat(
            current_brief=data.current_brief,
            chat_history=data.chat_history,
            user_message=data.user_message,
            model=model,
            app_mode=data.app_mode
        )
        return result
    except Exception as e:
        logger.error("intake_chat error for user=%s", getattr(data, 'user_message', '')[:40], exc_info=True)
        raise HTTPException(status_code=500, detail="Servis geçici olarak kullanılamıyor.")

@router.get("/models")
async def list_models():
    """Mevcut Ollama model listesini döner."""
    from packages.research_engine.providers import discover_ollama_models
    from packages.research_engine.database import get_system_config
    try:
        available = discover_ollama_models()
        config = get_system_config()
        return {
            "available_models": available,
            "active_b2c": config.get("b2c_model", ""),
            "active_b2b": config.get("b2b_model", ""),
        }
    except Exception as e:
        return {"available_models": [], "active_b2c": "", "active_b2b": "", "error": str(e)}

