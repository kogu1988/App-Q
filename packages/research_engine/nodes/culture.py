import math
from typing import List, Dict, Optional, Any

# ── Hofstede Türkiye Kültürel Boyutlar ────────────────────────────────────────
# Kaynak: Grounded Simulation §4.1; Hofstede (1980); hofstede-insights.com/country/turkey
# Per-country response style calibration: directness, hierarchical deference, acquiescence risk
HOFSTEDE_TURKEY = {
    "PDI": 66,  # Güç Mesafesi: Otorite/marka güvenine saygı yüksek
    "IDV": 37,  # Kolektivizm: Aile/çevre onayı önemli, yalnız karar verme zorlu
    "MAS": 45,  # Erillik: Dengeli — ne aşırı rekabetçi ne nazik
    "UAI": 85,  # Belirsizlikten Kaçınma: Belirsiz ürün/fiyat reddedilir
    "LTO": 46,  # Kısa vadeli: Anlık fayda görünce harekete geçer
    "IVR": 49,  # Orta: Ne aşırı zevkçi ne kısıtlayıcı
}

HOFSTEDE_TURKEY_PROMPT = (
    "\n[KÜLTÜREL BAĞLAM — TÜRKİYE]\n"
    "- Belirsiz fiyat veya net olmayan taahhüt gördüğünde güvenmezsin (UAI=85).\n"
    "- Arkadaş/aile tavsiyesi veya referans olmadan büyük kararlar almakta zorlanırsın (IDV=37).\n"
    "- Güvenilir marka, kurumsal garanti veya tanıdık isim önemlidir (PDI=66).\n"
    "- Hızlı fayda görmeden uzun vadeli ödeme yapmaktan kaçınırsın (LTO=46)."
)

SES_PROFILES: Dict[str, Dict[str, Any]] = {
    "AB": {
        "label": "AB — Üst Grup (%21.5)",
        "profile": "Yüksek eğitimli, üst düzey yönetici veya serbest meslek. Lüks/konfor odaklı, prestij hassas.",
        "price_sensitivity_range": (1, 4),
        "digital_confidence_range": (7, 10),
    },
    "C1": {
        "label": "C1 — Üst-Orta Grup (%22.4)",
        "profile": "Profesyonel meslek sahibi, orta düzey yönetici. Uzun vadeli yatırım ve lokasyon öncelikli.",
        "price_sensitivity_range": (3, 6),
        "digital_confidence_range": (6, 9),
    },
    "C2": {
        "label": "C2 — Alt-Orta Grup (%32.5)",
        "profile": "Memur, teknik personel, küçük esnaf. Fiyat-fayda dengesi öncelikli, fiyat duyarlı.",
        "price_sensitivity_range": (6, 9),
        "digital_confidence_range": (4, 7),
    },
    "DE": {
        "label": "DE — Alt Grup (%23.6)",
        "profile": "Vasıfsız işçi, emekli. Temel ihtiyaç odaklı, çok yüksek fiyat duyarlılığı.",
        "price_sensitivity_range": (8, 10),
        "digital_confidence_range": (2, 5),
    },
}

# ── TÜAD 2025 SES Kota Yönetimi ──────────────────────────────────────────────
# Türkiye nüfus dağılımı (TÜAD 2025 verileri, yaklaşık oranlar)
TUAD_SES_QUOTA: Dict[str, float] = {
    "AB": 0.215,   # Üst grup — %21.5
    "C1": 0.224,   # Üst-orta — %22.4
    "C2": 0.325,   # Alt-orta — %32.5 (en büyük dilim)
    "DE": 0.236,   # Alt grup — %23.6
}

def apply_ses_quota(
    panel_size: int,
    target_ses: Optional[List[str]] = None,
) -> Dict[str, int]:
    """TÜAD 2025 nüfus oranlarına göre SES başına panel kota hesaplar."""
    quota_groups = target_ses or list(TUAD_SES_QUOTA.keys())
    weights = {ses: TUAD_SES_QUOTA.get(ses, 0.25) for ses in quota_groups}
    total_w = sum(weights.values())

    # Ham hesaplama
    counts: Dict[str, int] = {
        ses: max(1, round(panel_size * w / total_w))
        for ses, w in weights.items()
    }

    # Toplam düzeltmesi — yuvarlama hatası varsa en büyük grubu ayarla
    diff = panel_size - sum(counts.values())
    if diff != 0:
        dominant = max(counts, key=lambda k: weights[k])
        counts[dominant] = max(1, counts[dominant] + diff)

    return counts

def get_turkey_behavior_context(persona: Any, question: Any) -> str:
    """Türkiye pazarı tüketicilerinin yerel işlem ve alışveriş davranış reflekslerini döner.
    İçerik: C2C pazarlık, enflasyon hedging/taksit, kargo sepet terk (OSCA).
    """
    question_text = getattr(question, "question", "").lower()
    question_tags = getattr(question, "tags", []) or []
    
    turkey_context = ""
    
    # 1. Fiyat / Ödeme / Bütçe İlgili Sorular
    if "fiyat" in question_text or "pricing" in question_tags:
        pazarlik_txt = (
            "\n[YEREL REFLEKS — C2C PAZARLIK]\n"
            "Türkiye pazarı alışkanlıkların gereği satıcının fiyatına karşı doğrudan 'Teklif Ver' veya pazarlık yap. "
            "Bütçeni korumak için en az %30 indirim talep et."
        )
        taksit_txt = (
            "\n[YEREL REFLEKS — ENFLASYON HEDGING VE TAKSİT]\n"
            "Yüksek enflasyon ortamında paranın zaman maliyetini hesaplayarak taksitli ödeme opsiyonunu tercih et. "
            "Kredi kartı limit doluluğun %50 seviyelerinde, asgari ödeme yapmaktan çekiniyorsun."
        )
        turkey_context = pazarlik_txt + taksit_txt
        
    # 2. Kargo / Teslimat / Nakliye İlgili Sorular (S-O-R Sepet Terk)
    elif any(marker in question_text for marker in ["kargo", "teslimat", "shipping"]):
        traits = getattr(persona, "traits", {}) or {}
        n_val = traits.get("Neuroticism", 50) / 10.0
        c_val = traits.get("Conscientiousness", 50) / 10.0
        
        # Logistic S-O-R model matching user-approved Turkey parameters
        logit = -1.5 + 0.4 * 8.0 + 0.2 * n_val - 0.1 * c_val
        prob_abandon = 1.0 / (1.0 + math.exp(-logit))
        
        if prob_abandon > 0.5:
            turkey_context = (
                f"\n[YEREL REFLEKS — S-O-R SEPET TERK (OSCA)]\n"
                f"Beklenmedik kargo ücreti sende ciddi bir hayal kırıklığı ve finansal kayıp algısı yarattı. "
                f"Sepet terk etme olasılığın çok yüksek ({prob_abandon:.2f}). Alışverişi tamamlamadan çıkacağını söyle."
            )
            
    return turkey_context
