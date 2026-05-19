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


st.set_page_config(page_title="App-Q Operator", page_icon="Q", layout="wide")

sample = load_sample()

st.title("App-Q")
st.caption("Türkiye pazarı için lokal sentetik persona araştırma operatörü")
st.caption(
    f"Model provider: {os.getenv('APP_MODEL_PROVIDER', 'mock')} / "
    f"model: {os.getenv('APP_MODEL_ID', 'mock-research-model')}"
)

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

plan_tab, persona_tab, report_tab, raw_tab = st.tabs(["Plan", "Personalar", "Rapor", "Ham Çıktı"])

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
        st.markdown(st.session_state["report_markdown"])
        st.download_button(
            "Markdown raporu indir",
            data=st.session_state["report_markdown"],
            file_name="app-q-report.md",
            mime="text/markdown",
        )

with raw_tab:
    if "report_json" not in st.session_state:
        st.json(asdict(plan))
    else:
        st.json(st.session_state["report_json"])
