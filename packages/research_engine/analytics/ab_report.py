"""A/B varyant simulasyonu raporu (refactor R7)."""
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


def synthesize_ab_report(
    brief: ResearchBrief,
    plan: ResearchPlan,
    personas: list[Persona],
    interviews: list[PersonaInterview],
    variant_preferences: dict[str, str] | None = None,
) -> ResearchReport | None:
    """A/B modunda rapor uretir; varyant yoksa None doner (standart yol devralir)."""
    if not (brief.variant_a and brief.variant_b):
        return None

    votes_a = 0
    votes_b = 0
    votes_undecided = 0

    pref_by_persona = {}
    ab_reasons: dict[str, list[str]] = {"A": [], "B": [], "Undecided": []}

    for interview in interviews:
        p_id = interview.persona.id
        pref = "Undecided"

        # Sprint 5 — Parse AB_MAP from consistency_notes
        ab_map_a_as_1 = True  # default: A = Seçenek 1
        for note in interview.consistency_notes:
            if note.startswith("AB_MAP:"):
                ab_map_a_as_1 = (note == "AB_MAP:A_AS_1")
                break

        if variant_preferences and p_id in variant_preferences:
            pref = variant_preferences[p_id]
        else:
            # auto-detect preference from interview answers
            for turn in interview.turns:
                q = turn.question
                ans = turn.answer.lower()
                # normalize Turkish c/c for robust matching
                q_norm = q.replace("ç", "c")
                ans_norm = ans.replace("ç", "c")

                # Sprint 5 — Blind labeling: Secenek 1 / Secenek 2
                if "Secenek 1" in q_norm and "Secenek 2" in q_norm:
                    if "secenek 1" in ans_norm and "secenek 2" not in ans_norm:
                        pref = "A" if ab_map_a_as_1 else "B"
                    elif "secenek 2" in ans_norm and "secenek 1" not in ans_norm:
                        pref = "B" if ab_map_a_as_1 else "A"
                    else:
                        pref = "Undecided"
                    if pref != "Undecided":
                        ab_reasons[pref].append(ans[:200])
                    break

                # Legacy detection: Varyant A / Varyant B
                if "Varyant A" in q and "Varyant B" in q:
                    has_a = "varyant a" in ans
                    has_b = "varyant b" in ans
                    if has_a and not has_b:
                        pref = "A"
                    elif has_b and not has_a:
                        pref = "B"
                    else:
                        pref = "Undecided"
                    if pref != "Undecided":
                        ab_reasons[pref].append(ans[:200])
                    break

        pref_by_persona[p_id] = pref
        if pref == "A":
            votes_a += 1
        elif pref == "B":
            votes_b += 1
        else:
            votes_undecided += 1

    total_votes = len(interviews) or 1
    pct_a = round(100 * votes_a / total_votes)
    pct_b = round(100 * votes_b / total_votes)
    pct_undecided = 100 - pct_a - pct_b

    winner = "Varyant A" if votes_a > votes_b else "Varyant B" if votes_b > votes_a else "Berabere / Kararsiz"

    # Sprint 5 — Segment-level A/B analysis
    # Stance breakdown
    stance_winners: dict[str, dict[str, int]] = {}
    # SES breakdown
    ses_winners: dict[str, dict[str, int]] = {}
    # Price sensitivity breakdown (high >= 7, low <= 3)
    price_winners: dict[str, dict[str, int]] = {"high_sensitivity": {"A": 0, "B": 0, "Undecided": 0}, "low_sensitivity": {"A": 0, "B": 0, "Undecided": 0}}

    for iv in interviews:
        p = iv.persona
        pref = pref_by_persona.get(p.id, "Undecided")

        # Stance
        stance = p.stance
        if stance not in stance_winners:
            stance_winners[stance] = {"A": 0, "B": 0, "Undecided": 0}
        stance_winners[stance][pref] += 1

        # SES
        ses = p.ses_group
        if ses not in ses_winners:
            ses_winners[ses] = {"A": 0, "B": 0, "Undecided": 0}
        ses_winners[ses][pref] += 1

        # Price sensitivity
        if p.price_sensitivity >= 7:
            price_winners["high_sensitivity"][pref] += 1
        elif p.price_sensitivity <= 3:
            price_winners["low_sensitivity"][pref] += 1

    # Build segment winner summaries
    def _seg_winner(counts: dict[str, int]) -> str:
        if counts["A"] > counts["B"]:
            return "A"
        elif counts["B"] > counts["A"]:
            return "B"
        return "Undecided"

    stance_lines = []
    for s in ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]:
        if s in stance_winners:
            c = stance_winners[s]
            sw = _seg_winner(c)
            var_name = brief.variant_a if sw == "A" else brief.variant_b if sw == "B" else "Kararsiz"
            stance_lines.append(f"{s}: {var_name} (A:{c['A']} B:{c['B']} U:{c['Undecided']})")

    ses_lines = []
    for ses in ["AB", "C1", "C2", "DE"]:
        if ses in ses_winners:
            c = ses_winners[ses]
            sw = _seg_winner(c)
            var_name = brief.variant_a if sw == "A" else brief.variant_b if sw == "B" else "Kararsiz"
            ses_lines.append(f"{ses}: {var_name}")

    # Price sensitivity segment
    ps_high = price_winners["high_sensitivity"]
    ps_low = price_winners["low_sensitivity"]
    ps_high_winner = _seg_winner(ps_high)
    ps_low_winner = _seg_winner(ps_low)
    ps_high_name = brief.variant_a if ps_high_winner == "A" else brief.variant_b if ps_high_winner == "B" else "Kararsiz"
    ps_low_name = brief.variant_a if ps_low_winner == "A" else brief.variant_b if ps_low_winner == "B" else "Kararsiz"

    # Confidence: weighted by vote margin
    margin = 0.0
    if total_votes > 0:
        margin = abs(votes_a - votes_b) / total_votes
        ab_confidence = round(0.5 + margin * 0.45, 2)  # 0.50 - 0.95 range
    else:
        ab_confidence = 0.50

    # Build reason summaries from collected evidence
    reasons_a = ab_reasons.get("A", [])
    reasons_b = ab_reasons.get("B", [])
    top_reason_a = _shorten(reasons_a[0], 160) if reasons_a else "Guven ve netlik odakli tercih."
    top_reason_b = _shorten(reasons_b[0], 160) if reasons_b else "Esneklik ve yenilik odakli tercih."

    # Recommendation
    if margin >= 0.4:
        recommendation = f"Net kazanan {winner}. Hemen bu varyantla ilerleyin."
    elif margin >= 0.2:
        recommendation = f"{winner} onde ama fark az. Kazanmayan varyantin sevilen ozelliklerini entegre edin."
    else:
        recommendation = "Yakin sonuc. Her iki varyantin guclu yonlerini birlestiren hibrit bir yaklasim dusunun."

    executive_summary = [
        f"A/B Simulasyonu sonucunda **{winner}** one cikmistir (guven: %{int(ab_confidence * 100)}).",
        f"Katilimcilarin %{pct_a}'si Varyant A'yi ('{_shorten(brief.variant_a, 60)}'), %{pct_b}'si Varyant B'yi ('{_shorten(brief.variant_b, 60)}') tercih etmistir. Kararsiz orani: %{pct_undecided}.",
        f"Oneri: {recommendation}",
        f"Stance kazananlari: {' | '.join(stance_lines) if stance_lines else 'Veri yetersiz.'}",
        f"SES kazananlari: {' | '.join(ses_lines) if ses_lines else 'Veri yetersiz.'}",
        f"Fiyat hassasiyeti: Yuksek hassasiyetli segment → {ps_high_name} | Dusuk hassasiyetli segment → {ps_low_name}",
    ]

    objection_evidence = collect_evidence(interviews, "objection")
    pricing_evidence = collect_evidence(interviews, "pricing")
    value_evidence = collect_evidence(interviews, "value")

    findings = [
        Finding(
            title=f"Kazanan Kurgu: {winner}",
            category="positioning",
            summary=(
                f"Yapilan sentetik mulakatlar dogrultusunda, {votes_a} persona Varyant A'yi, "
                f"{votes_b} persona Varyant B'yi secti. {votes_undecided} katilimci kararsiz kaldi. "
                f"Guven skoru: %{int(ab_confidence * 100)}. Oneri: {recommendation}"
            ),
            confidence=ab_confidence,
            evidence=value_evidence,
            implication=f"Pazarlama iletisiminde {winner} kurgusunun soylemleri birincil tercih olmalidir.",
        ),
        Finding(
            title="Varyant A Kurgusu Tercih Sebepleri",
            category="value",
            summary=(
                f"Varyant A ('{_shorten(brief.variant_a, 60)}'), ozellikle risk toleransi dusuk ve butce hassasiyeti yuksek segmentlerde "
                f"tercih ediliyor. Ornek sebep: '{top_reason_a}'"
            ),
            confidence=0.78,
            evidence=value_evidence,
            implication="Geleneksel pazarlama kanallarinda Varyant A'nin guven verici ve maliyet odakli mesajlari on planda olmalidir.",
        ),
        Finding(
            title="Varyant B Kurgusu Tercih Sebepleri",
            category="value",
            summary=(
                f"Varyant B ('{_shorten(brief.variant_b, 60)}'), esneklik ve yenilik arayan segmentler tarafindan tercih ediliyor. "
                f"Ornek sebep: '{top_reason_b}'"
            ),
            confidence=0.72,
            evidence=value_evidence,
            implication="Erken benimseyenler (Early Adopters) hedeflenirken Varyant B'nin argumanlari one cikarilabilir.",
        ),
        Finding(
            title="A/B Segment Analizi",
            category="positioning",
            summary=(
                f"Stance bazinda: {' | '.join(stance_lines) if stance_lines else 'Veri yetersiz.'} "
                f"SES bazinda: {' | '.join(ses_lines) if ses_lines else 'Veri yetersiz.'} "
                f"Fiyat hassasiyeti: Yuksek → {ps_high_name}, Dusuk → {ps_low_name}."
            ),
            confidence=0.80,
            evidence=value_evidence,
            implication="Segment bazinda farklilastirilmis mesaj stratejisi uygulayin.",
        ),
        Finding(
            title="A/B Ortak Itirazlar ve Riskler",
            category="risk",
            summary="Her iki varyantta da verilerin guvenligi, entegrasyon zorlugu ve operasyonel is yuku ortak cekinceler olarak one cikti.",
            confidence=0.90,
            evidence=objection_evidence,
            implication="Hangi varyant secilirse secilsin, iletisimde 'kurulum kolayligi' ve 'veri guvenligi' garantileri verilmelidir.",
        )
    ]

    pricing = PricingInsight(
        acceptable_range="Fiyatlama ikincil planda.",
        packaging_suggestion="Hangi varyant seçilirse seçilsin, test/deneme süresi sunularak bariyer düşürülmeli.",
        resistance_points=[
            "İlk kurulum maliyetleri",
            "Taahhüt süresi",
            "Beklenmeyen sürpriz ücretler"
        ]
    )

    report_dict_ab = {
        "personas": [asdict(p) for p in personas],
        "findings": [asdict(f) for f in findings],
        "executive_summary": executive_summary,
        "action_items": [
            f"{winner} kurgusu etrafında landing page revizyonu yapın.",
            "Karasız kitleyi dönüştürmek için somut vaka analizleri (Case Study) ekleyin.",
            "En güçlü itirazlara yanıt veren bir SSS (FAQ) bölümü hazırlayın."
        ],
        "recommendations": [
            "Önce küçük bir bütce ile Google/Meta reklamlarda bu iki varyanttı gerçek tıklamalarla (CTR) test edin.",
        ],
        "validation_next_steps": [
            "Kazanmayan varyanttı doğrudan çöpe atmak yerine, onun sevilen özelliklerini kazanan varyanta entegre edip edemeyeceğinizi inceleyin."
        ],
        "quality_issues": [],
    }
    adversarial_result = run_adversarial_review(report_dict_ab)

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
        title=f"A/B Simülasyonu: {brief.title}",
        plan=plan,
        personas=personas,
        interviews=interviews,
        model_usage=summarize_model_usage(interviews),
        quality_issues=collect_quality_issues(interviews),
        executive_summary=executive_summary,
        pain_point_matrix=build_pain_point_matrix(interviews),
        findings=findings,
        pricing=pricing,
        action_items=[
            f"{winner} kurgusu etrafinda landing page revizyonu yapın.",
            "Karasız kitleyi dönüştürmek için somut vaka analizleri (Case Study) ekleyin.",
            "En güçlü itirazlara yanıt veren bir SSS (FAQ) bölümü hazırlayın."
        ],
        recommendations=[
            "Önce küçük bir bütceyle Google/Meta reklamlarında bu iki varyanttı gerçek tıklamalarla (CTR) test edin.",
            "Varyant A'yı ana siteye, Varyant B'yi spesifik bir niş kampanyaya (örn. Product Hunt) ayırın."
        ],
        validation_next_steps=[
            "Kazanmayan varyanttı doğrudan çöpe atmak yerine, onun sevilen özelliklerini kazanan varyanta entegre edip edemeyeceğinizi inceleyin.",
            "En güçlü 2-3 bulgunu 5-8 gerçek kullanıcıyla kısa görüşme (15-20 dk) aracılığıyla doğrulayın.",
        ],
        limitations=[
            "Bu A/B testi, sentetik personalarin oylarıyla sınırlıdır. Canlı ortamdaki gerçek dönüşüm (conversion) oranları farklılık gösterebilir."
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
    )
