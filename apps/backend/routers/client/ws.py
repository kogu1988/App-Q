"""Websocket ticket ve sentez durumu akisi (R6-5)."""
import json
import logging
import os
from dataclasses import asdict
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from packages.research_engine.analytics import synthesize_report
from packages.research_engine.database import (
    archive_study,
    atomic_increment_simulation_count,
    check_simulation_limit,
    check_token_budget,
    count_chat_messages,
    count_user_non_ab_simulations,
    create_research_job,
    delete_study,
    delete_user_data,
    export_user_data,
    get_client_by_username,
    get_current_username,
    get_finding_detail,
    get_findings,
    get_research_job,
    list_studies,
    load_study_payload,
    record_token_usage,
    register_client_if_new,
    save_feedback,
    save_findings,
    save_study,
    upgrade_client_plan,
)
from packages.research_engine.db_vectors import get_personas_pool, save_persona_to_pool
from packages.research_engine.intake import process_intake_chat
from packages.research_engine.plan_config import (
    get_max_personas,
    get_min_plan_for_feature,
    get_plan_config,
    has_feature,
)
from packages.research_engine.privacy import PrivacyMasker, PrivacyResearchModelWrapper
from packages.research_engine.providers import get_model_provider
from packages.research_engine.workflow import (
    build_research_plan,
    generate_personas,
    run_interviews_batch,
    run_interviews_stream,
)

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

router = APIRouter()

@router.post("/ws/ticket")
@limiter.limit("20/minute")
def generate_ws_ticket(request: Request, x_username: str | None = Depends(get_current_username)):
    """
    Generates a 10-second single-use ticket for WebSocket authentication.
    """
    import os
    import uuid

    import redis

    VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")
    ticket = str(uuid.uuid4())
    username = x_username or "anonymous"
    try:
        r = redis.from_url(VALKEY_URL)
        # Store ticket mapping to username, expire in 10 seconds
        r.setex(f"ws_ticket:{ticket}", 10, username)
        return {"ticket": ticket, "expires_in": 10}
    except Exception as e:
        logger.error(f"Failed to generate WS ticket: {e}")
        raise HTTPException(status_code=500, detail="Bağlantı bileti üretilemedi. Lütfen tekrar deneyin.")

from fastapi import WebSocket, WebSocketDisconnect


@router.websocket("/ws/synthesis/{research_id}")
async def ws_synthesis_status(websocket: WebSocket, research_id: str, ticket: str = Query(...)):
    """
    Streams the thematic synthesis status and JSON payload to the client via Redis Pub/Sub.
    """
    import asyncio
    import os

    import redis as sync_redis
    import redis.asyncio as aioredis

    VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")

    # Authenticate ticket
    try:
        r_sync = sync_redis.from_url(VALKEY_URL)
        ticket_key = f"ws_ticket:{ticket}"
        username = r_sync.get(ticket_key)

        if not username:
            await websocket.close(code=1008, reason="Bağlantı biletiniz geçersiz veya süresi dolmuş. Lütfen sayfayı yenileyin.")
            return

        # Delete ticket so it's single use
        r_sync.delete(ticket_key)
    except Exception as e:
        logger.error(f"Ticket auth error: {e}")
        await websocket.close(code=1011, reason="Sunucu hatası.")
        return

    # Accept connection
    await websocket.accept()
    logger.info(f"WebSocket connected for synthesis {research_id}")

    r_async = None
    pubsub = None
    try:
        r_async = aioredis.from_url(VALKEY_URL)
        pubsub = r_async.pubsub()
        channel = f"synthesis_status:{research_id}"
        await pubsub.subscribe(channel)

        async for message in pubsub.listen():
            if message["type"] == "message":
                data_str = message["data"].decode("utf-8")
                await websocket.send_text(data_str)

                # Close if completed or failed
                try:
                    payload = json.loads(data_str)
                    if payload.get("status") in ("completed", "failed"):
                        await asyncio.sleep(0.5)
                        break
                except (json.JSONDecodeError, TypeError):
                    # Beklenen: yayınlanan mesaj JSON değilse yok say (protokol toleransı).
                    logger.debug("Synthesis WS: JSON olmayan mesaj atlandı.")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for synthesis {research_id}")
    except Exception as e:
        logger.error(f"WebSocket error for synthesis {research_id}: {e}")
    finally:
        if pubsub:
            try:
                await pubsub.unsubscribe()
            except Exception:
                logger.debug("WS pubsub unsubscribe başarısız (zaten kapalı olabilir).")
        try:
            await websocket.close()
        except Exception:
            # Bağlantı zaten kapanmış olabilir; kapanış hatası beklenen durumdur.
            logger.debug("WS close sırasında beklenen hata (bağlantı kapanmış).")
