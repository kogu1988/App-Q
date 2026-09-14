"use client";

import { Reveal } from "@/features/landing/hooks/use-reveal";

import { FEATURE_HIGHLIGHTS } from "@/features/landing/data";

/** Koyu özellik bandı (refactor R4-1). */
export function FeatureBand() {
  return (
  <section className="relative overflow-hidden band-deep-green py-20 px-6">
    {/* bg_image_2: right-side decorative */}
    <div
      className="absolute right-0 top-0 h-full w-1/2 bg-cover bg-center bg-[url('/bg_image_2.jpg')] opacity-20 pointer-events-none"
      aria-hidden="true"
    />
    {/* Right edge fade so image blends into background */}
    <div
      className="absolute right-0 top-0 h-full w-1/3 pointer-events-none bg-gradient-to-l from-deep-green to-transparent"
      aria-hidden="true"
    />
    {/* Left edge fade */}
    <div
      className="absolute left-0 top-0 h-full w-32 pointer-events-none bg-gradient-to-r from-deep-green to-transparent"
      aria-hidden="true"
    />

    <div className="relative max-w-6xl mx-auto">
      <Reveal>
        <p className="mono-label text-pale-green/60 mb-4">Nasıl çalışır?</p>
        <h2 className="display-section text-white mb-3">
          6 adımda AI araştırma
        </h2>
        <p className="text-lg text-white/60 mb-12 max-w-xl">Defne&apos;den sentez raporuna — bilimsel altyapı ile desteklenen tam araştırma akışı.</p>
      </Reveal>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch">
        {FEATURE_HIGHLIGHTS.map(({ icon: Icon, title, desc }, i) => (
          <Reveal key={title} delay={i * 60} className="h-full">
            <div
              className="h-full p-6 rounded-[8px] border border-white/10 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu flex flex-col bg-white/[0.04] group md:hover:border-coral/40 md:hover:scale-[1.01] md:hover:bg-white/[0.06]"
            >
              <div className="w-9 h-9 rounded-[4px] flex items-center justify-center mb-4 shrink-0 transition-transform duration-300 md:group-hover:scale-110 bg-coral">
                <Icon size={18} className="text-canvas" />
              </div>
              <h3 className="text-white font-semibold text-base mb-2 shrink-0 transition-colors duration-300 md:group-hover:text-coral">{title}</h3>
              <p className="text-white/55 text-sm leading-relaxed flex-1">{desc}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  </section>
  );
}
