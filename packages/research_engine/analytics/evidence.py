"""Kanit zinciri ve karar katmani (R7-3)."""
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

# ---------------------------------------------------------------------------
# Sprint 1 — Evidence Chain (Kanıt Zinciri)
# ---------------------------------------------------------------------------

# Türkçe duygu sınıflandırma anahtar kelimeleri
_SUPPORTING_KEYWORDS: set[str] = {
    "katılıyorum", "doğru", "evet", "iyi fikir", "güzel", "mantıklı",
    "işe yarar", "faydalı", "kullanırım", "alırım", "tercih ederim",
    "çözer", "yardımcı", "ihtiyaç", "gerekli", "harika", "mükemmel",
    "başarılı", "verimli", "pratik", "kolay", "hızlı", "etkili",
    "değer", "önemli", "kritik", "olmazsa olmaz", "tavsiye ederim",
    "şart", "lazım", "eksikliğini", "bekliyorum", "merakla",
    "denemek isterim", "fırsat", "avantaj", "kazanç",
}

_REFUTING_KEYWORDS: set[str] = {
    "katılmıyorum", "yanlış", "hayır", "pahalı", "değmez",
    "işe yaramaz", "saçma", "güvenmem", "riskli", "korkutucu",
    "kullanmam", "almam", "ihtiyacım yok", "gereksiz", "zaman kaybı",
    "kötü", "berbat", "verimsiz", "zor", "karmaşık", "anlamsız",
    "lüzumsuz", "boş", "aldatmaca", "şüpheli",
    "çekince", "endişe", "kaygı", "tedirgin", "tercih etmem",
    "uğraşmam", "vakit", "parası", "sıkıntı", "sorun",
    "entegrasyon", "uyumsuz", "desteklemiyor",
}

# "Sorun/bariyer VAR" iddiası taşıyan bulgu kategorileri — bu bulgularda olumsuz
# dil DESTEK, olumlu dil (inkar) KARŞI kanıttır.
_NEGATIVE_CLAIM_CATEGORIES: set[str] = {"pain_point", "risk"}



# Bulgu kategori ↔ görüşme sorusu etiketi eşlemesi. Bulgu kategorisi `risk` iken
# senaryo soruları `objection` etiketi taşıdığı için kanıt hiç eşleşmiyordu
# (karar öğeleri "0 destekleyici, 0 karşıt" gösteriyordu).
_CATEGORY_TAG_ALIASES: dict[str, set[str]] = {
    "pain_point": {"pain_point", "pain"},
    "risk": {"risk", "objection"},
    "value": {"value"},
    "positioning": {"positioning", "value"},
}


def classify_evidence_sentiment(quote: str, finding_summary: str = "", category: str | None = None) -> str:
    """Bir alıntının bulguya göre duygusunu sınıflandırır.

    `category` verilirse **bulgunun iddiasına göre** polarite uygulanır:
    - `pain_point` / `risk` bulguları "sorun/bariyer VAR" iddiasıdır → olumsuz dil
      bu iddiayı DESTEKLER, olumlu dil (inkar) karşı çıkar.
    - `value` / `positioning` bulguları olumlu iddiadır → olumlu dil destekler.

    `category` verilmezse eski (kategori-bağımsız) davranış korunur.
    Dönüş: "supporting", "refuting" veya "neutral"
    """
    if not quote or not isinstance(quote, str):
        return "neutral"
    text_lower = quote.lower()

    support_score = sum(1 for kw in _SUPPORTING_KEYWORDS if kw in text_lower)
    refute_score = sum(1 for kw in _REFUTING_KEYWORDS if kw in text_lower)

    # Kategori-farkında polarite: "sorun var" iddialarında olumsuz dil destektir.
    if category in _NEGATIVE_CLAIM_CATEGORIES:
        if refute_score > support_score:
            return "supporting"
        if support_score > refute_score:
            return "refuting"
        return "neutral"

    if support_score > refute_score:
        return "supporting"
    elif refute_score > support_score:
        return "refuting"
    else:
        return "neutral"


def build_evidence_graph(
    interviews: list[PersonaInterview],
    findings: list[Finding],
) -> list[EnhancedFinding]:
    """Mevcut bulguları mülakat verisiyle eşleştirerek kanıt zinciri oluşturur.

    Her bulgu için:
    - İlgili mülakat dönüşlerini tarar
    - Her alıntıyı supporting/refuting/neutral olarak etiketler
    - Destek/karşı/nötr sayılarını hesaplar
    - Çelişki skoru (contradiction_score) ve karar sinyali (decision_signal) üretir
    - Stance bazlı segment kırılımı (segment_breakdown) oluşturur
    """
    enhanced: list[EnhancedFinding] = []

    for finding in findings:
        # Bulgu kategorisiyle eşleşen mülakat dönüşlerini tara
        category_tag = finding.category
        wanted_tags = _CATEGORY_TAG_ALIASES.get(category_tag, {category_tag})
        relevant_evidence: list[dict] = []

        for interview in interviews:
            for turn in interview.turns:
                if wanted_tags & set(turn.tags or []):
                    sentiment = classify_evidence_sentiment(
                        turn.answer, finding.summary, category=category_tag
                    )
                    relevant_evidence.append({
                        "persona_id": interview.persona.id,
                        "persona_name": interview.persona.name,
                        "stance": interview.persona.stance,
                        "question": turn.question,
                        "quote": turn.answer,
                        "sentiment": sentiment,
                    })

        # Sayımları hesapla
        supporting = sum(1 for e in relevant_evidence if e["sentiment"] == "supporting")
        refuting = sum(1 for e in relevant_evidence if e["sentiment"] == "refuting")
        neutral = sum(1 for e in relevant_evidence if e["sentiment"] == "neutral")
        total = supporting + refuting + neutral

        # Çelişki skoru: 0 (tam uyum) → 1 (tam bölünmüşlük)
        if total > 0:
            contradiction = 1.0 - abs(supporting - refuting) / total
            contradiction = round(contradiction, 2)
        else:
            contradiction = 0.0

        # Karar sinyali
        if total == 0:
            decision: DecisionSignal = "INVESTIGATE"
        elif supporting >= total * 0.7 and refuting == 0:
            decision = "SHIP"
        elif supporting > refuting and contradiction < 0.5:
            decision = "ITERATE"
        elif contradiction >= 0.5:
            decision = "INVESTIGATE"
        elif refuting > supporting:
            decision = "KILL"
        else:
            decision = "INVESTIGATE"

        # Segment kırılımı (stance bazında)
        segment_breakdown: dict[str, dict[str, int]] = {}
        for ev in relevant_evidence:
            stance_key = ev["stance"] or "Mainstream"
            if stance_key not in segment_breakdown:
                segment_breakdown[stance_key] = {
                    "supporting": 0, "refuting": 0, "neutral": 0
                }
            segment_breakdown[stance_key][ev["sentiment"]] += 1

        # Evidence nesnelerini oluştur
        evidence_list: list[Evidence] = []
        for ev in relevant_evidence:
            e = Evidence(
                persona_id=ev["persona_id"],
                persona_name=ev["persona_name"],
                stance=ev["stance"],  # type: ignore[arg-type]
                quote=ev["quote"],
                source_question=ev["question"],
                sentiment=ev["sentiment"],
            )
            evidence_list.append(e)

        enhanced.append(EnhancedFinding(
            title=finding.title,
            category=finding.category,
            summary=finding.summary,
            confidence=finding.confidence,
            evidence=evidence_list,
            implication=finding.implication,
            supporting_count=supporting,
            refuting_count=refuting,
            neutral_count=neutral,
            contradiction_score=contradiction,
            decision_signal=decision,
            segment_breakdown=segment_breakdown,
        ))

    return enhanced

# Sprint 7 — Decision Layer: kategori → ITERATE için odak alanı eşlemesi
_ITERATE_ASPECT: dict[str, str] = {
    "pain_point": "kullanıcı deneyimi",
    "value": "değer önerisi",
    "objection": "güven",
    "risk": "risk yönetimi",
    "pricing": "fiyatlandırma",
    "positioning": "konumlandırma",
}

# Karar sinyallerinin son kullanıcıya dönük Türkçe karşılıkları
_SIGNAL_LABELS_TR: dict[str, str] = {
    "SHIP": "YAYINLA",
    "ITERATE": "İYİLEŞTİR",
    "INVESTIGATE": "ARAŞTIR",
    "KILL": "VAZGEÇ",
}

# Karar sinyalleri için renkler (PDF raporunda renkli rozetler)
_SIGNAL_COLORS: dict[str, str] = {
    "SHIP": "#0d9488",
    "ITERATE": "#d97706",
    "INVESTIGATE": "#0284c7",
    "KILL": "#dc2626",
}


def generate_decision_summary(enhanced_findings: list) -> list[DecisionItem]:
    """Enhanced findings'ları karar öğelerine (DecisionItem) dönüştürür.

    Her bulgu için sinyal gücüne göre spesifik, aksiyona dönük
    Türkçe tavsiyeler üretir.
    """
    items: list[DecisionItem] = []

    for ef in enhanced_findings:
        signal: str = ef.decision_signal
        supporting: int = ef.supporting_count
        refuting: int = ef.refuting_count
        contradiction: float = ef.contradiction_score

        evidence_summary = f"{supporting} destekleyici, {refuting} karşıt kanıt"

        aspect = _ITERATE_ASPECT.get(ef.category, "ürün")

        if signal == "SHIP":
            action = (
                f"Bu özelliği MVP'ye dahil et. "
                f"{supporting} persona destekliyor, itiraz yok."
            )
        elif signal == "ITERATE":
            action = (
                f"Kullanıcı geri bildirimine göre {aspect} yönünü geliştir. "
                f"{refuting} itiraz var."
            )
        elif signal == "INVESTIGATE":
            pct = int(contradiction * 100)
            action = (
                f"Daha fazla araştırma gerek. "
                f"%{pct} çelişki oranı. Hedefli anket öner."
            )
        else:  # KILL
            action = (
                f"Bu yönde ilerleme. "
                f"{refuting} persona reddediyor. Kaynakları başka alana yönlendir."
            )

        items.append(DecisionItem(
            signal=signal,
            title=ef.title,
            confidence=ef.confidence,
            supporting_count=supporting,
            refuting_count=refuting,
            evidence_summary=evidence_summary,
            recommended_action=action,
        ))

    return items
