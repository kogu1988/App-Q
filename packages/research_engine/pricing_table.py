"""DeepSeek model fiyatlandırma tablosu — USD / 1M token.

Maliyet muhasebesinin TEK doğruluk kaynağı (SSOT). DeepSeek fiyatları değiştiğinde
SADECE bu dosya güncellenir; alternatif olarak ortam değişkenleriyle override edilir:

    DEEPSEEK_PRICE_FLASH_INPUT, DEEPSEEK_PRICE_FLASH_OUTPUT, DEEPSEEK_PRICE_FLASH_CACHE_HIT
    DEEPSEEK_PRICE_PRO_INPUT,   DEEPSEEK_PRICE_PRO_OUTPUT,   DEEPSEEK_PRICE_PRO_CACHE_HIT

Not: DeepSeek context caching'de cache-hit token'lar indirimli faturalanır; bu yüzden
cache-hit ve cache-miss ayrı satırlar olarak hesaplanır.
"""
from __future__ import annotations

import os


def _price(env_key: str, default: float) -> float:
    try:
        return float(os.getenv(env_key, str(default)))
    except (TypeError, ValueError):
        return default


# USD / 1M token. Değerler DeepSeek resmi fiyat sayfasından doğrulanmalıdır.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": {
        "input": _price("DEEPSEEK_PRICE_FLASH_INPUT", 0.0),
        "output": _price("DEEPSEEK_PRICE_FLASH_OUTPUT", 0.0),
        "cache_hit": _price("DEEPSEEK_PRICE_FLASH_CACHE_HIT", 0.0),
    },
    "deepseek-v4-pro": {
        "input": _price("DEEPSEEK_PRICE_PRO_INPUT", 0.0),
        "output": _price("DEEPSEEK_PRICE_PRO_OUTPUT", 0.0),
        "cache_hit": _price("DEEPSEEK_PRICE_PRO_CACHE_HIT", 0.0),
    },
}

DEFAULT_PRICING: dict[str, float] = {"input": 0.0, "output": 0.0, "cache_hit": 0.0}

_TOKENS_PER_MILLION = 1_000_000


def calculate_cost(
    model_id: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cache_hit_tokens: int = 0,
    cache_miss_tokens: int | None = None,
) -> float:
    """Bir LLM çağrısının USD maliyetini hesaplar.

    cache_miss_tokens verilmezse prompt_tokens - cache_hit_tokens olarak türetilir.
    """
    price = MODEL_PRICING.get(model_id, DEFAULT_PRICING)

    if cache_miss_tokens is None:
        cache_miss_tokens = max(int(prompt_tokens or 0) - int(cache_hit_tokens or 0), 0)

    input_cost = (max(cache_miss_tokens, 0) / _TOKENS_PER_MILLION) * price["input"]
    cache_cost = (max(int(cache_hit_tokens or 0), 0) / _TOKENS_PER_MILLION) * price["cache_hit"]
    output_cost = (max(int(completion_tokens or 0), 0) / _TOKENS_PER_MILLION) * price["output"]

    return round(input_cost + cache_cost + output_cost, 6)
