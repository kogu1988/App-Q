"""Çok kullanıcılı organizasyon (multi_user) — Enterprise özelliği.

Bir organizasyon (org) birden çok kullanıcıyı barındırır; org üyeleri
araştırmaları paylaşır. Bu modül organizasyon/üyelik CRUD'unu sağlar.
RLS tabanlı veri paylaşımı bir sonraki adımda studies tablosuna bağlanır.
"""
from __future__ import annotations

from datetime import datetime

from .database import get_admin_db, get_db


def _create_org_tables(cur) -> None:
    """Organizasyon tablolarını oluşturur (idempotent).

    NOT: DDL yetkisi gerekir → yalnızca admin/superuser bağlantısı üzerinden
    çağrılmalıdır (`init_db` veya `get_admin_db`). App rolü (clarere_app) DDL
    yapamaz.
    """
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan_type TEXT NOT NULL DEFAULT 'Enterprise',
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_members (
            org_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,
            username TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            created_at TEXT,
            PRIMARY KEY (org_id, username)
        )
        """
    )


def init_org_schema() -> None:
    """Organizasyon tablolarını oluşturur (idempotent, admin bağlantısı)."""
    with get_admin_db(register_pgvector=False) as (_conn, cur):
        _create_org_tables(cur)


def create_organization(org_id: str, name: str, plan_type: str = "Enterprise", owner_username: str = "") -> None:
    """Yeni organizasyon oluşturur; isteğe bağlı sahibini 'admin' olarak ekler."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as (conn, cur):
        cur.execute(
            "INSERT INTO organizations (id, name, plan_type, created_at) VALUES (%s, %s, %s, %s)",
            (org_id, name, plan_type, now),
        )
        if owner_username:
            cur.execute(
                "INSERT INTO organization_members (org_id, username, role, created_at) VALUES (%s, %s, 'admin', %s)",
                (org_id, owner_username, now),
            )


def list_organizations() -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM organizations ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]


def add_organization_member(org_id: str, username: str, role: str = "member") -> None:
    """Organizasyona üye ekler; varsa rolünü günceller (upsert)."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as (conn, cur):
        cur.execute(
            "INSERT INTO organization_members (org_id, username, role, created_at) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (org_id, username) DO UPDATE SET role = EXCLUDED.role",
            (org_id, username, role, now),
        )


def remove_organization_member(org_id: str, username: str) -> bool:
    with get_db() as (conn, cur):
        cur.execute(
            "DELETE FROM organization_members WHERE org_id = %s AND username = %s",
            (org_id, username),
        )
        return cur.rowcount > 0


def list_organization_members(org_id: str) -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT * FROM organization_members WHERE org_id = %s ORDER BY created_at",
            (org_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_user_organization(username: str) -> dict | None:
    """Kullanıcının üyesi olduğu organizasyonu döner (yoksa None)."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT o.id, o.name, o.plan_type, o.created_at, m.role AS member_role
            FROM organizations o
            JOIN organization_members m ON m.org_id = o.id
            WHERE m.username = %s
            ORDER BY o.created_at
            LIMIT 1
            """,
            (username,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_org_id(username: str) -> str | None:
    """Kullanıcının org_id'sini döner (üye değilse None)."""
    with get_db() as (conn, cur):
        cur.execute(
            "SELECT org_id FROM organization_members WHERE username = %s LIMIT 1",
            (username,),
        )
        row = cur.fetchone()
        return row["org_id"] if row else None
