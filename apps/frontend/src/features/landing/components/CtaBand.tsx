"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Reveal } from "@/features/landing/hooks/use-reveal";

/** Alt CTA bandı (refactor R4-1). */
export function CtaBand() {
  return (
  <section className="band-primary py-20 px-6">
    <div className="max-w-3xl mx-auto text-center">
      <Reveal>
        <p className="mono-label text-white/40 mb-6">Başlamak için hazır mısın?</p>
        <h2 className="display-section text-white mb-4">
          İlk araştırmanı<br />bugün çalıştır.
        </h2>
        <p className="text-white/55 text-base mb-10 max-w-md mx-auto">
          Kart bilgisi gerekmez. Ücretsiz plan ile platformu tanı, hazır olunca yükselt.
        </p>
        <Link
          href="/client"
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-white text-primary font-medium text-sm hover:bg-white/90 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu group md:hover:scale-[1.02] md:active:scale-[0.98]"
        >
          Ücretsiz Başla <ArrowRight size={14} className="transition-transform duration-300 md:group-hover:translate-x-1" />
        </Link>
      </Reveal>
    </div>
  </section>
  );
}
