# PLAN-jwt-auth-migration.md
## App-Q — X-Username → JWT Kimlik Doğrulama Migrasyonu

> **Oluşturuldu:** 2026-05-23
> **Durum:** ⏳ ERTELENDİ — Production öncesi sprint'e alındı
> **Kaynak:** archaeologist_analysis.md → SA-3 / BS-4
> **Öncelik:** 🟡 Orta (lokal/demo aşamasında gerek yok)

> [!NOTE]
> **Neden Ertelendi?** Uygulama şu an lokal geliştirme ve demo aşamasında. X-Username header auth bu ortamda yeterli — dış erişim yok. Bu plan, ilk gerçek kullanıcıya açılmadan önce (pre-production sprint) uygulanmalıdır.


---

## 📌 Problem

Mevcut auth mekanizması:
```
Frontend → X-Username: "alice" (plain text header)
Backend  → get_client_by_username("alice") → plan bilgisi
```

**Güvenlik riski:** Herhangi bir kullanıcı `X-Username: enterprise` header'ı göndererek:
- Enterprise planı taklit edebilir
- Sınırsız simülasyon çalıştırabilir
- Diğer kullanıcıların kayıtlarına (study, feedback) erişebilir

**Etkilenen yerler:**
- Backend: `client.py` — 27 yerde `x_username` kullanımı
- Frontend: `localStorage["appq_username"]` → 5 dosyada `X-Username` header

---

## 🎯 Hedef Mimari

```
Kayıt/Giriş:
  Frontend → POST /api/auth/login {username} → {access_token: "eyJ..."} 
  Frontend → localStorage.setItem("appq_token", token)

Korumalı İstek:
  Frontend → Authorization: Bearer eyJ...
  Backend  → JWT decode → username extract → plan lookup
```

---

## ✅ Başarı Kriterleri

| Kriter | Ölçüm |
|--------|-------|
| JWT imzalı token üretimi | `POST /api/auth/login` → `access_token` dönüyor |
| Token doğrulama | İmzasız/süresi dolmuş token → 401 |
| Geriye dönük uyumluluk | Geçiş süresi: X-Username → JWT paralel çalışır |
| Frontend sıfır kırılma | Tüm dashboard akışları token ile çalışıyor |
| Güvenlik testi | Sahte username token → 401 |

---

## 🔧 Tech Stack Kararları

| Bileşen | Seçim | Neden |
|---------|-------|-------|
| JWT kütüphanesi | `python-jose[cryptography]` | FastAPI ekosisteminde standart, async uyumlu |
| İmzalama algoritması | `HS256` | Symmetric — tek sunucu, secret key yeterli |
| Token ömrü | `access: 7 gün` (şimdilik) | Refresh token yok → basit; SaaS için yeterli |
| Secret key | `JWT_SECRET_KEY` env var | `.env` dosyasına, production'da rotate edilir |
| Frontend depolama | `localStorage["appq_token"]` | Mevcut pattern ile uyumlu geçiş |

> **Neden Refresh Token YOK?** App-Q bir B2B araştırma aracı. Oturum süresi 7 gün — kullanıcı her haftabaşında yeniden giriş yapar. OAuth + refresh token kompleksliği bu aşamada overkill.

---

## 📁 Etkilenen Dosyalar

```
App-Q/
├── packages/research_engine/
│   └── database.py               ← [MODIFY] login hash yok, token_blacklist? değil
│
├── apps/backend/
│   ├── main.py                   ← [MODIFY] JWT_SECRET_KEY env var + routers
│   ├── auth.py                   ← [NEW] JWT encode/decode + login endpoint
│   └── routers/
│       ├── client.py             ← [MODIFY] x_username → current_user dependency
│       └── admin.py              ← [MODIFY] require_admin → header korunuyor (değişmez)
│
├── apps/frontend/src/
│   ├── lib/
│   │   └── auth.ts               ← [NEW] getToken(), setToken(), clearToken()
│   ├── hooks/
│   │   └── use-client-plan.ts    ← [MODIFY] X-Username → Bearer token
│   ├── components/
│   │   └── username-modal.tsx    ← [MODIFY] register → token kaydet
│   └── app/client/
│       ├── page.tsx              ← [MODIFY] X-Username → Bearer token
│       └── layout.tsx            ← [MODIFY] logout → clearToken()
│
├── .env                          ← [MODIFY] JWT_SECRET_KEY ekle
├── .env.example                  ← [MODIFY] JWT_SECRET_KEY placeholder ekle
└── requirements.txt              ← [MODIFY] python-jose[cryptography] ekle
```

---

## 📋 Görev Listesi

### 🔴 Faz 0 — Altyapı (Bağımsız, Önce Yapılmalı)

#### T-01: JWT bağımlılıklarını kur
- **Agent:** backend-specialist
- **Dosya:** `requirements.txt`, `pyproject.toml` (varsa)
- **INPUT:** `pip install python-jose[cryptography]`
- **OUTPUT:** `requirements.txt`'te `python-jose` satırı
- **VERIFY:** `python -c "from jose import jwt; print('ok')"`

#### T-02: `JWT_SECRET_KEY` env var ekle
- **Agent:** security-auditor
- **Dosya:** `.env`, `.env.example`
- **INPUT:** `openssl rand -hex 32` ile üretilmiş key
- **OUTPUT:** `.env` → `JWT_SECRET_KEY=<32-byte-hex>`
- **VERIFY:** `os.getenv("JWT_SECRET_KEY")` değer dönüyor
- ⚠️ **Dikkat:** `.env` git'e commit edilmemeli

---

### 🔴 Faz 1 — Backend Auth Modülü (T-01, T-02'ye bağımlı)

#### T-03: `apps/backend/auth.py` oluştur [YENİ]
- **Agent:** backend-specialist
- **INPUT:** Yok (yeni dosya)
- **OUTPUT:**
  ```python
  # auth.py içerik özeti:
  SECRET_KEY = os.getenv("JWT_SECRET_KEY")
  ALGORITHM = "HS256"
  TOKEN_EXPIRE_DAYS = 7
  
  def create_access_token(username: str) -> str
  def decode_token(token: str) -> str  # returns username
  def get_current_user(token: str = Depends(oauth2_scheme)) -> str
  ```
- **VERIFY:** `decode_token(create_access_token("alice")) == "alice"`

#### T-04: `POST /api/auth/login` endpoint ekle → `auth.py`
- **Agent:** backend-specialist
- **INPUT:** `{username: "alice"}` (şifresiz — mevcut model)
- **OUTPUT:** `{access_token: "eyJ...", token_type: "bearer", username: "alice"}`
- **LOGIC:**
  1. `get_client_by_username(username)` → kayıtlı mı?
  2. Kayıtlıysa → token üret ve dön
  3. Kayıtlı değilse → `register_client_if_new()` çağır → token üret
- **VERIFY:** `POST /api/auth/login {"username":"free"}` → 200 + token

#### T-05: `POST /api/auth/register` endpoint → token dönsün
- **Agent:** backend-specialist
- **INPUT:** `{username, new_plan?}` (mevcut `/register` gibi)
- **OUTPUT:** `{access_token, token_type, username, plan_type, created}`
- **LOGIC:** Mevcut `/register` mantığını taşı → login'de birleştir
- **VERIFY:** Yeni kullanıcı → token alıyor, `/me` ile doğrulanıyor

#### T-06: `main.py`'a auth router ekle
- **Agent:** backend-specialist
- **INPUT:** `auth.py` router tanımlı
- **OUTPUT:** `app.include_router(auth.router, prefix="/api/auth")`
- **VERIFY:** `GET /openapi.json` → `/api/auth/login` görünüyor

---

### 🔴 Faz 2 — Client Router Migrasyonu (T-03'e bağımlı)

#### T-07: `_resolve_plan()` → `get_current_user` dependency'e geçiş
- **Agent:** backend-specialist
- **Dosya:** `client.py`
- **STRATEJI:** Geriye dönük uyumluluk — geçiş süresi boyunca hem X-Username hem Bearer kabul et:
  ```python
  def get_optional_user(
      authorization: str | None = Header(default=None),
      x_username: str | None = Header(default=None),  # deprecated
  ) -> str | None:
      if authorization and authorization.startswith("Bearer "):
          return decode_token(authorization[7:])
      return x_username  # fallback: eski header
  ```
- **INPUT:** Tüm `x_username: str | None = Header(...)` parametreleri
- **OUTPUT:** `current_user: str | None = Depends(get_optional_user)`
- **VERIFY:** Hem eski hem yeni token ile `/me` → 200

#### T-08: Korumalı endpoint'lere zorunlu auth ekle
- **Agent:** security-auditor
- **Dosya:** `client.py`
- **KAPSAM:** `upgrade_plan`, `stream_interviews`, `synthesize` → `current_user` zorunlu (None → 401)
- **DIŞARIDA KALAN:** `intake_chat`, `create_plan` → optional (anonim kullanıcı desteklenebilir)
- **VERIFY:** `POST /upgrade-plan` Authorization header'sız → 401

---

### 🟡 Faz 3 — Frontend Migrasyonu (T-04'e bağımlı)

#### T-09: `apps/frontend/src/lib/auth.ts` oluştur [YENİ]
- **Agent:** frontend-specialist
- **INPUT:** Yok
- **OUTPUT:**
  ```typescript
  export function getToken(): string | null
  export function setToken(token: string): void
  export function clearToken(): void
  export function getUsername(): string | null  // token'dan decode
  export function isLoggedIn(): boolean
  ```
- **VERIFY:** `setToken("x"); getToken() === "x"` ✓

#### T-10: `username-modal.tsx` → register → token kaydet
- **Agent:** frontend-specialist
- **Dosya:** `apps/frontend/src/components/username-modal.tsx`
- **DEĞIŞIKLIK:**
  - `POST /api/client/register` → `POST /api/auth/login` (veya `/api/auth/register`)
  - Response'dan `access_token` al → `setToken(token)` çağır
  - `localStorage.setItem("appq_username", ...)` → `auth.ts`'e devret
- **VERIFY:** Modal submit → localStorage'da `appq_token` key var

#### T-11: `use-client-plan.ts` → Bearer token kullan
- **Agent:** frontend-specialist
- **Dosya:** `apps/frontend/src/hooks/use-client-plan.ts`
- **DEĞIŞIKLIK:**
  ```typescript
  // Eski
  headers: { "X-Username": username }
  // Yeni
  headers: { "Authorization": `Bearer ${getToken()}` }
  ```
- **VERIFY:** `/api/client/me` → 200 plan bilgisi geliyor

#### T-12: `page.tsx` ve `layout.tsx` → Bearer token
- **Agent:** frontend-specialist
- **Dosya:** `apps/frontend/src/app/client/page.tsx`, `layout.tsx`
- **DEĞIŞIKLIK:** Tüm `X-Username` header'ları → `Authorization: Bearer ${getToken()}`
- **Logout:** `clearToken()` çağır (localStorage key'i `appq_token` olacak)
- **VERIFY:** Logout → redirect `/` ✓; Giriş → dashboard açılıyor ✓

---

### 🟢 Faz 4 — Temizlik ve Güvenlik Sertleştirme (Tüm Fazlara Bağımlı)

#### T-13: `X-Username` fallback kaldır (geçiş tamamlandıktan sonra)
- **Agent:** security-auditor
- **Dosya:** `client.py`
- **TIMING:** Faz 3 verify + 1 hafta bekleme süresi (eski client'lar için)
- **OUTPUT:** `get_optional_user` → sadece Bearer token kabul eder
- **VERIFY:** `X-Username: enterprise` gönder → 401 (artık çalışmıyor)

#### T-14: Demo seed kullanıcılarını kaldır (DB-5 ile birlikte)
- **Agent:** security-auditor
- **Dosya:** `database.py`
- **NOT:** JWT ile artık seed kullanıcı = backdoor riski ortadan kalkar
- **OUTPUT:** `APP_ENV != production` koruması zaten var; seed tamamen kaldırılabilir
- **VERIFY:** Fresh `init_db()` → `clients` tablosu boş

#### T-15: Token expiry ve refresh akışı dokümanı
- **Agent:** backend-specialist
- **OUTPUT:** `docs/AUTH-FLOW.md` — token lifecycle, refresh yok, ne zaman gerekir
- **VERIFY:** Dosya var ve okunabilir

---

## 🧩 Bağımlılık Grafiği

```
T-01 (pip install)
T-02 (env var)
    │
T-03 (auth.py) ← T-01, T-02
    │
    ├─→ T-04 (login endpoint)
    ├─→ T-05 (register endpoint)
    ├─→ T-06 (main.py router)
    │
    └─→ T-07 (client.py migrate) ← T-03
            │
            └─→ T-08 (auth zorunlu) ← T-07
            
T-09 (auth.ts) ← T-04 (backend login hazır olunca)
    │
    ├─→ T-10 (modal migrate)
    ├─→ T-11 (hook migrate)
    └─→ T-12 (page/layout migrate)

T-13 (fallback kaldır) ← T-07, T-08, T-09-T-12 (tümü bitti)
T-14 (seed kaldır) ← T-13
T-15 (doküman) ← T-13, T-14
```

---

## ⚠️ Riskler ve Önlemler

| Risk | Önlem |
|------|-------|
| Mevcut kullanıcılar logout edilir | Geçiş süreci: paralel X-Username + Bearer (T-07) |
| JWT_SECRET_KEY kaybolursa tüm tokenlar geçersiz | `.env` backup alınmalı; rotation prosedürü belirlenmeli |
| `python-jose` güvenlik açığı | `pip-audit` + Dependabot ile izle |
| Demo seed kullanıcıları JWT'den sonra hâlâ backdoor | T-14 ile seed kaldırılıyor |
| Frontend localStorage XSS riski | Token sadece HttpOnly cookie'de güvenli; SPA için kabul edilebilir risk |

> **Not:** Şifre YOK. "Alice" giriş yaparken sadece `{username: "alice"}` gönderiyor. Bu basit model — SaaS ürününün B2B müşterileri için gelecekte SSO/OAuth entegrasyonu gerekebilir.

---

## 🔢 Tahmini Efor

| Faz | Görevler | Süre |
|-----|----------|------|
| Faz 0 | T-01, T-02 | 15 dk |
| Faz 1 | T-03 → T-06 | 1.5 saat |
| Faz 2 | T-07, T-08 | 1 saat |
| Faz 3 | T-09 → T-12 | 1.5 saat |
| Faz 4 | T-13 → T-15 | 30 dk |
| **TOPLAM** | **15 görev** | **~4.5 saat** |

---

## Phase X: Verification Checklist

- [ ] `python-jose` kurulu, `ast.parse` clean
- [ ] `JWT_SECRET_KEY` env var set
- [ ] `POST /api/auth/login {"username":"free"}` → 200 + `access_token`
- [ ] `GET /api/client/me` Authorization Bearer → 200
- [ ] `GET /api/client/me` X-Username fallback → 200 (geçiş süresi)
- [ ] `GET /api/client/me` header yok → 200, plan=Free (anonim)
- [ ] `POST /api/client/upgrade-plan` header yok → 401
- [ ] Sahte token → 401 (signature invalid)
- [ ] Süresi dolmuş token → 401 (expired)
- [ ] Frontend modal submit → token localStorage'da var
- [ ] Frontend dashboard → `/me` 200, plan bilgisi doğru
- [ ] Frontend logout → localStorage temiz → redirect `/`
- [ ] `npm run build` → sıfır TypeScript hatası
- [ ] `python .agent/scripts/verify_all.py .` → pass

---

## 🔴 Onay Soruları (Başlamadan Önce)

1. **Şifre?** — Şimdilik "username-only" yeterli mi, yoksa bcrypt password hash istiyor musun?
2. **Token süresi** — 7 gün yeterli mi? Kısa tutmak istersen 24 saat + refresh token mimarisi gerekir.
3. **HttpOnly cookie mi, localStorage mi?** — Cookie XSS'e karşı daha güvenli ama Next.js SSR ile extra konfigürasyon gerektirir.

---

*Plan: @[project-planner] + @[backend-specialist] + @[security-auditor] | App-Q v3.1 | 2026-05-23*
