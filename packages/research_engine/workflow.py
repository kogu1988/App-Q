from __future__ import annotations

from .models import (
    ClarifyingQuestion,
    Evidence,
    Finding,
    InterviewQuestion,
    InterviewTurn,
    PanelRole,
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

DEFAULT_TRAIT_ORDER = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]


def persona_traits(seed: int, stance: str, price_sensitivity: int, digital_confidence: int) -> dict[str, int]:
    openness = min(92, max(35, digital_confidence * 9 + (seed * 3 % 12)))
    conscientiousness = 62 + (seed * 7 % 28)
    extraversion = 42 + (seed * 5 % 35)
    agreeableness = 72 - (seed * 6 % 24)
    neuroticism = min(88, max(25, price_sensitivity * 7 + (seed * 4 % 18)))
    if stance in {"Skeptic", "Blocker"}:
        agreeableness = max(35, agreeableness - 12)
        neuroticism = min(92, neuroticism + 10)
    if stance == "Champion":
        openness = min(96, openness + 8)
        agreeableness = min(90, agreeableness + 10)
    return {
        "Openness": openness,
        "Conscientiousness": conscientiousness,
        "Extraversion": extraversion,
        "Agreeableness": agreeableness,
        "Neuroticism": neuroticism,
    }


def persona_attributes(
    segment: str,
    stance: str,
    price_sensitivity: int,
    digital_confidence: int,
) -> dict[str, str]:
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
    panel_roles: list[PanelRole] | None = None,
) -> list[InterviewQuestion]:
    category = brief.category or "ürün"
    target = ", ".join(brief.target_users) or "hedef kullanıcılar"
    competitors = ", ".join(brief.competitors) or "mevcut alternatifler"
    expected_price = brief.expected_price or "önerilecek fiyat/paket"
    role_text = ", ".join(f"{role.role} x{role.count}" for role in panel_roles or []) or "varsayılan panel"
    script = [
        InterviewQuestion(
            id="q_context",
            label="CONTEXT",
            question=(
                f"{category} bağlamında bugün bu problemi nasıl yaşıyorsun? Son yaşadığın somut bir örneği anlatır mısın?"
            ),
            reason="Pain point'i soyut fikir yerine gerçek olay üzerinden yakalamak.",
            tags=["pain_point"],
        ),
        InterviewQuestion(
            id="q_current_alternatives",
            label="CURRENT-TOOLS",
            question=(
                f"Bugün bu ihtiyacı {competitors} gibi hangi yöntemlerle çözüyorsun ve bu yöntemlerde seni en çok ne zorluyor?"
            ),
            reason="Alternatifler, switching cost ve mevcut davranışı görünür yapmak.",
            tags=["positioning", "pain_point"],
        ),
        InterviewQuestion(
            id="q_value",
            label="VALUE-PROPOSITION",
            question=(
                f"Bu fikir {target} için hangi durumda gerçekten değerli olur, hangi durumda gereksiz veya nice-to-have kalır?"
            ),
            reason="Değer önerisini satın alma bağlamında test etmek.",
            tags=["value"],
        ),
        InterviewQuestion(
            id="q_objection",
            label="OBJECTIONS",
            question="Satın alma veya deneme kararında seni en çok ne durdurur: güven, zaman, fiyat, veri gizliliği veya başka bir şey mi?",
            reason="Ana bariyerleri ve anti-dalkavukluk sinyallerini toplamak.",
            tags=["objection", "risk"],
        ),
        InterviewQuestion(
            id="q_pricing",
            label="PRICING",
            question=(
                f"{expected_price} için ödeme yapmayı düşünür müsün? Hangi fiyat aralığı makul, hangi nokta pahalı gelir?"
            ),
            reason="Türkiye pazarı için fiyat eşiğini ve paketleme sinyalini almak.",
            tags=["pricing"],
        ),
        InterviewQuestion(
            id="q_trust",
            label="TRUST-KVKK",
            question="Bu ürün kişisel/veri/gizlilik tarafında hangi güven kanıtlarını göstermeden seni ikna edemez?",
            reason="KVKK, güven ve kanıt zinciri itirazlarını zorlamak.",
            tags=["objection", "risk"],
        ),
        InterviewQuestion(
            id="q_role_fit",
            label="ROLE-FIT",
            question=(
                f"Bu araştırmadaki rol kompozisyonu ({role_text}) içinde kendi rolün açısından ürünün en güçlü ve en zayıf tarafı ne?"
            ),
            reason="Seçilen panel rolünün cevaba yansımasını kontrol etmek.",
            tags=["positioning", "value"],
        ),
        InterviewQuestion(
            id="q_decision",
            label="DECISION",
            question="Bu ürün canlıya alınmadan önce tek bir şeyi değiştirme hakkın olsa neyi değiştirirdin ve neden?",
            reason="Ürünleştirilebilir aksiyon maddesi çıkarmak.",
            tags=["risk", "value"],
        ),
    ]
    if brief.questions:
        for index, question in enumerate(brief.questions[:4], start=1):
            script.append(
                InterviewQuestion(
                    id=f"q_user_{index}",
                    label="USER-QUESTION",
                    question=question,
                    reason="Kullanıcının brief sırasında özellikle yanıtlanmasını istediği soru.",
                    tags=classify_question(question),
                )
            )
    return script


def build_research_plan(
    brief: ResearchBrief,
    panel_roles: list[PanelRole] | None = None,
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
    return ResearchPlan(
        objective=objective,
        assumptions=assumptions,
        clarifying_questions=clarifying_questions,
        interview_questions=[item.question for item in interview_script],
        recommended_panel_size=5,
        interview_script=interview_script,
    )


def generate_personas(brief: ResearchBrief, panel_roles: list[PanelRole] | None = None) -> list[Persona]:
    if panel_roles:
        return generate_personas_from_roles(brief, panel_roles)

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
            context=f"{market} pazarında hızlı büyümek isteyen, araç denemeye açık satıcı.",
            goals=["Ürün mesajını hızla test etmek", "Reklam bütçesini boşa harcamamak"],
            objections=["Raporun gerçek müşteri davranışını temsil edip etmediği"],
            knowledge_boundary="Kendi satış operasyonu, ürün listeleme ve reklam bütçesi hakkında konuşabilir.",
            bio="Pazaryeri ve kendi sitesi arasında büyümeye çalışan, hızlı test yapmayı seven ama sonuçları kanıtla görmek isteyen marka sahibi.",
            attributes=persona_attributes("KOBİ e-ticaret marka sahibi", "Champion", 7, 8),
            traits=persona_traits(1, "Champion", 7, 8),
        ),
        Persona(
            id="p2",
            name="Mert",
            age=29,
            city="İzmir",
            segment="Performans pazarlama uzmanı",
            role_title="CRO ve Reklam Uzmanı",
            stance="Pragmatist",
            price_sensitivity=6,
            digital_confidence=9,
            context="Veri ve çıktı kalitesi görmeden bütçe ayırmayan ajans çalışanı.",
            goals=["Landing page mesajını netleştirmek", "CRO risklerini erken görmek"],
            objections=["Çıktıların müşteriye sunulabilir kalitede olmaması"],
            knowledge_boundary="Kampanya, landing page, reklam mesajı ve CRO konularında yorum yapabilir.",
            bio="Ajans müşterilerinde hızlı deney kuran, raporun sunulabilirliğine ve aksiyona dönüşmesine bakan pazarlama uzmanı.",
            attributes=persona_attributes("Performans pazarlama uzmanı", "Pragmatist", 6, 9),
            traits=persona_traits(2, "Pragmatist", 6, 9),
        ),
        Persona(
            id="p3",
            name="Selin",
            age=38,
            city="Ankara",
            segment="Kurumsal ürün yöneticisi",
            role_title="Kurumsal Ürün Karar Verici",
            stance="Skeptic",
            price_sensitivity=5,
            digital_confidence=7,
            context="Sentetik araştırmaya temkinli yaklaşan, gerçek kullanıcı kanıtı isteyen karar verici.",
            goals=["Yanlış ürün kararlarını azaltmak", "İç paydaşları ikna etmek"],
            objections=["Sentetik araştırmaya fazla güvenilmesi", "KVKK ve veri gizliliği riski"],
            knowledge_boundary="Ürün kararları, iç onay süreçleri ve risk değerlendirmesi hakkında konuşabilir.",
            bio="Yeni araçları ancak iç paydaşlara açıklanabilir kanıtla savunabilen, risk ve uyumluluk tarafını önemseyen ürün yöneticisi.",
            attributes=persona_attributes("Kurumsal ürün yöneticisi", "Skeptic", 5, 7),
            traits=persona_traits(3, "Skeptic", 5, 7),
        ),
        Persona(
            id="p4",
            name="Ahmet",
            age=45,
            city="Ankara",
            segment="Fiyat hassas pazaryeri satıcısı",
            role_title="Maliyet Odaklı Satıcı",
            stance="Blocker",
            price_sensitivity=10,
            digital_confidence=5,
            context="Yeni SaaS giderlerine dirençli, hızlı ROI görmezse ürünü reddeden kullanıcı.",
            goals=["Aylık gideri düşük tutmak", "Somut satış etkisi görmek"],
            objections=["Abonelik maliyeti", "Ek araç öğrenme zahmeti", "Sonucun soyut kalması"],
            knowledge_boundary="Küçük satıcı maliyetleri, komisyon baskısı ve nakit akışı hakkında konuşabilir.",
            bio="Komisyon, reklam ve kargo maliyetleri arasında sıkışmış; yeni abonelikleri ancak hızlı geri dönüş görürse kabul eden satıcı.",
            attributes=persona_attributes("Fiyat hassas pazaryeri satıcısı", "Blocker", 10, 5),
            traits=persona_traits(4, "Blocker", 10, 5),
        ),
        Persona(
            id="p5",
            name="Derya",
            age=32,
            city="Bursa",
            segment="Ajans stratejisti",
            role_title="Müşteri Sunumu Stratejisti",
            stance="Observer",
            price_sensitivity=6,
            digital_confidence=8,
            context="Müşteriye sunulabilir rapor kalitesi ve beyaz etiket kullanımına bakan stratejist.",
            goals=["Pitch öncesi hızlı içgörü üretmek", "Araştırmayı faturalandırılabilir hizmete çevirmek"],
            objections=["Raporun jenerik görünmesi", "Kanıt zinciri olmadan müşterinin ikna olmaması"],
            knowledge_boundary="Ajans sunumu, raporlama ve müşteri ikna süreçleri hakkında konuşabilir.",
            bio="Müşteriye satılabilir araştırma çıktısı arayan, beyaz etiket kalite ve net metodoloji bekleyen stratejist.",
            attributes=persona_attributes("Ajans stratejisti", "Observer", 6, 8),
            traits=persona_traits(5, "Observer", 6, 8),
        ),
    ]


def generate_personas_from_roles(brief: ResearchBrief, panel_roles: list[PanelRole]) -> list[Persona]:
    market = brief.market or "Türkiye"
    persona_templates = {
        "Fiyat Hassas Kullanıcı": {
            "segment": "Fiyat hassas tüketici",
            "stance": "Blocker",
            "price_sensitivity": 10,
            "digital_confidence": 5,
            "goals": ["Parasının karşılığını almak", "Gizli ücret ve taahhütlerden kaçınmak"],
            "objections": ["Fiyatın beklenenden yüksek olması", "Taksit veya ücretsiz deneme olmaması"],
        },
        "Dijital Rahat Kullanıcı": {
            "segment": "Dijital alışkanlığı yüksek kullanıcı",
            "stance": "Pragmatist",
            "price_sensitivity": 6,
            "digital_confidence": 9,
            "goals": ["Hızlı ve zahmetsiz deneyim", "Mobilde net değer görmek"],
            "objections": ["Karmaşık onboarding", "Yavaş veya eski görünen arayüz"],
        },
        "Güven Şüphecisi": {
            "segment": "Güven ve gizlilik odaklı kullanıcı",
            "stance": "Skeptic",
            "price_sensitivity": 7,
            "digital_confidence": 6,
            "goals": ["Güvenli işlem yapmak", "Verisinin nasıl kullanıldığını bilmek"],
            "objections": ["KVKK belirsizliği", "Kart/veri güvenliği riski", "Kanıtlanmamış vaatler"],
        },
        "Bütçe Sahibi Karar Verici": {
            "segment": "Bütçe sahibi karar verici",
            "stance": "Skeptic",
            "price_sensitivity": 7,
            "digital_confidence": 7,
            "goals": ["ROI görmek", "İç paydaşları ikna etmek"],
            "objections": ["Abonelik maliyeti", "Kanıt zinciri olmadan satın alma riski"],
        },
        "Operasyonel Kullanıcı": {
            "segment": "Operasyonel kullanıcı",
            "stance": "Pragmatist",
            "price_sensitivity": 6,
            "digital_confidence": 8,
            "goals": ["Günlük işi hızlandırmak", "Ek araç öğrenme yükünü azaltmak"],
            "objections": ["Mevcut iş akışına uymaması", "Kullanım zahmeti"],
        },
        "Kurumsal Şüpheci": {
            "segment": "Kurumsal şüpheci",
            "stance": "Skeptic",
            "price_sensitivity": 5,
            "digital_confidence": 7,
            "goals": ["Riskleri azaltmak", "Gizlilik ve uyumluluğu korumak"],
            "objections": ["KVKK ve veri gizliliği riski", "Sentetik çıktıya fazla güvenilmesi"],
        },
    }
    names = ["Elif", "Mert", "Selin", "Ahmet", "Derya", "Ceren", "Burak", "Zeynep", "Onur", "Aylin"]
    cities = ["İstanbul", "İzmir", "Ankara", "Bursa", "Antalya", "Konya", "Kocaeli", "Eskişehir", "Adana", "Kayseri"]
    personas: list[Persona] = []
    for role in panel_roles:
        if role.count <= 0:
            continue
        template = persona_templates.get(
            role.role,
            {
                "segment": role.role,
                "stance": "Observer",
                "price_sensitivity": 6,
                "digital_confidence": 7,
                "goals": ["Ürünün net faydasını anlamak"],
                "objections": ["Değer önerisinin belirsiz kalması"],
            },
        )
        for _ in range(role.count):
            index = len(personas)
            personas.append(
                Persona(
                    id=f"p{index + 1}",
                    name=names[index % len(names)],
                    age=26 + ((index * 4) % 23),
                    city=cities[index % len(cities)],
                    segment=str(template["segment"]),
                    role_title=role.role,
                    stance=template["stance"],  # type: ignore[arg-type]
                    price_sensitivity=int(template["price_sensitivity"]),
                    digital_confidence=int(template["digital_confidence"]),
                    context=(
                        f"{market} pazarında {role.role} rolünü temsil eder. "
                        f"Rol gerekçesi: {role.why} Araştırma konusu: {brief.title}."
                    ),
                    goals=list(template["goals"]),
                    objections=list(template["objections"]),
                    knowledge_boundary=(
                        "Kendi rolü, satın alma davranışı, alternatif kullanımı, fiyat ve güven itirazları hakkında konuşabilir."
                    ),
                    bio=(
                        f"{role.role} perspektifinden konuşan, {brief.category or 'ürün'} fikrini kendi günlük kararı, "
                        "bütçesi ve güven eşiği üzerinden değerlendiren Türkiye pazarı katılımcısı."
                    ),
                    attributes=persona_attributes(
                        str(template["segment"]),
                        str(template["stance"]),
                        int(template["price_sensitivity"]),
                        int(template["digital_confidence"]),
                    ),
                    traits=persona_traits(
                        index + 1,
                        str(template["stance"]),
                        int(template["price_sensitivity"]),
                        int(template["digital_confidence"]),
                    ),
                )
            )
    return personas


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


def run_interviews(
    brief: ResearchBrief,
    personas: list[Persona],
    model: ResearchModel,
    interview_script: list[InterviewQuestion] | None = None,
) -> list[PersonaInterview]:
    interviews: list[PersonaInterview] = []
    script = interview_script or generate_interview_script(brief)
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
        for script_question in script:
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
                f"Soru etiketi: {script_question.label}\n"
                f"Soru: {script_question.question}\n"
                "Kısa, somut ve Türkiye pazarı gerçeklerine uygun cevap ver."
            )
            answer = model.generate(system, prompt)
            turns.append(
                InterviewTurn(
                    question=script_question.question,
                    answer=answer,
                    tags=script_question.tags or classify_question(script_question.question),
                    model_id=getattr(model, "last_model_id", None),
                    quality_flags=judge_answer_quality(persona, script_question.question, answer),
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


def run_research(
    brief: ResearchBrief,
    model: ResearchModel,
    panel_roles: list[PanelRole] | None = None,
) -> ResearchReport:
    plan = build_research_plan(brief, panel_roles)
    personas = generate_personas(brief, panel_roles)
    interviews = run_interviews(brief, personas, model, plan.interview_script)
    return synthesize_report(brief, plan, personas, interviews)
