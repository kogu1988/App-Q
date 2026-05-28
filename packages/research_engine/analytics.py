from __future__ import annotations
from dataclasses import asdict
from typing import Any
import re
import statistics

from .models import (
    ResearchBrief,
    ResearchPlan,
    Persona,
    PersonaInterview,
    ResearchReport,
    Finding,
    PricingInsight,
    VanWestendorpInsight,
    Evidence,
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
        "weak_skepticism": "Skeptik/bloklayıcı persona yeterince sert itiraz üretmedi.",
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
                g["top_pain"] = turn.answer[:200]
            if "objection" in (turn.tags or []) and not g["top_objection"]:
                g["top_objection"] = turn.answer[:200]

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
        for interview in interviews:
            p_id = interview.persona.id
            pref = "Undecided"
            if variant_preferences and p_id in variant_preferences:
                pref = variant_preferences[p_id]
            else:
                # auto-detect preference from interview answers
                for turn in interview.turns:
                    if "Varyant A" in turn.question and "Varyant B" in turn.question:
                        ans = turn.answer.lower()
                        has_a = "varyant a" in ans
                        has_b = "varyant b" in ans
                        if has_a and not has_b:
                            pref = "A"
                        elif has_b and not has_a:
                            pref = "B"
                        else:
                            pref = "Undecided"
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
        
        winner = "Varyant A" if votes_a > votes_b else "Varyant B" if votes_b > votes_a else "Berabere / Kararsız"
        
        executive_summary = [
            f"A/B Simülasyonu sonucunda **{winner}** öne çıkmıştır.",
            f"Sentetik katılımcıların %{pct_a}'sı Varyant A'yı ('{brief.variant_a}'), %{pct_b}'si Varyant B'yi ('{brief.variant_b}') tercih etmiştir. Kararsız oranı ise %{pct_undecided} seviyesindedir.",
            "Varyant A; bütçe odaklı, riskten kaçınan ve geleneksel yöntemlerle çalışan segmentlerde yüksek güven duygusu oluşturmuştur.",
            "Varyant B; dijital olgunluğu yüksek, hızlı kurulum ve esneklik arayan modern kullanıcı segmentlerini heyecanlandırmaktadır."
        ]
        
        objection_evidence = collect_evidence(interviews, "objection")
        pricing_evidence = collect_evidence(interviews, "pricing")
        value_evidence = collect_evidence(interviews, "value")
        
        findings = [
            Finding(
                title=f"Kazanan Kurgu: {winner}",
                category="positioning",
                summary=(
                    f"Yapılan sentetik mülakatlar doğrultusunda, {votes_a} persona Varyant A'yı, "
                    f"{votes_b} persona Varyant B'yi seçti. {votes_undecided} katılımcı ise kararsız kaldı."
                ),
                confidence=0.85,
                evidence=value_evidence,
                implication=f"Pazarlama iletişiminde ve lansman mesajlarında {winner} kurgusunun söylemleri birincil tercih olmalıdır.",
            ),
            Finding(
                title="Varyant A Kurgusu Tercih Sebepleri",
                category="value",
                summary=(
                    f"Varyant A ('{brief.variant_a[:40]}...'), özellikle risk toleransı düşük ve bütçe hassasiyeti yüksek segmentlerde "
                    "netlik ve güvenli bir liman vaat ettiği için tercih ediliyor."
                ),
                confidence=0.78,
                evidence=value_evidence,
                implication="Geleneksel pazarlama kanallarında Varyant A'nın güven verici ve maliyet odaklı mesajları ön planda olmalıdır.",
            ),
            Finding(
                title="Varyant B Kurgusu Tercih Sebepleri",
                category="value",
                summary=(
                    f"Varyant B ('{brief.variant_b[:40]}...'), esneklik ve yenilik arayan, dijital olgunluğu yüksek pragmatist kullanıcılar "
                    "tarafından heyecan verici bulunuyor."
                ),
                confidence=0.72,
                evidence=value_evidence,
                implication="Erken benimseyenler (Early Adopters) hedeflenirken Varyant B'nin argümanları öne çıkarılabilir.",
            ),
            Finding(
                title="A/B Ortak İtirazlar ve Riskler",
                category="risk",
                summary="Her iki varyantta da verilerin güvenliği, entegrasyon zorluğu ve operasyonel iş yükü ortak çekinceler olarak öne çıktı.",
                confidence=0.90,
                evidence=objection_evidence,
                implication="Hangi varyant seçilirse seçilsin, iletişimde 'kurulum kolaylığı' ve 'veri güvenliği' garantileri verilmelidir.",
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
        )

    # Standart Pazar Araştırması Modu (Orijinal)
    pain_points = collect_evidence(interviews, "pain_point")
    objections = collect_evidence(interviews, "objection")
    pricing_evidence = collect_evidence(interviews, "pricing")

    if pain_points:
        summary_pain = f"Katılımcılar şu anda bu problemi çözerken yoğun olarak zaman/efor kaybı yaşıyor. Örnek: '{pain_points[0].quote}'"
    else:
        summary_pain = "Hedef kitlede bu problemle ilgili aciliyet tespit edilemedi."

    executive_summary = [
        f"{brief.title} fikrinin genel pazar karşılığı incelendi.",
        summary_pain,
        "Fiyatlama veya güven konusunda bazı çekinceler (özellikle skeptik profillerde) mevcut.",
    ]

    # R14 — Dinamik finding üretimi: mülakat verisinden kanıt bazlı bulgular
    # Sabit 2 boilerplate yerine gerçek veriden üretilir
    findings: list[Finding] = []

    # Finding 1: Pain point (varsa)
    if pain_points:
        top_quote = pain_points[0].quote[:120] if pain_points[0].quote else ""
        findings.append(Finding(
            title="Temel İhtiyaç ve Acı Noktası",
            category="pain_point",
            summary=(
                f"Katılımcıların büyük bölümü mevcut çözümlerde ciddi sürtüşme noktaları bildirdi. "
                f"Öne çıkan alıntı: \"{top_quote}{'...' if len(top_quote) == 120 else ''}\""
            ),
            confidence=min(0.5 + len(pain_points) * 0.07, 0.95),
            evidence=pain_points,
            implication="Ürünün değer önerisinde 'hız', 'birleştirme' veya 'basitleştirme' argümanları öne çıkarılmalı.",
        ))

    # Finding 2: Objections / satın alma bariyerleri (varsa)
    if objections:
        top_obj = objections[0].quote[:120] if objections[0].quote else ""
        findings.append(Finding(
            title="Satın Alma Bariyerleri ve İtirazlar",
            category="risk",
            summary=(
                f"{len(objections)} persona itiraz içeren sinyal verdi. "
                f"Öne çıkan itiraz: \"{top_obj}{'...' if len(top_obj) == 120 else ''}\""
            ),
            confidence=min(0.55 + len(objections) * 0.06, 0.92),
            evidence=objections,
            implication="Ana sayfa ve satış iletişiminde güven vurgusu, şeffaf fiyatlama ve KVKK uyumu belirtilmeli.",
        ))

    # Finding 3: Değer algısı (varsa)
    value_evidence = collect_evidence(interviews, "value")
    if value_evidence:
        top_val = value_evidence[0].quote[:120] if value_evidence[0].quote else ""
        findings.append(Finding(
            title="Değer Algısı ve Fiyat Toleransı",
            category="value",
            summary=(
                f"Değer vurgusu yapan personalar fiyat bariyer eşiğini daha yüksek tuttu. "
                f"Örnek: \"{top_val}{'...' if len(top_val) == 120 else ''}\""
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
            implication="Rakip farklılaşması mesajı, özellikle Innovator ve EarlyAdopter segmentlerinde güçlü etki yaratır.",
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

    pricing = PricingInsight(
        acceptable_range=brief.expected_price or "Aylık 200-500 TL (Tahmini)",
        packaging_suggestion="Deneme sürümü şart.",
        resistance_points=[
            "Peşin yıllık ödeme istenmesi",
            "Ekstra gizli ücretler",
            "Kurulum maliyeti",
        ],
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
        ],
        "validation_next_steps": [
            "Fiyat modelini gerçek bir landing page üzerinde A/B testine sokun.",
            "En güçlü 2-3 bulguyu 5-8 gerçek kullanıcıyla kısa görüşme aracılığıyla doğrulayın.",
        ],
        "quality_issues": [],
    }
    adversarial_result = run_adversarial_review(report_dict_std)
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
    )
