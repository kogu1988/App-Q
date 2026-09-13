"""Van Westendorp fiyat analizi (R7-2)."""
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
