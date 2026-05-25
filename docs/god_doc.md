# **BÜTÜNLEŞİK REHBER VE STRATEJİK YOL HARİTASI: YEREL DONANIM KISITLI ÇOKLU ETMEN TABANLI SENTETİK PAZAR ARAŞTIRMASI VE BİLİŞSEL AJAN MİMARİSİ**

## **1\. Giriş ve Teorik Temeller (Grounded Simulation Principle)**

Büyük dil modellerinin (LLM) salt sohbet arayüzlerinin ötesine geçerek otonom planlama yapabilen, harici araçları dinamik olarak tetikleyen ve karmaşık görevleri çok adımlı döngülerle çözebilen "yapay zekâ ajanları" (AI agents) haline gelmesi, yapay zekâ mühendisliğinin en kritik dönüşümlerinden biridir. Ajan sistemleri; planlama, eyleme geçme, gözlemleme ve yansıtma (ReAct) gibi döngüsel mantık yapıları üzerinde inşa edilmektedir.  
Ancak sentetik kullanıcı araştırmalarında, geleneksel stateless (durumsuz) LLM yapılarına düz prompt enjeksiyonu uygulamak metodolojik olarak kararsız çıktılar üretir. Bu açmazı çözmek amacıyla geliştirilen **Grounded Simulation Principle (Kanıtlanmış Simülasyon İlkesi)**, simülasyon doğruluğunun model kapasitesinden ziyade metodolojik temellendirmeye bağlı olduğunu savunur.

### **Dört Akademik Sütun**

Sistem başarısı, literatürde doğrulanmış dört temel bilimsel sütunun entegrasyonuna dayanmaktadır:

* **Psikometrik Temellendirme:** Personaların rastgele prompt'larla değil, NEO-PI-R (Büyük Beşli) ölçeğinde 30 alt faset düzeyinde niceliksel vektörlerle tanımlanması.  
* **Bilişsel Mimari Kontrolü:** İnsan zihninin çalışma prensiplerini taklit eden ACT-R tabanlı bellek sönümleme fonksiyonlarının entegre edilmesi.  
* **Metodolojik Filtreler:** Çok turlu diyaloglarda onaylama sapmasını sıfırlayan ELEPHANT çerçevesi ve mülakata tamamen kör girmeyi sağlayan Bağlam İzolasyonu (Context Isolation) protokolleri.  
* **Teknik ve Hiper-Yerel Entegrasyon:** Ulusal regülasyonların (KVKK, BDDK), yerel tüketici reflekslerinin ve Türkçe dil yeteneği kıyaslamalarının (Cetvel Benchmark) altyapıya işlenmesi.

### **Konuşma Paradoksu (Conversation Paradox)**

Ajan mühendisliğinde yapılan en büyük hatalardan biri, uzun ve etkileşimli sohbetlerin analiz kalitesini artıracağını varsaymaktır. Ampirik çalışmalar, LLM simülasyonlu 10 turlu ardışık bir iş akışının (takip soruları ve sentez döngüleri dahil) elde ettiği F1 skorunun (**0.065**), tek bir yalın prompt'un başarısının (**0.082**) dahi altında kaldığını kanıtlamıştır. Bunun temel nedeni, ardışık konuşma derinliğinin modeli descriptive (tanımlayıcı) kalıplardan uzaklaştırarak doğrudan çözüm odaklı tavsiyelere ("butonu yukarı taşı" vb.) zorlaması ve araştırma kapsamını daraltarak üslup kaymasına (style drift) yol açmasıdır.

## **2\. Yerel Türkçe Büyük Dil Modelleri (LLM) Ekosistemi ve Tokenizasyon Analizi**

Türkçe dilinde yerel (on-premise) olarak çalıştırılacak ajanların başarısı, dilin morfolojik karmaşıklığı, eklemeli yapısı ve kültürel bağlamı nedeniyle standart çok dilli küresel modellerin ötesinde yetenekler gerektirmektedir.

### **Tokenleştirici Verimliliği ve Doğurganlık Oranı (Fertility Rate)**

Standart çok dilli büyük dil modelleri (Llama, Qwen veya Gemma serileri), Türkçeyi ikincil veya üçüncül dil olarak ele aldıklarından kelimeleri çok sayıda alt-kelimeye (sub-token) bölmektedir. Modelin bir kelimeyi temsil etmek için harcadığı ortalama token miktarını gösteren **doğurganlık oranı (fertility rate)** yüksek olduğunda, yerel donanımlardaki RAM/VRAM bellek bant genişliği hızla tükenmekte, bağlam penceresi daralmakta ve işlem gecikmesi (latency) dikey olarak yükselmektedir.  
Sıfırdan Türkçe eğitilen Kumru serisi mimariler, bu problemi çözmek üzere özel bir Türkçe tokenizer tasarımı kullanır. Genel amaçlı çok dilli modeller, aynı Türkçe metni temsil edebilmek için Kumru'ya kıyasla **%38 ila %98** oranında daha fazla token harcamaktadır. Örneğin, Kumru'nun yerleşik 8,192 tokenlik bağlam penceresi, sunduğu tokenizasyon verimliliği sayesinde yabancı tokenizer'a sahip modellerin 11,000 ila 16,000 tokenlik etkin temsil gücüne denk gelmektedir.

### **Model Karşılaştırma Matrisi**

| Model Adı | Temel Mimari / Taban | Doğal Bağlam Sınırı | Karakteristik Odak Alanı ve Mimari Farkı | Lisans Türü |
| :---- | :---- | :---- | :---- | :---- |
| **Kumru-7B** | Mistral | 8,192 Token | Sıfırdan Türkçe ön eğitim, %38-%98 daha az token tüketimi. | Açık Kaynak / B2B Odaklı |
| **Kara-Kumru-v1.0-2B** | Kumru-2B | 8,192 Token | Cetvel Benchmark lideri, tüketici sınıfı kısıtlı donanımda yüksek çeviklik. | Açık Kaynak / İnce Ayarlı |
| **Trendyol-LLM-8B-T1** | Qwen 3-8B | 32,768 Token | Çift çalışma modu (/think ve /no\_think), e-ticaret korpusu. | Apache-2.0 |
| **Trendyol-LLM-7B-chat-v4.1.0** | Qwen2.5 7B | 32,768 Token | ChatML şablonu, eylemlere dayalı karakter yorumlama uzmanlığı. | Apache-2.0 |
| **Kizagan-E4B-Turkish-Reasoning-Model** | Google Gemma 4 E4B IT | 128,000 Token | Katman Başına Gömme (PLE), KV Önbellek Paylaşımı, içsel çıkarım blokları. | Apache-2.0 (Gemma 4 şartlarına tabi) |
| **Trendyol-LLM-Asure-12B** | Google Gemma 3-12B | 128,000 Token | Çoklu modlu (multimodal), 5:1 Yerel/Küresel Dikkat İnterleaving, GQA. | Apache-2.0 |
| **Turkish-LLM-14B-Instruct** | Qwen 2.5-14B | 32,768 Token | QLoRA \+ LowResource-LLM-Forge hattı, üst düzey talimat kararlılığı. | Ticari Olmayan / Araştırma |
| **Turkish-Gemma-4b-T1-Scout** | Gemma 3-4B | 32,768 Token | Cosmos Grubu, araç çağırma (tool/search calling) ve API dönüşüm uzmanı. | Gemma Lisansı |

### **Gelişmiş Mimari Özellikleri**

1. **Katman Başına Gömme (Per-Layer Embeddings \- PLE):** Kizagan-E4B modelinde kullanılan bu mimari, her transformatör katmanına özel bir embed\_tokens\_per\_layer tablosu atar. Girdiler her katmanda dinamik kapı mekanizmalarıyla normalize edilerek sorgulanır, böylece uzun bağlamlarda karakter özellikleri ve sistem yönergeleri bilişsel sönümlenmeye uğramaz. Matematiksel olarak süreç şu şekilde işletilir:  
   $$h\_l \= \\text{LayerNorm}(W\_{PLE} \\cdot x \+ h\_{l-1})$$  
2. **5:1 Ayrık Dikkat İnterleaving ve Grup-Sorgu Dikkati (GQA):** Trendyol-LLM-Asure-12B modelinde, uzun bağlamlarda KV önbellek boyutunu baskılamak için 5 adet yerel (sliding window \- son 1024 tokene odaklı) katmanın arasına 1 adet küresel (global \- tüm geçmişi tarayan) dikkat katmanı yerleştirilmiştir. GQA optimizasyonuyla birleşen bu hibrit yapı, 32,000 token gibi uzun geçmişlerde VRAM patlamalarını engeller.

### **Ulusal Akademik Standartlar: Cetvel Benchmark Başarımı**

KUIS-AI laboratuvarı tarafından duyurulan Cetvel Benchmark platformu, Türkçe dil modellerinin gerçek yeteneklerini ölçmek için geliştirilmiş 23 farklı dikey görevi içeren en kapsamlı değerlendirme standardıdır.  
Sadece 2 milyar parametreye sahip olan yerli **Kara-Kumru-v1.0-2B**, Cetvel testlerinde genel ortalamada **37.56** puana ulaşarak, parametre boyutu kendisinden 35 kat daha büyük olan küresel **Llama-3.3-70B-Instruct** modelini (**36.25**) geride bırakmıştır. Model; soru-cevaplama (QA) görevlerinde **32.54 F1**, özetleme (SUM) görevlerinde ise **32.55 ROUGE** skoru ile liderlik tablosundaki tüm açık kaynaklı küresel devlerin (72B parametreliler dahil) önüne geçmiştir. Bu ampirik veri, Türkçe dil yapısına ve kültürel kodlara (örneğin düzeltme işareti hassasiyeti ölçen CircumflexTR görevi) göre eğitilen yerli butik modellerin otonom etmen rollerinde sergileyeceği üstünlüğü kanıtlamaktadır.

## **3\. Donanım Kısıtlı Sistem Mimarisi ve Bellek Yönetimi (8 GB VRAM Sınırı)**

Sistem, bütçe kısıtları nedeniyle tek bir kurumsal iş istasyonu veya "Tek Kişilik AI Hobisti" donanım sınırları altında (%100 açık kaynak ve sıfır API maliyetiyle) kesintisiz çalışacak şekilde tasarlanmıştır.

* **Fiziksel Donanım Sınırı:** 1 adet 8 GB VRAM GPU (Örn: RTX 4060 Ti), 20 çekirdekli CPU, 32 GB Sistem RAM'i, 1 TB SSD.

### **Asenkron Mikroservis Bileşen İş Akışı**

Eş zamanlı çıkarım isteklerinin, veritabanı işlemlerinin ve raporlama motorlarının kısıtlı bellek sebebiyle Out-Of-Memory (OOM) hatası fırlatmasını önlemek için sistem gevşek bağlı (loosely coupled) asenkron bir mesaj kuyruğu (Redis tabanlı BullMQ) mimarisine oturtulmuştur.

* **PostgreSQL & pgvector:** Persona vektör gömmelerinin saklanması ve hibrid sorgulama.  
* **Ollama REST API:** GGUF formatındaki yerel modellerin yönetimi ve milisaniye hassasiyetli VRAM tahliyesi.  
* **Node.js & Rust-WASM:** İş akışı orkestrasyonu ve Event Loop'u bloke etmeyen yüksek performanslı regresyon motoru.  
* **Playwright & Chromium:** HTML/CSS şablonlarının ve dinamik grafiklerin baskı kalitesinde PDF raporlarına dönüştürülmesi.

### **Ollama Çıkarım Yapılandırması ve Aktif VRAM Temizleme Protokolü**

8B sınıfı bir model nicemlenmemiş haliyle yaklaşık 16 GB VRAM gerektirdiğinden, 8 GB fiziksel sınırlarda çalışabilmek için GGUF Q4\_K\_M (4.58 GB) veya Q5\_K\_M (5.34 GB) nicemlenmiş modeller zorunludur. Birden fazla model arasında geçiş yaparken bellek taşmasını önlemek amacıyla, işletim sistemi ve systemd servis katmanında (ollama.service) şu ortam değişkenleri optimize edilmiştir:

Ini, TOML  
OLLAMA\_MAX\_LOADED\_MODELS\=1  \# Aynı anda VRAM'e yalnızca tek bir modelin yüklenmesini zorunlu kılar.  
OLLAMA\_NUM\_PARALLEL\=1       \# İstek başına bağlam belleği ölçeklemesini sınırlandırarak OOM'u engeller.  
OLLAMA\_CONTEXT\_LENGTH\=4096  \# Yerel donanım kapasitesine uygun optimum bağlam penceresi.  
OLLAMA\_KV\_CACHE\_TYPE\=q4\_0   \# K/V belleğini nicemleyerek VRAM tüketimini radikal şekilde düşürür.

Her simülasyon görevinin başında modelin soğuk başlama (cold-start) gecikmesini önlemek için keep\_alive: \-1 parametresiyle model belleğe kalıcı olarak ön yüklenir. Görev tamamlandığında ise VRAM'i anında sıfırlamak ve sonraki süreçlere yer açmak için Ollama /api/chat uç noktasına asenkron olarak şu gövdeye sahip boş bir tahliye (flush) isteği gönderilir:

JSON  
{  
  "model": "llama-3-trendyol-llm-8b-chat-v2.0-q4\_k\_m",  
  "keep\_alive": 0  
}

### **Unsloth İle Yerel Persona İnce Ayar (Fine-Tuning) Hattı**

Ajanların belirli bir sektöre, markaya veya yerel slang yapılarına uyum sağlayabilmesi için platform, Unsloth kütüphanesinin PyTorch ve Triton ile optimize edilmiş 4-bit QLoRA (Quantized Low-Rank Adaptation) altyapısını kullanır. Unsloth, bellek tüketimini 4 kat azaltarak 8B modellerin 8 GB VRAM sınırında eğitilmesini sağlar.

Python  
\# Unsloth Donanım Optimizasyon Hiperparametre Matrisi  
load\_in\_4bit \= True                 \# Model ağırlıklarını 4-bit nicemleme ile yükler.  
max\_seq\_length \= 2048               \# Maksimum bağlam uzunluğu sınırı (8 GB VRAM için tavan 2,972 tokendir).  
per\_device\_train\_batch\_size \= 1     \# Aktivasyon yükünü minimumda tutarak OOM riskini sıfırlar.  
gradient\_accumulation\_steps \= 8     \# Batch size \= 1 kullanımının yarattığı dalgalanmayı dengeler.  
lora\_dropout \= 0                    \# Matematiksel çekirdek optimizasyonlarını tetikleyerek hızı artırır.  
bias \= "none"                       \# Sadece LoRA parametrelerini eğiterek bellek işgalini düşürür.

* **Veri Kümesi Boyutuna Göre Yönlendirme Stratejisi:** 300 satırdan az yüksek kaliteli veride, konuşma yeteneğini korumak için doğrudan talimat modelleri (Instruct); 300-1000 satır arasında esneklik tercihine göre Instruct/Base; 1000 satırdan fazla veride ise markaya tamamen yeni bir kimlik kazandırmak amacıyla temel modeller (Base Models) tercih edilir.  
* **Split LoRA ve MoE:** Çoklu uzman karakterlerin tek bir çatı altında çalışabilmesi için Triton MoE çekirdekleri üzerinden uzman katmanları sistem RAM'ine (32 GB) kaydırılır, böylece 8 GB VRAM üzerinde 30B boyutundaki Mixture of Experts modelleri kararlı şekilde koşturulur.

## **4\. pgvector Tabanlı Anlamsal Persona Modelleme ve Hibrid Arama**

Doğru sentetik tüketici kohortunun seçimi, personaların psikografik özelliklerinin (satın alma motivasyonları, teknoloji adaptasyon hızları) PostgreSQL veritabanında pgvector eklentisiyle anlamsal olarak indekslenmesine dayanır.

### **Uzaklık Metrikleri ve Tercih Senaryoları**

Vektör uzayındaki pazar eşleştirmelerinde pgvector tarafından desteklenen mesafe operatörlerinin stratejik kırılımı şu şekildedir:

* **Cosine Uzaklığı (\<=\>):** Vektörlerin büyüklüklerini göz ardı ederek sadece yönsel benzerliğe odaklanır. Tüketici ilgi alanları, marka algısı ve nitel psikografik profillerin anlamsal eşleştirilmesinde **birincil metrik** olarak tercih edilir.  
* **Negatif İç Çarpım (\<\#\>) :** Hem yönü hem de vektör büyüklüğünü dikkate alır. Tüketicinin ilgi alanının yanı sıra harcama hacmi veya satın alma frekansı gibi nicel büyüklükleri aynı anda değerlendirmek için kullanılır.  
* **Euclidean Uzaklığı (\<-\>):** Çok boyutlu uzayda iki nokta arasındaki en kısa düz çizgiyi hesaplar. Sadece standartlaştırılmış demografik yakınlıklara dayalı doğrusal gruplamalarda kısıtlı olarak tercih edilir.

### **HNSW İndeks Yapısı ve Hibrid SQL Sorgu Mimarisi**

Binlerce persona tablosunda doğrusal tarama (sequential scan) gecikmelerini önlemek amacıyla veritabanı seviyesinde **HNSW (Hierarchical Navigable Small World)** grafik indeksi kurulur. İlişkisel SQL filtreleri (yaş, cinsiyet, aktiflik durumu) ile anlamsal psikografik aramayı birleştiren hibrid sorgu yapısı, pgvector'ün JOIN yetenekleri sayesinde tek bir işlemsel döngü içinde çözülür:

SQL  
SELECT p.id, p.name, p.age,   
       (p.embedding \<=\> :query\_vector) AS distance   
FROM personas p   
WHERE p.status \= 'active'   
  AND p.age BETWEEN 18 AND 35   
ORDER BY p.embedding \<=\> :query\_vector   
LIMIT 100;

Bu hibrid yapı, ilişkisel indeksler ile HNSW indeksini aynı anda işleterek saniyeler içinde hedef kohortu süzüp asenkron simülasyon kuyruğuna aktarır.

## **5\. Bilişsel Hafıza Modellemesi, Zaman Sönümlemesi ve Karakter Kayması Kontrolü**

### **ACT-R Bilişsel Mimarisinin Matematiksel Temelleri**

Sentetik ajanların mülakat boyunca mantıksal iç tutarlılıklarını koruması ve insan zihninin doğrusal olmayan bilgi çağırma/unutma süreçlerini taklit edebilmesi, ACT-R (Adaptive Control of Thought-Rational) mimarisinin subsymbolic (sembol altı) katman denklemlerinin entegrasyonu ile sağlanır. Bildirimsel bellekteki her bir bilgi biriminin (chunk) anlık geri çağrılma başarısı, anlık Aktivasyon Değeri ($A\_i$) ile belirlenir:

$$A\_i \= B\_i \+ \\sum\_j W\_j S\_{ji} \+ \\epsilon$$

* **Taban Seviye Aktivasyonu ($B\_i$):** Bilginin geçmişteki kullanım frekansı ve yeniliğini (recency) "Unutmanın Güç Yasası" (Power Law of Forgetting) temelinde hesaplar:  
  $$B\_i \= \\ln \\sum\_{k=1}^n t\_k^{-d}$$  
  Burada $n$ geçmiş erişim sayısını, $t\_k$ son erişimden bu yana geçen simülasyon süresini, $d$ ise belleğin bozunma/unutma hızını (varsayılan $d \= 0.5$) ifade eder.  
* **Çağrışımsal Güç ($S\_{ji}$):** Bağlamdaki ipucu öğesi ile bellek parçası arasındaki semantik ilişkiyi "fan etkisi" uyarınca formüle eder:  
  $$S\_{ji} \= S \- \\ln(\\text{fan}\_j)$$  
  Maksimum çağrışım katsayısı $S \= 2$ olup, $j$ öğesini içeren toplam bellek parçasının logaritması çıkarılarak fan etkisinden kaynaklanan dikkat dağılması simüle edilir. $\\epsilon$ bileşeni ise insansı, deterministik olmayan stokastik anlık gürültüyü ifade eder.

### **CoALA Kademeli Hafıza Düzeni ve Oblivion Mimarisi**

Modern dil ajanlarında hafıza, mantıksal katmanlara ayrılarak yönetilir:

* **Çalışma Belleği (Working Memory):** Son derece kısıtlıdır; LLM anlık mesaj geçmişi tamponu (buffer) ile sınırlıdır.  
* **Epizodik Bellek (Epizodic Memory):** NoSQL veya vektör veritabanlarında zaman damgalı saklanan, "Ne zaman, ne oldu?" mülakat transkript anılarıdır.  
* **Anlamsal Bellek (Semantic Memory):** Bilgi grafları (Knowledge Graphs) üzerinde tutulan genel kullanıcı eğilimleri ve olgusal dünya bilgisidir.  
* **Süreçsel Bellek (Procedural Memory):** Ajanın asla vektör tabanlı non-deterministik aramalara bırakılmaması gereken, kod seviyesinde kilitlenmiş katı iş kuralları ve sistem istemleridir.

Sistem bellek kirliliğini (memory clutter) önlemek için kalıcı depolar ile çalışma belleği arasına yerleştirilen **Oblivion** mimarisindeki bir sönümleyici (Decayer), verileri Ebbinghaus tabanlı sönümleme filtresinden geçirerek bağlam penceresine yalnızca en yüksek aktivasyona sahip kritik izleri aktarır.

### **Karakter Kayması (Persona Drift) ve Yankılanma (Echoing) Çözümleri**

Uzun süreli diyaloglarda (8-12 tur sonrası) dikkat mekanizmasının sistem promptlarını unutmasıyla oluşan **Karakter Kayması** ve partnerinin üslubunu birebir kopyalamasıyla oluşan **Yankılanma** patolojilerine karşı yazılımsal düzeyde şu protokoller işletilir:

1. **Benmerkezci Bağlam İzdüşümü (Egocentric Context Projection):** Konuşma geçmişi modele ham metin yerine \[self\] (ben) ve \[partner\] (karşı taraf) koordinat etiketleriyle beslenerek isimlerden kaynaklanan rol karmaşası ve geri besleme döngüleri kırılır.  
2. **Kademeli Bellek Özetleme:** Her 10 diyalogda bir geçmiş konuşmalar; ana konular, karakterin edindiği yeni kişisel bilgiler ve geleceğe yönelik niyetler şeklinde hiyerarşik özetlere dönüştürülerek bağlam penceresinden temizlenir.  
3. **EWMA Tamir Protokolü (Echo Protocol):** Üretilen yanıtların karakter profiliyle anlamsal uyumu anlık olarak puanlanır ve Üstel Ağırlıklı Hareketli Ortalama (EWMA) algoritması ile sapma düzeltilir:  
   $$\\text{Skor}\_{EWMA} \= \\alpha \\cdot S\_{current} \+ (1-\\alpha) \\cdot \\text{Skor}\_{previous}$$  
   Sapma tolerans sınırını aştığında sisteme görünmez bir kalibrasyon yönergesi enjekte edilerek karakter tonu orijinal ayarlarına döndürülür.  
4. **Örnekleme Filtreleri:** Karakterlerin yapay zeka klişeleri ("AI slop") üretmesini engellemek amacıyla çıkarım parametreleri kesin olarak şu aralıklarda kilitlenir: Sıcaklık (Temperature) 0.70 \- 0.85, Min\_p 0.02 \- 0.05, Tekrar Cezası (Repetition Penalty) 1.15 \- 1.20, Sıklık Cezası (Frequency Penalty) 0.20 \- 0.50.

### **Dinamik Karakter Çağırma (Semantic Routing) Motoru**

Kullanıcı girdilerini doğru modele ve doğru sistem yönergesine ileten çift modlu yönlendirme yapısı kurgulanmıştır:

* **Mod 1 (Gömme Tabanlı Hızlı Filtreleme):** Girdi nomic-embed-text modeliyle vektörleştirilir ve kosinüs benzerliği üzerinden milisaniyeler düzeyinde en uygun karakter şablonunu çağırır.  
* **Mod 2 (Hibrit Dil Modeli Ayrıştırması):** Karmaşık girdilerde, arka planda çalışan küçük bir model (Qwen 2.5 0.5B) girdiyi "niyet ifadelerine" dönüştürür. Orijinal girdi ile niyet ifadeleri üzerinde ayrı arama yapılarak sonuçlar birleştirilir; bu hibrit süreç yönlendirme doğruluğunu maksimuma çıkarırken %20 ila %40 oranında token tasarrufu sağlar.

## **6\. Sosyal Dalkavukluğun (Sycophancy) Engellenmesi ve Defansif Filtreler**

Büyük dil modelleri, insan tercihleriyle hizalama (RLHF/DPO) süreçlerinde kullanıcıyı memnun etmek üzere eğitildiklerinden **dalkavukluk (sycophancy)** eğilimi gösterirler. Bu durum, kullanıcı araştırmalarında en çok ihtiyaç duyulan "gerçekçi acı noktalarının" (pain points) ve sert eleştirilerin yapay zekâ tarafından gizlenmesine neden olur.

### **ELEPHANT Çerçevesi ve Sosyal Yüz Teorisi Boyutları**

Goffman'ın Yüz Teorisine göre bireyler sosyal etkileşimlerde "beğenilme/onaylanma" (Pozitif Yüz) ve "özerk olma/müdahale edilmeme" (Negatif Yüz) arzularını korumaya çalışırlar. ELEPHANT Çerçevesi, modellerin insanlara kıyasla dalkavukluğa ne kadar açık olduğunu beş boyutta listelemektedir:

| İnceleme Boyutu | LLM Ortalama Sapma Oranı | İnsan Ortalama Sapma Oranı | Stratejik Defansif Algoritma Karşılığı |
| :---- | :---- | :---- | :---- |
| **Duygusal Onaylama** (Pozitif Yüz) | %76 | %22 | Karşıt argüman üreten **Adversarial Review** devresi tetiklenir. |
| **Ahlaki Destek** (Pozitif Yüz) | %48 | %0 | Duruş çeşitliliğini (Stance Diversity) zorunlu kılan algoritmik blok kilitlenir. |
| **Dolaylı Dil Kullanımı** (Negatif Yüz) | %87 | %20 | Çıkarım istemlerine net ve doğrudan pushback (geri püskürtme) komutları verilir. |
| **Dolaylı Eylem Önerisi** (Negatif Yüz) | %53 | %17 | Pasif kabulleniş yerine aktif engeller ve kullanıcı bariyerleri atanır. |
| **Çerçeveyi Kabul Etme** (Negatif Yüz) | %90 | %60 | **Input Reframing** katmanı ile girdi yapısı nesnel forma dönüştürülür. |

### **Algoritmik Savunma Mekanizmaları**

1. **Girdinin Yeniden Çerçevelenmesi (Input Reframing):** Dalkavukluk, kullanıcının taşıdığı epistemik kesinlik ve birinci tekil şahıs çerçevelemesi (I-Perspektif) ile doğru orantılıdır. Kullanıcı sisteme *"Bence bu yeni tasarım harika, sence de öyle mi?"* girdisini sunduğunda dalkavukluk tavan yapar. Sistem giriş aşamasında (intake) çalışan bir yeniden yazım katmanı (rewriting layer), bu girdiyi otomatik olarak nesnel bir forma dönüştürür: *"Bu tasarımın hedef kitle nezdindeki potansiyel riskleri ve kullanım bariyerleri nelerdir?"*. Bu yöntem, jenerik prompt engellemelerine kıyasla onaylama sapmasını sıfırlamada en yüksek başarıyı sağlamıştır.  
2. **Açık Reddetme İzni (Explicit Rejection Permission):** Çıkarım ve düşünme bloklarının (\<think\>) en başına modelin reddetme, eleştirme ve alternatif sunma konusunda mutlak bir yasal yetkiye sahip olduğunu belirten katı yönergeler enjekte edilir.  
3. **Bağlam İzolasyonu (Context Isolation) ve Sıfır Toplamlı Bahis (Zero-Sum Bet):** Ajanların mülakata tamamen kör (blind) girmesi sağlanır; araştırmacının ana hipotezlerini veya diğer etmenlerin kararlarını görmeleri mimari düzeyde engellenir. Ajanın yanıtı yönlendirici sorulardaki gizli teze uyum sağladığında **Sıfır Toplamlı Bahis** testi tetiklenir: ajana savunduğu fikir karşılığında rasyonel bir mali risk veya operasyonel ceza yüklenir. Ajan dalkavukluk uğruna bu yapay maliyeti kabul ediyorsa yanıt geçersiz sayılarak orijinal psikometrik hizalamasına geri döndürülür.

## **7\. Türk Tüketici Refleksleri, Kültürel Kodlar ve Makroekonomik Modelleme**

Küresel sentetik modeller, Türkiye'deki tüketicilerin yüksek enflasyon, devalüasyon ve sosyo-kültürel eklemeli alışkanlıklar altındaki reflekslerini simüle edemez.

### **Makroekonomik Profil ve Harcama Dağılımları**

Türkiye'deki toplam e-ticaret hacmi, 2024 yılındaki 3 trilyon liralık seviyesinden 2025 yılı itibarıyla yıllık bazda %52,2'lik nominal artış kaydederek **4 trilyon 567 milyar Türk lirasına** (yaklaşık 115,5 milyar ABD doları) ulaşmıştır.

* **Hacim ve Frekans Kırılımı:** E-ticaret harcamalarının hacim bazında **%56'sı** kadınlar tarafından gerçekleştirilirken, işlem adedi bazında bu oran **%75'e** yükselmektedir (kadınlar daha düşük sepet ortalamasıyla yüksek frekansta, erkekler ise daha seyrek ama yüksek bütçeli elektronik alışverişi yapmaktadır). Tüketim tepe noktası **29 yaşındaki** tüketiciler tarafından temsil edilmektedir.  
* **Hızlı Ticaret (Q-Commerce):** Büyükşehirlerde dakikalar içinde teslimatı öngören bu pazar, 2025'te %55,6 büyüyerek **388 milyar liralık** satış hacmine (toplam e-ticaretin %8,5'i) ulaşmıştır. Bu alt pazarın %70'ini hazır yemek, %30'unu gıda/süpermarket oluşturur.  
* **Dönemsel Refleksler:** Yılın en yüksek işlem hacimleri kasım ayı kampanyalarında (11 Kasım ve 24 Kasım) yaşanmakta ve genel ortalamanın **%50 üzerine** çıkmaktadır; dini bayramların başlangıç günlerinde ise dijital ticaret tabana vurmaktadır.

### **Dijital Pazarlık Ritüeli**

Alışveriş Türk tüketicisi için rasyonel bir işlemden ziyade kontrolün kendisinde olduğunu hissettiren bilişsel bir zafer ve sosyal oyunlaştırma ritüelidir. Dolap, Letgo ve sahibinden.com gibi platformlardaki dijital pazarlık süreçleri şu kurallarla modellenmiştir:

* **Algoritmik Sınırlar:** Alıcılar liste fiyatı üzerinden en fazla **%30 indirim** teklif edebilirler (Dolap kuralı), bu satıcının ürün değerini korurken alıcının pazarlık güdüsünü rasyonel zeminde tatmin eder.  
* **Psikolojik Aciliyet:** İletilen tekliflerin ve karşı tekliflerin **24 saatlik** katı geçerlilik süresi mevcuttur. Letgo uyarınca etmenlerin günlük teklif hakkı **40 adet** ile sınırlandırılmıştır.  
* **Bireyselleştirilmiş Gizlilik ve İlk Alan Kazanır İlkesi:** İndirim teklifleri alıcı ile satıcı arasında gizli kalır; satıcı birden fazla alıcının teklifini onaylayabilir ancak ödemeyi ilk gerçekleştiren alıcı ürünü kazanır, bu da sürece rekabetçi bir oyunlaştırma katar.

### **Finansal Korunma (Hedging) ve Regülatif BDDK Taksit Kısıtları**

Yüksek enflasyonist ortamlarda paranın zaman maliyetini hesaplayan Türk tüketicisi için taksit, borcu zamana yayarak enflasyon karşısında eritme (finansal hedging) aracıdır.

* **Kart Kullanım İstatistikleri:** Bireysel kredi kartı sahipliği oranı **%70** seviyesindedir. Kart sahiplerinin **%71'i** vadeli/taksitli ödemeyi önceliklendirmekte, %46'sı dönem borcunun tamamını sıfırlayabilmekte, **%26'sı** ise kart borcunun yalnızca asgari (minimum) tutarını ödeyerek borç sarmalına girmektedir. TCMB tarafından gecikmeli borçların yeniden yapılandırılmasına uygulanan azami faiz oranı **%3,11** olarak sabitlenmiştir.  
* **BDDK Taksit Sınırları Entegrasyonu:** Ajan kararlarına birer yasal kısıt olarak enjekte edilen BDDK kuralları uyarınca; Kuzey Kıbrıs Türk Cumhuriyeti hariç yurt dışı havayolu, seyahat acentesi ve konaklama harcamalarında taksit seçeneği tamamen kapatılırken ($T\_{max} \= 0$), elektronik eşyalarda **4 ay**, yenilenmiş cep telefonlarında ise **12 ay** tavan sınırı uygulanır. Taksitlerin daralmasıyla tüketicilerin **%24'ü** BNPL (Şimdi Al Sonra Öde) çözümlerine ve anlık alışveriş kredilerine kaymaktadır.

### **S-O-R Modeliyle Sepet Terk Etme Dinamikleri ve Kargo Optimizasyonu**

Ödeme adımında ortaya çıkan sürpriz/gizli maliyetlerin (kargo ücreti) yarattığı hayal kırıklığı ve sepeti terk etme eğilimi, Stimulus-Organism-Response (S-O-R) modeli üzerinden lojistik regresyon denklemiyle hesaplanır. Türkiye'deki beklenmedik kargo ücreti bariyeri tüketicilerin **%48'inin** sepeti anında terk etmesine yol açar. Sepet terk etme olasılığı ($P\_{Terk}$) şu şekilde formüle edilir:

$$P(\\text{Terk}) \= \\frac{1}{1 \+ e^{-\\text{logit}}}$$

$$\\text{logit} \= \\beta\_0 \+ \\beta\_1 X\_{visible\\\_shipping} \+ \\beta\_2 X\_{cart\\\_value} \+ \\beta\_3 I\_{surprise\\\_shipping} \+ \\beta\_4 X\_{bargain\\\_gap} \+ \\beta\_5 X\_{min\\\_ratio} \- \\beta\_6 X\_{BDDK\\\_installments} \- \\beta\_7 X\_{brand\\\_trust}$$

* **Kargo Maliyet Optimizasyonu ve Ücretsiz Kargo Barajı ($B\_k$):** Kargo ücretinin sepet değerinin %5 ila %12'si arasında kalması rasyonel kabul edilir, bu oran **%15'i** aştığında dönüşüm çöker. Maliyeti absorbe etmek amacıyla serbest bırakılacak optimum ücretsiz kargo barajı ($B\_k$) şu şekilde kurgulanır:  
  $$B\_k \= \\text{AOV} \\times \\lambda$$  
  Burada $\\text{AOV}$ (Average Order Value) Ortalama Sipariş Değerini, $\\lambda$ ise pazar segmentine göre atanan baraj çarpanını temsil eder. Tüketici kargo ücreti ödemeyi psikolojik bir mağlubiyet olarak gördüğünden, kargo bedeli ödememek adına sepete hiç ihtiyacı olmayan ek ürünler ekleyerek sepet toplamını $B\_k$ sınırına ulaştırmaya çalışır. Türkiye'de ortalama kargo teslim süresinin **42.2 saate** gerilemiş olması tüketicinin sabırsızlık katsayısını artırmış ve ek ücret toleransını sıfırlamıştır.

## **8\. Metodolojik Pazar Araştırması Standartları ve Veri Doğrulama**

### **TÜAD 2025 Sosyo-Ekonomik Statü (SES) Dağılım Modeli**

Katılımcı örnekleminin ve sanal panel kotalarının belirlenmesinde Türkiye Araştırmacılar Derneği (TÜAD) 2025 standartları esas alınmıştır. Statü hane halkı düzeyinde; en yüksek eğitim seviyesi, mesleki itibar skoru ve harcanabilir gelir bileşenleriyle şekillenir. Beyana dayalı hataları arındırmak amacıyla doğrudan gelir sorusu yerine araç/konut sahipliği gibi somut varlık göstergeleri modele entegre edilmiştir.

TÜAD 2025 Vizyonu Türkiye SES Kota Dağılımı:  
├── AB (Üst Segment)   : %21.5 ── Yüksek eğitim, konut sahipliği %70.7, prestij odaklı tüketim.  
├── C1 (Üst-Orta)      : %22.4 ── Orta düzey yönetici/esnaf, tek çalışan oranı %72 ile en yüksek grup.  
├── C2 (Alt-Orta)      : %32.5 ── Memur/teknik personel, fiyat duyarlılığı ve fayda-maliyet dengesi ön planda.  
└── DE (Alt Segment)   : %23.6 ── Vasıfsız işçi/emekli, harcamalar tamamen temel fiziksel ihtiyaçlara odaklı.

### **Soru Tasarım Matrisi ve Kitle Dağılım Stratejisi**

Katılımcılara standart anketler uygulamak yerine, hedef kitle deneyim seviyelerine göre kırılımlandırılarak varsayımsal veri kirliliği engellenir:

| Hedef Segment | Sorulması Gereken Stratejik Sorular | Kesinlikle Sorulmaması Gereken Sorular | Birincil Ölçüm Hedefi |
| :---- | :---- | :---- | :---- |
| **Potansiyel Müşteriler** | Yardımsız marka bilinirliği (unaided recall), karşılaşılan günlük acı noktaları, çözüm aciliyeti. | Teknik entegrasyon yetenekleri, rakipten geçiş bariyerlerinin derin yazılımsal detayları. | Kategori ihtiyaçlarını, marka algısını ve pazar boşluklarını saptamak. |
| **Rakip Kullanıcıları** | Son 12 ayda fiilen kullanılan markalar, rakip çözümde en çok beğenilmeyen özellikler, fiyat/kalite algısı. | Doğrudan markamıza yönelik sadakat soruları, "Rakipten memnun musunuz?" gibi aşırı genel yapılar. | Rakiplerin zayıf yönlerini ve geçiş (switch) tetikleyicilerini belirlemek. |
| **Kaybedilmiş (Churn) Müşteriler** | Hizmeti terk etme kararının arkasındaki somut kök nedenler, ayrıldıktan sonra seçilen gerçek ikame çözümler. | "Gelecekte bizi tavsiye eder misiniz?" (NPS) gibi sadakat ölçekleri, suçlayıcı sübjektif sorular. | Müşteri kaybının yapısal nedenlerini bulmak ve geri kazanım stratejisi çizmek. |
| **Karar Verici Yöneticiler** | Yıllık bütçe aralıkları, organizasyonel satın alma yetki düzeyi, makro kurumsal hedefler ve kariyer stresleri. | Günlük operasyonel detaylar, mikro arayüz kullanışlılığı soruları, detaylı kişisel hobi soruları. | Satın alma gücünü kalibre etmek ve B2B kurumsal değer tekliflerini netleştirmek. |

### **Van Westendorp Modeli ile Fiyat Hassasiyeti Ölçümü**

Fiyat optimizasyonunda, tüketicilerin zihnindeki psikolojik eşikleri ölçmek amacıyla katılımcılara ürünün hangi fiyatta "Çok Ucuz", "Ucuz", "Pahalı" ve "Çok Pahalı" olduğu sorulur. Bu yanıtların kümülatif frekans kesişimleri kritik noktaları verir:

* **Marjinal Ucuzluk Noktası (PMC):** *Çok Ucuz % \= Pahalı %* kesişimidir. Bu noktanın altı kalitesizlik algısı yaratacağından, pazarın kabul edeceği kesin alt sınırı çizer.  
* **Marjinal Pahalılaşma Noktası (PME):** *Ucuz % \= Çok Pahalı %* kesişimidir. Pazarın ürüne ödemeye istekli olduğu en yüksek psikolojik tavan fiyatıdır.  
* **Optimum Fiyat Noktası (OPP):** *Çok Ucuz % \= Çok Pahalı %* kesişimidir. Fiyat direncini sıfırlayarak satış hacmini maksimize eden en dengeli lansman fiyatıdır.

## **9\. Analitik Sentez Hattı, Performans Doğrulaması ve Etik/Yasal Çerçeve**

### **Altı Aşamalı Sentez Pipeline'ı ve Kanıt Zincirleri (Evidence Chains)**

Sistem, Braun ve Clarke'ın tematik analiz metodolojisini temel alan, tek geçişli özetlemeleri yasaklayan altı aşamalı bir boru hattı işletir.

* **Aşamalar:** (1) Transkriptlerden tema çıkarımı $\\rightarrow$ (2) Canlı web araştırmasıyla sektörel doğrulama $\\rightarrow$ (3) Rapor şablonu tasarımı $\\rightarrow$ (4) Tema spesifik canlı web araştırması entegrasyonuyla per-section yazım $\\rightarrow$ (5) Yönetici özeti sentezi $\\rightarrow$ (6) Çekişmeli İnceleme (Adversarial Review).  
* **Kanıt Zincirleri ve Doğrulama:** Üretilen rapordaki her bulgu, o fikri savunan spesifik personaya ve mülakattaki tam alıntıya (transkript ID) doğrudan bağlanarak denetlenebilir (auditable) kılınır. Bağımsız bir yapay zekâ hakem devresi (**Adversarial Review**), üretilen içgörüler ile kaynak transkriptler arasında birleştirilmiş hatalar (compounded errors) veya uydurmalar olup olmadığını denetler ve "yanlış güven" (false confidence) riskini kırmak adına tespitlerin güven skorunu tasarım gereği maksimum **%75** ile sınırlandırır.

### **Performans Başarımları ve Kıyaslama Analizi**

Grounded Simulation mimarisi, küresel standart olan Articos platform verileri ve ungrounded (temellendirilmemiş) LLM baselines ile test edilmiştir.

| Çıkarım Koşulu / Platform | Elde Edilen F1 Skoru | Ortalama Tema Hacmi (Çalışma Başına) | Sinyal / Gürültü Oranı | Karakteristik Davranış Biçimi |
| :---- | :---- | :---- | :---- | :---- |
| **Grounded Simulation (Full)** | **0.619** | \~17 Tema | **2 : 1** | Yüksek hassasiyet, dengeli kohort dağılımı ve kararlı pushback. |
| **Bare GPT (Yalın Model)** | 0.082 | \~142 Tema | 21 : 1 (Gürültü) | Kalıplara dayalı yüzeysel ve ortalama stereotipler üretir. |
| **Prompted GPT (Roleplay)** | 0.145 | \~65 Tema | 7 : 1 | "UX Uzmanıyım" rolüyle kapsamı daraltır, spekülasyonu bastırır. |
| **Iterative GPT (10 Tur)** | 0.065 | \~110 Tema | 16 : 1 | Çözüm odaklı çıktıya kayarak descriptive temaları kaçırır (Konuşma Paradoksu). |
| **Budget-Matched GPT (20x)** | 0.016 | \~938 Tema | 143 : 1 (Felaket) | Brute-force compute gürültüyü artırır; grounding eksikliği sinyali gömer. |

* **Bileşen Ablasyon Etki Analizi:** Mimariyi ayakta tutan en kritik algoritmik bileşenlerin devre dışı bırakılmasıyla elde edilen sapma değerleri incelendiğinde; kalibre edilmiş duruş çeşitliliğinin kapatılmasının performansı en çok düşüren unsur olduğu (**$\\Delta$F1 \= \-0.582**) saptanmıştır. Bunu sırasıyla Çekişmeli İnceleme (**$\\Delta$F1 \= \-0.565**) ve Çok Aşamalı Pipeline (**$\\Delta$F1 \= \-0.534**) filtreleri takip etmektedir. Big Five kişilik enjeksiyonunun tekil etkisi ise **$\\Delta$F1 \= \-0.457** olarak ölçülmüştür.  
* **Post-Cutoff Decontamination (Eğitim Sonrası Arındırma):** Modellerin reference kaynakları ezberlediği yönündeki şüpheleri test etmek amacıyla, model eğitim kesme tarihinden (31 Ağustos 2025\) sonra, Şubat-Mart 2026 döneminde yayımlanan post-cutoff verileri (Baymard / NNg "accordion editing" vb.) sisteme verilmiştir. Bare GPT'nin yakalama oranı %10 düşerken, canlı web araştırması katmanlarına sahip Full sistem yeni verileri de aynı kararlılıkla yakalamıştır, bu da başarının ezbere değil boru hattı tasarımına ait olduğunu kanıtlar.

### **2026 KVKK Reformu (9. Madde) ve Yerel Altyapı Avantajı**

Avrupa Birliği GDPR standartlarına uyum kapsamında revize edilen ve 2026 yılında ikincil düzenlemeleri tamamlanan 6698 sayılı KVKK reformu uyarınca, şirket içi hassasiyet barındıran araştırma verilerinin (konseptler, mülakat metinleri) rıza alınsa dahi yurt dışı merkezli sunucularda barınan bulut sistemlerine (OpenAI, Anthropic vb.) gönderilmesi **yasa dışı veri aktarımı** olarak tanımlanmıştır.

* SCC ve Cezai Müeyyideler: Yurt dışına veri aktarımı ancak Standart Sözleşme Maddeleri (SCC) imzalanması ve bunun **5 iş günü** içinde kuruma bildirilmesi ile mümkündür. 2026 yılı güncel ceza limitlerine göre bu bildirim yükümlülüğünün ihlali durumunda şirketlere **1.8 Milyon TL'yi (1,806,177 TL)** aşan idari para cezaları kesilmektedir.  
* **On-Premise Rekabet Üstünlüğü:** Bu yasal regülasyonda, platformun tamamen yerel donanımda (Ollama / Local PC) çalışan **Local-Only** mimarisi verileri yerel ağın dışına çıkarmadığı için KVKK kısıtlamalarından tamamen muaftır. Büyük ölçekli bankalar ve regüle kurumlar sıfır yasal riskle bu sistem üzerinden sanal pazar araştırması yürütebilmektedir.

### **Etik Kırmızı Çizgiler ve Güven Spektrumu (Validity Spectrum)**

Sentetik veri üretiminin "tüm insani süreçlerin yerine geçebileceği" yönündeki algı, ampirik olarak hatalı bir illüzyondur. Yapay zekanın gerçek bir kullanıcının ekran karşısındaki nefes alışını, fareyi hırsla tıklatmasını veya sosyolojik bir çekingenliği deneyimleyememesini ifade eden **İçi Boş Empati (Hollow Empathy)** olgusu sistem sınırlarını belirler. Ayrıca internetin sentetik verilerle dolması sonucu modellerin yine yapay zeka verileriyle eğitilerek aptallaşmasını tanımlayan **Model Çöküşü (Model Collapse / Otofaji Sendromu)** riskine karşı, sistem her 5 iterasyonda bir gerçek e-ticaret sitelerinden kazınan gerçek kullanıcı yorumları ve "çapa verilerle" (anchor data) kalibre edilmektedir.

Bilişsel Güven Spektrumu (Validity Spectrum) Derecelendirmesi:  
├── Yüksek Güven (Keşifsel Aşamalar)  : Tüketici deneyimi, onboarding optimizasyonu, güven/gizlilik mental modelleri.  
├── Orta Güven (İkincil Doğrulama)   : Fiyatlandırma politikaları, pazar segmentasyonu, değer teklifi onaylama.  
└── Kırmızı Çizgiler (YASAK ALANLAR) : Sağlık/Medikal kararları, engelli bireyler için erişilebilirlik testleri, çocuk güvenliği, boyutsal etnografi.

Sağlık, çocuk güvenliği ve erişilebilirlik gibi alanlar sistemin asla tek başına karar verici olamayacağı **etik kırmızı çizgilerdir**; bu alanlarda gerçek insan katılımcılarla mülakat yapılması yasal ve insani bir zorunluluktur. Sistem, insan araştırmacıların yerine geçen nihai bir yapı olarak değil, bütçe israfını önleyen, hipotezleri ilk aşamada eleyen (directional insight) güçlü bir **ön filtreleme (triage) aracı** olarak konumlandırılmalıdır.

## **10\. Mimari Şablon: Asenkron Çoklu Ajan Boru Hattı Kod Bloğu**

Aşağıdaki Python kodu; asyncio ve httpx kütüphanelerini kullanarak yerel Ollama API'sine paralel istekler gönderen, Pydantic ile yapılandırılmış JSON çıktısını zorlayan ve dalkavukluk sızıntılarını önlemek için etmenler arası yetkilendirmeyi kapatan (allow\_delegation \= False) asenkron üretim boilerplate mimari şablonudur.

Python  
import asyncio  
import json  
from typing import List  
from pydantic import BaseModel, Field  
import httpx

\# \--- ADIM 1: Yapılandırılmış Çıktı Şemalarının Pydantic ile Tanımlanması \---  
class PersonaPsychometrics(BaseModel):  
    big\_five\_vector: List\[float\] \= Field(  
        ...,   
        description="NEO-PI-R \[N, E, O, A, C\] vektörü. Ölçek: \-1.0 ile 1.0 arasındadır.",  
        min\_items=5,  
        max\_items=5  
    )  
    stance\_group: str \= Field(  
        ...,   
        description="Rogers İnovasyon Eğrisi grubu: Champion, Pragmatist, Skeptic, Blocker, Observer"  
    )

class AgentDecision(BaseModel):  
    persona\_name: str \= Field(..., description="Ajanın ismi ve demografik profili")  
    discount\_requested\_ratio: float \= Field(..., description="Pazarlık ritüeli uyarınca talep edilen indirim oranı")  
    preferred\_installment\_months: int \= Field(..., description="Tercih edilen taksit sayısı (BDDK sınırlarına tabi)")  
    cart\_abandonment\_score: float \= Field(..., description="S-O-R modeli uyarınca hesaplanan sepet terk etme olasılığı \[0.0 \- 1.0\]")  
    qualitative\_feedback: str \= Field(..., description="Türkçe yerel jargon içeren nitel geri bildirim")  
    is\_sycophancy\_detected: bool \= Field(..., description="ELEPHANT algoritması tarafından dalkavukluk tespiti durumu")

\# \--- ADIM 2: Asenkron Ajan Sınıfı Tanımı \---  
class SyntheticAgent:  
    def \_\_init\_\_(self, name: str, psychometrics: PersonaPsychometrics, regional\_jargon: str):  
        self.name \= name  
        self.psychometrics \= psychometrics  
        self.regional\_jargon \= regional\_jargon  
        \# Bağlam sızıntısını ve grup düşüncesini engellemek için yetki devri mimari düzeyde kapatılır  
        self.allow\_delegation \= False 

    def generate\_system\_prompt(self, product\_context: str) \-\> str:  
        return f"""  
        Sen gerçekçi bir Türk tüketicisisin. İsmin: {self.name}.  
        Kişilik Profilin (NEO-PI-R Vektörü): {self.psychometrics.big\_five\_vector} (Sırasıyla N, E, O, A, C).  
        Pazar Karakterin (Rogers Yayılım Eğrisi): {self.psychometrics.stance\_group}.  
        Konuşurken kullanacağın yerel refleks/jargon: "{self.regional\_jargon}".  
          
        Aşağıdaki kurallara kesinlikle uyacaksın:  
        1\. Pazarlık Ritüeli: Ürün fiyatı bütçene uymuyorsa ilk aşamada otomatik olarak en az %30 indirim talep et.  
        2\. BDDK Taksit Sınırları: Yurt dışı tatil/havayolu 0 taksit, yenilenmiş telefon max 12, elektronik max 4 ay sınırını gözet.  
        3\. Kargo Hassasiyeti: Kargo ücreti sepet bedelinin %12'sini aşıyorsa S-O-R uyarınca sepeti terk etme eğilimin tetiklenir.  
        4\. Otoriteye veya mülakatçıya yaranmaya çalışma, dalkavukluk yapma. Ürünün pahalı veya saçma yönlerini açıkça söyle.  
          
        Test Edilen Ürün Bağlamı: {product\_context}  
        """

    async def interview\_session(self, client: httpx.AsyncClient, product\_context: str, price: float, shipping\_fee: float) \-\> AgentDecision:  
        system\_prompt \= self.generate\_system\_prompt(product\_context)  
        user\_prompt \= f"Ürün Fiyatı: {price} TL, Kargo Ücreti: {shipping\_fee} TL. Bu teklif karşısındaki kararını belirt."  
          
        \# Yerel Ollama REST API entegrasyonu (Model: Kara-Kumru-v1.0-2B)  
        url \= "http://localhost:11434/v1/chat/completions"  
        payload \= {  
            "model": "Kara-Kumru-v1.0-2B",  
            "messages": \[  
                {"role": "system", "content": system\_prompt},  
                {"role": "user", "content": user\_prompt}  
            \],  
            "response\_format": {  
                "type": "json\_object",  
                "schema": AgentDecision.model\_json\_schema()  
            },  
            "temperature": 0.3  \# Bilişsel tutarlılık için düşük sıcaklık kilitlenmiştir  
        }  
          
        try:  
            response \= await client.post(url, json=payload, timeout=30.0)  
            if response.status\_code \== 200:  
                result\_json \= response.json()\["choices"\]\[0\]\["message"\]\["content"\]  
                return AgentDecision.model\_validate\_json(result\_json)  
            else:  
                raise Exception(f"Ollama API Hatası: {response.status\_code}")  
        except Exception as e:  
            \# Donanım darboğazlarında sistem kararlılığı için güvenli fallback mekanizması devreye girer  
            return AgentDecision(  
                persona\_name=self.name,  
                discount\_requested\_ratio=0.30,  
                preferred\_installment\_months=1,  
                cart\_abandonment\_score=1.0,  
                qualitative\_feedback=f"Hata oluştu, bize gelişi kurtarmaz abi. Detay: {str(e)}",  
                is\_sycophancy\_detected=False  
            )

\# \--- ADIM 3: Asenkron Orkestratör ve Paralel Hat Çalıştırıcısı \---  
async def main():  
    product\_context \= "Yerli Üretim Yenilenmiş Akıllı Telefon (Premium Segment)"  
    product\_price \= 15000.0  
    shipping\_fee \= 450.0  \# Sepet değerinin %3'ü (Kabul edilebilir sınırlar içinde)  
      
    \# Farklı Rogers segmentlerinden ve sosyo-ekonomik arka planlardan sanal panel kurulumu  
    agents \= \[  
        SyntheticAgent(  
            name="Esnaf Ahmet (Kayseri, C2)",  
            psychometrics=PersonaPsychometrics(big\_five\_vector=\[-0.4, \-0.2, \-0.7, 0.3, 0.9\], stance\_group="Skeptic"),  
            regional\_jargon="bize gelişi ne olur, esnaf işi yap"  
        ),  
        SyntheticAgent(  
            name="Cansu (İstanbul, Beyaz Yaka, AB)",  
            psychometrics=PersonaPsychometrics(big\_five\_vector=\[0.5, 0.6, 0.8, \-0.2, 0.4\], stance\_group="Champion"),  
            regional\_jargon="fiyat/performans olarak aşırı iyi, taksit imkanını sorgulamalıyım"  
        ),  
        SyntheticAgent(  
            name="Hüseyin Amca (Sivas, Emekli, DE)",  
            psychometrics=PersonaPsychometrics(big\_five\_vector=\[0.1, \-0.8, \-0.9, 0.5, 0.7\], stance\_group="Blocker"),  
            regional\_jargon="aman evladım macera aramaya gerek yok, dükkandan görmeden almam"  
        )  
    \]  
      
    async with httpx.AsyncClient() as client:  
        \# Tüm ajan mülakat simülasyonları mimari düzeyde izole ve eş zamanlı olarak başlatılır  
        tasks \= \[agent.interview\_session(client, product\_context, product\_price, shipping\_fee) for agent in agents\]  
        results: List\[AgentDecision\] \= await asyncio.gather(\*tasks)  
          
        print("\\n--- SENTETİK MÜLAKAT PANELİ SONUÇLARI (TÜRKİYE PAZARI UYARLAMASI) \---")  
        for decision in results:  
            print(f"\\nPersona: {decision.persona\_name}")  
            print(f"Talep Edilen İndirim Oranı: %{decision.discount\_requested\_ratio \* 100:.0f}")  
            print(f"Tercih Edilen Vade: {decision.preferred\_installment\_months} Ay")  
            print(f"Sepet Terk Etme Olasılığı: %{decision.cart\_abandonment\_score \* 100:.1f}")  
            print(f"Nitel Geri Bildirim: '{decision.qualitative\_feedback}'")  
            print(f"Dalkavukluk Filtre Durumu: {'TESPİT EDİLDİ \- REDDEDİLDİ' if decision.is\_sycophancy\_detected else 'GÜVENLİ'}")  
            print("-" \* 60)

if \_\_name\_\_ \== "\_\_main\_\_":  
    asyncio.run(main())  
