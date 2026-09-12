import { NextRequest, NextResponse } from "next/server";

/**
 * proxy.ts — Next.js 16 proxy convention (middleware.ts'in yeni adı).
 *
 * Görevler:
 *   1. Kanonik host: www.clarere.com → clarere.com (301)
 *   2. Gizli rotalarda X-Robots-Tag: noindex, nofollow
 *   3. Derin bağlantı koruması: /client/* (kök hariç) oturum cookie'si ister
 *   4. Bilinen tarama/probe yollarını 404 ile keser
 *
 * ÖNEMLİ: `/client` kökü ASLA engellenmez — ilk kayıt (onboarding) orada olur.
 * Gerçek yetkilendirme API tarafındadır (JWT + admin key); proxy yalnızca
 * UX / defense-in-depth katmanıdır.
 */

const PRIVATE_PATHS = ["/admin", "/client", "/api"];

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

export function proxy(request: NextRequest) {
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

  // 3) Derin bağlantı koruması — `/client` kökü hariç
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

  // 2) Gizli rotalar indekslenmesin
  const response = NextResponse.next();
  if (PRIVATE_PATHS.some((p) => pathname.startsWith(p))) {
    response.headers.set("X-Robots-Tag", "noindex, nofollow");
  }
  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|og-image.svg|robots.txt|sitemap.xml).*)",
  ],
};
