"""Client API router'i (R6).

Endpoint aileleri alt router'lara ayrildi; ust router bunlari birlestirir.
Cagri yerleri (main.py) ve testlerin import ettigi isimler degismedi.
"""
from fastapi import APIRouter

from . import account, context, intake, interaction, research, studies, synthesis, ws

router = APIRouter()
router.include_router(account.router)
router.include_router(studies.router)
router.include_router(research.router)
router.include_router(synthesis.router)
router.include_router(interaction.router)
router.include_router(intake.router)
router.include_router(ws.router)

# Geriye donuk uyumluluk (testler ve dis moduller bu isimleri import eder)
from ._deps import (
    _DELETE_CONFIRM_TOKEN,
    FollowUpRequest,
    _build_persona_tolerant,
    _effective_plan,
    _enforce_token_budget,
    _record_usage,
    _require_delete_confirmation,
    _require_feature,
    _resolve_plan,
    is_trial_expired,
    limiter,
    logger,
)
from ._schemas import (
    BriefRequest,
    FeedbackCreate,
    GeneratePersonasRequest,
    IntakeChatRequest,
    PersonaCreate,
    PersonaSearch,
    RegisterRequest,
    ResearchRequest,
    StudioSimulationRequest,
    StudyPayload,
    SynthesizeRequest,
    UpgradePlanRequest,
)
from .account import (
    AccountDeleteRequest,
    contact_form,
    delete_my_account,
    export_my_data,
    get_me,
    register,
    submit_feedback,
    track_event,
    upgrade_plan,
)
from .context import build_research_context
from .intake import (
    create_persona,
    get_studio_simulation_status,
    intake_chat,
    list_personas,
    match_personas,
    trigger_studio_simulation,
)
from .interaction import (
    research_chat,
    study_follow_up,
)
from .research import (
    create_plan,
    generate_personas_from_plan,
    get_research_job_status,
    run_full_research,
    start_research_job,
    stream_interviews,
)
from .studies import (
    archive_study_endpoint,
    create_or_update_study,
    delete_study_endpoint,
    download_study_pdf,
    get_finding_detail_endpoint,
    get_findings_endpoint,
    get_studies,
    get_study,
)
from .synthesis import (
    _synthesize_impl,
    synthesize,
)
from .ws import (
    generate_ws_ticket,
    ws_synthesis_status,
)
