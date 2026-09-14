"use client";

import Logo from "@/components/logo";

interface SiteFooterProps {
  navigateTo: (href: string) => void;
}

/** Site alt bilgisi (refactor R4-1). */
export function SiteFooter({ navigateTo }: SiteFooterProps) {
  return (
  <footer className="border-t border-hairline bg-white py-8 px-6">
    <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <Logo size={24} className="text-muted-text" />
        <span className="text-sm text-muted-text">Clarere © 2026</span>
      </div>
      <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-text">
        <span onClick={() => navigateTo("/guide")} className="hover:text-ink transition-colors cursor-pointer" role="link">Kullanım Kılavuzu</span>
        <span onClick={() => navigateTo("/#faq")} className="hover:text-ink transition-colors cursor-pointer" role="link">SSS</span>
        <span onClick={() => navigateTo("/privacy")} className="hover:text-ink transition-colors cursor-pointer" role="link">Gizlilik</span>
        <span onClick={() => navigateTo("/terms")} className="hover:text-ink transition-colors cursor-pointer" role="link">Kullanım Koşulları</span>
      </div>
    </div>
  </footer>
  );
}
