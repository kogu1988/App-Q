"""JWT (HS256) token üretimi ve doğrulaması — stdlib tabanlı, ek bağımlılık yok.

Enterprise auth için temel: `create_token` imzalı bir access token üretir,
`verify_token` imzayı ve süreyi doğrular. HMAC karşılaştırması `compare_digest`
ile zamanlama saldırılarına karşı sabit-zamanlı yapılır.

Kullanım (sonraki adım: login endpoint + middleware):
  token = create_token("alice", secret)
  payload = verify_token(token, secret)  # {'sub': 'alice', 'iat':..., 'exp':...}
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

# Geliştirme varsayılanı — üretimde ASLA dönmemeli (bkz. get_jwt_secret).
_DEV_FALLBACK = "clarere-dev-secret-DO-NOT-USE-IN-PRODUCTION"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def get_jwt_secret() -> str:
    """JWT imzalama anahtarı.

    Production'da `JWT_SECRET` (veya `ADMIN_SECRET_KEY`) zorunludur; yoksa uygulama
    başlatılmaz. Development'ta eksikse bilinen bir varsayılana düşer ve uyarı loglanır.
    """
    secret = os.getenv("JWT_SECRET") or os.getenv("ADMIN_SECRET_KEY")
    app_env = os.getenv("APP_ENV", "development").lower()

    if not secret:
        if app_env == "production":
            raise RuntimeError(
                "JWT_SECRET ortam değişkeni production'da zorunludur. "
                'Üretmek için: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        logger.warning("JWT_SECRET ayarlanmamış — geliştirme varsayılanı kullanılıyor.")
        return _DEV_FALLBACK

    if app_env == "production" and len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET production'da en az 32 karakter olmalıdır "
            f"(mevcut: {len(secret)} karakter)."
        )

    return secret


def _default_token_expiry() -> int:
    """Token ömrü (saniye).

    Production'da güvenlik için 1 saat; dev/test ortamında ise 30 gün — böylece
    yerel denemelerde oturum süresinin dolmasıyla uğraşmak gerekmez.
    """
    if os.getenv("APP_ENV", "development").lower() == "production":
        return 3600
    return 30 * 24 * 3600


def create_token(username: str, secret: str | None = None, expires_in: int | None = None) -> str:
    """Bir kullanıcı adı için HS256 access token üretir."""
    secret = secret or get_jwt_secret()
    if expires_in is None:
        expires_in = _default_token_expiry()
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": username, "iat": now, "exp": now + expires_in}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def verify_token(token: str, secret: str | None = None) -> dict | None:
    """Token'ı doğrular; geçerliyse payload dict döner, değilse None."""
    secret = secret or get_jwt_secret()
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        return None
    signing_input = f"{header_b64}.{payload_b64}"
    expected = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    try:
        provided = _b64url_decode(signature_b64)
    except Exception:
        return None
    # Sabit-zamanlı imza karşılaştırması (timing attack koruması)
    if not hmac.compare_digest(provided, expected):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None
    if not isinstance(payload, dict) or "sub" not in payload:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


def extract_username(token: str, secret: str | None = None) -> str | None:
    """Token'dan kullanıcı adını çıkarır; geçersiz/süresi dolmuşsa None."""
    payload = verify_token(token, secret)
    return payload.get("sub") if payload else None
