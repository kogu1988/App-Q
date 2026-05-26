from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import sys
import os
from pathlib import Path

# Yapısal loglama — tüm alt paketler ve LangGraph worker'ları bu ortak konfigürasyonu kullanır
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Routers import katmanı — stream router'ını asenkron ağ hattına ekliyoruz
from apps.backend.routers import admin, client  # noqa: E402
from packages.research_engine.routers import stream  # noqa: E402
from packages.research_engine.database import current_tenant_var  # noqa: E402

# — Rate Limiter —
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="App-Q Backend API",
    description="FastAPI backend for App-Q Research Engine with integrated SSE and WebSockets Spec",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    # Geliştirme ortamında print yerine standart asenkron logger kullanımı (KVKK maskeleme güvenliği için)
    logger.error(f"Validation Error: {exc.errors()} | Raw Body Payload: {body.decode(errors='ignore')}")
    return JSONResponse(
        status_code=422, 
        content={"detail": exc.errors(), "body": body.decode(errors="ignore")}
    )

# CORS Güvenlik Katmanı — production'da ALLOWED_ORIGINS env var zorunluluğu korunuyor
_app_env = os.getenv("APP_ENV", "development").lower()
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if _raw_origins:
    _allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
elif _app_env == "production":
    raise RuntimeError(
        "Production ortamında ALLOWED_ORIGINS env var zorunludur. "
        "Örnek: ALLOWED_ORIGINS=https://app.appq.io"
    )
else:
    _allowed_origins = ["*"]  # Sadece development

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_app_env != "development",  # Cannot be True if origins is ['*']
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    """
    Tüm request'lerde X-Username header'ını yakalayıp contextvars içine atar.
    Bu sayede database.py içindeki get_db() çağrıldığında RLS (Row-Level Security)
    için gerekli olan tenant bilgisi veritabanına aktarılır.
    """
    username = request.headers.get("x-username")
    if username:
        current_tenant_var.set(username)
    else:
        current_tenant_var.set(None)
    response = await call_next(request)
    return response

# --- STANDART REST ROUTER KAYITLARI ---
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(client.router, prefix="/api/client", tags=["Client"])

# --- REALTİME STREAMING & WEBSOCKET ROUTER KAYDI (MÜHÜRLENEN KATMAN) ---
# stream.router kendi içinde "/api/v1/stream" prefix'ini ve "/ws" soket yollarını barındırır.
app.include_router(stream.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": _app_env}
