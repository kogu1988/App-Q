"""GRUP 10 — RFI Benchmark Formülü testleri.

Korunan değer: Bilimsel iddia. Ağırlıklar kayarsa yayınlanan skorlar geçersiz olur.

Ağırlıklar: theme_recall 0.30 · theme_precision 0.25 · critical_recall 0.25 ·
(1 - false_positive_rate) 0.20
"""
from __future__ import annotations

import json
import pathlib

import pytest

from packages.research_engine.benchmark import _rfi_grade, calculate_rfi

MATCHING_FINDINGS = [{"title": "Fiyat hassasiyeti", "summary": "Kullanıcılar fiyata duyarlı"}]
DISTINCT_LLM = [{"title": "aaaa", "summary": "bbbb"}]
DISTINCT_HUMAN = [{"title": "cccc", "summary": "dddd"}]

SAMPLES_PATH = pathlib.Path("data/evals/rfi_benchmark_samples.json")


def test_10_1_full_match_scores_one_and_grade_a():
    """Birebir aynı bulgu setleri RFI 1.0 ve A notu üretmeli."""
    result = calculate_rfi(MATCHING_FINDINGS, MATCHING_FINDINGS)

    assert result["overall_rfi"] == pytest.approx(1.0, abs=1e-6)
    assert result["grade"] == "A"


def test_10_2_no_match_scores_low_and_grade_f():
    """Hiç örtüşmeyen bulgu setleri düşük skor ve F notu üretmeli."""
    result = calculate_rfi(DISTINCT_LLM, DISTINCT_HUMAN)

    assert result["overall_rfi"] < 0.55
    assert result["grade"] == "F"


def test_10_3_weight_formula_matches_manual_calculation():
    """Ağırlıklı kompozit formülü elle hesapla birebir uyuşmalı."""
    result = calculate_rfi(MATCHING_FINDINGS, MATCHING_FINDINGS, human_critical=[])

    expected = (
        result["theme_recall"] * 0.30
        + result["theme_precision"] * 0.25
        + result["critical_recall"] * 0.25
        + (1.0 - result["false_positive_rate"]) * 0.20
    )
    assert result["overall_rfi"] == pytest.approx(min(1.0, max(0.0, expected)), abs=1e-3)


def test_10_4_grade_thresholds():
    """Harf notu eşikleri: 0.85→A, 0.75→B, 0.65→C, 0.55→D, altı→F."""
    assert _rfi_grade(0.90) == "A"
    assert _rfi_grade(0.85) == "A"
    assert _rfi_grade(0.75) == "B"
    assert _rfi_grade(0.65) == "C"
    assert _rfi_grade(0.55) == "D"
    assert _rfi_grade(0.54) == "F"


def test_10_5_empty_input_does_not_crash():
    """Boş girdi çökmemeli."""
    result = calculate_rfi([], [])

    assert "overall_rfi" in result
    assert "grade" in result


def test_10_6_all_metrics_within_unit_range():
    """Tüm metrikler 0..1 aralığında olmalı."""
    result = calculate_rfi(MATCHING_FINDINGS, DISTINCT_HUMAN)

    for key in ("theme_recall", "theme_precision", "critical_recall", "false_positive_rate", "segment_accuracy"):
        value = result[key]
        assert 0.0 <= value <= 1.0, f"{key}={value}"
    assert 0.0 <= result["overall_rfi"] <= 1.0


def test_10_7_sample_benchmark_file_is_schema_valid():
    """Örnek benchmark dosyası 5 senaryo ve zorunlu alanları içermeli."""
    if not SAMPLES_PATH.exists():
        pytest.skip(f"{SAMPLES_PATH} bulunamadı")

    data = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    scenarios = data if isinstance(data, list) else data.get("scenarios", [])

    assert len(scenarios) == 5, f"beklenen 5 senaryo, bulunan {len(scenarios)}"
    for scenario in scenarios:
        assert "brief" in scenario or "title" in scenario
        assert "llm_findings" in scenario or "human_findings" in scenario
