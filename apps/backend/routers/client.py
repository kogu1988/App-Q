from fastapi import APIRouter, HTTPException, Response, Query, Header, Request
import logging
from dataclasses import asdict
from pydantic import BaseModel
from typing import Optional, List
from fastapi.responses import StreamingResponse
from packages.research_engine.workflow import build_research_plan, generate_personas, run_interviews_stream, run_interviews_batch
from packages.research_engine.analytics import synthesize_report
from packages.research_engine.privacy import PrivacyMasker, PrivacyResearchModelWrapper
from packages.research_engine.database import (
    list_studies, load_study_payload, save_study, archive_study, delete_study, save_feedback,

    get_client_by_username, upgrade_client_plan, check_simulation_limit, 
    register_client_if_new, atomic_increment_simulation_count,
    count_user_non_ab_simulations
)
from packages.research_engine.db_vectors import (
    get_personas_pool, save_persona_to_pool
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
    created_at_val = client.get("created_at")
    if created_at_val:
        try:
            from datetime import datetime, timezone
            # Handle both string and datetime objects
            if isinstance(created_at_val, datetime):
                created_at = created_at_val
            elif "T" in str(created_at_val):
                created_at = datetime.fromisoformat(str(created_at_val))
            else:
                created_at = datetime.strptime(str(created_at_val), "%Y-%m-%d")
            
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

class StudioSimulationRequest(BaseModel):
    brief: str
    category: str
    pricing: str
    panel_roles: Optional[List[dict]] = []

class IntakeChatRequest(BaseModel):
    current_brief: dict = {}
    chat_history: List[dict] = []
    user_message: str
    app_mode: str = "research"  # "research" | "ab_test"


class GeneratePersonasRequest(BaseModel):
    plan: dict
    brief: dict = {}  # ResearchBrief verileri (optional, fallback ile)


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
    respondent_types: list[str] = []

class ResearchRequest(BaseModel):
    """Adım 2: Plan + Persona + Mülakatları tek seferde başlatır."""
    category: str
    title: str = "Araştırma"
    context: str  # brief fikri
    brand: str = ""
    budget: str = ""
    target_users: list[str] = []
    competitors: list[str] = []
    expected_price: str | None = None
    sales_channel: str | None = None
    success_metric: str | None = None
    questions: list[str] = []
    discovery_channels: list[str] = []
    respondent_types: list[str] = []
    # Intake (Defne) tarafından doldurulan alanlar
    intake_brief: dict = {}
    # Kaç persona kullanılacağı
    panel_size: int = 5

class StudyPayload(BaseModel):
    metadata: dict
    payload: dict

class PersonaSearch(BaseModel):
    query: str

class FollowUpRequest(BaseModel):
    persona_id: str
    question: str
    age: int
    city: str
    segment: str
    stance: str
    price_sensitivity: int

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
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")

    valid_plans = ["Free", "Flex", "Starter", "Pro", "Enterprise"]
    if req.new_plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Geçersiz plan: {req.new_plan}")
    if req.billing_cycle not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="Faturalama dönemi 'aylık' veya 'yıllık' olmalı.")

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

    payload = load_study_payload(study_id, include_pdf=False)

    # Try report_markdown first, fall back to report_html
    report_markdown = payload.get("report_markdown") or ""
    title = payload.get("title") or payload.get("metadata", {}).get("title") or f"Rapor {study_id}"

    if not report_markdown:
        raise HTTPException(
            status_code=404,
            detail="Bu araştırma için rapor içeriği henüz mevcut değil."
        )

    # On-the-fly: Markdown → HTML → PDF (no DB write needed)
    from packages.research_engine.pdf_generator import generate_pdf_from_markdown
    pdf_bytes = generate_pdf_from_markdown(report_markdown, title=title, study_id=study_id)

    if not pdf_bytes:
        raise HTTPException(
            status_code=500,
            detail="PDF oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Clarere-Report-{study_id}.pdf",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )



@router.put("/studies/{study_id}/archive")
async def archive_study_endpoint(study_id: str):
    archive_study(study_id)
    return {"status": "archived"}


@router.delete("/studies/{study_id}")
async def delete_study_endpoint(
    study_id: str,
    x_username: str | None = Header(default=None),
):
    """Araştırmayı kalıcı olarak siler.

    Sahiplik kontrolü: studies tablosunda username alanı ile eşleşme arananır.
    Eşleşme bulunamazsa ya da bulu(nan study başka bir kullanıcıya aitse 404 döner.
    """
    from packages.research_engine.database import get_study

    study = get_study(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı.")

    # Sahiplik kontrolü — study'nin username alanı varsa eşleştir
    owner = study.get("username") or study.get("created_by") or ""
    if owner and x_username and owner != x_username:
        raise HTTPException(
            status_code=403,
            detail="Bu araştırmayı silme yetkiniz yok.",
        )

    deleted = delete_study(study_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı ya da zaten silinmiş.")

    return {"status": "deleted", "study_id": study_id}

@router.post("/feedback")
async def submit_feedback(data: FeedbackCreate):
    save_feedback(data.username, data.study_id, data.item_type, data.item_id, data.vote, data.comment)
    return {"status": "success"}

@router.post("/studies/{study_id}/follow-up")
async def study_follow_up(study_id: str, data: FollowUpRequest, x_username: str | None = Header(default=None)):
    """Belirli bir personaya ek soru sormak için kullanılır."""
    from packages.research_engine.database import get_study
    from packages.research_engine.providers import get_model_provider
    from packages.research_engine.plan_config import get_plan_config
    import json
    
    # 1. Paket Limiti (Option A) Kontrolü
    plan_type, _ = _resolve_plan(x_username)
    plan_config = get_plan_config(plan_type)
    max_follow_ups = plan_config.get("max_follow_ups", 0)
    
    study = get_study(study_id)
    if not study or "payload" not in study:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı.")
        
    payload_str = study["payload"]
    if not payload_str:
        raise HTTPException(status_code=404, detail="Araştırma verisi boş.")
        
    try:
        payload = json.loads(payload_str)
    except:
        raise HTTPException(status_code=500, detail="Veri formatı geçersiz. Lütfen tekrar deneyin.")
        
    interviews = payload.get("interviews", [])
    
    # 2. Mevcut Follow-up sayısını say (Global Counter)
    current_follow_ups = 0
    for inv in interviews:
        for t in inv.get("turns", []):
            if "FOLLOW-UP" in t.get("tags", []):
                current_follow_ups += 1
                
    if current_follow_ups >= max_follow_ups:
        raise HTTPException(status_code=403, detail=f"Paket limitinize ulaştınız (Maksimum {max_follow_ups} takip sorusu). Lütfen paketinizi yükseltin.")

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
    
    # Reconstruct conversation
    messages = [
        {"role": "system", "content": f"Sen bir simülasyon personasısın. Adın {persona.get('name')}. Yaşın {persona.get('age')}. "
                                      f"Mesleğin {persona.get('role_title', 'Bilinmiyor')}. "
                                      f"Geçmiş sohbetine sadık kal ve sana sorulan ek soruya doğal, role uygun kısa bir cevap ver."}
    ]
    
    for turn in turns:
        messages.append({"role": "user", "content": turn.get("question", "")})
        messages.append({"role": "assistant", "content": turn.get("answer", "")})
        
    messages.append({"role": "user", "content": data.question})
    
    # Format for the prompt
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])
    prompt = f"Geçmiş:\n{history_text}\n\nYeni soru: {data.question}\nCevabın:"
    
    try:
        model = get_model_provider("flash", user_id=x_username or "")
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
    
    # Update payload
    target_interview["turns"].append(new_turn)
    payload["interviews"][target_idx] = target_interview
    
    # Save back
    from packages.research_engine.database import save_study
    save_study(study.get("metadata", {}), payload)
    
    return {"status": "success", "turn": new_turn}

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
        respondent_types=request.respondent_types,
    )
    from packages.research_engine.reframing import apply_input_reframing
    from packages.research_engine.providers import get_model_provider
    from dataclasses import replace

    plan = build_research_plan(brief)
    
    # Reframing katmanı ile sübjektif girdileri nesnelleştir (Sycophancy Mitigation)
    try:
        model = get_model_provider("flash", user_id=x_username or "")
        reframed = apply_input_reframing(brief, model)
        
        new_objective = reframed.get("objective_product_context", plan.objective)
        new_questions = reframed.get("primary_research_questions", plan.interview_questions)
        
        plan = replace(plan, objective=new_objective, interview_questions=new_questions)
    except Exception as e:
        print(f"Reframing katmanı başarısız: {e}")

    return plan

@router.post("/personas/generate")
async def generate_personas_from_plan(request: GeneratePersonasRequest, x_username: str | None = Header(default=None)):
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
async def run_full_research(request: ResearchRequest, x_username: str | None = Header(default=None)):
    """
    Adım 2 — Birleşik Araştırma: Plan + Persona + Mülakat.
    Brief'i alır; plan üretir, personaları oluşturur ve batch mülakatları çalıştırır.
    Model: deepseek-v4-flash (hızlı/ucuz).
    """
    plan_type, _ = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

    from packages.research_engine.models import ResearchBrief

    # Brief'i intake_brief (Defne çıktısı) veya doğrudan request'ten kur
    brief_data = request.intake_brief or {}
    brief = ResearchBrief(
        title=brief_data.get("title") or request.title,
        market="Türkiye",
        category=request.category,
        idea=brief_data.get("context") or brief_data.get("idea") or request.context,
        target_users=brief_data.get("target_users") or request.target_users or [],
        questions=brief_data.get("questions") or request.questions or [],
        competitors=brief_data.get("competitors") or request.competitors or [],
        expected_price=brief_data.get("expected_price") or request.expected_price,
        sales_channel=brief_data.get("sales_channel") or request.sales_channel,
        success_metric=brief_data.get("success_metric") or request.success_metric,
        respondent_types=brief_data.get("respondent_types") or request.respondent_types or [],
        discovery_channels=brief_data.get("discovery_channels") or request.discovery_channels or [],
    )

        # 1. Plan üret
    model = get_model_provider("flash", user_id=x_username or "")
    plan = build_research_plan(brief)

    # 2. Persona üret
    personas = generate_personas(brief)
    max_p = get_max_personas(plan_type)
    personas = personas[:max_p]

    # 3. Batch mülakat
    interviews = run_interviews_batch(brief, personas, model, plan.interview_script)

    # 4. Atomik kota artırma
    if x_username:
        try:
            atomic_increment_simulation_count(x_username)
        except Exception:
            logger.warning("Simulation count increment failed for %s", x_username, exc_info=True)

    return {
        "plan": asdict(plan),
        "personas": [asdict(p) for p in personas],
        "interviews": [asdict(iv) for iv in interviews],
    }


@router.post("/interviews/stream")
@limiter.limit("30/minute")
async def stream_interviews(request: Request, body: dict, x_username: str | None = Header(default=None)):
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

    from packages.research_engine.models import ResearchPlan, Persona, ResearchBrief
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

    # Wrap model with PrivacyMasker — masks PII + competitor brand names before LLM call
    base_model = get_model_provider("flash", user_id=x_username or "")
    custom_keywords = brief_dict.get("competitors", [])  # mask competitor names
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
            model.free_memory()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
    
@router.post("/studies/{study_id}/follow-up")
async def study_follow_up(study_id: str, data: FollowUpRequest, x_username: str | None = Header(default=None)):
    """Belirli bir personaya ek soru sormak için kullanılır."""
    from packages.research_engine.database import get_study, save_study
    from packages.research_engine.providers import get_model_provider
    
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
        model = get_model_provider("flash", user_id=x_username or "")
        response = model.generate(messages[0]["content"], prompt)
        answer = response.strip()
    except Exception as e:
        logger.error(f"Follow up error: {e}")
        raise HTTPException(status_code=500, detail="Cevap üretilemedi. Lütfen tekrar deneyin.")
        
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

    from packages.research_engine.models import PersonaInterview, ResearchPlan, ResearchBrief, Persona

    # brief → ResearchBrief
    bd = request.brief
    r_brief = ResearchBrief(
        title=bd.get("title", "Araştırma"),
        market=bd.get("market", "Türkiye"),
        category=bd.get("category", "Genel"),
        idea=bd.get("context") or bd.get("idea", ""),
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

    r_plan = ResearchPlan(**request.plan)
    # PersonaInterview icindeki nested dict'leri dogru objelere cevir
    from packages.research_engine.models import InterviewTurn, Persona
    raw_interviews = []
    for i in request.interviews:
        raw_turns = i.get("turns", [])
        turns = [InterviewTurn(**t) for t in raw_turns]
        raw_persona = i.get("persona", {})
        persona = Persona(**raw_persona) if isinstance(raw_persona, dict) else raw_persona
        pi = PersonaInterview(
            persona=persona,
            turns=turns,
            consistency_notes=i.get("consistency_notes", []),
        )
        raw_interviews.append(pi)
    p_interviews = raw_interviews

    # personas listesi varsa ilet (van_westendorp ve brand_health için gerekli)
    # SynthesizeRequest'e personas eklenmemişse boş liste ile devam et
    personas_raw = getattr(request, "personas", []) or []
    r_personas = [Persona(**p) for p in personas_raw] if personas_raw else [
        iv.persona for iv in p_interviews
    ]

    report = synthesize_report(
        brief=r_brief,
        plan=r_plan,
        personas=r_personas,
        interviews=p_interviews,
    )

    from dataclasses import asdict
    report_dict = asdict(report)

    # research_quality her plan için hesaplanır; Pro+ kontrolü yok —
    # frontend PlanGate ile gösterimi kısıtlıyor
    return report_dict

@router.post("/studio/simulate")
@limiter.limit("20/minute")
async def trigger_studio_simulation(request: Request, data: StudioSimulationRequest, x_username: str | None = Header(default=None)):
    """
    Research Studio: Tek turlu simülasyon başlatma endpoint'i.
    Gateway üzerinden geçip doğrudan Celery kuyruğuna aktarır.
    """
    try:
        from packages.research_engine.gateway import ResearchInflowGateway
        from packages.research_engine.database import get_db
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
async def get_studio_simulation_status(task_id: str, x_username: str | None = Header(default=None)):
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
async def match_personas(request: Request, data: dict, x_username: str | None = Header(default=None)):
    """
    Brief'e (veya idea'ya) uygun veritabanındaki hazır personaları eşleştirip önerir.
    Kullanıcıya 'hangi persona grubundan kaç tane istersiniz' diye sormak için kullanılır.
    """
    try:
        from packages.research_engine.database import get_personas_pool
        from packages.research_engine.providers import get_model_provider
        import json
        import re
        
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
        
        model = get_model_provider("flash", user_id=x_username or "")
        text = model.generate(system, prompt)
        
        # JSON parse (fallback safety)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)
            
        try:
            matched = json.loads(text)
        except:
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
async def intake_chat(request: Request, data: IntakeChatRequest, x_username: str | None = Header(default=None)):
    try:
        from packages.research_engine.database import get_system_config
        model = get_model_provider("flash", user_id=(x_username or "").strip() or "anonymous")
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
        return result
    except Exception:
        logger.error("intake_chat error for user=%s", getattr(data, 'user_message', '')[:40], exc_info=True)
        raise HTTPException(status_code=503, detail="Yapay Zeka servisi geçici olarak yoğun. Lütfen tekrar deneyin.")

@router.post("/contact")
async def contact_form(data: dict):
    """İletişim formu — mesajı DB'ye kaydeder."""
    from packages.research_engine.database import get_db
    from datetime import datetime
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Mesaj 2000 karakterden uzun olamaz.")
    try:
        with get_db() as (conn, cur):
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS contact_messages (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
                (name, email, message),
            )
        logger.info(f"Contact form submitted by {name} <{email}>")
        return {"status": "success", "message": "Mesajınız iletildi."}
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Mesaj kaydedilemedi. Lütfen clarere@clarere.com adresine e-posta atın.")


@router.post("/ws/ticket")
@limiter.limit("20/minute")
async def generate_ws_ticket(request: Request, x_username: str | None = Header(default=None)):
    """
    Generates a 10-second single-use ticket for WebSocket authentication.
    """
    import redis
    import os
    import uuid
    
    VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")
    ticket = str(uuid.uuid4())
    username = x_username or "anonymous"
    try:
        r = redis.from_url(VALKEY_URL)
        # Store ticket mapping to username, expire in 10 seconds
        r.setex(f"ws_ticket:{ticket}", 10, username)
        return {"ticket": ticket, "expires_in": 10}
    except Exception as e:
        logger.error(f"Failed to generate WS ticket: {e}")
        raise HTTPException(status_code=500, detail="Bağlantı bileti üretilemedi. Lütfen tekrar deneyin.")

from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/synthesis/{research_id}")
async def ws_synthesis_status(websocket: WebSocket, research_id: str, ticket: str = Query(...)):
    """
    Streams the thematic synthesis status and JSON payload to the client via Redis Pub/Sub.
    """
    import redis.asyncio as aioredis
    import redis as sync_redis
    import os
    import asyncio
    
    VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")
    
    # Authenticate ticket
    try:
        r_sync = sync_redis.from_url(VALKEY_URL)
        ticket_key = f"ws_ticket:{ticket}"
        username = r_sync.get(ticket_key)
        
        if not username:
            await websocket.close(code=1008, reason="Bağlantı biletiniz geçersiz veya süresi dolmuş. Lütfen sayfayı yenileyin.")
            return
            
        # Delete ticket so it's single use
        r_sync.delete(ticket_key)
    except Exception as e:
        logger.error(f"Ticket auth error: {e}")
        await websocket.close(code=1011, reason="Sunucu hatası.")
        return

    # Accept connection
    await websocket.accept()
    logger.info(f"WebSocket connected for synthesis {research_id}")
    
    r_async = None
    pubsub = None
    try:
        r_async = aioredis.from_url(VALKEY_URL)
        pubsub = r_async.pubsub()
        channel = f"synthesis_status:{research_id}"
        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                data_str = message["data"].decode("utf-8")
                await websocket.send_text(data_str)
                
                # Close if completed or failed
                try:
                    payload = json.loads(data_str)
                    if payload.get("status") in ("completed", "failed"):
                        await asyncio.sleep(0.5)
                        break
                except:
                    pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for synthesis {research_id}")
    except Exception as e:
        logger.error(f"WebSocket error for synthesis {research_id}: {e}")
    finally:
        if pubsub:
            await pubsub.unsubscribe()
        try:
            await websocket.close()
        except:
            pass

