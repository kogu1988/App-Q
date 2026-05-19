from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import ResearchModel


APP_Q_GENERATION_POLICY = """
App-Q üretim politikası:
- Türkçe cevap ver.
- Meta açıklama yapma; "persona şöyle düşünür" deme.
- Persona sorularında birinci tekil şahısla, gerçek kullanıcı gibi konuş.
- Somut Türkiye pazarı bağlamı kullan: fiyat, taksit, kargo, komisyon, bütçe, güven, KVKK.
- Araştırmacıyı memnun etmeye çalışma; zayıf noktaları açıkça söyle.
- Gereksiz maddeleme yapma; kısa ve doğrudan cevap ver.
"""


class ModelProviderError(RuntimeError):
    """Raised when a configured local model provider cannot respond."""


class MockResearchModel:
    """Deterministic provider used until a real LLM is connected."""

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


class OllamaResearchModel:
    """Local Ollama adapter using the chat API on localhost."""

    def __init__(
        self,
        model_id: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 120,
    ) -> None:
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def generate(self, system: str, prompt: str) -> str:
        system = f"{APP_Q_GENERATION_POLICY}\n\n{system}"
        payload = {
            "model": self.model_id,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096,
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
        except urllib.error.URLError as exc:
            raise ModelProviderError(
                "Ollama yanıt vermedi. Ollama'nın çalıştığından ve modelin yüklü olduğundan emin olun."
            ) from exc

        content = data.get("message", {}).get("content")
        if not content:
            raise ModelProviderError(f"Ollama boş yanıt döndürdü: {data}")
        return content.strip()


def get_model_provider(provider: str | None = None) -> ResearchModel:
    selected_provider = provider or os.getenv("APP_MODEL_PROVIDER", "mock")
    if selected_provider == "mock":
        return MockResearchModel()
    if selected_provider == "ollama":
        model_id = os.getenv("APP_MODEL_ID", "sentetik-tr-motor")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        timeout = int(os.getenv("APP_MODEL_TIMEOUT_SECONDS", "120"))
        return OllamaResearchModel(model_id=model_id, base_url=base_url, timeout_seconds=timeout)
    raise ValueError(f"Unsupported model provider: {selected_provider}")
