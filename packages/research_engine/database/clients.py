"""Istemci CRUD, plan/kota ve auth yardimcilari (refactor R5-3)."""
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


def get_system_config() -> dict:
    with get_db() as (conn, cur):
        cur.execute("SELECT key, value FROM system_config")
        return {row["key"]: row["value"] for row in cur.fetchall()}


def update_system_config(key: str, value: str) -> None:
    with get_db() as (conn, cur):
        cur.execute("INSERT INTO system_config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (key, value))





def log_audit(study_id: str, persona_name: str, error_reason: str, action_taken: str) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO audit_logs (study_id, persona_name, error_reason, action_taken, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (study_id, persona_name, error_reason, action_taken, datetime.now().isoformat(timespec="seconds"))
        )


def get_audit_logs() -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")
        return [dict(row) for row in cur.fetchall()]


def save_feedback(username: str, study_id: str, item_type: str, item_id: str, vote: int, comment: str) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO feedbacks (username, study_id, item_type, item_id, vote, comment, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (username, study_id, item_type, item_id, vote, comment, datetime.now().isoformat(timespec="seconds"))
        )


def get_feedbacks() -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM feedbacks ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]




def count_chat_messages(study_id: str) -> int:
    """Bir araştırma için toplam kullanıcı (user rolü) chat mesaj sayısını döner."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT COUNT(*) as cnt FROM research_chat_messages WHERE study_id = %s AND role = 'user'",
            (study_id,)
        )
        row = cur.fetchone()
        return row["cnt"] if row else 0


def count_user_non_ab_simulations(username: str) -> int:
    """Kullanıcının A/B testleri hariç toplam gerçekleştirdiği araştırma (simülasyon) sayısını döner."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT json_data FROM interview_responses WHERE username = %s",
            (username,)
        )
        rows = cur.fetchall()
        study_ids = []
        for r in rows:
            try:
                import json
                data = json.loads(r["json_data"])
                sid = data.get("study_id")
                if sid:
                    study_ids.append(sid)
            except Exception as _e:
                # Bozuk JSON kaydı — sessizce atla ama izle
                logger.debug("interview_response JSON parse edilemedi: %s", _e)
                
        if not study_ids:
            return 0
            
        cur.execute(
            """
            SELECT COUNT(*) as count FROM studies
            WHERE id = ANY(%s)
              AND (LOWER(category) NOT LIKE '%ab%%test%' AND LOWER(category) NOT LIKE '%a/b%%')
            """,
            (study_ids,)
        )
        row = cur.fetchone()
        return row["count"] if row else 0


def get_client_by_username(username: str) -> dict | None:
    """Kullanıcı adına göre client kaydını döner."""
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM clients WHERE username = %s", (username,))
        row = cur.fetchone()
        return dict(row) if row else None


def check_and_reset_period(username: str, conn, cur) -> None:
    """Çağrıldığında yeni bir faturalandırma dönemi başladıysa sayacı sıfırlar.
    Aynı DB bağlantısı içinde çağrılmak üzere tasarlanmıştır."""
    cur.execute("SELECT plan_type, billing_cycle, period_start FROM clients WHERE username = %s", (username,))
    row = cur.fetchone()
    if not row:
        return

    billing_cycle = row["billing_cycle"] or "monthly"
    period_start_str = row["period_start"]
    if not period_start_str:
        # Henüz set edilmemiş: bugünden başlat
        cur.execute("UPDATE clients SET period_start = %s, period_simulations = 0, tokens_used = 0 WHERE username = %s",
                    (datetime.now(timezone.utc).date().isoformat(), username))
        return

    period_start = datetime.fromisoformat(period_start_str).date()
    today = datetime.now(timezone.utc).date()  # timezone-aware
    days_in_period = 365 if billing_cycle == "annual" else 30

    if (today - period_start).days >= days_in_period:
        # Yeni dönem: sayıcıyı sıfırla ve period_start'i güncelle
        new_start = period_start + timedelta(days=days_in_period)
        cur.execute(
            "UPDATE clients SET period_start = %s, period_simulations = 0, tokens_used = 0 WHERE username = %s",
            (new_start.isoformat(), username)
        )


def increment_simulation_count(username: str) -> None:
    """Bir araştırma tamamlandığında hem genel hem de dönemsel sayacı artırır."""
    with get_db() as (conn, cur):
        # Önce dönem sıfırlama kontrolü
        check_and_reset_period(username, conn, cur)
        cur.execute(
            """
            UPDATE clients
            SET total_simulations   = total_simulations + 1,
                period_simulations  = period_simulations + 1
            WHERE username = %s
            """,
            (username,),
        )


def upgrade_client_plan(username: str, new_plan: str, billing_cycle: str = "monthly") -> None:
    """Plan yükseltme: yeni planı atar, dönem sayacını sıfırlar, period_start'i bugüne çeker."""
    from ..plan_config import get_plan_config
    cfg = get_plan_config(new_plan)
    with get_db() as (conn, cur):
        cur.execute(
            """
            UPDATE clients
            SET plan_type          = %s,
                billing_cycle      = %s,
                period_start       = %s,
                period_simulations = 0,
                max_simulations    = %s,
                max_tokens         = %s
            WHERE username = %s
            """,
            (
                new_plan,
                billing_cycle,
                datetime.now(timezone.utc).date().isoformat(),
                cfg["max_simulations"],
                cfg["max_tokens"],  # plan_config SSOT — fallback yok
                username,
            ),
        )


def check_simulation_limit(username: str) -> tuple[bool, int, int]:
    """(can_run, used_this_period, max_this_period) üretir.
    can_run = True ise yeni simülasyon başlatılabilir.
    NOT: Bu fonksiyon sadece READ yapar. Sayacı artırmak için
    atomic_increment_simulation_count() kullanın (TOCTOU-safe)."""
    with get_db() as (conn, cur):
        check_and_reset_period(username, conn, cur)
        cur.execute(
            "SELECT period_simulations, max_simulations FROM clients WHERE username = %s", (username,)
        )
        row = cur.fetchone()
        if not row:
            return False, 0, 0
        used = row["period_simulations"] or 0
        max_s = row["max_simulations"] or 0
        # 9999 = sınırsız (Enterprise)
        can_run = max_s >= 9999 or used < max_s
        return can_run, used, max_s


def atomic_increment_simulation_count(username: str) -> tuple[bool, int, int]:
    """TOCTOU-safe atomik kota kontrol + artırma.
    Tek SQL UPDATE ... RETURNING ile hem kontrol hem sayacı artırır.
    Returns: (success, used_after, max_s)
    success=False → kota aşıldı, işlem yapılmadı."""
    with get_db() as (conn, cur):
        check_and_reset_period(username, conn, cur)
        cur.execute(
            """
            UPDATE clients
            SET period_simulations = period_simulations + 1
            WHERE username = %s
              AND (max_simulations >= 9999 OR period_simulations < max_simulations)
            RETURNING period_simulations, max_simulations
            """,
            (username,),
        )
        row = cur.fetchone()
        if not row:
            # Etkilenen satır yok → kota aşıldı
            cur.execute(
                "SELECT period_simulations, max_simulations FROM clients WHERE username = %s", (username,)
            )
            info = cur.fetchone()
            used = info["period_simulations"] if info else 0
            max_s = info["max_simulations"] if info else 0
            return False, used, max_s
        return True, row["period_simulations"], row["max_simulations"]


# — P0-6: Token / Maliyet Muhasebesi —

# plan_config'te 9_999_999 = pratikte sınırsız (Pro/Enterprise)
_UNLIMITED_TOKENS = 9_999_999



def register_client_if_new(username: str, email: str = "") -> tuple[dict, bool]:
    """Kullanıcı yoksa Free planla kayıt eder. Varsa mevcut kaydı döner.
    Returns: (client_dict, was_created)"""
    from ..plan_config import get_plan_config
    cfg = get_plan_config("Free")
    today = datetime.now().date().isoformat()
    with get_db() as (conn, cur):
        # Önce var mı bak
        cur.execute("SELECT * FROM clients WHERE username = %s", (username,))
        row = cur.fetchone()
        if row:
            return dict(row), False
        # Yoksa oluştur
        cur.execute(
            """
            INSERT INTO clients
              (username, email, plan_type, max_simulations, max_tokens,
               billing_cycle, period_start, period_simulations,
               total_simulations, tokens_used, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            """,
            (
                username,
                email,
                "Free",
                cfg["max_simulations"],
                cfg.get("max_tokens", 100_000),
                "monthly",
                today,
                0,
                0,
                0,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        cur.execute("SELECT * FROM clients WHERE username = %s", (username,))
        row = cur.fetchone()
        return dict(row) if row else {"username": username, "plan_type": "Free"}, True


def set_client_password(username: str, password_hash: str) -> None:
    """Kullanıcının parola hash'ini kaydeder (JWT auth)."""
    with get_db() as (conn, cur):
        cur.execute("UPDATE clients SET password_hash = %s WHERE username = %s", (password_hash, username))


def get_client_password_hash(username: str) -> str | None:
    """Kullanıcının parola hash'ini döner (yoksa None)."""
    with get_db() as (conn, cur):
        cur.execute("SELECT password_hash FROM clients WHERE username = %s", (username,))
        row = cur.fetchone()
        return row["password_hash"] if row and row.get("password_hash") else None


