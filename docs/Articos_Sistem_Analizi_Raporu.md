# Articos Sistem ve Mimari Analiz Raporu

## 1. Yönetici Özeti (Executive Summary)
Articos, yapay zeka destekli sentetik kullanıcı araştırmaları (synthetic user research) platformudur. Geleneksel kullanıcı testlerinin maliyet ve zaman engellerini aşarak, hedeflenen kitleye uygun sanal personalar üretir ve bu personalarla derinlemesine mülakatlar veya A/B testleri gerçekleştirir. Sistem, rastgele LLM çıktıları yerine; bilişsel mimari, psikometrik modeller ve yerel pazar dinamikleri (örn. Türkiye) ile beslenen deterministik ve tutarlı bir yapı sunar.

## 2. Bilişsel Mimari ve Teknik Altyapı
Belgelerden elde edilen verilere göre sistem 3 ana teknolojik sütun üzerinde durmaktadır:
*   **NEO-PI-R Vektörel Enjeksiyonu:** Personalar rastgele prompt'larla değil, "Big Five" (OCEAN - Açıklık, Sorumluluk, Dışa Dönüklük, Uyumluluk, Nevrotiklik) skorlarıyla oluşturulur. Ekran görüntülerinde görülen *Ceren (TR)* veya *Travis (US)* profillerindeki 100 üzerinden verilen skorlar, bu karakterlerin mülakat sırasındaki davranışsal tutarlılığını garanti eder.
*   **ACT-R Bilişsel Hafıza:** Sistem Semantik ve Episodik hafızayı ayırır. Bir persona, geçmiş soruları hatırlar (Episodik) ancak aradan zaman (context window) geçtiğinde bilgileri unutma eğilimi gösterir (zaman sönümleme fonksiyonu).
*   **ELEPHANT Algoritması (Anti-Sycophancy):** Sistem, yapay zekanın "kullanıcıyı memnun etme" (dalkavukluk) eğilimini bastırır. Kullanıcıların (örn. Merve Şahin) ürünleri överken değil, kendi dağınık hayatlarını (WhatsApp, Google Takvim, çekmece) anlatırken sergiledikleri gerçekçi "acı noktaları" (pain points) bu sayede ortaya çıkar.

## 3. Kullanıcı Deneyimi ve Arayüz Akışı (UX/UI Flow)
Ekran görüntülerinin analizi, sistemin kusursuz bir "araştırma stüdyosu" mantığıyla çalıştığını göstermektedir. Ana akış şu şekildedir:
1.  **Context (Bağlam):** Kullanıcının araştırma hedefini (Research Goal) girdiği aşama.
2.  **Personas (Personalar):** Hedefe uygun demografik (Türkiye, ABD, AB) ve psikolojik özelliklere sahip, radar grafikleriyle (Relevancy of Roles) desteklenen 10-15 kişilik sentetik denek grubunun (panel) oluşturulması.
3.  **Script (Senaryo/Soru Seti):** Araştırma bağlamına özel, dinamik olarak üretilen derinlemesine mülakat soruları (Örn: Pet Management, Expense Tracking).
4.  **Interviews (Mülakatlar):** Her persona ile yapılan bağımsız simülasyonlar. Sistem bu aşamada şeffaftır; kullanıcı dilerse transkriptleri okuyabilir ve spesifik bir personaya "Follow-up" (Devam Sorusu) sorabilir.
5.  **Report (Raporlama):** Nitel (qualitative) mülakat verilerinin, nicel (quantitative) iş zekası raporlarına dönüştürüldüğü nihai aşama. Ödeme istekliliği (Willingness to pay), özellik önceliklendirmesi (Feature Prioritization) gibi metrikler pasta ve çubuk grafiklerle sunulur.

## 4. Araştırma Modülleri
Sistem iki ana araştırma tipini destekler:
*   **User Interviews (Kullanıcı Görüşmeleri):** Birebir derinlemesine mülakatlar ile keşifsel araştırma.
*   **A/B Test Landing Pages:** Tasarım ve değer önermesi (Value Proposition, CTA Effectiveness vb.) varyantlarının sentetik kitle üzerinde yan yana (side-by-side) test edilmesi.

## 5. Türkiye Pazarı Entegrasyonu
Belgelerdeki pazar verileri, Articos'un yerel refleksleri çok iyi simüle ettiğini göstermektedir.
*   Makro ekonomik koşullar (Taksit/BNPL bağımlılığı - %71 kredi kartı penetrasyonu).
*   C2C ve Q-Commerce (Hızlı ticaret) yatkınlığı.
*   Dijital pazarlık ve güven asimetrisi.
Merve ve Ceren gibi profiller, sadece isim olarak değil; "İstanbul fintech sahnesi" veya "dağınık dijital alışkanlıklar" gibi kültürel/sosyolojik katmanlarla (yerel bağlam) oluşturulmaktadır.

## 6. Sonuç ve Çıkarımlar
Articos, bir LLM arayüzü (wrapper) olmanın çok ötesindedir. Psikometriyi, bilişsel bilimleri ve veri görselleştirmeyi birleştiren entegre bir karar destek sistemidir. Geliştirilecek herhangi bir ajan mimarisinde veya lokal model (Ollama) entegrasyonunda;
*   Rastgelelik yerine NEO-PI-R vektörlerinin kullanılması,
*   Sycophancy'yi engelleyen prompt/algoritma yapılarının kurulması,
*   Arayüzde şeffaflık (transkriptlere erişim) ve etkileşim (follow-up soru) imkanının sunulması,
başarı için kritik öneme sahiptir.
