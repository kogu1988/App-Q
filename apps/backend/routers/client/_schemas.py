"""Client router istek modelleri (R6-6)."""
from typing import List, Optional

from pydantic import BaseModel


class StudioSimulationRequest(BaseModel):
    brief: str
    category: str
    pricing: str
    panel_roles: list[dict] | None = []

class IntakeChatRequest(BaseModel):
    current_brief: dict = {}
    chat_history: list[dict] = []
    user_message: str
    app_mode: str = "research"  # "research" | "ab_test"


class GeneratePersonasRequest(BaseModel):
    plan: dict
    brief: dict = {}  # ResearchBrief verileri (optional, fallback ile)


class SynthesizeRequest(BaseModel):
    interviews: list[dict]
    plan: dict
    brief: dict = {}

class BriefRequest(BaseModel):
    category: str
    title: str
    context: str
    brand: str
    budget: str
    target_users: list[str] = []
    competitors: list[str] = []
    expected_price: str | None = None
    sales_channel: str | None = None
    success_metric: str | None = None
    variant_a: str | None = None
    variant_b: str | None = None
    questions: list[str] = []
    discovery_channels: list[str] = []
    respondent_types: list[str] = []

class ResearchRequest(BaseModel):
    """Adım 2: Plan + Persona + Mülakatları tek seferde başlatır."""
    category: str
    title: str = "Araştırma"
    context: str  # brief fikri
    brand: str = ""
    budget: str = ""
    target_users: list[str] = []
    competitors: list[str] = []
    expected_price: str | None = None
    sales_channel: str | None = None
    success_metric: str | None = None
    questions: list[str] = []
    discovery_channels: list[str] = []
    respondent_types: list[str] = []
    # Intake (Defne) tarafından doldurulan alanlar
    intake_brief: dict = {}
    # Kaç persona kullanılacağı
    panel_size: int = 5

class StudyPayload(BaseModel):
    metadata: dict
    payload: dict

class PersonaSearch(BaseModel):
    query: str

class PersonaCreate(BaseModel):
    name: str
    age: int
    city: str
    segment: str
    stance: str
    price_sensitivity: int
    digital_confidence: int
    context: str
    goals: str
    objections: str
    knowledge_boundary: str
    country_code: str
    origin_country: str
    role_title: str
    bio: str
    attributes: str
    traits: str
    created_by: str = "system"
    is_global: bool = True
    b2b_role: str | None = None
    industry: str | None = None
    company_size: str | None = None
    b2b_company_type: str | None = None
    b2b_decision_maker: bool = False

class FeedbackCreate(BaseModel):
    username: str = "anonymous"
    study_id: str
    item_type: str
    item_id: str
    vote: int
    comment: str = ""


class UpgradePlanRequest(BaseModel):
    new_plan: str
    billing_cycle: str = "monthly"  # "monthly" | "annual"


class RegisterRequest(BaseModel):
    username: str
    email: str = ""
    new_plan: str = ""          # İsteğe bağlı: register sonrası bu plana yükselt
    billing_cycle: str = "monthly"
