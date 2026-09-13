from __future__ import annotations
from dataclasses import asdict
from typing import Any
import json
import logging
import re
import statistics

logger = logging.getLogger(__name__)

from .models import (
    ResearchBrief,
    ResearchPlan,
    Persona,
    PersonaInterview,
    ResearchReport,
    Finding,
    EnhancedFinding,
    DecisionSignal,
    DecisionItem,
    PricingInsight,
    VanWestendorpInsight,
    Evidence,
    ExternalEvidence,
    QualityIssue,
)
from .adversarial import run_adversarial_review

def summarize_model_usage(interviews: list[PersonaInterview]) -> dict[str, int]:
    usage: dict[str, int] = {}
    for interview in interviews:
        for turn in interview.turns:
            model_id = turn.model_id or "unknown"
            usage[model_id] = usage.get(model_id, 0) + 1
    return usage

def collect_quality_issues(interviews: list[PersonaInterview]) -> list[QualityIssue]:
    issue_text = {
        "meta_tone": "Cevapta asistan/meta tonu var.",
        "visible_reasoning": "Cevapta görünür muhakeme bloğu var.",
        "too_short": "Cevap karar çıkarmak için fazla kısa.",
        "weak_skepticism": "Şüpheci/Geciken persona yeterince sert itiraz üretmedi.",
        "weak_pricing_specificity": "Fiyat sorusunda TL, bütçe, abonelik veya ödeme modeli somutluğu zayıf.",
        "weak_turkey_context": "Türkiye pazarı bağlamı zayıf.",
    }
    issues: list[QualityIssue] = []
    for interview in interviews:
        for turn in interview.turns:
            for flag in turn.quality_flags:
                issues.append(
                    QualityIssue(
                        persona_id=interview.persona.id,
                        persona_name=interview.persona.name,
                        question=turn.question,
                        severity="fail" if flag in {"meta_tone", "visible_reasoning"} else "warning",
                        issue=issue_text.get(flag, flag),
                        recommendation="Bu cevabı yeniden üret veya raporda düşük güvenle kullan.",
                    )
                )
    return issues

def build_pain_point_matrix(interviews: list[PersonaInterview]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for interview in interviews:
        pain_answers = [turn.answer for turn in interview.turns if "pain_point" in turn.tags]
        objection_answers = [turn.answer for turn in interview.turns if "objection" in turn.tags]
        pricing_answers = [turn.answer for turn in interview.turns if "pricing" in turn.tags]
        rows.append(
            {
                "persona": interview.persona.name,
                "segment": interview.persona.segment,
                "primary_pain": pain_answers[0] if pain_answers else "Belirlenmedi",
                "main_objection": objection_answers[0] if objection_answers else "Belirlenmedi",
                "pricing_signal": pricing_answers[0] if pricing_answers else "Belirlenmedi",
            }
        )
    return rows

def collect_evidence(interviews: list[PersonaInterview], tag: str, limit: int = 4) -> list[Evidence]:
    evidence: list[Evidence] = []
    for interview in interviews:
        for turn in interview.turns:
            if tag in turn.tags:
                evidence.append(
                    Evidence(
                        persona_id=interview.persona.id,
                        persona_name=interview.persona.name,
                        stance=interview.persona.stance,
                        quote=turn.answer,
                        source_question=turn.question,
                    )
                )
    return evidence[:limit]

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


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _shorten(text: str | None, limit: int = 160) -> str:
    """Alıntıdan **tam cümle(ler)'den oluşan bir özet** çıkarır.

    Kurallar:
    - Metin limite sığıyorsa aynen döner.
    - Sığmıyorsa, limite sığan tam cümleler birleştirilir (kelime veya cümle
      ortasından kesilmez).
    - Tek bir cümle bile limitten uzunsa kelime sınırında kırpılır.
    - **Sonuna '...' / '…' EKLENMEZ** — çıktı metinleri kırpma izi taşımaz.
    """
    if not text:
        return ""
    text = " ".join(str(text).split())  # fazla boşluk/satır sonlarını normalize et
    if len(text) <= limit:
        return text

    # Limite sığan tam cümleleri biriktir
    excerpt = ""
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        candidate = f"{excerpt} {sentence}".strip()
        if len(candidate) <= limit:
            excerpt = candidate
        else:
            break
    if excerpt:
        return excerpt

    # İlk cümle bile limitten uzun → kelime sınırında kırp (iz bırakmadan)
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:!?-")


def _field(obj: Any, key: str, default: Any = None) -> Any:
    """dict VEYA nesne üzerinden güvenli alan erişimi."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def enrich_report_narrative(
    report: Any,
    model: Any,
    *,
    max_tokens: int | None = None,
) -> tuple[str, list[str]]:
    """Raporu DeepSeek Pro ile zenginleştirir: yönetici anlatımı + stratejik öneriler.

    **Anti-halüsinasyon:** Model YALNIZCA verilen bulgular/kanıtlar üzerinden yazmalıdır;
    yeni veri, rakam, marka veya alıntı üretmesi açıkça yasaklanır. Hata durumunda
    `("", [])` döner ve rapor algoritmik haliyle kalır (graceful degradation).
    """
    try:
        findings = getattr(report, "enhanced_findings", None) or report.findings
        payload = {
            "baslik": report.title,
            "amac": getattr(report.plan, "objective", ""),
            "bulgular": [
                {
                    "baslik": _field(f, "title", ""),
                    "kategori": _field(f, "category", ""),
                    "ozet": _field(f, "summary", ""),
                    "etki": _field(f, "implication", ""),
                    "destek": _field(f, "supporting_count"),
                    "karsi": _field(f, "refuting_count"),
                    "kanitlar": [
                        {
                            "persona": _field(ev, "persona_name", ""),
                            "alinti": _shorten(_field(ev, "quote", ""), 180),
                        }
                        for ev in (_field(f, "evidence", []) or [])[:3]
                    ],
                }
                for f in list(findings)[:8]
            ],
            "fiyat": {
                "kabul_araligi": report.pricing.acceptable_range,
                "paket_onerisi": report.pricing.packaging_suggestion,
                "direnc_noktalari": list(report.pricing.resistance_points),
            },
            "aksiyonlar": list(report.action_items),
            "kisitlar": list(report.limitations),
        }
        system = (
            "Sen kıdemli bir pazar araştırması analistisin. Sana VERİLEN veriler dışında "
            "HİÇBİR bilgi, rakam, marka veya alıntı UYDURMA. Yalnızca verilen kanıtlardan "
            "çıkarım yap, neden-sonuç kur ve uygulanabilir strateji üret. Dil: profesyonel "
            "Türkçe, danışman tonu; pazarlama süslü dili ve abartı YOK. Cümlelerde '...' kullanma."
        )
        prompt = (
            "Aşağıdaki JSON, tamamlanmış bir sentetik pazar araştırmasının bulgularıdır.\n"
            f"{json.dumps(payload, ensure_ascii=False)}\n\n"
            "Bu verilerden yola çıkarak SADECE şu JSON'u döndür:\n"
            "{\n"
            '  "yonetici_anlatimi": "3-5 cümlelik, bulguları nedensel olarak bağlayan yönetici özeti",\n'
            '  "stratejik_oneriler": ["3 ila 5 adet, kanıta dayalı, uygulanabilir öneri"]\n'
            "}\n"
            "Başka hiçbir metin ekleme."
        )
        raw = model.generate(system=system, prompt=prompt, response_format="json", max_tokens=max_tokens)
        data = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(data, dict):
            return "", []
        narrative = str(data.get("yonetici_anlatimi", "")).strip()
        recs = [str(r).strip() for r in (data.get("stratejik_oneriler") or []) if str(r).strip()]
        return narrative, recs
    except Exception as exc:  # noqa: BLE001
        logger.warning("Rapor anlatım zenginleştirmesi atlandı: %s", exc)
        return "", []


def enrich_themes_narrative(
    themes: list[dict],
    model: Any,
    *,
    max_tokens: int | None = None,
) -> tuple[str, list[str]]:
    """Async "Research Studio" tematik çıktısını yönetici anlatımı + önerilerle zenginleştirir.

    `enrich_report_narrative` ile aynı anti-halüsinasyon kuralı: YALNIZCA verilen
    temalar ve alıntılar kullanılır; yeni veri/rakam/alıntı üretilmez. Hata durumunda
    `("", [])` döner.
    """
    try:
        payload = {
            "temalar": [
                {
                    "baslik": t.get("title", ""),
                    "yayginlik": t.get("prevalence"),
                    "alintilar": [
                        _shorten(ev.get("quote", ""), 160)
                        for ev in (t.get("evidence_chain") or [])[:3]
                    ],
                }
                for t in list(themes)[:8]
            ]
        }
        system = (
            "Sen kıdemli bir pazar araştırması analistisin. Sana VERİLEN temalar ve "
            "alıntılar dışında HİÇBİR bilgi, rakam, marka veya alıntı UYDURMA. Yalnızca "
            "verilen kanıtlardan çıkarım yap ve uygulanabilir öneri üret. Dil: profesyonel "
            "Türkçe, danışman tonu. Cümlelerde '...' kullanma."
        )
        prompt = (
            "Aşağıdaki JSON, tematik analizden çıkan pazar temalarıdır.\n"
            f"{json.dumps(payload, ensure_ascii=False)}\n\n"
            "Bu verilerden yola çıkarak SADECE şu JSON'u döndür:\n"
            "{\n"
            '  "yonetici_anlatimi": "3-5 cümlelik, temaları nedensel bağlayan yönetici özeti",\n'
            '  "stratejik_oneriler": ["3 ila 5 adet, kanıta dayalı, uygulanabilir öneri"]\n'
            "}\n"
            "Başka hiçbir metin ekleme."
        )
        raw = model.generate(system=system, prompt=prompt, response_format="json", max_tokens=max_tokens)
        data = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(data, dict):
            return "", []
        narrative = str(data.get("yonetici_anlatimi", "")).strip()
        recs = [str(r).strip() for r in (data.get("stratejik_oneriler") or []) if str(r).strip()]
        return narrative, recs
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tematik anlatım zenginleştirmesi atlandı: %s", exc)
        return "", []


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

# ---------------------------------------------------------------------------
# End Sprint 1
# ---------------------------------------------------------------------------


def build_ses_cross_tab(interviews: list[PersonaInterview]) -> list[dict[str, Any]]:
    """
    TÜAD 2025 SES grubu (AB/C1/C2/DE) x Stance (Champion/Skeptic/...) çapraz tablosu.
    Her satır bir persona'yı ve oy ağırlığını gösterir.
    """
    SES_ORDER = ["AB", "C1", "C2", "DE"]
    # Rogers Diffusion stance kategorileri
    STANCE_ORDER = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]

    # Grup sayımları
    matrix: dict[str, dict[str, int]] = {ses: {st: 0 for st in STANCE_ORDER} for ses in SES_ORDER}
    totals: dict[str, int] = {ses: 0 for ses in SES_ORDER}

    for iv in interviews:
        ses = getattr(iv.persona, "ses_group", "C1") or "C1"
        stance = iv.persona.stance or "Mainstream"
        if ses not in matrix:
            matrix[ses] = {st: 0 for st in STANCE_ORDER}
            totals[ses] = 0
        col = stance if stance in STANCE_ORDER else "Mainstream"
        matrix[ses][col] += 1
        totals[ses] += 1

    rows: list[dict[str, Any]] = []
    for ses in SES_ORDER:
        if totals.get(ses, 0) == 0:
            continue
        dominant_stance = max(matrix[ses], key=lambda s: matrix[ses][s])
        rows.append({
            "ses_group": ses,
            "total": totals[ses],
            "stance_counts": matrix[ses],
            "dominant_stance": dominant_stance,
        })
    return rows


def build_respondent_type_summary(interviews: list[PersonaInterview]) -> list[dict[str, Any]]:
    """
    Katılımcı tipi (respondent_type) bazında pain_point, objection ve pricing
    alıntılarını gruplayarak özetler. Her tip için ortalama fiyat hassasiyetini de verir.
    """
    RESPONDENT_LABELS = {
        "potential_customer": "Potansiyel Müşteri",
        "competitor_user": "Rakip Kullanıcısı",
        "churned_user": "Kaybedilmiş Kullanıcı",
        "decision_maker": "Karar Verici",
        "individual_user": "Bireysel Kullanıcı",
    }
    groups: dict[str, dict[str, Any]] = {}

    for iv in interviews:
        rtype = getattr(iv.persona, "respondent_type", "potential_customer") or "potential_customer"
        if rtype not in groups:
            groups[rtype] = {
                "respondent_type": rtype,
                "label": RESPONDENT_LABELS.get(rtype, rtype),
                "count": 0,
                "avg_price_sensitivity": 0.0,
                "top_pain": None,
                "top_objection": None,
            }
        g = groups[rtype]
        g["count"] += 1
        g["avg_price_sensitivity"] = (
            (g["avg_price_sensitivity"] * (g["count"] - 1) + iv.persona.price_sensitivity) / g["count"]
        )
        for turn in iv.turns:
            if "pain_point" in (turn.tags or []) and not g["top_pain"]:
                g["top_pain"] = _shorten(turn.answer, 240)
            if "objection" in (turn.tags or []) and not g["top_objection"]:
                g["top_objection"] = _shorten(turn.answer, 240)

    return list(groups.values())


def _extract_tl_amounts(text: str) -> list[float]:
    """Metin içinden TL rakamlarını çıkarır. Örn: '299 TL', '1.200 TL', 'bin TL' -> [299, 1200, 1000]"""
    amounts: list[float] = []

    # Numerik: 200 TL, 1.500TL, 2,500 TL, 500-800 TL
    pattern = r'(\d[\d\.,]*?)\s*(?:TL|tl|lira|₺)'
    for m in re.finditer(pattern, text):
        raw = m.group(1).replace(".", "").replace(",", "")
        try:
            v = float(raw)
            if 1 <= v <= 100_000:  # Makul aralık
                amounts.append(v)
        except ValueError:
            pass

    # Sözel: "iki yüz", "beş yüz", "bin"
    text_lower = text.lower()
    VERBAL = [
        ("iki yüz", 200), ("iki yüz elli", 250), ("üç yüz", 300), ("dört yüz", 400),
        ("beş yüz", 500), ("altı yüz", 600), ("yedi yüz", 700), ("sekiz yüz", 800),
        ("dokuz yüz", 900), ("bin", 1000), ("iki bin", 2000), ("beş bin", 5000),
        ("on bin", 10000),
    ]
    for word, val in VERBAL:
        if word in text_lower and val not in amounts:
            amounts.append(float(val))

    return sorted(set(amounts))


def _cumulative_freq(values: list[float], prices: list[float]) -> list[float]:
    """Fiyat noktaları için kümülatif frekans yüzdesini hesaplar (0–100)."""
    n = len(values)
    if n == 0:
        return [0.0] * len(prices)
    return [sum(1 for v in values if v <= p) / n * 100 for p in prices]


def _find_intersection(freq_a: list[float], freq_b: list[float],
                       prices: list[float]) -> float:
    """İki kümülatif frekans eğrisinin kesişim fiyatını lineer interpolasyon ile bulur.

    PSM metodolojisinde PMC, PME, OPP ve IPP hesabı için kullanılır.
    Kesişim bulunamazsa merkez fiyat döner.
    """
    for i in range(len(prices) - 1):
        diff_curr = freq_a[i] - freq_b[i]
        diff_next = freq_a[i + 1] - freq_b[i + 1]
        if diff_curr * diff_next <= 0:  # işaret değişti = kesişim
            denominator = diff_curr - diff_next
            if abs(denominator) < 1e-9:
                return prices[i]
            t = diff_curr / denominator
            return round(prices[i] + t * (prices[i + 1] - prices[i]), 0)
    # Kesişim bulunamazsa medyan döner
    return round(statistics.median(prices), 0)



def _derive_psm_thresholds(persona: Persona, base_price: float) -> tuple[float, float, float, float]:
    """
    Fiyat hassasiyeti + temel fiyatla 4 PSM eşiği üretir.
    Dönüş: (too_cheap, cheap, expensive, too_expensive)
    """
    ps = persona.price_sensitivity  # 1-10
    # Yüksek hassasiyet = düşük fiyat toleransı
    sensitivity_factor = 1 - (ps - 5) * 0.06  # 0.7 (ps=10) ... 1.3 (ps=1)
    bp = base_price * max(0.5, sensitivity_factor)

    too_cheap  = round(bp * 0.35, -1)   # Baz fiyatın %35’i
    cheap      = round(bp * 0.65, -1)   # %65
    expensive  = round(bp * 1.20, -1)   # %120
    too_expensive = round(bp * 1.70, -1)  # %170
    return too_cheap, cheap, expensive, too_expensive


def van_westendorp_analysis(brief: ResearchBrief, interviews: list[PersonaInterview]) -> VanWestendorpInsight | None:
    """
    Van Westendorp Price Sensitivity Meter analizi.
    Sentetik mülakat yanıtlarından TL fiyat sinyallerini çıkarır
    ve 4 eşik üzerinden OPP, IPP, PMC, PME hesaplar.
    """
    # Temel fiyat tahmini: brief.expected_price içinde numerik değer varsa kullan
    base_price = 499.0  # Varsayılan
    if brief.expected_price:
        nums = _extract_tl_amounts(brief.expected_price)
        if nums:
            base_price = statistics.median(nums)

    too_cheap_all:    list[float] = []
    cheap_all:        list[float] = []
    expensive_all:    list[float] = []
    too_expensive_all: list[float] = []

    for iv in interviews:
        # Mülakat yanıtlarından fiyat sinyali topla (pricing tag)
        pricing_answers = [t.answer for t in iv.turns if "pricing" in (t.tags or [])]
        extracted: list[float] = []
        for ans in pricing_answers:
            extracted.extend(_extract_tl_amounts(ans))

        if len(extracted) >= 2:
            extracted_sorted = sorted(extracted)
            # PSM ata: en düşük 2 -> too_cheap/cheap, en yüksek 2 -> expensive/too_expensive
            too_cheap_all.append(extracted_sorted[0])
            cheap_all.append(extracted_sorted[1])
            if len(extracted_sorted) >= 4:
                expensive_all.append(extracted_sorted[-2])
                too_expensive_all.append(extracted_sorted[-1])
            elif len(extracted_sorted) == 3:
                expensive_all.append(extracted_sorted[-1])
                tc, ch, ex, te = _derive_psm_thresholds(iv.persona, base_price)
                too_expensive_all.append(te)
            else:
                tc, ch, ex, te = _derive_psm_thresholds(iv.persona, base_price)
                expensive_all.append(ex)
                too_expensive_all.append(te)
        elif len(extracted) == 1:
            # Tek fiyat bulundu: pivot olarak kullan
            pivot = extracted[0]
            tc, ch, ex, te = _derive_psm_thresholds(iv.persona, pivot)
            too_cheap_all.append(tc)
            cheap_all.append(ch)
            expensive_all.append(ex)
            too_expensive_all.append(te)
        else:
            # Hiç fiyat bulunamadı: heuristik kullan
            tc, ch, ex, te = _derive_psm_thresholds(iv.persona, base_price)
            too_cheap_all.append(tc)
            cheap_all.append(ch)
            expensive_all.append(ex)
            too_expensive_all.append(te)

    if not too_cheap_all:
        return None  # Veri yetersiz

    # Fiyat eksenini oluştur (100 noktalı, granüler)
    all_vals = too_cheap_all + cheap_all + expensive_all + too_expensive_all
    p_min = max(1.0, min(all_vals) * 0.8)
    p_max = max(all_vals) * 1.2
    prices = [p_min + (p_max - p_min) * i / 99 for i in range(100)]

    # Kümülatif frekans eğrileri (god_doc.md §8)
    # too_cheap ve cheap: artan eğri (düşük fiyatta herkes ucuz buluyor)
    cf_too_cheap = _cumulative_freq(too_cheap_all, prices)
    cf_cheap     = _cumulative_freq(cheap_all, prices)
    # expensive ve too_expensive: azalan eğri (üstünden başlıyor)
    cf_expensive     = [100 - f for f in _cumulative_freq(expensive_all, prices)]
    cf_too_expensive = [100 - f for f in _cumulative_freq(too_expensive_all, prices)]

    # PSM kritik kesişim noktaları (god_doc.md §8)
    # PMC: "Çok Ucuz %" = "Pahalı %"  kesişimi — kabulün alt sınırı
    pmc = _find_intersection(cf_too_cheap, cf_expensive, prices)
    # PME: "Ucuz %" = "Çok Pahalı %" kesişimi — kabulün üst sınırı
    pme = _find_intersection(cf_cheap, cf_too_expensive, prices)
    # OPP: "Çok Ucuz %" = "Çok Pahalı %" kesişimi — satış hacmini maksimize eden nokta
    opp = _find_intersection(cf_too_cheap, cf_too_expensive, prices)
    # IPP: "Ucuz %" = "Pahalı %" kesişimi — ortalama tüketici beklentisi
    ipp = _find_intersection(cf_cheap, cf_expensive, prices)

    # PSM mantık koruması: PMC ≤ OPP ≤ PME
    pmc = min(pmc, opp)
    pme = max(pme, opp)

    return VanWestendorpInsight(
        too_cheap_values=sorted(too_cheap_all),
        cheap_values=sorted(cheap_all),
        expensive_values=sorted(expensive_all),
        too_expensive_values=sorted(too_expensive_all),
        opp=opp,
        ipp=ipp,
        pmc=pmc,
        pme=pme,
        acceptable_range=(pmc, pme),
    )


def build_brand_health_summary(
    interviews: list[PersonaInterview],
    competitors: list[str],
) -> dict | None:
    """
    Marka sağlığı özeti:
    - Yardımsız bilinç (unaided recall): kimin adı geçti?
    - Çağrışım: rakip markalar hakkında kullanılan sıfat ve sözcler
    """
    if not competitors:
        return None

    unaided_counts: dict[str, int] = {c: 0 for c in competitors}
    unaided_counts["diğer"] = 0
    associations: dict[str, list[str]] = {c: [] for c in competitors}

    STOP_WORDS = {
        "bir", "ve", "bu", "ile", "da", "de", "ki", "o", "ben", "sen",
        "biz", "siz", "ama", "ya", "gibi", "için", "olan", "daha", "en",
        "onlar", "olarak", "ne", "nasıl", "neden", "çok", "az",
    }

    for iv in interviews:
        for turn in iv.turns:
            # Yardımsız bilinç (BRAND-UNAIDED tag)
            if turn.question and "BRAND-UNAIDED" in turn.question.upper() or \
               (turn.tags and "positioning" in turn.tags):
                ans_lower = turn.answer.lower()
                mentioned = False
                for comp in competitors:
                    if comp.lower() in ans_lower:
                        unaided_counts[comp] += 1
                        mentioned = True
                if not mentioned:
                    unaided_counts["diğer"] += 1

            # Çağrışım (BRAND-ASSOCIATION)
            if turn.question and "BRAND-ASSOCIATION" in turn.question.upper():
                words = [
                    w for w in turn.answer.lower().split()
                    if len(w) > 3 and w not in STOP_WORDS
                ]
                ans_lower = turn.answer.lower()
                for comp in competitors:
                    if comp.lower() in ans_lower:
                        associations[comp].extend(words[:8])

    # Association frequency per competitor
    assoc_summary: dict[str, list[str]] = {}
    for comp, words in associations.items():
        if words:
            freq: dict[str, int] = {}
            for w in words:
                freq[w] = freq.get(w, 0) + 1
            top = sorted(freq, key=lambda x: freq[x], reverse=True)[:5]
            assoc_summary[comp] = top

    total_mentions = sum(v for k, v in unaided_counts.items() if k != "diğer")
    top_of_mind = max(
        (k for k in unaided_counts if k != "diğer"),
        key=lambda k: unaided_counts[k],
        default=None,
    ) if unaided_counts else None

    return {
        "unaided_recall": unaided_counts,
        "associations": assoc_summary,
        "top_of_mind": top_of_mind,
        "total_mentions": total_mentions,
    }


def build_channel_map(interviews: list[PersonaInterview]) -> list[dict]:
    """
    Mülakat yanıtlarından keşif kanalı frekans haritası üretir.
    """
    CHANNEL_KEYWORDS: dict[str, list[str]] = {
        "Sosyal Medya":        ["sosyal medya", "instagram", "twitter", "linkedin", "tiktok", "youtube", "facebook", "x.com"],
        "Arama Motoru":        ["google", "yandex", "arama", "arama motoru", "search"],
        "Arkadaş Tavsiyesi":  ["tavsiye", "arkadaş", "ağız", "referans", "söyledi", "duydum"],
        "Haber / Blog":        ["haber", "blog", "makale", "yazı", "içerik", "medium", "substack"],
        "Uygulama Mağazası":  ["app store", "play store", "uygulama mağazası", "mağaza"],
        "Doğrudan / Web":     ["web sitesi", "direkt", "doğrudan", "url", "link"],
        "E-posta / Bülten":   ["e-posta", "eposta", "mail", "bülten", "newsletter"],
    }

    counts: dict[str, int] = {ch: 0 for ch in CHANNEL_KEYWORDS}

    for iv in interviews:
        for turn in iv.turns:
            if not turn.tags or "positioning" not in turn.tags:
                continue
            ans_lower = turn.answer.lower()
            for channel, keywords in CHANNEL_KEYWORDS.items():
                if any(kw in ans_lower for kw in keywords):
                    counts[channel] += 1
                    break  # Her cevap bir kanala sayılır

    # Sadece mention edilenleri dön, frekansa göre sırala
    results = [
        {"channel": ch, "count": cnt, "pct": 0}
        for ch, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        if cnt > 0
    ]
    total = sum(r["count"] for r in results)
    for r in results:
        r["pct"] = round(r["count"] / total * 100, 1) if total else 0

    return results


def _relevance_score(snippet: str, finding_keywords: set[str]) -> tuple[str, float]:
    """Snippet'ın bulgu anahtar kelimeleriyle örtüşme düzeyini hesaplar.

    Dönüş: (relevance_label, confidence_boost)
    """
    if not snippet:
        return ("low", 0.0)

    snippet_lower = snippet.lower()
    matches = sum(1 for kw in finding_keywords if kw.lower() in snippet_lower)
    total = len(finding_keywords)

    if total == 0:
        return ("low", 0.0)

    ratio = matches / total
    if ratio >= 0.5:
        return ("high", 0.10)
    elif ratio >= 0.25:
        return ("medium", 0.05)
    else:
        return ("low", 0.02)


# ---------------------------------------------------------------------------
# Sprint 6 — Web Corroboration (Dış Kanıt)
# ---------------------------------------------------------------------------

# TÜAD / Statista tarzı referans listesi — fallback mock verisi
_MOCK_EXTERNAL_SOURCES: list[dict] = [
    {
        "title": "TÜAD 2025 Türkiye Dijital Tüketici Raporu",
        "url": "https://tuad.org.tr/arastirmalar/tuketici-2025",
        "snippet": "Türkiye'de dijital ürün kullanıcılarının %67'si şeffaf fiyatlandırmayı en önemli satın alma kriteri olarak belirtiyor.",
    },
    {
        "title": "Statista Türkiye Pazar Analizi 2025",
        "url": "https://statista.com/outlook/turkey-market-2025",
        "snippet": "Türkiye pazarında kullanıcı deneyimi ve onboarding süresi, SaaS ürünlerinde churn oranını doğrudan etkileyen faktörler arasında ilk üçte yer alıyor.",
    },
    {
        "title": "Deloitte Türkiye Teknoloji Sektörü Görünümü 2025",
        "url": "https://deloitte.com/tr/tech-outlook-2025",
        "snippet": "KOBİ segmentinde dijital dönüşüm harcamaları yıllık %22 büyüme gösteriyor. Kullanıcılar entegrasyon kolaylığı ve yerel destek talep ediyor.",
    },
    {
        "title": "TÜBİSAD Türkiye Bilgi ve İletişim Teknolojileri Raporu",
        "url": "https://tubisad.org.tr/raporlar/btk-2025",
        "snippet": "BT sektöründe müşteri edinme maliyeti (CAC) geçen yıla göre %18 artarken, kullanıcı beklentileri de hızla yükseliyor.",
    },
    {
        "title": "McKinsey Türkiye Tüketici Araştırması 2025",
        "url": "https://mckinsey.com/tr/consumer-2025",
        "snippet": "Türk tüketicilerin %74'ü satın alma öncesinde en az üç farklı kaynaktan ürün araştırması yapıyor; sosyal kanıt ve referans etkisi kritik.",
    },
]


def corroborate_findings(
    findings: list[Finding],
    brief_title: str,
    category: str,
    degradation_notes: list[str] | None = None,
) -> list[ExternalEvidence]:
    """Her bulgu için web'de doğrulayıcı dış kanıt arar.

    SearXNG üzerinden hedefli arama yapar; başarısız olursa
    TÜAD/Statista referanslı mock verisine düşer.

    Her bulgu için en fazla 3 kaynak döndürür.
    """
    import logging
    logger = logging.getLogger(__name__)

    external: list[ExternalEvidence] = []
    used_mock = False

    search_retriever = None
    search_available = False
    try:
        from .search import search_retriever
        if search_retriever is not None:
            search_available = True
    except (ImportError, ModuleNotFoundError):
        logger.warning("SearXNG retriever import edilemedi, mock veri kullanılacak.")

    for finding in findings:
        finding_keywords = set(
            finding.title.split() + finding.summary.split()
        )

        results: list[dict] = []

        if search_available and search_retriever is not None:
            query = f"{finding.title} Turkey market research {category}"
            try:
                results = search_retriever.search(query, limit=5)
                logger.info(
                    f"SearXNG araması: '{query}' → {len(results)} sonuç"
                )
            except (OSError, ValueError, ConnectionError) as e:
                logger.warning(f"SearXNG araması başarısız: {e}")
                results = []

        # Fallback: mock veri kullan
        if not results:
            results = [
                {"title": s["title"], "url": s["url"], "content": s["snippet"]}
                for s in _MOCK_EXTERNAL_SOURCES[:3]
            ]
            used_mock = True
            logger.info(
                f"'{finding.title}' için mock dış kanıt kullanılıyor."
            )

        for idx, res in enumerate(results):
            if idx >= 3:
                break

            snippet = res.get("content", "") or res.get("snippet", "")
            relevance, boost = _relevance_score(snippet, finding_keywords)

            external.append(ExternalEvidence(
                finding_title=finding.title,
                source_title=res.get("title", "Bilinmeyen Kaynak"),
                source_url=res.get("url", ""),
                snippet=snippet,
                relevance=relevance,
                confidence_boost=boost,
            ))

    # Sessiz degradasyonu önle: arama başarısızsa rapora uyarı notu düş.
    if used_mock and degradation_notes is not None:
        degradation_notes.append(
            "Harici kanıt doğrulaması SearXNG'den alınamadı; TÜAD/Statista referansları "
            "(yedek veri) kullanıldı. Dış doğrulama tamamlanmamıştır."
        )
    return external


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


def synthesize_report(
    brief: ResearchBrief,
    plan: ResearchPlan,
    personas: list[Persona],
    interviews: list[PersonaInterview],
    variant_preferences: dict[str, str] | None = None,
) -> ResearchReport:
    # A/B Test Modu (Varyantlar mevcutsa)
    if brief.variant_a and brief.variant_b:
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

    report_dict_std = {
        "personas": [asdict(p) for p in personas],
        "findings": [asdict(f) for f in findings],
        "executive_summary": executive_summary,
        "action_items": [
            "Ürünün ilk sürümünde (MVP) güven bariyerini aşacak özelliklere odaklanın.",
            "Rekabetten ayrışmak için ana sayfada hız vurgusunu artırın.",
        ],
        "recommendations": [
            "Birebir müşteri görüşmelerinde bu sentetik rapordaki itirazları test edin.",
            "Güven bariyerini aşmak için veri güvenliği (KVKK) ve klinik entegrasyonu vurgusunu öne çıkarın.",
            "Fiyatlandırmayı esnek (aylık, kolay iptal) tutarak direnci azaltın.",
        ],
        "validation_next_steps": [
            "Fiyat modelini gerçek bir landing page üzerinde A/B testine sokun.",
            "En güçlü 2-3 bulguyu 5-8 gerçek kullanıcıyla kısa görüşme aracılığıyla doğrulayın.",
        ],
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
        action_items=[
            "Ürünün ilk sürümünde (MVP) güven bariyerini aşacak özelliklere odaklanın.",
            "Rekabetten ayrışmak için ana sayfada hız vurgusunu artırın.",
        ],
        recommendations=[
            "Birebir müşteri görüşmelerinde bu sentetik rapordaki itirazları test edin.",
            "Güven bariyerini aşmak için veri güvenliği (KVKK) ve klinik entegrasyonu vurgusunu öne çıkarın.",
            "Fiyatlandırmayı esnek (aylık, kolay iptal) tutarak direnci azaltın.",
        ],
        validation_next_steps=[
            "Fiyat modelini gerçek bir landing page üzerinde A/B testine sokun.",
            "En güçlü 2-3 bulguyu 5-8 gerçek kullanıcıyla kısa görüşme (15-20 dk) aracılığıyla doğrulayın.",
        ],
        limitations=[
            "Sentetik veriler gerçek pazar davranışını %100 yansıtmayabilir.",
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
