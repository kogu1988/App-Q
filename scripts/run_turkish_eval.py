from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.providers import ModelProviderError, get_model_provider


EVAL_PATH = ROOT / "data" / "evals" / "turkish_quality_eval.jsonl"
OUTPUT_PATH = ROOT / "data" / "outputs" / "turkish-eval-results.jsonl"


SYSTEM_PROMPT = (
    "App-Q için Türkçe pazar araştırması personası veya rapor sentezleyicisi gibi cevap ver. "
    "Doğal Türkçe kullan, jenerik asistan tonu kullanma, belirsizliği saklama."
)


def load_evals() -> list[dict]:
    rows: list[dict] = []
    with EVAL_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    provider = os.getenv("APP_MODEL_PROVIDER", "mock")
    model_id = os.getenv("APP_MODEL_ID", "mock-research-model")
    model = get_model_provider(provider)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = load_evals()
    with OUTPUT_PATH.open("w", encoding="utf-8") as output:
        for row in rows:
            try:
                answer = model.generate(SYSTEM_PROMPT, row["prompt"])
                error = None
            except ModelProviderError as exc:
                answer = ""
                error = str(exc)

            result = {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "provider": provider,
                "model_id": model_id,
                "eval_id": row["id"],
                "category": row["category"],
                "prompt": row["prompt"],
                "rubric": row["rubric"],
                "answer": answer,
                "error": error,
                "manual_scores": {
                    "turkish_naturalness": None,
                    "persona_consistency": None,
                    "insight_usefulness": None,
                    "specificity": None,
                    "hallucination_risk": None,
                    "report_readiness": None,
                },
                "review_note": "",
            }
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            status = "ERROR" if error else "OK"
            print(f"{status} {row['id']}")

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
