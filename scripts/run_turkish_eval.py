from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.providers import ModelProviderError, get_model_provider


EVAL_PATH = ROOT / "data" / "evals" / "turkish_quality_eval.jsonl"
OUTPUT_DIR = ROOT / "data" / "outputs" / "evals"


SYSTEM_PROMPT = (
    "App-Q için Türkçe pazar araştırması personası veya rapor sentezleyicisi gibi cevap ver. "
    "Persona senaryolarında birinci tekil şahıs kullan. Doğal Türkçe kullan, jenerik asistan tonu kullanma, "
    "belirsizliği saklama ve meta açıklama yapma."
)


def load_evals() -> list[dict]:
    rows: list[dict] = []
    with EVAL_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()


def main() -> None:
    model_id = os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash")
    model = get_model_provider("flash")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{safe_name(model_id)}.jsonl"

    rows = load_evals()
    with output_path.open("w", encoding="utf-8") as output:
        for row in rows:
            started = time.perf_counter()
            try:
                answer = model.generate(SYSTEM_PROMPT, row["prompt"])
                error = None
            except ModelProviderError as exc:
                answer = ""
                error = str(exc)
            elapsed_ms = round((time.perf_counter() - started) * 1000)

            result = {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "provider": provider,
                "model_id": model_id,
                "eval_id": row["id"],
                "category": row["category"],
                "prompt": row["prompt"],
                "rubric": row["rubric"],
                "answer": answer,
                "elapsed_ms": elapsed_ms,
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
            print(f"{status} {row['id']} {elapsed_ms}ms")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
