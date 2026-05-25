from typing import TypedDict
import json
import logging
import redis
import os

from langgraph.graph import StateGraph, START, END
# VALKEY_URL from celery_app might be circular if we import it, better get from env or duplicate
VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")

logger = logging.getLogger(__name__)

class SynthesisState(TypedDict):
    """
    Braun & Clarke 6-Stage Thematic Synthesis Pipeline State
    """
    research_id: str
    status: str                    # "in_progress", "completed", "failed"
    current_stage: int             # 1 to 6
    quantitative_metrics: dict
    extracted_themes: list[dict]
    transcripts: list[dict]        # [{"persona_id": "...", "transcript": "...", "stance": "...", "ses": "..."}]
    atomic_codes: list[dict]       # [{"code_id": "...", "quote": "...", "semantic_embedding": [...], "persona_id": "..."}]
    themes: list[dict]             # [{"theme_id": "...", "codes": ["code_id_1", ...], "name": ""}]
    evidence_chains: list[dict]    # Mapped from themes and codes
    final_report: str              # Markdown report
    is_rejected: bool              # True if sycophancy detected
    confidence_score: float        # Max 0.75
    adversarial_loops_count: int   # Counter to prevent infinite O(N^2) token generation
    max_adversarial_loops: int     # Bound from the plan

def publish_state(state: dict):
    """
    Publishes the current state to Redis Pub/Sub for progressive loading on the frontend.
    """
    try:
        r = redis.from_url(VALKEY_URL)
        research_id = state.get('research_id')
        if not research_id:
            return
            
        channel = f"synthesis_status:{research_id}"
        
        # Serialize only the fields requested by the frontend
        payload = {
            "research_id": research_id,
            "status": state.get("status", "in_progress"),
            "current_stage": state.get("current_stage", 1),
            "quantitative_metrics": state.get("quantitative_metrics", {}),
            "extracted_themes": state.get("extracted_themes", [])
        }
        
        r.publish(channel, json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Failed to publish state to Redis: {e}")

def familiarization_node(state: SynthesisState):
    logger.info("Stage 1: Familiarization started.")
    transcripts = state.get("transcripts", [])
    if not transcripts:
        logger.warning("No transcripts found for familiarization.")
        
    updates = {"current_stage": 1, "atomic_codes": []}
    state.update(updates)
    publish_state(state)
    return updates

def initial_coding_node(state: SynthesisState):
    logger.info("Stage 2: Initial Coding started.")
    transcripts = state.get("transcripts", [])
    
    from packages.research_engine.providers import get_model_provider
    import uuid
    import json
    model = get_model_provider()
    
    codes = []
    
    system = """
    Sen bir nitel araştırma uzmanısın (Braun & Clarke Aşama 2: Initial Coding).
    Görevin: Verilen mülakat deşifresini okuyup, içindeki en önemli itiraz, ihtiyaç, fiyat bariyeri ve kullanım motivasyonlarını (atomic codes) çıkarmaktır.
    Lütfen her bir kodu kısa ve öz (1-5 kelime) bir tema etiketiyle belirle.
    Çıktını KESİNLİKLE sadece aşağıdaki JSON listesi formatında ver. Başka hiçbir açıklama ekleme.
    
    [
        {
            "quote": "Kullanıcının tam cümlesi (örn: Aylık ödeme yapmak yerine başta toplu öderim.)",
            "theme_tag": "Kısa Kod (örn: Abonelik Direnci)"
        }
    ]
    """
    
    for t_data in transcripts:
        persona_id = t_data.get("persona_id", "unknown")
        transcript_text = t_data.get("transcript", "")
        if not transcript_text:
            continue
            
        prompt = f"Deşifre:\n{transcript_text}"
        try:
            response = model.generate(system, prompt, response_format="json")
            extracted = json.loads(response)
            for item in extracted:
                if "quote" in item and "theme_tag" in item:
                    codes.append({
                        "id": f"code_{uuid.uuid4().hex[:8]}",
                        "persona_id": persona_id,
                        "quote": item["quote"],
                        "theme_tag": item["theme_tag"],
                        "semantic_embedding": [0.0] * 384 # Placeholder for clustering logic
                    })
        except Exception as e:
            logger.error(f"Coding extraction failed for persona {persona_id}: {e}")
            
    updates = {"current_stage": 2, "atomic_codes": codes}
    state.update(updates)
    publish_state(state)
    return updates

def generating_themes_node(state: SynthesisState):
    logger.info("Stage 3: Generating Themes started.")
    codes = state.get("atomic_codes", [])
    
    from packages.research_engine.db_vectors import cluster_atomic_codes
    import uuid

    clusters = cluster_atomic_codes(codes, threshold=0.15)
    
    themes = []
    for i, cluster in enumerate(clusters):
        theme_id = f"THEME_{uuid.uuid4().hex[:8]}"
        themes.append({
            "theme_id": theme_id,
            "codes": [c.get("id") for c in cluster],
            "name": f"Theme Candidate {i+1}",
            "evidence_chains": cluster
        })
    
    updates = {"current_stage": 3, "themes": themes}
    state.update(updates)
    publish_state(state)
    return updates

def reviewing_themes_node(state: SynthesisState):
    logger.info("Stage 4: Reviewing Themes started.")
    updates = {"current_stage": 4}
    state.update(updates)
    publish_state(state)
    return updates

def defining_themes_node(state: SynthesisState):
    logger.info("Stage 5: Defining Themes started.")
    
    themes = state.get("themes", [])
    extracted_themes = []
    for t in themes:
        extracted_themes.append({
            "theme_id": t["theme_id"],
            "title": t["name"],
            "prevalence": 50.0,
            "risk_priority": "MEDIUM",
            "summary": "Taslak tanım",
            "evidence_chain": t["evidence_chains"]
        })
        
    updates = {"current_stage": 5, "is_rejected": False, "extracted_themes": extracted_themes}
    state.update(updates)
    publish_state(state)
    return updates

def adversarial_review_node(state: SynthesisState):
    logger.info("Stage 6: Adversarial Review started.")
    is_rejected = False
    
    # Increment the loop counter
    loops = state.get("adversarial_loops_count", 0) + 1
    
    updates = {
        "current_stage": 6,
        "is_rejected": is_rejected,
        "confidence_score": 0.75,
        "final_report": "Draft Report",
        "adversarial_loops_count": loops
    }
    
    if not is_rejected:
        updates["status"] = "completed"
        
    state.update(updates)
    publish_state(state)
    return updates

def route_adversarial(state: SynthesisState):
    if state.get("is_rejected"):
        loops = state.get("adversarial_loops_count", 0)
        max_loops = state.get("max_adversarial_loops", 1)
        if loops < max_loops:
            logger.warning(f"Adversarial Review rejected the themes (Sycophancy detected). Loop {loops}/{max_loops}. Routing back to Stage 5.")
            return "defining_themes"
        else:
            logger.error(f"HARD LIMIT REACHED: Adversarial Review exceeded {max_loops} loops. Terminating Graph to prevent VRAM depletion.")
            return END
    return END

workflow = StateGraph(SynthesisState)

workflow.add_node("familiarization", familiarization_node)
workflow.add_node("initial_coding", initial_coding_node)
workflow.add_node("generating_themes", generating_themes_node)
workflow.add_node("reviewing_themes", reviewing_themes_node)
workflow.add_node("defining_themes", defining_themes_node)
workflow.add_node("adversarial_review", adversarial_review_node)

workflow.add_edge(START, "familiarization")
workflow.add_edge("familiarization", "initial_coding")
workflow.add_edge("initial_coding", "generating_themes")
workflow.add_edge("generating_themes", "reviewing_themes")
workflow.add_edge("reviewing_themes", "defining_themes")
workflow.add_edge("defining_themes", "adversarial_review")

workflow.add_conditional_edges(
    "adversarial_review",
    route_adversarial,
    {
        "defining_themes": "defining_themes",
        END: END
    }
)

app_synthesis = workflow.compile()

def run_thematic_synthesis(research_id: str, transcripts: list[dict], max_adversarial_loops: int = 1) -> dict:
    """
    Entrypoint for the synthesis pipeline.
    """
    initial_state = {
        "research_id": research_id,
        "status": "in_progress",
        "current_stage": 0,
        "quantitative_metrics": {
            "willingness_to_pay_score": 0.0,
            "overall_cart_abandonment_risk": 0.0,
            "segment_friction_distribution": []
        },
        "extracted_themes": [],
        "transcripts": transcripts,
        "atomic_codes": [],
        "themes": [],
        "evidence_chains": [],
        "final_report": "",
        "is_rejected": False,
        "confidence_score": 0.0,
        "adversarial_loops_count": 0,
        "max_adversarial_loops": max_adversarial_loops
    }
    
    final_state = app_synthesis.invoke(initial_state)
    
    # Final cleanup publish
    final_state["status"] = "completed"
    publish_state(final_state)
    
    return final_state
