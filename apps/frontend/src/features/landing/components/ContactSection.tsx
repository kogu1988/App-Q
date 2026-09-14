"use client";

import { Reveal } from "@/features/landing/hooks/use-reveal";

import { ContactForm } from "./ContactForm";

/** İletişim bölümü (refactor R4-1). */
export function ContactSection() {
  return (
  <section id="contact" className="bg-muted-surface px-6 py-20">
    <div className="max-w-2xl mx-auto">
      <Reveal>
        <p className="mono-label text-muted-text mb-3">İletişim</p>
        <h2 className="display-section text-primary mb-3">Bize Ulaşın</h2>
        <p className="text-body-muted mb-8">Sorularınız için hiclarere@clarere.com adresine her zaman yazabilir veya aşağıdaki formu doldurabilirsiniz.</p>
      </Reveal>

      <Reveal>
        <ContactForm />
      </Reveal>
    </div>
  </section>
  );
}
