from __future__ import annotations
import difflib


# ── Bias Detection — Sabit Kelime Listeleri ──────────────────────────────────

# Acquiescence (uzlaşmacılık) sinyalleri — Skeptic/Blocker'dan beklenmez
ACQUIESCENCE_KEYWORDS = [
    "evet", "kesinlikle", "harika", "mükemmel", "tabii", "elbette",
    "güzel", "katılıyorum", "olur", "tamam", "doğru", "anlıyorum",
    "çok iyi", "süper", "mantıklı", "uygun", "fena değil",
]

# Social desirability (sosyal beğeni etkisi) klişe ifadeler
SOCIAL_DESIRABILITY_PHRASES = [
    "çok mantıklı", "kesinlikle evet", "tabii ki", "elbette evet",
    "çok iyi fikir", "harika bir fikir", "muhteşem", "bayıldım",
    "tam ihtiyacım olan", "bunu bekliyordum", "mükemmel çözüm",
]

# Negatif / itirazlı kelimeler — bunlar az olursa social desirability riski
NEGATIVE_SIGNALS = [
    "hayır", "olmaz", "şüphe", "riskli", "endişe", "güvensiz",
    "pahalı", "mantıksız", "inanmıyorum", "abartı", "sorun",
    "dezavantaj", "eksik", "yetersiz", "tehlike", "sakıncalı",
]


def detect_straight_lining(answers: list[str]) -> bool:
    """
    Ardışık cevaplar arasında yüksek metin benzerliği varsa True döner.
    Eşik: herhangi 2 ardışık cevap arasında SequenceMatcher ratio >= 0.58
    ve ortalama ratio >= 0.45 (genel tekdüzelik göstergesi).
    """
    if len(answers) < 3:
        return False

    ratios: list[float] = []
    for i in range(len(answers) - 1):
        a, b = answers[i].lower()[:300], answers[i + 1].lower()[:300]
        ratio = difflib.SequenceMatcher(None, a, b).ratio()
        ratios.append(ratio)

    high_sim_count = sum(1 for r in ratios if r >= 0.58)
    avg_ratio = sum(ratios) / len(ratios)

    return high_sim_count >= 2 or avg_ratio >= 0.45


def detect_acquiescence(stance: str, answers: list[str]) -> bool:
    """
    Skeptic veya Blocker stance'li personada yüksek olumlu kelime yoğunluğu varsa True.
    Eşik: cevap başına ortalama ≥ 2.5 acquiescence anahtar kelimesi
    ve negatif sinyal / kelime oranı < 0.02.
    """
    if stance not in {"Skeptic", "Blocker"}:
        return False

    all_text = " ".join(answers).lower()
    words = all_text.split()
    if not words:
        return False

    acq_count = sum(1 for kw in ACQUIESCENCE_KEYWORDS if kw in all_text)
    neg_count = sum(1 for ns in NEGATIVE_SIGNALS if ns in all_text)
    acq_per_answer = acq_count / max(len(answers), 1)
    neg_density = neg_count / max(len(words), 1)

    return acq_per_answer >= 2.5 and neg_density < 0.02


def detect_social_desirability(answers: list[str]) -> bool:
    """
    Sosyal onay arayan klişe ifadelerin sıklığı yüksekse True.
    Eşik: ≥ 3 farklı social desirability ifadesi VE negatif sinyal oranı < 0.015.
    """
    all_text = " ".join(answers).lower()
    words = all_text.split()
    if not words:
        return False

    phrase_count = sum(1 for p in SOCIAL_DESIRABILITY_PHRASES if p in all_text)
    neg_count = sum(1 for ns in NEGATIVE_SIGNALS if ns in all_text)
    neg_density = neg_count / max(len(words), 1)

    return phrase_count >= 3 and neg_density < 0.015


def detect_bias_flags(interviews: list[dict]) -> dict[str, list[str]]:
    """
    Her persona için yanıt sapması bayraklarını tespit eder.
    Döner: {persona_id: [flag1, flag2, ...]}
    """
    results: dict[str, list[str]] = {}

    for iv in interviews:
        persona = iv.get("persona", {}) if isinstance(iv, dict) else {}
        persona_id = persona.get("id", "unknown")
        stance = persona.get("stance", "Mainstream")
        turns = iv.get("turns", []) if isinstance(iv, dict) else []

        answers = [t.get("answer", "") for t in turns if isinstance(t, dict)]
        flags: list[str] = []

        if detect_straight_lining(answers):
            flags.append("straight_lining")
        if detect_acquiescence(stance, answers):
            flags.append("acquiescence_bias")
        if detect_social_desirability(answers):
            flags.append("social_desirability")

        if flags:
            results[persona_id] = flags

    return results


def calculate_turn_quality(flags: list[str]) -> float:
    """Tek bir turun kalitesini (0.0 - 1.0 arası) bayraklara göre hesaplar."""
    score = 1.0
    for flag in flags:
        if flag in {"meta_tone", "visible_reasoning"}:
            score -= 0.5
        elif flag in {"too_short", "weak_skepticism"}:
            score -= 0.3
        else:
            score -= 0.2
    return max(0.0, score)


def calculate_ewma(current_score: float, previous_ewma: float, alpha: float = 0.3) -> float:
    """Exponentially Weighted Moving Average (EWMA) hesaplar."""
    return alpha * current_score + (1 - alpha) * previous_ewma


def enrich_report_json(
    report_json: dict,
    model: object | None = None,
    plan_type: str = "Free",
) -> dict:
    """Enriches a report dict with quality, performance and fidelity metrics.
    Adversarial review (Grounded Sim §4.5 Phase 6) only runs for Pro+ plans with a model.
    """
    enriched = dict(report_json)
    enriched["research_quality"] = compute_research_quality(enriched)
    enriched["model_performance"] = compute_model_performance(enriched)
    enriched["research_fidelity"] = compute_rfi(enriched)  # Grounded Sim §6.4 — RFI

    # Adversarial review: plan limiti olmaksızın tüm araştırmalarda çalışır (Grounded Sim §4.5)
    if model is not None:
        enriched["adversarial_review"] = adversarial_review(enriched, model)
    else:
        enriched["adversarial_review"] = {"reviewed": False, "reason": "model eksik"}

    return enriched


def adversarial_review(report_dict: dict, model: object) -> dict:
    """Grounded Simulation §4.5 Aşama 6: Adversarial Review.

    Üretilen raporu 3 boyutta eleştirel olarak inceler:
    1. BIAS CHECK    — Herhangi bir stance sistematik olarak kayirılıyor mu?
    2. EVIDENCE CHAIN — Bulgular yeterli kanıta dayanmış mı?
    3. DOUBLE-SIM    — Yapay persona → yapay analiz döngüsünden hangi bulgular şüpheli?

    Kaynak: Bilal (2026) Grounded Simulation §4.5
    """
    system = (
        "Sen uzman bir UX araştırma metodoloji kritikisisin. "
        "Sana bir sentetik araştırma raporunun özeti verilecek. "
        "Raporu 3 boyutta eleştirel olarak incele:\n"
        "1. BIAS CHECK: Herhangi bir stance (Innovator, Skeptic vb.) bulgularda sistemik olarak fazla/az temsil ediliyor mu?\n"
        "2. EVIDENCE CHAIN: Bulgular yeterli sayıda, çeşitli stance'lardan kanıta dayanmış mı, yoksa iddia düzeyinde mi kalıyor?\n"
        "3. DOUBLE-SIM: Yapay persona → yapay analiz döngüsünden kaynaklanabilecek, şüpheli veya aşırı güvenilir görünen bulgu var mı?\n"
        "Her boyut için kısa, net, Turkçe özet ver. JSON formatında dön."
    )
    findings_summary = [
        {
            "title": f.get("title", ""),
            "category": f.get("category", ""),
            "evidence_count": len(f.get("evidence", [])),
            "confidence": f.get("confidence", 0.5),
        }
        for f in report_dict.get("findings", [])[:10]  # Max 10 bulgu gönder
    ]
    stances_present = list({
        ev.get("stance", "")
        for f in report_dict.get("findings", [])
        for ev in f.get("evidence", [])
        if ev.get("stance")
    })
    prompt = (
        f"Bulgular ({len(findings_summary)} adet): {findings_summary}\n"
        f"Temsil edilen stance'lar: {stances_present}\n\n"
        "Adversarial inceleme yap. JSON formatında: "
        '{{"bias_check": "...", "evidence_chain": "...", "double_sim_warning": "...", "overall_confidence": "high/medium/low"}}'
    )
    try:
        response = model.generate(system, prompt)  # type: ignore[attr-defined]
        # JSON parse denemesi
        import json as _json
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1:
            parsed = _json.loads(response[start:end + 1])
            return {"reviewed": True, **parsed}
        return {"reviewed": True, "raw": response}
    except Exception as exc:
        return {"reviewed": False, "error": str(exc)}


def compute_research_quality(report_json: dict) -> dict:
    """Computes quality score and metrics for a research report."""
    findings = report_json.get("findings", [])
    interviews = report_json.get("interviews", [])
    quality_issues = report_json.get("quality_issues", [])
    evidence_count = sum(len(finding.get("evidence", [])) for finding in findings)

    turns = [turn for interview in interviews for turn in interview.get("turns", [])]
    pricing_signal_count = sum(
        1 for turn in turns if "pricing" in (turn.get("tags") or []) or "fiyat" in turn.get("answer", "").lower()
    )
    trust_or_kvkk_signal_count = sum(
        1
        for turn in turns
        if any(marker in turn.get("answer", "").lower() for marker in ["kvkk", "güven", "guven", "veri", "gizlilik"])
    )
    weak_answer_count = sum(1 for turn in turns if len(turn.get("answer", "").split()) < 25)
    issue_count = len(quality_issues)
    meta_issue_count = sum(
        1
        for issue in quality_issues
        if any(marker in str(issue).lower() for marker in ["meta", "asistan", "reasoning", "visible_reasoning"])
    )

    # ── Bias Detection ──────────────────────────────────────────────────────
    bias_results = detect_bias_flags(interviews)
    straight_lining_count = sum(1 for flags in bias_results.values() if "straight_lining" in flags)
    acquiescence_count    = sum(1 for flags in bias_results.values() if "acquiescence_bias" in flags)
    social_desir_count    = sum(1 for flags in bias_results.values() if "social_desirability" in flags)

    score = 68
    score += min(evidence_count, 12) * 2
    score += min(pricing_signal_count, 6) * 2
    score += min(trust_or_kvkk_signal_count, 6)
    score -= issue_count * 6
    score -= weak_answer_count * 3
    score -= meta_issue_count * 10
    # Bias cezaları
    score -= straight_lining_count * 8
    score -= acquiescence_count * 10
    score -= social_desir_count * 5
    score = max(0, min(100, score))

    grade = (
        "green" if score >= 80 and meta_issue_count == 0 and not bias_results
        else "yellow" if score >= 60
        else "red"
    )

    bias_summary = []
    if straight_lining_count:
        bias_summary.append(f"{straight_lining_count} personada tekdüze yanıt kalıbı (straight-lining)")
    if acquiescence_count:
        bias_summary.append(f"{acquiescence_count} Skeptic/Blocker personada beklenmedik uzlaşmacılık")
    if social_desir_count:
        bias_summary.append(f"{social_desir_count} personada sosyal beğeni etkisi")

    summary = (
        f"{score}/100 kalite skoru; {evidence_count} kanıt, {pricing_signal_count} fiyat sinyali, "
        f"{trust_or_kvkk_signal_count} güven/KVKK sinyali, {issue_count} kalite uyarısı."
    )
    if bias_summary:
        summary += " Sapma uyarıları: " + "; ".join(bias_summary) + "."

    return {
        "overall_score": score,
        "grade": grade,
        "evidence_count": evidence_count,
        "pricing_signal_count": pricing_signal_count,
        "trust_or_kvkk_signal_count": trust_or_kvkk_signal_count,
        "quality_issue_count": issue_count,
        "weak_answer_count": weak_answer_count,
        "bias_flags": bias_results,
        "straight_lining_count": straight_lining_count,
        "acquiescence_count": acquiescence_count,
        "social_desirability_count": social_desir_count,
        "summary": summary,
    }


def compute_model_performance(report_json: dict) -> list[dict]:
    """Computes performance summary stats for models utilized in the interviews."""
    models: dict[str, dict] = {}
    for interview in report_json.get("interviews", []):
        role = interview.get("persona", {}).get("role_title") or interview.get("persona", {}).get("segment", "")
        for turn in interview.get("turns", []):
            model_id = turn.get("model_id") or "unknown"
            row = models.setdefault(
                model_id,
                {"model": model_id, "answers": 0, "quality_warnings": 0, "roles": set(), "tags": set()},
            )
            row["answers"] += 1
            row["quality_warnings"] += len(turn.get("quality_flags") or [])
            if role:
                row["roles"].add(role)
            for tag in turn.get("tags") or []:
                row["tags"].add(tag)

    rows: list[dict] = []
    for row in models.values():
        answers = int(row["answers"])
        rows.append(
            {
                "model": row["model"],
                "answers": answers,
                "avg_quality_warnings": round(row["quality_warnings"] / answers, 2) if answers else 0,
                "roles": ", ".join(sorted(row["roles"])) or "-",
                "question_tags": ", ".join(sorted(row["tags"])) or "-",
            }
        )
    return rows


import math


# ── Research Fidelity Index (RFI) ─────────────────────────────────────────────
# Kaynak: Bilal (2026) Grounded Simulation §6.4, Tablo 2
# Ağırlıklar: PGR 0.30, CNS 0.20, AC 0.20, PCal 0.10, PR 0.10, CRA 0.10

RFI_WEIGHTS = {
    "PGR":  0.30,  # Prevalence-Graded Recall — bulgular yeterince geniş kapsamlı mı?
    "CNS":  0.20,  # Constructive Novelty Score — actionable bulgu oranı
    "AC":   0.20,  # Analytical Coherence — executive summary + limitations kalitesi
    "PR":   0.10,  # Population Representativeness — SES + stance Shannon entropy
    "CRA":  0.10,  # Cross-Rater Agreement — stance'lar arası sonuç tutarlılığı
    "PCal": 0.10,  # Prevalence Calibration — güven skoru kalibrasyonu
}

RFI_VALIDITY_THRESHOLD = 0.65  # Bilal (2026): tüm 46 çalışma bu eşiğin üzerinde


def _shannon_entropy(values: list) -> float:
    """Normalize edilmiş Shannon entropy (0-1). Çeşitlilik arttıkça 1'e yaklaşır."""
    if not values:
        return 0.0
    total = len(values)
    counts: dict = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    probs = [c / total for c in counts.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return min(1.0, entropy / max_entropy) if max_entropy > 0 else 0.0


def compute_rfi(report_dict: dict) -> dict:
    """
    Research Fidelity Index (RFI) hesaplar.
    Kaynak: Bilal (2026) Grounded Simulation §6.4 — geometric mean aggregation.

    Returns:
        {
            "rfi": float,          # Kompozit skor 0-1
            "components": dict,    # Her bileşen ayrı
            "valid": bool,         # >= 0.65 eşiği
            "interpretation": str  # İnsan okunabilir yorum
        }
    """
    findings = report_dict.get("findings", [])
    personas = report_dict.get("personas", [])
    executive_summary = report_dict.get("executive_summary", [])
    limitations = report_dict.get("limitations", [])
    action_items = report_dict.get("action_items", [])
    finding_count = len(findings)
    all_categories = {"pain_point", "value", "objection", "pricing", "positioning", "risk"}
    covered = {f.get("category") for f in findings if f.get("category")} & all_categories

    # PGR — kategori kapsamı
    pgr = len(covered) / len(all_categories) if all_categories else 0.5
    pgr = min(1.0, pgr + 0.05 * min(finding_count, 4) / 4)

    # CNS — actionable bulgu oranı
    actionable = sum(
        1 for f in findings
        if f.get("implication") and len(f.get("implication", "")) > 30
        and len(f.get("evidence", [])) >= 1
    )
    cns = actionable / finding_count if finding_count else 0.5

    # AC — raporun analitik bütünlüğü
    exec_score = min(1.0, len(executive_summary) / 4)
    limit_score = min(1.0, len(limitations) / 2)
    action_score = min(1.0, len(action_items) / 3)
    ac = exec_score * 0.4 + limit_score * 0.3 + action_score * 0.3

    # PR — SES + stance Shannon entropy
    stances = [p.get("stance", "") for p in personas if p.get("stance")]
    ses_groups = [p.get("ses_group", "") for p in personas if p.get("ses_group")]
    pr = _shannon_entropy(stances) * 0.6 + _shannon_entropy(ses_groups) * 0.4

    # PCal — güven kalibrasyonu
    if findings:
        avg_conf = sum(f.get("confidence", 0.5) for f in findings) / finding_count
        avg_ev = sum(len(f.get("evidence", [])) for f in findings) / finding_count
        pcal = (0.8 if 0.4 <= avg_conf <= 0.9 else 0.5) + (0.2 if avg_ev >= 1.5 else 0.0)
    else:
        pcal = 0.5

    # CRA — stance'lar arası paylaşılan bulgu kategorileri
    stance_cats: dict[str, set] = {}
    for f in findings:
        for ev in f.get("evidence", []):
            st = ev.get("stance", "")
            if st:
                stance_cats.setdefault(st, set()).add(f.get("category", ""))
    if len(stance_cats) >= 2:
        shared = set.intersection(*stance_cats.values())
        cra = min(1.0, 0.5 + len(shared) * 0.1)
    else:
        cra = 0.6

    components = {"PGR": pgr, "CNS": cns, "AC": ac, "PR": pr, "PCal": pcal, "CRA": cra}

    # Geometric mean: RFI = Π(component ^ weight)
    rfi = math.exp(sum(w * math.log(max(0.001, components[k])) for k, w in RFI_WEIGHTS.items()))
    rfi = min(1.0, max(0.0, rfi))
    valid = rfi >= RFI_VALIDITY_THRESHOLD

    if rfi >= 0.80:
        interpretation = f"Yüksek güven (RFI={rfi:.3f}) — Bulgular hipotez üretimi ve stakeholder sunumu için hazır."
    elif rfi >= 0.65:
        interpretation = f"Orta güven (RFI={rfi:.3f}) — Yön gösterici; kritik kararlar için gerçek kullanıcı doğrulaması önerilir."
    else:
        interpretation = (
            f"Düşük güven (RFI={rfi:.3f}) — Geçerlilik eşiğinin altında. "
            "Stance çeşitliliğini artırın veya daha fazla kanıt toplayın."
        )

    weak = [k for k, v in components.items() if v < 0.6]
    if weak:
        interpretation += f" Zayıf bileşenler: {', '.join(weak)}."

    return {
        "rfi": round(rfi, 3),
        "components": {k: round(v, 3) for k, v in components.items()},
        "valid": valid,
        "validity_threshold": RFI_VALIDITY_THRESHOLD,
        "interpretation": interpretation,
        "source": "Bilal (2026) Grounded Simulation §6.4",
    }
