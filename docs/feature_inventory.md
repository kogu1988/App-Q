# App-Q — Mevcut Özellik Envanteri

Bu liste, sistemde **fiilen var olan** özellikleri katmana göre gruplar.  
Amaç: hangi özelliğin hangi plana gireceğine karar vermek için temel referans olmak.

---

## 🧠 Araştırma Motoru (Research Engine)

| # | Özellik | Ne işe yarar? |
|---|---|---|
| 1 | **Defne — Akıllı Brief Sihirbazı** | Kullanıcıyla sohbet ederek araştırma brief'ini adım adım doldurur. Ürün kategorisini otomatik algılar, buna göre persona değişir (UX uzmanı, FMCG müdürü vb.) |
| 2 | **A/B Test Modu** | Tek araştırmada iki varyantı (metin, fiyat, konsept) aynı anda test eder; persona paneli her varyanta ayrı ayrı maruz kalır |
| 3 | **Pazar Araştırması Modu** | Ürün/hizmet fikrine yönelik derinlemesine keşif araştırması; pain point, itiraz, değer algısı |
| 4 | **Rogers Diffusion Stance Sistemi** | Her persona 5 benimseme kategorisinden birine atanır: Innovator, EarlyAdopter, Mainstream, Laggard, Skeptic. Panel her zaman belirli dağılıma göre kurulur (1-1-2-1) |
| 5 | **OCEAN / Big Five Psikometrik Profil** | Her persona için 5 kişilik boyutu (Açıklık, Sorumluluk, Dışadönüklük, Uyumluluk, Nevrotiklik) Rogers stance'ına göre kalibre edilir |
| 6 | **NEO Facet Annotasyonu** | OCEAN'ın 12 alt boyutuyla her personaya biyografik tutarlılık sağlanır |
| 7 | **SES (Sosyoekonomik Statü) Segmentasyonu** | Alt/orta/üst SES gruplarını panel dengesi için kullanır; cross-tab raporlama için etiketler |
| 8 | **Respondent Type Sınıflaması** | Karar verici, etkileyici, son kullanıcı, bütçe sahibi vb. profesyonel roller |
| 9 | **B2B Persona Modu** | Şirket tipi, sektör, çalışan sayısı, karar alma yetkisi gibi B2B alanlarını destekler |
| 10 | **Settlement Type (Yerleşim Tipi)** | İstanbul/büyükşehir, il merkezi, ilçe/köy ayrımıyla coğrafi çeşitlilik sağlar |
| 11 | **Sıralı Mülakat Motoru (Streaming)** | Her persona izole biçimde mülakata alınır; cevaplar SSE (Server-Sent Events) ile gerçek zamanlı akar |
| 12 | **Çift Model Yönlendirme** | B2C ve B2B sorular için farklı model kullanılır (örn. Trendyol LLM vs Kizagan-E4B) |
| 13 | **Anti-Sycophancy / Gizli Yargıç** | Her persona cevabı üretilince gizli yargıç geçer; persona duruşuna aykırıysa yeniden üretilir |
| 14 | **Anlamsal Soru Önbelleği (Semantic Caching)** | Benzer sorulara daha önce üretilmiş cevapları getirir; LLM API maliyetini düşürür |

---

## 📊 Analitik ve Sentez

| # | Özellik | Ne işe yarar? |
|---|---|---|
| 15 | **Otomatik Rapor Sentezi** | Tüm mülakat verileri, bulgu kategorilerine (pain_point, value, objection, pricing, positioning, risk) göre sentezlenir |
| 16 | **Executive Summary** | Bulgulardan 3-5 maddelik karar vericilere yönelik özet üretir |
| 17 | **Kanıt Bağlı Bulgular (Evidence-Linked Findings)** | Her bulgu, hangi personanın hangi cevabından geldiğini gösterir |
| 18 | **Van Westendorp Fiyat Duyarlılığı Modeli** | Çok pahalı / pahalı / ucuz / çok ucuz eşiklerini hesaplar; OPP ve IPP noktaları çıkarır |
| 19 | **Marka Sağlığı (Brand Health)** | Spontan hatırlama, çağrışımlar, zihin payı ölçümü |
| 20 | **Kanal Haritası** | Personaların ürüne nasıl ulaşacağı (web, mağaza, sosyal medya vb.) dağılımı |
| 21 | **SES Cross-Tab Tablosu** | SES grubu × dominan stance × stance sayıları çapraz tablosu |
| 22 | **Respondent Type Özeti** | Her rol tipi için fiyat hassasiyeti, en çok dile getirilen acı noktası ve itiraz |
| 23 | **Adversarial Review (S2)** | Üç aşamalı bağımsız denetim: bias_audit → evidence_chain_validation → double_simulation_check |
| 24 | **Research Fidelity Index — RFI (S3)** | Bilal (2026) metodolojisine göre 6 bileşenli araştırma kalite skoru (PGR, CNS, AC, PR, PCal, CRA). Eşik ≥0.65 |
| 25 | **Validation Next Steps** | Araştırmadan sonra yapılacak gerçek dünya doğrulama önerilerini otomatik üretir |
| 26 | **Ki-Kare Anlamlılık Testi** | Stance-tercih ilişkisinin istatistiksel anlamlılığını test eder (p-değeri) |
| 27 | **Pain Point Matrisi** | Tüm persona × soru kombinasyonlarını acı noktası etiketlerine göre görselleştirir |
| 28 | **Kalite Bayrakları (Quality Flags)** | Tekdüze yanıt, sosyal beğeni etkisi, görünür düşünce zinciri gibi sorunları tespit eder |

---

## 💻 Frontend (Next.js İstemci Arayüzü)

| # | Özellik | Ne işe yarar? |
|---|---|---|
| 29 | **Dashboard — Araştırma Geçmişi** | Tüm araştırma projelerini listeler; durum, tarih, rapor görüntüleme |
| 30 | **Yeni Araştırma Akışı (4 adım)** | Defne ile sohbet → plan onay → persona paneli → mülakat akışı — tek sayfada uçtan uca |
| 31 | **Gerçek Zamanlı Mülakat Akışı** | SSE ile persona cevapları karakter karakter yazar; bekleme ekranı göstermez |
| 32 | **Araştırma Detay Sayfası (Tabs)** | Overview, Personas, Interviews, Report sekmelerine bölünmüş zengin rapor görünümü |
| 33 | **Van Westendorp PSM Grafiği** | CDF eğrilerini SVG ile inline çizer (Too Cheap, Cheap, Expensive, Too Expensive) |
| 34 | **Kanal Keşif Bar Chart** | Kanal dağılımını renk kodlu yatay çubuk grafikle gösterir |
| 35 | **RFI Kart + Bileşen Bar Chart** | Araştırma bütünlüğü skoru, geçerlilik rozeti, 6 bileşen mini bar chart |
| 36 | **Adversarial Flags Görünümü** | Adversarial review aşama rozetleri (✓ / ⚠) ve uyarı mesajları |
| 37 | **PDF İndirme** | Tamamlanmış araştırmayı PDF olarak indirir |
| 38 | **Araştırma Arşivleme** | Çalışmaları arşive taşır; varsayılan listede göstermez |
| 39 | **Bulgu Feedback (Like/Dislike)** | Kullanıcı her bulguyu beğenebilir/beğenmeyebilir; admin panelinde toplanır |

---

## 🛠️ Admin Paneli

| # | Özellik | Ne işe yarar? |
|---|---|---|
| 40 | **İstemci Yönetimi** | Müşteri oluştur, düzenle, sil; plan tipi, simülasyon ve token limiti ata |
| 41 | **Plan Tipi Atama** | Her müşteriye Free / Starter / Pro / Enterprise plan atanabilir |
| 42 | **Token ve Simülasyon Limiti** | Müşteri başına `max_simulations` ve `max_tokens` alanları DB'de takip edilir |
| 43 | **Persona Havuzu Yönetimi** | Sistemdeki tüm personaları görüntüle; persona havuzunu yönet (admin) |
| 44 | **Soru Koleksiyonu (Curated Questions)** | Araştırmalarda üretilen soruları beğen, sınıflandır, sil; fine-tuning verisi için |
| 45 | **Sistem Konfigürasyonu** | Varsayılan pazar, kategori, fiyat aralığı, satış kanalı, başarı metriği ayarları |
| 46 | **Varsayılan Mülakat Soruları** | Admin panelinden mülakat soru şablonunu DB'ye kaydeder; tüm araştırmalara uygulanır |
| 47 | **Geri Bildirim Merkezi** | Tüm kullanıcı feedback'lerini (like/dislike/yorum) tek ekranda görüntüler |
| 48 | **Audit Log** | Sistemdeki işlem geçmişini kaydeder ve listeler |
| 49 | **Agent Şema Görüntüleyici** | Brief, persona, mülakat, sentez şemalarını ve concept pool'larını gösterir |

---

## 🔐 Altyapı ve Güvenlik

| # | Özellik | Ne işe yarar? |
|---|---|---|
| 50 | **Çift Model Konfigürasyonu** | B2C ve B2B için ayrı model seçimi; admin panelinden değiştirilebilir |
| 51 | **Mailer Entegrasyonu** | E-posta gönderimi için altyapı (rapor paylaşımı, bildirim) |
| 52 | **Privacy Modülü** | Hassas verilerin maskelenmesi ve gizlilik kuralları |
| 53 | **DB Auth** | İstemci kimlik doğrulama altyapısı |
| 54 | **Araştırma Kalitesi İzleme** | Her araştırmaya `quality_score`, `quality_grade`, `quality_summary` atanır |

---

**Toplam: 54 özellik**

> Sonraki adım: Bu özellikleri Free / Starter / Pro / Enterprise planlarına dağıtmak.
