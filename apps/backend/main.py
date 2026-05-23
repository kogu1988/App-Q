from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import sys
import os
from pathlib import Path

# Yapısal loglama — tüm paketler bu konfigürasyonı kullanır
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from apps.backend.routers import admin, client

# — Rate Limiter —
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="App-Q Backend API",
    description="FastAPI backend for App-Q Research Engine",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — production'da ALLOWED_ORIGINS env var zorunlu
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(client.router, prefix="/api/client", tags=["Client"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": _app_env}
