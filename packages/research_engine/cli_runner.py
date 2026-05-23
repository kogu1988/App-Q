import os
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from packages.research_engine.models import ResearchBrief, PanelRole
from packages.research_engine.workflow import build_research_plan, generate_personas
from packages.research_engine.analytics import synthesize_report
from packages.research_engine.providers import get_model_provider
from packages.research_engine.privacy import PrivacyMasker, PrivacyResearchModelWrapper
from packages.research_engine.quality import enrich_report_json
from packages.research_engine.reporting import render_markdown

from dataclasses import asdict

STUDIES_DIR = Path(os.getenv("APP_Q_STUDIES_DIR", ROOT / "data" / "studies"))

def run_simulation(study_id: str):
    study_path = STUDIES_DIR / study_id
    if not study_path.exists():
        raise FileNotFoundError(f"Study path not found: {study_path}")

    # Load brief and roles
    brief_data = json.loads((study_path / "brief.json").read_text(encoding="utf-8"))
    roles_data = json.loads((study_path / "roles.json").read_text(encoding="utf-8"))

    # Convert to models
    brief = ResearchBrief(
        title=brief_data["title"],
        market=brief_data.get("market", "Türkiye"),
        category=brief_data.get("category", ""),
        idea=brief_data["idea"],
        target_users=brief_data.get("target_users", []),
        questions=brief_data.get("questions", []),
        competitors=brief_data.get("competitors", []),
        expected_price=brief_data.get("expected_price"),
        sales_channel=brief_data.get("sales_channel"),
        success_metric=brief_data.get("success_metric"),
    )

    panel_roles = [
        PanelRole(role=str(r["role"]), why=str(r["why"]), count=int(r["count"]))
        for r in roles_data if r.get("selected") and int(r.get("count", 0)) > 0
    ]

    model = get_model_provider()
    wrapped_model = PrivacyResearchModelWrapper(model, PrivacyMasker([]))

    print("[CLI] Building research plan...")
    plan = build_research_plan(brief, panel_roles or None)

    print("[CLI] Generating personas...")
    personas = generate_personas(brief, plan, wrapped_model)

    print("[CLI] Running interviews (headless)...")
    # We do a blocking run instead of streaming for the CLI runner
    # We can just import and use a blocking interview function or consume the stream
    from packages.research_engine.workflow import run_interviews_stream
    stream = run_interviews_stream(brief, personas, wrapped_model, plan.interview_script)
    interviews = []
    try:
        for _ in stream:
            pass # consume stream
    except StopIteration as e:
        interviews = e.value

    print("[CLI] Synthesizing report...")
    report = synthesize_report(brief, plan, personas, interviews)
    report_json = enrich_report_json(asdict(report))
    report_markdown = render_markdown(report)

    # Save initial files
    (study_path / "report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")
    (study_path / "report.md").write_text(report_markdown, encoding="utf-8")
    
    print("[CLI] Generating High-Quality PDF via Fastify Playwright engine...")
    import requests
    pdf_path = study_path / "report.pdf"
    try:
        res = requests.post("http://localhost:3000/api/report/pdf", json=report_json, timeout=120)
        if res.status_code == 200:
            pdf_path.write_bytes(res.content)
            print(f"[CLI] PDF successfully generated at {pdf_path}")
        else:
            print(f"[CLI] PDF generation failed with status {res.status_code}")
    except Exception as e:
        print(f"[CLI] Could not connect to Fastify backend for PDF generation: {e}")
    
    # Update metadata
    metadata_path = study_path / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["has_report"] = True
        if pdf_path.exists():
            metadata["has_pdf"] = True
            metadata["pdf_status"] = "generated"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        
    print("[CLI] Simulation completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study_id", required=True, help="Study ID to run simulation for")
    args = parser.parse_args()
    
    run_simulation(args.study_id)
