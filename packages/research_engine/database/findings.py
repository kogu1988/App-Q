"""Kanit zinciri (bulgular/kanit) ve AI gerekce kaydi (refactor R5)."""
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

