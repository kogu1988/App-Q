"""providers.py — içerik-hash LLM önbelleği testleri (maliyet azaltma)."""
from __future__ import annotations

import packages.research_engine.providers as providers


def test_cache_key_is_stable_and_content_sensitive():
    k1 = providers._cache_key("m", "sys", "prompt", None, 100)
    k2 = providers._cache_key("m", "sys", "prompt", None, 100)
    k3 = providers._cache_key("m", "sys", "baska-prompt", None, 100)
    assert k1 == k2
    assert k1 != k3


def test_cache_set_get_roundtrip():
    key = providers._cache_key("m2", "sys", "unique-prompt-roundtrip", None, 100)
    assert providers._cache_get(key) is None
    providers._cache_set(key, "deger")
    assert providers._cache_get(key) == "deger"


def test_cache_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(providers, "LLM_CACHE_ENABLED", False)
    key = providers._cache_key("m3", "sys", "disabled-prompt", None, 100)
    providers._cache_set(key, "x")
    assert providers._cache_get(key) is None


def test_cache_empty_value_not_stored():
    key = providers._cache_key("m4", "sys", "empty-value", None, 100)
    providers._cache_set(key, "")
    assert providers._cache_get(key) is None
