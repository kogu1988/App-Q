# App-Q V3.0 Geliştirme Notları ve Yol Haritası (Backlog)

Bu belge, App-Q platformunun gelecekteki sürümlerinde eklenecek özellik fikirlerini, metodoloji notlarını ve tamamlanan sprint geçmişini içerir.

## ✅ Tamamlanan Sprintler

| Sprint | Açıklama | Dosya (Arşiv) |
|---|---|---|
| Codebase Audit & DRY Refactor | Streamlit WET kod temizliği, `packages/core` silindi, `reporting.py` ortak katman | PLAN-codebase-audit-refactor.md (silindi) |
| React + FastAPI Migration | Streamlit → Next.js + FastAPI geçişi | PLAN-react-fastapi.md (silindi) |
| Grounded Simulation S1+S2+S3 | Rogers stance, adversarial pipeline, RFI metriği | PLAN-grounded-simulation.md (silindi) |

---

## 🚀 Planlanan Özellikler (Pro Sürüm)

### 1. Melez Araştırma Motoru (Kalitatif + Kantitatif)
- **Sentetik Odak Grup (Focus Group) Simülasyonu [Efor: Yüksek]:** Birebir mülakatlara ek olarak 4-5 farklı personanın aynı sanal odada ürünü tartıştığı, fikirlerin çarpıştığı dinamik oturumlar.
- **Büyük Ölçekli Sentetik Anketler [Efor: Orta]:** Derinlemesine mülakatlara girmeden önce daha hafif bir LLM ile saniyeler içinde 1.000 kişilik sentetik kitleye A/B veya çoktan seçmeli anket çözdürülerek istatistiksel veri elde edilmesi.

### 2. Gelişmiş Raporlama 
- Sadece PDF değil, elde edilen verilerin interaktif grafiklere dönüştürülmesi (Heatmap, Pie Chart). **[Efor: Yüksek]**
- Anket verilerinin doğrudan `chi-square` ötesinde çeşitli istatistiksel geçerlilik testlerine sokulması. **[Efor: Orta]**

### 3. Kullanım Alanı (Use-Case) Genişletmeleri
- **Reklam ve Metin Test Motoru (Copywriting Validator) [Efor: Orta]:** Pazarlama ekiplerinin A/B test edeceği reklam kopyalarını veya e-posta metinlerini yükleyip, saniyeler içinde 50 farklı personaya göstererek yayın öncesi Tıklanma Oranı (CTR) potansiyelini ölçmeleri. Günlük aktif kullanımı artırmak için kritik.
- **Müşteri "Dijital İkiz" Klonlama (CRM RAG Entegrasyonu) [Efor: Yüksek]:** Şirketlerin kendi Zendesk veya destek verilerini sisteme yükleyerek, hayali personalar yerine doğrudan *kendi müşterilerinin klonlarıyla* test yapabilme yeteneği.

### 4. Gelir Modeli ve Ticarileştirme Stratejisi
- **Koltuk Başına Sabit Ücret (SaaS Per-Seat) [Efor: Düşük]:** Müşterilerin kontör stresi yaşamaması ve platforma bağımlı hale gelmeleri için limitsiz (fair-use korumalı) standart SaaS modeli aboneliği.
- **Ajans "White-Label" Lisanslama [Efor: Yüksek]:** Reklam ve araştırma ajanslarının kendi logoları ile müşterilerine PDF pazar araştırma raporları basabilmesi için yüksek marjlı ve kurumsal (Enterprise) proje bazlı lisanslama.

### 5. Kullanıcı Deneyimi (UX) ve İlk Karşılaşma (Onboarding)
- **Tinder-Tarzı Soru Seçimi (Swipe-to-Curate) [Efor: Orta]:** Kullanıcıyı "Hangi soruları sormak istersin?" diye boş bir ekranla baş başa bırakmak yerine, yapay zekanın ürettiği 10 soruyu "Flashcard" olarak ekrana getirmek. Kullanıcının sağa (bunu sor) veya sola (geç) kaydırarak oyunlaştırılmış bir şekilde mülakat senaryosunu saniyeler içinde oluşturması.
- **Görsel Persona Yaratıcısı (Visual AI Portraits) [Efor: Yüksek]:** Personaların sadece metin tabanlı (Örn: "Ayşe, 35") kalmaması, arka planda DALL-E/Stable Diffusion kullanılarak personanın yaş, gelir durumu ve şüphecilik seviyesi gibi "slider" ayarları değiştikçe yüz ifadesi ve vesikalık fotoğrafının anlık olarak yapay zeka ile üretilip ekrana yansıtılması.

### 6. Rekabet Avantajı ve Veri Hendeği (Data Moat)
- **Sektörel "Altın" Şablon Pazaryeri (Community Marketplace) [Efor: Yüksek]:** Başarılı araştırmacıların veya büyük ajansların kendi yarattıkları özel mülakat şablonlarını (Prompt + Soru Setleri) platformda yayınlayıp satabildikleri, sistemi kopyalanamaz kılan bir ekosistem.
- **"Sentetik Yanılsama" Kusur Motoru (Flaw/Bias Engine) [Efor: Yüksek]:** LLM'leri "mükemmel cevap veren asistanlar" olmak yerine bilerek insani ön yargılar, mantık hataları ve duygusal tepkiler (cognitive biases) üretecek şekilde eğiterek piyasadaki en "gerçekçi" ve kopyalanamaz sentetik kitleyi yaratmak.
- **Şirketlere Özel "Evrimleşen" Model (Iterative Auto-Tuning) [Efor: Yüksek]:** Müşterilerin (şirketlerin) mülakatlarda düzelttiği sorular ve verdiği geribildirimlerle sürekli beslenen, zamanla o şirketin DNA'sını ezberleyen kuruma özel ufak LoRA adaptörleri.

### 7. Teknik Optimizasyon ve Maliyet Düşürme (AI Inference)
- **Yarı-Sentetik Anlamsal Önbellek (Semantic Caching Tree) [Efor: Orta]:** LLM API maliyetlerini %90 düşürmek için pgvector kullanarak benzer sorulara daha önceden verilen yanıtların hızlıca getirilip hafifçe değiştirilmesi.

### 8. Pazara Çıkış Stratejisi ve Kullanıcı Kazanımı (Go-To-Market)
- **Ücretsiz Startup "Roast" Servisi [Efor: Düşük]:** Kullanıcıların ürün fikirlerini acımasızca eleştiren tek bir sentetik personanın yer aldığı mini, viral bir araç ile ana ürüne on binlerce bedava organik trafik (Word-of-Mouth) çekilmesi.
- **Sentetik Endüstri Raporları (LinkedIn Düşünce Liderliği) [Efor: Düşük]:** Platformu kullanarak ücretsiz ve ilgi çekici sektörel pazar araştırma raporları üretip, şirketin veya kurucuların sektör otoritesi (Inbound Marketing) olarak konumlanmasını sağlamak.
- **AI Destekli "Inception" Soğuk Satış (Hyper-Personalized Outreach) [Efor: Orta]:** Satış yapılacak hedef CEO veya yöneticinin dijital ayak izlerinden sentetik bir personasını yaratıp, satış argümanını önce o yapay zekaya sunmak. Elde edilen itirazlara göre asıl yöneticiye kusursuz bir e-posta atmak.

---

## 🔬 Metodoloji İyileştirme Notları

### Tuzak Soru (Attention Check) Entegrasyonu [Efor: Düşük] — Beklemede
- **Amaç:** Mülakat script'ine katılımcının dikkati ölçen "tuzak sorular" (attention check / trap questions) eklemek.
- **Örnek:** *"Bu soruyu atlayarak sadece 'mavi' yazın"* — LLM tüm soruları anlam odaklı yanıtladığı için bu tür sorular simülasyon kalitesini artırmak yerine karmaşıklık ekler.
- **Not:** Gerçek insan panellerinde kritik (yüksek value), ancak sentetik LLM personalarında öncelik düşük. Gerçek kullanıcı paneli entegrasyonu eklenirse yeniden değerlendir.
- **İlgili dosyalar:** `workflow.py` → `generate_interview_script()`, `quality.py` → `compute_research_quality()`

### ACT-R Working Memory Capping [Efor: Yüksek] — Kapsam Dışı (S4 Backlog)
- **Amaç:** Bilal (2026) Grounded Simulation makalesindeki ACT-R bilişsel mimari prensibi — personaların bir mülakat boyunca taşıyabileceği "çalışan bellek" kapasitesini sınırlandırarak daha gerçekçi bilişsel yük simülasyonu yapmak.
- **Neden şimdi değil:** LLM API çağrıları stateless'tır; her turn bağımsız olduğu için tam ACT-R uygulaması mümkün değil. Temsili çözüm için `cross-question consistency` ve `turn-count limit` heuristikleri geçici alternatif olarak değerlendirilebilir.
- **Ön koşul:** Multi-turn stateful oturum mimarisi (örn. conversation memory, per-persona context buffer) kurulmadan anlamlı bir uygulama yapılamaz.
- **Referans:** Bilal (2026) Grounded Simulation §3.2 — ACT-R declarative memory activation formula.
- **İlgili dosyalar:** `workflow.py` → `run_persona_interview()`, `models.py` → `InterviewTurn`

### Hofstede Kültürel Boyutlar Entegrasyonu [Efor: Orta] — Kapsam Dışı (S4 Backlog)
- **Amaç:** Bilal (2026) makalesindeki Hofstede'nin 6 kültürel boyutunu (Power Distance, Individualism, Uncertainty Avoidance, Long-Term Orientation, Indulgence, Masculinity) persona trait kalibrasyonuna eklemek.
- **Neden şimdi değil:** App-Q şu an Türkiye tek pazarını hedefliyor; 93 ülkeli Hofstede veri setinin tamamını entegre etmek bu aşamada orantısız karmaşıklık ekler. Türkiye profili (`PDI=66, IDV=37, UAI=85, LTO=46`) model prompt'larına encoding ile kısmen uygulanabilir.
- **Ön koşul:** Çok pazarlı (`market`) araştırma desteği aktif hale geldiğinde öncelik artar. O aşamada `SES_PROFILES` ile birleşik bir `CulturalProfile` yapısı tasarlanmalı.
- **Referans:** Bilal (2026) Grounded Simulation §3.3 — Cultural Context Layer; Hofstede (2010) Cultures and Organizations.
- **İlgili dosyalar:** `models.py` → `Persona`, `workflow.py` → `persona_attributes()`

### Operatör (Admin) Paneli Next.js Yeniden Tasarımı [Efor: Orta]
- **Bağlam:** Streamlit operatör UI (`apps/operator/streamlit_app.py`) hâlâ aktif; istemci tarafı Next.js'e taşındı ancak operatör ekranı taşınmadı.
- **Yapılacaklar:** Operatör panelini Next.js'e taşı, "Modern SaaS Dashboard" temasına (Trust Blue `#2563EB`, Fira Sans) getir. KPI kartları, drill-down grid layoutlar, minimal padding.
- **Ön koşul:** Admin rotaları `/admin` sayfasına eklenecek (`apps/frontend/src/app/admin`).
- **İlgili dosyalar:** `apps/operator/streamlit_app.py` (kaynak), `apps/frontend/src/app/admin/page.tsx` (hedef)

### Persona Builder UI (Next.js) [Efor: Orta]
- **Bağlam:** B2B persona oluşturma ekranı planlandı ama Streamlit hedefli yazıldı; Next.js'e uyarlanmadı.
- **Yapılacaklar:** `/client/personas/new` rotasına çok adımlı form (Temel Bilgiler → B2B Metrikleri → Özel Trait'ler). B2B alanları: `b2b_company_type`, `b2b_industry`, `b2b_company_size`, `b2b_decision_maker`. PostgreSQL `personas_pool` tablosuna kaydet.
- **Güvenlik notu:** Özel metrik key'lerinde SQL injection vektörlerine dikkat.
- **İlgili dosyalar:** `apps/frontend/src/app/client/personas/`, `packages/research_engine/db_vectors.py`

---
*Not: Bu belge beyin fırtınası oturumlarından elde edilen çıktılarla güncellenmeye devam edecektir.*
