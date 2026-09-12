"""Launch Clarere — tek tikla baslatma.

Kullanim:
    python launch.py          -> Docker stack (onerilen; prod benzeri)
                                 Frontend: http://localhost:4001
                                 Tam stack (Caddy): http://localhost:8080
    python launch.py --dev    -> Host dev modu (hizli backend reload)
                                 Backend: http://127.0.0.1:4000  (uvicorn --reload)
                                 Frontend: http://localhost:4001 (next dev)

Docker modu, production ile ayni imajlari kullanir (`docker-compose.prod.yml` +
`docker-compose.local.yml` override). Host dev modu icin Docker stack kapali olmalidir
(4001 portu paylasilir).
"""
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

os.chdir(os.path.dirname(os.path.abspath(__file__)))

COMPOSE = [
    "docker", "compose",
    "-f", "docker-compose.prod.yml",
    "-f", "docker-compose.local.yml",
]

FRONTEND_URL = "http://localhost:4001"
STACK_URL = "http://localhost:8080"


# ---------------------------------------------------------------------------
# Yardimcilar
# ---------------------------------------------------------------------------

def _run(args, check=True):
    return subprocess.run(args, check=check)


def _http_ok(url, timeout=3):
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        return r.status in (200, 304, 307, 308)
    except Exception:
        return False


def _wait_http(url, attempts, delay, label):
    for _ in range(attempts):
        if _http_ok(url):
            print(f"  OK  ({label})")
            return True
        time.sleep(delay)
    return False


def _docker_running():
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=15,
        )
        return r.returncode == 0
    except Exception:
        return False


def _kill_port(port):
    """Windows: belirtilen portu dinleyen sureci kapat (host dev modu icin)."""
    subprocess.run(
        f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}.*LISTENING\') '
        f"do taskkill /F /PID %a 2>nul",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# ---------------------------------------------------------------------------
# Docker modu (varsayilan)
# ---------------------------------------------------------------------------

def launch_docker():
    print("\n[Docker] Stack baslatiliyor (prod + local override)...")
    print("         (ilk derleme birkac dakika surebilir)\n")

    _run(COMPOSE + ["up", "-d", "--build"])

    print("\n[Kontrol] Servisler hazir mi?")
    # API + frontend (Caddy uzerinden) hazir olana kadar bekle
    api_ok = _wait_http(f"{STACK_URL}/health", attempts=30, delay=2, label="API /health")
    fe_ok = _wait_http(FRONTEND_URL, attempts=30, delay=2, label="Frontend :4001")

    if not (api_ok and fe_ok):
        print("\n  UYARI: Bazi servisler henuz hazir degil.")
        print("  Durum icin: docker compose -f docker-compose.prod.yml -f docker-compose.local.yml ps")
        print("  Loglar icin: docker compose -f docker-compose.prod.yml -f docker-compose.local.yml logs -f")

    print(f"""
{'=' * 46}
  CLARERE HAZIR (Docker)

  Frontend : {FRONTEND_URL}
  Tam stack: {STACK_URL}
  API docs : {STACK_URL}/docs
{'=' * 46}

  Durdurmak icin:
    docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down

  Test kullanicilari: free / flex / starter / pro / enterprise
""")

    webbrowser.open(FRONTEND_URL)


# ---------------------------------------------------------------------------
# Host dev modu (--dev)
# ---------------------------------------------------------------------------

def launch_dev():
    print("\n[Dev] Host modu — Docker stack kapali olmali (4001 paylasilir).\n")

    if not _docker_running():
        print("  HATA: Docker calismiyor. PostgreSQL + Redis gerekli.")
        sys.exit(1)

    print("[Docker] PostgreSQL + Redis (host dev)...")
    _run(["docker", "compose", "up", "-d", "postgres", "redis"])
    time.sleep(3)
    print("  OK")

    print("\n[Backend] Port 4000 (uvicorn --reload)...")
    _kill_port(4000)
    time.sleep(1)
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "apps.backend.main:app",
         "--host", "127.0.0.1", "--port", "4000", "--reload"],
    )
    if not _wait_http("http://127.0.0.1:4000/health", attempts=20, delay=1, label="Backend"):
        print("  HATA: Backend baslamadi!")
        api.kill()
        sys.exit(1)

    print("\n[Frontend] Port 4001 (next dev)...")
    _kill_port(4001)
    os.chdir("apps/frontend")
    if not os.path.exists("node_modules"):
        print("  npm install...")
        _run(["cmd", "/c", "npm install"])
    fe = subprocess.Popen(["cmd", "/c", "npx next dev -p 4001"])
    os.chdir("../..")

    print("  Bekleniyor (ilk derleme ~30sn)...")
    if not _wait_http(FRONTEND_URL, attempts=30, delay=2, label="Frontend"):
        print("  UYARI: Frontend henuz hazir degil, derleniyor olabilir.")

    print(f"""
{'=' * 46}
  CLARERE HAZIR (Host dev)

  Frontend : {FRONTEND_URL}
  API      : http://127.0.0.1:4000/docs
{'=' * 46}

  Cikmak icin Ctrl+C
""")
    webbrowser.open(FRONTEND_URL)

    try:
        api.wait()
    except KeyboardInterrupt:
        print("\nKapatiliyor...")
        fe.terminate()
        api.terminate()
        print("Tamam.")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 46)
    print("  Clarere — Baslatiliyor")
    print("=" * 46)

    if not _docker_running():
        print("\nHATA: Docker calismiyor. Docker Desktop'i baslatip tekrar deneyin.")
        sys.exit(1)

    if "--dev" in sys.argv:
        launch_dev()
    else:
        launch_docker()
