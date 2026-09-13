"""Harici kanit (web corroboration) (R7-4)."""
from __future__ import annotations

import json
import logging
import re
import statistics
from dataclasses import asdict
from typing import Any

logger = logging.getLogger(__name__)

from ..adversarial import run_adversarial_review
from ..models import (
    DecisionItem,
    DecisionSignal,
    EnhancedFinding,
    Evidence,
    ExternalEvidence,
    Finding,
    Persona,
    PersonaInterview,
    PricingInsight,
    QualityIssue,
    ResearchBrief,
    ResearchPlan,
    ResearchReport,
    VanWestendorpInsight,
)


def _relevance_score(snippet: str, finding_keywords: set[str]) -> tuple[str, float]:
    """Snippet'ın bulgu anahtar kelimeleriyle örtüşme düzeyini hesaplar.

    Dönüş: (relevance_label, confidence_boost)
    """
    if not snippet:
        return ("low", 0.0)

    snippet_lower = snippet.lower()
    matches = sum(1 for kw in finding_keywords if kw.lower() in snippet_lower)
    total = len(finding_keywords)

    if total == 0:
        return ("low", 0.0)

    ratio = matches / total
    if ratio >= 0.5:
        return ("high", 0.10)
    elif ratio >= 0.25:
        return ("medium", 0.05)
    else:
        return ("low", 0.02)


# ---------------------------------------------------------------------------
# Sprint 6 — Web Corroboration (Dış Kanıt)
# ---------------------------------------------------------------------------

# NOT: Daha önce burada TÜAD/Statista/Deloitte/McKinsey adına uydurulmuş "yedek"
# kaynak listesi vardı. Bu kaynaklar gerçek dış kanıt değildi ve rapora doğrulanmış
# kanıt gibi girmesi ciddi bir güvenilirlik riskiydi. Kaldırıldı: harici arama
# başarısız olursa rapor boş dış kanıt + "Metodolojik Uyarılar" notu ile ilerler.


def corroborate_findings(
    findings: list[Finding],
    brief_title: str,
    category: str,
    degradation_notes: list[str] | None = None,
) -> list[ExternalEvidence]:
    """Her bulgu için web'de doğrulayıcı dış kanıt arar.

    SearXNG üzerinden hedefli arama yapar. Arama kullanılamıyorsa veya sonuç
    dönmezse **uydurma kaynak üretilmez**; boş liste döner ve `degradation_notes`
    içine metodolojik uyarı eklenir. Her bulgu için en fazla 3 kaynak döndürür.
    """
    import logging
    from urllib.parse import urlparse

    logger = logging.getLogger(__name__)

    external: list[ExternalEvidence] = []
    search_unavailable = False

    search_retriever = None
    search_available = False
    try:
        from ..search import search_retriever
        if search_retriever is not None:
            search_available = True
    except (ImportError, ModuleNotFoundError):
        search_unavailable = True
        logger.warning("SearXNG retriever import edilemedi; harici kanıt atlanıyor.")

    for finding in findings:
        finding_keywords = set(
            finding.title.split() + finding.summary.split()
        )

        results: list[dict] = []

        if search_available and search_retriever is not None:
            query = f"{finding.title} Turkey market research {category}"
            try:
                results = search_retriever.search(query, limit=5)
                logger.info(
                    f"SearXNG araması: '{query}' → {len(results)} sonuç"
                )
            except (OSError, ValueError, ConnectionError) as e:
                logger.warning(f"SearXNG araması başarısız: {e}")
                results = []

        if not results:
            search_unavailable = True

        for idx, res in enumerate(results):
            if idx >= 3:
                break

            snippet = res.get("content", "") or res.get("snippet", "")
            relevance, boost = _relevance_score(snippet, finding_keywords)
            url = res.get("url", "") or ""

            external.append(ExternalEvidence(
                finding_title=finding.title,
                source_title=res.get("title", "Bilinmeyen Kaynak"),
                source_url=url,
                snippet=snippet,
                relevance=relevance,
                confidence_boost=boost,
                source_domain=urlparse(url).netloc if url else "",
                is_verified=bool(url),
            ))

    # Sessiz degradasyonu önle: arama sonuç vermediyse rapora uyarı notu düş.
    if search_unavailable and degradation_notes is not None:
        degradation_notes.append(
            "Harici kanıt doğrulaması tamamlanamadı: web araması sonuç döndürmedi. "
            "Rapor yalnızca sentetik mülakat bulgularına dayanmaktadır; dış doğrulama yapılmamıştır."
        )
    return external
