# Clarere — Agent Memory

> Bu dosya, projedeki her dosyanın ne işe yaradığını, kritik kararları ve mimariyi özetler.  
> **Amaç:** Her seferinde tüm kodu okumak yerine buradan hızlıca bağlam yakalamak.

---

## 🧠 Proje Özeti

Türkiye odaklı sentetik persona pazar araştırma platformu. DeepSeek API (Flash + Pro) ile çalışır.

## 🏗️ Mimari (3 Aşamalı API)

```
POST /api/client/intake       → Defne sohbeti (flash)
POST /api/client/research     → Plan + Persona + Batch Mülakat (flash)
POST /api/client/synthesize   → Rapor (algoritmik)
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
| `routers/client.py` | Tüm client endpoint'leri | API endpoint ekleme/değiştirme |
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
| `quality.py` | Kalite fonksiyonları (EWMA, echo, bias) | Kalite kontrolü |
| `adversarial.py` | 4-aşamalı adversarial review | Rapor denetimi |
| `database.py` | `init_db()`, bağlantı havuzu, tüm DB CRUD | Veritabanı değişikliği |
| `plan_config.py` | Plan feature gate SSOT (Free→Enterprise) | Plan/özellik değişikliği |

### LangGraph Nodes (`packages/research_engine/nodes/`)

| Dosya | Görev |
|---|---|
| `sycophancy.py` | ELEPHANT anti-dalkavukluk prompt + `judge_answer_quality()` |
| `culture.py` | Hofstede TR, SES profilleri, taksit/BDDK lojistiği |
| `memory.py` | ACT-R bilişsel bellek modeli |
| `router.py` | Keyword-based routing (basitleştirildi) |

### Frontend (`apps/frontend/`)

| Dosya | Görev |
|---|---|
| `src/app/page.tsx` | Landing page + fiyatlandırma |
| `src/app/client/new/page.tsx` | Araştırma sihirbazı (Defne → Research) |
| `src/app/client/studies/[id]/page.tsx` | Araştırma detay/rapor sayfası |
| `src/app/client/page.tsx` | Client dashboard |
| `next.config.ts` | Proxy `/api/*` → `localhost:4000`, security headers |
| `package.json` | Next.js 16, React 19, Tailwind 4, shadcn, recharts |

### Konfigürasyon

| Dosya | Görev |
|---|---|
| `.env` | DeepSeek API key + DB/Redis ayarları (gitignored) |
| `docker-compose.yml` | PostgreSQL (5433) + Redis (4006) |
| `launch.py` | Tek tıkla başlatma (Docker kontrolü + backend + frontend) |
| `start.bat` | `python launch.py` wrapper |

---

## 🔑 Kritik Kararlar

1. **Ollama/Mock tamamen kaldırıldı** — Sadece DeepSeek API (Flash + Pro) var
2. **Semantic cache kaldırıldı** — Embedding API'si yok, hash-based cache de riskli bulundu
3. **Batch interview** — Persona başına tek API çağrısı (5 persona = 5 istek). Conversation Paradox ile uyumlu (F1: 0.065 vs 0.082)
4. **Thinking Mode** — DeepSeek varsayılanı, `temperature` KULLANILMAZ. `reasoning_content` ayrı alanda gelir
5. **`user_id`** — DeepSeek isolation için `[a-zA-Z0-9_-]+` regex ile sanitize ediliyor
6. **3 aşamalı flow** — Her aşama ayrı endpoint, model kafası karışmasın diye
7. **Enterprise feature'lar** — Yerel LLM fine-tuning, embedding, persona havuzu eşleştirme (ileride)

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

## 🐛 Bilinen Sorunlar / TODO

- Study detay sayfasında "Sentez Raporu" butonu yok — kullanıcı manuel synthesize edemiyor
- 110 test çalıştırılmadı (Ollama mimarisi için yazılanlar kırık olabilir)
- Celery worker / async pipeline test edilmedi
- Admin panel embedding'siz çalışıyor (Enterprise'ta geri gelecek)
- PDF export test edilmedi
