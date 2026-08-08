from __future__ import annotations
import json
import logging
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
    """
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    var = (seed * 7 % 13) - 6

    agreeableness = 60 + profile["agreeableness_mod"] + var

    openness = min(92, max(35, digital_confidence * 9 + (seed * 3 % 12)))
    conscientiousness = 62 + (seed * 7 % 28)
    extraversion = 42 + (seed * 5 % 35)
    neuroticism = min(88, max(25, price_sensitivity * 7 + (seed * 4 % 18)))

    openness = min(100, max(1, openness + profile["openness_mod"]))
    neuroticism = min(100, max(1, neuroticism + profile["neuroticism_mod"]))

    return {
        "Openness":          min(100, max(1, openness)),
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
        return [
            InterviewQuestion(
                id="q_context",
                label="CONTEXT",
                question=f"{category} bağlamında bugün bu problemi nasıl yaşıyorsun? Son yaşadığın somut bir örneği anlatır mısın?",
                reason="Pain point'i soyut fikir yerine gerçek olay üzerinden yakalamak.",
                tags=["pain_point"],
            ),
            InterviewQuestion(
                id="q_pricing",
                label="PRICING",
                question=f"{expected_price} için ödeme yapmayı düşünür müsün? Hangi fiyat aralığı makul, hangi nokta pahalı gelir?",
                reason="Türkiye pazarı için fiyat eşiğini ve paketleme sinyalini almak.",
                tags=["pricing"],
            )
        ]

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
        
    return script


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
    return [
        Persona(
            id="p1",
            name="Elif",
            age=34,
            city="İstanbul",
            segment="KOBİ e-ticaret marka sahibi",
            role_title="Growth Odaklı Kurucu",
            stance="Champion",
            price_sensitivity=7,
            digital_confidence=8,
            context=f"{market} pazarında hızlı büyümek isteyen satıcı.",
            goals=["Ürün mesajını hızla test etmek"],
            objections=["Raporun gerçek müşteri davranışını temsil etmemesi"],
            knowledge_boundary="Kendi satış operasyonu hakkında konuşabilir.",
            bio="Pazaryeri ve kendi sitesi arasında büyümeye çalışan marka sahibi.",
            attributes=persona_attributes("KOBİ e-ticaret marka sahibi", "Champion", 7, 8),
            traits=persona_traits(1, "Champion", 7, 8),
        )
    ]


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

    for persona in personas:
        original_system = db_prompt if db_prompt else build_elephant_system_prompt(persona)
        base_system = original_system
        ewma_score = 1.0  # EWMA başlangıç skoru (god_doc.md §5)

        turns: List[InterviewTurn] = [
        ]
        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
        ]

        for script_question in script:
            # 1. ACT-R Episodic Memory
            turn_memory = calculate_act_r_memory_prompt(turns, script_question)

            # 2. Turkey-specific local reflexes
            turkey_context = get_turkey_behavior_context(persona, script_question)

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
                f"Soru etiketi: {script_question.label}\n"
                f"Soru: {script_question.question}\n"
                "Kısa, somut ve Türkiye pazarı gerçeklerine uygun cevap ver."
            )
            answer = model.generate(base_system, prompt)
            quality_flags = judge_answer_quality(persona, script_question.question, answer)

            # 3. ELEPHANT & Zero-Sum Bet check
            answer, quality_flags = handle_zero_sum_bet(
                persona, script_question, answer, base_system, prompt, model, quality_flags
            )

            # 4. Echo Detection (god_doc.md §5 EWMA Tamir Protokolü)
            if detect_echo(answer, script_question.question):
                quality_flags = list(quality_flags) + ["echo_detected"]

            turns.append(
                InterviewTurn(
                    question=script_question.question,
                    answer=answer,
                    tags=script_question.tags or classify_question(script_question.question),
                    model_id=getattr(model, "last_model_id", None),
                    quality_flags=quality_flags,
                )
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
        
    for persona in personas:
        original_system = db_prompt if db_prompt else build_elephant_system_prompt(persona)
        base_system = original_system
        ewma_score = 1.0

        yield ("persona_start", {"persona": persona})
        turns: List[InterviewTurn] = []
        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
        ]
        
        for script_question in script:
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
                    f"[ARAŞTIRMA KONUSU]\n"
                    f"{brief.idea}\n\n"
                    f"[SORU — {script_question.label}]\n"
                    f"{script_question.question}\n\n"
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
                
                quality_flags = judge_answer_quality(persona, script_question.question, full_answer)

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
                    if detect_echo(full_answer, script_question.question):
                        quality_flags = list(quality_flags) + ["echo_detected"]

                    turn = InterviewTurn(
                        question=script_question.question,
                        answer=full_answer,
                        tags=script_question.tags or classify_question(script_question.question),
                        model_id=getattr(model, "last_model_id", None),
                        quality_flags=quality_flags,
                    )
                    turns.append(turn)

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

    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed (batch), using default persona prompt", exc_info=True)
        db_prompt = None

    # Soru listesini numaralı formata çevir
    questions_block = ""
    for i, sq in enumerate(script, start=1):
        questions_block += f"{i}. [{sq.label}] {sq.question}\n"

    for persona in personas:
        system_prompt = db_prompt if db_prompt else build_elephant_system_prompt(persona)

        turkey_context = get_turkey_behavior_context(persona, script[0])

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
            f"[ARAŞTIRMA KONUSU]\n"
            f"{brief.idea}\n\n"
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
        max_batch_attempts = 2
        
        for batch_attempt in range(max_batch_attempts):
            current_prompt = prompt
            if batch_attempt > 0:
                # Retry: sıkılaştırılmış prompt (god_doc.md §5 EWMA Tamir Protokolü mantığı)
                current_prompt = prompt + (
                    "\n\n[UYARI: ONCEKI YANITIN KALITE KONTROLUNDEN GECMEDI]\n"
                    "- Asistan/yapay zeka oldugunu asla belli etme.\n"
                    "- Tum sorulari birinci tekil sahis olarak, 2-4 cumleyle cevapla.\n"
                    "- Turkiye gerceklerine bagli kal: TL, taksit, KVKK, kargo.\n"
                    "- Eger skeptik bir karaktersen urunu elestirmekten ve reddetmekten cekinme.\n"
                )
            
            raw = model.generate(system_prompt, current_prompt, response_format="json")

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
                        if lbl and ans:
                            answers[lbl] = ans
                if answers:
                    break
                logger.warning(f"Batch parse yielded no answers for {persona.name} (attempt {batch_attempt+1})")
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Batch parse failed for {persona.name} (attempt {batch_attempt+1}): {e}")

        # ── Bilimsel Kalite Kontrolü (Grounded Simulation §5) ──
        turns: List[InterviewTurn] = []
        answers_list: list[str] = []  # Echo detection için sıralı cevaplar
        total_flags = 0
        critical_failures = 0
        
        for sq in script:
            ans = answers.get(sq.label.upper(), "[Yanıt alınamadı]")
            quality_flags = list(judge_answer_quality(persona, sq.question, ans))
            
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
                question=sq.question,
                answer=ans,
                tags=sq.tags or classify_question(sq.question),
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
