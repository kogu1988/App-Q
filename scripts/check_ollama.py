from __future__ import annotations

import os

from packages.research_engine.providers import ModelProviderError, OllamaResearchModel


def main() -> None:
    model_id = os.getenv("APP_MODEL_ID", "sentetik-tr-motor")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = OllamaResearchModel(model_id=model_id, base_url=base_url, timeout_seconds=30)
    try:
        answer = model.generate(
            system="Kısa cevap veren lokal model bağlantı testisin.",
            prompt="Tek cümleyle Türkçe cevap ver: App-Q lokal model bağlantısı çalışıyor mu?",
        )
    except ModelProviderError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
    print(answer)


if __name__ == "__main__":
    main()
