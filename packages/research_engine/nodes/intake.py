import logging
from typing import Any, Dict
from packages.research_engine.state import GlobalResearchState, PrivacyFilterException
from packages.research_engine.privacy import LocalPIIScrubber
from packages.research_engine.matrix import allocate_cohort_matrix
from packages.research_engine.providers import get_model_provider
from packages.research_engine.utils import safe_extract_json, publish_live_status
from packages.research_engine.search import search_retriever

logger = logging.getLogger(__name__)

def intake_and_reframing_node(state: GlobalResearchState) -> Dict[str, Any]:
    logger.info("Ajan 1: Giriş ve Regülasyon Katmanı tetiklendi.")
    
    # 1. Katı KVKK Güvenlik Süzgeci (PII Masking)
    scrubber = LocalPIIScrubber()
    try:
        # Actually LocalPIIScrubber.sanitize_input is async, we should either await or run synchronously.
        # Since langgraph nodes can be async or sync, we will make this node async.
        # But wait, the signature provided by the user was `async def intake_and_reframing_node`
        pass
    except Exception as ex:
        raise PrivacyFilterException(f"Lokal NER Güvenlik Modeli yanıt vermiyor. KVKK ihlal riski nedeniyle süreç iptal edildi: {ex}")
        
    return {}

async def async_intake_and_reframing_node(state: GlobalResearchState) -> Dict[str, Any]:
    logger.info("Ajan 1: Giriş ve Regülasyon Katmanı tetiklendi.")
    
    # 1. Katı KVKK Güvenlik Süzgeci (PII Masking)
    scrubber = LocalPIIScrubber()
    try:
        # Yerel SLM (Kara-Kumru-2B) üzerinden PII temizleme çağrısı
        sanitized_out = await scrubber.sanitize_input(state["raw_idea"])
        sanitized_text = sanitized_out.sanitized_text
    except Exception as ex:
        # MODEL ÇÖKERSE YASAL RİSK ALMA, SİSTEMİ DURDUR (FAIL-FAST)
        raise PrivacyFilterException(f"Lokal NER Güvenlik Modeli yanıt vermiyor. KVKK ihlal riski nedeniyle süreç iptal edildi: {ex}")
    
    # Web Arama ile Pazar Analizi (Phase 3 SearXNG Entegrasyonu)
    try:
        search_query = f"{sanitized_text[:50]} pazarı, güncel fiyatlar ve rakipler"
        raw_results = search_retriever.search(query=search_query, limit=3)
        search_context = "\n".join([f"- {r['title']}: {r['content'][:150]}" for r in raw_results]) if raw_results else "Canlı arama sonucu bulunamadı."
    except Exception as e:
        logger.warning(f"Arama motoru entegrasyon hatası (SearXNG): {e}")
        search_context = "Arama yapılamadı."

    # 2. Input Reframing Katmanı (DeepSeek)
    model = get_model_provider("flash")  # Hızlı model — input reframing
    system_prompt = "Sen UK AISI standartlarında bir Girdi Yeniden Çerçeveleme (Input Reframing) modelisin. Girdiyi analiz edip JSON formatında 'objective_product_context' ve 'primary_research_questions' alanlarını döndür."
    user_prompt = f"Brief Fikri: \"{sanitized_text}\"\n\nCanlı Pazar Verisi (Web Search):\n{search_context}\n\nMetni tüm öznel başarı inançlarından arındırıp, canlı pazar verisini de dikkate alarak nesnelleştir."
    
    response = model.generate(system=system_prompt, prompt=user_prompt)
    try:
        objective_context = safe_extract_json(response)
    except Exception as _e:
        logger.warning("JSON parse başarısız, fallback kullanılıyor: %s", _e)
        objective_context = {
            "objective_product_context": sanitized_text,
            "primary_research_questions": ["Bu ürün konseptine dair tüketici bariyerleri nelerdir?"]
        }
        
    # Free VRAM
    if hasattr(model, "free_memory"):
        model.free_memory()
    
    # 3. Deterministik İstatistiksel Kota Tahsisi (Largest Remainder Fonksiyonu)
    # Sabit 15 personalık kararlı bir panel büyüklüğü simüle ediliyor
    try:
        allocated_personas = allocate_cohort_matrix(N=15)
    except Exception as _e:
        logger.warning("allocate_cohort_matrix başarısız, tek-persona fallback kullanılıyor: %s", _e)
        allocated_personas = [
            {"stance": "Skeptic", "ses_group": "DE", "big_five_constraints": {"openness": 30}}
        ]
    
    updates = {
        "sanitized_idea": sanitized_text,
        "objective_context": objective_context,
        "allocated_personas": allocated_personas,
        "status": "in_progress"
    }
    
    # Create temp state to publish
    temp_state = dict(state)
    temp_state.update(updates)
    publish_live_status(temp_state, "intake_completed")
    
    return updates
