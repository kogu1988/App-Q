"""
adversarial.py — Grounded Simulation Adversarial Review Pipeline (S2)

3-aşamalı adversarial review:
  1. Bias Audit       — persona convergence + SES/stance dağılım kontrolü
  2. Evidence Chain   — her Finding ≥2 farklı stance kanıt + güven kalibrasyon
  3. Double-Simulation Awareness — dil kalibrasyonu + validation önerileri

Kaynak: Bilal (2026) Grounded Simulation §4.5, §8.1
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ── Sabitler ──────────────────────────────────────────────────────────────────

# Makale: stance diversity en büyük driver (ΔF1 = −0.582)
MIN_STANCE_DIVERSITY = 3          # Bir panelde en az kaç farklı stance olmalı
MIN_EVIDENCE_STANCES = 2          # Her Finding'de en az kaç farklı stance kanıtı
HIGH_CONFIDENCE_THRESHOLD = 0.75  # Bu eşiğin üzerinde kanıt sayısı da kontrol edilir
LOW_EVIDENCE_COUNT = 2            # Yüksek güven + bu sayının altında kanıt → downgrade

# Dil kalibrasyon eşlemeleri: "doğrulayıcı" → "tutarlı" dil
OVERCONFIDENT_LANGUAGE: dict[str, str] = {
    "kanıtlandı": "ile tutarlı",
    "doğrulandı": "ile örtüşüyor",
    "confirmed": "consistent with",
    "validated": "aligned with",
    "proves": "suggests",
    "kesin olarak": "büyük olasılıkla",
    "mutlaka": "büyük ölçüde",
}


# ── Aşama 1: Bias Audit ───────────────────────────────────────────────────────

def bias_audit(report_dict: dict) -> list[dict]:
    """
    Persona convergence ve dağılım biasını tespit eder.

    Kontroller:
    - Stance çeşitliliği: panelde en az MIN_STANCE_DIVERSITY farklı stance
    - SES çeşitliliği: tek bir SES grubunun hakimiyeti
    - Persona convergence: tüm personaların benzer sonuca varması (finding tekrarı)
    """
    flags: list[dict] = []
    personas = report_dict.get("personas", [])
    findings = report_dict.get("findings", [])

    # Stance çeşitliliği
    stances = {p.get("stance", "Bilinmiyor") for p in personas}
    if len(stances) < MIN_STANCE_DIVERSITY:
        flags.append({
            "phase": "bias_audit",
            "severity": "warning",
            "code": "LOW_STANCE_DIVERSITY",
            "message": (
                f"Panelde yalnızca {len(stances)} farklı stance var ({', '.join(stances)}). "
                f"Grounded Simulation mimarisi en az {MIN_STANCE_DIVERSITY} stance gerektirir. "
                "Stance diversity, F1 üzerindeki en büyük tek driver (ΔF1 = −0.582)."
            ),
        })

    # SES hakimiyeti
    ses_counts: dict[str, int] = {}
    for p in personas:
        sg = p.get("ses_group", "C1")
        ses_counts[sg] = ses_counts.get(sg, 0) + 1
    if personas:
        dominant_ses = max(ses_counts, key=ses_counts.__getitem__)
        dominant_ratio = ses_counts[dominant_ses] / len(personas)
        if dominant_ratio > 0.6 and len(personas) >= 3:
            flags.append({
                "phase": "bias_audit",
                "severity": "info",
                "code": "SES_DOMINANCE",
                "message": (
                    f"SES grubu '{dominant_ses}' panelin %{dominant_ratio:.0%}'ini oluşturuyor. "
                    "TÜAD 2025 kota dağılımına yaklaşmak için panel büyüklüğünü artırmayı düşünün."
                ),
            })

    # Persona convergence — tüm finding kanıtları tek stanceden mi geliyor?
    for finding in findings:
        evidence_list = finding.get("evidence", [])
        ev_stances = {ev.get("stance", "") for ev in evidence_list}
        if len(evidence_list) >= 3 and len(ev_stances) == 1:
            flags.append({
                "phase": "bias_audit",
                "severity": "warning",
                "code": "PERSONA_CONVERGENCE",
                "message": (
                    f"Bulgu '{finding.get('title', '?')}': tüm {len(evidence_list)} kanıt "
                    f"tek stance'tan ({next(iter(ev_stances))}). "
                    "Bu, persona convergence belirtisi olabilir — farklı stance'ların görüşü alındı mı?"
                ),
            })

    return flags


# ── Aşama 2: Evidence Chain Validation ───────────────────────────────────────

def evidence_chain_validation(report_dict: dict) -> list[dict]:
    """
    Her Finding için kanıt zinciri bütünlüğünü doğrular.

    Kontroller:
    - Her Finding'in en az MIN_EVIDENCE_STANCES farklı stanceden kanıtı olmalı
    - Yüksek güven ama az kanıt → confidence downgrade önerisi
    - Double-citation: aynı quote birden fazla Finding'de tekrarlanıyor mu?
    """
    flags: list[dict] = []
    findings = report_dict.get("findings", [])

    # Tüm quote'ları topla — double citation tespiti için
    all_quotes: dict[str, list[str]] = {}  # quote → [finding titles]
    for finding in findings:
        for ev in finding.get("evidence", []):
            q = ev.get("quote", "").strip()
            if q:
                if q not in all_quotes:
                    all_quotes[q] = []
                all_quotes[q].append(finding.get("title", "?"))

    # Her Finding için kontrol
    for finding in findings:
        title = finding.get("title", "?")
        confidence = finding.get("confidence", 0.5)
        evidence_list = finding.get("evidence", [])
        ev_stances = {ev.get("stance", "") for ev in evidence_list if ev.get("stance")}

        # Az stance çeşitliliği
        if len(ev_stances) < MIN_EVIDENCE_STANCES and evidence_list:
            flags.append({
                "phase": "evidence_chain",
                "severity": "warning",
                "code": "INSUFFICIENT_STANCE_COVERAGE",
                "finding": title,
                "message": (
                    f"'{title}': kanıtlar yalnızca {len(ev_stances)} farklı stance içeriyor "
                    f"(mevcut: {', '.join(ev_stances) or 'belirsiz'}). "
                    f"Güvenilir bir bulgu için en az {MIN_EVIDENCE_STANCES} farklı stance gerekir."
                ),
            })

        # Yüksek güven + az kanıt
        if confidence >= HIGH_CONFIDENCE_THRESHOLD and len(evidence_list) < LOW_EVIDENCE_COUNT:
            flags.append({
                "phase": "evidence_chain",
                "severity": "warning",
                "code": "OVERCONFIDENT_FINDING",
                "finding": title,
                "message": (
                    f"'{title}': güven skoru {confidence:.2f} ama yalnızca {len(evidence_list)} kanıt var. "
                    f"Güven skorunun {confidence * 0.7:.2f}'e düşürülmesi önerilir."
                ),
                "suggested_confidence": round(confidence * 0.7, 2),
            })

    # Double citation uyarıları
    for quote, finding_titles in all_quotes.items():
        if len(finding_titles) > 1 and len(quote) > 20:
            flags.append({
                "phase": "evidence_chain",
                "severity": "info",
                "code": "DOUBLE_CITATION",
                "message": (
                    f"Bir alıntı {len(finding_titles)} farklı bulguda kullanılmış: "
                    f"{', '.join(finding_titles[:3])}. "
                    "Aynı kanıt farklı bulgulara atıfta bulunuyorsa bağımsızlık azalır."
                ),
            })

    return flags


# ── Aşama 3: Double-Simulation Awareness ────────────────────────────────────

def double_simulation_check(report_dict: dict) -> list[dict]:
    """
    Çift simülasyon farkındalığını uygular:
    - Rapordaki fazla kesin ('kanıtlandı', 'doğrulandı') dil kullanımını tespit eder
    - Validation next steps'i denetler — gerçek kullanıcı doğrulama önerileri var mı?

    Bilal (2026) §4.5: "double-simulation awareness (detecting when AI-generated
    and AI-analyzed data compounds errors invisibly)"
    """
    flags: list[dict] = []

    # Executive summary + action items dil kontrolü
    overconfident_found: list[str] = []
    texts_to_check = (
        report_dict.get("executive_summary", [])
        + report_dict.get("action_items", [])
        + report_dict.get("recommendations", [])
    )
    for text in texts_to_check:
        for overconfident_term in OVERCONFIDENT_LANGUAGE:
            if overconfident_term.lower() in text.lower():
                overconfident_found.append(f"'{overconfident_term}' → '{OVERCONFIDENT_LANGUAGE[overconfident_term]}'")

    if overconfident_found:
        flags.append({
            "phase": "double_simulation",
            "severity": "info",
            "code": "OVERCONFIDENT_LANGUAGE",
            "message": (
                "Raporda doğrulayıcı dil kalıpları tespit edildi. "
                "Sentetik araştırma sonuçları için 'ile tutarlı', 'ile örtüşüyor' "
                "gibi ifadeler tercih edilmeli. "
                f"Önerilen değişiklikler: {'; '.join(set(overconfident_found[:5]))}."
            ),
        })

    # Validation next steps kontrolü
    validation_steps = report_dict.get("validation_next_steps", [])
    has_human_validation = any(
        any(kw in step.lower() for kw in ["gerçek kullanıcı", "real user", "röportaj", "doğrula", "validate", "insan"])
        for step in validation_steps
    )
    if not has_human_validation:
        flags.append({
            "phase": "double_simulation",
            "severity": "warning",
            "code": "MISSING_HUMAN_VALIDATION",
            "message": (
                "Validation next steps bölümünde gerçek kullanıcı doğrulama adımı bulunamadı. "
                "Sentetik araştırma hipotez üretimi için uygundur; kritik kararlar için "
                "gerçek kullanıcı görüşmeleriyle doğrulama zorunludur (Bilal 2026, §7.3)."
            ),
            "suggested_step": (
                "En güçlü 2-3 bulguyu 5-8 gerçek kullanıcıyla kısa görüşme (15-20 dk) "
                "aracılığıyla doğrulayın."
            ),
        })

    return flags


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_adversarial_review(report_dict: dict) -> dict:
    """
    3-aşamalı adversarial review'u çalıştırır ve özet döner.

    Returns:
        {
            "flags": [...],           # Tüm uyarı ve bilgiler
            "flag_count": int,        # Toplam flag sayısı
            "warning_count": int,     # Sadece warning/fail
            "phases_passed": [...],   # Sorunsuz geçen aşamalar
            "phases_flagged": [...],  # Uyarı üretilen aşamalar
            "summary": str,           # İnsan okunabilir özet
        }
    """
    all_flags: list[dict] = []

    # Aşama 1
    bias_flags = bias_audit(report_dict)
    all_flags.extend(bias_flags)

    # Aşama 2
    ev_flags = evidence_chain_validation(report_dict)
    all_flags.extend(ev_flags)

    # Aşama 3
    ds_flags = double_simulation_check(report_dict)
    all_flags.extend(ds_flags)

    # Özet hesapla
    warning_count = sum(1 for f in all_flags if f.get("severity") in ("warning", "fail"))
    phases_flagged = list({f["phase"] for f in all_flags if f.get("severity") in ("warning", "fail")})
    phases_all = {"bias_audit", "evidence_chain", "double_simulation"}
    phases_passed = list(phases_all - set(phases_flagged))

    if not all_flags:
        summary = "Adversarial review tamamlandı — tüm aşamalar geçildi. Önemli bir bias veya kanıt zinciri sorunu tespit edilmedi."
    elif warning_count == 0:
        summary = f"Adversarial review tamamlandı — {len(all_flags)} bilgi notu ({', '.join(phases_flagged)} aşaması). Kritik uyarı yok."
    else:
        summary = (
            f"Adversarial review: {warning_count} uyarı, {len(all_flags) - warning_count} bilgi notu. "
            f"Dikkat gerektiren aşamalar: {', '.join(phases_flagged)}."
        )

    return {
        "flags": all_flags,
        "flag_count": len(all_flags),
        "warning_count": warning_count,
        "phases_passed": phases_passed,
        "phases_flagged": phases_flagged,
        "summary": summary,
    }
