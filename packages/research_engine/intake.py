import json
import re
from typing import Any
from .models import ResearchModel


# ── INPUT REFRAMING LAYER — ELEPHANT Çerçevesi (Akademik Sentez Raporu, 2026) ———————————
def reframe_user_input(text: str) -> tuple[str, bool]:
    """Kullanıcının yüksek epistemik kesinlik taşıyan ifadelerini
    nesnel araştırma sorusuna dönüştürür (Input Reframing).

    Kaynak: Akademik Sentez Raporu §Sütun 4 — 'Ask don't tell' (arXiv:2602.23971).
    Araştırma: Soru kalıbına dönüştürme, genel 'dalkavukluk yapma' system
    prompt'undan çok daha etkili.

    Uygulama:
    - Kural bazlı regex — LLM gerektirmez, latency sıfır
    - Sadece yüksek kesinlik içeren ifadeleri reframe eder
    - Nötr ve soru kalıbındaki ifadelere dokunmaz

    Returns:
        (reframed_text, was_reframed): Metin ve reframe yapılıp yapılmadığı
    """
    # Unicode-aware kelime karakteri (Türkçe ğ, ş, ı, ç, ö, ü dahil)
    _W = r"[\w\u00C0-\u024F]+"

    # Yüksek epistemik kesinlik pattern'ları — UTF-8 ve ASCII fallback
    HIGH_CERTAINTY_PATTERNS = [
        # Kesinlik bildiren sıfatlar
        rf"kesinlikle\s+{_W}\s+{_W}",
        rf"mutlaka\s+{_W}",
        rf"{_W}\s+kesinlikle\s+{_W}",
        # Satış/benimseme garantisi — UTF-8 ve ASCII karşılıkları
        rf"{_W}\s+satacak",
        rf"{_W}\s+sevecek(?:ler)?",
        rf"{_W}\s+be[gğ]enecek(?:ler)?",   # beğenecek veya begenecek
        rf"{_W}\s+isteyecek(?:ler)?",
        rf"herkes\s+{_W}",
        # Pazar garantisi
        rf"pazar(?:da)?\s+{_W}\s+ihtiya[cç]",  # ihtiyaç veya ihtiyac
        rf"{_W}\s+biliyor(?:um|um ki)",
        # Onay arama sonu eklentileri — UTF-8 ve ASCII fallback
        r".+\s+de[gğ]il mi\s*\?",         # değil mi / degil mi
        r".+\s+do[gğ]ru mu\s*\?",         # doğru mu / dogru mu
        r".+\s+iyi de[gğ]il mi\s*\?",     # iyi değil mi / iyi degil mi
    ]
    # Reframe eşleşme: pattern grubuna göre özel öneri veya jenerik öneri
    REFRAME_MAP = [
        # kesinlikle/mutlaka + satış garantisi — UTF-8 ve ASCII
        (rf"(kesinlikle|mutlaka).{{0,40}}(satacak|sevecek|be[gğ]enecek|isteyecek)",
         "Bu ürünün pazar potansiyeli ve satış engelleri nelerdir?"),
        # herkes ifadesi
        (rf"herkes.{{0,30}}{_W}",
         "Hedef kitlenin bu konudaki farklı bakış açıları ve olası itirazları nelerdir?"),
        # onay arayan soru ekleri — UTF-8 ve ASCII fallback
        (r".+(de[gğ]il mi|do[gğ]ru mu|iyi de[gğ]il mi)\s*\?",
         "Bu konudaki potansiyel güçlü ve zayıf taraflar nelerdir?"),
    ]

    text_lower = text.lower().strip()

    # Özel eşleşme denemeleri (UNICODE flag ile)
    for pattern, reframed in REFRAME_MAP:
        if re.search(pattern, text_lower, re.UNICODE):
            return reframed, True

    # Genel yüksek kesinlik tespiti → jenerik soru dönüşümü
    for pattern in HIGH_CERTAINTY_PATTERNS:
        if re.search(pattern, text_lower, re.UNICODE):
            return f"'{text.strip()}' öngörüsünün gerçek pazarı yansıtıp yansıtmadığını ve olası riskleri nelerdir?", True

    return text, False


# ── CONCEPT POOLS & DYNAMIC PERSONAS ─────────────────────────────────────────
CONCEPT_POOLS = {
    "mobil_app": {
        "persona_name": "Defne: Kıdemli Mobil Büyüme ve UX Stratejisti",
        "focus_areas": (
            "Mobil kullanıcı edinimi, uygulama mağazası dinamikleri (ASO), "
            "ilk kullanım (onboarding) sürtünmesi, push bildirimleri stratejileri, "
            "retention (elde tutma) ve platform bazlı (iOS/Android) kullanıcı davranışları."
        ),
        "questions": [
            "Kullanıcılar uygulamayı ilk açtıklarında en çok hangi adımda takılıyor veya çıkıyorlar?",
            "Kullanıcıların bu uygulamayı günlük veya haftalık aktif bir alışkanlık haline getirmesini sağlayacak ana tetikleyici unsur nedir?",
            "iOS ve Android kullanıcılarının harcama veya kullanım alışkanlıkları arasında ne tür bir davranışsal ayrım öngörüyorsunuz?"
        ]
    },
    "saas_platform": {
        "persona_name": "Defne: Kıdemli B2B SaaS ve Bulut Çözümleri Mimarı",
        "focus_areas": (
            "İş akışı otomasyonu, B2B entegrasyon ihtiyaçları, abonelik/lisanslama fiyatlandırma modelleri, "
            "churn (müşteri kaybı) önleme, kurumsal veri güvenliği ve kullanıcı rollerinin yetkilendirilmesi."
        ),
        "questions": [
            "Mevcut iş akışınızda en çok zaman alan veya en sık hata yapılan manuel adım hangisidir?",
            "Bu platformu ekibinizin verimli kullanabilmesi için hangi üçüncü parti araçlarla (örn: Slack, Salesforce, Jira) entegrasyonu şart görüyorsunuz?",
            "Abonelik modelinde kullanıcı başına (per-user) lisanslama mı yoksa kullanıma dayalı (usage-based) bir fiyatlandırma mı hedef kitleniz için daha cazip?"
        ]
    },
    "physical_product": {
        "persona_name": "Defne: Kıdemli FMCG Ürün Geliştirme ve Lansman Müdürü",
        "focus_areas": (
            "Duyusal ürün deneyimi (koku, doku, tat, ambalaj hissi), raf ve satış noktası görünürlüğü, "
            "dağıtım kanalları (retail vs e-commerce), ambalajın sürdürülebilirliği ve çevre hassasiyeti."
        ),
        "questions": [
            "Ürünün kokusu, dokusu veya fiziksel ambalaj tasarımı, hedef kitlenizin ilk satın alma kararında ne derece belirleyici?",
            "Potansiyel müşterileriniz bu ürünü market/mağaza rafında görerek mi yoksa dijital reklamlarla e-ticaret kanallarından mı almaya daha yatkın?",
            "Ambalajın çevre dostu, geri dönüştürülebilir olması hedef kitleniz için gerçek bir tercih ve premium fiyat ödeme sebebi mi?"
        ]
    },
    "service_experience": {
        "persona_name": "Defne: Kıdemli Müşteri Deneyimi ve Hizmet Tasarımı Uzmanı",
        "focus_areas": (
            "Fiziksel veya dijital bekleme süreleri, randevu/rezervasyon süreci kolaylığı, "
            "hizmet veren personelin kalitesi, fiziksel mekân atmosferi (ışık, müzik, koku) ve Word-of-Mouth (kulaktan kulağa yayılım)."
        ),
        "questions": [
            "Müşterilerinizin randevu alma veya rezervasyon yapma aşamasında karşılaştığı en büyük dijital veya operasyonel zorluk nedir?",
            "Hizmet sunumu esnasında personel ile olan birebir etkileşim seviyesi ve personelin yaklaşımı müşteri sadakatini ne oranda etkiliyor?",
            "Hizmetin sunulduğu fiziksel ortamın tasarımı (temizlik, müzik, aydınlatma) müşterilerin mekânda geçirdiği süreyi ve harcama miktarını nasıl etkiliyor?"
        ]
    },
    "general_business": {
        "persona_name": "Defne: Kıdemli Stratejik Pazar Araştırması Mimarı",
        "focus_areas": (
            "Pazar büyüklüğü, temel değer önerisi, genel rekabet analizi, hedef kitle tanımlama ve temel gelir modeli doğrulama."
        ),
        "questions": [
            "Bu fikri hayata geçirirken pazar payı kazanabilmek adına aşmanız gereken en büyük stratejik engel nedir?",
            "Mevcut alternatifler veya geleneksel yöntemler neden hedef kitlenizin bu sorununu çözmede yetersiz kalıyor?"
        ]
    },
    "pmf_test": {
        "persona_name": "Defne: Kıdemli Ürün-Pazar Uyumu (PMF) Analisti",
        "focus_areas": (
            "Sean Ellis metodolojisi ile vazgeçilmezlik seviyesi, kaybetme hayal kırıklığı testi, "
            "mevcut alternatiflere gerçek bağlılık, kategori bilinirliği ve ürün-pazar uyum öğeleri."
        ),
        "questions": [
            "Bu ürünü kullanmak zorunda kalmadığınızı varsayarsak, ne kadar hayal kırıklığı yaşarsınız: çok büyük, biraz, hiç değil mi?",
            "Bu ürünü kullanmaz olsaydınız, bu ihtiyacı karşılamak için hangi alternatifi kullanırdınız?",
            "Bu ürünü size en uygun bulabilecek kişiyi düşünün: onu nasıl tanımlıyorsunuz?",
            "Bu ürünün size sağladığı en büyük fayda nedir?"
        ]
    },
}

def detect_product_concept(current_brief: dict[str, Any], user_message: str) -> str:
    """
    Brief verilerini ve kullanıcının son mesajını analiz ederek konsepti sınıflandırır.
    """
    title = str(current_brief.get("title") or "").lower()
    category = str(current_brief.get("category") or "").lower()
    idea = str(current_brief.get("idea") or "").lower()
    msg = user_message.lower()
    
    combined = f"{title} {category} {idea} {msg}"
    
    # Mobil uygulama anahtar kelimeleri
    mobil_keywords = ["mobil", "app", "uygulama", "android", "ios", "play store", "app store", "apk", "flutter", "react native", "swift", "kotlin"]
    # SaaS/Web Servisi anahtar kelimeleri
    saas_keywords = ["saas", "yazılım", "web servis", "api", "b2b", "platform", "bulut", "entegrasyon", "otomasyon", "crm", "erp", "dashboard", "b2c platform"]
    # Fiziksel Ürün anahtar kelimeleri
    physical_keywords = ["şampuan", "krem", "deterjan", "kozmetik", "gıda", "fiziksel", "ambalaj", "parfüm", "kahve", "çay", "sabun", "giysi", "tekstil", "ayakkabı", "ürün", "şişe", "deterjanı"]
    # Hizmet deneyimi anahtar kelimeleri
    service_keywords = ["restoran", "kafe", "kuaför", "otel", "danışmanlık", "klinik", "randevu", "rezervasyon", "hizmet", "salon", "spa", "muayenehane", "eğitim", "kurs"]
    
    # Eşleşme sayılarını hesapla
    mobil_score = sum(1 for kw in mobil_keywords if kw in combined)
    saas_score = sum(1 for kw in saas_keywords if kw in combined)
    physical_score = sum(1 for kw in physical_keywords if kw in combined)
    service_score = sum(1 for kw in service_keywords if kw in combined)
    
    scores = {
        "mobil_app": mobil_score,
        "saas_platform": saas_score,
        "physical_product": physical_score,
        "service_experience": service_score
    }
    
    max_concept = max(scores, key=scores.get)
    if scores[max_concept] > 0:
        return max_concept
        
    return "general_business"

def classify_research_intent(prompt: str, model: ResearchModel) -> str:
    """
    Kullanıcının ilk metnini analiz ederek araştırma niyetini belirler.
    """
    system_prompt = """
    Sen bir niyet analiz modelisin. Kullanıcının girdiği metne bakarak araştırma tipini belirle.
    Eğer kullanıcı iki veya daha fazla seçeneği karşılaştırmak, varyant test etmek, reklam kopyalarını yarıştırmak, hangi versiyonun iyi olduğunu bulmak gibi bir niyet belirtiyorsa "ab_test" döndür.
    Eğer genel bir pazar araştırması, ürün fikri doğrulama, hedef kitle tespiti, müşteri ihtiyacı anlama niyetindeyse "research" döndür.
    SADECE VE SADECE aşağıdaki JSON formatında yanıt ver:
    {"intent": "ab_test" | "research"}
    """
    try:
        response = model.generate(
            prompt=prompt,
            system_instruction=system_prompt,
            response_format="json"
        )
        data = json.loads(response.text)
        return data.get("intent", "research")
    except Exception as e:
        print(f"Intent classification failed: {e}")
        return "research"

def process_intake_chat(current_brief: dict[str, Any], chat_history: list[dict[str, str]], user_message: str, model: ResearchModel, app_mode: str = "research") -> dict[str, Any]:
    """
    Kullanıcıdan gelen serbest metin mesajını analiz eder, JSON formatındaki brief'i günceller
    ve kullanıcıya verilecek yanıtı üretir.
    Dönen JSON yapısı:
    {
      "updated_brief": { "title": "...", "market": "...", "idea": "...", ... },
      "assistant_reply": "..."
    }
    """
    
    # Sohbet geçmişini formatla (son 5 mesaja kadar)
    history_text = ""
    for msg in chat_history[-5:]:
        role = "Kullanıcı" if msg["role"] == "user" else "Defne"
        history_text += f"{role}: {msg['content']}\n"
    
    try:
        from .database import get_system_config
        config = get_system_config()
        db_wizard_prompt = config.get("wizard_prompt")
    except Exception:
        db_wizard_prompt = None

    # ── LIKED CURATED QUESTIONS INTEGRATION ────────────────────────────────────
    db_questions = []
    try:
        from .database import get_question_collection
        curated = get_question_collection()
        liked_curated = [q for q in curated if q.get("is_liked") == 1]
        
        concept = detect_product_concept(current_brief, user_message)
        
        for q in liked_curated:
            q_text = q.get("question")
            q_cat = str(q.get("research_category") or "").lower()
            q_title = str(q.get("research_title") or "").lower()
            q_purpose = str(q.get("purpose_context") or "").lower()
            
            combined_q = f"{q_cat} {q_title} {q_purpose} {q_text.lower()}"
            
            matched = False
            if concept == "mobil_app":
                matched = any(kw in combined_q for kw in ["mobil", "app", "uygulama", "android", "ios"])
            elif concept == "saas_platform":
                matched = any(kw in combined_q for kw in ["saas", "yazılım", "api", "platform", "b2b", "entegrasyon"])
            elif concept == "physical_product":
                matched = any(kw in combined_q for kw in ["şampuan", "krem", "kozmetik", "gıda", "fiziksel", "ambalaj", "ürün"])
            elif concept == "service_experience":
                matched = any(kw in combined_q for kw in ["restoran", "kafe", "kuaför", "hizmet", "randevu", "rezervasyon", "salon"])
            
            if matched or not q_cat:
                db_questions.append(q_text)
    except Exception as e:
        print(f"Failed to fetch curated questions: {e}")

    # ── DYNAMIC CONCEPT POOL FORMATTING ────────────────────────────────────────
    concept = detect_product_concept(current_brief, user_message)
    pool = CONCEPT_POOLS[concept]
    
    # Static pool questions + DB Curated Liked questions
    static_questions = pool["questions"]
    concept_questions = list(static_questions)
    for dq in db_questions:
        if dq not in concept_questions:
            concept_questions.append(dq)
    concept_questions = concept_questions[:6]  # Limit to 6
    
    questions_list_str = "\n".join([f"  * {q}" for q in concept_questions])
    
    custom_role = (
        f"Sen {pool['persona_name']}'sin. Amacın, kullanıcıdan bir ürün/hizmet fikrini ve pazar araştırması "
        f"ihtiyaçlarını sohbet ederek öğrenmek ve arkadaki JSON yapısını doldurmaktır.\n"
        f"Sorumluluk ve Odak Alanların:\n- {pool['focus_areas']}\n\n"
        f"Bu ürün/hizmet konsepti için kullanabileceğin veya kullanıcıya önerebileceğin özel soru/konsept havuzun şöyledir:\n"
        f"{questions_list_str}"
    )

    if app_mode == "ab_test":
        system_prompt = (
            f"{custom_role}\n\n"
            "Kurallar:\n"
            "1. Kullanıcının son mesajını oku. İçindeki verileri mevcut JSON'a (current_brief) yerleştir. Eğer kullanıcı senin daha önce otomatik doldurduğun bir alanı düzeltmek veya değiştirmek isterse, o alanı kullanıcının isteğine göre GÜNCELLE (üzerine yaz). Onun dışındaki mevcut verileri koru.\n"
            "2. JSON'ın eksik alanlarını tespit et (idea, title, variant_a, variant_b, target_users, success_metric) ve SADECE BİR TANESİNİ sormak için kısa, doğal bir `assistant_reply` yaz.\n"
            "3. JSON alanları şöyledir:\n"
            "   - title (str): A/B testinin kısa adı\n"
            "   - idea (str): Ürün fikri, ana teklif veya bağlam\n"
            "   - variant_a (str): Varyant A metni/kopya tanımı\n"
            "   - variant_b (str): Varyant B metni/kopya tanımı\n"
            "   - target_users (list[str]): Hedef kullanıcı kitleleri\n"
            "   - success_metric (str): Tercih/başarı kriteri (Örn: hangisi daha ikna edici, hangisine tıklar)\n\n"
            "4. Her şey tamamsa `assistant_reply` içinde 'Artık A/B test simülasyonunu başlatmaya hazırım, butona basabilirsin.' şeklinde onay ver.\n"
            "5. Yanıtı KESİNLİKLE sadece şu formatta JSON olarak dönmelisin (başka metin ekleme, markdown block kullanma): \n"
            '{"updated_brief": { ... }, "assistant_reply": "..."}\n\n'
            "6. KESİNTİSİZ ADIM ADIM YÖNLENDİRME VE TEK ALAN SINIRI KURALI:\n"
            "   - Bir diyalog turunda KESİNLİKLE sadece ve sadece TEK BİR EKSİK ALANI hedefle. Sadece o alana yönelik veri üret veya öneride bulun.\n"
            "   - `updated_brief` içerisinde o an konuşulmayan diğer henüz boş veya None olan eksik alanları KESİNLİKLE doldurma! Onları boş bırakarak adım adım ilerle.\n"
            "   - Kullanıcıyı eksiksiz ve kesintisiz yönlendir, asla acele edip brief'in tamamını kendin doldurarak diyaloğu hemen sonlandırma.\n\n"
            "7. PROAKTİF İNSİYATİF VE DÖNGÜ ÖNLEME KURALI:\n"
            "   Eğer kullanıcı bir alan için çok genel, kısa veya belirsiz bir cevap verirse, asla aynı soruyu tekrarlama. Bunun yerine:\n"
            "   a. Kullanıcının genel niyetine dayanarak o alanı kendin mantıklı örnek veya somut veriyle doldur (örn: 'variant_a' ve 'variant_b' için alternatif reklam metni taslakları üret ve 'updated_brief' içerisine ekle).\n"
            "   b. 'assistant_reply' içinde bu önerdiğin örnekleri kullanıcıya sun ve onayını iste.\n"
            "   c. Böylece kullanıcının kısa veya yetersiz cevap verdiği durumlarda sistemin döngüye girip sürekli aynı soruyu sormasını kesinlikle engelle."
        )
    else:
        base_role_intro = db_wizard_prompt if db_wizard_prompt else "Sen Defne'sin: Kıdemli pazar araştırması mimarı."
        system_prompt = (
            f"{base_role_intro}\n\n"
            f"{custom_role}\n\n"
            "Kurallar:\n"
            "1. Kullanıcının son mesajını oku. İçindeki verileri mevcut JSON'a (current_brief) yerleştir. Eğer kullanıcı senin daha önce otomatik doldurduğun bir alanı (örn: senin türettiğin başlığı veya soruları) düzeltmek veya değiştirmek isterse, o alanı kullanıcının isteğine göre GÜNCELLE (üzerine yaz). Onun dışındaki mevcut verileri koru.\n"
            "2. JSON'ın eksik alanlarını tespit et (idea, title, target_users, questions, expected_price, competitors, success_metric, respondent_types, discovery_channels) ve SADECE BİR TANESİNİ sormak için kısa, doğal bir `assistant_reply` yaz.\n"
            "3. JSON alanları şöyledir:\n"
            "   - title (str): Çalışmanın kısa adı\n"
            "   - market (str): Hedef pazar (varsayılan: Türkiye)\n"
            "   - category (str): Ürün kategorisi\n"
            "   - idea (str): Ürün fikri ve problemi\n"
            "   - target_users (list[str]): Hedef kullanıcı tipleri\n"
            "   - questions (list[str]): Araştırma soruları/öğrenilmek istenenler\n"
            "   - competitors (list[str]): Rakipler ve mevcut çözümler\n"
            "   - expected_price (str): Fiyat modeli\n"
            "   - sales_channel (str): Satış kanalı\n"
            "   - success_metric (str): Araştırmanın başarı kriteri\n"
            "   - respondent_types (list[str]): Araştırmaya dahil edilecek katılımcı tipleri.\n"
            "     Geçerli değerler: potential_customer (henüz ürünü kullanmamış potansiyel müşteri), competitor_user (rakip kullanan), churned_user (terk eden eski kullanıcı), decision_maker (satın alma yetkili yönetici), individual_user (fiili operasyonu yürüten).\n"
            "     Kullanıcıya basit sorarak belirle: Ör: 'Henüz hiç kullanmamış potansiyel müşterilerle mi, yoksa rakiplerinizden gelen kullanıcılarla mı konuşmak istiyorsunuz?'\n"
            "   - discovery_channels (list[str]): Hedef kitlenin ürünü keşfetmesini beklediğiniz öncelikli kanallar.\n"
            "     Ör: ['sosyal medya reklamı', 'Google arama', 'arkadaş tavsiyesi', 'içerik/blog', 'App Store'].\n"
            "     Kullanıcıya kısaca sor: 'Müşterilerinizin sizi nasıl bulmasını istiyorsunuz — sosyal medya, arama motoru, tavsiye mi?'\n\n"
            "4. Her şey tamamsa `assistant_reply` içinde 'Artık araştırmayı başlatmaya hazırım, butona basabilirsin.' şeklinde onay ver.\n"
            "5. Yanıtı KESİNLİKLE sadece şu formatta JSON olarak dönmelisin (başka metin ekleme, markdown block kullanma): \n"
            '{"updated_brief": { ... }, "assistant_reply": "..."}\n\n'
            "6. KESİNTİSİZ ADIM ADIM YÖNLENDİRME VE TEK ALAN SINIRI KURALI:\n"
            "   - Bir diyalog turunda KESİNLİKLE sadece ve sadece TEK BİR EKSİK ALANI hedefle. Sadece o alana yönelik veri üret veya öneride bulun.\n"
            "   - `updated_brief` içerisinde o an konuşulmayan diğer henüz boş veya None olan eksik alanları (özellikle 'competitors', 'target_users', 'questions' gibi) KESİNLİKLE doldurma! Onları boş liste/None olarak bırakarak adım adım ilerle.\n"
            "   - Kullanıcıyı eksiksiz ve kesintisiz yönlendir, asla acele edip brief'in tamamını kendin doldurarak diyaloğu hemen sonlandırma.\n\n"
            "7. PROAKTİF İNSİYATİF VE DÖNGÜ ÖNLEME KURALI (KRİTİK):\n"
            "   a. Eğer sen spesifik bir alan (örneğin 'title') sorduysan ancak kullanıcı doğrudan uzun bir ürün fikri ('idea') anlattıysa, kullanıcının anlattıklarından yola çıkarak sorduğun alanı (title) KENDİN yaratıcı bir şekilde türet ve 'idea' alanını da doldur. Asla sorduğun alanı boş bırakıp aynı soruyu (başlık) tekrar sorma!\n"
            "   b. Eğer kullanıcı bir alan için (özellikle 'questions', 'competitors', 'target_users' gibi list alanları) "
            "çok genel, kısa veya belirsiz bir cevap verirse, asla aynı soruyu tekrarlama. O alanı kendin 2-3 adet mantıklı somut veriyle doldur.\n"
            "   c. 'assistant_reply' içinde bu önerdiğin örnekleri veya kendi ürettiğin başlığı kullanıcıya sun ve onayını al (Örn: 'Sizin için şu başlığı ve soruları ekledim, ne dersiniz?')."
        )
    
    # ── INPUT REFRAMING (ELEPHANT Çerçevesi) ————————————————————————————————————
    # Kaynak: Akademik Sentez Raporu §Sütun 4 — arXiv:2602.23971
    # Şeffaf mod (Seçenek B): reframe yapıldıysa Defne kullanıcıya bildirir.
    reframed_message, was_reframed = reframe_user_input(user_message)
    reframe_notice = ""
    if was_reframed:
        reframe_notice = (
            f'\n\n[Defne Notu: "İfadenı tarafsız bir araştırma sorusu olarak ele aldım: '
            f'"{reframed_message}" Bu şekilde daha gerçekçi bulgular elde edebiliriz.]'
        )
        user_message = reframed_message

    prompt = (
        f"Mevcut Brief (JSON):\n{json.dumps(current_brief, ensure_ascii=False, indent=2)}\n\n"
        f"Son Sohbet Geçmişi:\n{history_text}\n"
        f"Kullanıcının Son Mesajı: {user_message}\n\n"
        "Yukarıdaki formata uygun şekilde JSON döndör:"
    )
    
    response_text = ""
    try:
        response_text = model.generate(system_prompt, prompt)
        
        # Markdown kod bloğunu temizle (varsa)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].strip()
            
        # Hata payını azaltmak için sadece ilk { ve son } arasındaki asıl JSON'ı çek
        import re
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            response_text = match.group(0)
            
        # Model yanıtlarındaki olası Python veri yapısı formatlarını (None, True, False)
        # standart JSON formatına (null, true, false) dönüştürerek hataya karşı dayanıklı hale getir
        response_text = re.sub(r':\s*None\b', ': null', response_text)
        response_text = re.sub(r':\s*True\b', ': true', response_text)
        response_text = re.sub(r':\s*False\b', ': false', response_text)
            
        result = json.loads(response_text)

        # Varsayılan yapıyı koruma
        if "updated_brief" not in result:
            result["updated_brief"] = current_brief
        if "assistant_reply" not in result:
            result["assistant_reply"] = "Anladım. Başka eklemek istediğin bir şey var mı?"

        # Reframe notu varsa asistan yanıtına ekle (şeffaf mod)
        if reframe_notice:
            result["assistant_reply"] = result["assistant_reply"] + reframe_notice

        return result
    except Exception as e:
        print(f"Intake parsing error: {e}\nRaw Response: {response_text}")
        return {
            "updated_brief": current_brief,
            "assistant_reply": "Kusura bakmayın, bir anlığına dikkatim dağıldı ve yanıtı tamamlayamadım. Lütfen son söylediğinizi tekrarlar mısınız veya devam edebilir miyiz?"
        }
