"""
Test: EWMA Echo Protokolü (god_doc.md §5)

Kapsam:
  - detect_echo() Jaccard yankılanma tespiti
  - calculate_ewma() formül doğrulaması
  - calculate_turn_quality() echo_detected penaltısı
  - echo_drift_audit() adversarial pipeline entegrasyonu
  - run_interviews() EWMA entegrasyonu (non-stream)
"""
from __future__ import annotations
from unittest.mock import MagicMock, patch

from packages.research_engine.quality import (
    detect_echo,
    calculate_ewma,
    calculate_turn_quality,
)
from packages.research_engine.adversarial import (
    echo_drift_audit,
    EWMA_DRIFT_THRESHOLD,
    ECHO_PERSONA_RATIO,
)


# ── detect_echo Testleri ──────────────────────────────────────────────────────

def test_echo_detected_high_overlap():
    """Soru ile yüksek token örtüşmeli yanıt → echo tespit edilmeli."""
    # ASCII-safe kelimeler — Windows encoding sorununu önler
    question = "urun fiyat kalite begendin mi satin alir misin"
    answer = "urun fiyat kalite begendim satin alirim tabiki"
    assert detect_echo(answer, question) is True


def test_echo_not_detected_original_answer():
    """Bağımsız, orijinal cevap → echo tespit edilmemeli."""
    question = "Bu ürünü pahalı buluyor musun?"
    answer = "Bakın kaparo verdim dükkan sahibi yarın teslim edecek bana, umarım kaliteli çıkar."
    assert detect_echo(answer, question) is False


def test_echo_empty_answer():
    """Boş cevap → echo tespit edilmemeli (çökmemeli)."""
    assert detect_echo("", "Herhangi bir soru?") is False


def test_echo_empty_question():
    """Boş soru → echo tespit edilmemeli (çökmemeli)."""
    assert detect_echo("Herhangi bir cevap.", "") is False


def test_echo_returns_bool():
    """detect_echo her zaman bool döndürmeli."""
    result = detect_echo("cevap metni", "soru metni")
    assert isinstance(result, bool)


def test_echo_threshold_custom():
    """Özel eşik değeri ile tespit doğru çalışmalı."""
    question = "ürün fiyat kalite"
    answer = "ürün fiyat kalite değerlendiriyorum"
    # Düşük eşikte echo var
    assert detect_echo(answer, question, threshold=0.30) is True
    # Yüksek eşikte echo yok
    assert detect_echo(answer, question, threshold=0.99) is False


def test_echo_stop_words_filtered():
    """Stop word'ler filtrelenmeli — sadece stop word içeren cevap echo sayılmamalı."""
    question = "bu bir sorudur ve bu çok önemlidir"
    answer = "bu ve bir de da ile"
    # Stop wordler çıkarıldıktan sonra gerçek token kalmıyor → echo yok
    assert detect_echo(answer, question) is False


# ── calculate_ewma Testleri ───────────────────────────────────────────────────

def test_ewma_formula():
    """god_doc.md §5 formülü: α·S_t + (1-α)·EWMA_{t-1}"""
    alpha = 0.3
    current = 0.8
    previous = 1.0
    expected = alpha * current + (1 - alpha) * previous  # = 0.24 + 0.70 = 0.94
    result = calculate_ewma(current, previous, alpha)
    assert abs(result - expected) < 1e-9


def test_ewma_perfect_score():
    """Mükemmel tur (1.0) ile önceki 1.0 → EWMA 1.0 kalmalı."""
    result = calculate_ewma(1.0, 1.0)
    assert abs(result - 1.0) < 1e-9


def test_ewma_zero_score():
    """Sıfır kaliteli tur → EWMA düşmeli."""
    result = calculate_ewma(0.0, 1.0, alpha=0.3)
    assert result < 1.0
    assert result == 0.7  # (1-0.3) * 1.0


def test_ewma_converges():
    """Sürekli düşük skorla EWMA belirli eşiğin altına inmeli."""
    ewma = 1.0
    for _ in range(20):
        ewma = calculate_ewma(0.0, ewma)
    assert ewma < EWMA_DRIFT_THRESHOLD


# ── calculate_turn_quality echo_detected Testleri ────────────────────────────

def test_turn_quality_echo_penalized():
    """echo_detected flag'i 0.4 puan düşürmeli."""
    assert abs(calculate_turn_quality(["echo_detected"]) - 0.6) < 1e-9


def test_turn_quality_echo_plus_meta_tone():
    """echo + meta_tone → max(0, 1.0 - 0.4 - 0.5) = 0.1"""
    result = calculate_turn_quality(["echo_detected", "meta_tone"])
    assert abs(result - 0.1) < 1e-9


def test_turn_quality_no_flags():
    """Flag yoksa kalite 1.0 olmalı."""
    assert calculate_turn_quality([]) == 1.0


def test_turn_quality_never_negative():
    """Kalite skoru asla negatif olmamalı."""
    result = calculate_turn_quality(["echo_detected", "meta_tone", "visible_reasoning", "too_short"])
    assert result >= 0.0


# ── echo_drift_audit Testleri ────────────────────────────────────────────────

def _make_iv(persona_name: str, ewma_notes: list[str], echo_count: int, total_turns: int):
    """Test için sahte PersonaInterview nesnesi."""
    iv = MagicMock()
    iv.persona.name = persona_name
    iv.consistency_notes = ewma_notes
    turns = []
    for i in range(total_turns):
        t = MagicMock()
        t.quality_flags = ["echo_detected"] if i < echo_count else []
        turns.append(t)
    iv.turns = turns
    return iv


def test_echo_drift_no_drift():
    """Yüksek EWMA, düşük echo → flag yok."""
    iv = _make_iv("Ahmet", ["Turn 1 EWMA: 0.95", "Turn 2 EWMA: 0.90"], 0, 4)
    flags = echo_drift_audit({"interviews": [iv]})
    assert len(flags) == 0


def test_echo_drift_low_ewma_warns():
    """EWMA eşiğin altında → PERSONA_DRIFT_DETECTED uyarısı."""
    iv = _make_iv("Ayşe", ["Turn 1 EWMA: 0.90", "Turn 2 EWMA: 0.60"], 0, 4)
    flags = echo_drift_audit({"interviews": [iv]})
    codes = [f["code"] for f in flags]
    assert "PERSONA_DRIFT_DETECTED" in codes


def test_echo_drift_high_echo_ratio_warns():
    """Echo oranı ≥ 0.5 → HIGH_ECHO_RATIO uyarısı."""
    iv = _make_iv("Mehmet", ["Turn 1 EWMA: 0.95"], 3, 4)  # 3/4 = 0.75
    flags = echo_drift_audit({"interviews": [iv]})
    codes = [f["code"] for f in flags]
    assert "HIGH_ECHO_RATIO" in codes


def test_echo_drift_empty_interviews():
    """Mülakat yoksa flag yok, exception yok."""
    flags = echo_drift_audit({"interviews": []})
    assert flags == []


def test_echo_drift_flag_severity():
    """Tüm echo/drift flag'leri 'warning' severity olmalı."""
    iv = _make_iv("Test", ["Turn 1 EWMA: 0.50"], 4, 4)
    flags = echo_drift_audit({"interviews": [iv]})
    for flag in flags:
        assert flag["severity"] == "warning"


def test_echo_drift_phase_label():
    """Tüm flag'lerin phase değeri 'echo_drift' olmalı."""
    iv = _make_iv("Test", ["Turn 1 EWMA: 0.50"], 4, 4)
    flags = echo_drift_audit({"interviews": [iv]})
    for flag in flags:
        assert flag["phase"] == "echo_drift"


def test_ewma_drift_threshold_value():
    """EWMA eşiği 0.65 olmalı (god_doc.md §5 uyumlu)."""
    assert EWMA_DRIFT_THRESHOLD == 0.65


def test_echo_persona_ratio_value():
    """Echo oran eşiği 0.5 olmalı."""
    assert ECHO_PERSONA_RATIO == 0.5
