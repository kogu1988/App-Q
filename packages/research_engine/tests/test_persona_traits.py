"""GRUP 13 — Persona Trait Kalibrasyonu regresyon testleri.

Korunan değer: Openness/stance hizalaması ve Big Five kalibrasyonu. Formül tekrar
bozulmamalı — persona kişiliği ile stance çelişirse mülakatlar inandırıcılığını yitirir.

Formül (workflow.persona_traits):
    Agreeableness = 60 + stance_modifier + küçük varyasyon(+/-6)
    Openness      = 52 + (dc-5)*3 + varyasyon(+/-6) + stance_openness_mod
    Neuroticism   = clamp(ps*7 + varyasyon) + stance_neuroticism_mod
"""
from __future__ import annotations

from packages.research_engine.workflow import generate_personas, persona_traits

STANCES = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]


def test_13_1_openness_order_is_stance_driven_at_same_digital_confidence():
    """Aynı dijital özgüvende Openness sıralaması: Innovator > EarlyAdopter > Mainstream > Laggard."""
    dc = 6
    values = [persona_traits(1, s, 5, dc)["Openness"] for s in ("Innovator", "EarlyAdopter", "Mainstream", "Laggard")]

    assert values == sorted(values, reverse=True)
    assert len(set(values)) == len(values), "stance'ler aynı Openness üretmemeli"


def test_13_2_skeptic_openness_below_mainstream():
    """Skeptic, Mainstream'den daha düşük Openness üretmeli (aynı dc)."""
    skeptic = persona_traits(1, "Skeptic", 5, 6)["Openness"]
    mainstream = persona_traits(1, "Mainstream", 5, 6)["Openness"]

    assert skeptic < mainstream


def test_13_3_agreeableness_order_holds_across_seeds():
    """Agreeableness: Skeptic < Mainstream < Innovator — her seed'de geçerli."""
    for seed in range(1, 8):
        skeptic = persona_traits(seed, "Skeptic", 5, 6)["Agreeableness"]
        mainstream = persona_traits(seed, "Mainstream", 5, 6)["Agreeableness"]
        innovator = persona_traits(seed, "Innovator", 5, 6)["Agreeableness"]

        assert skeptic < mainstream < innovator, f"seed={seed}"


def test_13_4_neuroticism_grows_with_price_sensitivity():
    """Yüksek fiyat hassasiyeti daha yüksek Neuroticism üretmeli."""
    low = persona_traits(1, "Mainstream", 2, 6)["Neuroticism"]
    high = persona_traits(1, "Mainstream", 9, 6)["Neuroticism"]

    assert high > low


def test_13_5_all_scores_within_bounds():
    """Tüm skorlar 1..100, Openness 20..92 aralığında kalmalı."""
    for stance in STANCES:
        for seed in range(1, 10):
            traits = persona_traits(seed, stance, 5, 6)
            assert set(traits) == {"Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"}
            for key, value in traits.items():
                assert 1 <= value <= 100, f"{stance}/{seed}/{key}={value}"
            assert 20 <= traits["Openness"] <= 92


def test_13_6_trait_calculation_is_deterministic():
    """Aynı parametreler her zaman aynı çıktıyı üretmeli."""
    first = persona_traits(7, "Innovator", 4, 8)
    second = persona_traits(7, "Innovator", 4, 8)

    assert first == second


def test_13_7_five_person_panel_has_five_distinct_stances():
    """5 kişilik panel 5 farklı stance üretmeli (stance diversity garantisi)."""
    from packages.research_engine.tests.helpers import make_brief

    personas = generate_personas(make_brief())
    stances = [p.stance for p in personas]

    assert len(personas) == 5
    assert len(set(stances)) == 5, f"stance'ler: {stances}"
    assert "Skeptic" in stances, "anti-sycophancy guard: Skeptic zorunlu"


def test_13_8_big_five_is_populated_for_every_persona():
    """Her personada 5 anahtarlı, sıfır olmayan big_five bulunmalı (UI radar grafiği)."""
    from packages.research_engine.tests.helpers import make_brief

    personas = generate_personas(make_brief())

    for persona in personas:
        assert persona.big_five, f"{persona.name} big_five boş"
        assert set(persona.big_five) == {
            "Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism",
        }
        assert all(v > 0 for v in persona.big_five.values()), persona.big_five
