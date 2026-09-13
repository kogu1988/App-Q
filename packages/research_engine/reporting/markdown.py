"""Markdown rapor render'i (R7-9)."""
from __future__ import annotations

import re
from html import escape

from ..models import ResearchReport

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

def _clip(text: str | None, limit: int = 160) -> str:
    """Tam cümlelerden özet çıkarır; sonuna '...'/'…' EKLEMEZ.

    Limite sığan tam cümleler birleştirilir; tek cümle bile uzunsa kelime
    sınırında kırpılır.
    """
    if not text:
        return ""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    excerpt = ""
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        candidate = f"{excerpt} {sentence}".strip()
        if len(candidate) <= limit:
            excerpt = candidate
        else:
            break
    if excerpt:
        return excerpt
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:!?-")

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

_SIGNAL_TR = {
    "SHIP": "✅ YAYINLA",
    "ITERATE": "🔁 İYİLEŞTİR",
    "INVESTIGATE": "🔍 ARAŞTIR",
    "KILL": "⛔ VAZGEÇ",
}


def _g(obj, key, default=None):
    """dict VEYA nesne üzerinden güvenli alan erişimi.

    `synthesize_report` bazı alanları (`enhanced_findings`) `asdict` ile dict'e
    çeviriyor; `render_markdown` ise nesne bekliyordu → AttributeError → rapor
    fallback'e düşüyordu. Bu yardımcı iki biçimi de destekler.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


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
    lines.extend(f"- {item}" for item in report.executive_summary if str(item).strip())
    # DeepSeek Pro ile üretilen kanıta bağlı anlatım (varsa)
    if getattr(report, "executive_narrative", ""):
        lines.extend(["", "### Yönetici Anlatımı", "", report.executive_narrative])

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
            lines.extend(["", "**Davranış alanları:**", ""])
            lines.extend(f"- {_ATTR_TR.get(key, key)}: {value}" for key, value in persona.attributes.items())
            lines.append("")
        if persona.traits:
            lines.extend(["", "**Kişilik skorları:**", ""])
            lines.extend(f"- {_TRAIT_TR.get(key, key)}: {value}/100" for key, value in persona.traits.items())
            lines.append("")

    lines.extend(["", "## Pain Point Matrisi", ""])
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

    lines.extend(["", "## Bulgular", ""])
    # Enhanced findings varsa onları kullan (kanıt sayıları + karar sinyali ile)
    _source_findings = getattr(report, "enhanced_findings", None) or report.findings
    for finding in _source_findings:
        f_title = _g(finding, "title", "")
        f_category = _g(finding, "category", "")
        f_confidence = _g(finding, "confidence", 0.0) or 0.0
        f_summary = _g(finding, "summary", "")
        f_implication = _g(finding, "implication", "")
        lines.extend(
            [
                f"### {f_title}",
                "",
                f"- Kategori: {_CATEGORY_TR.get(f_category, f_category)}",
                f"- Güven skoru: **{int(f_confidence * 100)}%**",
                f"- Özet: {f_summary}",
                f"- Etki: {f_implication}",
                "",
            ]
        )
        # Enhanced finding alanları (varsa)
        supporting = _g(finding, "supporting_count")
        refuting = _g(finding, "refuting_count")
        signal = _g(finding, "decision_signal")
        if supporting is not None:
            lines.append(
                f"- Destekleyen: **{supporting}** persona | Karşı çıkan: **{refuting or 0}** persona"
            )
        if signal:
            lines.append(f"- Karar sinyali: **{_SIGNAL_TR.get(signal, signal)}**")
        lines.append("")
        lines.append("Kanıtlar:")
        for evidence in (_g(finding, "evidence", []) or []):
            e_persona = _g(evidence, "persona_name", "")
            e_stance = _g(evidence, "stance", "")
            e_quote = _g(evidence, "quote", "")
            lines.append(
                f"- {e_persona} ({_STANCE_TR.get(e_stance, e_stance)}) - \"{_clip(e_quote, 220)}\""
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
                "- **Uyarı:** Bu fiyat aralığı sentetik persona sinyallerine dayanır; istatistiksel temsil iddiası taşımaz. Gerçek fiyat kararı için gerçek kullanıcı/satış verisi gerekir.",
            ]
        )

    # ── Karar Katmanı (varsa) ──
    if getattr(report, "decision_items", None):
        lines.extend(["", "## Karar Katmanı", ""])
        _sig_counts: dict[str, int] = {}
        for d in report.decision_items:
            _sig_counts[d.signal] = _sig_counts.get(d.signal, 0) + 1
        lines.append(
            "- Karar dağılımı: "
            + " · ".join(
                f"{_SIGNAL_TR.get(sig, sig)} ({_sig_counts.get(sig, 0)})"
                for sig in ("SHIP", "ITERATE", "INVESTIGATE", "KILL")
            )
        )
        for d in report.decision_items:
            lines.extend(
                [
                    "",
                    f"### [{_SIGNAL_TR.get(d.signal, d.signal)}] {d.title}",
                    "",
                    f"- Güven: {int(d.confidence * 100)}% | Destek: {d.supporting_count} | Karşı: {d.refuting_count}",
                    f"- Kanıt: {d.evidence_summary}",
                    f"- Önerilen aksiyon: {d.recommended_action}",
                ]
            )

    # ── Harici Kanıtlar (varsa) ──
    if getattr(report, "external_evidence", None):
        lines.extend(["", "## Harici Kanıt Doğrulaması", ""])
        lines.append("Sentetik bulguları destekleyen dış kaynaklar:")
        for ev in report.external_evidence:
            _rel = {"high": "Yüksek", "medium": "Orta", "low": "Düşük"}.get(ev.relevance, ev.relevance)
            lines.append(f"- **{ev.source_title}** (İlgi: {_rel})")
            if ev.snippet:
                lines.append(f"  - {_clip(ev.snippet, 160)}")

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

    # DeepSeek Pro ile üretilen stratejik öneriler (varsa)
    if getattr(report, "strategic_recommendations", None):
        lines.extend(["", "## Stratejik Öneriler", ""])
        lines.extend(f"- {item}" for item in report.strategic_recommendations)

    lines.extend(["", "## Aksiyon Listesi", ""])
    lines.extend(f"- {item}" for item in report.action_items)

    if getattr(report, "degradation_notes", None):
        lines.extend(["", "## Metodolojik Uyarılar", ""])
        lines.extend(f"- {item}" for item in report.degradation_notes)

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

    # ── Sprint 3: Rapor metrikleri ve veri kökeni etiketleri ──
    _rm = report.report_metrics or {}
    if _rm:
        lines.extend(["", "## Rapor Metrikleri", ""])
        lines.append(
            f"- Bulgu: {_rm.get('findings_total', 0)} · Kanıtlı bulgu: {_rm.get('findings_with_evidence', 0)} · "
            f"Kaynaksız bulgu: {_rm.get('unsourced_findings', 0)}"
        )
        lines.append(
            f"- Bulgu başına ortalama kanıt: {_rm.get('evidence_per_finding', 0)} · "
            f"Kanıtta benzersiz persona: {_rm.get('unique_personas_in_evidence', 0)}"
        )
        lines.append(
            f"- Karşı kanıt oranı: {_rm.get('refuting_ratio', 0)} · "
            f"Yanıt tamamlanma oranı: {_rm.get('answer_completion_rate', 0)}"
        )
        lines.append(f"- Harici kanıt kaynağı: {_rm.get('external_evidence_count', 0)}")

        lines.extend(["", "### Veri Kökeni", ""])
        lines.append("- **Sentetik:** Persona mülakatlarından türeyen bulgular, alıntılar ve karşı kanıtlar (kanıt zinciri).")
        lines.append("- **Algoritmik:** Van Westendorp PSM, SES × Stance tablosu, kalite ve bütünlük metrikleri.")
        lines.append("- **Harici:** Web aramasından gelen doğrulama kaynakları (yoksa dış doğrulama yapılmamıştır).")
        lines.append("- **Not:** Sentetik ve algoritmik çıktılar yönlendirici hipotezdir; istatistiksel temsil iddiası taşımaz.")

    lines.extend(["", "## Sınırlılıklar", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    lines.append("")

    return "\n".join(lines)



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
