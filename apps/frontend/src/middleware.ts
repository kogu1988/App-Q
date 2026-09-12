import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Clarere — Edge middleware.
 *
 * Amaçlar:
 *   1. Kanonik host: www.clarere.com → clarere.com (301)
 *   2. Derin bağlantı koruması: /client/* altında dosya olmadan gelenler /client'e
 *      yönlendirilir (oturum modali orada açılır).
 *   3. Arama motoru indekslemeden koruma: /client ve /admin noindex.
 *   4. Bilinen tarama/probe yollarını 404 ile kesme.
 *
 * ÖNEMLİ: `/client` kökü ASLA engellenmez — ilk kayıt (onboarding) orada olur.
 * Gerçek yetkilendirme API tarafındadır (JWT + admin key); middleware yalnızca
 * UX/defense-in-depth katmanıdır.
 */

const PROBE_PATHS = [
  "/.env",
  "/.git",
  "/wp-admin",
  "/wp-login.php",
  "/phpmyadmin",
  "/xmlrpc.php",
];

// Oturum işareti — hassas veri içermez, yalnızca "bu tarayıcı giriş yaptı" bilgisi.
const SESSION_COOKIE = "clarere_session";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const host = request.headers.get("host") ?? "";

  // 1) Kanonik host (yalnızca production alan adında)
  if (host.startsWith("www.clarere.com")) {
    const url = request.nextUrl.clone();
    url.host = "clarere.com";
    url.protocol = "https:";
    return NextResponse.redirect(url, 301);
  }

  // 4) Bilinen probe yolları
  if (PROBE_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return new NextResponse("Not Found", { status: 404 });
  }

  // 2) Derin bağlantı koruması — `/client` kökü hariç
  if (pathname !== "/client" && pathname.startsWith("/client")) {
    const hasSession = Boolean(request.cookies.get(SESSION_COOKIE)?.value);
    if (!hasSession) {
      const planParam = request.nextUrl.searchParams.get("plan");
      const url = request.nextUrl.clone();
      url.pathname = "/client";
      url.search = planParam ? `?plan=${encodeURIComponent(planParam)}` : "";
      return NextResponse.redirect(url);
    }
  }

  const response = NextResponse.next();

  // 3) Panel sayfaları indekslenmesin
  if (pathname.startsWith("/client") || pathname.startsWith("/admin")) {
    response.headers.set("X-Robots-Tag", "noindex, nofollow");
  }

  return response;
}

export const config = {
  matcher: [
    "/client/:path*",
    "/admin/:path*",
    "/.env",
    "/.git/:path*",
    "/wp-admin/:path*",
    "/wp-login.php",
    "/phpmyadmin/:path*",
    "/xmlrpc.php",
  ],
};
