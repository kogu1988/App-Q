from __future__ import annotations

import json
import logging
import os
import re

from .models import ResearchModel

logger = logging.getLogger(__name__)

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

# — OpenRouter config (deneme/trial model) —
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "stealth/ox-alpha")


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
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        except ImportError:
            self.client = None
            logger.error("openai package not found. DeepSeek adapter will fail.")

    @observe(as_type="generation")
    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        self.last_model_id = self.model_id

        if not self.client:
            raise ModelProviderError("OpenAI client not initialized. Install openai package.")

        kwargs: dict = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
            # temperature thinking mode'da etkisiz — kaldırıldı
            "extra_body": {
                "thinking": {"type": "enabled"},
                "user_id": self.user_id,
            },
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise ModelProviderError(f"DeepSeek API çağrısı başarısız ({self.model_id}): {exc}") from exc

        # DeepSeek thinking mode: reasoning_content ayrı alanda gelir (inline <thinking> tag'i DEĞİL)
        reasoning = getattr(response.choices[0].message, "reasoning_content", "") or ""
        content = response.choices[0].message.content or ""

        if response_format == "json":
            content = clean_json_output(content)

        # Log rationale if reasoning was present
        if reasoning:
            import hashlib
            prompt_hash = hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
            try:
                from .database import log_ai_rationale
                log_ai_rationale(prompt_hash, self.model_id, reasoning, content)
            except ImportError:
                pass

        return content

    @observe(as_type="generation")
    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        self.last_model_id = self.model_id

        if not self.client:
            raise ModelProviderError("OpenAI client not initialized.")

        kwargs: dict = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
            "stream": True,
            "extra_body": {
                "thinking": {"type": "enabled"},
                "user_id": self.user_id,
            },
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
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


class OpenRouterModel:
    """OpenRouter adapter — OpenAI-compatible client (trial/deneme model)."""

    def __init__(self, model_id: str | None = None, api_key: str | None = None, user_id: str = "") -> None:
        self.model_id = model_id or OPENROUTER_MODEL
        self.last_model_id = self.model_id
        self.user_id = user_id

        api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ModelProviderError("OPENROUTER_API_KEY env var zorunlu.")

        self.api_key = api_key

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
        except ImportError:
            self.client = None
            logger.error("openai package not found. OpenRouter adapter will fail.")

    @observe(as_type="generation")
    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        self.last_model_id = self.model_id

        if not self.client:
            raise ModelProviderError("OpenAI client not initialized. Install openai package.")

        kwargs: dict = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise ModelProviderError(f"OpenRouter API çağrısı başarısız ({self.model_id}): {exc}") from exc

        content = response.choices[0].message.content or ""

        if response_format == "json":
            content = clean_json_output(content)

        return content

    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        raise ModelProviderError("OpenRouter stream desteklenmiyor (persona üretimi stream kullanmaz).")

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
    flash_aliases = {None, "flash", "intake", "interview", "plan"}
    pro_aliases = {"pro", "synthesis", "report"}
    persona_aliases = {"persona"}

    provider = (provider or "").lower()

    # DeepSeek user_id regex: [a-zA-Z0-9\-_]+, max 512 char
    import re
    safe_user_id = re.sub(r'[^a-zA-Z0-9\-_]', '', (user_id or "").strip())[:64] or "anonymous"

    # Persona üretimi → OpenRouter ox-alpha (deneme/trial model)
    if provider in persona_aliases:
        return OpenRouterModel(user_id=safe_user_id)

    if provider in flash_aliases or provider == "":
        model_id = DEEPSEEK_FLASH_MODEL
    elif provider in pro_aliases:
        model_id = DEEPSEEK_PRO_MODEL
    else:
        model_id = provider

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    return DeepSeekResearchModel(model_id=model_id, api_key=api_key, user_id=safe_user_id)
