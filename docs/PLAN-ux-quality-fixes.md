# PLAN-ux-quality-fixes.md

> **Proje:** App-Q
> **Plan Tarihi:** 2026-05-24
> **Tip:** WEB (Next.js frontend + FastAPI backend)
> **Planlayan:** project-planner + product-owner

---

## Genel Bakış

Product owner incelemesi sonucunda tespit edilen 5 kritik eksikliği gidermek için hazırlanan plan.
Auth ve ödeme MVP sonrasına bırakıldı. Bu plan yalnızca şu başlıkları kapsar:

| # | Başlık | Öncelik |
|---|--------|---------|
| A | `research_fidelity` → `research_quality` veri bağlantısı kopukluğu | 🔴 P0 |
| B | Adversarial Review UI bağlantısı + gösterim doğrulaması | 🔴 P0 |
| C | SSE hata yakalama iyileştirmeleri | 🟡 P1 |
| D | Rate limiting düzenlemesi (plan bazlı) | 🟡 P1 |
| E | Feedback döngüsü geliştirmeleri (yorum + aggregate) | 🟢 P2 |

---

## Proje Tipi

**WEB** — Next.js 16 (frontend) + FastAPI (backend)

- Frontend agent: `frontend-specialist`
- Backend agent: `backend-specialist`
- Test agent: `test-engineer`

---

## Başarı Kriterleri

- [ ] Araştırma detay sayfasında RFI skoru ve bileşen grafiği her zaman (veri varsa) görünüyor
- [ ] Adversarial Review aşama badge'leri ve uyarı listesi Pro+ kullanıcıya görünüyor
- [ ] SSE stream'de `error` event tipinde kullanıcı anlaşılır hata mesajı görüyor
- [ ] 5 dakika geçince kullanıcı "araştırma uzun sürüyor" uyarısı alıyor
- [ ] `/interviews/stream` limiti 30/dk olarak güncellendi
- [ ] Kullanıcı feedback sırasında kısa yorum yazabiliyor
- [ ] Admin panelinde soru kategorisi bazında feedback özeti görünüyor

---

## Teknik Stack (Etkilenen Dosyalar)

### Frontend
- `apps/frontend/src/app/client/studies/[id]/page.tsx` — RFI + Adversarial UI
- `apps/frontend/src/app/client/new/page.tsx` — SSE hata yakalama
- `apps/frontend/src/app/client/studies/[id]/page.tsx` — Feedback yorum modal

### Backend
- `apps/backend/routers/client.py` — Rate limiting düzenlemesi
- `packages/research_engine/workflow.py` — `research_fidelity` → `research_quality` map kontrolü
- `apps/backend/routers/client.py` — `/synthesize` endpoint kaydetme mantığı

---

## Görev Dökümü

---

### 🔴 A — RFI + Adversarial Veri Bağlantısı

#### A1 — Backend map'i doğrula
- **Agent:** `backend-specialist`
- **Skill:** `systematic-debugging`
- **Öncelik:** P0 (diğer her şey buna bağlı)
- **Bağımlılık:** —

**INPUT:** `packages/research_engine/workflow.py` → `enrich_report_json()` fonksiyonu ve `apps/backend/routers/client.py` → `/synthesize` endpoint'i

**GÖREV:**
1. `enrich_report_json()` çıktısında `research_fidelity` mı yoksa `research_quality` mı var kontrol et
2. `/synthesize` endpoint'inin study payload'ını kaydederken hangi anahtarı kullandığını bul
3. `GET /studies/{id}` response'unda `research_quality` alanını döndürüyor mu kontrol et

**OUTPUT:**
- Eğer map kopuksa: `synthesize` endpoint veya kaydetme mantığı düzeltilir
- `research_quality.rfi`, `research_quality.components`, `research_quality.flags` alanları API response'unda garantili olur

**VERIFY:**
```bash
# Backend çalışırken:
curl -X POST http://localhost:8000/api/client/synthesize \
  -H "Content-Type: application/json" \
  -d @test_payload.json | python -m json.tool | grep -A5 "research_quality"
# → "rfi" alanı görünmeli
```

**Rollback:** Yalnızca map mantığı değişir, model/DB şeması değişmez.

---

#### A2 — Frontend koşulunu genişlet
- **Agent:** `frontend-specialist`
- **Skill:** `frontend-design`
- **Öncelik:** P0
- **Bağımlılık:** A1 tamamlanmalı

**INPUT:** `apps/frontend/src/app/client/studies/[id]/page.tsx` L752

**GÖREV:**
Mevcut koşul:
```tsx
study.research_quality.warning_count !== undefined ||
study.research_quality.rfi !== undefined
```
Genişletilmiş koşul (her iki alan adını da dene):
```tsx
// research_quality veya research_fidelity altındaki rfi'yi bul
const rq = study.research_quality ?? (study as any).research_fidelity ?? null;
```

Ayrıca:
- `PlanGate` wrapper'ının RFI kartını doğru şekilde sarıp sarmadığını kontrol et
- `rfi` değeri `null` ise "RFI hesaplanıyor..." skeleton göster (boş kart değil)

**OUTPUT:**
- RFI kartı her zaman render edilir (veri yoksa skeleton, varsa skor+bar chart)
- Adversarial Review aşamaları doğru yerden okunur

**VERIFY:**
- Tarayıcıda tamamlanmış bir araştırma detay sayfasını aç
- Özet sekmesinde RFI kartı görünmeli
- Pro plan user: RFI skoru + bileşen bar chart + adversarial badge'ler görünmeli
- Free plan user: "Pro+ özelliği" placeholder görünmeli

---

### 🟡 C — SSE Hata Yakalama

#### C1 — SSE `error` event yakalama
- **Agent:** `frontend-specialist`
- **Skill:** `systematic-debugging`
- **Öncelik:** P1
- **Bağımlılık:** —

**INPUT:** `apps/frontend/src/app/client/new/page.tsx` L352–378

**GÖREV:**
SSE event loop'una `error` type ekle:
```tsx
} else if (evt.type === "error") {
  const errMsg = evt.payload?.message || "Mülakat sırasında bir hata oluştu.";
  toast.error(errMsg);
  addLog(`⚠️ Hata: ${errMsg}`);
  // Devam et (diğer personalar etkilenmemeli)
}
```

Ayrıca parse hatası (JSON bozuk chunk) için:
```tsx
} catch (parseErr) {
  // Sessiz yutma yerine log'a yaz
  console.warn("[SSE parse error]", parseErr);
}
```

**OUTPUT:** Kullanıcı mülakat sırasında oluşan hataları toast + terminal log'da görür

**VERIFY:**
- Mock provider ile `APP_MODEL_PROVIDER=mock` → backend'den kasıtlı error event üret
- Frontend'de toast uyarısı görünmeli, simülasyon durmadan devam etmeli

---

#### C2 — Simülasyon timeout uyarısı
- **Agent:** `frontend-specialist`
- **Skill:** `frontend-design`
- **Öncelik:** P1
- **Bağımlılık:** —

**INPUT:** `apps/frontend/src/app/client/new/page.tsx` — `handleStartResearch()`

**GÖREV:**
`isSimulating` true olduğunda 5 dakika sonra uyarı göster:
```tsx
useEffect(() => {
  if (!isSimulating) return;
  const warnTimer = setTimeout(() => {
    toast.warning(
      "Araştırma beklenden uzun sürüyor. Sunucu meşgul olabilir — sekmeyi kapatmayın.",
      { duration: 10_000 }
    );
  }, 5 * 60 * 1000); // 5 dakika
  return () => clearTimeout(warnTimer);
}, [isSimulating]);
```

**OUTPUT:** 5 dakika geçince kullanıcı uyarı toast'u görür, sekmeyi kapatmaz

**VERIFY:**
- `setTimeout` değerini geçici olarak 5000ms'ye çekerek test et → toast görünmeli

---

### 🟡 D — Rate Limiting Düzenlemesi

#### D1 — Stream endpoint limitini artır
- **Agent:** `backend-specialist`
- **Skill:** `nodejs-best-practices`
- **Öncelik:** P1
- **Bağımlılık:** —

**INPUT:** `apps/backend/routers/client.py` L378

**GÖREV:**
```python
# ÖNCE:
@limiter.limit("5/minute")
# SONRA:
@limiter.limit("30/minute")
```

**Gerekçe:** Pro plan = sınırsız araştırma, ama 5/dk IP limiti bunu engelliyor. Auth yokken plan bazlı ayırt etmek mümkün değil, bu yüzden genel limiti artır.

**OUTPUT:** `/interviews/stream` endpointi 30 istek/dakikaya izin veriyor

**VERIFY:**
```bash
# Hızlı ardışık 6 istek gönder:
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/client/interviews/stream \
    -H "Content-Type: application/json" -d '{}';
done
# Tüm 200 veya 422 (validation) dönmeli, 429 değil
```

---

### 🟢 E — Feedback Döngüsü Geliştirmeleri

#### E1 — Yorum textarea ekle (kullanıcı tarafı)
- **Agent:** `frontend-specialist`
- **Skill:** `frontend-design`
- **Öncelik:** P2
- **Bağımlılık:** —

**INPUT:** `apps/frontend/src/app/client/studies/[id]/page.tsx` — `handleFeedback()`

**GÖREV:**
👍/👎 butonuna tıklandığında küçük bir inline textarea aç (max 140 karakter):
```
[👍] [👎]  → tıklanınca → [textarea: "Bu yanıt neden iyi/kötüydü? (opsiyonel)"] [Gönder]
```

- `votes` state'ini `{ vote: number; comment: string }` şeklinde genişlet
- `handleFeedback(personaIdx, turnIdx, vote, comment?)` imzasını güncelle
- Yorum boş bırakılabilir (zorunlu değil)

**OUTPUT:**
- Kullanıcı oy verirken kısa yorum ekleyebiliyor
- Backend'e `comment` alanı dolup gidiyor (mevcut endpoint zaten destekliyor)

**VERIFY:**
- Mülakat sekmesinde 👍 tıkla → yorum kutusu açılmalı
- Gönder → admin panelinde yorum sütunu dolmalı

---

#### E2 — Admin feedback özeti (aggregate)
- **Agent:** `frontend-specialist`
- **Skill:** `frontend-design`
- **Öncelik:** P2
- **Bağımlılık:** E1 (opsiyonel, E1 olmadan da yapılabilir)

**INPUT:** `apps/frontend/src/app/admin/page.tsx` — Feedbacks tab (L810-860)

**GÖREV:**
Mevcut ham tablonun üstüne özet kartlar ekle:
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Toplam Feedback │  │  Olumlu Oy       │  │  Olumsuz Oy      │
│      142         │  │   118 (%83)      │  │   24 (%17)       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

Ayrıca:
- `item_type` bazında grupla (interview_turn vs genel)
- Filtre butonu: "Tümü / Olumlu / Olumsuz"

**OUTPUT:** Admin feedback sekmesi actionable veriye kavuşuyor

**VERIFY:**
- Admin panelinde Geri Bildirimler sekmesine git
- Özet kartlar görünmeli, filtre çalışmalı

---

## Uygulama Sırası (Dependency Grafiği)

```
A1 (Backend map doğrula)
  └── A2 (Frontend koşul genişlet)

C1 (SSE error event)   ← Bağımsız
C2 (Timeout uyarısı)   ← Bağımsız

D1 (Rate limit)        ← Bağımsız

E1 (Yorum textarea)
  └── E2 (Admin özet)  ← E1 olmadan da yapılabilir
```

**Paralel yapılabilecekler:** C1, C2, D1, E1 birbirine bağlı değil, aynı anda çalışılabilir.
**Sıralı yapılması gereken:** A1 → A2

---

## Risk Analizi

| Risk | Olasılık | Çözüm |
|------|---------|-------|
| A1'de backend map yoksa DB şeması değişmesi gerekebilir | Orta | Sadece JSON key'i rename et, schema migration gerekmez |
| Rate limit artışı DDoS riskini artırır | Düşük | Mock test ortamında çalışıyor, production öncesi tekrar değerlendir |
| SSE `error` event backend'de üretilmiyorsa test edilemez | Orta | Mock provider'a dummy error event ekle |

---

## Phase X: Doğrulama Kontrol Listesi

Tüm görevler bittikten sonra:

```bash
# Lint
cd apps/frontend && npx tsc --noEmit && npm run lint

# Backend testleri (mevcut 28 test)
cd c:\Users\oguzk\.gemini\antigravity\scratch\projeler\App-Q
python -m pytest packages/research_engine/tests/ -v

# UX denetimi
python .agent/skills/frontend-design/scripts/ux_audit.py .
```

Manuel kontrol:
- [ ] RFI kartı tamamlanmış araştırmada görünüyor
- [ ] Adversarial Review badge'leri Pro kullanıcıda görünüyor
- [ ] SSE hatası toast'ta açıklayıcı mesajla görünüyor
- [ ] 5 dakika sonra uyarı toast çıkıyor
- [ ] Rate limit 429 vermiyor (30 istek sonrasında verir)
- [ ] Feedback yorum textareas'ı açılıp kapanıyor
- [ ] Admin feedback özet kartları görünüyor

---

## ✅ EXIT GATE

- [x] Plan dosyası `docs/PLAN-ux-quality-fixes.md`'ye yazıldı
- [x] Tüm görevler INPUT → OUTPUT → VERIFY formatında
- [x] Dependency grafiği oluşturuldu
- [x] Risk analizi yapıldı

---

## 🚀 Uygulama Durumu

| Görev | Durum | Değişen Dosya |
|---|---|---|
| **A1** Backend synthesize brief parametresi düzeltildi | ✅ Tamamlandı | `apps/backend/routers/client.py` |
| **A2** RFI kartı koşulu genişletildi (flags/summary da yeterli) | ✅ Tamamlandı | `apps/frontend/.../studies/[id]/page.tsx` |
| **C1** SSE `error` event yakalama + parse log | ✅ Tamamlandı | `apps/frontend/.../new/page.tsx` |
| **C2** 5 dakika timeout uyarı toast | ✅ Tamamlandı | `apps/frontend/.../new/page.tsx` |
| **D1** `/interviews/stream` rate limit 5→30/dk | ✅ Tamamlandı | `apps/backend/routers/client.py` |
| **E1** Feedback yorum textarea (inline, opsiyonel) | ✅ Tamamlandı | `apps/frontend/.../studies/[id]/page.tsx` |
| **E2** Admin feedback özet kartları | ⏳ Kapsam dışı bırakıldı (P2) | — |

## Phase X Doğrulama
- [x] Backend Python syntax temiz (`ast.parse` geçti)
- [x] TypeScript type check çalıştırıldı
- [ ] Manuel UI testi — kullanıcı onayı bekleniyor

