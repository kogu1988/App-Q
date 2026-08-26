"""Test: RLS tenant izolasyonu (canlı Postgres gerekir — yoksa skip).

Bu test gerçek PostgreSQL üzerinde çalışır:
  1. İki kullanıcı oluşturur (alice_rls, bob_rls)
  2. Alice bir çalışma (study) kaydeder
  3. Bob'un RLS oturumunda Alice'in çalışmasını GÖREMEMESİ gerekir
  4. Alice'in RLS oturumunda kendi çalışmasını GÖREBİLMESİ gerekir

Postgres ayakta değilse pytest.skip ile atlanır (CI/offline güvenliği).
"""
import pytest
import os

pytestmark = pytest.mark.skipif(
    os.getenv("APP_ENV", "development").lower() == "production",
    reason="Production'da izolasyon testi riskli olabilir.",
)


def _db_available() -> bool:
    try:
        from packages.research_engine.database import get_db
        with get_db(register_pgvector=False) as (conn, cur):
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _setup_users(username: str) -> None:
    from packages.research_engine.database import get_db
    with get_db(register_pgvector=False) as (conn, cur):
        cur.execute(
            "INSERT INTO clients (username, created_at, plan_type, max_simulations, max_tokens, billing_cycle, period_start, period_simulations)"
            " VALUES (%s, NOW(), 'Free', 2, 100000, 'monthly', NOW(), 0)"
            " ON CONFLICT (username) DO NOTHING",
            (username,),
        )


def _insert_study_as(username: str, study_id: str) -> None:
    from packages.research_engine.database import get_db
    from packages.research_engine.database import current_tenant_var
    token = current_tenant_var.set(username)
    try:
        with get_db(register_pgvector=False) as (conn, cur):
            cur.execute(
                "INSERT INTO studies (id, title, created_at, updated_at, archived, has_report, has_pdf, created_by, org_id)"
                " VALUES (%s, %s, NOW(), NOW(), FALSE, FALSE, FALSE, %s, NULL)",
                (study_id, f"RLS Test {study_id}", username),
            )
    finally:
        current_tenant_var.reset(token)


def _can_see_study(username: str, study_id: str) -> bool:
    from packages.research_engine.database import get_db
    from packages.research_engine.database import current_tenant_var
    token = current_tenant_var.set(username)
    try:
        with get_db(register_pgvector=False) as (conn, cur):
            cur.execute("SELECT COUNT(*) AS n FROM studies WHERE id = %s", (study_id,))
            row = cur.fetchone()
            return bool(row and row["n"] > 0)
    finally:
        current_tenant_var.reset(token)


def test_rls_tenant_isolation_live():
    if not _db_available():
        pytest.skip("PostgreSQL çalışmıyor — canlı RLS testi atlandı.")

    from packages.research_engine.database import init_db
    init_db()  # Tablo + RLS politikalarının kurulu olduğundan emin ol

    _setup_users("alice_rls")
    _setup_users("bob_rls")

    study_id = "rls_test_001"
    _insert_study_as("alice_rls", study_id)

    try:
        # Alice kendi çalışmasını görebilir
        assert _can_see_study("alice_rls", study_id), "Alice kendi çalışmasını göremiyor (RLS çok sıkı)"

        # Bob Alice'in çalışmasını GÖREMEZ (tenant izolasyonu)
        assert not _can_see_study("bob_rls", study_id), "Bob başka kullanıcının çalışmasını görebiliyor (RLS yok/bozuk)"
    finally:
        # Temizlik
        from packages.research_engine.database import get_db
        from packages.research_engine.database import current_tenant_var
        token = current_tenant_var.set("alice_rls")
        try:
            with get_db(register_pgvector=False) as (conn, cur):
                cur.execute("DELETE FROM studies WHERE id = %s", (study_id,))
                cur.execute("DELETE FROM clients WHERE username IN ('alice_rls', 'bob_rls')")
        finally:
            current_tenant_var.reset(token)
