"""Prefix-cache invariant: mülakat system prompt'unda SABİT bloklar, persona'ya
göre DEĞİŞEN bloklardan önce gelmeli (DeepSeek disk cache prefix tabanlıdır)."""
from __future__ import annotations

from packages.research_engine.nodes.sycophancy import build_elephant_system_prompt
from packages.research_engine.tests.helpers import make_persona


def test_constant_blocks_precede_variable_blocks():
    skeptic = make_persona(
        stance="Skeptic",
        traits={"Agreeableness": 20, "Neuroticism": 80, "Openness": 30},
    )
    innovator = make_persona(
        stance="Innovator",
        traits={"Agreeableness": 80, "Neuroticism": 30, "Openness": 90},
    )

    p1 = build_elephant_system_prompt(skeptic, hypothesis_blind=True)
    p2 = build_elephant_system_prompt(innovator, hypothesis_blind=True)

    # İki farklı persona arasındaki ortak önek makul uzunlukta olmalı
    common = 0
    for a, b in zip(p1, p2):
        if a != b:
            break
        common += 1
    assert common > 200, f"ortak önek çok kısa: {common}"

    # Sabit bloklar, değişken kişilik bloğundan önce gelmeli
    assert p1.index("[HİPOTEZ-KÖRÜ MÜLAKAT]") < p1.index("[KİŞİLİK —")
