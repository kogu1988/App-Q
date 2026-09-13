"""Rapor metrikleri, model kullanimi ve kalite sorunlari (R7-5)."""
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


def summarize_model_usage(interviews: list[PersonaInterview]) -> dict[str, int]:
    usage: dict[str, int] = {}
    for interview in interviews:
        for turn in interview.turns:
            model_id = turn.model_id or "unknown"
            usage[model_id] = usage.get(model_id, 0) + 1
    return usage

def collect_quality_issues(interviews: list[PersonaInterview]) -> list[QualityIssue]:
    issue_text = {
        "meta_tone": "Cevapta asistan/meta tonu var.",
        "visible_reasoning": "Cevapta görünür muhakeme bloğu var.",
        "too_short": "Cevap karar çıkarmak için fazla kısa.",
        "weak_skepticism": "Şüpheci/Geciken persona yeterince sert itiraz üretmedi.",
        "weak_pricing_specificity": "Fiyat sorusunda TL, bütçe, abonelik veya ödeme modeli somutluğu zayıf.",
        "weak_turkey_context": "Türkiye pazarı bağlamı zayıf.",
    }
    issues: list[QualityIssue] = []
    for interview in interviews:
        for turn in interview.turns:
            for flag in turn.quality_flags:
                issues.append(
                    QualityIssue(
                        persona_id=interview.persona.id,
                        persona_name=interview.persona.name,
                        question=turn.question,
                        severity="fail" if flag in {"meta_tone", "visible_reasoning"} else "warning",
                        issue=issue_text.get(flag, flag),
                        recommendation="Bu cevabı yeniden üret veya raporda düşük güvenle kullan.",
                    )
                )
    return issues

def build_report_metrics(
    interviews: list[PersonaInterview],
    findings: list[Finding],
    enhanced_findings: list,
    external_evidence: list[ExternalEvidence],
    decision_items: list,
) -> dict:
    """Raporu yalnız uzunluğuyla değil, kanıt yoğunluğu ve izlenebilirlikle ölçer.

    Çıktı, raporun “Rapor Metrikleri” bölümünde ve admin panelinde gösterilir.
    """
    total_findings = len(findings) or len(enhanced_findings)
    evidence_total = 0
    findings_with_evidence = 0
    persona_ids: set[str] = set()
    supporting = 0
    refuting = 0
    neutral = 0

    for ef in enhanced_findings:
        ev = getattr(ef, "evidence", None)
        if ev is None and isinstance(ef, dict):
            ev = ef.get("evidence", [])
        ev = ev or []
        if ev:
            findings_with_evidence += 1
        evidence_total += len(ev)
        supporting += int(getattr(ef, "supporting_count", 0) or (ef.get("supporting_count", 0) if isinstance(ef, dict) else 0))
        refuting += int(getattr(ef, "refuting_count", 0) or (ef.get("refuting_count", 0) if isinstance(ef, dict) else 0))
        neutral += int(getattr(ef, "neutral_count", 0) or (ef.get("neutral_count", 0) if isinstance(ef, dict) else 0))
        for e in ev:
            pid = getattr(e, "persona_id", None) if not isinstance(e, dict) else e.get("persona_id")
            if pid:
                persona_ids.add(str(pid))

    polarity_total = supporting + refuting
    refuting_ratio = round(refuting / polarity_total, 3) if polarity_total else 0.0
    answered_turns = sum(
        1
        for iv in interviews
        for t in (getattr(iv, "turns", None) or [])
        if (getattr(t, "answer", "") or "").strip() and "[Yanıt alınamadı]" not in (getattr(t, "answer", "") or "")
    )
    total_turns = sum(len(getattr(iv, "turns", None) or []) for iv in interviews)

    signal_counts: dict[str, int] = {}
    for di in decision_items:
        sig = getattr(di, "signal", None) if not isinstance(di, dict) else di.get("signal")
        if sig:
            signal_counts[sig] = signal_counts.get(sig, 0) + 1

    return {
        "findings_total": total_findings,
        "findings_with_evidence": findings_with_evidence,
        "evidence_total": evidence_total,
        "evidence_per_finding": round(evidence_total / total_findings, 2) if total_findings else 0.0,
        "unsourced_findings": max(total_findings - findings_with_evidence, 0),
        "unique_personas_in_evidence": len(persona_ids),
        "refuting_ratio": refuting_ratio,
        "supporting_count": supporting,
        "refuting_count": refuting,
        "neutral_count": neutral,
        "answered_turns": answered_turns,
        "total_turns": total_turns,
        "answer_completion_rate": round(answered_turns / total_turns, 3) if total_turns else 0.0,
        "external_evidence_count": len(external_evidence),
        "decision_signals": signal_counts,
    }
