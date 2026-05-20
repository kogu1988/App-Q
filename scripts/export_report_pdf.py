from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.pdf_export import export_html_to_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Export an App-Q HTML report to PDF.")
    parser.add_argument("html_path", type=Path, help="Path to report.html")
    parser.add_argument("pdf_path", type=Path, nargs="?", help="Output PDF path")
    args = parser.parse_args()

    pdf_path = args.pdf_path or args.html_path.with_suffix(".pdf")
    output = export_html_to_pdf(args.html_path, pdf_path)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
