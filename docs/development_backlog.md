# App-Q V3.0 — Geliştirme Backlog ve Yol Haritası

Bu belge tamamlanan sprint geçmişini, bekleyen özellik fikirlerini ve metodoloji notlarını içerir.

---

## ✅ Tamamlanan Sprintler

| Sprint | Açıklama | Durum |
|--------|----------|-------|
| Codebase Audit & DRY Refactor | Streamlit WET kod temizliği, `packages/core` silindi, `reporting.py` ortak katman | ✅ Tamamlandı |
| React + FastAPI Migration | Streamlit → Next.js + FastAPI geçişi | ✅ Tamamlandı |
| Grounded Simulation S1+S2+S3 | Rogers stance, adversarial pipeline, RFI metriği | ✅ Tamamlandı |
| SEO/GEO Optimizasyonu | robots.ts, sitemap.ts, middleware, JSON-LD schema, OG image | ✅ Tamamlandı |
| Yasal Sayfalar | /privacy (KVKK), /terms (kullanım koşulları + algoritma koruması) | ✅ Tamamlandı |
| Landing Page FAQ | 5 soruluk SSS bölümü + FAQPage JSON-LD | ✅ Tamamlandı |

---

## 🔒 Güvenlik — Kritik (Production Öncesi Zorunlu)

| Görev | Açıklama | Öncelik |
|-------|----------|---------|
| **JWT Auth Migrasyonu** | Mevcut `X-Username` header auth → Bearer JWT. `docs/PLAN-jwt-auth-migration.md` oluşturulacak | 🔴 Kritik |
| **ADMIN_SECRET_KEY** | `.env`'de set edilmeli — production'da API korumas&#305;z çalışmaz | 🔴 Kritik |
| **CORS Kısıtlaması** | `ALLOWED_ORIGINS=*` yalnızca dev — production'da domain kısıtlanmalı | 🔴 Kritik |

---

## 🚀 Planlanan Özellikler

### 1. Melez Araştırma Motoru

- **Sentetik Odak Grup (Focus Group) Simülasyonu** `[Efor: Yüksek]`  
  4-5 farklı personanın aynı sanal odada ürünü tartıştığı, fikirlerin çarpıştığı dinamik oturumlar.

- **Büyük Ölçekli Sentetik Anketler** `[Efor: Orta]`  
  1.000 kişilik sentetik kitleye A/B veya çoktan seçmeli anket çözdürerek istatistiksel veri elde etme.

### 2. Gelişmiş Raporlama

- **İnteraktif Grafikler** `[Efor: Yüksek]` — Heatmap, Pie Chart, Cross-tab görselleştirme
- **İstatistiksel Geçerlilik Testleri** `[Efor: Orta]` — Chi-square ötesinde çok değişkenli analiz

### 3. Kullanım Alanı Genişletmeleri

- **Reklam ve Metin Test Motoru (Copywriting Validator)** `[Efor: Orta]`  
  A/B test edilen reklam kopyalarını 50 farklı personaya göstererek yayın öncesi CTR potansiyelini ölçme.

- **Müşteri "Dijital İkiz" Klonlama (CRM RAG Entegrasyonu)** `[Efor: Yüksek]`  
  Şirketin kendi Zendesk/destek verilerini yükleyerek kendi müşterilerinin klonlarıyla test yapabilme.

### 4. Gelir Modeli

- **Per-Seat SaaS Aboneliği** `[Efor: Düşük]` — Kontör stresiz limitsiz (fair-use) model
- **Ajans White-Label Lisanslama** `[Efor: Yüksek]` — Kendi logoyla PDF rapor basma

### 5. UX ve Onboarding

- **Swipe-to-Curate Soru Seçimi** `[Efor: Orta]`  
  10 AI üretilmiş soruyu flashcard olarak gösterip sağa/sola kaydırarak senaryo oluşturma.

- **Görsel Persona Yaratıcısı (AI Portraits)** `[Efor: Yüksek]`  
  Persona slider'ları değiştikçe DALL-E/Stable Diffusion ile anlık yüz üretimi.

### 6. Rekabet Avantajı ve Veri Hendeği

- **Sektörel Şablon Pazaryeri** `[Efor: Yüksek]` — Araştırmacıların şablon yayınlayıp sattığı ekosistem
- **İnsani Önyargı Motoru (Flaw/Bias Engine)** `[Efor: Yüksek]` — LLM'leri kasıtlı bilişsel önyargı üretecek şekilde kalibre etme
- **Kuruma Özel Evrimleşen Model (LoRA)** `[Efor: Yüksek]` — Müşteri geri bildirimiyle sürekli fine-tune

### 7. Teknik Optimizasyon

- **Anlamsal Önbellek (Semantic Caching Tree)** `[Efor: Orta]`  
  pgvector cosine similarity ile benzer sorulara önceki yanıtları yeniden kullanarak LLM maliyetini %90 düşürme.

### 8. Pazara Çıkış (GTM)

- **Startup "Roast" Servisi** `[Efor: Düşük]` — Viral mini araç ile organik trafik
- **Sentetik Endüstri Raporları** `[Efor: Düşük]` — LinkedIn thought leadership içeriği
- **Hyper-Personalized Outreach** `[Efor: Orta]` — Hedef yöneticinin sentetik personasına satış argümanı önce test etme

---

## 🔬 Metodoloji — Backlog Notları

### Tuzak Soru (Attention Check) Entegrasyonu `[Efor: Düşük]` — Beklemede

- **Amaç:** Mülakat script'ine dikkat ölçen "tuzak sorular" eklemek.
- **Neden şimdi değil:** LLM tüm soruları anlam odaklı yanıtladığı için sentetik panelde öncelik düşük. Gerçek kullanıcı paneli entegrasyonu eklenirse yeniden değerlendir.
- **İlgili:** `workflow.py → generate_interview_script()`, `quality.py → compute_research_quality()`

### ACT-R Working Memory Capping `[Efor: Yüksek]` — S4 Backlog

- **Amaç:** Personaların mülakat boyunca taşıyabileceği "çalışan bellek" kapasitesini sınırlayarak gerçekçi bilişsel yük simülasyonu.
- **Neden şimdi değil:** LLM API çağrıları stateless; tam ACT-R uygulaması için multi-turn stateful oturum mimarisi (per-persona context buffer) önce kurulmalı. Mevcut geçici çözüm: `cross-question consistency` + `turn-count limit` heuristikleri.
- **Ön koşul:** Conversation memory + per-persona context buffer mimarisi.
- **İlgili:** `workflow.py → run_persona_interview()`, `models.py → InterviewTurn`

### Hofstede Kültürel Boyutlar Entegrasyonu `[Efor: Orta]` — S4 Backlog

- **Amaç:** 6 kültürel boyutu (PDI, IDV, UAI, LTO, IND, MAS) persona trait kalibrasyonuna eklemek.
- **Neden şimdi değil:** App-Q şu an Türkiye tek pazarını hedefliyor. Türkiye profili (`PDI=66, IDV=37, UAI=85, LTO=46`) model prompt'larına kısmen encoding ile uygulanmakta. Çok pazarlı destek aktif olunca öncelik artar.
- **Ön koşul:** `market` parametreli araştırma desteği + `CulturalProfile` yapısı.
- **İlgili:** `models.py → Persona`, `workflow.py → persona_attributes()`

### Operatör (Admin) Paneli Next.js Yeniden Tasarımı `[Efor: Orta]`

- **Bağlam:** `apps/operator/streamlit_app.py` hâlâ aktif; istemci Next.js'e taşındı, operatör taşınmadı.
- **Hedef:** Next.js `/admin` rotası — KPI kartları, drill-down grid, Trust Blue tema.
- **İlgili:** `apps/operator/streamlit_app.py` (kaynak) → `apps/frontend/src/app/admin/page.tsx` (hedef)

### Persona Builder UI (Next.js) `[Efor: Orta]`

- **Bağlam:** B2B persona oluşturma ekranı Streamlit hedefli yazıldı; Next.js'e uyarlanmadı.
- **Hedef:** `/client/personas/new` → çok adımlı form (Temel Bilgiler → B2B Metrikleri → Özel Trait'ler).
- **Güvenlik notu:** Özel metrik key'lerinde SQL injection vektörlerine dikkat.
- **İlgili:** `apps/frontend/src/app/client/personas/`, `packages/research_engine/db_vectors.py`

---

*Not: Bu belge beyin fırtınası oturumlarından elde edilen çıktılarla güncellenmeye devam edecektir.*
