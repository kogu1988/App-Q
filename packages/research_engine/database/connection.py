"""Veritabani baglantisi, baglanti havuzlari ve oturum yonetimi (refactor R5-1)."""
from __future__ import annotations

import contextvars
import json
import logging
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from pgvector.psycopg2 import register_vector
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor

# Global ContextVar for Multi-Tenancy (B2B Isolation)
current_tenant_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_tenant", default=None)

logger = logging.getLogger(__name__)


def get_current_username() -> str | None:
    """Mevcut request'in çözümlenmiş kullanıcı adını döner (JWT veya X-Username).

    Tenant middleware'i tarafından set edilen current_tenant_var'ı okur.
    """
    return current_tenant_var.get()


PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5433")
PG_USER = os.getenv("POSTGRES_USER", "clarere_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
if not PG_PASS:
    _app_env = os.getenv("APP_ENV", "development").lower()
    if _app_env == "production":
        raise RuntimeError("POSTGRES_PASSWORD env var zorunlu (production)")
    else:
        PG_PASS = "clarere_password"
        logger.warning("POSTGRES_PASSWORD ayarlanmamış — geliştirme varsayılanı kullanılıyor")
PG_DB = os.getenv("POSTGRES_DB", "clarere_db")

# SSL modu — yönetilen PostgreSQL (Neon vb.) SSL'i ZORUNLU kılar; self-hosted
# kurulumda boş bırakılır ve bağlantı davranışı değişmez. Örnek: `require`.
PG_SSLMODE = os.getenv("POSTGRES_SSLMODE", "").strip()

# App bağlantısı — RLS'yi uygulayan superuser OLMAYAN rol (tenant izolasyonu için)
APP_DB_USER = os.getenv("APP_DB_USER", "clarere_app")
APP_DB_PASS = os.getenv("APP_DB_PASSWORD", PG_PASS or "clarere_password")

# — Bağlantı Havuzu —
_POOL_MIN = int(os.getenv("PG_POOL_MIN", "2"))
_POOL_MAX = int(os.getenv("PG_POOL_MAX", "10"))
_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def _conn_params(user: str, password: str) -> dict:
    """Bağlantı havuzu parametreleri.

    `sslmode` yalnızca `POSTGRES_SSLMODE` ayarlıysa eklenir; aksi halde
    psycopg2/libpq varsayılanı (ve gerekirse `PGSSLMODE` env'i) geçerlidir.
    """
    params: dict = {
        "host": PG_HOST,
        "port": PG_PORT,
        "user": user,
        "password": password,
        "dbname": PG_DB,
    }
    if PG_SSLMODE:
        params["sslmode"] = PG_SSLMODE
    return params


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    """Lazy-init edilmiş thread-safe bağlantı havuzunu döner."""
    global _pool
    if _pool is None or _pool.closed:
        with _pool_lock:
            if _pool is None or _pool.closed:
                _pool = pg_pool.ThreadedConnectionPool(
                    minconn=_POOL_MIN,
                    maxconn=_POOL_MAX,
                    **_conn_params(PG_USER, PG_PASS),
                )
                logger.info(f"PostgreSQL bağlantı havuzu oluşturuldu (min={_POOL_MIN}, max={_POOL_MAX})")
    return _pool


_app_pool: pg_pool.ThreadedConnectionPool | None = None


def _get_app_pool() -> pg_pool.ThreadedConnectionPool:
    """App bağlantı havuzu — RLS'ye tabi, superuser olmayan rol."""
    global _app_pool
    if _app_pool is None or _app_pool.closed:
        with _pool_lock:
            if _app_pool is None or _app_pool.closed:
                _app_pool = pg_pool.ThreadedConnectionPool(
                    minconn=_POOL_MIN,
                    maxconn=_POOL_MAX,
                    **_conn_params(APP_DB_USER, APP_DB_PASS),
                )
                logger.info(f"App bağlantı havuzu oluşturuldu (user={APP_DB_USER})")
    return _app_pool


@contextmanager
def get_db(register_pgvector=True):
    """App bağlantısı (RLS'ye tabi rol) ve işlem sonrası geri verir."""
    conn = _get_app_pool().getconn()
    if register_pgvector:
        try:
            register_vector(conn)
        except Exception:
            pass  # extension might not be created yet
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # RLS Session değişkenlerini HER istekte set et (anon dahil) — havuzdan kalıntı değer kalmasın
            tenant_id = current_tenant_var.get() or ""
            cur.execute("SELECT set_config('clarere.current_tenant', %s, true)", (tenant_id,))
            # Organizasyon bağlamı (multi-user paylaşımı) — üye değilse '' (boş)
            try:
                cur.execute(
                    "SELECT set_config('clarere.current_org', COALESCE((SELECT org_id FROM organization_members WHERE username = %s LIMIT 1), ''), true)",
                    (tenant_id,),
                )
            except Exception:
                cur.execute("SELECT set_config('clarere.current_org', '', true)")
            yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_app_pool().putconn(conn)

@contextmanager
def get_admin_db(register_pgvector=False):
    """Superuser bağlantısı — init_db/migration için (RLS'yi bypass eder)."""
    conn = _get_pool().getconn()
    if register_pgvector:
        try:
            register_vector(conn)
        except Exception:
            pass
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)


def _ensure_app_role(cur) -> None:
    """RLS'ye tabi, superuser olmayan app rolünü oluşturur ve yetkilendirir.

    PostgreSQL superuser'ları RLS'yi bypass eder; tenant izolasyonunun
    fiilen çalışması için app bu rol (clarere_app) üzerinden bağlanmalı.

    Yönetilen PostgreSQL (Neon vb.) `CREATE ROLE` yetkisi vermez. Bu durumda
    rol oluşturma atlanır — `FORCE ROW LEVEL SECURITY` sayesinde tablo sahibi
    de policy'ye tabi olduğu için tenant izolasyonu çalışmaya devam eder.
    """
    from psycopg2 import sql as psql

    if APP_DB_USER != "clarere_app":
        logger.info(
            "App rolü yönetilen DB tarafından sağlanıyor (APP_DB_USER=%s) — "
            "rol oluşturma atlandı.",
            APP_DB_USER,
        )
        return

    try:
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'clarere_app') THEN
                    CREATE ROLE clarere_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB;
                END IF;
            END
            $$;
            """
        )
        cur.execute(
            psql.SQL("ALTER ROLE clarere_app WITH LOGIN PASSWORD {}").format(psql.Literal(APP_DB_PASS))
        )
        cur.execute("GRANT USAGE ON SCHEMA public TO clarere_app;")
        cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO clarere_app;")
        cur.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO clarere_app;")
        cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO clarere_app;")
        cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO clarere_app;")
    except Exception as exc:
        logger.warning(
            "clarere_app rolü oluşturulamadı (%s) — yönetilen DB olabilir; "
            "FORCE ROW LEVEL SECURITY ile izolasyon devam eder.",
            exc,
        )

