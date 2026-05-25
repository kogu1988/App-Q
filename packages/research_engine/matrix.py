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

    # 3. Aşama: Kotaları bireysel görev (taslak) objelerine aç
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
