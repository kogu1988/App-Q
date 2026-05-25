import hashlib
from typing import Dict, Any
from .celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

class ResearchInflowGateway:
    def __init__(self, db_session=None):
        self.db = db_session

    def generate_question_hash(self, product_context: str, category: str, pricing: str) -> str:
        """Aynı sorunun 2x simüle edilmesini engelleyen Context Isolation bileşeni"""
        raw_string = f"{product_context.strip().lower()}_{category}_{pricing}"
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    def enforce_regulatory_rules(self, category: str) -> Dict[str, Any]:
        """Kategoriye göre sistem promptuna otomatik yasal kısıt enjekte eden süreçsel hafıza"""
        base_rules = {
            "bddk_max_installments": 12,
            "shipping_sensitivity": True,
            "haggling_allowed": True
        }
        category_lower = category.lower()
        if "elektronik" in category_lower:
            base_rules["bddk_max_installments"] = 4
        elif "seyahat" in category_lower or "havayolu" in category_lower:
            base_rules["bddk_max_installments"] = 0
        elif "evcil_hayvan" in category_lower or "pet" in category_lower:
            base_rules["bddk_max_installments"] = 12
        return base_rules

    def input_reframing_layer(self, user_brief: str) -> str:
        """ELEPHANT Algoritması: Kullanıcının onaylanma arayışını nesnel forma çevirir"""
        # Kullanıcının aşırı kesinlik içeren ifadelerini filtreleyip nesnel bir soruya çevirir.
        from .intake import reframe_user_input
        reframed_text, was_reframed = reframe_user_input(user_brief)
        
        # Eğer reframe yapılamadıysa veya ek bir genel bariyer sorusu eklemek istiyorsak:
        if not was_reframed:
            reframed_text = f"'{user_brief}' konseptinin pazar bariyerleri, riskleri ve kullanıcı nezdindeki gerçek sürtünme noktaları nelerdir?"
            
        return reframed_text

    async def trigger_simulation_triage(self, username: str, brief: str, category: str, pricing: str, panel_roles: list[dict] = None, max_adversarial_loops: int = 1):
        """Asenkron simülasyon kuyruğunu başlatır"""
        
        # 0. Aşama: Deterministik PII (Kişisel Veri) Maskeleme
        from .privacy import LocalPIIScrubber, PrivacyFilterException
        try:
            scrubber = LocalPIIScrubber()
            sanitized_output = await scrubber.sanitize_input(brief)
            safe_brief = sanitized_output.sanitized_text
        except PrivacyFilterException as e:
            logger.error(f"PII Filter blocked simulation triage: {e}")
            return {
                "status": "failed",
                "message": "Sistem geçici bir güvenlik filtrelemesi hatası aldı. Lütfen tekrar deneyiniz.",
                "error_code": "PII_FILTER_FAILURE"
            }
        
        question_hash = self.generate_question_hash(safe_brief, category, pricing)
        
        # 1. Aşama: Cache Kontrolü
        if self.db:
            # PostgreSQL ile cache kontrolü
            with self.db() as (conn, cur):
                cur.execute("SELECT json_data FROM interview_responses WHERE hash = %s AND username = %s", (question_hash, username))
                row = cur.fetchone()
                if row:
                    return {"status": "success", "source": "cache", "data": row["json_data"]}
            
        # 2. Aşama: Kuralları ve Nesnel Çerçeveyi Hazırla
        regulatory_context = self.enforce_regulatory_rules(category)
        objective_question = self.input_reframing_layer(safe_brief)
        
        logger.info("⚠️ Research quality için mülakat tek turlu kısıtlanmıştır. Analiz başlıyor...")
        
        payload = {
            "hash": question_hash,
            "username": username,
            "original_brief": safe_brief,
            "question": objective_question,
            "rules": regulatory_context,
            "category": category,
            "pricing": pricing,
            "panel_roles": panel_roles,
            "pii_context": sanitized_output.context.model_dump(), # Kaydet ama LLM görmesin
            "max_adversarial_loops": max_adversarial_loops
        }
        
        # Celery görevini tetikle
        task = run_simulation_task.delay(payload)
        
        return {
            "status": "queued", 
            "message": "Simülasyon paneli asenkron olarak başlatıldı.", 
            "task_id": task.id,
            "payload": payload
        }


@celery_app.task(bind=True, max_retries=3)
def run_simulation_task(self, payload: dict):
    """Celery üzerinde çalışacak asıl simülasyon görevi."""
    logger.info(f"Starting async simulation task for hash: {payload.get('hash')}")
    try:
        import time
        import uuid
        from dataclasses import asdict
        from .database import get_db, save_study
        from .providers import get_model_provider
        from .workflow import run_research
        from .models import ResearchBrief, PanelRole

        # 1. Brief Oluştur
        brief = ResearchBrief(
            title=f"Araştırma: {payload.get('original_brief')[:30]}...",
            market="Türkiye",
            category=payload.get("category"),
            idea=payload.get("original_brief"),
            questions=[payload.get("question")]
        )
        
        # 1.5 Parse Panel Roles
        raw_roles = payload.get("panel_roles")
        panel_roles_obj = None
        if raw_roles and isinstance(raw_roles, list):
            panel_roles_obj = [
                PanelRole(role=r.get("role"), why=r.get("why"), count=int(r.get("count", 1)))
                for r in raw_roles if r.get("role")
            ]
        
        # 2. Araştırmayı Modüler LangGraph Üzerinden Başlat (Ajan 1 -> Ajan 2 -> Ajan 3)
        from .graph import app_q_orchestrator
        import asyncio
        
        study_id = str(uuid.uuid4())
        initial_state = {
            "research_id": study_id,
            "raw_idea": payload.get("original_brief", ""),
            "status": "pending",
            "adversarial_loops_count": 0,
            "max_adversarial_loops": 2
        }
        
        # Invoke is async, so we use asyncio.run in the celery worker
        final_state = asyncio.run(app_q_orchestrator.ainvoke(initial_state))
        
        if final_state.get("status") == "failed":
            raise Exception(f"Super-Graph failed: {final_state.get('error_message')}")
            
        rfi_score = final_state.get("confidence_score", 0.75)
        metadata = {
            "id": study_id,
            "title": "Araştırma Sonucu",
            "category": payload.get("category"),
            "has_report": True,
            "quality_score": int(rfi_score * 100),
            "quality_grade": "A" if rfi_score >= 0.8 else "B",
            "quality_summary": "Simülasyon başarıyla tamamlandı (Modüler Super-Graph)."
        }
        
        # Modüler mimariden gelen dictionary'i kaydediyoruz
        study_payload = {
            "brief": {
                "content": payload.get("original_brief"),
                "brand": "Genel Fikir",
                "budget": "Belirtilmedi",
                "context": payload.get("original_brief")
            },
            "plan": final_state.get("objective_context"),
            "personas": final_state.get("allocated_personas"),
            "interviews": final_state.get("transcripts"),
            "report_markdown": final_state.get("final_report"),
            "ses_cross_tab": {},
            "respondent_type_summary": {},
            "brand_health": {},
            "channel_map": {},
            "research_quality": {"rfi": rfi_score}
        }

        
        save_study(metadata, study_payload)
        
        # Cache'e kaydetme (opsiyonel ama gateway oradan okuyor)
        result_data = {"study_id": study_id, "status": "completed"}
        with get_db() as (conn, cur):
            cur.execute(
                """
                INSERT INTO interview_responses (hash, username, persona_id, question, json_data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (hash) DO NOTHING
                """,
                (
                    payload.get("hash"),
                    payload.get("username"),
                    "anchor_persona_01", # Placeholder
                    payload.get("question"),
                    json.dumps(result_data)
                )
            )
            
        return result_data
        
    except Exception as exc:
        logger.error(f"Error in simulation task: {exc}")
        raise self.retry(exc=exc, countdown=10)

@celery_app.task(bind=True, max_retries=1)
def run_thematic_synthesis_task(self, research_id: str, transcripts: list[dict], max_adversarial_loops: int = 1):
    """
    Celery task that runs the LangGraph Braun & Clarke 6-Stage Thematic Synthesis Pipeline.
    It publishes its progress to Redis for the WebSocket Progressive Loading UX.
    """
    logger.info(f"Starting async thematic synthesis task for research_id: {research_id}")
    try:
        from packages.research_engine.synthesis_pipeline import run_thematic_synthesis
        
        # Execute the LangGraph pipeline
        final_state = run_thematic_synthesis(
            research_id=research_id, 
            transcripts=transcripts, 
            max_adversarial_loops=max_adversarial_loops
        )
        
        return {
            "status": "success",
            "research_id": research_id,
            "final_report": final_state.get("final_report")
        }
    except Exception as exc:
        logger.error(f"Error in thematic synthesis task: {exc}")
        
        # Publish failed state to Redis so frontend can stop loading
        from packages.research_engine.synthesis_pipeline import publish_state
        publish_state({
            "research_id": research_id,
            "status": "failed",
            "current_stage": 0
        })
        
        raise self.retry(exc=exc, countdown=5)
