from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import os
from packages.research_engine.database import (
    get_clients, get_system_config, get_feedbacks, get_audit_logs,
    add_client, update_client, delete_client, update_system_config,
    get_personas_pool, get_question_collection, update_question_liked_status,
    update_question_purpose, delete_from_question_collection
)
from packages.research_engine.plan_config import PLAN_CONFIG, PLAN_ORDER, FEATURE_MIN_PLAN

_ADMIN_KEY = os.getenv("ADMIN_SECRET_KEY", "")

def require_admin(x_admin_key: str = Header(default="")) -> None:
    """Admin endpoint koruyucu dependency. ADMIN_SECRET_KEY env var zorunlu."""
    if not _ADMIN_KEY:
        # Geliştirme ortamı: key set edilmemişse uyar ama geçir
        print("[WARN] ADMIN_SECRET_KEY ayarlanmamış — admin API korumasız!")
        return
    if x_admin_key != _ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Yetkisiz: Geçersiz admin anahtarı.")


router = APIRouter(dependencies=[Depends(require_admin)])

class ClientCreate(BaseModel):
    username: str
    email: str
    plan_type: str
    max_simulations: int
    max_tokens: int
    plan_start: Optional[str] = None
    plan_end: Optional[str] = None

class ClientUpdate(BaseModel):
    email: str
    plan_type: str
    max_simulations: int
    max_tokens: int
    plan_start: str
    plan_end: str
    status: str

class ConfigUpdate(BaseModel):
    key: str
    value: str

class DefaultQuestionsUpdate(BaseModel):
    questions: List[str]

@router.get("/clients")
async def list_clients():
    return get_clients()

@router.post("/clients")
async def create_client(client: ClientCreate):
    add_client(
        client.username, client.email, client.plan_type, 
        client.max_simulations, client.max_tokens, 
        client.plan_start, client.plan_end
    )
    return {"status": "success"}

@router.put("/clients/{username}")
async def update_client_endpoint(username: str, client: ClientUpdate):
    update_client(
        username, client.email, client.plan_type, 
        client.max_simulations, client.max_tokens, 
        client.plan_start, client.plan_end, client.status
    )
    return {"status": "success"}

@router.delete("/clients/{username}")
async def delete_client_endpoint(username: str):
    delete_client(username)
    return {"status": "success"}

@router.get("/config")
async def get_config():
    return get_system_config()

@router.post("/config")
async def update_config(config: ConfigUpdate):
    update_system_config(config.key, config.value)
    return {"status": "success"}

@router.get("/feedbacks")
async def list_feedbacks():
    return get_feedbacks()

@router.get("/audit_logs")
async def list_audit_logs():
    return get_audit_logs()

@router.get("/personas")
async def list_personas():
    return get_personas_pool()

@router.get("/questions")
async def list_questions():
    return get_question_collection()

@router.put("/questions/{question_id}/like")
async def like_question(question_id: int, is_liked: bool):
    update_question_liked_status(question_id, is_liked)
    return {"status": "success"}

@router.put("/questions/{question_id}/purpose")
async def update_purpose(question_id: int, purpose: str):
    update_question_purpose(question_id, purpose)
    return {"status": "success"}

@router.delete("/questions/{question_id}")
async def delete_question(question_id: int):
    delete_from_question_collection(question_id)
    return {"status": "success"}

# ─── Agent Schemas & Template Management ────────────────────────────────────────────────

@router.get("/schemas")
async def get_agent_schemas():
    """Tüm ajanların beklediği JSON şemalarını, varsayılan soruları ve concept pool'ları döner."""
    import json
    from packages.research_engine.workflow import DEFAULT_QUESTIONS
    from packages.research_engine.intake import CONCEPT_POOLS

    config = get_system_config()
    raw = config.get("default_interview_questions", "")
    try:
        db_questions = json.loads(raw) if raw else list(DEFAULT_QUESTIONS)
    except Exception:
        db_questions = list(DEFAULT_QUESTIONS)

    brief_defaults = {
        "market":         config.get("default_market", "Türkiye"),
        "category":       config.get("default_category", ""),
        "expected_price": config.get("default_expected_price", ""),
        "sales_channel":  config.get("default_sales_channel", ""),
        "success_metric": config.get("default_success_metric", ""),
    }

    return {
        "brief_schema": {
            "description": "Defne ajanına iletilen araştırma brief'i yapısı",
            "fields": [
                {"key": "title",          "type": "str",       "required": True,  "desc": "Çalışmanın kısa adı"},
                {"key": "market",         "type": "str",       "required": False, "desc": "Hedef pazar (varsayılan: Türkiye)"},
                {"key": "category",       "type": "str",       "required": False, "desc": "Ürün/hizmet kategorisi"},
                {"key": "idea",           "type": "str",       "required": True,  "desc": "Ürün fikri ve çözülen problem"},
                {"key": "target_users",   "type": "list[str]", "required": False, "desc": "Hedef kullanıcı segmentleri"},
                {"key": "questions",      "type": "list[str]", "required": False, "desc": "Araştırmada yanıtlanacak sorular"},
                {"key": "competitors",    "type": "list[str]", "required": False, "desc": "Rakipler ve mevcut alternatifler"},
                {"key": "expected_price", "type": "str",       "required": False, "desc": "Fiyat modeli / aralığı"},
                {"key": "sales_channel",  "type": "str",       "required": False, "desc": "Satış kanalı (web, mobil, mağaza vb.)"},
                {"key": "success_metric", "type": "str",       "required": False, "desc": "Araştırmanın başarı kriteri"},
                {"key": "variant_a",      "type": "str",       "required": False, "desc": "[A/B Test] Varyant A metni"},
                {"key": "variant_b",      "type": "str",       "required": False, "desc": "[A/B Test] Varyant B metni"},
            ],
            "defaults": brief_defaults,
        },
        "persona_schema": {
            "description": "LLM persona üretim şablonu — workflow.py generate_personas_from_roles()",
            "fields": [
                {"key": "name",               "type": "str",       "desc": "Türkçe isim"},
                {"key": "age",                "type": "int",       "desc": "Yaş (18-65)"},
                {"key": "city",               "type": "str",       "desc": "Türkiye şehri"},
                {"key": "segment",            "type": "str",       "desc": "Pazar segmenti"},
                {"key": "stance",             "type": "enum",      "desc": "Champion | Pragmatist | Skeptic | Blocker | Observer"},
                {"key": "price_sensitivity",  "type": "int 1-10",  "desc": "Fiyat hassasiyeti"},
                {"key": "digital_confidence", "type": "int 1-10",  "desc": "Dijital özgüven"},
                {"key": "context",            "type": "str",       "desc": "Persona bağlamı"},
                {"key": "goals",              "type": "list[str]", "desc": "Kısa vadeli hedefler"},
                {"key": "objections",         "type": "list[str]", "desc": "Ürüne itirazları"},
                {"key": "knowledge_boundary", "type": "str",       "desc": "Bilgi sınırı"},
                {"key": "bio",                "type": "str",       "desc": "Kısa hikaye"},
            ],
        },
        "interview_schema": {
            "description": "Her persona-soru turunda modele iletilen prompt değişkenleri",
            "prompt_variables": [
                "brief.idea", "brief.target_users", "persona.name", "persona.age",
                "persona.city", "persona.segment", "persona.stance",
                "persona.price_sensitivity", "persona.digital_confidence",
                "persona.context", "persona.goals", "persona.objections",
                "persona.knowledge_boundary", "question.label", "question.question",
            ],
            "output": {
                "question":      "str — Sorulan mülakat sorusu",
                "answer":        "str — Personanın cevabı",
                "tags":          "list[str] — pain_point | value | objection | pricing | positioning | risk",
                "model_id":      "str — Yanıtı üreten model",
                "quality_flags": "list[str] — meta_tone | visible_reasoning | too_short | weak_skepticism | ...",
            },
        },
        "synthesis_schema": {
            "description": "Sentez raporuna giden veri — analytics.py synthesize_report()",
            "inputs": ["ResearchBrief", "ResearchPlan", "list[Persona]", "list[PersonaInterview]"],
            "output_fields": [
                "executive_summary", "findings", "pricing", "pain_point_matrix",
                "action_items", "quality_issues", "recommendations",
                "validation_next_steps", "limitations", "model_usage",
            ],
        },
        "default_interview_questions": db_questions,
        "concept_pools": {
            name: {
                "persona_name": pool["persona_name"],
                "focus_areas":  pool["focus_areas"],
                "questions":    pool["questions"],
            }
            for name, pool in CONCEPT_POOLS.items()
        },
    }

@router.put("/schemas/brief-defaults")
async def update_brief_defaults(data: dict):
    """Brief varsayılan değerlerini system_config'e kaydeder."""
    allowed = {"default_market", "default_category", "default_expected_price",
               "default_sales_channel", "default_success_metric"}
    for key, value in data.items():
        if key in allowed:
            update_system_config(key, str(value))
    return {"status": "success"}

@router.put("/schemas/interview-questions")
async def update_interview_questions(data: DefaultQuestionsUpdate):
    """Varsayılan mülakat sorularını system_config'e JSON olarak kaydeder."""
    import json
    update_system_config("default_interview_questions", json.dumps(data.questions, ensure_ascii=False))
    return {"status": "success"}


@router.get("/plan-config")
async def get_plan_config_endpoint():
    """Plan konfigürasyonunu JSON olarak döner.
    Frontend bu endpoint'i kullanarak PLAN_ORDER ve PLAN_CONFIG'i backend'den çekebilir.
    Bu, frontend-backend duplikasyonunu (R18) ortadan kaldırır."""
    return {
        "plan_order": PLAN_ORDER,
        "plans": {
            name: {
                "max_simulations": cfg["max_simulations"],
                "max_personas":    cfg["max_personas"],
                "max_tokens":      cfg["max_tokens"],
                "features": {k: v for k, v in cfg.items() if isinstance(v, bool)},
            }
            for name, cfg in PLAN_CONFIG.items()
        },
        "feature_min_plan": FEATURE_MIN_PLAN,
    }
