"""Workflow paylasilan sabitleri (refactor R8)."""
from typing import Dict, List

DEFAULT_QUESTIONS = [
    "Bu ürün fikrini ilk duyduğunda hangi problemi çözdüğünü düşünüyorsun?",
    "Satın alma veya deneme kararında seni en çok ne durdurur?",
    "Bu çözüm hangi durumda para ödemeye değer olur?",
    "Hangi iddia sana abartılı, eksik veya güvenilmez gelir?",
    "Bu ürünü mevcut alternatiflerle kıyaslayınca en net avantaj ve dezavantaj ne olur?",
]

RESPONDENT_QUESTION_FILTER: dict[str, list[str]] = {
    "potential_customer": ["pain_point", "value", "positioning"],
    "competitor_user":    ["objection", "pricing", "positioning", "risk"],
    "churned_user":       ["pain_point", "objection", "risk"],
    "decision_maker":     ["pricing", "value", "risk"],
    "individual_user":    ["pain_point", "value", "positioning"],
}

DEFAULT_TRAIT_ORDER = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]

