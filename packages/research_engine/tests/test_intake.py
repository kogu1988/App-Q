"""
Test: packages/research_engine/intake.py
Kapsam: reframe_user_input() — T1.1 test vakalarının tamamı
"""
import pytest
from packages.research_engine.intake import reframe_user_input


class TestReframeUserInput:
    """T1.1 — Input Reframing Layer (ELEPHANT Çerçevesi, arXiv:2602.23971)"""

    # ── Happy Path ────────────────────────────────────────────────────────────

    def test_T1_1_1_satis_garantisi_reframe_edilir(self):
        """Yüksek kesinlik — 'kesinlikle satacak' ifadesi reframe edilmeli."""
        result, was_reframed = reframe_user_input("Bu urun kesinlikle cok satacak")
        assert was_reframed is True, "Kesinlik ifadesi reframe edilmeli"
        assert result != "Bu urun kesinlikle cok satacak", "Metin değişmeli"
        assert len(result) > 10, "Reframe sonucu boş olmamalı"

    def test_T1_1_2_herkes_ifadesi_reframe_edilir(self):
        """'Herkes bu uygulamayı sevecek' → itiraz sorusu."""
        result, was_reframed = reframe_user_input("Herkes bu uygulamayi sevecek")
        assert was_reframed is True
        assert len(result) > 5

    def test_T1_1_3_onay_arayan_soru_eki(self):
        """'iyi değil mi?' kalıbı reframe edilmeli (Türkçe karakter ile)."""
        result, was_reframed = reframe_user_input("Bu tasarım iyi değil mi?")
        assert was_reframed is True, f"'iyi değil mi?' kalıbı reframe edilmeli, sonuç: {was_reframed}"

    def test_T1_1_7_turkce_karakter_kesinlik(self):
        """Türkçe karakter içeren kesinlik ifadesi."""
        result, was_reframed = reframe_user_input("Urunumuz mutlaka begenilecek")
        assert was_reframed is True

    # ── Edge Cases ────────────────────────────────────────────────────────────

    def test_T1_1_4_notr_ifade_dokunulmaz(self):
        """Nötr araştırma sorusu reframe edilmemeli."""
        text = "Fiyatlandirma nasil olmali?"
        result, was_reframed = reframe_user_input(text)
        assert was_reframed is False, "Nötr ifade reframe edilmemeli"
        assert result == text, "Metin değişmemeli"

    def test_T1_1_5_bos_string_crash_yapmaz(self):
        """Boş string crash yapmamalı, (str, bool) dönmeli."""
        result, was_reframed = reframe_user_input("")
        assert isinstance(result, str)
        assert isinstance(was_reframed, bool)
        assert was_reframed is False

    def test_T1_1_6_tek_kelime_stabil(self):
        """Tek kelime girdi — crash yapmamalı."""
        result, was_reframed = reframe_user_input("test")
        assert isinstance(result, str)
        assert isinstance(was_reframed, bool)

    def test_T1_1_doğru_tip_doner(self):
        """Her zaman (str, bool) tuple dönmeli."""
        for text in ["Bir fikir var", "", "kesinlikle iyi", "doğru mu?"]:
            result, flag = reframe_user_input(text)
            assert isinstance(result, str), f"str bekleniyor, {type(result)} geldi"
            assert isinstance(flag, bool), f"bool bekleniyor, {type(flag)} geldi"
