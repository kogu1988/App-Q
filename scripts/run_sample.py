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
    from packages.research_engine.workflow import build_research_plan, generate_personas, run_interviews_batch
    from packages.research_engine.analytics import synthesize_report

    model = get_model_provider("flash")

    # 1. Plan
    plan = build_research_plan(brief)
    # 2. Personas
    personas = generate_personas(brief)[:5]
    # 3. Batch interviews
    interviews = run_interviews_batch(brief, personas, model, plan.interview_script)
    # 4. Synthesize report
    report = synthesize_report(brief, plan, personas, interviews)

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
