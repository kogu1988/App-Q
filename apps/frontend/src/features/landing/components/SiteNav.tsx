"use client";

import Link from "next/link";

import Logo from "@/components/logo";

interface SiteNavProps {
  scrolled: boolean;
  navigateTo: (href: string) => void;
}

/** Üst gezinme çubuğu (refactor R4-1). */
export function SiteNav({ scrolled, navigateTo }: SiteNavProps) {
  return (
  <nav
    className={`fixed left-0 right-0 z-50 transition-all duration-300 mx-auto px-4 sm:px-6 ${
      scrolled
        ? "top-4 max-w-6xl bg-white/85 backdrop-blur-md border border-hairline/70 rounded-full shadow-lg"
        : "top-0 max-w-full bg-transparent border-transparent rounded-none shadow-none"
    }`}
  >
    <div className="max-w-6xl mx-auto h-16 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Logo size={32} strokeColor={scrolled ? "#17171c" : "#ffffff"} />
        <span
          className={`font-semibold text-base tracking-tight transition-colors duration-300 ${scrolled ? "text-primary" : "text-white"}`}
        >
          Clarere
        </span>
      </div>
      <div className="flex items-center gap-6">
        <div className="relative group hidden sm:block">
          <span className={`text-sm transition-colors duration-300 relative py-1 cursor-pointer flex items-center gap-1 ${scrolled ? "text-muted-text hover:text-primary" : "text-white/70 hover:text-white"}`}>
            Çözümler
            <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-coral transition-all duration-300 group-hover:w-full" />
          </span>
          <div className="absolute top-full left-1/2 -translate-x-1/2 mt-4 w-56 bg-white border border-hairline/70 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 flex flex-col p-2 z-[60] transform translate-y-2 group-hover:translate-y-0">
            <Link href="/agencies" className="px-3 py-2.5 text-sm text-ink/70 hover:text-primary hover:bg-stone/50 rounded-lg transition-colors font-medium">Ajanslar</Link>
            <Link href="/b2b-saas" className="px-3 py-2.5 text-sm text-ink/70 hover:text-primary hover:bg-stone/50 rounded-lg transition-colors font-medium">B2B SaaS</Link>
            <Link href="/consultants" className="px-3 py-2.5 text-sm text-ink/70 hover:text-primary hover:bg-stone/50 rounded-lg transition-colors font-medium">Danışmanlar</Link>
            <Link href="/growth-marketers" className="px-3 py-2.5 text-sm text-ink/70 hover:text-primary hover:bg-stone/50 rounded-lg transition-colors font-medium">Growth Marketers</Link>
            <Link href="/user-interviews" className="px-3 py-2.5 text-sm text-ink/70 hover:text-primary hover:bg-stone/50 rounded-lg transition-colors font-medium">Kullanıcı Görüşmeleri</Link>
            <Link href="/ab-testing" className="px-3 py-2.5 text-sm text-ink/70 hover:text-primary hover:bg-stone/50 rounded-lg transition-colors font-medium">A/B Test Simülasyonu</Link>
          </div>
        </div>
        <span
          onClick={() => navigateTo("/#pricing")}
          className={`text-sm transition-colors duration-300 hidden sm:block hover:opacity-100 relative group py-1 cursor-pointer ${scrolled ? "text-muted-text" : "text-white/70"}`}
          role="link"
        >
          Fiyatlandırma
          <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-coral transition-all duration-300 group-hover:w-full" />
        </span>
        <span
          onClick={() => navigateTo("/#faq")}
          className={`text-sm transition-colors duration-300 hidden sm:block hover:opacity-100 relative group py-1 cursor-pointer ${scrolled ? "text-muted-text" : "text-white/70"}`}
          role="link"
        >
          SSS
          <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-coral transition-all duration-300 group-hover:w-full" />
        </span>
        <Link
          href="/client"
          className={`btn-pill-primary text-sm transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu md:hover:scale-[1.02] md:active:scale-[0.98] ${
            scrolled
              ? "bg-primary text-white border-none"
              : "bg-white/15 text-white border border-white/35 backdrop-blur-sm"
          }`}
        >
          Giriş Yap
        </Link>
      </div>
    </div>
  </nav>
  );
}
