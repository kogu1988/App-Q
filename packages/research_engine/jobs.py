"""Celery görevleri — uzun süren araştırma işleri (P0-1 Aşama 2).

Web süreci yalnızca kuyruğa ekler; çalıştırma Celery worker'da olur. Böylece
60 saniyelik araştırma API'nin threadpool'unu meşgul etmez.
"""
from __future__ import annotations

import logging

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="clarere.run_research_job", bind=True, max_retries=0)
def run_research_job(self, job_id: str, payload: dict, username: str, plan_type: str) -> dict:
    """Araştırma job'ını çalıştırır ve sonucu `research_jobs` tablosuna yazar."""
    from .database import update_research_job
    from .research_runner import execute_research

    update_research_job(job_id, status="running", progress=1)

    try:
        result = execute_research(
            payload,
            username,
            plan_type,
            on_progress=lambda value: update_research_job(job_id, progress=value),
        )
    except Exception as exc:
        logger.error("Araştırma job'ı başarısız: %s", job_id, exc_info=True)
        update_research_job(job_id, status="failed", error=str(exc))
        raise

    update_research_job(job_id, status="completed", progress=100, result=result)
    return {"job_id": job_id, "status": "completed"}
