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
    increment_simulation_count, atomic_increment_simulation_count,
    count_user_non_ab_simulations
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


class FollowUpRequest(BaseModel):
    persona_id: str
    question: str


def is_trial_expired(client: dict | None) -> tuple[bool, str]:
    """Free plan trial expiration checker: 3 days or 2 researches (excluding A/B tests)."""
    if not client or client.get("plan_type") != "Free":
        return False, ""

    # 1. Check 3 days limit since created_at
    created_at_str = client.get("created_at")
    if created_at_str:
        try:
            from datetime import datetime, timezone
            # parse timezone-aware or naive iso format
            if "T" in created_at_str:
                created_at = datetime.fromisoformat(created_at_str)
            else:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%d")
            
            if created_at.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now()
                
            elapsed = now - created_at
            if elapsed.days >= 3:
                return True, "3 günlük ücretsiz deneme süreniz dolmuştur. Devam etmek için lütfen bir plan seçin."
        except Exception as e:
            logger.error(f"Error parsing created_at for client {client.get('username')}: {e}")

    # 2. Check 2 researches limit (excluding A/B tests)
    username = client.get("username")
    if username:
        non_ab_sims = count_user_non_ab_simulations(username)
        if non_ab_sims >= 2:
            return True, "Deneme sürümündeki 2 ücretsiz araştırma limitine ulaştınız. Devam etmek için lütfen bir plan seçin."

    return False, ""


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

    expired, reason = is_trial_expired(client)

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
        "trial_expired": expired,
        "trial_expired_reason": reason,
    }


@router.post("/upgrade-plan")
async def upgrade_plan(req: UpgradePlanRequest, x_username: str | None = Header(default=None)):
    """Kayıtlı kullanıcının planını yükseltir ve dönem sayacını sıfırlar."""
    if not x_username:
        raise HTTPException(status_code=401, detail="X-Username header gerekli.")

    valid_plans = ["Free", "Flex", "Starter", "Pro", "Enterprise"]
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
    if req.new_plan and req.new_plan in ["Flex", "Starter", "Pro", "Enterprise"]:
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
    client = get_client_by_username(x_username) if x_username else None
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

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
    
@router.post("/studies/{study_id}/follow-up")
async def study_follow_up(study_id: str, data: FollowUpRequest, x_username: str | None = Header(default=None)):
    """Belirli bir personaya ek soru sormak için kullanılır."""
    from packages.research_engine.database import get_study, save_study
    from packages.research_engine.providers import get_model_provider
    import json
    
    plan_type, plan_config = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None
    
    # 1. Deneme süresi kontrolü
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)
        
    # 2. Free planda engelle
    if plan_type == "Free":
        raise HTTPException(status_code=403, detail="Free planda takip sorusu sorulamaz. Lütfen planınızı yükseltin.")
        
    study = get_study(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı.")
        
    payload = load_study_payload(study_id, include_pdf=False)
    interviews = payload.get("interviews", [])
    
    # 3. Starter plan follow-up limiti kontrolü (Maks 3 adet)
    max_follow_ups = plan_config.get("max_follow_ups", 9999)
    current_follow_ups = 0
    for inv in interviews:
        for t in inv.get("turns", []):
            if "FOLLOW-UP" in t.get("tags", []):
                current_follow_ups += 1
                
    if current_follow_ups >= max_follow_ups:
        raise HTTPException(
            status_code=403, 
            detail=f"Starter plan limitinize ulaştınız (Maksimum {max_follow_ups} takip sorusu). Lütfen planınızı yükseltin."
        )

    target_interview = None
    target_idx = -1
    for i, inv in enumerate(interviews):
        if inv.get("persona", {}).get("id") == data.persona_id:
            target_interview = inv
            target_idx = i
            break
            
    if not target_interview:
        raise HTTPException(status_code=404, detail="Persona mülakatı bulunamadı.")
        
    persona = target_interview["persona"]
    turns = target_interview.get("turns", [])
    
    # Konuşma geçmişini kur
    messages = [
        {"role": "system", "content": f"Sen bir simülasyon personasısın. Adın {persona.get('name')}. Yaşın {persona.get('age')}. "
                                      f"Mesleğin {persona.get('role_title', 'Bilinmiyor')}. "
                                      f"Geçmiş sohbetine sadık kal ve sana sorulan ek soruya doğal, role uygun kısa bir cevap ver."}
    ]
    for turn in turns:
        messages.append({"role": "user", "content": turn.get("question", "")})
        messages.append({"role": "assistant", "content": turn.get("answer", "")})
        
    messages.append({"role": "user", "content": data.question})
    
    # Modeli çağır
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])
    prompt = f"Geçmiş:\n{history_text}\n\nYeni soru: {data.question}\nCevabın:"
    
    try:
        model = get_model_provider()
        response = model.generate(messages[0]["content"], prompt)
        answer = response.strip()
    except Exception as e:
        logger.error(f"Follow up error: {e}")
        raise HTTPException(status_code=500, detail="Cevap üretilemedi.")
        
    new_turn = {
        "question": data.question,
        "answer": answer,
        "tags": ["FOLLOW-UP"]
    }
    
    # Payload güncelle
    target_interview["turns"].append(new_turn)
    payload["interviews"][target_idx] = target_interview
    
    # Kaydet
    metadata = study
    save_study(metadata, payload)
    
    return {"status": "success", "turn": new_turn}
    
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

