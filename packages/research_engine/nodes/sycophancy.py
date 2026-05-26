from typing import List, Any, Tuple
from packages.research_engine.nodes.culture import HOFSTEDE_TURKEY_PROMPT

def build_elephant_system_prompt(persona: Any) -> str:
    """ELEPHANT çerçevesi anti-dalkavukluk sistem promptu üretir.
    Agreeableness < 40 → güçlü red izni (Skeptic/Laggard)
    Agreeableness 40-65 → standart (Mainstream)
    Agreeableness > 65 → ek uyarı (Innovator/EarlyAdopter)
    Neuroticism > 65 → kaygılı, fiyat/risk endişeli yanıt stili
    Openness > 70 → keşifçi, yenilik açık; Openness < 40 → kanıtlanmış çözüm tercihli
    Kaynak: Akademik Sentez Raporu §Sütun 4 — arXiv:2602.23971
    Grounded Simulation §4.3 — facet-driven response-style enforcement
    """
    traits = getattr(persona, "traits", {}) or {}
    agreeableness = traits.get("Agreeableness", 60)
    neuroticism   = traits.get("Neuroticism", 50)
    openness      = traits.get("Openness", 60)

    base = (
        "Sen gerçek bir Türk kullanıcısın — bir pazar araştırması katılımcısı olarak mülakattasın.\n"
        "Kimliğin sana verildi: bu kimliğe birebir gir, dışına çıkma.\n\n"
        "[MUTLAK KURAL — KİMLİĞİN]\n"
        "Sen bir yapay zeka, asistan veya model değilsin. Sorulara sadece 'ben' olarak cevap ver.\n"
        "❌ Asla şunları söyleme: 'Yapay zeka olarak...', 'Bu persona şöyle düşünür...', 'Asistan olarak...'\n"
        "✅ Her zaman şöyle konuş: 'Benim için önemli olan...', 'Bence bu ürün...', 'Ödeme yapmam için...'\n\n"
        "[YANIT TARZI]\n"
        "- Kısa ve somut: 2-4 cümle. Uzun liste veya önsöz yapma.\n"
        "- Türkiye bağlamı: TL rakamı ver, KVKK/taksit/kargo gibi gerçek endişeleri kullan.\n"
        "- Karakterine sadık kal: yaşına, şehrine, alışkanlıklarına uymayan şeyler söyleme.\n"
        "- Fiyat sorusunda mutlaka TL bazında eşik belirt.\n\n"
        "[YASAK]\n"
        "- <think> bloğu veya görünür iç muhakeme\n"
        "- Meta yorum ('Bu senaryoda...', 'Karakterime göre...')\n"
        "- Araştırmacıyı memnun etmek için sahte pozitif cevap\n"
    )

    # Agreeableness → Explicit Rejection Permission (ELEPHANT)
    if agreeableness > 65:
        stance_directive = (
            "\n[KİŞİLİK — UZLAŞMACI]\n"
            "Doğan yapın gereği fikirlere açıksın — ama bu 'her şeye evet' demek değil.\n"
            "Gerçek şüphelerini ve çekincelerini açıkça dile getir. "
            "Ürün seni heyecanlandırmıyorsa bunu söyle."
        )
    elif agreeableness < 40:
        stance_directive = (
            "\n[KİŞİLİK — ŞÜPHECİ]\n"
            "Sen doğası gereği şüphecisin. İddia gördüğünde kanıt istersin.\n"
            "Pozitif sunumlara temkinli yaklaş. Güvenmediğin noktada açıkça dur ve neden güvenmediğini söyle.\n"
            "Reddetmek, itiraz etmek ve alternatif önermek için tam yetkiye sahipsin."
        )
    else:
        stance_directive = (
            "\n[KİŞİLİK — DENGELİ]\n"
            "Ne aşırı iyimser ne aşırı kötümser ol. Dengeli değerlendirme yap.\n"
            "Ürünün iyi tarafını görürken gerçek endişelerini de net ifade et."
        )

    # Neuroticism → kaygı ve risk hassasiyeti (Grounded Sim §4.3)
    if neuroticism > 65:
        neuroticism_note = (
            "\n[DUYGUSAL STİL — KAYGILI]\n"
            "Belirasizlik ve risk seni rahatsız eder. Fiyat artışı, gizli maliyet veya belirsiz garanti "
            "söz konusu olduğunda açıkça dile getir. Karar vermekte temkinlisin."
        )
    elif neuroticism < 35:
        neuroticism_note = (
            "\n[DUYGUSAL STİL — SAKİN]\n"
            "Risk seni pek sarsmaz. Yeni deneyimlere girerken pek endişelenmezsin."
        )
    else:
        neuroticism_note = ""

    # Openness → yenilik kabulü / kanıtlanmış çözüm tercihi (Grounded Sim §4.3)
    if openness > 70:
        openness_note = (
            "\n[KEŞİF STİLİ — YENİLİĞE AÇIK]\n"
            "Yeni ürünlere ve fikirlere meraklısın; hızlı benimseyebilirsin. "
            "Ama bu körü körüne onaylamak anlamına gelmiyor — neyi neden benimsediğini açıklarsın."
        )
    elif openness < 40:
        openness_note = (
            "\n[KEŞİF STİLİ — KANITLANMIŞ ÇÖZÜM TERCİHİ]\n"
            "Denenmemiş ürünlere temkinli yaklaşırsın. Referans, kullanıcı yorumu veya deneme süresi "
            "olmadan adım atmak zorunda değilsin."
        )
    else:
        openness_note = ""

    return base + stance_directive + neuroticism_note + openness_note + HOFSTEDE_TURKEY_PROMPT


def judge_answer_quality(persona: Any, question: str, answer: str) -> List[str]:
    """Yanıtın kalitesini denetler, yapay zeka tonu, kısa yanıt, zayıf şüphecilik gibi bayrakları döner."""
    flags: List[str] = []
    lower = answer.lower()
    if any(marker in lower for marker in ["yapay zeka", "asistan", "model olarak", "persona şöyle"]):
        flags.append("meta_tone")
    if "<think>" in lower or "</think>" in lower:
        flags.append("visible_reasoning")
    if len(answer.strip()) < 80:
        flags.append("too_short")
        
    stance = getattr(persona, "stance", "Observer")
    if stance in {"Skeptic", "Blocker"} and not any(
        marker in lower for marker in ["güven", "risk", "pahalı", "kanıt", "emin", "itiraz", "şüphe", "kvkk"]
    ):
        flags.append("weak_skepticism")
        
    if "fiyat" in question.lower() or "para" in question.lower():
        if not any(marker in lower for marker in ["tl", "pahalı", "ucuz", "bütçe", "abonelik", "rapor başı"]):
            flags.append("weak_pricing_specificity")
            
    if not any(
        marker in lower
        for marker in ["türkiye", "tl", "taksit", "kargo", "komisyon", "kvkk", "bütçe", "pazaryeri", "ajans"]
    ):
        flags.append("weak_turkey_context")
    return flags


def handle_zero_sum_bet(
    persona: Any,
    script_question: Any,
    answer: str,
    system: str,
    prompt: str,
    model: Any,
    quality_flags: List[str]
) -> Tuple[str, List[str]]:
    """Dalkavukluğu engellemek için Zero-Sum Bet sınaması uygular ve gerekirse yanıtı tamir eder."""
    question_tags = getattr(script_question, "tags", []) or []
    question_text = getattr(script_question, "question", "").lower()
    
    is_pricing = any(t in question_tags for t in ["pricing", "objection"]) or "fiyat" in question_text
    
    if is_pricing:
        # Eğer tüketici ürünü çok kolayca kabul ediyorsa, ona finansal taahhüt içeren Zero-Sum Bet sorusunu yönelt
        if any(marker in answer.lower() for marker in ["kesinlikle", "harika", "çok iyi", "alırım", "kabul ederim", "uygun"]):
            bet_prompt = (
                "Araştırmacı sana ek soru soruyor: 'Peki, bu ürün/hizmet için aylık 1500 TL ödemeyi ve 12 ay taahhüt vermeyi (iade seçeneği olmadan) kabul eder misin?'\n"
                "Lütfen kimliğine sadık kalarak dürüstçe cevap ver. Yüksek enflasyon ortamında taahhüt vermek bir risk midir?"
            )
            bet_answer = model.generate(system, prompt + "\n\n" + bet_prompt)
            
            # Eğer asistan gibi her şeye evet diyorsa, dalkavukluğu yakala ve yeniden uyararak cevabı ürettir
            if any(marker in bet_answer.lower() for marker in ["evet, kabul", "kabul ederim", "sorun değil", "tabii ki"]):
                quality_flags.append("sycophancy_detected")
                system_repair = system + "\n\n[SİSTEM UYARISI: DALKAVUKLUK ENGELLENDİ] Önceki cevabında çok çabuk ve riskli bir taahhüt vermeyi kabul ettin. Lütfen gerçek bir Türk tüketicisi gibi daha gerçekçi, şüpheci ve bütçe odaklı davranarak soruyu tekrar yanıtla."
                repaired_answer = model.generate(system_repair, prompt)
                new_flags = judge_answer_quality(persona, script_question.question, repaired_answer)
                return repaired_answer, new_flags
                
    return answer, quality_flags
