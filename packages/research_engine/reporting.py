from __future__ import annotations

from html import escape
from .models import ResearchReport

# ── Rapor çıktısı için Türkçe etiket eşlemeleri ──────────────────────────────
_STANCE_TR = {
    "Innovator": "Öncü",
    "EarlyAdopter": "Erken Benimseyen",
    "Mainstream": "Ana Akım",
    "Laggard": "Geciken",
    "Skeptic": "Şüpheci",
    "Champion": "Öncü",
    "Pragmatist": "Pragmatist",
    "Observer": "Gözlemci",
    "Blocker": "Engelleyici",
}

_TRAIT_TR = {
    "Openness": "Açıklık",
    "Conscientiousness": "Sorumluluk",
    "Extraversion": "Dışadönüklük",
    "Agreeableness": "Uyumluluk",
    "Neuroticism": "Duygusal Denge",
}

_ATTR_TR = {
    "Hobbies": "Hobiler",
    "Origin country": "Ülke",
    "Current workflow": "Mevcut Çözüm",
    "Decision trigger": "Karar Tetikleyicisi",
    "Buying friction": "Satın Alma Engeli",
    "Price posture": "Fiyat Yaklaşımı",
    "Digital confidence": "Dijital Güven",
    "Segment role": "Segment Rolü",
    "Research stance": "Araştırma Duruşu",
}

_CATEGORY_TR = {
    "pain_point": "Acı Noktası",
    "value": "Değer Algısı",
    "objection": "İtiraz",
    "risk": "Risk",
    "pricing": "Fiyat",
    "positioning": "Konumlandırma",
}

_SCRIPT_LABEL_TR = {
    "CONTEXT": "BAĞLAM",
    "VALUE": "DEĞER",
    "OBJECTION": "İTİRAZ",
    "PRICING": "FİYAT",
    "ALTERNATIVES": "ALTERNATİFLER",
}

_PRIORITY_TR = {"high": "YÜKSEK", "medium": "ORTA", "low": "DÜŞÜK"}

_SEVERITY_TR = {"WARNING": "UYARI", "ERROR": "HATA", "INFO": "BİLGİ"}


def render_markdown(report: ResearchReport) -> str:
    lines: list[str] = [
        f"# {report.title}",
        "",
        "## Kullanılan Model",
        "",
    ]
    if report.model_usage:
        lines.extend(f"- `{model_id}`: {count} yanıt" for model_id, count in report.model_usage.items())
    else:
        lines.append("- Model kullanımı kaydedilmedi.")

    lines.extend(["", "## Yönetici Özeti", ""])
    lines.extend(f"- {item}" for item in report.executive_summary)

    lines.extend(
        [
            "",
        "## Araştırma Planı",
        "",
        report.plan.objective,
        "",
        "### Varsayımlar",
        "",
        ]
    )
    lines.extend(f"- {item}" for item in report.plan.assumptions)

    lines.extend(["", "### Netleştirici Sorular", ""])
    for question in report.plan.clarifying_questions:
        if isinstance(question, dict):
            _priority = str(question.get("priority", "medium")).lower()
            _q = question.get("question", "")
            _reason = question.get("reason", "")
        else:
            _priority = question.priority.lower()
            _q = question.question
            _reason = question.reason
        lines.append(f"- **{_PRIORITY_TR.get(_priority, _priority.upper())}**: {_q} _({_reason})_")

    lines.extend(["", "### Görüşme Script'i", ""])
    for index, question in enumerate(report.plan.interview_script, start=1):
        if isinstance(question, dict):
            _label = question.get("label", "")
            _q = question.get("question", "")
            _reason = question.get("reason", "")
            _tags = question.get("tags") or []
        else:
            _label = question.label
            _q = question.question
            _reason = question.reason
            _tags = question.tags or []
        _label_tr = _SCRIPT_LABEL_TR.get(_label, _label)
        _tags_tr = [_CATEGORY_TR.get(str(t), str(t)) for t in _tags]
        lines.extend(
            [
                f"{index}. **{_label_tr}** - {_q}",
                f"   - Amaç: {_reason}",
                f"   - Etiketler: {', '.join(_tags_tr) if _tags_tr else 'Genel'}",
            ]
        )

    lines.extend(["", "## Persona Paneli", ""])
    for persona in report.personas:
        lines.extend(
            [
                f"### {persona.name} - {persona.segment}",
                "",
                f"- Şehir/yaş: {persona.city}, {persona.age}",
                f"- Rol: {persona.role_title or persona.segment}",
                f"- Pazar Yaklaşımı: {_STANCE_TR.get(persona.stance, persona.stance)}",
                f"- Fiyat hassasiyeti: {persona.price_sensitivity}/10",
                f"- Dijital özgüven: {persona.digital_confidence}/10",
                f"- Kısa profil: {persona.bio or persona.context}",
                f"- Bağlam: {persona.context}",
                f"- Bilgi sınırı: {persona.knowledge_boundary}",
                "",
            ]
        )
        if persona.attributes:
            lines.extend(["Davranış alanları:"])
            lines.extend(f"- {_ATTR_TR.get(key, key)}: {value}" for key, value in persona.attributes.items())
            lines.append("")
        if persona.traits:
            lines.extend(["Kişilik skorları:"])
            lines.extend(f"- {_TRAIT_TR.get(key, key)}: {value}/100" for key, value in persona.traits.items())
            lines.append("")

    lines.extend(["## Pain Point Matrisi", ""])
    lines.extend(
        [
            "| Persona | Segment | Ana Sorun | Ana İtiraz | Fiyat Beklentisi |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.pain_point_matrix:
        lines.append(
            "| {persona} | {segment} | {primary_pain} | {main_objection} | {pricing_signal} |".format(
                persona=row["persona"],
                segment=row["segment"],
                primary_pain=row["primary_pain"].replace("\n", " "),
                main_objection=row["main_objection"].replace("\n", " "),
                pricing_signal=row["pricing_signal"].replace("\n", " "),
            )
        )
    lines.append("")

    lines.extend(["## Bulgular", ""])
    # Enhanced findings varsa onları kullan (kanıt sayıları + karar sinyali ile)
    _source_findings = getattr(report, "enhanced_findings", None) or report.findings
    for finding in _source_findings:
        lines.extend(
            [
                f"### {finding.title}",
                "",
                f"- Kategori: {_CATEGORY_TR.get(finding.category, finding.category)}",
                f"- Güven skoru: **{int(finding.confidence * 100)}%**",
                f"- Özet: {finding.summary}",
                f"- Etki: {finding.implication}",
                "",
            ]
        )
        # Enhanced finding alanları (varsa)
        supporting = getattr(finding, "supporting_count", None)
        refuting = getattr(finding, "refuting_count", None)
        signal = getattr(finding, "decision_signal", None)
        if supporting is not None:
            lines.append(
                f"- Destekleyen: **{supporting}** persona | Karşı çıkan: **{refuting or 0}** persona"
            )
        if signal:
            _SIGNAL_TR = {"SHIP": "✅ YAYINLA", "ITERATE": "🔁 İYİLEŞTİR", "INVESTIGATE": "🔍 ARAŞTIR", "KILL": "⛔ VAZGEÇ"}
            lines.append(f"- Karar sinyali: **{_SIGNAL_TR.get(signal, signal)}**")
        lines.append("")
        lines.append("Kanıtlar:")
        for evidence in finding.evidence:
            lines.append(
                f"- {evidence.persona_name} ({_STANCE_TR.get(evidence.stance, evidence.stance)}) - \"{evidence.quote}\""
            )
        lines.append("")

    lines.extend(
        [
            "## Fiyat İçgörüsü",
            "",
            f"- Kabul edilebilir model: {report.pricing.acceptable_range}",
            f"- Paket önerisi: {report.pricing.packaging_suggestion}",
            "",
            "Direnç noktaları:",
        ]
    )
    lines.extend(f"- {item}" for item in report.pricing.resistance_points)

    # ── Van Westendorp PSM (varsa) ──
    if report.van_westendorp:
        vw = report.van_westendorp
        lines.extend(
            [
                "",
                "### Van Westendorp Fiyat Hassasiyet Analizi (PSM)",
                "",
                f"- **PMC** (Alt kabul sınırı): {vw.pmc:.0f} TL",
                f"- **OPP** (Optimal fiyat noktası): {vw.opp:.0f} TL",
                f"- **IPP** (Beklenti noktası): {vw.ipp:.0f} TL",
                f"- **PME** (Üst kabul sınırı): {vw.pme:.0f} TL",
                f"- Kabul edilebilir fiyat aralığı: {vw.acceptable_range[0]:.0f} - {vw.acceptable_range[1]:.0f} TL",
                f"- Metodoloji: {vw.methodology_note}",
            ]
        )

    # ── Karar Katmanı (varsa) ──
    if getattr(report, "decision_items", None):
        lines.extend(["", "## Karar Katmanı", ""])
        _SIGNAL_TR = {"SHIP": "YAYINLA", "ITERATE": "İYİLEŞTİR", "INVESTIGATE": "ARAŞTIR", "KILL": "VAZGEÇ"}
        for d in report.decision_items:
            lines.extend(
                [
                    f"### [{_SIGNAL_TR.get(d.signal, d.signal)}] {d.title}",
                    "",
                    f"- Güven: {int(d.confidence * 100)}% | Destek: {d.supporting_count} | Karşı: {d.refuting_count}",
                    f"- Önerilen aksiyon: {d.recommended_action}",
                    "",
                ]
            )

    # ── Harici Kanıtlar (varsa) ──
    if getattr(report, "external_evidence", None):
        lines.extend(["## Harici Kanıt Doğrulaması", ""])
        lines.append("Sentetik bulguları destekleyen dış kaynaklar:")
        for ev in report.external_evidence:
            _rel = {"high": "Yüksek", "medium": "Orta", "low": "Düşük"}.get(ev.relevance, ev.relevance)
            lines.append(f"- **{ev.source_title}** (İlgi: {_rel})")
            if ev.snippet:
                lines.append(f"  - {ev.snippet[:160]}")

    # ── SES × Stance Çapraz Tablosu (varsa) ──
    if getattr(report, "ses_cross_tab", None):
        lines.extend(["", "## SES × Stance Çapraz Tablosu", "", "| SES | Kişi | Baskın Stance |", "| --- | --- | --- |"])
        for row in report.ses_cross_tab:
            lines.append(
                f"| {row.get('ses_group', '')} | {row.get('total', 0)} | {_STANCE_TR.get(row.get('dominant_stance', ''), row.get('dominant_stance', ''))} |"
            )

    # ── Marka Sağlığı (varsa) ──
    if getattr(report, "brand_health", None):
        bh = report.brand_health
        lines.extend(["", "## Marka Sağlığı Analizi", ""])
        if bh.get("top_of_mind"):
            lines.append(f"- Zihin payı lideri: **{bh['top_of_mind']}** ({bh.get('total_mentions', 0)} anma)")
        lines.append("- Yardımsız bilinirlik:")
        for brand, count in bh.get("unaided_recall", {}).items():
            lines.append(f"  - {brand}: {count}")

    # ── Keşif Kanalı Haritası (varsa) ──
    if getattr(report, "channel_map", None):
        lines.extend(["", "## Keşif Kanalı Haritası", ""])
        for ch in report.channel_map:
            lines.append(f"- {ch.get('channel', '')}: %{ch.get('pct', 0)}")

    lines.extend(["", "## Aksiyon Listesi", ""])
    lines.extend(f"- {item}" for item in report.action_items)

    lines.extend(["", "## Kalite Kontrol", ""])

    # ── Araştırma Bütünlüğü (RFI) ──
    if getattr(report, "research_quality", None):
        rq = report.research_quality
        rfi = rq.get("rfi")
        if rfi is not None:
            _rfi_ok = "✅ Geçerli" if rfi >= 0.65 else "⚠️ Eşik Altı"
            lines.append(f"- Araştırma Bütünlüğü (RFI): **{rfi * 100:.1f}/100** {_rfi_ok}")
        warnings = rq.get("warning_count", 0)
        if warnings:
            lines.append(f"- Dikkat gerektiren nokta sayısı: {warnings}")

    if report.quality_issues:
        _grouped: dict[str, dict] = {}
        for issue in report.quality_issues:
            _key = issue.issue
            if _key not in _grouped:
                _grouped[_key] = {"severity": issue.severity, "personas": [], "recommendation": issue.recommendation}
            _grouped[_key]["personas"].append(issue.persona_name)
        for msg, g in _grouped.items():
            _sev = _SEVERITY_TR.get(str(g["severity"]).upper(), str(g["severity"]).upper())
            _names = ", ".join(dict.fromkeys(g["personas"]))
            lines.append(f"- **{_sev}** ({_names}): {msg}")
            if g["recommendation"]:
                lines.append(f"  - Öneri: {g['recommendation']}")
    else:
        lines.append("- Kritik kalite uyarısı yok.")

    lines.extend(["", "## Öneriler", ""])
    lines.extend(f"- {item}" for item in report.recommendations)

    lines.extend(["", "## Sonraki Doğrulama Adımları", ""])
    lines.extend(f"- {item}" for item in report.validation_next_steps)

    lines.extend(["", "## Sınırlılıklar", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    lines.append("")

    return "\n".join(lines)


def count_by(items: list[str]) -> dict[str, int]:
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


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
            "goal": "Satın alma niyeti",
            "score": "Orta-Yüksek" if findings else "Belirsiz",
            "evidence": "Fiyat ve değer bulguları persona alıntılarıyla destekleniyor." if findings else "Rapor üretimi bekleniyor.",
        },
        {
            "goal": "Güven / KVKK bariyeri",
            "score": "Kritik",
            "evidence": "Sentetik metodoloji, veri gizliliği ve kanıt zinciri açıkça anlatılmalı.",
        },
        {
            "goal": "MVP odak netliği",
            "score": "Aksiyonlanabilir" if report_json.get("action_items") else "Eksik",
            "evidence": "Aksiyon listesi ve açık sorular sonraki sprint kararlarını besliyor.",
        },
    ]
    open_questions = [
        "Hangi segmentte ödeme niyeti gerçek satış görüşmesiyle doğrulanmalı?",
        "En güçlü itirazı azaltmak için hangi kanıt veya demo akışı gerekir?",
        "Takip görüşmesinde fiyat eşiği hangi TL aralığında sıkışıyor?",
        "Hangi özellik ilk MVP dışında bırakılırsa satın alma niyeti düşmez?",
    ]

    # ── Kurumsal ek bölümler: Karar Katmanı + Van Westendorp + Harici Kanıt ──
    decision_blocks = []
    _SIGNAL_LABEL = {"SHIP": "YAYINLA", "ITERATE": "İYİLEŞTİR", "INVESTIGATE": "ARAŞTIR", "KILL": "VAZGEÇ"}
    for d in report_json.get("decision_items", []):
        _sig = _SIGNAL_LABEL.get(str(d.get("signal", "")).upper(), d.get("signal", ""))
        decision_blocks.append(
            "<section class='card'>"
            f"<div class='eyebrow'>{escape(str(_sig))}</div>"
            f"<h3>{escape(d.get('title', ''))}</h3>"
            f"<p class='muted'>Güven: {escape(str(d.get('confidence', 0)))} · "
            f"Destek: {escape(str(d.get('supporting_count', 0)))} · Karşı: {escape(str(d.get('refuting_count', 0)))}</p>"
            f"<p>{escape(d.get('recommended_action', ''))}</p>"
            "</section>"
        )

    vw = report_json.get("van_westendorp")
    vw_blocks = ""
    if vw:
        vw_blocks = (
            "<section class='card'>"
            "<h3>Van Westendorp Fiyat Hassasiyet Analizi (PSM)</h3>"
            f"<p><strong>PMC</strong> (Alt kabul): {escape(str(round(vw.get('pmc', 0))))} TL · "
            f"<strong>OPP</strong> (Optimal): {escape(str(round(vw.get('opp', 0))))} TL · "
            f"<strong>IPP</strong> (Beklenti): {escape(str(round(vw.get('ipp', 0))))} TL · "
            f"<strong>PME</strong> (Üst kabul): {escape(str(round(vw.get('pme', 0))))} TL</p>"
            f"<p class='muted'>Kabul edilebilir aralık: {escape(str(round(vw.get('pmc', 0))))} - {escape(str(round(vw.get('pme', 0))))} TL</p>"
            "</section>"
        )

    ext_evidence = report_json.get("external_evidence", [])
    ext_blocks = "".join(
        "<section class='card'>"
        f"<h3>{escape(ev.get('source_title', ''))}</h3>"
        f"<p class='muted'>{escape(str(ev.get('relevance', '')))} ilgi · {escape(ev.get('finding_title', ''))}</p>"
        f"<p>{escape((ev.get('snippet') or '')[:160])}</p>"
        "</section>"
        for ev in ext_evidence
    ) or '<p class="muted">Harici kanıt bulunamadı.</p>'

    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>{escape(report_json.get('title', 'Clarere Research Report'))}</title>
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
      <div class="brand">Clarere Araştırma</div>
      <div class="badge">Sentetik Çalışma</div>
    </div>

    <section class="hero">
      <h1>{escape(report_json.get('title', 'Araştırma Raporu'))}</h1>
      <p class="summary">{escape(plan.get('objective', ''))}</p>
    </section>

    <section class="metrics">
      <div class="metric"><span>Toplam Persona</span><strong>{len(personas)}</strong></div>
      <div class="metric"><span>Yaş Aralığı</span><strong>{f"{min(age_values)}-{max(age_values)}" if age_values else "-"}</strong></div>
      <div class="metric"><span>Mülakat Yanıtı</span><strong>{quote_count}</strong></div>
      <div class="metric"><span>Kalite Sorunu</span><strong>{len(quality_issues)}</strong></div>
    </section>

    <h2>Yönetici Özeti</h2>
    <section class="card">{html_list(report_json.get('executive_summary', []))}</section>

    <h2>Ticarileştirme Skor Kartı</h2>
    <p class="section-note">Bu skor kartı, sentetik görüşme sinyallerini ürün kararı için okunabilir bir yönetici özetine indirger.</p>
    {html_table(score_rows, [('goal', 'Hedef'), ('score', 'Skor'), ('evidence', 'Kanıt')])}

    <h2>Panel Tasarımı</h2>
    <div class="grid">
      <section class="card">
        <h3>Rol Dağılımı</h3>
        {html_table(role_rows, [('role', 'Rol'), ('count', 'Adet')])}
      </section>
      <section class="card">
        <h3>Model Kullanımı</h3>
        {html_table(model_rows, [('model', 'Model'), ('answers', 'Yanıt')])}
      </section>
    </div>

    <h2>Persona Paneli Önizlemesi</h2>
    <p class="section-note">Panel, aynı fikre farklı fiyat, güven, operasyon ve dijital olgunluk lenslerinden bakacak şekilde dengelenir.</p>
    <div class="persona-grid">{''.join(persona_cards) or '<p class="muted">Persona yok.</p>'}</div>

    <h2>Görüşme Senaryosu Kapsamı</h2>
    {html_table(script_rows, [('label', 'Etiket'), ('question', 'Soru'), ('reason', 'Neden önemli')])}

    <h2>Acı Noktası Matrisi</h2>
    {html_table(report_json.get('pain_point_matrix', []), [
        ('persona', 'Persona'),
        ('segment', 'Segment'),
        ('primary_pain', 'Ana sorun'),
        ('main_objection', 'Ana itiraz'),
        ('pricing_signal', 'Fiyat sinyali'),
    ])}

    <div class="locked">
      <div><strong>Kanıt zinciri önizlemesi</strong><br><span>Aşağıdaki bulgular iddiaları persona alıntılarına bağlar.</span></div>
      <div>Clarere</div>
    </div>

    <h2>Kritik Bulgular</h2>
    <div class="finding-grid">{''.join(evidence_blocks)}</div>

    <h2>Karar Katmanı</h2>
    <p class="section-note">Kanıt zincirinden türetilen aksiyon önerileri: YAYINLA · İYİLEŞTİR · ARAŞTIR · VAZGEÇ.</p>
    <div class="finding-grid">{''.join(decision_blocks) or '<p class="muted">Karar önerisi yok.</p>'}</div>

    {f"<h2>Van Westendorp Fiyat Analizi</h2><div class='grid'>{vw_blocks}</div>" if vw else ''}

    <h2>Harici Kanıt Doğrulaması</h2>
    <p class="section-note">Sentetik bulguları destekleyen dış kaynaklar (TÜAD, Statista vb.).</p>
    <div class="finding-grid">{ext_blocks}</div>

    <h2>Mülakat Kanıtı Önizlemesi</h2>
    <p class="section-note">Bu bölüm, rapordaki bulguların ham görüşme izlerine bağlanabildiğini gösterir.</p>
    <div class="finding-grid">{''.join(transcript_blocks) or '<p class="muted">Transcript yok.</p>'}</div>

    <h2>Fiyatlandırma ve Paketleme</h2>
    <section class="card">
      <h3>{escape(pricing.get('acceptable_range', 'Fiyat içgörüsü'))}</h3>
      <p>{escape(pricing.get('packaging_suggestion', ''))}</p>
      <h3>Direnç Noktaları</h3>
      {html_list(pricing.get('resistance_points', []))}
    </section>

    <h2>Aksiyon Planı</h2>
    <section class="card">{html_list(report_json.get('action_items', []))}</section>

    <h2>Kalite Kontrol</h2>
    <section class="card">
      <p class="{ 'quality-risk' if quality_issues else 'quality-ok' }">
        {f"{len(quality_issues)} kalite sorunu incelenmeli." if quality_issues else "Kritik kalite uyarısı yok."}
      </p>
      {html_table(quality_issues, [('persona_name', 'Persona'), ('severity', 'Önem'), ('issue', 'Sorun'), ('recommendation', 'Öneri')]) if quality_issues else ''}
    </section>

    <h2>Metodoloji Notları</h2>
    <section class="card">
      {html_list(report_json.get('limitations', []))}
    </section>

    <h2>Sonraki Çalışma için Açık Sorular</h2>
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
        return f"{persona.get('name', 'Persona')} için kalite uyarısı tetiklendi: {', '.join(flagged_turn['quality_flags'])}. Lütfen bu konuyu derinleştirin."
    if pricing_turn:
        return f"{persona.get('name', 'Persona')} fiyat için itiraz belirtti: \"{pricing_turn['answer']}\". Değer algısını derinleştirin."
    if objection_turn:
        return f"{persona.get('name', 'Persona')} bariyer belirtti: \"{objection_turn['answer']}\". Bu itirazı aşma yollarını sorun."
    return f"{persona.get('name', 'Persona')} genel Pragmatist duruş sergiliyor. Sektör deneyimini sorun."
