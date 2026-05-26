import os
import re
import json
import logging
from typing import Any
from packages.research_engine.state import GlobalResearchState, JSONParsingException

logger = logging.getLogger(__name__)

def safe_extract_json(model_response: str) -> Any:
    """
    Model yanıtı içerisindeki ilk geçerli JSON bloğunu veya listesini bulur,
    kazara eklenen markdown kod bloklarını ve prose metinleri semantik olarak ayıklar.
    """
    json_match = re.search(r'(\{.*\}|\[.*\])', model_response, re.DOTALL)
    if not json_match:
        raise JSONParsingException("Model çıktısında geçerli hiçbir JSON yapısı tespit edilemedi.")
    
    try:
        clean_json_str = json_match.group(1)
        return json.loads(clean_json_str)
    except json.JSONDecodeError as je:
        raise JSONParsingException(f"Ayıklanan JSON bloğu parse edilemedi (Malformed Schema): {str(je)}")

def publish_live_status(state: GlobalResearchState, pipeline_node_info: str):
    """Ön yüz progressive loading bileşenlerini asenkron besleyen Redis Pub/Sub motoru."""
    try:
        import redis
        # Valkey / Redis URL çevre değişkeni optimizasyonu
        r = redis.from_url(os.getenv("VALKEY_URL", "redis://localhost:6379/0"))
        research_id = state.get("research_id")
        if not research_id:
            return
            
        channel = f"synthesis_status:{research_id}"
        payload = {
            "research_id": research_id,
            "status": state.get("status"),
            "node": pipeline_node_info,
            "metrics": {
                "personas_count": len(state.get("allocated_personas", [])),
                "transcripts_count": len(state.get("transcripts", [])),
                "themes_count": len(state.get("extracted_themes", []))
            }
        }
        r.publish(channel, json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Redis durum yayını başarısız (UX progressive loading kesildi): {e}")
