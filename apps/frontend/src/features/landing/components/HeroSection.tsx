"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Reveal } from "@/features/landing/hooks/use-reveal";

/** Hero bölümü (refactor R4-1). */
export function HeroSection() {
  return (
  <section className="relative overflow-hidden min-h-screen">
    {/* Full-bleed background image */}
    <div
      className="absolute inset-0 bg-cover bg-center bg-no-repeat bg-[url('/bg_image_1.jpg')]"
      aria-hidden="true"
    />
    {/* Gradient overlay: dark bottom for text, fade top */}
    <div
      className="absolute inset-0 bg-gradient-to-b from-primary/55 via-primary/72 to-primary/88"
      aria-hidden="true"
    />

    <div className="relative max-w-5xl mx-auto px-6 pt-36 pb-20 text-center">
      <Reveal>
        <h1 className="display-hero text-white mb-6 max-w-[880px] mx-auto">
          Gerçek mülakatlardan önce{" "}
          <span className="text-coral">sentetik panel</span> kur.
        </h1>
      </Reveal>

      <Reveal delay={160}>
        <p className="text-lg max-w-2xl mx-auto leading-relaxed mb-6 text-white/70 font-normal">
          Gerçek kullanıcıya ihtiyaç duymadan, gerçek içgörüler elde edin. Clarere, sentetik personalarla anında kullanıcı mülakatı ve A/B testi yapmanızı sağlar.
        </p>
        {/* Methodology Badges */}
        <div className="flex flex-wrap justify-center gap-2 mb-8 max-w-lg mx-auto">
          <span className="px-3 py-1 rounded-[2px] text-[10px] sm:text-xs font-semibold border border-white/10 text-white/80 bg-white/5 uppercase tracking-wider font-mono">
            Rogers Diffusion
          </span>
          <span className="px-3 py-1 rounded-[2px] text-[10px] sm:text-xs font-semibold border border-white/10 text-white/80 bg-white/5 uppercase tracking-wider font-mono">
            OCEAN Psikometrisi
          </span>
          <span className="px-3 py-1 rounded-[2px] text-[10px] sm:text-xs font-semibold border border-white/10 text-white/80 bg-white/5 uppercase tracking-wider font-mono">
            A/B Test Simülasyonu
          </span>
          <span className="px-3 py-1 rounded-[2px] text-[10px] sm:text-xs font-semibold border border-white/10 text-white/80 bg-white/5 uppercase tracking-wider font-mono">
            Adversarial Review
          </span>
        </div>
      </Reveal>

      <Reveal delay={240}>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/client"
            className="btn-pill-primary bg-coral text-primary text-sm group transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu md:hover:scale-[1.02] md:active:scale-[0.98]"
          >
            Ücretsiz Başla <ArrowRight size={14} className="ml-2 inline transition-transform duration-300 md:group-hover:translate-x-1" />
          </Link>
          <a
            href="#pricing"
            className="btn-text-link text-white font-medium no-underline text-sm relative group py-1"
          >
            Planları Gör
            <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-coral transition-all duration-300 group-hover:w-full" />
          </a>
        </div>
      </Reveal>

      {/* Trust strip */}
      <Reveal delay={320}>
        <div className="mt-16 pt-8 border-t border-white/12">
          <p className="mono-label mb-6 text-pale-green/50">Platform hakkında</p>
          <div className="flex flex-wrap justify-center gap-x-10 gap-y-3 text-sm text-white/50">
            <span>Kanıt zinciriyle izlenebilir bulgular</span>
            <span className="text-white/20">·</span>
            <span>Anti-dalkavukluk ve çeşitlilik denetimi</span>
            <span className="text-white/20">·</span>
            <span>Van Westendorp fiyat analizi</span>
            <span className="text-white/20">·</span>
            <span>Türkiye odaklı TÜAD 2025 SES dağılımı</span>
          </div>
        </div>
      </Reveal>
    </div>
  </section>
  );
}
