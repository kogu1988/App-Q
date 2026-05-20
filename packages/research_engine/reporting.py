from __future__ import annotations

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
