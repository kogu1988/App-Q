"""GRUP 15 — Tolerant Synthesize regresyon testleri.

Korunan değer: Frontend eksik veri gönderdiğinde 500 değil 422 dönmeli ve eksik
alanlar varsayılanla doldurulmalı. Aksi halde tek bir eksik alan tüm raporu düşürür.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from apps.backend.routers.client import (
    SynthesizeRequest,
    _build_persona_tolerant,
    _synthesize_impl,
    synthesize,
)


def test_15_1_missing_plan_fields_are_defaulted():
    """Boş plan sözlüğü çökmemeli — varsayılanlarla rapor üretilmeli."""
    request = SynthesizeRequest(interviews=[], plan={}, brief={})

    report = _synthesize_impl(request, None)

    assert isinstance(report, dict)
    assert "report_markdown" in report


def test_15_2_missing_persona_fields_are_defaulted():
    """Eksik persona alanları geçerli bir Persona üretmeli."""
    persona = _build_persona_tolerant({"name": "Ali"})

    assert persona.name == "Ali"
    assert persona.age == 30
    assert persona.city == "İstanbul"
    assert persona.stance == "Mainstream"
    assert persona.ses_group == "C1"
    assert persona.respondent_type == "potential_customer"


def test_15_3_missing_turn_fields_are_safe():
    """Yalnızca 'question' içeren turn güvenli şekilde işlenmeli."""
    request = SynthesizeRequest(
        interviews=[{"persona": {"name": "Ali"}, "turns": [{"question": "Q"}]}],
        plan={},
        brief={},
    )

    report = _synthesize_impl(request, None)

    assert isinstance(report, dict)


def test_15_4_broken_input_returns_422_not_500():
    """Tamamen bozuk girdi 422 dönmeli (500 değil)."""
    request = SynthesizeRequest(
        interviews=[{"persona": "bu-bir-sozluk-degil", "turns": "bu-liste-degil"}],
        plan={},
        brief={},
    )

    with pytest.raises(HTTPException) as exc:
        synthesize(request, None)

    assert exc.value.status_code == 422


def test_15_5_personas_derived_from_interviews_when_absent():
    """personas alanı yoksa personalar mülakatlardan türetilmeli."""
    request = SynthesizeRequest(
        interviews=[
            {
                "persona": {"name": "Zeynep", "stance": "Skeptic", "ses_group": "C2"},
                "turns": [{"question": "Q", "answer": "A", "tags": ["pricing"]}],
            }
        ],
        plan={},
        brief={"title": "Test", "context": "Test fikri"},
    )

    report = _synthesize_impl(request, None)

    assert isinstance(report, dict)
    # Mülakattaki persona rapora yansımalı (personas=None → interview'lardan türetilir)
    serialized = str(report)
    assert "Zeynep" in serialized
