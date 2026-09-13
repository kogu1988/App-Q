"""Study CRUD, bulgular, PDF, arsiv/silme, feedback ve event (R6-3)."""
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


@router.get("/studies")
def get_studies(include_archived: bool = Query(False)):
    return list_studies(include_archived=include_archived)

@router.get("/studies/{study_id}")
def get_study(study_id: str):
    return load_study_payload(study_id, include_pdf=False)


# ---------------------------------------------------------------------------
# Sprint 1 — Evidence Chain (Kanıt Zinciri) API
# ---------------------------------------------------------------------------

@router.get("/studies/{study_id}/findings")
def get_findings_endpoint(
    study_id: str,
    x_username: str | None = Depends(get_current_username),
):
    """Bir araştırmaya ait tüm bulguları kanıt sayılarıyla döner."""
    try:
        findings = get_findings(study_id)
        if findings:
            return {"study_id": study_id, "findings": findings}

        # Fallback: eski çalışmalar için report_json'dan bulguları çıkar
        payload = load_study_payload(study_id, include_pdf=False)
        report_json_str = payload.get("report_json")
        if not report_json_str:
            return {"study_id": study_id, "findings": []}

        import json as _json
        try:
            report = _json.loads(report_json_str) if isinstance(report_json_str, str) else report_json_str
        except (_json.JSONDecodeError, TypeError):
            return {"study_id": study_id, "findings": []}

        # enhanced_findings varsa onu, yoksa findings kullan
        raw_findings = report.get("enhanced_findings") or report.get("findings") or []
        return {"study_id": study_id, "findings": raw_findings}

    except Exception as e:
        logger.error(f"Error fetching findings for study {study_id}: {e}")
        raise HTTPException(status_code=500, detail="Bulgular alınırken bir hata oluştu.")


@router.get("/studies/{study_id}/findings/{finding_id}")
def get_finding_detail_endpoint(
    study_id: str,
    finding_id: int,
    x_username: str | None = Depends(get_current_username),
):
    """Tek bir bulgunun tüm kanıt alıntılarıyla birlikte detayını döner."""
    try:
        finding = get_finding_detail(study_id, finding_id)
        if finding:
            return {"study_id": study_id, "finding": finding}

        # Fallback: eski çalışmalar için report_json'dan ara
        payload = load_study_payload(study_id, include_pdf=False)
        report_json_str = payload.get("report_json")
        if not report_json_str:
            raise HTTPException(status_code=404, detail="Bulgu bulunamadı.")

        import json as _json
        try:
            report = _json.loads(report_json_str) if isinstance(report_json_str, str) else report_json_str
        except (_json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=404, detail="Bulgu bulunamadı.")

        raw_findings = report.get("enhanced_findings") or report.get("findings") or []

        # finding_id 1-bazlı (normal findings listesi) veya DB id'ye göre ara
        target = None
        for i, f in enumerate(raw_findings):
            fid = f.get("id", i + 1)
            if fid == finding_id:
                target = f
                break

        if not target:
            raise HTTPException(status_code=404, detail="Bulgu bulunamadı.")

        return {"study_id": study_id, "finding": target}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching finding detail for study {study_id}, finding {finding_id}: {e}")
        raise HTTPException(status_code=500, detail="Bulgu detayı alınırken bir hata oluştu.")

# ---------------------------------------------------------------------------
# End Sprint 1
# ---------------------------------------------------------------------------

@router.get("/studies/{study_id}/pdf")
def download_study_pdf(study_id: str, x_username: str | None = Depends(get_current_username)):
    plan_type, _ = _resolve_plan(x_username)
    _require_feature(plan_type, "pdf_export")

    payload = load_study_payload(study_id, include_pdf=False)

    # Try report_markdown first, fall back to report_html
    report_markdown = payload.get("report_markdown") or ""
    title = payload.get("title") or payload.get("metadata", {}).get("title") or f"Rapor {study_id}"

    if not report_markdown:
        raise HTTPException(
            status_code=404,
            detail="Bu araştırma için rapor içeriği henüz mevcut değil."
        )

    # On-the-fly: Markdown → HTML → PDF (no DB write needed)
    from packages.research_engine.pdf_generator import (
        generate_pdf_from_markdown,
        horizontal_bar_chart,
    )
    from packages.research_engine.plan_config import get_brand_name

    # Grafikler — persona panelinden basit dağılımlar (PDF'e görsel zenginlik katar)
    charts = []
    personas = payload.get("personas") or []
    if personas:
        from collections import Counter
        _stance_tr = {
            "Innovator": "Öncü", "EarlyAdopter": "Erken Benimseyen",
            "Mainstream": "Ana Akım", "Laggard": "Geciken", "Skeptic": "Şüpheci",
        }
        _stance_order = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]
        _sc = Counter((p.get("stance") or "Mainstream") for p in personas)
        _items = [(_stance_tr.get(s, s), _sc.get(s, 0)) for s in _stance_order if _sc.get(s, 0)]
        if _items:
            charts.append(("Duruş Dağılımı", horizontal_bar_chart("Duruş Dağılımı", _items)))

        _ses_order = ["AB", "C1", "C2", "DE"]
        _sesc = Counter((p.get("ses_group") or "C1") for p in personas)
        _ses_items = [(s, _sesc.get(s, 0)) for s in _ses_order if _sesc.get(s, 0)]
        if _ses_items:
            charts.append(("Sosyo-Ekonomik Grup Dağılımı", horizontal_bar_chart("Sosyo-Ekonomik Grup Dağılımı", _ses_items, color="#ff7759")))

        # Fiyat hassasiyeti (persona bazında, 1-10)
        _ps_items = [(p.get("name") or "Persona", int(p.get("price_sensitivity") or 0)) for p in personas if (p.get("price_sensitivity") or 0) > 0]
        if _ps_items:
            charts.append(("Fiyat Hassasiyeti (1-10)", horizontal_bar_chart("Fiyat Hassasiyeti", _ps_items, color="#1863dc")))

        # Dijital özgüven (persona bazında, 1-10)
        _dc_items = [(p.get("name") or "Persona", int(p.get("digital_confidence") or 0)) for p in personas if (p.get("digital_confidence") or 0) > 0]
        if _dc_items:
            charts.append(("Dijital Özgüven (1-10)", horizontal_bar_chart("Dijital Özgüven", _dc_items, color="#0d9488")))

    brand = get_brand_name(plan_type)
    pdf_bytes = generate_pdf_from_markdown(
        report_markdown, title=title, study_id=study_id, brand_name=brand, charts=charts or None
    )

    if not pdf_bytes:
        raise HTTPException(
            status_code=500,
            detail="PDF oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
        )

    filename = f"{brand}-Report-{study_id}.pdf" if brand else f"Research-Report-{study_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )



@router.put("/studies/{study_id}/archive")
def archive_study_endpoint(study_id: str):
    archive_study(study_id)
    return {"status": "archived"}


@router.delete("/studies/{study_id}")
def delete_study_endpoint(
    study_id: str,
    x_username: str | None = Depends(get_current_username),
):
    """Araştırmayı kalıcı olarak siler.

    Sahiplik kontrolü: studies tablosunda username alanı ile eşleşme arananır.
    Eşleşme bulunamazsa ya da bulu(nan study başka bir kullanıcıya aitse 404 döner.
    """
    from packages.research_engine.database import get_study

    study = get_study(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı.")

    # Sahiplik kontrolü — study'nin username alanı varsa eşleştir
    owner = study.get("username") or study.get("created_by") or ""
    if owner and x_username and owner != x_username:
        raise HTTPException(
            status_code=403,
            detail="Bu araştırmayı silme yetkiniz yok.",
        )

    deleted = delete_study(study_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Araştırma bulunamadı ya da zaten silinmiş.")

    return {"status": "deleted", "study_id": study_id}

@router.post("/studies")
def create_or_update_study(data: StudyPayload, x_username: str | None = Depends(get_current_username)):
    if not x_username:
        raise HTTPException(status_code=401, detail="Oturum bilgisi eksik. Lütfen giriş yapın.")
    study_id = data.metadata.get("id", "")
    # Org bağlamı (multi-user paylaşımı) — org üyesiyse çalışmayı org'a bağla
    if x_username and not data.metadata.get("org_id"):
        try:
            from packages.research_engine.db_org import get_user_org_id
            data.metadata["org_id"] = get_user_org_id(x_username) or ""
        except Exception:
            data.metadata["org_id"] = ""
    save_study(data.metadata, data.payload)

    # Sprint 1 — Kanıt zincirini DB'ye kaydet (varsa)
    try:
        report_json_str = data.payload.get("report_json")
        if report_json_str:
            import json as _json
            report = _json.loads(report_json_str) if isinstance(report_json_str, str) else report_json_str
            enhanced = report.get("enhanced_findings")
            if enhanced and study_id:
                from packages.research_engine.models import EnhancedFinding, Evidence
                # EnhancedFindings dict'ten objeye dönüştür
                findings_objs = []
                for ef_dict in enhanced:
                    evidence_objs = []
                    for ev in ef_dict.get("evidence", []):
                        evidence_objs.append(Evidence(
                            persona_id=ev.get("persona_id", ""),
                            persona_name=ev.get("persona_name", ""),
                            stance=ev.get("stance", "Mainstream"),
                            quote=ev.get("quote", ""),
                            source_question=ev.get("source_question", ""),
                        ))
                    f_obj = EnhancedFinding(
                        title=ef_dict.get("title", ""),
                        category=ef_dict.get("category", "pain_point"),
                        summary=ef_dict.get("summary", ""),
                        confidence=ef_dict.get("confidence", 0.5),
                        evidence=evidence_objs,
                        implication=ef_dict.get("implication", ""),
                        supporting_count=ef_dict.get("supporting_count", 0),
                        refuting_count=ef_dict.get("refuting_count", 0),
                        neutral_count=ef_dict.get("neutral_count", 0),
                        contradiction_score=ef_dict.get("contradiction_score", 0.0),
                        decision_signal=ef_dict.get("decision_signal", "INVESTIGATE"),
                        segment_breakdown=ef_dict.get("segment_breakdown", {}),
                    )
                    findings_objs.append(f_obj)
                save_findings(study_id, findings_objs)
                logger.info(f"Saved {len(findings_objs)} enhanced findings for study {study_id}")
    except Exception as e:
        logger.warning(f"Failed to save findings for study {study_id}: {e}")

    return {"status": "success", "id": study_id}
