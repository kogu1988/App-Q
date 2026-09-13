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
│   │       ├── client/       İstemci API endpoint'leri (paket)
│   │       │   ├── studies.py       Study CRUD / bulgular / PDF
│   │       │   ├── research.py      Plan, persona üretimi, araştırma, stream
│   │       │   ├── synthesis.py     Sentez raporu
│   │       │   ├── interaction.py   Takip sorusu + copilot
│   │       │   ├── intake.py        Defne intake + persona havuzu
│   │       │   ├── account.py       Hesap/plan, iletişim, KVKK
│   │       │   ├── ws.py            WebSocket ticket/durum
│   │       │   ├── context.py       Araştırma bağlamı (PII)
│   │       │   ├── _deps.py         Ortak bağımlılıklar (plan/kota/limit)
│   │       │   └── _schemas.py      İstek modelleri
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
│       ├── workflow/          Araştırma orkestrasyonu (paket)
│       │   ├── planning.py         Plan, varsayım, mülakat senaryosu
│       │   ├── personas.py         Persona üretimi + bio zenginleştirme
│       │   ├── interviews.py       Senkron mülakat
│       │   ├── interviews_stream.py Streaming mülakat
│       │   ├── interviews_batch.py  Batch mülakat + tur yenileme
│       │   └── _constants.py        Paylaşılan sabitler
│       ├── analytics/         Rapor sentezi (paket)
│       │   ├── synthesis.py     synthesize_report orkestrasyonu
│       │   ├── ab_report.py     A/B varyant raporu
│       │   ├── findings.py      Bulgu çıkarımı + pain-point/segment özetleri
│       │   ├── evidence.py      Kanıt zinciri + karar katmanı
│       │   ├── pricing.py       Van Westendorp PSM
│       │   ├── corroboration.py Harici kanıt (web)
│       │   ├── metrics.py       Rapor metrikleri + kalite
│       │   └── enrichment.py    Anlatı zenginleştirme (Pro LLM)
│       ├── matrix.py          Rogers × SES kohort matrisi & stance diversity
│       ├── quality.py         Kalite değerlendirmesi + EWMA + echo detection
│       ├── adversarial.py     4-aşamalı adversarial review motoru
│       ├── intake.py          Defne chatbot akışı
│       ├── providers.py       LLM adaptörü (DeepSeek API)
│       ├── database/          DB katmanı (paket) — bağlantı, CRUD, migration, KPI
│       │   ├── connection.py     Bağlantı havuzu + oturum yönetimi
│       │   ├── studies.py        Çalışma CRUD + PDF + araştırma job kuyruğu
│       │   ├── clients.py        İstemci CRUD + plan/kota + auth
│       │   ├── usage.py          Token kullanımı + maliyet
│       │   ├── events.py         Ürün (KPI) event'leri
│       │   ├── billing.py        Paddle webhook durumu + KVKK veri işlemleri
│       │   ├── findings.py       Kanıt zinciri + AI gerekçe kaydı
│       │   └── migrations/       init_db() + şema/migration/seed
│       ├── models.py          Dataclass veri sözleşmeleri
│       ├── plan_config.py     Plan katmanı feature gate SSOT
│       ├── pricing_table.py   DeepSeek token fiyatlandırma SSOT (USD/1M)
│       ├── paddle_config.py   Paddle price → plan eşlemesi SSOT
│       ├── paddle_webhooks.py Paddle imza doğrulama + event işleme
│       └── reporting/         Markdown/HTML rapor üretimi (paket)
│           ├── markdown.py      render_markdown
│           ├── html.py          render_report_html
│           └── _html_utils.py   HTML yardımcıları
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
| **Admin Koruması** | `X-Admin-Key` header dependency; production'da key yoksa erişim kapalı (503) |
| **Event Loop Koruması** | Senkron LLM/DB endpoint'leri threadpool'da çalışır — eşzamanlı istekler birbirini kilitlemez |
| **LLM Dayanıklılık** | Timeout + exponential backoff retry + araştırma süre bütçesi |
| **Token Muhasebesi** | Her LLM çağrısı `token_usage`'a yazılır; dönemsel bütçe aşımında 429 |
| **Paddle Billing** | Checkout + webhook (HMAC imza, idempotent, sıralı) — Paddle merchant of record |

---

## Bilimsel Altyapı

Clarere, grounded simulation akademik çerçevesine dayanır (Bilal 2026, Rogers 2003, TÜAD 2025 SES, Hofstede). Metodolojik detaylar `packages/research_engine/` içindeki modüller ve `MEMORY.md` dosyasında özetlenmiştir.

> **Kapsam ve sınırlılık:** Clarere bir **hipotez ve araştırma triage** platformudur. Çıktılar istatistiksel temsil iddiası taşımaz; kişilik/dağılım modelleri kamuya açık çerçevelerden yararlanır. Rapor yüzeyleri veriyi kökenine göre **sentetik / algoritmik / harici** olarak etiketler. Yüksek riskli kararlar gerçek kullanıcı, satış veya saha verisiyle doğrulanmalıdır.

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
| Deneme süresi | 1 ay veya 2 araştırma (hangisi önce biterse) | — | — | — | — |
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
git clone https://github.com/kogu1988/clarere.git
cd clarere
```

### 2. Ortam Değişkenlerini Ayarla

`.env` dosyasını oluştur:

```env
DEEPSEEK_API_KEY=sk-your-key-here
POSTGRES_PASSWORD=guclu-bir-sifre
```

### 3. Tek Tıkla Başlat (Docker — önerilen)

```powershell
python launch.py
# veya Windows'ta: start.bat
```

Bu komut:
1. Docker stack'ini başlatır (`docker-compose.prod.yml` + `docker-compose.local.yml`): PostgreSQL, Redis, API, Celery, SearXNG, frontend, Caddy
2. Servisler hazır olana kadar bekler
3. Tarayıcıda otomatik açar

| Servis | Adres |
|--------|-------|
| Frontend | http://localhost:4001 |
| Tam stack (Caddy) | http://localhost:8080 |
| API Docs | http://localhost:8080/docs |

Durdurmak için:

```powershell
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down
```

### Host Dev Modu (hızlı backend reload)

```powershell
python launch.py --dev
```

Backend `uvicorn --reload` (:4000) + frontend `next dev` (:4001) olarak host'ta çalışır.
Docker stack kapalı olmalıdır (4001 portu paylaşılır).

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|-----------|---------|
| `DEEPSEEK_API_KEY` | — | **Zorunlu** — DeepSeek API anahtarı |
| `DEEPSEEK_FLASH_MODEL` | `deepseek-flash` | Intake ve interview modeli (eski `deepseek-v4-flash` emekli) |
| `DEEPSEEK_PRO_MODEL` | `deepseek-v4-pro` | Sentez ve analiz modeli |
| `DEEPSEEK_TIMEOUT` | `120` | LLM çağrısı zaman aşımı (saniye) |
| `DEEPSEEK_MAX_RETRIES` | `3` | LLM yeniden deneme sayısı (exponential backoff) |
| `DEEPSEEK_MAX_TOKENS` | `8192` | Çağrı başına maksimum üretim token'ı |
| `DEEPSEEK_REASONING_EFFORT` | `high` | Thinking effort: `low` \| `high` \| `max` (rol bazlı override edilir) |
| `LLM_CACHE_ENABLED` | `true` | İçerik-hash LLM önbelleği (maliyet azaltma) |
| `LLM_CACHE_MAX` / `LLM_CACHE_TTL` | `512` / `3600` | Önbellek boyutu / TTL (saniye) |
| `RESEARCH_DEADLINE_SECONDS` | `300` | Araştırma süre bütçesi — aşılırsa kalan personalar atlanır |
| `THREADPOOL_SIZE` | `64` | Senkron endpoint'ler için threadpool boyutu |
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
| `ADMIN_SECRET_KEY` | — | Admin API koruması — production'da zorunlu |
| `JWT_SECRET` | — | JWT imzalama anahtarı — production'da zorunlu, min 32 karakter |
| `ALLOWED_ORIGINS` | `*` (dev) | CORS — production'da zorunlu |
| `CELERY_CONCURRENCY` | `1` | Celery worker sayısı |

### Paddle Billing

| Değişken | Açıklama |
|----------|---------|
| `PADDLE_ENV` | `sandbox` \| `production` |
| `PADDLE_API_KEY` | Sunucu tarafı API anahtarı (sandbox: `pdl_sdbx_...`) |
| `PADDLE_WEBHOOK_SECRET` | Notification destination imza anahtarı |
| `PADDLE_PRICE_FLEX` / `_STARTER_MONTHLY` / `_STARTER_ANNUAL` / `_PRO_MONTHLY` / `_PRO_ANNUAL` | Plan → Paddle price ID eşlemesi |
| `NEXT_PUBLIC_PADDLE_ENV` | Frontend Paddle.js ortamı |
| `NEXT_PUBLIC_PADDLE_CLIENT_TOKEN` | Frontend Paddle.js client token (yayınlanması güvenli) |

---

## API Referansı

### İstemci API (`/api/client`)

| Method | Endpoint | Açıklama | Auth | Model |
|--------|----------|---------|------|-------|
| `POST` | `/register` | Kullanıcı kaydı (idempotent) | — | — |
| `GET` | `/me` | Plan ve kullanım bilgisi | `X-Username` | — |
| `POST` | `/upgrade-plan` | Plan yükseltme | `X-Username` | — |
| `POST` | `/intake` | Defne chatbot mesajı | — | Flash |
| `POST` | `/research` | Plan + Persona + Batch Mülakat (senkron) | `X-Username` | Flash |
| `POST` | `/research/jobs` | Async araştırma başlat → 202 `job_id` | `X-Username` | Flash |
| `GET` | `/research/jobs/{id}` | Async araştırma durumu (queued/running/completed/failed) | `X-Username` | — |
| `POST` | `/synthesize` | Sentez raporu üret | `X-Username` | Pro (zenginleştirme) |
| `GET` | `/studies` | Araştırma listesi | `X-Username` | — |
| `GET` | `/studies/{id}` | Araştırma detayı | `X-Username` | — |
| `GET` | `/me/export` | KVKK veri dışa aktarma (JSON indirme) | `X-Username` | — |
| `DELETE` | `/me` | KVKK hesap silme (abonelik iptali + veri silme) | `X-Username` | — |
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
| `GET` | `/usage` | Kullanıcı bazlı token + maliyet özeti |

### Billing API (`/api/billing`)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|---------|------|
| `POST` | `/checkout` | Paddle checkout için price ID + müşteri bilgisi | `X-Username` |
| `GET` | `/subscription` | Abonelik durumu (plan, status, dönem sonu) | `X-Username` |
| `GET` | `/portal` | Paddle müşteri portalı linki | `X-Username` |
| `POST` | `/webhook` | Paddle webhook — **HMAC imza doğrulaması** (auth header yok) | İmza |

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
├── workflow/            Araştırma orkestrasyonu (paket)
│                          → build_research_plan()      [planning.py]
│                          → generate_personas()        [personas.py]
│                          → run_interviews()           [interviews.py]
│                          → run_interviews_stream()    [interviews_stream.py]
│                          → run_interviews_batch()     [interviews_batch.py]
│                          → build_research_plan()
│                          → generate_personas()
│                          → run_interviews_batch()
│                          → run_interviews()
│                          → run_interviews_stream()
├── analytics/           Rapor sentezi (paket)
│                          → synthesize_report()          [synthesis.py]
│                          → synthesize_ab_report()       [ab_report.py]
│                          → van_westendorp_analysis()    [pricing.py]
│                          → build_ses_cross_tab()        [findings.py]
│                          → build_evidence_graph()       [evidence.py]
│                          → corroborate_findings()       [corroboration.py]
│                          → build_report_metrics()       [metrics.py]
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
├── database/            DB katmanı (paket)
│                          → ThreadedConnectionPool (min=2, max=10)
│                          → init_db() + migrations (migrations/)
│                          → studies / clients / usage / events / billing / findings
├── nodes/               LangGraph node'ları
│   ├── sycophancy.py    ELEPHANT anti-dalkavukluk prompt
│   ├── culture.py       Hofstede TR + SES profilleri
│   ├── memory.py        ACT-R bilişsel bellek modeli
│   └── router.py        Keyword-based routing
├── routers/             Streaming router
├── reporting/           Markdown/HTML üretimi (paket)
│                          → render_markdown()            [markdown.py]
│                          → render_report_html()         [html.py]
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

| Test Alanı | Kapsam |
|---|---|
| Stance diversity | Shannon entropy, Largest Remainder, Skeptic garantisi |
| EWMA & echo | `detect_echo`, `calculate_ewma`, echo drift denetimi |
| Van Westendorp | PSM kesişimleri (OPP/IPP/PMC/PME) |
| Intake | Input reframing, Jaccard, loop detection, tur limiti |
| Workflow & ELEPHANT | Sistem promptu, Agreeableness kalibrasyonu |
| Quality | Bias, acquiescence, meta-tone, research quality |
| Evidence chain & Decision layer | Kanıt grafiği, SHIP/ITERATE/INVESTIGATE/KILL |
| Plan enforcement | Plan gate'leri, gelir sızıntısı regresyonu |
| Paddle & fiyatlandırma | İmza doğrulama, plan eşlemesi, token maliyeti |
| Güvenlik & KVKK | JWT/admin guard, PII maskeleme, veri silme |
| Priv/privacy, RLS, org | Tenant/organizasyon izolasyonu |

> **Test sayısı SSOT:** Kesin sayı **CI'nın güncel koşusudur** (`ci.yml` her push'ta job özetine yazar). Tek komutla yerel çalıştırma (Postgres port-forward'ını otomatik kurar):
>
> ```bash
> python scripts/run_tests.py
> ```
>
> Ayrıntılar, DB-gated testler ve stack gerektiren testler: **[`TESTING.md`](./TESTING.md)**

---

## Güvenlik Notları

- **Lokal/Demo:** Mevcut `X-Username` header auth bu ortam için yeterlidir
- **Production öncesi:** JWT auth migrasyonu zorunludur (`JWT_SECRET`, min 32 karakter)
- **`ADMIN_SECRET_KEY`** production'da zorunludur — yoksa admin API **503** döner (erişim verilmez). Karşılaştırma timing-safe'dir; başarısız denemeler audit log'a yazılır
- **`DEEPSEEK_API_KEY`** `.env`'de tutulmalı, asla commit edilmemeli
- **Paddle:** `PADDLE_WEBHOOK_SECRET` olmadan webhook reddedilir; imza doğrulanmadan hiçbir payload işlenmez
- **CORS:** Production'da `ALLOWED_ORIGINS` mutlaka kısıtlanmalı (varsayılan `*` yalnızca geliştirme içindir)
- **`/upgrade-plan`** production'da kapalıdır — plan yalnızca Paddle ödeme akışıyla yükseltilir

---

## Production / Dağıtım

Canlıya geçiş için ayrıntılı, sıralı plan: **`server_plan.md`**

**Mimari (statüs için `server_plan.md` §Statü matrisi):**

- **Birincil (aktif karar):** Oracle Cloud Always Free — **tek ARM VM**, self-hosted (PostgreSQL + pgvector + Redis + API + Celery + Caddy).
- **İkincil (yedek):** **Vercel** (frontend) + **netcup VPS** (API + Celery + Redis + Caddy + SearXNG) + **Neon** (PostgreSQL + pgvector).

> ⚠️ Aktif karar Oracle'dır; netcup + Neon + Vercel yedektir ve `docker-compose.cloud.yml` yedek mimariye aittir. Karar değişirse bu bölüm ve `server_plan.md` birlikte güncellenir.

| Dosya | Görev |
|---|---|
| `server_plan.md` | Faz faz canlıya geçiş planı (kontrol listeleriyle) |
| `docker-compose.cloud.yml` | Bulut production stack — PostgreSQL yok (Neon), Caddy ile TLS |
| `Caddyfile.cloud` | `api.clarere.com` otomatik Let's Encrypt + reverse proxy |
| `docker-compose.prod.yml` + `docker-compose.local.yml` | Tek-sunucu / yerel Docker stack (korunmuştur) |
| `.env.production.example` | Sunucu env şablonu |
| `.github/workflows/ci.yml` | CI: pytest + `tsc --noEmit` + lint |
| `scripts/backup_db.sh` | Günlük `pg_dump` yedeği (14 gün) |
| `scripts/setup_paddle_catalog.py` | Paddle ürün/fiyat/destination idempotent kurulum |

```bash
# Sunucuda:
cp .env.production.example .env && chmod 600 .env   # değerleri doldur
docker compose -f docker-compose.cloud.yml up -d --build
curl -s https://api.clarere.com/health
```

**Opsiyonel servisler (env ile açılır):** `SENTRY_DSN` → hata izleme · `RESEND_API_KEY` → işlemsel e-posta.

---

## Kısıtlamalar

Clarere **yönlendirici hipotezler** üretir, istatistiksel olarak temsili pazar araştırması değildir. Yüksek riskli kararlar gerçek kullanıcı görüşmeleri, satış verisi veya saha araştırmasıyla doğrulanmalıdır.

---

*Clarere — FastAPI + Next.js + PostgreSQL/pgvector + DeepSeek API*
*Stance Diversity · EWMA Echo · Van Westendorp PSM · Batch Interviews*
