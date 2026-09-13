"""Mulakat yurutumu (senkron) (R8-3)."""
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


def classify_question(question: str) -> list[str]:
    lower = question.lower()
    tags: list[str] = []
    if "problem" in lower or "çözdüğünü" in lower or "sorun" in lower or "zorluk" in lower:
        tags.append("pain_point")
    if "durdurur" in lower or "güvenilmez" in lower or "hayır" in lower or "endişe" in lower:
        tags.append("objection")
    # PSM: Türk e-ticaretinde fiyat sinyali yakalayan kapsamlı keyword seti
    PRICING_KW = [
        "para", "fiyat", "ücret", "tl", "lira", "₺", "ödeme", "bütçe",
        "pahalı", "ucuz", "ne kadar", "kaç", "maliyet", "kargo ücreti",
        "taksit", "indirim", "kampanya", "fırsatı",
    ]
    if any(kw in lower for kw in PRICING_KW):
        tags.append("pricing")
    if "avantaj" in lower or "dezavantaj" in lower:
        tags.extend(["value", "positioning"])
    return tags or ["risk"]

def run_interviews(
    brief: ResearchBrief,
    personas: list[Persona],
    model: ResearchModel,
    interview_script: list[InterviewQuestion] | None = None,
) -> list[PersonaInterview]:
    interviews: list[PersonaInterview] = []
    script = interview_script or generate_interview_script(brief)

    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed, using default persona prompt", exc_info=True)
        db_prompt = None

    for persona_idx, persona in enumerate(personas):
        original_system = db_prompt if db_prompt else build_elephant_system_prompt(persona, brief.hypothesis_blind)
        base_system = original_system
        ewma_score = 1.0  # EWMA başlangıç skoru (god_doc.md §5)

        turns: list[InterviewTurn] = [
        ]
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

            # 1. ACT-R Episodic Memory
            turn_memory = calculate_act_r_memory_prompt(turns, script_question)

            # 2. Turkey-specific local reflexes
            turkey_context = get_turkey_behavior_context(persona, script_question)

            # ── Hypothesis-Blind Context (Grounded Simulation §4.3) ──
            research_context_block = ""
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
                f"Dijital özgüven: {persona.digital_confidence}/10\n"
                f"Kullanım sıklığı: {persona.usage_frequency}\n"
                f"Marka sadakati: {persona.brand_loyalty}/10\n"
                f"Bağlam: {persona.context}\n"
                f"Hedefler: {', '.join(persona.goals)}\n"
                f"İtirazlar: {', '.join(persona.objections)}\n"
                f"Bilgi sınırı: {persona.knowledge_boundary}\n"
                f"{turn_memory}"
                f"{turkey_context}\n"
                f"{research_context_block}"
                f"Soru etiketi: {script_question.label}\n"
                f"Soru: {question_text}\n"
                "Kısa, somut ve Türkiye pazarı gerçeklerine uygun cevap ver."
            )
            answer = model.generate(base_system, prompt)
            quality_flags = judge_answer_quality(persona, question_text, answer)

            # 3. ELEPHANT & Zero-Sum Bet check
            answer, quality_flags = handle_zero_sum_bet(
                persona, script_question, answer, base_system, prompt, model, quality_flags
            )

            # 4. Echo Detection (god_doc.md §5 EWMA Tamir Protokolü)
            if detect_echo(answer, question_text):
                quality_flags = list(quality_flags) + ["echo_detected"]

            turns.append(
                InterviewTurn(
                    question=question_text,
                    answer=answer,
                    tags=script_question.tags or classify_question(question_text),
                    model_id=getattr(model, "last_model_id", None),
                    quality_flags=quality_flags,
                )
            )

            # ── Sprint 3: Adaptive Probe Engine ──
            if total_probes < 3 and should_probe(answer, script_question.label):
                total_probes += 1
                probe_question = generate_probe_question(
                    answer, question_text, persona.stance
                )
                probe_prompt = (
                    f"{prompt}\n\n"
                    f"[TAKİP SORUSU — Araştırmacı soruyor]\n"
                    f"{probe_question}\n"
                    "Bu takip sorusuna kimliğine sadık kalarak, kısa ve somut cevap ver."
                )
                probe_answer = model.generate(base_system, probe_prompt)

                # Probe quality guard: discard if too similar to original (Jaccard > 0.7)
                sim = jaccard_similarity(answer, probe_answer)
                if sim <= 0.7:
                    probe_flags = judge_answer_quality(persona, probe_question, probe_answer)
                    turns.append(
                        InterviewTurn(
                            question=probe_question,
                            answer=probe_answer,
                            tags=script_question.tags or classify_question(script_question.question),
                            model_id=getattr(model, "last_model_id", None),
                            quality_flags=probe_flags,
                            is_probe=True,
                        )
                    )
                    consistency_notes.append(
                        f"Probe ({total_probes}/3) — Jaccard: {sim:.2f}"
                    )
                else:
                    total_probes -= 1  # Don't count discarded probe against limit
                    consistency_notes.append(
                        f"Probe discarded — Jaccard too high: {sim:.2f}"
                    )

            # 5. EWMA Tamir Protokolü (god_doc.md §5)
            turn_quality = calculate_turn_quality(quality_flags)
            ewma_score = calculate_ewma(turn_quality, ewma_score)
            consistency_notes.append(f"Turn {len(turns)} EWMA: {ewma_score:.2f}")

            if ewma_score < 0.65:
                base_system = original_system + (
                    "\n\n[SİSTEM UYARISI: KALİTE DÜŞTÜ] "
                    "Karakterinden kayıyorsun veya soruları tekrarlıyorsun. "
                    "Kısa, somut ve GERÇEK BİR TÜRK KULLANICI gibi cevap ver. "
                    "Asistan olduğunu ASLA belli etme."
                )
            elif ewma_score >= 0.80:
                base_system = original_system  # Sistem promptunu sıfırla

        interviews.append(PersonaInterview(persona=persona, turns=turns, consistency_notes=consistency_notes))
    return interviews
