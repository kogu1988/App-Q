"""Test yardımcıları — gerçek LLM/DB çağrısı YAPILMAZ.

`FakeModel` prompt'ları kaydeder; böylece mülakat akışları ağ çağrısı olmadan
doğrulanabilir (docs/TEST_PLAN.md teknik kuralı).
"""
from __future__ import annotations

from packages.research_engine.models import (
    Finding,
    InterviewQuestion,
    InterviewTurn,
    Persona,
    PersonaInterview,
    ResearchBrief,
)


class FakeModel:
    """Sırayla önceden verilen yanıtları döner; tüm çağrıları kaydeder."""

    def __init__(self, responses=None):
        self.calls: list[tuple] = []          # (system, prompt, response_format)
        self.responses = list(responses or [])

    def generate(self, system, prompt, response_format=None):
        self.calls.append((system, prompt, response_format))
        return self.responses.pop(0) if self.responses else "[]"

    def generate_stream(self, system, prompt, response_format=None):
        yield self.generate(system, prompt, response_format)

    def free_memory(self):
        pass


def make_brief(**overrides) -> ResearchBrief:
    data = {
        "title": "Test Araştırması",
        "market": "Türkiye",
        "category": "genel",
        "idea": "Evcil hayvan bakım takip uygulaması",
        "target_users": ["kobi"],
    }
    data.update(overrides)
    return ResearchBrief(**data)


def make_persona(pid: str = "p1", name: str = "Elif", stance: str = "Mainstream", **overrides) -> Persona:
    data = {
        "id": pid,
        "name": name,
        "age": 34,
        "city": "İstanbul",
        "segment": "genel",
        "stance": stance,
        "price_sensitivity": 5,
        "digital_confidence": 6,
        "context": "Test bağlamı",
        "goals": ["büyümek"],
        "objections": ["fiyat"],
        "knowledge_boundary": "genel tüketici",
        "role_title": "Kurucu",
        "bio": "",
        "ses_group": "C1",
    }
    data.update(overrides)
    return Persona(**data)


def make_script() -> list[InterviewQuestion]:
    return [
        InterviewQuestion(
            id="q1", label="PAIN",
            question="Bu problemi bugün nasıl yaşıyorsun?",
            reason="pain", tags=["pain_point"],
        ),
        InterviewQuestion(
            id="q2", label="PRICE",
            question="Bu ürün için ne kadar ödemeyi düşünürsün?",
            reason="pricing", tags=["pricing"],
        ),
    ]


def turn(question: str, answer: str, tags: list[str]) -> InterviewTurn:
    return InterviewTurn(question=question, answer=answer, tags=list(tags))  # type: ignore[arg-type]


def make_interview(persona: Persona, turns: list[InterviewTurn]) -> PersonaInterview:
    return PersonaInterview(persona=persona, turns=list(turns), consistency_notes=[])


def make_finding(
    title: str = "Fiyat hassasiyeti",
    category: str = "pricing",
    summary: str = "Kullanıcılar fiyata duyarlı",
    confidence: float = 0.8,
) -> Finding:
    return Finding(
        title=title,
        category=category,  # type: ignore[arg-type]
        summary=summary,
        confidence=confidence,
        evidence=[],
        implication="test",
    )
