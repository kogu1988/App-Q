"""GRUP 6 — Adaptive Probe Engine testleri.

Korunan değer: Mülakat derinliği. Jenerik "neden?" sorularına dönülürse Arkanıt
arayan takip sorusu avantajı kaybolur.
"""
from __future__ import annotations

import pathlib

from packages.research_engine.nodes.probe import (
    PROBE_TEMPLATES,
    generate_probe_question,
    jaccard_similarity,
    should_probe,
)

# Somut TL içeren, fiyat sinyali taşıyan uzun cevap
ANSWER_WITH_TL = "Bu ürün için ayda 150 TL ödemeyi düşünebilirim, bütçeme uygun olur"
# Fiyattan söz eden ama rakam vermeyen cevap
ANSWER_VAGUE_PRICING = "Bu ürün bana gerçekten çok pahalı geldi, bütçemi oldukça aşıyor"
# Ne fiyat ne itiraz sinyali içeren doyurucu cevap.
# NOT: "kayıtları" bilinçli kullanılıyor — içinde "tl" alt-dizisi geçer ve
# probe heuristiğinin bu tür yanlış pozitifleri artık üretmemesi gerekir (O-1).
ANSWER_SUBSTANTIVE = (
    "Geçen hafta veteriner kayıtlarını deftere elle yazdım ve bu beni oldukça "
    "yordu, her defasında yeniden düzenlemek zorunda kaldım."
)


def test_6_1_short_answer_triggers_probe():
    """Çok kısa cevap probe tetiklemeli."""
    assert should_probe("Evet.", "VALUE") is True


def test_6_2_pricing_without_amount_triggers_probe():
    """Fiyat kelimesi var ama somut TL tutarı yoksa probe tetiklenmeli."""
    assert should_probe(ANSWER_VAGUE_PRICING, "PRICING") is True


def test_6_3_answer_with_concrete_tl_does_not_trigger_probe():
    """Somut TL tutarı içeren cevap probe tetiklememeli."""
    assert should_probe(ANSWER_WITH_TL, "PRICING") is False


def test_6_4_substantive_answer_does_not_trigger_probe():
    """Somut detaylı, doyurucu cevap probe tetiklememeli."""
    assert should_probe(ANSWER_SUBSTANTIVE, "PAIN") is False


def test_6_5_probe_question_is_evidence_seeking_not_generic():
    """Probe sorusu jenerik 'neden?' değil; kategoriye özel kanıt arayan kalıplardan gelmeli."""
    question = generate_probe_question(ANSWER_VAGUE_PRICING, "Fiyat sorusu?", "Mainstream")

    assert question in PROBE_TEMPLATES["pricing"], "fiyat sinyali fiyat şablonunu seçmeli"
    assert question not in PROBE_TEMPLATES["generic"], "jenerik şablon kullanılmamalı"
    assert question.strip().lower() != "neden?"
    assert question.strip().endswith("?"), "probe bir soru olmalı"


def test_6_6_jaccard_guard_detects_duplicate_answers():
    """Jaccard benzerliği aynı metinde 1.0 olmalı; eşik 0.7 üzeri tekrar sayılır."""
    text = "Bu ürün için ödeme yapmak istemiyorum çünkü güvenmiyorum"

    assert jaccard_similarity(text, text) == 1.0
    assert jaccard_similarity("a b c", "d e f") == 0.0
    almost_same = "Bu ürün için ödeme yapmak istemiyorum çünkü güvenmiyorum."
    assert jaccard_similarity(text, almost_same) > 0.7


def test_6_7_template_selection_is_label_driven():
    """Fiyat içeren cevap fiyat şablonundan, itiraz içeren cevap itiraz şablonundan seçilmeli."""
    pricing = generate_probe_question(ANSWER_VAGUE_PRICING, "Soru?", "Mainstream")
    objection = generate_probe_question(
        "Bu ürüne güvenmiyorum, emin değilim açıkçası ve riskli görünüyor bana", "Soru?", "Skeptic"
    )

    assert pricing in PROBE_TEMPLATES["pricing"]
    assert objection in PROBE_TEMPLATES["objection"]


def test_6_8_probe_limit_is_capped_at_three():
    """Mülakat başına probe sayısı 3 ile sınırlı olmalı (kaynak kontrolü)."""
    source = pathlib.Path("packages/research_engine/workflow.py").read_text(encoding="utf-8")

    assert source.count("total_probes < 3") >= 2, "probe limiti (3) mülakat akışlarında uygulanmalı"
    assert "is_probe=True" in source


def test_6_9_standalone_tl_triggers_pricing_probe():
    """Rakamsız ama açıkça 'TL' geçen cevap fiyat sinyali sayılmalı (kelime sınırı eşleşmesi)."""
    answer = "Bu işi TL üzerinden hesaplıyorum ama net bir aralık yok kafamda şu an, bakacağım"
    assert should_probe(answer, "PRICING") is True


def test_6_10_tl_substring_does_not_false_positive():
    """O-1 regresyonu: 'tl' alt-dizisi içeren kelimeler (kayıtları) fiyat sinyali sayılmamalı."""
    answer = (
        "Geçen hafta veteriner kayıtlarını deftere yazdım, çok yorucu ve düzensizdi"
    )
    assert should_probe(answer, "PAIN") is False
