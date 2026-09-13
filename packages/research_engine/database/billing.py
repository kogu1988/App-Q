"""Paddle webhook durumu, abonelik cache'i ve KVKK veri islemleri (refactor R5)."""
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


def already_processed_paddle_event(notification_id: str) -> bool:
    """Webhook idempotensi — aynı notification_id daha önce işlendi mi?"""
    if not notification_id:
        return False
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT 1 FROM paddle_events WHERE notification_id = %s", (notification_id,)
        )
        return cur.fetchone() is not None


def record_paddle_event(
    notification_id: str,
    event_type: str,
    occurred_at: str,
    payload: dict,
    status: str = "ok",
    error_message: str | None = None,
) -> None:
    """Webhook event'ini kaydeder (idempotensi + audit)."""
    import json as _json

    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO paddle_events
              (notification_id, event_type, occurred_at, payload, process_status, error_message)
            VALUES (%s, %s, %s::timestamptz, %s::jsonb, %s, %s)
            ON CONFLICT (notification_id) DO UPDATE SET
                process_status = EXCLUDED.process_status,
                error_message  = EXCLUDED.error_message,
                processed_at   = NOW()
            """,
            (
                notification_id, event_type, occurred_at,
                _json.dumps(payload, ensure_ascii=False), status, error_message,
            ),
        )


def get_last_event_occurred_at(event_type: str):
    """Aynı türde son başarıyla işlenen event'in zamanı — eski event'i elemek için."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT MAX(occurred_at) AS ts FROM paddle_events "
            "WHERE event_type = %s AND process_status = 'ok'",
            (event_type,),
        )
        row = cur.fetchone()
        return row["ts"] if row else None


def find_client_by_paddle_subscription(subscription_id: str) -> dict | None:
    """paddle_subscription_id ile kullanıcıyı bulur (custom_data yoksa fallback)."""
    if not subscription_id:
        return None
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT * FROM clients WHERE paddle_subscription_id = %s", (subscription_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_client_subscription(
    username: str,
    plan_type: str | None = None,
    status: str | None = None,
    subscription_id: str | None = None,
    customer_id: str | None = None,
    period_end: str | None = None,
) -> None:
    """Paddle webhook'undan gelen abonelik durumunu clients tablosuna yansıtır.

    plan_type verilirse ilgili planın kota limitleri de (max_simulations, max_tokens)
    güncellenir.
    """
    from ..plan_config import get_plan_config

    sets: list[str] = []
    params: list = []

    if plan_type is not None:
        cfg = get_plan_config(plan_type)
        sets.extend(["plan_type = %s", "max_simulations = %s", "max_tokens = %s"])
        params.extend([plan_type, cfg["max_simulations"], cfg["max_tokens"]])
    if status is not None:
        sets.append("subscription_status = %s")
        params.append(status)
    if subscription_id is not None:
        sets.append("paddle_subscription_id = %s")
        params.append(subscription_id)
    if customer_id is not None:
        sets.append("paddle_customer_id = %s")
        params.append(customer_id)
    if period_end is not None:
        sets.append("current_period_end = %s::timestamptz")
        params.append(period_end)

    if not sets:
        return

    params.append(username)
    with get_db() as (conn, cur):
        cur.execute(
            f"UPDATE clients SET {', '.join(sets)} WHERE username = %s", tuple(params)
        )


def add_flex_credits(username: str, credits: int = 3) -> None:
    """Flex (one-time Research Pack) satın alındığında araştırma hakkı ekler."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            UPDATE clients
            SET max_simulations = COALESCE(max_simulations, 0) + %s,
                plan_type = CASE WHEN plan_type = 'Free' THEN 'Flex' ELSE plan_type END
            WHERE username = %s
            """,
            (credits, username),
        )


# — KVKK / GDPR: veri taşınabilirliği ve hesap silme —


def export_user_data(username: str) -> dict:
    """Kullanıcının tüm verisini makine-okunur formatta döner (veri taşınabilirliği)."""
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM clients WHERE username = %s", (username,))
        client_row = cur.fetchone()
        account = dict(client_row) if client_row else {}
        account.pop("password_hash", None)  # asla dışa aktarılmaz

        cur.execute(
            """
            SELECT id, title, market, category, created_at, updated_at,
                   archived, has_report, quality_score, quality_grade
            FROM studies WHERE created_by = %s ORDER BY updated_at DESC
            """,
            (username,),
        )
        studies = [dict(r) for r in cur.fetchall()]

        # report_pdf (BYTEA) hariç — büyük binary veri
        cur.execute(
            """
            SELECT study_id, brief, plan, personas, interviews, report_markdown
            FROM study_payloads
            WHERE study_id IN (SELECT id FROM studies WHERE created_by = %s)
            """,
            (username,),
        )
        payloads = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT item_type, item_id, vote, comment, created_at FROM feedbacks "
            "WHERE username = %s",
            (username,),
        )
        feedbacks = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT model_id, operation, prompt_tokens, completion_tokens, total_tokens, "
            "cost_usd, created_at FROM token_usage WHERE username = %s ORDER BY created_at DESC",
            (username,),
        )
        usage = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT persona_id, question, created_at FROM interview_responses "
            "WHERE username = %s",
            (username,),
        )
        responses = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT id, name, age, city, segment, stance FROM personas_pool "
            "WHERE created_by = %s",
            (username,),
        )
        personas = [dict(r) for r in cur.fetchall()]

    return {
        "username": username,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "account": account,
        "studies": studies,
        "study_payloads": payloads,
        "feedbacks": feedbacks,
        "token_usage": usage,
        "interview_responses": responses,
        "personas_created": personas,
    }


def delete_user_data(username: str) -> dict:
    """Kullanıcının verisini siler. Global/paylaşılan personalar korunur.

    Not: Paddle aboneliği iptali çağıran tarafın sorumluluğundadır (önce iptal,
    sonra bu fonksiyon — aksi halde kullanıcı ücretlendirilmeye devam eder).
    """
    counts: dict[str, int] = {}
    with get_db() as (conn, cur):
        cur.execute("SELECT id FROM studies WHERE created_by = %s", (username,))
        study_ids = [r["id"] for r in cur.fetchall()]

        if study_ids:
            cur.execute("DELETE FROM research_chat_messages WHERE study_id = ANY(%s)", (study_ids,))
            cur.execute("DELETE FROM research_findings WHERE study_id = ANY(%s)", (study_ids,))
        cur.execute("DELETE FROM studies WHERE created_by = %s", (username,))
        counts["studies"] = len(study_ids)

        cur.execute("DELETE FROM feedbacks WHERE username = %s", (username,))
        counts["feedbacks"] = cur.rowcount
        cur.execute("DELETE FROM token_usage WHERE username = %s", (username,))
        counts["token_usage"] = cur.rowcount
        cur.execute("DELETE FROM interview_responses WHERE username = %s", (username,))
        counts["interview_responses"] = cur.rowcount
        cur.execute(
            "DELETE FROM personas_pool WHERE created_by = %s AND COALESCE(is_global, FALSE) = FALSE",
            (username,),
        )
        counts["personas"] = cur.rowcount
        try:
            cur.execute("DELETE FROM organization_members WHERE username = %s", (username,))
            counts["org_memberships"] = cur.rowcount
        except Exception:
            logger.debug("organization_members silinemedi (tablo yok olabilir).", exc_info=True)
            counts["org_memberships"] = 0
        cur.execute("DELETE FROM clients WHERE username = %s", (username,))
        counts["account"] = cur.rowcount

    return counts


# — P0-1 Aşama 2: Araştırma job kuyruğu (Celery) —


