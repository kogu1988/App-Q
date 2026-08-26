# Clarere

> **Türkiye odaklı sentetik persona araştırma platformu.** Bir ürün fikrini veya pazar araştırması brief'ini alır; yapay zeka personaları oluşturur, yapılandırılmış mülakatlar simüle eder ve kanıta dayalı pazar içgörüleri üretir.

---

## İçindekiler

- [Genel Bakış](#genel-bakış)
- [Mimari](#mimari)
- [Özellikler](#özellikler)
- [Bilimsel Altyapı](#bilimsel-altyapı)
- [Plan Katmanları](#plan-katmanları)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [API Referansı](#api-referansı)
- [Proje Yapısı](#proje-yapısı)
- [Testler](#testler)
- [Güvenlik Notları](#güvenlik-notları)
- [Kısıtlamalar](#kısıtlamalar)

---

## Genel Bakış

Clarere, gerçek kullanıcı görüşmesi yapmadan pazar araştırması yürütmek isteyen ürün ekipleri, kurucular ve araştırma mimarları için tasarlanmıştır. Sistem şu adımlarla çalışır:

1. **Brief Alma** — Defne (araştırma sihirbazı yapay zeka) kullanıcıyla sohbet ederek araştırma brief'ini adım adım doldurur
2. **Plan Üretme** — Brief'e göre mülakat planı ve soru seti oluşturur
3. **Persona Oluşturma** — TÜAD 2025 SES × Rogers Diffusion matrisine göre kalibre edilmiş sentetik personalar üretir
4. **Mülakat Simülasyonu** — Her persona için tüm soruları batch olarak yanıtlar (tek API çağrısı)
5. **Sentez Raporu** — Pazar içgörülerini, fiyatlandırma analizini (Van Westendorp PSM) ve aksiyon önerilerini raporlar
6. **Adversarial Review** — Raporun 4 aşamalı eleştirel denetimi; stance diversity, bias ve echo drift kontrolleri dahil

---

## Mimari

```
Clarere/
├── apps/
│   ├── backend/              FastAPI (Python 3.10+) — REST API
│   │   ├── main.py           Uygulama başlatma, CORS, rate limiting
│   │   └── routers/
│   │       ├── client.py     İstemci API endpoint'leri
│   │       └── admin.py      Operatör/admin API endpoint'leri
│   │
│   └── frontend/             Next.js 16 + React 19 + TypeScript
│       └── src/app/
│           ├── page.tsx      Landing page
│           ├── client/       Müşteri dashboard & araştırma akışı
│           └── admin/        Operatör paneli
│
├── packages/
│   └── research_engine/      Domain mantığı (Python)
│       ├── workflow.py        Araştırma orkestrasyonu + batch interviews
│       ├── analytics.py       Rapor sentezi & Van Westendorp PSM
│       ├── matrix.py          Rogers × SES kohort matrisi & stance diversity
│       ├── quality.py         Kalite değerlendirmesi + EWMA + echo detection
│       ├── adversarial.py     4-aşamalı adversarial review motoru
│       ├── intake.py          Defne chatbot akışı
│       ├── providers.py       LLM adaptörü (DeepSeek API)
│       ├── database.py        Tüm DB operasyonları + bağlantı havuzu
│       ├── models.py          Dataclass veri sözleşmeleri
│       ├── plan_config.py     Plan katmanı feature gate SSOT
│       └── reporting.py       PDF/HTML rapor üretimi
│
├── launch.py                  Tek tıkla başlatma
├── docker-compose.yml         PostgreSQL (pgvector) + Redis
└── .env                       Ortam değişkenleri (API key, DB)
```

**Veri akışı:**
```
Frontend (Next.js :4001)
    → POST /api/client/intake              → Defne chatbot (DeepSeek Flash)
    → POST /api/client/research            → Plan + Persona + Batch Mülakat (DeepSeek Flash)
    → POST /api/client/synthesize          → Sentez raporu
```

---

## Özellikler

### Araştırma Motoru

| Özellik | Açıklama |
|---------|---------|
| **Defne Chatbot** | Araştırma brief'ini sohbet yoluyla adım adım dolduran yapay zeka sihirbazı |
| **TÜAD SES × Rogers Kota** | Türkiye nüfus dağılımı (AB/C1/C2/DE) × Rogers Diffusion (5 stance) matris kotalaması |
| **Stance Diversity Garantisi** | Shannon entropy skoru; N≥5 panelde Skeptic zorunlu (anti-sycophancy guard) |
| **Batch Mülakatlar** | Her persona için tüm sorular tek API çağrısıyla yanıtlanır |
| **EWMA Kalite Kontrolü** | Exponentially Weighted Moving Average ile tur bazlı kalite izleme; düşüşte prompt tamir |
| **Echo Detection** | Jaccard benzerliği ile yankılanma tespiti; echo → −0.4 kalite penaltısı |
| **Van Westendorp PSM** | Kesişim tabanlı fiyat hassasiyeti analizi — OPP, IPP, PMC, PME eşikleri |
| **A/B Test Modu** | İki farklı ürün/kurgu arasında sentetik oy simülasyonu |
| **B2B Modu** | Organizasyon şeması, B2B karar verici personalar, endüstri segmentasyonu |
| **4-Aşamalı Adversarial Review** | Bias, stance diversity, methodology ve echo drift denetimi |
| **PDF/HTML Rapor** | Araştırma raporunun PDF ve HTML formatında dışa aktarımı |

### Teknik Özellikler

| Özellik | Açıklama |
|---------|---------|
| **DeepSeek API** | Flash (intake/interview) + Pro (synthesis) — Thinking Mode aktif |
| **user_id Isolation** | KVCache, content safety ve scheduling izolasyonu |
| **Context Caching** | DeepSeek disk cache — ortak prefix'ler için otomatik maliyet avantajı |
| **Bağlantı Havuzu** | `ThreadedConnectionPool` (min=2, max=10) ile verimli DB yönetimi |
| **Rate Limiting** | slowapi — endpoint bazlı sınırlar |
| **Atomik Kota** | `UPDATE...RETURNING` ile TOCTOU-güvenli simülasyon sayacı |
| **Migration Versioning** | `schema_migrations` tablosu ile idempotent DB migrationları |
| **Security Headers** | X-Frame-Options, CSP, HSTS, nosniff, Referrer-Policy |
| **Admin Koruması** | `X-Admin-Key` header dependency ile tüm admin endpoint'leri korumalı |

---

## Bilimsel Altyapı

Clarere, grounded simulation akademik çerçevesine dayanır (Bilal 2026, Rogers 2003, TÜAD 2025 SES, Hofstede). Metodolojik detaylar `packages/research_engine/` içindeki modüller ve `MEMORY.md` dosyasında özetlenmiştir.

### Grounded Simulation Principle

| Bileşen | Açıklama | Dosya |
|---------|---------|-------|
| **NEO-PI-R / OCEAN** | Persona psikometrik profilleme (Big Five) | `matrix.py` |
| **ACT-R Bellek Modeli** | Güç Yasası sönümlemesi ile bilişsel bağlam yönetimi | `workflow.py` |
| **ELEPHANT Çerçevesi** | Onaylama sapması sıfırlama protokolü | `nodes/sycophancy.py` |
| **Hofstede TR** | Kültürel yanıt kalibrasyonu (PDI=66, IDV=37, UAI=85) | `nodes/culture.py` |

### Stance Diversity (ΔF1 = −0.582)

Rogers Diffusion of Innovations 5 duruşu (Innovator, EarlyAdopter, Mainstream, Laggard, Skeptic) × TÜAD 2025 SES dağılımı (AB/C1/C2/DE) ile Largest Remainder yöntemi kullanılarak deterministik panel kotalaması yapılır:

- **Minimum 3 farklı stance** zorunlu
- **Skeptic her panelde** bulunmalı (anti-sycophancy guard)
- **Shannon entropy skoru** ≥ 0.5 önerilir

### EWMA Echo Protokolü

```
EWMA_t = α · S_t + (1 − α) · EWMA_{t−1}   [α = 0.3]
```

Her mülakat turunda kalite skoru hesaplanır. Skor 0.65 altına düştüğünde veya Jaccard echo ≥ 0.40 tetiklendiğinde sistem prompt otomatik tamir edilir.

### Van Westendorp PSM

Kümülatif frekans eğrilerinin matematiksel kesişimleri ile:
- **OPP** (Optimal Price Point) — "Çok Ucuz" ∩ "Çok Pahalı"
- **IPP** (Indifference Price Point) — "Ucuz" ∩ "Pahalı"
- **PMC / PME** — Kabul edilebilir fiyat aralığı sınırları

---

## Plan Katmanları

| Özellik | Free | Flex | Starter | Pro | Enterprise |
|---------|:----:|:----:|:-------:|:---:|:----------:|
| Aylık araştırma | 2 | 3 | 10 | Sınırsız | Sınırsız |
| Persona sayısı | 10 | 10 | 10 | 10 | Sınırsız |
| Streaming SSE | — | ✓ | ✓ | ✓ | ✓ |
| PDF export | — | ✓ | ✓ | ✓ | ✓ |
| SES cross-tab | — | ✓ | ✓ | ✓ | ✓ |
| A/B Test modu | — | ✓ | ✓ | ✓ | ✓ |
| B2B modu | — | — | — | ✓ | ✓ |
| Adversarial review | ✓ | ✓ | ✓ | ✓ | ✓ |
| Brand health analizi | — | — | — | ✓ | ✓ |
| White-label | — | — | — | ✓ | ✓ |
| Özel persona havuzu | — | — | — | — | ✓ |
| Multi-user org | — | — | — | — | ✓ |
| Fine-tuning export | — | — | — | — | ✓ |

---

## Hızlı Başlangıç

### Ön Gereksinimler

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- [DeepSeek API key](https://platform.deepseek.com)

### 1. Depoyu Klonla

```powershell
git clone https://github.com/kogu1988/App-Q.git
cd App-Q
```

### 2. Ortam Değişkenlerini Ayarla

`.env` dosyasını oluştur:

```env
DEEPSEEK_API_KEY=sk-your-key-here
POSTGRES_PASSWORD=guclu-bir-sifre
```

### 3. Tek Tıkla Başlat

```powershell
python launch.py
```

Bu komut sırasıyla:
1. Docker servislerini kontrol eder ve başlatır (PostgreSQL + Redis)
2. Backend API'i başlatır (port 4000)
3. Frontend'i başlatır (port 4001, gerekirse `npm install` çeker)
4. Tarayıcıda otomatik açar

### Manuel Başlatma

```powershell
# Altyapı
docker compose up -d postgres redis

# Backend
python -m uvicorn apps.backend.main:app --host 127.0.0.1 --port 4000 --reload

# Frontend
cd apps/frontend
npm install
npm run dev
```

| Servis | Adres |
|--------|-------|
| Frontend | http://localhost:4001 |
| API | http://localhost:4000 |
| API Docs | http://localhost:4000/docs |

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|-----------|---------|
| `DEEPSEEK_API_KEY` | — | **Zorunlu** — DeepSeek API anahtarı |
| `DEEPSEEK_FLASH_MODEL` | `deepseek-v4-flash` | Intake ve interview modeli |
| `DEEPSEEK_PRO_MODEL` | `deepseek-v4-pro` | Sentez ve analiz modeli |
| `APP_ENV` | `development` | `development` \| `production` |
| `POSTGRES_USER` | `clarere_user` | PostgreSQL kullanıcı adı |
| `POSTGRES_PASSWORD` | `clarere_password` | PostgreSQL şifresi |
| `POSTGRES_DB` | `clarere_db` | Veritabanı adı |
| `POSTGRES_HOST` | `localhost` | PostgreSQL sunucu adresi |
| `POSTGRES_PORT` | `5433` | PostgreSQL port |
| `REDIS_HOST` | `localhost` | Redis sunucu adresi |
| `REDIS_PORT` | `6379` | Redis port |
| `VALKEY_URL` | `redis://localhost:6379/0` | Celery broker URL |
| `PG_POOL_MIN` | `2` | Bağlantı havuzu minimum |
| `PG_POOL_MAX` | `10` | Bağlantı havuzu maksimum |
| `ADMIN_SECRET_KEY` | — | Admin API koruması |
| `ALLOWED_ORIGINS` | `*` (dev) | CORS — production'da zorunlu |
| `CELERY_CONCURRENCY` | `1` | Celery worker sayısı |

---

## API Referansı

### İstemci API (`/api/client`)

| Method | Endpoint | Açıklama | Auth | Model |
|--------|----------|---------|------|-------|
| `POST` | `/register` | Kullanıcı kaydı (idempotent) | — | — |
| `GET` | `/me` | Plan ve kullanım bilgisi | `X-Username` | — |
| `POST` | `/upgrade-plan` | Plan yükseltme | `X-Username` | — |
| `POST` | `/intake` | Defne chatbot mesajı | — | Flash |
| `POST` | `/research` | Plan + Persona + Batch Mülakat | `X-Username` | Flash |
| `POST` | `/synthesize` | Sentez raporu üret | `X-Username` | — |
| `GET` | `/studies` | Araştırma listesi | `X-Username` | — |
| `GET` | `/studies/{id}` | Araştırma detayı | `X-Username` | — |
| `POST` | `/feedback` | Geri bildirim gönder | — | — |

> **Auth:** `X-Username: <kullanıcı-adı>` header'ı. Kayıt olmadan `Free` plan uygulanır.

### Admin API (`/api/admin`)

Tüm endpoint'ler `X-Admin-Key: <ADMIN_SECRET_KEY>` header'ı gerektirir.

| Method | Endpoint | Açıklama |
|--------|----------|---------|
| `GET` | `/clients` | Tüm müşteri listesi |
| `POST` | `/clients` | Yeni müşteri ekle |
| `PUT` | `/clients/{username}` | Müşteri güncelle |
| `DELETE` | `/clients/{username}` | Müşteri sil |
| `GET` | `/config` | Sistem konfigürasyonu |
| `POST` | `/config` | Konfigürasyon güncelle |
| `GET` | `/feedbacks` | Geri bildirimler |
| `GET` | `/audit_logs` | Audit logları |
| `GET` | `/personas` | Persona havuzu |

### Rate Limitleri

| Endpoint | Limit |
|----------|-------|
| `POST /register` | 10 istek/dakika |
| `GET /me` | 60 istek/dakika |
| `POST /interviews/stream` | 30 istek/dakika |
| `POST /intake` | 20 istek/dakika |
| Tüm diğer | 200 istek/dakika |

---

## Proje Yapısı

```
packages/research_engine/
├── models.py            Veri sözleşmeleri (dataclass, frozen)
├── workflow.py          Araştırma orkestrasyonu + batch interviews
│                          → build_research_plan()
│                          → generate_personas()
│                          → run_interviews_batch()
│                          → run_interviews()
│                          → run_interviews_stream()
├── analytics.py         Rapor sentezi (~750 satır)
│                          → synthesize_report()
│                          → van_westendorp_analysis()
│                          → build_ses_cross_tab()
├── matrix.py            Rogers × SES kohort matrisi
│                          → allocate_cohort_matrix()  [Largest Remainder]
│                          → validate_stance_diversity()
├── quality.py           LLM yanıt kalitesi
│                          → judge_answer_quality()
│                          → calculate_ewma()  [alpha=0.3]
│                          → detect_echo()  [Jaccard]
│                          → detect_acquiescence()
├── adversarial.py       4-aşamalı adversarial review
├── intake.py            Defne chatbot akışı
│                          → process_intake_chat()
├── providers.py         LLM adaptörü
│                          → DeepSeekResearchModel  (Flash + Pro)
├── database.py          DB operasyonları (~800 satır)
│                          → ThreadedConnectionPool (min=2, max=10)
│                          → init_db() + migrations
├── nodes/               LangGraph node'ları
│   ├── sycophancy.py    ELEPHANT anti-dalkavukluk prompt
│   ├── culture.py       Hofstede TR + SES profilleri
│   ├── memory.py        ACT-R bilişsel bellek modeli
│   └── router.py        Keyword-based routing
├── routers/             Streaming router
├── reporting.py         PDF/HTML üretimi
└── plan_config.py       Plan feature gate SSOT
```

---

## Testler

```powershell
# Tüm test süiti
pytest packages/research_engine/tests/ -v

# Belirli modül testleri
pytest packages/research_engine/tests/test_stance_diversity.py -v
pytest packages/research_engine/tests/test_ewma_echo.py -v
pytest packages/research_engine/tests/test_van_westendorp.py -v
```

| Test Dosyası | Kapsam | Test Sayısı |
|---|---|:---:|
| `test_stance_diversity.py` | Shannon entropy, validate_stance_diversity, Skeptic garantisi | 23 |
| `test_ewma_echo.py` | detect_echo, calculate_ewma, echo_drift_audit | 23 |
| `test_van_westendorp.py` | PSM kesişim hesabı | 22 |
| `test_intake.py` | Input reframing, Jaccard, loop detection, turn limit | 15 |
| `test_workflow.py` | ELEPHANT prompt, agreeableness kalibrasyonu | 14 |
| `test_quality.py` | Bias detection, acquiescence, meta-tone, research_quality | 14 |
| `test_semantic_router.py` | Keyword fallback, route validasyonu | 12 |
| `test_grounded.py` | ACT-R bellek, S-O-R sepet terk, Big Five | 3 |
| **Toplam** | | **126** |

---

## Güvenlik Notları

- **Lokal/Demo:** Mevcut `X-Username` header auth bu ortam için yeterlidir
- **Production öncesi:** JWT auth migrasyonu zorunludur
- **`ADMIN_SECRET_KEY`** set edilmezse admin API korumasız çalışır — development'ta terminal uyarısı verir, production'da **zorunludur**
- **`DEEPSEEK_API_KEY`** `.env`'de tutulmalı, asla commit edilmemeli
- **CORS:** Production'da `ALLOWED_ORIGINS` mutlaka kısıtlanmalı (varsayılan `*` yalnızca geliştirme içindir)

---

## Kısıtlamalar

Clarere **yönlendirici hipotezler** üretir, istatistiksel olarak temsili pazar araştırması değildir. Yüksek riskli kararlar gerçek kullanıcı görüşmeleri, satış verisi veya saha araştırmasıyla doğrulanmalıdır.

---

*Clarere — FastAPI + Next.js + PostgreSQL/pgvector + DeepSeek API*
*Stance Diversity · EWMA Echo · Van Westendorp PSM · Batch Interviews*
