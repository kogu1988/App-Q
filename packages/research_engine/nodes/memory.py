import math
import random
from typing import List, Any, Optional


def calculate_act_r_memory_prompt(turns: List[Any], script_question: Any) -> str:
    """ACT-R base-level learning model with working memory (Cowan's limit = 4 items).
    Computes mathematical memory activation based on time decay:
    A_i = ln(sum_j (t - t_j)^-0.5) + cue_overlap + epsilon

    Egocentric Context Projection (god_doc.md §5):
    Persona'nın kendi cevapları [self] etiketi ile, mülakat sorular [partner]
    etiketi ile işaretlenir. Rol karmaşasını ve geri besleme döngüsünü önler.
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
        question_text = getattr(t, "question", "")

        # Kelime sınırında kırp, '...' izi bırakma
        q_txt = " ".join(question_text.split())
        if len(q_txt) > 60:
            q_txt = q_txt[:60].rsplit(" ", 1)[0]
        a_txt = " ".join(answer_text.split())
        if len(a_txt) > length:
            a_txt = a_txt[:length].rsplit(" ", 1)[0]

        # Egocentric Context Projection: [self] = persona, [partner] = mülakat
        weighted_lines.append(
            f"[partner | {tag}] {q_txt}"
        )
        weighted_lines.append(
            f"[self | {tag} | Akt={a_i:.2f}] {a_txt}"
        )

    return "\nACT-R Bellek (Egocentric — En Aktif Sönümlü Anılar):\n" + "\n".join(weighted_lines)


def summarize_turns_if_needed(turns: List[Any], threshold: int = 10) -> Optional[str]:
    """Her `threshold` turda bir kademeli bellek özetlemesi üretir (god_doc.md §5).

    Hiyerarşik özet: tag dağılımı + ilk cümle. Max ~200 token bütçe.
    Döndüğünde consistency_notes'a ve ACT-R bağlamına enjekte edilir.
    """
    if len(turns) < threshold or len(turns) % threshold != 0:
        return None

    tag_counts: dict = {}
    highlights: List[str] = []

    for t in turns[-threshold:]:
        tags = getattr(t, "tags", []) or []
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        answer = getattr(t, "answer", "")
        first_sentence = answer.split(".")[0].strip()
        if first_sentence:
            highlights.append(f"- {first_sentence[:80]}")

    top_tags = sorted(tag_counts, key=tag_counts.get, reverse=True)[:3]  # type: ignore[arg-type]
    summary = (
        f"[BELLEK ÖZETİ — Son {threshold} Tur]\n"
        f"Öne çıkan konular: {', '.join(top_tags) or 'belirsiz'}\n"
        + "\n".join(highlights[:3])
    )
    return summary
