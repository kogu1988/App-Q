"""Arastirma baglami kurulumu (PII maskeleme + brief normalizasyonu)."""
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


def build_research_context(report: dict) -> str:
    """
    Araştırma raporundan LLM için kompakt ama zengin bağlam metni oluşturur.

    İçerik:
      - Yönetici özeti
      - Her bulgu (kanıt alıntılarıyla birlikte)
      - Persona özetleri (stance, segment, SES)
      - Fiyatlandırma içgörüleri
      - Stance dağılımı
    """
    parts: list[str] = []

    # 1. Executive Summary
    exec_summary = report.get("executive_summary")
    if exec_summary:
        parts.append("=== YÖNETİCİ ÖZETİ ===")
        if isinstance(exec_summary, list):
            for item in exec_summary:
                parts.append(f"• {item}")
        else:
            parts.append(str(exec_summary))

    # 2. Findings with evidence (öncelikle enhanced_findings, yoksa findings)
    findings = report.get("enhanced_findings") or report.get("findings") or []
    if findings:
        parts.append("\n=== BULGULAR ===")
        for i, f in enumerate(findings, 1):
            title = f.get("title", "Bulgular")
            category = f.get("category", "")
            summary = f.get("summary", "")
            implication = f.get("implication", "")
            confidence = f.get("confidence", 0)
            decision = f.get("decision_signal", "")

            parts.append(f"\nBulgu {i}: {title}")
            parts.append(f"  Kategori: {category} | Güven: {confidence:.0%}")
            parts.append(f"  Özet: {summary}")
            if implication:
                parts.append(f"  Çıkarım: {implication}")
            if decision:
                parts.append(f"  Karar Sinyali: {decision}")

            # Evidence quotes
            evidence = f.get("evidence", [])
            if evidence:
                parts.append("  Kanıtlar:")
                for ev in evidence:
                    pname = ev.get("persona_name", "?")
                    stance = ev.get("stance", "")
                    quote = ev.get("quote", "")
                    sentiment = ev.get("sentiment", "")
                    question = ev.get("source_question", ev.get("question", ""))
                    ses = ev.get("ses_group", "")
                    label_parts = [pname]
                    if stance:
                        label_parts.append(stance)
                    if ses:
                        label_parts.append(ses)
                    label = ", ".join(label_parts)
                    sentiment_tag = f" [{sentiment}]" if sentiment else ""
                    parts.append(f"    {label}{sentiment_tag}: \"{quote}\"")
                    if question:
                        parts.append(f"      → Soru: {question}")

            # Contradiction info (enhanced findings)
            supp = f.get("supporting_count")
            ref = f.get("refuting_count")
            neu = f.get("neutral_count")
            contra = f.get("contradiction_score")
            if supp is not None or ref is not None:
                parts.append(f"  Destek: {supp or 0} | Karşı: {ref or 0} | Nötr: {neu or 0} | Çelişki: {contra or 0:.2f}")

    # 3. Persona summaries
    personas = report.get("personas") or []
    if personas:
        parts.append("\n=== PERSONALAR ===")
        for p in personas:
            name = p.get("name", "?")
            age = p.get("age", "?")
            city = p.get("city", "?")
            stance = p.get("stance", "?")
            segment = p.get("segment", "?")
            ses = p.get("ses_group", "")
            context = p.get("context", "")
            goals = p.get("goals", [])
            objections = p.get("objections", [])
            price_sens = p.get("price_sensitivity", 5)
            resp_type = p.get("respondent_type", "")

            label_parts = [name]
            if stance:
                label_parts.append(stance)
            if ses:
                label_parts.append(ses)
            if resp_type:
                label_parts.append(resp_type)
            label = ", ".join(label_parts)

            parts.append(f"\n  {label} — {age} yaş, {city}, {segment} segment")
            parts.append(f"    Fiyat Hassasiyeti: {price_sens}/10")
            if context:
                parts.append(f"    Bağlam: {context}")
            if goals:
                parts.append(f"    Hedefler: {'; '.join(goals)}")
            if objections:
                parts.append(f"    İtirazlar: {'; '.join(objections)}")

    # 4. Pricing insights
    pricing = report.get("pricing")
    if pricing and isinstance(pricing, dict):
        parts.append("\n=== FİYATLANDIRMA ===")
        ar = pricing.get("acceptable_range", "")
        rp = pricing.get("resistance_points", [])
        ps = pricing.get("packaging_suggestion", "")
        if ar:
            parts.append(f"  Kabul Edilebilir Aralık: {ar}")
        if rp:
            parts.append(f"  Direnç Noktaları: {'; '.join(rp)}")
        if ps:
            parts.append(f"  Paketleme Önerisi: {ps}")
        # Van Westendorp
        vw = report.get("van_westendorp")
        if vw and isinstance(vw, dict):
            opp = vw.get("opp")
            ar_vw = vw.get("acceptable_range")
            if opp:
                parts.append(f"  Van Westendorp OPP: {opp} TL")
            if ar_vw:
                parts.append(f"  Van Westendorp Aralık: {ar_vw}")

    # 5. Stance distribution overview
    stances: dict[str, int] = {}
    for p in personas:
        s = p.get("stance", "")
        if s:
            stances[s] = stances.get(s, 0) + 1
    if stances:
        parts.append("\n=== STANCE DAĞILIMI ===")
        for stance, count in sorted(stances.items()):
            parts.append(f"  {stance}: {count} persona")

    # 6. Segment breakdown
    seg_break = report.get("segment_breakdown")
    if seg_break and isinstance(seg_break, dict):
        parts.append("\n=== SEGMENT KIRILIMI ===")
        for seg, info in seg_break.items():
            if isinstance(info, dict):
                parts.append(f"  {seg}: {info}")
            else:
                parts.append(f"  {seg}: {info}")

    # 7. Limitations (for honesty)
    limitations = report.get("limitations") or []
    if limitations:
        parts.append("\n=== ARAŞTIRMA KISITLARI ===")
        for lim in limitations:
            parts.append(f"  • {lim}")

    return "\n".join(parts)
