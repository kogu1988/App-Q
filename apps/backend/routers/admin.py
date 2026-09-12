from fastapi import APIRouter, HTTPException, Depends, Header, Response, Request
from pydantic import BaseModel
from typing import Optional, List
import hmac
import logging
import os
from packages.research_engine.database import (
    get_system_config, get_feedbacks, get_audit_logs, update_system_config, get_db,
    get_token_usage_summary,
)
from packages.research_engine.db_auth import (
    get_clients, add_client, update_client, delete_client
)
from packages.research_engine.db_vectors import (
    get_personas_pool, get_question_collection, update_question_liked_status,
    update_question_purpose, delete_from_question_collection
)
from packages.research_engine.plan_config import PLAN_CONFIG, PLAN_ORDER, FEATURE_MIN_PLAN

logger = logging.getLogger(__name__)


def _get_admin_key() -> str:
    """ADMIN_SECRET_KEY'i her çağrıda taze oku.

    Import anında okumak, runtime'da set edilen değerin görülmemesine yol açıyordu.
    """
    return os.getenv("ADMIN_SECRET_KEY", "")


def require_admin(request: Request, x_admin_key: str = Header(default="")) -> None:
    """Admin endpoint koruyucu dependency.

    - Production'da ADMIN_SECRET_KEY yoksa erişim verilmez (503).
    - Anahtar karşılaştırması timing-safe (`hmac.compare_digest`).
    - Başarısız denemeler audit log'a yazılır.
    """
    admin_key = _get_admin_key()
    app_env = os.getenv("APP_ENV", "development").lower()

    if not admin_key:
        if app_env == "production":
            raise HTTPException(
                status_code=503,
                detail="Admin API yapılandırılmamış (ADMIN_SECRET_KEY eksik).",
            )
        logger.warning("ADMIN_SECRET_KEY yok — admin API geliştirme modunda korumasız.")
        return

    if not hmac.compare_digest(x_admin_key or "", admin_key):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning("Başarısız admin girişi: ip=%s", client_ip)
        try:
            from packages.research_engine.database import log_audit
            log_audit("admin-api", "-", f"Geçersiz admin anahtarı (ip={client_ip})", "403 Forbidden")
        except Exception:
            logger.debug("Admin audit log yazılamadı.", exc_info=True)
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

class GeneratePersonaRequest(BaseModel):
    role_title: str
    count: int
    category: Optional[str] = "genel"
    market: Optional[str] = "Türkiye"
    target_users: Optional[str] = "genel tüketici"
    why: Optional[str] = "Hedef kitle temsilcisi"
    save_to_pool: Optional[bool] = True
    negative_targeting: Optional[str] = ""

class BulkAddPersonasRequest(BaseModel):
    personas: List[dict]

class ManualPersonaCreate(BaseModel):
    name: str
    age: int
    city: str
    segment: str
    role_title: Optional[str] = None
    respondent_type: Optional[str] = "potential_customer"
    settlement_type: Optional[str] = "kentsel"
    stance: Optional[str] = "Mainstream"
    ses_group: Optional[str] = "C1"
    price_sensitivity: Optional[int] = 5
    digital_confidence: Optional[int] = 6
    is_global: Optional[bool] = True
    bio: Optional[str] = ""
    traits: Optional[dict] = None
    attributes: Optional[dict] = None
    goals: Optional[List[str]] = None
    objections: Optional[List[str]] = None
    pazarlik_propensity: Optional[float] = 0.5
    taksit_preference: Optional[bool] = True
    sor_osca_threshold: Optional[float] = 0.5
    credit_card_limit_doluluk: Optional[float] = 0.5
    neo_facets: Optional[dict] = None


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

@router.post("/personas/generate")
async def generate_personas_endpoint(req: GeneratePersonaRequest):
    from packages.research_engine.persona_generator import generate_and_save_personas
    from packages.research_engine.providers import get_model_provider
    
    model = get_model_provider()
    
    personas = generate_and_save_personas(
        role_title=req.role_title,
        count=req.count,
        model=model,
        category=req.category,
        market=req.market,
        target_users=req.target_users,
        why=req.why,
        save_to_pool=req.save_to_pool,
        negative_targeting=req.negative_targeting
    )
    
    return {
        "status": "success", 
        "generated_count": len(personas),
        "personas": [p.model_dump() for p in personas]
    }

@router.post("/personas/bulk-add")
async def bulk_add_personas(req: BulkAddPersonasRequest):
    from packages.research_engine.db_vectors import save_persona_to_pool
    import uuid
    
    saved_count = 0
    for p_dict in req.personas:
        if "id" not in p_dict or not p_dict["id"]:
            p_dict["id"] = f"p_{uuid.uuid4().hex[:8]}"
        # Embedding devre disi (Enterprise'ta geri gelecek)
        save_persona_to_pool(p_dict, embedding=None)
        saved_count += 1
        
    return {"status": "success", "saved_count": saved_count}

@router.get("/personas/draft")
async def get_random_persona_draft():
    from packages.research_engine.persona_generator import generate_random_persona_draft
    from packages.research_engine.providers import get_model_provider
    
    model = get_model_provider()
    
    draft = generate_random_persona_draft(model)
    if not draft:
        raise HTTPException(status_code=500, detail="Taslak persona üretilemedi.")
    return {"status": "success", "draft": draft}

@router.post("/personas/create")
async def create_manual_persona(req: ManualPersonaCreate):
    from packages.research_engine.db_vectors import save_persona_to_pool
    import uuid
    
    p_id = f"p_{uuid.uuid4().hex[:8]}"
    p_dict = req.model_dump()
    p_dict["id"] = p_id
    # Embedding devre disi (Enterprise'ta geri gelecek)
    save_persona_to_pool(p_dict, embedding=None)
    
    return {"status": "success", "persona_id": p_id, "persona": p_dict}


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: str):
    from packages.research_engine.db_vectors import delete_persona_from_pool, get_personas_pool
    personas = get_personas_pool()
    target = None
    for p in personas:
        if p.get("id") == persona_id:
            target = p
            break
            
    if not target:
        raise HTTPException(status_code=404, detail="Persona bulunamadı.")
        
    if target.get("is_locked"):
        raise HTTPException(status_code=400, detail="Bu persona aktif veya tamamlanmış bir araştırmada yer aldığı için silinemez.")
        
    success = delete_persona_from_pool(persona_id)
    if not success:
        raise HTTPException(status_code=500, detail="Silme işlemi gerçekleştirilemedi. Lütfen tekrar deneyin.")
    return {"status": "success", "message": "Persona başarıyla silindi"}

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

@router.get("/fine-tuning/export")
async def export_finetuning_endpoint():
    """Beğenilmiş curated soruları ShareGPT JSONL formatında dışa aktarır (Enterprise fine-tuning verisi)."""
    from packages.research_engine.db_vectors import export_finetuning_data
    data = export_finetuning_data(liked_only=True)
    if not data:
        raise HTTPException(status_code=404, detail="Dışa aktarılacak beğenilmiş soru bulunamadı.")
    return Response(
        content=data,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=clarere-finetuning.jsonl"},
    )


# ─── Multi-User Organizations (Enterprise) ────────────────────────────────────

class OrgCreate(BaseModel):
    org_id: str
    name: str
    plan_type: str = "Enterprise"
    owner_username: str = ""

class OrgMemberAdd(BaseModel):
    org_id: str
    username: str
    role: str = "member"

@router.get("/organizations")
async def list_organizations_endpoint():
    from packages.research_engine.db_org import list_organizations
    return list_organizations()

@router.post("/organizations")
async def create_organization_endpoint(org: OrgCreate):
    from packages.research_engine.db_org import create_organization
    create_organization(org.org_id, org.name, org.plan_type, org.owner_username)
    return {"status": "success", "org_id": org.org_id}

@router.get("/organizations/{org_id}/members")
async def list_organization_members_endpoint(org_id: str):
    from packages.research_engine.db_org import list_organization_members
    return list_organization_members(org_id)

@router.post("/organizations/members")
async def add_organization_member_endpoint(member: OrgMemberAdd):
    from packages.research_engine.db_org import add_organization_member
    add_organization_member(member.org_id, member.username, member.role)
    return {"status": "success"}

@router.delete("/organizations/{org_id}/members/{username}")
async def remove_organization_member_endpoint(org_id: str, username: str):
    from packages.research_engine.db_org import remove_organization_member
    removed = remove_organization_member(org_id, username)
    if not removed:
        raise HTTPException(status_code=404, detail="Üye bulunamadı.")
    return {"status": "success"}


# ─── Metrics ─────────────────────────────────────────────────────────────────

@router.get("/metrics")
async def get_metrics():
    """Token kullanim, model ve simulasyon metriklerini toplu doner."""
    with get_db() as (conn, cur):
        # Per-client token verileri
        cur.execute("""
            SELECT username, plan_type, tokens_used, max_tokens,
                   total_simulations, max_simulations, status, period_simulations
            FROM clients
            ORDER BY tokens_used DESC
        """)
        clients_raw = [dict(r) for r in cur.fetchall()]

        # Plan bazinda dagilim
        cur.execute("""
            SELECT plan_type,
                   COUNT(*)                AS count,
                   SUM(tokens_used)        AS total_tokens,
                   SUM(total_simulations)  AS total_sims
            FROM clients
            GROUP BY plan_type
        """)
        plan_dist = [dict(r) for r in cur.fetchall()]

        # Genel toplamlar
        cur.execute("""
            SELECT COUNT(*)                    AS total_clients,
                   SUM(tokens_used)            AS total_tokens_used,
                   SUM(max_tokens)             AS total_tokens_capacity,
                   SUM(total_simulations)      AS total_simulations
            FROM clients
        """)
        totals = dict(cur.fetchone())

        # Study metrikleri
        cur.execute("""
            SELECT COUNT(*)                                     AS total_studies,
                   AVG(quality_score)                          AS avg_quality,
                   COUNT(CASE WHEN has_report THEN 1 END)      AS with_report,
                   COUNT(CASE WHEN archived THEN 1 END)        AS archived
            FROM studies
        """)
        study_stats = dict(cur.fetchone())

        # Kategori dagilimi
        cur.execute("""
            SELECT category, COUNT(*) AS count
            FROM studies
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            LIMIT 8
        """)
        categories = [dict(r) for r in cur.fetchall()]

        # Hata sayisi
        cur.execute("SELECT COUNT(*) AS error_count FROM audit_logs")
        error_count = cur.fetchone()["error_count"]

        # Persona havuzu istatistikleri
        cur.execute("SELECT COUNT(*) AS total FROM personas_pool")
        persona_total = cur.fetchone()["total"]

        cur.execute("""
            SELECT name, stance, ses_group, usage_count, created_at
            FROM personas_pool
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        top_personas = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT stance, COUNT(*) AS count
            FROM personas_pool
            GROUP BY stance
            ORDER BY count DESC
        """)
        persona_stances = [dict(r) for r in cur.fetchall()]

    config = get_system_config()
    active_models = {
        "b2c": config.get("b2c_model", "—"),
        "b2b": config.get("b2b_model", "—"),
        "orchestrator": config.get("orchestrator_model", "—"),
    }

    return {
        "totals": {
            "clients":           int(totals.get("total_clients") or 0),
            "tokens_used":       int(totals.get("total_tokens_used") or 0),
            "tokens_capacity":   int(totals.get("total_tokens_capacity") or 0),
            "simulations":       int(totals.get("total_simulations") or 0),
        },
        "plan_distribution": plan_dist,
        "clients":           clients_raw,
        "study_stats": {
            "total":       int(study_stats.get("total_studies") or 0),
            "avg_quality": round(float(study_stats.get("avg_quality") or 0), 1),
            "with_report": int(study_stats.get("with_report") or 0),
            "archived":    int(study_stats.get("archived") or 0),
            "error_count": int(error_count or 0),
        },
        "categories": categories,
        "models":     active_models,
        "persona_pool": {
            "total": int(persona_total or 0),
            "top_used": top_personas,
            "stances": persona_stances,
        },
    }


# ─── Agent Schemas & Template Management ──────────────────────────────────────

@router.get("/schemas")
async def get_agent_schemas():
    """Tum ajanlarin bekledigı JSON semalari, varsayilan sorular ve concept pool'lari doner."""
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
            "description": "Defne ajanina iletilen arastirma brief'i yapisi",
            "fields": [
                {"key": "title",          "type": "str",       "required": True,  "desc": "Calismanin kisa adi"},
                {"key": "market",         "type": "str",       "required": False, "desc": "Hedef pazar (varsayilan: Türkiye)"},
                {"key": "category",       "type": "str",       "required": False, "desc": "Ürün/hizmet kategorisi"},
                {"key": "idea",           "type": "str",       "required": True,  "desc": "Ürün fikri ve cozulen problem"},
                {"key": "target_users",   "type": "list[str]", "required": False, "desc": "Hedef kullanici segmentleri"},
                {"key": "questions",      "type": "list[str]", "required": False, "desc": "Arastirmada yanitlanacak sorular"},
                {"key": "competitors",    "type": "list[str]", "required": False, "desc": "Rakipler ve mevcut alternatifler"},
                {"key": "expected_price", "type": "str",       "required": False, "desc": "Fiyat modeli / araligi"},
                {"key": "sales_channel",  "type": "str",       "required": False, "desc": "Satis kanali (web, mobil, magaza vb.)"},
                {"key": "success_metric", "type": "str",       "required": False, "desc": "Arastirmanin basari kriteri"},
                {"key": "variant_a",      "type": "str",       "required": False, "desc": "[A/B Test] Varyant A metni"},
                {"key": "variant_b",      "type": "str",       "required": False, "desc": "[A/B Test] Varyant B metni"},
            ],
            "defaults": brief_defaults,
        },
        "persona_schema": {
            "description": "LLM persona uretim sablonu — workflow.py generate_personas_from_roles()",
            "fields": [
                {"key": "name",               "type": "str",       "desc": "Türkce isim"},
                {"key": "age",                "type": "int",       "desc": "Yas (18-65)"},
                {"key": "city",               "type": "str",       "desc": "Türkiye sehri"},
                {"key": "segment",            "type": "str",       "desc": "Pazar segmenti"},
                {"key": "stance",             "type": "enum",      "desc": "Champion | Pragmatist | Skeptic | Blocker | Observer"},
                {"key": "price_sensitivity",  "type": "int 1-10",  "desc": "Fiyat hassasiyeti"},
                {"key": "digital_confidence", "type": "int 1-10",  "desc": "Dijital ozguven"},
                {"key": "context",            "type": "str",       "desc": "Persona baglamı"},
                {"key": "goals",              "type": "list[str]", "desc": "Kisa vadeli hedefler"},
                {"key": "objections",         "type": "list[str]", "desc": "Urune itirazlari"},
                {"key": "knowledge_boundary", "type": "str",       "desc": "Bilgi siniri"},
                {"key": "bio",                "type": "str",       "desc": "Kisa hikaye"},
            ],
        },
        "interview_schema": {
            "description": "Her persona-soru turunda modele iletilen prompt degiskenleri",
            "prompt_variables": [
                "brief.idea", "brief.target_users", "persona.name", "persona.age",
                "persona.city", "persona.segment", "persona.stance",
                "persona.price_sensitivity", "persona.digital_confidence",
                "persona.context", "persona.goals", "persona.objections",
                "persona.knowledge_boundary", "question.label", "question.question",
            ],
            "output": {
                "question":      "str — Sorulan mulakat sorusu",
                "answer":        "str — Personanin cevabi",
                "tags":          "list[str] — pain_point | value | objection | pricing | positioning | risk",
                "model_id":      "str — Yaniti ureten model",
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
    """Brief varsayilan degerlerini system_config'e kaydeder."""
    allowed = {"default_market", "default_category", "default_expected_price",
               "default_sales_channel", "default_success_metric"}
    for key, value in data.items():
        if key in allowed:
            update_system_config(key, str(value))
    return {"status": "success"}

@router.put("/schemas/interview-questions")
async def update_interview_questions(data: DefaultQuestionsUpdate):
    """Varsayilan mulakat sorularini system_config'e JSON olarak kaydeder."""
    import json
    update_system_config("default_interview_questions", json.dumps(data.questions, ensure_ascii=False))
    return {"status": "success"}


@router.get("/plan-config")
async def get_plan_config_endpoint():
    """Plan konfigurasyonunu JSON olarak doner."""
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


@router.get("/usage")
async def get_usage_summary(
    username: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """Kullanıcı bazlı token ve maliyet özeti (P0-6).

    Query paramları: username, start (ISO tarih), end (ISO tarih).
    """
    try:
        return {"usage": get_token_usage_summary(username=username, start=start, end=end)}
    except Exception as e:
        logger.error("Kullanım özeti alınamadı: %s", e)
        raise HTTPException(status_code=500, detail="Kullanım özeti alınamadı.")

