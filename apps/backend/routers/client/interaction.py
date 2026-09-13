"""Takip sorusu ve arastirma asistani (R6-4)."""
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

from .context import build_research_context


@router.post("/studies/{study_id}/follow-up")
def study_follow_up(study_id: str, data: FollowUpRequest, x_username: str | None = Depends(get_current_username)):
    """Belirli bir personaya ek soru sormak için kullanılır."""
    from packages.research_engine.database import get_study, save_study
    from packages.research_engine.providers import get_model_provider

    plan_type, plan_config = _resolve_plan(x_username)
    client = get_client_by_username(x_username) if x_username else None

    # 1. Deneme süresi kontrolü
    expired, reason = is_trial_expired(client)
    if expired:
        raise HTTPException(status_code=403, detail=reason)

    # 2. Free planda engelle
    if plan_type == "Free":
        raise HTTPException(status_code=403, detail="Free planda takip sorusu sorulamaz. Lütfen planınızı yükseltin.")

    _enforce_token_budget(x_username, plan_type)

    study = get_study(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı.")

    payload = load_study_payload(study_id, include_pdf=False)
    interviews = payload.get("interviews", [])

    # 3. Flex/Starter plan follow-up limiti kontrolü (Maks 3 adet)
    max_follow_ups = plan_config.get("max_follow_ups", 9999)
    current_follow_ups = 0
    for inv in interviews:
        for t in inv.get("turns", []):
            if "FOLLOW-UP" in t.get("tags", []):
                current_follow_ups += 1

    if current_follow_ups >= max_follow_ups:
        raise HTTPException(
            status_code=403,
            detail=f"Plan limitinize ulaştınız (Maksimum {max_follow_ups} takip sorusu). Lütfen planınızı yükseltin."
        )

    target_interview = None
    target_idx = -1
    for i, inv in enumerate(interviews):
        if inv.get("persona", {}).get("id") == data.persona_id:
            target_interview = inv
            target_idx = i
            break

    if not target_interview:
        raise HTTPException(status_code=404, detail="Persona mülakatı bulunamadı.")

    persona = target_interview["persona"]
    turns = target_interview.get("turns", [])

    # Konuşma geçmişini kur
    messages = [
        {"role": "system", "content": f"Sen bir simülasyon personasısın. Adın {persona.get('name')}. Yaşın {persona.get('age')}. "
                                      f"Mesleğin {persona.get('role_title', 'Bilinmiyor')}. "
                                      f"Geçmiş sohbetine sadık kal ve sana sorulan ek soruya doğal, role uygun kısa bir cevap ver."}
    ]
    for turn in turns:
        messages.append({"role": "user", "content": turn.get("question", "")})
        messages.append({"role": "assistant", "content": turn.get("answer", "")})

    messages.append({"role": "user", "content": data.question})

    # Modeli çağır
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])
    prompt = f"Geçmiş:\n{history_text}\n\nYeni soru: {data.question}\nCevabın:"

    try:
        model = get_model_provider("flash", user_id=x_username or "", effort="high")
        response = model.generate(messages[0]["content"], prompt)
        answer = response.strip()
        _record_usage(x_username, model, "followup", study_id)
    except Exception as e:
        logger.error(f"Follow up error: {e}")
        raise HTTPException(status_code=500, detail="Cevap üretilemedi. Lütfen tekrar deneyin.")

    new_turn = {
        "question": data.question,
        "answer": answer,
        "tags": ["FOLLOW-UP"]
    }

    # Payload güncelle
    target_interview["turns"].append(new_turn)
    payload["interviews"][target_idx] = target_interview

    # Kaydet
    metadata = study
    save_study(metadata, payload)

    return {"status": "success", "turn": new_turn}

@router.post("/studies/{study_id}/chat")
def research_chat(
    study_id: str,
    data: dict,
    request: Request,
    x_username: str | None = Depends(get_current_username),
):
    """
    Tamamlanmış bir araştırma raporu hakkında soru-cevap.

    Kullanıcı araştırma verisine dayalı sorular sorabilir:
      - "Skeptikler neden reddetti?"
      - "Hangi segment ödemeye en yatkın?"
      - "Sadece çelişkili kanıtları göster."

    Copilot SADECE araştırma verisine dayanarak yanıt verir, halüsinasyon yapmaz.
    Yanıtlar persona adı ve alıntı ile referanslandırılır.
    """
    from packages.research_engine.database import get_db
    from packages.research_engine.providers import get_model_provider

    question = (data.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Soru zorunludur.")

    # ── Plan ve kota kontrolü ──
    plan_type, plan_cfg = _resolve_plan(x_username)
    max_queries = plan_cfg.get("max_talk_to_research", 0)

    _enforce_token_budget(x_username, plan_type)

    if max_queries == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PLAN_GATE",
                "feature": "talk_to_research",
                "current_plan": plan_type,
                "required_plan": "Flex",
                "message": "Research Copilot özelliği mevcut planınızda bulunmuyor.",
            },
        )

    used_queries = count_chat_messages(study_id)
    if max_queries < 9999 and used_queries >= max_queries:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "QUOTA_EXCEEDED",
                "feature": "talk_to_research",
                "used": used_queries,
                "limit": max_queries,
                "message": f"Bu araştırma için soru limitine ulaştınız ({used_queries}/{max_queries}).",
            },
        )

    # ── Araştırma verisini yükle ──
    with get_db() as (conn, cur):
        cur.execute("SELECT report_json FROM study_payloads WHERE study_id = %s", (study_id,))
        row = cur.fetchone()
        if not row or not row["report_json"]:
            raise HTTPException(status_code=404, detail="Çalışma bulunamadı veya rapor henüz oluşturulmamış.")

        report = json.loads(row["report_json"])

        # Son 10 mesajı yükle (chat history)
        cur.execute(
            "SELECT role, content FROM research_chat_messages WHERE study_id = %s ORDER BY created_at DESC LIMIT 10",
            (study_id,)
        )
        history_rows = list(cur.fetchall())

    # ── Bağlam ve sistem prompt'u oluştur ──
    context = build_research_context(report)

    system_prompt = (
        "Sen Clarere Research Copilot'sun. Görevin tamamlanmış bir pazar araştırması "
        "raporu hakkında kullanıcının sorularını yanıtlamak.\n\n"
        "KURALLAR:\n"
        "- SADECE aşağıda verilen ARAŞTIRMA VERİSİNE dayanarak yanıt ver. Halüsinasyon yapma, uydurma.\n"
        "- Veride olmayan bir bilgiyi asla söyleme. Emin değilsen 'Bu konuda araştırma verisinde yeterli bilgi yok' de.\n"
        "- Bir bulgudan veya kanıttan bahsederken MUTLAKA ilgili persona adını, stance'ını, SES grubunu ve alıntısını belirt.\n"
        "  Format: Ahmet (Skeptic, C1): \"Alıntı metni...\"\n"
        "- Bu verinin sentetik olduğunu ve gerçek kullanıcı araştırması yerine geçmediğini unutma.\n"
        "  Kullanıcıya gerektiğinde bunu hatırlat.\n"
        "- Kullanıcı sorduğunda: karşıt görüşleri karşılaştır, segment farklarını göster, en güçlü itirazları sırala.\n"
        "- Çelişkili kanıtları özellikle vurgula — bunlar en değerli içgörülerdir.\n"
        "- Yanıtlarında yapılandırılmış, net ve profesyonel ol. Gereksiz uzatma.\n"
        "- Türkçe yanıt ver. Samimi ama profesyonel bir ton kullan.\n\n"
        f"ARAŞTIRMA VERİSİ:\n{context}"
    )

    # ── Mesaj geçmişini prompt'a göm (DeepSeek generate sadece system+user destekler) ──
    history_prompt = ""
    if history_rows:
        history_parts: list[str] = []
        for h in reversed(history_rows):
            role_label = "Kullanıcı" if h["role"] == "user" else "Copilot"
            history_parts.append(f"[{role_label}]: {h['content']}")
        history_prompt = (
            "\n\nÖNCEKİ KONUŞMA (referans için):\n"
            + "\n".join(history_parts)
            + "\n\nYENİ SORU: "
        )

    user_prompt = f"{history_prompt}{question}"

    # ── DeepSeek Pro ile yanıt üret ──
    safe_user_id = (x_username or "").strip() or "anonymous"
    model = get_model_provider("pro", user_id=safe_user_id, effort="high")

    try:
        answer = model.generate(system_prompt, user_prompt)
    except Exception as e:
        logger.error(f"Research copilot LLM call failed for study {study_id}: {e}")
        raise HTTPException(status_code=502, detail="Yapay zeka yanıtı alınamadı. Lütfen tekrar deneyin.")
    finally:
        model.free_memory()

    _record_usage(x_username, model, "copilot", study_id)

    # ── Mesajları kaydet ──
    with get_db() as (conn, cur):
        cur.execute(
            "INSERT INTO research_chat_messages (study_id, role, content) VALUES (%s, %s, %s)",
            (study_id, "user", question)
        )
        cur.execute(
            "INSERT INTO research_chat_messages (study_id, role, content) VALUES (%s, %s, %s)",
            (study_id, "assistant", answer)
        )

    return {
        "answer": answer,
        "study_id": study_id,
        "queries_used": used_queries + 1,
        "queries_limit": max_queries if max_queries < 9999 else None,
    }
