#!/usr/bin/env python
"""Tek komutla deterministik test çalıştırıcısı (S7-1).

Neden: Tam süit için Postgres'e erişim gerekir; yerelde DB host'a publish
edilmediğinden port-forward elle kuruluyordu. Bu script bunu otomatikleştirir.

Kullanım:
    python scripts/run_tests.py              # DB varsa/forward kurulabiliyorsa tam süit
    python scripts/run_tests.py --no-db      # DB'siz (CI-benzeri) çalıştırma
    python scripts/run_tests.py -- -k cache  # pytest'e ek argüman geçir

Davranış:
    1. DB erişilebilir mi kontrol eder.
    2. Değilse ve docker varsa geçici bir socat konteyneri ile port-forward kurar.
    3. pytest'i uygun ortam değişkenleriyle çalıştırır.
    4. Kurduğu forward'ı temizler.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import uuid

# Windows konsolu (cp1254 vb.) Unicode ok işaretlerini kodlayamayabilir —
# çıktıyı UTF-8'e zorla (aksi halde script çöker).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5433",
    "POSTGRES_DB": "clarere_db",
    "POSTGRES_USER": "clarere_user",
    "POSTGRES_PASSWORD": "clarere_password",
}

NETWORK = "clarere_default"
TARGET = "postgres:5432"
LOCAL_PORT = "5433"


def _port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _docker_available() -> bool:
    try:
        return subprocess.run(
            ["docker", "version"], capture_output=True, text=True, timeout=15
        ).returncode == 0
    except Exception:
        return False


def _start_forward() -> str | None:
    """socat ile geçici port-forward başlatır; konteyner adı döner (yoksa None)."""
    name = f"clarere-test-fwd-{uuid.uuid4().hex[:6]}"
    try:
        proc = subprocess.run(
            [
                "docker", "run", "--rm", "-d",
                "--name", name,
                "--network", NETWORK,
                "-p", f"{LOCAL_PORT}:5432",
                "alpine/socat",
                f"tcp-listen:5432,fork,reuseaddr",
                f"tcp-connect:{TARGET}",
            ],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            print(f"[test] Port-forward kurulamadı: {proc.stderr.strip()}", file=sys.stderr)
            return None
        return name
    except Exception as exc:  # pragma: no cover - ortama bağlı
        print(f"[test] Port-forward hatası: {exc}", file=sys.stderr)
        return None


def _stop_forward(name: str | None) -> None:
    if not name:
        return
    try:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Clarere deterministik test çalıştırıcısı")
    parser.add_argument("--no-db", action="store_true", help="Postgres olmadan çalıştır (CI-benzeri)")
    parser.add_argument("pytest_args", nargs="*", help="pytest'e geçilecek ek argümanlar")
    args = parser.parse_args()

    env = os.environ.copy()
    env["APP_ENV"] = env.get("APP_ENV", "development")
    forward = None

    if not args.no_db:
        if _port_open(DB_ENV["POSTGRES_HOST"], int(DB_ENV["POSTGRES_PORT"])):
            print("[test] Postgres zaten erişilebilir (localhost:5433).")
        elif _docker_available():
            print("[test] Port-forward kuruluyor (socat -> postgres:5432)...")
            forward = _start_forward()
            if forward:
                import time

                for _ in range(20):
                    if _port_open(DB_ENV["POSTGRES_HOST"], int(DB_ENV["POSTGRES_PORT"])):
                        break
                    time.sleep(0.5)
        else:
            print("[test] Docker yok; DB testleri atlanacak (skipped).", file=sys.stderr)

        if _port_open(DB_ENV["POSTGRES_HOST"], int(DB_ENV["POSTGRES_PORT"])):
            env.update(DB_ENV)

    cmd = [sys.executable, "-m", "pytest", "packages/research_engine/tests/", "-q", *args.pytest_args]
    print(f"[test] Komut: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, cwd=ROOT, env=env).returncode
    finally:
        _stop_forward(forward)


if __name__ == "__main__":
    raise SystemExit(main())
