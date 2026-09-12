"""Paddle Billing entegrasyonu — checkout, portal, abonelik durumu ve webhook (P0-2).

Paddle merchant of record'dur: ödemeyi alır, aboneliği oluşturur ve webhook ile
Clarere'ye bildirir. Bu router'da manuel abonelik OLUŞTURULMAZ.

Webhook endpoint'i auth kullanmaz; güvenlik imza doğrulaması (HMAC-SHA256) iledir.
"""
from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from packages.research_engine.database import (
    already_processed_paddle_event,
    get_client_by_username,
    get_current_username,
    get_last_event_occurred_at,
    record_paddle_event,
)
from packages.research_engine.paddle_config import PADDLE_ENV, is_configured, price_for_plan
from packages.research_engine.paddle_webhooks import (
    handle_paddle_event,
    verify_paddle_signature,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_PADDLE_API_BASE = (
    "https://sandbox-api.paddle.com" if PADDLE_ENV == "sandbox" else "https://api.paddle.com"
)


class CheckoutRequest(BaseModel):
    plan: str
    cycle: str = "monthly"


def _paddle_api_base() -> str:
    env = (os.getenv("PADDLE_ENV", PADDLE_ENV) or "sandbox").strip().lower()
    return "https://sandbox-api.paddle.com" if env == "sandbox" else "https://api.paddle.com"


@router.post("/checkout")
def start_checkout(
    data: CheckoutRequest,
    x_username: str | None = Depends(get_current_username),
):
    """Frontend'in Paddle.js overlay'ini açması için price_id + müşteri bilgisi döner.

    Paddle.js checkout tamamlandığında aboneliği kendisi oluşturur; backend'de
    manuel abonelik yaratılmaz.
    """
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")

    if data.plan == "Enterprise":
        raise HTTPException(
            status_code=400,
            detail="Enterprise planı satış görüşmesi ile aktive edilir. hiclarere@clarere.com ile iletişime geçin.",
        )

    price_id = price_for_plan(data.plan, data.cycle)
    if not price_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "Ödeme altyapısı bu plan için yapılandırılmamış. "
                "hiclarere@clarere.com ile iletişime geçin."
            ),
        )

    client = get_client_by_username(x_username) or {}
    return {
        "price_id": price_id,
        "plan": data.plan,
        "cycle": data.cycle,
        "customer_email": client.get("email") or "",
        "paddle_customer_id": client.get("paddle_customer_id") or "",
        "environment": (os.getenv("PADDLE_ENV", PADDLE_ENV) or "sandbox").strip().lower(),
    }


@router.get("/subscription")
def get_subscription(
    x_username: str | None = Depends(get_current_username),
):
    """Kullanıcının önbelleğe alınmış abonelik durumunu döner."""
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")
    client = get_client_by_username(x_username) or {}
    return {
        "plan": client.get("plan_type") or "Free",
        "status": client.get("subscription_status") or "none",
        "current_period_end": (
            client["current_period_end"].isoformat()
            if client.get("current_period_end")
            else None
        ),
        "paddle_customer_id": client.get("paddle_customer_id") or "",
    }


@router.get("/portal")
def get_customer_portal(
    x_username: str | None = Depends(get_current_username),
):
    """Paddle müşteri portalı oturum linki (abonelik yönetimi, iptal, kart güncelleme)."""
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")

    api_key = os.getenv("PADDLE_API_KEY", "").strip()
    client = get_client_by_username(x_username) or {}
    customer_id = client.get("paddle_customer_id")

    if not api_key or not customer_id:
        raise HTTPException(
            status_code=503,
            detail="Abonelik yönetimi için Paddle yapılandırması eksik.",
        )

    try:
        import requests

        resp = requests.post(
            f"{_paddle_api_base()}/customers/{customer_id}/portal-sessions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={},
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json().get("data", {})
        portals = (payload.get("urls") or {})
        url = (portals.get("general") or {}).get("overview") or portals.get("general")
        if not url:
            raise ValueError("Portal URL missing in Paddle response")
        return {"url": url}
    except Exception:
        logger.error("Paddle portal oturumu oluşturulamadı (user=%s)", x_username, exc_info=True)
        raise HTTPException(status_code=502, detail="Abonelik portalı açılamadı. Lütfen tekrar deneyin.")


@router.post("/webhook")
async def paddle_webhook(request: Request):
    """Paddle webhook alıcısı.

    Güvenlik: imza doğrulaması. Auth header KULLANILMAZ.
    Sıra: imza → idempotensi → sıralama → işleme.
    """
    raw = await request.body()  # RAW — parse edip yeniden serialize ETME
    signature = request.headers.get("paddle-signature", "")
    secret = os.getenv("PADDLE_WEBHOOK_SECRET", "")

    if not secret:
        logger.error("PADDLE_WEBHOOK_SECRET ayarlanmamış — webhook reddedildi.")
        raise HTTPException(status_code=503, detail="Webhook yapılandırılmamış.")

    if not verify_paddle_signature(raw, signature, secret):
        logger.warning("Paddle webhook: geçersiz imza.")
        raise HTTPException(status_code=400, detail="invalid signature")

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid payload")

    notification_id = event.get("notification_id") or ""
    event_type = event.get("event_type") or ""
    occurred_at = event.get("occurred_at") or ""
    data = event.get("data") or {}

    # 1) İdempotensi — Paddle at-least-once teslim eder
    if already_processed_paddle_event(notification_id):
        return {"status": "duplicate_ignored"}

    # 2) Sıralama — aynı türde daha yeni bir event işlendiyse eskisini yok say
    try:
        last_ts = get_last_event_occurred_at(event_type)
        if last_ts and occurred_at:
            from datetime import datetime, timezone

            incoming = datetime.fromisoformat(str(occurred_at).replace("Z", "+00:00"))
            if incoming.tzinfo is None:
                incoming = incoming.replace(tzinfo=timezone.utc)
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            if incoming < last_ts:
                return {"status": "stale_ignored"}
    except Exception:
        logger.debug("Paddle sıralama kontrolü atlandı.", exc_info=True)

    # 3) İşle
    try:
        handle_paddle_event(event_type, data, event)
        record_paddle_event(notification_id, event_type, occurred_at, event, "ok")
    except Exception as e:
        try:
            record_paddle_event(notification_id, event_type, occurred_at, event, "error", str(e)[:500])
        except Exception:
            logger.debug("Paddle event hata kaydı yazılamadı.", exc_info=True)
        logger.exception("Paddle webhook işlenemedi: %s", notification_id)
        raise HTTPException(status_code=500, detail="processing failed")  # Paddle retry etsin

    return {"status": "ok"}
