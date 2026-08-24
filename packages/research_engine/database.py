from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from contextlib import contextmanager
import contextvars

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

# App bağlantısı — RLS'yi uygulayan superuser OLMAYAN rol (tenant izolasyonu için)
APP_DB_USER = os.getenv("APP_DB_USER", "clarere_app")
APP_DB_PASS = os.getenv("APP_DB_PASSWORD", PG_PASS or "clarere_password")

# — Bağlantı Havuzu —
_POOL_MIN = int(os.getenv("PG_POOL_MIN", "2"))
_POOL_MAX = int(os.getenv("PG_POOL_MAX", "10"))
_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    """Lazy-init edilmiş thread-safe bağlantı havuzunu döner."""
    global _pool
    if _pool is None or _pool.closed:
        with _pool_lock:
            if _pool is None or _pool.closed:
                _pool = pg_pool.ThreadedConnectionPool(
                    minconn=_POOL_MIN,
                    maxconn=_POOL_MAX,
                    host=PG_HOST,
                    port=PG_PORT,
                    user=PG_USER,
                    password=PG_PASS,
                    dbname=PG_DB,
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
                    host=PG_HOST,
                    port=PG_PORT,
                    user=APP_DB_USER,
                    password=APP_DB_PASS,
                    dbname=PG_DB,
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
            # Set Local RLS Session Variable for B2B Isolation
            tenant_id = current_tenant_var.get()
            if tenant_id:
                cur.execute("SELECT set_config('clarere.current_tenant', %s, true)", (tenant_id,))
                # Organizasyon bağlamı (multi-user paylaşımı)
                try:
                    cur.execute(
                        "SELECT set_config('clarere.current_org', m.org_id, true) FROM organization_members m WHERE m.username = %s LIMIT 1",
                        (tenant_id,),
                    )
                except Exception:
                    pass  # org tablosu henüz yoksa sessizce geç
            else:
                # Anon: tenant/org ayarlarını açıkça sıfırla (havuzdan kalıntı değer kalmasın)
                try:
                    cur.execute("RESET clarere.current_tenant; RESET clarere.current_org;")
                except Exception:
                    pass
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
    """
    from psycopg2 import sql as psql
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


def init_db() -> None:
    with get_admin_db(register_pgvector=False) as (conn, cur):
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
                    OR (org_id IS NOT NULL AND org_id = current_setting('clarere.current_org', true))
                )
                """
            )
        except Exception as e:
            print(f"[DB] Studies RLS migration warning: {e}")

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

        # Production'da bu kayıtlar X-Username backdoor riski oluşturur
        _app_env = os.getenv("APP_ENV", "development").lower()
        if _app_env != "production":
            _now = datetime.now().isoformat()
            _today = datetime.now().date().isoformat()
            _defaults = [
                ("free",       "free@example.com",       "Free",       2,      100_000),
                ("flex",       "flex@example.com",       "Flex",       3,      200_000),
                ("starter",    "starter@example.com",    "Starter",    10,     500_000),
                ("pro",        "pro@example.com",        "Pro",        9999,   9_999_999),
                ("enterprise", "enterprise@example.com", "Enterprise", 9999,   9_999_999),
            ]
            for _uname, _email, _plan, _sims, _tokens in _defaults:
                cur.execute("""
                    INSERT INTO clients (username, created_at, email, plan_type, max_simulations, max_tokens, billing_cycle, period_start, period_simulations)
                    VALUES (%s, %s, %s, %s, %s, %s, 'monthly', %s, 0)
                    ON CONFLICT (username) DO UPDATE SET
                        email           = EXCLUDED.email,
                        plan_type       = EXCLUDED.plan_type,
                        max_simulations = EXCLUDED.max_simulations,
                        max_tokens      = EXCLUDED.max_tokens,
                        billing_cycle   = EXCLUDED.billing_cycle,
                        period_start    = EXCLUDED.period_start
                """, (_uname, _now, _email, _plan, _sims, _tokens, _today))
        
        # Default system config
        cur.execute("INSERT INTO system_config (key, value) VALUES ('b2c_model', 'DeepSeek V4 Flash (deepseek-v4-flash)') ON CONFLICT (key) DO NOTHING")
        cur.execute("INSERT INTO system_config (key, value) VALUES ('b2b_model', 'DeepSeek V4 Pro (deepseek-v4-pro)') ON CONFLICT (key) DO NOTHING")
        cur.execute("INSERT INTO system_config (key, value) VALUES ('pii_active', 'true') ON CONFLICT (key) DO NOTHING")
        cur.execute("INSERT INTO system_config (key, value) VALUES ('pii_terms', 'Trendyol, Hepsiburada, Amazon') ON CONFLICT (key) DO NOTHING")
        
        # Default Prompts
        default_wizard = (
            "Sen Defne'sin, kıdemli bir Pazar Araştırması Mimarısın. Amacın kullanıcının iş fikrini hızlıca anlayıp araştırmaya hazır hale getirmek.\n\n"
            "AŞAMALI AKIŞ (SIRAYLA UYGULA):\n\n"
            "AŞAMA 1 — BİLGİ TOPLAMA (ilk 2-3 tur):\n"
            "- Kullanıcı fikrini anlattıktan sonra, brief'te halen EKSİK olan kritik alanları sor.\n"
            "- Kritik alanlar: idea (ürün/hizmet), target_users (hedef kitle), expected_price (fiyat beklentisi), success_metric (başarı kriteri).\n"
            "- Bir seferde 2 soru sorabilirsin; örneğin 'Hedef kitlen kim, hangi fiyat aralığı düşünüyorsun?' gibi. Ama 2'den fazla sorma.\n\n"
            "AŞAMA 2 — ÖZET VE ONAY (tüm kritik alanlar dolduğunda):\n"
            "- Brief'in tamamını maddeler halinde özetle.\n"
            "- Kullanıcıya 'Bu özet doğru mu? Araştırmayı başlatabilir miyiz?' diye sor.\n"
            "- Bu aşamada is_complete'i HENÜZ true yapma, kullanıcının onayını bekle.\n\n"
            "AŞAMA 3 — TAMAMLAMA (kullanıcı onay verdiğinde):\n"
            "- Kullanıcı 'evet', 'tamam', 'doğru', 'başlat', 'hazırım' gibi bir onay verirse → is_complete: true yap.\n"
            "- assistant_reply: 'Harika! Araştırmayı başlatmaya hazırız. Aşağıdaki butona tıklayarak başlayabilirsiniz.'\n\n"
            "KISMİ GÜNCELLEME (DELTA):\n"
            "- SADECE kullanıcının son mesajında verdiği yeni bilgileri 'updated_fields' objesine koy.\n"
            "- Yeni bilgi yoksa updated_fields boş obje {} olsun.\n"
            "- Şablon metin veya örnek yazma; sadece kullanıcının gerçek verdiği bilgileri al.\n\n"
            "DİL KURALLARI (KESİNLİKLE UY):\n"
            "- Samimi, akıcı, gündelik Türkçe kullan.\n"
            "- Şu kelimeler YASAK: 'spesifik', 'acı nokta', 'ekosistem', 'vertikal', 'yaşam evresi', 'konumlandırma'.\n"
            "- Kullanıcının anlattığı ürün/sektörle ilgili örnekler ver.\n"
            "- Kullanıcının belirttiği hedef kitleyi daraltma veya değiştirme.\n\n"
            "MAKSİMUM TUR: Konuşma 5 turu geçtiyse zorla is_complete: true yap.\n\n"
            "ZORUNLU JSON ÇIKTISI (BAŞKA HİÇBİR METİN EKLEME):\n"
            "{\n"
            '  "thinking": "Kullanıcının ne anlattığı, hangi alanların dolduğu, hangilerinin eksik olduğu",\n'
            '  "updated_fields": { "alan_adi": "kullanıcının verdiği gerçek değer" },\n'
            '  "assistant_reply": "Kullanıcıya gösterilecek mesaj",\n'
            '  "is_complete": false\n'
            "}"
        )
        default_persona = (
            "Sen Clarere araştırma panelindeki sentetik bir personasın. Rolünün özelliklerine, yaşına, "
            "yaşadığı şehre ve fiyat hassasiyetine tamamen uygun hareket et. Bir yapay zeka olduğunu asla söyleme. "
            "Birinci şahıstan konuş, gerçek bir insan gibi samimi ve doğrudan cevap ver. Türkiye pazarının yerel "
            "dinamiklerini (kargo, taksit, KVKK, komisyon vb.) göz önünde bulundur."
        )
        default_synthesis = (
            "[ROLE]\n"
            "Sen, pazar araştırması boru hattının (pipeline) \"Tepe Denetleyicisi ve Tematik Analist\"isin. "
            "Mülakat transkriptlerini Braun & Clarke tematik analiz çerçevesine göre kodlamak ve nesnel kanıtlara (Evidence Chain) dayalı pazar raporları üretmekle görevlisin.\n\n"
            "[BOUNDARIES (KESİN SINIRLAR)]\n"
            "- Sıfır Halüsinasyon (Zero-Shot Hallucination Ban): Transkriptte GÖREMEDİĞİN hiçbir şikayeti, fiyat itirazını veya övgüyü rapora ekleyemezsin.\n"
            "- Çekişmeli Kalite İncelemesi (Adversarial Review): Müşterinin \"Ürünüm çok güzel olacak\" varsayımını asla destekleme. Raporda en az 3 \"Kritik Başarısızlık Bariyeri\" (Barrier to Entry) belirteceksin.\n"
            "- Görev Dönüşüm Etkisi (Task-Transformation): Sentezi yazarken yapay zeka tonunu kapat. Bir McKinsey danışmanı gibi, acımasızca dürüst ve doğrudan bir profesyonel dil kullan.\n\n"
            "[OUTPUT FORMAT]\n"
            "Sadece ayrıştırılabilir JSON dön. (Markdown ```json bloğu içine ALMA).\n"
            "Şema:\n"
            "{\n"
            "  \"market_viability_score\": \"1-100\",\n"
            "  \"critical_barriers\": [\"bariyer_1\", \"bariyer_2\"],\n"
            "  \"evidence_chain\": [\n"
            "    {\"claim\": \"Kullanıcılar fiyatı yüksek buluyor\", \"quote\": \"Bu parayı vermem, çok pahalı\", \"persona\": \"Ahmet (C1)\"}\n"
            "  ],\n"
            "  \"strategic_recommendations\": [\"öneri_1\", \"öneri_2\"]\n"
            "}"
        )
        cur.execute("INSERT INTO system_config (key, value) VALUES ('wizard_prompt', %s) ON CONFLICT (key) DO NOTHING", (default_wizard,))
        cur.execute("INSERT INTO system_config (key, value) VALUES ('persona_interview_prompt', %s) ON CONFLICT (key) DO NOTHING", (default_persona,))
        cur.execute("INSERT INTO system_config (key, value) VALUES ('synthesis_prompt', %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (default_synthesis,))

        # App rolü (superuser olmayan, RLS'ye tabi) oluştur + yetkilendir
        _ensure_app_role(cur)


def save_study(metadata: dict, payload: dict) -> str:
    study_id = metadata["id"]
    # Tenant + org bilgisi (multi-user RLS için)
    created_by = current_tenant_var.get() or metadata.get("created_by") or metadata.get("username") or ""
    org_id = metadata.get("org_id") or None
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO studies (
                id, title, market, category, created_at, updated_at, archived, has_report, has_pdf,
                pdf_status, pdf_error, quality_score, quality_grade, quality_summary, brief_hash, roles_hash, cache_status,
                created_by, org_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                market = EXCLUDED.market,
                category = EXCLUDED.category,
                updated_at = EXCLUDED.updated_at,
                archived = EXCLUDED.archived,
                has_report = EXCLUDED.has_report,
                has_pdf = EXCLUDED.has_pdf,
                pdf_status = EXCLUDED.pdf_status,
                pdf_error = EXCLUDED.pdf_error,
                quality_score = EXCLUDED.quality_score,
                quality_grade = EXCLUDED.quality_grade,
                quality_summary = EXCLUDED.quality_summary,
                brief_hash = EXCLUDED.brief_hash,
                roles_hash = EXCLUDED.roles_hash,
                cache_status = EXCLUDED.cache_status
            """,
            (
                study_id,
                metadata.get("title", ""),
                metadata.get("market", ""),
                metadata.get("category", ""),
                metadata.get("created_at", datetime.now().isoformat(timespec="seconds")),
                metadata.get("updated_at", datetime.now().isoformat(timespec="seconds")),
                metadata.get("archived", False),
                metadata.get("has_report", False),
                metadata.get("has_pdf", False),
                metadata.get("pdf_status", "not_generated"),
                metadata.get("pdf_error", ""),
                metadata.get("quality_score"),
                metadata.get("quality_grade"),
                metadata.get("quality_summary"),
                metadata.get("brief_hash"),
                metadata.get("roles_hash"),
                metadata.get("cache_status"),
                created_by,
                org_id,
            ),
        )

        cur.execute(
            """
            INSERT INTO study_payloads (
                study_id, brief, roles, plan, personas, interviews, report_json, report_markdown, report_html, report_pdf, script
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (study_id) DO UPDATE SET
                brief = EXCLUDED.brief,
                roles = EXCLUDED.roles,
                plan = EXCLUDED.plan,
                personas = EXCLUDED.personas,
                interviews = EXCLUDED.interviews,
                report_json = EXCLUDED.report_json,
                report_markdown = EXCLUDED.report_markdown,
                report_html = EXCLUDED.report_html,
                report_pdf = EXCLUDED.report_pdf,
                script = EXCLUDED.script
            """,
            (
                study_id,
                json.dumps(payload.get("brief", {}), ensure_ascii=False) if payload.get("brief") else None,
                json.dumps(payload.get("roles", []), ensure_ascii=False) if payload.get("roles") else None,
                json.dumps(payload.get("plan", {}), ensure_ascii=False) if payload.get("plan") else None,
                json.dumps(payload.get("personas", []), ensure_ascii=False) if payload.get("personas") else None,
                json.dumps(payload.get("interviews", []), ensure_ascii=False) if payload.get("interviews") else None,
                json.dumps(payload.get("report_json", {}), ensure_ascii=False) if payload.get("report_json") else None,
                payload.get("report_markdown"),
                payload.get("report_html"),
                payload.get("report_pdf"),
                json.dumps(payload.get("script", []), ensure_ascii=False) if payload.get("script") else None,
            ),
        )
    return study_id


def list_studies(include_archived: bool = False) -> list[dict]:
    with get_db() as (conn, cur):
        query = "SELECT * FROM studies"
        if not include_archived:
            query += " WHERE archived = FALSE OR archived IS NULL"
        query += " ORDER BY updated_at DESC"

        cur.execute(query)
        rows = cur.fetchall()

        studies = []
        for row in rows:
            study = dict(row)
            study["archived"] = bool(study["archived"])
            study["has_report"] = bool(study["has_report"])
            study["has_pdf"] = bool(study["has_pdf"])
            studies.append(study)
        return studies


def get_study(study_id: str) -> dict | None:
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM studies WHERE id = %s", (study_id,))
        row = cur.fetchone()
        if not row:
            return None
        study = dict(row)
        study["archived"] = bool(study["archived"])
        study["has_report"] = bool(study["has_report"])
        study["has_pdf"] = bool(study["has_pdf"])
        return study


def load_study_payload(study_id: str, include_pdf: bool = False) -> dict:
    with get_db() as (conn, cur):
        # PDF BYTEA'yı sadece gerektiğinde çek (bellek israfını önle)
        _cols = "brief, roles, plan, personas, interviews, report_json, report_markdown, report_html, script"
        if include_pdf:
            _cols += ", report_pdf"
        cur.execute(f"SELECT {_cols} FROM study_payloads WHERE study_id = %s", (study_id,))  # noqa: S608

        row = cur.fetchone()

        payload = {}
        if row:
            for key in ["brief", "roles", "plan", "personas", "interviews", "report_json", "script"]:
                val = row.get(key)
                if val:
                    try:
                        payload[key] = json.loads(val)
                    except json.JSONDecodeError:
                        payload[key] = None
            payload["report_markdown"] = row.get("report_markdown")
            payload["report_html"] = row.get("report_html")
            if include_pdf:
                payload["report_pdf"] = row.get("report_pdf")

        study = get_study(study_id)
        if study:
            payload["metadata"] = study

        return payload


def archive_study(study_id: str) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            "UPDATE studies SET archived = TRUE, updated_at = %s WHERE id = %s",
            (datetime.now().isoformat(timespec="seconds"), study_id),
        )


def delete_study(study_id: str) -> bool:
    """Kullanıcı tarafından silinen araştırmayı listeden gizler (soft delete).

    Veriler fiziksel olarak silinmez; archived=TRUE yapılır.
    İç araştırma/analiz amaçlı DB’de korunur.

    Returns:
        True  → işlem başarılı
        False → study_id bulunamadı
    """
    with get_db() as (conn, cur):
        cur.execute(
            "UPDATE studies SET archived = TRUE, updated_at = %s WHERE id = %s",
            (datetime.now().isoformat(timespec="seconds"), study_id),
        )
        return cur.rowcount > 0


def update_pdf_status(study_id: str, status: str, error: str = "") -> None:
    with get_db() as (conn, cur):
        cur.execute(
            "UPDATE studies SET has_pdf = %s, pdf_status = %s, pdf_error = %s, updated_at = %s WHERE id = %s",
            (
                True if status == "generated" else False,
                status,
                error,
                datetime.now().isoformat(timespec="seconds"),
                study_id,
            ),
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
        cur.execute("UPDATE clients SET period_start = %s, period_simulations = 0 WHERE username = %s",
                    (datetime.now(timezone.utc).date().isoformat(), username))
        return

    period_start = datetime.fromisoformat(period_start_str).date()
    today = datetime.now(timezone.utc).date()  # timezone-aware
    days_in_period = 365 if billing_cycle == "annual" else 30

    if (today - period_start).days >= days_in_period:
        # Yeni dönem: sayıcıyı sıfırla ve period_start'i güncelle
        new_start = period_start + timedelta(days=days_in_period)
        cur.execute(
            "UPDATE clients SET period_start = %s, period_simulations = 0 WHERE username = %s",
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
    from .plan_config import get_plan_config
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


def register_client_if_new(username: str, email: str = "") -> tuple[dict, bool]:
    """Kullanıcı yoksa Free planla kayıt eder. Varsa mevcut kaydı döner.
    Returns: (client_dict, was_created)"""
    from .plan_config import get_plan_config
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


def log_ai_rationale(prompt_hash: str, model_id: str, thinking_text: str, response_text: str) -> None:
    """Log the <thinking> block to the database for transparency and auditing."""
    if not thinking_text:
        return
    try:
        with get_db() as (conn, cur):
            cur.execute(
                """
                INSERT INTO ai_rationales (prompt_hash, model_id, thinking_text, response_text)
                VALUES (%s, %s, %s, %s)
                """,
                (prompt_hash, model_id, thinking_text, response_text)
            )
    except Exception as e:
        logger.error(f"Failed to log AI rationale: {e}")


def save_findings(study_id: str, findings: list) -> list[dict]:
    """Bir araştırmaya ait EnhancedFinding listesini research_findings ve
    research_evidence tablolarına kaydeder. Dönen listede her finding'in DB id'si bulunur."""
    saved: list[dict] = []
    with get_db() as (conn, cur):
        # Eski bulguları ve kanıtları temizle (idempotent yeniden kayıt)
        cur.execute(
            "DELETE FROM research_findings WHERE study_id = %s", (study_id,)
        )
        for f in findings:
            cur.execute(
                """
                INSERT INTO research_findings (
                    study_id, title, category, summary, confidence, implication,
                    supporting_count, refuting_count, neutral_count,
                    contradiction_score, decision_signal
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    study_id,
                    f.title,
                    f.category,
                    f.summary,
                    f.confidence,
                    f.implication,
                    getattr(f, "supporting_count", 0),
                    getattr(f, "refuting_count", 0),
                    getattr(f, "neutral_count", 0),
                    getattr(f, "contradiction_score", 0.0),
                    getattr(f, "decision_signal", "INVESTIGATE"),
                ),
            )
            finding_row = cur.fetchone()
            if not finding_row:
                continue
            finding_id = finding_row["id"]
            finding_dict = {
                "id": finding_id,
                "title": f.title,
                "category": f.category,
                "summary": f.summary,
                "confidence": f.confidence,
                "implication": f.implication,
                "supporting_count": getattr(f, "supporting_count", 0),
                "refuting_count": getattr(f, "refuting_count", 0),
                "neutral_count": getattr(f, "neutral_count", 0),
                "contradiction_score": getattr(f, "contradiction_score", 0.0),
                "decision_signal": getattr(f, "decision_signal", "INVESTIGATE"),
            }

            # Kanıtları kaydet
            for ev in f.evidence:
                sentiment = getattr(ev, "sentiment", "neutral")
                cur.execute(
                    """
                    INSERT INTO research_evidence (
                        finding_id, persona_id, persona_name, stance,
                        question, quote, sentiment
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        finding_id,
                        ev.persona_id,
                        ev.persona_name,
                        ev.stance,
                        ev.source_question,
                        ev.quote,
                        sentiment,
                    ),
                )
            saved.append(finding_dict)
    return saved


def get_findings(study_id: str) -> list[dict]:
    """Bir araştırmaya ait tüm bulguları (kanıt sayılarıyla birlikte) döner."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT id, title, category, summary, confidence, implication,
                   supporting_count, refuting_count, neutral_count,
                   contradiction_score, decision_signal, created_at
            FROM research_findings
            WHERE study_id = %s
            ORDER BY id
            """,
            (study_id,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def get_finding_detail(study_id: str, finding_id: int) -> dict | None:
    """Tek bir bulgunun tüm kanıt alıntılarıyla birlikte detayını döner."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT id, title, category, summary, confidence, implication,
                   supporting_count, refuting_count, neutral_count,
                   contradiction_score, decision_signal, created_at
            FROM research_findings
            WHERE study_id = %s AND id = %s
            """,
            (study_id, finding_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        finding = dict(row)
        cur.execute(
            """
            SELECT id, persona_id, persona_name, stance, question, quote, sentiment, created_at
            FROM research_evidence
            WHERE finding_id = %s
            ORDER BY id
            """,
            (finding_id,),
        )
        evidence_rows = cur.fetchall()
        finding["evidence"] = [dict(ev) for ev in evidence_rows]
        return finding


# Initial DB setup
try:
    init_db()
except Exception as e:
    print(f"[DB] Initial DB setup failed, Postgres might not be running yet: {e}")
