import json
import uuid

from .models import Persona
from .db_vectors import save_persona_to_pool
from .matrix import allocate_cohort_matrix, validate_stance_diversity
from .workflow import persona_traits, persona_attributes, STANCE_PROFILE, neo_facets_from_traits
from .caching import get_embedding

def generate_and_save_personas(
    role_title: str,
    count: int,
    model,
    category: str = "genel",
    market: str = "Türkiye",
    target_users: str = "genel tüketici",
    why: str = "Hedef kitle temsilcisi",
    save_to_pool: bool = True,
    negative_targeting: str = ""
) -> list[Persona]:
    """Admin veya Enterprise için LLM ile persona üretir ve havuza kaydeder."""
    personas = []
    
    matrix_allocations = allocate_cohort_matrix(count)
    
    constraints_text = ""
    for i, alloc in enumerate(matrix_allocations):
        bf = alloc["big_five_constraints"]
        constraints_text += (
            f"Persona {i+1}:\n"
            f"- Cinsiyet: {alloc.get('gender', 'Bilinmiyor')}\n"
            f"- Yaş Grubu: {alloc.get('age_group', 'Bilinmiyor')}\n"
            f"- Stance: {alloc['stance']}\n"
            f"- SES Grubu: {alloc['ses_group']}\n"
            f"- Big Five Sınırları: Openness ({bf.get('openness')}), Conscientiousness ({bf.get('conscientiousness')}), "
            f"Extroversion ({bf.get('extroversion')}), Agreeableness ({bf.get('agreeableness')}), Neuroticism ({bf.get('neuroticism')})\n\n"
        )

    system = "Sen App-Q için dinamik persona üreticisisin. İstenilen rolünde, Türkiye pazarında inandırıcı, spesifik bir persona JSON'u üret. JSON dışında hiçbir şey yazma."
    prompt = (
        f"Kategori: {category}\n"
        f"Pazar: {market}\n"
        f"Hedef kullanıcı grubu: {target_users}\n"
        f"Rol: {role_title} (Gerekçe: {why})\n"
        f"Üretilecek Persona Sayısı: {count}\n\n"
        f"{('NEGATİF HEDEFLEME KISITLARI (KESİNLİKLE İÇERMEMESİ GEREKEN ÖZELLİKLER):\n- ' + negative_targeting + '\n\n') if negative_targeting else ''}"
        "LÜTFEN AŞAĞIDAKİ MATRİS KISITLARINA (HARD CONSTRAINTS) KESİNLİKLE UY:\n"
        f"{constraints_text}"
        "Lütfen aşağıdaki yapıda bir JSON listesi döndür:\n"
        "[\n"
        "  {\n"
        "    \"name\": \"Türkçe isim\",\n"
        "    \"gender\": \"Kotalarda atanan cinsiyet\",\n"
        "    \"age\": 30,\n"
        "    \"city\": \"Türkiye şehri\",\n"
        "    \"segment\": \"Pazar segmenti\",\n"
        "    \"stance\": \"Matriste atanan Stance\",\n"
        "    \"price_sensitivity\": 7,\n"
        "    \"digital_confidence\": 8,\n"
        "    \"ses_group\": \"Matriste atanan SES\",\n"
        "    \"respondent_type\": \"potential_customer, competitor_user, vs.\",\n"
        "    \"settlement_type\": \"kentsel, banliyö veya kırsal\",\n"
        "    \"context\": \"Kısa bağlam\",\n"
        "    \"goals\": [\"hedef 1\"],\n"
        "    \"objections\": [\"itiraz 1\"],\n"
        "    \"knowledge_boundary\": \"bilgi sınırı\",\n"
        "    \"bio\": \"kısa hikayesi\"\n"
        "  }\n"
        "]"
    )
    
    try:
        response_text = model.generate(system, prompt, response_format="json")
        parsed_list = json.loads(response_text)
        for i, item in enumerate(parsed_list):
            new_id = f"p_{uuid.uuid4().hex[:8]}"
            st = item.get("stance", "Mainstream")
            # Calculate traits using the assigned stance
            traits_d = persona_traits(i, st, item.get("price_sensitivity", 5), item.get("digital_confidence", 5))
            
            p = Persona(
                id=new_id,
                name=item.get("name", "İsimsiz"),
                age=item.get("age", 30),
                city=item.get("city", "İstanbul"),
                segment=item.get("segment", role_title),
                role_title=role_title,
                stance=st,
                price_sensitivity=item.get("price_sensitivity", 5),
                digital_confidence=item.get("digital_confidence", 5),
                context=item.get("context", ""),
                goals=item.get("goals", []),
                objections=item.get("objections", []),
                knowledge_boundary=item.get("knowledge_boundary", ""),
                bio=item.get("bio", ""),
                ses_group=item.get("ses_group", "C1"),
                respondent_type=item.get("respondent_type", "potential_customer"),
                settlement_type=item.get("settlement_type", "kentsel"),
                attributes=persona_attributes(item.get("segment", role_title), item.get("stance", "Mainstream"), item.get("price_sensitivity", 5), item.get("digital_confidence", 5)),
                traits=traits_d,
                diffusion_stage=STANCE_PROFILE.get(st, {}).get("tr_description", ""),
                neo_facets=neo_facets_from_traits(traits_d, st),
            )
            personas.append(p)
            
            if save_to_pool:
                # Semantic embedding for the role string
                embedding = get_embedding(role_title)
                
                # Save to pool
                save_persona_to_pool(p.model_dump(), embedding=embedding)
    except Exception as e:
        print("LLM Persona generation failed:", str(e))

    # Stance Diversity doğrulaması — panel oluştuktan hemen sonra (god_doc.md §bias_audit)
    if personas:
        panel_dicts = [{"stance": p.stance, "ses_group": p.ses_group} for p in personas]
        diversity_check = validate_stance_diversity(panel_dicts)
        if not diversity_check["valid"]:
            print(
                f"[UYARI] Stance Diversity doğrulaması başarısız "
                f"(balance: {diversity_check['balance_score']:.2f}, "
                f"stance_count: {diversity_check['stance_count']}): "
                + " | ".join(diversity_check["issues"])
            )

    return personas

def generate_random_persona_draft(model) -> dict:
    """Frontend formu için tek bir rastgele persona taslağı üretir."""
    import random
    
    archetypes = [
        "Mavi Yakalı Fabrika İşçisi", "Üniversite Öğrencisi (Z Kuşağı)", "Ev Hanımı",
        "Kurumsal Beyaz Yaka Yönetici", "Küçük Esnaf (Geleneksel)", "Teknoloji Girişimcisi",
        "Emekli Memur", "Serbest Çalışan (Sanatçı/Tasarımcı)", "Sağlık Çalışanı (Hemşire/Doktor)",
        "Ataması Yapılmamış Öğretmen", "Tarım Çalışanı / Çiftçi", "İnşaat Ustası",
        "Kurye / Lojistik Çalışanı", "Güzellik Uzmanı / Kuaför", "Yazılım Geliştirici",
        "Çağrı Merkezi Temsilcisi", "Banka Memuru", "Kasiyer / Mağaza Çalışanı"
    ]
    selected_seed = random.choice(archetypes)
    
    # Python ile yaş, tecrübe sınırı ve katılımcı tipini önceden (rastgele) belirliyoruz.
    # LLM'in matematik halüsinasyonlarını engelliyoruz.
    random_age = random.randint(18, 65)
    max_experience_years = max(0, random_age - 18)
    respondent_types = ["potential_customer", "competitor_user", "individual_user"]
    selected_respondent_type = random.choice(respondent_types)
    
    system = "Sen App-Q için dinamik persona üreticisisin. Tamamen rastgele, inandırıcı ve Türkiye pazarına uygun bir tüketici profili üret. JSON dışında hiçbir şey yazma."
    prompt = (
        f"Lütfen MÜTLAKA şu temel arketip etrafında şekillenen bir profil üret: **{selected_seed}**.\n"
        f"DİKKAT! Bu kişinin yaşı: **{random_age}**.\n"
        f"Bu kişinin yasal olarak en fazla **{max_experience_years}** yıllık iş tecrübesi olabilir (18 yaş sınırından dolayı). Biyografisinde sakın {max_experience_years} yıldan daha fazla çalıştığını iddia etme!\n"
        f"Bu kişinin Katılımcı Tipi (respondent_type) şudur: **{selected_respondent_type}**.\n\n"
        "Aşağıdaki yapıda TEK bir JSON objesi döndür. Değerleri seçerken SOSYOEKONOMİK STATÜ (SES), MESLEK ve HEDEFLER/İTİRAZLAR "
        "arasında kusursuz bir mantıksal tutarlılık kur.\n"
        "Şablon içindeki veri tiplerini kendi yaratıcılığınla doldur.\n\n"
        "{\n"
        "  \"_reasoning\": \"Seçilen yaş, SES, meslek ve itirazların neden birbiriyle uyumlu olduğuna dair kısa bir analiz...\",\n"
        "  \"name\": \"<Gerçekçi ve yaygın bir Türk ismi>\",\n"
        f"  \"age\": {random_age},\n"
        "  \"city\": \"<Türkiye'den mantıklı bir şehir>\",\n"
        "  \"segment\": \"<Seçtiğin spesifik rol veya segment>\",\n"
        "  \"stance\": \"<Innovator, EarlyAdopter, Mainstream, Laggard veya Skeptic>\",\n"
        "  \"ses_group\": \"<AB, C1, C2, veya DE>\",\n"
        f"  \"respondent_type\": \"{selected_respondent_type}\",\n"
        "  \"settlement_type\": \"<kentsel, banliyö veya kırsal>\",\n"
        "  \"goals\": \"<Kısa, net ve arketipe uygun 2-3 hedef (virgülle ayrılmış)>\",\n"
        "  \"objections\": \"<Kısa, net ve arketipe uygun 2-3 itiraz veya endişe (virgülle ayrılmış)>\",\n"
        f"  \"bio\": \"<Kısa hayat hikayesi. En fazla {max_experience_years} yıllık tecrübesi olabilir!>\"\n"
        "}"
    )
    
    try:
        response_text = model.generate(system, prompt, response_format="json")
        parsed = json.loads(response_text)
        return parsed
    except Exception as e:
        print("Draft Persona generation failed:", str(e))
        return {}
