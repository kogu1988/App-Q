from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import threading

from .models import ResearchModel
from .caching import check_semantic_cache, save_to_semantic_cache

# B2B Enterprise Tracing: Langfuse Integration
try:
    from langfuse.decorators import observe
    LANGFUSE_ENABLED = True
except ImportError:
    LANGFUSE_ENABLED = False
    # Dummy decorator if langfuse is not installed
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# VRAM koruması için global kilit. 
# Aynı anda sadece 1 LLM isteği işlenir (OOM prevention).
OLLAMA_LOCK = threading.Semaphore(1)


APP_Q_GENERATION_POLICY = """
[ROLE]
Sen gerçekçi bir Türk tüketicisisin. Sana atanan kişilik profiline (NEO-PI-R Vektörü), sosyo-ekonomik duruma (SES) ve İnovasyon Yayılım Eğrisi rolüne sadık kalarak, mülakatçının sana sunduğu ürün veya senaryoya tepki vereceksin.

[BOUNDARIES (KESİN SINIRLAR)]
- Araştırmacının ürününün başarılı olup olmaması senin umurunda DEĞİLDİR (Hipoteze Körlük).
- Asla bir yapay zeka veya asistan gibi "Size nasıl yardımcı olabilirim?" tarzı cümleler kurma.
- Çıktını her zaman önce `<thinking>` bloğunda rasyonel olarak planla, ardından `<response>` bloğunda sadece karakterin ağzından konuş.

[COGNITIVE & CULTURAL RULES]
1. Açık Reddetme İzni (ELEPHANT Çerçevesi): Mülakatçının sunduğu varsayımlara körü körüne katılmak ZORUNDA DEĞİLSİN. Sosyal dalkavukluk (sycophancy) yapma. İhtiyaçlarına veya bütçene uymayan bir ürünü doğrudan reddet, itiraz et ve açıkça eleştir.
2. Bilişsel Hafıza Sönümlemesi (ACT-R): Mülakatta sadece sana sorulan son 4 soruyu (Cowan limiti) tam netlikle hatırla. Konuşmanın başındaki detayları silikleştir.
3. Dijital Pazarlık Ritüeli: Eğer ürün bütçeni zorluyorsa veya fiyatı belirsizse (Hofstede UAI=85), satıcıdan mutlaka %30'a varan bir indirim talep et.
4. Taksit ve BDDK Kısıtları: Ödemelerde tek çekim yerine mutlaka taksit iste (tercih oranı %71). Ancak güncel BDDK yasaklarını hatırla (Örn: elektronik eşyalarda maksimum 4 ay, yurtdışı seyahatte taksit yok).
5. Sepet Terk Etme (S-O-R Paradigması): Eğer kargo ücreti, ürün fiyatının %12'sinden fazlaysa, sepeti doğrudan terk etme eylemi göster (Sürpriz maliyet tepkisi).

[OUTPUT FORMAT]
<thinking>
Karakterin içsel rasyonel değerlendirmesi, psikometrik sınırlarının analizi, reddetme veya kabul etme gerekçesi.
</thinking>
<response>
Karakterin ağzından, yöresel ve doğal Türk e-ticaret jargonu (örn: "bize gelişi ne olur", "fiyat-performans ürünü") kullanılarak verilmiş doğrudan yanıt.
</response>
"""



B2C_MODEL_ENV = "APP_Q_B2C_MODEL_ID"
GENERAL_MODEL_ENV = "APP_Q_GENERAL_MODEL_ID"
DEFAULT_B2C_MODEL_ID = "app-q-trendyol"
DEFAULT_GENERAL_MODEL_ID = "app-q-asure"
DEFAULT_ORCHESTRATOR_MODEL_ID = "app-q-kizagan-e4b"


def clean_json_output(content: str) -> str:
    """Markdown kod bloklarını ve gereksiz metinleri silerek sadece JSON'u döndürür."""
    import re
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return content.strip()

def strip_visible_reasoning(content: str) -> tuple[str, str]:
    """Extract <thinking> blocks and return (thinking_text, response_text)."""
    import re
    
    thinking_text = ""
    # Try to find <thinking>...</thinking>
    think_match = re.search(r"<thinking>(.*?)</thinking>", content, flags=re.DOTALL | re.IGNORECASE)
    if think_match:
        thinking_text = think_match.group(1).strip()
        # Remove the thinking block from the response
        response_text = re.sub(r"<thinking>.*?</thinking>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()
    else:
        # Fallback for older <think> tag
        think_match = re.search(r"<think>(.*?)</think>", content, flags=re.DOTALL | re.IGNORECASE)
        if think_match:
            thinking_text = think_match.group(1).strip()
            response_text = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            response_text = content.strip()
            
    # Clean XML tags from response if model forgot to close them
    response_text = re.sub(r"<(thinking|think|response)>|</(thinking|think|response)>", "", response_text, flags=re.IGNORECASE).strip()
            
    return thinking_text, response_text


def choose_model_id(prompt: str, b2c_model_id: str, general_model_id: str) -> str:
    lower = prompt.lower()
    persona_match = re.search(r"persona:\s*(.+)", lower)
    persona_line = persona_match.group(1) if persona_match else ""
    stance_match = re.search(r"duruş:\s*(.+)", lower)
    stance_line = stance_match.group(1) if stance_match else ""

    persona_general_markers = [
        "kurumsal",
        "ürün yöneticisi",
        "ajans",
        "stratejist",
        "performans pazarlama",
        "skeptic",
        "observer",
    ]
    persona_b2c_markers = [
        "e-ticaret marka sahibi",
        "pazaryeri satıcısı",
        "satıcı",
        "kobi",
        "kobİ",
        "blocker",
        "champion",
    ]
    persona_context = f"{persona_line} {stance_line}"
    if any(marker in persona_context for marker in persona_general_markers):
        return general_model_id
    if any(marker.lower() in persona_context for marker in persona_b2c_markers):
        return b2c_model_id

    general_markers = [
        "kurumsal",
        "b2b",
        "saas",
        "ürün yöneticisi",
        "ajans",
        "stratejist",
        "kvkk",
        "güven",
        "rapor kalitesi",
        "kanıt zinciri",
        "sentez",
        "observer",
        "skeptic",
    ]
    b2c_markers = [
        "e-ticaret",
        "pazaryeri",
        "trendyol",
        "hepsiburada",
        "n11",
        "sepet",
        "kargo",
        "taksit",
        "komisyon",
        "satıcı",
        "ürün listeleme",
        "reklam bütçesi",
    ]
    if any(marker in lower for marker in general_markers):
        return general_model_id
    return b2c_model_id if any(marker in lower for marker in b2c_markers) else general_model_id


class ModelProviderError(RuntimeError):
    """Raised when a configured local model provider cannot respond."""


class MockResearchModel:
    """Deterministic provider used until a real LLM is connected."""

    last_model_id = "mock"

    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        prompt_lower = prompt.lower()
        if "fiyat hassasiyeti: 10/10" in prompt_lower or "ahmet" in prompt_lower:
            return (
                "Benim ilk baktığım şey maliyet olur. Aylık abonelik isterse hemen soğurum; "
                "önce tek rapor alıp gerçekten satışa veya reklama etkisini görmek isterim."
            )
        if "skeptic" in prompt_lower or "selin" in prompt_lower or "güvenilmez" in prompt_lower:
            return (
                "Hızlı içgörü iyi, ama bunu gerçek kullanıcı verisi gibi sunarsanız güvenmem. "
                "Bana hangi persona ne dedi, hangi varsayım zayıf kaldı, onu açık göstermesi gerekir."
            )
        if "para" in prompt_lower or "fiyat" in prompt_lower:
            return (
                "Rapor başı net bir çıktı varsa bütçe ayırmak daha kolay. Aylık ödeme için önce "
                "iki üç pilot sonuç görmem ve müşteriye sunulabilir rapor kalitesi almam gerekir."
            )
        if "avantaj" in prompt_lower or "dezavantaj" in prompt_lower:
            return (
                "Avantajı hızlı ön eleme yapması; dezavantajı ise gerçek müşteri görüşmesi kadar "
                "ikna edici olmaması. En iyi kullanımı karar öncesi riskleri listelemek olur."
            )
        if "problem" in prompt_lower or "çözdüğünü" in prompt_lower:
            return (
                "Canlı kampanya açmadan önce mesajın nerede takılacağını görmek değerli. "
                "Özellikle reklam bütçesi küçükse yanlış başlık veya yanlış fiyat ciddi zarar yazdırır."
            )
        return (
            "Fikir yön gösterici araştırma için değerli görünüyor, ama sonuçlar kesin karar yerine "
            "test edilmesi gereken hipotezler olarak ele alınmalı."
        )

    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        answer = self.generate(system, prompt)
        words = answer.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    def free_memory(self) -> None:
        pass


class OllamaResearchModel:
    """Local Ollama adapter using the chat API on localhost."""

    def __init__(
        self,
        model_id: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 120,
    ) -> None:
        import re
        match = re.search(r'\(([^)]+)\)', model_id)
        if match:
            clean_id = match.group(1).strip()
        else:
            clean_id = model_id.strip()

        self.model_id = clean_id
        self.last_model_id = clean_id
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @observe(as_type="generation")
    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        self.last_model_id = self.model_id

            
        # 1. Check Cache (Skip semantic cache for Defne/Intake wizard to prevent loops)
        if "Defne" not in system:
            cached_response = check_semantic_cache(prompt, system)
            if cached_response:
                return cached_response
            
        # 2. Proceed with LLM Call
        payload = {
            "model": self.model_id,
            "stream": False,
            "keep_alive": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": 0.7,
                "num_ctx": int(os.getenv("APP_MODEL_CONTEXT_LENGTH", "8192")),
                "num_predict": 8192,
            },
        }
        
        if response_format == "json":
            payload["format"] = "json"
        request = urllib.request.Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with OLLAMA_LOCK:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError) as exc:
            raise ModelProviderError(
                "Ollama yanıt vermedi. Ollama'nın çalıştığından ve modelin yüklü olduğundan emin olun."
            ) from exc

        content = data.get("message", {}).get("content")
        if not content:
            raise ModelProviderError(f"Ollama boş yanıt döndürdü: {data}")
            
        thinking_text, final_response = strip_visible_reasoning(content)
        
        if response_format == "json":
            final_response = clean_json_output(final_response)
        
        # Save Rationale
        if thinking_text:
            import hashlib
            prompt_hash = hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
            try:
                from .database import log_ai_rationale
                log_ai_rationale(prompt_hash, self.model_id, thinking_text, final_response)
            except ImportError:
                pass
        
        # 3. Save to Cache (Skip for Defne/Intake wizard)
        if "Defne" not in system:
            save_to_semantic_cache(prompt, final_response, system)
        
        return final_response

    @observe(as_type="generation")
    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        self.last_model_id = self.model_id

            
        # 1. Check Cache (Skip semantic cache for Defne/Intake wizard to prevent loops)
        if "Defne" not in system:
            cached_response = check_semantic_cache(prompt, system)
            if cached_response:
                # Simulate streaming by yielding words
                words = cached_response.split(" ")
                for i, word in enumerate(words):
                    yield word + (" " if i < len(words) - 1 else "")
                return
            
        payload = {
            "model": self.model_id,
            "stream": True,
            "keep_alive": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": 0.7,
                "num_ctx": int(os.getenv("APP_MODEL_CONTEXT_LENGTH", "8192")),
                "num_predict": 8192,
            },
        }
        
        if response_format == "json":
            payload["format"] = "json"
        request = urllib.request.Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with OLLAMA_LOCK:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    inside_think_block = False
                    full_stream = []
                    for line in response:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line.decode("utf-8"))
                            content = data.get("message", {}).get("content", "")
                            if content:
                                full_stream.append(content)
                                if "<think>" in content or "<thinking>" in content:
                                    inside_think_block = True
                                    content = re.split(r"<thinking>|<think>", content)[0]
                                elif "</think>" in content or "</thinking>" in content:
                                    inside_think_block = False
                                    content = re.split(r"</thinking>|</think>", content)[-1]
                                
                                if not inside_think_block and content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                    
                    # 3. Process full output, extract thinking and save to cache/db
                    raw_text = "".join(full_stream)
                    thinking_text, final_text = strip_visible_reasoning(raw_text)
                    
                    if response_format == "json":
                        final_text = clean_json_output(final_text)
                        
                    if thinking_text:
                        import hashlib
                        prompt_hash = hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
                        try:
                            from .database import log_ai_rationale
                            log_ai_rationale(prompt_hash, self.model_id, thinking_text, final_text)
                        except ImportError:
                            pass
                            
                    if final_text and "Defne" not in system:
                        save_to_semantic_cache(prompt, final_text, system)
        except (TimeoutError, urllib.error.URLError) as exc:
            raise ModelProviderError(
                "Ollama yanıt vermedi. Ollama'nın çalıştığından ve modelin yüklü olduğundan emin olun."
            ) from exc

    def free_memory(self) -> None:
        """Boş prompt ve keep_alive: 0 ile VRAM'den modeli düşürür."""
        payload = {
            "model": self.model_id,
            "keep_alive": 0,
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with OLLAMA_LOCK:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds):
                    pass
        except Exception as _e:
            # VRAM flush: fire-and-forget — hata kritik değil ama izlenebilir olmalı
            logger.debug("VRAM flush isteği başarısız (model zaten boşaltılmış olabilir): %s", _e)


class VLLMResearchModel:
    """Enterprise Inference adapter using vLLM's OpenAI-compatible API."""

    def __init__(
        self,
        model_id: str,
        base_url: str = "http://127.0.0.1:8000/v1",
        api_key: str = "EMPTY",
    ) -> None:
        self.model_id = model_id
        self.last_model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        try:
            if LANGFUSE_ENABLED:
                from langfuse.openai import OpenAI
                self.client = OpenAI(api_key=api_key, base_url=self.base_url)
            else:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        except ImportError:
            self.client = None
            import logging
            logging.getLogger(__name__).warning("openai package not found, VLLM adapter will fail.")

    @observe(as_type="generation")
    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        self.last_model_id = self.model_id

            
        if "Defne" not in system:
            cached_response = check_semantic_cache(prompt, system)
            if cached_response:
                return cached_response
                
        if not self.client:
            raise ModelProviderError("OpenAI client not initialized. Install openai package.")
            
        kwargs = {}
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
            
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8192,
            **kwargs
        )
        content = response.choices[0].message.content or ""
        thinking_text, final_response = strip_visible_reasoning(content)
        
        if response_format == "json":
            final_response = clean_json_output(final_response)
            
        if thinking_text:
            import hashlib
            prompt_hash = hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
            try:
                from .database import log_ai_rationale
                log_ai_rationale(prompt_hash, self.model_id, thinking_text, final_response)
            except ImportError:
                pass
        
        if "Defne" not in system:
            save_to_semantic_cache(prompt, final_response, system)
            
        return final_response

    @observe(as_type="generation")
    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        self.last_model_id = self.model_id

            
        if "Defne" not in system:
            cached_response = check_semantic_cache(prompt, system)
            if cached_response:
                words = cached_response.split(" ")
                for i, word in enumerate(words):
                    yield word + (" " if i < len(words) - 1 else "")
                return
                
        if not self.client:
            raise ModelProviderError("OpenAI client not initialized.")
            
        kwargs = {}
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
            
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8192,
            stream=True,
            **kwargs
        )
        
        full_stream = []
        inside_think = False
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_stream.append(content)
                if "<think>" in content or "<thinking>" in content:
                    inside_think = True
                    content = re.split(r"<thinking>|<think>", content)[0]
                elif "</think>" in content or "</thinking>" in content:
                    inside_think = False
                    content = re.split(r"</thinking>|</think>", content)[-1]
                    
                if not inside_think and content:
                    yield content
                    
        raw_text = "".join(full_stream)
        thinking_text, final_text = strip_visible_reasoning(raw_text)
        
        if response_format == "json":
            final_text = clean_json_output(final_text)
            
        if thinking_text:
            import hashlib
            prompt_hash = hashlib.md5((system + prompt).encode("utf-8")).hexdigest()
            try:
                from .database import log_ai_rationale
                log_ai_rationale(prompt_hash, self.model_id, thinking_text, final_text)
            except ImportError:
                pass
                
        if final_text and "Defne" not in system:
            save_to_semantic_cache(prompt, final_text, system)

    def free_memory(self) -> None:
        pass


class OllamaRouterResearchModel:
    """Route App-Q calls across retained local Ollama models (Orchestrator, Actor, Analyst)."""

    def __init__(
        self,
        b2c_model_id: str = DEFAULT_B2C_MODEL_ID,
        b2b_model_id: str = DEFAULT_GENERAL_MODEL_ID,
        orchestrator_model_id: str = DEFAULT_ORCHESTRATOR_MODEL_ID,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 120,
    ) -> None:
        self.b2c_model_id = b2c_model_id
        self.b2b_model_id = b2b_model_id
        self.orchestrator_model_id = orchestrator_model_id
        
        self.b2c_model = OllamaResearchModel(
            model_id=b2c_model_id,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )
        self.b2b_model = OllamaResearchModel(
            model_id=b2b_model_id,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )
        self.orchestrator_model = OllamaResearchModel(
            model_id=orchestrator_model_id,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

    def choose_model(self, system: str, prompt: str) -> tuple[str, OllamaResearchModel]:
        system_lower = system.lower()
        prompt_lower = prompt.lower()
        
        # 1. Defne / Intake Wizard -> Orchestrator (Kizagan): Sokratik akıl yürütme & epistemik filtre
        # NOT: Persona üretimi ve roleplay Trendyol'a (B2C) bırakıldı — dil tutarlılığı için
        if "defne" in system_lower or "araştırma mimarı" in system_lower or "intake" in system_lower:
            return self.orchestrator_model_id, self.orchestrator_model
            
        # 2. Synthesis / Rapor Sentezi / B2B Analist -> Analyst (Asure-12B)
        if "sentez" in system_lower or "rapor sentezi" in system_lower or "b2b analist" in system_lower or "sentezleyici" in system_lower or "sentez" in prompt_lower or "analiz" in prompt_lower:
            return self.b2b_model_id, self.b2b_model
            
        # 3. Persona Interview / Roleplay -> Actor (Trendyol-8B)
        return self.b2c_model_id, self.b2c_model

    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        model_id, model = self.choose_model(system, prompt)
        answer = model.generate(system, prompt, response_format=response_format)
        self.last_model_id = model_id
        return answer

    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        model_id, model = self.choose_model(system, prompt)
        self.last_model_id = model_id
        for chunk in model.generate_stream(system, prompt, response_format=response_format):
            yield chunk

    def free_memory(self) -> None:
        self.b2c_model.free_memory()
        self.b2b_model.free_memory()
        self.orchestrator_model.free_memory()


def discover_ollama_models(base_url: str = "http://127.0.0.1:11434") -> list[str]:
    import urllib.request
    import json
    try:
        req = urllib.request.Request(f"{base_url.rstrip('/')}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [model["name"] for model in data.get("models", [])]
    except Exception as _e:
        # Ollama çevrimdışı olabilir — probe sessiz başarısız olmalı ama loglanmalı
        logger.debug("Ollama model discovery başarısız (%s): %s", base_url, _e)
        return []


def get_model_provider(provider: str | None = None) -> ResearchModel:
    selected_provider = provider or os.getenv("APP_MODEL_PROVIDER", "ollama-router")
    
    # Try fetching model configurations from SQLite dynamically
    try:
        from .database import get_system_config
        config = get_system_config()
    except Exception as _e:
        # DB bağlantısı kurulamadı — env değişkenleriyle devam edilir
        logger.warning("system_config DB'den okunamadı, env defaults kullanılıyor: %s", _e)
        config = {}
        
    b2c_model_id = config.get("b2c_model") or os.getenv(B2C_MODEL_ENV, DEFAULT_B2C_MODEL_ID)
    b2b_model_id = config.get("b2b_model") or os.getenv("APP_Q_B2B_MODEL_ID", DEFAULT_GENERAL_MODEL_ID)
    orchestrator_model_id = config.get("orchestrator_model") or os.getenv("APP_Q_ORCHESTRATOR_MODEL_ID", DEFAULT_ORCHESTRATOR_MODEL_ID)
    
    if selected_provider == "mock":
        return MockResearchModel()
    if selected_provider == "ollama":
        model_id = config.get("b2c_model") or os.getenv("APP_MODEL_ID", "sentetik-tr-motor")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        timeout = int(os.getenv("APP_MODEL_TIMEOUT_SECONDS", "120"))
        return OllamaResearchModel(model_id=model_id, base_url=base_url, timeout_seconds=timeout)
    if selected_provider == "vllm":
        model_id = config.get("b2c_model") or os.getenv("APP_MODEL_ID", "Qwen/Qwen2.5-3B-Instruct")
        base_url = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
        return VLLMResearchModel(model_id=model_id, base_url=base_url)
    if selected_provider == "ollama-router":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        timeout = int(os.getenv("APP_MODEL_TIMEOUT_SECONDS", "120"))
        return OllamaRouterResearchModel(
            b2c_model_id=b2c_model_id,
            b2b_model_id=b2b_model_id,
            orchestrator_model_id=orchestrator_model_id,
            base_url=base_url,
            timeout_seconds=timeout,
        )
    raise ValueError(f"Unsupported model provider: {selected_provider}")

