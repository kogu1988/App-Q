"""Test: Multi-user ORG paylaşımı — canlı Postgres RLS (yoksa skip).

O-4: Enterprise `multi_user` özelliğinin RLS ayağı. Kod seviyesinde tamam olan
"aynı org üyeleri birbirinin çalışmasını görür, üye olmayan göremez" davranışı
gerçek PostgreSQL üzerinde doğrulanır.

Korunan değer: Tenant izolasyonu ile org paylaşımı arasındaki denge.
`studies_tenant_policy` bozulursa ya veri sızar (org dışı görür) ya da meşru
paylaşım çalışmaz (org üyesi göremez).

Gereksinim: Canlı PostgreSQL. Yoksa `pytest.skip`.
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("APP_ENV", "development").lower() == "production",
    reason="Production'da izolasyon testi riskli olabilir.",
)

ORG_ID = "org_rls_sharing_test"
OWNER = "org_rls_owner"
MEMBER = "org_rls_member"
OUTSIDER = "org_rls_outsider"
STUDY_ID = "org_rls_sharing_study"


def _db_available() -> bool:
    try:
        from packages.research_engine.database import get_db

        with get_db(register_pgvector=False) as (_conn, cur):
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _upsert_user(username: str) -> None:
    from packages.research_engine.database import get_db

    with get_db(register_pgvector=False) as (_conn, cur):
        cur.execute("DELETE FROM clients WHERE username = %s", (username,))
        cur.execute(
            "INSERT INTO clients (username, created_at, plan_type, max_simulations, max_tokens,"
            " billing_cycle, period_start, period_simulations)"
            " VALUES (%s, NOW(), 'Enterprise', 9999, 9999999, 'monthly', NOW(), 0)",
            (username,),
        )


def _insert_org_study(owner: str, org_id: str) -> None:
    from packages.research_engine.database import current_tenant_var, get_db

    token = current_tenant_var.set(owner)
    try:
        with get_db(register_pgvector=False) as (_conn, cur):
            cur.execute("DELETE FROM studies WHERE id = %s", (STUDY_ID,))
            cur.execute(
                "INSERT INTO studies (id, title, created_at, updated_at, archived, has_report,"
                " has_pdf, created_by, org_id)"
                " VALUES (%s, %s, NOW(), NOW(), FALSE, FALSE, FALSE, %s, %s)",
                (STUDY_ID, "Org Paylaşım Testi", owner, org_id),
            )
    finally:
        current_tenant_var.reset(token)


def _can_see_study(tenant: str, study_id: str) -> bool:
    from packages.research_engine.database import current_tenant_var, get_db

    token = current_tenant_var.set(tenant)
    try:
        with get_db(register_pgvector=False) as (_conn, cur):
            cur.execute("SELECT COUNT(*) AS n FROM studies WHERE id = %s", (study_id,))
            row = cur.fetchone()
            return bool(row and row["n"] > 0)
    finally:
        current_tenant_var.reset(token)


def _cleanup() -> None:
    from packages.research_engine.database import current_tenant_var, get_db

    token = current_tenant_var.set(OWNER)
    try:
        with get_db(register_pgvector=False) as (_conn, cur):
            cur.execute("DELETE FROM studies WHERE id = %s", (STUDY_ID,))
            cur.execute("DELETE FROM organization_members WHERE org_id = %s", (ORG_ID,))
            cur.execute("DELETE FROM organizations WHERE id = %s", (ORG_ID,))
            cur.execute(
                "DELETE FROM clients WHERE username IN (%s, %s, %s)",
                (OWNER, MEMBER, OUTSIDER),
            )
    finally:
        current_tenant_var.reset(token)


def test_rls_org_sharing_live():
    """Org üyesi paylaşılan çalışmayı görür; org dışı kullanıcı göremez."""
    if not _db_available():
        pytest.skip("PostgreSQL çalışmıyor — canlı org paylaşım testi atlandı.")

    from packages.research_engine.database import init_db
    from packages.research_engine.db_org import (
        add_organization_member,
        create_organization,
        init_org_schema,
    )

    init_db()
    init_org_schema()
    _cleanup()

    try:
        for username in (OWNER, MEMBER, OUTSIDER):
            _upsert_user(username)

        # OWNER org sahibi (admin), MEMBER ise org üyesi; OUTSIDER üye değil.
        create_organization(ORG_ID, "RLS Test Org", "Enterprise", owner_username=OWNER)
        add_organization_member(ORG_ID, MEMBER, "member")

        _insert_org_study(OWNER, ORG_ID)

        # Sahip kendi çalışmasını görür.
        assert _can_see_study(OWNER, STUDY_ID) is True
        # Aynı org üyesi paylaşım sayesinde görür (RLS: org_id = current_org).
        assert _can_see_study(MEMBER, STUDY_ID) is True
        # Org dışı kullanıcı göremez (tenant + org izolasyonu).
        assert _can_see_study(OUTSIDER, STUDY_ID) is False
    finally:
        _cleanup()


def test_rls_org_membership_revoked_removes_access():
    """Üyelik kaldırılınca erişim de kalkmalı (paylaşım kalıcı sızıntıya dönüşmez)."""
    if not _db_available():
        pytest.skip("PostgreSQL çalışmıyor — canlı org paylaşım testi atlandı.")

    from packages.research_engine.database import init_db
    from packages.research_engine.db_org import (
        add_organization_member,
        create_organization,
        init_org_schema,
        remove_organization_member,
    )

    init_db()
    init_org_schema()
    _cleanup()

    try:
        for username in (OWNER, MEMBER):
            _upsert_user(username)

        create_organization(ORG_ID, "RLS Test Org", "Enterprise", owner_username=OWNER)
        add_organization_member(ORG_ID, MEMBER, "member")
        _insert_org_study(OWNER, ORG_ID)

        assert _can_see_study(MEMBER, STUDY_ID) is True

        assert remove_organization_member(ORG_ID, MEMBER) is True
        assert _can_see_study(MEMBER, STUDY_ID) is False, "Üyelik kaldırıldı ama erişim sürüyor"
    finally:
        _cleanup()
