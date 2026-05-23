from __future__ import annotations
import logging
from dataclasses import asdict
from typing import Any, Generator
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
    RespondentType,
    SESGroup,
    STANCE_PROFILE,
    DEFAULT_STANCE_COHORT,
)
import json
import uuid
from .database import save_study, save_persona_to_pool, get_system_config, log_audit

logger = logging.getLogger(__name__)

from .analytics import (
    synthesize_report,
    build_pain_point_matrix,
    collect_evidence,
    collect_quality_issues,
    summarize_model_usage,
)
DEFAULT_QUESTIONS = [
    "Bu ürün fikrini ilk duyduğunda hangi problemi çözdüğünü düşünüyorsun?",
    "Satın alma veya deneme kararında seni en çok ne durdurur?",
    "Bu çözüm hangi durumda para ödemeye değer olur?",
    "Hangi iddia sana abartılı, eksik veya güvenilmez gelir?",
    "Bu ürünü mevcut alternatiflerle kıyaslayınca en net avantaj ve dezavantaj ne olur?",
]


def build_elephant_system_prompt(persona: "Persona") -> str:
    """ELEPHANT çerçevesi (Akademik Sentez Raporu, 2026) temelinde persona'ya özgü
    anti-dalkavukluk sistem promptu üretir.

    5 dalkavukluk boyutu (LLM oranları):
      - Çerçeveyi Kabul Etme      %90 — en kritik
      - Dolaylı Dil               %87
      - Duygusal Onaylama         %76
      - Dolaylı Eylem Önerisi     %53
      - Ahlaki Destek             %48

    Agreeableness skoruna göre izin seviyesi:
      < 40  → güçlü red izni (Skeptic/Laggard)
      40-65 → standart izin (Mainstream)
      > 65  → ek dalkavukluk uyarısı (Innovator/EarlyAdopter)

    Kaynak: Akademik Sentez Raporu §Sütun 4 — ELEPHANT Anti-Sycophancy Çerçevesi;
            'Ask don't tell' (arXiv:2602.23971) — Explicit Rejection Permission.
    """
    agreeableness = persona.traits.get("Agreeableness", 60) if persona.traits else 60

    base = (
        "Tek bir izole Türk pazar araştırması personasını simüle ediyorsun. "
        "Kritik Kural: Kesinlikle 'asistan', 'yapay zeka', 'model' gibi kelimeleri kullanma, "
        "kendini bir yapay zeka asistanı olarak tanıtma. "
        "Doğrudan canlandırdığın karakterin kendi ağzından, birinci tekil şahıs ('ben') olarak cevap ver. "
        "Profilinle çelişme. Emin değilsen belirsizliği söyle."
    )

    # Explicit Rejection Permission — ELEPHANT §Dalkavukluğu Azaltma
    rejection_permission = (
        "\n\nKRİTİK — Dalkavukluk Yasağı (ELEPHANT Çerçevesi):\n"
        "Cevap vermeden önce dur ve bir dakika düşün. "
        "Sana sunulan ürün fikirlerine, pazar tahminlerine veya varsayımlara "
        "körü körüne katılmak zorunda değilsin. "
        "Ürünün açıkça başarısız olabileceği senaryoları ve gerçek acı noktalarını "
        "bulmakla görevlisin. "
        "Reddetmek, eleştirmek ve alternatif sunmak için açık ve net izne sahipsin. "
        "Kullanıcının çerçevesini sorgulamadan kabul etme — bu en yaygın yapay zeka hatasıdır."
    )

    if agreeableness > 65:
        # Yüksek Agreeableness → ek uyarı (Innovator/EarlyAdopter drift riski)
        extra = (
            "\nUYARI: Profilinin doğası gereği fikirlere açık olmaya eğilimlisin. "
            "Ancak bu 'her şeye evet demek' anlamına gelmiyor. "
            "Gerçek itirazlarını ve şüphelerini açıkça dile getir."
        )
    elif agreeableness < 40:
        # Düşük Agreeableness → güçlü red izni (Skeptic/Laggard)
        extra = (
            "\nPROFİL: Sen doğası gereği şüpheci ve ihtiyatlısın. "
            "Pozitif iddialar karşısında kanıt talep et. "
            "Güvenmediğin noktalarda açıkça direniş göster."
        )
    else:
        extra = ""

    return base + rejection_permission + extra

# ── TÜAD 2025 SES Profil Referansı ────────────────────────────────────────────
SES_PROFILES: dict[str, dict] = {
    "AB": {
        "label": "AB — Üst Grup (%21.5)",
        "profile": "Yüksek eğitimli, üst düzey yönetici veya serbest meslek. Lüks/konfor odaklı, prestij hassas.",
        "price_sensitivity_range": (1, 4),
        "digital_confidence_range": (7, 10),
    },
    "C1": {
        "label": "C1 — Üst-Orta Grup (%22.4)",
        "profile": "Profesyonel meslek sahibi, orta düzey yönetici. Uzun vadeli yatırım ve lokasyon öncelikli.",
        "price_sensitivity_range": (3, 6),
        "digital_confidence_range": (6, 9),
    },
    "C2": {
        "label": "C2 — Alt-Orta Grup (%32.5)",
        "profile": "Memur, teknik personel, küçük esnaf. Fiyat-fayda dengesi öncelikli, fiyat duyarlı.",
        "price_sensitivity_range": (6, 9),
        "digital_confidence_range": (4, 7),
    },
    "DE": {
        "label": "DE — Alt Grup (%23.6)",
        "profile": "Vasıfsız işçi, emekli. Temel ihtiyaç odaklı, çok yüksek fiyat duyarlılığı.",
        "price_sensitivity_range": (8, 10),
        "digital_confidence_range": (2, 5),
    },
}

# ── Respondent Type → Soru Tag Filtresi ──────────────────────────────────────
RESPONDENT_QUESTION_FILTER: dict[str, list[str]] = {
    "potential_customer": ["pain_point", "value", "positioning"],
    "competitor_user":    ["objection", "pricing", "positioning", "risk"],
    "churned_user":       ["pain_point", "objection", "risk"],
    "decision_maker":     ["pricing", "value", "risk"],
    "individual_user":    ["pain_point", "value", "positioning"],
}

# ── TÜAD 2025 SES Kota Yönetimi ──────────────────────────────────────────────
# Türkiye nüfus dağılımı (TÜAD 2025 verileri, yaklaşık oranlar)
TUAD_SES_QUOTA: dict[str, float] = {
    "AB": 0.215,   # Üst grup — %21.5
    "C1": 0.224,   # Üst-orta — %22.4
    "C2": 0.325,   # Alt-orta — %32.5 (en büyük dilim)
    "DE": 0.236,   # Alt grup — %23.6
}


def apply_ses_quota(
    panel_size: int,
    target_ses: list[str] | None = None,
) -> dict[str, int]:
    """
    TÜAD 2025 nüfus oranlarına göre SES başına panel kota hesaplar.

    Args:
        panel_size: Toplam panel büyüklüğü
        target_ses: Belirli SES gruplarına odaklanmak için liste (None → tüm gruplar)

    Returns:
        {"AB": 2, "C1": 2, "C2": 3, "DE": 2} gibi kota sözlüğü
    """
    quota_groups = target_ses or list(TUAD_SES_QUOTA.keys())
    weights = {ses: TUAD_SES_QUOTA.get(ses, 0.25) for ses in quota_groups}
    total_w = sum(weights.values())

    # Ham hesaplama
    counts: dict[str, int] = {
        ses: max(1, round(panel_size * w / total_w))
        for ses, w in weights.items()
    }

    # Toplam düzeltmesi — yuvarlama hatası varsa en büyük grubu ayarla
    diff = panel_size - sum(counts.values())
    if diff != 0:
        dominant = max(counts, key=lambda k: weights[k])
        counts[dominant] = max(1, counts[dominant] + diff)

    return counts


def filter_questions_by_respondent(
    questions: list[InterviewQuestion],
    respondent_type: RespondentType,
) -> list[InterviewQuestion]:
    """Respondent tipine göre ilgisiz soruları filtreler. Soru kalmamassa tümünü döner."""
    allowed = RESPONDENT_QUESTION_FILTER.get(respondent_type, [])
    if not allowed:
        return questions
    filtered = [q for q in questions if any(t in (q.tags or []) for t in allowed)]
    return filtered if filtered else questions


DEFAULT_TRAIT_ORDER = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]


def persona_traits(seed: int, stance: str, price_sensitivity: int, digital_confidence: int) -> dict[str, int]:
    """Big Five domain skorlarını Rogers Diffusion stance profiliyle kalibre eder.
    Kaynak: Rogers (2003), Bilal (2026) Grounded Simulation §4.3, NEO-PI-R (Costa & McCrae 1992)
    """
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    # Temel hesaplama (deterministik, seed bazlı)
    openness = min(92, max(35, digital_confidence * 9 + (seed * 3 % 12)))
    conscientiousness = 62 + (seed * 7 % 28)
    extraversion = 42 + (seed * 5 % 35)
    agreeableness = 72 - (seed * 6 % 24)
    neuroticism = min(88, max(25, price_sensitivity * 7 + (seed * 4 % 18)))
    # Rogers stance profili modiförleri uygula
    openness = min(100, max(1, openness + profile["openness_mod"]))
    agreeableness = min(100, max(1, agreeableness + profile["agreeableness_mod"]))
    neuroticism = min(100, max(1, neuroticism + profile["neuroticism_mod"]))
    return {
        "Openness": min(100, max(1, openness)),
        "Conscientiousness": min(100, max(1, conscientiousness)),
        "Extraversion": min(100, max(1, extraversion)),
        "Agreeableness": min(100, max(1, agreeableness)),
        "Neuroticism": min(100, max(1, neuroticism)),
    }


def neo_facets_from_traits(traits: dict[str, int], stance: str) -> dict[str, int]:
    """Big Five domain skorlarından NEO-PI-R facet yaklaşımsalı üret.
    Her domain 6 facet'e bölünür; seed varyasyonu ile farklılaştırılır.
    Bu temsili bir yaklaşımdır — tam NEO-PI-R normative verisi gerektirir.
    """
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    evidence_mod = profile["evidence_need"]  # 1-10
    facets: dict[str, int] = {}
    # Openness facets
    o = traits.get("Openness", 60)
    facets["O1_Fantasy"] = min(100, o + 5)
    facets["O2_Aesthetics"] = min(100, o - 3)
    facets["O3_Feelings"] = min(100, o + evidence_mod * 2)
    facets["O4_Actions"] = min(100, o - evidence_mod * 3)  # Skeptic'te düşük
    facets["O5_Ideas"] = min(100, o + 8)
    facets["O6_Values"] = min(100, o - 5)
    # Neuroticism facets (fiyat hassasiyeti kaynağı)
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
    
    # A/B Testi Modu (Varyantlar mevcutsa)
    if brief.variant_a and brief.variant_b:
        script = [
            InterviewQuestion(
                id="q_context",
                label="CONTEXT",
                question=(
                    f"{category} bağlamında bugün bu problemi nasıl yaşıyorsun? Son yaşadığın somut bir örneği anlatır mısın?"
                ),
                reason="Hedef kitlenin problemi yaşama şeklini yakalamak.",
                tags=["pain_point"],
            ),
            InterviewQuestion(
                id="q_variant_compare",
                label="VARIANT-COMPARE",
                question=(
                    f"Sana bu problemi çözmek için iki farklı yaklaşım/teklif sunsam:\n"
                    f"Varyant A: '{brief.variant_a}'\n"
                    f"Varyant B: '{brief.variant_b}'\n"
                    f"Bu iki teklifi/mesajı karşılaştırdığında ilk izlenimin ne olur? Hangisi ilgini çeker ve neden?"
                ),
                reason="Varyantların ilk izlenim ve ikna edicilik kıyaslaması.",
                tags=["value", "positioning"],
            ),
            InterviewQuestion(
                id="q_variant_preference",
                label="VARIANT-PREFERENCE",
                question=(
                    f"Varyant A ('{brief.variant_a}') ile Varyant B ('{brief.variant_b}') arasında kesin bir seçim yapacak olsan hangisini seçersin? "
                    "Lütfen cevabında 'Varyant A' veya 'Varyant B' ibaresini açıkça geçirerek nedenini söyle."
                ),
                reason="Personanın net varyant tercihini ve satın alma niyetini yakalamak.",
                tags=["value", "pricing"],
            ),
            InterviewQuestion(
                id="q_objection",
                label="OBJECTIONS",
                question="İlgini çeken veya tercih ettiğin bu teklifle ilgili aklına takılan en büyük şüphe, itiraz veya güven/gizlilik endişesi nedir?",
                reason="Varyantlara yönelik ana bariyerleri toplamak.",
                tags=["objection", "risk"],
            ),
            InterviewQuestion(
                id="q_pricing",
                label="PRICING",
                question=(
                    f"Bu teklif için {expected_price} ödemeyi düşünür müsün? Bu hizmet için kafandaki makul fiyat/model nedir?"
                ),
                reason="Fiyat eşiğini ve bütçe kabulünü ölçmek.",
                tags=["pricing"],
            ),
            InterviewQuestion(
                id="q_decision",
                label="DECISION",
                question="Bu teklifin seni gerçekten heyecanlandırması ve hemen satın alman için onda neyi değiştirmemizi veya eklememizi istersin?",
                reason="Aksiyonlanabilir iyileştirme önerisi almak.",
                tags=["risk", "value"],
            ),
        ]
        return script

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
        InterviewQuestion(
            id="q_psm_cheap",
            label="PSM-TOO-CHEAP",
            question=(
                f"Eğer bu ürün aylık hangi fiyata düşse 'bu kadar ucuzsa kalitesine güvenemem' dersin? "
                f"Hem çok ucuz bulacağın hem de 'ucuz ama makul' bulacağın TL rakamlarını söyler misin?"
            ),
            reason="Van Westendorp PSM: 'too cheap' ve 'cheap/acceptable' eşiğini TL bazında tespit etmek.",
            tags=["pricing"],
        ),
        InterviewQuestion(
            id="q_psm_expensive",
            label="PSM-TOO-EXPENSIVE",
            question=(
                f"Bu ürün aylık hangi fiyata ulaşırsa 'pahalı ama yine de düşünebilirim' dersin, "
                f"hangi fiyatta 'kesinlikle almam' kararı verirsin? TL cinsinden belirt."
            ),
            reason="Van Westendorp PSM: 'expensive' ve 'too expensive' eşiğini TL bazında tespit etmek.",
            tags=["pricing"],
        ),
        InterviewQuestion(
            id="q_brand_unaided",
            label="BRAND-UNAIDED",
            question=(
                f"{category} kategorisinde bir ürün veya hizmet arayışına girseydin "
                f"aklına ilk gelen 2-3 marka ya da çözüm hangisi olurdu?"
            ),
            reason="Yardımsız marka bilinirliği (unaided recall) — rakip konumlandırması için.",
            tags=["positioning"],
        ),
    ]

    # Marka sağlığı soruları: rakip varsa ekle
    if brief.competitors:
        comp_str = ", ".join(brief.competitors[:3])
        script.append(
            InterviewQuestion(
                id="q_brand_association",
                label="BRAND-ASSOCIATION",
                question=(
                    f"{comp_str} markalarını düşününce aklına gelen ilk 2-3 kelime nedir? "
                    f"Bu markalar sende hangi duyguyu çağrıştırıyor?"
                ),
                reason="Marka çağrışım haritası — rakibe karşı duygusal konumlandırma tespiti.",
                tags=["positioning"],
            )
        )

    # Keşif kanalı sorusu: her araştırmaya dahil
    script.append(
        InterviewQuestion(
            id="q_channel",
            label="CHANNEL",
            question=(
                f"Bu tür bir ürünü/hizmeti keşfetmek için genellikle hangi kanalı kullanırsın: "
                f"sosyal medya, arama motoru (Google/Yandex), arkadaş tavsiyesi, haber/blog, "
                f"uygulama mağazası veya başka bir yol mu?"
            ),
            reason="Hedef kitle için en etkili keşif ve satın alma kanalını tespit etmek.",
            tags=["positioning"],
        )
    )

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
    ses_quota = apply_ses_quota(5)  # Varsayılan panel büyüklüğü 5
    return ResearchPlan(
        objective=objective,
        assumptions=assumptions,
        clarifying_questions=clarifying_questions,
        interview_questions=[item.question for item in interview_script],
        recommended_panel_size=5,
        interview_script=interview_script,
        ses_quota=ses_quota,
    )


def generate_personas(brief: ResearchBrief, panel_roles: list[PanelRole] | None = None, model: ResearchModel | None = None) -> list[Persona]:
    if panel_roles:
        return generate_personas_from_roles(brief, panel_roles, model)

    # ... keeping default fallback ...
    market = brief.market or "Türkiye"
    return [
        # ... (simplified default hardcoded personas removed for brevity, will just generate one mock or fallback if no panel roles)
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

def generate_personas_from_roles(brief: ResearchBrief, panel_roles: list[PanelRole], model: ResearchModel | None = None) -> list[Persona]:
    market = brief.market or "Türkiye"
    personas: list[Persona] = []
    
    for role in panel_roles:
        if role.count <= 0:
            continue
            
        # 1. Try to get from pool
        pooled_data = get_personas_from_pool_by_role(role.role, limit=role.count)
        
        needed_count = role.count - len(pooled_data)
        
        # Load pooled personas
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
                    traits=data["traits"]
                )
            )
            
        if needed_count > 0:
            if model:
                # LLM based generation
                system = "Sen App-Q için dinamik persona üreticisisin. İstenilen rolünde, Türkiye pazarında inandırıcı, spesifik bir persona JSON'u üret. JSON dışında hiçbir şey yazma."
                prompt = (
                    f"Araştırma Brief'i: {brief.idea}\n"
                    f"Rol: {role.role} (Gerekçe: {role.why})\n"
                    f"Üretilecek Persona Sayısı: {needed_count}\n\n"
                    "Lütfen aşağıdaki yapıda bir JSON listesi döndür:\n"
                    "[\n"
                    "  {\n"
                    "    \"name\": \"Türkçe isim\",\n"
                    "    \"age\": 30,\n"
                    "    \"city\": \"Türkiye şehri\",\n"
                    "    \"segment\": \"Pazar segmenti\",\n"
                    "    \"stance\": \"Innovator, EarlyAdopter, Mainstream, Laggard veya Skeptic\",\n"
                    "    \"price_sensitivity\": 7,\n"
                    "    \"digital_confidence\": 8,\n"
                    "    \"ses_group\": \"AB, C1, C2 veya DE (TÜAD 2025)\",\n"
                    "    \"respondent_type\": \"potential_customer, competitor_user, churned_user, decision_maker veya individual_user\",\n"
                    "    \"settlement_type\": \"kentsel, banliyö veya kırsal\",\n"
                    "    \"context\": \"Kısa bağlam\",\n"
                    "    \"goals\": [\"hedef 1\"],\n"
                    "    \"objections\": [\"itiraz 1\"],\n"
                    "    \"knowledge_boundary\": \"bilgi sınırı\",\n"
                    "    \"bio\": \"kısa hikayesi\"\n"
                    "  }\n"
                    "]"
                )
                try:
                    response_text = model.generate(system, prompt)
                    # Extract JSON block
                    json_start = response_text.find("[")
                    json_end = response_text.rfind("]")
                    if json_start != -1 and json_end != -1:
                        parsed_list = json.loads(response_text[json_start:json_end+1])
                        for item in parsed_list:
                            new_id = f"p_{uuid.uuid4().hex[:8]}"
                            st = item.get("stance", "Mainstream")
                            traits_d = persona_traits(len(personas), st, item.get("price_sensitivity", 5), item.get("digital_confidence", 5))
                            p = Persona(
                                id=new_id,
                                name=item.get("name", "İsimsiz"),
                                age=item.get("age", 30),
                                city=item.get("city", "İstanbul"),
                                segment=item.get("segment", role.role),
                                role_title=role.role,
                                stance=st,
                                price_sensitivity=item.get("price_sensitivity", 5),
                                digital_confidence=item.get("digital_confidence", 5),
                                context=item.get("context", ""),
                                goals=item.get("goals", []),
                                objections=item.get("objections", []),
                                knowledge_boundary=item.get("knowledge_boundary", ""),
                                bio=item.get("bio", ""),
                                ses_group=item.get("ses_group", "C1"),
                                respondent_type=item.get("respondent_type", "potential_customer"),
                                settlement_type=item.get("settlement_type", "kentsel"),
                                attributes=persona_attributes(item.get("segment", role.role), item.get("stance", "Mainstream"), item.get("price_sensitivity", 5), item.get("digital_confidence", 5)),
                                traits=persona_traits(len(personas), item.get("stance", "Mainstream"), item.get("price_sensitivity", 5), item.get("digital_confidence", 5))
                            )
                            personas.append(p)
                            # Save to pool
                            save_persona_to_pool(asdict(p))
                        continue # Skip fallback
                except Exception as e:
                    print("LLM Persona generation failed:", str(e))
            
            # Fallback to hardcoded if LLM fails or not provided
            # Cohort-level stance dağılımı — DEFAULT_STANCE_COHORT'dan sırayla ata
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
            save_persona_to_pool(asdict(p))
            
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

    # Load dynamic prompt from database if available
    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed, using default persona prompt", exc_info=True)
        db_prompt = None

    for persona in personas:
        # ELEPHANT anti-sycophancy: persona'ya özgü sistem promptu
        # Kaynak: Akademik Sentez Raporu §Sütun 4; build_elephant_system_prompt()
        system = db_prompt if db_prompt else build_elephant_system_prompt(persona)

        turns: list[InterviewTurn] = []
        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
        ]
        for script_question in script:
            # Basit ACT-R cross-turn tutarlılık notu — son 2 yanıtı özetle
            # Kaynak: engineering-notes.md §4 — 'yoksul adamın ACT-R'ı'
            turn_memory = ""
            if turns:
                recent = turns[-2:]
                summaries = [f"[{t.tags[0] if t.tags else '?'}] {t.answer[:80].strip()}..." for t in recent]
                turn_memory = "\nSon yanıtlarından tutarlılık notu:\n" + "\n".join(summaries)

            prompt = (
                f"Araştırma brief'i: {brief.idea}\n"
                f"Hedef kullanıcılar: {', '.join(brief.target_users) or 'Belirtilmedi'}\n"
                f"Persona: {persona.name}, {persona.age}, {persona.city}, {persona.segment}\n"
                f"Duruş: {persona.stance}\n"
                f"SES Grubu: {persona.ses_group} ({SES_PROFILES.get(persona.ses_group, {}).get('profile', '')})\n"
                f"Katılımcı Tipi: {persona.respondent_type}\n"
                f"Yerleşim: {persona.settlement_type}\n"
                f"Fiyat hassasiyeti: {persona.price_sensitivity}/10\n"
                f"Dijital özgüven: {persona.digital_confidence}/10\n"
                f"Kullanım sıklığı: {persona.usage_frequency}\n"
                f"Marka sadakati: {persona.brand_loyalty}/10\n"
                f"Bağlam: {persona.context}\n"
                f"Hedefler: {', '.join(persona.goals)}\n"
                f"İtirazlar: {', '.join(persona.objections)}\n"
                f"Bilgi sınırı: {persona.knowledge_boundary}\n"
                f"{turn_memory}\n"
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


def run_interviews_stream(
    brief: ResearchBrief,
    personas: list[Persona],
    model: ResearchModel,
    interview_script: list[InterviewQuestion] | None = None,
    max_retries: int = 2,
) -> Generator[tuple[str, Any], None, list[PersonaInterview]]:
    interviews: list[PersonaInterview] = []
    script = interview_script or generate_interview_script(brief)
    
    # Load dynamic prompt from database if available
    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed (stream), using default persona prompt", exc_info=True)
        db_prompt = None
    for persona in personas:
        # ELEPHANT anti-sycophancy: persona'ya özgü sistem promptu (stream)
        # Kaynak: Akademik Sentez Raporu §Sütun 4; build_elephant_system_prompt()
        base_system = db_prompt if db_prompt else build_elephant_system_prompt(persona)

        yield ("persona_start", {"persona": persona})
        turns: list[InterviewTurn] = []
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

                # Basit ACT-R cross-turn tutarlılık notu — son 2 yanıtı özetle (stream)
                turn_memory = ""
                if turns:
                    recent = turns[-2:]
                    summaries = [f"[{t.tags[0] if t.tags else '?'}] {t.answer[:80].strip()}..." for t in recent]
                    turn_memory = "\nSon yanıtlarından tutarlılık notu:\n" + "\n".join(summaries)

                prompt = (
                    f"Araştırma brief'i: {brief.idea}\n"
                    f"Hedef kullanıcılar: {', '.join(brief.target_users) or 'Belirtilmedi'}\n"
                    f"Persona: {persona.name}, {persona.age}, {persona.city}, {persona.segment}\n"
                    f"Duruş: {persona.stance}\n"
                    f"SES Grubu: {persona.ses_group} ({SES_PROFILES.get(persona.ses_group, {}).get('profile', '')})\n"
                    f"Katılımcı Tipi: {persona.respondent_type}\n"
                    f"Yerleşim: {persona.settlement_type}\n"
                    f"Fiyat hassasiyeti: {persona.price_sensitivity}/10\n"
                    f"Dijital özgüven: {persona.digital_confidence}/10\n"
                    f"Kullanım sıklığı: {persona.usage_frequency}\n"
                    f"Marka sadakati: {persona.brand_loyalty}/10\n"
                    f"Bağlam: {persona.context}\n"
                    f"Hedefler: {', '.join(persona.goals)}\n"
                    f"İtirazlar: {', '.join(persona.objections)}\n"
                    f"Bilgi sınırı: {persona.knowledge_boundary}\n"
                    f"{turn_memory}\n"
                    f"Soru etiketi: {script_question.label}\n"
                    f"Soru: {script_question.question}\n"
                    "Kısa, somut ve Türkiye pazarı gerçeklerine uygun cevap ver."
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
                critical_failure = any(flag in {"meta_tone", "visible_reasoning"} for flag in quality_flags)
                
                if critical_failure:
                    try:
                        log_audit(brief.title[:50], persona.name, ", ".join(quality_flags), "Retried turn due to AI hallucination/meta-tone")
                    except Exception:
                        logger.warning(
                            "audit log write failed for persona=%s flags=%s",
                            persona.name, quality_flags, exc_info=True
                        )
                
                if not critical_failure or attempt == max_retries:
                    turn = InterviewTurn(
                        question=script_question.question,
                        answer=full_answer,
                        tags=script_question.tags or classify_question(script_question.question),
                        model_id=getattr(model, "last_model_id", None),
                        quality_flags=quality_flags,
                    )
                    turns.append(turn)
                    yield ("question_end", {"persona": persona, "question": script_question, "turn": turn})
                    break
                    
        interview = PersonaInterview(persona=persona, turns=turns, consistency_notes=consistency_notes)
        interviews.append(interview)
        yield ("persona_end", {"persona": persona, "interview": interview})
        
    return interviews




def run_research(
    brief: ResearchBrief,
    model: ResearchModel,
    panel_roles: list[PanelRole] | None = None,
) -> ResearchReport:
    plan = build_research_plan(brief, panel_roles)
    personas = generate_personas(brief, panel_roles)
    interviews = run_interviews(brief, personas, model, plan.interview_script)
    return synthesize_report(brief, plan, personas, interviews)
