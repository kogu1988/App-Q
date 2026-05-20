from __future__ import annotations

from .models import (
    ClarifyingQuestion,
    Evidence,
    Finding,
    InterviewTurn,
    Persona,
    PersonaInterview,
    PricingInsight,
    QualityIssue,
    ResearchBrief,
    ResearchModel,
    ResearchPlan,
    ResearchReport,
)


INTERVIEW_GUIDE = [
    "Bu ürün fikrini ilk duyduğunda hangi problemi çözdüğünü düşünüyorsun?",
    "Satın alma veya deneme kararında seni en çok ne durdurur?",
    "Bu çözüm hangi durumda para ödemeye değer olur?",
    "Hangi iddia sana abartılı, eksik veya güvenilmez gelir?",
    "Bu ürünü mevcut alternatiflerle kıyaslayınca en net avantaj ve dezavantaj ne olur?",
]


def build_research_plan(brief: ResearchBrief) -> ResearchPlan:
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
    return ResearchPlan(
        objective=objective,
        assumptions=assumptions,
        clarifying_questions=clarifying_questions,
        interview_questions=INTERVIEW_GUIDE,
        recommended_panel_size=5,
    )


def generate_personas(brief: ResearchBrief) -> list[Persona]:
    market = brief.market or "Türkiye"
    return [
        Persona(
            id="p1",
            name="Elif",
            age=34,
            city="İstanbul",
            segment="KOBİ e-ticaret marka sahibi",
            stance="Champion",
            price_sensitivity=7,
            digital_confidence=8,
            context=f"{market} pazarında hızlı büyümek isteyen, araç denemeye açık satıcı.",
            goals=["Ürün mesajını hızla test etmek", "Reklam bütçesini boşa harcamamak"],
            objections=["Raporun gerçek müşteri davranışını temsil edip etmediği"],
            knowledge_boundary="Kendi satış operasyonu, ürün listeleme ve reklam bütçesi hakkında konuşabilir.",
        ),
        Persona(
            id="p2",
            name="Mert",
            age=29,
            city="İzmir",
            segment="Performans pazarlama uzmanı",
            stance="Pragmatist",
            price_sensitivity=6,
            digital_confidence=9,
            context="Veri ve çıktı kalitesi görmeden bütçe ayırmayan ajans çalışanı.",
            goals=["Landing page mesajını netleştirmek", "CRO risklerini erken görmek"],
            objections=["Çıktıların müşteriye sunulabilir kalitede olmaması"],
            knowledge_boundary="Kampanya, landing page, reklam mesajı ve CRO konularında yorum yapabilir.",
        ),
        Persona(
            id="p3",
            name="Selin",
            age=38,
            city="Ankara",
            segment="Kurumsal ürün yöneticisi",
            stance="Skeptic",
            price_sensitivity=5,
            digital_confidence=7,
            context="Sentetik araştırmaya temkinli yaklaşan, gerçek kullanıcı kanıtı isteyen karar verici.",
            goals=["Yanlış ürün kararlarını azaltmak", "İç paydaşları ikna etmek"],
            objections=["Sentetik araştırmaya fazla güvenilmesi", "KVKK ve veri gizliliği riski"],
            knowledge_boundary="Ürün kararları, iç onay süreçleri ve risk değerlendirmesi hakkında konuşabilir.",
        ),
        Persona(
            id="p4",
            name="Ahmet",
            age=45,
            city="Ankara",
            segment="Fiyat hassas pazaryeri satıcısı",
            stance="Blocker",
            price_sensitivity=10,
            digital_confidence=5,
            context="Yeni SaaS giderlerine dirençli, hızlı ROI görmezse ürünü reddeden kullanıcı.",
            goals=["Aylık gideri düşük tutmak", "Somut satış etkisi görmek"],
            objections=["Abonelik maliyeti", "Ek araç öğrenme zahmeti", "Sonucun soyut kalması"],
            knowledge_boundary="Küçük satıcı maliyetleri, komisyon baskısı ve nakit akışı hakkında konuşabilir.",
        ),
        Persona(
            id="p5",
            name="Derya",
            age=32,
            city="Bursa",
            segment="Ajans stratejisti",
            stance="Observer",
            price_sensitivity=6,
            digital_confidence=8,
            context="Müşteriye sunulabilir rapor kalitesi ve beyaz etiket kullanımına bakan stratejist.",
            goals=["Pitch öncesi hızlı içgörü üretmek", "Araştırmayı faturalandırılabilir hizmete çevirmek"],
            objections=["Raporun jenerik görünmesi", "Kanıt zinciri olmadan müşterinin ikna olmaması"],
            knowledge_boundary="Ajans sunumu, raporlama ve müşteri ikna süreçleri hakkında konuşabilir.",
        ),
    ]


def classify_question(question: str) -> list[str]:
    lower = question.lower()
    tags: list[str] = []
    if "problem" in lower or "çözdüğünü" in lower:
        tags.append("pain_point")
    if "durdurur" in lower or "güvenilmez" in lower:
        tags.append("objection")
    if "para" in lower or "fiyat" in lower:
        tags.append("pricing")
    if "avantaj" in lower or "dezavantaj" in lower:
        tags.extend(["value", "positioning"])
    return tags or ["risk"]


def judge_answer_quality(persona: Persona, question: str, answer: str) -> list[str]:
    flags: list[str] = []
    lower = answer.lower()
    if any(marker in lower for marker in ["yapay zeka", "asistan", "model olarak", "persona şöyle"]):
        flags.append("meta_tone")
    if "<think>" in lower or "</think>" in lower:
        flags.append("visible_reasoning")
    if len(answer.strip()) < 80:
        flags.append("too_short")
    if persona.stance in {"Skeptic", "Blocker"} and not any(
        marker in lower for marker in ["güven", "risk", "pahalı", "kanıt", "emin", "itiraz", "şüphe", "kvkk"]
    ):
        flags.append("weak_skepticism")
    if "fiyat" in question.lower() or "para" in question.lower():
        if not any(marker in lower for marker in ["tl", "pahalı", "ucuz", "bütçe", "abonelik", "rapor başı"]):
            flags.append("weak_pricing_specificity")
    if not any(
        marker in lower
        for marker in ["türkiye", "tl", "taksit", "kargo", "komisyon", "kvkk", "bütçe", "pazaryeri", "ajans"]
    ):
        flags.append("weak_turkey_context")
    return flags


def run_interviews(brief: ResearchBrief, personas: list[Persona], model: ResearchModel) -> list[PersonaInterview]:
    interviews: list[PersonaInterview] = []
    system = (
        "Tek bir izole Türk pazar araştırması personasını simüle ediyorsun. "
        "Araştırmacıyı memnun etmeye çalışma. Profilinle çelişme. Emin değilsen belirsizliği söyle."
    )
    for persona in personas:
        turns: list[InterviewTurn] = []
        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
        ]
        for question in INTERVIEW_GUIDE:
            prompt = (
                f"Araştırma brief'i: {brief.idea}\n"
                f"Hedef kullanıcılar: {', '.join(brief.target_users) or 'Belirtilmedi'}\n"
                f"Persona: {persona.name}, {persona.age}, {persona.city}, {persona.segment}\n"
                f"Duruş: {persona.stance}\n"
                f"Fiyat hassasiyeti: {persona.price_sensitivity}/10\n"
                f"Dijital özgüven: {persona.digital_confidence}/10\n"
                f"Bağlam: {persona.context}\n"
                f"Hedefler: {', '.join(persona.goals)}\n"
                f"İtirazlar: {', '.join(persona.objections)}\n"
                f"Bilgi sınırı: {persona.knowledge_boundary}\n"
                f"Soru: {question}\n"
                "Kısa, somut ve Türkiye pazarı gerçeklerine uygun cevap ver."
            )
            answer = model.generate(system, prompt)
            turns.append(
                InterviewTurn(
                    question=question,
                    answer=answer,
                    tags=classify_question(question),
                    model_id=getattr(model, "last_model_id", None),
                    quality_flags=judge_answer_quality(persona, question, answer),
                )
            )
        interviews.append(PersonaInterview(persona=persona, turns=turns, consistency_notes=consistency_notes))
    return interviews


def summarize_model_usage(interviews: list[PersonaInterview]) -> dict[str, int]:
    usage: dict[str, int] = {}
    for interview in interviews:
        for turn in interview.turns:
            model_id = turn.model_id or "unknown"
            usage[model_id] = usage.get(model_id, 0) + 1
    return usage


def collect_quality_issues(interviews: list[PersonaInterview]) -> list[QualityIssue]:
    issue_text = {
        "meta_tone": "Cevapta asistan/meta tonu var.",
        "visible_reasoning": "Cevapta görünür muhakeme bloğu var.",
        "too_short": "Cevap karar çıkarmak için fazla kısa.",
        "weak_skepticism": "Skeptik/bloklayıcı persona yeterince sert itiraz üretmedi.",
        "weak_pricing_specificity": "Fiyat sorusunda TL, bütçe, abonelik veya ödeme modeli somutluğu zayıf.",
        "weak_turkey_context": "Türkiye pazarı bağlamı zayıf.",
    }
    issues: list[QualityIssue] = []
    for interview in interviews:
        for turn in interview.turns:
            for flag in turn.quality_flags:
                issues.append(
                    QualityIssue(
                        persona_id=interview.persona.id,
                        persona_name=interview.persona.name,
                        question=turn.question,
                        severity="fail" if flag in {"meta_tone", "visible_reasoning"} else "warning",
                        issue=issue_text.get(flag, flag),
                        recommendation="Bu cevabı yeniden üret veya raporda düşük güvenle kullan.",
                    )
                )
    return issues


def build_pain_point_matrix(interviews: list[PersonaInterview]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for interview in interviews:
        pain_answers = [turn.answer for turn in interview.turns if "pain_point" in turn.tags]
        objection_answers = [turn.answer for turn in interview.turns if "objection" in turn.tags]
        pricing_answers = [turn.answer for turn in interview.turns if "pricing" in turn.tags]
        rows.append(
            {
                "persona": interview.persona.name,
                "segment": interview.persona.segment,
                "primary_pain": pain_answers[0] if pain_answers else "Belirlenmedi",
                "main_objection": objection_answers[0] if objection_answers else "Belirlenmedi",
                "pricing_signal": pricing_answers[0] if pricing_answers else "Belirlenmedi",
            }
        )
    return rows


def collect_evidence(interviews: list[PersonaInterview], tag: str, limit: int = 4) -> list[Evidence]:
    evidence: list[Evidence] = []
    for interview in interviews:
        for turn in interview.turns:
            if tag in turn.tags:
                evidence.append(
                    Evidence(
                        persona_id=interview.persona.id,
                        persona_name=interview.persona.name,
                        stance=interview.persona.stance,
                        quote=turn.answer,
                        source_question=turn.question,
                    )
                )
    return evidence[:limit]


def synthesize_report(
    brief: ResearchBrief,
    plan: ResearchPlan,
    personas: list[Persona],
    interviews: list[PersonaInterview],
) -> ResearchReport:
    objection_evidence = collect_evidence(interviews, "objection")
    pricing_evidence = collect_evidence(interviews, "pricing")
    value_evidence = collect_evidence(interviews, "value")
    pain_evidence = collect_evidence(interviews, "pain_point")

    findings = [
        Finding(
            title="Güvenilirlik ana satın alma bariyeri",
            category="objection",
            summary=(
                "Kullanıcılar sentetik araştırmanın hızını değerli bulabilir, ancak çıktının gerçek müşteri "
                "davranışını ne kadar temsil ettiğini sorgular. Kanıt zinciri ve sınırlılık beyanı şart."
            ),
            confidence=0.72,
            evidence=objection_evidence,
            implication="Ürün raporlarında her bulgu persona alıntısına bağlanmalı ve kesinlik dili sınırlanmalı.",
        ),
        Finding(
            title="En güçlü değer önerisi bütçe yakmadan ön test",
            category="value",
            summary=(
                "Ajanslar, e-ticaret satıcıları ve ürün ekipleri için ana fayda; kampanya, fiyat veya ürün "
                "mesajını canlı trafik veya geliştirme bütçesi harcamadan önce test etmek."
            ),
            confidence=0.70,
            evidence=value_evidence or pain_evidence,
            implication="Pazarlama mesajı 'gerçek araştırmanın yerine geçer' değil, 'karar öncesi hızlı ön filtre' olmalı.",
        ),
        Finding(
            title="Türkiye pazarı için fiyat eşiği düşük tutulmalı",
            category="pricing",
            summary=(
                "KOBİ ve pazaryeri satıcısı segmentinde abonelik direnci yüksek. İlk paket düşük giriş maliyetli "
                "ve somut rapor çıktısı odaklı olmalı."
            ),
            confidence=0.68,
            evidence=pricing_evidence,
            implication="MVP satışında self-serve SaaS yerine rapor başı ürünleştirilmiş hizmet daha uygulanabilir.",
        ),
    ]

    pricing = PricingInsight(
        acceptable_range="İlk MVP için rapor başı hizmet modeli; self-serve abonelik daha sonra test edilmeli.",
        resistance_points=[
            "Aylık sabit SaaS gideri",
            "Sentetik çıktıya güven sorunu",
            "Raporun müşteriye sunulabilir olmaması",
        ],
        packaging_suggestion=(
            "48 saatlik ürünleştirilmiş araştırma raporu, ardından düşük fiyatlı tekrar test paketi."
        ),
        evidence=pricing_evidence,
    )

    recommendations = [
        "İlk sürümü lokal operatör aracı olarak tasarla; eşzamanlılık yerine sıralı persona görüşmesi kullan.",
        "E-ticaret araştırmalarında Trendyol odaklı model, B2B/SaaS araştırmalarında genel model route et.",
        "Rapor çıktısını pain point, itiraz, fiyat hassasiyeti, mesajlaşma ve doğrulama adımlarına böl.",
        "KVKK dilini kesin uyumluluk iddiası yerine veri yerelliği ve üçüncü taraf API maruziyetini azaltma olarak kur.",
    ]
    validation_next_steps = [
        "3 gerçek ürün fikriyle pilot çalıştır ve bulguları kurucu/ürün sahibi geri bildirimiyle kıyasla.",
        "Her raporda en az 5 persona alıntısı ve her kritik bulgu için kanıt zinciri zorunlu kıl.",
        "Bir gerçek kullanıcı görüşmesiyle sentetik rapordaki en riskli varsayımı doğrula veya çürüt.",
    ]
    limitations = [
        "Bu çıktı istatistiksel pazar araştırması değildir; yön gösterici hipotez üretir.",
        "Sentetik personalar gerçek duygu, sosyal baskı ve satın alma davranışını birebir deneyimlemez.",
        "Model ve veri kaynaklarının lisans, KVKK ve telif uygunluğu ticari kullanımdan önce ayrıca incelenmelidir.",
    ]
    quality_issues = collect_quality_issues(interviews)
    executive_summary = [
        "App-Q için en güçlü konumlandırma, canlı trafik veya geliştirme bütçesi harcanmadan önce hızlı ön test yapma vaadidir.",
        "Satın alma bariyeri güvenilirliktir: raporun gerçek kullanıcı görüşmesi yerine sentetik hipotez ürettiği açıkça gösterilmelidir.",
        "KOBİ ve pazaryeri segmentinde rapor başı hizmet modeli, erken aşamada aylık abonelikten daha düşük direnç üretir.",
        "Raporun ticari değeri, her bulgunun persona alıntısı ve sınırlılık notuyla desteklenmesine bağlıdır.",
    ]
    action_items = [
        "Satış teklifini '48 saatte karar öncesi risk raporu' olarak paketle.",
        "Her müşteri raporunda bulgu başına en az iki persona kanıtı göster.",
        "İlk fiyatı rapor başı hizmet olarak tut; aboneliği tekrar eden müşterilerde test et.",
        "KVKK iddiasını abartma; yerel çalışma, veri minimizasyonu ve üçüncü taraf API kullanmama mesajını öne çıkar.",
        "Kalite uyarısı alan cevapları müşteri raporunda kullanmadan önce yeniden üret.",
    ]

    return ResearchReport(
        title=brief.title,
        executive_summary=executive_summary,
        plan=plan,
        personas=personas,
        interviews=interviews,
        findings=findings,
        pricing=pricing,
        pain_point_matrix=build_pain_point_matrix(interviews),
        action_items=action_items,
        quality_issues=quality_issues,
        recommendations=recommendations,
        validation_next_steps=validation_next_steps,
        limitations=limitations,
        model_usage=summarize_model_usage(interviews),
    )


def run_research(brief: ResearchBrief, model: ResearchModel) -> ResearchReport:
    plan = build_research_plan(brief)
    personas = generate_personas(brief)
    interviews = run_interviews(brief, personas, model)
    return synthesize_report(brief, plan, personas, interviews)
