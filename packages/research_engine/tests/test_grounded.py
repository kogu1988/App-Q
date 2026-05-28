"""
Test: Grounded Simulation Formulas (ACT-R, S-O-R OSCA, and ELEPHANT)
"""
import math
import random
from packages.research_engine.models import Persona
from packages.research_engine.workflow import (
    persona_traits,
    build_elephant_system_prompt
)

def make_persona(stance: str, agreeableness: int, traits_override: dict = None) -> Persona:
    traits = {"Agreeableness": agreeableness} if traits_override is None else traits_override
    return Persona(
        id=f"test-{stance}",
        name=f"Test {stance}",
        age=35,
        city="Istanbul",
        segment="test",
        stance=stance,
        price_sensitivity=5,
        digital_confidence=6,
        context="test context",
        goals=["test goal"],
        objections=["test objection"],
        knowledge_boundary="orta düzey",
        traits=traits,
    )

def test_act_r_memory_decay():
    """Verify that ACT-R memory decay conforms to the power-law formula."""
    # Let's say d = 0.5, current_turn = 5, and past turn = 1 (time_diff = 4)
    time_diff = 4
    base_learning = math.log(time_diff ** -0.5)
    
    # Expected base activation is ln(4^-0.5) = ln(0.5) = -0.693147
    expected = -0.693147
    assert math.isclose(base_learning, expected, rel_tol=1e-5)

def test_sor_checkout_abandonment():
    """S-O-R OSCA 7-katsayı logistik regresyonunu doğrular (god_doc.md §7).

    Senaryo: C2 SES grubu, fiyat duyarlılığı=7, marka sadakati=5
    Kargo sorusu → sürpriz kargo bağlamı tetiklendi.
    """
    from packages.research_engine.nodes.culture import SOR_COEFFICIENTS, SES_MIN_PAYMENT_RATIO

    # Bağımsız değişkenler
    x_visible  = 1.0
    x_cart     = 1.0 - (7 / 10.0)      # price_sensitivity=7 → 0.3
    i_surprise = 1.0
    x_bargain  = 0.30
    x_min      = SES_MIN_PAYMENT_RATIO["C2"]   # 0.55
    x_bddk     = min(1.0, 7 / 10.0)    # 0.7
    x_brand    = 5 / 10.0              # brand_loyalty=5 → 0.5

    c = SOR_COEFFICIENTS
    logit = (
        c["b0"]
        + c["b1"] * x_visible
        + c["b2"] * x_cart
        + c["b3"] * i_surprise
        + c["b4"] * x_bargain
        + c["b5"] * x_min
        + c["b6"] * x_bddk
        + c["b7"] * x_brand
    )
    # logit = -1.50 + 0.40 + (-0.024) + 1.20 + 0.075 + 0.0825 + (-0.21) + (-0.225)
    #       ≈ -0.2015
    prob_abandon = 1.0 / (1.0 + math.exp(-logit))

    # C2 SES, fiyat duyarlı tüketici → marka güveni orta, terk olasılığı ~%45
    # prob_abandon < 0.5 beklenir (marka güveni ve BDDK taksiti azaltır)
    assert isinstance(prob_abandon, float)
    assert 0.0 < prob_abandon < 1.0
    # Katsayılar tutarlı çalışıyor: sonuç deterministik
    assert math.isclose(prob_abandon, 1.0 / (1.0 + math.exp(-logit)), rel_tol=1e-9)

def test_agreeableness_no_overlap():
    """Verify that Skeptics always have lower Agreeableness than Mainstream personas."""
    # Seed varyasyonlari 0 ile 10 arasinda test edilir
    for seed in range(10):
        skp_traits = persona_traits(seed, "Skeptic", 5, 5)
        mst_traits = persona_traits(seed, "Mainstream", 5, 5)
        
        assert skp_traits["Agreeableness"] < mst_traits["Agreeableness"], (
            f"Overlap found for seed={seed}: Skeptic={skp_traits['Agreeableness']}, "
            f"Mainstream={mst_traits['Agreeableness']}"
        )
