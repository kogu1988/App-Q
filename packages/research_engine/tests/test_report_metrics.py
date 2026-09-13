"""Sprint 3 — Rapor kalite metrikleri regresyon testleri."""
from __future__ import annotations

from packages.research_engine.analytics import build_report_metrics
from packages.research_engine.models import EnhancedFinding, Evidence


def _ef(title: str, ev: int, sup: int, ref: int, neu: int) -> EnhancedFinding:
    evidence = [
        Evidence(
            persona_id=f"p{i}",
            persona_name=f"P{i}",
            stance="Mainstream",
            quote="alıntı",
            source_question="soru",
        )
        for i in range(ev)
    ]
    return EnhancedFinding(
        title=title,
        category="pricing",
        summary="özet",
        confidence=0.5,
        evidence=evidence,
        implication="çıkarım",
        supporting_count=sup,
        refuting_count=ref,
        neutral_count=neu,
    )


def test_metrics_counts_evidence_and_unsourced():
    findings = [_ef("A", 2, 2, 1, 0), _ef("B", 0, 0, 0, 0)]

    m = build_report_metrics([], [], findings, [], [])

    assert m["findings_total"] == 2
    assert m["findings_with_evidence"] == 1
    assert m["unsourced_findings"] == 1
    assert m["evidence_total"] == 2
    assert m["evidence_per_finding"] == 1.0


def test_metrics_refuting_ratio_and_unique_personas():
    findings = [_ef("A", 2, 2, 1, 0)]

    m = build_report_metrics([], [], findings, [], [])

    assert m["supporting_count"] == 2
    assert m["refuting_count"] == 1
    assert m["refuting_ratio"] == round(1 / 3, 3)
    assert m["unique_personas_in_evidence"] == 2


def test_metrics_handles_dict_form():
    """Kalıcı JSON'dan gelen dict biçimi de desteklenmeli (tolerant)."""
    findings = [
        {
            "title": "A",
            "evidence": [{"persona_id": "p1"}, {"persona_id": "p2"}],
            "supporting_count": 1,
            "refuting_count": 0,
            "neutral_count": 1,
        }
    ]

    m = build_report_metrics([], [], findings, [], [])

    assert m["findings_with_evidence"] == 1
    assert m["evidence_total"] == 2
    assert m["unique_personas_in_evidence"] == 2


def test_metrics_empty_is_safe():
    m = build_report_metrics([], [], [], [], [])

    assert m["findings_total"] == 0
    assert m["evidence_per_finding"] == 0.0
    assert m["refuting_ratio"] == 0.0
    assert m["external_evidence_count"] == 0
