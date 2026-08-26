"""Clarere Demo Çalışması Üretici — sunum/kurumsal demo için.

Tam akışı (brief → plan → persona → batch mülakat → sentez) çalıştırır,
raporu DB'ye kaydeder ve tarayıcıda gösterilebilir bir çalışma oluşturur.

Kullanım:
    python scripts/generate_demo_study.py --username free
    python scripts/generate_demo_study.py --username pro --ab-test
    python scripts/generate_demo_study.py --brief data/samples/first-brief.json

Gereksinim: Postgres + Redis ayakta (start.bat), DEEPSEEK_API_KEY .env'de.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.analytics import synthesize_report
from packages.research_engine.database import current_tenant_var, save_study
from packages.research_engine.models import ResearchBrief
from packages.research_engine.providers import get_model_provider
from packages.research_engine.reporting import render_markdown
from packages.research_engine.workflow import build_research_plan, generate_personas, run_interviews_batch

DEFAULT_BRIEF = {
    "title": "Clarere — Sentetik Pazar Araştırması Servisi",
    "market": "Türkiye",
    "category": "B2B SaaS / Araştırma",
    "idea": (
        "KOBİ ve e-ticaret satıcılarının ürün fikirlerini, fiyatlamasını ve pazarlama "
        "mesajlarını gerçek kullanıcı görüşmesi yapmadan test eden yapay zeka destekli "
        "sentetik persona araştırma platformu. Defne asistanı brief'i toplar, Rogers×SES "
        "matrisiyle kalibre edilmiş personalar mülakat yapar, rapor kanıt zinciri ve "
        "karar katmanıyla sunulur."
    ),
    "target_users": [
        "Trendyol ve Hepsiburada satıcıları",
        "Küçük e-ticaret markaları",
        "Ajanslar",
        "Ürün yöneticileri",
    ],
    "competitors": [
        "Klasik pazar araştırma ajansları",
        "ChatGPT ile manuel araştırma",
        "Anket araçları",
    ],
    "expected_price": "Rapor başı 3.000 - 5.000 TL pilot hizmet; aylık 2.690 TL abonelik",
    "sales_channel": "LinkedIn üzerinden ajanslar ve e-ticaret kurucularına satış",
    "success_metric": "Müşterinin raporu karar toplantısında kullanması ve ikinci test satın alması",
    "questions": [
        "Bu servis hangi pain pointleri çözer?",
        "Hangi fiyat aralığı kabul edilebilir olur?",
        "Kullanıcılar çıktılara ne kadar güvenir?",
        "Satın alma önündeki itirazlar nelerdir?",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Clarere demo çalışması üret")
    parser.add_argument("--username", default="free", help="Çalışmayı kaydedecek kullanıcı")
    parser.add_argument("--study-id", default="", help="Özel çalışma ID (boşsa otomatik)")
    parser.add_argument("--brief", default="", help="Brief JSON yolu (boşsa yerleşik demo brief)")
    parser.add_argument("--ab-test", action="store_true", help="A/B varyant testi ekle")
    args = parser.parse_args()

    # ── 1. Brief ──
    if args.brief:
        brief_path = ROOT / args.brief
        brief_data = json.loads(brief_path.read_text(encoding="utf-8"))
    else:
        brief_data = dict(DEFAULT_BRIEF)

    if args.ab_test:
        brief_data["variant_a"] = "Hızla ürün fikrini test et, 15 dakikada rapor al"
        brief_data["variant_b"] = "Pazar fırsatını bilimsel yöntemle doğrula, kararını ver"

    brief = ResearchBrief(**brief_data)
    study_id = args.study_id or f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    model = get_model_provider("flash")

    print("1/5 Araştırma planı oluşturuluyor...")
    plan = build_research_plan(brief)

    print("2/5 Persona paneli üretiliyor (5 stance × SES)...")
    personas = generate_personas(brief)[:5]

    print("3/5 Batch mülakatlar çalıştırılıyor (DeepSeek Flash)...")
    interviews = run_interviews_batch(brief, personas, model, plan.interview_script)
    answered = sum(1 for iv in interviews for t in iv.turns if t.answer != "[Yanıt alınamadı]")
    total = sum(len(iv.turns) for iv in interviews)
    print(f"   → {answered}/{total} yanıt alındı")

    print("4/5 Sentez raporu üretiliyor...")
    report = synthesize_report(brief, plan, personas, interviews)
    report_dict = asdict(report)
    report_dict["report_markdown"] = render_markdown(report)

    print("5/5 DB'ye kaydediliyor...")
    metadata = {
        "id": study_id,
        "title": brief.title,
        "market": brief.market,
        "category": brief.category,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "archived": False,
        "has_report": True,
        "has_pdf": False,
        "pdf_status": "not_generated",
        "pdf_error": "",
        "quality_score": None,
        "quality_grade": None,
        "quality_summary": None,
        "brief_hash": None,
        "roles_hash": None,
        "cache_status": None,
        "created_by": args.username,
    }
    payload = {
        "brief": asdict(brief),
        "roles": [],
        "plan": asdict(plan),
        "personas": [asdict(p) for p in personas],
        "interviews": [asdict(iv) for iv in interviews],
        "report_json": report_dict,
        "report_markdown": report_dict["report_markdown"],
        "script": [asdict(q) for q in plan.interview_script],
    }

    token = current_tenant_var.set(args.username)
    try:
        save_study(metadata, payload)
        # Kanıt zincirini research_findings/research_evidence tablolarına yaz
        from packages.research_engine.database import save_findings
        if report.enhanced_findings:
            save_findings(study_id, report.enhanced_findings)
            print(f"   → {len(report.enhanced_findings)} bulgu + kanıt zinciri kaydedildi")
    finally:
        current_tenant_var.reset(token)

    # ── Özet ──
    print()
    print("=" * 56)
    print("  DEMO ÇALIŞMA HAZIR")
    print("=" * 56)
    print(f"  ID       : {study_id}")
    print(f"  URL      : http://localhost:4001/client/studies/{study_id}")
    print(f"  Kullanıcı: {args.username}")
    print(f"  Persona  : {len(personas)} ({', '.join(p.stance for p in personas)})")
    print(f"  Yanıt    : {answered}/{total}")
    print(f"  Bulgu    : {len(report.findings)}")
    print(f"  Karar    : {len(getattr(report, 'decision_items', []))}")
    print("=" * 56)


if __name__ == "__main__":
    main()
