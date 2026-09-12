from __future__ import annotations
import json
import logging
import os
import random
import re
import uuid
from typing import Any, Generator, Dict, List, Optional

from .models import (
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
    STANCE_PROFILE,
    DEFAULT_STANCE_COHORT,
)
from .database import get_system_config, log_audit
from .quality import calculate_turn_quality, calculate_ewma, detect_echo

# Import modular components for clean structure and delegation
from packages.research_engine.nodes.memory import (
    calculate_act_r_memory_prompt,
    summarize_turns_if_needed,
)
from packages.research_engine.nodes.culture import (
    HOFSTEDE_TURKEY,
    HOFSTEDE_TURKEY_PROMPT,
    SES_PROFILES,
    TUAD_SES_QUOTA,
    apply_ses_quota,
    get_turkey_behavior_context,
)
from packages.research_engine.nodes.sycophancy import (
    build_elephant_system_prompt,
    judge_answer_quality,
    handle_zero_sum_bet,
)
from packages.research_engine.nodes.probe import (
    should_probe,
    generate_probe_question,
    jaccard_similarity,
)

logger = logging.getLogger(__name__)

DEFAULT_QUESTIONS = [
    "Bu ürün fikrini ilk duyduğunda hangi problemi çözdüğünü düşünüyorsun?",
    "Satın alma veya deneme kararında seni en çok ne durdurur?",
    "Bu çözüm hangi durumda para ödemeye değer olur?",
    "Hangi iddia sana abartılı, eksik veya güvenilmez gelir?",
    "Bu ürünü mevcut alternatiflerle kıyaslayınca en net avantaj ve dezavantaj ne olur?",
]

RESPONDENT_QUESTION_FILTER: Dict[str, List[str]] = {
    "potential_customer": ["pain_point", "value", "positioning"],
    "competitor_user":    ["objection", "pricing", "positioning", "risk"],
    "churned_user":       ["pain_point", "objection", "risk"],
    "decision_maker":     ["pricing", "value", "risk"],
    "individual_user":    ["pain_point", "value", "positioning"],
}

DEFAULT_TRAIT_ORDER = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]


def filter_questions_by_respondent(
    questions: List[InterviewQuestion],
    respondent_type: RespondentType,
) -> List[InterviewQuestion]:
    """Respondent tipine göre ilgisiz soruları filtreler. Soru kalmazsa tümünü döner."""
    allowed = RESPONDENT_QUESTION_FILTER.get(respondent_type, [])
    if not allowed:
        return questions
    filtered = [q for q in questions if any(t in (q.tags or []) for t in allowed)]
    return filtered if filtered else questions


def persona_traits(seed: int, stance: str, price_sensitivity: int, digital_confidence: int) -> Dict[str, int]:
    """Big Five domain skorlarını Rogers Diffusion stance profiliyle kalibre eder.
    Agreeableness prensibi:
      base=60 + stance_modifier + küçük varyasyon (+/-6)
      modifier büyüklüğü (min 4, max 10) > max varyasyon (6) olduğu için
      Skeptic her zaman Mainstream'den düşük Agreeableness puanına sahip olur.
    Openness prensibi:
      Stance modifier birincil sürücüdür (Innovator +12 ... Laggard -8);
      digital_confidence ikincil etki olarak merkezlenmiş şekilde (dc-5)*3 eklenir.
    """
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    var = (seed * 7 % 13) - 6

    agreeableness = 60 + profile["agreeableness_mod"] + var

    # Openness: stance baskın; digital_confidence merkezlenmiş ikincil etki
    openness = 52 + (digital_confidence - 5) * 3 + ((seed * 3 % 12) - 6) + profile["openness_mod"]
    conscientiousness = 62 + (seed * 7 % 28)
    extraversion = 42 + (seed * 5 % 35)
    neuroticism = min(88, max(25, price_sensitivity * 7 + (seed * 4 % 18)))

    neuroticism = min(100, max(1, neuroticism + profile["neuroticism_mod"]))

    return {
        "Openness":          min(92, max(20, openness)),
        "Conscientiousness": min(100, max(1, conscientiousness)),
        "Extraversion":      min(100, max(1, extraversion)),
        "Agreeableness":     min(100, max(1, agreeableness)),
        "Neuroticism":       min(100, max(1, neuroticism)),
    }


def neo_facets_from_traits(traits: Dict[str, int], stance: str) -> Dict[str, int]:
    """Big Five domain skorlarından NEO-PI-R facet yaklaşımsalı üret."""
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    evidence_mod = profile["evidence_need"]
    facets: Dict[str, int] = {}
    
    o = traits.get("Openness", 60)
    facets["O1_Fantasy"] = min(100, o + 5)
    facets["O2_Aesthetics"] = min(100, o - 3)
    facets["O3_Feelings"] = min(100, o + evidence_mod * 2)
    facets["O4_Actions"] = min(100, o - evidence_mod * 3)
    facets["O5_Ideas"] = min(100, o + 8)
    facets["O6_Values"] = min(100, o - 5)
    
    n = traits.get("Neuroticism", 50)
    facets["N1_Anxiety"] = min(100, n + evidence_mod * 2)
    facets["N2_Anger"] = min(100, n - 5)
    facets["N3_Depression"] = min(100, n - 10)
    facets["N4_SelfConsciousness"] = min(100, n + 3)
    facets["N5_Impulsiveness"] = min(100, max(1, 60 - n + evidence_mod))
    facets["N6_Vulnerability"] = min(100, n + evidence_mod)
    
    return {k: max(1, v) for k, v in facets.items()}


def persona_attributes(
    segment: str,
    stance: str,
    price_sensitivity: int,
    digital_confidence: int,
) -> Dict[str, str]:
    return {
        "Hobbies": "Mobil uygulama denemek, kısa video içerikleri izlemek, hafta sonu şehir içi keşifler",
        "Origin country": "Türkiye",
        "Current workflow": "Notlar, Excel/Google Sheets, WhatsApp grupları ve birkaç parçalı SaaS aracı",
        "Decision trigger": "Somut zaman veya para tasarrufu görürse denemeye yaklaşır",
        "Buying friction": "Gizli ücret, uzun kurulum, belirsiz veri kullanımı ve kanıtlanmamış vaatler",
        "Price posture": "Çok hassas" if price_sensitivity >= 8 else "Kanıt görürse ödeme yapabilir",
        "Digital confidence": "Yüksek" if digital_confidence >= 8 else "Orta",
        "Segment role": segment,
        "Research stance": stance,
    }


def generate_interview_script(
    brief: ResearchBrief,
    panel_roles: List[PanelRole] | None = None,
) -> List[InterviewQuestion]:
    from .db_vectors import get_question_collection
    
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
                question=f"Bu ürünün sana sağlayacağı en büyük fayda ne olurdu? Hangi özellik seni en çok heyecanlandırır?",
                reason="Değer algısını ve kullanıcı beklentilerini ölçmek.",
                tags=["value"],
            ),
            InterviewQuestion(
                id="q_objection",
                label="OBJECTION",
                question=f"Bu ürünü kullanmaktan seni alıkoyacak en büyük engel ne olurdu?",
                reason="Satın alma bariyerlerini ve itirazları tespit etmek.",
                tags=["objection"],
            ),
            InterviewQuestion(
                id="q_pricing",
                label="PRICING",
                question=f"Bu ürün için aylık ne kadar ödemeyi kabul edersin? Hangi fiyattan sonra 'bu çok pahalı' dersin?",
                reason="Türkiye pazarı için fiyat eşiğini ve paketleme sinyalini almak.",
                tags=["pricing"],
            ),
            InterviewQuestion(
                id="q_alternatives",
                label="ALTERNATIVES",
                question=f"Şu anda bu ihtiyacını nasıl karşılıyorsun? Hangi alternatifleri kullanıyorsun?",
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
    panel_roles: List[PanelRole] | None = None,
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

    clarifying_questions: List[ClarifyingQuestion] = []
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
    ses_quota = apply_ses_quota(5)
    return ResearchPlan(
        objective=objective,
        assumptions=assumptions,
        clarifying_questions=clarifying_questions,
        interview_questions=[item.question for item in interview_script],
        recommended_panel_size=5,
        interview_script=interview_script,
        ses_quota=ses_quota,
    )


def generate_personas(brief: ResearchBrief, panel_roles: List[PanelRole] | None = None, model: ResearchModel | None = None) -> List[Persona]:
    if panel_roles:
        return generate_personas_from_roles(brief, panel_roles, model)

    market = brief.market or "Türkiye"
    from .matrix import allocate_cohort_matrix
    
    allocations = allocate_cohort_matrix(5)
    
    # Stance diversity zorlaması: en az 3 farklı stance + Skeptic
    present = set(a["stance"] for a in allocations)
    if len(present) < 5:
        target = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]
        for i in range(min(5, len(allocations))):
            allocations[i]["stance"] = target[i]
    
    personas: List[Persona] = []
    
    SES_SEGMENTS = {
        "AB": ["Üst Düzey Yönetici", "Beyaz Yaka Profesyonel", "Girişimci"],
        "C1": ["Orta Düzey Uzman", "KOBİ Çalışanı", "Serbest Çalışan"],
        "C2": ["Esnaf", "Teknisyen", "Mavi Yaka Ustabaşı"],
        "DE": ["Öğrenci", "Emekli", "Yarı Zamanlı Çalışan"],
    }
    NAMES = ["Ahmet", "Ayşe", "Mehmet", "Zeynep", "Mustafa"]
    CITIES = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"]
    CONTEXTS = [
        f"{market} pazarında yeni ürünleri denemeye açık.",
        f"{market} pazarında fiyat-performans odaklı.",
        f"{market} pazarında güvenilir çözümler arıyor.",
        f"{market} pazarında mevcut alternatifleri değerlendiriyor.",
        f"{market} pazarında yeniliklere temkinli yaklaşıyor.",
    ]
    
    for idx, alloc in enumerate(allocations):
        stance = alloc["stance"]
        ses = alloc.get("ses_group", "C1")
        ps = 3 + (idx % 7)
        dc = 4 + (idx % 6)
        tr = persona_traits(idx + 1, stance, ps, dc)
        segment = SES_SEGMENTS.get(ses, SES_SEGMENTS["C1"])[idx % 3]
        
        personas.append(Persona(
            id=f"p{idx + 1}",
            name=NAMES[idx],
            age=25 + (idx * 7) % 30,
            city=CITIES[idx],
            segment=segment,
            role_title=segment,
            stance=stance,
            price_sensitivity=ps,
            digital_confidence=dc,
            context=CONTEXTS[idx],
            goals=["Ürünün faydasını değerlendirmek", "Fiyat-performans dengesini anlamak"],
            objections=["Değer önerisinin belirsizliği", "Alternatiflerin varlığı"],
            knowledge_boundary="Kendi deneyim ve alışkanlıkları hakkında konuşabilir.",
            bio=f"{segment} olarak {market} pazarında {stance} tutumuna sahip.",
            attributes=persona_attributes(segment, stance, ps, dc),
            traits=tr,
            big_five=tr,
            ses_group=ses,
            diffusion_stage=STANCE_PROFILE.get(stance, {}).get("tr_description", ""),
            neo_facets=neo_facets_from_traits(tr, stance),
        ))
    
    return personas


def generate_personas_from_roles(brief: ResearchBrief, panel_roles: List[PanelRole], model: ResearchModel | None = None) -> List[Persona]:
    from packages.research_engine.matrix import allocate_cohort_matrix
    from packages.research_engine.db_vectors import get_personas_from_pool_by_role

    market = brief.market or "Türkiye"
    personas: List[Persona] = []
    
    total_needed = 0
    role_needs = []
    for role in panel_roles:
        if role.count <= 0:
            continue
        pooled_data = get_personas_from_pool_by_role(role.role, limit=role.count)
        needed = role.count - len(pooled_data)
        role_needs.append({"role": role, "pooled": pooled_data, "needed": needed})
        total_needed += needed

    matrix_allocations = allocate_cohort_matrix(total_needed)

    for item in role_needs:
        role = item["role"]
        pooled_data = item["pooled"]
        needed_count = item["needed"]
        
        for data in pooled_data:
            personas.append(
                Persona(
                    id=data["id"],
                    name=data["name"],
                    age=data["age"],
                    city=data["city"],
                    segment=data["segment"],
                    role_title=data["role_title"],
                    stance=data["stance"],
                    price_sensitivity=data["price_sensitivity"],
                    digital_confidence=data["digital_confidence"],
                    context=data["context"],
                    goals=data["goals"],
                    objections=data["objections"],
                    knowledge_boundary=data["knowledge_boundary"],
                    country_code=data["country_code"],
                    origin_country=data["origin_country"],
                    bio=data["bio"],
                    attributes=data["attributes"],
                    traits=data["traits"],
                    big_five=data.get("big_five", {})
                )
            )
            
        if needed_count > 0:
            # Embedding tabanli persona eslestirme devre disi (Enterprise'ta geri gelecek)
            # Dogrudan yeni persona uret
            pass
            loaded_ids = {p.id for p in personas}
            
            # Fallback: fresh persona generation
            while needed_count > 0:
                index = len(personas)
                fallback_stance = DEFAULT_STANCE_COHORT[index % len(DEFAULT_STANCE_COHORT)]
                new_id = f"p_{uuid.uuid4().hex[:8]}"
                fallback_traits = persona_traits(index, fallback_stance, 6, 7)
                p = Persona(
                    id=new_id,
                    name=f"Kullanıcı {index}",
                    age=30 + (index % 15),
                    city="İstanbul",
                    segment=role.role,
                    role_title=role.role,
                    stance=fallback_stance,
                    price_sensitivity=6,
                    digital_confidence=7,
                    context=f"{market} pazarında {role.role} rolünü temsil eder.",
                    goals=["Ürünün faydasını anlamak"],
                    objections=["Değer önerisinin belirsizliği"],
                    knowledge_boundary="Kendi rolü hakkında konuşabilir.",
                    bio=f"{role.role} rolünde Türkiye pazarı katılımcısı.",
                    attributes=persona_attributes(role.role, fallback_stance, 6, 7),
                    traits=fallback_traits,
                    diffusion_stage=STANCE_PROFILE.get(fallback_stance, {}).get("tr_description", ""),
                    neo_facets=neo_facets_from_traits(fallback_traits, fallback_stance),
                )
                personas.append(p)
                needed_count -= 1
            
    return personas


def classify_question(question: str) -> List[str]:
    lower = question.lower()
    tags: List[str] = []
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
    personas: List[Persona],
    model: ResearchModel,
    interview_script: List[InterviewQuestion] | None = None,
) -> List[PersonaInterview]:
    interviews: List[PersonaInterview] = []
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

        turns: List[InterviewTurn] = [
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


def run_interviews_stream(
    brief: ResearchBrief,
    personas: List[Persona],
    model: ResearchModel,
    interview_script: List[InterviewQuestion] | None = None,
    max_retries: int = 2,
) -> Generator[tuple[str, Any], None, List[PersonaInterview]]:
    interviews: List[PersonaInterview] = []
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
        turns: List[InterviewTurn] = []
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


def _skipped_interview(persona: Persona, script: List[InterviewQuestion]) -> PersonaInterview:
    """Süre bütçesi aşıldığında kalan personalar için boş mülakat üretir (P0-5)."""
    turns = [
        InterviewTurn(
            question=sq.question,
            answer="[Yanıt alınamadı]",
            tags=sq.tags or classify_question(sq.question),
            model_id=None,
            quality_flags=["timeout"],
        )
        for sq in script
    ]
    return PersonaInterview(
        persona=persona,
        turns=turns,
        consistency_notes=[
            "Süre bütçesi (RESEARCH_DEADLINE_SECONDS) aşıldı — mülakat çalıştırılmadı."
        ],
    )


def run_interviews_batch(
    brief: ResearchBrief,
    personas: List[Persona],
    model: ResearchModel,
    interview_script: List[InterviewQuestion] | None = None,
) -> List[PersonaInterview]:
    """
    Batch interview: her persona için TÜM soruları tek bir API çağrısında JSON array olarak alır.
    Soru başına ayrı çağrı yapmaz — maliyet ve süre avantajı sağlar.
    """
    interviews: List[PersonaInterview] = []
    script = interview_script or generate_interview_script(brief)

    # ── Süre bütçesi (P0-5): aşılırsa kalan personalar atlanır ──
    import time as _time
    _deadline: float | None = None
    try:
        _deadline_seconds = float(os.getenv("RESEARCH_DEADLINE_SECONDS", "300"))
        if _deadline_seconds > 0:
            _deadline = _time.monotonic() + _deadline_seconds
    except (TypeError, ValueError):
        _deadline = None

    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed (batch), using default persona prompt", exc_info=True)
        db_prompt = None

    # Soru listesini numaralı formata çevir (AB_TEST hariç — kişiye özel aşağıda)
    non_ab_questions = [sq for sq in script if sq.label != "AB_TEST"]
    has_ab = any(sq.label == "AB_TEST" for sq in script) and brief.variant_a and brief.variant_b

    for persona_idx, persona in enumerate(personas):
        # Süre bütçesi aşıldıysa: kullanıcıyı daha fazla bekletme, kalanları boş mülakatla doldur.
        if _deadline is not None and _time.monotonic() > _deadline:
            logger.warning(
                "Araştırma süre bütçesi aşıldı — %d persona atlanıyor (indeks %d).",
                len(personas) - persona_idx, persona_idx,
            )
            for skipped in personas[persona_idx:]:
                interviews.append(_skipped_interview(skipped, script))
            break

        system_prompt = db_prompt if db_prompt else build_elephant_system_prompt(persona, brief.hypothesis_blind)

        # Sprint 5 — A/B soru metnini kişiye özel randomize et (batch için)
        ab_question_text: str | None = None
        ab_mapping: str | None = None
        if has_ab:
            ab_question_text, ab_mapping = _format_ab_question(brief, persona_idx)

        # Soru bloğunu kişiye özel oluştur (AB sorusu varsa ekle)
        questions_block = ""
        for i, sq in enumerate(non_ab_questions, start=1):
            questions_block += f"{i}. [{sq.label}] {sq.question}\n"
        if ab_question_text:
            ab_num = len(non_ab_questions) + 1
            questions_block += f"{ab_num}. [AB_TEST] {ab_question_text}\n"

        turkey_context = get_turkey_behavior_context(persona, script[0])

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
            f"Ekonomik Grup: {persona.ses_group} | Tutum: {persona.stance}\n"
            f"Fiyat Hassasiyeti: {persona.price_sensitivity}/10 | Dijital Özgüven: {persona.digital_confidence}/10\n"
            f"Katılımcı Tipi: {persona.respondent_type} | Yerleşim: {persona.settlement_type}\n"
            f"Bağlam: {persona.context}\n"
            f"Hedeflerin: {', '.join(persona.goals) if persona.goals else 'Belirtilmedi'}\n"
            f"İtirazların: {', '.join(persona.objections) if persona.objections else 'Belirtilmedi'}\n"
            f"{turkey_context}\n\n"
            f"{research_context_block}"
            f"[SORULAR]\n"
            f"{questions_block}\n"
            f"[GÖREV]\n"
            f"Yukarıdaki kimliğe girerek her soruyu 2-4 cümle ile yanıtla.\n"
            f"- Birinci tekil şahıs kullan, Türkiye gerçeklerine bağlı kal (TL, taksit, KVKK).\n"
            f"- Dürüst ol; ürünü beğenmek zorunda değilsin.\n"
            f"- ZORUNLU: Yanıtını şu JSON dizisi olarak ver, başka hiçbir metin ekleme:\n"
            f'[{{"label": "SORU_ETIKETI", "answer": "..."}}, ...]\n'
        )

        # Batch interview — retry loop (DeepSeek JSON mode may rarely return empty)
        answers: dict[str, str] = {}
        batch_attempt = 0
        max_batch_attempts = 3
        expected_labels = {sq.label.upper() for sq in script}
        
        for batch_attempt in range(max_batch_attempts):
            missing_labels = expected_labels - set(answers.keys())
            if not missing_labels:
                break

            current_prompt = prompt
            if batch_attempt > 0:
                # Retry: sadece eksik soruları hedefle
                missing_block = "\n".join(f"{i}. [{lbl}] ..." for i, lbl in enumerate(sorted(missing_labels), 1))
                current_prompt = prompt + (
                    f"\n\n[UYARI: BAZI SORULARA CEVAP VERILMEDI]\n"
                    f"Su etiketli sorulara MUTLAKA cevap ver: {sorted(missing_labels)}\n"
                    "- Asistan/yapay zeka oldugunu asla belli etme.\n"
                    "- Tum sorulari birinci tekil sahis olarak, 2-4 cumleyle cevapla.\n"
                    "- Turkiye gerceklerine bagli kal: TL, taksit, KVKK, kargo.\n"
                    "- Eger skeptik bir karaktersen urunu elestirmekten ve reddetmekten cekinme.\n"
                )
            
            raw = model.generate(system_prompt, current_prompt)

            if not raw or raw.strip() == "":
                logger.warning(f"Batch empty response for {persona.name} (attempt {batch_attempt+1}), retrying...")
                continue

            try:
                clean = re.sub(r'```(?:json)?\s*|```', '', raw)
                match = re.search(r'\[.*\]', clean, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    for item in parsed:
                        lbl = item.get("label", "").upper()
                        ans = item.get("answer", "")
                        if lbl and ans and lbl not in answers:
                            answers[lbl] = ans
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Batch parse failed for {persona.name} (attempt {batch_attempt+1}): {e}")

            still_missing = expected_labels - set(answers.keys())
            if still_missing:
                logger.warning(f"Batch partial answers for {persona.name} (attempt {batch_attempt+1}): missing {sorted(still_missing)}, raw[:150]={raw[:150]}")

        # ── Bilimsel Kalite Kontrolü (Grounded Simulation §5) ──
        turns: List[InterviewTurn] = []
        answers_list: list[str] = []  # Echo detection için sıralı cevaplar
        total_flags = 0
        critical_failures = 0
        
        for sq in script:
            # Sprint 5 — A/B sorusu için kişiye özel metni kullan
            sq_question = ab_question_text if (sq.label == "AB_TEST" and ab_question_text) else sq.question
            ans = answers.get(sq.label.upper(), "[Yanıt alınamadı]")
            quality_flags = list(judge_answer_quality(persona, sq_question, ans))
            
            # ── Intra-Persona Echo Detection (Jaccard, god_doc.md §5.3) ──
            if len(answers_list) >= 1:
                # Son cevapla şimdiki cevap arasında echo kontrolü
                if detect_echo(ans, answers_list[-1]):
                    quality_flags.append("echo_detected")
            answers_list.append(ans)
            
            # ── Acquiescence Detection (god_doc.md §5.1) ──
            from .quality import detect_acquiescence
            if persona.stance in {"Skeptic", "Laggard"}:
                if detect_acquiescence(persona.stance, [ans]):
                    quality_flags.append("acquiescence_bias")
            
            total_flags += len(quality_flags)
            if any(f in {"meta_tone", "visible_reasoning", "sycophancy_detected"} for f in quality_flags):
                critical_failures += 1

            turns.append(InterviewTurn(
                question=sq_question,
                answer=ans,
                tags=sq.tags or classify_question(sq_question),
                model_id=getattr(model, "last_model_id", None),
                quality_flags=quality_flags,
            ))
        
        # ── Batch Quality Score (Grounded Simulation §5 EWMA eşdeğeri) ──
        answered_count = len([t for t in turns if t.answer != "[Yanıt alınamadı]"])
        total_questions = len(script)
        flag_rate = total_flags / max(total_questions, 1)
        
        # Kalite skoru: 1.0 = mükemmel, <0.5 = zayıf
        quality_score = max(0.0, 1.0 - (flag_rate * 0.5) - (critical_failures * 0.15))

        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
            f"Batch interview — {answered_count}/{total_questions} yanıt alındı",
            f"Kalite skoru: {quality_score:.2f} | Flag sayısı: {total_flags} | Kritik hata: {critical_failures}",
        ]
        if ab_mapping:
            consistency_notes.append(ab_mapping)
        
        # Stance uyumluluk notu (Grounded Simulation §4.3)
        if persona.stance == "Skeptic":
            has_objection = any(
                any(kw in t.answer.lower() for kw in ["güvenmiyorum", "şüphe", "risk", "pahalı", "kanıt", "itiraz", "emin değilim"])
                for t in turns
            )
            if not has_objection:
                consistency_notes.append("UYARI: Skeptic persona yeterince itiraz üretmedi — stance uyumsuzluğu.")

        interviews.append(PersonaInterview(
            persona=persona,
            turns=turns,
            consistency_notes=consistency_notes,
        ))

    return interviews
