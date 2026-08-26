# Clarere — Agent Memory

> Bu dosya, projedeki her dosyanın ne işe yaradığını, kritik kararları ve mimariyi özetler.  
> **Amaç:** Her seferinde tüm kodu okumak yerine buradan hızlıca bağlam yakalamak.

---

## 🧠 Proje Özeti

Türkiye odaklı sentetik persona pazar araştırma platformu. DeepSeek API (Flash + Pro) ile çalışır.
Marka: **Clarere** | İletişim: **hiclarere@clarere.com**

> **Son güncelleme (2026-08-10):** Articos Parity tamamlandı. 8 sprint'te Evidence Chain, Hypothesis-Blind, Adaptive Probe, Research Copilot, A/B Testing, Web Corroboration, Decision Layer ve RFI Benchmark eklendi. Backend 14 dosya, Frontend 1 dosya (2153 satır).

> **Stabilizasyon (2026-08):** Duplicate `follow-up` endpoint + `FollowUpRequest` temizlendi (frontend 422/404 bug'ı). `test_semantic_router.py` bayat Ollama import'ları düzeltildi (süit koleksiyonunu engelliyordu → 126 test yeşil). `run_benchmark.py` Windows cp1254 emoji çökmesi giderildi. `.env.example` DeepSeek/Clarere'ye göre yeniden yazıldı, `run_backend.py` port 4000, App-Q kalıntıları temizlendi.

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
python launch.py  # Tek tıkla. Backend :4000, Frontend :4001
# --reload aktif, kod değişince otomatik yeniden başlar
```

## 🐳 Docker Stack (docker-compose.yml)

| Servis | Port | Görev |
|---|---|---|
| postgres (pgvector:pg16) | 5433 | Ana DB — vector ext, RLS, tüm tablolar |
| redis (7.2) | 4006 | Celery broker + WebSocket pub/sub |
| searxng | 4003 | Meta arama (Sprint 6 web corroboration) |
| clarere-api | 4000 | FastAPI (Docker build) |
| celery_worker | — | Async pipeline (`--concurrency=1`) |
| langfuse | 4002 | Observability (profiles: optional) |

> `launch.py` SADECE postgres+redis'i ayağa kaldırır; API/Celery/SearXNG host'ta çalışır.

## 🧪 Test Durumu (2026-08)

```bash
python -m pytest packages/research_engine/tests/ -q  # 156 passed
```

| Test Dosyası | Kapsam |
|---|---|
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
| `src/app/client/upgrade/page.tsx` | Plan yükseltme sayfası |
| `src/app/layout.tsx` | Root layout, metadata, JSON-LD, favicon |
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
| `docker-compose.yml` | PostgreSQL (5433) + Redis (4006) + API + Celery + SearXNG |
| `launch.py` | Tek tıkla başlatma (Docker kontrolü + backend --reload + frontend) |
| `start.bat` | `python launch.py` wrapper |
| `SUNUM.md` | 14 slidelık yatırımcı sunumu |
| `MEMORY.md` | Bu dosya |
| `scripts/run_benchmark.py` | RFI benchmark runner (Sprint 8) |
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
9. **Tüm App-Q referansları Clarere olarak değiştirildi** — localStorage, PDF adı, API title, prompt'lar
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
| White-label | Pro | ✅ client nav + PDF filename (backend + frontend); `render_report_html` ölü kod |
| Fine-tuning export | Enterprise | ✅ `db_vectors.export_finetuning_data` + admin `/fine-tuning/export` |
| Multi-user org | Enterprise | ✅ org/member CRUD (`db_org.py`) + studies RLS (tenant + org paylaşımı); DB testi gerekli |

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

- `docs/` — Bilimsel dökümanlar (god_doc.md, grounded_simulation.md vb.) **artık repoda yok** (silindi)
- `README.md` — Bilimsel altyapı özeti (Stance Diversity, EWMA, PSM)
- `data/evals/turkish_quality_eval.jsonl` — Kalite değerlendirme veri seti
- `models/` — Sadece README.md kaldı (eski yerel model klasörü)

---

## 🐛 Bilinen Sorunlar / Notlar (2026-08 derin analiz)

1. ✅ **README docs referansı** — `docs/god_doc.md` atfı kaldırıldı, akademik kaynaklara yönlendirildi.
2. ℹ️ **`models/` klasörü** — Sadece README.md (DeepSeek config). Kullanıcı onayıyla kaldırılabilir ama içeriği güncel, silinmedi.
3. ✅ **Batch interview retry** — 2→3 deneme; eksik label'ları hedefli yeniden ister (`run_interviews_batch`).
4. ✅ **synthesize 500 tolerant** — `_synthesize_impl` eksik plan/persona/turn alanlarını varsayılanla doldurur, hata 422 ile döner.
5. ✅ **Openness stance hizalaması** — `persona_traits`'te dc*k9 formülü merkezlendi; Innovator > EarlyAdopter > Mainstream > Skeptic > Laggard sıralaması sağlandı (aynı dc'de).
6. ✅ **RLS canlı testi** — `test_rls_isolation.py` eklendi (Postgres yoksa skip). Tenant izolasyonunu gerçek DB'de doğrular.
7. ℹ️ **Frontend commit'lenmemiş değişiklik** — `studies/[id]/page.tsx` (paywall teaser + brief/Big5 fix) commit bekliyor.
8. ℹ️ **Docker API/Celery host'ta** — `launch.py` sadece postgres+redis'i başlatır; tam Docker deploy için `docker compose up -d clarere-api celery_worker`.

> **Test durumu:** 156 passed + 1 skipped (RLS canlı test — Postgres gerektirir).
