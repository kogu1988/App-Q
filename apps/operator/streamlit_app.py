from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from packages.research_engine.models import ResearchBrief
from packages.research_engine.providers import ModelProviderError, get_model_provider
from packages.research_engine.reporting import render_markdown
from packages.research_engine.workflow import build_research_plan, generate_personas, run_research


SAMPLE_PATH = ROOT / "data" / "samples" / "first-brief.json"
OUTPUT_DIR = ROOT / "data" / "outputs"


def parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def load_sample() -> dict:
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


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


st.set_page_config(page_title="App-Q Operator", page_icon="Q", layout="wide")

sample = load_sample()

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
    st.header("Araştırma Brief'i")
    use_sample = st.toggle("Örnek brief'i yükle", value=True)
    defaults = sample if use_sample else {}

    title = st.text_input("Başlık", value=defaults.get("title", ""))
    market = st.text_input("Pazar", value=defaults.get("market", "Türkiye"))
    category = st.text_input("Kategori", value=defaults.get("category", ""))
    expected_price = st.text_input("Beklenen fiyat/paket", value=defaults.get("expected_price", ""))
    sales_channel = st.text_input("Satış kanalı", value=defaults.get("sales_channel", ""))
    success_metric = st.text_input("Başarı metriği", value=defaults.get("success_metric", ""))
    idea = st.text_area("Ürün fikri / araştırma konusu", value=defaults.get("idea", ""), height=170)
    target_users = st.text_area(
        "Hedef kullanıcılar",
        value="\n".join(defaults.get("target_users", [])),
        height=100,
    )
    competitors = st.text_area(
        "Alternatifler / rakipler",
        value="\n".join(defaults.get("competitors", [])),
        height=90,
    )
    research_questions = st.text_area(
        "Yanıtlanacak sorular",
        value="\n".join(defaults.get("questions", [])),
        height=120,
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

if not title or not idea:
    st.info("Başlık ve ürün fikri girildiğinde araştırma planı ve rapor üretilebilir.")
    st.stop()

brief = build_brief(brief_data)
plan = build_research_plan(brief)
personas = generate_personas(brief)

plan_tab, persona_tab, report_tab, interview_tab, raw_tab = st.tabs(
    ["Plan", "Personalar", "Rapor", "Görüşmeler", "Ham Çıktı"]
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
    cols = st.columns(2)
    for index, persona in enumerate(personas):
        with cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"### {persona.name}")
                st.write(f"{persona.age}, {persona.city} - {persona.segment}")
                st.write(f"**Duruş:** {persona.stance}")
                st.write(f"**Fiyat hassasiyeti:** {persona.price_sensitivity}/10")
                st.write(f"**Dijital özgüven:** {persona.digital_confidence}/10")
                st.caption(persona.context)
                st.markdown("**İtirazlar**")
                for objection in persona.objections:
                    st.markdown(f"- {objection}")

if run_button:
    with st.spinner("Personalar sırayla görüşmeye alınıyor..."):
        try:
            report = run_research(brief, get_model_provider())
            report_json = asdict(report)
            report_markdown = render_markdown(report)
            persist_outputs(report_markdown, report_json)
            st.session_state["report_json"] = report_json
            st.session_state["report_markdown"] = report_markdown
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
        for interview in st.session_state["report_json"].get("interviews", []):
            persona = interview.get("persona", {})
            with st.expander(f"{persona.get('name')} - {persona.get('segment')}", expanded=False):
                for turn in interview.get("turns", []):
                    st.markdown(f"**Soru:** {turn.get('question')}")
                    st.write(turn.get("answer"))
                    meta = [f"model: `{turn.get('model_id') or 'unknown'}`"]
                    flags = turn.get("quality_flags") or []
                    if flags:
                        meta.append("uyarı: " + ", ".join(flags))
                    st.caption(" / ".join(meta))
                    st.divider()

with raw_tab:
    if "report_json" not in st.session_state:
        st.json(asdict(plan))
    else:
        st.json(st.session_state["report_json"])
