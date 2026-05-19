from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


ResearchStage = Literal["briefing", "persona_design", "interview", "synthesis"]
FindingCategory = Literal["pain_point", "value", "objection", "pricing", "positioning", "risk"]
PersonaStance = Literal["Champion", "Pragmatist", "Skeptic", "Blocker", "Observer"]


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


@dataclass(frozen=True)
class ClarifyingQuestion:
    id: str
    question: str
    reason: str
    priority: Literal["high", "medium", "low"] = "medium"


@dataclass(frozen=True)
class ResearchPlan:
    objective: str
    assumptions: list[str]
    clarifying_questions: list[ClarifyingQuestion]
    interview_questions: list[str]
    recommended_panel_size: int


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


@dataclass(frozen=True)
class InterviewTurn:
    question: str
    answer: str
    tags: list[FindingCategory] = field(default_factory=list)


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
    evidence: list[Evidence]


@dataclass(frozen=True)
class ResearchReport:
    title: str
    plan: ResearchPlan
    personas: list[Persona]
    interviews: list[PersonaInterview]
    findings: list[Finding]
    pricing: PricingInsight
    recommendations: list[str]
    validation_next_steps: list[str]
    limitations: list[str]


class ResearchModel(Protocol):
    def generate(self, system: str, prompt: str) -> str:
        """Generate a response from the configured model provider."""
