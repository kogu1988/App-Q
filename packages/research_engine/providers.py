from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from .models import ResearchModel
from .caching import check_semantic_cache, save_to_semantic_cache


APP_Q_GENERATION_POLICY = """
App-Q üretim politikası:
- Türkçe cevap ver.
- Meta açıklama yapma; "persona şöyle düşünür" deme.
- Persona sorularında birinci tekil şahısla, gerçek kullanıcı gibi konuş.
- Somut Türkiye pazarı bağlamı kullan: fiyat, taksit, kargo, komisyon, bütçe, güven, KVKK.
- Araştırmacıyı memnun etmeye çalışma; zayıf noktaları açıkça söyle.
- Gizli muhakeme, <think> bloğu veya iç analiz yazma.
- Gereksiz maddeleme yapma; kısa ve doğrudan cevap ver.
"""

INTAKE_POLICY = """
App-Q Asistan (Defne) politikası:
- Türkçe, kibar, empatik ve destekleyici bir tonda cevap ver.
- Kullanıcıyı asla azarlama, eksiklerini yüzüne vurma veya eleştirme ("göz ardı edemeyiz", "belirsiz zemine oturtamayız" gibi sert ifadeler KULLANMA).
- Kullanıcı bir konuda (örn. rakipler) fikri olmadığını veya eksik olduğunu belirtirse, onu rahatlat ve 2-3 jenerik, mantıklı varsayım/örnek üreterek süreci ilerlet.
- Kısa, net ve yapıcı ol. Gereksiz maddeleme yapma.
- Gizli muhakeme, <think> bloğu veya iç analiz yazma.
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

    def generate(self, system: str, prompt: str) -> str:
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

    def generate_stream(self, system: str, prompt: str):
        answer = self.generate(system, prompt)
        words = answer.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


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

    def generate(self, system: str, prompt: str) -> str:
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
        request = urllib.request.Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
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

    def generate_stream(self, system: str, prompt: str):
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
        request = urllib.request.Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
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

    def generate(self, system: str, prompt: str) -> str:
        model_id, model = self.choose_model(system, prompt)
        answer = model.generate(system, prompt)
        self.last_model_id = model_id
        return answer

    def generate_stream(self, system: str, prompt: str):
        model_id, model = self.choose_model(system, prompt)
        self.last_model_id = model_id
        for chunk in model.generate_stream(system, prompt):
            yield chunk


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

