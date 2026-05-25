"""
Test: packages/research_engine/intake.py
Kapsam:
  - T1.1: reframe_user_input()
  - T1.5: Discovery Loop Guard ve Güvenlik Mekanizmaları
"""
import pytest
from packages.research_engine.intake import (
    reframe_user_input,
    calculate_jaccard_similarity,
    DiscoveryLoopGuard,
    process_intake_chat
)


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


class TestDiscoveryLoopGuard:
    """T1.5 — Discovery Loop Guard ve Güvenlik Mekanizmaları"""

    # ── Jaccard Similarity Tests ──────────────────────────────────────────────

    def test_calculate_jaccard_similarity_identical(self):
        """Aynı cümleler için benzerlik oranı 1.0 olmalı."""
        q1 = "Ücretlendirme modelini nasıl düşünüyorsunuz?"
        q2 = "Ücretlendirme modelini nasıl düşünüyorsunuz?"
        assert calculate_jaccard_similarity(q1, q2) == 1.0

    def test_calculate_jaccard_similarity_different(self):
        """Tamamen farklı cümleler için benzerlik oranı düşük olmalı."""
        q1 = "Ücretlendirme modelini nasıl düşünüyorsunuz?"
        q2 = "Araştırmaya kimleri dahil etmek istersiniz?"
        assert calculate_jaccard_similarity(q1, q2) < 0.3

    def test_calculate_jaccard_similarity_similar(self):
        """Küçük değişikliklerle tekrar edilen cümleler için benzerlik yüksek olmalı."""
        q1 = "Ücretlendirme modelini nasıl sunmayı planlıyorsunuz?"
        q2 = "Bu uygulamayı kullanıcılarımıza nasıl sunmayı planlıyorsunuz?"
        assert calculate_jaccard_similarity(q1, q2) > 0.35

    # ── Loop Detection Tests ──────────────────────────────────────────────────

    def test_loop_detection_triggers_context_shift(self):
        """Son sorulan soru ile yeni üretilen soru benzerse döngü kırılmalı ve sıradaki alana geçilmeli."""
        # 1. Diyalog geçmişi (Son asistan sorusu expected_price hakkında)
        chat_history = [
            {"role": "user", "content": "Merhaba"},
            {"role": "assistant", "content": "Evcil hayvan uygulaması için ücretlendirme modelini nasıl düşünüyorsunuz — ücretsiz deneme mi, abonelik mi?"},
            {"role": "user", "content": "aylık abonelik olacak ve reklamlı kısıtlı free sürüm de olacak."}
        ]
        
        # 2. Mevcut kısmi brief (idea, title ve target_users doldurulmuş, success_metric boş)
        current_brief = {
            "idea": "Evcil hayvan takip uygulaması",
            "title": "Evcil Hayvan Takip Araştırması",
            "target_users": ["Evcil hayvan sahipleri"],
            "expected_price": "aylık abonelik",
            "success_metric": None
        }
        
        # 3. Model yeni yanıtta aynı soruyu reword ederek tekrar üretiyor (Döngü hatası!)
        result = {
            "updated_brief": {
                "expected_price": "aylık abonelik"
            },
            "assistant_reply": "Harika bir fiyat modeli! Peki, bu uygulamayı kullanıcılarımıza nasıl sunmayı planlıyorsunuz — ücretsiz deneme süresiyle mi, aylık abonelik modeliyle mi, yoksa tek seferlik mi?"
        }
        
        class MockResearchModel:
            def generate(self, system, prompt):
                return type("MockResponse", (), {"text": "{}"})()
                
        # 4. Guard turn'ü denetler
        guard = DiscoveryLoopGuard(max_turns=10, loop_threshold=0.60)
        protected_result = guard.guard_turn(current_brief, chat_history, result, MockResearchModel())
        
        # 5. assistant_reply'ın override edildiğini ve sıradaki eksik alan olan success_metric (başarı kriteri) sorusunu sorduğunu doğrula!
        assert "başarıyı nasıl ölçeceğiz" in protected_result["assistant_reply"]
        assert "ücretsiz deneme" not in protected_result["assistant_reply"]

    # ── Turn Limit Tests ──────────────────────────────────────────────────────

    def test_turn_limit_triggers_force_extraction(self):
        """Turn sayısı 10'a ulaştığında veya aştığında, zorla brief çıkarımı (FORCE_EXTRACTION) yapılmalı."""
        # 1. 10 turluk uzun konuşma geçmişi (her turn 1 user ve 1 assistant mesajı içerir)
        chat_history = []
        for i in range(10):
            chat_history.append({"role": "user", "content": f"cevap {i}"})
            chat_history.append({"role": "assistant", "content": f"soru {i}?"})
            
        current_brief = {"idea": "Evcil hayvan aşısı takip uygulaması"}
        result = {
            "updated_brief": {},
            "assistant_reply": "Hâlâ sormam gereken birkaç soru var..."
        }
        
        # 2. Model mock extraction dönüşünü JSON döndürür
        mock_extracted_json = """
        {
            "title": "Evcil Hayvan Takip Araştırması",
            "market": "Türkiye",
            "idea": "Evcil hayvan aşısı takip uygulaması",
            "target_users": ["Evcil hayvan sahipleri"],
            "expected_price": "Aylık abonelik",
            "success_metric": "Kullanıcı memnuniyeti",
            "respondent_types": ["potential_customer"],
            "discovery_channels": ["sosyal medya"]
        }
        """
        
        class MockResearchModel:
            def generate(self, system, prompt):
                class MockResponse:
                    text = mock_extracted_json
                return MockResponse()
                
        # 3. Guard turn'ü denetler
        guard = DiscoveryLoopGuard(max_turns=10)
        protected_result = guard.guard_turn(current_brief, chat_history, result, MockResearchModel())
        
        # 4. Brief'in otomatik doldurulduğunu ve mülakat sonlandırma onayının verildiğini doğrula!
        assert protected_result["updated_brief"]["expected_price"] == "Aylık abonelik"
        assert protected_result["updated_brief"]["success_metric"] == "Kullanıcı memnuniyeti"
        assert "başlatmaya hazırız" in protected_result["assistant_reply"]
        assert "süreci tetikleyebilirsiniz" in protected_result["assistant_reply"]

    def test_competitor_loop_with_agglutinated_turkish_detected(self):
        """Son sorudaki 'kimleri eklemeyi düşünüyorsunuz' ile yeni sorudaki 'kimleri eklemeyi' eşleşmesi döngü olarak yakalanmalıdır."""
        # 1. Diyalog geçmişi
        chat_history = [
            {"role": "user", "content": "14 gün deneme olacak."},
            {"role": "assistant", "content": "Harika! Şimdi rakipleri ele alalım. Bu alana kimleri eklemeyi düşünüyorsunuz?"},
            {"role": "user", "content": "rakip analizi yapmak istemiyorum, kimseyi ekleme."}
        ]
        
        current_brief = {
            "idea": "Evcil hayvan takip uygulaması",
            "title": "Evcil Hayvan Takip Araştırması",
            "target_users": ["Evcil hayvan sahipleri"],
            "expected_price": "aylık abonelik",
            "success_metric": None
        }
        
        # 2. Model yeni yanıtta aynı soruyu tekrar üretiyor (Döngü hatası!)
        result = {
            "updated_brief": {},
            "assistant_reply": "Harika bir fiyatlandırma stratejisi! Bu modeli destekleyecek rakipleri araştırmada ele almalıyız. Bu alana kimleri eklemeyi düşünüyorsunuz?"
        }
        
        class MockResearchModel:
            def generate(self, system, prompt):
                return type("MockResponse", (), {"text": "{}"})()
                
        guard = DiscoveryLoopGuard(max_turns=10, loop_threshold=0.72)
        protected_result = guard.guard_turn(current_brief, chat_history, result, MockResearchModel())
        
        # 3. Döngünün yakalandığını ve sıradaki alan olan success_metric sorusuna geçildiğini doğrula!
        assert "başarıyı nasıl ölçeceğiz" in protected_result["assistant_reply"]
        assert "kimleri eklemeyi" not in protected_result["assistant_reply"]

    def test_loop_detection_with_intermediate_fallback(self):
        """Araya hata/jenerik yanıt girse bile, 3 turn öncesine kadar olan stratejik soruların tekrarlanması döngü olarak yakalanmalıdır."""
        # 1. Diyalog geçmişi (Arada 'Başka eklemek istediğiniz var mı?' gibi jenerik soru var)
        chat_history = [
            {"role": "assistant", "content": "Uygulamayı hangi platformlardan veya hangi yöntemlerle pazara sürmeyi planlıyorsunuz? Örneğin, doğrudan uygulama mağazaları üzerinden mi, yoksa sosyal medya reklamları üzerinden mi?"},
            {"role": "user", "content": "uygulama mağazaları üzerinden."},
            {"role": "assistant", "content": "Kusura bakmayın, bir anlığına dikkatim dağıldı ve yanıtı tamamlayamadım. Lütfen son söylediğinizi tekrarlar mısınız veya devam edebilir miyiz?"},
            {"role": "user", "content": "uygulama mağazaları üzerinden."},
            {"role": "assistant", "content": "Anladım. Başka eklemek istediğiniz bir şey var mı?"},
            {"role": "user", "content": "hayır yok."}
        ]
        
        current_brief = {
            "idea": "Evcil hayvan takip uygulaması",
            "title": "Evcil Hayvan Takip Araştırması",
            "target_users": ["Evcil hayvan sahipleri"],
            "expected_price": "aylık abonelik",
            "success_metric": None,
            "discovery_channels": ["uygulama mağazaları"]
        }
        
        # 2. Model yeni yanıtta 3 turn önceki aynı soruyu tekrar üretiyor (Döngü hatası!)
        result = {
            "updated_brief": {},
            "assistant_reply": "Araştırmamızın temel soruları ve hedefleri çok netleşti! Şimdi tek bir alanımız kaldı: Uygulamayı hangi platformlardan veya hangi yöntemlerle pazara sürmeyi planlıyorsunuz? Örneğin, doğrudan uygulama mağazaları üzerinden mi, yoksa sosyal medya reklamları üzerinden mi?"
        }
        
        class MockResearchModel:
            def generate(self, system, prompt):
                return type("MockResponse", (), {"text": "{}"})()
                
        guard = DiscoveryLoopGuard(max_turns=10, loop_threshold=0.72)
        protected_result = guard.guard_turn(current_brief, chat_history, result, MockResearchModel())
        
        # 3. Döngünün başarıyla yakalandığını ve kalan son eksik alan olan success_metric sorusuna geçildiğini doğrula!
        assert "başarıyı nasıl ölçeceğiz" in protected_result["assistant_reply"]
        assert "hangi platformlardan" not in protected_result["assistant_reply"]

