"""Client router ortak bagimliliklari: plan cozumu, kota, limitler (R6-6)."""
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

logger = logging.getLogger(__name__)

# Limiter, main.py'deki app.state.limiter ile uyumlu
limiter = Limiter(key_func=get_remote_address)


class FollowUpRequest(BaseModel):
    persona_id: str
    question: str


def is_trial_expired(client: dict | None) -> tuple[bool, str]:
    """Free plan trial expiration checker: 1 month OR 2 researches (whichever comes first, excluding A/B tests)."""
    if not client or client.get("plan_type") != "Free":
        return False, ""

    # 1. Check 1 month limit since created_at
    created_at_val = client.get("created_at")
    if created_at_val:
        try:
            from datetime import datetime, timezone
            # Handle both string and datetime objects
            if isinstance(created_at_val, datetime):
                created_at = created_at_val
            elif "T" in str(created_at_val):
                created_at = datetime.fromisoformat(str(created_at_val))
            else:
                created_at = datetime.strptime(str(created_at_val), "%Y-%m-%d")

            if created_at.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now()

            elapsed = now - created_at
            if elapsed.days >= 30:
                return True, "1 aylık ücretsiz deneme süreniz dolmuştur. Devam etmek için lütfen bir plan seçin."
        except Exception as e:
            logger.error(f"Error parsing created_at for client {client.get('username')}: {e}")

    # 2. Check 2 researches limit (excluding A/B tests)
    username = client.get("username")
    if username:
        non_ab_sims = count_user_non_ab_simulations(username)
        if non_ab_sims >= 2:
            return True, "Deneme sürümündeki 2 ücretsiz araştırma limitine ulaştınız. Devam etmek için lütfen bir plan seçin."

    return False, ""


def _effective_plan(client: dict) -> str:
    """Abonelik durumuna göre geçerli planı döner (P0-2).

    - active / trialing / past_due → plan korunur (past_due'da erişim kesilmez)
    - paused / canceled          → Free'ye düşürülür
    """
    plan_type = client.get("plan_type") or "Free"
    status = (client.get("subscription_status") or "").lower()
    if status in {"paused", "canceled"}:
        return "Free"
    return plan_type


def _resolve_plan(x_username: str | None) -> tuple[str, dict]:
    """Header'dan username al, plan tipini ve config'ini döner. Kullanıcı bulunamazsa Free plan uygular."""
    plan_type = "Free"
    if x_username:
        client = get_client_by_username(x_username)
        if client:
            plan_type = _effective_plan(client)
    return plan_type, get_plan_config(plan_type)


def _require_feature(plan_type: str, feature: str) -> None:
    """Özellik plan'da yoksa HTTP 403 fırlatır."""
    if not has_feature(plan_type, feature):
        min_plan = get_min_plan_for_feature(feature)
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PLAN_GATE",
                "feature": feature,
                "current_plan": plan_type,
                "required_plan": min_plan,
                "message": "Bu özellik güncel planınızda bulunmuyor.",
            },
        )


def _enforce_token_budget(username: str | None, plan_type: str) -> None:
    """Dönemsel token bütçesi aşıldıysa 429 fırlatır (P0-6).

    Muhasebe hatasında fail-open davranır — kullanıcı, altyapı sorunu yüzünden engellenmez.
    """
    allowed, used, limit = check_token_budget(username, plan_type)
    if allowed:
        return
    raise HTTPException(
        status_code=429,
        detail={
            "code": "TOKEN_BUDGET_EXCEEDED",
            "used": used,
            "limit": limit,
            "current_plan": plan_type,
            "message": (
                "Bu dönem için token bütçeniz doldu. "
                "Planınızı yükselterek araştırmaya devam edebilirsiniz."
            ),
        },
    )


def _record_usage(username: str | None, model, operation: str, study_id: str | None = None) -> None:
    """LLM çağrı(lar)ının token kullanımını kaydeder. Hata araştırmayı çökertmez."""
    try:
        usage = getattr(model, "cumulative_usage", None) or getattr(model, "last_usage", None) or {}
        model_id = getattr(model, "model_id", None) or getattr(model, "last_model_id", None) or ""
        record_token_usage(
            username=username or "",
            model_id=model_id,
            operation=operation,
            usage=usage,
            study_id=study_id,
        )
    except Exception:
        logger.debug("Token kullanımı kaydedilemedi.", exc_info=True)


# ── KVKK / GDPR: hesap silme onayı ──

_DELETE_CONFIRM_TOKEN = "DELETE"


def _require_delete_confirmation(value: str) -> None:
    """Hesap silme için açık onay zorunlu (yanlışlıkla silmeyi önler)."""
    if (value or "").strip().upper() != _DELETE_CONFIRM_TOKEN:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CONFIRMATION_REQUIRED",
                "message": (
                    "Hesabı silmek için 'confirm' alanına "
                    f"'{_DELETE_CONFIRM_TOKEN}' yazılmalıdır."
                ),
            },
        )



def _build_persona_tolerant(p: dict):
    """Eksik alanları varsayılanla doldurarak Persona dataclass'ı kurar (500 yerine tolerant)."""
    from packages.research_engine.models import Persona
    return Persona(
        id=p.get("id") or f"p_{abs(hash(str(p.get('name', '')))) % 100000}",
        name=p.get("name") or "Katılımcı",
        age=p.get("age") or 30,
        city=p.get("city") or "İstanbul",
        segment=p.get("segment") or "Genel",
        stance=p.get("stance") or "Mainstream",
        price_sensitivity=p.get("price_sensitivity") or 5,
        digital_confidence=p.get("digital_confidence") or 5,
        context=p.get("context") or "",
        goals=p.get("goals") or [],
        objections=p.get("objections") or [],
        knowledge_boundary=p.get("knowledge_boundary") or "",
        country_code=p.get("country_code") or "TR",
        origin_country=p.get("origin_country") or "Türkiye",
        role_title=p.get("role_title") or "",
        bio=p.get("bio") or "",
        attributes=p.get("attributes") or {},
        traits=p.get("traits") or {},
        ses_group=p.get("ses_group") or "C1",
        respondent_type=p.get("respondent_type") or "potential_customer",
        settlement_type=p.get("settlement_type") or "kentsel",
        usage_frequency=p.get("usage_frequency") or "weekly",
        brand_loyalty=p.get("brand_loyalty") or 5,
        diffusion_stage=p.get("diffusion_stage") or "",
        neo_facets=p.get("neo_facets") or {},
        big_five=p.get("big_five") or p.get("traits") or {},
        pazarlik_propensity=p.get("pazarlik_propensity") or 0.3,
        taksit_preference=p.get("taksit_preference") or 0.71,
        sor_osca_threshold=p.get("sor_osca_threshold") or 0.5,
        credit_card_limit_doluluk=p.get("credit_card_limit_doluluk") or 0.5,
    )
