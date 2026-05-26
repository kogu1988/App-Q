import math
import random
from typing import List, Any

def calculate_act_r_memory_prompt(turns: List[Any], script_question: Any) -> str:
    """ACT-R base-level learning model with working memory (Cowan's limit = 4 items).
    Computes mathematical memory activation based on time decay:
    A_i = ln(sum_j (t - t_j)^-0.5) + cue_overlap + epsilon
    """
    if not turns:
        return ""
        
    current_turn_index = len(turns)
    activations = []
    
    for j, t in enumerate(turns):
        time_diff = current_turn_index - j
        # Base level learning decay (d = 0.5)
        base_learning = math.log(time_diff ** -0.5)
        
        current_tags = getattr(script_question, "tags", []) or []
        past_tags = getattr(t, "tags", []) or []
        
        # Cue-based retrieval activation
        cue_overlap = 0.5 if any(tag in past_tags for tag in current_tags) else 0.0
        
        # Stochastic noise
        epsilon = random.uniform(-0.05, 0.05)
        
        a_i = base_learning + cue_overlap + epsilon
        activations.append((a_i, t))
    
    # Cowan working memory limit: top 4 active memories are kept in focus
    active_turns = sorted(activations, key=lambda x: x[0], reverse=True)[:4]
    
    weighted_lines = []
    for a_i, t in reversed(active_turns):
        t_tags = getattr(t, "tags", [])
        tag = t_tags[0] if t_tags else "?"
        
        # Adjust fidelity based on decay level
        length = 80 if a_i > -1.0 else 40
        answer_text = getattr(t, "answer", "")
        weighted_lines.append(
            f"[{tag}, Aktivasyon={a_i:.2f}] {answer_text[:length].strip()}..."
        )
        
    return "\nACT-R Bellek (En Aktif Sönümlü Anılar):\n" + "\n".join(weighted_lines)
