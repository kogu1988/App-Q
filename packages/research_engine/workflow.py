from __future__ import annotations

from .models import (
    ClarifyingQuestion,
    Evidence,
    Finding,
    InterviewTurn,
    Persona,
    PersonaInterview,
    PricingInsight,
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
            turns.append(InterviewTurn(question=question, answer=answer, tags=classify_question(question)))
        interviews.append(PersonaInterview(persona=persona, turns=turns, consistency_notes=consistency_notes))
    return interviews


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

    return ResearchReport(
        title=brief.title,
        plan=plan,
        personas=personas,
        interviews=interviews,
        findings=findings,
        pricing=pricing,
        recommendations=recommendations,
        validation_next_steps=validation_next_steps,
        limitations=limitations,
    )


def run_research(brief: ResearchBrief, model: ResearchModel) -> ResearchReport:
    plan = build_research_plan(brief)
    personas = generate_personas(brief)
    interviews = run_interviews(brief, personas, model)
    return synthesize_report(brief, plan, personas, interviews)
