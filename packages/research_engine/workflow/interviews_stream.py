"""Mulakat yurutumu (streaming) (R8-3)."""
from __future__ import annotations

import json
import logging
import os
import random
import re
import uuid
from collections.abc import Generator
from dataclasses import replace
from typing import Any, Dict, List, Optional

from packages.research_engine.nodes.culture import (
    HOFSTEDE_TURKEY,
    HOFSTEDE_TURKEY_PROMPT,
    SES_PROFILES,
    TUAD_SES_QUOTA,
    apply_ses_quota,
    get_turkey_behavior_context,
)

# Import modular components for clean structure and delegation
from packages.research_engine.nodes.memory import (
    calculate_act_r_memory_prompt,
    summarize_turns_if_needed,
)
from packages.research_engine.nodes.probe import (
    generate_probe_question,
    jaccard_similarity,
    should_probe,
)
from packages.research_engine.nodes.sycophancy import (
    build_elephant_system_prompt,
    handle_zero_sum_bet,
    judge_answer_quality,
)

from ..database import get_system_config, log_audit
from ..models import (
    DEFAULT_STANCE_COHORT,
    STANCE_PROFILE,
    ClarifyingQuestion,
    InterviewQuestion,
    InterviewTurn,
    PanelRole,
    Persona,
    PersonaInterview,
    ResearchBrief,
    ResearchModel,
    ResearchPlan,
    RespondentType,
)
from ..quality import calculate_ewma, calculate_turn_quality, detect_echo

logger = logging.getLogger(__name__)

from .planning import _format_ab_question, generate_interview_script


def run_interviews_stream(
    brief: ResearchBrief,
    personas: list[Persona],
    model: ResearchModel,
    interview_script: list[InterviewQuestion] | None = None,
    max_retries: int = 2,
) -> Generator[tuple[str, Any], None, list[PersonaInterview]]:
    interviews: list[PersonaInterview] = []
    script = interview_script or generate_interview_script(brief)
    
    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed (stream), using default persona prompt", exc_info=True)
        db_prompt = None
        
    for persona_idx, persona in enumerate(personas):
        original_system = db_prompt if db_prompt else build_elephant_system_prompt(persona, brief.hypothesis_blind)
        base_system = original_system
        ewma_score = 1.0

        yield ("persona_start", {"persona": persona})
        turns: list[InterviewTurn] = []
        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
        ]
        total_probes = 0  # Sprint 3: max 3 probes per interview
        
        for script_question in script:
            # Sprint 5 — A/B soru metnini kişiye özel randomize et
            question_text = script_question.question
            if script_question.label == "AB_TEST" and brief.variant_a and brief.variant_b:
                question_text, ab_mapping = _format_ab_question(brief, persona_idx)
                consistency_notes.append(ab_mapping)

            yield ("question_start", {"persona": persona, "question": script_question})
            
            for attempt in range(max_retries + 1):
                if attempt == 0:
                    system = base_system
                else:
                    yield ("retry", {"persona": persona, "question": script_question, "attempt": attempt})
                    system = base_system + "\nUYARI: Önceki cevabında asistan/yapay zeka olduğunu belli ettin veya çok jenerik/kısa konuştun. LÜTFEN ASLA ASİSTAN OLDUĞUNU BELLİ ETME, %100 gerçek bir insan gibi cevap ver."

                # 1. ACT-R Episodic Memory
                turn_memory = calculate_act_r_memory_prompt(turns, script_question)

                # 2. Turkey-specific local reflexes
                turkey_context = get_turkey_behavior_context(persona, script_question)

                # ── Hypothesis-Blind Context (Grounded Simulation §4.3) ──
                if brief.hypothesis_blind:
                    product_desc = brief.idea or f"{brief.category} kategorisinde bir ürün"
                    research_context_block = (
                        f"[BAĞLAM]\n"
                        f"Şu ürün/hizmet hakkında görüşlerin sorulacak:\n"
                        f"{product_desc}\n\n"
                        f"Sana sorulan soruları kendi deneyimlerine ve alışkanlıklarına göre yanıtla.\n"
                        f"Bu ürün hakkında ne düşündüğünü bilmek istiyoruz; doğru/yanlış cevap yok.\n\n"
                    )
                else:
                    research_context_block = (
                        f"[ARAŞTIRMA KONUSU]\n"
                        f"{brief.idea}\n\n"
                    )

                prompt = (
                    f"[KİMLİĞİN]\n"
                    f"{persona.name}, {persona.age} yaş, {persona.city} — {persona.segment}\n"
                    f"Ekonomik Grup: {persona.ses_group} ({SES_PROFILES.get(persona.ses_group, {}).get('profile', '')})\n"
                    f"Tutum: {persona.stance} | Fiyat Hassasiyeti: {persona.price_sensitivity}/10 | Dijital Özgüven: {persona.digital_confidence}/10\n"
                    f"Katılımcı Tipi: {persona.respondent_type} | Yerleşim: {persona.settlement_type}\n"
                    f"Bağlam: {persona.context}\n"
                    f"Hedeflerin: {', '.join(persona.goals)}\n"
                    f"İtirazların: {', '.join(persona.objections)}\n"
                    f"Bilgi Sınırın: {persona.knowledge_boundary}\n"
                    f"{turn_memory}"
                    f"{turkey_context}\n\n"
                    f"{research_context_block}"
                    f"[SORU — {script_question.label}]\n"
                    f"{question_text}\n\n"
                    f"[GÖREV]\n"
                    f"Yukarıdaki kimliğine girerek bu soruyu yanıtla.\n"
                    f"- 2-4 cümle, somut, birinci tekil şahıs.\n"
                    f"- Türkiye gerçeklerine bağlı kal (TL, KVKK, taksit, kargo, güven).\n"
                    f"- Önceki cevaplarınla çelişme; tutarlı bir karakter ol.\n"
                    f"- Dürüst ol: endişelerin varsa gizleme. Ürünü beğenmek zorunda değilsin."
                )
                
                full_answer = ""
                if hasattr(model, "generate_stream"):
                    for chunk in model.generate_stream(system, prompt):
                        full_answer += chunk
                        yield ("chunk", {"text": chunk})
                else:
                    full_answer = model.generate(system, prompt)
                    yield ("chunk", {"text": full_answer})
                
                quality_flags = judge_answer_quality(persona, question_text, full_answer)

                # 3. ELEPHANT & Zero-Sum Bet check & repair ( pricing check at attempt 0 )
                if attempt == 0:
                    full_answer, quality_flags = handle_zero_sum_bet(
                        persona, script_question, full_answer, system, prompt, model, quality_flags
                    )

                critical_failure = any(flag in {"meta_tone", "visible_reasoning", "sycophancy_detected"} for flag in quality_flags)
                
                if critical_failure:
                    try:
                        log_audit(brief.title[:50], persona.name, ", ".join(quality_flags), "Retried turn due to AI hallucination/meta-tone")
                    except Exception:
                        logger.warning(
                            "audit log write failed for persona=%s flags=%s",
                            persona.name, quality_flags, exc_info=True
                        )
                
                if not critical_failure or attempt == max_retries:
                    # 4. Echo Detection (god_doc.md §5 EWMA Tamir Protokolü)
                    if detect_echo(full_answer, question_text):
                        quality_flags = list(quality_flags) + ["echo_detected"]

                    turn = InterviewTurn(
                        question=question_text,
                        answer=full_answer,
                        tags=script_question.tags or classify_question(question_text),
                        model_id=getattr(model, "last_model_id", None),
                        quality_flags=quality_flags,
                    )
                    turns.append(turn)

                    # ── Sprint 3: Adaptive Probe Engine ──
                    if total_probes < 3 and should_probe(full_answer, script_question.label):
                        total_probes += 1
                        probe_question = generate_probe_question(
                            full_answer, question_text, persona.stance
                        )
                        yield ("probe_start", {"persona": persona, "probe": probe_question})

                        probe_prompt = (
                            f"{prompt}\n\n"
                            f"[TAKİP SORUSU — Araştırmacı soruyor]\n"
                            f"{probe_question}\n"
                            "Bu takip sorusuna kimliğine sadık kalarak, kısa ve somut cevap ver."
                        )
                        probe_answer = ""
                        if hasattr(model, "generate_stream"):
                            for chunk in model.generate_stream(system, probe_prompt):
                                probe_answer += chunk
                                yield ("chunk", {"text": chunk})
                        else:
                            probe_answer = model.generate(system, probe_prompt)
                            yield ("chunk", {"text": probe_answer})

                        # Probe quality guard: discard if too similar to original (Jaccard > 0.7)
                        sim = jaccard_similarity(full_answer, probe_answer)
                        if sim <= 0.7:
                            probe_flags = judge_answer_quality(persona, probe_question, probe_answer)
                            probe_turn = InterviewTurn(
                                question=probe_question,
                                answer=probe_answer,
                                tags=script_question.tags or classify_question(script_question.question),
                                model_id=getattr(model, "last_model_id", None),
                                quality_flags=probe_flags,
                                is_probe=True,
                            )
                            turns.append(probe_turn)
                            consistency_notes.append(
                                f"Probe ({total_probes}/3) — Jaccard: {sim:.2f}"
                            )
                            yield ("probe_end", {"persona": persona, "turn": probe_turn})
                        else:
                            total_probes -= 1  # Don't count discarded probe against limit
                            consistency_notes.append(
                                f"Probe discarded — Jaccard too high: {sim:.2f}"
                            )

                    # Kademeli Bellek Özetleme: her 10 turda tetiklenir (god_doc.md §5)
                    mem_summary = summarize_turns_if_needed(turns)
                    if mem_summary:
                        consistency_notes.append(mem_summary)

                    turn_quality = calculate_turn_quality(quality_flags)
                    ewma_score = calculate_ewma(turn_quality, ewma_score)
                    consistency_notes.append(f"Turn {len(turns)} EWMA: {ewma_score:.2f}")
                    
                    if ewma_score < 0.65:
                        base_system = original_system + "\n\n[SİSTEM UYARISI: KALİTE DÜŞTÜ] Önceki yanıtların zayıfladı. Karakterinden kayıyorsun. Lütfen kısa, somut ve Türkiye gerçeklerine uygun bir Türk kullanıcısı gibi cevap ver. Asistan olduğunu ASLA belli etme."
                    elif ewma_score >= 0.80:
                        base_system = original_system

                    yield ("question_end", {"persona": persona, "question": script_question, "turn": turn})
                    break
                    
        interview = PersonaInterview(persona=persona, turns=turns, consistency_notes=consistency_notes)
        interviews.append(interview)
        yield ("persona_end", {"persona": persona, "interview": interview})
        
    return interviews
