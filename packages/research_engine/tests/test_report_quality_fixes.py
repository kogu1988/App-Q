"""Rapor kalitesi & karar katmanı düzeltmeleri (P1/P2) regresyon testleri.

Korunan değerler:
- Kanıt duygusu bulgunun İDDİASINA göre yorumlanmalı (pain_point'te olumsuz dil = destek).
- Bulgu kategorisi ile soru etiketi eşleşmeli (risk ↔ objection) — yoksa kanıt 0 kalır.
- Kişiler arası yankı (cross-persona echo) tespit edilmeli.
"""
from __future__ import annotations

from packages.research_engine.analytics import build_evidence_graph, classify_evidence_sentiment
from packages.research_engine.nodes.sycophancy import judge_answer_quality
from packages.research_engine.quality import detect_cross_persona_echo
from packages.research_engine.tests.helpers import (
    make_finding,
    make_interview,
    make_persona,
    turn,
)


# ── P1-2: Kategori-farkında duygu sınıflandırması ──

NEGATIVE = "Geçen ay aşıyı kaçırdım, her şey üç ayrı yerde dağınık, çok karmaşık ve zaman kaybı."
POSITIVE = "Bu harika ve çok faydalı bir çözüm, kesinlikle kullanırım, çok pratik."


def test_pain_point_negative_language_is_supporting():
    """Pain point bulgusunda acıyı anlatan (olumsuz) dil DESTEK kanıttır."""
    assert classify_evidence_sentiment(NEGATIVE, category="pain_point") == "supporting"


def test_pain_point_positive_language_is_refuting():
    """'Acı yok' diyen (olumlu) dil pain point iddiasına KARŞIdır."""
    assert classify_evidence_sentiment(POSITIVE, category="pain_point") == "refuting"


def test_risk_category_negative_language_is_supporting():
    """Risk/bariyer bulgusunda itiraz dili destektir."""
    assert classify_evidence_sentiment(NEGATIVE, category="risk") == "supporting"


def test_value_category_positive_language_is_supporting():
    """Değer bulgusunda olumlu dil destektir (mevcut davranış korunur)."""
    assert classify_evidence_sentiment(POSITIVE, category="value") == "supporting"


def test_default_category_keeps_legacy_behaviour():
    """Kategori verilmezse eski davranış korunmalı (geriye dönük uyum)."""
    assert classify_evidence_sentiment(POSITIVE) == "supporting"
    assert classify_evidence_sentiment(NEGATIVE) == "refuting"
    assert classify_evidence_sentiment("") == "neutral"


# ── P1-3: Bulgu kategorisi ↔ soru etiketi eşlemesi ──

def test_risk_finding_matches_objection_tagged_turns():
    """`risk` bulgusu, `objection` etiketli mülakat turlarıyla eşleşmeli."""
    persona = make_persona(pid="p1", name="Ahmet", stance="Skeptic")
    interview = make_interview(persona, [
        turn("Ürünü alır mıydın?", NEGATIVE, ["objection"]),
    ])
    finding = make_finding(title="Satın alma bariyerleri", category="risk")

    enhanced = build_evidence_graph([interview], [finding])

    assert len(enhanced) == 1
    ef = enhanced[0]
    assert len(ef.evidence) == 1, "objection etiketi risk bulgusuyla eşleşmeliydi"
    assert ef.supporting_count == 1, "itiraz dili risk bulgusunu DESTEKLEMELİ"
    assert ef.decision_signal != "KILL"


def test_pain_point_finding_no_longer_killed_by_negative_talk():
    """Pain point, acı anlatan yanıtlarla KILL değil destek almalı (ana regresyon)."""
    interviews = [
        make_interview(make_persona(pid=f"p{i}", name=f"P{i}"), [
            turn("Problemi nasıl yaşıyorsun?", NEGATIVE, ["pain_point"]),
        ])
        for i in range(3)
    ]
    finding = make_finding(title="Temel ihtiyaç ve acı noktası", category="pain_point")

    ef = build_evidence_graph(interviews, [finding])[0]

    assert ef.supporting_count == 3
    assert ef.refuting_count == 0
    assert ef.decision_signal in {"SHIP", "ITERATE"}


# ── P2-1: Cross-persona echo ──

def test_cross_persona_echo_detects_shared_invented_name():
    """Üç persona aynı uydurulmuş özel adı kullanıyorsa yankı olarak işaretlenmeli."""
    common = "Geçen ay kedim Pamuk'un aşısını kaçırdım, veteriner karnesi çekmecedeydi."
    interviews = [
        make_interview(make_persona(pid=f"p{i}", name=f"P{i}"), [
            turn("Problemi anlat", common, ["pain_point"]),
        ])
        for i in range(3)
    ]

    result = detect_cross_persona_echo(interviews)

    assert "Pamuk" in result["shared_tokens"]
    assert set(result["echoing_persona_ids"]) == {"p0", "p1", "p2"}


def test_cross_persona_echo_clean_when_distinct():
    """Farklı örnekler kullanan personalar yankı sayılmamalı."""
    interviews = [
        make_interview(make_persona(pid="p0", name="A"), [
            turn("Problemi anlat", "Köpeğim Boncuk'un aşı günlüğünü kaybettim, deftere yazıyordum.", ["pain_point"]),
        ]),
        make_interview(make_persona(pid="p1", name="B"), [
            turn("Problemi anlat", "Muhabbet kuşum Mavi için ilaç saatlerini telefon alarmıyla takip ediyorum.", ["pain_point"]),
        ]),
        make_interview(make_persona(pid="p2", name="C"), [
            turn("Problemi anlat", "İki kedimin karma aşı kartlarını buzdolabına mıknatısla asıyorum.", ["pain_point"]),
        ]),
    ]

    result = detect_cross_persona_echo(interviews)

    assert result["shared_tokens"] == []


# ── P2-2: Meta ton yanlış pozitifi ──

def test_product_ai_feature_mention_is_not_meta_tone():
    """Ürünün 'yapay zeka özelliği'nden bahsetmek meta ton SAYILMAMALI (yanlış pozitif)."""
    persona = make_persona()
    answer = (
        "Ürünün yapay zeka kısmı güzel pazarlama ama benim için olmazsa olmaz değil; "
        "önce basit ve çalışan bir hatırlatma sistemi olsun yeter."
    )
    flags = judge_answer_quality(persona, "En çok hangi özellik heyecanlandırır?", answer)
    assert "meta_tone" not in flags


def test_self_identification_still_flagged_as_meta_tone():
    """Kişi kendini yapay zeka/asistan olarak tanımlarsa meta ton yakalanmalı."""
    persona = make_persona()
    flags = judge_answer_quality(
        persona, "Sen kimsin?",
        "Ben bir yapay zekayım ve sana yardımcı olmak için buradayım, bu soruya cevap verebilirim.",
    )
    assert "meta_tone" in flags
