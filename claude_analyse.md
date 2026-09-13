# Clarere — Product Manager + Senior Full-Stack Durum Analizi

> **Analiz tarihi:** 13 Eylül 2026  
> **Kapsam:** Ürün stratejisi, kullanıcı deneyimi, bilimsel iddialar, mimari, güvenlik, operasyon, kalite, monetizasyon ve satışa hazırlık  
> **İncelenen ana kaynaklar:** `README.md`, `MEMORY.md`, `DESIGN.md`, `REKABET.md`, `SUNUM.md`, `UNIT_ECONOMICS.md`, `server_plan.md`, `packages/prompts/research_rules.md`, alt README dosyaları, bağımlılık/compose dosyaları ve kritik uygulama modülleri  
> **Kapsam dışı:** Canlı sunucu kurulumu ve ertelenmiş Enterprise yerel model/embedding uygulamaları

---

## 1. Yönetici Özeti

Clarere, sıradan bir LLM persona arayüzünden belirgin biçimde ileri seviyededir. Ürün; brief toplama, deterministik persona paneli kurma, hipotez-kör mülakat, anti-dalkavukluk kontrolleri, kanıt zinciri, karar katmanı, fiyat analizi ve zengin rapor üretimini tek akışta birleştirir. Teknik olarak çalışan bir beta ürün, güçlü bir yatırımcı demosu ve kontrollü pilot müşteri çalışmaları için yeterli seviyededir.

Buna karşılık Clarere henüz geniş ölçekte production-ready ve hukuken risksiz biçimde satılabilir bir SaaS olarak değerlendirilmemelidir. En büyük açıklar yeni özellik eksikliği değil; bilimsel/pazarlama iddialarının kanıt seviyesi, doküman tutarsızlığı, bazı büyük modüllerin bakım maliyeti, gerçek kullanıcı doğrulamasının sınırlı olması ve canlı operasyon katmanının ertelenmiş olmasıdır.

### Genel olgunluk skoru

| Alan | Skor | Değerlendirme |
|---|---:|---|
| Ürün fikri ve değer önerisi | 8.5/10 | Net, farklılaştırılmış, demo edilebilir |
| Araştırma akışının bütünlüğü | 8.5/10 | Brief → persona → mülakat → kanıt → rapor zinciri güçlü |
| Frontend ürün deneyimi | 7.5/10 | Ana akış tamam; yoğun ekranlar ve metin yükü var |
| Backend/domain mimarisi | 7.5/10 | Güçlü fonksiyonellik; bazı modüller aşırı büyük |
| Test ve CI | 8.5/10 | 366 test + typecheck/lint + Playwright; DB/LLM canlı test ayrımı daha görünür olmalı |
| Bilimsel savunulabilirlik | 6/10 | Mekanizmalar güçlü; dışa dönük bazı iddialar fazla kesin veya doğrulanamaz |
| Güvenlik ve KVKK hazırlığı | 7.5/10 | İyi temel; production secrets, hukuk ve altyapı doğrulaması bekliyor |
| Monetizasyon | 7/10 | Plan gate ve Paddle sandbox hazır; fiyat-pazar uyumu doğrulanmamış |
| Operasyon/observability | 5.5/10 | Docker ve CI hazır; canlı monitoring, SLA, backup çalıştırması ertelendi |
| Satışa hazırlık | 7/10 | Pilot/beta satılabilir; kurumsal SLA ve iddia paketi hazır değil |

### Son karar

- **Yatırımcı/yönetici demosu:** Evet, hazır.
- **Kontrollü beta ve tasarım partneri satışı:** Evet, doğru beklenti yönetimiyle hazır.
- **Self-service public launch:** Teknik olarak yakın, operasyonel olarak ertelenmiş.
- **Enterprise sözleşmeli satış:** Hayır; ertelenmiş altyapı, hukuk, veri yerleşimi ve SLA katmanı tamamlanmalı.
- **Bilimsel olarak doğrulanmış araştırma platformu iddiası:** Şu an bu kesinlikte kullanılmamalı. Doğru ifade “bilimsel çerçevelerden yararlanan, yönlendirici sentetik araştırma sistemi” olmalıdır.

---

## 2. Ürünün Ne Yapmak İstediği

Clarere’nin temel işi, gerçek kullanıcı araştırmasının yerine geçmek değil, araştırma öncesi belirsizliği azaltmaktır:

1. Kullanıcı Defne ile ürün fikrini ve araştırma problemini tanımlar.
2. Sistem brief’i yapılandırır ve görüşme senaryosu üretir.
3. TÜAD SES ve Rogers duruş dağılımından yararlanan persona paneli kurar.
4. Big Five, kültürel bağlam ve anti-sycophancy kurallarıyla persona görüşmeleri simüle edilir.
5. Cevaplardan bulgu, destekleyen/karşı çıkan kanıt ve karar sinyali çıkarılır.
6. Van Westendorp, segment analizi, harici kanıt ve adversarial review ile rapor zenginleştirilir.
7. Kullanıcı çıktıyı gerçek müşteri görüşmesi, satış testi veya saha araştırması için hipotez kaynağı olarak kullanır.

Bu tanım ürünün en savunulabilir ve satılabilir konumudur. “Gerçek kullanıcı olmadan gerçek içgörü” söylemi dikkat çekici olsa da bilimsel ve hukuki açıdan “gerçek kullanıcı araştırmasından önce daha iyi hipotez” söylemi daha güvenlidir.

---

## 3. Product Manager Değerlendirmesi

### 3.1 Güçlü değer önerisi

Clarere aşağıdaki sorunları aynı anda çözüyor:

- Erken aşama ekiplerin araştırma bütçesi bulamaması
- Kullanıcı görüşmelerinin yavaş ve operasyonel olarak zahmetli olması
- Düz LLM promptlarının aşırı uzlaşmacı, tekrarlı ve izlenemez olması
- Ürün fikirlerinin fiyat, bariyer ve segment boyutunda yeterince sınanmaması
- Araştırma bulgularının kanıta bağlanmadan sunulması

En güçlü ürün vaadi “2 dakikada araştırma” değil; **persona → mülakat → kanıt → karar zincirinin izlenebilir biçimde ürünleştirilmesi**dir.

### 3.2 Farklılaştırıcı unsurlar

| Farklılaştırıcı | Gerçek değer | Savunulabilirlik |
|---|---|---|
| Türkiye odağı | SES, dil, TL, kültürel davranış ve yerel satın alma bağlamı | Yüksek |
| Hipotez-kör mülakat | Personanın araştırmacı hipotezine göre cevap vermesini azaltır | Yüksek |
| Skeptic zorunluluğu | Her panelde itiraz üretme olasılığını artırır | Yüksek |
| Kanıt zinciri | Bulguyu persona/soru/yanıta bağlar | Çok yüksek |
| Karar katmanı | Araştırmayı aksiyon diline çevirir | Yüksek |
| Echo/acquiescence kontrolleri | LLM tekdüzeliğini görünür ve azaltılabilir yapar | Orta-yüksek |
| Van Westendorp | Fiyat konuşmasını yapılandırır | Orta; sentetik panel olduğu açıkça belirtilmeli |
| Harici kanıt | Sentetik sonucu dış kaynakla karşılaştırır | Orta; kaynak kalitesi ve sahte fallback riski yönetilmeli |
| RFI | Kaliteyi sistematik ölçme hedefi | Potansiyel yüksek; mevcut eşleştirme yöntemi sınırlı |

### 3.3 Kullanıcı segmentleri

Önerilen öncelik sırası:

1. **Ürün danışmanları ve araştırma ajansları:** Çıktıyı yorumlayabilir, metodolojik sınırları anlar, yüksek ödeme isteğine sahiptir.
2. **B2B SaaS ürün ekipleri:** Mesajlaşma, fiyatlandırma, itiraz ve onboarding hipotezleri için sık kullanım sağlar.
3. **Erken aşama kurucular:** Güçlü edinim kanalıdır; bütçe ve churn riski yüksektir.
4. **Growth/kreatif ekipler:** A/B, mesaj ve teklif testlerinden değer görür.
5. **Siyasi araştırma:** Ayrı ürün/release olmalıdır. Yasal, etik ve itibar riski nedeniyle genel akışa hızlıca eklenmemelidir.

### 3.4 Ürün paketleme ve fiyatlandırma

Mevcut USD fiyatları:

- Free: $0, 1 ay veya 2 araştırma
- Flex: $49, 3 araştırma
- Starter: $69/ay
- Pro: $169/ay
- Enterprise: özel

COGS fiyatlandırmayı sınırlamıyor. Asıl soru müşterinin sonuçlara güveni ve iş akışındaki değerdir. Bu nedenle fiyat doğrulaması yalnızca maliyet + marj üzerinden yapılmamalı; aşağıdaki metriklerle ölçülmelidir:

- Brief başlatma → araştırma tamamlama oranı
- Araştırma tamamlama → rapor görüntüleme oranı
- Free limit → upgrade CTA tıklama oranı
- Paddle checkout başlatma → ödeme oranı
- 30 günlük tekrar araştırma oranı
- Rapor indirme/paylaşma oranı
- Araştırma başına kullanıcı tarafından kabul edilen aksiyon sayısı
- Sentetik bulgunun gerçek görüşmede doğrulanma oranı

Flex ile Starter arasında değer açıklaması netleştirilmelidir. Flex tek seferlik satın alma, Starter devam eden iş akışı olarak konumlanmalı; yalnız kota farkı gibi görünmemelidir.

### 3.5 Free plan stratejisi

Free planın iki kapılı yapısı mantıklı:

- 30 gün
- 2 araştırma
- Hangisi önce biterse trial sona erer

Fakat “2 araştırma ücretsiz” ile “tam rapor ücretli” söylemi kullanıcıda çelişki yaratabilir. Ürün dili şu şekilde ayrılmalıdır:

- Ücretsiz araştırma çalıştırma hakkı
- Ücretsiz sınırlı rapor önizlemesi
- Tam rapor ve export için ücretli plan

Bu ayrım fiyatlandırma, FAQ, onboarding ve paywall metinlerinde aynı olmalıdır.

### 3.6 Rapor ürünü

Referans çalışma `study_1789318823185` iyi bir ürün standardı oluşturuyor. Rapor artık:

- Yönetici özeti
- Persona paneli
- Pain-point matrisi
- Kanıtlı bulgular
- Van Westendorp PSM
- Karar katmanı
- Harici kanıt
- SES × stance
- Marka sağlığı
- Keşif kanalı
- Stratejik öneriler
- Kalite ve sınırlılıklar

bölümlerini içeriyor.

Bu kapsam yatırımcı demosu ve pilot müşteri için doyurucudur. Ancak rapor kalitesi yalnız uzunlukla ölçülmemelidir. Ürün metriği olarak şunlar eklenmelidir:

- Bulgu başına benzersiz persona sayısı
- Bulgu başına karşı kanıt oranı
- Tekrarlanan öneri oranı
- Kaynaksız iddia oranı
- Kullanıcı tarafından yararlı işaretlenen öneri oranı
- Gerçek kullanıcı araştırmasında doğrulanan tema oranı

---

## 4. Bilimsel ve Metodolojik Değerlendirme

### 4.1 İyi yapılanlar

Kod tabanında bilimsel çerçeve yalnız pazarlama metni değildir; davranışa dönüştürülmüş bileşenler vardır:

- Rogers stance ataması
- TÜAD SES kotası ve Largest Remainder dağıtımı
- Big Five/OCEAN sayısal alanları
- NEO facet yaklaşımları
- Hipotez-kör prompt tasarımı
- ELEPHANT anti-sycophancy promptu
- Hofstede Türkiye bağlamı
- Skeptic zorunluluğu
- Jaccard echo kontrolleri
- EWMA kalite izleme
- Acquiescence ve meta-tone kontrolleri
- Persona izolasyonu
- Kanıt zinciri
- Adversarial review
- Gerçek kullanıcı doğrulaması önerisi

Yeni doğal persona biyografisi özelliği de bilimsel atamaları değiştirmiyor. Yalnızca `bio` alanını yeniden yazar; Big Five, Rogers stance, SES, NEO facet ve davranış girdileri korunur. Ayrıca `bio`, mülakat davranış prompt'unun belirleyicisi değildir.

### 4.2 Bilimsel iddia riskleri

En ciddi ürün riski kod değil, dokümanlarda kullanılan kesin dildir.

#### Kanıtı açıkça gösterilmesi gereken iddialar

- “Grounded Simulation (Bilal, 2026)”
- “46 çalışmada RFI = 0.815”
- “Uzman referansın %93’ü”
- “23 kör UX araştırmacısı”
- “Değerlendiricilerin %65’i insan üretimi dedi”
- “7.5× daha az gürültü”
- “Stance Diversity ΔF1 = −0.582”
- “Rakiplerin hiçbirinde metodoloji yok”
- “Dalkavukluk yapmayan tek sistem”
- “Türkiye’de yerel rakip yok”

Bu iddialar yayımlanmış, erişilebilir ve bağımsız kaynaklarla desteklenmiyorsa landing page, JSON-LD, yatırımcı sunumu ve satış materyalinde kesin gerçek olarak kullanılmamalıdır.

Özellikle `layout.tsx` içindeki FAQ JSON-LD doğrudan arama motorlarına yapılandırılmış bilimsel iddia yayımlıyor. Buradaki yanlış veya doğrulanamayan ifade, normal pazarlama metninden daha yüksek itibar ve uyum riski taşır.

#### RFI sınırı

`benchmark.py` gerçek embedding/semantic model yerine `SequenceMatcher + token Jaccard` hibriti kullanır. Bu yöntem tekrarlanabilir ve ucuzdur; ancak “anlamsal doğruluk” iddiası için sınırlıdır. Eşikler kod içinde sabittir ve geniş, bağımsız Türkçe benchmark ile kalibre edildiğine dair repoda doğrulanabilir kanıt yoktur.

Bu nedenle:

- RFI, “ürün içi kalite/uyum göstergesi” olarak sunulabilir.
- “Bağımsız bilimsel doğruluk endeksi” olarak sunulmamalıdır.
- “Üretime hazır” ifadesi `_rfi_interpretation` içinde aşırı kesin; “yüksek referans uyumu” gibi daha temkinli ifade tercih edilmelidir.

#### Van Westendorp sınırı

Van Westendorp yöntemi gerçek katılımcı yanıtları için tasarlanmıştır. Sentetik persona cevaplarına uygulanması yapılandırılmış fiyat hipotezi üretir; istatistiksel fiyat araştırması üretmez. Rapor ve UI bu ayrımı sürekli göstermelidir.

### 4.3 Metodolojik tutarlılık sorunu

README “minimum 3 stance” derken ana akış 5 kişilik panelde doğrudan beş farklı stance zorlar. Bu tasarım anti-sycophancy için güçlüdür, ancak TÜAD/gerçek pazar temsili iddiasıyla karıştırılmamalıdır. Stance çeşitliliği araştırma sağlamlığı guard'ıdır; nüfus temsili değildir.

Ayrıca 10 persona vaat edilmesine rağmen referans akış ve bazı dokümanlar 5 persona üzerinden anlatılıyor. Plan tablosu, gerçek `generate_personas()` varsayılanı ve satış metni aynı panel boyutunu ifade etmelidir.

### 4.4 Önerilen bilimsel konumlandırma

Kullanılması gereken ifade:

> Clarere, davranış bilimi ve araştırma metodolojisi çerçevelerinden yararlanan sentetik bir hipotez üretme ve araştırma triage platformudur. Çıktılar istatistiksel temsil iddiası taşımaz; yüksek riskli kararlar gerçek kullanıcı, satış veya saha verisiyle doğrulanmalıdır.

Kaçınılması gereken ifade:

> Gerçek kullanıcı olmadan gerçek içgörü, insan araştırmasıyla eşdeğer doğruluk, bilimsel olarak kanıtlanmış pazar sonucu.

---

## 5. Kullanıcı Deneyimi ve Frontend

### 5.1 Güçlü yönler

- Landing, fiyatlandırma, use-case landing sayfaları ve FAQ mevcut.
- Defne → araştırma → çalışma detayı akışı tamam.
- Plan paywall ve buzlu rapor önizlemesi ürünleştirilmiş.
- Çalışma detayı altı temel sekmeyi eksiksiz gösteriyor:
  - Özet & Hedefler
  - Personalar
  - Senaryo
  - Mülakat Kayıtları
  - Kanıt Zinciri
  - Sentez Raporu
- Big Five radar, SES × stance, Van Westendorp ve kanal görselleri raporu zenginleştiriyor.
- Transkript dialogu ve persona follow-up akışı mevcut.
- Admin paneli müşteri alanından ayrılmış ve doğrudan landing bağlantısı kaldırılmış.
- TypeScript strict, typecheck ve lint CI'da çalışıyor.

### 5.2 UX ve bakım riskleri

Dört ana sayfa aşırı büyük:

| Dosya | Satır |
|---|---:|
| `client/studies/[id]/page.tsx` | 2309 |
| `admin/page.tsx` | 1470 |
| `page.tsx` | 869 |
| `client/new/page.tsx` | 620 |

Bu durum:

- Görsel değişikliklerde regresyon riskini artırır.
- Plan gate, veri formatlama ve API mantığını UI içine gömer.
- Kod review'u ve test izolasyonunu zorlaştırır.
- Client bundle ve hydration karmaşıklığını büyütebilir.

Önerilen parçalama:

- `features/studies/components/SummaryTab.tsx`
- `PersonaPanel.tsx`
- `InterviewTranscriptDialog.tsx`
- `EvidenceTab.tsx`
- `ReportTab.tsx`
- `hooks/use-study-detail.ts`
- `lib/study-normalizers.ts`
- `features/admin/*`
- `features/pricing/*`

Bu refaktör yeni özellik değil, sürdürülebilirlik yatırımıdır.

### 5.3 Tasarım sistemi

`DESIGN.md` iyi tanımlı bir sistem sunuyor: beyaz/mineral yüzeyler, koyu yeşil bantlar, coral vurgu, ince border, düşük gölge, açık alan ve iki font karakteri.

Riskler:

- Tasarım belgesi Cohere türevi görsel analiz olarak tanımlanıyor; marka özgünlüğü daha da ayrıştırılmalı.
- Büyük study/admin ekranlarında çok sayıda kart kullanımı, belgenin “her bölümü karta dönüştürmeyin” kuralıyla gerilim yaratıyor.
- `DESIGN.md` exact fontların paketlenmediğini söylüyor; uygulama Space Grotesk/Space Mono kullanıyor. Bu kabul edilebilir fallback, fakat belge ile gerçek tokenlar tek SSOT değil.
- Mobile ekran görüntüleri yeniden üretilmemiş. Kritik çalışma detayı ve rapor için 375px/768px görsel regresyon testi gereklidir.

### 5.4 Frontend doküman borcu

`apps/frontend/README.md` hâlâ create-next-app boilerplate'idir ve yanlış port (`3000`), yanlış font (`Geist`) ve genel Vercel metni içerir. Bu, repo inceleyen yatırımcı/teknik ekip için düşük kalite sinyalidir. Clarere’ye özel setup, env, proxy ve test bilgileriyle değiştirilmelidir.

### 5.5 İçerik kalitesi

`layout.tsx` içinde görülen yazım hataları:

- “yapıy zeka”
- “büdçe”
- “büyme”
- “değlendirmede”

Ayrıca landing FAQ'da “Clarere'nun” kullanımı hatalıdır. Kurumsal görünüm için tüm public metinler otomatik spellcheck veya içerik checklist'inden geçmelidir.

Enterprise metnindeki `%100 Yerel Veri Lokalizasyonu (2026 KVKK Uyumlu)` iddiası mevcut aktif altyapıyla doğrulanmıyorsa kaldırılmalı veya “kurumsal kurulum seçeneği” olarak gelecek zamanla yazılmalıdır.

---

## 6. Backend ve Mimari

### 6.1 Güçlü yönler

- FastAPI API katmanı ile domain motoru ayrılmış.
- Senkron ve Celery akışı `research_runner.py` ortak çekirdeğinde birleşiyor.
- PostgreSQL connection pool kullanılıyor.
- RLS tenant/org bağlamı var.
- Migration sistemi idempotent.
- Kota artışı atomik.
- LLM çağrıları timeout/retry/deadline ile korunuyor.
- Token muhasebesi ve maliyet tablosu var.
- İçerik-hash LLM cache ve DeepSeek prefix-cache uyumlu prompt sırası mevcut.
- Model effort rol bazlı: intake düşük, mülakat yüksek, sentez maksimum.
- API ve Celery container'ları ayrı.
- Degradasyon rapora taşınıyor; harici kaynak başarısızlığı gizlenmiyor.
- PII regex maskesi her planda, yerel NER Enterprise gate arkasında.

### 6.2 Teknik borç ve refaktör ihtiyacı

Ana backend dosyaları çok büyük:

| Dosya | Satır |
|---|---:|
| `database.py` | 1954 |
| `client.py` | 1917 |
| `analytics.py` | 1534 |
| `workflow.py` | 1355 |

Önerilen ayrım:

- `database/clients.py`, `database/studies.py`, `database/usage.py`, `database/migrations.py`
- `routers/intake.py`, `routers/research.py`, `routers/studies.py`, `routers/privacy.py`
- `analytics/findings.py`, `analytics/pricing.py`, `analytics/quality.py`, `analytics/report_enrichment.py`
- `workflow/personas.py`, `workflow/interviews.py`, `workflow/prompts.py`

Bu dosyalar çalışıyor olsa da tek değişiklikte geniş etki alanı yaratıyor. Özellikle `client.py` API, plan enforcement, persistence ve LLM orchestration sorumluluklarını birlikte taşıyor.

### 6.3 Model/domain tutarlılığı

`Persona` frozen dataclass kullanımı iyi bir immutability kararıdır. Son doğal bio geliştirmesinde `dataclasses.replace()` ihtiyacının ortaya çıkması, bu modelin doğru koruma sağladığını gösterir.

Buna karşılık:

- Bazı yollar dataclass, bazı yollar dict kullanıyor.
- Sentez/render katmanında tolerant `_g()` gibi çözümler geçmişte dict/object uyumsuzluğunu kapatmak zorunda kalmış.
- API sınırında Pydantic DTO → domain dataclass → persistence schema dönüşümleri merkezi mapper katmanında toplanmalıdır.

### 6.4 Harici kanıt sistemi

`SearXNGRetriever` başarısız olduğunda boş liste döndürüyor; bu doğru graceful degradation davranışıdır.

Ancak `Crawl4AIExtractor`, paket yoksa `[Mock Content for ...]` döndürüyor. Mock içerik production raporuna ulaşabiliyorsa bu kritik güven sorunudur. Production'da mock metin hiçbir zaman kanıt olarak kullanılmamalıdır. Doğru davranış:

- Development/test: açıkça test fixture
- Production: boş sonuç + degradation note
- Kaynak doğrulama: URL, tarih, domain, başlık ve erişim zamanı saklama

### 6.5 WebSocket hata yönetimi

`client.py` WebSocket kapanışlarında bare `except: pass` kullanıyor. Bağlantı kapanması için bazı istisnaların yutulması normal olabilir; fakat yalnız `WebSocketDisconnect` ve beklenen network istisnaları yakalanmalı, beklenmeyen hata loglanmalıdır.

### 6.6 Bağımlılık yönetimi

Python bağımlılıkları pinlenmiştir; bu reproducibility açısından güçlüdür. Frontend doğrudan bağımlılıkları exact ve caret karışımıdır, fakat `package-lock.json` CI'da `npm ci` ile kullanıldığı için deterministik kurulum sağlanır.

Dikkat noktaları:

- `psycopg2-binary` production için çalışır; uzun vadede psycopg 3 değerlendirilmesi performans ve async seçenekleri için düşünülebilir.
- `pandas`, `numpy`, `altair`, `plotly`, `pyarrow` backend image'ını büyütür. Gerçekte kullanılmayan analytics paketleri çıkarılmalı veya rapor worker image'ına ayrılmalıdır.
- `crawl4ai` kodda opsiyonel fakat requirements'ta yoktur; bu özellik ya resmi olarak devre dışı bırakılmalı ya da ayrı optional dependency grubu olarak tanımlanmalıdır.

---

## 7. Güvenlik ve KVKK

### 7.1 Güçlü yönler

- JWT secret production'da zorunlu.
- Admin secret timing-safe karşılaştırılıyor.
- Development `X-Username`, production JWT ayrımı var.
- Admin başarısız girişleri audit log'a yazılıyor.
- CORS production'da kısıtlanmak zorunda.
- Paddle webhook HMAC ve idempotency içeriyor.
- KVKK export/delete endpoint'leri var.
- Sentry PII gönderimi kapalı.
- Prompt PII maskeleme katmanı var.
- RLS tenant ve organizasyon erişimini sınırlar.
- Security headers ve CSP uygulanıyor.
- `/upgrade-plan` production'da kapalı.

### 7.2 Açık riskler

- Production güvenliği deploy edilmeden doğrulanmış sayılmaz. Secret, CORS, TLS ve RLS gerçek ortamda test edilmelidir.
- KVKK metni teknik uygulama ile hukuk görüşünün birleşimini gerektirir; kodun varlığı tek başına KVKK uyumu sağlamaz.
- Kullanım koşullarında “metodoloji ve algoritmalar tescilli fikri mülkiyettir” gibi ifadeler hukuki inceleme gerektirir.
- “%100 yerel veri lokalizasyonu” aktif servis DeepSeek iken doğru değildir; veri işleme lokasyonu ve alt işleyenler açıklanmalıdır.
- DeepSeek'e giden veri kategorileri, saklama politikası ve DPA şartları belgelenmelidir.
- API key daha önce sohbet ortamında paylaşılmıştır; bu anahtarın döndürülmüş/rotate edilmiş olduğu doğrulanmalıdır. Secret hiçbir repo veya dokümana yazılmamalıdır.
- Rate limiting tek instance için yeterli olabilir; distributed deployment'ta Redis-backed limit doğrulanmalıdır.

---

## 8. Test, CI ve Kalite

### 8.1 Mevcut durum

- En son tam yerel süit: **366 passed**.
- GitHub Actions CI: backend pytest + frontend typecheck + lint yeşil.
- Actions güncel v7 sürümlerine yükseltilmiş ve uyarısız çalışmıştır.
- Playwright üç ana alanı kapsar:
  - Landing/login/upgrade/admin
  - Gerçek LLM research flow
  - Study sekmeleri/transkript/sentez
- E2E maliyetli olduğu için manuel/haftalık ve DeepSeek secret gate'lidir.
- Test kullanıcıları Free/Flex/Starter/Pro/Enterprise olarak mevcuttur.
- Plan gate canlı olarak doğrulanmıştır.

### 8.2 Doküman drift

Test sayıları ciddi biçimde tutarsızdır:

- `README.md`: 187 + 1 skipped
- `MEMORY.md` başı: 290 + 10 skipped
- `MEMORY.md` alt bölümler: 304, 344, 354, 364 ve 366
- Gerçek son tam süit: 366 passed

README ve MEMORY tarihsel günlük ile güncel SSOT'yi karıştırıyor. Öneri:

- README yalnız “güncel doğrulama” tablosu taşımalı.
- MEMORY tarihsel olay günlüğü olabilir, fakat üstte tek bir `Current State` bölümü bulunmalı.
- Test sayısı CI tarafından badge veya otomatik script ile güncellenmeli.

### 8.3 Test kapsamındaki kalan boşluklar

- Production JWT + CORS + Caddy gerçek domain E2E
- Paddle live webhook ve ödeme lifecycle
- Backup restore tatbikatı
- Resend gerçek teslimat testi
- Sentry gerçek exception capture
- SearXNG gerçek kaynak kalite testi
- Büyük panel concurrency/load testi
- Celery worker crash/retry/idempotency testi
- Mobile visual regression
- PDF snapshot/golden test
- LLM model sürüm değişiminde kalite regresyonu
- Gerçek insan bulgularına karşı bağımsız benchmark

### 8.4 Test komutu gözlemi

Bu analiz sırasında doğrudan tam pytest komutu 120 saniyelik tool sınırında sonuç üretmeden zaman aşımına uğradı. Bu, önceki doğrulanmış 366 test sonucunu geçersiz kılmaz; ancak test komutunun bazen DB/env beklemesi veya süreç kapanışı nedeniyle uzayabildiğini gösterir. CI ve yerel DB-forward test akışları tek, belgeli komuta indirgenmelidir.

---

## 9. DevOps ve Operasyon

### 9.1 Güçlü hazırlık

- Local prod-like Docker stack hazır.
- Cloud compose ayrılmış.
- Caddy TLS/reverse proxy dosyaları var.
- Redis/Celery/SearXNG servisleri ayrılmış.
- Healthcheck ve log rotation cloud compose içinde mevcut.
- Neon, Vercel, VPS ve Oracle alternatifleri planlanmış.
- DB backup script'i mevcut.
- Sentry ve Resend env-gated.
- Rollback ve troubleshooting server planında belgelenmiş.

### 9.2 Production blocker'ları

Canlıya geçiş ertelenmiş olduğundan aşağıdakiler açık kalır:

- Domain ve TLS gerçek doğrulama
- Production JWT/CORS/secrets
- Paddle live catalog/webhook
- Backup cron + restore testi
- Sentry/Resend gerçek bağlantı
- Uptime ve alerting
- Queue monitoring
- Database migration release süreci
- SLA ve incident response

Bu nedenle “kod production'a yakın” denebilir, fakat “sistem production'da doğrulandı” denemez.

### 9.3 Altyapı planı tutarsızlığı

Dokümanlarda birincil plan değişmiştir:

- `server_plan.md`: Oracle Always Free birincil, netcup+Neon+Vercel ikincil
- README production bölümü: Vercel + netcup + Neon
- `docker-compose.prod.yml` başlığı: Hetzner
- MEMORY: Oracle blokeli, netcup yedek

Tek bir “onaylı hedef mimari” seçilene kadar bu belgeler statü etiketi taşımalıdır. Aksi halde deployment sırasında yanlış compose veya yanlış DB mimarisi seçilebilir.

---

## 10. Doküman ve Pazarlama Tutarlılığı

### 10.1 Kritik drift örnekleri

| Konu | Belge A | Belge B / Kod | Risk |
|---|---|---|---|
| Flash model adı | README/models README: `deepseek-v4-flash` | Kod/MEMORY: `deepseek-flash` | Yanlış kurulum |
| Timeout | README: 90 sn | MEMORY/kod: 120 sn | Operasyon şaşkınlığı |
| Plan fiyatı | SUNUM: TL | UNIT_ECONOMICS/UI: USD | Satış tutarsızlığı |
| Ödeme | SUNUM yol haritası: Stripe | Kod: Paddle | Yatırımcı güveni |
| Test sayısı | 187/290/304/344/354/364 | Gerçek: 366 | Teknik itibar |
| Panel boyutu | Bazı belgeler 5 | Plan/kota 10 | Ürün vaadi |
| Cloud mimari | Oracle / netcup / Hetzner | Birden fazla compose | Deploy riski |
| Rapor modeli | README `/synthesize`: model “—” | Gerçekte Pro zenginleştirme | Maliyet/işlev belirsizliği |
| Yerel veri | Enterprise metni %100 | DeepSeek aktif | Uyum riski |

### 10.2 Öncelikli doküman düzeltmeleri

1. `README.md` model adları, timeout, test sayısı, panel boyutu ve API model sütununu güncelle.
2. `SUNUM.md` tüm fiyatları USD yap; Stripe'ı Paddle olarak değiştir.
3. `apps/frontend/README.md` boilerplate'i kaldır.
4. `models/README.md` Flash model adını ve effort rollerini güncelle.
5. Public FAQ ve JSON-LD bilimsel iddialarını kaynaklı/temkinli hale getir.
6. `server_plan.md` başında “aktif plan / ertelenmiş / alternatif” matrisi oluştur.
7. MEMORY üstüne tek güncel durum özeti koy; tarihsel sayıları günlük olarak tut.

---

## 11. Rekabet Analizi Değerlendirmesi

`REKABET.md` yön gösterici olsa da satış veya yatırım materyali için yeterince derin ve doğrulanabilir değildir.

Sorunlar:

- Rakip listesi eksik ve bazı isimler genel/kanıtsız.
- Fiyat, özellik, hedef müşteri, fonlama, entegrasyon ve veri politikası karşılaştırması yok.
- “Rakiplerin hiçbirinde metodoloji yok” ve “yerel rakip yok” doğrulanması zor kesin iddialardır.
- Synthetic Users, UserTesting, Maze ve ChatGPT farklı kategorilerdedir; aynı tabloda değer zinciri bazında ayrıştırılmalıdır.

Önerilen rekabet matrisi:

- Sentetik araştırma platformları
- Gerçek kullanıcı araştırma platformları
- Survey/prototype test araçları
- Araştırma ajansları
- Genel LLM/DIY workflow

Karşılaştırma boyutları:

- Türkiye kültürel/SES desteği
- Persona izolasyonu
- Kanıt zinciri
- Karşı kanıt
- Fiyat testi
- Gerçek kullanıcı entegrasyonu
- Metodoloji açıklığı
- Export/API
- Kurumsal güvenlik
- Fiyat
- Veri işleme lokasyonu

Clarere’nin bugünkü savunulabilir wedge'i: **Türkiye bağlamlı, izlenebilir ve itiraz üretebilen sentetik araştırma workflow'u**dur.

---

## 12. Birim Ekonomi ve Ticari Gerçeklik

`UNIT_ECONOMICS.md` faydalı bir başlangıçtır ve varsayım olduğunu açıkça belirtmesi doğrudur.

Güçlü taraflar:

- Cache-hit/miss ayrımı
- Peak/off-peak ayrımı
- Flash/Pro rol ayrımı
- Retry/echo/adversarial çarpan riskinin kabulü
- Token usage tablosuyla gerçek veriye geçiş yolu

Eksikler:

- Paddle komisyonu ve vergi/MoR etkisi
- Vercel/VPS/Neon gerçek aylık sabit giderleri
- Resend/Sentry/backup maliyeti
- Support zamanı
- Chargeback/refund
- Free kullanıcı edinim maliyeti
- Pro “sınırsız” kullanım tail riski
- Persona bio için ek LLM çağrısı
- Harici arama ve gelecekteki scraping maliyeti

Brüt LLM marjı çok yüksek görünse de satılabilir SaaS marjı yalnız API maliyeti değildir. Yine de fiyatların teknik COGS tarafından rahatça taşındığı sonucu doğrudur.

---

## 13. Önceliklendirilmiş Açıklar

### P0 — Public launch öncesi zorunlu

1. Public JSON-LD ve landing bilimsel iddialarını doğrulanabilir hale getir.
2. “%100 yerel veri” gibi aktif mimariye uymayan iddiaları kaldır.
3. README/SUNUM/model doküman drift'ini kapat.
4. Production JWT, CORS, secrets, TLS ve RLS E2E çalıştır.
5. Paddle live lifecycle testini tamamla.
6. Backup cron kur ve restore tatbikatı yap.
7. Mock Crawl4AI içeriğinin production raporuna girmesini teknik olarak engelle.
8. API key rotation durumunu doğrula.

### P1 — Beta kalitesi ve bakım

1. Study detail, admin, analytics, workflow, database ve client router dosyalarını parçala.
2. API/domain/persistence mapper katmanı oluştur.
3. Frontend README'yi Clarere'ye özgü hale getir.
4. Mobile study/report E2E ve görsel regresyon ekle.
5. PDF golden/snapshot test ekle.
6. Gerçek kullanım KPI event şeması oluştur.
7. Free → paid funnel ölçümünü ekle.
8. Harici kanıt kaynak metadata ve güven derecelendirmesi ekle.
9. Test sayısını CI'dan otomatik raporla.

### P2 — Ürün savunulabilirliği

1. En az 20 gerçek araştırma brief'i için uzman referans benchmark oluştur.
2. İki bağımsız araştırmacıyla kör tema eşleme yap.
3. RFI eşiklerini bu veriyle kalibre et.
4. Sentetik bulgu → gerçek kullanıcı doğrulama oranını yayınla.
5. Persona tekrar üretilebilirliği ve model drift dashboard'u oluştur.
6. Prompt/model sürümünü her çalışmada sakla.
7. Rapor “hangi veri sentetik, hangi veri harici, hangi veri algoritmik” etiketlerini güçlendir.

### P3 — Ertelenmiş

- Enterprise yerel Türkçe LLM
- Embedding/persona vektör havuzu
- Yerel NER altyapısı
- Canlı sunucu/domain operasyonu
- Siyasi araştırma dikeyi

---

## 14. Önerilen 90 Günlük Ürün Planı

### Aşama 1 — Güven ve tutarlılık (1–2 hafta)

- Bilimsel iddia temizliği
- Public metin spellcheck
- Tüm doküman SSOT düzeltmesi
- Frontend README
- Mock kanıt engeli
- Production checklist'in executable hale getirilmesi

### Aşama 2 — Pilot ölçüm (2–4 hafta)

- 5–10 tasarım partneri
- Her partnerden 3 gerçek brief
- Rapor yararlılık puanı
- Öneri kabul oranı
- Gerçek görüşmede tema doğrulama oranı
- Upgrade willingness görüşmeleri

### Aşama 3 — Mimari sadeleştirme (3–6 hafta)

- Study detail component ayrımı
- Admin feature ayrımı
- Backend router/service/repository ayrımı
- Analytics alt modülleri
- Mapper/DTO katmanı
- PDF snapshot ve mobile E2E

### Aşama 4 — Public launch hazırlığı (altyapı kararı sonrası)

- Deploy
- Paddle live
- Backup/restore
- Sentry/Resend
- Load test
- Incident playbook
- Beta cohort

---

## 15. KPI Önerisi

### Acquisition

- Landing → research start
- SEO landing → signup
- Persona/use-case bazlı conversion

### Activation

- İlk brief tamamlama süresi
- İlk araştırma başarı oranı
- İlk rapor görüntüleme oranı
- İlk bulguya ulaşma süresi

### Value

- Rapor görüntüleme süresi
- PDF indirme
- Evidence expand oranı
- Follow-up kullanımı
- Kabul edilen öneri sayısı

### Revenue

- Free limit → upgrade CTA
- Checkout conversion
- Starter/Pro ARPA
- Refund/churn
- Plan başına gross margin

### Research Quality

- Cevapsız tur oranı
- Echo regeneration oranı
- Bulgu başına kanıt
- Karşı kanıt oranı
- Degradation note oranı
- Uzman doğrulama oranı
- Model sürümü bazında benchmark drift

---

## 16. SWOT

| Güçlü Yanlar | Zayıf Yanlar |
|---|---|
| Uçtan uca research workflow | Bilimsel iddialarda aşırı kesin dil |
| Türkiye bağlamı | Büyük monolitik dosyalar |
| Kanıt zinciri ve karar katmanı | Gerçek kullanıcı benchmark'ı sınırlı |
| Anti-sycophancy ve persona izolasyonu | Tek LLM sağlayıcısı (bilinçli karar) |
| Güçlü test/CI disiplini | Doküman drift |
| Çok düşük model COGS | Canlı operasyon ertelenmiş |

| Fırsatlar | Tehditler |
|---|---|
| Türkiye’de kategori liderliği | Global rakiplerin hızlı yerelleşmesi |
| Ajans ve B2B SaaS tasarım partnerleri | Sentetik araştırmaya güven sorunu |
| API/white-label dağıtımı | LLM fiyat/model değişimi |
| Gerçek araştırma triage pazarı | Bilimsel iddia/itibar riski |
| Doğrulanmış benchmark ile moat | KVKK ve veri lokasyonu riski |

---

## 17. Sonuç

Clarere, fonksiyonel kapsam, araştırma zinciri ve teknik kalite açısından güçlü bir beta üründür. Projenin en değerli tarafı persona üretmek değil; araştırma problemini yapılandırıp persona yanıtlarını kanıta, karşı kanıta ve karara dönüştüren mimarisidir. Bu yönüyle profesyonel rakiplerle yarışabilecek bir ürün çekirdeği vardır.

Bugünkü haliyle en doğru ticari statü:

> **Investor-demo ready + design-partner beta ready + production deployment pending.**

Satılabilirlik için yeni özellik eklemekten önce güven paketini tamamlamak gerekir:

1. İddiaları kanıt seviyesine göre yeniden yazmak
2. Doküman ve fiyat/plan SSOT'sini düzeltmek
3. Gerçek kullanıcı/uzman benchmark'ı üretmek
4. Büyük modülleri kontrollü biçimde parçalamak
5. Canlı operasyon checklist'ini uygulamak

Bu adımlar tamamlandığında Clarere yalnız çalışan bir demo değil, savunulabilir metodolojiye, ölçülebilir ürün değerine ve sürdürülebilir teknik temele sahip bir SaaS olarak konumlanabilir.
