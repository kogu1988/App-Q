import logging
from typing import Any, Dict
from packages.research_engine.state import GlobalResearchState
from packages.research_engine.providers import get_model_provider
from packages.research_engine.utils import publish_live_status

# Try to import from workflow, if missing use a fallback
try:
    from packages.research_engine.workflow import build_elephant_system_prompt
except ImportError:
    def build_elephant_system_prompt(persona):
        return f"Sen {persona.name} adında bir kullanıcısın. Duruşun: {persona.stance}. (ELEPHANT Anti-Sycophancy Modu)"

logger = logging.getLogger(__name__)

async def hypothesis_blind_simulation_node(state: GlobalResearchState) -> Dict[str, Any]:
    logger.info("Ajan 2: Sanal Kohort Görüşme Döngüsü Başlatıldı.")
    
    allocated_personas = state.get("allocated_personas", [])
    objective_context = state.get("objective_context", {})
    objective_questions = objective_context.get("primary_research_questions", [])
    product_definition = objective_context.get("objective_product_context", state.get("sanitized_idea", ""))
    
    # Hafif mülakat SLM motoru
    interview_model = get_model_provider("app-q-kara-kumru")
    simulated_transcripts = []
    
    # Donanım darboğazını (8GB VRAM) yönetmek adına mülakatları sıralı asenkron havuzda işliyoruz
    for idx, persona_meta in enumerate(allocated_personas):
        # Sahte pozitifliği kıran ELEPHANT anti-sycophancy prompt inşası
        from packages.research_engine.models import Persona
        
        # Determine traits safely
        traits = persona_meta.get("big_five_constraints", {})
        
        p_obj = Persona(
            id=f"p_{idx}", 
            name=f"Katılımcı_{idx}", 
            stance=persona_meta.get("stance", "Observer"), 
            traits=traits, 
            ses_group=persona_meta.get("ses_group", "C1")
        )
        system_instruction = build_elephant_system_prompt(p_obj)
        
        conversation_history = []
        for question in objective_questions:
            prompt = f"Ürün Saf Bağlamı: {product_definition}\nSoru: {question}\nCevap ver (2-4 cümle, Sokratik kal):"
            try:
                answer = interview_model.generate(system=system_instruction, prompt=prompt)
                conversation_history.append(f"Soru: {question}\nCevap: {answer}")
            except Exception as e:
                logger.error(f"Görüşme hatası (Persona {idx}): {e}")
                conversation_history.append(f"Soru: {question}\nCevap: [Yanıt alınamadı]")
            
        simulated_transcripts.append({
            "persona_id": p_obj.id,
            "stance": p_obj.stance,
            "ses_group": p_obj.ses_group,
            "full_dialogue": "\n".join(conversation_history)
        })
        
    # Belleği tahliye et (VRAM Flush)
    if hasattr(interview_model, "free_memory"):
        interview_model.free_memory()
        
    updates = {"transcripts": simulated_transcripts}
    
    temp_state = dict(state)
    temp_state.update(updates)
    publish_live_status(temp_state, "simulation_completed")
    
    return updates
