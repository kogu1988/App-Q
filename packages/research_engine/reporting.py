from __future__ import annotations

from html import escape
from .models import ResearchReport


def render_markdown(report: ResearchReport) -> str:
    lines: list[str] = [
        f"# {report.title}",
        "",
        "## Model Kullanımı",
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
    lines.extend(
        f"- **{question.priority.upper()}**: {question.question} _({question.reason})_"
        for question in report.plan.clarifying_questions
    )

    lines.extend(["", "### Görüşme Script'i", ""])
    for index, question in enumerate(report.plan.interview_script, start=1):
        lines.extend(
            [
                f"{index}. **{question.label}** - {question.question}",
                f"   - Amaç: {question.reason}",
                f"   - Etiketler: {', '.join(question.tags) if question.tags else 'risk'}",
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
                f"- Duruş: {persona.stance}",
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
            lines.extend(f"- {key}: {value}" for key, value in persona.attributes.items())
            lines.append("")
        if persona.traits:
            lines.extend(["Kişilik skorları:"])
            lines.extend(f"- {key}: {value}/100" for key, value in persona.traits.items())
            lines.append("")

    lines.extend(["## Pain Point Matrisi", ""])
    lines.extend(
        [
            "| Persona | Segment | Ana Pain Point | Ana İtiraz | Fiyat Sinyali |",
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
    for finding in report.findings:
        lines.extend(
            [
                f"### {finding.title}",
                "",
                f"- Kategori: {finding.category}",
                f"- Güven skoru: {finding.confidence:.2f}",
                f"- Özet: {finding.summary}",
                f"- Etki: {finding.implication}",
                "",
                "Kanıtlar:",
            ]
        )
        for evidence in finding.evidence:
            lines.append(
                f"- {evidence.persona_name} ({evidence.stance}) - \"{evidence.quote}\""
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

    lines.extend(["", "## Aksiyon Listesi", ""])
    lines.extend(f"- {item}" for item in report.action_items)

    lines.extend(["", "## Kalite Kontrol", ""])
    if report.quality_issues:
        for issue in report.quality_issues:
            lines.append(
                f"- **{issue.severity.upper()}** {issue.persona_name}: {issue.issue} "
                f"Öneri: {issue.recommendation}"
            )
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
      <div class="brand">Clarere Research</div>
      <div class="badge">Synthetic Study</div>
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
      <div>Clarere</div>
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
        return f"{persona.get('name', 'Persona')} için kalite uyarısı tetiklendi: {', '.join(flagged_turn['quality_flags'])}. Lütfen bu konuyu derinleştirin."
    if pricing_turn:
        return f"{persona.get('name', 'Persona')} fiyat için itiraz belirtti: \"{pricing_turn['answer']}\". Değer algısını derinleştirin."
    if objection_turn:
        return f"{persona.get('name', 'Persona')} bariyer belirtti: \"{objection_turn['answer']}\". Bu itirazı aşma yollarını sorun."
    return f"{persona.get('name', 'Persona')} genel Pragmatist duruş sergiliyor. Sektör deneyimini sorun."
