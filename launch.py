"""Launch Clarere — persistent background servers.
Run: python launch.py
"""
import subprocess, sys, time, webbrowser, os, urllib.request, json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_docker(container_name):
    """Return True if Docker container is running and healthy."""
    r = subprocess.run(
        ["docker", "ps", "--filter", f"name={container_name}", "--filter", "status=running",
         "--format", "ok"],
        capture_output=True, text=True
    )
    return "ok" in r.stdout

def cmd(cmd_str):
    """Run a command via cmd.exe, show output."""
    return subprocess.run(["cmd", "/c", cmd_str], check=True)

print("=" * 40)
print("  Clarere — Baslatiliyor")
print("=" * 40)

# ── Docker ──
print("\n[Docker] PostgreSQL...")
if not check_docker("clarere-postgres"):
    print("  Baslatiliyor...")
    cmd("docker compose up -d postgres")
    for _ in range(15):
        time.sleep(2)
        if check_docker("clarere-postgres"):
            break
        print("  Bekleniyor...")
    if not check_docker("clarere-postgres"):
        print("  HATA: PostgreSQL baslamadi!")
        sys.exit(1)
print("  OK")

print("[Docker] Redis...")
if not check_docker("clarere-redis"):
    print("  Baslatiliyor...")
    cmd("docker compose up -d redis")
    for _ in range(10):
        time.sleep(2)
        if check_docker("clarere-redis"):
            break
    if not check_docker("clarere-redis"):
        print("  HATA: Redis baslamadi!")
        sys.exit(1)
print("  OK")

# ── Backend ──
print("\n[Backend] Port 4000...")
# Kill any existing process on port 4000 (cleanup) — --reload spawns child, so use port-based kill
subprocess.run("for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :4000.*LISTENING') do taskkill /F /PID %a 2>nul",
               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(1)  # Port serbest kalsın

api = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "apps.backend.main:app", "--host", "127.0.0.1", "--port", "4000", "--reload"],
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
)

for _ in range(10):
    time.sleep(1)
    try:
        r = urllib.request.urlopen("http://127.0.0.1:4000/health", timeout=2)
        data = json.loads(r.read())
        if data.get("status") == "ok":
            print(f"  OK ({data['env']})")
            break
    except:
        pass
else:
    print("  HATA: Backend baslamadi!")
    print(api.stderr.read().decode(errors="replace")[-500:])
    api.kill()
    sys.exit(1)

# ── Frontend ──
print("\n[Frontend] Port 4001...")
# Kill any existing process on port 4001
subprocess.run("for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :4001.*LISTENING') do taskkill /F /PID %a 2>nul",
               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

os.chdir("apps/frontend")
if not os.path.exists("node_modules"):
    print("  npm install...")
    cmd("npm install")

fe = subprocess.Popen(
    ["cmd", "/c", "npx next dev -p 4001"],
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
)

print("  Bekleniyor (ilk derleme 30sn surer)...")
for i in range(30):
    time.sleep(2)
    try:
        r = urllib.request.urlopen("http://127.0.0.1:4001", timeout=2)
        if r.status in (200, 304, 307, 308):
            print("  OK")
            break
    except:
        pass
else:
    print("  UYARI: Frontend henuz hazir degil. Derleniyor olabilir, bekleyin...")
    # Don't fail — Next.js may still be compiling

os.chdir("../..")

# ── Ready ──
print(f"""
{'=' * 40}
  CLARERE HAZIR

  Frontend : http://localhost:4001
  API      : http://localhost:4000/docs
{'=' * 40}

Test kullanicilari: free (Free) / pro (Pro)
Cikmak icin Ctrl+C
""")

webbrowser.open("http://localhost:4001")

try:
    api.wait()
except KeyboardInterrupt:
    print("\nKapatiliyor...")
    fe.terminate()
    api.terminate()
    print("Tamam.")
