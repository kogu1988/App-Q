"""GRUP 14 — Batch Mülakat Dayanıklılığı regresyon testleri.

Korunan değer: Kısmi-cevap retry mantığı ve `response_format="json"` bug'ının
tekrar etmemesi. `json_object` modu array döndürmeyi engelliyordu → tüm yanıtlar boş
geliyordu. Batch akışı DÜZ METİN + regex parse kullanmalı.
"""
from __future__ import annotations

import json

from packages.research_engine.tests.helpers import (
    FakeModel,
    make_brief,
    make_persona,
    make_script,
)
from packages.research_engine.workflow import run_interviews_batch

FULL = json.dumps(
    [{"label": "PAIN", "answer": "Somut acı"}, {"label": "PRICE", "answer": "150 TL öderim"}],
    ensure_ascii=False,
)
PARTIAL = json.dumps([{"label": "PAIN", "answer": "Somut acı"}], ensure_ascii=False)
FENCED = f"```json\n{FULL}\n```"
UNANSWERED = "[Yanıt alınamadı]"


def _run(monkeypatch, responses):
    """Batch mülakatı sabit yanıtlarla çalıştırır; (model, interview) döner."""
    monkeypatch.setenv("RESEARCH_DEADLINE_SECONDS", "0")  # süre bütçesini kapat (determinizm)

    brief = make_brief(hypothesis_blind=True)
    model = FakeModel(responses)
    interviews = run_interviews_batch(brief, [make_persona()], model, make_script())
    return model, interviews[0]


def test_14_1_partial_answer_triggers_retry(monkeypatch):
    """Eksik label varsa ikinci çağrı yapılmalı."""
    model, _ = _run(monkeypatch, [PARTIAL, FULL])

    assert len(model.calls) == 2, "eksik cevap retry tetiklemeli"


def test_14_2_full_answer_does_not_retry(monkeypatch):
    """Tam yanıtta tek çağrı yeterli olmalı."""
    model, _ = _run(monkeypatch, [FULL])

    assert len(model.calls) == 1, "gereksiz retry yapılmamalı"


def test_14_3_empty_answer_triggers_retry(monkeypatch):
    """Boş yanıt tekrar deneme tetiklemeli."""
    model, _ = _run(monkeypatch, ["", FULL])

    assert len(model.calls) == 2


def test_14_4_stops_after_max_attempts_and_marks_unanswered(monkeypatch):
    """Sürekli boş yanıtta 3 denemede durulmalı ve cevaplar boş işaretlenmeli."""
    model, interview = _run(monkeypatch, ["", "", ""])

    assert len(model.calls) == 3
    assert all(t.answer == UNANSWERED for t in interview.turns)


def test_14_5_broken_json_does_not_crash(monkeypatch):
    """Bozuk JSON çökmemeli; cevaplar boş işaretlenmeli."""
    model, interview = _run(monkeypatch, ["{bozuk json", "[]", "yine bozuk"])

    assert len(interview.turns) == 2
    assert all(t.answer == UNANSWERED for t in interview.turns)


def test_14_6_markdown_fence_is_stripped(monkeypatch):
    """```json fenced blok düzgün parse edilmeli."""
    _, interview = _run(monkeypatch, [FENCED])

    answers = [t.answer for t in interview.turns]
    assert answers == ["Somut acı", "150 TL öderim"]


def test_14_7_response_format_json_is_never_used(monkeypatch):
    """Batch akışı json_object modu KULLANMAMALI (array döndürmeyi engelliyordu)."""
    model, _ = _run(monkeypatch, [PARTIAL, FULL])

    assert model.calls, "model çağrılmadı"
    assert all(call[2] is None for call in model.calls), "response_format='json' kullanılmamalı"
