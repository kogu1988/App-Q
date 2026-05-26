from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


ResearchStage = Literal["briefing", "persona_design", "interview", "synthesis"]
FindingCategory = Literal["pain_point", "value", "objection", "pricing", "positioning", "risk"]
# Rogers Diffusion of Innovations stance kategorileri (Rogers 2003)
PersonaStance = Literal["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]
QualitySeverity = Literal["info", "warning", "fail"]

# Rogers Diffusion stance profilleri — her kategori için davranışsal özellikler
# Kaynak: Rogers (2003), Bilal (2026) Grounded Simulation §4.3
STANCE_PROFILE: dict[str, dict] = {
    "Innovator": {
        "adoption_eagerness": 10,   # 1–10; ne kadar hızlı benimser
        "risk_tolerance": 9,        # 1–10; belirsizliğe tolerans
        "evidence_need": 2,         # 1–10; karar için ne kadar kanıt ister
        "roi_threshold": 2,         # 1–10; ROI beklentisi ne kadar yüksek
        "agreeableness_mod": +4,    # Big Five Agreeableness delta — +4 (ELEPHANT/Pairit: yüksek agreeableness araştırma kalitesini düşürür)
        "openness_mod": +12,        # Big Five Openness delta
        "neuroticism_mod": -8,      # Big Five Neuroticism delta
        "tr_description": "Teknolojiyi ilk benimseyen. Risk almaktan çekinmez. Referans değeri yüksek.",
    },
    "EarlyAdopter": {
        "adoption_eagerness": 8,
        "risk_tolerance": 7,
        "evidence_need": 4,
        "roi_threshold": 4,
        "agreeableness_mod": +4,
        "openness_mod": +8,
        "neuroticism_mod": -4,
        "tr_description": "Kanıt görünce hızla harekete geçer. Sosyal etkisi yüksek, opinion leader.",
    },
    "Mainstream": {
        "adoption_eagerness": 5,
        "risk_tolerance": 5,
        "evidence_need": 6,
        "roi_threshold": 6,
        "agreeableness_mod": 0,
        "openness_mod": 0,
        "neuroticism_mod": 0,
        "tr_description": "Çoğunluğun davranışını izler. Somut fayda ve sosyal onay gerektirir.",
    },
    "Laggard": {
        "adoption_eagerness": 2,
        "risk_tolerance": 2,
        "evidence_need": 9,
        "roi_threshold": 8,
        "agreeableness_mod": -4,
        "openness_mod": -8,
        "neuroticism_mod": +6,
        "tr_description": "Son benimseyenler. Geleneksel yöntemleri tercih eder, zorlanmadan değişmez.",
    },
    "Skeptic": {
        "adoption_eagerness": 1,
        "risk_tolerance": 1,
        "evidence_need": 10,
        "roi_threshold": 10,
        "agreeableness_mod": -10,
        "openness_mod": -4,
        "neuroticism_mod": +12,
        "tr_description": "Ürünü reddetme eğiliminde. Güçlü itirazlar barındırır. Araştırma için kritik sinyal kaynağı.",
    },
}

# Önerilen kohort dağılımı (5 kişilik panel için)
# Bilal (2026): stance diversity en büyük tek driver (ΔF1 = -0.582)
DEFAULT_STANCE_COHORT: list[PersonaStance] = [
    "Innovator", "EarlyAdopter", "Mainstream", "Mainstream", "Skeptic"
]

# Türkiye TÜAD 2025 SES grupları
SESGroup = Literal["AB", "C1", "C2", "DE"]

# Araştırma katılımcı tipi (segment bazlı soru filtresi)
RespondentType = Literal[
    "potential_customer",   # Potansiyel müşteri — henüz ürünü kullanmamış
    "competitor_user",      # Rakip kullanıcısı — aktif rakip tercih eden
    "churned_user",         # Kaybedilmiş kullanıcı — terk eden eski müşteri
    "decision_maker",       # Karar verici / yönetici — satın alma yetkisi olan
    "individual_user",      # Bireysel kullanıcı — fiili operasyonu yürüten
]

SettlementType = Literal["kentsel", "banliyö", "kırsal"]


@dataclass(frozen=True)
class ResearchBrief:
    title: str
    market: str
    category: str
    idea: str
    target_users: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    expected_price: str | None = None
    sales_channel: str | None = None
    success_metric: str | None = None
    variant_a: str | None = None
    variant_b: str | None = None
    # Araştırmaya dahil edilecek katılımcı tipleri
    respondent_types: list[RespondentType] = field(default_factory=list)
    # Hedef kitle için öncelikli keşif kanalları
    discovery_channels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClarifyingQuestion:
    id: str
    question: str
    reason: str
    priority: Literal["high", "medium", "low"] = "medium"


@dataclass(frozen=True)
class InterviewQuestion:
    id: str
    label: str
    question: str
    reason: str
    tags: list[FindingCategory] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchPlan:
    objective: str
    assumptions: list[str]
    clarifying_questions: list[ClarifyingQuestion]
    interview_questions: list[str]
    recommended_panel_size: int
    interview_script: list[InterviewQuestion] = field(default_factory=list)
    # TÜAD 2025 oranlarına göre önerilen SES kota dağılımı
    ses_quota: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PanelRole:
    role: str
    why: str
    count: int


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    age: int
    city: str
    segment: str
    stance: PersonaStance
    price_sensitivity: int
    digital_confidence: int
    context: str
    goals: list[str]
    objections: list[str]
    knowledge_boundary: str
    country_code: str = "TR"
    origin_country: str = "Türkiye"
    role_title: str = ""
    bio: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    traits: dict[str, int] = field(default_factory=dict)
    # Pazar araştırması metodolojisi alanları
    ses_group: SESGroup = "C1"                        # TÜAD 2025 sosyo-ekonomik statü
    respondent_type: RespondentType = "potential_customer"  # Katılımcı tipi
    settlement_type: SettlementType = "kentsel"       # Yerleşim tipi
    # Davranışsal segmentasyon alanları
    usage_frequency: Literal["daily", "weekly", "monthly", "rarely"] = "weekly"  # Kullanım sıklığı
    brand_loyalty: int = 5  # 1 (marka sadakatsiz) → 10 (bağımlı). Satın alma kararında markaya bağımlılık
    # Rogers Diffusion — grounded stance metadatası
    diffusion_stage: str = ""           # Stance'ın Türkçe kısa açıklaması (STANCE_PROFILE'dan)
    neo_facets: dict[str, int] = field(default_factory=dict)  # NEO-PI-R facet skorları (0-100)
    big_five: dict[str, int] = field(default_factory=dict)  # Big Five (Openness, Conscientiousness, Extroversion, Agreeableness, Neuroticism)


@dataclass(frozen=True)
class InterviewTurn:
    question: str
    answer: str
    tags: list[FindingCategory] = field(default_factory=list)
    model_id: str | None = None
    quality_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QualityIssue:
    persona_id: str
    persona_name: str
    question: str
    severity: QualitySeverity
    issue: str
    recommendation: str


@dataclass(frozen=True)
class PersonaInterview:
    persona: Persona
    turns: list[InterviewTurn]
    consistency_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Evidence:
    persona_id: str
    persona_name: str
    stance: PersonaStance
    quote: str
    source_question: str


@dataclass(frozen=True)
class Finding:
    title: str
    category: FindingCategory
    summary: str
    confidence: float
    evidence: list[Evidence]
    implication: str


@dataclass(frozen=True)
class PricingInsight:
    acceptable_range: str
    resistance_points: list[str]
    packaging_suggestion: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass(frozen=True)
class VanWestendorpInsight:
    """Van Westendorp Price Sensitivity Meter (PSM) sonuçları."""
    # Her persona için 4 fiyat eşiği (örnek: [150, 299, 499, 799])
    too_cheap_values: list[float]       # Çok ucuz — kalitesiz görünür
    cheap_values: list[float]           # Ucuz/makul — iyi alım
    expensive_values: list[float]       # Pahalı ama düşünülebilir
    too_expensive_values: list[float]   # Çok pahalı — hiç almam
    # PSM kritik noktaları
    opp: float                          # Optimal Price Point (PMC x PME kesişimi)
    ipp: float                          # Indifference Price Point
    pmc: float                          # Point of Marginal Cheapness (alt kabul sınırı)
    pme: float                          # Point of Marginal Expensiveness (üst kabul sınırı)
    acceptable_range: tuple[float, float]   # Kabul edilebilir fiyat aralığı (PMC, PME)
    currency: str = "TL"
    methodology_note: str = "Van Westendorp PSM — Sentetik mülakat yanıtlarından çıkarılan heuristik fiyat aralıkları."


@dataclass(frozen=True)
class ResearchReport:
    title: str
    executive_summary: list[str]
    plan: ResearchPlan
    personas: list[Persona]
    interviews: list[PersonaInterview]
    findings: list[Finding]
    pricing: PricingInsight
    pain_point_matrix: list[dict[str, str]]
    action_items: list[str]
    quality_issues: list[QualityIssue]
    recommendations: list[str]
    validation_next_steps: list[str]
    limitations: list[str]
    model_usage: dict[str, int] = field(default_factory=dict)
    # TÜAD 2025 SES × Stance çapraz tablosu
    ses_cross_tab: list[dict] = field(default_factory=list)
    # Katılımcı tipi bazında bulgu özeti
    respondent_type_summary: list[dict] = field(default_factory=list)
    # Van Westendorp PSM (varsa)
    van_westendorp: VanWestendorpInsight | None = None
    # Marka sağlığı özeti — yardımsız bilinirlik ve çağrışım analizi
    brand_health: dict | None = None
    # Keşif kanalı haritası — kanal bazında frekans
    channel_map: list[dict] = field(default_factory=list)
    # Araştırma bütünlüğü puanı (Grounded Simulation RFI metriği)
    research_quality: dict | None = None


class ResearchModel(Protocol):
    def generate(self, system: str, prompt: str, response_format: Literal["json"] | None = None) -> str:
        """Generate a response from the configured model provider."""

    def generate_stream(self, system: str, prompt: str, response_format: Literal["json"] | None = None):
        """Generate a response as a stream of chunks."""

    def free_memory(self) -> None:
        """Free VRAM/memory after task completion."""
