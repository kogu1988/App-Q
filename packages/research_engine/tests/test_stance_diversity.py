"""
Test: Stance Diversity Doğrulaması

Kapsam:
  - stance_balance_score() Shannon entropy hesabı
  - validate_stance_diversity() tüm kontroller
  - allocate_cohort_matrix() sonrası diversiy garantisi
  - Skeptic zorunluluğu (anti-sycophancy guard)
  - Sabit değer doğrulaması
"""
from __future__ import annotations
import math

from packages.research_engine.matrix import (
    stance_balance_score,
    validate_stance_diversity,
    allocate_cohort_matrix,
    P_ROGERS,
    MIN_STANCE_COUNT,
    SKEPTIC_REQUIRED,
)


# ── Sabit Testler ─────────────────────────────────────────────────────────────

def test_min_stance_count_value():
    """Minimum stance sayısı 3 olmalı (adversarial.py ile senkron)."""
    assert MIN_STANCE_COUNT == 3


def test_skeptic_required_true():
    """Skeptic her zaman zorunlu olmalı (anti-sycophancy guard)."""
    assert SKEPTIC_REQUIRED is True


def test_rogers_has_skeptic():
    """P_ROGERS dağılımında Skeptic bulunmalı."""
    assert "Skeptic" in P_ROGERS


def test_rogers_probabilities_sum_to_one():
    """Rogers dağılımı toplamı 1.0'a eşit olmalı."""
    total = sum(P_ROGERS.values())
    assert abs(total - 1.0) < 1e-9


# ── stance_balance_score Testleri ─────────────────────────────────────────────

def test_balance_score_empty_list():
    """Boş liste → 0.0 dönmeli."""
    assert stance_balance_score([]) == 0.0


def test_balance_score_single_stance():
    """Tek stance → 0.0 (hiç çeşitlilik yok)."""
    personas = [{"stance": "Mainstream"}] * 5
    assert stance_balance_score(personas) == 0.0


def test_balance_score_all_stances_equal():
    """Tüm stance'lar eşit → 1.0 (maksimum çeşitlilik)."""
    stances = list(P_ROGERS.keys())
    personas = [{"stance": s} for s in stances]
    score = stance_balance_score(personas)
    assert abs(score - 1.0) < 1e-9


def test_balance_score_range():
    """Skor her zaman [0, 1] aralığında olmalı."""
    personas = [
        {"stance": "Innovator"},
        {"stance": "Innovator"},
        {"stance": "Skeptic"},
        {"stance": "Mainstream"},
    ]
    score = stance_balance_score(personas)
    assert 0.0 <= score <= 1.0


def test_balance_score_more_diverse_higher():
    """Daha çeşitli panel daha yüksek skor almalı."""
    low_diversity = [{"stance": "Mainstream"}] * 8 + [{"stance": "Skeptic"}] * 2
    high_diversity = [{"stance": s} for s in list(P_ROGERS.keys()) * 2]
    assert stance_balance_score(high_diversity) > stance_balance_score(low_diversity)


def test_balance_score_returns_float():
    """Dönüş tipi her zaman float olmalı."""
    result = stance_balance_score([{"stance": "Mainstream"}])
    assert isinstance(result, float)


# ── validate_stance_diversity Testleri ───────────────────────────────────────

def _make_panel(stances: list[str]) -> list[dict]:
    return [{"stance": s, "ses_group": "C1"} for s in stances]


def test_validate_empty_panel():
    """Boş panel → valid=False."""
    result = validate_stance_diversity([])
    assert result["valid"] is False
    assert result["stance_count"] == 0
    assert result["has_skeptic"] is False


def test_validate_full_diverse_panel():
    """Tüm stance'lar mevcut → valid=True."""
    stances = list(P_ROGERS.keys())  # 5 farklı stance
    result = validate_stance_diversity(_make_panel(stances))
    assert result["valid"] is True
    assert result["stance_count"] == 5
    assert result["has_skeptic"] is True


def test_validate_missing_skeptic():
    """Skeptic olmayan panel → valid=False, issues listesinde Skeptic uyarısı."""
    stances = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard"]  # Skeptic yok
    result = validate_stance_diversity(_make_panel(stances))
    assert result["valid"] is False
    assert result["has_skeptic"] is False
    assert any("Skeptic" in issue for issue in result["issues"])


def test_validate_too_few_stances():
    """2 farklı stance → minimum 3 koşulunu sağlamıyor → issues içinde uyarı."""
    stances = ["Innovator", "Innovator", "Skeptic", "Skeptic"]
    result = validate_stance_diversity(_make_panel(stances))
    assert result["stance_count"] == 2
    assert any(str(MIN_STANCE_COUNT) in issue for issue in result["issues"])


def test_validate_dominant_stance_warns():
    """Tek stance %60+ baskın → issues içinde uyarı (n>=3 şartı)."""
    stances = ["Mainstream"] * 7 + ["Skeptic"] * 1 + ["Innovator"] * 1 + \
              ["EarlyAdopter"] * 1
    result = validate_stance_diversity(_make_panel(stances))
    assert any("Mainstream" in issue for issue in result["issues"])


def test_validate_returns_distribution():
    """stance_distribution doğru sayıları içermeli."""
    stances = ["Innovator", "Skeptic", "Skeptic", "Mainstream"]
    result = validate_stance_diversity(_make_panel(stances))
    assert result["stance_distribution"]["Skeptic"] == 2
    assert result["stance_distribution"]["Innovator"] == 1
    assert result["stance_distribution"]["Mainstream"] == 1


def test_validate_balance_score_in_result():
    """Sonuç dict'i balance_score içermeli."""
    result = validate_stance_diversity(_make_panel(list(P_ROGERS.keys())))
    assert "balance_score" in result
    assert isinstance(result["balance_score"], float)


def test_validate_issues_is_list():
    """issues her zaman liste olmalı."""
    result = validate_stance_diversity(_make_panel(["Mainstream"]))
    assert isinstance(result["issues"], list)


# ── allocate_cohort_matrix Entegrasyon Testi ──────────────────────────────────

def test_allocate_cohort_diversity_guaranteed():
    """allocate_cohort_matrix(N>=8) → validate_stance_diversity geçmeli."""
    for n in [8, 10, 15]:
        personas = allocate_cohort_matrix(n)
        result = validate_stance_diversity(personas)
        assert result["valid"] is True, (
            f"N={n} için stance diversity başarısız: {result['issues']}"
        )


def test_allocate_cohort_has_all_stances():
    """N>=5 için tüm Rogers stance'ları temsil edilmeli."""
    personas = allocate_cohort_matrix(10)
    stances_in_panel = {p["stance"] for p in personas}
    for stance in P_ROGERS:
        assert stance in stances_in_panel, f"'{stance}' panelde yok (N=10)"


def test_allocate_cohort_has_skeptic():
    """N>=5 panellerde Skeptic bulunmalı (anti-sycophancy guard garantisi)."""
    for n in [5, 8, 10, 15]:
        personas = allocate_cohort_matrix(n)
        stances = [p["stance"] for p in personas]
        assert "Skeptic" in stances, f"N={n} için Skeptic eksik"


def test_allocate_zero_returns_empty():
    """N=0 için boş liste dönmeli."""
    assert allocate_cohort_matrix(0) == []


def test_allocate_returns_correct_count():
    """Döndürülen lista uzunluğu N'e eşit olmalı."""
    for n in [3, 5, 10, 15]:
        assert len(allocate_cohort_matrix(n)) == n
