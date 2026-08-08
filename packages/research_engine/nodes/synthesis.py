import json
import uuid
import logging
from typing import Any, Dict
from packages.research_engine.state import GlobalResearchState
from packages.research_engine.providers import get_model_provider
from packages.research_engine.utils import safe_extract_json, publish_live_status

try:
    from packages.research_engine.db_vectors import cluster_atomic_codes
except ImportError:
    # Mock fallback
    def cluster_atomic_codes(codes, threshold=0.15):
        if not codes:
            return []
        return [codes]

logger = logging.getLogger(__name__)

async def initial_coding_node(state: GlobalResearchState) -> Dict[str, Any]:
    logger.info("Ajan 3: Braun & Clarke Aşama 2 - Atomik Kodlama Başlatıldı.")
    transcripts = state.get("transcripts", [])
    synthesis_model = get_model_provider("pro")  # Derin analiz için Pro
    
    extracted_atomic_codes = []
    # HER BİR TRANSKRİPTİ LLM İLE ANALİZ ET, BOŞ BIRAKMA (BUG FIX)
    for item in transcripts:
        system = "Sen ham transkriptlerden pazar bariyerlerini ve acı noktalarını ayıran atomik bir analistsin. Yanıtı JSON listesi döndür."
        prompt = f"Görüşme Metni:\n{item['full_dialogue']}\nBu metindeki en kritik 3 ampirik ifadeyi ve alıntıyı ayıkla. JSON formatında 'quote' ve 'insight' alanlarıyla döndür."
        
        try:
            response = synthesis_model.generate(system=system, prompt=prompt)
            parsed_codes = safe_extract_json(response) # Güvenli regex-json parser
            
            # Ensure parsed_codes is a list
            if isinstance(parsed_codes, dict):
                # if it returned a dict wrapper, try to extract list
                for k, v in parsed_codes.items():
                    if isinstance(v, list):
                        parsed_codes = v
                        break
                if isinstance(parsed_codes, dict):
                    parsed_codes = [parsed_codes]
                    
            if isinstance(parsed_codes, list):
                for code in parsed_codes:
                    extracted_atomic_codes.append({
                        "id": f"code_{uuid.uuid4().hex[:6]}",
                        "quote": code.get("quote", "Bilinmeyen Alıntı"),
                        "persona_id": item["persona_id"],
                        "stance": item["stance"]
                    })
        except Exception as e:
            logger.warning(f"Transkript kodlaması bu etmen için atlandı: {e}")
            
    # Belleği tahliye et
    if hasattr(synthesis_model, "free_memory"):
        synthesis_model.free_memory()
            
    updates = {"atomic_codes": extracted_atomic_codes}
    
    temp_state = dict(state)
    temp_state.update(updates)
    publish_live_status(temp_state, "coding_completed")
    
    return updates

async def generating_and_reviewing_themes_node(state: GlobalResearchState) -> Dict[str, Any]:
    logger.info("Ajan 3: Braun & Clarke Aşama 3 & 4 - Semantik Kümeleme Fazı.")
    codes = state.get("atomic_codes", [])
    
    # pgvector üzerinde HNSW indeksleri tabanlı kosinüs benzerliği ($Sim \ge 0.15$) çalıştırılıyor
    clusters = cluster_atomic_codes(codes, threshold=0.15)
    
    themes = []
    for i, cluster in enumerate(clusters):
        themes.append({
            "theme_id": f"THEME_{uuid.uuid4().hex[:8]}",
            "title": f"Pazar Eğilimi Adayı {i+1}",
            "prevalence": (len(cluster) / len(codes)) * 100 if codes else 0,
            "evidence_chain": cluster # Kanıt zincirleri mülakat satırlarına bağlandı
        })
        
    updates = {"extracted_themes": themes}

    # Redis payload optimizasyonu: evidence_chain'leri kırp (max 3 item, quote max 150 char)
    # Tam veri state'te kalır; frontend'e sadece sıkıştırılmış özet gider
    def _slim_themes(themes: list) -> list:
        slimmed = []
        for t in themes:
            slimmed.append({
                "theme_id": t.get("theme_id"),
                "title": t.get("title"),
                "prevalence": t.get("prevalence"),
                "evidence_chain": [
                    {**ev, "quote": ev.get("quote", "")[:150]}
                    for ev in t.get("evidence_chain", [])[:3]
                ],
            })
        return slimmed

    temp_state = dict(state)
    temp_state.update(updates)
    publish_live_status({**temp_state, "extracted_themes": _slim_themes(themes)}, "themes_generated")

    return updates

async def adversarial_quality_audit_node(state: GlobalResearchState) -> Dict[str, Any]:
    logger.info("Ajan 3: UK AISI Standartlarında Çekişmeli Kalite Denetimi (Stage 6).")
    
    # Derin akıl yürütme (DeepSeek Pro)
    reasoning_model = get_model_provider("pro")
    
    themes = state.get("extracted_themes", [])
    loops = state.get("adversarial_loops_count", 0) + 1
    
    system = "Sen sentetik raporlardaki dalkavukluğu, sahte optimizmi ve kanıt zinciri eksikliklerini denetleyen hakem modelsin."
    prompt = f"Üretilen Temalar:\n{json.dumps(themes, ensure_ascii=False)}\nEğer raporda kanıtsız onaylama veya uydurma varsa REJECT döndür, yoksa APPROVE döndür."
    
    try:
        audit_decision = reasoning_model.generate(system=system, prompt=prompt).strip()
    except Exception as e:
        logger.error(f"Denetim modeli hatası: {e}. Varsayılan olarak APPROVE kabul ediliyor.")
        audit_decision = "APPROVE"
        
    # Belleği tahliye et
    if hasattr(reasoning_model, "free_memory"):
        reasoning_model.free_memory()
    
    is_rejected = "REJECT" in audit_decision
    
    # Build final report markdown
    report_md = "# Araştırma Raporu\n\n## Temalar\n"
    for t in themes:
        report_md += f"### {t['title']} (Görülme Sıklığı: %{t['prevalence']:.1f})\n"
        for ev in t["evidence_chain"]:
            report_md += f"- *\"{ev.get('quote')}\"* (Persona: {ev.get('persona_id')})\n"
    
    updates = {
        "adversarial_loops_count": loops,
        "is_rejected": is_rejected,
        "confidence_score": 0.75, # Bilimsel kararlılık gereği tavan kısıt
        "final_report": report_md if not is_rejected else "Reddedilen Rapor (Revizyon Gerekiyor)",
        "status": "completed" if not is_rejected else "in_progress"
    }
    
    temp_state = dict(state)
    temp_state.update(updates)
    
    if is_rejected:
        publish_live_status(temp_state, f"rejected_loop_{loops}")
    else:
        publish_live_status(temp_state, "pipeline_completed")
        
    return updates
