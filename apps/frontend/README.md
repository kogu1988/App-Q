# Clarere — Frontend

Clarere’nin Next.js tabanlı web arayüzü. Landing sayfaları, müşteri paneli, araştırma sihirbazı ve yönetici panelini içerir.

## Teknoloji

- **Next.js 16** (App Router, Turbopack)
- **React 19** + **TypeScript** (strict)
- **Tailwind CSS 4**
- **shadcn/ui** + Base UI bileşenleri
- **recharts** (rapor grafikleri), **sonner** (bildirimler)

## Geliştirme

Bağımlılıkları kur:

```bash
npm ci
```

Geliştirme sunucusu (port **4001**):

```bash
npm run dev
```

> Port `4001` sabittir ve backend proxy’si buna göre yapılandırılmıştır. Varsayılan Next.js `3000` portu kullanılmaz.

Diğer komutlar:

```bash
npm run build     # production build
npm start         # production sunucu
npm run lint      # eslint
npx tsc --noEmit  # tip kontrolü
```

## Ortam Değişkenleri

`next.config.ts` içindeki rewrite kuralları `/api/*` isteklerini backend’e yönlendirir.

| Değişken | Amaç |
|---|---|
| `API_PROXY_TARGET` | Backend hedefi (derleme zamanı build arg). Örn. `http://localhost:4000` |
| `NEXT_PUBLIC_PADDLE_ENV` | Paddle.js ortamı (`sandbox` \| `production`) |
| `NEXT_PUBLIC_PADDLE_CLIENT_TOKEN` | Paddle.js client token (yayımlanması güvenlidir) |

> **Not:** `API_PROXY_TARGET` bir **build arg**’dır; `next.config.ts` rewrite’ları derleme anında gömülür ve çalışma zamanı ortam değişkeninden etkilenmez. Değiştirince yeniden derlemek gerekir.

## Yapı

```
src/
├── app/
│   ├── page.tsx                 Landing + fiyatlandırma + SSS + iletişim
│   ├── layout.tsx               Kök layout, metadata, JSON-LD, Paddle.js
│   ├── client/                  Müşteri paneli
│   │   ├── page.tsx             Dashboard
│   │   ├── new/page.tsx         Araştırma sihirbazı (Defne → Research)
│   │   ├── studies/[id]/page.tsx Çalışma detay + rapor
│   │   └── upgrade/page.tsx     Plan yükseltme (Paddle checkout)
│   ├── admin/page.tsx           Operatör paneli
│   └── {agencies,b2b-saas,...}  SEO landing sayfaları
├── components/                  Paylaşılan bileşenler (plan-gate, logo, admin/*)
├── hooks/                       use-client-plan vb.
└── lib/                         auth, paddle, yardımcılar
```

## Auth

Geliştirmede `X-Username` header’ı kullanılır. Token varsa `Authorization: Bearer <JWT>` de gönderilir. Production’da JWT zorunludur.

## Docker

Yerel tam yığın (önerilen) proje kökünden:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml up -d --build
```

Frontend `http://localhost:4001`, tam yığın (Caddy) `http://localhost:8080`.

## Test

E2E testleri kök dizindeki `e2e/` klasöründedir (ayrı `package.json`):

```bash
cd ../e2e && npx playwright test
```

Docker yığını çalışıyor olmalıdır.
