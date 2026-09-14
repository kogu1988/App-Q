# Clarere — Agent Memory

> Bu dosya, projedeki her dosyanın ne işe yaradığını, kritik kararları ve mimariyi özetler.  
> **Amaç:** Her seferinde tüm kodu okumak yerine buradan hızlıca bağlam yakalamak.

---

## 🧠 Proje Özeti

Türkiye odaklı sentetik persona pazar araştırma platformu. DeepSeek API (Flash + Pro) ile çalışır.
Marka: **Clarere** | İletişim: **hiclarere@clarere.com**

> **Son güncelleme (2026-08-10):** Articos Parity tamamlandı. 8 sprint'te Evidence Chain, Hypothesis-Blind, Adaptive Probe, Research Copilot, A/B Testing, Web Corroboration, Decision Layer ve RFI Benchmark eklendi. Backend 14 dosya, Frontend 1 dosya (2153 satır).

> **Stabilizasyon (2026-08):** Duplicate `follow-up` endpoint + `FollowUpRequest` temizlendi (frontend 422/404 bug'ı). `test_semantic_router.py` bayat Ollama import'ları düzeltildi (süit koleksiyonunu engelliyordu → 126 test yeşil). `run_benchmark.py` Windows cp1254 emoji çökmesi giderildi. `.env.example` DeepSeek/Clarere'ye göre yeniden yazıldı, `run_backend.py` port 4000, eski marka kalıntıları temizlendi.

> **Kurumsal Seviye (2026-08):** Rapor export'u tamamlandı. `render_markdown` + `render_report_html` artık Karar Katmanı (SHIP/ITERATE/ARAŞTIR/VAZGEÇ), Van Westendorp PSM, Harici Kanıt, SES×Stance tablosu, Marka Sağlığı, Keşif Kanalı ve RFI içeriyor. Güven skorları `%78` formatında. HTML raporu tamamen Türkçe (İngilizce başlıklar kaldırıldı). Frontend markdown parser'a tablo desteği eklendi. `scripts/generate_demo_study.py` sunum demo çalışması üretir (DB'ye kaydeder). Test: 158 passed + 1 skipped.

> **Deploy blocker (2026-09):** Oracle Cloud Always Free'de **Ampere A1 (ARM) kapasitesi dolu** ("Out of host capacity"). Instance açılamıyor. **Yerel geliştirmeye devam ediliyor**; canlıya geçiş bu blok çözülene kadar bekler. Çözüm adımları + Cloud Shell retry script'i **`server_plan.md §0a` "Kapasite hatası"** bölümünde. İkincil plan (netcup + Neon + Vercel) yedekte.

> **Kalite & Maliyet turu (2026-09):** (1) Alıntı kesilmesi kök nedeni düzeltildi — `quote[:110]` gibi ham dilimler yerine `analytics._shorten()` / `reporting._clip()` **tam cümle özeti** çıkarır ve **`...`/`…` eklemez**. (2) `providers.py`'ye **içerik-hash LLM önbelleği** eklendi (`LLM_CACHE_ENABLED`, `LLM_CACHE_MAX`, `LLM_CACHE_TTL`, `get_llm_cache_stats()`); adversarial döngülerde tekrar kodlamayı ucuza indirir. `DEEPSEEK_MAX_TOKENS` (varsayılan 8192) + timeout 120sn + çağrı başına `max_tokens` eklendi. (3) **Celery async hat tamir edildi**: `gateway` checkpointer `thread_id` eksikliği + `nodes/simulation.py` `Persona` eksik alanları (`persona_traits` ile `big_five`). Async panel boyutu **plan bazlıdır** (`plan_config.max_personas`, varsayılan 10; `ASYNC_PERSONA_COUNT` env yalnız fallback). (4) **Rapor zenginleştirme**: `analytics.enrich_report_narrative()` DeepSeek Pro ile kanıta bağlı yönetici anlatımı + stratejik öneriler üretir; `ResearchReport.executive_narrative` / `strategic_recommendations`; `REPORT_ENRICH_ENABLED` ile kapatılabilir; `render_markdown` yeni bölümleri basar. (5) Markdown başlık boşlukları/etiket biçimi düzeltildi. Testler: **344 passed**.

> **DeepSeek API güncellemesi (2026-09, `docs/deepseek_api.txt`):** Önerilen model adı **`deepseek-flash`**; eski `deepseek-v4-flash` emekliye ayrıldı (V4.1-Flash ile karşılanır, Flash fiyatı). `.env` Flash adı güncellendi. **`reasoning_effort` (low/high/max, varsayılan high)** artık destekleniyor — `get_model_provider(..., effort=...)` ve `DEEPSEEK_REASONING_EFFORT` env'i; sentez zenginleştirmesi `effort="max"` kullanır (maliyet kaldıracı: düşük effort = az reasoning token). Context caching **otomatik ve prefix tabanlı**; `prompt_cache_hit_tokens`/`miss_tokens` takip ediliyor — sabit sistem promptu başta tutulmalı. Thinking modda temperature/presence/frequency etkisiz, top_p ≥0.95. JSON çıktıda makul `max_tokens` şart (kesilmeyi önler). `deepseek-v4-pro` adı doğrulandı — resmi Models & Pricing sayfası V4 Pro servisinin 14 Eylül 2026 sonrası da süreceğini belirtiyor. **Off-peak (01:00–04:00 ve 06:00–10:00 UTC dışı) fiyatlar yarı yarıyadır** — ağır sentez/toplu işler off-peak'e çekilirse maliyet %50 düşer. Context 1M, max output 384K. Cache-hit fiyatı cache-miss'e göre ~50x ucuz (prefix cache kritik).

> **Kapanış turu (2026-09):** (1) Async hat async-özel 3 bug daha kapatıldı (dict→slice KeyError, gateway `import json`, REJECT'te placeholder rapor) ve çalışma sahibine bağlandı (`bind_tenant_context` — RLS görünürlüğü). (2) **Degradasyon sinyali**: `ResearchReport.degradation_notes`; harici kanıt SearXNG'den alınamazsa rapora "Metodolojik Uyarılar" düşer (markdown + HTML + PDF). (3) Async raporu **"Tematik Ön Analiz (Research Studio)"** olarak etiketlendi; tam sentez raporuyla iki katman açıkça ayrıldı. (4) **requirements.txt tamamen pinlendi** (celery 5.6.3, redis 8.1.0, langgraph 1.2.11, langchain-core 1.6.3, openai 3.13.0, sentry-sdk 2.69.1, xhtml2pdf 0.2.19). (5) **E2E CI** eklendi (`.github/workflows/e2e.yml`, secret yoksa atlar). (6) **UNIT_ECONOMICS.md** — off-peak/cache ile COGS ve plan marjları. Testler: **354 passed**. DeepSeek tek sağlayıcı olarak kalır (çoklu sağlayıcı şimdilik yok).

## 🏗️ Mimari (3 Aşamalı API)

```
POST /api/client/intake       → Defne sohbeti (flash) — 3-5 tur, özet+onay
POST /api/client/research     → Plan + Persona + Batch Mülakat (flash)
POST /api/client/synthesize   → Rapor (algoritmik + kanıt zinciri + karar katmanı)
POST /api/client/contact      → İletişim formu (DB'ye kaydeder)
GET  /api/client/studies/{id}/findings        → Kanıt zinciri (Sprint 1)
GET  /api/client/studies/{id}/findings/{fid}  → Tek bulgu detayı (Sprint 1)
POST /api/client/studies/{id}/chat           → Research Copilot (pro, Sprint 4)
POST /api/client/studies/{id}/follow-up      → Personaya ek soru (probing)
POST /api/client/studies/{id}/pdf            → PDF rapor (plan gated)
POST /api/client/studies                    → Çalışma kaydet (findings'i de DB'ye yazar)
POST /api/client/personas/generate           → Plan'dan persona üret
POST /api/client/interviews/stream           → SSE streaming mülakat
POST /api/client/studio/simulate             → Celery async simülasyon
POST /api/auth/register|login               → JWT auth (parola + token)
```

## 🔐 Auth Katmanı

- `apps/backend/main.py` middleware: `Authorization: Bearer <JWT>` → username; geliştirmede `X-Username` fallback
- `jwt_utils.py` token üret/doğrula, `auth_utils.py` parola hash (bcrypt)
- Frontend `src/lib/auth.ts`: token varsa Bearer + her zaman X-Username gönderir (dev)
- RLS: `current_tenant_var` → PostgreSQL `clarere.current_tenant` session değişkeni (B2B izolasyonu)
- Admin: `X-Admin-Key` header (ADMIN_SECRET_KEY)

## ⚡ Hızlı Başlatma

```bash
python launch.py        # Docker stack (onerilen): frontend :4001, tam stack :8080
python launch.py --dev  # Host dev: backend :4000 (--reload) + frontend :4001
```

`start.bat` → `python launch.py` (Docker modu).

## 🐳 Docker

İki akış var — **KARIŞTIRMAYIN**:

| Akış | Komut | Kullanım |
|---|---|---|
| **Yerel Docker (onerilen)** | `docker compose -f docker-compose.prod.yml -f docker-compose.local.yml up -d --build` | Prod benzeri; Caddy :8080, frontend :4001 |
| Host dev altyapı | `docker compose up -d postgres redis` | Sadece DB+Redis; API/Celery host'ta (`--dev`) |

> `launch.py` (varsayılan) prod+local Docker stack'ini ayağa kaldırır. `--dev` ile eski host akışı (uvicorn --reload).

## 🧪 Test Durumu

> **SSOT = CI.** Kesin güncel sayı `.github/workflows/ci.yml` job özetinden okunur (her push'ta yazılır). Aşağıdaki komut yereldir; DB testleri için port-forward gerekir.

```bash
python -m pytest packages/research_engine/tests/ -q
```

| Test Dosyası | Kapsam |
|---|---|
| test_blockers_p0.py | Paddle imza/plan eşlemesi, token fiyat, JWT/admin guard, usage birikimi (P0) |
| test_production_readiness.py | KVKK silme onayı, e-posta fail-safe, Paddle iptali, job runner |
| test_integrations.py | Resend sözleşmesi/fail-safe, HTML kaçışı, Sentry env kapısı |
| test_hypothesis_blind.py | Varsayılan blind, bağlam bloğu, 3 mülakat fonksiyonu uyumu (GRUP 3) |
| test_evidence_chain.py | Duygu sınıflandırma, kanıt grafiği, çelişki skoru (GRUP 1) |
| test_decision_layer.py | SHIP/ITERATE/INVESTIGATE/KILL eşikleri (GRUP 2) |
| test_persona_traits.py | Openness/Agreeableness kalibrasyonu, big_five (GRUP 13) |
| test_batch_resilience.py | Batch retry, response_format regresyonu (GRUP 14) |
| test_synthesize_tolerance.py | Tolerant synthesize, 422 (GRUP 15) |
| test_plan_enforcement.py | Plan gate'leri + gelir sızıntısı regresyonu (GRUP 5) |
| test_quota_atomicity.py | Atomik kota / TOCTOU (GRUP 4, DB-gated) |
| test_architecture.py | Domain izolasyonu, bağımlılık kuralları (GRUP 11) |
| test_migrations.py | init_db idempotensi (GRUP 12, DB-gated) |
| test_probe_engine.py | Adaptive probe heuristikleri (GRUP 6) |
| test_ab_variants.py | A/B kör randomizasyon (GRUP 7) |
| test_adversarial.py | 4 aşamalı denetim flag'leri (GRUP 8) |
| test_web_corroboration.py | SearXNG yoksa graceful degradation (GRUP 9) |
| test_benchmark.py | RFI ağırlık formülü ve grade eşikleri (GRUP 10) |
| test_stance_diversity.py | Rogers×SES matris, Largest Remainder, Skeptic garantisi |
| test_ewma_echo.py | EWMA, Jaccard echo, echo drift |
| test_van_westendorp.py | PSM kesişimleri (OPP/IPP/PMC/PME) |
| test_workflow.py | ELEPHANT prompt, agreeableness kalibrasyonu |
| test_quality.py | bias, acquiescence, meta-tone |
| test_semantic_router.py | keyword routing |
| test_intake.py | Defne akışı |
| test_grounded.py | Grounded Simulation |
| test_auth_utils.py, test_jwt_utils.py | auth |
| test_db_org.py | organizasyon RLS |
| test_plan_config.py | feature gate |
| test_reporting.py | rapor render |
| test_finetuning_export.py | ShareGPT JSONL export |

## 📁 Kritik Dosya Haritası

### Backend API (`apps/backend/`)

| Dosya | Görev | Ne Zaman Bak |
|---|---|---|
| `main.py` | FastAPI app, CORS, rate limit, tenant middleware | Port/CORS değişikliği |
| `routers/client/` | Client API endpoint'leri (paket): studies, research, synthesis, interaction, intake, account, ws + `_deps`/`_schemas` | API endpoint ekleme/değiştirme |
| `routers/admin.py` | Admin panel endpoint'leri | Admin özellikleri |

### Research Engine (`packages/research_engine/`)

| Dosya | Görev | Ne Zaman Bak |
|---|---|---|
| `providers.py` | `DeepSeekResearchModel` + `get_model_provider()` | LLM değişikliği |
| `workflow/` | Araştırma orkestrasyonu (paket): `planning`, `personas`, `interviews`, `interviews_stream`, `interviews_batch` | Araştırma akışı |
| `models.py` | Tüm dataclass'lar (ResearchBrief, Persona, vb.) | Veri modeli değişikliği |
| `intake.py` | `process_intake_chat()` — Defne chatbot (Articos-tarzı hızlı akış, 3-5 tur) | Defne davranışı |
| `analytics/` | Rapor sentezi (paket): `synthesis`, `ab_report`, `findings`, `evidence`, `pricing`, `corroboration`, `metrics`, `enrichment` | Rapor değişikliği |
| `matrix.py` | Rogers×SES kohort matrisi, stance diversity | Persona dağılımı |
| `quality.py` | Kalite fonksiyonları (EWMA, echo, bias, acquiescence) | Kalite kontrolü |
| `adversarial.py` | 4-aşamalı adversarial review | Rapor denetimi |
| `database/` | DB paketi: `connection` (havuz/oturum), `studies`, `clients`, `usage`, `events`, `billing`, `findings`, `migrations/` (`init_db` + şema + seed) | Veritabanı değişikliği |
| `plan_config.py` | Plan feature gate SSOT (Free/Flex/Starter/Pro/Enterprise) | Plan/özellik değişikliği |
| `db_vectors.py` | pgvector tabanlı persona havuzu, curated questions | Vektör DB |
| `gateway.py` | Celery async simulation gateway | Async işler |
| `celery_app.py` | Celery konfigürasyonu | Async queue |
| `privacy.py` | PII scrubbing | Güvenlik |
| `reframing.py` | Input reframing (sycophancy mitigation) | Brief işleme |
| `search.py` | SearXNG web search | Canlı arama |
| `reporting/` | Markdown/HTML rapor render (paket: `markdown`, `html`, `_html_utils`) | Rapor çıktısı |
| `pdf_generator.py` | PDF üretimi (xhtml2pdf) | PDF export |
| `persona_generator.py` | Admin için LLM ile persona üretimi | Admin panel |
| `synthesis_pipeline.py` | LangGraph tabanlı tematik sentez pipeline | Async sentez |
| `pricing_table.py` | DeepSeek token fiyatlandırma SSOT (USD/1M) — `calculate_cost()` | Maliyet hesabı (P0-6) |
| `paddle_config.py` | Paddle price → plan eşlemesi SSOT | Paddle fiyat ID'leri (P0-2) |
| `paddle_webhooks.py` | Paddle imza doğrulama + event işleme + abonelik iptali | Webhook mantığı (P0-2) |
| `research_runner.py` | `execute_research()` — senkron + Celery ortak araştırma çekirdeği | Araştırma akışı (P0-1 Aşama 2) |
| `jobs.py` | Celery görevi `run_research_job` — async araştırma | Job kuyruğu |
| `email_service.py` | Resend işlemsel e-posta (env-gated, opsiyonel) | E-posta bildirimleri |

| `benchmark.py` | Clarere RFI — 6 metrikli validasyon benchmark'ı (Sprint 8) | Kalite ölçümü |

### LangGraph Nodes (`packages/research_engine/nodes/`)

| Dosya | Görev |
|---|---|
| `sycophancy.py` | ELEPHANT anti-dalkavukluk + hypothesis_blind parametresi |
| `culture.py` | Hofstede TR, SES profilleri, taksit/BDDK lojistiği |
| `memory.py` | ACT-R bilişsel bellek modeli |
| `router.py` | Keyword-based routing |
| `probe.py` | Adaptive Probe Engine — kanıt arayan takip soruları (Sprint 3) |

### Frontend (`apps/frontend/`)

| Dosya | Görev |
|---|---|
| `src/app/page.tsx` | Landing shell (49 satır) — bölümler `features/landing`, fiyat `features/pricing` |
| `src/features/landing/` | Hero, manifesto, özellik bandı, iletişim, SSS, CTA, footer, nav + `use-reveal` |
| `src/features/pricing/plans.ts` | Landing plan/fiyat SSOT (PLAN_PRICES, PLAN_META, FEATURES) |
| `src/features/wizard/` | Sihirbaz tipleri, `research-client` (job + senkron fallback), `BriefPreview`, `ModeSelection`, `SimulatingScreen` |
| `src/app/client/new/page.tsx` | Araştırma sihirbazı (ince sayfa; adımlar `features/wizard`'da) |
| `src/app/client/studies/[id]/page.tsx` | Araştırma detay/rapor sayfası + "Raporu Oluştur" |
| `src/app/client/page.tsx` | Client dashboard |
| `src/app/client/upgrade/page.tsx` | Plan yükseltme sayfası — Paddle checkout + ödeme yoklama |
| `src/lib/paddle.ts` | Paddle.js v2 başlatma + checkout overlay |
| `src/proxy.ts` | Next.js 16 proxy: www→apex, `/client/*` derin bağlantı koruması, noindex, probe engelleme |
| `src/lib/auth.ts` | Auth header'ları + oturum işareti cookie'si (`setSessionMarker`) |
| `src/app/layout.tsx` | Root layout, metadata, JSON-LD, favicon, Paddle.js script |
| `src/hooks/use-client-plan.ts` | Plan bilgisi hook (DEFAULT_PLAN: Free) |
| `src/components/plan-gate.tsx` | Paywall bileşeni (blur + Lock + "Planı Yükselt →") |
| `src/app/guide/page.tsx` | Kullanım kılavuzu |
| `src/app/privacy/page.tsx` | KVKK/Gizlilik politikası |
| `src/app/terms/page.tsx` | Kullanım koşulları |
| `src/app/{agencies,b2b-saas,consultants,growth-marketers,user-interviews,ab-testing}/` | SEO landing sayfaları |
| `next.config.ts` | Proxy `/api/*` → `localhost:4000`, security headers |

### Konfigürasyon

| Dosya | Görev |
|---|---|
| `.env` | DeepSeek API key + DB/Redis ayarları (gitignored) |
| `.env.production.example` | Sunucu production env şablonu (secretsiz) |
| `docker-compose.yml` | Yerel (host) dev: PostgreSQL (5433) + Redis (4006) + SearXNG + API + Celery |
| `docker-compose.prod.yml` | Tek-sunucu / self-hosted stack (frontend + PostgreSQL + Caddy dahil) |
| `docker-compose.local.yml` | `prod.yml` üzerine **yerel override** (Caddy → :8080, `Caddyfile.local`) |
| `docker-compose.cloud.yml` | **Bulut (onaylanan)**: Neon (PG yok) + Redis + API + Celery + Caddy |
| `Caddyfile` | Self-hosted: clarere.com + www + /api/* tek sunucuda |
| `Caddyfile.local` | Yerel: `localhost:8080` |
| `Caddyfile.cloud` | **Bulut**: yalnızca `api.clarere.com` (+ Paddle webhook) |
| `.github/workflows/ci.yml` | CI: pytest + `tsc --noEmit` + lint |
| `scripts/backup_db.sh` | Günlük `pg_dump` yedeği (14 gün saklama) |
| `launch.py` | Tek tıkla başlatma — Docker stack (varsayılan) / host dev (`--dev`) |
| `start.bat` | `python launch.py` wrapper |
| `SUNUM.md` | 14 slidelık yatırımcı sunumu |
| `server_plan.md` | Canlıya geçiş planı (Vercel + netcup VPS + Neon + Paddle) — sıralı fazlar |
| `MEMORY.md` | Bu dosya |
| `scripts/run_benchmark.py` | RFI benchmark runner (Sprint 8) |
| `scripts/setup_paddle_catalog.py` | Paddle ürün/fiyat/destination idempotent kurulum (P0-2) |
| `scripts/generate_demo_study.py` | Sunum demo çalışması üretici (DB'ye kaydeder) |
| `docs/TEST_PLAN.md` | ⚠️ gitignored — Güçlü yönleri koruma test planı (15 grup, ~110 test) |
| `docs/CRITICAL_BLOCKERS_PLAN.md` | ⚠️ gitignored — P0 blocker'lar + Paddle entegrasyon spesifikasyonu |
| `data/evals/rfi_benchmark_samples.json` | 5 Türkiye pazarı benchmark senaryosu (Sprint 8) |

---

## 🔑 Kritik Kararlar

1. **Ollama/Mock tamamen kaldırıldı** — Sadece DeepSeek API (Flash + Pro) var
2. **Semantic cache kaldırıldı** — Embedding API'si yok
3. **Batch interview** — Persona başına tek API çağrısı (5 persona = 5 istek). Conversation Paradox ile uyumlu
4. **Thinking Mode** — DeepSeek varsayılanı, `temperature` KULLANILMAZ. `reasoning_content` ayrı alanda gelir
5. **`user_id`** — DeepSeek isolation için `[a-zA-Z0-9_-]+` regex ile sanitize
6. **3 aşamalı flow** — Her aşama ayrı endpoint, model kafası karışmasın diye
7. **Defne hızlı akış (Articos tarzı)** — Sokratik tek soru yerine 2 sorulu hızlı toplama + özet + onay. Max 5 tur. Prompt hem `intake.py` hardcoded fallback'te hem `database.py` DB default'unda güncellendi. ⚠️ DB'de `ON CONFLICT DO NOTHING` olduğu için mevcut DB'yi sıfırlamadan (`docker compose down -v && docker compose up -d`) yeni prompt aktif olmaz.
8. **Enterprise feature'lar** — Yerel LLM fine-tuning, embedding, persona havuzu eşleştirme (ileride)
9. **Tüm eski marka referansları Clarere olarak değiştirildi** — localStorage, PDF adı, API title, prompt'lar
10. **5 demo kullanıcı** — free, flex, starter, pro, enterprise (development modunda)
11. **Free plan upsell** — Paywall (blur + Lock), "Planı Yükselt →" CTA
12. **Evidence Chain (Sprint 1)** — Her bulgu persona → soru → alıntı → destek/karşı zinciriyle DB'ye kaydedilir. `research_findings` + `research_evidence` tabloları. `build_evidence_graph()` ile otomatik sentiment sınıflandırması.
13. **Hypothesis-Blind Interviews (Sprint 2)** — Persona araştırma hipotezini GÖRMEZ. `brief.hypothesis_blind=True` varsayılan. Sadece kategorik bağlam + sorular.
14. **Adaptive Probe Engine (Sprint 3)** — Cevaba göre kanıt arayan takip soruları. `nodes/probe.py`. Max 1 probe/soru, 3 probe/mülakat. Jaccard guard.
15. **Research Copilot (Sprint 4)** — `POST /studies/{id}/chat` endpoint. DeepSeek Pro ile araştırma raporuyla sohbet. Plan limitli (Free: 0, Starter: 3).
16. **A/B Variant Testing (Sprint 5)** — Kör karşılaştırma (Seçenek 1/2), randomized exposure, segment-level kazanan analizi.
17. **Web Corroboration (Sprint 6)** — Sentetik bulguları web kanıtıyla destekleme. SearXNG + mock fallback. TÜAD/Statista referansları.
18. **Decision Layer (Sprint 7)** — Her bulgu SHIP/ITERATE/INVESTIGATE/KILL sinyali taşır. Executive decision summary raporda.
19. **Validation Benchmark (Sprint 8)** — Clarere RFI. `benchmark.py`. 6 metrik (recall, precision, critical recall, FPR, segment accuracy, contradiction). 5 örnek senaryo.

---

## 🛡️ P0 Blocker Durumu (Sprint 9 — tamamlandı)

| # | Blocker | Çözüm | Dosya |
|---|---|---|---|
| P0-1 | `async def` içinde blocking LLM → tüm API donuyordu | Tüm senkron endpoint'ler `def`'e çevrildi (threadpool); `lifespan`'da `THREADPOOL_SIZE` (64) | `client.py`, `main.py` |
| P0-3 | JWT secret hardcoded fallback | Production'da `JWT_SECRET` zorunlu + min 32 karakter; dev'de `_DEV_FALLBACK` + uyarı | `jwt_utils.py` |
| P0-4 | `ADMIN_SECRET_KEY` yoksa admin API açıktı | Production'da 503; `hmac.compare_digest`; başarısız deneme audit log | `admin.py` |
| P0-5 | LLM timeout/retry yoktu | `tenacity` retry (timeout/conn/ratelimit/5xx) + `DEEPSEEK_TIMEOUT=90`; stream'de retry yalnızca ilk chunk öncesi; `RESEARCH_DEADLINE_SECONDS` bütçesi | `providers.py`, `workflow.py` |
| P0-6 | Token muhasebesi kurguydu | `usage` yakalama + `token_usage` tablosu + dönemsel bütçe (`TOKEN_BUDGET_EXCEEDED` 429) + admin `/usage` | `providers.py`, `database.py`, `pricing_table.py`, `client.py`, `admin.py` |
| P0-2 | Ödeme entegrasyonu yoktu | Paddle Billing: checkout/portal/subscription + webhook (HMAC, idempotent, sıralı) + Paddle.js | `billing.py`, `paddle_config.py`, `paddle_webhooks.py`, `paddle.ts`, `upgrade/page.tsx` |

**Ek düzeltmeler:** `PrivacyResearchModelWrapper.free_memory()` eksikti (streaming finalizer'ı `AttributeError` veriyordu). `/upgrade-plan` production'da kapatıldı.

**Test:** `test_blockers_p0.py` — 20 test (imza doğrulama, plan eşlemesi, fiyat hesabı, JWT/admin guard, usage birikimi, süre bütçesi). Güncel toplam için bkz. "Test Durumu" (290 passed + 10 skipped).

**⚠️ Paddle için kullanıcı aksiyonu:** `PADDLE_API_KEY` `.env`'e konur, ardından `python scripts/setup_paddle_catalog.py` katalogu + webhook destination'ı otomatik oluşturur ve env satırlarını basar. **Fiyatlar USD'ye çevrildi** (Paddle TRY'yi desteklemiyor; kur varsayımı ~40 TL/USD): Flex $49 one-time · Starter $69/ay, $55/ay (yıllık) · Pro $169/ay, $135/ay (yıllık).

---

## 👤 Test Kullanıcıları

| Kullanıcı | Plan | Limit |
|---|---|---|
| `free` | Free | 2 sim/ay, 10 persona |
| `flex` | Flex | 3 sim/paket |
| `starter` | Starter | 10 sim/ay |
| `pro` | Pro | Sınırsız |
| `enterprise` | Enterprise | Sınırsız |

---

## 🔬 Bilimsel Altyapı Durumu

| Bileşen | Batch'te Durum |
|---|---|
| Big Five / NEO-PI-R | ✅ Stance profilleri |
| Rogers × SES matrisi | ✅ Largest Remainder |
| ELEPHANT anti-sycophancy | ✅ Prompt'ta aktif |
| Hofstede TR | ✅ Prompt'a gömülü |
| Stance diversity | ✅ Skeptic zorunlu |
| Echo detection | ✅ Intra-persona Jaccard |
| Acquiescence detection | ✅ Skeptic/Laggard için |
| Van Westendorp PSM | ✅ Algoritmik |
| ACT-R bellek | ⚠️ Batch'te gerekmiyor (tek prompt) |
| EWMA kalite takibi | ✅ Batch uyarlaması (skor + retry) |

---

## 🏢 Enterprise SaaS Özellik Durumu

| Özellik | Min Plan | Durum |
|---|---|---|
| A/B Test | Flex | ✅ `client.py` + `analytics.py` |
| B2B modu | Pro | ✅ `intake.py` + `analytics.py` |
| Brand health | Pro | ✅ `build_brand_health_summary` |
| SES cross-tab | Flex | ✅ `build_ses_cross_tab` |
| Custom personas | Enterprise | ✅ `db_vectors.py` + admin |
| Audit log | Enterprise | ✅ admin `/audit_logs` |
| Streaming / PDF export | Flex | ✅ |
| White-label | Pro | ✅ client nav + PDF filename (backend + frontend); `render_report_html` sentezde kullanılıyor |
| Fine-tuning export | Enterprise | ✅ `db_vectors.export_finetuning_data` + admin `/fine-tuning/export` |
| Multi-user org | Enterprise | ✅ org/member CRUD (`db_org.py`) + studies RLS (tenant + org paylaşımı); **canlı DB testi tamam** (`test_rls_org_sharing.py`) |

> ⚠️ Üç enterprise özelliği kod seviyesinde tamamlandı. `multi_user` RLS'i (`studies_tenant_policy`, `clarere.current_org`) gerçek DB'de test edilmeli: `docker compose up -d` + `python launch.py`.

---

## 🏭 Enterprise: Yerel Türkçe LLM Yol Haritası

> DeepSeek API'den yerel modellere geçiş için referans. Şu an aktif değil.

### Model Kaynakları

| Model | Parametre | Uzmanlık | Lisans |
|---|---|---|---|
| **Kumru-7B** | 7B | Sıfırdan Türkçe, %38-98 daha az token | Açık Kaynak |
| **Trendyol-LLM-8B** | 8B | E-ticaret, kişilik yorumlama | Apache-2.0 |
| **Kizagan-E4B** | 4B etkin | Türkçe akıl yürütme (CoT) | Gemma |
| **Trendyol-Asure-12B** | 12B | Çok modlu, yüksek talimat uyumu | Apache-2.0 |

### Eğitim Pipeline

```
1. Veri toplama    → curated_questions (DB) + turkish_quality_eval.jsonl
2. Veri hazırlama   → scripts/prepare_finetuning_data.py
3. Fine-tuning      → scripts/train_unsloth.py (QLoRA, RTX 4060 8GB)
4. GGUF dönüşümü   → llama.cpp / Ollama
5. Modele alias     → Ollama Modelfile
6. Adapter ekle     → providers.py'ye OllamaResearchModel geri dön
```

### Geçiş Adımları

1. `curated_questions` tablosunu beğenilen sorularla doldur
2. `scripts/prepare_finetuning_data.py` ile ShareGPT formatına çevir
3. `scripts/train_unsloth.py` ile LoRA adapter üret
4. GGUF'a dönüştür, Ollama'ya yükle
5. `providers.py`'ye eski `OllamaResearchModel` adapter'ını geri ekle
6. `APP_MODEL_PROVIDER=ollama` ile test et

### Referans

- `docs/` — Bilimsel dökümanlar **yerelde mevcut** (god_doc.md, grounded_simulation.md, Türk Tüketici Refleksleri vb.) ancak `.gitignore`'da — **kasıtlı olarak repoya gönderilmiyor**. Klonlayan biri bu dosyaları görmez; bu yüzden README onlara referans vermez.
- `README.md` — Bilimsel altyapı özeti (Stance Diversity, EWMA, PSM)
- `data/evals/turkish_quality_eval.jsonl` — Kalite değerlendirme veri seti
- `models/` — Sadece README.md kaldı (eski yerel model klasörü)

---

## 🐛 Bilinen Sorunlar / Notlar

1. ✅ **P0 blocker'lar kapatıldı** — bkz. "P0 Blocker Durumu (Sprint 9)".
2. ✅ **Production Docker hazırlığı** — `docker-compose.cloud.yml`, `Caddyfile.cloud`, `.env.production.example`, `next.config.ts` env-driven proxy, `_ensure_app_role` Neon-uyumlu (non-fatal). ⚠️ `docker-compose.prod.yml` + `docker-compose.local.yml` (yerel/self-hosted) **korundu**.
3. ✅ **CI** — `.github/workflows/ci.yml` (pytest + tsc + lint).
4. ✅ **Sentry** — `SENTRY_DSN` varsa aktif, `send_default_pii=False` (KVKK).
5. ✅ **Resend** — `email_service.py`; iletişim formu bildirimi bağlandı. `RESEND_API_KEY` yoksa no-op.
6. ✅ **KVKK** — `GET /api/client/me/export` + `DELETE /api/client/me` (abonelik iptali + veri silme, `confirm: "DELETE"`).
7. ✅ **Index'ler** — `research_findings(study_id)`, `research_evidence(finding_id)` (migration 005).
8. ✅ **Yedekleme** — `scripts/backup_db.sh` (cron'a eklenmeli).
9. ⚠️ **Paddle env doldurulmalı** — sandbox katalog kuruldu; live için `PADDLE_ENV=production` + live price ID'ler. Webhook secret `PADDLE_WEBHOOK_URL` verilince oluşturulacak.
10. ✅ **`/research` job pattern (P0-1 Aşama 2)** — `POST /research/jobs` → 202 `job_id`; `GET /research/jobs/{id}` durum. Celery görevi `jobs.py`, ortak çekirdek `research_runner.py`. Frontend: job dener, 503'te senkron `/research`'e düşer.
11. ✅ **Ölü kod DEĞİL (denetim hatası düzeltildi)** — `graph.py`, `state.py`, `nodes/intake.py`, `synthesis_pipeline.py` **canlı**: `gateway.py` → `/studio/simulate` bunları kullanıyor. **SİLİNMEMELİ.**
12. ✅ **Frontend proxy (middleware)** — `src/proxy.ts` (Next.js 16 konvansiyonu; `middleware.ts` DEĞİL). Prod host kanonikleştirme, derin bağlantı koruması, noindex, probe engelleme. `/client` kökü bilinçli olarak açık (onboarding orada).
13. ✅ **Admin 'Maliyet' sekmesi** — `GET /api/admin/usage` verisini gösterir (kullanıcı bazlı token tüketimi + tahmini USD maliyet).
14. ℹ️ **`models/` klasörü** sadece README.
15. ℹ️ **Canlıya geçiş** — `server_plan.md` fazları uygulanacak (VPS + Neon + Vercel).
16. ✅ **Repo yeniden adlandırıldı** — `kogu1988/App-Q` → **`kogu1988/clarere`**. `git remote` + README/server_plan/SUNUM/ruff referansları güncellendi.
17. ✅ **O-2 kararı** — `ai_semantic_cache` şeması **bilinçli korunuyor** (Enterprise vektör havuzu rezervi); kod içine açıklayıcı NOT eklendi.
18. ✅ **Güvenlik yamaları (0 bilinen açık)** — Öncesi: npm 16 (1 kritik), pip-audit 75. Sonrası: **0 + 0**. `next`/`eslint-config-next` 16.3.5; `fastapi` 0.141.1, `starlette` 1.3.1, `pillow` 12.3.0, `GitPython` 3.1.59. ⚠️ `starlette` 1.3.1'e sabitlendi: tüm açıkları kapatır ve yine <1.4.0 kalır (paylaşılan global env'deki `streamlit` kısıtını bozmamak için). 304 test yeşil.
19. ✅ **Yerel Docker :4001** — `docker-compose.local.yml`'de frontend doğrudan `http://localhost:4001`'de. `API_PROXY_TARGET` **BUILD ARG**: `next.config` rewrites derleme anında gömülür, runtime env etkisizdir.
20. 🔴→✅ **KRİTİK: tenacity kwargs hatası (düzeltildi)** — `providers.py::_chat` içinde `_retry_policy()(fn)(**kwargs)` yazımı `fn`'i **argümansız** çağırıyordu → OpenAI SDK "Missing required arguments" → **gerçek DeepSeek çağrılarının TAMAMI başarısız** (Defne fallback yanıtı, brief %0, mülakat/sentez boş). Doğrusu: `_retry_policy()(fn, **kwargs)`. Testler `FakeModel` kullandığı için yakalanmamıştı. Regresyon: `test_providers.py` (4 test).
21. ✅ **E2E harness (Playwright)** — `e2e/` klasörü (ayrı package.json, frontend build'ini etkilemez). `tests/01-ui` (landing/giriş/upgrade/admin), `tests/02-research-flow` (tam akış, gerçek LLM), `tests/03-study-actions` (mevcut çalışma: sekmeler+transkript+sentez). Ekran görüntüleri `e2e/artifacts/screens/`. Çalıştır: `cd e2e && npx playwright test` (Docker stack açık olmalı).
22. ✅ **Rapor kalitesi bulguları (DÜZELTİLDİ — E2E ile doğrulandı)** — plan: `docs/REPORT_QUALITY_FIXES.md`.
    - ✅ **Rapor zayıftı:** `render_markdown` `enhanced_findings` dict'lerinde `.title` çağırıp çöküyordu (`'dict' object has no attribute 'title'`) → fallback (~2 KB). Tolerant `_g()` eklendi. **Sonuç: 2 KB → 33,7 KB**, tam başlıklı rapor (Bulgular/Karar Katmanı/Van Westendorp/SES×Stance/Marka Sağlığı).
    - ✅ **Karar katmanı tutarsızlığı:** (a) `risk` bulgusu `objection` etiketli turlarla eşleşmiyordu → `_CATEGORY_TAG_ALIASES`; (b) pain_point'te acı dili 'karşı kanıt' sayılıp KILL veriyordu → kategori-farkında polarite (`_NEGATIVE_CLAIM_CATEGORIES`). **Sonuç: kanıt 0 → 5/bulgu; pain point KILL(0/3) → INVESTIGATE(1/1).**
    - ✅ **Kişiler arası yankı:** `quality.detect_cross_persona_echo` + `workflow._regen_persona_turns` ile yankılanan persona 'kaçın' listesiyle yeniden üretilir. **Sonuç: 5/5 persona aynı adı ("Pamuk") yerine farklı adlar (Şila, Zeytin, Paşa, Pamuk, Poyraz).**
    - ✅ **Meta ton yanlış pozitifi:** `judge_answer_quality` ürünün "yapay zeka özelliği"nden bahsedince meta_tone veriyordu → yalnızca kendine-referans kalıplarına daraltıldı.
    - ✅ **Kalite skoru kalibrasyonu:** eski formül sabit cezalarla 68 tabanını ezip skoru 0 yapıyordu (grade C ile tutarsız). Oran-tabanlı + sınırlı cezalara geçildi; kanıt artık `enhanced_findings`'ten sayılır. **Sonuç: 0/C → 90/A.**
    - ✅ **`report_html` boştu:** sentezde `render_report_html` üretilip frontend kaydediyor. **Sonuç: 0 → 37 KB.**
    - ✅ **Gürültülü uyarılar:** `weak_turkey_context` yalnızca ticari/ödeme sorularında; `weak_skepticism` yalnızca değerlendirme sorularında tetiklenir. **Sonuç: 12 → 2 uyarı** (kalan 2 meşru: şüpheci persona fayda sorusunda itiraz etmedi).
    - ⚠️ **Ders:** Async araştırma **Celery worker**'da çalışır — backend kod düzeltince `celery_worker` de yeniden derlenmeli, sadece `clarere-api` değil.
23. ✅ **Demo kullanıcı plan senkronizasyonu** — seed `ON CONFLICT DO NOTHING` yüzünden `free` DB'de Flex kalmıştı; dev'de `DO UPDATE` ile fixture planları senkronize edilir (prod'da demo seed yok). Test: `test_12_4_demo_users_are_synced_to_fixtures`.
24. 🔴→✅ **Gelir sızıntısı: senkron `/research` kotayı atlıyordu** — `execute_research` sayacı yalnızca SONDA (gating olmadan) artırıyordu; async `/research/jobs` kontrol ederken senkron yol etmiyordu → async 503'te frontend fallback'i ile sınırsız araştırma. `run_full_research`'e önceden `check_simulation_limit` + `QUOTA_EXCEEDED` (403) eklendi. Test: `test_5_10_sync_research_enforces_quota`. Canlı doğrulama: Starter 10/10 → 403.
25. ℹ️ **Free plan iki kapılı (1 ay VEYA 2 araştırma):** `is_trial_expired` Free için `created_at`'ten itibaren **30 gün VEYA 2 araştırma** sınırı koyar — hangisi önce biterse Free plan sona erer ve kullanıcı plan seçmeye yönlendirilir. (`plan_config.Free.max_simulations=2` ayrı kapı.) Önceki 3 gün → 1 ay olarak güncellendi (backend + frontend + README). Demo `free` kullanıcısı eski olduğu için araştırma yapamaz (403 deneme süresi).
26. ✅ **Plan gating canlı doğrulandı** (X-Username ile): Free={adversarial,rfi} · Starter=+{ab_test,streaming,pdf_export,ses_crosstab} · Pro=+{b2b_mode,brand_health,white_label}. Uygulama testleri: b2b Free/Starter 403, Pro 200 · ab_test Free 403 · PDF Free 403 · Copilot Free 403 · sentez çıktısı: brand_health Free/Starter YOK, Pro VAR; ses_cross_tab Free 0, Starter/Pro 1.
27. 🔴→✅ **`/studio/simulate` her çağrıda başarısız oluyordu** — `LocalPIIScrubber` `localhost:11434` (Ollama/Kara-Kumru) çağırıyordu; Ollama kaldırıldığı için bağlantı reddi → `PrivacyFilterException` → `{status:failed, PII_FILTER_FAILURE}`. Düzeltme: `privacy.py` env-yapılandırılabilir (`PII_MODEL_URL`, `PII_MODEL_NAME`, `PII_TIMEOUT`, `PII_NER_ENABLED`, `PII_STRICT`) + regex'e zarif fallback (model yoksa çökmez; `PII_STRICT=true` ise fırlatır). Canlı: `status:queued` ✅. Test: `test_privacy_pii.py` (4).
28. ✅ **PII plan gate'i** — `local_pii_scrubbing` özelliği eklendi (yalnızca **Enterprise**). Regex katmanı (telefon/e-posta/TC) HER planda çalışır; yerel NER modeli (isim/lokasyon) Enterprise'da. `gateway.trigger_simulation_triage` plana göre `enable_ner` geçer. Canlı: Pro=False, Enterprise=True.
29. ✅ **`PrivacyMasker` no-op açığı KAPATILDI** — `mask()/unmask()` artık gerçekten çalışıyor: telefon/e-posta/TC placeholder'lanır (`[PHONE_1]`…), `PrivacyResearchModelWrapper` prompt'u LLM'e gitmeden maskeler, yanıtı kullanıcıya dönmeden açar (stream'de yarım placeholder tamponlanır). Rakip marka maskeleme opsiyonel (`PII_MASK_COMPETITORS`, varsayılan KAPALI — kamuya açık marka adları KVKK dışı ve kaliteyi düşürür). Test: `test_privacy_pii.py` (8).

> **Test durumu:** 304 passed, 0 skipped (DB testleri dahil — `POSTGRES_HOST/PORT` env ile tam süit).

### Test planı sonrası bulunan gerçek sorunlar

- **`workflow.py`'de `os` importu eksikti** — P0-5 süre bütçesi `os.getenv` çağırıyordu ama import yoktu; `run_interviews_batch` **NameError ile çöküyordu**. GRUP 3 testleri yakaladı (commit `eeffd0f`).
- **Gelir sızıntısı** — `brand_health` (Pro+) ve `ses_crosstab` (Flex+) hiçbir endpoint'te gate'lenmiyordu. `_synthesize_impl` artık plan yetersizse bu alanları rapor çıktısından çıkarır (commit `f8cef2c`).
- ✅ **Probe heuristiği kısa-token zaafı (O-1)** — `"tl"` alt-dizi olarak eşlendiği için "kayıtları" gibi kelimeler yanlış pozitif üretiyordu. Kısa/çok anlamlı tokenlar (`tl`, `try`) artık **kelime sınırı** ile eşleşir (`_has_pricing_signal`); uzun kelimeler substring kalmaya devam eder. Regresyon: `test_6_9`, `test_6_10`.
- ✅ **Org tabloları oluşturulmuyordu (gerçek bug)** — `db_org.init_org_schema()` hiçbir kod yolundan çağrılmıyordu ve app rolü DDL yetkisine sahip değildi → Enterprise `multi_user` sessizce bozuktu. Düzeltme: DDL `db_org._create_org_tables(cur)`'a taşındı; `init_db()` admin bağlantısıyla (app role grant'ından önce) oluşturuyor. Regresyon testi: `test_rls_org_sharing.py`.
- ✅ **Zaman-bağımlı test kırılganlığı** — `test_quota_atomicity._prepare_user` sabit geçmiş tarih (`2026-01-01`) kullanıyordu; 30 günü aştığı için `check_and_reset_period` sayacı sıfırlıyor ve testler yanlış başarısız oluyordu. Varsayılan period_start artık **bugün**.
- ✅ **RLS bağlamı olmadan insert** — `test_migrations.test_12_2` tenant bağlamı olmadan studies insert ediyordu → politika ihlali. `current_tenant_var` + `created_by` eklendi.

### Çalışma detay sekmeleri doğrulaması (2026-09-13)

- **Tüm sekmeler dolu/çalışıyor** (E2E ile DOM denetimi, `pro` + `study_1789318823185`): Özet & Hedefler, Personalar, Senaryo, Mülakat Kayıtları, Kanıt Zinciri, Sentez Raporu — hiçbirinde placeholder (`Belirtilmemiş`, `bulunamadı` vb.) yok. Transkript dialogu açılıyor, tam Q&A gösteriyor.
- ✅ **RFI rozeti tutarsızlığı** — `research_quality` payload'unda `rfi`/`components` yokken arayüz yanıltıcı şekilde **"Eşik Altı"** gösteriyordu. Artık `rfi` yoksa nötr **"Ölçülmedi"** (gri) gösterilir.
- ✅ **Özet & Hedefler brief kartı zenginleşti** — yalnızca Marka/Fiyat/Problemi yerine artık Kategori, Hedef Kitle, Rakipler, Başarı Kriteri, Satış Kanalı, Panel & Coğrafya da gösteriliyor.
- ✅ **Personalar kartı zenginleşti** — persona `attributes` alanından Mevcut İş Akışı, Karar Tetikleyicisi, Satın Alma Sürtünmesi ekleniyor (şablon bio tek başına yetersiz kalıyordu).
- ✅ **Küçük düzeltmeler** — bozuk `bg-[#f1f5ff]0` Tailwind sınıfı, RFI uyarı metnindeki `...` kesmesi kaldırıldı.
- Doğrulama: `npx tsc --noEmit` + `npx eslint` temiz; frontend imajı yeniden derlendi.

### Persona biyografisi doğallaştırma (2026-09-13)

- ✅ **`enrich_persona_bios()`** (`workflow.py`) — Persona `bio` alanı artık LLM ile doğal, TR pazarına bağlı biçimde yeniden yazılır. **Tek** ek API çağrısı (tüm panel için JSON `{"bios": {"<id>": "..."}}`).
- **Anti-halüsinasyon:** Prompt yalnızca mevcut `attributes` (Current workflow, Decision trigger, Buying friction, Hobbies), SES, Rogers duruşu, şehir ve fiyat/dijital skorlarını kullanmaya zorlar; yeni sayı/marka/kurum uydurma yasak. `60–700` karakter dışı veya `...`/`…` içeren çıktı reddedilir.
- **Fail-safe:** LLM hatası/geçersiz JSON → mevcut şablon bio korunur; akış çökmez. `generate_personas()` model'sız çağrıldığında (testler) davranış değişmez.
- **Frozen dataclass:** `Persona` `frozen=True` olduğundan atama değil `dataclasses.replace()` kullanılır (aksi halde `FrozenInstanceError` sessizce yutuluyordu).
- **Bağlantı:** `research_runner.execute_research` adım 2'den sonra çağrılır.
- Test: `tests/test_persona_bio.py` (5). Canlı doğrulama: 5/5 persona doğal bio üretti. Tam süit **364 passed**.

> **Maliyet notu:** Bu adım araştırma başına 1 ek LLM çağrısı ekler (küçük prompt/çıktı). Prefix-cache ve içerik-hash cache'ten pay almaz.

#### Bilimsel bağlılık güvencesi (2026-09-13)

- **`bio` mülakat davranışını ETKİLEMEZ** — `build_elephant_system_prompt` bio'yu kullanmaz; kalibrasyon Big Five/Agreeableness/Neuroticism/Openness üzerinden yürür. Bio yalnızca raporda ve persona havuzunda görünür.
- **Bilimsel alanlar dokunulmaz** — `enrich_persona_bios` yalnızca `bio` metnini `dataclasses.replace()` ile değiştirir; `big_five`, `traits`, `neo_facets`, `stance`, `ses_group`, `diffusion_stage`, `price_sensitivity`, `digital_confidence`, `attributes` aynen korunur. Regresyon: `test_enrich_persona_bios_preserves_scientific_fields`.
- **Psikometriye bağlı anlatım** — Prompt persona kataloğuna Big Five skorları ve Rogers aşama açıklaması eklenir; "bu atamalar bilimseldir, DEĞİŞTİRİLEMEZ" kuralı ve davranış dili zorunluluğu vardır (skorlar sayı olarak yazılmaz). Regresyon: `test_enrich_persona_bios_prompt_is_psychometrically_grounded`.
- Tam süit: **366 passed**.

### Sprint 1 — Güven, bilimsel iddia ve içerik temizliği (2026-09-13)

> Kaynak plan: `analyze_plan.md` · Analiz: `claude_analyse.md`

- ✅ **Uydurma dış kanıt kaynakları KALDIRILDI (kritik).** `analytics._MOCK_EXTERNAL_SOURCES` (TÜAD/Statista/Deloitte/TÜBİSAD/McKinsey adına uydurulmuş başlık, URL ve istatistikler) silindi. Artık web araması sonuç vermezse **uydurma kaynak üretilmez**; boş liste + "Metodolojik Uyarılar" notu döner. `ExternalEvidence`'a `source_domain` + `is_verified` eklendi. Testler: `test_web_corroboration.py` (8), `test_degradation_and_tenant.py` güncellendi.
- ✅ **Crawl4AI mock sızıntısı engellendi.** `search.py` artık `APP_ENV=production` iken mock içerik döndürmez (boş + log); test/geliştirmede açıkça `[TEST FIXTURE …]` etiketli.
- ✅ **Bilimsel iddialar temkinlileştirildi.** Frontend'ten kanıtsız sayısal/kesin iddialar kaldırıldı: `RFI 0.815`, `%93 tema doğruluğu`, `%86 eşleşme`, `7.5 kat`, `46 araştırma alanı`, `23 kör UX araştırmacısı`, `%90 risk`, `%85 korelasyon … bilimsel olarak kanıtlanmıştır`, `Baymard/NNg doğrulaması`. Yerine mekanizma odaklı, savunulabilir dil kullanıldı (`layout.tsx` JSON-LD/FAQ, `page.tsx`, `guide`, `b2b-saas`, `user-interviews`).
- ✅ **"%100 Yerel Veri Lokalizasyonu (KVKK Uyumlu)" iddiası kaldırıldı** (`client/upgrade`). Aktif mimari DeepSeek API kullanıyor; metin artık "kurumsal veri işleme seçenekleri" diyor.
- ✅ **Van Westendorp sentetik uyarısı** hem `models.VanWestendorpInsight.methodology_note` varsayılanına hem markdown/HTML raporuna eklendi (istatistiksel temsil iddiası taşımaz).
- ✅ **RFI yorum dili** temkinlileştirildi (`benchmark._rfi_interpretation`): "Üretime hazır" → "Yüksek uyum".
- ✅ **Yazım hataları:** yapıy zeka, büdçe, büyme, değlendirme, Clarere'nun, rekrutüman, "platformumuz and ilgili", `**…**` markdown artığı, "sistem and metodoloji".
- ✅ **Panel boyutu drift'i** (`user-interviews`: "50'ye kadar persona" → "10 kişilik standart panel").
- ✅ **Frontend README** create-next-app boilerplate'inden Clarere'ye özgü dokümana çevrildi (port 4001, env, proxy build-arg, Docker, E2E).
- ⚠️ **Secret taraması:** repoda gerçek secret yok (yalnızca `sk-...` placeholder'ları). Sohbette paylaşılan Paddle sandbox anahtarı için **rotasyon kullanıcı aksiyonu** gerektirir (dış etmen).
- Doğrulama: `npx tsc --noEmit` + `npx eslint` temiz; backend tam süit **368 passed**.

### Sprint 2 — Doküman & fiyat SSOT tutarlılığı (2026-09-13)

- ✅ **Gerçek bug: Flash fiyat kaydı yoktu.** `pricing_table.MODEL_PRICING` yalnızca emekli `deepseek-v4-flash` anahtarını taşıyordu; aktif `deepseek-flash` çağrıları `DEFAULT_PRICING` (0.0)'a düşüyordu → **admin maliyet paneli Flash için $0 gösteriyordu.** Aktif ad eklendi, emekli ad aynı dict'e bağlandı. Regresyon: `test_active_flash_model_has_pricing_entry`.
- ✅ **Panel boyutu tutarlılığı (S2-7).** Motor 5 persona üretirken planlar "10 persona" vaat ediyordu. `generate_personas(..., panel_size=)` ve `build_research_plan(..., panel_size=)` eklendi; `research_runner` panel boyutunu `plan_config.max_personas`'tan alır (standart akış üst sınırı 10). İsim/şehir/bağlam havuzları 10'a genişletildi; stance diversity 5 duruşu garanti eder. Varsayılan `panel_size=5` geriye uyumlu. Regresyon: `test_13_9`, `test_13_10`, `test_13_11`.
- ✅ **Model adı drift'i:** `models/README.md`, `README.md`, `server_plan.md`, `.env.example`, `.env.production.example`, `database.py` system_config → `deepseek-flash`.
- ✅ **Timeout/limit drift'i:** README ve prod env örneği `DEEPSEEK_TIMEOUT=120`, `DEEPSEEK_MAX_TOKENS=8192`, `DEEPSEEK_REASONING_EFFORT=high`; eksik env'ler dokümante edildi.
- ✅ **Test sayısı SSOT:** README'deki sabit 187 sayılı tablo kaldırıldı; CI artık test özetini job summary'e yazıyor (`ci.yml`). MEMORY "Test Durumu" CI'ya yönlendiriyor.
- ✅ **Fiyat/ödeme drift'i:** `SUNUM.md` TL → USD (Flex $49, Starter $69/$55, Pro $169/$135), Stripe → Paddle, marj tablosu gerçek COGS ile; "90x" → "~10–25x". `REKABET.md` 0.25 TL → ~$0.01–0.04 ve "7.5× az gürültü"/"dalkavukluk yapmayan tek sistem" gibi kanıtsız üstünlük iddiaları temkinlilileştirildi.
- ✅ **Altyapı statü matrisi:** `server_plan.md` başına aktif/yedek/durum tablosu (Oracle birincil, netcup+Neon+Vercel yedek); README production bölümü aynı çift-plana bağlandı.
- ✅ **`UNIT_ECONOMICS.md` TCO bölümü:** Paddle komisyonu, sabit giderler, persona-bio çağrısı, destek yükü, chargeback, free edinim maliyeti ve Pro fair-use riski eklendi.
- Doğrulama: backend tam süit **372 passed**.

### Sprint 3 — Rapor kalitesi, veri etiketleme ve ölçüm (2026-09-13)

- ✅ **Şablon sızıntısı düzeltildi (gerçek bug).** `synthesize_report` önerileri/aksiyonları tüm araştırmalarda sabitti ve sağlık örneğinden gelen **“klinik entegrasyonu”** gibi alakasız ifade içeriyordu. Artık öneriler **bulgulardan türetilir** (`derived_recommendations`, en yüksek güvenli 3 bulgu) ve `action_items`/`validation_next_steps` jeneriktir.
- ✅ **Rapor metrikleri (S3-1/S3-3):** `analytics.build_report_metrics()` → kanıtlı bulgu, kaynaksız bulgu, bulgu başına kanıt, kanıtta benzersiz persona, karşı kanıt oranı, yanıt tamamlanma oranı, harici kaynak sayısı, karar sinyali dağılımı. `ResearchReport.report_metrics` alanı eklendi.
- ✅ **Veri kökeni etiketleme (S3-2):** Rapor (markdown + HTML) ve study detay UI'ında **Sentetik / Algoritmik / Harici** etiketleri ve “istatistiksel temsil iddiası taşımaz” notu.
- ✅ **Free plan mesaj netliği (S3-4):** Paywall metni “2 araştırma hakkı veya 1 ay · Tam rapor için plan gerekir” olarak netleştirildi.
- ✅ **KPI event altyapısı (S3-5/S3-6):** `product_events` tablosu + `record_product_event()` + `get_product_event_summary()` (funnel oranları, [0,1] clamp'li). Backend event'leri: `research_started`, `research_completed`, `report_synthesized`. İstemci event'leri: `POST /api/client/events` (beyaz liste) + `src/lib/events.ts`; study detay/rapor sekmesi ve upgrade sayfası event gönderir.
- ✅ **Admin kabul özeti (S3-8):** `GET /api/admin/product-events/summary?days=30` → event sayıları + funnel oranları.
- ✅ **Metodolojik tutarlılık notu (S3-7):** README Bilimsel Altyapı bölümüne kapsam/sınırlılık notu; raporda veri kökeni bölümü.
- Test: `test_report_metrics.py` (4), `test_product_events.py` (2, DB-gated). Doğrulama: backend tam süit **378 passed** (DB'li) / CI'da 363 passed + 15 skipped; `tsc` + `eslint` temiz.

### Sprint 6 — Güvenlik, KVKK ve prod hazırlığı (yerel kısımlar) (2026-09-13)

- ✅ **Bare `except:` temizliği.** `client.py` (WS mesaj/close, JSON parse) ve `db_vectors.py` (big_five vector parse) dar istisna tipleriyle (`json.JSONDecodeError`, `TypeError`, `ValueError`) değiştirildi; beklenmeyen hatalar artık `logger.debug` ile görünür.
- ✅ **CORS production guard test edilebilir hale getirildi.** `main.resolve_allowed_origins(app_env, raw_origins)` ayrıştırıldı; production'da `ALLOWED_ORIGINS` yoksa `RuntimeError` (uygulama açılmaz). Regresyon: 4 test (production zorunlu, parse, dev wildcard, boş entry).
- ✅ **Mevcut guard'lar doğrulandı:** JWT secret (production zorunlu/min 32), admin `X-Admin-Key` (production'da 503, timing-safe), `X-Username` fallback yalnızca development.
- ✅ **Secret hijyeni:** tracked dosyalarda gerçek anahtar yok (yalnızca `sk-...` placeholder'ları). ⚠️ Sohbette paylaşılan Paddle sandbox anahtarı için rotasyon kullanıcı aksiyonudur.
- ✅ **Bağımlılık denetimi:** `pip-audit -r requirements.txt` → 0 açık; `npm audit --omit=dev` → 0 açık.
- ✅ **KVKK veri akışı:** `privacy/page.tsx` alt işleyen listesi mimariden bağımsız hale getirildi ve **"6A. Veri Akışı Özeti"** eklendi (brief→LLM + PII maskeleme, ödeme→Paddle, çıktılar→kendi DB, hata→Sentry PII kapalı, e-posta→Resend).
- ⚠️ **Hukuki inceleme bekliyor (kullanıcı aksiyonu):** `terms/page.tsx` fikri mülkiyet/gizlilik ifadeleri ve `privacy/page.tsx` KVKK metni canlı öncesi **avukat incelemesinden** geçmeli. Kod tarafı hazır; metin hukuk onayı gerektirir.
- Doğrulama: `test_blockers_p0.py` 25 passed; CI-safe tam süit **367 passed + 15 skipped**; `tsc` + `eslint` temiz.

### Sprint 7 — Test derinliği ve CI determinizmi (2026-09-13)

- ✅ **Tek komut test koşucusu (S7-1):** `scripts/run_tests.py` — Postgres erişimini kontrol eder, yoksa Docker `socat` ile port-forward kurar, tam süiti çalıştırır, sonra temizler. `--no-db` (CI-benzeri) ve `-- <pytest args>` destekler. Windows `cp1254` Unicode çökmesi `stdout.reconfigure(utf-8)` ile engellendi. Canlı: **392 passed**.
- ✅ **PDF yapısal testi (S7-2):** `test_pdf_golden.py` — geçerli `%PDF-` imzası, `%%EOF`, makul boyut ve üretim stabilitesi.
- ✅ **LLM önbellek testleri (S7-6):** `test_llm_cache.py` — anahtar determinizmi, her girdi boyutunda değişim, roundtrip, boş değer reddi, istatistik şekli, LRU tahliyesi.
- ✅ **Persona determinizmi (S7-7):** `test_13_12` — aynı girdi ile panel kimlik/isim/duruş/Big Five birebir aynı (model drift kontrolü).
- ✅ **E2E/test dokümantasyonu (S7-8):** `TESTING.md` — tek komut, DB-gated testler, CI yapısı, E2E secret kurulumu ve **stack gerektiren testler** (mobil görsel regresyon, yük, Celery retry/idempotency, Paddle canlı, backup/restore) açıkça belgelendi. README testler bölümü bu dosyaya yönlendirildi.
- Not: Stack gerektiren 5 test türü S7 kapsamında **belgelendi**, otomatikleştirilmesi altyapı (S10) sonrasına bırakıldı.
- Doğrulama: `python scripts/run_tests.py` → **392 passed**.

### Sprint 9 — Rekabet, GTM ve pilot program paketi (2026-09-13)

- ✅ **`REKABET.md` derin matris (S9-1):** Kategori (sentetik / gerçek kullanıcı / survey / ajans / DIY) + 11 karşılaştırma boyutu + **doğrulama görev listesi**. Uydurma rakip fiyatı/özelliği YOK; doğrulanmamış hücreler `?` ve teyit yöntemiyle işaretli. "Rakiplerde yok" iddiası yerine "Clarere'de ürünleşmiş ve test edilmiş" dili kullanıldı.
- ✅ **`GTM_PLAYBOOK.md` (S9-2/3/4/5/6):** Pilot program kiti (5–10 partner, 4 hafta, başarı kriterleri), fiyat doğrulama planı (Van Westendorp uyarlaması + karar kuralı), Free→paid funnel hipotezleri (H1–H4, `product_events` ile ölçülür), KPI dashboard tanımı (Edinim/Aktivasyon/Değer/Gelir/Kalite) ve yatırımcı deck tutarlılık kontrol listesi.
- Not: Fiyat/rakip doğrulaması **gerçek partner verisi** gerektirir; plan hazır, uygulama canlı sonrası (S10).
- Doğrulama: doküman değişikliği; CI yeşil.

### Sprint 8 — Bağımsız benchmark & RFI kalibrasyonu (KISMİ, 2026-09-13)

> ⚠️ **Harness hazır; gerçek veri ve bağımsız insan değerlendirici bekliyor.** Bu sprint tek başına kapatılamaz — dış veri + insan gerektirir.

- ✅ **`benchmark.py` genişletmeleri:** `validate_case()` (vaka sözleşmesi), `case_is_annotated()`, `cohens_kappa()` (iki bağımsız değerlendirici uyumu) ve `summarize_rfi()` (ortalama/min/maks + metrik ortalamaları). Regresyon: `test_benchmark_agreement.py` (12).
- ✅ **`scripts/benchmark_collect.py`:** Bir `study_id`'nin Clarere bulgularını DB'den (yoksa `report_json`'dan) alıp **anotasyona hazır vaka iskeleti** üretir. `human_findings`/`critical`/`contradictions`/`synthetic_validation` alanlarını **insan doldurur**; script uydurma veri üretmez. Canlı doğrulandı (4 bulgu).
- ✅ **`scripts/benchmark_report.py`:** Anotasyonlu vakalar için RFI + iki değerlendirici varsa `cohens_kappa` hesaplar, `--write-summary` ile `summary.json` yazar. Şablon dosyalarını (`_` öneki) atlar.
- ✅ **`data/evals/benchmark/`:** `README.md` (kör tema eşleme protokolü, vaka şeması, etiket tanımları, kalibrasyon planı, yayımlama kuralı) + `cases/_template.json`.
- **Bekleyen (dış):** 20 gerçek brief, uzman `human_findings`, 2 bağımsız değerlendirici, eşik kalibrasyonu (`_THEME_MATCH_THRESHOLD` vb. varsayılan), `summary.json` yayımı.
- **Kural:** Bu adımlar tamamlanana kadar hiçbir yerde “bağımsız bilimsel doğrulama” iddiası kullanılmaz.
- Doğrulama: CI-safe tam süit **388 passed + 15 skipped**.

### Refaktör R1 — Study detay veri katmanı ayrımı (2026-09-13)

> Kaynak plan: `refactor_plan.md` · Sprint sırası: R1 → R2 → R5 → R6 → R7 → R8 → R3 → R4. Kurallar: davranış dondurma, shim stratejisi, golden markdown + OpenAPI diff, modül başına < ~500 satır.

- ✅ **Yeni feature katmanı:** `src/features/studies/` altında `types.ts` (tüm detay tipleri), `api/studies-api.ts` (fetch/response katmanı), `hooks/use-study-detail.ts` (veri + state + funnel event), `lib/normalize-study.ts` (Big Five toleranslı okuma), `lib/constants.ts` (`DECISION_CONFIG`, `STANCE_TR`), `components/` (FindingCard, ChannelBarChart, BigFiveRadar, PSMChart).
- ✅ **`studies/[id]/page.tsx` 2364 → 1758 satır.** `fetch(` çağrısı kalmadı; veri/olay/sunum yardımcıları feature katmanına taşındı. Kabul kriteri (< 1800 satır) sağlandı.
- ✅ **Next.js anti-pattern düzeltmesi:** effect içinde `cancelled` guard eklendi (unmount sonrası `setState` engellendi). Davranış ve görsel çıktı birebir korundu.
- Doğrulama: `npx tsc --noEmit` + `npx eslint` temiz (0 error, 0 warning); `page.tsx`'te fetch yok.
- **Sıradaki:** R2 — 6 sekmeyi bağımsız bileşenlere ayır (`page.tsx` < 350 satır).

### Refaktör R2 — Study detay sekme bileşenleri (2026-09-13)

- ✅ **`studies/[id]/page.tsx` 1758 → 327 satır** (kabul: < 350). Her sekme dosyası < 600 satır.
- ✅ **Yeni bileşenler:** `SummaryTab` (314), `PersonasTab` (293), `ReportTab` (359), `InterviewsTab` + `InterviewTranscriptDialog`, `ScriptTab`, `EvidenceTab`; yardımcılar `StudyTabNav`, `StudyHeaderActions`.
- ✅ **Yeni lib:** `lib/render-markdown.tsx` (harici bağımlılıksız markdown ayrıştırıcı), `lib/synthesis.ts` (`synthesizeAndSaveReport`; sentez + kaydet + reload tek yerde).
- ✅ **Davranış dondurma:** görsel çıktı ve metinler birebir korundu; state/handler'lar `page.tsx`'te kaldı, bileşenlere prop olarak geçti.
- Not: `lib/format.ts` (R2-7) oluşturulmadı — paylaşılan bir biçimlendirme yardımcısı kalmadı (tek tarih formatı `page.tsx` başlığında inline).
- Doğrulama: `tsc` + `eslint` temiz; Docker frontend rebuild; Playwright **5/5 passed** (`01-ui`, `03-study-actions`).
- **Sıradaki:** R5 — `database.py` (2034) → paket (shim stratejisi).

### Refaktör R5 — `database.py` → paket (2026-09-13)

- ✅ **2034 satırlık tek modül pakete bölündü.** `database.py` silindi; `database/` paketi oluştu. **Hiçbir çağrı yeri değişmedi** (grep ile doğrulandı) — tüm genel isimler `database/__init__.py` shim'inden re-export edilir.
- **Modüller:** `connection.py` (191), `studies.py` (309), `clients.py` (318), `usage.py` (159), `events.py` (87), `billing.py` (269), `findings.py` (170), `migrations/` (`__init__.py` 13, `prompts.py` 42, `schema_core.py` 182, `schema_infra.py` 355, `seed.py` 153). En büyük dosya 355 satır (kabul: < 500); shim 85 satır (kabul: < 250).
- **`init_db()` sırası korundu:** `apply_core_schema` → `apply_infra_schema` → `seed_defaults`; import anında init denemesi (eski davranış) `database/__init__.py` sonuna taşındı.
- 🐛 **Gerçek regresyon yakalandı ve düzeltildi:** `migrations/seed.py` içindeki `_create_org_tables` importu `..db_org` (yanlış kapsam) idi → container logunda `No module named 'packages.research_engine.database.db_org'` uyarısı; `...db_org` olarak düzeltildi, uyarı kayboldu. Test paketi bu yolu try/except içinde yuttuğu için **yeşil test yeterli olmadı** — konteyner logu kontrolü şart oldu.
- ✅ **Test güncellemesi:** `test_quota_atomicity.py::test_4_5` artık `database/clients.py` kaynağını okuyor (atomik UPDATE...RETURNING deseni).
- ✅ **README** proje yapısı pakete göre güncellendi.
- Doğrulama: `python scripts/run_tests.py` → **403 passed**; Playwright `01-ui` + `03-study-actions` → **5/5 passed**; `clarere-api` + `celery_worker` rebuild sonrası konteyner logu temiz.
- ⚠️ **Kapsam dışı kalan bilinen bug (R5 değiştirmedi, R6'da düzeltildi):** `match_personas` içinde `get_personas_pool` yanlış modülden import ediliyordu. Modül seviyesindeki import doğru olduğu için bozuk yerel import satırı R6'da kaldırıldı.
- Not: `ruff check` sonrası BLE001 (blind-except) sayısı 26 → 32 (yeni paket yapısındaki mevcut catch-all desenleri); diğer kurallar taban çizgisiyle aynı.
- **Sıradaki:** R6 — `routers/client.py` (1976) → alt router'lar.

### Refaktör R6 — `routers/client.py` → alt router paketi (2026-09-13)

- ✅ **1976 satırlık router pakete bölündü.** `client/` altında: `_deps.py` (plan çözümü, kota, limitler), `_schemas.py` (istek modelleri), `context.py` (araştırma bağlamı + PII), `studies.py`, `research.py`, `synthesis.py`, `interaction.py`, `intake.py`, `account.py`, `ws.py`, `__init__.py` (üst router + shim). En büyük dosya 374 satır (kabul: < 400).
- ✅ **OpenAPI şeması birebir aynı.** R6 öncesi canlı `/openapi.json` ile karşılaştırıldı: 71 operation, path/metot kümesi, `components`, `tags`, `info` tamamen eşit (diff boş).
- ✅ **`limiter` tek örnek:** `_deps`'te tanımlı; dekoratörlü rotalar aynı nesneyi kullanır (davranış korundu).
- ✅ **Test uyarlamaları:** `test_plan_enforcement.py` kaynak taraması artık `client/` paketinin tamamını okuyor; `monkeypatch` hedefi `client._deps`; `pathlib` yolu `client/research.py`.
- 🐛 **Gerçek bug düzeltildi:** `match_personas` içindeki bozuk `get_personas_pool` importu kaldırıldı (R5 notu). Yeni `test_router_imports.py` (7 test) router import'larının hedef modülde gerçekten var olduğunu ve shim'in genel isimleri dışa verdiğini doğrular.
- Doğrulama: `python scripts/run_tests.py` → **410 passed**; Playwright `01-ui` + `03-study-actions` → **5/5 passed**; canlı `/openapi.json` diff boş; konteyner logu temiz.
- **Sıradaki:** R7 — `analytics.py` (1585) → paket + `reporting` ince ayarı.

### Refaktör R7 — `analytics.py` + `reporting.py` → paketler (2026-09-13)

- ✅ **`analytics.py` (1585) → `analytics/` paketi:** `synthesis.py` (251), `ab_report.py` (358), `findings.py` (248), `evidence.py` (288), `pricing.py` (205), `corroboration.py` (141), `metrics.py` (131), `enrichment.py` (197), `__init__.py` shim. En büyük dosya 358 satır.
- ✅ **`reporting.py` (911) → `reporting/` paketi:** `markdown.py` (441), `html.py` (461), `_html_utils.py` (31), `__init__.py` shim.
- ✅ **A/B dalı ayrıldı:** `synthesize_report` içindeki 305 satırlık A/B gövdesi `synthesize_ab_report()` oldu (varyant yoksa `None` → standart yol devralır). Davranış aynı.
- ✅ **GOLDEN DOĞRULAMA (kabul kriteri):** deterministik fixture (2 persona, offline corroboration) ile `render_markdown(synthesize_report(...))` çıktısı refactor öncesi/sonrası **birebir aynı** (7023 karakter). `report_json` içindeki farklar yalnızca Python set sırası kaynaklı **mevcut nondeterminizm** (aynı kod ardışık iki çalıştırmada da farklı) — refactor kaynaklı değil.
- 🐛 İki kez yanlış ara slice sınırı yakalandı (`slice(996,1076)` bir fonksiyonun `}` satırından başlıyordu → `slice(999,1076)`). Ayrıca paket derinliği nedeniyle `from .models` → `from ..models` düzeltmesi gerekti (modül seviyesi relative import'lar ilk denemede atlanmıştı).
- Doğrulama: `python scripts/run_tests.py` → **410 passed**; Playwright `01-ui` + `03-study-actions` → **5/5 passed**; `ruff` düzeltmeleri sonrası golden hâlâ birebir; konteyner logu temiz.
- **Sıradaki:** R8 — `workflow.py` (1392) → paket + mapper/DTO + bağımlılık.

### Refaktör R8 — `workflow.py` → paket (+ bağımlılık temizliği) (2026-09-13)

- ✅ **`workflow.py` (1392) → `workflow/` paketi:** `planning.py` (280), `personas.py` (411), `interviews.py` (226), `interviews_stream.py` (258), `interviews_batch.py` (416), `_constants.py` (23), `__init__.py` (83). En büyük dosya 416 satır (kabul: < 500).
- ✅ **Shim tam kapsamlı:** `__init__.py` eski dosyanın import bloğunu aynen taşıdığı için `build_elephant_system_prompt`, `STANCE_PROFILE`, `HOFSTEDE_*` gibi **node yardımcıları** da eskisi gibi `workflow` üzerinden erişilebilir (nodes/simulation.py bu yolu kullanıyor). `DEFAULT_QUESTIONS` (admin.py) ve `_format_ab_question` (test) dâhil.
- ✅ **R8-8 bağımlılık temizliği:** `requirements.txt`'ten kullanılmayan görselleştirme/veri yığını kaldırıldı — `pandas`, `numpy`, `altair`, `plotly`, `pyarrow`, `GitPython` (kod tabanında **sıfır** referans; grep ile doğrulandı). İmaj yeniden derlendi, container açılışı + API smoke (study detail 200) + E2E yeşil. Not: `numpy` başka bir paketin transitif bağımlılığı olarak imajda kalıyor.
- ✅ **R8-9 opsiyonel grup:** `requirements-optional.txt` eklendi (`crawl4ai` — `search.py` kurulu değilse mock'a düşüyor).
- ✅ **R8-10 mimari testi:** `test_architecture.py::test_11_6_no_circular_imports_after_package_split` eklendi — paketler arası relative import grafiğini çıkarıp döngü arar. **Yalnızca modül seviyesi import'lar** sayılır; fonksiyon içi tembel import'lar (`...db_org`) yanlış pozitif üretmesin diye dışlanır.
- ⏸️ **Ertelenen iş kalemleri (gerekçeli):** R8-6/R8-7 (yeni `mappers/` DTO katmanı ve tolerant alan okumanın tek yerde toplanması) **davranış dondurma** kuralıyla çelişiyor — çağrı yerlerinin değişmesini gerektirir. Ayrı bir "mimari sadeleştirme" işi olarak planlanmalı; bu sprintte shim tabanlı bölünme ile sınırlı kalındı.
- 🐛 **İki test kaynak-yolu güncellemesi:** `test_probe_engine.py::test_6_8` artık `workflow/` paketinin tamamını tarıyor.
- Doğrulama: `python scripts/run_tests.py` → **411 passed**; Playwright `01-ui` + `03-study-actions` → **5/5**; container logu temiz; API smoke 200.
- **Sıradaki:** R3 — `admin/page.tsx` (1470) → bileşenler.

### Refaktör R3 — Admin panel ayrımı (2026-09-13)

- ✅ **`admin/page.tsx` 1470 → 115 satır** (kabul: < 300).
- ✅ **Veri katmanı ayrıldı:** `features/admin/hooks/use-admin.ts` (189) — durum, `fetchAll`, tembel yükleme (`loadSchemas/loadMetrics/loadUsage`) ve mutasyon handler'ları; `features/admin/types.ts` (132) — tüm arayüzler.
- ✅ **Yeni bileşenler (`components/admin/`):** `admin-header` (48), `admin-tab-nav` (64), `questions-tab` (144), `feedback-tab` (113), `logs-tab` (71), `schemas-tab` (434), `metrics-tab` (328), `usage-tab` (89), `delete-question-modal` (57).
- ✅ **BİREBİRLİK DOĞRULAMASI:** 6 sekme gövdesi, refactor öncesi dosyadaki karşılıklarıyla **birebir aynı** (boşluk-duyarsız karşılaştırma; 2.950–10.437 karakter arası bloklar). Yalnızca prop adı yeniden adlandırmaları yapıldı (`setX` → `onXChange`).
- ✅ **E2E güçlendirildi:** `01-ui.spec.ts`'e "admin sekmeleri geçiş yapar" testi eklendi — 9 sekmenin tamamı tıklanır ve ilgili içerik görünürlüğü doğrulanır.
- Not: `clients/config/personas/feedback` sekmeleri daha önce ayrılmıştı (mevcut düzen korundu).
- ⏸️ **R3-7 ertelendi:** `EventsTab` (ürün event/funnel özeti) **yeni bir sekme/özellik** demektir; davranış dondurma kuralı gereği refaktör kapsamına alınmadı. API (`GET /api/admin/product-events/summary`) hazır, UI eklenmesi ayrı bir özellik işi.
- Doğrulama: `npx tsc --noEmit` + `npx eslint` **0 error / 0 warning**; Docker frontend rebuild; Playwright `01-ui` (5) + `03-study-actions` (1) → **6/6 passed**.
- **Sıradaki:** R4 — `page.tsx` + `client/new/page.tsx` + tasarım tokenları.

### Refaktör R4 — Landing / Wizard ayrımı (2026-09-13)

- ✅ **`src/app/page.tsx` 869 → 45 satır** (kabul: < 350); **`client/new/page.tsx` 620 → 342 satır** (kabul: < 400).
- ✅ **Landing bölümleri ayrıldı (`features/landing/`):** `SiteNav` (79), `HeroSection` (88), `ManifestoSection` (71), `FeatureBand` (57), `ContactSection` (27), `ContactForm` (80), `FaqSection` (69), `CtaBand` (31), `SiteFooter` (30), `hooks/use-reveal.tsx` (44), `data.ts` (34).
- ✅ **Fiyat/plan TEK KAYNAK (`features/pricing/plans.ts` + `PricingSection.tsx`):** `PLAN_PRICES`, `PLAN_META`, `FEATURES` buraya taşındı; kart bazlı aylık/yıllık toggle state'i bileşen içine alındı (gözlemlenebilir davranış aynı).
- ✅ **Sihirbaz adımları ayrıldı (`features/wizard/`):** `types.ts`, `lib/research-client.ts` (job + senkron fallback), `components/{BriefPreview, ModeSelection, SimulatingScreen}`.
- ✅ **BİREBİRLİK DOĞRULAMASI:** 9 landing bölümü + ModeSelection + SimulatingScreen gövdeleri refactor öncesiyle **birebir aynı** (boşluk-duyarsız karşılaştırma; 441–6.777 karakter). Yalnızca `setResearchMode → onModeChange`, `router.push → onUpgrade`, başlatma bloğu → `onStart` yeniden adlandırmaları yapıldı.
- ✅ **E2E güçlendirildi:** `01-ui.spec.ts`'e sihirbaz mod seçimi + Defne sohbeti testi eklendi (LLM çağrısı yapmaz). Playwright **7/7 passed**.
- ⏸️ **Ertelenen iş kalemleri (gerekçeli):**
  - **R4-4 (tasarım tokenları):** inline hex'lerin `tokens.css`'e taşınması tüm frontend'i kapsayan görsel bir iş; `DESIGN.md` karşılaştırması ve ayrı bir görsel regresyon turu gerektirir → ayrı iş olarak planlandı.
  - **R4-5 (kart yoğunluğu azaltma):** planın kendisi "görsel iyileştirme, **ayrı commit**" diyor; davranış dondurma kuralı gereği bu sprintte yapılmadı.
  - **E2E `02-research-flow` çalıştırılmadı:** uçtan uca gerçek DeepSeek çağrıları yapıyor (maliyet + ~20 dk). Yerine sihirbazın aynı giriş adımlarını LLM'siz doğrulayan test eklendi; kod birebirliği ayrıca kanıtlandı.
- Doğrulama: `npx tsc --noEmit` + `npx eslint` **0 error / 0 warning**; Docker frontend rebuild; Playwright **7/7**.
- **Refaktör bloğu tamamlandı:** R1, R2, R5, R6, R7, R8, R3, R4 — planlanan sıranın tamamı uygulandı (ertelenen kalemler gerekçeleriyle yukarıda).

### Refaktör R4-4 — Tasarım tokenları: inline renk → token (2026-09-14)

- ✅ **1.533 Tailwind arbitrary hex → token sınıfı**, 48 dosya. Örnek eşleme: `bg-[#17171c]` → `bg-primary`, `text-[#616161]` → `text-body-muted`, `border-[#d9d9dd]` → `border-hairline`, `text-[#ff7759]` → `text-coral`, `bg-[#eeece7]` → `bg-soft-stone`.
- ✅ **72 çıplak (prop/JS) hex temizlendi:**
  - `Logo`'dan `strokeColor` prop'u **kaldırıldı** (`stroke="currentColor"` + Tailwind `text-*`); 23 çağrı yeri 14 dosyada güncellendi.
  - `AgentLogo`'dan `strokeColor` / `innerStrokeColor` / `dotColor` kaldırıldı → `stroke-deep-green`, `stroke-coral`, `stroke-action-blue`, `fill-deep-green` sınıfları. `think-glow` keyframe'i `color-mix(in srgb, var(--color-coral) N%, transparent)` kullanır.
  - `BigFiveRadar` ve `PSMChart` SVG presentation attribute'ları → `stroke-*` / `fill-*` sınıfları (**SVG attribute'ları `var()` kabul etmez**).
  - Veri görselleştirme paletleri token'a bağlandı: `--color-series-1..7`, `--color-series-neutral`, `--color-price-*`, `--color-psm-*`, `--color-chart-*`.
- ✅ **21 `rgba()` literali** → token + slash-opacity. Çarpanlı ikisi birebir korundu: `[rgba(24,99,220,0.35)]/50` → `action-blue/[0.175]`, `[rgba(24,99,220,0.35)]/40` → `action-blue/[0.14]`.
- ✅ **`globals.css` genişletildi:** 10 yeni semantik yüzey token'ı, `on-primary`/`on-dark`, 8 seri + 3 chart + 4 fiyat + 4 PSM token'ı. Utility katmanındaki hex'ler `var(--color-*)`'a bağlandı. Ölü radius çakışması temizlendi: Cohere ölçeği `--radius-cohere-*` olarak korundu (shadcn alias'ları canlı `rounded-sm/md/lg/xl` değerleri).
- ⏸️ **ERTELENEN (kullanıcı kararı 2026-09-14 — "sonra bakarız"):** Cohere radius ölçeği (`--radius-cohere-md` 16px, `-lg` 22px, `-xl` 30px) **tanımlı ama uygulanmıyor**; canlı `rounded-*` değerleri shadcn alias'larından (taban 8px) geliyor. Hizalamak kart/pill görünümünü tüm frontend'de değiştirir → ayrı görsel inceleme turu gerektirir. Detay: `DESIGN.md` → Known Gaps.
- ✅ **KANIT — renk eşdeğerliği:** 42 token'ın CSS değeri, eşlendiği hex ile **birebir** doğrulandı. Üretim CSS'inde 143 referanslı token'ın 124'ü literal hex, 19'u **mevcut** shadcn tema-duyarlı katman (`var(--x)`; değişiklikten önce de böyleydi). `--color-primary = #17171c` → alias çakışması YOK.
- ✅ **Üretilen sınıf doğrulaması:** `border-action-blue/[0.175]` → `#1863dc2d` (45/255 = 0.176), `border-canvas/10` → `#ffffff1a` (26/255 = 0.102), `bg-action-blue/25` → `#1863dc40` (64/255 = 0.251) — hepsi beklenen alfaya eşit.
- **Davranış dondurma korundu:** hiçbir metin, özellik veya veri akışı değişmedi; yalnızca renk kaynağı token'a taşındı.
- ✅ **Bulunan kusurlar kapatıldı** → bkz. aşağıdaki **R4-4b** kaydı.
- ⚠️ **Kapsam dışı bırakıldı:** shadcn katmanından gelen `bg-secondary` / `bg-muted` / `border-border` gibi tema-duyarlı alias'lar bilinçli olarak `var()` tabanlı bırakıldı (dark-mode davranışı bunlara bağlı).
- Doğrulama: `npx tsc --noEmit` **0 hata**; `npx eslint src` **0 error / 0 warning** (97 dosya); `npx next build` **19 sayfa, başarılı**; Docker frontend rebuild; Playwright `01-ui` + `03-study-actions` + kapsamlı teşhis (konsol/sayfa hatası, token renk çözümlemesi, transkript dialog) → **9/9 passed**, beklenmeyen konsol hatası **0**.

### R4-4b — Bulguların kapatılması (2026-09-14)

R4-4 sırasında bulunan 3 kusur kapatıldı. **İkisi yüzeysel değil, aynı kök nedene bağlıydı.**

**1) KÖK NEDEN — oturum çözülmeden alt bileşenler mount ediliyordu.**
`ClientLayout` `children`'ı auth'tan bağımsız render edip giriş modalını üstte açıyordu. Bu yüzden `SubscriptionCard`, `ClientDashboard` araştırma listesi, `SidebarStudiesWidget` ve `useClientPlan()` **giriş öncesi** mount olup boş `getAuthHeaders()` ile fetch atıyor, 401/boş veri alıyor ve boş dependency array yüzünden **bir daha denemiyordu**. Sonuç: doğrudan `/client`'a gelen bir kullanıcıda abonelik kartı, araştırma geçmişi, kenar çubuğu ve **plan bilgisi boş/yanlış** kalıyordu (giriş sonrası elle yenileme gerekiyordu).

Çözüm (kök neden):
- `lib/auth.ts`'e **oturum deposu** eklendi: `subscribeAuth`, `getAuthUsernameSnapshot`, `getAuthUsernameServerSnapshot`, `setAuthUsername`, `clearAuth`. localStorage bir **dış sistem** olduğu için oturum `useSyncExternalStore` ile okunur (React 19'un doğru deseni; `set-state-in-effect` lint kuralına da uygun).
- `ClientLayout` artık üç durumlu: **bilinmiyor** (hydration; sadece iskelet), **anonim** (yalnızca modal), **oturumlu** (shell + `children`). Oturum bilinmeden **hiçbir veri çeken bileşen mount edilmez**.
- Auth'a bağlı tüm markup + `useClientPlan()` `AuthenticatedShell` bileşenine taşındı → hook'lar yalnızca oturum çözüldükten sonra çalışır.
- `UsernameModal` `onComplete` prop'unu bıraktı; `setAuthUsername(value)` çağırır (dinleyiciler kendiliğinden yenilenir). Çıkışta `clearAuth()`.

**2) `PersonasTab` bozuk JSX girintisi düzeltildi.** Yapı aslında dengeliydi (derleniyordu); sorun `</div>` kapanışının kolon 0'da kalmasıydı → okunabilirlik bozuluyordu. Doğru derinliğe alındı.

**3) Ölü `selectedPersonaIdx` state'i işlevsel hale getirildi.** Persona kartındaki "Mülakat Kayıtlarını İncele" sekmeyi değiştiriyordu ama kullanıcıya **hangi kaydı** göreceğini göstermiyordu.
- `StudyDetailPage` artık indeksi gerçekten okuyup `InterviewsTab`'a `focusIndex` olarak geçiriyor.
- `InterviewsTab`: ilgili kart `scrollIntoView` ile görünür alana gelir ve kalıcı `ring-2 ring-action-blue` vurgusu alır. `prefers-reduced-motion` durumunda kaydırma animasyonsuz yapılır. (Vurgu için React state **kullanılmadı** → `set-state-in-effect` uyarısı yok.)

**Kalıcı regresyon testleri eklendi** (bu hata sınıfı mevcut E2E tarafından görülmüyordu):
- `e2e/tests/04-session.spec.ts` — giriş öncesi kimlik gerektiren veri çağrısı **yapılmadığını** ve giriş sonrası panelin **dolu** geldiğini (araştırma geçmişi + plan etiketi) doğrular.
- `03-study-actions.spec.ts`'e odak testi eklendi — `[data-interview-index="1"].ring-2` tam 1 elemanda bulunmalı.

Doğrulama: `npx tsc --noEmit` **0 hata**; `npx eslint src` **0 error / 0 warning**; Docker frontend rebuild; Playwright `01-ui` + `03-study-actions` + `04-session` → **10/10 passed**. Kanıt: giriş öncesi veri çağrısı **0**, giriş sonrası `BuddyNote` görünür, plan etiketi `Pro`, hatalı istek **0**, konsol hatası **0**.
