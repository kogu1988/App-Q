from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.models import ResearchBrief
from packages.research_engine.providers import get_model_provider
from packages.research_engine.reporting import render_markdown
from packages.research_engine.workflow import run_research


def main() -> None:
    sample_path = ROOT / "data" / "samples" / "first-brief.json"
    brief_data = json.loads(sample_path.read_text(encoding="utf-8"))
    brief = ResearchBrief(**brief_data)
    provider = os.getenv("APP_MODEL_PROVIDER", "mock")
    report = run_research(brief, get_model_provider(provider))

    output_path = ROOT / "data" / "outputs" / "sample-report.json"
    output_path.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")

    markdown_path = ROOT / "data" / "outputs" / "sample-report.md"
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {markdown_path}")


if __name__ == "__main__":
    main()
