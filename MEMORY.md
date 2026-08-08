# Clarere — Agent Memory

> Bu dosya, projedeki her dosyanın ne işe yaradığını, kritik kararları ve mimariyi özetler.  
> **Amaç:** Her seferinde tüm kodu okumak yerine buradan hızlıca bağlam yakalamak.

---

## 🧠 Proje Özeti

Türkiye odaklı sentetik persona pazar araştırma platformu. DeepSeek API (Flash + Pro) ile çalışır.
Marka: **Clarere** | İletişim: **hiclarere@clarere.com**

## 🏗️ Mimari (3 Aşamalı API)

```
POST /api/client/intake       → Defne sohbeti (flash)
POST /api/client/research     → Plan + Persona + Batch Mülakat (flash)
POST /api/client/synthesize   → Rapor (algoritmik)
POST /api/client/contact      → İletişim formu (DB'ye kaydeder)
```

## ⚡ Hızlı Başlatma

```bash
python launch.py  # Tek tıkla. Backend :4000, Frontend :4001
# --reload aktif, kod değişince otomatik yeniden başlar
```

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
| `intake.py` | `process_intake_chat()` — Defne chatbot | Defne davranışı |
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

### LangGraph Nodes (`packages/research_engine/nodes/`)

| Dosya | Görev |
|---|---|
| `sycophancy.py` | ELEPHANT anti-dalkavukluk prompt + `judge_answer_quality()` |
| `culture.py` | Hofstede TR, SES profilleri, taksit/BDDK lojistiği |
| `memory.py` | ACT-R bilişsel bellek modeli |
| `router.py` | Keyword-based routing (basitleştirildi, geriye dönük uyumluluk) |

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

---

## 🔑 Kritik Kararlar

1. **Ollama/Mock tamamen kaldırıldı** — Sadece DeepSeek API (Flash + Pro) var
2. **Semantic cache kaldırıldı** — Embedding API'si yok
3. **Batch interview** — Persona başına tek API çağrısı (5 persona = 5 istek). Conversation Paradox ile uyumlu
4. **Thinking Mode** — DeepSeek varsayılanı, `temperature` KULLANILMAZ. `reasoning_content` ayrı alanda gelir
5. **`user_id`** — DeepSeek isolation için `[a-zA-Z0-9_-]+` regex ile sanitize
6. **3 aşamalı flow** — Her aşama ayrı endpoint, model kafası karışmasın diye
7. **Enterprise feature'lar** — Yerel LLM fine-tuning, embedding, persona havuzu eşleştirme (ileride)
8. **Tüm App-Q referansları Clarere olarak değiştirildi** — localStorage, PDF adı, API title, prompt'lar
9. **5 demo kullanıcı** — free, flex, starter, pro, enterprise (development modunda)
10. **Free plan upsell** — Paywall (blur + Lock), "Planı Yükselt →" CTA

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
