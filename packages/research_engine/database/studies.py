"""Calisma (study) CRUD, PDF durumu ve arastirma job kuyrugu (refactor R5-4)."""
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
        cur.execute(f"SELECT {_cols} FROM study_payloads WHERE study_id = %s", (study_id,))

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

            # report_json'ı üst seviyeye yay — frontend structured kartları
            # (van_westendorp, ses_cross_tab, brand_health, research_quality,
            # channel_map, findings, decision_items vb.) doğrudan study.<alan>
            # olarak okur; brief/plan/personas/interviews ayrı saklandığı için ezilmez.
            _report_json = payload.get("report_json")
            if isinstance(_report_json, dict):
                for _k, _v in _report_json.items():
                    if _k in ("plan", "personas", "interviews", "title"):
                        continue
                    payload.setdefault(_k, _v)

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





def create_research_job(job_id: str, username: str) -> None:
    """Yeni bir araştırma job'ı kaydeder (status=queued)."""
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO research_jobs (job_id, username, status, progress)
            VALUES (%s, %s, 'queued', 0)
            ON CONFLICT (job_id) DO NOTHING
            """,
            (job_id, username),
        )


def update_research_job(
    job_id: str,
    status: str | None = None,
    progress: int | None = None,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    """Job durumunu günceller. Hata araştırmayı çökertmez (fail-safe)."""
    import json as _json

    sets: list[str] = ["updated_at = NOW()"]
    params: list = []
    if status is not None:
        sets.append("status = %s")
        params.append(status)
    if progress is not None:
        sets.append("progress = %s")
        params.append(int(progress))
    if result is not None:
        sets.append("result = %s")
        params.append(_json.dumps(result, ensure_ascii=False, default=str))
    if error is not None:
        sets.append("error = %s")
        params.append(error[:1000])

    params.append(job_id)
    try:
        with get_db() as (conn, cur):
            cur.execute(
                f"UPDATE research_jobs SET {', '.join(sets)} WHERE job_id = %s",
                tuple(params),
            )
    except Exception:
        logger.warning("research_jobs güncellenemedi (job=%s)", job_id, exc_info=True)


def get_research_job(job_id: str) -> dict | None:
    """Job durumunu ve (varsa) sonucunu döner."""
    import json as _json

    with get_db() as (conn, cur):
        cur.execute(
            "SELECT job_id, username, status, progress, result, error, created_at, updated_at "
            "FROM research_jobs WHERE job_id = %s",
            (job_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)

    raw_result = data.get("result")
    if raw_result:
        try:
            data["result"] = _json.loads(raw_result)
        except Exception:
            logger.warning("research_jobs result ayrıştırılamadı (job=%s)", job_id, exc_info=True)
            data["result"] = None
    return data


