"""Test: render_markdown tam rapor üretir (PDF/HTML export kaynağı)."""
from packages.research_engine.models import (
    Evidence,
    Finding,
    Persona,
    PricingInsight,
    ResearchPlan,
    ResearchReport,
)
from packages.research_engine.reporting import render_markdown


def _minimal_report() -> ResearchReport:
    plan = ResearchPlan(
        objective="Test hedefi",
        assumptions=["Varsayım1"],
        clarifying_questions=[],
        interview_questions=["Soru1"],
        recommended_panel_size=1,
        interview_script=[],
        ses_quota={},
    )
    persona = Persona(
        id="p1",
        name="Ali",
        age=30,
        city="İstanbul",
        segment="Genel",
        stance="Mainstream",
        price_sensitivity=5,
        digital_confidence=6,
        context="",
        goals=[],
        objections=[],
        knowledge_boundary="",
    )
    evidence = Evidence(
        persona_id="p1",
        persona_name="Ali",
        stance="Mainstream",
        quote="Güzel ürün",
        source_question="q1",
    )
    finding = Finding(
        title="Fiyat hassasiyeti",
        category="pain_point",
        summary="Özet",
        confidence=0.8,
        evidence=[evidence],
        implication="Etki",
    )
    pricing = PricingInsight(
        acceptable_range="100-200 TL",
        resistance_points=["Fiyat"],
        packaging_suggestion="Aylık",
    )
    return ResearchReport(
        title="Test Raporu",
        executive_summary=["Özet1"],
        plan=plan,
        personas=[persona],
        interviews=[],
        findings=[finding],
        pricing=pricing,
        pain_point_matrix=[],
        action_items=["Aksiyon1"],
        quality_issues=[],
        recommendations=["Öneri1"],
        validation_next_steps=[],
        limitations=["Limit1"],
        model_usage={"deepseek-v4-flash": 5},
    )


def test_render_markdown_contains_full_report_sections():
    """Tam rapor; yalnızca yönetici özeti DEĞİL — tüm bölümler mevcut."""
    md = render_markdown(_minimal_report())
    assert "Test Raporu" in md
    assert "Yönetici Özeti" in md
    assert "Bulgular" in md
    assert "Fiyat hassasiyeti" in md
    assert "Fiyat İçgörüsü" in md
    assert "Aksiyon Listesi" in md
    assert "Öneriler" in md
    assert "Sınırlılıklar" in md


def test_render_markdown_includes_evidence_quote():
    md = render_markdown(_minimal_report())
    assert "Güzel ürün" in md
    assert "Ali" in md
