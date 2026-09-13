"""HTML rapor render'i (R7-9)."""
from __future__ import annotations

import re
from html import escape

from ..models import ResearchReport

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
from ._html_utils import count_by, html_list, html_table
from .markdown import _clip, _g


def render_report_html(report_json: dict, report_markdown: str) -> str:
    plan = report_json.get("plan", {})
    personas = report_json.get("personas", [])
    interviews = report_json.get("interviews", [])
    findings = report_json.get("findings", [])
    pricing = report_json.get("pricing", {})
    quality_issues = report_json.get("quality_issues", [])
    model_usage = report_json.get("model_usage", {})

    # DeepSeek Pro zenginleştirmesi (varsa) için HTML blokları — üst düzey f-string
    # içinde iç içe f-string kullanmamak adına önceden hazırlanır.
    _narrative = report_json.get("executive_narrative") or ""
    _strategic = report_json.get("strategic_recommendations") or []
    narrative_block = f'<section class="card">{escape(_narrative)}</section>' if _narrative else ""
    strategic_block = (
        '<h2>Stratejik Öneriler</h2><section class="card">' + html_list(_strategic) + "</section>"
    ) if _strategic else ""
    _degradations = report_json.get("degradation_notes") or []
    degradation_block = (
        '<h2>Metodolojik Uyarılar</h2><section class="card">' + html_list(_degradations) + "</section>"
    ) if _degradations else ""
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
            "<p class='muted'>Bu aralık sentetik persona sinyallerine dayanır; istatistiksel temsil iddiası taşımaz ve gerçek fiyat kararı için gerçek kullanıcı verisiyle doğrulanmalıdır.</p>"
            "</section>"
        )

    ext_evidence = report_json.get("external_evidence", [])
    ext_blocks = "".join(
        "<section class='card'>"
        f"<h3>{escape(ev.get('source_title', ''))}</h3>"
        f"<p class='muted'>{escape(str(ev.get('relevance', '')))} ilgi · {escape(ev.get('finding_title', ''))}</p>"
        f"<p>{escape(_clip(ev.get('snippet'), 160))}</p>"
        "</section>"
        for ev in ext_evidence
    ) or '<p class="muted">Harici kanıt bulunamadı.</p>'

    # Sprint 3 — Rapor metrikleri + veri kökeni
    _rm = report_json.get("report_metrics", {}) or {}
    metrics_block = ""
    if _rm:
        metrics_block = (
            "<section class='card'>"
            "<h3>Rapor Metrikleri</h3>"
            f"<p>Bulgu: <strong>{escape(str(_rm.get('findings_total', 0)))}</strong> · "
            f"Kanıtlı bulgu: <strong>{escape(str(_rm.get('findings_with_evidence', 0)))}</strong> · "
            f"Kaynaksız bulgu: <strong>{escape(str(_rm.get('unsourced_findings', 0)))}</strong></p>"
            f"<p>Bulgu başına ortalama kanıt: <strong>{escape(str(_rm.get('evidence_per_finding', 0)))}</strong> · "
            f"Kanıtta benzersiz persona: <strong>{escape(str(_rm.get('unique_personas_in_evidence', 0)))}</strong></p>"
            f"<p>Karşı kanıt oranı: <strong>{escape(str(_rm.get('refuting_ratio', 0)))}</strong> · "
            f"Yanıt tamamlanma oranı: <strong>{escape(str(_rm.get('answer_completion_rate', 0)))}</strong> · "
            f"Harici kaynak: <strong>{escape(str(_rm.get('external_evidence_count', 0)))}</strong></p>"
            "<p class='muted'><strong>Veri kökeni:</strong> Sentetik = persona mülakatları; "
            "Algoritmik = PSM/SES tabloları ve kalite metrikleri; Harici = web doğrulama kaynakları. "
            "Sentetik ve algoritmik çıktılar yönlendirici hipotezdir; istatistiksel temsil iddiası taşımaz.</p>"
            "</section>"
        )

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
    {narrative_block}
    {strategic_block}
    {degradation_block}

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
    <p class="section-note">Sentetik bulguları destekleyen, harici aramadan gelen gerçek kaynaklar.</p>
    <div class="finding-grid">{ext_blocks}</div>

    <h2>Rapor Metrikleri ve Veri Kökeni</h2>
    {metrics_block or '<p class="muted">Metrik bulunmuyor.</p>'}

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


