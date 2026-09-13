"""init_db() orkestratoru (refactor R5-2)."""
from ..connection import get_admin_db
from .prompts import DEFAULT_WIZARD_PROMPT
from .schema_core import apply_core_schema
from .schema_infra import apply_infra_schema
from .seed import seed_defaults


def init_db() -> None:
    with get_admin_db(register_pgvector=False) as (conn, cur):
        apply_core_schema(conn, cur)
        apply_infra_schema(conn, cur)
        seed_defaults(conn, cur)
