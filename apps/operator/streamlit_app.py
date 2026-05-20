from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from html import escape
from dataclasses import asdict
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from packages.research_engine.models import (
    ClarifyingQuestion,
    InterviewQuestion,
    InterviewTurn,
    PanelRole,
    Persona,
    PersonaInterview,
    ResearchBrief,
    ResearchPlan,
)
from packages.research_engine.providers import ModelProviderError, get_model_provider
from packages.research_engine.reporting import render_markdown
from packages.research_engine.workflow import build_research_plan, generate_personas, run_research, synthesize_report


SAMPLE_PATH = ROOT / "data" / "samples" / "first-brief.json"
OUTPUT_DIR = ROOT / "data" / "outputs"
STUDIES_DIR = ROOT / "data" / "studies"
WIZARD_NAME = "Defne"
WIZARD_ROLE = "App-Q araştırma mimarı"
WIZARD_SYSTEM_STYLE = (
    "Defne, pazara çıkmadan önce ürün fikrini keskinleştiren kıdemli bir araştırma mimarıdır. "
    "Kibar ama gevşek değildir; kullanıcının fikrini onaylamak yerine karar alınabilir brief ister. "
    "Her adımda tek ana eksikliği yakalar, somut soru sorar ve sonunda araştırma hedefi ile rol önerilerini çıkarır."
)
CITY_COORDS = {
    "İstanbul": {"lat": 41.0082, "lon": 28.9784},
    "Izmir": {"lat": 38.4237, "lon": 27.1428},
    "İzmir": {"lat": 38.4237, "lon": 27.1428},
    "Ankara": {"lat": 39.9334, "lon": 32.8597},
    "Bursa": {"lat": 40.1826, "lon": 29.0665},
    "Antalya": {"lat": 36.8969, "lon": 30.7133},
    "Konya": {"lat": 37.8746, "lon": 32.4932},
    "Kocaeli": {"lat": 40.7654, "lon": 29.9408},
    "Eskişehir": {"lat": 39.7667, "lon": 30.5256},
    "Adana": {"lat": 37.0, "lon": 35.3213},
    "Kayseri": {"lat": 38.7205, "lon": 35.4826},
}
BRIEF_STATE_KEYS = {
    "title": "brief_title",
    "market": "brief_market",
    "category": "brief_category",
    "idea": "brief_idea",
    "target_users": "brief_target_users",
    "questions": "brief_questions",
    "competitors": "brief_competitors",
    "expected_price": "brief_expected_price",
    "sales_channel": "brief_sales_channel",
    "success_metric": "brief_success_metric",
}


def parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def load_sample() -> dict:
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


def seed_brief_state(data: dict) -> None:
    st.session_state[BRIEF_STATE_KEYS["title"]] = data.get("title", "")
    st.session_state[BRIEF_STATE_KEYS["market"]] = data.get("market", "Türkiye")
    st.session_state[BRIEF_STATE_KEYS["category"]] = data.get("category", "")
    st.session_state[BRIEF_STATE_KEYS["idea"]] = data.get("idea", "")
    st.session_state[BRIEF_STATE_KEYS["target_users"]] = "\n".join(data.get("target_users", []))
    st.session_state[BRIEF_STATE_KEYS["questions"]] = "\n".join(data.get("questions", []))
    st.session_state[BRIEF_STATE_KEYS["competitors"]] = "\n".join(data.get("competitors", []))
    st.session_state[BRIEF_STATE_KEYS["expected_price"]] = data.get("expected_price", "")
    st.session_state[BRIEF_STATE_KEYS["sales_channel"]] = data.get("sales_channel", "")
    st.session_state[BRIEF_STATE_KEYS["success_metric"]] = data.get("success_metric", "")


def current_brief_data() -> dict:
    return {
        "title": st.session_state.get(BRIEF_STATE_KEYS["title"], ""),
        "market": st.session_state.get(BRIEF_STATE_KEYS["market"], "Türkiye"),
        "category": st.session_state.get(BRIEF_STATE_KEYS["category"], ""),
        "idea": st.session_state.get(BRIEF_STATE_KEYS["idea"], ""),
        "target_users": parse_lines(st.session_state.get(BRIEF_STATE_KEYS["target_users"], "")),
        "questions": parse_lines(st.session_state.get(BRIEF_STATE_KEYS["questions"], "")),
        "competitors": parse_lines(st.session_state.get(BRIEF_STATE_KEYS["competitors"], "")),
        "expected_price": st.session_state.get(BRIEF_STATE_KEYS["expected_price"], ""),
        "sales_channel": st.session_state.get(BRIEF_STATE_KEYS["sales_channel"], ""),
        "success_metric": st.session_state.get(BRIEF_STATE_KEYS["success_metric"], ""),
    }


def apply_wizard_answer(field_name: str, answer: str) -> None:
    answer = answer.strip()
    if not answer:
        return
    state_key = BRIEF_STATE_KEYS[field_name]
    if field_name in {"target_users", "questions", "competitors"}:
        existing = st.session_state.get(state_key, "").strip()
        st.session_state[state_key] = f"{existing}\n{answer}".strip() if existing else answer
    elif field_name == "title":
        st.session_state[state_key] = answer.splitlines()[0][:90]
    else:
        st.session_state[state_key] = answer


def append_wizard_message(role: str, content: str) -> None:
    st.session_state.setdefault("wizard_messages", []).append({"role": role, "content": content})


def role_state_key(role_name: str, suffix: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "_" for char in role_name)
    return f"wizard_role_{normalized}_{suffix}"


def sync_role_state(role_rows: list[dict[str, str | int | bool]]) -> None:
    current_roles = {role["role"] for role in role_rows}
    previous_roles = set(st.session_state.get("wizard_role_names", []))
    if current_roles != previous_roles:
        for role in role_rows:
            selected_key = role_state_key(str(role["role"]), "selected")
            count_key = role_state_key(str(role["role"]), "count")
            st.session_state[selected_key] = bool(role["selected"])
            st.session_state[count_key] = int(role["count"])
        st.session_state["wizard_role_names"] = sorted(current_roles)


def selected_role_rows(role_rows: list[dict[str, str | int | bool]]) -> list[dict[str, str | int]]:
    selected: list[dict[str, str | int]] = []
    for role in role_rows:
        role_name = str(role["role"])
        selected_key = role_state_key(role_name, "selected")
        count_key = role_state_key(role_name, "count")
        if st.session_state.get(selected_key, bool(role["selected"])):
            selected.append(
                {
                    "role": role_name,
                    "why": str(role["why"]),
                    "count": int(st.session_state.get(count_key, int(role["count"]))),
                }
            )
    return selected


def build_panel_roles(role_rows: list[dict[str, str | int | bool]]) -> list[PanelRole]:
    return [
        PanelRole(role=str(role["role"]), why=str(role["why"]), count=int(role["count"]))
        for role in selected_role_rows(role_rows)
        if int(role["count"]) > 0
    ]


def current_role_state_snapshot() -> list[dict[str, str | int | bool]]:
    role_rows = build_role_suggestions(current_brief_data())
    snapshot: list[dict[str, str | int | bool]] = []
    for role in role_rows:
        role_name = str(role["role"])
        selected_key = role_state_key(role_name, "selected")
        count_key = role_state_key(role_name, "count")
        snapshot.append(
            {
                "role": role_name,
                "why": str(role["why"]),
                "selected": bool(st.session_state.get(selected_key, bool(role["selected"]))),
                "count": int(st.session_state.get(count_key, int(role["count"]))),
            }
        )
    return snapshot


def restore_role_state(saved_roles: list[dict[str, str | int | bool]]) -> None:
    role_rows = build_role_suggestions(current_brief_data())
    saved_by_name = {str(role.get("role")): role for role in saved_roles}
    for role in role_rows:
        role_name = str(role["role"])
        saved = saved_by_name.get(role_name, {})
        st.session_state[role_state_key(role_name, "selected")] = bool(
            saved.get("selected", role.get("selected", False))
        )
        st.session_state[role_state_key(role_name, "count")] = int(saved.get("count", role.get("count", 0)))
    st.session_state["wizard_role_names"] = sorted(str(role["role"]) for role in role_rows)


def clear_generated_state() -> None:
    for key in ["report_json", "report_markdown", "selected_interview_id"]:
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if key.startswith("follow_up_question_") or key.startswith("focus_follow_up_"):
            st.session_state.pop(key, None)


def slugify_title(value: str) -> str:
    normalized = value.lower().strip()
    normalized = normalized.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
    normalized = normalized.replace("ş", "s").replace("ö", "o").replace("ç", "c")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized[:60] or "study"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def study_path(study_id: str) -> Path:
    return STUDIES_DIR / study_id


def list_studies(include_archived: bool = False) -> list[dict]:
    if not STUDIES_DIR.exists():
        return []
    studies: list[dict] = []
    for metadata_path in STUDIES_DIR.glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("archived") and not include_archived:
            continue
        metadata["id"] = metadata.get("id") or metadata_path.parent.name
        studies.append(metadata)
    return sorted(studies, key=lambda item: item.get("updated_at", ""), reverse=True)


def load_study_payload(study_id: str) -> dict:
    path = study_path(study_id)
    payload: dict = {}
    for file_name, key in [
        ("metadata.json", "metadata"),
        ("brief.json", "brief"),
        ("roles.json", "roles"),
        ("report.json", "report_json"),
    ]:
        target = path / file_name
        if target.exists():
            payload[key] = json.loads(target.read_text(encoding="utf-8"))
    markdown_path = path / "report.md"
    if markdown_path.exists():
        payload["report_markdown"] = markdown_path.read_text(encoding="utf-8")
    return payload


def save_study_payload(study_id: str | None = None) -> str:
    brief_data = current_brief_data()
    title = brief_data.get("title") or "Adsiz App-Q Calismasi"
    created_at = now_iso()
    if not study_id:
        study_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify_title(title)}"
    path = study_path(study_id)
    path.mkdir(parents=True, exist_ok=True)

    metadata_path = path / "metadata.json"
    existing_metadata: dict = {}
    if metadata_path.exists():
        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    report_json = st.session_state.get("report_json")
    report_markdown = st.session_state.get("report_markdown")
    metadata = {
        "id": study_id,
        "title": title,
        "market": brief_data.get("market", ""),
        "category": brief_data.get("category", ""),
        "created_at": existing_metadata.get("created_at", created_at),
        "updated_at": created_at,
        "archived": False,
        "has_report": bool(report_json and report_markdown),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (path / "brief.json").write_text(json.dumps(brief_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (path / "roles.json").write_text(
        json.dumps(current_role_state_snapshot(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if report_json and report_markdown:
        (path / "report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")
        (path / "report.md").write_text(report_markdown, encoding="utf-8")
        (path / "report.html").write_text(render_report_html(report_json, report_markdown), encoding="utf-8")
    return study_id


def archive_study(study_id: str) -> None:
    metadata_path = study_path(study_id) / "metadata.json"
    if not metadata_path.exists():
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["archived"] = True
    metadata["updated_at"] = now_iso()
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_study_payload(study_id: str, payload: dict) -> None:
    seed_brief_state(payload.get("brief", {}))
    restore_role_state(payload.get("roles", []))
    clear_generated_state()
    if payload.get("report_json") and payload.get("report_markdown"):
        st.session_state["report_json"] = payload["report_json"]
        st.session_state["report_markdown"] = payload["report_markdown"]
    st.session_state["current_study_id"] = study_id
    st.session_state["wizard_messages"] = [
        {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
    ]


def study_dashboard_rows(studies: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for study in studies:
        payload = load_study_payload(study["id"])
        report_json = payload.get("report_json") or {}
        brief = payload.get("brief") or {}
        rows.append(
            {
                "title": study.get("title", study["id"]),
                "market": study.get("market") or brief.get("market", ""),
                "category": study.get("category") or brief.get("category", ""),
                "updated_at": study.get("updated_at", ""),
                "status": "Archived" if study.get("archived") else ("Report ready" if study.get("has_report") else "Brief only"),
                "personas": len(report_json.get("personas", [])),
                "findings": len(report_json.get("findings", [])),
                "id": study["id"],
            }
        )
    return rows


def render_studies_dashboard() -> None:
    include_archived = st.toggle("Arsivlenmis calismalari goster", value=False)
    studies = list_studies(include_archived=include_archived)
    rows = study_dashboard_rows(studies)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Kayitli Calisma", len(studies))
    metric_cols[1].metric("Raporlu", sum(1 for item in studies if item.get("has_report")))
    metric_cols[2].metric("Brief Asamasi", sum(1 for item in studies if not item.get("has_report")))
    metric_cols[3].metric("Arsiv", sum(1 for item in studies if item.get("archived")))

    if not studies:
        st.info("Kayitli calisma yok. Sol panelden brief'i doldurup Kaydet ile ilk calismayi olusturabilirsin.")
        return

    st.dataframe(rows, use_container_width=True, hide_index=True, column_order=[
        "title",
        "status",
        "market",
        "category",
        "personas",
        "findings",
        "updated_at",
        "id",
    ])

    st.markdown("#### Hızlı Aksiyonlar")
    for index, study in enumerate(studies[:8]):
        payload = load_study_payload(study["id"])
        brief = payload.get("brief") or {}
        report_json = payload.get("report_json") or {}
        with st.container(border=True):
            cols = st.columns([0.5, 0.16, 0.16, 0.18])
            with cols[0]:
                st.markdown(f"##### {study.get('title', study['id'])}")
                st.caption(
                    f"{study.get('market') or brief.get('market', '')} / "
                    f"{study.get('category') or brief.get('category', '')} / "
                    f"{study.get('updated_at', '')}"
                )
                if brief.get("idea"):
                    st.write(str(brief["idea"])[:240] + ("..." if len(str(brief["idea"])) > 240 else ""))
            cols[1].metric("Persona", len(report_json.get("personas", [])))
            cols[2].metric("Bulgu", len(report_json.get("findings", [])))
            with cols[3]:
                if st.button("Ac", key=f"dashboard_open_{study['id']}_{index}", use_container_width=True):
                    apply_study_payload(study["id"], payload)
                    st.rerun()
                if not study.get("archived") and st.button(
                    "Arsivle",
                    key=f"dashboard_archive_{study['id']}_{index}",
                    use_container_width=True,
                ):
                    archive_study(study["id"])
                    if st.session_state.get("current_study_id") == study["id"]:
                        st.session_state.pop("current_study_id", None)
                    st.rerun()


def render_trait_bar(label: str, value: int) -> None:
    cols = st.columns([0.68, 0.32])
    cols[0].caption(label)
    cols[1].caption(f"{value}/100")
    st.progress(max(0, min(value, 100)) / 100)


def render_persona_card(persona) -> None:
    with st.container(border=True):
        header_cols = st.columns([0.18, 0.82])
        avatar = persona.name[:1].upper()
        header_cols[0].markdown(f"## {avatar}")
        header_cols[1].markdown(f"### {persona.name}")
        header_cols[1].caption(
            f"{persona.age} yaşında • {persona.city}, {persona.origin_country} • "
            f"{persona.country_code} • {persona.role_title or persona.segment}"
        )
        header_cols[1].write(persona.bio or persona.context)

        st.divider()
        attribute_items = list(persona.attributes.items())[:8]
        for label, value in attribute_items:
            st.caption(label.upper())
            st.write(value)

        st.markdown("#### Karar Profili")
        profile_cols = st.columns(3)
        profile_cols[0].metric("Duruş", persona.stance)
        profile_cols[1].metric("Fiyat", f"{persona.price_sensitivity}/10")
        profile_cols[2].metric("Dijital", f"{persona.digital_confidence}/10")

        st.markdown("#### İtirazlar")
        for objection in persona.objections:
            st.markdown(f"- {objection}")

        st.markdown("#### Kişilik Skorları")
        for trait, value in persona.traits.items():
            render_trait_bar(trait, int(value))


def persona_role_name(persona) -> str:
    return persona.role_title or persona.segment or "Bilinmeyen"


def average(values: list[int]) -> int:
    return round(sum(values) / len(values)) if values else 0


def persona_overview_rows(personas: list) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for persona in personas:
        rows.append(
            {
                "persona": persona.name,
                "role": persona_role_name(persona),
                "city": persona.city,
                "age": persona.age,
                "stance": persona.stance,
                "price_sensitivity": persona.price_sensitivity,
                "digital_confidence": persona.digital_confidence,
                "trust_friction": int(persona.traits.get("Neuroticism", persona.price_sensitivity * 8)),
                "openness": int(persona.traits.get("Openness", persona.digital_confidence * 9)),
            }
        )
    return rows


def count_by(items: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def role_relevancy_rows(personas: list) -> list[dict[str, str | int]]:
    grouped: dict[str, list] = {}
    for persona in personas:
        grouped.setdefault(persona_role_name(persona), []).append(persona)

    rows: list[dict[str, str | int]] = []
    for role, role_personas in grouped.items():
        rows.append(
            {
                "role": role,
                "count": len(role_personas),
                "willingness_to_pay": average([10 - item.price_sensitivity for item in role_personas]) * 10,
                "digital_readiness": average([item.digital_confidence for item in role_personas]) * 10,
                "objection_strength": average([item.price_sensitivity for item in role_personas]) * 10,
                "trust_risk": average([int(item.traits.get("Neuroticism", 50)) for item in role_personas]),
                "research_fit": average(
                    [
                        min(
                            10,
                            3
                            + item.digital_confidence // 2
                            + (2 if item.stance in {"Skeptic", "Blocker"} else 1),
                        )
                        for item in role_personas
                    ]
                )
                * 10,
            }
        )
    return rows


def persona_map_rows(personas: list) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for persona in personas:
        coords = CITY_COORDS.get(persona.city)
        if coords:
            rows.append(
                {
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "persona": persona.name,
                    "role": persona_role_name(persona),
                    "city": persona.city,
                }
            )
    return rows


def render_persona_overview(personas: list) -> None:
    rows = persona_overview_rows(personas)
    ages = [int(row["age"]) for row in rows]
    roles = [str(row["role"]) for row in rows]
    cities = [str(row["city"]) for row in rows]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Toplam Persona", len(personas))
    metric_cols[1].metric("Yaş Aralığı", f"{min(ages)}-{max(ages)}" if ages else "-")
    metric_cols[2].metric("Rol Sayısı", len(set(roles)))
    metric_cols[3].metric("Şehir Sayısı", len(set(cities)))

    st.markdown("#### Panel Dağılımı")
    dist_cols = st.columns(2)
    with dist_cols[0]:
        st.caption("Roller")
        st.bar_chart(count_by(roles))
    with dist_cols[1]:
        st.caption("Şehirler")
        st.bar_chart(count_by(cities))

    map_rows = persona_map_rows(personas)
    if map_rows:
        st.markdown("#### Demografi Haritası")
        st.map(map_rows, latitude="lat", longitude="lon")

    st.markdown("#### Rol Relevancy Skorları")
    relevancy = role_relevancy_rows(personas)
    st.dataframe(relevancy, use_container_width=True, hide_index=True)

    st.markdown("#### Persona Özeti")
    st.dataframe(rows, use_container_width=True, hide_index=True)


def interview_quality_summary(interview: dict) -> dict[str, int]:
    turns = interview.get("turns", [])
    warning_count = 0
    fail_count = 0
    for turn in turns:
        flags = turn.get("quality_flags") or []
        warning_count += len(flags)
        fail_count += sum(1 for flag in flags if flag in {"meta_tone", "visible_reasoning"})
    return {
        "turn_count": len(turns),
        "warning_count": warning_count,
        "fail_count": fail_count,
    }


def interview_model_usage(interview: dict) -> dict[str, int]:
    usage: dict[str, int] = {}
    for turn in interview.get("turns", []):
        model_id = turn.get("model_id") or "unknown"
        usage[model_id] = usage.get(model_id, 0) + 1
    return usage


def render_transcript_markdown(interview: dict) -> str:
    persona = interview.get("persona", {})
    lines = [
        f"# {persona.get('name', 'Persona')} Transcript",
        "",
        f"- Segment: {persona.get('segment', '')}",
        f"- Rol: {persona.get('role_title') or persona.get('segment', '')}",
        f"- Şehir/yaş: {persona.get('city', '')}, {persona.get('age', '')}",
        "",
    ]
    for index, turn in enumerate(interview.get("turns", []), start=1):
        lines.extend(
            [
                f"## {index}. Soru",
                "",
                turn.get("question", ""),
                "",
                "Yanıt:",
                "",
                turn.get("answer", ""),
                "",
                f"Model: {turn.get('model_id') or 'unknown'}",
                f"Kalite uyarıları: {', '.join(turn.get('quality_flags') or []) or 'yok'}",
                "",
            ]
        )
    return "\n".join(lines)


def html_list(items: list[str]) -> str:
    if not items:
        return "<p class='muted'>Kayıt yok.</p>"
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def html_table(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    if not rows:
        return "<p class='muted'>Tablo verisi yok.</p>"
    header = "".join(f"<th>{escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(row.get(key, '')))}</td>" for key, _ in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def render_report_html(report_json: dict, report_markdown: str) -> str:
    plan = report_json.get("plan", {})
    personas = report_json.get("personas", [])
    interviews = report_json.get("interviews", [])
    findings = report_json.get("findings", [])
    pricing = report_json.get("pricing", {})
    quality_issues = report_json.get("quality_issues", [])
    model_usage = report_json.get("model_usage", {})
    age_values = [persona.get("age") for persona in personas if persona.get("age")]
    roles = [
        persona.get("role_title") or persona.get("segment") or "Bilinmeyen"
        for persona in personas
    ]
    role_counts = count_by([str(role) for role in roles])
    quote_count = sum(len(interview.get("turns", [])) for interview in interviews)
    evidence_blocks = []
    for finding in findings:
        evidence_items = finding.get("evidence", [])[:3]
        quotes = "".join(
            "<blockquote>"
            f"{escape(item.get('quote', ''))}"
            f"<footer>{escape(item.get('persona_name', ''))} · {escape(item.get('stance', ''))}</footer>"
            "</blockquote>"
            for item in evidence_items
        )
        evidence_blocks.append(
            "<section class='card'>"
            f"<div class='eyebrow'>{escape(str(finding.get('category', 'finding')).upper())}</div>"
            f"<h3>{escape(finding.get('title', 'Bulgu'))}</h3>"
            f"<p>{escape(finding.get('summary', ''))}</p>"
            f"<p class='impact'><strong>Etki:</strong> {escape(finding.get('implication', ''))}</p>"
            f"{quotes or '<p class=\"muted\">Kanıt alıntısı yok.</p>'}"
            "</section>"
        )

    role_rows = [{"role": role, "count": count} for role, count in role_counts.items()]
    model_rows = [{"model": model_id, "answers": count} for model_id, count in model_usage.items()]
    script_rows = [
        {"label": item.get("label", ""), "question": item.get("question", ""), "reason": item.get("reason", "")}
        for item in plan.get("interview_script", [])[:8]
    ]
    persona_cards = []
    for persona in personas[:6]:
        persona_cards.append(
            "<section class='persona-card'>"
            f"<h3>{escape(persona.get('name', 'Persona'))}</h3>"
            f"<p class='muted'>{escape(str(persona.get('age', '')))} - "
            f"{escape(persona.get('city', ''))} - "
            f"{escape(persona.get('role_title') or persona.get('segment') or '')}</p>"
            f"<p>{escape(persona.get('bio') or persona.get('context') or '')}</p>"
            f"<div class='mini-metrics'>"
            f"<span>Fiyat {escape(str(persona.get('price_sensitivity', '-')))}/10</span>"
            f"<span>Dijital {escape(str(persona.get('digital_confidence', '-')))}/10</span>"
            f"<span>{escape(persona.get('stance', ''))}</span>"
            f"</div>"
            "</section>"
        )
    transcript_blocks = []
    for interview in interviews[:4]:
        persona = interview.get("persona", {})
        first_turn = (interview.get("turns") or [{}])[0]
        transcript_blocks.append(
            "<section class='card transcript'>"
            f"<div class='eyebrow'>{escape(persona.get('role_title') or persona.get('segment') or 'PERSONA')}</div>"
            f"<h3>{escape(persona.get('name', 'Persona'))}</h3>"
            f"<p><strong>Soru:</strong> {escape(first_turn.get('question', ''))}</p>"
            f"<blockquote>{escape(first_turn.get('answer', ''))}"
            f"<footer>{escape(first_turn.get('model_id') or 'model unknown')}</footer></blockquote>"
            "</section>"
        )
    score_rows = [
        {
            "goal": "Satin alma niyeti",
            "score": "Orta-Yuksek" if findings else "Belirsiz",
            "evidence": "Fiyat ve deger bulgulari persona alintilariyla destekleniyor." if findings else "Rapor uretimi bekleniyor.",
        },
        {
            "goal": "Guven / KVKK bariyeri",
            "score": "Kritik",
            "evidence": "Sentetik metodoloji, veri gizliligi ve kanit zinciri acikca anlatilmali.",
        },
        {
            "goal": "MVP odak netligi",
            "score": "Aksiyonlanabilir" if report_json.get("action_items") else "Eksik",
            "evidence": "Aksiyon listesi ve acik sorular sonraki sprint kararlarini besliyor.",
        },
    ]
    open_questions = [
        "Hangi segmentte ödeme niyeti gerçek satış görüşmesiyle doğrulanmalı?",
        "En güçlü itirazı azaltmak için hangi kanıt veya demo akışı gerekir?",
        "Takip görüşmesinde fiyat eşiği hangi TL aralığında sıkışıyor?",
        "Hangi özellik ilk MVP dışında bırakılırsa satın alma niyeti düşmez?",
    ]

    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>{escape(report_json.get('title', 'App-Q Research Report'))}</title>
  <style>
    :root {{
      --ink: #2f2a24;
      --muted: #7b756b;
      --line: #ece3cf;
      --soft: #fbf8ef;
      --accent: #f4b521;
      --green: #33b978;
      --danger: #c85a4a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--ink);
      background: #f4f1e9;
      line-height: 1.55;
    }}
    .page {{
      max-width: 1040px;
      margin: 0 auto;
      padding: 42px 44px 72px;
      background: #fffdf8;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 34px;
    }}
    .brand {{ font-weight: 800; letter-spacing: .02em; }}
    .badge {{
      display: inline-block;
      border-radius: 999px;
      background: #fff0c7;
      color: #87610b;
      padding: 5px 11px;
      font-size: 12px;
      font-weight: 700;
    }}
    h1 {{ font-size: 48px; line-height: 1.05; margin: 0 0 16px; font-weight: 500; }}
    h2 {{ margin: 42px 0 14px; font-size: 24px; }}
    h3 {{ margin: 6px 0 8px; font-size: 18px; }}
    p {{ margin: 0 0 12px; }}
    .muted {{ color: var(--muted); }}
    .hero {{
      padding: 24px 0 10px;
    }}
    .summary {{
      font-size: 17px;
      max-width: 920px;
      color: #4f4a43;
    }}
    .section-note {{
      max-width: 760px;
      color: var(--muted);
      margin-top: -6px;
      margin-bottom: 18px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin: 28px 0;
    }}
    .metric, .card {{
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 10px 28px rgba(58, 45, 22, .05);
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 8px; }}
    .metric strong {{ font-size: 28px; font-weight: 500; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
    .persona-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
    .persona-card {{
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 12px;
      padding: 16px;
    }}
    .persona-card h3 {{ margin-top: 0; }}
    .mini-metrics {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }}
    .mini-metrics span {{
      border-radius: 999px;
      background: var(--soft);
      border: 1px solid var(--line);
      padding: 4px 8px;
      font-size: 12px;
      color: #5e554a;
    }}
    .finding-grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
    .eyebrow {{
      display: inline-block;
      background: #fff2c9;
      color: #9b7412;
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .04em;
      margin-bottom: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
      overflow: hidden;
      font-size: 13px;
    }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: var(--soft); font-size: 12px; color: #71695f; }}
    blockquote {{
      margin: 12px 0 0;
      padding: 14px 16px;
      background: var(--soft);
      border-left: 4px solid var(--accent);
      border-radius: 8px;
    }}
    blockquote footer {{ margin-top: 8px; color: var(--muted); font-size: 12px; }}
    .impact {{ color: #514a40; }}
    .locked {{
      margin: 22px 0;
      padding: 14px 18px;
      background: #191713;
      color: #fff;
      border-radius: 9px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .locked span {{ color: #f8d37a; font-weight: 700; }}
    .quality-ok {{ color: var(--green); font-weight: 700; }}
    .quality-risk {{ color: var(--danger); font-weight: 700; }}
    .transcript blockquote {{
      max-height: 220px;
      overflow: hidden;
    }}
    .next-study {{
      border: 1px solid #f3d07d;
      background: #fff9e8;
      border-radius: 12px;
      padding: 20px;
    }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ padding: 18mm; max-width: none; }}
      .locked {{ break-inside: avoid; }}
      .card, table, blockquote {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="topbar">
      <div class="brand">App-Q Research</div>
      <div class="badge">Local Synthetic Study</div>
    </div>

    <section class="hero">
      <h1>{escape(report_json.get('title', 'Research Report'))}</h1>
      <p class="summary">{escape(plan.get('objective', ''))}</p>
    </section>

    <section class="metrics">
      <div class="metric"><span>Total personas</span><strong>{len(personas)}</strong></div>
      <div class="metric"><span>Age range</span><strong>{f"{min(age_values)}-{max(age_values)}" if age_values else "-"}</strong></div>
      <div class="metric"><span>Interview answers</span><strong>{quote_count}</strong></div>
      <div class="metric"><span>Quality issues</span><strong>{len(quality_issues)}</strong></div>
    </section>

    <h2>Executive Summary</h2>
    <section class="card">{html_list(report_json.get('executive_summary', []))}</section>

    <h2>Commercialisation Scorecard</h2>
    <p class="section-note">Bu skor kartı, sentetik görüşme sinyallerini ürün kararı için okunabilir bir yönetici özetine indirger.</p>
    {html_table(score_rows, [('goal', 'Goal'), ('score', 'Score'), ('evidence', 'Evidence')])}

    <h2>Panel Design</h2>
    <div class="grid">
      <section class="card">
        <h3>Role Distribution</h3>
        {html_table(role_rows, [('role', 'Role'), ('count', 'Count')])}
      </section>
      <section class="card">
        <h3>Model Usage</h3>
        {html_table(model_rows, [('model', 'Model'), ('answers', 'Answers')])}
      </section>
    </div>

    <h2>Persona Panel Preview</h2>
    <p class="section-note">Panel, aynı fikre farklı fiyat, güven, operasyon ve dijital olgunluk lenslerinden bakacak şekilde dengelenir.</p>
    <div class="persona-grid">{''.join(persona_cards) or '<p class="muted">Persona yok.</p>'}</div>

    <h2>Interview Script Coverage</h2>
    {html_table(script_rows, [('label', 'Label'), ('question', 'Question'), ('reason', 'Why it matters')])}

    <h2>Pain Point Matrix</h2>
    {html_table(report_json.get('pain_point_matrix', []), [
        ('persona', 'Persona'),
        ('segment', 'Segment'),
        ('primary_pain', 'Primary pain'),
        ('main_objection', 'Main objection'),
        ('pricing_signal', 'Pricing signal'),
    ])}

    <div class="locked">
      <div><strong>Evidence chain preview</strong><br><span>Findings below connect claims to persona quotes.</span></div>
      <div>App-Q</div>
    </div>

    <h2>Critical Findings</h2>
    <div class="finding-grid">{''.join(evidence_blocks)}</div>

    <h2>Transcript Evidence Preview</h2>
    <p class="section-note">Bu bölüm, rapordaki bulguların ham görüşme izlerine bağlanabildiğini gösterir.</p>
    <div class="finding-grid">{''.join(transcript_blocks) or '<p class="muted">Transcript yok.</p>'}</div>

    <h2>Pricing and Packaging</h2>
    <section class="card">
      <h3>{escape(pricing.get('acceptable_range', 'Pricing insight'))}</h3>
      <p>{escape(pricing.get('packaging_suggestion', ''))}</p>
      <h3>Resistance Points</h3>
      {html_list(pricing.get('resistance_points', []))}
    </section>

    <h2>Action Plan</h2>
    <section class="card">{html_list(report_json.get('action_items', []))}</section>

    <h2>Quality Control</h2>
    <section class="card">
      <p class="{ 'quality-risk' if quality_issues else 'quality-ok' }">
        {f"{len(quality_issues)} quality issue(s) need review." if quality_issues else "No critical quality warning."}
      </p>
      {html_table(quality_issues, [('persona_name', 'Persona'), ('severity', 'Severity'), ('issue', 'Issue'), ('recommendation', 'Recommendation')]) if quality_issues else ''}
    </section>

    <h2>Methodology Notes</h2>
    <section class="card">
      {html_list(report_json.get('limitations', []))}
    </section>

    <h2>Open Questions for the Next Study</h2>
    <section class="next-study">{html_list(open_questions)}</section>
  </main>
</body>
</html>"""


def suggest_follow_up_question(interview: dict) -> str:
    persona = interview.get("persona", {})
    turns = interview.get("turns", [])
    flagged_turn = next((turn for turn in turns if turn.get("quality_flags")), None)
    pricing_turn = next((turn for turn in turns if "pricing" in (turn.get("tags") or [])), None)
    objection_turn = next((turn for turn in turns if "objection" in (turn.get("tags") or [])), None)
    if flagged_turn:
        return (
            f"{persona.get('name', 'Bu persona')}, az önceki cevabında yeterince somut olmayan nokta vardı. "
            "Bunu gerçek bir satın alma anına bağlayıp hangi kanıtı görürsen fikrinin değişeceğini net söyler misin?"
        )
    if pricing_turn:
        return (
            f"{persona.get('name', 'Bu persona')}, fiyat tarafında tek bir eşik söyle: hangi TL seviyesinde "
            "denemeye değer, hangi seviyede direkt vazgeçersin?"
        )
    if objection_turn:
        return (
            f"{persona.get('name', 'Bu persona')}, bu itirazı gidermek için ürün sayfasında veya satış görüşmesinde "
            "hangi kanıtı açıkça görmek isterdin?"
        )
    return (
        f"{persona.get('name', 'Bu persona')}, bu ürünü bir arkadaşına veya yöneticine önermek için hangi tek şartın "
        "mutlaka sağlanması gerekir?"
    )


def run_follow_up_turn(interview: dict, question: str, model) -> dict:
    persona = interview.get("persona", {})
    system = (
        "Tek bir izole Türk pazar araştırması personasını simüle ediyorsun. "
        "Önceki cevaplarınla çelişme. Birinci tekil şahısla, somut ve kısa cevap ver."
    )
    prompt = (
        f"Persona: {persona.get('name')}, {persona.get('age')}, {persona.get('city')}, {persona.get('segment')}\n"
        f"Duruş: {persona.get('stance')}\n"
        f"Bağlam: {persona.get('context')}\n"
        f"Bio: {persona.get('bio')}\n"
        f"İtirazlar: {', '.join(persona.get('objections') or [])}\n"
        f"Takip sorusu: {question}\n"
        "Cevabında yeni ve karar verilebilir bir detay ver."
    )
    answer = model.generate(system, prompt)
    return {
        "question": question,
        "answer": answer,
        "tags": classify_follow_up_tags(question),
        "model_id": getattr(model, "last_model_id", None),
        "quality_flags": [],
    }


def classify_follow_up_tags(question: str) -> list[str]:
    lower = question.lower()
    tags: list[str] = []
    if any(marker in lower for marker in ["fiyat", "tl", "ödeme", "pahalı", "ucuz", "paket"]):
        tags.append("pricing")
    if any(marker in lower for marker in ["güven", "kanıt", "kvkk", "risk", "itiraz"]):
        tags.extend(["objection", "risk"])
    if any(marker in lower for marker in ["değer", "öner", "şart", "fayda"]):
        tags.append("value")
    return tags or ["risk"]


def plan_from_json(data: dict) -> ResearchPlan:
    return ResearchPlan(
        objective=data.get("objective", ""),
        assumptions=data.get("assumptions", []),
        clarifying_questions=[
            ClarifyingQuestion(
                id=item.get("id", ""),
                question=item.get("question", ""),
                reason=item.get("reason", ""),
                priority=item.get("priority", "medium"),
            )
            for item in data.get("clarifying_questions", [])
        ],
        interview_questions=data.get("interview_questions", []),
        recommended_panel_size=data.get("recommended_panel_size", 0),
        interview_script=[
            InterviewQuestion(
                id=item.get("id", ""),
                label=item.get("label", ""),
                question=item.get("question", ""),
                reason=item.get("reason", ""),
                tags=item.get("tags", []),
            )
            for item in data.get("interview_script", [])
        ],
    )


def persona_from_json(data: dict) -> Persona:
    return Persona(
        id=data.get("id", ""),
        name=data.get("name", ""),
        age=int(data.get("age", 0)),
        city=data.get("city", ""),
        segment=data.get("segment", ""),
        stance=data.get("stance", "Observer"),
        price_sensitivity=int(data.get("price_sensitivity", 5)),
        digital_confidence=int(data.get("digital_confidence", 5)),
        context=data.get("context", ""),
        goals=data.get("goals", []),
        objections=data.get("objections", []),
        knowledge_boundary=data.get("knowledge_boundary", ""),
        country_code=data.get("country_code", "TR"),
        origin_country=data.get("origin_country", "Türkiye"),
        role_title=data.get("role_title", ""),
        bio=data.get("bio", ""),
        attributes=data.get("attributes", {}),
        traits=data.get("traits", {}),
    )


def interview_from_json(data: dict) -> PersonaInterview:
    return PersonaInterview(
        persona=persona_from_json(data.get("persona", {})),
        turns=[
            InterviewTurn(
                question=turn.get("question", ""),
                answer=turn.get("answer", ""),
                tags=turn.get("tags", []),
                model_id=turn.get("model_id"),
                quality_flags=turn.get("quality_flags", []),
            )
            for turn in data.get("turns", [])
        ],
        consistency_notes=data.get("consistency_notes", []),
    )


def resynthesize_report_json(report_json: dict, brief: ResearchBrief) -> tuple[dict, str]:
    plan = plan_from_json(report_json.get("plan", {}))
    interviews = [interview_from_json(item) for item in report_json.get("interviews", [])]
    personas = [interview.persona for interview in interviews]
    report = synthesize_report(brief, plan, personas, interviews)
    report_dict = asdict(report)
    report_markdown = render_markdown(report)
    return report_dict, report_markdown


def interview_progress(interview: dict, script_count: int) -> tuple[int, int]:
    turn_count = len(interview.get("turns", []))
    target = script_count or turn_count or 1
    return min(turn_count, target), target


def render_interview_card(interview: dict, script_count: int, card_key: str) -> None:
    persona = interview.get("persona", {})
    quality = interview_quality_summary(interview)
    done, target = interview_progress(interview, script_count)
    progress = done / target if target else 0
    persona_role = persona.get("role_title") or persona.get("segment", "Bilinmeyen")
    with st.container(border=True):
        header_cols = st.columns([0.18, 0.82])
        header_cols[0].markdown(f"## {str(persona.get('name', '?'))[:1]}")
        header_cols[1].markdown(f"#### {persona.get('name')}, {persona.get('age')}")
        header_cols[1].caption(f"{persona_role} · {persona.get('city')}, {persona.get('origin_country', 'Türkiye')}")

        status = "Completed" if done >= target and quality["fail_count"] == 0 else "Review"
        st.caption(f"{done}/{target}")
        st.progress(progress)
        if status == "Completed":
            st.success("Completed", icon="✓")
        else:
            st.warning("Review needed", icon="!")

        if quality["warning_count"]:
            st.caption(f"{quality['warning_count']} kalite uyarısı")
        if st.button("View Transcript", key=f"view_transcript_{card_key}", use_container_width=True):
            st.session_state["selected_interview_id"] = persona.get("id")
            st.rerun()
        if st.button("Follow Up Question", key=f"follow_up_select_{card_key}", use_container_width=True):
            st.session_state["selected_interview_id"] = persona.get("id")
            st.session_state[f"focus_follow_up_{persona.get('id')}"] = True
            st.rerun()


def wizard_missing_fields(data: dict) -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    if not data.get("idea"):
        missing.append(("idea", "Ürün fikrini ve çözdüğü problemi 4-5 cümleyle anlatır mısın?"))
    if not data.get("title"):
        missing.append(("title", "Bu çalışmaya raporda görünecek kısa bir başlık verelim."))
    if not data.get("target_users"):
        missing.append(("target_users", "En çok öğrenmek istediğin kullanıcı tipi kim: kimler, hangi durumda, ne için kullanacak?"))
    if not data.get("questions"):
        missing.append(("questions", "Bu araştırma sonunda hangi kararı almak istiyorsun: fiyat, özellik önceliği, mesaj, hedef segment veya devam/iptal kararı mı?"))
    if not data.get("expected_price"):
        missing.append(("expected_price", "Aklındaki fiyat, paket veya ödeme modeli ne? Bilmiyorsan test etmek istediğin aralığı yaz."))
    if not data.get("competitors"):
        missing.append(("competitors", "Kullanıcı bugün bu ihtiyacı hangi alternatiflerle çözüyor? Rakip, Excel, WhatsApp, ajans, manuel süreç olabilir."))
    if not data.get("success_metric"):
        missing.append(("success_metric", "Bu araştırmada başarı sinyali ne olacak: satın alma niyeti, güven, fiyat kabulü, özellik önceliği veya churn riski?"))
    return missing


def wizard_readiness_score(data: dict) -> int:
    fields = ["title", "idea", "target_users", "questions", "expected_price", "competitors", "success_metric"]
    complete = 0
    for field_name in fields:
        value = data.get(field_name)
        if isinstance(value, list):
            complete += 1 if value else 0
        else:
            complete += 1 if value else 0
    return round(100 * complete / len(fields))


def build_wizard_reply(data: dict) -> str:
    missing = wizard_missing_fields(data)
    score = wizard_readiness_score(data)
    if not data.get("idea"):
        return (
            "Önce fikrin çekirdeğini netleştirelim. Ne inşa etmeyi düşünüyorsun, kimin hangi problemine çözüm olacak "
            "ve kullanıcı bugün bu işi nasıl çözüyor?"
        )
    if missing:
        next_question = missing[0][1]
        return (
            f"Brief şu an %{score} hazır. Fikir anlaşılır, ama araştırmanın karar üretebilmesi için bir boşluğu "
            f"kapatmamız gerekiyor: {next_question}"
        )
    return (
        f"Brief %{score} hazır. Bu haliyle persona üretimine geçebiliriz. Ben bu çalışmayı fikir doğrulama, fiyat "
        "itirazları, alternatiflere göre konumlandırma ve satın alma bariyerleri üzerinden koştururdum."
    )


def build_llm_wizard_reply(data: dict, model) -> str:
    missing = wizard_missing_fields(data)
    next_question = missing[0][1] if missing else "Brief yeterli. Araştırmayı başlatmadan önce en riskli varsayımı seçtir."
    system = (
        "Sen Defne'sin: App-Q içinde çalışan kıdemli Türkçe pazar araştırması mimarı. "
        "Kullanıcıyı memnun etmeye çalışma; karar alınabilir brief üret. "
        "Tek seferde en fazla bir ana soru sor. Kısa, net, Türkçe cevap ver."
    )
    prompt = (
        f"Mevcut brief JSON:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
        f"Deterministik sıradaki soru: {next_question}\n\n"
        "Görevin: Kısa bir durum değerlendirmesi yap, eksik alanı söyle ve kullanıcıya tek net soru sor. "
        "Eğer brief tamam ise araştırma hedefini onayla ve en riskli varsayımı seçmesini iste."
    )
    return model.generate(system, prompt)


def build_generated_goal(data: dict) -> str:
    target = ", ".join(data.get("target_users", [])) or "hedef kullanıcılar"
    questions = ", ".join(data.get("questions", [])) or "satın alma ve kullanım bariyerleri"
    price = data.get("expected_price") or "belirlenecek fiyat/paket"
    return (
        f"{data.get('title') or 'Yeni ürün fikri'} için {data.get('market') or 'Türkiye'} pazarında {target} "
        f"segmentlerinin {data.get('idea') or 'ürün fikrine'} tepkisini test etmek; özellikle {questions}, "
        f"{price} kabulü, güven bariyerleri ve mevcut alternatiflere göre avantaj/dezavantajları ortaya çıkarmak."
    )


def build_role_suggestions(data: dict) -> list[dict[str, str | int | bool]]:
    category = (data.get("category") or "").lower()
    targets = " ".join(data.get("target_users", [])).lower()
    is_b2c = any(marker in f"{category} {targets}" for marker in ["e-ticaret", "pazaryeri", "tüketici", "mobil", "alışveriş"])
    if is_b2c:
        return [
            {
                "selected": True,
                "role": "Fiyat Hassas Kullanıcı",
                "why": "TL fiyat, kampanya, taksit, kargo ve beklenmeyen ücretlere sert tepki verir.",
                "count": 3,
            },
            {
                "selected": True,
                "role": "Dijital Rahat Kullanıcı",
                "why": "Mobil akış, hız, tasarım ve kolaylık beklentisini temsil eder.",
                "count": 2,
            },
            {
                "selected": True,
                "role": "Güven Şüphecisi",
                "why": "KVKK, kart bilgisi, yorum güveni ve satıcı güvenilirliği itirazlarını üretir.",
                "count": 2,
            },
        ]
    return [
        {
            "selected": True,
            "role": "Bütçe Sahibi Karar Verici",
            "why": "Satın alma niyeti, ROI beklentisi ve abonelik direncini test eder.",
            "count": 2,
        },
        {
            "selected": True,
            "role": "Operasyonel Kullanıcı",
            "why": "Günlük iş akışı, zaman kazancı ve öğrenme zahmeti üzerinden değerlendirir.",
            "count": 2,
        },
        {
            "selected": True,
            "role": "Kurumsal Şüpheci",
            "why": "KVKK, güvenilirlik, iç onay ve kanıt zinciri risklerini zorlar.",
            "count": 1,
        },
    ]


def build_brief(data: dict) -> ResearchBrief:
    return ResearchBrief(
        title=data["title"],
        market=data.get("market", "Türkiye"),
        category=data.get("category", ""),
        idea=data["idea"],
        target_users=data.get("target_users", []),
        questions=data.get("questions", []),
        competitors=data.get("competitors", []),
        expected_price=data.get("expected_price") or None,
        sales_channel=data.get("sales_channel") or None,
        success_metric=data.get("success_metric") or None,
    )


def persist_outputs(report_markdown: str, report_json: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "operator-report.md").write_text(report_markdown, encoding="utf-8")
    (OUTPUT_DIR / "operator-report.json").write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def render_report_dashboard(report_json: dict, report_markdown: str) -> None:
    model_usage = report_json.get("model_usage", {})
    quality_issues = report_json.get("quality_issues", [])
    findings = report_json.get("findings", [])
    pricing = report_json.get("pricing", {})

    st.subheader("Yönetici Özeti")
    for item in report_json.get("executive_summary", []):
        st.markdown(f"- {item}")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Persona", len(report_json.get("personas", [])))
    metric_cols[1].metric("Görüşme Yanıtı", sum(model_usage.values()) if model_usage else 0)
    metric_cols[2].metric("Kalite Uyarısı", len(quality_issues))
    metric_cols[3].metric("Bulgu", len(findings))

    st.markdown("#### Model Kullanımı")
    if model_usage:
        cols = st.columns(len(model_usage))
        for index, (model_id, count) in enumerate(model_usage.items()):
            cols[index].metric(model_id, count)
    else:
        st.info("Model kullanımı kaydedilmedi.")

    st.markdown("#### Pain Point Matrisi")
    matrix = report_json.get("pain_point_matrix", [])
    if matrix:
        st.dataframe(matrix, use_container_width=True, hide_index=True)
    else:
        st.info("Pain point matrisi henüz yok.")

    st.markdown("#### Kritik Bulgular")
    for finding in findings:
        with st.container(border=True):
            st.markdown(f"##### {finding.get('title', 'Bulgu')}")
            st.write(finding.get("summary", ""))
            st.caption(f"Kategori: {finding.get('category')} / Güven: {finding.get('confidence')}")
            evidence = finding.get("evidence", [])
            if evidence:
                with st.expander("Kanıt alıntıları"):
                    for item in evidence:
                        st.markdown(
                            f"- **{item.get('persona_name')} ({item.get('stance')})**: "
                            f"“{item.get('quote')}”"
                        )

    st.markdown("#### Fiyat ve Paketleme")
    st.write(pricing.get("acceptable_range", ""))
    st.caption(pricing.get("packaging_suggestion", ""))
    for point in pricing.get("resistance_points", []):
        st.markdown(f"- {point}")

    st.markdown("#### Aksiyon Listesi")
    for item in report_json.get("action_items", []):
        st.markdown(f"- {item}")

    st.markdown("#### Kalite Kontrol")
    if quality_issues:
        fail_count = sum(1 for issue in quality_issues if issue.get("severity") == "fail")
        if fail_count:
            st.error(f"{fail_count} kritik kalite sorunu var. Raporu müşteriye göndermeden önce gözden geçir.")
        else:
            st.warning("Kalite uyarıları var. Zayıf cevapları kontrol et.")
        st.dataframe(quality_issues, use_container_width=True, hide_index=True)
    else:
        st.success("Kritik kalite uyarısı yok.")

    st.download_button(
        "Markdown raporu indir",
        data=report_markdown,
        file_name="app-q-report.md",
        mime="text/markdown",
    )
    st.download_button(
        "HTML raporu indir",
        data=render_report_html(report_json, report_markdown),
        file_name="app-q-report.html",
        mime="text/html",
    )


st.set_page_config(page_title="App-Q Operator", page_icon="Q", layout="wide")

sample = load_sample()
if "brief_initialized" not in st.session_state:
    seed_brief_state(sample)
    st.session_state["brief_initialized"] = True
if "wizard_messages" not in st.session_state:
    st.session_state["wizard_messages"] = [
        {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
    ]

st.title("App-Q")
st.caption("Türkiye pazarı için lokal sentetik persona araştırma operatörü")
provider_name = os.getenv("APP_MODEL_PROVIDER", "mock")
if provider_name == "ollama-router":
    model_caption = (
        f"B2C: {os.getenv('APP_Q_B2C_MODEL_ID', 'app-q-trendyol')} / "
        f"Genel: {os.getenv('APP_Q_GENERAL_MODEL_ID', 'app-q-kizagan-e4b')}"
    )
else:
    model_caption = os.getenv("APP_MODEL_ID", "mock-research-model")
st.caption(f"Model provider: {provider_name} / model: {model_caption}")

with st.sidebar:
    with st.expander("Kayitli Calismalar", expanded=True):
        studies = list_studies()
        current_study_id = st.session_state.get("current_study_id")
        if current_study_id:
            st.caption(f"Acik calisma: `{current_study_id}`")
        else:
            st.caption("Henuz kayitli bir calisma acik degil.")

        study_options = {
            f"{item.get('title', item['id'])} - {item.get('updated_at', '')}": item["id"]
            for item in studies
        }
        selected_study_label = st.selectbox(
            "Calisma sec",
            options=list(study_options.keys()),
            index=0 if study_options else None,
            placeholder="Kayitli calisma yok",
            label_visibility="collapsed",
        )
        study_cols = st.columns(3)
        if study_cols[0].button("Ac", use_container_width=True, disabled=not selected_study_label):
            selected_study_id = study_options[selected_study_label]
            apply_study_payload(selected_study_id, load_study_payload(selected_study_id))
            st.success("Calisma yuklendi.")
            st.rerun()
        if study_cols[1].button("Kaydet", use_container_width=True):
            saved_id = save_study_payload(current_study_id)
            st.session_state["current_study_id"] = saved_id
            st.success("Calisma kaydedildi.")
            st.rerun()
        if study_cols[2].button("Arsivle", use_container_width=True, disabled=not selected_study_label):
            selected_study_id = study_options[selected_study_label]
            archive_study(selected_study_id)
            if current_study_id == selected_study_id:
                st.session_state.pop("current_study_id", None)
            st.success("Calisma arsivlendi.")
            st.rerun()

        if st.button("Yeni bos calisma", use_container_width=True):
            seed_brief_state({"market": "TÃ¼rkiye"})
            st.session_state["wizard_messages"] = [
                {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
            ]
            st.session_state.pop("wizard_role_names", None)
            st.session_state.pop("current_study_id", None)
            clear_generated_state()
            st.rerun()
    st.header("Araştırma Brief'i")
    col_sample, col_clear = st.columns(2)
    if col_sample.button("Örneği yükle", use_container_width=True):
        seed_brief_state(sample)
        st.session_state["wizard_messages"] = [
            {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
        ]
        st.session_state.pop("wizard_role_names", None)
        st.session_state.pop("current_study_id", None)
        clear_generated_state()
        st.rerun()
    if col_clear.button("Sıfırla", use_container_width=True):
        seed_brief_state({"market": "Türkiye"})
        st.session_state["wizard_messages"] = [
            {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
        ]
        st.session_state.pop("wizard_role_names", None)
        st.session_state.pop("current_study_id", None)
        clear_generated_state()
        st.rerun()

    title = st.text_input("Başlık", key=BRIEF_STATE_KEYS["title"])
    market = st.text_input("Pazar", key=BRIEF_STATE_KEYS["market"])
    category = st.text_input("Kategori", key=BRIEF_STATE_KEYS["category"])
    expected_price = st.text_input("Beklenen fiyat/paket", key=BRIEF_STATE_KEYS["expected_price"])
    sales_channel = st.text_input("Satış kanalı", key=BRIEF_STATE_KEYS["sales_channel"])
    success_metric = st.text_input("Başarı metriği", key=BRIEF_STATE_KEYS["success_metric"])
    idea = st.text_area("Ürün fikri / araştırma konusu", height=170, key=BRIEF_STATE_KEYS["idea"])
    target_users = st.text_area(
        "Hedef kullanıcılar",
        height=100,
        key=BRIEF_STATE_KEYS["target_users"],
    )
    competitors = st.text_area(
        "Alternatifler / rakipler",
        height=90,
        key=BRIEF_STATE_KEYS["competitors"],
    )
    research_questions = st.text_area(
        "Yanıtlanacak sorular",
        height=120,
        key=BRIEF_STATE_KEYS["questions"],
    )

    run_button = st.button("Araştırmayı Çalıştır", type="primary", use_container_width=True)

brief_data = {
    "title": title,
    "market": market,
    "category": category,
    "idea": idea,
    "target_users": parse_lines(target_users),
    "questions": parse_lines(research_questions),
    "competitors": parse_lines(competitors),
    "expected_price": expected_price,
    "sales_channel": sales_channel,
    "success_metric": success_metric,
}

wizard_score = wizard_readiness_score(brief_data)
missing_fields = wizard_missing_fields(brief_data)

with st.container(border=True):
    header_cols = st.columns([0.72, 0.28])
    with header_cols[0]:
        st.subheader(f"{WIZARD_NAME} - {WIZARD_ROLE}")
        st.caption(WIZARD_SYSTEM_STYLE)
    with header_cols[1]:
        st.metric("Brief Hazırlığı", f"%{wizard_score}")
        st.progress(wizard_score / 100)

    st.markdown("#### Wizard cevabı")
    st.write(build_wizard_reply(brief_data))
    if st.button("Defne cevabını lokal modelle iyileştir", use_container_width=True):
        try:
            llm_reply = build_llm_wizard_reply(brief_data, get_model_provider())
            append_wizard_message("assistant", llm_reply)
            st.rerun()
        except ModelProviderError as exc:
            st.error(str(exc))

    st.markdown("#### Defne ile brief sohbeti")
    for message in st.session_state.get("wizard_messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if missing_fields:
        next_field, next_question = missing_fields[0]
        with st.form("wizard_intake_form", clear_on_submit=True):
            answer = st.text_area("Cevabın", placeholder=next_question, height=110)
            submitted = st.form_submit_button("Defne'ye gönder", type="primary")
        if submitted:
            if answer.strip():
                append_wizard_message("user", answer.strip())
                apply_wizard_answer(next_field, answer)
                updated_data = current_brief_data()
                append_wizard_message("assistant", build_wizard_reply(updated_data))
                st.rerun()
            else:
                st.warning("Defne'nin brief'i ilerletebilmesi için kısa bir cevap yaz.")
    else:
        st.caption("Brief tamamlandı. İstersen sol panelden manuel düzeltme yapabilir veya araştırmayı çalıştırabilirsin.")

    if missing_fields:
        st.markdown("#### Eksik netlik alanları")
        for _, question in missing_fields[:4]:
            st.markdown(f"- {question}")
    else:
        st.success("Brief araştırma akışını başlatmak için yeterli görünüyor.")

    if idea:
        st.markdown("#### Üretilen araştırma hedefi")
        st.info(build_generated_goal(brief_data))

    st.markdown("#### Önerilen araştırma rolleri")
    role_rows = build_role_suggestions(brief_data)
    sync_role_state(role_rows)
    selected_roles = selected_role_rows(role_rows)
    role_cols = st.columns(len(role_rows))
    for index, role in enumerate(role_rows):
        role_name = str(role["role"])
        selected_key = role_state_key(role_name, "selected")
        count_key = role_state_key(role_name, "count")
        with role_cols[index]:
            with st.container(border=True):
                st.checkbox("Seç", key=selected_key)
                st.markdown(f"##### {role_name}")
                st.write(role["why"])
                st.number_input("Sayı", min_value=0, max_value=10, step=1, key=count_key)

    total_selected = sum(int(role["count"]) for role in selected_roles)
    if selected_roles:
        st.caption(
            "Seçilen panel: "
            + ", ".join(f"{role['role']} x{role['count']}" for role in selected_roles)
            + f" / toplam {total_selected} katılımcı"
        )
    else:
        st.warning("En az bir araştırma rolü seçilmeden persona paneli anlamlı olmayacak.")

if not title or not idea:
    st.subheader("Studies")
    render_studies_dashboard()
    st.info("Başlık ve ürün fikri girildiğinde araştırma planı ve rapor üretilebilir.")
    st.stop()

brief = build_brief(brief_data)
role_suggestions = build_role_suggestions(brief_data)
selected_roles = selected_role_rows(role_suggestions)
panel_roles = build_panel_roles(role_suggestions)
plan = build_research_plan(brief, panel_roles or None)
personas = generate_personas(brief, panel_roles or None)

with st.expander("Studies Dashboard", expanded=False):
    render_studies_dashboard()

plan_tab, persona_tab, script_tab, interview_tab, report_tab, raw_tab = st.tabs(
    ["Plan", "Personalar", "Script", "Görüşmeler", "Rapor", "Ham Çıktı"]
)

with plan_tab:
    st.subheader("Araştırma Planı")
    st.write(plan.objective)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Varsayımlar")
        for assumption in plan.assumptions:
            st.markdown(f"- {assumption}")
    with col_b:
        st.markdown("#### Netleştirici Sorular")
        for question in plan.clarifying_questions:
            st.markdown(f"- **{question.priority.upper()}**: {question.question}")
            st.caption(question.reason)

    st.markdown("#### Görüşme Rehberi")
    for index, question in enumerate(plan.interview_questions, start=1):
        st.markdown(f"{index}. {question}")

with persona_tab:
    st.subheader("Persona Paneli")
    overview_tab, cards_tab = st.tabs(["Overview", "Kartlar"])
    with overview_tab:
        render_persona_overview(personas)

    with cards_tab:
        if selected_roles:
            st.markdown("#### Wizard Panel Kompozisyonu")
            st.dataframe(selected_roles, use_container_width=True, hide_index=True)
        else:
            st.warning("Wizard tarafında seçili araştırma rolü yok.")
        st.markdown("#### Üretilen Sentetik Personalar")
        cols = st.columns(3)
        for index, persona in enumerate(personas):
            with cols[index % 3]:
                render_persona_card(persona)

with script_tab:
    st.subheader("Interview Script")
    st.caption("Brief ve seçilen araştırma rollerinden üretilen etiketli soru seti.")
    for index, question in enumerate(plan.interview_script, start=1):
        with st.container(border=True):
            st.caption(question.label)
            st.markdown(f"#### {index}. {question.question}")
            with st.expander("Soru amacı ve etiketler"):
                st.write(question.reason)
                if question.tags:
                    st.caption("Etiketler: " + ", ".join(question.tags))

if run_button:
    with st.spinner("Personalar sırayla görüşmeye alınıyor..."):
        try:
            report = run_research(brief, get_model_provider(), panel_roles or None)
            report_json = asdict(report)
            report_markdown = render_markdown(report)
            persist_outputs(report_markdown, report_json)
            st.session_state["report_json"] = report_json
            st.session_state["report_markdown"] = report_markdown
            if st.session_state.get("current_study_id"):
                save_study_payload(st.session_state["current_study_id"])
        except ModelProviderError as exc:
            st.error(str(exc))

with report_tab:
    if "report_markdown" not in st.session_state:
        st.info("Raporu üretmek için sol panelden araştırmayı çalıştır.")
    else:
        render_report_dashboard(st.session_state["report_json"], st.session_state["report_markdown"])

with interview_tab:
    if "report_json" not in st.session_state:
        st.info("Görüşmeleri görmek için araştırmayı çalıştır.")
    else:
        interviews = st.session_state["report_json"].get("interviews", [])
        total_turns = sum(len(interview.get("turns", [])) for interview in interviews)
        total_warnings = sum(interview_quality_summary(interview)["warning_count"] for interview in interviews)
        completed = len(interviews)
        summary_cols = st.columns(4)
        summary_cols[0].metric("Tamamlanan Persona", completed)
        summary_cols[1].metric("Toplam Yanıt", total_turns)
        summary_cols[2].metric("Kalite Uyarısı", total_warnings)
        summary_cols[3].metric("Script Sorusu", len(st.session_state["report_json"].get("plan", {}).get("interview_script", [])))

        role_options = sorted(
            {
                interview.get("persona", {}).get("role_title")
                or interview.get("persona", {}).get("segment", "Bilinmeyen")
                for interview in interviews
            }
        )
        selected_role_filter = st.segmented_control(
            "Rol filtresi",
            options=["Tümü", *role_options],
            default="Tümü",
        )

        script_count = len(st.session_state["report_json"].get("plan", {}).get("interview_script", []))
        visible_interviews = []
        for interview in interviews:
            persona = interview.get("persona", {})
            persona_role = persona.get("role_title") or persona.get("segment", "Bilinmeyen")
            if selected_role_filter == "Tümü" or persona_role == selected_role_filter:
                visible_interviews.append(interview)

        st.markdown("#### Interview Cards")
        card_cols = st.columns(3)
        for index, interview in enumerate(visible_interviews):
            with card_cols[index % 3]:
                persona = interview.get("persona", {})
                render_interview_card(interview, script_count, f"{persona.get('id')}_{index}")

        if visible_interviews and "selected_interview_id" not in st.session_state:
            st.session_state["selected_interview_id"] = visible_interviews[0].get("persona", {}).get("id")

        selected_interview = next(
            (
                interview
                for interview in visible_interviews
                if interview.get("persona", {}).get("id") == st.session_state.get("selected_interview_id")
            ),
            visible_interviews[0] if visible_interviews else None,
        )

        st.markdown("#### Transcript Detail")
        if not selected_interview:
            st.info("Bu filtrede görüşme yok.")
        else:
            interview = selected_interview
            persona = interview.get("persona", {})
            persona_role = persona.get("role_title") or persona.get("segment", "Bilinmeyen")
            quality = interview_quality_summary(interview)
            model_usage = interview_model_usage(interview)
            title = (
                f"{persona.get('name')} - {persona_role} "
                f"({quality['turn_count']}/{len(st.session_state['report_json'].get('plan', {}).get('interview_script', [])) or quality['turn_count']})"
            )
            with st.container(border=True):
                st.markdown(f"### {title}")
                cols = st.columns(4)
                cols[0].metric("Yanıt", quality["turn_count"])
                cols[1].metric("Uyarı", quality["warning_count"])
                cols[2].metric("Kritik", quality["fail_count"])
                cols[3].metric("Model", ", ".join(f"{key} x{value}" for key, value in model_usage.items()))

                st.caption(persona.get("bio") or persona.get("context", ""))
                st.download_button(
                    "Transcript indir",
                    data=render_transcript_markdown(interview),
                    file_name=f"{persona.get('name', 'persona').lower()}-transcript.md",
                    mime="text/markdown",
                    key=f"download_transcript_{persona.get('id')}",
                )

                for turn in interview.get("turns", []):
                    st.markdown(f"**Soru:** {turn.get('question')}")
                    st.write(turn.get("answer"))
                    meta = [f"model: `{turn.get('model_id') or 'unknown'}`"]
                    flags = turn.get("quality_flags") or []
                    if flags:
                        meta.append("uyarı: " + ", ".join(flags))
                    st.caption(" / ".join(meta))
                    st.divider()

                st.markdown("#### Takip Sorusu Önerisi")
                follow_up_question = suggest_follow_up_question(interview)
                follow_up_key = f"follow_up_question_{persona.get('id')}"
                if st.session_state.pop(f"focus_follow_up_{persona.get('id')}", False):
                    st.info("Karttan takip sorusu alanına geldin. Soruyu düzenleyip çalıştırabilirsin.")
                edited_follow_up = st.text_area(
                    "Takip sorusu",
                    value=st.session_state.get(follow_up_key, follow_up_question),
                    key=follow_up_key,
                    height=90,
                )
                if st.button("Takip sorusunu çalıştır", key=f"run_follow_up_{persona.get('id')}"):
                    try:
                        follow_up_turn = run_follow_up_turn(interview, edited_follow_up, get_model_provider())
                        interview.setdefault("turns", []).append(follow_up_turn)
                        updated_report_json, updated_report_markdown = resynthesize_report_json(
                            st.session_state["report_json"],
                            brief,
                        )
                        st.session_state["report_json"] = updated_report_json
                        st.session_state["report_markdown"] = updated_report_markdown
                        persist_outputs(st.session_state["report_markdown"], st.session_state["report_json"])
                        if st.session_state.get("current_study_id"):
                            save_study_payload(st.session_state["current_study_id"])
                        st.success("Takip cevabı transcript'e eklendi ve rapor yeniden sentezlendi.")
                        st.rerun()
                    except ModelProviderError as exc:
                        st.error(str(exc))

with raw_tab:
    if "report_json" not in st.session_state:
        st.json({"plan": asdict(plan), "wizard_roles": selected_roles})
    else:
        st.json({"report": st.session_state["report_json"], "wizard_roles": selected_roles})
