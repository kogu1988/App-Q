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
    
    # Mülakat modeli (DeepSeek Flash)
    interview_model = get_model_provider("flash", effort="high")
    simulated_transcripts = []
    
    # Donanım darboğazını (8GB VRAM) yönetmek adına mülakatları sıralı asenkron havuzda işliyoruz
    for idx, persona_meta in enumerate(allocated_personas):
        # Sahte pozitifliği kıran ELEPHANT anti-sycophancy prompt inşası
        from packages.research_engine.models import Persona
        from packages.research_engine.workflow import persona_traits

        stance = persona_meta.get("stance", "Observer")
        ses_group = persona_meta.get("ses_group", "C1")
        price_sensitivity = int(persona_meta.get("price_sensitivity", 5))
        digital_confidence = int(persona_meta.get("digital_confidence", 6))
        # Big Five domain skorları (radar grafiği + ELEPHANT kalibrasyonu için sayısal)
        big_five = persona_meta.get("big_five") or persona_traits(
            idx, stance, price_sensitivity, digital_confidence
        )

        # Not: matris yalnızca stance/ses/big_five_constraints üretir; Persona'nın
        # zorunlu alanları burada makul varsayımlarla doldurulur (aks/i akışta
        # Persona.__init__ eksik argüman hatası veriyordu).
        p_obj = Persona(
            id=f"p_{idx}",
            name=f"Katılımcı_{idx}",
            age=int(persona_meta.get("age", 32)),
            city=persona_meta.get("city", "İstanbul"),
            segment=persona_meta.get("segment", ses_group),
            stance=stance,
            price_sensitivity=price_sensitivity,
            digital_confidence=digital_confidence,
            context=(product_definition or "")[:300],
            goals=[],
            objections=[],
            knowledge_boundary="orta",
            traits=big_five,
            big_five=big_five,
            ses_group=ses_group,
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
