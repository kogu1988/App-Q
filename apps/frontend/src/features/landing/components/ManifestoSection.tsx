"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Reveal } from "@/features/landing/hooks/use-reveal";

/** Marka manifestosu bölümü (refactor R4-1). */
export function ManifestoSection() {
  return (
  <section className="bg-white py-24 px-6 border-b border-hairline relative">
    <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-12 md:gap-16">

      {/* Left sticky column */}
      <div className="md:w-5/12 md:sticky md:top-28 self-start space-y-4">
        <p className="mono-label text-coral uppercase tracking-wider text-xs">Manifesto</p>
        <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-primary leading-tight" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          Fikrinizin parlaması için gereken berraklık.
        </h2>
        <div className="w-12 h-1 bg-coral mt-6" />
      </div>

      {/* Right scrolling narrative column */}
      <div className="md:w-7/12 space-y-12">

        <Reveal>
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-primary tracking-tight">Sislerin Ötesinde Bir Fikir</h3>
            <p className="text-body-muted text-base leading-relaxed">
              Her büyük ürün, bir sisin içinde başlar. Zihninizdeki fikir parlaktır ama onu başkalarının gözünden görmeye çalıştığınız anda şekiller bulanıklaşır. Mülakatlar, anketler, A/B testleri… Hepsi sizi netliğe götürmesi gerekirken sürecin kendisi yeni bir gürültü yaratır.
            </p>
          </div>
        </Reveal>

        <Reveal delay={60}>
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-primary tracking-tight">Clarere: Berraklaşmak</h3>
            <p className="text-body-muted text-base leading-relaxed">
              Clarere işte tam burada devreye girer. Latince <em className="text-coral not-italic font-semibold">“parlamak, berraklaşmak”</em> anlamından gelen ismimiz, vaadimizin ta kendisidir. Gerçek kullanıcıların karmaşasına, lojistiğine ve belirsizliğine takılmadan, yapay zekânın ürettiği sentetik personalarla fikrinizin üzerindeki sisi dağıtmanızı sağlarız.
            </p>
          </div>
        </Reveal>

        <Reveal delay={120}>
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-primary tracking-tight">Canlı ve Düşünen Profiller</h3>
            <p className="text-body-muted text-base leading-relaxed">
              Artık sorularınız havada asılı kalmaz. Karşınızda konuşan, düşünen, itiraz eden, heyecanlanan insan profilleri vardır. Onlar zihninizin karanlık köşelerine ışık tutar; siz fark etmediğiniz ihtiyaçları, duymadığınız itirazları onlardan duyarsınız.
            </p>
          </div>
        </Reveal>

        <Reveal delay={180}>
          <div className="pt-6 border-t border-hairline space-y-4">
            <p className="text-lg font-bold text-primary font-heading">
              İlk sentetik kullanıcınızla tanışmaya hazır mısınız?
            </p>
            <Link
              href="/client"
              className="inline-flex items-center gap-2 btn-pill-primary text-sm shrink-0 bg-primary text-white group transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu md:hover:scale-[1.02] md:active:scale-[0.98]"
            >
              Hemen Tanışın <ArrowRight size={14} className="transition-transform duration-300 md:group-hover:translate-x-1" />
            </Link>
          </div>
        </Reveal>

      </div>
    </div>
  </section>
  );
}
