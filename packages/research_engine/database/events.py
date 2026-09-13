"""Urun (KPI) event'leri (refactor R5-6)."""
from __future__ import annotations

import json
import logging
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from pgvector.psycopg2 import register_vector
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor

from .connection import (
    APP_DB_PASS,
    APP_DB_USER,
    PG_DB,
    PG_HOST,
    PG_PASS,
    PG_PORT,
    PG_USER,
    current_tenant_var,
    get_admin_db,
    get_current_username,
    get_db,
    logger,
)


def record_product_event(
    event_name: str,
    username: str | None = None,
    study_id: str | None = None,
    props: dict | None = None,
) -> None:
    """Ürün KPI event'i kaydeder (funnel ölçümü).

    Fail-safe: ölçüm hatası ürün akışını ÇÖKERTMEZ.
    """
    if not event_name:
        return
    try:
        import json as _json

        with get_db() as (conn, cur):
            cur.execute(
                "INSERT INTO product_events (event_name, username, study_id, props) VALUES (%s, %s, %s, %s)",
                (event_name, username or "", study_id or "", _json.dumps(props or {}, ensure_ascii=False)),
            )
    except Exception:
        logger.debug("Ürün event'i kaydedilemedi (%s).", event_name, exc_info=True)


def get_product_event_summary(days: int = 30) -> dict:
    """Son N gündeki event sayılarını ve temel funnel oranlarını döner."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT event_name, COUNT(*) AS cnt
            FROM product_events
            WHERE created_at >= NOW() - (%s || ' days')::interval
            GROUP BY event_name
            ORDER BY cnt DESC
            """,
            (str(int(days)),),
        )
        counts = {row["event_name"]: int(row["cnt"]) for row in cur.fetchall()}

    def _pct(numerator: int, denominator: int) -> float:
        if not denominator:
            return 0.0
        return round(min(numerator / denominator, 1.0), 3)

    started = counts.get("research_started", 0)
    completed = counts.get("research_completed", 0)
    synthesized = counts.get("report_synthesized", 0)
    upgrade = counts.get("upgrade_cta_viewed", 0)
    return {
        "days": days,
        "counts": counts,
        "research_completion_rate": _pct(completed, started),
        "report_rate": _pct(synthesized, completed),
        "upgrade_cta_rate": _pct(upgrade, started),
    }


