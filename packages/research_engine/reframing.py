import json
import logging
from typing import Any
from .models import ResearchBrief, ResearchModel

logger = logging.getLogger(__name__)

def apply_input_reframing(brief: ResearchBrief, model: ResearchModel) -> dict[str, Any]:
    """
    Kullanıcının öznel brief girdisini nesnel (objective) araştırma sorularına
    ve bağlama dönüştüren Reframing katmanı.
    """
    system_prompt = (
        "Sen, sentetik pazar araştırması sisteminin ön yüzünde çalışan, UK AISI standartlarında "
        "optimize edilmiş bir 'Girdi Yeniden Çerçeveleme' (Input Reframing) ara katman modelisin.\n"
        "Görevin: Kullanıcı tarafından girilen brief metnini analiz etmek; metnin içindeki tüm 'öznel inançları', "
        "'birinci tekil şahıs iddialarını', 'başarı beklentilerini' ve 'yönlendirici validasyon arayışlarını' tamamen kazımaktır.\n\n"
        "Girdiyi şu katı kurallara göre dönüştüreceksin:\n"
        "1. Kesinlikle kullanıcının tarafını tutma, iddiaları doğru kabul etme.\n"
        "2. Metni hipotez-nötr, tamamen nesnel, yanlışlanabilir ve Sokratik bir araştırma sorusu setine dönüştür.\n"
        "3. Çıktıda kullanıcının kimliğine, tasarımına dair övgülere yer verme. Ürünü/servisi çıplak işlevleriyle tanımla.\n"
        "4. Çıktıyı kesinlikle aşağıdaki JSON formatında döndür. JSON haricinde hiçbir prose veya açıklama metni ekleme.\n\n"
        "RESPONSE_JSON_SCHEMA:\n"
        "{\n"
        "  \"objective_product_context\": \"Ürünün/fikrin tüm öznel övgülerden arındırılmış saf, fonksiyonel tanımı.\",\n"
        "  \"primary_research_questions\": [\n"
        "    \"Açık uçlu, hipoteze kör, risk ve pazar direncini ölçmeye odaklanan nesnel araştırma sorusu 1\",\n"
        "    \"Açık uçlu, hipoteze kör nesnel araştırma sorusu 2\"\n"
        "  ]\n"
        "}"
    )

    # Brief parçalarını birleştirerek analize sunalım
    target_users = ", ".join(brief.target_users) if brief.target_users else "Belirtilmemiş"
    user_questions = "\\n- ".join(brief.questions) if brief.questions else "Belirtilmemiş"

    user_prompt = (
        f"Brief Fikri: \"{brief.idea}\"\n"
        f"Hedef Kitle: {target_users}\n"
        f"Kullanıcının Sorduğu Sorular:\n- {user_questions}\n"
    )

    try:
        response_text = model.generate(system=system_prompt, prompt=user_prompt)
        
        # Sadece JSON kısmını ayrıştır
        json_start = response_text.find("{")
        json_end = response_text.rfind("}")
        
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start:json_end+1]
            result = json.loads(json_str)
            return result
        else:
            raise ValueError("Model geçerli bir JSON döndürmedi.")
            
    except Exception as e:
        logger.error(f"Input reframing başarısız oldu: {e}")
        # Fallback durumu (Hata olursa orijinal veriyi kabaca nötralize etmeye çalış)
        return {
            "objective_product_context": brief.idea,
            "primary_research_questions": brief.questions or [
                f"{brief.category} bağlamında tüketici itirazları nelerdir?",
                "Mevcut fiyat/fayda dengesi tüketici tarafından nasıl algılanıyor?"
            ]
        }
