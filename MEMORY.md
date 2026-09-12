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

```bash
python -m pytest packages/research_engine/tests/ -q  # 290 passed + 10 skipped
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
| `routers/client.py` | Tüm client endpoint'leri (intake, research, synthesize, contact) | API endpoint ekleme/değiştirme |
| `routers/admin.py` | Admin panel endpoint'leri | Admin özellikleri |

### Research Engine (`packages/research_engine/`)

| Dosya | Görev | Ne Zaman Bak |
|---|---|---|
| `providers.py` | `DeepSeekResearchModel` + `get_model_provider()` | LLM değişikliği |
| `workflow.py` | `build_research_plan()`, `generate_personas()`, `run_interviews_batch()` | Araştırma akışı |
| `models.py` | Tüm dataclass'lar (ResearchBrief, Persona, vb.) | Veri modeli değişikliği |
| `intake.py` | `process_intake_chat()` — Defne chatbot (Articos-tarzı hızlı akış, 3-5 tur) | Defne davranışı |
| `analytics.py` | `synthesize_report()` + Van Westendorp | Rapor değişikliği |
| `matrix.py` | Rogers×SES kohort matrisi, stance diversity | Persona dağılımı |
| `quality.py` | Kalite fonksiyonları (EWMA, echo, bias, acquiescence) | Kalite kontrolü |
| `adversarial.py` | 4-aşamalı adversarial review | Rapor denetimi |
| `database.py` | `init_db()`, bağlantı havuzu, tüm DB CRUD, 5 demo kullanıcı | Veritabanı değişikliği |
| `plan_config.py` | Plan feature gate SSOT (Free/Flex/Starter/Pro/Enterprise) | Plan/özellik değişikliği |
| `db_vectors.py` | pgvector tabanlı persona havuzu, curated questions | Vektör DB |
| `gateway.py` | Celery async simulation gateway | Async işler |
| `celery_app.py` | Celery konfigürasyonu | Async queue |
| `privacy.py` | PII scrubbing | Güvenlik |
| `reframing.py` | Input reframing (sycophancy mitigation) | Brief işleme |
| `search.py` | SearXNG web search | Canlı arama |
| `reporting.py` | Markdown/HTML rapor render | Rapor çıktısı |
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
| `src/app/page.tsx` | Landing page + fiyatlandırma + SSS + iletişim formu |
| `src/app/client/new/page.tsx` | Araştırma sihirbazı (Defne → Research) |
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
25. ℹ️ **Free plan iki kapılı:** `is_trial_expired` Free için **3 gün VEYA 2 araştırma** sınırı koyar (created_at'e bağlı). `plan_config.Free.max_simulations=2` ayrı bir kapıdır; Free'de pratikte deneme kapısı önce devreye girer. Demo `free` kullanıcısı eski olduğu için araştırma yapamaz (403 deneme süresi).
26. ✅ **Plan gating canlı doğrulandı** (X-Username ile): Free={adversarial,rfi} · Starter=+{ab_test,streaming,pdf_export,ses_crosstab} · Pro=+{b2b_mode,brand_health,white_label}. Uygulama testleri: b2b Free/Starter 403, Pro 200 · ab_test Free 403 · PDF Free 403 · Copilot Free 403 · sentez çıktısı: brand_health Free/Starter YOK, Pro VAR; ses_cross_tab Free 0, Starter/Pro 1.

> **Test durumu:** 304 passed, 0 skipped (DB testleri dahil — `POSTGRES_HOST/PORT` env ile tam süit).

### Test planı sonrası bulunan gerçek sorunlar

- **`workflow.py`'de `os` importu eksikti** — P0-5 süre bütçesi `os.getenv` çağırıyordu ama import yoktu; `run_interviews_batch` **NameError ile çöküyordu**. GRUP 3 testleri yakaladı (commit `eeffd0f`).
- **Gelir sızıntısı** — `brand_health` (Pro+) ve `ses_crosstab` (Flex+) hiçbir endpoint'te gate'lenmiyordu. `_synthesize_impl` artık plan yetersizse bu alanları rapor çıktısından çıkarır (commit `f8cef2c`).
- ✅ **Probe heuristiği kısa-token zaafı (O-1)** — `"tl"` alt-dizi olarak eşlendiği için "kayıtları" gibi kelimeler yanlış pozitif üretiyordu. Kısa/çok anlamlı tokenlar (`tl`, `try`) artık **kelime sınırı** ile eşleşir (`_has_pricing_signal`); uzun kelimeler substring kalmaya devam eder. Regresyon: `test_6_9`, `test_6_10`.
- ✅ **Org tabloları oluşturulmuyordu (gerçek bug)** — `db_org.init_org_schema()` hiçbir kod yolundan çağrılmıyordu ve app rolü DDL yetkisine sahip değildi → Enterprise `multi_user` sessizce bozuktu. Düzeltme: DDL `db_org._create_org_tables(cur)`'a taşındı; `init_db()` admin bağlantısıyla (app role grant'ından önce) oluşturuyor. Regresyon testi: `test_rls_org_sharing.py`.
- ✅ **Zaman-bağımlı test kırılganlığı** — `test_quota_atomicity._prepare_user` sabit geçmiş tarih (`2026-01-01`) kullanıyordu; 30 günü aştığı için `check_and_reset_period` sayacı sıfırlıyor ve testler yanlış başarısız oluyordu. Varsayılan period_start artık **bugün**.
- ✅ **RLS bağlamı olmadan insert** — `test_migrations.test_12_2` tenant bağlamı olmadan studies insert ediyordu → politika ihlali. `current_tenant_var` + `created_by` eklendi.
