"""Sprint 7 — LLM içerik-hash önbelleği regresyon testleri (S7-6).

Korunan değer: Maliyet. Aynı (model, system, prompt, format, max_tokens, effort)
için ikinci çağrı API'ye gitmemeli; farklı girdi ise isabet ETMEMELİ
(yanlış eşleşme = yanlış cevap riski).
"""
from __future__ import annotations

from packages.research_engine import providers


def _key(**over):
    base = dict(
        model_id="deepseek-flash",
        system="sys",
        prompt="user prompt",
        response_format=None,
        max_tokens=1024,
        effort="high",
    )
    base.update(over)
    return providers._cache_key(**base)


def test_cache_key_is_deterministic():
    assert _key() == _key()


def test_cache_key_changes_on_each_input_dimension():
    baseline = _key()
    variants = [
        _key(model_id="deepseek-v4-pro"),
        _key(system="sys2"),
        _key(prompt="farklı"),
        _key(response_format="json"),
        _key(max_tokens=2048),
        _key(effort="low"),
    ]
    for v in variants:
        assert v != baseline, "Girdi değişince önbellek anahtarı değişmeli"


def test_cache_set_and_get_roundtrip():
    key = _key(prompt="roundtrip-test")
    providers._cache_set(key, "cevap")

    assert providers._cache_get(key) == "cevap"


def test_cache_get_missing_returns_none():
    assert providers._cache_get(_key(prompt="kesinlikle-yok-" + str(id(object())))) is None


def test_cache_ignores_empty_value():
    key = _key(prompt="empty-value-test")
    providers._cache_set(key, "")
    providers._LLM_CACHE.pop(key, None)
    assert providers._cache_get(key) is None


def test_cache_stats_shape():
    stats = providers.get_llm_cache_stats()
    assert set(stats) >= {"enabled", "size", "hits", "misses"}


def test_cache_lru_eviction_respects_max(monkeypatch):
    # Küçük bir üst sınırla LRU tahliyesini doğrula.
    monkeypatch.setattr(providers, "_LLM_CACHE_MAX", 2)
    providers._LLM_CACHE.clear()

    providers._cache_set("k1", "v1")
    providers._cache_set("k2", "v2")
    providers._cache_set("k3", "v3")  # k1 tahliye edilmeli

    assert providers._cache_get("k1") is None
    assert providers._cache_get("k2") == "v2"
    assert providers._cache_get("k3") == "v3"
