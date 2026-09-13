#!/usr/bin/env python
"""Bağımsız benchmark — vaka toplayıcı (S8-1, kısmi).

Bir Clarere araştırma çalışmasının bulgularını alıp, uzman anotasyonu için
hazır bir benchmark vakası iskeleti üretir.

ÖNEMLİ: Bu script **uydurma veri üretmez.** Yalnızca Clarere'nin kendi
bulgularını dışa aktarır; `human_findings`, `critical`, `contradictions` ve
`synthetic_validation` alanlarını **insan/uzman** doldurur.

Kullanım:
    python scripts/benchmark_collect.py --study-id study_xxx
    python scripts/benchmark_collect.py --study-id study_xxx --name "BuddyNote"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "data" / "evals" / "benchmark" / "cases"


def _load_findings(study_id: str) -> list[dict]:
    """Çalışmanın bulgularını DB'den (yoksa report_json'dan) yükler."""
    from packages.research_engine.database import get_findings, load_study_payload

    findings = get_findings(study_id)
    if findings:
        return [
            {
                "title": f.get("title", ""),
                "summary": f.get("summary", ""),
                "category": f.get("category", ""),
                "confidence": f.get("confidence", 0.0),
            }
            for f in findings
        ]

    payload = load_study_payload(study_id, include_pdf=False)
    raw = payload.get("report_json")
    if not raw:
        return []
    report = json.loads(raw) if isinstance(raw, str) else raw
    source = report.get("enhanced_findings") or report.get("findings") or []
    return [
        {
            "title": (f.get("title") if isinstance(f, dict) else getattr(f, "title", "")),
            "summary": (f.get("summary") if isinstance(f, dict) else getattr(f, "summary", "")),
            "category": (f.get("category") if isinstance(f, dict) else getattr(f, "category", "")),
            "confidence": (f.get("confidence") if isinstance(f, dict) else getattr(f, "confidence", 0.0)),
        }
        for f in source
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark vakası iskeleti üretir")
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--category", default="")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    try:
        findings = _load_findings(args.study_id)
    except Exception as exc:
        print(f"[HATA] Bulgular yüklenemedi: {exc}", file=sys.stderr)
        return 1

    if not findings:
        print("[HATA] Çalışma için bulgu bulunamadı (sentez yapılmamış olabilir).", file=sys.stderr)
        return 1

    case = {
        "id": args.study_id,
        "name": args.name or args.study_id,
        "category": args.category,
        "brief": {},
        "llm_findings": findings,
        # ── Aşağıdaki alanlar UZMAN tarafından doldurulur ──
        "human_findings": [],
        "critical": [],
        "contradictions": [],
        "synthetic_validation": {
            "validated_by": [],
            "method": "real_user_interview | sales_data | field_study | none",
            "notes": "",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else (OUT_DIR / f"{args.study_id}.json")
    out_path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] Vaka iskeleti yazıldı: {out_path}")
    print(f"     Clarere bulgusu: {len(findings)}")
    print("     Sıradaki adım: `human_findings` / `critical` / `contradictions` alanlarını uzman doldursun.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
