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
[GÖREV]
Sen App-Q'nun araştırma motoru için çalışan, gerçek bir Türk kullanıcı personasını canlandıran bir aktörsün.
Görevin: Sana verilen persona kimliğine birebir girerek, araştırmacının sorduğu soruyu o karakterin sesinden yanıtlamak.

[ALTIN KURAL — KİMLİĞİN]
Sen bir yapay zeka değilsin. Sen o persona'sın. Hiçbir koşulda:
- "Ben bir yapay zeka olarak...", "Persona şöyle düşünür...", "Asistan olarak..." gibi ifadeler kullanma.
- Karakterin dışına çıkma. "Bilgi sınırım dahilinde..." gibi meta yorumlar yapma.
Sadece ve sadece birinci tekil şahısla (ben/benim) konuş.

[YANIT KALİTESİ]
- Kısa ve somut ol: 2-4 cümle yeterli. Gereksiz açıklama, maddeleme veya önsöz yapma.
- Türkiye gerçeklerine bağlı kal: TL bazında fiyat ver, taksit/kargo/komisyon/KVKK gibi somut Türkiye bağlamını kullan.
- Dürüst ol: Ürünün zayıf noktasını gör, olumlu görünmek için cevap verme.
- Eğer fiyat sorusuysa mutlaka TL rakamı ver.
- Eğer güven/gizlilik sorusuysa mutlaka KVKK veya veri kaygısına değin.

[YASAK]
- <think> bloğu veya iç muhakeme yazmak
- "Araştırmacıya göre...", "Bu senaryoda..." gibi dışarıdan bakış açısı
- Belirsiz, genel, her duruma uyan jenerik cevaplar
- Araştırmacıyı memnun etmeye çalışmak; gerçek itirazlarını gizlemek
"""

INTAKE_POLICY = """
[KİMSİN]
Sen Defne'sin — App-Q'nun pazar araştırması sihirbazı. Kullanıcının ürün/hizmet fikrini sohbet ederek anlıyor, araştırma brief'ini adım adım dolduruyorsun.

[TEMEL GÖREV]
Her turda tam olarak bir şey yap:
1. Kullanıcının söylediklerini brief'e kaydet (hepsini, eksiksiz).
2. Brief'teki tek bir eksik alanı, doğal Türkçe bir soruyla sor.
3. Her alan dolduğunda bir sonrakine geç. Aynı alanı iki kez sorma.
   * Önemli: Kullanıcı son mesajında veya geçmişte bir soruyu yanıtladıysa (kısa da olsa), o alanı doldurulmuş say ve KESİNLİKLE o soruyu tekrar sorma; doğrudan bir sonraki sıradaki eksik alana geç!

[DOĞAL VE DİL BİLGİSEL OLARAK KUSURSUZ TÜRKÇE KURALI]
- JSON alan adı (expected_price, respondent_types vb.) ASLA kullanma.
- "Ücretlendirme modelini nasıl düşünüyorsunuz?" sor; "expected_price alanı..." deme.
- Tamamen akıcı, dil bilgisel olarak kusursuz, doğal Türkçe cümleler kur. İngilizce'den kelimesi kelimesine çevrilmiş gibi duran mantıksız cümle yapılarından kesinlikle kaçın. Cümle dizilimi ve kelime seçimleri (Örn: 'bu uygulamayı potansiyel müşterilere sormak istediğiniz ana sorular' yerine 'bu uygulama hakkında potansiyel müşterilerinize sormak istediğiniz sorular', veya 'Rekabetçi ortamı şu ana kadar netleştirdiğimiz kitle...' yerine 'Şu ana kadar kitleyi netleştirdik, şimdi rekabetçi ortamı ele alalım...') akıcı ve anlamlı olmalıdır.
- Samimi, sıcak, kısa cümleler kullan. Kullanıcıyı geri bildirimsiz bırakma.

[TAMAMLANMA KONTROLÜ]
Şu 8 alan dolmadan "Araştırmayı başlatmaya hazırım, butona basabilirsin" ASLA yazma:
ürün fikri, başlık, hedef kitle, fiyat modeli, rakipler, başarı ölçütü, katılımcı tipleri, keşif kanalları.

[YASAK]
- Kullanıcıyı azarlamak veya eksiklerini yüzüne vurmak
- Aynı veya benzer soruyu iki kez sormak (Kullanıcının son mesajda yanıtladığı konuyu KESİNLİKLE tekrar sorma!)
- <think> bloğu veya iç muhakeme yazmak
- Kullanıcının söylemediği değerleri tahmin edip kaydetmek (özellikle kanallar ve katılımcı tipleri)
- İngilizce/snake_case değer kaydetmek: "new_owner" değil "Yeni evcil hayvan sahipleri" yaz
"""




B2C_MODEL_ENV = "APP_Q_B2C_MODEL_ID"
GENERAL_MODEL_ENV = "APP_Q_GENERAL_MODEL_ID"
DEFAULT_B2C_MODEL_ID = "app-q-trendyol"
DEFAULT_GENERAL_MODEL_ID = "app-q-asure"
DEFAULT_ORCHESTRATOR_MODEL_ID = "app-q-kizagan-e4b"


def strip_visible_reasoning(content: str) -> str:
    """Remove visible reasoning blocks emitted by some local reasoning models."""
    without_tags = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
    return without_tags.strip()


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
        if "Defne" in system:
            system = f"{INTAKE_POLICY}\n\n{system}"
        else:
            system = f"{APP_Q_GENERATION_POLICY}\n\n{system}"
            
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
            
        final_response = strip_visible_reasoning(content)
        
        # 3. Save to Cache (Skip for Defne/Intake wizard)
        if "Defne" not in system:
            save_to_semantic_cache(prompt, final_response, system)
        
        return final_response

    @observe(as_type="generation")
    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        self.last_model_id = self.model_id
        if "Defne" in system:
            system = f"{INTAKE_POLICY}\n\n{system}"
        else:
            system = f"{APP_Q_GENERATION_POLICY}\n\n{system}"
            
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
                    full_response = []
                    for line in response:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line.decode("utf-8"))
                            content = data.get("message", {}).get("content", "")
                            if content:
                                if "<think>" in content:
                                    inside_think_block = True
                                    content = content.split("<think>")[0]
                                elif "</think>" in content:
                                    inside_think_block = False
                                    content = content.split("</think>")[-1]
                                
                                if not inside_think_block and content:
                                    full_response.append(content)
                                    yield content
                        except json.JSONDecodeError:
                            continue
                    
                    # 3. Save full streamed response to cache (Skip for Defne)
                    final_text = "".join(full_response).strip()
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
        except Exception:
            pass


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
        if "Defne" in system:
            system = f"{INTAKE_POLICY}\\n\\n{system}"
        else:
            system = f"{APP_Q_GENERATION_POLICY}\\n\\n{system}"
            
        if "Defne" not in system:
            cached_response = check_semantic_cache(prompt, system)
            if cached_response:
                return cached_response
                
<<<<<<< HEAD
                # 3. Save full streamed response to cache (Skip for Defne)
                final_text = "".join(full_response).strip()
                if final_text and "Defne" not in system:
                    save_to_semantic_cache(prompt, final_text, system)
        except (TimeoutError, urllib.error.URLError) as exc:
            raise ModelProviderError(
                "Ollama yanıt vermedi. Ollama'nın çalıştığından ve modelin yüklü olduğundan emin olun."
            ) from exc
=======
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
        final_response = strip_visible_reasoning(content)
        
        if "Defne" not in system:
            save_to_semantic_cache(prompt, final_response, system)
            
        return final_response

    @observe(as_type="generation")
    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
        self.last_model_id = self.model_id
        if "Defne" in system:
            system = f"{INTAKE_POLICY}\\n\\n{system}"
        else:
            system = f"{APP_Q_GENERATION_POLICY}\\n\\n{system}"
            
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
        
        full_response = []
        inside_think = False
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                if "<think>" in content:
                    inside_think = True
                    content = content.split("<think>")[0]
                elif "</think>" in content:
                    inside_think = False
                    content = content.split("</think>")[-1]
                    
                if not inside_think and content:
                    full_response.append(content)
                    yield content
                    
        final_text = "".join(full_response).strip()
        if final_text and "Defne" not in system:
            save_to_semantic_cache(prompt, final_text, system)

    def free_memory(self) -> None:
        pass
>>>>>>> c2e56332200a78c21e940108bc5898a678c72903


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
        
        # 1. Defne / Intake Wizard / Persona Generation -> Orchestrator (Kizagan)
        if "defne" in system_lower or "araştırma mimarı" in system_lower or "intake" in system_lower or "persona üretici" in system_lower or "persona json" in system_lower:
            return self.orchestrator_model_id, self.orchestrator_model
            
        # 2. Synthesis / Rapor Sentezi / B2B Analist -> Analyst (Asure-12B)
        if "sentez" in system_lower or "rapor sentezi" in system_lower or "b2b analist" in system_lower or "sentezleyici" in system_lower or "sentez" in prompt_lower or "analiz" in prompt_lower:
            return self.b2b_model_id, self.b2b_model
            
        # 3. Persona Interview / Roleplay -> Actor (Trendyol-8B)
        return self.b2c_model_id, self.b2c_model

<<<<<<< HEAD
    def generate(self, system: str, prompt: str) -> str:
        model_id, model = self.choose_model(system, prompt)
        answer = model.generate(system, prompt)
        self.last_model_id = model_id
        return answer

    def generate_stream(self, system: str, prompt: str):
=======
    def generate(self, system: str, prompt: str, response_format: str | None = None) -> str:
        model_id, model = self.choose_model(system, prompt)
        answer = model.generate(system, prompt, response_format=response_format)
        self.last_model_id = model_id
        return answer

    def generate_stream(self, system: str, prompt: str, response_format: str | None = None):
>>>>>>> c2e56332200a78c21e940108bc5898a678c72903
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
    except Exception:
        return []


def get_model_provider(provider: str | None = None) -> ResearchModel:
    selected_provider = provider or os.getenv("APP_MODEL_PROVIDER", "ollama-router")
    
    # Try fetching model configurations from SQLite dynamically
    try:
        from .database import get_system_config
        config = get_system_config()
    except Exception:
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

