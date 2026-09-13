"""Altyapi tablolari + indeksler + surumlu migration'lar (refactor R5-2)."""
from __future__ import annotations

from datetime import datetime


def apply_infra_schema(conn, cur) -> None:
    # NOTE (O-2 / karar 2026-09-12): ai_semantic_cache KASITLI olarak korunuyor.
    # Şu an hiçbir kod yolu bu tabloyu okumuyor/yazmıyor (semantic cache kullanıcı
    # isteğiyle devre dışı bırakıldı). Ancak Enterprise planındaki "vektör tabanlı
    # persona havuzu / içerik eşleştirme" özelliği için altyapı rezervidir.
    # SİLMEDEN ÖNCE: Enterprise yol haritası (MEMORY.md § Enterprise) ile birlikte karar ver.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_semantic_cache (
            id SERIAL PRIMARY KEY,
            query_type TEXT,
            prompt_hash TEXT UNIQUE,
            prompt_embedding vector(384),
            llm_response TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    try:
        # Create HNSW index for fast semantic search if not exists
        cur.execute("CREATE INDEX IF NOT EXISTS ai_semantic_cache_embedding_idx ON ai_semantic_cache USING hnsw (prompt_embedding vector_cosine_ops);")
    except Exception as e:
        print(f"[DB] Index migration warning for ai_semantic_cache: {e}")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_rationales (
            id SERIAL PRIMARY KEY,
            prompt_hash TEXT,
            model_id TEXT,
            thinking_text TEXT,
            response_text TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    # — Migration versiyon tablosu (DB-3) —
    # Her migration satırı idempotent olarak izlenir.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )

    # — P0-6: Token / maliyet muhasebesi —
    # Her LLM çağrısı buraya bir satır yazar; clients.tokens_used dönemsel toplamdır.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS token_usage (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            study_id TEXT,
            model_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cache_hit_tokens INTEGER DEFAULT 0,
            cost_usd NUMERIC(10,6) DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS curated_questions (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            study_id TEXT,
            research_title TEXT,
            research_category TEXT,
            purpose_context TEXT,
            is_liked BOOLEAN DEFAULT TRUE,
            created_at TEXT,
            embedding vector(384)
        )
        """
    )

    # Sprint 3 — Ürün KPI event'leri (funnel ölçümü)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS product_events (
            id SERIAL PRIMARY KEY,
            event_name TEXT NOT NULL,
            username TEXT,
            study_id TEXT,
            props JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    try:
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_product_events_name_time ON product_events(event_name, created_at DESC);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_product_events_user ON product_events(username);"
        )
    except Exception as e:
        logger.warning("product_events index migration warning: %s", e)

    # Sprint 1 — Evidence Chain tabloları
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS research_findings (
            id SERIAL PRIMARY KEY,
            study_id TEXT REFERENCES studies(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            category TEXT,
            summary TEXT,
            confidence FLOAT,
            implication TEXT,
            supporting_count INTEGER DEFAULT 0,
            refuting_count INTEGER DEFAULT 0,
            neutral_count INTEGER DEFAULT 0,
            contradiction_score FLOAT DEFAULT 0,
            decision_signal TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS research_evidence (
            id SERIAL PRIMARY KEY,
            finding_id INTEGER REFERENCES research_findings(id) ON DELETE CASCADE,
            persona_id TEXT,
            persona_name TEXT,
            stance TEXT,
            question TEXT,
            quote TEXT,
            sentiment TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )

    # Sprint 4 — Research Copilot chat messages
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS research_chat_messages (
            id SERIAL PRIMARY KEY,
            study_id TEXT REFERENCES studies(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    )
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_study ON research_chat_messages(study_id, created_at);")
    except Exception as e:
        print(f"[DB] Index migration warning for research_chat_messages: {e}")

    # Performans indeksleri — sorgu pattern'lerine göre (tablo oluşturulduktan SONRA)
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_interview_responses_user ON interview_responses(username);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_studies_updated_at ON studies(updated_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_studies_active ON studies(updated_at DESC) WHERE archived = FALSE OR archived IS NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_personas_pool_stance ON personas_pool(stance);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_personas_pool_segment ON personas_pool(segment);")
    except Exception as e:
        print(f"[DB] Index migration warning: {e}")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            study_id TEXT,
            persona_name TEXT,
            error_reason TEXT,
            action_taken TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            username TEXT PRIMARY KEY,
            total_simulations INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Aktif',
            created_at TEXT,
            email TEXT,
            plan_type TEXT DEFAULT 'Free',
            plan_start TEXT,
            plan_end TEXT,
            max_simulations INTEGER DEFAULT 2,
            max_tokens INTEGER DEFAULT 100000
        )
        """
    )
    # Billing & period tracking migrations (safe to run on existing DBs)
    try:
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS billing_cycle TEXT DEFAULT 'monthly';")
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS period_start TEXT;")
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS period_simulations INTEGER DEFAULT 0;")
        # Backfill: mevcut kayıtlar için period_start yoksa bugünü kullan
        cur.execute("UPDATE clients SET period_start = %s WHERE period_start IS NULL;", (datetime.now().date().isoformat(),))
    except Exception as e:
        print(f"[DB] Billing migration warning: {e}")
    # Auth migration (JWT password hashing)
    try:
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash TEXT;")
    except Exception as e:
        print(f"[DB] Auth migration warning: {e}")

    # — P0-2: Paddle abonelik durumu ("Lean Cache" — sadece erişim kararı alanları) —
    try:
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS paddle_customer_id TEXT;")
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS paddle_subscription_id TEXT;")
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS subscription_status TEXT;")
        cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMPTZ;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clients_paddle_sub ON clients(paddle_subscription_id);")
    except Exception as e:
        print(f"[DB] Paddle migration warning: {e}")

    # Webhook idempotensi + sıralama — Paddle at-least-once teslim eder
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS paddle_events (
            notification_id TEXT PRIMARY KEY,
            event_type      TEXT NOT NULL,
            occurred_at     TIMESTAMPTZ NOT NULL,
            payload         JSONB NOT NULL,
            processed_at    TIMESTAMPTZ DEFAULT NOW(),
            process_status  TEXT DEFAULT 'ok',
            error_message   TEXT
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_paddle_events_occurred ON paddle_events(occurred_at DESC);"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feedbacks (
            id SERIAL PRIMARY KEY,
            username TEXT,
            study_id TEXT,
            item_type TEXT,
            item_id TEXT,
            vote INTEGER,
            comment TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS curated_questions (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            study_id TEXT,
            research_title TEXT,
            research_category TEXT,
            purpose_context TEXT,
            is_liked BOOLEAN DEFAULT TRUE,
            created_at TEXT,
            embedding vector(384)
        )
        """
    )

    # — DB-6: feedbacks.study_id FK constraint (migration 001) —
    # Orphaned feedback verilerini önler; study silinince cascade siler.
    try:
        cur.execute(
            "SELECT version FROM schema_migrations WHERE version = '001-feedbacks-fk'"
        )
        if not cur.fetchone():
            cur.execute(
                """
                ALTER TABLE feedbacks
                ADD CONSTRAINT fk_feedbacks_study_id
                FOREIGN KEY (study_id) REFERENCES studies(id) ON DELETE CASCADE;
                """
            )
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES ('001-feedbacks-fk')"
            )
            logger.info("Migration 001-feedbacks-fk uygulandı")
    except Exception as e:
        logger.warning("Migration 001-feedbacks-fk atlandı: %s", e)

    # — DB-4: Timestamp sütunlarını TEXT'den TIMESTAMPTZ'ye dönüştür (migration 002) —
    # NOT: Mevcut ISO 8601 TEXT verisi USING cast ile dönüştürülür.
    # Production'da mevcut veri kontrol edilmeli — development'ta güvenli.
    _ts_migrations = [
        ("studies",   ["created_at", "updated_at"]),
        ("audit_logs",["created_at"]),
        ("clients",   ["created_at"]),
        ("feedbacks", ["created_at"]),
    ]
    try:
        cur.execute(
            "SELECT version FROM schema_migrations WHERE version = '002-timestamp-types'"
        )
        if not cur.fetchone():
            for table, cols in _ts_migrations:
                for col in cols:
                    try:
                        cur.execute(
                            f"""
                            ALTER TABLE {table}
                            ALTER COLUMN {col} TYPE TIMESTAMP WITH TIME ZONE
                            USING {col}::TIMESTAMP WITH TIME ZONE;
                            """
                        )
                    except Exception as col_err:
                        # Bazı satırlar formatı bozuksa NULL'a düşürülür
                        logger.warning("TS migration %s.%s atlandı: %s", table, col, col_err)
                        conn.rollback()
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES ('002-timestamp-types')"
            )
            logger.info("Migration 002-timestamp-types uygulandı")
    except Exception as e:
        logger.warning("Migration 002-timestamp-types atlandı: %s", e)

    # — Curated Questions İndeksleri (migration 003) —
    # curated_questions tablosundaki aramaları ve filtrelemeleri hızlandırır.
    try:
        cur.execute(
            "SELECT version FROM schema_migrations WHERE version = '003-curated-questions-indexes'"
        )
        if not cur.fetchone():
            cur.execute("CREATE INDEX IF NOT EXISTS idx_curated_questions_study_id ON curated_questions(study_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_curated_questions_liked ON curated_questions(is_liked) WHERE is_liked = TRUE;")
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES ('003-curated-questions-indexes')"
            )
            logger.info("Migration 003-curated-questions-indexes uygulandı")
    except Exception as e:
        logger.warning("Migration 003-curated-questions-indexes atlandı: %s", e)
