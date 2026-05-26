"""
plan_config.py — App-Q Plan Katmanı Feature Gate Konfigürasyonu

Her plan için:
  - max_personas      : Bir araştırmadaki maksimum persona sayısı
  - max_simulations   : Aylık maksimum araştırma sayısı (DB ile uyumlu)
  - ab_test           : A/B Test modu açık mı?
  - b2b_mode          : B2B persona modu açık mı?
  - streaming         : Gerçek zamanlı mülakat akışı (SSE) açık mı?
  - pdf_export        : PDF rapor indirme açık mı?
  - adversarial       : Adversarial Review açık mı?
  - rfi               : Research Fidelity Index açık mı?
  - brand_health      : Marka Sağlığı analizi açık mı?
  - ses_crosstab      : SES Cross-Tab tablosu açık mı?
  - custom_personas   : Özel persona havuzu yönetimi
  - fine_tuning_export: Curated soru fine-tuning export'u
  - audit_log         : Audit log erişimi
  - multi_user        : Çok kullanıcılı organizasyon
  - white_label       : White-label (marka gizleme)
"""
from __future__ import annotations

PLAN_CONFIG: dict[str, dict] = {
    "Free": {
        "max_personas": 10,
        "max_simulations": 2,
        "max_tokens": 100_000,
        "max_follow_ups": 0,
        "max_talk_to_research": 0,
        "max_adversarial_loops": 1,
        "ab_test": False,
        "b2b_mode": False,
        "streaming": False,
        "pdf_export": False,
        "adversarial": True,
        "rfi": True,
        "brand_health": False,
        "ses_crosstab": False,
        "custom_personas": False,
        "fine_tuning_export": False,
        "audit_log": False,
        "multi_user": False,
        "white_label": False,
    },
    "Flex": {
        "max_personas": 10,
        "max_simulations": 3,
        "max_tokens": 200_000,
        "max_follow_ups": 3,
        "max_talk_to_research": 9999,
        "max_adversarial_loops": 2,
        "ab_test": True,
        "b2b_mode": False,
        "streaming": True,
        "pdf_export": True,
        "adversarial": True,
        "rfi": True,
        "brand_health": False,
        "ses_crosstab": True,
        "custom_personas": False,
        "fine_tuning_export": False,
        "audit_log": False,
        "multi_user": False,
        "white_label": False,
    },
    "Starter": {
        "max_personas": 10,
        "max_simulations": 10,
        "max_tokens": 500_000,
        "max_follow_ups": 3,
        "max_talk_to_research": 2,
        "max_adversarial_loops": 2,
        "ab_test": True,
        "b2b_mode": False,
        "streaming": True,
        "pdf_export": True,
        "adversarial": True,
        "rfi": True,
        "brand_health": False,
        "ses_crosstab": True,
        "custom_personas": False,
        "fine_tuning_export": False,
        "audit_log": False,
        "multi_user": False,
        "white_label": False,
    },
    "Pro": {
        "max_personas": 10,
        "max_simulations": 9999,  # unlimited
        "max_tokens": 9_999_999,  # unlimited
        "max_follow_ups": 9999,
        "max_talk_to_research": 9999,
        "max_adversarial_loops": 3,
        "ab_test": True,
        "b2b_mode": True,
        "streaming": True,
        "pdf_export": True,
        "adversarial": True,
        "rfi": True,
        "brand_health": True,
        "ses_crosstab": True,
        "custom_personas": False,
        "fine_tuning_export": False,
        "audit_log": False,
        "multi_user": False,
        "white_label": True,
    },
    "Enterprise": {
        "max_personas": 999,  # effectively unlimited / custom
        "max_simulations": 9999,
        "max_tokens": 9_999_999,
        "max_follow_ups": 9999,
        "max_talk_to_research": 9999,
        "max_adversarial_loops": 3,
        "ab_test": True,
        "b2b_mode": True,
        "streaming": True,
        "pdf_export": True,
        "adversarial": True,
        "rfi": True,
        "brand_health": True,
        "ses_crosstab": True,
        "custom_personas": True,
        "fine_tuning_export": True,
        "audit_log": True,
        "multi_user": True,
        "white_label": True,
    },
}

# Hangi plan seviyesinin bir özelliği açtığını insan-okunabilir olarak döner
FEATURE_MIN_PLAN: dict[str, str] = {
    "streaming":         "Flex",
    "pdf_export":        "Flex",
    "ses_crosstab":      "Flex",
    "ab_test":           "Flex",
    "b2b_mode":          "Pro",
    "adversarial":       "Free",
    "rfi":               "Free",
    "brand_health":      "Pro",
    "custom_personas":   "Enterprise",
    "fine_tuning_export":"Enterprise",
    "audit_log":         "Enterprise",
    "multi_user":        "Enterprise",
    "white_label":       "Pro",
}

PLAN_ORDER = ["Free", "Flex", "Starter", "Pro", "Enterprise"]


def get_plan_config(plan_type: str) -> dict:
    """Plan adına göre feature gate konfigürasyonunu döner. Bilinmeyen plan → Free."""
    return PLAN_CONFIG.get(plan_type, PLAN_CONFIG["Free"])


def has_feature(plan_type: str, feature: str) -> bool:
    """Verilen plan için özelliğin aktif olup olmadığını kontrol eder."""
    config = get_plan_config(plan_type)
    return bool(config.get(feature, False))


def get_max_personas(plan_type: str) -> int:
    """Plan için maksimum persona sayısını döner."""
    return get_plan_config(plan_type)["max_personas"]


def get_min_plan_for_feature(feature: str) -> str:
    """Bir özellik için minimum plan adını döner."""
    return FEATURE_MIN_PLAN.get(feature, "Enterprise")
