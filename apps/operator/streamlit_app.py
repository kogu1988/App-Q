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
WIZARD_NAME = "Defne"
WIZARD_ROLE = "App-Q araştırma mimarı"
WIZARD_SYSTEM_STYLE = (
    "Defne, pazara çıkmadan önce ürün fikrini keskinleştiren kıdemli bir araştırma mimarıdır. "
    "Kibar ama gevşek değildir; kullanıcının fikrini onaylamak yerine karar alınabilir brief ister. "
    "Her adımda tek ana eksikliği yakalar, somut soru sorar ve sonunda araştırma hedefi ile rol önerilerini çıkarır."
)
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
    st.header("Araştırma Brief'i")
    col_sample, col_clear = st.columns(2)
    if col_sample.button("Örneği yükle", use_container_width=True):
        seed_brief_state(sample)
        st.session_state["wizard_messages"] = [
            {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
        ]
        st.rerun()
    if col_clear.button("Sıfırla", use_container_width=True):
        seed_brief_state({"market": "Türkiye"})
        st.session_state["wizard_messages"] = [
            {"role": "assistant", "content": build_wizard_reply(current_brief_data())}
        ]
        st.session_state.pop("report_json", None)
        st.session_state.pop("report_markdown", None)
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
    role_cols = st.columns(len(role_rows))
    for index, role in enumerate(role_rows):
        with role_cols[index]:
            with st.container(border=True):
                status = "Seçili" if role["selected"] else "Opsiyonel"
                st.caption(status)
                st.markdown(f"##### {role['role']}")
                st.write(role["why"])
                st.metric("Önerilen sayı", role["count"])

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
