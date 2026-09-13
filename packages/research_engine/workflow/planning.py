"""Plan uretimi: objective, varsayimlar ve mulakat senaryosu (R8-1)."""
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

from ._constants import DEFAULT_QUESTIONS, RESPONDENT_QUESTION_FILTER


def filter_questions_by_respondent(
    questions: list[InterviewQuestion],
    respondent_type: RespondentType,
) -> list[InterviewQuestion]:
    """Respondent tipine göre ilgisiz soruları filtreler. Soru kalmazsa tümünü döner."""
    allowed = RESPONDENT_QUESTION_FILTER.get(respondent_type, [])
    if not allowed:
        return questions
    filtered = [q for q in questions if any(t in (q.tags or []) for t in allowed)]
    return filtered if filtered else questions

def generate_interview_script(
    brief: ResearchBrief,
    panel_roles: list[PanelRole] | None = None,
) -> list[InterviewQuestion]:
    from ..db_vectors import get_question_collection
    
    category = brief.category or "ürün"
    expected_price = brief.expected_price or "önerilecek fiyat/paket"
    
    all_questions = get_question_collection()
    
    if not all_questions:
        cat_text = f"{category} ürünü" if category != "genel" else "bu ürün/hizmet"
        price_text = expected_price if expected_price not in ("önerilecek fiyat/paket",) else "belirtilen fiyat"
        fallback = [
            InterviewQuestion(
                id="q_context",
                label="CONTEXT",
                question=f"{cat_text} bağlamında bugün bu problemi nasıl yaşıyorsun? Son yaşadığın somut bir örneği anlatır mısın?",
                reason="Pain point'i soyut fikir yerine gerçek olay üzerinden yakalamak.",
                tags=["pain_point"],
            ),
            InterviewQuestion(
                id="q_value",
                label="VALUE",
                question="Bu ürünün sana sağlayacağı en büyük fayda ne olurdu? Hangi özellik seni en çok heyecanlandırır?",
                reason="Değer algısını ve kullanıcı beklentilerini ölçmek.",
                tags=["value"],
            ),
            InterviewQuestion(
                id="q_objection",
                label="OBJECTION",
                question="Bu ürünü kullanmaktan seni alıkoyacak en büyük engel ne olurdu?",
                reason="Satın alma bariyerlerini ve itirazları tespit etmek.",
                tags=["objection"],
            ),
            InterviewQuestion(
                id="q_pricing",
                label="PRICING",
                question="Bu ürün için aylık ne kadar ödemeyi kabul edersin? Hangi fiyattan sonra 'bu çok pahalı' dersin?",
                reason="Türkiye pazarı için fiyat eşiğini ve paketleme sinyalini almak.",
                tags=["pricing"],
            ),
            InterviewQuestion(
                id="q_alternatives",
                label="ALTERNATIVES",
                question="Şu anda bu ihtiyacını nasıl karşılıyorsun? Hangi alternatifleri kullanıyorsun?",
                reason="Mevcut rakipleri ve switching maliyetini öğrenmek.",
                tags=["positioning"],
            ),
        ]
        # Sprint 5 — A/B varyant karşılaştırma sorusu
        if brief.variant_a and brief.variant_b:
            fallback.append(build_ab_comparison_question(brief))
        return fallback

    liked_questions = [q for q in all_questions if q.get("is_liked")]
    if not liked_questions:
        liked_questions = all_questions

    script = []
    for i, q in enumerate(liked_questions[:6]):
        tags_raw = q.get("purpose_context", "value")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        if not tags:
            tags = ["value"]

        q_text = q["question"].replace("{category}", category).replace("{expected_price}", expected_price)

        script.append(
            InterviewQuestion(
                id=f"q_db_{i}",
                label=tags[0].upper(),
                question=q_text,
                reason="DB Curated Pool",
                tags=tags,
            )
        )

    # Sprint 5 — A/B varyant karşılaştırma sorusu
    if brief.variant_a and brief.variant_b:
        script.append(build_ab_comparison_question(brief))

    return script

def build_ab_comparison_question(brief: ResearchBrief) -> InterviewQuestion:
    """
    Creates an A/B comparison question that presents both variants
    with randomized labels (neutral names like "Seçenek 1" and "Seçenek 2")
    and asks the persona to compare them.

    The actual randomization per persona happens in _format_ab_question()
    during interview execution, using persona index as seed for reproducibility.
    """
    return InterviewQuestion(
        id="q_ab_test",
        label="AB_TEST",
        question=(
            "Şimdi sana iki farklı ürün anlatacağım. İkisini de dikkatlice dinle ve "
            "hangisini tercih edeceğini söyle.\n\n"
            "{first_label}: {first_variant}\n\n"
            "{second_label}: {second_variant}\n\n"
            "Hangisini tercih edersin? Neden?"
        ),
        reason="A/B varyant testi — kör karşılaştırma",
        tags=["positioning", "value"],
    )

def _format_ab_question(brief: ResearchBrief, persona_index: int) -> tuple[str, str]:
    """
    Randomized A/B question per persona.
    Uses persona_index as seed for reproducible randomization.

    Returns (formatted_question_text, mapping_note) where mapping_note
    encodes which variant was presented as Seçenek 1 and which as Seçenek 2.
    """
    rng = random.Random(persona_index)
    if rng.random() > 0.5:
        first_variant = brief.variant_a
        second_variant = brief.variant_b
        mapping = "AB_MAP:A_AS_1"  # Variant A = Seçenek 1, Variant B = Seçenek 2
    else:
        first_variant = brief.variant_b
        second_variant = brief.variant_a
        mapping = "AB_MAP:A_AS_2"  # Variant A = Seçenek 2, Variant B = Seçenek 1

    question_text = (
        "Şimdi sana iki farklı ürün anlatacağım. İkisini de dikkatlice dinle ve "
        "hangisini tercih edeceğini söyle.\n\n"
        f"Seçenek 1: {first_variant}\n\n"
        f"Seçenek 2: {second_variant}\n\n"
        "Hangisini tercih edersin? Neden?"
    )
    return question_text, mapping

def build_research_plan(
    brief: ResearchBrief,
    panel_roles: list[PanelRole] | None = None,
    panel_size: int = 5,
) -> ResearchPlan:
    assumptions = [
        f"Araştırma pazarı: {brief.market or 'Türkiye'}",
        f"Kategori: {brief.category or 'Belirtilmedi'}",
        "Çıktılar yön gösterici hipotez olarak ele alınacak.",
    ]
    if brief.sales_channel:
        assumptions.append(f"Satış kanalı: {brief.sales_channel}")
    if brief.expected_price:
        assumptions.append(f"Beklenen fiyat: {brief.expected_price}")

    clarifying_questions: list[ClarifyingQuestion] = []
    if not brief.target_users:
        clarifying_questions.append(
            ClarifyingQuestion(
                id="cq_target",
                question="Bu ürünün birincil hedef kullanıcısı kim?",
                reason="Persona panelinin segment dağılımı hedef kullanıcıya göre kurulmalı.",
                priority="high",
            )
        )
    if not brief.expected_price and "fiyat" not in " ".join(brief.questions).lower():
        clarifying_questions.append(
            ClarifyingQuestion(
                id="cq_price",
                question="Hedeflenen fiyat veya paket aralığı nedir?",
                reason="Türkiye pazarı için fiyat hassasiyeti ana itirazlardan biri olabilir.",
                priority="high",
            )
        )
    if not brief.competitors:
        clarifying_questions.append(
            ClarifyingQuestion(
                id="cq_competitors",
                question="Kullanıcı bugün aynı ihtiyacı hangi alternatiflerle çözüyor?",
                reason="Konumlandırma ve switching cost ancak mevcut alternatiflerle kıyaslanabilir.",
            )
        )
    if not brief.success_metric:
        clarifying_questions.append(
            ClarifyingQuestion(
                id="cq_success",
                question="Başarı ölçütü ne olacak: satın alma niyeti, mesaj netliği, fiyat kabulü veya dönüşüm?",
                reason="Raporun karar verilebilir olması için tek ana metrik gerekir.",
            )
        )

    if not clarifying_questions:
        clarifying_questions.append(
            ClarifyingQuestion(
                id="cq_depth",
                question="Bu araştırmada özellikle çürütmek istediğiniz en riskli varsayım nedir?",
                reason="İyi araştırma sadece fikri doğrulamaz, en kırılgan varsayımı test eder.",
                priority="medium",
            )
        )

    objective = (
        f"{brief.title} fikrinin {brief.market} pazarındaki pain point, değer önerisi, "
        "itiraz, fiyat hassasiyeti ve konumlandırma risklerini sentetik persona görüşmeleriyle test etmek."
    )
    interview_script = generate_interview_script(brief, panel_roles)
    panel_size = max(1, int(panel_size))
    ses_quota = apply_ses_quota(panel_size)
    return ResearchPlan(
        objective=objective,
        assumptions=assumptions,
        clarifying_questions=clarifying_questions,
        interview_questions=[item.question for item in interview_script],
        recommended_panel_size=panel_size,
        interview_script=interview_script,
        ses_quota=ses_quota,
    )
