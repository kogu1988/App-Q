"use client";

import { useRouter } from "next/navigation";
import { SiteNav } from "@/features/landing/components/SiteNav";
import { HeroSection } from "@/features/landing/components/HeroSection";
import { ManifestoSection } from "@/features/landing/components/ManifestoSection";
import { FeatureBand } from "@/features/landing/components/FeatureBand";
import { PricingSection } from "@/features/pricing/PricingSection";
import { ContactSection } from "@/features/landing/components/ContactSection";
import { FaqSection } from "@/features/landing/components/FaqSection";
import { CtaBand } from "@/features/landing/components/CtaBand";
import { SiteFooter } from "@/features/landing/components/SiteFooter";
import { useScrolled } from "@/features/landing/hooks/use-reveal";

// ── Main page ───────────────────────────────────────────────────────────────

export default function HomePage() {
  const scrolled = useScrolled();
  const router = useRouter();
  const navigateTo = (href: string) => { router.push(href); };

  return (
    <div className="min-h-screen text-ink antialiased font-heading">

      <SiteNav scrolled={scrolled} navigateTo={navigateTo} />

      <HeroSection />

      <ManifestoSection />

      <FeatureBand />

      <PricingSection />

      <ContactSection />

      <FaqSection />

      <CtaBand />

      <SiteFooter navigateTo={navigateTo} />

    </div>
  );
}
