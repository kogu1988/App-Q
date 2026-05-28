import math

# Rogers Diffusion of Innovations (AMP Codes) Dağılımı
P_ROGERS = {
    "Innovator": 0.15,      # AMP_01
    "EarlyAdopter": 0.35,   # AMP_02
    "Mainstream": 0.20,     # AMP_03
    "Laggard": 0.15,        # AMP_04
    "Skeptic": 0.15,        # AMP_05
}

# TÜAD 2025 SES (Sosyo-Ekonomik Statü) Dağılımı
P_SES = {
    "AB": 0.215,
    "C1": 0.224,
    "C2": 0.325,
    "DE": 0.236,
}

# TÜİK 2024 Yaş Dağılımı (Yetişkin İnternet Kullanıcıları)
P_AGE = {
    "18-24": 0.15,
    "25-34": 0.30,
    "35-44": 0.25,
    "45-54": 0.20,
    "55+": 0.10,
}

# TÜİK Cinsiyet Dağılımı
P_GENDER = {
    "Kadın": 0.50,
    "Erkek": 0.50,
}

# Stance Diversity sabitleri (adversarial.py §bias_audit ile senkron)
MIN_STANCE_COUNT    = 3     # Panelde bulunması gereken minimum farklı stance sayısı
MIN_PER_STANCE      = 1     # Her stance'tan en az bu kadar persona
SKEPTIC_REQUIRED    = True  # Skeptic her panelde zorunlu (dalkavukluğa karşı anti-sycophancy guard)


def calculate_joint_probability_matrix() -> dict[tuple[str, str], float]:
    """
    Rogers x SES birleşik olasılık matrisini (M_Cohort) hesaplar.
    """
    matrix = {}
    for stance, p_stance in P_ROGERS.items():
        for ses, p_ses in P_SES.items():
            matrix[(stance, ses)] = p_stance * p_ses
    return matrix

def allocate_cohort_matrix(N: int) -> list[dict]:
    """
    Verilen N persona sayısı için Largest Remainder (En Büyük Kalan) metodunu
    kullanarak matris hücrelerine deterministik tamsayı (integer) kotalar atar.
    Geriye, her elemanı bir persona için {"stance": ..., "ses_group": ...} olan N boyutlu liste döner.
    """
    if N <= 0:
        return []

    matrix = calculate_joint_probability_matrix()
    
    # 1. Aşama: Tam kısımları (integer) hesapla ve kalanları bul
    allocations = {key: 0 for key in matrix}
    remainders = {}
    
    total_allocated = 0
    for key, prob in matrix.items():
        exact_value = prob * N
        integer_part = math.floor(exact_value)
        allocations[key] = integer_part
        remainders[key] = exact_value - integer_part
        total_allocated += integer_part
        
    # 2. Aşama: Kalan (Remainder) ataması (Largest Remainder)
    remaining_slots = N - total_allocated
    
    # Kalanları büyükten küçüğe sırala
    sorted_remainders = sorted(remainders.items(), key=lambda x: x[1], reverse=True)
    
    for i in range(remaining_slots):
        key = sorted_remainders[i][0]
        allocations[key] += 1
    # Skeptic garantisi: küçük panellerde Skeptic sıfıra düşebilir (anti-sycophancy guard)
    # N >= 5 ise en az 1 Skeptic zorunlu — baskın stanceden 1 yeri Skeptic'e ver
    if N >= 5:
        skeptic_total = sum(v for (s, _), v in allocations.items() if s == "Skeptic")
        if skeptic_total == 0:
            # Largest Remainder ile en fazla atanan stance hücresinden 1 al
            dominant_key = max(
                [(k, v) for k, v in allocations.items() if k[0] != "Skeptic"],
                key=lambda x: x[1]
            )[0]
            if allocations[dominant_key] > 0:
                allocations[dominant_key] -= 1
                # Skeptic için mevcut SES'leri kullan — en yüksek sesli Skeptic hücresi
                skeptic_keys = [k for k in allocations if k[0] == "Skeptic"]
                if skeptic_keys:
                    allocations[skeptic_keys[0]] += 1

    assigned_personas = []
    for (stance, ses), count in allocations.items():
        for _ in range(count):
            big_five_constraints = calculate_big_five_constraints(stance, ses)
            assigned_personas.append({
                "stance": stance,
                "ses_group": ses,
                "big_five_constraints": big_five_constraints
            })
            
    # 4. Aşama: Bağımsız Demografik Stratifikasyon (Yaş ve Cinsiyet)
    # TUIK kotalarına göre listeyi boyayacağız (deterministik round-robin/largest remainder)
    age_allocations = {k: math.floor(v * N) for k, v in P_AGE.items()}
    age_remainders = {k: (v * N) - math.floor(v * N) for k, v in P_AGE.items()}
    age_remaining = N - sum(age_allocations.values())
    for k, _ in sorted(age_remainders.items(), key=lambda x: x[1], reverse=True)[:age_remaining]:
        age_allocations[k] += 1
        
    gender_allocations = {k: math.floor(v * N) for k, v in P_GENDER.items()}
    gender_remainders = {k: (v * N) - math.floor(v * N) for k, v in P_GENDER.items()}
    gender_remaining = N - sum(gender_allocations.values())
    for k, _ in sorted(gender_remainders.items(), key=lambda x: x[1], reverse=True)[:gender_remaining]:
        gender_allocations[k] += 1

    # Apply to assigned_personas list
    age_pool = [age for age, count in age_allocations.items() for _ in range(count)]
    gender_pool = [gen for gen, count in gender_allocations.items() for _ in range(count)]
    
    # Sort them to distribute evenly
    age_pool.sort()
    gender_pool.sort(reverse=True) # Mix it up
    
    for i, p in enumerate(assigned_personas):
        p["age_group"] = age_pool[i] if i < len(age_pool) else "25-34"
        p["gender"] = gender_pool[i] if i < len(gender_pool) else "Kadın"
        
    return assigned_personas

def calculate_big_five_constraints(stance: str, ses: str) -> dict[str, str]:
    """
    Matris koordinatına göre psikometrik NEO-PI-R / OCEAN sınırlarını belirler.
    Hard Constraint (Katı Sınır) oluşturmak için string prompt kuralları döner.
    """
    constraints = {}
    
    # Openness (O)
    if stance == "Innovator":
        constraints["openness"] = "80-100 (Çok Yüksek: Yeniliğe ve risk almaya iştahlı)"
    elif stance == "EarlyAdopter":
        constraints["openness"] = "60-80 (Yüksek: Mantıklı kanıt gördüğünde yeniliğe açık)"
    elif stance == "Laggard":
        constraints["openness"] = "0-30 (Çok Düşük: Geleneksel, değişime aktif direnç gösteren)"
    else:
        constraints["openness"] = "40-60 (Orta)"

    # Conscientiousness (C)
    if ses in ("AB", "C1"):
        constraints["conscientiousness"] = "70-100 (Yüksek: Planlı, organize, hesaplı)"
    else:
        constraints["conscientiousness"] = "30-60 (Orta-Düşük: Daha anlık tepkiler veren)"

    # Agreeableness (A)
    if stance == "Skeptic":
        constraints["agreeableness"] = "0-30 (Çok Düşük: Doğrudan reddeden, dalkavukluğa kapalı, cynic bariyer)"
    elif stance == "Innovator":
        constraints["agreeableness"] = "30-50 (Düşük: Kendi doğrusunu savunan, ürünü zorlayan)"
    else:
        constraints["agreeableness"] = "50-70 (Orta: Yapıcı ama körü körüne onaylamayan)"

    # Neuroticism (N)
    if stance == "Skeptic" or ses == "DE":
        constraints["neuroticism"] = "70-100 (Yüksek: Finansal kayıp veya güvenlik korkusu yüksek)"
    elif stance == "Innovator" and ses == "AB":
        constraints["neuroticism"] = "0-30 (Çok Düşük: Finansal kaygısı olmayan, özgüvenli)"
    else:
        constraints["neuroticism"] = "40-60 (Orta)"

    # Extroversion (E)
    if stance in ("EarlyAdopter", "Innovator"):
        constraints["extroversion"] = "70-100 (Yüksek: Dışa dönük, sosyal referans olmayı seven)"
    else:
        constraints["extroversion"] = "40-60 (Orta)"

    return constraints


# ── Stance Diversity Doğrulaması ───────────────────────────────────────────────

def stance_balance_score(personas: list[dict]) -> float:
    """Shannon entropi tabanlı stance denge skoru hesaplar (0.0-1.0).

    1.0 = mükemmel denge (tüm stanceler eşit dağılım)
    0.0 = tekil stance (hiç çeşitlilik yok)

    Grounded Simulation §bias_audit: stance diversity F1 üzerindeki en büyük
    tek driver (ΔF1 = −0.582).
    """
    if not personas:
        return 0.0

    counts: dict[str, int] = {}
    for p in personas:
        stance = p.get("stance", "Unknown")
        counts[stance] = counts.get(stance, 0) + 1

    n = len(personas)
    k = len(P_ROGERS)  # Maksimum olası stance sayısı

    # Shannon entropi H = -Σ p_i * log(p_i)
    entropy = 0.0
    for count in counts.values():
        p_i = count / n
        if p_i > 0:
            entropy -= p_i * math.log2(p_i)

    # Maksimum entropi log2(k) ile normalize et → [0, 1]
    max_entropy = math.log2(k) if k > 1 else 1.0
    return round(entropy / max_entropy, 4)


def validate_stance_diversity(personas: list[dict]) -> dict:
    """Panel persona listesinin stance çeşitliliğini doğrular.

    adversarial.py'deki bias_audit raporlama sonrası değil,
    panel oluşturulduktan hemen sonra çağrılır — yani sorun kaynağında yakalanır.

    Returns:
        {
            "valid": bool,           # True = panel geçerli
            "stance_count": int,     # Farklı stance sayısı
            "balance_score": float,  # Shannon entropy 0-1
            "issues": list[str],     # Bulunan sorunlar
            "stance_distribution": dict,  # Stance → persona sayısı
            "has_skeptic": bool,     # Anti-sycophancy guard
        }
    """
    issues: list[str] = []

    if not personas:
        return {
            "valid": False,
            "stance_count": 0,
            "balance_score": 0.0,
            "issues": ["Panel boş — persona bulunamadı."],
            "stance_distribution": {},
            "has_skeptic": False,
        }

    # Stance dağılımını hesapla
    distribution: dict[str, int] = {}
    for p in personas:
        stance = p.get("stance", "Unknown")
        distribution[stance] = distribution.get(stance, 0) + 1

    stance_count = len(distribution)
    balance = stance_balance_score(personas)
    has_skeptic = "Skeptic" in distribution

    # Minimum stance sayısı kontrolü
    if stance_count < MIN_STANCE_COUNT:
        issues.append(
            f"Yetersiz stance çeşitliliği: {stance_count} farklı stance "
            f"(minimum: {MIN_STANCE_COUNT}). "
            "Stance diversity F1 üzerinde en büyük single driver (ΔF1 = −0.582)."
        )

    # Skeptic zorunluluğu (anti-sycophancy guard)
    if SKEPTIC_REQUIRED and not has_skeptic:
        issues.append(
            "Panel'de 'Skeptic' stance eksik. "
            "Skeptic, dalkavukluğu engelleyen zorunlu anti-sycophancy bariyer persona'sıdır. "
            "Modelin onaylama sapmasını engeller."
        )

    # Aşırı baskın stance kontrolü (%60 üstü)
    n = len(personas)
    for stance, count in distribution.items():
        ratio = count / n
        if ratio > 0.60 and n >= 3:
            issues.append(
                f"'{stance}' stance panel'in %{ratio:.0%}'ini oluşturuyor — "
                "aşırı baskınlık echo chamber riskini artırır."
            )

    # Shannon denge skoru düşükse uyar
    if balance < 0.5 and n >= 3:
        issues.append(
            f"Stance denge skoru düşük: {balance:.2f} (Shannon entropy tabanlı). "
            "0.5 üstü önerilir — gerçekçi pazar çeşitliliğini yansıtmaz."
        )

    return {
        "valid": len(issues) == 0,
        "stance_count": stance_count,
        "balance_score": balance,
        "issues": issues,
        "stance_distribution": distribution,
        "has_skeptic": has_skeptic,
    }
