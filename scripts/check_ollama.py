from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.providers import ModelProviderError, OllamaResearchModel


def main() -> None:
    model_id = os.getenv("APP_MODEL_ID", "sentetik-tr-motor")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = OllamaResearchModel(model_id=model_id, base_url=base_url, timeout_seconds=30)
    try:
        answer = model.generate(
            system="Sadece bağlantı testi yap. Türkçe cevap ver. En fazla 8 kelime kullan.",
            prompt="App-Q lokal model bağlantısı çalışıyor mu? Sadece 'Bağlantı çalışıyor.' yaz.",
        )
    except ModelProviderError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
    print(answer)


if __name__ == "__main__":
    main()
