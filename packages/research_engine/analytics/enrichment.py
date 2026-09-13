"""Rapor anlatisini zenginlestirme (Pro LLM) (R7-6)."""
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
