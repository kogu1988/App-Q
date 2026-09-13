"""synthesize_report orkestrasyonu (R7-7)."""
from __future__ import annotations

import json
import logging
import re
import statistics
from dataclasses import asdict
from typing import Any

logger = logging.getLogger(__name__)

from ..adversarial import run_adversarial_review
from ..models import (
    DecisionItem,
    DecisionSignal,
    EnhancedFinding,
    Evidence,
    ExternalEvidence,
    Finding,
    Persona,
    PersonaInterview,
    PricingInsight,
    QualityIssue,
    ResearchBrief,
    ResearchPlan,
    ResearchReport,
    VanWestendorpInsight,
)
from .ab_report import synthesize_ab_report
from .corroboration import corroborate_findings
from .enrichment import _shorten
from .evidence import build_evidence_graph, generate_decision_summary
from .findings import (
    build_brand_health_summary,
    build_channel_map,
    build_pain_point_matrix,
    build_respondent_type_summary,
    build_ses_cross_tab,
    collect_evidence,
)
from .metrics import build_report_metrics, collect_quality_issues, summarize_model_usage
from .pricing import van_westendorp_analysis


def synthesize_report(
    brief: ResearchBrief,
    plan: ResearchPlan,
    personas: list[Persona],
    interviews: list[PersonaInterview],
    variant_preferences: dict[str, str] | None = None,
) -> ResearchReport:
    ab_report = synthesize_ab_report(brief, plan, personas, interviews, variant_preferences)
    if ab_report is not None:
        return ab_report

    # Standart Pazar Araştırması Modu (Orijinal)
    pain_points = collect_evidence(interviews, "pain_point")
    objections = collect_evidence(interviews, "objection")
    pricing_evidence = collect_evidence(interviews, "pricing")

    if pain_points:
        summary_pain = f"Katılımcılar şu anda bu problemi çözerken yoğun olarak zaman/efor kaybı yaşıyor. Örnek: '{pain_points[0].quote}'"
    else:
        summary_pain = "Hedef kitlede bu problemle ilgili aciliyet tespit edilemedi."

    objection_hint = (
        f"En güçlü bariyer güven/KVKK ve entegrasyon endişesi: \"{_shorten(objections[0].quote, 140)}\""
        if objections and objections[0].quote
        else "Belirgin bir satın alma bariyeri öne çıkmadı."
    )
    price_hint = (
        f"Fiyat beklentisi orta seviyede kümeleniyor: \"{_shorten(pricing_evidence[0].quote, 140)}\""
        if pricing_evidence and pricing_evidence[0].quote
        else "Fiyat beklentisi konusunda net bir sinyal toplanamadı."
    )

    executive_summary = [
        f"{brief.title} fikrinin hedef kitle nezdindeki pazar karşılığı incelendi.",
        summary_pain,
        objection_hint,
        price_hint,
    ]

    # R14 — Dinamik finding üretimi: mülakat verisinden kanıt bazlı bulgular
    # Sabit 2 boilerplate yerine gerçek veriden üretilir
    findings: list[Finding] = []

    # Finding 1: Pain point (varsa)
    if pain_points:
        top_quote = _shorten(pain_points[0].quote, 160)
        findings.append(Finding(
            title="Temel İhtiyaç ve Acı Noktası",
            category="pain_point",
            summary=(
                f"Katılımcıların büyük bölümü mevcut çözümlerde ciddi sürtüşme noktaları bildirdi. "
                f"Öne çıkan alıntı: \"{top_quote}\""
            ),
            confidence=min(0.5 + len(pain_points) * 0.07, 0.95),
            evidence=pain_points,
            implication="Ürünün değer önerisinde 'hız', 'birleştirme' veya 'basitleştirme' argümanları öne çıkarılmalı.",
        ))

    # Finding 2: Objections / satın alma bariyerleri (varsa)
    if objections:
        top_obj = _shorten(objections[0].quote, 160)
        findings.append(Finding(
            title="Satın Alma Bariyerleri ve İtirazlar",
            category="risk",
            summary=(
                f"{len(objections)} persona itiraz içeren sinyal verdi. "
                f"Öne çıkan itiraz: \"{top_obj}\""
            ),
            confidence=min(0.55 + len(objections) * 0.06, 0.92),
            evidence=objections,
            implication="Ana sayfa ve satış iletişiminde güven vurgusu, şeffaf fiyatlama ve KVKK uyumu belirtilmeli.",
        ))

    # Finding 3: Değer algısı (varsa)
    value_evidence = collect_evidence(interviews, "value")
    if value_evidence:
        top_val = _shorten(value_evidence[0].quote, 160)
        findings.append(Finding(
            title="Değer Algısı ve Fiyat Toleransı",
            category="value",
            summary=(
                f"Değer vurgusu yapan personalar fiyat bariyer eşiğini daha yüksek tuttu. "
                f"Örnek: \"{top_val}\""
            ),
            confidence=min(0.60 + len(value_evidence) * 0.05, 0.90),
            evidence=value_evidence,
            implication="Ürünün değer önerisini somutlaştırmak fiyat direncini azaltır.",
        ))

    # Finding 4: Positioning / farkındalık (varsa)
    pos_evidence = collect_evidence(interviews, "positioning")
    if pos_evidence:
        findings.append(Finding(
            title="Pazar Konumlandırma Sinyalleri",
            category="positioning",
            summary=(
                f"{len(pos_evidence)} persona konumlandırma sorusuna anlamlı yanıt verdi. "
                "Rakiplerden ayrışma fırsatı belirlendi."
            ),
            confidence=min(0.55 + len(pos_evidence) * 0.05, 0.88),
            evidence=pos_evidence,
            implication="Rakip farklılaşması mesajı, özellikle Öncü ve Erken Benimseyen segmentlerinde güçlü etki yaratır.",
        ))

    # Veri yoksa minimum fallback (golden master uyumlu)
    if not findings:
        findings = [
            Finding(
                title="Pazar Tepkisi — Veri Yetersiz",
                category="pain_point",
                summary="Mülakat verisinden yeterli sinyal çıkarılamadı. Daha geniş persona paneli önerilir.",
                confidence=0.40,
                evidence=[],
                implication="Panel büyüklüğünü artırarak veya soruları yeniden yapılandırarak araştırmayı tekrarlayın.",
            )
        ]

    _resistance = ["Peşin yıllık ödeme istenmesi", "Ekstra gizli ücretler", "Kurulum maliyeti"]
    if objections and objections[0].quote:
        _resistance.insert(0, f"Güven/KVKK ve klinik entegrasyonu endişesi (örn: \"{_shorten(objections[0].quote, 100)}\")")

    pricing = PricingInsight(
        acceptable_range=brief.expected_price or "Aylık 200-500 TL (Tahmini)",
        packaging_suggestion=(
            "Ücretsiz planı kısıtlı, ücretli planı cazip tutan freemium yapı korunmalı; "
            "deneme sürümü ve aylık ödeme seçeneği satın alma bariyerini düşürür."
        ),
        resistance_points=_resistance,
    )

    # Sprint 3 — Bulgulara dayalı, şablondan bağımsız öneriler (kategori sızıntısını önler)
    top_findings = sorted(findings, key=lambda f: f.confidence, reverse=True)[:3]
    derived_recommendations = [
        f"\u201c{f.title}\u201d bulgusunu ger\u00e7ek kullan\u0131c\u0131 g\u00f6r\u00fc\u015fmelerinde \u00f6ncelikli do\u011frulay\u0131n."
        for f in top_findings
    ] or [
        "Bu sentetik raporun en g\u00fc\u00e7l\u00fc bulgular\u0131n\u0131 5-8 ger\u00e7ek kullan\u0131c\u0131yla k\u0131sa g\u00f6r\u00fc\u015fmelerle do\u011frulay\u0131n."
    ]
    derived_recommendations.append(
        "Y\u00fcksek \u00e7eli\u015fki skorlu bulgular\u0131 segment baz\u0131nda ay\u0131r\u0131p hedef kitleyi daralt\u0131n."
    )
    derived_action_items = [
        "En y\u00fcksek g\u00fcvenli bulguyu MVP kapsam\u0131na al\u0131n.",
        "En g\u00fc\u00e7l\u00fc itiraz\u0131 azaltacak kan\u0131t veya demo ak\u0131\u015f\u0131n\u0131 haz\u0131rlay\u0131n.",
    ]
    derived_validation_steps = [
        "Fiyat modelini ger\u00e7ek bir landing page \u00fc\u00e7zerinde A/B testine sokun.",
        "En g\u00fc\u00e7l\u00fc 2-3 bulguyu 5-8 ger\u00e7ek kullan\u0131c\u0131yla k\u0131sa g\u00f6r\u00fc\u015fme (15-20 dk) arac\u0131l\u0131\u011f\u0131yla do\u011frulay\u0131n.",
    ]

    report_dict_std = {
        "personas": [asdict(p) for p in personas],
        "findings": [asdict(f) for f in findings],
        "executive_summary": executive_summary,
        "action_items": derived_action_items,
        "recommendations": derived_recommendations,
        "validation_next_steps": derived_validation_steps,
        "quality_issues": [],
    }
    adversarial_result = run_adversarial_review(report_dict_std)

    # Sprint 1 — Kanıt zinciri oluştur
    enhanced = build_evidence_graph(interviews, findings)

    # Sprint 7 — Karar katmanı
    decision_items = generate_decision_summary(enhanced)

    # Sprint 6 — Web doğrulama (dış kanıt)
    degradation_notes: list[str] = []
    external_evidence = corroborate_findings(
        findings, brief.title, brief.category, degradation_notes=degradation_notes
    )

    return ResearchReport(
        title=f"Araştırma Raporu: {brief.title}",
        plan=plan,
        personas=personas,
        interviews=interviews,
        model_usage=summarize_model_usage(interviews),
        quality_issues=collect_quality_issues(interviews),
        executive_summary=executive_summary,
        pain_point_matrix=build_pain_point_matrix(interviews),
        findings=findings,
        pricing=pricing,
        action_items=derived_action_items,
        recommendations=derived_recommendations,
        validation_next_steps=derived_validation_steps,
        limitations=[
            "Sentetik veriler gerçek pazar davranışını tam olarak yansıtmaz; yönlendirici hipotez olarak ele alınmalıdır.",
            "Bu çıktı istatistiksel temsil iddiası taşımaz.",
        ],
        ses_cross_tab=build_ses_cross_tab(interviews),
        respondent_type_summary=build_respondent_type_summary(interviews),
        van_westendorp=van_westendorp_analysis(brief, interviews),
        brand_health=build_brand_health_summary(interviews, brief.competitors),
        channel_map=build_channel_map(interviews),
        research_quality=adversarial_result,
        enhanced_findings=[asdict(e) for e in enhanced],
        external_evidence=external_evidence,
        decision_items=decision_items,
        degradation_notes=degradation_notes,
        report_metrics=build_report_metrics(
            interviews, findings, enhanced, external_evidence, decision_items
        ),
    )
