"""GRUP 7 — A/B Varyant Testi (Kör + Randomize) testleri.

Korunan değer: Bilimsel geçerlilik. Sıra yanlılığı (order bias) engelleniyor;
deterministik seed sayesinde tekrarlanabilir.
"""
from __future__ import annotations

from packages.research_engine.tests.helpers import make_brief
from packages.research_engine.workflow import (
    _format_ab_question,
    generate_interview_script,
)


def _ab_brief():
    return make_brief(
        variant_a="Klasik defter takibi",
        variant_b="Yapay zeka destekli uygulama",
    )


def test_7_1_same_persona_index_produces_same_order():
    """Aynı persona index'i her zaman aynı sırayı üretmeli (deterministik)."""
    brief = _ab_brief()

    first = _format_ab_question(brief, 3)
    second = _format_ab_question(brief, 3)

    assert first == second


def test_7_2_labels_are_neutral():
    """Çıktıda Seçenek 1/2 kullanılmalı; Varyant A/B ifşası olmamalı."""
    text, _mapping = _format_ab_question(_ab_brief(), 1)

    assert "Seçenek 1" in text
    assert "Seçenek 2" in text
    assert "Varyant A" not in text
    assert "Varyant B" not in text


def test_7_3_order_distribution_is_balanced():
    """100 persona index'i için sıra dağılımı ~%50/50 olmalı (order bias yok)."""
    brief = _ab_brief()
    a_as_1 = 0

    for index in range(100):
        _text, mapping = _format_ab_question(brief, index)
        if mapping == "AB_MAP:A_AS_1":
            a_as_1 += 1

    ratio = a_as_1 / 100
    assert 0.35 <= ratio <= 0.65, f"A-önce oranı dengeli değil: {ratio}"


def test_7_4_mapping_note_is_produced():
    """Her çağrı geçerli bir AB_MAP notu üretmeli (sentez için gerekli)."""
    for index in range(10):
        _text, mapping = _format_ab_question(_ab_brief(), index)
        assert mapping in {"AB_MAP:A_AS_1", "AB_MAP:A_AS_2"}


def test_7_5_variants_appear_in_question_text():
    """Her iki varyantın metni de soruya gömülmeli."""
    brief = _ab_brief()
    text, _mapping = _format_ab_question(brief, 0)

    assert brief.variant_a in text
    assert brief.variant_b in text


def test_7_6_no_ab_question_when_variants_absent(monkeypatch):
    """Varyant tanımlı değilse planda AB_TEST sorusu bulunmamalı."""
    import packages.research_engine.db_vectors as db_vectors

    # DB'siz çalışmak için soru havuzunu boş döndür → fallback script kullanılır
    monkeypatch.setattr(db_vectors, "get_question_collection", lambda: [], raising=True)

    brief = make_brief()  # variant_a / variant_b yok
    labels = [q.label for q in generate_interview_script(brief)]

    assert "AB_TEST" not in labels


def test_7_7_ab_question_is_added_when_variants_present(monkeypatch):
    """Varyantlar tanımlıysa script'e AB_TEST sorusu eklenmeli."""
    import packages.research_engine.db_vectors as db_vectors

    monkeypatch.setattr(db_vectors, "get_question_collection", lambda: [], raising=True)

    brief = _ab_brief()
    labels = [q.label for q in generate_interview_script(brief)]

    assert "AB_TEST" in labels
