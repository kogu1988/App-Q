# App-Q

> **Türkiye odaklı sentetik persona araştırma platformu.** Bir ürün fikrini veya pazar araştırması brief'ini alır; yapay zeka personaları oluşturur, yapılandırılmış mülakatlar simüle eder ve kanıta dayalı pazar içgörüleri üretir.

---

## İçindekiler

- [Genel Bakış](#genel-bakış)
- [Mimari](#mimari)
- [Özellikler](#özellikler)
- [Plan Katmanları](#plan-katmanları)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [API Referansı](#api-referansı)
- [Proje Yapısı](#proje-yapısı)
- [Geliştirme Notları](#geliştirme-notları)

---

## Genel Bakış

App-Q, gerçek kullanıcı görüşmesi yapmadan pazar araştırması yürütmek isteyen ürün ekipleri, kurucular ve araştırma mimarları için tasarlanmıştır. Sistem şu adımlarla çalışır:

1. **Brief Alma** — Defne (araştırma sihirbazı yapay zeka) kullanıcıyla sohbet ederek araştırma brief'ini adım adım doldurur
2. **Plan Üretme** — Brief'e göre mülakat planı ve soru seti oluşturur
3. **Persona Oluşturma** — TÜAD 2025 SES dağılımına göre kalibre edilmiş sentetik personalar üretir
4. **Mülakat Simülasyonu** — Her persona ile yapılandırılmış mülakat gerçekleştirir (streaming SSE)
5. **Sentez Raporu** — Pazar içgörülerini, fiyatlandırma analizini (Van Westendorp PSM) ve aksiyon önerilerini raporlar

---

## Mimari

```
App-Q/
├── apps/
│   ├── backend/              FastAPI (Python 3.10+) — REST API, SSE streaming
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
│       ├── workflow.py        Araştırma orkestrasyonu
│       ├── analytics.py       Rapor sentezi & Van Westendorp PSM
│       ├── intake.py          Defne chatbot akışı
│       ├── providers.py       LLM adaptör katmanı (Ollama router)
│       ├── caching.py         Semantik önbellek (hash → pgvector)
│       ├── database.py        Tüm DB operasyonları + bağlantı havuzu
│       ├── models.py          Dataclass veri sözleşmeleri
│       ├── plan_config.py     Plan katmanı feature gate SSOT
│       ├── quality.py         LLM yanıt kalite değerlendirmesi
│       ├── adversarial.py     Adversarial review motoru
│       └── reporting.py       PDF/HTML rapor üretimi
│
├── docker-compose.yml         PostgreSQL (pgvector) + Redis
└── .env.example               Ortam değişkeni şablonu
```

**Veri akışı:**
```
Frontend (Next.js)
    → POST /api/client/plan        → Araştırma planı
    → POST /api/client/personas/generate → Personalar
    → POST /api/client/interviews/stream → SSE mülakat akışı
    → POST /api/client/synthesize  → Sentez raporu
```

---

## Özellikler

### Araştırma Motoru

| Özellik | Açıklama |
|---------|---------|
| **Defne Chatbot** | Araştırma brief'ini sohbet yoluyla adım adım dolduran yapay zeka sihirbazı |
| **TÜAD SES Kota** | Türkiye nüfus dağılımına (AB/C1/C2/DE) göre kalibre edilmiş persona paneli |
| **Streaming Mülakatlar** | Server-Sent Events (SSE) ile gerçek zamanlı mülakat akışı |
| **Van Westendorp PSM** | Fiyat hassasiyeti analizi — OPP, IPP, PMC, PME eşikleri |
| **A/B Test Modu** | İki farklı ürün/kurgu arasında sentetik oy simülasyonu |
| **B2B Modu** | Organizasyon şeması, B2B karar verici personalar, endüstri segmentasyonu |
| **Adversarial Review** | Araştırma raporunu eleştirel gözle değerlendiren yapay zeka audit motoru |
| **Semantik Önbellek** | Hash + pgvector cosine similarity ile LLM maliyeti azaltma |
| **PDF/HTML Rapor** | Araştırma raporunun PDF ve HTML formatında dışa aktarımı |

### Teknik Özellikler

| Özellik | Açıklama |
|---------|---------|
| **Bağlantı Havuzu** | `ThreadedConnectionPool` (min=2, max=10) ile verimli DB yönetimi |
| **Rate Limiting** | slowapi — endpoint bazlı sınırlar (register: 10/dk, stream: 5/dk) |
| **Atomik Kota** | `UPDATE...RETURNING` ile TOCTOU-güvenli simülasyon sayacı |
| **Migration Versioning** | `schema_migrations` tablosu ile idempotent DB migrationları |
| **Security Headers** | X-Frame-Options, CSP, HSTS, nosniff, Referrer-Policy |
| **Admin Koruması** | `X-Admin-Key` header dependency ile tüm admin endpoint'leri korumalı |

---

## Plan Katmanları

| Özellik | Free | Starter | Pro | Enterprise |
|---------|:----:|:-------:|:---:|:----------:|
| Aylık araştırma | 2 | 10 | Sınırsız | Sınırsız |
| Persona sayısı | 3 | 5 | 7 | Sınırsız |
| Streaming SSE | — | ✓ | ✓ | ✓ |
| PDF export | — | ✓ | ✓ | ✓ |
| SES cross-tab | — | ✓ | ✓ | ✓ |
| A/B Test modu | — | — | ✓ | ✓ |
| B2B modu | — | — | ✓ | ✓ |
| Adversarial review | — | — | ✓ | ✓ |
| Brand health analizi | — | — | ✓ | ✓ |
| Özel persona havuzu | — | — | — | ✓ |
| White-label | — | — | — | ✓ |
| Multi-user org | — | — | — | ✓ |

---

## Hızlı Başlangıç

### Ön Gereksinimler

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- [Ollama](https://ollama.ai) (yerel LLM için)

### 1. Depoyu Klonla

```powershell
git clone <repo-url>
cd App-Q
```

### 2. Ortam Değişkenlerini Ayarla

```powershell
Copy-Item .env.example .env
```

`.env` dosyasını düzenle — en azından `POSTGRES_PASSWORD` zorunlu:

```env
POSTGRES_PASSWORD=güçlü-bir-şifre-gir
APP_MODEL_PROVIDER=ollama        # veya 'mock' (test için)
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### 3. Altyapıyı Başlat (Docker)

```powershell
docker compose up -d postgres
```

> Redis opsiyonel — mevcut sürümde aktif kullanımda değil.

### 4. Python Ortamını Kur

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5. Backend'i Başlat

```powershell
.\.venv\Scripts\uvicorn.exe apps.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend sağlık kontrolü:
```powershell
Invoke-RestMethod http://localhost:8000/health
# → { status: "ok", env: "development" }
```

### 6. Frontend'i Başlat

```powershell
cd apps/frontend
npm install
npm run dev
```

Frontend: [http://localhost:3000](http://localhost:3000)

### 7. Ollama Modeli (Opsiyonel)

```powershell
ollama pull qwen2.5:7b
# Veya App-Q özel fine-tune modeli:
ollama pull <model-adı>
```

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|-----------|---------|
| `APP_ENV` | `development` | `development` \| `production` |
| `APP_MODEL_PROVIDER` | `mock` | `mock` \| `ollama` \| `ollama-router` |
| `APP_MODEL_ID` | `app-q-qwen7b` | Varsayılan Ollama model adı |
| `APP_Q_B2C_MODEL_ID` | `app-q-trendyol` | B2C araştırmalar için model |
| `APP_Q_GENERAL_MODEL_ID` | `app-q-kizagan-e4b` | Genel araştırmalar için model |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API adresi |
| `APP_MODEL_TIMEOUT_SECONDS` | `240` | LLM zaman aşımı (saniye) |
| `POSTGRES_PASSWORD` | — | **Zorunlu** — PostgreSQL şifresi |
| `POSTGRES_USER` | `appq_user` | PostgreSQL kullanıcı adı |
| `POSTGRES_DB` | `appq_db` | Veritabanı adı |
| `POSTGRES_HOST` | `localhost` | PostgreSQL sunucu adresi |
| `POSTGRES_PORT` | `5433` | PostgreSQL port |
| `PG_POOL_MIN` | `2` | Bağlantı havuzu minimum |
| `PG_POOL_MAX` | `10` | Bağlantı havuzu maksimum |
| `ADMIN_SECRET_KEY` | — | Admin API koruması — production'da zorunlu |
| `ALLOWED_ORIGINS` | `*` (dev) | CORS — production'da zorunlu |
| `APP_LOG_PROMPTS` | `false` | LLM prompt'larını logla |

### Model Provider Seçimi

```env
# Test/geliştirme — LLM çağrısı yapmaz
APP_MODEL_PROVIDER=mock

# Tek model
APP_MODEL_PROVIDER=ollama
APP_MODEL_ID=qwen2.5:7b

# Çoklu model yönlendirme (B2C/Genel)
APP_MODEL_PROVIDER=ollama-router
APP_Q_B2C_MODEL_ID=app-q-trendyol
APP_Q_GENERAL_MODEL_ID=app-q-kizagan-e4b
```

---

## API Referansı

### İstemci API (`/api/client`)

| Method | Endpoint | Açıklama | Auth |
|--------|----------|---------|------|
| `POST` | `/register` | Kullanıcı kaydı (idempotent) | — |
| `GET` | `/me` | Plan ve kullanım bilgisi | `X-Username` |
| `POST` | `/upgrade-plan` | Plan yükseltme | `X-Username` |
| `POST` | `/intake` | Defne chatbot mesajı | — |
| `POST` | `/plan` | Araştırma planı oluştur | `X-Username` |
| `POST` | `/personas/generate` | Persona paneli üret | `X-Username` |
| `POST` | `/interviews/stream` | Mülakat simülasyonu (SSE) | `X-Username` |
| `POST` | `/synthesize` | Sentez raporu üret | `X-Username` |
| `GET` | `/studies` | Araştırma listesi | `X-Username` |
| `GET` | `/studies/{id}` | Araştırma detayı | `X-Username` |
| `GET` | `/studies/{id}/pdf` | PDF indir | `X-Username` |
| `POST` | `/feedback` | Geri bildirim gönder | — |

> **Auth:** `X-Username: <kullanıcı-adı>` header'ı. Kayıt olmadan `Free` plan uygulanır.  
> **Not:** JWT auth migrasyonu production öncesi sprint'te planlanmıştır.

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
| `GET` | `/schemas` | Brief ve soru şemaları |
| `GET` | `/plan-config` | Plan katmanı konfigürasyonu (JSON) |

### Rate Limitleri

| Endpoint | Limit |
|----------|-------|
| `POST /register` | 10 istek/dakika |
| `GET /me` | 60 istek/dakika |
| `POST /interviews/stream` | 5 istek/dakika |
| `POST /intake` | 20 istek/dakika |
| Tüm diğer | 200 istek/dakika |

---

## Proje Yapısı

```
packages/research_engine/
├── models.py          Veri sözleşmeleri (dataclass, frozen)
├── workflow.py        Araştırma orkestrasyonu (~870 satır)
│                        → build_research_plan()
│                        → generate_personas()
│                        → run_interviews_stream()
├── analytics.py       Rapor sentezi (~730 satır)
│                        → synthesize_report()
│                        → van_westendorp_analysis()
│                        → build_ses_cross_tab()
├── intake.py          Defne chatbot akışı
│                        → process_intake_chat()
├── providers.py       LLM adaptörü
│                        → OllamaResearchModel
│                        → OllamaRouterResearchModel (çoklu model)
│                        → MockResearchModel (test)
├── caching.py         Semantik önbellek
│                        → check_semantic_cache() (hash → cosine)
│                        → save_to_semantic_cache()
├── database.py        Tüm DB operasyonları (~790 satır)
│                        → ThreadedConnectionPool (min=2, max=10)
│                        → init_db() + schema_migrations versioning
│                        → atomic_increment_simulation_count()
├── quality.py         LLM yanıt kalitesi
│                        → judge_answer_quality()
│                        → detect_acquiescence()
├── adversarial.py     Araştırma audit motoru
├── reporting.py       PDF/HTML üretimi
└── plan_config.py     Plan feature gate SSOT
```

---

## Geliştirme Notları

### Backend Yeniden Başlatma

Kod değişikliklerinden sonra `__pycache__` temizlenmeden yeniden başlatma eski kodu çalıştırabilir:

```powershell
Remove-Item -Recurse -Force apps\backend\__pycache__, packages\research_engine\__pycache__ -ErrorAction SilentlyContinue
.\.venv\Scripts\uvicorn.exe apps.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Mock Modda Test

LLM olmadan UI ve API akışlarını test etmek için:

```env
APP_MODEL_PROVIDER=mock
```

Mock provider deterministik yanıtlar döner — Ollama bağlantısı gerektirmez.

### Veritabanı Durumu

`init_db()` uygulama başladığında otomatik çalışır ve:
- Tabloları oluşturur (`CREATE TABLE IF NOT EXISTS`)
- Migrationları uygular (`schema_migrations` ile versioned)
- Development ortamında demo kullanıcıları ekler (Free/Starter/Pro/Enterprise)

> Demo kullanıcılar production'da (`APP_ENV=production`) **oluşturulmaz**.

### Frontend Ortam Değişkeni

```env
# apps/frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ⚠️ Güvenlik Notları

- **Lokal/Demo:** Mevcut `X-Username` header auth bu ortam için yeterlidir
- **Production öncesi:** JWT auth migrasyonu zorunludur — bkz. [`docs/PLAN-jwt-auth-migration.md`](docs/PLAN-jwt-auth-migration.md)
- **`ADMIN_SECRET_KEY`** set edilmezse admin API korumasız çalışır (development uyarısı verir)
- **`POSTGRES_PASSWORD`** `.env`'de tutulmalı, asla commit edilmemeli

---

## Kısıtlamalar

App-Q **yönlendirici hipotezler** üretir, istatistiksel olarak temsili pazar araştırması değildir. Yüksek riskli kararlar gerçek kullanıcı görüşmeleri, satış verisi veya saha araştırmasıyla doğrulanmalıdır.

---

*App-Q v3.0 — FastAPI + Next.js + PostgreSQL/pgvector + Ollama*
