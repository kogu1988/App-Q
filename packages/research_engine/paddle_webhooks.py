"""Paddle webhook imza doğrulama ve event işleme (P0-2).

İmza algoritması Paddle tarafından dökümante edilmiştir:
    signed_payload = "<ts>:<raw_body>"
    h1             = HMAC-SHA256(signed_payload, PADDLE_WEBHOOK_SECRET)

Header formatı: `ts=<unix_ts>;h1=<hex_digest>`

Kritik: `raw_body` parse edilmeden, **olduğu gibi** kullanılmalıdır. JSON parse edip
yeniden serialize etmek (tek bir boşluk bile) imzayı bozar.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time

logger = logging.getLogger(__name__)


def verify_paddle_signature(
    raw_body: bytes,
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 5,
) -> bool:
    """Paddle-Signature header'ını doğrular. Geçerliyse True."""
    if not secret or not signature_header:
        return False

    parts: dict[str, str] = {}
    for chunk in signature_header.split(";"):
        if "=" in chunk:
            key, value = chunk.split("=", 1)
            parts[key.strip()] = value.strip()

    ts = parts.get("ts")
    h1 = parts.get("h1")
    if not ts or not h1:
        return False

    try:
        if abs(int(time.time()) - int(ts)) > tolerance_seconds:  # replay koruması
            return False
    except (TypeError, ValueError):
        return False

    signed_payload = ts.encode("utf-8") + b":" + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, h1)


def _extract_price_ids(data: dict) -> list[str]:
    """subscription/transaction data'sından price ID'lerini çıkarır."""
    price_ids: list[str] = []
    for item in (data.get("items") or []):
        price = item.get("price") or {}
        price_id = price.get("id") or item.get("price_id")
        if price_id:
            price_ids.append(price_id)
    return price_ids


def _username_from_data(data: dict) -> str | None:
    """custom_data.clarere_username — e-posta değişebileceği için güvenilir bağ."""
    custom = data.get("custom_data") or {}
    username = (custom.get("clarere_username") or "").strip()
    return username or None


def _customer_id_from_data(data: dict) -> str | None:
    return data.get("customer_id") or (data.get("customer") or {}).get("id")


def _plan_from_data(data: dict) -> str | None:
    from .paddle_config import plan_for_price

    for price_id in _extract_price_ids(data):
        mapped = plan_for_price(price_id)
        if mapped:
            return mapped[0]
    return None


def _has_one_time_item(data: dict) -> bool:
    from .paddle_config import plan_for_price

    for price_id in _extract_price_ids(data):
        mapped = plan_for_price(price_id)
        if mapped and mapped[1] == "one_time":
            return True
    return False


def handle_paddle_event(event_type: str, data: dict, event: dict) -> None:
    """Bir Paddle event'ini Clarere abonelik durumuna yansıtır.

    Not: `subscription.updated`; yenileme, upgrade, downgrade ve iptal-planlama
    dahil tüm abonelik değişikliklerini kapsar (ayrı event gerekmez).
    """
    from .database import (
        add_flex_credits,
        find_client_by_paddle_subscription,
        update_client_subscription,
    )

    username = _username_from_data(data)
    customer_id = _customer_id_from_data(data)

    if event_type.startswith("subscription."):
        sub_id = data.get("id")
        if not username and sub_id:
            client = find_client_by_paddle_subscription(sub_id)
            username = client.get("username") if client else None

        if not username:
            logger.warning("Paddle %s: kullanıcı eşleşmedi (sub=%s)", event_type, sub_id)
            return

        status = (data.get("status") or "").lower()
        period_end = ((data.get("current_billing_period") or {}).get("ends_at"))

        if event_type == "subscription.canceled" or status in {"paused", "canceled"}:
            update_client_subscription(
                username, plan_type="Free", status=status or "canceled",
                subscription_id=sub_id, customer_id=customer_id, period_end=period_end,
            )
            return

        plan = _plan_from_data(data)
        if not plan:
            logger.warning("Paddle %s: price→plan eşleşmedi, plan korunuyor (sub=%s)", event_type, sub_id)
        update_client_subscription(
            username, plan_type=plan, status=status or "active",
            subscription_id=sub_id, customer_id=customer_id, period_end=period_end,
        )
        return

    if event_type == "transaction.completed":
        if not username:
            return
        if _has_one_time_item(data):
            # Flex / Research Pack — tek seferlik 3 araştırma hakkı
            add_flex_credits(username, credits=3)
        return

    if event_type in {"customer.created", "customer.updated"}:
        if username and customer_id:
            update_client_subscription(username, customer_id=customer_id)
        return

    logger.debug("Paddle event yok sayıldı: %s", event_type)


def cancel_paddle_subscription(subscription_id: str) -> bool:
    """Paddle aboneliğini hemen iptal eder (best-effort).

    KVKK hesap silme akışında çağrılır — kullanıcı ücretlendirilmeye devam etmesin.
    Anahtar yoksa veya istek başarısızsa False döner (istisna fırlatmaz).
    """
    import os

    import requests

    if not subscription_id:
        return False

    api_key = (os.getenv("PADDLE_API_KEY") or "").strip()
    if not api_key:
        logger.warning("PADDLE_API_KEY yok — abonelik iptal edilemedi: %s", subscription_id)
        return False

    env = (os.getenv("PADDLE_ENV", "sandbox") or "sandbox").strip().lower()
    base = "https://sandbox-api.paddle.com" if env == "sandbox" else "https://api.paddle.com"

    try:
        resp = requests.post(
            f"{base}/subscriptions/{subscription_id}/cancel",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"effective_from": "immediately"},
            timeout=15,
        )
        if resp.status_code >= 400:
            logger.error(
                "Paddle abonelik iptali başarısız (%s): %s", resp.status_code, resp.text[:200]
            )
            return False
        logger.info("Paddle aboneliği iptal edildi: %s", subscription_id)
        return True
    except Exception:
        logger.warning("Paddle iptal isteği başarısız: %s", subscription_id, exc_info=True)
        return False
