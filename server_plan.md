# Clarere — Canlıya Geçiş Planı

> **Durum:** Uygulama planı. Sıra ile ilerlenir; her fazın sonunda doğrulama adımı vardır.
>
> **⚠️ Mimari güncellemesi (2026-09):** **Birincil plan = Oracle Cloud Always Free (tek ARM VM, tek-VM self-hosted).**
> Aşağıdaki netcup + Neon + Vercel planı **ikincil/yedek plan** olarak korunur (§1–§14).
>
> **Sorumluluk ayrımı:** 🔴 = kullanıcı yapmalı (hesap/DNS/ödeme, browser+kimlik gerektirir) · 🟢 = ajan SSH/terminal üzerinden yapabilir

---

## 0a. Birincil Plan — Oracle Cloud Always Free (tek VM)

**Neden:** Tek VM'de Postgres+pgvector, Redis, API, Celery, Caddy ve (opsiyonel) SearXNG birlikte çalışır;
ayrı managed servis (Neon/Upstash) gerekmez. Kod zaten env tabanlı olduğu için ileride parça parça
taşınabilir (Neon'a geçiş = sadece `POSTGRES_HOST` değişikliği).

**Kaynak ihtiyacı:** 2 OCPU / 12 GB ARM (Ampere A1, Always Free) rahat yeter; ayrıca 2–4 GB **swap** ekle.

### Kullanıcı adımları (🔴)

1. **Oracle Cloud hesabı** aç (Always Free uygun bölge seç: ör. Frankfurt/Amsterdam).
2. **Compute → Instance** oluştur:
   - Shape: **VM.Standard.A1.Flex** (2 OCPU / 12 GB) — ARM Ampere
   - Image: **Ubuntu 22.04 veya 24.04**
   - SSH anahtarını yükle (mevcut public key veya yeni üret)
3. **Reserved Public IP** ata (Always Free, kalıcı — ephemeral kullanma).
4. **Security List / NSG** — giriş portları: **22, 80, 443**.
5. (Opsiyonel) İlk girişte disk/swap ve `ufw` ayarı ajan tarafından yapılır.

### Kapasite hatası — "Out of host capacity" (🔴, uygulanacak)

> **Durum (2026-09):** Oracle Frankfurt'ta Ampere A1 (ARM, Always Free) kapasitesi **dolu**. Instance
> oluşturulamıyor. Aşağıdaki retry döngüsüyle boşalan kapasite otomatik yakalanır. **Bu blok tamamlanana
> kadar canlıya geçiş bekler; yerel geliştirme etkilenmez.**

**Yöntem: Oracle Cloud Shell** (yerelde SDK/API key/config GEREKMEZ; Cloud Shell'de `oci` CLI zaten
kurulu ve oturum yetkili).

1. **Cloud Shell aç:** Konsol sağ üstteki `>_` simgesi.
2. **ID'leri topla:**
   ```bash
   echo $OCI_TENANCY                                                   # compartment/tenancy
   oci iam availability-domain list --compartment-id $OCI_TENANCY \
     --query 'data[].name' --raw-output                                # AD adları (1-3)
   oci network subnet list --compartment-id $OCI_TENANCY \
     --display-name "public subnet-clarere-vcn" --query 'data[0].id' --raw-output   # subnet
   oci compute image list --compartment-id $OCI_TENANCY \
     --operating-system "Canonical Ubuntu" --shape "VM.Standard.A1.Flex" \
     --sort-by TIMECREATED --sort-order DESC \
     --query 'data[?"display-name"!=null].["display-name",id]' --output table | head -15   # image
   ```
3. **SSH public key yaz** (`launch_arm.sh` bunu `--ssh-authorized-keys-file` ile kullanır):
   ```bash
   mkdir -p ~/.ssh
   cat > ~/.ssh/instance_key.pub <<'EOF'
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIELHN1I7M6lXloAw20dR7naupagZbKb684g7XuhgxplK oguzk@ACER-Nitro5
   EOF
   ```
4. **Retry script** (`launch_arm.sh`) — AD'leri sırayla dener; **yalnızca "capacity" hatasında**
   döner (diğer hatada durur ve basar), başarıda RUNNING bekleyip **public IP** yazar:

   ```bash
   #!/bin/bash
   set -uo pipefail
   COMPARTMENT_ID="$OCI_TENANCY"
   SUBNET_ID="BURAYA_SUBNET_OCID"
   IMAGE_ID="BURAYA_IMAGE_OCID"
   SSH_KEY_PATH="$HOME/.ssh/instance_key.pub"
   DISPLAY_NAME="clarere"
   ADS=( "BURAYA_AD_1" "BURAYA_AD_2" "BURAYA_AD_3" )
   OCPUS=2; MEMORY=12; RETRY=60

   while true; do
     for AD in "${ADS[@]}"; do
       OUT=$(oci compute instance launch \
         --compartment-id "$COMPARTMENT_ID" --availability-domain "$AD" \
         --shape "VM.Standard.A1.Flex" \
         --shape-config "{\"ocpus\": $OCPUS, \"memoryInGBs\": $MEMORY}" \
         --subnet-id "$SUBNET_ID" --image-id "$IMAGE_ID" \
         --ssh-authorized-keys-file "$SSH_KEY_PATH" \
         --assign-public-ip true --display-name "$DISPLAY_NAME" 2>&1)
       STATUS=$?
       if [ $STATUS -eq 0 ]; then
         OCID=$(echo "$OUT" | grep -o 'ocid1.instance[^"]*' | head -1)
         echo "BASARILI ($AD): $OCID"
         for i in $(seq 1 40); do
           STATE=$(oci compute instance get --instance-id "$OCID" --query 'data."lifecycle-state"' --raw-output 2>/dev/null)
           [ "$STATE" = "RUNNING" ] && {
             VNIC=$(oci compute instance list-vnics --instance-id "$OCID" --query 'data[0].id' --raw-output)
             IP=$(oci network vnic get --vnic-id "$VNIC" --query 'data."public-ip"' --raw-output)
             echo "PUBLIC IP: $IP"; exit 0; }
           sleep 15
         done
         exit 0
       fi
       if echo "$OUT" | grep -qi "capacity"; then
         echo "[$(date +%H:%M:%S)] $AD dolu, ${RETRY}s sonra..."
       else
         echo "!!! KAPASITE DISI HATA - DURDURULDU !!!"; echo "$OUT"; exit 1
       fi
       sleep $RETRY
     done
   done
   ```
5. **Çalıştır:** `chmod +x launch_arm.sh && nohup ./launch_arm.sh > launch.log 2>&1 &` → `tail -f launch.log`

**Notlar / tuzaklar:**
- ⚠️ **Cloud Shell ~20 dk boşta kalınca oturumu kapatır** ve `nohup` işi ölür. Sekmeyi açık tut,
  arada Enter'a bas. Ölürse komutu tekrar çalıştır (kapasite yakalanmadıysa kayıp yok).
- **2 OCPU / 12 GB** Always Free'nin tam sınırı değil → sığması 4/24'ten çok daha kolay. Sığmazsa
  `OCPUS=1, MEMORY=6` dene (SearXNG o durumda kapatılır; 4 GB swap yeter).
- Instance açılınca **VCN Security List'e TCP 80 ve 443 ingress** ekle (ufw tek başına yetmez; Oracle
  VCN ayrı bir katmandır, varsayılan olarak yalnızca 22 açıktır).
- **Public IPv4** formda pasif kaldıysa: VCN'i ayrı oluşturup "select existing" ile seç, ya da
  instance'ı public IP'siz açıp sonra **Reserved public IP → Create → VNIC'e ata**.
- Otomatik retry yerine yerel Python/OCI SDK script'i de mümkündür (API key + `~/.oci/config` gerekir);
  Cloud Shell yolu SDK kurulumu gerektirmediği için tercih edildi.

### Ajan adımları (🟢 — SSH erişimi verildikten sonra)

6. Sistem güncelleme, 3–4 GB swap, Docker + compose kurulumu, `ufw allow 22/80/443`.
7. `git clone https://github.com/kogu1988/clarere.git /opt/clarere` + `.env` oluştur (`chmod 600`).
8. **Tek-VM stack:** `docker compose -f docker-compose.prod.yml up -d --build` (postgres+redis+api+celery+caddy+searxng),
   `Caddyfile` (prod) ile `clarere.com`/`api.clarere.com` + otomatik TLS.
9. `init_db()` migrationları, admin/secrets, `python scripts/setup_paddle_catalog.py` (webhook public URL ile).
10. Yedekleme cron'u (`scripts/backup_db.sh`) + Sentry/Resend anahtarları.
11. Uçtan uca doğrulama (§8) + Paddle webhook testi.

### Ajanın senden ihtiyaç duyduğu bilgiler (🔴 → 🟢)

- **VM public IP** (reserved) ve **SSH kullanıcı adı** (`ubuntu`)
- **SSH özel anahtarının bu makinedeki yolu** (anahtarı sohbete YAZMA; dosya olarak yerelde dursun)
- **DNS erişimi** (Squarespace) — `A` kayıtlarını sen mi ekleyeceksin, yoksa adımları mı vereyim?
- **Karar:** DB tek VM'de mi (öneri) yoksa Neon'da mı?
- **Sırlar:** `ADMIN_SECRET_KEY`, `JWT_SECRET`, `POSTGRES_PASSWORD` (yeni güçlü değerler; `.env`'e senin makinede yazılır)

### ARM uyumu notları

- Base image'lar multi-arch (`node:20-alpine`, `python:3.12-slim`, `pgvector/pgvector:pg16`, `redis`) → sorun beklenmiyor.
- Gerekirse build'de `--platform linux/arm64`.
- `psycopg2-binary`, `pillow`, `pyarrow` vb. arm64 wheel'leri mevcut.

---

## 0. Mimari Özet

```
                        ┌──────────────────────────────┐
   Kullanıcı ──HTTPS──▶ │  Vercel (Next.js, ücretsiz)  │
                        │  clarere.com / www           │
                        └──────────────┬───────────────┘
                                       │ /api/* rewrite (server-side)
                                       ▼
                        ┌──────────────────────────────┐
   Paddle webhook ─────▶│  netcup VPS (2 GB)           │
                        │  Caddy (TLS)                 │
                        │   └─ clarere-api:3000        │
                        │   └─ celery_worker           │
                        │   └─ redis:6379              │
                        │   └─ searxng:8080 (internal) │
                        │  api.clarere.com             │
                        └──────────────┬───────────────┘
                                       │ SSL (pooled)
                                       ▼
                        ┌──────────────────────────────┐
                        │  Neon PostgreSQL + pgvector  │
                        └──────────────────────────────┘
```

| Katman | Platform | Aylık maliyet |
|---|---|---|
| Frontend | Vercel Hobby | 0 (ücretsiz) |
| Backend + Celery + Redis + Caddy + SearXNG | netcup VPS nano G11s (2 vCore / 2 GB / 60 GB) | netcup fiyatı |
| PostgreSQL + pgvector | Neon Free | 0 (ücretsiz) |
| DNS | Squarespace | domain yenileme |
| Ödeme | Paddle | işlem başına komisyon |

**Sunucu kaynak bütçesi (~1.2–1.85 GB):** OS+Docker 250–300 MB · Redis 50–100 MB · FastAPI 300–500 MB · Celery 250–400 MB · Caddy 30–50 MB · SearXNG 300–500 MB → 2 GB + 3 GB swap ile **SearXNG dahil sığar**.

---

## 1. Ön Koşullar (kontrol listesi)

- [ ] 🔴 netcup hesabı + VPS nano G11s siparişi (Nuremberg, Ubuntu 24.04)
- [ ] 🔴 Neon hesabı (ücretsiz)
- [ ] 🔴 Vercel hesabı (GitHub ile giriş)
- [ ] 🔴 Squarespace DNS paneli erişimi (clarere.com)
- [ ] 🔴 GitHub repo erişimi (`kogu1988/clarere`)
- [ ] 🟢 Paddle sandbox katalogu — **TAMAMLANDI** (5 fiyat ID'si `.env`'de)
- [ ] 🔴 Paddle webhook secret (Faz 6'da oluşturulacak)
- [ ] 🔴 SSH anahtarı (VPS'e erişim için)

---

## 2. Faz 1 — Neon PostgreSQL 🟢/🔴

### 2.1 Proje oluştur (🔴 browser)

1. https://console.neon.tech → **New Project**
2. Ayarlar:
   - **Name:** `clarere`
   - **Region:** `AWS eu-central-1` (Frankfurt) — Nuremberg'e en yakın, düşük gecikme
   - **Postgres version:** 16 (pgvector uyumu için)
   - **Database name:** `clarere_db`
3. **Connection string**'i kopyala. İki tanesini de al:
   - **Pooled** (PgBouncer): host `...-pooler.eu-central-1.aws.neon.tech` → **uygulama için**
   - Direct: host `ep-xxx.eu-central-1.aws.neon.tech` → **migration/init için**

### 2.2 pgvector uzantısı (🔴 Neon SQL Editor)

`init_db()` uzantıyı oluşturmaya çalışır ama yetki sorunu olabilir. Önceden oluştur:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```
Beklenen: `vector | 0.7.x` (veya üzeri).

### 2.3 Bağlantı bilgilerini hazırla

`.env` içine (Faz 4'te sunucuya taşınacak):

```env
POSTGRES_HOST=<...-pooler.eu-central-1.aws.neon.tech>
POSTGRES_PORT=5432
POSTGRES_DB=clarere_db
POSTGRES_USER=<neon-rol>
POSTGRES_PASSWORD=<neon-sifre>

# Neon'da ayrı rol oluşturulamaz → aynı rolü app bağlantısı için de kullan
APP_DB_USER=<neon-rol>
APP_DB_PASSWORD=<neon-sifre>

# 2 GB sunucu + Neon bağlantı limiti → havuzu küçült
PG_POOL_MIN=1
PG_POOL_MAX=5
```

### 2.4 Doğrulama

```bash
python -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); \
c=psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT'), \
dbname=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'), \
password=os.getenv('POSTGRES_PASSWORD')); \
cur=c.cursor(); cur.execute('SELECT version()'); print(cur.fetchone()[0])"
```
Beklenen: PostgreSQL 16 sürüm satırı. Bağlantı reddedilirse `sslmode=require` eklenmeli.

> ⚠️ **Kritik not (kod değişikliği gerektirir):** `database.py` içindeki `_ensure_app_role()`
> `CREATE ROLE clarere_app ...` çalıştırır. Neon'da bu **başarısız olur**. Fonksiyonun
> hata verdiğinde **uyarı loglayıp devam etmesi** gerekir (aksi halde init_db çöker).
> `FORCE ROW LEVEL SECURITY` sayesinde tablo sahibi de policy'ye tabi olduğu için ayrı rol
> olmadan tenant izolasyonu çalışır.

---

## 3. Faz 2 — VPS Kurulum ve Sertleştirme 🟢

SSH ile bağlandıktan sonra (root):

### 3.1 Sistem güncelleme

```bash
apt update && apt upgrade -y
apt install -y curl git ufw fail2ban ca-certificates
```

### 3.2 Swap (3 GB) — zorunlu

```bash
fallocate -l 3G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
sysctl -w vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.conf
free -h   # Swap: 3.0Gi doğrula
```

### 3.3 Docker + Compose

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker --version && docker compose version
```

### 3.4 Firewall

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status verbose
```
> Postgres (5433), Redis (4006), SearXNG (4003), Backend (4000) portları **dışa açılmaz** —
> hepsi Docker iç ağında kalır, yalnızca Caddy 80/443 dinler.

### 3.5 Proje dizini

```bash
mkdir -p /opt/clarere && cd /opt/clarere
git clone https://github.com/kogu1988/clarere.git .
```

### 3.6 Doğrulama

```bash
docker run --rm hello-world | tail -3
swapon --show
ss -tlnp | grep -E ':(80|443|22)\b'
```

---

## 4. Faz 3 — DNS Kayıtları (Squarespace) 🔴

Squarespace → Domainler → clarere.com → **DNS Settings**.

| Tip | Host | Değer | Amaç |
|---|---|---|---|
| A | `api` | `<VPS_IP>` | Backend + Paddle webhook |
| A | `@` | Vercel talimatı (ör. `76.76.21.21`) | Frontend kök |
| CNAME | `www` | `cname.vercel-dns.com` | Frontend www |

> `@` ve `www` değerlerini Vercel projesini ekledikten sonra Vercel'in "Domains"
> ekranının verdiği **tam değerlerle** gir (Vercel sana kesin hedefi söyler).
> TTL: varsayılan (3600).

### Doğrulama

```bash
nslookup api.clarere.com
nslookup clarere.com
```
`api` → VPS IP dönmeli. DNS yayılımı 5 dk – 24 saat sürebilir.

---

## 5. Faz 4 — Backend Deploy (Docker Stack) 🟢

### 5.1 Sunucuda `.env` oluştur

`/opt/clarere/.env` (asla commit edilmez):

```env
# ── Ortam ──
APP_ENV=production
ALLOWED_ORIGINS=https://clarere.com,https://www.clarere.com

# ── Güvenlik (production'da ZORUNLU) ──
JWT_SECRET=<openssl rand -base64 48>
ADMIN_SECRET_KEY=<openssl rand -base64 48>

# ── DeepSeek ──
DEEPSEEK_API_KEY=<mevcut anahtar>
DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro
DEEPSEEK_TIMEOUT=90
DEEPSEEK_MAX_RETRIES=3
RESEARCH_DEADLINE_SECONDS=300
THREADPOOL_SIZE=32

# ── Neon PostgreSQL ──
POSTGRES_HOST=<...-pooler.eu-central-1.aws.neon.tech>
POSTGRES_PORT=5432
POSTGRES_DB=clarere_db
POSTGRES_USER=<neon-rol>
POSTGRES_PASSWORD=<neon-sifre>
APP_DB_USER=<neon-rol>
APP_DB_PASSWORD=<neon-sifre>
PG_POOL_MIN=1
PG_POOL_MAX=5

# ── Redis (Docker iç ağı) ──
REDIS_HOST=redis
REDIS_PORT=6379
VALKEY_URL=redis://redis:6379/0
CELERY_CONCURRENCY=1

# ── Paddle (sandbox → canlıda production anahtarları) ──
PADDLE_ENV=sandbox
PADDLE_API_KEY=<sandbox veya live anahtar>
PADDLE_PRICE_STARTER_MONTHLY=pri_01m2b36gdt2tym30cqp13cqbdg
PADDLE_PRICE_STARTER_ANNUAL=pri_01m2b36ha49sxq7hwdas1j59vh
PADDLE_PRICE_PRO_MONTHLY=pri_01m2b36k59dm780nx7cxjskbb4
PADDLE_PRICE_PRO_ANNUAL=pri_01m2b36m1cd4xr8jqhjr2ye9bn
PADDLE_PRICE_FLEX=pri_01m2b36nx6ptyyp9zt4gp6jhjd
PADDLE_WEBHOOK_SECRET=<Faz 6'da doldurulacak>

# ── Token muhasebesi fiyatları (USD/1M token — DeepSeek fiyat sayfasından) ──
DEEPSEEK_PRICE_FLASH_INPUT=0
DEEPSEEK_PRICE_FLASH_OUTPUT=0
DEEPSEEK_PRICE_FLASH_CACHE_HIT=0
DEEPSEEK_PRICE_PRO_INPUT=0
DEEPSEEK_PRICE_PRO_OUTPUT=0
DEEPSEEK_PRICE_PRO_CACHE_HIT=0
```

```bash
chmod 600 /opt/clarere/.env
```

### 5.2 `docker-compose.cloud.yml` oluştur

> **Not:** `docker-compose.prod.yml` (tek-sunucu/self-hosted) ve `docker-compose.local.yml`
> **korunmuştur** — yerel Docker geliştirmesi onları kullanmaya devam eder. Bu bölümdeki
> dosya yalnızca **Vercel + Neon** bulut dağıtımı içindir.

Postgres **çıkarıldı** (Neon), Caddy **eklendi**, portlar dışa kapatıldı.

```yaml
services:
  redis:
    image: redis:7.2-alpine
    container_name: clarere-redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits: { cpus: '0.5', memory: 256M }
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  searxng:
    image: searxng/searxng:latest
    container_name: clarere-searxng
    volumes:
      - searxng_data:/etc/searxng
    environment:
      - SEARXNG_BASE_URL=https://api.clarere.com/
    restart: unless-stopped
    deploy:
      resources:
        limits: { cpus: '0.5', memory: 400M }

  clarere-api:
    build:
      context: .
      dockerfile: ./apps/backend/Dockerfile
    container_name: clarere-api
    env_file: [.env]
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - VALKEY_URL=redis://redis:6379/0
      - SEARXNG_URL=http://searxng:8080
    expose: ["3000"]
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits: { cpus: '1.0', memory: 700M }

  celery_worker:
    build:
      context: .
      dockerfile: ./apps/backend/Dockerfile
    container_name: clarere-celery-worker
    command: celery -A packages.research_engine.celery_app worker --loglevel=info --concurrency=1
    env_file: [.env]
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - VALKEY_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits: { cpus: '0.5', memory: 500M }

  caddy:
    image: caddy:2-alpine
    container_name: clarere-caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile.cloud:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on: [clarere-api]
    restart: unless-stopped

volumes:
  redis_data:
  searxng_data:
  caddy_data:
  caddy_config:
```

### 5.3 `Caddyfile.cloud` oluştur

> Not: `docker-compose.prod.yml` + `docker-compose.local.yml` + `Caddyfile` + `Caddyfile.local`
> dosyaları **yerel Docker geliştirme ve tek-sunucu (self-hosted) senaryosu** için korunmuştur.
> Bulut dağıtımı (Vercel + Neon) `docker-compose.cloud.yml` + `Caddyfile.cloud` kullanır.

```caddy
api.clarere.com {
	encode gzip
	request_body {
		max_size 10MB
	}
	reverse_proxy clarere-api:3000
	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		X-Content-Type-Options "nosniff"
		X-Frame-Options "DENY"
		Referrer-Policy "strict-origin-when-cross-origin"
		-Server
	}
	log {
		output file /data/access.log {
			roll_size 20mb
			roll_keep 5
		}
	}
}
```

> Caddy, `api.clarere.com` için Let's Encrypt sertifikasını **otomatik** alır ve yeniler.
> DNS `api` kaydı yayıldıktan sonra ilk istekte sertifika üretilir.
> Paddle webhook gövdesi **değiştirilmeden** iletilir (imza doğrulaması bozulmaz).

### 5.4 Build & başlat

```bash
cd /opt/clarere
docker compose -f docker-compose.cloud.yml build
docker compose -f docker-compose.cloud.yml up -d
docker compose -f docker-compose.cloud.yml ps
```

### 5.5 Doğrulama

```bash
curl -s https://api.clarere.com/health
# Beklenen: {"status":"ok","env":"production"}

docker compose -f docker-compose.cloud.yml logs --tail=50 clarere-api
docker stats --no-stream
free -h
```
- `/health` 200 dönmeli.
- `clients` tablosu Neon'da oluşmuş olmalı (init_db migrationları çalıştı).
- Bellek kullanımı 1.8 GB altında olmalı.

---

## 6. Faz 5 — Frontend (Vercel) 🔴/🟢

### 6.1 Kod değişikliği (🟢 — deploy öncesi)

`apps/frontend/next.config.ts` içindeki rewrite hedefi **env ile** verilecek şekilde değişir:

```ts
destination: `${process.env.API_PROXY_TARGET ?? "http://127.0.0.1:4000"}/api/:path*`
```

CSP `connect-src` listesine `https://api.clarere.com` eklenir:

```
"connect-src 'self' https://api.clarere.com http://localhost:* ws://localhost:* ..."
```

> Not: Vercel'de rewrite **server-side** çalıştığı için CORS gerekmez ve
> `X-Username`/`Authorization` header'ları korunur. Yine de doğrulama gerekir
> (aşağıda 6.4).

### 6.2 Vercel projesi

1. https://vercel.com/new → GitHub → `kogu1988/clarere` import et
2. **Root Directory:** `apps/frontend`
3. Framework: Next.js (otomatik algılanır)
4. Environment Variables:

```env
API_PROXY_TARGET=https://api.clarere.com
NEXT_PUBLIC_PADDLE_ENV=sandbox
NEXT_PUBLIC_PADDLE_CLIENT_TOKEN=<Paddle client token>
```
5. Deploy

### 6.3 Domain bağlama

Vercel → Project → Settings → Domains → `clarere.com` ve `www.clarere.com` ekle.
Vercel'in verdiği **A/CNAME değerlerini** Faz 3'teki Squarespace kayıtlarına yaz.

### 6.4 Doğrulama

- [ ] https://clarere.com açılıyor, SSL otomatik
- [ ] Kayıt ol → `/client` dashboard yükleniyor
- [ ] `/api/client/me` çağrısı Vercel proxy'sinden geçip 200 dönüyor
- [ ] DeepSeek ile Defne sohbeti çalışıyor (gerçek API)
- [ ] **SSE (`/interviews/stream`) streaming** Vercel proxy'sinden akıyor
      → Eğer buffer'lanıyorsa alternatif: frontend doğrudan `https://api.clarere.com`
      çağırır ve `ALLOWED_ORIGINS`'e `https://clarere.com` eklenir (CORS).
- [ ] Paddle checkout overlay açılıyor (sandbox, test kartı `4242 4242 4242 4242`)

---

## 7. Faz 6 — Paddle Webhook Canlı 🟢/🔴

### 7.1 Destination oluştur (🟢 — ajan, script ile)

`.env` içine ekle:
```env
PADDLE_WEBHOOK_URL=https://api.clarere.com/api/billing/webhook
```
Sonra çalıştır:
```bash
python scripts/setup_paddle_catalog.py
```
Bu, `Clarere — webhook` destination'ını oluşturur ve `PADDLE_WEBHOOK_SECRET`
(`pdl_ntfset_...`) değerini basar. **Secret yalnızca oluşturma anında gösterilir** →
hemen `.env`'e yaz ve backend'i yeniden başlat:
```bash
docker compose -f docker-compose.cloud.yml up -d --force-recreate clarere-api
```

### 7.2 Doğrulama

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://api.clarere.com/api/billing/webhook
# Beklenen: 400 (imzasız istek reddedilir — doğru davranış)
```
- [ ] 🔴 Paddle Dashboard → Developer Tools → Notifications → **simulator** ile
      `subscription.created` gönder → destination'a 200 iletildi mi?
- [ ] Test kullanıcıyla checkout → `clients.plan_type` güncellendi mi?
- [ ] Aynı webhook 2 kez gönderilince ikincisi `duplicate_ignored` (idempotensi)

### 7.3 Canlıya geçiş (🔴)

Sandbox doğrulandıktan sonra:
1. Paddle **live** hesapta aynı 3 ürün + 5 fiyatı oluştur (ürün adlarını **`Clarere — `**
   önekiyle** aç → diğer projeyle karışmaz)
2. Ayrı bir live notification destination + secret
3. `.env`'de `PADDLE_ENV=production`, live `PADDLE_API_KEY`, live `PADDLE_PRICE_*`, live secret
4. Backend'i yeniden başlat
5. `POST /api/client/upgrade-plan` production'da kapalıdır (kontrol: 403 dönmeli)

---

## 8. Faz 7 — Uçtan Uca Doğrulama

| # | Senaryo | Beklenen |
|---|---|---|
| 1 | `GET /health` | `{"status":"ok","env":"production"}` |
| 2 | Kayıt + giriş | JWT üretilir, `/client` açılır |
| 3 | Defne ile brief | Flash modeli yanıt verir, brief dolar |
| 4 | Araştırma çalıştır | N persona, batch mülakat, ~30–60 sn |
| 5 | Sentez raporu | Rapor üretilir, PDF (Pro/Flex) iner |
| 6 | Plan gate | Free kullanıcı Pro özelliğinde 403 + upgrade CTA |
| 7 | Kota | Free 1 araştırma sonrası 2.'de 403 |
| 8 | Token bütçesi | Aşımda 429 `TOKEN_BUDGET_EXCEEDED` |
| 9 | Admin paneli | `X-Admin-Key` ile `/api/admin/clients` 200; yanlış key 403 |
| 10 | Admin koruması | Key yok + `APP_ENV=production` → 503 |
| 11 | Paddle checkout | Test kartı ile plan yükselir |
| 12 | Paddle webhook | İmzasız 400, doğru imza 200 |
| 13 | Eşzamanlılık (P0-1) | 1 araştırma sürerken başka istemci `/me`'yi <500 ms alır |
| 14 | Celery | `/studio/simulate` → worker işler, status SUCCESS |
| 15 | Yeniden başlatma | `docker compose restart` sonrası her şey ayağa kalkar |

---

## 9. Faz 8 — Lansman Sonrası

### 9.1 Yedekleme (acil)

Neon free tier'da otomatik yedek geçmişi sınırlıdır. Sunucuda günlük `pg_dump`:

```bash
# /opt/clarere/backup.sh
#!/usr/bin/env bash
set -euo pipefail
mkdir -p /opt/clarere/backups
pg_dump "$DATABASE_URL" | gzip > "/opt/clarere/backups/clarere-$(date +%F).sql.gz"
find /opt/clarere/backups -name '*.sql.gz' -mtime +14 -delete
```
```bash
chmod +x /opt/clarere/backup.sh
# crontab -e → 03:30 her gün
30 3 * * * /opt/clarere/backup.sh >> /var/log/clarere-backup.log 2>&1
```

### 9.2 İzleme

- **Sentry** (önerilir): backend'e `sentry-sdk[fastapi]`, frontend'e `@sentry/nextjs`.
  `SENTRY_DSN` env ile. P0-5 retry logları ile birlikte hata görünürlüğü sağlar.
- **Uptime:** `/health` için harici uptime kontrolü (ücretsiz: UptimeRobot/BetterStack).
- **Log rotasyonu:** Caddy `/data/access.log` zaten rotate ediyor; `docker compose logs` için `max-size` eklenebilir.

### 9.3 E-posta (Resend)

- Resend'de `clarere.com` domainini doğrula → Squarespace DNS'e **SPF + DKIM** kayıtları.
- Kullanım: şifre sıfırlama, iletişim formu bildirimi (`hiclarere@clarere.com`),
  dönem sonu/ödeme uyarıları.
- Env: `RESEND_API_KEY`, `RESEND_FROM=Clarere <hiclarere@clarere.com>`

### 9.4 Opsiyonel iyileştirmeler

- **Cloudflare** (DNS/CDN/WAF) — Squarespace DNS yerine. `api` kaydını **DNS-only** (proxy kapalı)
  bırak, aksi halde Paddle webhook IP'leri sorun çıkarabilir.
- **Cloudflare R2 / S3** — PDF'leri VPS diskinden çıkarmak (çok instance'a geçilirse şart).
- **Neon paid plan** — PITR ve daha yüksek compute limiti.
- **Hetzner/netcup yükseltme** — 4 GB'a çıkış, Celery concurrency artışı.

---

## 10. Deploy Öncesi Kod Değişiklikleri (blocker listesi)

| # | Dosya | Değişiklik | Neden |
|---|---|---|---|
| 1 | `packages/research_engine/database.py` | `_ensure_app_role()` hata verirse **uyarı loglayıp devam etsin** | Neon `CREATE ROLE` desteklemez |
| 2 | `apps/frontend/next.config.ts` | Rewrite hedefi `API_PROXY_TARGET` env'inden | Vercel'de localhost:4000 geçersiz |
| 3 | `apps/frontend/next.config.ts` | CSP `connect-src`'e `https://api.clarere.com` | API çağrıları engellenmesin |
| 4 | `docker-compose.cloud.yml` *(yeni)* | Postgres'siz, Caddy'li, portsuz stack | Production topolojisi |
| 5 | `Caddyfile.cloud` *(yeni)* | `api.clarere.com` + otomatik SSL | TLS + reverse proxy |
| 6 | `.env.production.example` *(yeni)* | Sunucu env şablonu (secretsiz) | Kurulum kolaylığı |
| 7 | `apps/backend/Dockerfile` | `.dockerignore` kontrolü (node_modules, data) | Build boyutu/RAM |
| 8 | `packages/research_engine/database.py` | Neon için `sslmode` desteği (gerekirse DSN'e ekle) | Neon SSL zorunlu |

---

## 11. Ortam Değişkenleri Referansı (production)

| Değişken | Zorunlu | Not |
|---|:---:|---|
| `APP_ENV` | ✅ | `production` (JWT/ALLOWED_ORIGINS guard'larını açar) |
| `JWT_SECRET` | ✅ | min 32 karakter; yoksa uygulama **başlamaz** |
| `ADMIN_SECRET_KEY` | ✅ | yoksa admin API **503** |
| `ALLOWED_ORIGINS` | ✅ | `https://clarere.com,https://www.clarere.com` |
| `DEEPSEEK_API_KEY` | ✅ | Flash + Pro |
| `POSTGRES_*` / `APP_DB_*` | ✅ | Neon pooled host |
| `PG_POOL_MAX` | ✅ | **5** (Neon bağlantı limiti) |
| `VALKEY_URL` / `REDIS_*` | ✅ | `redis://redis:6379/0` |
| `CELERY_CONCURRENCY` | ✅ | **1** (2 GB sunucu) |
| `PADDLE_*` | ✅ | `PADDLE_WEBHOOK_SECRET` olmadan webhook reddedilir |
| `THREADPOOL_SIZE` | ➖ | 32 (2 vCore için) |
| `RESEARCH_DEADLINE_SECONDS` | ➖ | 300 |
| `DEEPSEEK_PRICE_*` | ➖ | Maliyet muhasebesi doğruluğu için doldur |

---

## 12. Sorun Giderme

| Belirti | Olası neden | Çözüm |
|---|---|---|
| `/health` 502 | API konteyneri ayakta değil | `docker compose logs clarere-api` |
| Sertifika alınamıyor | `api` A kaydı yayılmamış / 80 kapalı | `nslookup api.clarere.com`, `ufw status` |
| DB bağlantı hatası | Neon host/ssl | `sslmode=require` ekle, pooled host kullan |
| `CREATE ROLE` hatası | Neon kısıtı | `_ensure_app_role` non-fatal yap (Bölüm 10/1) |
| `too many connections` | Havuz + Celery | `PG_POOL_MAX=5`, `CELERY_CONCURRENCY=1` |
| OOM-kill | Bellek sınırı | Swap kontrol, SearXNG'yi kapat, limitleri düşür |
| Vercel'de `/api/*` 404 | `API_PROXY_TARGET` yanlış | Vercel env'i kontrol et, redeploy |
| Paddle webhook 400 | Secret yanlış / gövde değişmiş | Secret'ı yenile, Caddy'de gövdeyi dönüştürme |
| SSE buffer'lanıyor | Vercel proxy | Doğrudan API + CORS alternatifine geç |
| İlk istek yavaş | Neon autosuspend | Kabul edilebilir (~1 sn); paid plan ile kalkar |

---

## 13. Geri Alma (Rollback)

1. **Kod:** `git -C /opt/clarere log --oneline -5` → `git checkout <önceki_sha>` → `docker compose -f docker-compose.cloud.yml up -d --build`
2. **Frontend:** Vercel → Deployments → önceki deployment → **Promote to Production**
3. **DB:** Neon → Branches/Restore (paid plan'da PITR; free'de günlük `pg_dump` yedeğinden geri yükle)
4. **DNS:** Squarespace'te kaydı eski IP'ye çevir (TTL nedeniyle ~1 saat gecikme olabilir)

> **Asla:** `.env` dosyasını commit etme · `PADDLE_API_KEY` / `JWT_SECRET` / Neon şifresini
> log veya sohbete yazma · `admin` endpoint'lerini `ADMIN_SECRET_KEY` olmadan production'da açma.

---

## 14. Faz Özeti ve Süre Tahmini

| Faz | İçerik | Kim | Süre |
|---|---|---|---|
| 2 | Neon kurulum + pgvector | 🔴 + 🟢 | 20 dk |
| 3 | VPS kurulum + swap + docker + firewall | 🟢 | 30 dk |
| 4 | DNS kayıtları | 🔴 | 10 dk (+yayılım) |
| 5 | Backend deploy (compose + caddy) | 🟢 | 45 dk |
| 6 | Frontend Vercel | 🔴 + 🟢 | 30 dk |
| 7 | Paddle webhook canlı | 🟢 + 🔴 | 20 dk |
| 8 | Uçtan uca doğrulama | 🟢 | 30 dk |
| 9 | Yedekleme + izleme (Sentry/Resend) | 🟢 + 🔴 | 1–2 saat |

**Toplam (kritik yol):** ~3–4 saat aktif çalışma + DNS yayılım süresi.

---

*Clarere — Vercel + netcup VPS + Neon + Redis (Docker) + Paddle*
*Bu dosya canlıya geçiş sırasında güncellenmelidir.*
