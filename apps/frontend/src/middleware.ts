import { NextRequest, NextResponse } from "next/server";

/**
 * middleware.ts — Gizli rotalar için X-Robots-Tag header enjeksiyonu
 *
 * robots.ts Googlebot'u kurallarla yönlendirir.
 * Bu middleware ise HTTP seviyesinde tüm crawler'lara
 * "noindex, nofollow" header'ı ekler — robots.txt'i atlayan botlara karşı ek katman.
 */

const PRIVATE_PATHS = ["/admin", "/client", "/api"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Gizli rota kontrolü
  const isPrivate = PRIVATE_PATHS.some((p) => pathname.startsWith(p));

  const response = NextResponse.next();

  if (isPrivate) {
    // Arama motorlarına: indexleme ve takip etme
    response.headers.set("X-Robots-Tag", "noindex, nofollow");
  }

  return response;
}

export const config = {
  // API route'larını ve static dosyaları atla
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|og-image.png|robots.txt|sitemap.xml).*)",
  ],
};
