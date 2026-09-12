"""GRUP 8 — Adversarial Review (4 Aşama) testleri.

Korunan değer: Kalite denetim katmanı — raporun kendi kendini eleştirme yeteneği.
Bias, evidence chain, çift simülasyon ve echo drift aşamaları çalışmaya devam etmeli.
"""
from __future__ import annotations

from packages.research_engine.adversarial import (
    MIN_STANCE_DIVERSITY,
    bias_audit,
    echo_drift_audit,
    evidence_chain_validation,
    run_adversarial_review,
)


def _personas(stances, ses_groups=None):
    ses_groups = ses_groups or ["C1"] * len(stances)
    return [
        {"name": f"P{i}", "stance": stance, "ses_group": ses}
        for i, (stance, ses) in enumerate(zip(stances, ses_groups))
    ]


def test_8_1_low_stance_diversity_is_flagged():
    """Panelde yetersiz stance çeşitliliği LOW_STANCE_DIVERSITY flag'i üretmeli."""
    report = {"personas": _personas(["Mainstream", "Mainstream"]), "findings": []}

    codes = {flag["code"] for flag in bias_audit(report)}

    assert "LOW_STANCE_DIVERSITY" in codes
    assert MIN_STANCE_DIVERSITY >= 3


def test_8_2_ses_dominance_is_flagged():
    """Tek SES grubunun %60+ hakimiyeti SES_DOMINANCE flag'i üretmeli."""
    report = {
        "personas": _personas(["Innovator", "Mainstream", "Skeptic"], ["C1", "C1", "C1"]),
        "findings": [],
    }

    codes = {flag["code"] for flag in bias_audit(report)}

    assert "SES_DOMINANCE" in codes


def test_8_3_single_stance_evidence_is_flagged():
    """Tek stance'tan gelen 3+ kanıt PERSONA_CONVERGENCE uyarısı üretmeli."""
    report = {
        "personas": _personas(["Innovator", "Mainstream", "Skeptic"]),
        "findings": [
            {
                "title": "Tek taraflı bulgu",
                "evidence": [{"stance": "Mainstream"}] * 3,
            }
        ],
    }

    codes = {flag["code"] for flag in bias_audit(report)}

    assert "PERSONA_CONVERGENCE" in codes


def test_8_4_evidence_chain_phase_emits_structured_flags():
    """Evidence chain aşaması yapılandırılmış flag listesi döndürmeli (düşük kanıt senaryosu)."""
    report = {
        "findings": [
            {
                "title": "Yüksek güvenli ama az kanıtlı bulgu",
                "confidence": 0.9,
                "evidence": [{"stance": "Mainstream", "quote": "tek kanıt"}],
            }
        ]
    }

    flags = evidence_chain_validation(report)

    assert isinstance(flags, list)
    for flag in flags:
        assert "code" in flag
        assert "message" in flag


def test_8_5_echo_drift_phase_runs():
    """Echo drift aşaması çökmeden çalışmalı ve liste döndürmeli."""
    report = {
        "interviews": [
            {
                "persona": {"name": "P1"},
                "turns": [
                    {"question": "Q1", "answer": "Aynı cevap metni burada"},
                    {"question": "Q2", "answer": "Aynı cevap metni burada"},
                ],
            }
        ]
    }

    assert isinstance(echo_drift_audit(report), list)


def test_8_6_all_four_phases_run_through_main_entry():
    """run_adversarial_review 4 aşamayı da çalıştırıp dict döndürmeli."""
    report = {
        "personas": _personas(["Innovator", "Mainstream", "Skeptic"]),
        "findings": [],
        "interviews": [],
    }

    result = run_adversarial_review(report)

    assert isinstance(result, dict)


def test_8_7_healthy_report_gets_no_bias_warnings():
    """Dengeli panel + çok stance'lı kanıt → bias uyarısı olmamalı."""
    report = {
        "personas": _personas(
            ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"],
            ["AB", "C1", "C2", "C1", "DE"],
        ),
        "findings": [
            {
                "title": "Dengeli bulgu",
                "evidence": [{"stance": "Innovator"}, {"stance": "Mainstream"}, {"stance": "Skeptic"}],
            }
        ],
    }

    assert bias_audit(report) == []
