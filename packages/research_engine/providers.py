from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import OrderedDict

from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from .models import ResearchModel

logger = logging.getLogger(__name__)

# — Retry edilebilir OpenAI/DeepSeek hataları —
# Kimlik doğrulama (401) veya geçersiz istek (400) YENİDEN DENENMEZ: boşuna gecikme olur.
try:
    from openai import (
        APIConnectionError,
        APITimeoutError,
        InternalServerError,
        RateLimitError,
    )

    _RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
        APITimeoutError,
        APIConnectionError,
        RateLimitError,
        InternalServerError,
    )
except ImportError:  # openai yoksa retry devre dışı
    _RETRYABLE_EXCEPTIONS = ()


# LLM çağrısı zaman aşımı (saniye) — asılı kalmayı önler (P0-5)
# Uzun sentez/mülakatlar için 120sn makul; gerektiğinde DEEPSEEK_TIMEOUT ile artırılır.
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "120"))
# Maksimum üretim token sayısı (nihai içerik; thinking modunda reasoning ayrı alandır).
# Uzun raporlar kesilmesin diye env ile artırılabilir (ör. DEEPSEEK_MAX_TOKENS=16384).
DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "8192"))
# Maksimum yeniden deneme sayısı (ilk deneme dahil)
DEEPSEEK_MAX_RETRIES = int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))


def _resolve_max_tokens(override: int | None = None) -> int:
    """Çağrı anında geçerli max_tokens değerini döndürür (env her çağrıda okunur).

    Öncelik: açık `override` > `DEEPSEEK_MAX_TOKENS` env > modül varsayılanı.
    """
    if override and override > 0:
        return int(override)
    return int(os.getenv("DEEPSEEK_MAX_TOKENS", str(DEEPSEEK_MAX_TOKENS)))


# ── LLM içerik-hash önbelleği (maliyet azaltma) ────────────────────────────
# Aynı (model, system, prompt, response_format, max_tokens) için ikinci çağrı
# API'ye gitmez. Adversarial döngülerde aynı transkriptlerin tekrar kodlanması
# gibi tekrarlı çağrıları ucuza indirir. Semantik (embedding) DEĞİL, birebir
# içerik hash'idir; bu yüzden yanlış eşleşme riski yoktur.
LLM_CACHE_ENABLED = os.getenv("LLM_CACHE_ENABLED", "true").lower() in {"1", "true", "yes"}
_LLM_CACHE_MAX = int(os.getenv("LLM_CACHE_MAX", "512"))
_LLM_CACHE_TTL = float(os.getenv("LLM_CACHE_TTL", "3600"))
_LLM_CACHE: "OrderedDict[str, tuple[float, str]]" = OrderedDict()
_LLM_CACHE_LOCK = threading.Lock()
_LLM_CACHE_HITS = 0
_LLM_CACHE_MISSES = 0


def _cache_key(model_id: str, system: str, prompt: str,
               response_format: str | None, max_tokens: int | None) -> str:
    hasher = hashlib.sha256()
    for part in (model_id, system, prompt, response_format or "", str(max_tokens or "")):
        hasher.update(part.encode("utf-8"))
        hasher.update(b"\x00")
    return hasher.hexdigest()


def _cache_get(key: str) -> str | None:
    global _LLM_CACHE_HITS, _LLM_CACHE_MISSES
    if not LLM_CACHE_ENABLED:
        return None
    with _LLM_CACHE_LOCK:
        entry = _LLM_CACHE.get(key)
        if not entry:
            _LLM_CACHE_MISSES += 1
            return None
        ts, value = entry
        if _LLM_CACHE_TTL > 0 and (time.time() - ts) > _LLM_CACHE_TTL:
            _LLM_CACHE.pop(key, None)
            _LLM_CACHE_MISSES += 1
            return None
        _LLM_CACHE.move_to_end(key)
        _LLM_CACHE_HITS += 1
        return value


def _cache_set(key: str, value: str) -> None:
    if not LLM_CACHE_ENABLED or not value:
        return
    with _LLM_CACHE_LOCK:
        _LLM_CACHE[key] = (time.time(), value)
        _LLM_CACHE.move_to_end(key)
        while len(_LLM_CACHE) > _LLM_CACHE_MAX:
            _LLM_CACHE.popitem(last=False)


def get_llm_cache_stats() -> dict:
    """Önbellek istatistikleri (maliyet gözlemi için)."""
    with _LLM_CACHE_LOCK:
        return {
            "enabled": LLM_CACHE_ENABLED,
            "size": len(_LLM_CACHE),
            "hits": _LLM_CACHE_HITS,
            "misses": _LLM_CACHE_MISSES,
        }


def _retry_policy() -> Retrying:
    """Çağrı anında okunan retry politikası (test edilebilirlik için env her seferinde okunur)."""
    retryable = _RETRYABLE_EXCEPTIONS or (Exception,)
    return Retrying(
        stop=stop_after_attempt(int(os.getenv("DEEPSEEK_MAX_RETRIES", str(DEEPSEEK_MAX_RETRIES)))),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        retry=retry_if_exception_type(retryable),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# B2B Enterprise Tracing: Langfuse Integration
try:
    from langfuse.decorators import observe
    LANGFUSE_ENABLED = True
except ImportError:
    LANGFUSE_ENABLED = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# — DeepSeek API config —
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_FLASH_MODEL = os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash")
DEEPSEEK_PRO_MODEL = os.getenv("DEEPSEEK_PRO_MODEL", "deepseek-v4-pro")


class ModelProviderError(RuntimeError):
    """Raised when the configured model provider cannot respond."""


def clean_json_output(content: str) -> str:
    """Markdown kod bloklarını ve gereksiz metinleri silerek sadece JSON'u döndürür."""
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return content.strip()


class DeepSeekResearchModel:
    """
    DeepSeek API adapter — OpenAI-compatible client.
    
    Thinking Mode: Her iki modelde de varsayılan olarak aktif.
    - Pro: "low" effort bile "high" olarak haritalanır → her zaman düşünür
    - Flash: effort değerine göre low/high/max
    - reasoning_content: ayrı alanda gelir, <thinking> tag'leri KULLANILMAZ
    - temperature/bastırma parametreleri thinking mode'da etkisizdir
    """

    def __init__(
        self,
        model_id: str,
        base_url: str = DEEPSEEK_BASE_URL,
        api_key: str | None = None,
        user_id: str = "",
    ) -> None:
        self.model_id = model_id
        self.last_model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id  # KVCache isolation + content safety

        api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ModelProviderError("DEEPSEEK_API_KEY env var zorunlu.")

        self.api_key = api_key

        try:
            from openai import OpenAI

            # max_retries=0: retry'ı tenacity yönetir → çift retry/çift ücret olmaz.
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.base_url,
                timeout=DEEPSEEK_TIMEOUT,
                max_retries=0,
            )
        except ImportError:
            self.client = None
            logger.error("openai package not found. DeepSeek adapter will fail.")

        # Son çağrının token kullanımı (P0-6 maliyet muhasebesi)
        self.last_usage: dict = {}
        # İşlem boyunca biriken kullanım — batch mülakatlarda tek tek değil toplam kaydedilir
        self.cumulative_usage: dict = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 0,
        }

    def _chat(self, **kwargs):
        """Tek LLM çağrısı — timeout + exponential backoff retry (P0-5).

        Stream için de kullanılır: `create()` iterator döndürdüğü için retry SADECE
        ilk chunk'tan önce çalışır. Yarıda kesilen stream yeniden denenmez.

        NOT: tenacity `Retrying.__call__(fn, *args, **kwargs)`; kwargs, `fn`'e
        GEÇİLMELİDİR. `_retry_policy()(fn)(**kwargs)` yazılırsa fn argümansız
        çağrılır ve OpenAI SDK "Missing required arguments" hatası verir.
        """
        if not self.client:
            raise ModelProviderError("OpenAI client not initialized. Install openai package.")
        return _retry_policy()(self.client.chat.completions.create, **kwargs)

    def _capture_usage(self, response) -> None:
        """DeepSeek yanıtındaki token kullanımını saklar (cache-hit alanları dahil)."""
        usage = getattr(response, "usage", None)
        if not usage:
            return
        self.last_usage = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            # DeepSeek context caching — indirimli faturalanır
            "prompt_cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", 0) or 0,
            "prompt_cache_miss_tokens": getattr(usage, "prompt_cache_miss_tokens", 0) or 0,
        }
        for key, value in self.last_usage.items():
            self.cumulative_usage[key] = self.cumulative_usage.get(key, 0) + int(value or 0)

    @observe(as_type="generation")
    def generate(
        self,
        system: str,
        prompt: str,
        response_format: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        self.last_model_id = self.model_id

        if not self.client:
            raise ModelProviderError("OpenAI client not initialized. Install openai package.")

        kwargs: dict = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": _resolve_max_tokens(max_tokens),
            # temperature thinking mode'da etkisiz — kaldırıldı
            "extra_body": {
                "thinking": {"type": "enabled"},
                "user_id": self.user_id,
            },
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        # İçerik-hash önbelleği: birebir aynı çağrı tekrar API'ye gitmez
        cache_key = _cache_key(self.model_id, system, prompt, response_format, kwargs.get("max_tokens"))
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self._chat(**kwargs)
        except ModelProviderError:
            raise
        except Exception as exc:
            raise ModelProviderError(f"DeepSeek API çağrısı başarısız ({self.model_id}): {exc}") from exc

        self._capture_usage(response)

        # DeepSeek thinking mode: reasoning_content ayrı alanda gelir (inline <thinking> tag'i DEĞİL)
        reasoning = getattr(response.choices[0].message, "reasoning_content", "") or ""
        content = response.choices[0].message.content or ""

        if response_format == "json":
            content = clean_json_output(content)

        # Log rationale if reasoning was present
        if reasoning:
            import hashlib as _hashlib
            prompt_hash = _hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
            try:
                from .database import log_ai_rationale
                log_ai_rationale(prompt_hash, self.model_id, reasoning, content)
            except ImportError:
                pass

        _cache_set(cache_key, content)
        return content

    @observe(as_type="generation")
    def generate_stream(
        self,
        system: str,
        prompt: str,
        response_format: str | None = None,
        max_tokens: int | None = None,
    ):
        self.last_model_id = self.model_id

        if not self.client:
            raise ModelProviderError("OpenAI client not initialized.")

        kwargs: dict = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": _resolve_max_tokens(max_tokens),
            "stream": True,
            "extra_body": {
                "thinking": {"type": "enabled"},
                "user_id": self.user_id,
            },
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self._chat(**kwargs)
        except ModelProviderError:
            raise
        except Exception as exc:
            raise ModelProviderError(f"DeepSeek API stream çağrısı başarısız ({self.model_id}): {exc}") from exc

        full_content: list[str] = []
        full_reasoning: list[str] = []

        for chunk in response:
            delta = chunk.choices[0].delta
            # reasoning_content → zincirleme düşünce (stream edilmez, sadece loglanır)
            rc = getattr(delta, "reasoning_content", "")
            if rc:
                full_reasoning.append(rc)
            # content → asıl yanıt (kullanıcıya stream edilir)
            c = getattr(delta, "content", "")
            if c:
                full_content.append(c)
                yield c

        # Stream sonrası reasoning'i logla
        if full_reasoning:
            import hashlib
            prompt_hash = hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
            try:
                from .database import log_ai_rationale
                log_ai_rationale(
                    prompt_hash,
                    self.model_id,
                    "".join(full_reasoning),
                    "".join(full_content),
                )
            except ImportError:
                pass

    def free_memory(self) -> None:
        pass  # Cloud API — no local memory to free


def get_model_provider(provider: str | None = None, user_id: str = "") -> ResearchModel:
    """
    Factory for model providers.

    provider:
      - None / "flash" / "intake" / "persona"   → deepseek-v4-flash
      - "pro" / "synthesis" / "report"           → deepseek-v4-pro
      - Full model ID (e.g. "deepseek-v4-flash") → direkt kullan

    user_id: DeepSeek user_id isolation (KVCache, content safety, scheduling).
             Yalnizca [a-zA-Z0-9_-] karakterleri — otomatik temizlenir.
    """
    flash_aliases = {None, "flash", "intake", "persona", "interview", "plan"}
    pro_aliases = {"pro", "synthesis", "report"}

    provider = (provider or "").lower()

    if provider in flash_aliases or provider == "":
        model_id = DEEPSEEK_FLASH_MODEL
    elif provider in pro_aliases:
        model_id = DEEPSEEK_PRO_MODEL
    else:
        model_id = provider

    # DeepSeek user_id regex: [a-zA-Z0-9\-_]+, max 512 char
    import re
    safe_user_id = re.sub(r'[^a-zA-Z0-9\-_]', '', (user_id or "").strip())[:64] or "anonymous"

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    return DeepSeekResearchModel(model_id=model_id, api_key=api_key, user_id=safe_user_id)
