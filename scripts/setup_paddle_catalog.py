"""Paddle kataloğunu (ürün + fiyat + webhook destination) idempotent olarak kurar.

Kullanım (anahtar `.env` içinde olmalı — sohbete/commit'e YAZMA):

    # .env
    PADDLE_ENV=sandbox
    PADDLE_API_KEY=pdl_sdbx_...
    PADDLE_WEBHOOK_URL=https://<tunnel>.example.com/api/billing/webhook   # opsiyonel

    python scripts/setup_paddle_catalog.py

Yaptıkları:
  1. "Clarere — ..." ürünlerini oluşturur (varsa atlar)
  2. Her ürün için fiyatları oluşturur (varsa atlar)
  3. PADDLE_WEBHOOK_URL verilmişse notification destination oluşturur
  4. Elde edilen ID'leri `.env` için hazır blok olarak stdout'a basar

Notlar:
  - Idempotent: tekrar çalıştırmak yeni kopya üretmez (isimle eşleştirir).
  - Fiyatlar KDV hariçtir; Paddle merchant of record olarak vergiyi üstlenir.
  - Yıllık fiyat = yıllık TOPLAM tutardır (aylık eşdeğer × 12).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Proje kökünü sys.path'e ekle (scripts/ altından çalıştırılabilir)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

# (product_name, [ (price_env, price_name, amount_cents, billing_cycle) ])
# billing_cycle None → tek seferlik
CATALOG = [
    (
        "Clarere — Starter",
        "Starter planı: 10 araştırma/ay, 10 persona, PDF rapor, Van Westendorp PSM.",
        [
            ("PADDLE_PRICE_STARTER_MONTHLY", "Starter (monthly)", 6900, {"interval": "month", "frequency": 1}),
            ("PADDLE_PRICE_STARTER_ANNUAL", "Starter (annual)", 66000, {"interval": "year", "frequency": 1}),
        ],
    ),
    (
        "Clarere — Pro",
        "Pro plan: sınırsız araştırma, White-label, B2B modu, Marka Sağlığı analizi.",
        [
            ("PADDLE_PRICE_PRO_MONTHLY", "Pro (monthly)", 16900, {"interval": "month", "frequency": 1}),
            ("PADDLE_PRICE_PRO_ANNUAL", "Pro (annual)", 162000, {"interval": "year", "frequency": 1}),
        ],
    ),
    (
        "Clarere — Research Pack",
        "Tek seferlik araştırma paketi: 3 araştırma hakkı (Flex).",
        [
            ("PADDLE_PRICE_FLEX", "Research Pack (one-time)", 4900, None),
        ],
    ),
]

SUBSCRIBED_EVENTS = [
    "subscription.created",
    "subscription.updated",
    "subscription.canceled",
    "subscription.past_due",
    "transaction.completed",
    "customer.created",
    "customer.updated",
]

NOTIFICATION_DESCRIPTION = "Clarere — webhook (backend /api/billing/webhook)"


def _base_url() -> str:
    env = (os.getenv("PADDLE_ENV", "sandbox") or "sandbox").strip().lower()
    return "https://sandbox-api.paddle.com" if env == "sandbox" else "https://api.paddle.com"


def _headers() -> dict:
    key = os.getenv("PADDLE_API_KEY", "").strip()
    if not key:
        raise SystemExit("HATA: .env içinde PADDLE_API_KEY yok.")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _get(path: str, params: dict | None = None) -> dict:
    resp = requests.get(f"{_base_url()}{path}", headers=_headers(), params=params or {}, timeout=30)
    if resp.status_code >= 400:
        raise SystemExit(f"GET {path} başarısız ({resp.status_code}): {resp.text[:400]}")
    return resp.json()


def _post(path: str, payload: dict) -> dict:
    resp = requests.post(f"{_base_url()}{path}", headers=_headers(), json=payload, timeout=30)
    if resp.status_code >= 400:
        raise SystemExit(f"POST {path} başarısız ({resp.status_code}): {resp.text[:400]}")
    return resp.json()


def find_or_create_product(name: str, description: str) -> str:
    data = _get("/products", {"per_page": 200}).get("data", [])
    for product in data:
        if product.get("name") == name:
            print(f"  = ürün mevcut: {name} ({product['id']})")
            return product["id"]
    created = _post(
        "/products",
        {"name": name, "tax_category": "standard", "description": description},
    )["data"]
    print(f"  + ürün oluşturuldu: {name} ({created['id']})")
    return created["id"]


def find_or_create_price(
    product_id: str,
    env_var: str,
    price_name: str,
    amount_cents: int,
    billing_cycle: dict | None,
) -> tuple[str, str]:
    prices = _get("/prices", {"product_id": product_id, "per_page": 200}).get("data", [])
    for price in prices:
        if price.get("name") == price_name:
            print(f"    = fiyat mevcut: {price_name} ({price['id']})")
            return env_var, price["id"]

    payload: dict = {
        "product_id": product_id,
        "name": price_name,
        "description": price_name,
        "unit_price": {"amount": str(amount_cents), "currency_code": "USD"},
    }
    if billing_cycle:
        payload["billing_cycle"] = billing_cycle

    created = _post("/prices", payload)["data"]
    print(f"    + fiyat oluşturuldu: {price_name} ({created['id']})")
    return env_var, created["id"]


def find_or_create_destination(webhook_url: str) -> str | None:
    settings = _get("/notification-settings", {"per_page": 200}).get("data", [])
    for setting in settings:
        if setting.get("destination") == webhook_url:
            print(f"  = destination mevcut ({setting['id']})")
            secret = setting.get("endpoint_secret_key")
            if not secret:
                detail = _get(f"/notification-settings/{setting['id']}").get("data", {})
                secret = detail.get("endpoint_secret_key")
            return secret

    payload = {
        "description": NOTIFICATION_DESCRIPTION,
        "type": "url",
        "destination": webhook_url,
        "traffic_source": "all",  # simulator + gerçek event
        "subscribed_events": SUBSCRIBED_EVENTS,
    }
    created = _post("/notification-settings", payload)["data"]
    print(f"  + destination oluşturuldu: {created['id']}")
    return created.get("endpoint_secret_key")


def main() -> None:
    env_name = (os.getenv("PADDLE_ENV", "sandbox") or "sandbox").strip().lower()
    print(f"Paddle katalog kurulumu — ortam: {env_name} ({_base_url()})")

    price_ids: list[tuple[str, str]] = []
    for product_name, description, prices in CATALOG:
        product_id = find_or_create_product(product_name, description)
        for env_var, price_name, amount, cycle in prices:
            price_ids.append(
                find_or_create_price(product_id, env_var, price_name, amount, cycle)
            )

    webhook_url = (os.getenv("PADDLE_WEBHOOK_URL", "") or "").strip()
    secret = find_or_create_destination(webhook_url) if webhook_url else None

    print("\n" + "=" * 60)
    print("# .env dosyasına eklenecek satırlar")
    print("=" * 60)
    print(f"PADDLE_ENV={env_name}")
    for env_var, price_id in price_ids:
        print(f"{env_var}={price_id}")
    if secret:
        print(f"PADDLE_WEBHOOK_SECRET={secret}")
    else:
        print("# PADDLE_WEBHOOK_SECRET: PADDLE_WEBHOOK_URL verilmedi (destination oluşturulmadı)")
    print("=" * 60)
    if secret:
        print("UYARI: endpoint_secret_key yalnızca oluşturma anında gösterilir — hemen kaydedin.")


if __name__ == "__main__":
    main()
