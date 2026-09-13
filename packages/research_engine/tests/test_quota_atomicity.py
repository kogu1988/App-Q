"""GRUP 4 — Atomik Kota (TOCTOU Güvenliği) testleri.

Korunan değer: Finansal bütünlük. `UPDATE ... RETURNING` pattern'i doğru yapılmış;
naif `SELECT → if → UPDATE` refaktörüne dönülürse kullanıcı limitini aşar.

Gereksinim: Canlı PostgreSQL. Yoksa DB gerektiren testler `pytest.skip` ile atlanır
(test_rls_isolation.py deseni).
"""
from __future__ import annotations

import pathlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest


def _db_available() -> bool:
    try:
        from packages.research_engine.database import get_db

        with get_db() as (_conn, cur):
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


DB_REQUIRED = pytest.mark.skipif(not _db_available(), reason="Canlı PostgreSQL gerekli")

TEST_USER = "quota_atomicity_test"


def _prepare_user(simulations: int = 0, period_start: str | None = None) -> None:
    from packages.research_engine.database import get_db

    # NOT: Varsayılan period_start BUGÜN olmalı. Sabit geçmiş bir tarih verilirse
    # check_and_reset_period() dönem devri algılar ve sayacı sıfırlar (zaman-bağımlı
    # kırılganlık). Dönem devrini test etmek için period_start açıkça verilir (bkz. 4.4).
    effective_start = period_start or datetime.now(timezone.utc).date().isoformat()

    with get_db() as (conn, cur):
        cur.execute("DELETE FROM clients WHERE username = %s", (TEST_USER,))
        cur.execute(
            """
            INSERT INTO clients (username, created_at, email, plan_type, max_simulations,
                                 max_tokens, billing_cycle, period_start, period_simulations)
            VALUES (%s, NOW(), %s, 'Free', 2, 100000, 'monthly', %s, %s)
            """,
            (TEST_USER, f"{TEST_USER}@example.com", effective_start, simulations),
        )


def _cleanup() -> None:
    from packages.research_engine.database import get_db

    with get_db() as (conn, cur):
        cur.execute("DELETE FROM clients WHERE username = %s", (TEST_USER,))


@DB_REQUIRED
def test_4_1_counter_increments_on_single_call():
    """Tek çağrı dönemsel simülasyon sayacını 1 artırmalı."""
    from packages.research_engine.database import get_client_by_username, increment_simulation_count

    try:
        _prepare_user(simulations=0)
        increment_simulation_count(TEST_USER)
        client = get_client_by_username(TEST_USER)
        assert client["period_simulations"] == 1
    finally:
        _cleanup()


@DB_REQUIRED
def test_4_2_concurrent_calls_increment_exactly_once_each():
    """Eşzamanlı 10 çağrı tam 10 artış üretmeli (race condition yok)."""
    from packages.research_engine.database import get_client_by_username, increment_simulation_count

    try:
        _prepare_user(simulations=0)
        with ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(lambda _: increment_simulation_count(TEST_USER), range(10)))

        client = get_client_by_username(TEST_USER)
        assert client["period_simulations"] == 10, f"beklenen 10, gelen {client['period_simulations']}"
    finally:
        _cleanup()


@DB_REQUIRED
def test_4_3_limit_exceeded_is_rejected():
    """Limit dolduğunda check_simulation_limit False dönmeli."""
    from packages.research_engine.database import check_simulation_limit

    try:
        _prepare_user(simulations=2)  # Free plan limiti = 2
        can_run, used, max_s = check_simulation_limit(TEST_USER)
        assert can_run is False
        assert used == 2
        assert max_s == 2
    finally:
        _cleanup()


@DB_REQUIRED
def test_4_4_period_rollover_resets_counter():
    """period_start geçmişteyse sayaç sıfırlanmalı."""
    from packages.research_engine.database import check_simulation_limit

    try:
        _prepare_user(simulations=2, period_start="2020-01-01")
        can_run, used, _ = check_simulation_limit(TEST_USER)
        assert used == 0, "dönem devri sayacı sıfırlamalı"
        assert can_run is True
    finally:
        _cleanup()


def test_4_5_atomic_update_returning_pattern_is_used():
    """Kaynak kodda atomik UPDATE...RETURNING kullanılmalı (naif SELECT→UPDATE değil)."""
    source = pathlib.Path("packages/research_engine/database/clients.py").read_text(encoding="utf-8")

    assert "atomic_increment_simulation_count" in source
    assert "RETURNING period_simulations, max_simulations" in source, (
        "atomik artırma RETURNING kullanmalı"
    )
