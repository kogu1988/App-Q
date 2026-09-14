"""GRUP 12 — Migration İdempotensi testleri.

Korunan değer: Deploy güvenliği. `init_db()` her başlatmada çalışır; ikinci çalıştırma
veri kaybetmemeli veya hata vermemeli.

Gereksinim: Canlı PostgreSQL, yoksa `pytest.skip`.
"""
from __future__ import annotations

import pytest

DEMO_USER = "free"
# Migration testinin insert ettiği study'nin sahibi (RLS: created_by = current_tenant).
MIGRATION_TENANT = "migration_test_user"


def _db_available() -> bool:
    try:
        from packages.research_engine.database import get_db

        with get_db() as (_conn, cur):
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


DB_REQUIRED = pytest.mark.skipif(not _db_available(), reason="Canlı PostgreSQL gerekli")

EXPECTED_INDEXES = {
    "idx_token_usage_user_date",
    "idx_research_findings_study",
    "idx_research_evidence_finding",
    "idx_research_jobs_user",
}


@DB_REQUIRED
def test_12_1_init_db_is_idempotent():
    """init_db() ardışık iki kez hatasız çalışmalı."""
    from packages.research_engine.database import init_db

    init_db()
    init_db()


@DB_REQUIRED
def test_12_2_existing_data_is_preserved():
    """init_db() mevcut veriyi silmemeli."""
    from packages.research_engine.database import current_tenant_var, get_db, init_db

    study_id = "migration_idempotency_test"
    # RLS aktiftir (FORCE ROW LEVEL SECURITY): studies insert/select yalnızca
    # created_by = clarere.current_tenant eşleşmesiyle mümkündür. Tenant bağlamı
    # set edilmezse insert politika ihlaliyle reddedilir.
    token = current_tenant_var.set(MIGRATION_TENANT)
    try:
        with get_db() as (_conn, cur):
            cur.execute("DELETE FROM studies WHERE id = %s", (study_id,))
            cur.execute(
                "INSERT INTO studies (id, title, market, category, created_by)"
                " VALUES (%s, %s, %s, %s, %s)",
                (study_id, "Kalıcılık Testi", "Türkiye", "genel", MIGRATION_TENANT),
            )

        init_db()
        with get_db() as (_conn, cur):
            cur.execute("SELECT title FROM studies WHERE id = %s", (study_id,))
            row = cur.fetchone()
        assert row is not None, "init_db() mevcut kaydı sildi"
        assert row["title"] == "Kalıcılık Testi"
    finally:
        with get_db() as (_conn, cur):
            cur.execute("DELETE FROM studies WHERE id = %s", (study_id,))
        current_tenant_var.reset(token)


@DB_REQUIRED
def test_12_3_schema_migrations_has_no_duplicate_versions():
    """schema_migrations'ta her versiyon tek satır olmalı."""
    from packages.research_engine.database import get_db

    with get_db() as (_conn, cur):
        cur.execute(
            "SELECT version, COUNT(*) AS c FROM schema_migrations GROUP BY version HAVING COUNT(*) > 1"
        )
        duplicates = [dict(r) for r in cur.fetchall()]

    assert duplicates == [], f"mükerrer migration kaydı: {duplicates}"


@DB_REQUIRED
def test_12_4_demo_users_are_synced_to_fixtures():
    """init_db() demo kullanıcıları fixture planına senkronize etmeli (dev).

    Dev'de demo kullanıcılar deterministik fixture'dır: eski/yanlış bir plan
    kaydı kalıcı olmamalı (ör. `free` yanlışlıkla Flex kalmamalı) ve **deneme
    penceresi de tazelenmeli** — aksi halde eski `created_at` yüzünden Free
    demo kullanıcısı 403 alır ve demo yapılamaz.
    Production'da demo kullanıcı hiç seed edilmez.
    """
    from packages.research_engine.database import get_client_by_username, get_db, init_db

    original = get_client_by_username(DEMO_USER)
    if original is None:
        pytest.skip(f"demo kullanıcı '{DEMO_USER}' yok")

    with get_db() as (_conn, cur):
        cur.execute(
            "UPDATE clients SET plan_type = 'Flex', created_at = %s WHERE username = %s",
            ("2020-01-01T00:00:00", DEMO_USER),
        )

    try:
        init_db()
        after = get_client_by_username(DEMO_USER)
        assert after["plan_type"] == "Free", (
            "init_db() demo kullanıcının planını fixture değerine (Free) senkronize etmeli"
        )

        # Deneme penceresi de sıfırlanmalı (ay kapısı `created_at`'e bağlı).
        from apps.backend.routers.client import is_trial_expired

        expired, reason = is_trial_expired(after)
        assert expired is False, (
            f"demo '{DEMO_USER}' kullanıcısı araştırma yapabilmeli (reason: {reason})"
        )
    finally:
        with get_db() as (_conn, cur):
            cur.execute("UPDATE clients SET plan_type = 'Free' WHERE username = %s", (DEMO_USER,))


@DB_REQUIRED
def test_12_5_expected_indexes_exist():
    """Kritik performans index'leri oluşturulmuş olmalı."""
    from packages.research_engine.database import get_db

    with get_db() as (_conn, cur):
        cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        present = {r["indexname"] for r in cur.fetchall()}

    missing = EXPECTED_INDEXES - present
    assert missing == set(), f"eksik index'ler: {missing}"
