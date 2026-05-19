from __future__ import annotations

from .models import ResearchReport


def render_markdown(report: ResearchReport) -> str:
    lines: list[str] = [
        f"# {report.title}",
        "",
        "## Araştırma Planı",
        "",
        report.plan.objective,
        "",
        "### Varsayımlar",
        "",
    ]
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
                f"- Duruş: {persona.stance}",
                f"- Fiyat hassasiyeti: {persona.price_sensitivity}/10",
                f"- Dijital özgüven: {persona.digital_confidence}/10",
                f"- Bağlam: {persona.context}",
                f"- Bilgi sınırı: {persona.knowledge_boundary}",
                "",
            ]
        )

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

    lines.extend(["", "## Öneriler", ""])
    lines.extend(f"- {item}" for item in report.recommendations)

    lines.extend(["", "## Sonraki Doğrulama Adımları", ""])
    lines.extend(f"- {item}" for item in report.validation_next_steps)

    lines.extend(["", "## Sınırlılıklar", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    lines.append("")

    return "\n".join(lines)
