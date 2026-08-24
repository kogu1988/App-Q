# Clarere — Hetzner Deploy Runbook (clarere.com)

> Production deploy için adım adım. Hedef: Hetzner sunucuda Docker ile, `clarere.com` → Caddy (otomatik HTTPS) → frontend + backend.

## 0. Ön Koşullar

- Hetzner sunucu (Ubuntu/Debian önerilir), root/ssh erişimi
- `clarere.com` domaini — DNS A kaydı sunucunun IP'sine yönlendirilmeli (ve `www`)
- Docker + Docker Compose v2 kurulu
- 80 ve 443 portları açık (firewall/security group)

## 1. DNS Ayarı (Hetzner DNS veya domain sağlayıcı)

```
A   clarere.com    → <sunucu-IP>
A   www.clarere.com → <sunucu-IP>
```

## 2. Sunucuda Depoyu Klonla

```bash
git clone https://github.com/kogu1988/App-Q.git clarere
cd clarere
```

## 3. `.env` Oluştur (production)

```bash
cp .env.example .env
nano .env
```

Kritik değerleri doldur:

```env
APP_ENV=production

DEEPSEEK_API_KEY=sk-...              # gerçek anahtar
DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro

POSTGRES_PASSWORD=<güçlü-şifre>      # zorunlu
POSTGRES_USER=clarere_user
POSTGRES_DB=clarere_db

APP_DB_USER=clarere_app
APP_DB_PASSWORD=<güçlü-şifre>        # RLS app rolü

ADMIN_SECRET_KEY=<rastgele-uzun>     # admin API
JWT_SECRET=<rastgele-uzun>           # JWT imzalama
ALLOWED_ORIGINS=https://clarere.com  # CORS — production'da ZORUNLU
```

> ⚠️ `APP_ENV=production` iken `ALLOWED_ORIGINS` boşsa backend `RuntimeError` ile açılmaz.
> ⚠️ `APP_ENV=production` iken `X-Username` header auth'u KAPALIDIR — yalnızca JWT (`Authorization: Bearer`) çalışır.

## 4. Build + Deploy

```bash
# Tüm servisleri build et ve başlat (frontend dahil)
docker compose -f docker-compose.prod.yml up -d --build
```

Servisler:
- `caddy` — public giriş (80/443), otomatik Let's Encrypt HTTPS
- `frontend` — Next.js standalone (3000, internal)
- `clarere-api` — FastAPI (3000, internal)
- `postgres` + `redis` + `searxng` + `celery_worker` — internal

## 5. İlk Başlatma

`clarere-api` ilk başlatmada `init_db()` çalıştırır: tablolar + `clarere_app` rolü + RLS policy'leri + demo kullanıcılar (production'da demo seed edilmez).

```bash
# Logları izle
docker compose -f docker-compose.prod.yml logs -f clarere-api
```

## 6. Doğrulama

```bash
# 1. Health
curl https://clarere.com/api/health
# → {"status":"ok","env":"production"}

# 2. JWT register (production'da X-Username ÇALIŞMAZ, JWT şart)
curl -X POST https://clarere.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ilk-kullanici","password":"guclu-sifre"}'

# 3. Login + korumalı istek
TOKEN=$(curl -s -X POST https://clarere.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ilk-kullanici","password":"guclu-sifre"}' | jq -r .access_token)

curl https://clarere.com/api/client/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Frontend
curl -I https://clarere.com/   # → 200
```

## 7. Admin Panel

- `/admin` → tarayıcıda aç, header'daki "Admin anahtarı" alanına `ADMIN_SECRET_KEY`'i gir + Kaydet.
- Admin API istekleri artık `X-Admin-Key` ile korunur.

## 8. Güncelleme (yeni kod push'landığında)

```bash
cd clarere
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## 9. Sorun Giderme

| Belirti | Çözüm |
|---|---|
| Backend açılmıyor, `ALLOWED_ORIGINS` hatası | `.env`'de `ALLOWED_ORIGINS=https://clarere.com` set et |
| HTTPS yok | DNS A kaydı doğru mu? 443 portu açık mı? Caddy loglarını kontrol et |
| `GET /studies` boş | RLS aktif; kullanıcı kendi study'sini görür. Demo kullanıcı üretimde seed edilmez |
| SearXNG hata | Web doğrulama mock'a düşer (graceful); SearXNG konteynerini kontrol et |
| PDF hata | `markdown`/`xhtml2pdf` kurulu mu? (backend imajında requirements.txt'den kurulur) |

## 10. Yedekleme (opsiyonel)

```bash
# PostgreSQL dump
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U clarere_user clarere_db > backup.sql
```
