#!/usr/bin/env python
"""Bağımsız benchmark — rapor üretici (S8-3/S8-5/S8-7, kısmi).

Toplanan (uzman anotasyonlu) benchmark vakalarını çalıştırır, RFI metriklerini
ve varsa iki değerlendirici arası **Cohen's kappa** uyumunu hesaplar.

Uydurma veri üretmez: yalnızca `data/evals/benchmark/cases/` altındaki gerçek
vakaları ölçer. Anotasyonsuz vakalar "beklemede" olarak raporlanır.

Kullanım:
    python scripts/benchmark_report.py
    python scripts/benchmark_report.py --write-summary
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.benchmark import (  # noqa: E402
    calculate_rfi,
    case_is_annotated,
    cohens_kappa,
    summarize_rfi,
    validate_case,
)

BENCH_DIR = ROOT / "data" / "evals" / "benchmark"
CASES_DIR = BENCH_DIR / "cases"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="RFI benchmark raporu")
    parser.add_argument("--write-summary", action="store_true", help="summary.json yaz")
    args = parser.parse_args()

    case_paths = [p for p in sorted(CASES_DIR.glob("*.json")) if not p.name.startswith("_")]
    if not case_paths:
        print("[bilgi] Henüz benchmark vakası yok (yalnızca şablon mevcut).")
        print(f"        Vaka üretmek için: python scripts/benchmark_collect.py --study-id <id>")
        print(f"        Dizin: {CASES_DIR}")
        return 0

    results: list[dict] = []
    pending = 0
    invalid = 0

    print("=" * 68)
    print("  Clarere RFI — Bağımsız Benchmark Raporu")
    print("=" * 68)

    for case_path in case_paths:
        case = _load_json(case_path)
        problems = validate_case(case)
        if problems:
            invalid += 1
            print(f"\n[HATA] {case_path.name}: {', '.join(problems)}")
            continue

        if not case_is_annotated(case):
            pending += 1
            print(f"\n⏳ {case.get('name', case.get('id'))} — uzman anotasyonu bekliyor")
            continue

        rfi = calculate_rfi(
            case.get("llm_findings", []),
            case.get("human_findings", []),
            case.get("critical") or None,
            case.get("contradictions") or None,
        )
        results.append(rfi)
        print(f"\n📋 {case.get('name', case.get('id'))}")
        print(f"   Overall RFI:     {rfi['overall_rfi']:.2f}  ({rfi['grade']})")
        print(f"   Theme Recall:    {rfi['theme_recall']:.0%}")
        print(f"   Theme Precision: {rfi['theme_precision']:.0%}")
        print(f"   Critical Recall: {rfi['critical_recall']:.0%}")
        print(f"   False Positive:  {rfi['false_positive_rate']:.0%}")

    summary = summarize_rfi(results)

    print(f"\n{'=' * 68}")
    print(f"  Değerlendirilen: {summary['cases']} · Anotasyon bekleyen: {pending} · Geçersiz: {invalid}")
    if results:
        print(f"  Ortalama RFI: {summary['mean_rfi']:.2f}  (min {summary['min_rfi']:.2f} / max {summary['max_rfi']:.2f})")
        print(f"  Ortalama metrikler: {summary['mean_metrics']}")

    # İki değerlendirici uyumu (varsa)
    eval_a = BENCH_DIR / "evaluator_a.json"
    eval_b = BENCH_DIR / "evaluator_b.json"
    if eval_a.exists() and eval_b.exists():
        labels_a = _load_json(eval_a)
        labels_b = _load_json(eval_b)
        kappa = cohens_kappa(list(labels_a), list(labels_b))
        if kappa is not None:
            print(f"  Değerlendiriciler arası uyum (Cohen's kappa): {kappa:.3f}")
            summary["cohens_kappa"] = kappa
        else:
            print("  [uyarı] Değerlendirici etiketleri karşılaştırılamadı (uzunluk/boşluk).")
    else:
        print("  [bilgi] İki değerlendirici etiketi yok (evaluator_a.json / evaluator_b.json).")

    print("=" * 68)
    print("  NOT: Bu rapor bir iddia üretmez; yalnızca ölçüm özetidir.")

    if args.write_summary:
        out = BENCH_DIR / "summary.json"
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [ok] Özet yazıldı: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
