from __future__ import annotations

import os
import subprocess
from pathlib import Path


def browser_candidates() -> list[Path]:
    env_path = os.getenv("APP_Q_BROWSER_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))

    program_files = [os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)"), os.getenv("LOCALAPPDATA")]
    for root in [item for item in program_files if item]:
        base = Path(root)
        candidates.extend(
            [
                base / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                base / "Google" / "Chrome" / "Application" / "chrome.exe",
                base / "Chromium" / "Application" / "chrome.exe",
            ]
        )
    return candidates


def find_browser() -> Path | None:
    for candidate in browser_candidates():
        if candidate.exists():
            return candidate
    return None


def export_html_to_pdf(html_path: Path, pdf_path: Path, browser_path: Path | None = None) -> Path:
    html_path = html_path.resolve()
    pdf_path = pdf_path.resolve()
    browser = browser_path or find_browser()
    if not browser:
        raise RuntimeError(
            "Chrome/Edge bulunamadi. APP_Q_BROWSER_PATH ile msedge.exe veya chrome.exe yolunu belirt."
        )
    if not html_path.exists():
        raise FileNotFoundError(f"HTML raporu bulunamadi: {html_path}")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={pdf_path}",
        str(html_path.as_uri()),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if completed.returncode != 0 or not pdf_path.exists():
        stderr = completed.stderr.strip() or completed.stdout.strip() or "Bilinmeyen PDF export hatasi."
        raise RuntimeError(stderr)
    return pdf_path
