# Clarere — Deploy / Launch Checklist

> Production'a almak için somut adımlar. Kod tarafı hazır; bu adımlar iş/operasyon katmanıdır.

## 1. Production Ortam Değişkenleri (`.env`)

```env
APP_ENV=production

# Model
DEEPSEEK_API_KEY=sk-...          # zorunlu
DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro

# PostgreSQL (zorunlu)
POSTGRES_USER=clarere_user       # superuser (migration için)
POSTGRES_PASSWORD=<güçlü-şifre>  # zorunlu
POSTGRES_DB=clarere_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# App DB rolü (RLS'ye tabi, superuser OLMAYAN)
APP_DB_USER=clarere_app
APP_DB_PASSWORD=<güçlü-şifre>

# Güvenlik (production'da ZORUNLU — set edilmezse uygulama açılmaz)
ADMIN_SECRET_KEY=<rastgele-uzun>  # admin API
JWT_SECRET=<rastgele-uzun>        # JWT imzalama
ALLOWED_ORIGINS=https://your-domain.com  # CORS — main.py production'da bunu zorunlu kılar
```

> **Kritik:** `ALLOWED_ORIGINS` boşsa ve `APP_ENV=production` ise backend başlarken `RuntimeError` fırlatır. `ADMIN_SECRET_KEY` boşsa admin API korumasız çalışır (terminal uyarısı).

## 2. Güvenlik Kontrolleri

- [ ] `JWT_SECRET` ve `ADMIN_SECRET_KEY` güçlü, rastgele ve sadece `.env`'de
- [ ] `ALLOWED_ORIGINS` gerçek domaine ayarlı (production'da `*` değil)
- [ ] HTTPS/SSL aktif (reverse proxy veya hosting SSL)
- [ ] Production'da auth: **yalnızca JWT** (`Authorization: Bearer`) — `X-Username` fallback'i kod tarafından kapatıldı
- [ ] `.env` git'e push'lanmadı (`.gitignore`'da)

## 3. Veritabanı

```powershell
# pgvector'lü PostgreSQL (docker-compose bunu sağlar)
docker compose up -d postgres redis
```

- [ ] `init_db()` ilk başlatmada tabloları + `clarere_app` rolünü + RLS policy'lerini oluşturur
- [ ] `clarere_app` (superuser olmayan) app bağlantısı RLS'ye tabidir — tenant izolasyonu gerçekten çalışır
- [ ] Demo kullanıcıları yalnızca `APP_ENV != production`'da seed edilir

## 4. Backend Deploy

```powershell
pip install -r requirements.txt
# Docker ile:
docker compose up -d --build clarere-api celery_worker
# veya manuel:
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 4000 --workers 4
```

- [ ] `/health` → `{"status":"ok","env":"production"}`
- [ ] `/docs` (Swagger) production'da kapatılabilir (opsiyonel)

## 5. Frontend Build + Deploy

```powershell
cd apps/frontend
npm install
npm run build          # production derlemesi
# Vercel / Node sunucu / static hosting'e deploy et
```

- [ ] `NEXT_PUBLIC_API_URL` backend'in gerçek adresine ayarlı
- [ ] Proxy (`next.config.ts`) `/api/*` → backend'e yönlendiriyor

## 6. Post-Launch Smoke Test

```powershell
# 1. Health
curl https://your-domain.com/api/health

# 2. JWT auth
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"sifre123"}'

# 3. JWT ile korumalı istek
curl https://your-domain.com/api/client/me \
  -H "Authorization: Bearer <token>"

# 4. Araştırma akışı (intake → research → synthesize → PDF)
# 5. Admin panel (X-Admin-Key ile)
```

## 7. Bilinen Kalan İşler (opsiyonel)

- [x] GitHub repo adı **`clarere`** olarak değiştirildi — README clone URL buna uygun
- [ ] Gözlemlenebilirlik: Langfuse (`docker compose --profile optional up -d langfuse-server`)
- [ ] Yerel Türkçe LLM geçişi (Enterprise yol haritası — `docs/god_doc.md`) şu an aktif değil
