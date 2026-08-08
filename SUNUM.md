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

**Süre: 2 dakika. Maliyet: 0.25 TL.**

---

## Slide 4: Bilimsel Altyapı

### Grounded Simulation (Bilal, 2026)

| Metodoloji | Açıklama |
|---|---|
| **Big Five / NEO-PI-R** | Kişilik profilleme — her persona psikometrik vektör |
| **Rogers Diffusion** | 5 yenilik benimseme profili (Innovator → Skeptic) |
| **Hofstede Kültür** | Türkiye özel: PDI=66, IDV=37, UAI=85 |
| **Van Westendorp PSM** | Fiyat hassasiyet analizi (OPP, IPP, PMC, PME) |
| **ELEPHANT Çerçevesi** | Anti-dalkavukluk — personalar ürünü beğenmek zorunda değil |

**Akademik doğrulama:** 46 çalışmada RFI = 0.815. Uzman referansın %93'ü.

---

## Slide 5: Teknoloji

### Modern Stack

| Katman | Teknoloji |
|---|---|
| **LLM** | DeepSeek V4 (Flash + Pro) — araştırma başına ~0.25 TL |
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

   "Fikrini anlat..."    5 sentetik persona      Findings
                         Tüm sorular tek          Van Westendorp PSM
                         API çağrısı              Pain matrix
                                                  Aksiyon önerileri
```

### Demo: `localhost:4001` → 2 dakikada tam araştırma

---

## Slide 7: İş Modeli

### 5 Katmanlı Plan

| Plan | Fiyat (aylık) | Araştırma | Hedef |
|---|---|---|---|
| **Free** | 0 TL | 2/ay | Deneme, değer kanıtlama |
| **Flex** | 1.990 TL | 3/paket | Tek seferlik projeler |
| **Starter** | 2.690 TL | 10/ay | Solo founder, küçük ekip |
| **Pro** | 6.790 TL | Sınırsız | Ajans, ürün ekibi |
| **Enterprise** | Özel | Sınırsız | Kurumsal, özelleştirilmiş |

### Upsell Stratejisi

Free'de **paywall + buzlu önizleme.** Kullanıcı değeri görür → yükseltmek ister.

---

## Slide 8: Birim Ekonomisi

### Araştırma Başına Maliyet

| Kaynak | Maliyet |
|---|---|
| DeepSeek API | ~0.25 TL |
| Sunucu (VPS) | ~0.50 TL |
| **Toplam** | **~0.75 TL** |

### Karlılık

| Plan | Aylık Gelir | Max Maliyet | Marj |
|---|---|---|---|
| Flex | 1.990 TL | ~2 TL | %99.9 |
| Starter | 2.690 TL | ~7 TL | %99.7 |
| Pro | 6.790 TL | ~75 TL | %98.9 |

**1 Pro kullanıcı = tüm altyapı maliyetini 90x karşılar.**

---

## Slide 9: Rekabet Avantajı

| Özellik | Clarere | Geleneksel | Diğer AI Araçları |
|---|---|---|---|
| Türkiye odağı | ✅ KVKK, BDDK, SES | ❌ | ❌ |
| Bilimsel metodoloji | ✅ Grounded Simulation | ⚠️ | ❌ |
| Süre | 2 dakika | 4-6 hafta | Değişken |
| Maliyet/araştırma | ~0.25 TL | 50.000+ TL | $10-100 |
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
| **Faz 2** | JWT auth, Stripe ödeme, public launch | 2 ay |
| **Faz 3** | Enterprise: yerel Türkçe LLM fine-tuning | 3-6 ay |
| **Faz 4** | İngilizce, Arapça, Avrupa pazarları | 6-12 ay |

---

## Slide 12: Takım & İletişim

### İletişim

- **Email:** hiclarere@clarere.com
- **Demo:** [github.com/kogu1988/App-Q](https://github.com/kogu1988/App-Q)

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
