"""Varsayilan kayitlar: sistem ayarlari, prompt'lar, dev demo kullanicilar (refactor R5-2)."""
from __future__ import annotations

import logging
import os
from datetime import datetime

from ..connection import _ensure_app_role
from .prompts import DEFAULT_WIZARD_PROMPT

logger = logging.getLogger(__name__)


def seed_defaults(conn, cur) -> None:
    # — P0-1 (Aşama 2): Araştırma job kuyruğu —
    # Uzun süren (≥30 sn) araştırmalar Celery'ye devredilir; API bloke olmaz.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS research_jobs (
            job_id     TEXT PRIMARY KEY,
            username   TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT 'queued',
            progress   INTEGER DEFAULT 0,
            result     TEXT,
            error      TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    try:
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_jobs_user "
            "ON research_jobs(username, created_at DESC);"
        )
    except Exception as e:
        print(f"[DB] research_jobs index warning: {e}")

    # — Token usage indeksleri (migration 004) —
    # Kullanıcı bazlı maliyet sorguları ve tarih filtreleri için.
    try:
        cur.execute(
            "SELECT version FROM schema_migrations WHERE version = '004-token-usage-indexes'"
        )
        if not cur.fetchone():
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_token_usage_user_date "
                "ON token_usage(username, created_at DESC);"
            )
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES ('004-token-usage-indexes')"
            )
            logger.info("Migration 004-token-usage-indexes uygulandı")
    except Exception as e:
        logger.warning("Migration 004-token-usage-indexes atlandı: %s", e)

    # — Evidence Chain indeksleri (migration 005) —
    # Bulgu ve kanıt sorguları study/finding bazlı; indekssiz büyük veride yavaşlar.
    try:
        cur.execute(
            "SELECT version FROM schema_migrations WHERE version = '005-evidence-indexes'"
        )
        if not cur.fetchone():
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_research_findings_study "
                "ON research_findings(study_id);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_research_evidence_finding "
                "ON research_evidence(finding_id);"
            )
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES ('005-evidence-indexes')"
            )
            logger.info("Migration 005-evidence-indexes uygulandı")
    except Exception as e:
        logger.warning("Migration 005-evidence-indexes atlandı: %s", e)

    # Production'da bu kayıtlar X-Username backdoor riski oluşturur.
    # Dev'de demo kullanıcılar DETERMİNİSTİK fixture'dır: plan/limitleri VE deneme
    # penceresi her başlatmada senkronize edilir (aksi halde eski bir plan kaydı
    # kalıcı olur, ör. `free` kullanıcısı yanlışlıkla Flex kalır — ya da eski
    # `created_at` yüzünden Free deneme süresi dolar ve demo yapılamaz).
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
                    email = EXCLUDED.email,
                    plan_type = EXCLUDED.plan_type,
                    max_simulations = EXCLUDED.max_simulations,
                    max_tokens = EXCLUDED.max_tokens,
                    created_at = EXCLUDED.created_at,
                    period_start = EXCLUDED.period_start,
                    period_simulations = EXCLUDED.period_simulations
            """, (_uname, _now, _email, _plan, _sims, _tokens, _today))

    # Default system config
    cur.execute("INSERT INTO system_config (key, value) VALUES ('b2c_model', 'DeepSeek Flash (deepseek-flash)') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO system_config (key, value) VALUES ('b2b_model', 'DeepSeek V4 Pro (deepseek-v4-pro)') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO system_config (key, value) VALUES ('pii_active', 'true') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO system_config (key, value) VALUES ('pii_terms', 'Trendyol, Hepsiburada, Amazon') ON CONFLICT (key) DO NOTHING")

    # Default Prompts
    default_wizard = DEFAULT_WIZARD_PROMPT
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

    # Multi-user organizasyon tabloları (Enterprise) — DDL admin bağlantısı gerektirir.
    # _ensure_app_role'dan ÖNCE oluşturulur ki "GRANT ... ON ALL TABLES" kapsamına girsin.
    try:
        from ...db_org import _create_org_tables

        _create_org_tables(cur)
    except Exception as e:
        logger.warning("Org tabloları oluşturulamadı (multi_user devre dışı kalabilir): %s", e)

    # App rolü (superuser olmayan, RLS'ye tabi) oluştur + yetkilendir
    _ensure_app_role(cur)
