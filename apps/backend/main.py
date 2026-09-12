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
from contextlib import asynccontextmanager

# .env dosyasini yukle — subprocess ile baslatilsa bile calisir
from dotenv import load_dotenv
load_dotenv()

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
from apps.backend.routers import admin, client, auth, billing  # noqa: E402
from packages.research_engine.routers import stream  # noqa: E402
from packages.research_engine.database import current_tenant_var  # noqa: E402

# — Rate Limiter —
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü.

    Senkron endpoint'ler (LLM + DB çağrıları) FastAPI tarafından anyio threadpool'una
    taşınır. Varsayılan 40 thread eşzamanlı araştırmalar için yetersiz kalabildiğinden
    limit burada yapılandırılabilir hale getirilir (P0-1).
    """
    try:
        import anyio

        limiter_ = anyio.to_thread.current_default_thread_limiter()
        limiter_.total_tokens = int(os.getenv("THREADPOOL_SIZE", "64"))
        logger.info("Threadpool boyutu: %s", limiter_.total_tokens)
    except Exception:  # anyio sürüm farkı — kritik değil
        logger.warning("Threadpool boyutu ayarlanamadı, varsayılan kullanılıyor.", exc_info=True)
    yield


app = FastAPI(
    title="Clarere Backend API",
    description="FastAPI backend for Clarere Research Engine",
    version="1.0.0",
    lifespan=lifespan,
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
        "Örnek: ALLOWED_ORIGINS=https://clarere.com"
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

# — Sentry (opsiyonel) — SENTRY_DSN yoksa tamamen devre dışı
_sentry_dsn = (os.getenv("SENTRY_DSN") or "").strip()
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            environment=_app_env,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            integrations=[FastApiIntegration()],
            send_default_pii=False,  # KVKK: kişisel veri gönderilmez
        )
        logger.info("Sentry aktif (env=%s)", _app_env)
    except ImportError:
        logger.warning("SENTRY_DSN verildi ama sentry-sdk kurulu değil — Sentry devre dışı.")
    except Exception:
        logger.warning("Sentry başlatılamadı.", exc_info=True)

@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    """
    Tenant'ı belirler:
      1. JWT: `Authorization: Bearer <token>` → doğrula → `sub` claim'i
      2. Fallback: `X-Username` header (YALNIZCA development)
    Production'da JWT zorunludur. Tenant bilgisi RLS için kullanılır.
    """
    username = None

    # 1. JWT doğrulaması
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        from packages.research_engine.jwt_utils import extract_username
        token = auth_header[7:].strip()
        if token:
            username = extract_username(token)

    # 2. Fallback: X-Username header — YALNIZCA development (production'da JWT zorunlu)
    if not username and _app_env != "production":
        username = request.headers.get("x-username")

    current_tenant_var.set(username)
    response = await call_next(request)
    return response

# --- STANDART REST ROUTER KAYITLARI ---
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(client.router, prefix="/api/client", tags=["Client"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])

# --- REALTİME STREAMING & WEBSOCKET ROUTER KAYDI (MÜHÜRLENEN KATMAN) ---
# stream.router kendi içinde "/api/v1/stream" prefix'ini ve "/ws" soket yollarını barındırır.
app.include_router(stream.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": _app_env}
