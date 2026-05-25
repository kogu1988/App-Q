import { NextRequest, NextResponse } from "next/server";

/**
 * proxy.ts - Next.js 16 proxy convention
 * Gizli rotalar icin X-Robots-Tag header enjeksiyonu
 */

const PRIVATE_PATHS = ["/admin", "/client", "/api"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPrivate = PRIVATE_PATHS.some((p) => pathname.startsWith(p));
  const response = NextResponse.next();
  if (isPrivate) {
    response.headers.set("X-Robots-Tag", "noindex, nofollow");
  }
  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|og-image.svg|robots.txt|sitemap.xml).*)",
  ],
};
