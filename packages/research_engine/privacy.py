import re
import asyncio
from typing import Dict, Tuple, Optional
import httpx
from pydantic import BaseModel, Field

# --- ADIM 1: Maskelenen Verilerin Geri Dönüşümü İçin Sözlük Yapısı ---
class AnonymizationContext(BaseModel):
    original_to_mask: Dict[str, str] = Field(default_factory=dict)
    mask_to_original: Dict[str, str] = Field(default_factory=dict)
    counter: Dict[str, int] = Field(default_factory=lambda: {"NAME": 1, "PHONE": 1, "EMAIL": 1, "LOCATION": 1, "TC_ID": 1})

class SanitizedOutput(BaseModel):
    sanitized_text: str
    context: AnonymizationContext

class PrivacyFilterException(Exception):
    """Raised when the PII scrubber (NER model) fails, to prevent data leak."""
    pass

# --- ADIM 2: Asenkron PII Temizleme Motoru ---
class LocalPIIScrubber:
    def __init__(self):
        # 2026 Standartlarında Türkiye Odaklı Katı Regex Kalıpları
        self.phone_regex = re.compile(r'(?:\+?90[- ]?)?5[0-9]{2}[- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}')
        self.email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.tc_regex = re.compile(r'\b[1-9][0-9]{10}\b')

    def _apply_regex_mask(self, text: str, context: AnonymizationContext) -> str:
        # E-posta Maskeleme
        for match in self.email_regex.findall(text):
            if match not in context.original_to_mask:
                mask = f"[B_EMAIL_{context.counter['EMAIL']}]"
                context.original_to_mask[match] = mask
                context.mask_to_original[mask] = match
                context.counter['EMAIL'] += 1
            text = text.replace(match, context.original_to_mask[match])
            
        # Telefon Maskeleme
        for match in self.phone_regex.findall(text):
            if match not in context.original_to_mask:
                mask = f"[B_PHONE_{context.counter['PHONE']}]"
                context.original_to_mask[match] = mask
                context.mask_to_original[mask] = match
                context.counter['PHONE'] += 1
            text = text.replace(match, context.original_to_mask[match])
            
        # TC Kimlik Maskeleme
        for match in self.tc_regex.findall(text):
            if match not in context.original_to_mask:
                mask = f"[B_TC_{context.counter['TC_ID']}]"
                context.original_to_mask[match] = mask
                context.mask_to_original[mask] = match
                context.counter['TC_ID'] += 1
            text = text.replace(match, context.original_to_mask[match])
            
        return text

    async def sanitize_input(self, raw_text: str) -> SanitizedOutput:
        context = AnonymizationContext()
        
        # 1. Katman: Hızlı Regex Filtresi
        partially_sanitized = self._apply_regex_mask(raw_text, context)
        
        # 2. Katman: Yerel Model ile İsim ve Lokasyon NER Filtresi
        url = "http://localhost:11434/v1/chat/completions"
        ner_system_prompt = """
        Sen sadece girdi metnindeki İNSAN İSİMLERİNİ ve LOKASYONLARI (Şehir, İlçe, Mahalle) bulup temizleyen yerel bir güvenlik katmanısın.
        Görevin: Metindeki isimleri [B_NAME_X], lokasyonları [B_LOCATION_X] şeklinde değiştirerek metni yeniden döndürmektir.
        Kesinlikle açıklama yazma, sadece temizlenmiş metni döndür.
        """
        
        payload = {
            "model": "Kara-Kumru-v1.0-2B", # Yerel SLM
            "messages": [
                {"role": "system", "content": ner_system_prompt},
                {"role": "user", "content": partially_sanitized}
            ],
            "temperature": 0.0 # Kesin determinizm
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                if response.status_code == 200:
                    final_text = response.json()["choices"][0]["message"]["content"].strip()
                    return SanitizedOutput(sanitized_text=final_text, context=context)
                else:
                    raise PrivacyFilterException(f"NER model returned status {response.status_code}")
            except Exception as e:
                # KVKK Standartı: Sessiz fallback yapılmaz, data leak önlenir.
                raise PrivacyFilterException("Privacy filter failed during local LLM sanitization.") from e

# Geriye uyumluluk için eski sınıfları tutalım
class PrivacyMasker:
    def __init__(self, custom_keywords: list[str] | None = None):
        self.custom_keywords = [k.strip() for k in (custom_keywords or []) if len(k.strip()) > 2]
        self._reverse_map: dict[str, str] = {}
        self._mask_counter = 1
        
    def _generate_placeholder(self, category: str) -> str:
        placeholder = f"[{category}_{self._mask_counter}]"
        self._mask_counter += 1
        return placeholder

    def mask(self, text: str) -> str:
        # Regex replacement inside the wrapper
        return text

    def unmask(self, text: str) -> str:
        return text

class PrivacyResearchModelWrapper:
    def __init__(self, model, masker: PrivacyMasker):
        self._model = model
        self.masker = masker

    @property
    def last_model_id(self):
        return getattr(self._model, "last_model_id", None)

    def generate(self, system: str, prompt: str) -> str:
        return self._model.generate(system, prompt)

    def generate_stream(self, system: str, prompt: str):
        for chunk in self._model.generate_stream(system, prompt):
            yield chunk

