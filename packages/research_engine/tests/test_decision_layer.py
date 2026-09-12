"""GRUP 2 — Decision Layer (Karar Katmanı) regresyon testleri.

Korunan değer: "Karar zekası" konumlandırmasının somut çıktısı. Eşikler kayarsa
yanlış iş kararı önerilir — müşteri güveni doğrudan zarar görür.

Eşik tablosu (build_evidence_graph içinde uygulanır):
    total == 0                                  → INVESTIGATE
    supporting >= %70 ve refuting == 0          → SHIP
    supporting > refuting ve contradiction < .5 → ITERATE
    contradiction >= 0.5                        → INVESTIGATE
    refuting > supporting                       → KILL
"""
from __future__ import annotations

from packages.research_engine.analytics import (
    build_evidence_graph,
    generate_decision_summary,
)
from packages.research_engine.tests.helpers import (
    make_finding,
    make_interview,
    make_persona,
    turn,
)

SUPPORTING_QUOTE = "harika ve faydalı"
REFUTING_QUOTE = "pahalı ve gereksiz"
VALID_SIGNALS = {"SHIP", "ITERATE", "INVESTIGATE", "KILL"}


def _enhanced(supporting: int, refuting: int, category: str = "pricing"):
    """İstenen duygu dağılımını üreten tek EnhancedFinding döner."""
    interviews = []
    idx = 0
    for answer, count in ((SUPPORTING_QUOTE, supporting), (REFUTING_QUOTE, refuting)):
        for _ in range(count):
            idx += 1
            persona = make_persona(pid=f"p{idx}", name=f"P{idx}")
            interviews.append(
                make_interview(persona, [turn("Fiyat sorusu?", answer, [category])])
            )

    return build_evidence_graph(interviews, [make_finding(category=category)])[0]


# ── 2.1–2.4 Karar sinyali eşikleri ──

def test_2_1_full_support_is_ship():
    """Yüksek destek + sıfır itiraz → SHIP."""
    assert _enhanced(5, 0).decision_signal == "SHIP"


def test_2_2_majority_support_low_contradiction_is_iterate():
    """Destek > itiraz ve düşük çelişki → ITERATE."""
    assert _enhanced(4, 1).decision_signal == "ITERATE"


def test_2_3_high_contradiction_is_investigate():
    """Yüksek çelişki (3-3 bölünme) → INVESTIGATE."""
    assert _enhanced(3, 3).decision_signal == "INVESTIGATE"


def test_2_4_majority_refuting_is_kill():
    """İtiraz > destek → KILL."""
    assert _enhanced(1, 4).decision_signal == "KILL"


# ── 2.5–2.9 Karar özeti ──

def test_2_5_one_decision_item_per_finding():
    """Her geliştirilmiş bulgu için bir DecisionItem üretilmeli."""
    enhanced = [_enhanced(5, 0), _enhanced(1, 4, category="value")]
    assert len(generate_decision_summary(enhanced)) == len(enhanced)


def test_2_6_every_signal_has_turkish_action_text():
    """Dört sinyalin hepsinde boş olmayan Türkçe aksiyon metni olmalı."""
    enhanced = [
        _enhanced(5, 0),            # SHIP
        _enhanced(4, 1),            # ITERATE
        _enhanced(3, 3),            # INVESTIGATE
        _enhanced(1, 4),            # KILL
    ]
    items = generate_decision_summary(enhanced)

    assert {i.signal for i in items} == VALID_SIGNALS
    for item in items:
        assert item.recommended_action.strip()
        assert item.evidence_summary.strip()


def test_2_7_kill_action_mentions_refuting_count():
    """KILL aksiyon metni itiraz sayısını içermeli."""
    kill = _enhanced(1, 4)
    item = generate_decision_summary([kill])[0]

    assert item.signal == "KILL"
    assert str(kill.refuting_count) in item.recommended_action


def test_2_8_signals_stay_within_enum():
    """Üretilen tüm sinyaller {SHIP, ITERATE, INVESTIGATE, KILL} içinde olmalı."""
    enhanced = [_enhanced(s, r) for s, r in [(5, 0), (4, 1), (3, 3), (1, 4)]]
    items = generate_decision_summary(enhanced)

    for item in items:
        assert item.signal in VALID_SIGNALS


def test_2_9_empty_list_is_safe():
    """Boş liste → boş liste (exception yok)."""
    assert generate_decision_summary([]) == []
