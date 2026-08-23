"""
Clarere RFI Benchmark Runner
Usage: python scripts/run_benchmark.py

Bu script, benchmark verilerini yükler ve her senaryo için
Research Fidelity Index (RFI) metriklerini hesaplar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Windows konsolunda UTF-8 çıktısı için (emoji/ok karakterleri cp1254'te çöker)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure the project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.benchmark import calculate_rfi


BENCHMARK_PATH = ROOT / "data" / "evals" / "rfi_benchmark_samples.json"


def main() -> None:
    if not BENCHMARK_PATH.exists():
        print(f"[HATA] Benchmark verisi bulunamadı: {BENCHMARK_PATH}")
        sys.exit(1)

    with BENCHMARK_PATH.open("r", encoding="utf-8") as f:
        samples = json.load(f)

    print("=" * 65)
    print("  Clarere Research Fidelity Index (RFI) — Benchmark Sonuçları")
    print("=" * 65)

    all_rfi: list[float] = []

    for sample in samples:
        rfi = calculate_rfi(
            sample["llm_findings"],
            sample["human_findings"],
            sample.get("critical"),
            sample.get("contradictions"),
        )

        all_rfi.append(rfi["overall_rfi"])

        print(f"\n📋 {sample['name']}")
        print(f"   ID: {sample['id']}")
        print(f"   ─────────────────────────────────────────────")
        print(f"   Overall RFI:    {rfi['overall_rfi']:.2f}  ({rfi['grade']})")
        print(f"   Theme Recall:   {rfi['theme_recall']:.0%}")
        print(f"   Theme Precision:{rfi['theme_precision']:.0%}")
        print(f"   Critical Recall:{rfi['critical_recall']:.0%}")
        print(f"   False Positive: {rfi['false_positive_rate']:.0%}")
        print(f"   Segment Acc:    {rfi['segment_accuracy']:.0%}")
        if rfi["contradiction_detection"] is not None:
            print(f"   Contradiction:  {rfi['contradiction_detection']:.0%}")
        print(f"   → {rfi['interpretation']}")

    # Aggregate summary
    if all_rfi:
        avg_rfi = sum(all_rfi) / len(all_rfi)
        print(f"\n{'=' * 65}")
        print(f"  Toplam {len(samples)} senaryo değerlendirildi")
        print(f"  Ortalama RFI: {avg_rfi:.2f}")
        print(f"  En Düşük: {min(all_rfi):.2f}  |  En Yüksek: {max(all_rfi):.2f}")
        print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
