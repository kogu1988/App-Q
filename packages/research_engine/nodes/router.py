"""
router.py — Keyword-based routing (semantic router simplified).

Ollama embedding/Qwen bağımlılığı kaldırıldı. DeepSeek API'ye geçişle
beraber model routing ihtiyacı da ortadan kalktı — tüm çağrılar
DeepSeek Flash (intake/interview) veya Pro (synthesis) üzerinden yapılıyor.

Bu modül yalnızca keyword-based fallback routing sağlar ve geriye dönük
uyumluluk için korunur.
"""
from __future__ import annotations


def _keyword_fallback(system: str, prompt: str) -> str:
    """Keyword-based routing — Ollama kaldırıldığı için tek seçenek."""
    text = (system + " " + prompt).lower()
    if any(kw in text for kw in ["defne", "araştırma mimarı", "intake", "brief", "sokratik"]):
        return "orchestrator"
    if any(kw in text for kw in ["sentez", "rapor sentezi", "b2b analist", "sentezleyici", "analiz", "rapor"]):
        return "synthesis"
    return "persona"


def route(system: str, prompt: str, base_url: str = "") -> str:
    """Semantic routing — keyword fallback yapar. base_url parametresi geriye dönük uyumluluk için tutulur."""
    return _keyword_fallback(system, prompt)


def reset_template_cache() -> None:
    """Önbellek temizliği (geriye dönük uyumluluk — artık önbellek yok)."""
    pass
