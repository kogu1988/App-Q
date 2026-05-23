from __future__ import annotations
from datetime import datetime
from .database import get_db

def get_clients() -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM clients")
        return [dict(row) for row in cur.fetchall()]

def update_client_usage(username: str, sim_increment: int = 1, tokens: int = 0) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            UPDATE clients 
            SET total_simulations = total_simulations + %s, 
                tokens_used = tokens_used + %s
            WHERE username = %s
            """,
            (sim_increment, tokens, username)
        )

def add_client(username: str, email: str, plan_type: str, max_sims: int, max_tokens: int, plan_start: str = None, plan_end: str = None) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO clients (username, email, plan_type, max_simulations, max_tokens, plan_start, plan_end, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                email,
                plan_type,
                max_sims,
                max_tokens,
                plan_start or datetime.now().strftime("%Y-%m-%d"),
                plan_end or "",
                datetime.now().isoformat(timespec="seconds")
            )
        )

def update_client(username: str, email: str, plan_type: str, max_sims: int, max_tokens: int, plan_start: str, plan_end: str, status: str) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            UPDATE clients
            SET email = %s,
                plan_type = %s,
                max_simulations = %s,
                max_tokens = %s,
                plan_start = %s,
                plan_end = %s,
                status = %s
            WHERE username = %s
            """,
            (email, plan_type, max_sims, max_tokens, plan_start, plan_end, status, username)
        )

def delete_client(username: str) -> None:
    with get_db() as (conn, cur):
        cur.execute("DELETE FROM clients WHERE username = %s", (username,))
