import logging
from langgraph.graph import StateGraph, START, END

from packages.research_engine.state import GlobalResearchState
from packages.research_engine.nodes.intake import async_intake_and_reframing_node
from packages.research_engine.nodes.simulation import hypothesis_blind_simulation_node
from packages.research_engine.nodes.synthesis import (
    initial_coding_node,
    generating_and_reviewing_themes_node,
    adversarial_quality_audit_node
)

logger = logging.getLogger(__name__)

def route_adversarial_decision(state: GlobalResearchState) -> str:
    """Ajan 3 denetiminden geçemeyen sahte pozitif raporları geri döndüren algoritmik kapı."""
    if state.get("is_rejected"):
        loops = state.get("adversarial_loops_count", 0)
        max_loops = state.get("max_adversarial_loops", 2)
        
        if loops < max_loops:
            logger.warning(f"Çekişmeli İnceleme Raporu Reddetti (Dalkavukluk Saptandı). Döngü {loops}/{max_loops}. Yeniden kodlamaya dönülüyor.")
            return "initial_coding" # Güvenli bir şekilde kodlama düğümüne geri dön
        else:
            logger.error(f"DONANIM GÜVENLİK BARİYERİ: Maksimum Çekişmeli İnceleme Sınırı ({max_loops}) aşıldı. VRAM tükenmesini önlemek için sonlandırılıyor.")
            return END
    return END

# --- MOTORUN DERLENMESİ (COMPILATION) ---
workflow = StateGraph(GlobalResearchState)

# Düğümler Graf Yapısına Kaydediliyor
workflow.add_node("intake_reframing", async_intake_and_reframing_node)
workflow.add_node("simulation", hypothesis_blind_simulation_node)
workflow.add_node("initial_coding", initial_coding_node)
workflow.add_node("generating_themes", generating_and_reviewing_themes_node)
workflow.add_node("adversarial_audit", adversarial_quality_audit_node)

# Deterministik İlişki Zincirleri (Linear Path)
workflow.add_edge(START, "intake_reframing")
workflow.add_edge("intake_reframing", "simulation")
workflow.add_edge("simulation", "initial_coding")
workflow.add_edge("initial_coding", "generating_themes")
workflow.add_edge("generating_themes", "adversarial_audit")

# Koşullu Geri Besleme Rotası (Conditional Feedback Loop)
workflow.add_conditional_edges(
    "adversarial_audit",
    route_adversarial_decision,
    {
        "initial_coding": "initial_coding", # Kalite düşükse Aşama 2'ye geri dönüp döngüyü düzeltir
        END: END
    }
)

app_q_orchestrator = workflow.compile()
