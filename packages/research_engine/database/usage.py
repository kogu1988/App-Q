"""Token kullanimi ve maliyet muhasebesi (refactor R5-5)."""
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

from .clients import check_and_reset_period
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


def record_token_usage(
    username: str,
    model_id: str,
    operation: str,
    usage: dict | None = None,
    study_id: str | None = None,
) -> None:
    """Bir LLM çağrısının token kullanımını ve tahmini maliyetini kaydeder.

    Muhasebe hatası araştırmayı ÇÖKERTMEZ — yalnızca loglanır (fail-safe).
    operation: intake | interview | synthesis | copilot | followup | match
    """
    if not username or username == "anonymous":
        return
    usage = usage or {}
    try:
        prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", 0) or 0)
        cache_hit = int(usage.get("prompt_cache_hit_tokens", 0) or 0)

        from ..pricing_table import calculate_cost
        cost = calculate_cost(
            model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_hit_tokens=cache_hit,
            cache_miss_tokens=usage.get("prompt_cache_miss_tokens"),
        )

        with get_db() as (conn, cur):
            cur.execute(
                """
                INSERT INTO token_usage
                  (username, study_id, model_id, operation, prompt_tokens,
                   completion_tokens, total_tokens, cache_hit_tokens, cost_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username, study_id, model_id, operation,
                    prompt_tokens, completion_tokens, total_tokens, cache_hit, cost,
                ),
            )
            cur.execute(
                "UPDATE clients SET tokens_used = COALESCE(tokens_used, 0) + %s WHERE username = %s",
                (total_tokens, username),
            )
    except Exception:
        logger.warning(
            "Token muhasebesi kaydedilemedi (user=%s, op=%s).",
            username, operation, exc_info=True,
        )



def check_token_budget(username: str | None, plan_type: str | None = None) -> tuple[bool, int, int]:
    """Dönemsel token bütçesi kontrolü.

    Returns: (izin_var, kullanilan, limit)
    - Kullanıcı yok / anonim ise izin verilir (kota DB'de yoksa engellemeyiz).
    - limit 9_999_999 ise sınırsız sayılır.
    """
    if not username:
        return True, 0, 0
    try:
        with get_db() as (conn, cur):
            check_and_reset_period(username, conn, cur)
            cur.execute(
                "SELECT plan_type, tokens_used, max_tokens FROM clients WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
            if not row:
                return True, 0, 0
            used = row["tokens_used"] or 0
            limit = row["max_tokens"] or 0
            if limit <= 0:
                from ..plan_config import get_plan_config
                limit = get_plan_config(row["plan_type"] or plan_type or "Free").get("max_tokens", 0)
            if limit >= _UNLIMITED_TOKENS:
                return True, used, limit
            return used < limit, used, limit
    except Exception:
        logger.warning("Token bütçesi kontrol edilemedi (user=%s).", username, exc_info=True)
        return True, 0, 0  # fail-open: muhasebe hatası kullanıcıyı engellemez


def get_token_usage_summary(
    username: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> list[dict]:
    """Kullanıcı bazlı token + maliyet özeti (admin görünürlüğü)."""
    with get_db() as (conn, cur):
        where: list[str] = []
        params: list = []
        if username:
            where.append("username = %s")
            params.append(username)
        if start:
            where.append("created_at >= %s")
            params.append(start)
        if end:
            where.append("created_at <= %s")
            params.append(end)
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        cur.execute(
            f"""
            SELECT username,
                   COUNT(*)                         AS calls,
                   COALESCE(SUM(prompt_tokens), 0)     AS prompt_tokens,
                   COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                   COALESCE(SUM(total_tokens), 0)      AS total_tokens,
                   COALESCE(SUM(cache_hit_tokens), 0)  AS cache_hit_tokens,
                   COALESCE(SUM(cost_usd), 0)          AS cost_usd
            FROM token_usage
            {clause}
            GROUP BY username
            ORDER BY cost_usd DESC
            """,
            tuple(params),
        )
        return [dict(r) for r in cur.fetchall()]


# — P0-2: Paddle abonelik işlemleri —


