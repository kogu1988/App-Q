"""Test: plan_config feature gating + white-label marka helper."""
from packages.research_engine.plan_config import (
    get_brand_name,
    get_plan_config,
    get_min_plan_for_feature,
    has_feature,
)


def test_white_label_pro_and_enterprise_empty_brand():
    """White-label planlarda marka adı boş döner."""
    assert get_brand_name("Pro") == ""
    assert get_brand_name("Enterprise") == ""


def test_non_white_label_plans_return_clarere():
    """White-label olmayan planlarda marka adı Clarere."""
    assert get_brand_name("Free") == "Clarere"
    assert get_brand_name("Flex") == "Clarere"
    assert get_brand_name("Starter") == "Clarere"


def test_unknown_plan_defaults_to_free_brand():
    """Bilinmeyen plan Free gibi davranır."""
    assert get_brand_name("BilinmeyenPlan") == "Clarere"


def test_has_feature_white_label():
    assert has_feature("Pro", "white_label") is True
    assert has_feature("Starter", "white_label") is False


def test_feature_min_plan():
    assert get_min_plan_for_feature("white_label") == "Pro"
    assert get_min_plan_for_feature("multi_user") == "Enterprise"


def test_get_plan_config_fallback():
    assert get_plan_config("BilinmeyenPlan") == get_plan_config("Free")
