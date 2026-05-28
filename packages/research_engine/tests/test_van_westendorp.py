"""
Test: Van Westendorp PSM — Bilimsel kesişim hesabı doğrulaması

PSM metodolojisi (god_doc.md §8):
  PMC = "Çok Ucuz %" = "Pahalı %" kesişimi
  PME = "Ucuz %"     = "Çok Pahalı %" kesişimi
  OPP = "Çok Ucuz %" = "Çok Pahalı %" kesişimi
  IPP = "Ucuz %"     = "Pahalı %" kesişimi

Sıralama koşulu: PMC ≤ OPP ≤ PME
"""
from __future__ import annotations
from dataclasses import dataclass, field
from unittest.mock import MagicMock

from packages.research_engine.analytics import (
    _cumulative_freq,
    _find_intersection,
    van_westendorp_analysis,
)
from packages.research_engine.workflow import classify_question


# ── Yardımcılar ──────────────────────────────────────────────────────────────

def _make_persona(price_sensitivity: int = 5) -> MagicMock:
    p = MagicMock()
    p.price_sensitivity = price_sensitivity
    p.ses = "B"
    return p


def _make_interview(persona, pricing_answers: list[str], non_pricing: list[str] | None = None):
    """Test için sahte PersonaInterview oluşturur."""
    iv = MagicMock()
    iv.persona = persona
    turns = []
    for ans in pricing_answers:
        t = MagicMock()
        t.answer = ans
        t.tags = ["pricing"]
        turns.append(t)
    for ans in (non_pricing or []):
        t = MagicMock()
        t.answer = ans
        t.tags = ["pain_point"]
        turns.append(t)
    iv.turns = turns
    return iv


def _make_brief(expected_price: str | None = "500 TL") -> MagicMock:
    b = MagicMock()
    b.expected_price = expected_price
    b.title = "Test Ürünü"
    return b


# ── _cumulative_freq Testleri ────────────────────────────────────────────────

def test_cumulative_freq_monotonic():
    """Kümülatif frekans her zaman artan (0 → 100) olmalı."""
    values = [100.0, 200.0, 300.0, 400.0, 500.0]
    prices = [50.0, 150.0, 250.0, 350.0, 450.0, 550.0]
    freq = _cumulative_freq(values, prices)
    for i in range(len(freq) - 1):
        assert freq[i] <= freq[i + 1], f"Monotonluk bozuldu: {freq[i]} > {freq[i+1]}"


def test_cumulative_freq_empty_values():
    """Boş liste → tüm sıfırlar."""
    freq = _cumulative_freq([], [100.0, 200.0, 300.0])
    assert freq == [0.0, 0.0, 0.0]


def test_cumulative_freq_range():
    """Frekans 0-100 aralığında olmalı."""
    values = [200.0, 400.0, 600.0]
    prices = [100.0, 300.0, 500.0, 700.0]
    freq = _cumulative_freq(values, prices)
    for f in freq:
        assert 0.0 <= f <= 100.0


def test_cumulative_freq_all_above():
    """Tüm değerler fiyat ekseninin üstündeyse → hep 0."""
    values = [1000.0, 2000.0]
    prices = [100.0, 200.0, 300.0]
    freq = _cumulative_freq(values, prices)
    assert all(f == 0.0 for f in freq)


def test_cumulative_freq_all_below():
    """Tüm değerler fiyat ekseninin altındaysa → hep 100."""
    values = [10.0, 20.0]
    prices = [100.0, 200.0, 300.0]
    freq = _cumulative_freq(values, prices)
    assert all(f == 100.0 for f in freq)


# ── _find_intersection Testleri ──────────────────────────────────────────────

def test_find_intersection_simple():
    """Bilinen iki doğrunun kesişimi 50 olmalı."""
    prices = [0.0, 25.0, 50.0, 75.0, 100.0]
    freq_a = [0.0, 25.0, 50.0, 75.0, 100.0]   # artan
    freq_b = [100.0, 75.0, 50.0, 25.0, 0.0]   # azalan
    result = _find_intersection(freq_a, freq_b, prices)
    assert abs(result - 50.0) < 5.0, f"Kesişim 50 bekleniyordu, {result} geldi"


def test_find_intersection_no_cross_returns_median():
    """Kesişim yoksa medyan döner, exception fırlatmaz."""
    prices = [100.0, 200.0, 300.0]
    freq_a = [10.0, 20.0, 30.0]  # hep altta
    freq_b = [50.0, 60.0, 70.0]  # hep üstte
    result = _find_intersection(freq_a, freq_b, prices)
    assert result in prices or (100.0 <= result <= 300.0)


def test_find_intersection_returns_float():
    """Sonuç her zaman float/int olmalı, exception fırlatmamalı."""
    prices = [100.0, 200.0, 300.0, 400.0]
    freq_a = [10.0, 30.0, 60.0, 90.0]
    freq_b = [90.0, 60.0, 30.0, 10.0]
    result = _find_intersection(freq_a, freq_b, prices)
    assert isinstance(result, (int, float))


# ── van_westendorp_analysis Testleri ────────────────────────────────────────

def test_van_westendorp_no_interviews_returns_none():
    """Mülakat yoksa None dönmeli."""
    brief = _make_brief()
    result = van_westendorp_analysis(brief, [])
    assert result is None


def test_van_westendorp_returns_insight():
    """Geçerli mülakatlarla VanWestendorpInsight dönmeli."""
    persona = _make_persona(price_sensitivity=5)
    iv = _make_interview(
        persona,
        pricing_answers=["100 TL ucuz, 500 TL pahalı, 800 TL çok pahalı, 50 TL çok ucuz"],
    )
    brief = _make_brief("300 TL")
    result = van_westendorp_analysis(brief, [iv])
    assert result is not None


def test_van_westendorp_pmc_lte_opp_lte_pme():
    """PMC ≤ OPP ≤ PME sıralaması korunmalı (god_doc.md §8 zorunluluğu)."""
    persona = _make_persona(price_sensitivity=5)
    interviews = [
        _make_interview(persona, ["150 TL ucuz, 400 TL pahalı, 700 TL çok pahalı, 80 TL çok ucuz"]),
        _make_interview(persona, ["200 TL ucuz, 450 TL pahalı, 750 TL çok pahalı, 100 TL çok ucuz"]),
        _make_interview(_make_persona(3), ["300 TL ucuz, 600 TL pahalı, 900 TL çok pahalı, 150 TL çok ucuz"]),
    ]
    brief = _make_brief("400 TL")
    result = van_westendorp_analysis(brief, interviews)
    assert result is not None
    assert result.pmc <= result.opp, f"PMC ({result.pmc}) > OPP ({result.opp})"
    assert result.opp <= result.pme, f"OPP ({result.opp}) > PME ({result.pme})"


def test_van_westendorp_acceptable_range_matches():
    """acceptable_range == (pmc, pme) olmalı."""
    persona = _make_persona(5)
    iv = _make_interview(persona, ["200 TL ucuz, 500 TL pahalı, 800 TL çok pahalı, 100 TL çok ucuz"])
    brief = _make_brief("350 TL")
    result = van_westendorp_analysis(brief, [iv])
    if result:
        assert result.acceptable_range == (result.pmc, result.pme)


def test_van_westendorp_no_pricing_tags_uses_heuristic():
    """Pricing etiketi olmayan mülakatlar heuristik fallback kullanmalı, None dönmemeli."""
    persona = _make_persona(7)
    iv = _make_interview(persona, pricing_answers=[], non_pricing=["Ürünü beğendim"])
    brief = _make_brief("500 TL")
    result = van_westendorp_analysis(brief, [iv])
    # Heuristik devreye girmeli → None dönmemeli
    assert result is not None


def test_van_westendorp_currency_default():
    """Para birimi varsayılan olarak TL olmalı."""
    persona = _make_persona(5)
    iv = _make_interview(persona, ["300 TL ucuz, 600 TL pahalı"])
    brief = _make_brief()
    result = van_westendorp_analysis(brief, [iv])
    if result:
        assert result.currency == "TL"


# ── classify_question Pricing Keyword Testleri ──────────────────────────────

def test_classify_pricing_fiyat():
    assert "pricing" in classify_question("Bu ürün için hangi fiyat makul?")


def test_classify_pricing_ucuz():
    assert "pricing" in classify_question("Ne zaman ucuz buluyorsun?")


def test_classify_pricing_pahali():
    assert "pricing" in classify_question("Sence bu pahalı mı?")


def test_classify_pricing_tl():
    assert "pricing" in classify_question("500 TL öder misin?")


def test_classify_pricing_ne_kadar():
    assert "pricing" in classify_question("Ne kadar ödemek istersin?")


def test_classify_pricing_taksit():
    assert "pricing" in classify_question("Taksit seçeneği önemli mi?")


def test_classify_no_pricing_neutral():
    """Fiyatsız soru pricing etiketi almamalı."""
    tags = classify_question("Bu ürünü nasıl buluyorsun?")
    assert "pricing" not in tags


def test_classify_pain_point_extended():
    """Genişletilmiş pain_point keywordleri çalışmalı."""
    assert "pain_point" in classify_question("Bu konuda yaşadığın zorluk nedir?")
    assert "pain_point" in classify_question("Bunu çözmekte sorun yaşıyor musun?")
