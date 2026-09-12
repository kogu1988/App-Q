"""Paddle fiyat ↔ Clarere planı eşlemesi (SSOT).

Paddle Dashboard'da oluşturulan her fiyatın ID'si ilgili `PADDLE_PRICE_*` ortam
değişkenine yazılır. Plan adları `plan_config.PLAN_CONFIG` ile birebir tutarlı olmalıdır.

Örnek .env:
    PADDLE_ENV=sandbox
    PADDLE_PRICE_FLEX=pri_...
    PADDLE_PRICE_STARTER_MONTHLY=pri_...
    PADDLE_PRICE_STARTER_ANNUAL=pri_...
    PADDLE_PRICE_PRO_MONTHLY=pri_...
    PADDLE_PRICE_PRO_ANNUAL=pri_...
"""
from __future__ import annotations

import os

PADDLE_ENV = (os.getenv("PADDLE_ENV", "sandbox") or "sandbox").strip().lower()

# (env değişkeni, clarere planı, faturalama döngüsü)
_PRICE_ROWS: list[tuple[str, str, str]] = [
    ("PADDLE_PRICE_FLEX", "Flex", "one_time"),
    ("PADDLE_PRICE_STARTER_MONTHLY", "Starter", "monthly"),
    ("PADDLE_PRICE_STARTER_ANNUAL", "Starter", "annual"),
    ("PADDLE_PRICE_PRO_MONTHLY", "Pro", "monthly"),
    ("PADDLE_PRICE_PRO_ANNUAL", "Pro", "annual"),
]


def build_price_map() -> dict[str, tuple[str, str]]:
    """price_id → (plan, cycle). Boş env değerleri atlanır."""
    mapping: dict[str, tuple[str, str]] = {}
    for env_key, plan, cycle in _PRICE_ROWS:
        price_id = (os.getenv(env_key) or "").strip()
        if price_id:
            mapping[price_id] = (plan, cycle)
    return mapping


def plan_for_price(price_id: str) -> tuple[str, str] | None:
    """Paddle price ID'sinden (plan, cycle) döner; eşleşme yoksa None."""
    return build_price_map().get((price_id or "").strip())


def price_for_plan(plan: str, cycle: str) -> str | None:
    """Plan + döngü için yapılandırılmış Paddle price ID'sini döner."""
    for env_key, row_plan, row_cycle in _PRICE_ROWS:
        if row_plan == plan and row_cycle == cycle:
            return (os.getenv(env_key) or "").strip() or None
    return None


def is_configured() -> bool:
    """En az bir fiyat eşlemesi tanımlı mı?"""
    return bool(build_price_map())
