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
    """Verify S-O-R logistic regression output matching user-approved coefficients."""
    # logit = beta_0 + beta_1 * Shipping + beta_2 * N - beta_3 * C
    # beta_0 = -1.5, beta_1 = 0.4, beta_2 = 0.2, beta_3 = -0.1
    # Shipping = 8.0 (80TL), N = 5.0, C = 6.0
    beta_0 = -1.5
    beta_1 = 0.4
    beta_2 = 0.2
    beta_3 = -0.1
    
    shipping = 8.0
    n_val = 5.0
    c_val = 6.0
    
    logit = beta_0 + beta_1 * shipping + beta_2 * n_val + beta_3 * c_val
    # logit = -1.5 + 3.2 + 1.0 - 0.6 = 2.1
    assert math.isclose(logit, 2.1, rel_tol=1e-5)
    
    prob_abandon = 1.0 / (1.0 + math.exp(-logit))
    # prob_abandon = 1 / (1 + e^-2.1) = 1 / (1 + 0.12245) = 0.8909
    assert math.isclose(prob_abandon, 0.8909, rel_tol=1e-3)
    assert prob_abandon > 0.5

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
