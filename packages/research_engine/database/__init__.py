"""Veritabani katmani (refactor R5).

Eskiden tek dosya olan database.py, sorumluluk bazinda pakete bolundu.
Cagri yerleri degismesin diye tum genel isimler buradan yeniden disa verilir.
"""
from .billing import (
    add_flex_credits,
    already_processed_paddle_event,
    delete_user_data,
    export_user_data,
    find_client_by_paddle_subscription,
    get_last_event_occurred_at,
    record_paddle_event,
    update_client_subscription,
)
from .clients import (
    atomic_increment_simulation_count,
    check_and_reset_period,
    check_simulation_limit,
    count_chat_messages,
    count_user_non_ab_simulations,
    get_audit_logs,
    get_client_by_username,
    get_client_password_hash,
    get_feedbacks,
    get_system_config,
    increment_simulation_count,
    log_audit,
    register_client_if_new,
    save_feedback,
    set_client_password,
    update_system_config,
    upgrade_client_plan,
)
from .connection import (
    APP_DB_PASS,
    APP_DB_USER,
    PG_DB,
    PG_HOST,
    PG_PASS,
    PG_PORT,
    PG_USER,
    _ensure_app_role,
    _get_app_pool,
    _get_pool,
    current_tenant_var,
    get_admin_db,
    get_current_username,
    get_db,
    logger,
)
from .events import (
    get_product_event_summary,
    record_product_event,
)
from .findings import (
    get_finding_detail,
    get_findings,
    log_ai_rationale,
    save_findings,
)
from .migrations import DEFAULT_WIZARD_PROMPT, init_db
from .studies import (
    archive_study,
    create_research_job,
    delete_study,
    get_research_job,
    get_study,
    list_studies,
    load_study_payload,
    save_study,
    update_pdf_status,
    update_research_job,
)
from .usage import (
    check_token_budget,
    get_token_usage_summary,
    record_token_usage,
)

# Initial DB setup (eski database.py ile ayni davranis: import aninda init denenir)
try:
    init_db()
except Exception as e:
    print(f"[DB] Initial DB setup failed, Postgres might not be running yet: {e}")
