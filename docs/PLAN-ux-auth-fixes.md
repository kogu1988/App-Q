# PLAN-ux-auth-fixes.md
# App-Q — UX, Auth & Veri Bütünlüğü Düzeltme Planı

> Durum: TASLAK — Kullanıcı onayı bekleniyor  
> Tarih: 2026-05-23  
> Kaynak: /brainstorm çıktısı

---

## Kapsam

Brainstorm oturumunda tespit edilen 6 problemi öncelik sırasına göre ele alır.
**Kimlik doğrulama mimari değişikliği içermez** — mevcut `X-Username` header yapısı korunur,
sadece kullanıcı deneyimi ve veri doğruluğu iyileştirilir.

---

## Problem Listesi ve Çözüm Özeti

| # | Problem | Etki | Efor | Öncelik |
|---|---------|------|------|---------|
| P1 | UsageWidget yanlış metrik (`total` yerine `period`) | Yanıltıcı UI | XS | 🔴 Kritik |
| P2 | SEO: `metadata` yok (`"use client"` ile çakıştı) | Google indexleme | S | 🔴 Kritik |
| P3 | "Çıkış Yap" localStorage'ı temizlemiyor | Session kirliği | XS | 🟡 Önemli |
| P4 | İlk kullanım: `appq_username` hiç set edilmiyor | Tüm plan sistemi çalışmıyor | M | 🔴 Kritik |
| P5 | Landing page'den "Starter/Pro ile Başla" → `/client` gidiyor ama username yok | Boş onboarding | M | 🟡 Önemli |
| P6 | `PlanGate` sıralama mantığı doğrulama — OK (zaten `PLAN_ORDER` dizisi var) | — | — | ✅ Çözülmüş |

---

## Detaylı Görev Planı

---

### P1 — UsageWidget: `period_simulations` kullan

**Dosya:** `apps/frontend/src/app/client/page.tsx`

**Mevcut Durum:**
```ts
const used = plan.total_simulations;   // tüm zamanlar toplamı — YANLIŞ
```

**Hedef:**
```ts
const used = plan.period_simulations;  // bu dönem — DOĞRU
```

Ayrıca kullanıcıya dönem bilgisi de gösterilmeli:
- "Bu ay X / Y araştırma kullandınız"
- Dönem bitiş tarihi: `period_start` + 30 gün (monthly) veya + 365 gün (annual)
- Dönem bitiş tarihini küçük tooltip/alt metin olarak ekle

**Değişecek satırlar:** `UsageWidget` fonksiyonu (L22–L78)

---

### P2 — SEO: `metadata` ayrı server component'e taşı

**Problem:** `page.tsx` `"use client"` olduğu için `export const metadata` çalışmıyor.
Next.js App Router'da metadata yalnızca Server Component'lerde kullanılabilir.

**Çözüm Mimarisi:**

```
app/
  page.tsx           → "use client" kalır (mevcut interaktif landing)
  layout.tsx         → metadata buraya taşınır (zaten server component)
```

`layout.tsx` Next.js'de `metadata` export'unu destekler ve tüm `/` route'u için geçerli olur.

**Hedef `apps/frontend/src/app/layout.tsx`:**
```ts
export const metadata: Metadata = {
  title: "App-Q — Yapay Zeka Destekli Sentetik Pazar Araştırması",
  description: "Gerçek mülakatlardan önce sentetik tüketici panelleriyle ürün fikirlerinizi test edin...",
  openGraph: { ... },
};
```

**Dikkat:** Root layout zaten `<html lang>` içeriyor, metadata oraya merge edilir.

---

### P3 — "Çıkış Yap": localStorage temizle

**Dosya:** `apps/frontend/src/app/client/layout.tsx`

**Mevcut:**
```tsx
<Link href="/" className="...">Çıkış Yap</Link>
```

**Hedef:**
```tsx
<button onClick={() => {
  localStorage.removeItem("appq_username");
  window.location.href = "/";
}} className="...">
  Çıkış Yap
</button>
```

`<Link>` yerine `<button>` çünkü click handler gerekiyor.

---

### P4 + P5 — İlk Kullanım: Username Onboarding

**Problem:** Kullanıcı ilk kez `/client`'e geldiğinde `appq_username` localStorage'da yok.
Hook `""` gönderip backend `anonymous` döner → plan = Free (doğru), ama kullanım takibi hiç çalışmıyor.

**Çözüm: Basit Username Modal (ilk giriş)**

`/client/page.tsx` ya da `layout.tsx`'e mount anında:
1. `localStorage.getItem("appq_username")` kontrol et
2. Eğer yoksa → modal aç: "Devam etmek için bir kullanıcı adı girin"
3. Kullanıcı submit eder → `localStorage.setItem("appq_username", value)`
4. Modal kapanır, plan hook yeniden fetch eder

**UI tasarımı:**
- Tam ekran blur overlay + merkez kart
- `<input>` sadece alphanumeric, max 20 karakter
- "Başla" butonu
- Alt metin: "Bu cihaza özel oturum kimliğinizdir. Kayıt gerektirmez."
- Eğer username backend'de bulunamazsa → otomatik `Free` planla oluşturulur
  (Backend: `/api/client/register` endpoint — sadece INSERT OR IGNORE)

**Yeni Backend Endpoint:**
```
POST /api/client/register
Body: { "username": "ali123", "email": "" }
Response: { "username": "ali123", "plan_type": "Free", "created": true/false }
```
`created: false` = zaten vardı, mevcut planla devam et.

**Landing page CTA bağlantısı:**
- "Starter ile Başla" → `/client?plan=starter` — onboarding modal'da plan bilgisi prefill olur
- "Pro ile Başla" → `/client?plan=pro`
- Modal submit → eğer `?plan` varsa → `POST /api/client/upgrade-plan` çağır

---

## Dosya Değişiklik Listesi

### Backend

| Dosya | Değişiklik |
|-------|-----------|
| `apps/backend/routers/client.py` | `POST /register` endpoint ekle |

### Frontend

| Dosya | Değişiklik |
|-------|-----------|
| `apps/frontend/src/app/layout.tsx` | `metadata` export ekle (root layout) |
| `apps/frontend/src/app/client/page.tsx` | `UsageWidget`: `total_simulations` → `period_simulations`, dönem bitiş tarihi |
| `apps/frontend/src/app/client/layout.tsx` | "Çıkış Yap" Link → button + localStorage.removeItem |
| `apps/frontend/src/app/client/layout.tsx` | `UsernameModal` bileşeni ekle (mount'ta kontrol) |
| `apps/frontend/src/app/page.tsx` | "Starter/Pro ile Başla" CTA href'lerine `?plan=starter/pro` query ekle |

---

## Uygulama Sırası

```
1. P2 — layout.tsx metadata          (bağımsız, hızlı)
2. P1 — UsageWidget period fix       (bağımsız, hızlı)
3. P3 — Çıkış Yap fix               (bağımsız, hızlı)
4. Backend: /register endpoint       (P4/P5 için gerekli)
5. Frontend: UsernameModal           (backend hazır olduktan sonra)
6. Landing CTA ?plan= query          (modal hazır olduktan sonra)
```

---

## Doğrulama Kriterleri

| Senaryo | Beklenen Sonuç |
|---------|---------------|
| `localStorage` boşken `/client` aç | Username modal açılır |
| Modal'da "ali123" yaz, Başla'ya bas | Dashboard açılır, UsageWidget "0 / 2 araştırma (Bu Dönem)" gösterir |
| "Starter ile Başla" linkine tıkla | `/client?plan=starter` → modal'da "Starter planı seçildi" mesajı |
| Araştırma yap → dashboard'a dön | UsageWidget sayacı artar (`period_simulations`) |
| "Çıkış Yap"a tıkla | localStorage temizlenir, anasayfaya yönlendirilir |
| Yeniden `/client` aç | Username modal tekrar görünür |
| Google'da "App-Q" ara | Title tag ve description doğru görünür |

---

## Kapsam Dışı (Bu Plana Dahil Değil)

- Gerçek ödeme sistemi (Stripe entegrasyonu)
- JWT/OAuth kimlik doğrulama
- E-posta doğrulama
- Admin panel Next.js'e taşıma
- Persona Builder UI

---

*Onaylandıktan sonra `/create` veya "uygula" komutuyla başlanır.*
