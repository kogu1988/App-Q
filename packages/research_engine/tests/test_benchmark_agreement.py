"""Sprint 8 (kısmi) — Benchmark harness: uyum, doğrulama ve özet testleri."""
from __future__ import annotations

from packages.research_engine.benchmark import (
    case_is_annotated,
    cohens_kappa,
    summarize_rfi,
    validate_case,
)


# ── Cohen's kappa ───────────────────────────────────────────────────────────

def test_kappa_perfect_agreement():
    labels = ["match", "no_match", "partial", "match"]
    assert cohens_kappa(labels, labels) == 1.0


def test_kappa_symmetric():
    a = ["match", "no_match", "partial", "match"]
    b = ["match", "partial", "partial", "no_match"]
    assert cohens_kappa(a, b) == cohens_kappa(b, a)


def test_kappa_returns_none_for_mismatched_lengths():
    assert cohens_kappa(["match"], ["match", "no_match"]) is None
    assert cohens_kappa([], []) is None


def test_kappa_with_partial_disagreement_is_between_0_and_1():
    a = ["match", "match", "no_match", "no_match", "partial"]
    b = ["match", "no_match", "no_match", "no_match", "partial"]
    kappa = cohens_kappa(a, b)
    assert kappa is not None
    assert 0.0 <= kappa < 1.0


def test_kappa_single_category():
    assert cohens_kappa(["match", "match"], ["match", "match"]) == 1.0
    assert cohens_kappa(["match", "match"], ["match", "no_match"]) == 0.0


# ── Vaka doğrulama ──────────────────────────────────────────────────────────

def _base_case():
    return {
        "id": "study_x",
        "name": "X",
        "brief": {},
        "llm_findings": [{"title": "a", "summary": "b"}],
        "human_findings": [],
    }


def test_validate_case_accepts_valid_skeleton():
    assert validate_case(_base_case()) == []


def test_validate_case_reports_missing_fields():
    problems = validate_case({"id": "x"})
    assert any("name" in p for p in problems)
    assert any("human_findings" in p for p in problems)


def test_validate_case_rejects_non_list_findings():
    case = _base_case()
    case["human_findings"] = "metin"
    assert any("liste" in p for p in validate_case(case))


def test_case_is_annotated_requires_human_and_validation():
    case = _base_case()
    assert case_is_annotated(case) is False

    case["human_findings"] = [{"title": "h", "summary": "s"}]
    assert case_is_annotated(case) is False  # synthetic_validation yok

    case["synthetic_validation"] = {"method": "real_user_interview"}
    assert case_is_annotated(case) is True


# ── Özet ────────────────────────────────────────────────────────────────────

def test_summarize_empty_is_safe():
    s = summarize_rfi([])
    assert s["cases"] == 0
    assert s["mean_rfi"] == 0.0


def test_summarize_computes_mean_min_max():
    results = [
        {"overall_rfi": 0.8, "theme_recall": 0.9, "theme_precision": 0.7, "critical_recall": 0.8, "false_positive_rate": 0.1, "segment_accuracy": 0.9},
        {"overall_rfi": 0.6, "theme_recall": 0.7, "theme_precision": 0.5, "critical_recall": 0.6, "false_positive_rate": 0.2, "segment_accuracy": 0.8},
    ]
    s = summarize_rfi(results)
    assert s["cases"] == 2
    assert s["mean_rfi"] == 0.7
    assert s["min_rfi"] == 0.6
    assert s["max_rfi"] == 0.8
    assert s["mean_metrics"]["theme_recall"] == 0.8
