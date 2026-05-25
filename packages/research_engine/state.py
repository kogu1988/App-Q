import logging
from typing import Any, TypedDict, List, Dict, Optional

logger = logging.getLogger(__name__)

# --- HATA YÖNETİMİ İSTİSNALARI ---
class PrivacyFilterException(Exception):
    """NER güvenlik filtresi çöktüğünde PII sızıntısını önlemek için fırlatılan katı istisna."""
    pass

class JSONParsingException(Exception):
    """Model çıktısından geçerli bir JSON şeması ayıklanamadığında fırlatılan istisna."""
    pass

# --- GLOBAL LANGGRAPH STATE ---
class GlobalResearchState(TypedDict):
    research_id: str
    status: str                         # "in_progress", "completed", "failed"
    error_message: Optional[str]
    
    # Giriş Fazı (Ajan 1) Verileri
    raw_idea: str                       # Kullanıcıdan gelen ham metin
    sanitized_idea: str                 # PII Scrubber'dan geçmiş temiz metin
    objective_context: Dict[str, Any]   # Reframed Sokratik bağlam ve nesnel sorular
    allocated_personas: List[Dict]      # Rogers x TÜAD Matrisinden çıkan tamsayı kotalar
    
    # Görüşme Fazı (Ajan 2) Verileri
    transcripts: List[Dict]             # [{"persona_id": "...", "transcript": "..."}]
    
    # Analiz ve İnceleme Fazı (Ajan 3) Verileri
    atomic_codes: List[Dict]            # Kodlama fazından çıkan doğrulanmış kod haritası
    extracted_themes: List[Dict]        # Braun & Clarke sentezinden süzülen kanıt zincirli temalar
    final_report: str                   # Çekişmeli denetimden geçmiş nihai Markdown rapor
    confidence_score: float             # Maksimum 0.75 yasal/bilimsel güven sınırı
    
    # Döngü Denetimleri
    adversarial_loops_count: int
    max_adversarial_loops: int
