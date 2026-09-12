import logging
import os
import re
from typing import Dict
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    """İki katmanlı PII temizleyici.

    1) Katman — Regex: telefon/e-posta/TC (model GEREKTİRMEZ, her planda çalışır).
    2) Katman — Yerel NER modeli: isim/lokasyon (Enterprise özelliği; yerel SLM ister).

    Yapılandırma (env):
      PII_NER_ENABLED : yerel NER modeli kullanılsın mı (varsayılan: false — model yoksa çağrı denemez)
      PII_MODEL_URL   : OpenAI-uyumlu chat/completions adresi (varsayılan: localhost:11434)
      PII_MODEL_NAME  : model adı
      PII_TIMEOUT     : saniye (varsayılan 10)
      PII_STRICT      : true ise NER hatasında exception fırlatır (varsayılan: false → regex'e düşer)
    """

    def __init__(self, enable_ner: bool | None = None):
        # 2026 Standartlarında Türkiye Odaklı Katı Regex Kalıpları
        self.phone_regex = re.compile(r'(?:\+?90[- ]?)?5[0-9]{2}[- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}')
        self.email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.tc_regex = re.compile(r'\b[1-9][0-9]{10}\b')

        self.model_url = os.getenv("PII_MODEL_URL", "http://localhost:11434/v1/chat/completions")
        self.model_name = os.getenv("PII_MODEL_NAME", "Kara-Kumru-v1.0-2B")
        try:
            self.timeout = float(os.getenv("PII_TIMEOUT", "10"))
        except ValueError:
            self.timeout = 10.0
        self.strict = os.getenv("PII_STRICT", "false").lower() in {"1", "true", "yes"}
        if enable_ner is None:
            enable_ner = os.getenv("PII_NER_ENABLED", "false").lower() in {"1", "true", "yes"}
        self.enable_ner = bool(enable_ner)

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

        # 1. Katman: Hızlı Regex Filtresi (her planda, model gerektirmez)
        partially_sanitized = self._apply_regex_mask(raw_text, context)

        # NER kapalıysa (varsayılan: yerel model yok / plan uygun değil) doğrudan regex sonucu.
        if not self.enable_ner:
            return SanitizedOutput(sanitized_text=partially_sanitized, context=context)

        # 2. Katman: Yerel Model ile İsim ve Lokasyon NER Filtresi
        ner_system_prompt = """
        Sen sadece girdi metnindeki İNSAN İSİMLERİNİ ve LOKASYONLARI (Şehir, İlçe, Mahalle) bulup temizleyen yerel bir güvenlik katmanısın.
        Görevin: Metindeki isimleri [B_NAME_X], lokasyonları [B_LOCATION_X] şeklinde değiştirerek metni yeniden döndürmektir.
        Kesinlikle açıklama yazma, sadece temizlenmiş metni döndür.
        """

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": ner_system_prompt},
                {"role": "user", "content": partially_sanitized},
            ],
            "temperature": 0.0,  # Kesin determinizm
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.model_url, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    final_text = response.json()["choices"][0]["message"]["content"].strip()
                    return SanitizedOutput(sanitized_text=final_text, context=context)
                raise RuntimeError(f"NER model returned status {response.status_code}")
            except Exception as e:
                if self.strict:
                    # Enterprise/katı mod: sessiz fallback yok, veri sızıntısı önlenir.
                    raise PrivacyFilterException(
                        "Privacy filter failed during local LLM sanitization."
                    ) from e
                # Dayanıklı mod (varsayılan): regex maskesi uygulanmış metinle devam et.
                logger.warning(
                    "Yerel PII/NER modeli kullanılamadı (%s) — regex maskeleme ile devam ediliyor. "
                    "İsim/lokasyon maskelemesi devre dışı; Enterprise'da PII_STRICT=true önerilir.",
                    e,
                )
                return SanitizedOutput(sanitized_text=partially_sanitized, context=context)

# Geriye uyumluluk için eski sınıfları tutalım
class PrivacyMasker:
    """LLM'e gitmeden önce PII maskeleyen GERÇEK maskeleyici (eskiden no-op'tu).

    - Telefon / e-posta / TC kimlik → her planda (KVKK temel katman)
    - custom_keywords (ör. rakip markalar) → opsiyonel, çağıran taraf karar verir

    Aynı değer her zaman aynı placeholder'a eşlenir (request boyunca tutarlı),
    `unmask` ile orijinal değerler geri getirilir.
    """

    def __init__(self, custom_keywords: list[str] | None = None):
        self.custom_keywords = [k.strip() for k in (custom_keywords or []) if len(k.strip()) > 2]
        self._reverse_map: dict[str, str] = {}   # placeholder -> original
        self._forward_map: dict[str, str] = {}   # original -> placeholder
        self._counter: dict[str, int] = {"EMAIL": 1, "TC_ID": 1, "PHONE": 1, "BRAND": 1}

        self._email_re = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self._tc_re = re.compile(r'\b[1-9][0-9]{10}\b')
        self._phone_re = re.compile(r'(?:\+?90[- ]?)?5[0-9]{2}[- ]?[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{2}')

    def _placeholder(self, category: str, original: str) -> str:
        existing = self._forward_map.get(original)
        if existing:
            return existing
        placeholder = f"[{category}_{self._counter[category]}]"
        self._counter[category] += 1
        self._forward_map[original] = placeholder
        self._reverse_map[placeholder] = original
        return placeholder

    def mask(self, text: str) -> str:
        if not text:
            return text
        out = text
        # Sıra önemli: TC (11 hane) telefondan (10 hane) önce maskelenmeli.
        out = self._email_re.sub(lambda m: self._placeholder("EMAIL", m.group(0)), out)
        out = self._tc_re.sub(lambda m: self._placeholder("TC_ID", m.group(0)), out)
        out = self._phone_re.sub(lambda m: self._placeholder("PHONE", m.group(0)), out)
        for kw in self.custom_keywords:
            out = re.sub(
                re.escape(kw),
                lambda m: self._placeholder("BRAND", m.group(0)),
                out,
                flags=re.IGNORECASE,
            )
        return out

    def unmask(self, text: str) -> str:
        if not text or not self._reverse_map:
            return text
        out = text
        for placeholder, original in self._reverse_map.items():
            out = out.replace(placeholder, original)
        return out


class PrivacyResearchModelWrapper:
    """Modeli sarar: prompt LLM'e gitmeden maskelenir, yanıt kullanıcıya dönmeden açılır."""

    def __init__(self, model, masker: PrivacyMasker):
        self._model = model
        self.masker = masker

    @property
    def last_model_id(self):
        return getattr(self._model, "last_model_id", None)

    @property
    def model_id(self):
        return getattr(self._model, "model_id", None) or self.last_model_id

    @property
    def last_usage(self):
        return getattr(self._model, "last_usage", {})

    @property
    def cumulative_usage(self):
        return getattr(self._model, "cumulative_usage", {})

    def free_memory(self) -> None:
        """Alt modele devret — aksi halde streaming finalizer'ı AttributeError verir."""
        free = getattr(self._model, "free_memory", None)
        if callable(free):
            free()

    def generate(self, system: str, prompt: str, response_format=None) -> str:
        masked_system = self.masker.mask(system)
        masked_prompt = self.masker.mask(prompt)
        response = self._model.generate(masked_system, masked_prompt, response_format)
        return self.masker.unmask(response)

    def generate_stream(self, system: str, prompt: str, response_format=None):
        masked_system = self.masker.mask(system)
        masked_prompt = self.masker.mask(prompt)
        buffer = ""
        for chunk in self._model.generate_stream(masked_system, masked_prompt, response_format):
            buffer += chunk
            # Placeholder (`[PHONE_1]`) parçalanmasın: yarım kalan kuyruğu tamponla.
            idx = buffer.rfind("[")
            if idx != -1 and "]" not in buffer[idx:]:
                emit, buffer = buffer[:idx], buffer[idx:]
            else:
                emit, buffer = buffer, ""
            if emit:
                yield self.masker.unmask(emit)
        if buffer:
            yield self.masker.unmask(buffer)

