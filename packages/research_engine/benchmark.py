"""
Clarere Research Fidelity Index (RFI) — Validation Benchmark

Bu modül, LLM tarafından üretilen araştırma bulgularının insan (ground truth)
bulgularına karşı doğruluk ve kapsam ölçümlerini yapar.

Ölçüm yaptığımız metrikler:
1. Theme Recall        — İnsan bulgularının ne kadarı LLM tarafından bulundu?
2. Theme Precision     — LLM bulgularının ne kadarı insan bulgularıyla eşleşiyor?
3. Critical Issue Recall — Kritik sorunların yakalanma oranı
4. False Positive Rate — LLM'in ürettiği ama insanlarda olmayan bulgular
5. Segment Accuracy    — Segment bazında bulguların doğruluğu
6. Contradiction Detection — Çelişkili bulguların tespit oranı
"""

from __future__ import annotations

import difflib
import re
from typing import Any


# ── RFI Grade Scale ──────────────────────────────────────────────────────────

def _rfi_grade(rfi: float) -> str:
    """RFI skorunu harf notuna çevirir."""
    if rfi >= 0.85:
        return "A"
    elif rfi >= 0.75:
        return "B"
    elif rfi >= 0.65:
        return "C"
    elif rfi >= 0.55:
        return "D"
    else:
        return "F"


def _rfi_interpretation(rfi: float, grade: str) -> str:
    """RFI skoru için insan okunabilir yorum."""
    interpretations = {
        "A": f"Yüksek uyum (RFI={rfi:.2f}) — Bulgular referans bulgularla güçlü örtüşüyor; yine de yönlendirici hipotez olarak ele alınmalı.",
        "B": f"İyi uyum (RFI={rfi:.2f}) — Çoğu bulgu referansla örtüşüyor; bazı boşluklar için manuel doğrulama önerilir.",
        "C": f"Orta uyum (RFI={rfi:.2f}) — Belirgin boşluklar mevcut. Kritik kararlar için manuel doğrulama önerilir.",
        "D": f"Düşük uyum (RFI={rfi:.2f}) — Kapsamlı yeniden çalışma gerekli. Temel bulgularda dahi uyumsuzluk var.",
        "F": f"Yetersiz (RFI={rfi:.2f}) — Bulgular referansla örtüşmüyor; çıktı kullanılmamalı.",
    }
    return interpretations.get(grade, interpretations["F"])


# ── Semantic Similarity ─────────────────────────────────────────────────────

# Türkçe stop words — anlamsal eşleşmeyi güçlendirmek için filtrelenir
_TR_STOP_WORDS: set[str] = {
    "bir", "bu", "için", "ile", "ve", "veya", "da", "de", "mi", "mı",
    "mu", "mü", "ki", "ne", "en", "çok", "daha", "ama", "fakat", "gibi",
    "kadar", "olarak", "olan", "ise", "ya", "çünkü", "zira",
    "bazı", "her", "tüm", "bütün", "hiç", "sadece", "yalnızca", "ancak",
    "artık", "henüz", "hala", "şu", "o", "ben", "sen", "biz", "onlar",
}


def _normalize(text: str) -> str:
    """Metni normalize eder: küçük harf, noktalama temizliği, stop word filtresi."""
    cleaned = re.sub(r"[^\w\sçğıöşüÇĞİÖŞÜ]", " ", text.lower())
    tokens = cleaned.split()
    filtered = [t for t in tokens if t not in _TR_STOP_WORDS and len(t) > 1]
    return " ".join(filtered)


def _semantic_similarity(a: str, b: str) -> float:
    """İki metin arasındaki anlamsal benzerliği hesaplar.

    difflib.SequenceMatcher (karakter bazlı) ve token overlap'in
    ağırlıklı ortalamasını kullanır. Bu, Türkçe'deki farklı ifade
    biçimleri arasında daha sağlam eşleşme sağlar.
    """
    a_norm = _normalize(a)
    b_norm = _normalize(b)

    if not a_norm or not b_norm:
        return 0.0

    # Karakter-bazlı benzerlik (difflib)
    char_sim = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()

    # Token-bazlı Jaccard benzerliği
    tokens_a = set(a_norm.split())
    tokens_b = set(b_norm.split())
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    token_sim = len(intersection) / len(union) if union else 0.0

    # Hibrit skor: char benzerliği %60, token benzerliği %40
    return char_sim * 0.6 + token_sim * 0.4


def _best_match_score(target: str, candidates: list[str]) -> float:
    """Bir hedef metin için adaylar arasındaki en yüksek anlamsal benzerliği döndürür."""
    if not candidates:
        return 0.0
    return max(_semantic_similarity(target, c) for c in candidates)


def _extract_texts(findings: list[dict], key: str = "title") -> list[str]:
    """Bulgu listesinden metin listesini çıkarır.

    Her bulgudan hem title hem summary alanlarını birleştirerek
    daha zengin bir metin temsili oluşturur.
    """
    texts: list[str] = []
    for f in findings:
        parts = [str(f.get(k, "")) for k in ("title", "summary") if f.get(k)]
        combined = " ".join(parts).strip()
        if combined:
            texts.append(combined)
    return texts


# ── Core Metrics ─────────────────────────────────────────────────────────────

# Hibrit benzerlik eşik değerleri (difflib + Jaccard)
_THEME_MATCH_THRESHOLD = 0.30
_CRITICAL_MATCH_THRESHOLD = 0.25
_CONTRADICTION_MATCH_THRESHOLD = 0.25


def calculate_theme_recall(
    llm_findings: list[dict], human_findings: list[dict]
) -> float:
    """İnsan bulgularının ne kadarı LLM tarafından bulundu?

    Her insan bulgusu için LLM bulguları arasında en iyi anlamsal eşleşmeyi
    arar. Eşik değerinin üzerindeki eşleşmeler "bulundu" kabul edilir.

    Args:
        llm_findings: LLM tarafından üretilen bulgu listesi (dict listesi).
        human_findings: İnsan (ground truth) bulgu listesi.

    Returns:
        0.0–1.0 arası recall skoru.
    """
    if not human_findings:
        return 1.0

    llm_texts = _extract_texts(llm_findings)
    human_texts = _extract_texts(human_findings)

    if not llm_texts:
        return 0.0

    matched = 0
    for h_text in human_texts:
        score = _best_match_score(h_text, llm_texts)
        if score >= _THEME_MATCH_THRESHOLD:
            matched += 1

    return matched / len(human_texts)


def calculate_theme_precision(
    llm_findings: list[dict], human_findings: list[dict]
) -> float:
    """LLM bulgularının ne kadarı insan bulgularıyla eşleşiyor?

    Her LLM bulgusu için insan bulguları arasında en iyi anlamsal eşleşmeyi
    arar. Eşik değerinin üzerindekiler "doğru" kabul edilir.

    Args:
        llm_findings: LLM tarafından üretilen bulgu listesi.
        human_findings: İnsan (ground truth) bulgu listesi.

    Returns:
        0.0–1.0 arası precision skoru.
    """
    if not llm_findings:
        return 1.0

    llm_texts = _extract_texts(llm_findings)
    human_texts = _extract_texts(human_findings)

    if not human_texts:
        return 0.0

    matched = 0
    for l_text in llm_texts:
        score = _best_match_score(l_text, human_texts)
        if score >= _THEME_MATCH_THRESHOLD:
            matched += 1

    return matched / len(llm_texts)


def calculate_critical_recall(
    llm_findings: list[dict], human_critical: list[str]
) -> float:
    """Kritik sorunların yakalanma oranı.

    İnsan tarafından işaretlenmiş kritik bulguların ne kadarı
    LLM tarafından tespit edilmiş?

    Args:
        llm_findings: LLM bulguları.
        human_critical: İnsan tarafından kritik olarak işaretlenmiş
            bulgu başlıkları/özetleri.

    Returns:
        0.0–1.0 arası critical recall skoru.
    """
    if not human_critical:
        return 1.0

    llm_texts = _extract_texts(llm_findings)

    if not llm_texts:
        return 0.0

    matched = 0
    for crit in human_critical:
        score = _best_match_score(crit, llm_texts)
        if score >= _CRITICAL_MATCH_THRESHOLD:
            matched += 1

    return matched / len(human_critical)


def calculate_false_positive_rate(
    llm_findings: list[dict], human_findings: list[dict]
) -> float:
    """LLM'in ürettiği ama insanlarda olmayan bulguların oranı.

    False positive = (eşleşmeyen LLM bulguları) / (toplam LLM bulguları).
    Bu, 1 - precision'a eşittir ancak ayrı bir metrik olarak sunulur.

    Args:
        llm_findings: LLM bulguları.
        human_findings: İnsan (ground truth) bulguları.

    Returns:
        0.0–1.0 arası false positive oranı.
    """
    precision = calculate_theme_precision(llm_findings, human_findings)
    return 1.0 - precision


def calculate_segment_accuracy(
    llm_findings: list[dict],
    human_findings: list[dict],
    segment_key: str = "category",
) -> float:
    """Segment (kategori) bazında bulguların doğruluğu.

    LLM bulgularının kategorileri ile insan bulgularının kategorileri
    arasındaki örtüşmeyi ölçer.

    Args:
        llm_findings: LLM bulguları.
        human_findings: İnsan bulguları.
        segment_key: Kategori alanının dict anahtarı (varsayılan: "category").

    Returns:
        0.0–1.0 arası segment doğruluk skoru.
    """
    llm_categories = {
        f.get(segment_key) for f in llm_findings if f.get(segment_key)
    }
    human_categories = {
        f.get(segment_key) for f in human_findings if f.get(segment_key)
    }

    if not human_categories:
        return 1.0

    intersection = llm_categories & human_categories
    return len(intersection) / len(human_categories)


def calculate_contradiction_detection(
    llm_findings: list[dict],
    human_contradictions: list[tuple[str, str]],
) -> float:
    """Çelişkili bulguların tespit oranı.

    İnsan tarafından işaretlenmiş çelişkili bulgu çiftlerinin
    LLM tarafından ne kadarının yakalandığını ölçer.

    Args:
        llm_findings: LLM bulguları.
        human_contradictions: İnsan tarafından işaretlenmiş çelişkili
            bulgu çiftleri [(bulgu_a, bulgu_b), ...].

    Returns:
        0.0–1.0 arası contradiction detection skoru.
    """
    if not human_contradictions:
        return 1.0

    llm_texts = _extract_texts(llm_findings)

    detected = 0
    for a, b in human_contradictions:
        score_a = _best_match_score(a, llm_texts)
        score_b = _best_match_score(b, llm_texts)
        # Her iki taraf da en azından kısmen eşleşiyorsa tespit edilmiş say
        if (
            score_a >= _CONTRADICTION_MATCH_THRESHOLD
            and score_b >= _CONTRADICTION_MATCH_THRESHOLD
        ):
            detected += 1

    return detected / len(human_contradictions)


# ── Composite RFI ────────────────────────────────────────────────────────────

# Ağırlıklar: theme_recall * 0.30 + theme_precision * 0.25
# + critical_recall * 0.25 + (1 - false_positive_rate) * 0.20
RFI_BENCHMARK_WEIGHTS: dict[str, float] = {
    "theme_recall": 0.30,
    "theme_precision": 0.25,
    "critical_recall": 0.25,
    "false_positive_rate": 0.20,
}


def calculate_rfi(
    llm_findings: list[dict],
    human_findings: list[dict],
    human_critical: list[str] | None = None,
    human_contradictions: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Clarere Research Fidelity Index (RFI) hesaplar.

    LLM bulgularını insan (ground truth) bulgularıyla karşılaştırarak
    çok boyutlu bir doğruluk skoru üretir.

    Args:
        llm_findings: LLM tarafından üretilen bulgular.
            Her dict en azından "title" ve "summary" içermeli.
        human_findings: İnsan (ground truth) bulgular.
        human_critical: Kritik olarak işaretlenmiş insan bulgularının
            başlık/özet listesi. None ise critical_recall = 1.0.
        human_contradictions: İnsan tarafından işaretlenmiş çelişkili
            bulgu çiftleri. None ise contradiction_detection hesaplanmaz.

    Returns:
        {
            "theme_recall": float,           # 0.0–1.0
            "theme_precision": float,        # 0.0–1.0
            "critical_recall": float,        # 0.0–1.0
            "false_positive_rate": float,    # 0.0–1.0 (düşük = iyi)
            "segment_accuracy": float,       # 0.0–1.0
            "contradiction_detection": float | None,  # 0.0–1.0 veya None
            "overall_rfi": float,            # 0.0–1.0 ağırlıklı kompozit
            "grade": str,                    # A–F harf notu
            "interpretation": str,           # İnsan okunabilir yorum
        }
    """
    theme_recall = calculate_theme_recall(llm_findings, human_findings)
    theme_precision = calculate_theme_precision(llm_findings, human_findings)
    false_positive_rate = calculate_false_positive_rate(llm_findings, human_findings)
    segment_accuracy = calculate_segment_accuracy(llm_findings, human_findings)

    if human_critical is not None:
        critical_recall = calculate_critical_recall(llm_findings, human_critical)
    else:
        critical_recall = 1.0

    if human_contradictions is not None:
        contradiction_detection = calculate_contradiction_detection(
            llm_findings, human_contradictions
        )
    else:
        contradiction_detection = None

    # Ağırlıklı RFI:
    # theme_recall * 0.30 + theme_precision * 0.25 + critical_recall * 0.25
    # + (1 - false_positive_rate) * 0.20
    overall_rfi = (
        theme_recall * RFI_BENCHMARK_WEIGHTS["theme_recall"]
        + theme_precision * RFI_BENCHMARK_WEIGHTS["theme_precision"]
        + critical_recall * RFI_BENCHMARK_WEIGHTS["critical_recall"]
        + (1.0 - false_positive_rate) * RFI_BENCHMARK_WEIGHTS["false_positive_rate"]
    )
    overall_rfi = min(1.0, max(0.0, overall_rfi))

    grade = _rfi_grade(overall_rfi)
    interpretation = _rfi_interpretation(overall_rfi, grade)

    result: dict[str, Any] = {
        "theme_recall": round(theme_recall, 4),
        "theme_precision": round(theme_precision, 4),
        "critical_recall": round(critical_recall, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "segment_accuracy": round(segment_accuracy, 4),
        "contradiction_detection": (
            round(contradiction_detection, 4)
            if contradiction_detection is not None
            else None
        ),
        "overall_rfi": round(overall_rfi, 4),
        "grade": grade,
        "interpretation": interpretation,
    }

    return result
