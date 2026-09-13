"""Hesap/plan, iletisim ve KVKK export-silme (R6-5)."""
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

@router.get("/me")
@limiter.limit("60/minute")
def get_me(request: Request, x_username: str | None = Depends(get_current_username)):
    """Mevcut kullanıcının plan bilgisini döner."""
    plan_type, config = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None

    period_simulations = 0
    billing_cycle = "monthly"
    period_start = None
    if client:
        _, used, _ = check_simulation_limit(x_username) if x_username else (True, 0, 0)
        period_simulations = client.get("period_simulations", 0)
        billing_cycle = client.get("billing_cycle") or "monthly"
        period_start = client.get("period_start")

    expired, reason = is_trial_expired(client)

    return {
        "username": x_username or "anonymous",
        "plan_type": plan_type,
        "billing_cycle": billing_cycle,
        "period_start": period_start,
        "limits": {
            "max_personas": config["max_personas"],
            "max_simulations": config["max_simulations"],
        },
        "features": {k: v for k, v in config.items() if isinstance(v, bool)},
        "total_simulations": client.get("total_simulations", 0) if client else 0,
        "period_simulations": period_simulations,
        "trial_expired": expired,
        "trial_expired_reason": reason,
    }


@router.post("/upgrade-plan")
def upgrade_plan(req: UpgradePlanRequest, x_username: str | None = Depends(get_current_username)):
    """Kayıtlı kullanıcının planını yükseltir ve dönem sayacını sıfırlar."""
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")

    valid_plans = ["Free", "Flex", "Starter", "Pro", "Enterprise"]
    if req.new_plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Geçersiz plan: {req.new_plan}")
    if req.billing_cycle not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="Faturalama dönemi 'aylık' veya 'yıllık' olmalı.")

    # Production'da para almadan plan yükseltme KAPALI — satın alma Paddle webhook'u ile olur.
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise HTTPException(
            status_code=403,
            detail=(
                "Plan yükseltme yalnızca ödeme akışıyla yapılır. "
                "Lütfen planlar sayfasından satın alın."
            ),
        )

    upgrade_client_plan(x_username, req.new_plan, req.billing_cycle)
    _, config = _resolve_plan(x_username)
    return {
        "success": True,
        "username": x_username,
        "new_plan": req.new_plan,
        "billing_cycle": req.billing_cycle,
        "message": f"Plan başarıyla {req.new_plan} olarak güncellendi. Dönem sayacı sıfırlandı.",
        "new_limits": {
            "max_simulations": config["max_simulations"],
            "max_personas": config["max_personas"],
        },
    }


@router.post("/register")
@limiter.limit("10/minute")
def register(request: Request, req: RegisterRequest):
    """Yeni kullanıcı kaydı: yoksa Free planla oluşturur, varsa mevcut planı döner.
    İsteğe bağlı: new_plan verilmişse kayıt sonrası planı yükseltir."""
    username = (req.username or "").strip()
    if not username or len(username) < 2 or len(username) > 20:
        raise HTTPException(status_code=400, detail="Kullanıcı adı 2-20 karakter arasında olmalı.")
    if not username.isalnum() and not all(c.isalnum() or c in "-_" for c in username):
        raise HTTPException(status_code=400, detail="Kullanıcı adı sadece harf, rakam, - ve _ içerebilir.")

    client, created = register_client_if_new(username, req.email)

    # İsteğe bağlı plan yükseltme
    if req.new_plan and req.new_plan in ["Flex", "Starter", "Pro", "Enterprise"]:
        upgrade_client_plan(username, req.new_plan, req.billing_cycle)
        client["plan_type"] = req.new_plan

    return {
        "username": username,
        "plan_type": client.get("plan_type", "Free"),
        "created": created,
        "message": "Kayıt tamamlandı." if created else "Hoş geldiniz, mevcut hesabınıza devam ediliyor.",
    }

@router.post("/feedback")
def submit_feedback(data: FeedbackCreate):
    save_feedback(data.username, data.study_id, data.item_type, data.item_id, data.vote, data.comment)
    return {"status": "success"}


# İzin verilen istemci taraflı KPI event'leri (funnel ölçümü).
# Serbest metin kabul edilmez; yalnızca bu liste kaydedilir.
_ALLOWED_CLIENT_EVENTS = {
    "upgrade_cta_viewed",
    "upgrade_cta_clicked",
    "paywall_viewed",
    "study_detail_viewed",
    "report_tab_viewed",
    "pdf_export_clicked",
    "wizard_started",
}


@router.post("/events")
def track_event(
    data: dict,
    x_username: str | None = Depends(get_current_username),
):
    """İstemci taraflı ürün event'i kaydeder (auth opsiyonel).

    Yalnızca beyaz listedeki event adları kabul edilir; başarısızlık sessizdir.
    """
    event_name = (data.get("event_name") or "").strip()
    if event_name not in _ALLOWED_CLIENT_EVENTS:
        raise HTTPException(status_code=400, detail="Geçersiz event adı.")
    try:
        from packages.research_engine.database import record_product_event

        props = data.get("props") if isinstance(data.get("props"), dict) else {}
        record_product_event(
            event_name,
            username=x_username,
            study_id=str(data.get("study_id") or ""),
            props=props,
        )
    except Exception:
        logger.debug("İstemci event'i kaydedilemedi: %s", event_name, exc_info=True)
    return {"status": "ok"}

@router.post("/contact")
def contact_form(data: dict):
    """İletişim formu — mesajı DB'ye kaydeder."""
    from datetime import datetime

    from packages.research_engine.database import get_db
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Mesaj 2000 karakterden uzun olamaz.")
    try:
        with get_db() as (conn, cur):
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS contact_messages (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
                (name, email, message),
            )
        # Bildirim e-postası (opsiyonel — RESEND_API_KEY yoksa sessizce atlanır)
        try:
            from packages.research_engine.email_service import notify_contact_form
            notify_contact_form(name, email, message)
        except Exception:
            logger.debug("İletişim bildirimi gönderilemedi.", exc_info=True)
        logger.info(f"Contact form submitted by {name} <{email}>")
        return {"status": "success", "message": "Mesajınız iletildi."}
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Mesaj kaydedilemedi. Lütfen hiclarere@clarere.com adresine e-posta atın.")

@router.get("/me/export")
def export_my_data(x_username: str | None = Depends(get_current_username)):
    """KVKK/GDPR veri taşınabilirliği — kullanıcının tüm verisini JSON olarak indirir."""
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")
    try:
        data = export_user_data(x_username)
    except Exception:
        logger.error("Veri dışa aktarma başarısız (user=%s)", x_username, exc_info=True)
        raise HTTPException(status_code=500, detail="Verileriniz dışa aktarılamadı. Lütfen tekrar deneyin.")

    body = json.dumps(data, ensure_ascii=False, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="clarere-{x_username}-export.json"'
        },
    )


class AccountDeleteRequest(BaseModel):
    confirm: str = ""


@router.delete("/me")
def delete_my_account(
    data: AccountDeleteRequest,
    x_username: str | None = Depends(get_current_username),
):
    """KVKK hesap silme — aboneliği iptal eder ve kullanıcı verisini siler.

    Güvenlik: `confirm: "DELETE"` zorunlu. Abonelik iptal edilemezse silme yapılmaz
    (kullanıcı ücretlendirilmeye devam ederken verisi silinmesin).
    """
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")
    _require_delete_confirmation(data.confirm)

    client = get_client_by_username(x_username) or {}
    subscription_id = client.get("paddle_subscription_id")
    if subscription_id:
        from packages.research_engine.paddle_webhooks import cancel_paddle_subscription
        if not cancel_paddle_subscription(subscription_id):
            raise HTTPException(
                status_code=502,
                detail=(
                    "Abonelik iptal edilemediği için hesap silinemedi. "
                    "Lütfen hiclarere@clarere.com ile iletişime geçin."
                ),
            )

    try:
        counts = delete_user_data(x_username)
    except Exception:
        logger.error("Hesap silme başarısız (user=%s)", x_username, exc_info=True)
        raise HTTPException(status_code=500, detail="Hesap silinemedi. Lütfen tekrar deneyin.")

    logger.info("Hesap silindi: %s (%s)", x_username, counts)
    return {"status": "deleted", "deleted": counts}
