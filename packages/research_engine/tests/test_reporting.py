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


def _enterprise_report() -> ResearchReport:
    """Karar katmanı + Van Westendorp + harici kanıt + enhanced findings içeren kurumsal rapor."""
    from packages.research_engine.models import (
        ClarifyingQuestion,
        DecisionItem,
        EnhancedFinding,
        ExternalEvidence,
        VanWestendorpInsight,
    )

    base = _minimal_report()
    ev = Evidence(
        persona_id="p1", persona_name="Ali", stance="Skeptic",
        quote="Çok pahalı", source_question="q1", sentiment="refuting",
    )
    ef = EnhancedFinding(
        title="Fiyat bariyeri", category="pricing", summary="Özet",
        confidence=0.72, evidence=[ev], implication="Etki",
        supporting_count=2, refuting_count=3, neutral_count=0,
        contradiction_score=0.4, decision_signal="INVESTIGATE",
    )
    di = DecisionItem(
        signal="INVESTIGATE", title="Fiyat bariyeri", confidence=0.72,
        supporting_count=2, refuting_count=3, evidence_summary="özet",
        recommended_action="Hedefli anket öner",
    )
    vw = VanWestendorpInsight(
        too_cheap_values=[100], cheap_values=[200],
        expensive_values=[400], too_expensive_values=[600],
        opp=300, ipp=250, pmc=150, pme=500, acceptable_range=(150, 500),
    )
    ee = ExternalEvidence(
        finding_title="Fiyat bariyeri", source_title="TÜAD 2025",
        source_url="http://x", snippet="Fiyat şeffaflığı önemli",
        relevance="high", confidence_boost=0.05,
    )
    return ResearchReport(
        title=base.title,
        executive_summary=base.executive_summary,
        plan=base.plan,
        personas=base.personas,
        interviews=base.interviews,
        findings=base.findings,
        pricing=base.pricing,
        pain_point_matrix=base.pain_point_matrix,
        action_items=base.action_items,
        quality_issues=base.quality_issues,
        recommendations=base.recommendations,
        validation_next_steps=base.validation_next_steps,
        limitations=base.limitations,
        model_usage=base.model_usage,
        enhanced_findings=[ef],
        decision_items=[di],
        van_westendorp=vw,
        external_evidence=[ee],
        research_quality={"rfi": 0.71, "warning_count": 1},
    )


def test_render_markdown_enterprise_sections():
    """Kurumsal bölümler: karar katmanı, PSM, harici kanıt, kanıt sayıları, RFI."""
    md = render_markdown(_enterprise_report())
    assert "Karar Katmanı" in md
    assert "Van Westendorp Fiyat Hassasiyet Analizi" in md
    assert "Harici Kanıt Doğrulaması" in md
    assert "72%" in md  # güven skoru yüzde olarak
    assert "71.0/100" in md  # RFI
    assert "ARAŞTIR" in md  # karar sinyali Türkçe
    assert "150 - 500 TL" in md  # PSM kabul aralığı
    assert "Destekleyen: **2**" in md  # kanıt sayıları
    assert "TÜAD 2025" in md  # harici kanıt


def test_render_report_html_turkish_headers():
    """HTML raporu tamamen Türkçe ve kurumsal bölümleri içerir."""
    from packages.research_engine.reporting import render_report_html
    report = _enterprise_report()
    import json
    from dataclasses import asdict
    html = render_report_html(asdict(report), render_markdown(report))
    assert "Yönetici Özeti" in html
    assert "Karar Katmanı" in html
    assert "Van Westendorp" in html
    assert "Harici Kanıt Doğrulaması" in html
    assert "Ticarileştirme Skor Kartı" in html
    assert "Total personas" not in html  # İngilizce kalıntı yok
    assert "Synthetic Study" not in html


def test_render_markdown_tolerates_dict_enhanced_findings():
    """Regresyon: `synthesize_report` enhanced_findings'i `asdict` ile dict yapar.

    render_markdown bu dict'lerde `.title` çağırdığı için
    `'dict' object has no attribute 'title'` ile çöküyordu → client tarafında
    fallback (yalnızca executive_summary) devreye giriyor ve rapor ~2 KB kalıyordu.
    """
    from dataclasses import asdict, replace

    report = _enterprise_report()
    assert report.enhanced_findings, "test raporunda enhanced_findings olmalı"

    dict_findings = [asdict(f) for f in report.enhanced_findings]
    report = replace(report, enhanced_findings=dict_findings)

    md = render_markdown(report)
    assert "Fiyat bariyeri" in md
    assert "Kanıtlar:" in md


def test_render_markdown_decision_summary_is_clean():
    """Karar özeti artık executive_summary'ye gömülü değil: ham HTML/boş madde olmamalı."""
    md = render_markdown(_enterprise_report())
    assert "Karar dağılımı:" in md
    assert "<span" not in md  # ham HTML span yok
    assert "\n- \n" not in md  # boş madde yok


def test_render_markdown_includes_narrative_section():
    """Zenginleştirme anlatımı net bir başlık altında gelmeli."""
    from dataclasses import replace

    report = replace(_enterprise_report(), executive_narrative="Örnek yönetici anlatımı metni.")
    md = render_markdown(report)
    assert "### Yönetici Anlatımı" in md
    assert "Örnek yönetici anlatımı metni." in md
    assert "Çok pahalı" in md
    assert "Destekleyen: **2**" in md
