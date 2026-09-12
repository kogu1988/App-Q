"""GRUP 3 — Hypothesis-Blind mülakat regresyon testleri.

Korunan değer: Metodolojik dürüstlük. Persona araştırma hipotezini görürse yapay
konsensüs oluşur ve bilimsel iddia çöker. Sessizce bozulması en tehlikeli özellik.
"""
from __future__ import annotations

from packages.research_engine.nodes.sycophancy import build_elephant_system_prompt
from packages.research_engine.tests.helpers import (
    FakeModel,
    make_brief,
    make_persona,
    make_script,
)
from packages.research_engine.workflow import (
    run_interviews,
    run_interviews_batch,
    run_interviews_stream,
)


def _first_prompt(model: FakeModel) -> str:
    assert model.calls, "model hiç çağrılmadı"
    return model.calls[0][1]


def test_3_1_default_brief_is_hypothesis_blind():
    """Varsayılan davranış hipotez-körü olmalı."""
    assert make_brief().hypothesis_blind is True


def test_3_2_blind_prompt_uses_context_block_not_topic_block():
    """Blind modda [BAĞLAM] kullanılır, [ARAŞTIRMA KONUSU] kullanılmaz."""
    brief = make_brief(hypothesis_blind=True)
    model = FakeModel()
    run_interviews_batch(brief, [make_persona()], model, make_script())

    prompt = _first_prompt(model)
    assert "[BAĞLAM]" in prompt
    assert "[ARAŞTIRMA KONUSU]" not in prompt


def test_3_3_blind_prompt_still_includes_product_description():
    """Persona ürünü bilmeli — sadece hipotezi bilmemeli."""
    brief = make_brief(idea="Pet bakım takip uygulaması", hypothesis_blind=True)
    model = FakeModel()
    run_interviews_batch(brief, [make_persona()], model, make_script())

    assert brief.idea in _first_prompt(model)


def test_3_4_blind_prompt_has_no_hypothesis_framing():
    """Blind modda hipotez/doğrulama/başarı kriteri çerçevesi geçmemeli."""
    brief = make_brief(hypothesis_blind=True)
    model = FakeModel()
    run_interviews_batch(brief, [make_persona()], model, make_script())

    prompt = _first_prompt(model).lower()
    for keyword in ("doğrula", "hipotez", "başarı kriteri"):
        assert keyword not in prompt, f"blind modda '{keyword}' geçmemeli"


def test_3_5_non_blind_uses_research_topic_block():
    """hypothesis_blind=False eski davranışı korur."""
    brief = make_brief(hypothesis_blind=False)
    model = FakeModel()
    run_interviews_batch(brief, [make_persona()], model, make_script())

    prompt = _first_prompt(model)
    assert "[ARAŞTIRMA KONUSU]" in prompt
    assert "[BAĞLAM]" not in prompt


def test_3_6_all_three_interview_functions_honor_the_flag():
    """run_interviews, _stream ve _batch aynı blind davranışı göstermeli."""
    brief = make_brief(hypothesis_blind=True)
    persona = make_persona()
    script = make_script()

    for fn in (run_interviews, run_interviews_batch):
        model = FakeModel()
        fn(brief, [persona], model, script)
        assert "[BAĞLAM]" in _first_prompt(model), f"{fn.__name__} blind değil"

    stream_model = FakeModel()
    list(run_interviews_stream(brief, [persona], stream_model, script))
    assert "[BAĞLAM]" in _first_prompt(stream_model), "run_interviews_stream blind değil"


def test_3_7_persona_does_not_see_other_personas():
    """Bir personanın prompt'unda başka persona adı/alıntısı olmamalı."""
    brief = make_brief(hypothesis_blind=True)
    other = make_persona(pid="p2", name="Zeynep")
    target = make_persona(pid="p1", name="Elif")

    model = FakeModel()
    run_interviews_batch(brief, [target], model, make_script())

    prompt = _first_prompt(model)
    assert other.name not in prompt
    assert target.name in prompt


def test_3_8_elephant_prompt_adds_blind_directive():
    """build_elephant_system_prompt blind direktifini yalnızca True'da ekler."""
    persona = make_persona()

    blind = build_elephant_system_prompt(persona, hypothesis_blind=True)
    open_ = build_elephant_system_prompt(persona, hypothesis_blind=False)

    assert "[HİPOTEZ-KÖRÜ" in blind
    assert "[HİPOTEZ-KÖRÜ" not in open_
