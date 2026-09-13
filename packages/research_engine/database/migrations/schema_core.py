"""Cekirdek sema + tenant/RLS migration'lari (refactor R5-2)."""
from __future__ import annotations

from pgvector.psycopg2 import register_vector


def apply_core_schema(conn, cur) -> None:
    # Create extension for pgvector
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    # Now register it
    try:
        register_vector(conn)
    except Exception:
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS studies (
            id TEXT PRIMARY KEY,
            title TEXT,
            market TEXT,
            category TEXT,
            created_at TEXT,
            updated_at TEXT,
            archived BOOLEAN,
            has_report BOOLEAN,
            has_pdf BOOLEAN,
            pdf_status TEXT,
            pdf_error TEXT,
            quality_score INTEGER,
            quality_grade TEXT,
            quality_summary TEXT,
            brief_hash TEXT,
            roles_hash TEXT,
            cache_status TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS study_payloads (
            study_id TEXT PRIMARY KEY,
            brief TEXT,
            roles TEXT,
            plan TEXT,
            personas TEXT,
            interviews TEXT,
            report_json TEXT,
            report_markdown TEXT,
            report_html TEXT,
            report_pdf BYTEA,
            script TEXT,
            FOREIGN KEY(study_id) REFERENCES studies(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interview_responses (
            hash TEXT PRIMARY KEY,
            username TEXT,
            persona_id TEXT,
            question TEXT,
            json_data TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS personas_pool (
            id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            city TEXT,
            segment TEXT,
            stance TEXT,
            price_sensitivity INTEGER,
            digital_confidence INTEGER,
            context TEXT,
            goals TEXT,
            objections TEXT,
            knowledge_boundary TEXT,
            country_code TEXT,
            origin_country TEXT,
            role_title TEXT,
            bio TEXT,
            attributes TEXT,
            traits TEXT,
            created_at TEXT,
            embedding vector(384)
        )
        """
    )

    # B2B & Tenancy Migrations for personas_pool
    try:
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS created_by TEXT;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS is_global BOOLEAN DEFAULT TRUE;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS b2b_role TEXT;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS industry TEXT;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS company_size TEXT;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS b2b_company_type TEXT;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS b2b_decision_maker BOOLEAN DEFAULT FALSE;")
        # Anchor Panel Migrations
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS big_five_vector vector(5);")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS innovation_stance TEXT;")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;")
        # Demographics and quota fields
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS ses_group TEXT DEFAULT 'C1';")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS respondent_type TEXT DEFAULT 'potential_customer';")
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS settlement_type TEXT DEFAULT 'kentsel';")
        # Usage tracking
        cur.execute("ALTER TABLE personas_pool ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;")
    except Exception as e:
        print(f"[DB] Migration warning for personas_pool: {e}")

    # Row-Level Security (RLS) for personas_pool (B2B Isolation)
    try:
        cur.execute("ALTER TABLE personas_pool ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE personas_pool FORCE ROW LEVEL SECURITY;")
        # Sadece kendi oluşturduğu personalar VEYA global olanları görebilir/kullanabilir
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE policyname = 'tenant_isolation_policy' AND tablename = 'personas_pool'
                ) THEN
                    CREATE POLICY tenant_isolation_policy ON personas_pool
                    USING (created_by = current_setting('clarere.current_tenant', true) OR is_global = TRUE);
                END IF;
            END
            $$;
        """)
    except Exception as e:
        print(f"[DB] RLS Migration warning for personas_pool: {e}")

    # Çok kullanıcılı organizasyon (multi_user) — Enterprise özelliği
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

    # Studies tenancy migration (multi-user RLS — tenant + org paylaşımı)
    try:
        cur.execute("ALTER TABLE studies ADD COLUMN IF NOT EXISTS created_by TEXT;")
        cur.execute("ALTER TABLE studies ADD COLUMN IF NOT EXISTS org_id TEXT;")
        cur.execute("ALTER TABLE studies ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE studies FORCE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS studies_tenant_policy ON studies;")
        cur.execute(
            """
            CREATE POLICY studies_tenant_policy ON studies
            USING (
                created_by = current_setting('clarere.current_tenant', true)
                OR (org_id IS NOT NULL AND org_id <> '' AND org_id = current_setting('clarere.current_org', true))
            )
            """
        )
    except Exception as e:
        print(f"[DB] Studies RLS migration warning: {e}")
