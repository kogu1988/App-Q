"""GRUP 1 — Evidence Chain (Kanıt Zinciri) regresyon testleri.

Korunan değer: Ürünün en büyük farklılaştırıcısı. Her bulgu persona → soru → alıntı →
destek/karşı zinciriyle bağlı. Bozulursa rapor "AI'ın uydurduğu metin" seviyesine düşer.

Not: `classify_evidence_sentiment` keyword tabanlıdır — Türkçe keyword seti değişirse
bu testler de güncellenmelidir (kasıtlı sıkı bağ).
"""
from __future__ import annotations

from packages.research_engine.analytics import (
    build_evidence_graph,
    classify_evidence_sentiment,
)
from packages.research_engine.models import EnhancedFinding
from packages.research_engine.tests.helpers import (
    make_finding,
    make_interview,
    make_persona,
    turn,
)

SUPPORTING_QUOTE = "harika ve faydalı"
REFUTING_QUOTE = "pahalı ve gereksiz"
NEUTRAL_QUOTE = "emin değilim"


def _interviews(supporting: int, refuting: int, neutral: int = 0, category: str = "pricing"):
    """Belirtilen duygu dağılımıyla mülakat listesi üretir."""
    interviews = []
    idx = 0
    for answer, count in (
        (SUPPORTING_QUOTE, supporting),
        (REFUTING_QUOTE, refuting),
        (NEUTRAL_QUOTE, neutral),
    ):
        for _ in range(count):
            idx += 1
            persona = make_persona(pid=f"p{idx}", name=f"P{idx}")
            interviews.append(
                make_interview(persona, [turn("Fiyat sorusu?", answer, [category])])
            )
    return interviews


# ── 1.1–1.3 Duygu sınıflandırma ──

def test_1_1_supporting_statement_is_detected():
    """Destekleyici ifade 'supporting' olarak sınıflanmalı."""
    assert classify_evidence_sentiment("harika, kesinlikle alırım", "fiyat") == "supporting"


def test_1_2_refuting_statement_is_detected():
    """Karşıt ifade 'refuting' olarak sınıflanmalı."""
    assert classify_evidence_sentiment("çok pahalı, güvenmiyorum", "fiyat") == "refuting"


def test_1_3_neutral_and_invalid_input_is_safe():
    """Boş/None/sayı girdiler 'neutral' döner, exception fırlatmaz."""
    assert classify_evidence_sentiment("", "fiyat") == "neutral"
    assert classify_evidence_sentiment(None, "fiyat") == "neutral"  # type: ignore[arg-type]
    assert classify_evidence_sentiment(123, "fiyat") == "neutral"  # type: ignore[arg-type]
    assert classify_evidence_sentiment(NEUTRAL_QUOTE, "fiyat") == "neutral"


# ── 1.4–1.10 Kanıt grafiği ──

def test_1_4_returns_enhanced_finding_per_input_finding():
    """Her bulgu için bir EnhancedFinding döner."""
    findings = [make_finding(title="A"), make_finding(title="B", category="value")]
    out = build_evidence_graph(_interviews(2, 1), findings)

    assert len(out) == len(findings)
    assert all(isinstance(f, EnhancedFinding) for f in out)


def test_1_5_sentiment_counts_sum_to_evidence_count():
    """Destek + karşı + nötr toplamı kanıt sayısına eşit olmalı."""
    findings = [make_finding()]
    out = build_evidence_graph(_interviews(3, 2, 1), findings)
    finding = out[0]

    assert finding.supporting_count + finding.refuting_count + finding.neutral_count == len(finding.evidence)


def test_1_6_contradiction_score_within_bounds():
    """Çelişki skoru her senaryoda 0..1 aralığında olmalı."""
    for supporting, refuting in [(5, 0), (0, 5), (3, 3), (1, 0), (0, 0)]:
        out = build_evidence_graph(_interviews(supporting, refuting), [make_finding()])
        score = out[0].contradiction_score
        assert 0.0 <= score <= 1.0, f"s={supporting}, r={refuting} → {score}"


def test_1_7_full_consensus_has_zero_contradiction():
    """Tam konsensüs (5 destek, 0 karşı) → çelişki 0."""
    out = build_evidence_graph(_interviews(5, 0), [make_finding()])
    assert out[0].contradiction_score == 0.0


def test_1_8_even_split_has_high_contradiction():
    """Tam bölünme (3 destek, 3 karşı) → çelişki >= 0.9."""
    out = build_evidence_graph(_interviews(3, 3), [make_finding()])
    assert out[0].contradiction_score >= 0.9


def test_1_9_empty_interviews_does_not_crash():
    """Boş mülakat listesi çökmemeli; kanıtsız bulgu üretilmeli."""
    out = build_evidence_graph([], [make_finding()])

    assert len(out) == 1
    assert out[0].evidence == []
    assert out[0].contradiction_score == 0.0


def test_1_10_evidence_preserves_persona_identity():
    """Her kanıt kaydı gerçek bir personaya bağlı olmalı."""
    interviews = _interviews(2, 0)
    expected_ids = {i.persona.id for i in interviews}

    out = build_evidence_graph(interviews, [make_finding()])
    for evidence in out[0].evidence:
        assert evidence.persona_id in expected_ids
        assert evidence.persona_name
        assert evidence.quote
        assert evidence.source_question
