# Clarere — Yatırımcı Sunumu

---

## Slide 1: Kapak

# Clarere

### Yapay Zeka Destekli Sentetik Pazar Araştırma Platformu

**Gerçek kullanıcıya ihtiyaç duymadan, gerçek içgörüler.**

---

## Slide 2: Problem

### Pazar araştırması neden kırık?

| Geleneksel Yöntem | Sorun |
|---|---|
| Kullanıcı mülakatı | 4-6 hafta, katılımcı başına 500-2000 TL |
| Anket şirketleri | Minimum 1000 katılımcı, proje başı 50.000+ TL |
| Odak grupları | Lojistik, moderatör, mekan maliyeti |
| DIY (kendi başına) | Önyargılı, metodolojisiz, güvenilmez |

**Sonuç:** Startuplar ve KOBİ'ler pazar araştırması yapamıyor. Yapanlar da geç kalıyor.

---

## Slide 3: Çözüm

### Clarere: Sentetik Persona Araştırması

1. **Fikrini anlat** — Defne (yapay zeka) ile 5 dakikalık sohbet
2. **Personalar oluşturulsun** — TÜAD 2025 SES × Rogers Diffusion bilimsel kotalama
3. **Mülakatları izle** — Her persona ürününü değerlendirir, itiraz eder, fiyat verir
4. **Raporu al** — Van Westendorp fiyat analizi, pain point matrisi, aksiyon önerileri

**Süre: ~2 dakika. Model maliyeti: araştırma başına ~$0.01–0.04.**

---

## Slide 4: Bilimsel Altyapı

### Grounded Simulation (dahili mimari)

| Metodoloji | Açıklama |
|---|---|
| **Big Five / NEO-PI-R** | Kişilik profilleme — her persona psikometrik vektör |
| **Rogers Diffusion** | 5 yenilik benimseme profili (Innovator → Skeptic) |
| **Hofstede Kültür** | Türkiye özel: PDI=66, IDV=37, UAI=85 |
| **Van Westendorp PSM** | Fiyat hassasiyet analizi (OPP, IPP, PMC, PME) |
| **ELEPHANT Çerçevesi** | Anti-dalkavukluk — personalar ürünü beğenmek zorunda değil |

**Doğrulama yaklaşımı:** Her bulgu persona → soru → alıntı düzeyinde **kanıt zinciriyle** izlenir; panel anti-dalkavukluk (ELEPHANT) ve çeşitlilik denetiminden geçer. Çıktılar **yönlendirici hipotezdir**; istatistiksel temsil iddiası taşımaz ve yüksek riskli kararlar gerçek kullanıcı verisiyle doğrulanmalıdır.

---

## Slide 5: Teknoloji

### Modern Stack

| Katman | Teknoloji |
|---|---|
| **DeepSeek** | Flash + Pro — araştırma başına ~$0.01–0.04 |
| **Backend** | FastAPI (Python) — 3 aşamalı REST API |
| **Frontend** | Next.js 16 + React 19 + TypeScript + Tailwind |
| **Veritabanı** | PostgreSQL + pgvector |
| **Altyapı** | Docker Compose — tek komutla kurulum |

### Neden DeepSeek?

- **Maliyet:** GPT-4'ün ~1/20'si
- **Thinking Mode:** Zincirleme düşünce ile daha tutarlı yanıtlar
- **Türkçe:** KVKK, BDDK, taksit, pazarlık gibi yerel bağlamı anlıyor

---

## Slide 6: Ürün

### 3 Adımlı Araştırma Akışı

```
1. Defne Sohbet        2. Mülakat             3. Rapor
   (Flash)                (Flash, batch)         (algoritmik)

   "Fikrini anlat..."    10 sentetik persona      Findings
                         Tüm sorular tek          Van Westendorp PSM
                         API çağrısı              Pain matrix
                                                  Aksiyon önerileri
```

### Demo: `localhost:4001` → 2 dakikada tam araştırma

---

## Slide 7: İş Modeli

### 5 Katmanlı Plan

| Plan | Fiyat (USD) | Araştırma | Hedef |
|---|---|---|---|
| **Free** | $0 | 2 (veya 1 ay) | Deneme, değer kanıtlama |
| **Flex** | $49 (tek seferlik) | 3 araştırma | Tek seferlik projeler |
| **Starter** | $69/ay ($55/ay yıllık) | 10/ay | Solo founder, küçük ekip |
| **Pro** | $169/ay ($135/ay yıllık) | Sınırsız | Ajans, ürün ekibi |
| **Enterprise** | Özel | Sınırsız | Kurumsal, özelleştirilmiş |

### Upsell Stratejisi

Free'de **paywall + buzlu önizleme.** Kullanıcı değeri görür → yükseltmek ister.

---

## Slide 8: Birim Ekonomisi

### Araştırma Başına Maliyet

| Kaynak | Maliyet |
|---|---|
| DeepSeek API | ~$0.008–0.024 / araştırma |
| Sunucu (payı) | ~$0.01 / araştırma |
| **Toplam** | **~$0.02–0.04** |

### Karlılık

| Plan | Aylık Gelir | Max COGS | Marj |
|---|---|---|---|
| Flex | $49 | ~$0.05 | ~%99.9 |
| Starter | $69 | ~$0.20 | ~%99.7 |
| Pro | $169 | ~$2 | ~%98.8 |

**1 Pro kullanıcı, tüm altyapı maliyetini ~10–25x karşılar.**

---

## Slide 9: Rekabet Avantajı

| Özellik | Clarere | Geleneksel | Diğer AI Araçları |
|---|---|---|---|
| Türkiye odağı | ✅ KVKK, BDDK, SES | ❌ | ❌ |
| Bilimsel metodoloji | ✅ Grounded Simulation | ⚠️ | ❌ |
| Süre | 2 dakika | 4-6 hafta | Değişken |
| Maliyet/araştırma | ~$0.01–0.04 | 50.000+ TL | $10-100 |
| Fiyat analizi | ✅ Van Westendorp | ✅ | ❌ |
| Anti-dalkavukluk | ✅ ELEPHANT | ❌ | ❌ |

---

## Slide 10: Pazar Fırsatı

### Hedef Kitle

| Segment | Pazar Büyüklüğü (TR) |
|---|---|
| Startup'lar | 15.000+ aktif |
| Dijital ajanslar | 5.000+ |
| E-ticaret işletmeleri | 500.000+ |
| Ürün ekipleri (KOBİ) | 50.000+ |

### Adreslenebilir Pazar

**%1 pazar payı = 5.700 müşteri × ortalama 3.000 TL/ay = 17M TL/ay**

---

## Slide 11: Yol Haritası

| Faz | Hedef | Zaman |
|---|---|---|
| **Şu an** | MVP hazır, demo çalışıyor | ✅ |
| **Faz 1** | Beta kullanıcı (50 kişi), geri bildirim | 1 ay |
| **Faz 2** | JWT auth, Paddle ödeme, public launch | 2 ay |
| **Faz 3** | Enterprise: yerel Türkçe LLM fine-tuning | 3-6 ay |
| **Faz 4** | İngilizce, Arapça, Avrupa pazarları | 6-12 ay |

---

## Slide 12: Takım & İletişim

### İletişim

- **Email:** hiclarere@clarere.com
- **Demo:** [github.com/kogu1988/clarere](https://github.com/kogu1988/clarere)

---

## Slide 13: Demo Zamanı

# Canlı Demo

### `python launch.py` → `localhost:4001`

1. Defne ile sohbet (30 sn)
2. Araştırmayı Başlat (15 sn)
3. Raporu Oluştur (3 sn)
4. Sonuçları gör

---

## Slide 14: Kapanış

# Clarere

### Pazar araştırmasını demokratikleştiriyoruz.

**Soru & Cevap**
