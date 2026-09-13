"""Sprint 3 — Ürün KPI event kaydı ve funnel özeti testleri (DB gerektirir)."""
from __future__ import annotations

import uuid

import pytest


def _db_available() -> bool:
    try:
        from packages.research_engine.database import get_db

        with get_db() as (_conn, cur):
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="Canlı PostgreSQL gerekli")


def test_record_and_summarize_product_events():
    from packages.research_engine.database import get_product_event_summary, record_product_event

    user = f"events_test_{uuid.uuid4().hex[:8]}"
    record_product_event("research_started", username=user)
    record_product_event("research_completed", username=user)
    record_product_event("report_synthesized", username=user)

    summary = get_product_event_summary(days=1)

    assert isinstance(summary["counts"], dict)
    assert summary["counts"].get("research_started", 0) >= 1
    assert 0.0 <= summary["research_completion_rate"] <= 1.0
    assert 0.0 <= summary["report_rate"] <= 1.0


def test_record_product_event_is_failsafe_without_event_name():
    from packages.research_engine.database import record_product_event

    # Boş event adı sessizce yok sayılmalı (istisna fırlatmaz).
    record_product_event("", username="x")
