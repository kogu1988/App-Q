"""Bulgu cikarimi, pain-point matrisi ve segment ozetleri (R7-1)."""
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
from .enrichment import _shorten


def build_pain_point_matrix(interviews: list[PersonaInterview]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for interview in interviews:
        pain_answers = [turn.answer for turn in interview.turns if "pain_point" in turn.tags]
        objection_answers = [turn.answer for turn in interview.turns if "objection" in turn.tags]
        pricing_answers = [turn.answer for turn in interview.turns if "pricing" in turn.tags]
        rows.append(
            {
                "persona": interview.persona.name,
                "segment": interview.persona.segment,
                "primary_pain": pain_answers[0] if pain_answers else "Belirlenmedi",
                "main_objection": objection_answers[0] if objection_answers else "Belirlenmedi",
                "pricing_signal": pricing_answers[0] if pricing_answers else "Belirlenmedi",
            }
        )
    return rows

def collect_evidence(interviews: list[PersonaInterview], tag: str, limit: int = 4) -> list[Evidence]:
    evidence: list[Evidence] = []
    for interview in interviews:
        for turn in interview.turns:
            if tag in turn.tags:
                evidence.append(
                    Evidence(
                        persona_id=interview.persona.id,
                        persona_name=interview.persona.name,
                        stance=interview.persona.stance,
                        quote=turn.answer,
                        source_question=turn.question,
                    )
                )
    return evidence[:limit]

def build_ses_cross_tab(interviews: list[PersonaInterview]) -> list[dict[str, Any]]:
    """
    TÜAD 2025 SES grubu (AB/C1/C2/DE) x Stance (Champion/Skeptic/...) çapraz tablosu.
    Her satır bir persona'yı ve oy ağırlığını gösterir.
    """
    SES_ORDER = ["AB", "C1", "C2", "DE"]
    # Rogers Diffusion stance kategorileri
    STANCE_ORDER = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]

    # Grup sayımları
    matrix: dict[str, dict[str, int]] = {ses: {st: 0 for st in STANCE_ORDER} for ses in SES_ORDER}
    totals: dict[str, int] = {ses: 0 for ses in SES_ORDER}

    for iv in interviews:
        ses = getattr(iv.persona, "ses_group", "C1") or "C1"
        stance = iv.persona.stance or "Mainstream"
        if ses not in matrix:
            matrix[ses] = {st: 0 for st in STANCE_ORDER}
            totals[ses] = 0
        col = stance if stance in STANCE_ORDER else "Mainstream"
        matrix[ses][col] += 1
        totals[ses] += 1

    rows: list[dict[str, Any]] = []
    for ses in SES_ORDER:
        if totals.get(ses, 0) == 0:
            continue
        dominant_stance = max(matrix[ses], key=lambda s: matrix[ses][s])
        rows.append({
            "ses_group": ses,
            "total": totals[ses],
            "stance_counts": matrix[ses],
            "dominant_stance": dominant_stance,
        })
    return rows


def build_respondent_type_summary(interviews: list[PersonaInterview]) -> list[dict[str, Any]]:
    """
    Katılımcı tipi (respondent_type) bazında pain_point, objection ve pricing
    alıntılarını gruplayarak özetler. Her tip için ortalama fiyat hassasiyetini de verir.
    """
    RESPONDENT_LABELS = {
        "potential_customer": "Potansiyel Müşteri",
        "competitor_user": "Rakip Kullanıcısı",
        "churned_user": "Kaybedilmiş Kullanıcı",
        "decision_maker": "Karar Verici",
        "individual_user": "Bireysel Kullanıcı",
    }
    groups: dict[str, dict[str, Any]] = {}

    for iv in interviews:
        rtype = getattr(iv.persona, "respondent_type", "potential_customer") or "potential_customer"
        if rtype not in groups:
            groups[rtype] = {
                "respondent_type": rtype,
                "label": RESPONDENT_LABELS.get(rtype, rtype),
                "count": 0,
                "avg_price_sensitivity": 0.0,
                "top_pain": None,
                "top_objection": None,
            }
        g = groups[rtype]
        g["count"] += 1
        g["avg_price_sensitivity"] = (
            (g["avg_price_sensitivity"] * (g["count"] - 1) + iv.persona.price_sensitivity) / g["count"]
        )
        for turn in iv.turns:
            if "pain_point" in (turn.tags or []) and not g["top_pain"]:
                g["top_pain"] = _shorten(turn.answer, 240)
            if "objection" in (turn.tags or []) and not g["top_objection"]:
                g["top_objection"] = _shorten(turn.answer, 240)

    return list(groups.values())

def build_brand_health_summary(
    interviews: list[PersonaInterview],
    competitors: list[str],
) -> dict | None:
    """
    Marka sağlığı özeti:
    - Yardımsız bilinç (unaided recall): kimin adı geçti?
    - Çağrışım: rakip markalar hakkında kullanılan sıfat ve sözcler
    """
    if not competitors:
        return None

    unaided_counts: dict[str, int] = {c: 0 for c in competitors}
    unaided_counts["diğer"] = 0
    associations: dict[str, list[str]] = {c: [] for c in competitors}

    STOP_WORDS = {
        "bir", "ve", "bu", "ile", "da", "de", "ki", "o", "ben", "sen",
        "biz", "siz", "ama", "ya", "gibi", "için", "olan", "daha", "en",
        "onlar", "olarak", "ne", "nasıl", "neden", "çok", "az",
    }

    for iv in interviews:
        for turn in iv.turns:
            # Yardımsız bilinç (BRAND-UNAIDED tag)
            if turn.question and "BRAND-UNAIDED" in turn.question.upper() or \
               (turn.tags and "positioning" in turn.tags):
                ans_lower = turn.answer.lower()
                mentioned = False
                for comp in competitors:
                    if comp.lower() in ans_lower:
                        unaided_counts[comp] += 1
                        mentioned = True
                if not mentioned:
                    unaided_counts["diğer"] += 1

            # Çağrışım (BRAND-ASSOCIATION)
            if turn.question and "BRAND-ASSOCIATION" in turn.question.upper():
                words = [
                    w for w in turn.answer.lower().split()
                    if len(w) > 3 and w not in STOP_WORDS
                ]
                ans_lower = turn.answer.lower()
                for comp in competitors:
                    if comp.lower() in ans_lower:
                        associations[comp].extend(words[:8])

    # Association frequency per competitor
    assoc_summary: dict[str, list[str]] = {}
    for comp, words in associations.items():
        if words:
            freq: dict[str, int] = {}
            for w in words:
                freq[w] = freq.get(w, 0) + 1
            top = sorted(freq, key=lambda x: freq[x], reverse=True)[:5]
            assoc_summary[comp] = top

    total_mentions = sum(v for k, v in unaided_counts.items() if k != "diğer")
    top_of_mind = max(
        (k for k in unaided_counts if k != "diğer"),
        key=lambda k: unaided_counts[k],
        default=None,
    ) if unaided_counts else None

    return {
        "unaided_recall": unaided_counts,
        "associations": assoc_summary,
        "top_of_mind": top_of_mind,
        "total_mentions": total_mentions,
    }


def build_channel_map(interviews: list[PersonaInterview]) -> list[dict]:
    """
    Mülakat yanıtlarından keşif kanalı frekans haritası üretir.
    """
    CHANNEL_KEYWORDS: dict[str, list[str]] = {
        "Sosyal Medya":        ["sosyal medya", "instagram", "twitter", "linkedin", "tiktok", "youtube", "facebook", "x.com"],
        "Arama Motoru":        ["google", "yandex", "arama", "arama motoru", "search"],
        "Arkadaş Tavsiyesi":  ["tavsiye", "arkadaş", "ağız", "referans", "söyledi", "duydum"],
        "Haber / Blog":        ["haber", "blog", "makale", "yazı", "içerik", "medium", "substack"],
        "Uygulama Mağazası":  ["app store", "play store", "uygulama mağazası", "mağaza"],
        "Doğrudan / Web":     ["web sitesi", "direkt", "doğrudan", "url", "link"],
        "E-posta / Bülten":   ["e-posta", "eposta", "mail", "bülten", "newsletter"],
    }

    counts: dict[str, int] = {ch: 0 for ch in CHANNEL_KEYWORDS}

    for iv in interviews:
        for turn in iv.turns:
            if not turn.tags or "positioning" not in turn.tags:
                continue
            ans_lower = turn.answer.lower()
            for channel, keywords in CHANNEL_KEYWORDS.items():
                if any(kw in ans_lower for kw in keywords):
                    counts[channel] += 1
                    break  # Her cevap bir kanala sayılır

    # Sadece mention edilenleri dön, frekansa göre sırala
    results = [
        {"channel": ch, "count": cnt, "pct": 0}
        for ch, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        if cnt > 0
    ]
    total = sum(r["count"] for r in results)
    for r in results:
        r["pct"] = round(r["count"] / total * 100, 1) if total else 0

    return results
