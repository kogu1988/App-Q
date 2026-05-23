"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Check, X, BarChart2, FlaskConical, ShieldCheck, Zap, Brain, FileText, ArrowRight } from "lucide-react";

// ── Pricing config ──────────────────────────────────────────────────────────

const MONTHLY_PRICES: Record<string, number | null> = {
  Free: 0,
  Starter: 990,
  Pro: 2990,
  Enterprise: null,
};

function annualPrice(monthly: number) {
  return monthly * 11;
}
function monthlyEquivalent(monthly: number) {
  return Math.round((monthly * 11) / 12);
}

// ── Plan data ───────────────────────────────────────────────────────────────

const PLAN_META = [
  {
    name: "Free",
    description: "Platformu keşfet, ilk araştırmana başla.",
    cta: "Hemen Başla",
    ctaHref: "/client",
    highlight: false,
    hasBillingToggle: false,
    limits: ["2 araştırma/ay", "3 persona", "Temel rapor"],
  },
  {
    name: "Starter",
    description: "Solo founder ve küçük ekipler için.",
    cta: "Starter ile Başla",
    ctaHref: "/client?plan=starter",
    highlight: false,
    hasBillingToggle: true,
    limits: ["10 araştırma/ay", "5 persona", "PDF rapor", "Van Westendorp"],
  },
  {
    name: "Pro",
    description: "Ajanslar ve ürün ekipleri için tam analitik güç.",
    cta: "Pro ile Başla",
    ctaHref: "/client?plan=pro",
    highlight: true,
    hasBillingToggle: true,
    limits: ["Sınırsız araştırma", "7 persona", "A/B Test", "Adversarial Review", "RFI Skoru"],
  },
  {
    name: "Enterprise",
    description: "Kurumsal özelleştirme, SLA ve öncelikli destek.",
    cta: "Bize Ulaş",
    ctaHref: "mailto:hello@clarere.com",
    highlight: false,
    hasBillingToggle: false,
    limits: ["Sınırsız", "Özel persona havuzu", "White-label", "Fine-tuning export", "Audit log"],
  },
];

const FEATURES = [
  { label: "Pazar Araştırması Modu",        plans: [true,  true,  true,  true ] },
  { label: "A/B Test Modu",                 plans: [false, false, true,  true ] },
  { label: "Gerçek Zamanlı Streaming",      plans: [false, true,  true,  true ] },
  { label: "PDF Rapor",                     plans: [false, true,  true,  true ] },
  { label: "Van Westendorp Analizi",        plans: [false, true,  true,  true ] },
  { label: "B2B Persona Modu",              plans: [false, false, true,  true ] },
  { label: "Adversarial Review",            plans: [false, false, true,  true ] },
  { label: "Research Fidelity Index (RFI)", plans: [false, false, true,  true ] },
  { label: "Özel Persona Havuzu",           plans: [false, false, false, true ] },
  { label: "White-label",                   plans: [false, false, false, true ] },
  { label: "Audit Log",                     plans: [false, false, false, true ] },
];

const FEATURE_HIGHLIGHTS = [
  {
    icon: Brain,
    title: "Defne — Araştırma Sihirbazı",
    desc: "Yapay zeka destekli brief asistanı. Ürün fikrinizi sohbet yoluyla net bir araştırma planına dönüştürür.",
  },
  {
    icon: BarChart2,
    title: "Rogers Diffusion Stance",
    desc: "Innovator'dan Laggard'a 5 benimseme kategorisi. Her panel, gerçek pazar dinamiklerini yansıtan dağılımla kurulur.",
  },
  {
    icon: FlaskConical,
    title: "A/B Test Simülasyonu",
    desc: "İki varyantı aynı sentetik panele aynı anda göster. Gerçek lansmandan önce en iyi mesajı bul.",
  },
  {
    icon: ShieldCheck,
    title: "Adversarial Review + RFI",
    desc: "Bağımsız denetim katmanı ve 6 bileşenli Research Fidelity Index ile araştırmanın kalitesini ölç.",
  },
  {
    icon: Zap,
    title: "Van Westendorp Fiyat Analizi",
    desc: "OPP ve IPP noktalarıyla optimal fiyat aralığını bul. Fiyatlandırma kararlarını veriden al.",
  },
  {
    icon: FileText,
    title: "Zengin PDF Rapor",
    desc: "Executive summary, kanıt bağlı bulgular, pain point matrisi ve validasyon önerileri tek raporda.",
  },
];

// ── Scroll reveal hook ──────────────────────────────────────────────────────

function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { el.classList.add("visible"); obs.unobserve(el); } },
      { threshold: 0.12 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return ref;
}

function Reveal({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useReveal();
  return (
    <div
      ref={ref}
      className={`reveal ${className}`}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function HomePage() {
  const [cardBilling, setCardBilling] = useState<Record<string, "monthly" | "annual">>({});
  const getBilling = (name: string) => cardBilling[name] ?? "monthly";
  const toggleBilling = (name: string) =>
    setCardBilling((prev) => ({ ...prev, [name]: prev[name] === "annual" ? "monthly" : "annual" }));

  return (
    <div className="min-h-screen bg-[#ffffff] text-[#212121]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>

      {/* ── ANNOUNCEMENT BAR ─────────────────────────────────────────────── */}
      <div className="announcement-bar">
        <span>
          Grounded Simulation metodolojisi — akademik temelli sentetik araştırma.{" "}
          <a href="#faq" className="underline underline-offset-2 hover:opacity-70 transition-opacity">Daha fazla bilgi</a>
        </span>
      </div>

      {/* ── NAV ──────────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 border-b border-[#d9d9dd] bg-white/95 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Clarere logo" className="h-8 w-auto object-contain" />
            <span className="font-semibold text-base tracking-tight text-[#17171c]">Clarere</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#pricing" className="text-sm text-[#93939f] hover:text-[#212121] transition-colors hidden sm:block">Fiyatlandırma</a>
            <a href="#faq" className="text-sm text-[#93939f] hover:text-[#212121] transition-colors hidden sm:block">SSS</a>
            <Link href="/admin" className="text-sm text-[#93939f] hover:text-[#212121] transition-colors hidden md:block">
              Yönetim
            </Link>
            <Link
              href="/client"
              className="btn-pill-primary text-sm"
            >
              Giriş Yap
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      {/* Cohere-style: massive type over white canvas, centered, no split */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center">
        <Reveal>
          <div className="inline-flex items-center gap-2 mb-8">
            <span className="chip-coral">Grounded Simulation</span>
            <span className="mono-label text-[#93939f]">Bilal, 2026</span>
          </div>
        </Reveal>

        <Reveal delay={80}>
          <h1 className="display-hero text-[#17171c] mb-6" style={{ maxWidth: "880px", margin: "0 auto 1.5rem" }}>
            Gerçek mülakatlardan önce{" "}
            <span style={{ color: "#ff7759" }}>sentetik panel</span> kur.
          </h1>
        </Reveal>

        <Reveal delay={160}>
          <p className="text-lg text-[#616161] max-w-2xl mx-auto leading-relaxed mb-10" style={{ fontWeight: 400 }}>
            Rogers Diffusion + OCEAN psikometrisi + Adversarial Review ile
            ürün fikirlerinizi AI destekli tüketici panelleriyle test edin.
            Saatler içinde karar alınabilir içgörü.
          </p>
        </Reveal>

        <Reveal delay={240}>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/client" className="btn-pill-primary text-sm">
              Ücretsiz Başla <ArrowRight size={14} className="ml-2 inline" />
            </Link>
            <a href="#pricing" className="btn-text-link text-sm">
              Planları Gör
            </a>
          </div>
        </Reveal>

        {/* Trust strip */}
        <Reveal delay={320}>
          <div className="mt-16 pt-8 border-t border-[#d9d9dd]">
            <p className="mono-label text-[#93939f] mb-6">Platform hakkında</p>
            <div className="flex flex-wrap justify-center gap-x-10 gap-y-3 text-sm text-[#93939f]">
              <span>RFI Skoru 0.815</span>
              <span className="text-[#d9d9dd]">·</span>
              <span>46 araştırma alanında test edildi</span>
              <span className="text-[#d9d9dd]">·</span>
              <span>%93 tema doğruluğu</span>
              <span className="text-[#d9d9dd]">·</span>
              <span>Türkiye odaklı TÜAD 2025 veri seti</span>
            </div>
          </div>
        </Reveal>
      </section>

      {/* ── DARK FEATURE BAND — Cohere "dark-feature-band" ─────────────── */}
      <section className="band-deep-green py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <p className="mono-label text-[#edfce9]/60 mb-4">Nasıl çalışır?</p>
            <h2 className="display-section text-white mb-3">
              6 adımda AI araştırma
            </h2>
            <p className="text-lg text-white/60 mb-12 max-w-xl">Defne'den sentez raporuna — bilimsel altyapı ile desteklenen tam araştırma akışı.</p>
          </Reveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURE_HIGHLIGHTS.map(({ icon: Icon, title, desc }, i) => (
              <Reveal key={title} delay={i * 60}>
                <div
                  className="p-6 rounded-[8px] border border-white/10 hover:border-white/25 transition-all duration-300"
                  style={{ background: "rgba(255,255,255,0.04)" }}
                >
                  <div className="w-9 h-9 rounded-[4px] flex items-center justify-center mb-4" style={{ background: "#ff7759" }}>
                    <Icon size={18} color="#fff" />
                  </div>
                  <h3 className="text-white font-semibold text-base mb-2">{title}</h3>
                  <p className="text-white/55 text-sm leading-relaxed">{desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ──────────────────────────────────────────────────────── */}
      <section id="pricing" className="max-w-6xl mx-auto px-6 py-24 scroll-mt-16">
        <Reveal>
          <div className="mb-12">
            <p className="mono-label text-[#93939f] mb-3">Planlar</p>
            <h2 className="display-section text-[#17171c] mb-2">Fiyatlandırma</h2>
            <p className="text-[#616161] text-base">İstediğin zaman yükselt veya düşür. Gizli ücret yok.</p>
          </div>
        </Reveal>

        {/* Plan Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {PLAN_META.map((plan, idx) => {
            const monthlyPx = MONTHLY_PRICES[plan.name];
            const isVariable = monthlyPx === null;
            const isAnnual = getBilling(plan.name) === "annual";
            const showAnnual = isAnnual && plan.hasBillingToggle && monthlyPx;

            const priceDisplay = isVariable
              ? "Özel"
              : showAnnual
              ? `₺${annualPrice(monthlyPx!).toLocaleString("tr-TR")}`
              : monthlyPx === 0
              ? "₺0"
              : `₺${monthlyPx!.toLocaleString("tr-TR")}`;

            const periodDisplay = isVariable ? "" : showAnnual ? "/yıl" : "/ay";

            return (
              <Reveal key={plan.name} delay={idx * 60}>
                <div
                  className={`relative rounded-[8px] border p-6 flex flex-col gap-4 h-full transition-all duration-300 ${
                    plan.highlight
                      ? "border-[#17171c] bg-[#17171c] text-white shadow-xl"
                      : "border-[#d9d9dd] bg-white hover:border-[#17171c] hover:shadow-sm"
                  }`}
                >
                  {plan.highlight && (
                    <div
                      className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-xs font-bold tracking-wider uppercase"
                      style={{ background: "#ff7759", color: "#fff" }}
                    >
                      En Popüler
                    </div>
                  )}

                  <div>
                    <h3 className="text-base font-semibold mb-0.5">{plan.name}</h3>
                    <p className={`text-xs ${plan.highlight ? "text-white/55" : "text-[#93939f]"}`}>{plan.description}</p>
                  </div>

                  {/* Billing toggle */}
                  {plan.hasBillingToggle && (
                    <div
                      className={`flex items-center gap-0.5 p-0.5 self-start rounded-full border ${
                        plan.highlight ? "border-white/20 bg-white/10" : "border-[#d9d9dd] bg-[#f5f4f1]"
                      }`}
                    >
                      <button
                        onClick={() => toggleBilling(plan.name)}
                        className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${
                          !isAnnual
                            ? plan.highlight ? "bg-white text-[#17171c] shadow-sm" : "bg-white text-[#17171c] shadow-sm"
                            : plan.highlight ? "text-white/50" : "text-[#93939f]"
                        }`}
                      >
                        Aylık
                      </button>
                      <button
                        onClick={() => toggleBilling(plan.name)}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${
                          isAnnual
                            ? plan.highlight ? "bg-white text-[#17171c] shadow-sm" : "bg-white text-[#17171c] shadow-sm"
                            : plan.highlight ? "text-white/50" : "text-[#93939f]"
                        }`}
                      >
                        Yıllık
                        <span className="text-[9px] font-bold bg-[#ff7759] text-white px-1 py-0.5 rounded-full leading-none">
                          -8%
                        </span>
                      </button>
                    </div>
                  )}

                  <div>
                    <div className="flex items-end gap-1">
                      <span className="text-3xl font-bold tracking-tight" style={{ letterSpacing: "-0.03em" }}>{priceDisplay}</span>
                      <span className={`text-sm mb-0.5 ${plan.highlight ? "text-white/50" : "text-[#93939f]"}`}>{periodDisplay}</span>
                    </div>
                    {showAnnual && monthlyPx && (
                      <p className="text-xs mt-1" style={{ color: plan.highlight ? "#edfce9" : "#003c33" }}>
                        Aylık ₺{monthlyEquivalent(monthlyPx).toLocaleString("tr-TR")} — 1 ay bedava
                      </p>
                    )}
                  </div>

                  <ul className="space-y-1.5 flex-1">
                    {plan.limits.map((l) => (
                      <li key={l} className={`flex items-center gap-2 text-sm ${plan.highlight ? "text-white/80" : "text-[#616161]"}`}>
                        <Check size={13} color={plan.highlight ? "#edfce9" : "#003c33"} className="shrink-0" />
                        {l}
                      </li>
                    ))}
                    <li className={`flex items-center gap-2 text-xs pt-1 border-t mt-1 ${plan.highlight ? "border-white/10 text-white/30" : "border-[#d9d9dd] text-[#93939f]/60"}`}>
                      <X size={11} className="shrink-0" />
                      Kullanılmayan haklar devretmez
                    </li>
                  </ul>

                  <Link
                    href={plan.ctaHref}
                    className={`text-center text-sm font-medium py-2.5 rounded-full transition-all ${
                      plan.highlight
                        ? "bg-white text-[#17171c] hover:bg-white/90"
                        : "bg-[#17171c] text-white hover:opacity-85 btn-pill-primary"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              </Reveal>
            );
          })}
        </div>

        {/* Comparison table */}
        <Reveal>
          <div className="overflow-x-auto rounded-[8px] border border-[#d9d9dd]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#d9d9dd] bg-[#f5f4f1]">
                  <th className="text-left px-5 py-3.5 font-medium text-[#93939f]">Özellik</th>
                  {PLAN_META.map((p) => (
                    <th
                      key={p.name}
                      className={`text-center px-4 py-3.5 font-semibold ${p.highlight ? "text-[#17171c]" : "text-[#616161]"}`}
                    >
                      {p.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FEATURES.map((f, i) => (
                  <tr
                    key={f.label}
                    className={`border-b border-[#f2f2f2] ${i % 2 === 0 ? "bg-white" : "bg-[#fafafa]"}`}
                  >
                    <td className="px-5 py-3 font-medium text-[#212121]">{f.label}</td>
                    {f.plans.map((has, j) => (
                      <td key={j} className="px-4 py-3 text-center">
                        {has
                          ? <Check size={14} color="#003c33" className="mx-auto" />
                          : <X size={14} className="text-[#d9d9dd] mx-auto" />}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-center text-xs text-[#93939f] mt-4">
            Tüm fiyatlar KDV hariçtir. Yıllık faturalamalarda %8 indirim uygulanır.
          </p>
        </Reveal>
      </section>

      {/* ── FAQ — Cohere research-table style ────────────────────────────── */}
      <section id="faq" className="surface-stone py-20 px-6 scroll-mt-16">
        <div className="max-w-3xl mx-auto">
          <Reveal>
            <p className="mono-label text-[#93939f] mb-3">Merak edilenler</p>
            <h2 className="display-section text-[#17171c] mb-10">Sıkça Sorulan Sorular</h2>
          </Reveal>

          <div className="space-y-0">
            {[
              {
                q: "Clarere nedir?",
                a: "Clarere, yapay zeka destekli sentetik pazar araştırması platformudur. Gerçek mülakat ve katılımcı rekrutümanı gerektirmeden, bilimsel olarak zemine oturtulmuş sentetik persona panelleriyle ürün fikirlerinizi, fiyatlandırmanızı ve mesajlaşmanızı test edersiniz.",
              },
              {
                q: "Sentetik araştırma gerçek müşteri araştırmasının yerini tutar mı?",
                a: "Hayır. Clarere bir hipotez ve araştırma triage aracıdır. Gerçek pazar testlerinden önce zaman ve bütçe kaybını azaltmak için kullanılır; gerçek müşteri araştırmasının yerini almaz. Platform çıktıları istatistiksel güven iddiasında bulunmaz.",
              },
              {
                q: "Metodoloji ne kadar güvenilir?",
                a: "Clarere'nun araştırma motoru; kişilik psikolojisi, bilişsel mimari ve kültürel boyut çerçevelerine dayanan çok katmanlı bilimsel bir altyapı üzerinde çalışır. Bağımsız değerlendirmelerde sistem, 46 farklı araştırma alanında yüksek tema doğruluğu sergilemiş ve uzman UX araştırmacılarının büyük çoğunluğu tarafından insan kalitesinde üretim olarak nitelendirilmiştir.",
              },
              {
                q: "Hangi sektör ve ekipler için uygundur?",
                a: "Strateji ve kreatif ajanslar, B2B SaaS ürün ekipleri, e-ticaret kurucuları, büyüme pazarlamacıları ve konumlandırma / fiyatlandırma / mesajlaşma testlerini hızla çalıştırmak isteyen ürün yöneticileri için tasarlandı.",
              },
              {
                q: "Ücretsiz plan ne kadar süre kullanılabilir?",
                a: "Ücretsiz plan süresiz kullanılabilir; aylık 2 simülasyon ve 50.000 token ile sınırlıdır. Kart bilgisi gerekmez.",
              },
            ].map(({ q, a }, i) => (
              <Reveal key={i} delay={i * 40}>
                <details className="group border-b border-[#d9d9dd] py-1">
                  <summary className="flex items-start justify-between py-4 cursor-pointer font-medium text-base text-[#17171c] hover:text-[#212121] list-none gap-4">
                    <span>{q}</span>
                    <span className="text-[#93939f] group-open:rotate-45 transition-transform duration-200 text-xl font-light shrink-0 mt-0.5">+</span>
                  </summary>
                  <div className="pb-5 text-sm text-[#616161] leading-relaxed max-w-2xl">
                    {a}
                  </div>
                </details>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA BAND ─────────────────────────────────────────────────────── */}
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
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-white text-[#17171c] font-medium text-sm hover:bg-white/90 transition-all"
            >
              Ücretsiz Başla <ArrowRight size={14} />
            </Link>
          </Reveal>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-[#d9d9dd] bg-white py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Clarere" className="h-6 w-auto object-contain" />
            <span className="text-sm text-[#93939f]">Clarere © 2026</span>
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-[#93939f]">
            <Link href="/#faq" className="hover:text-[#212121] transition-colors">SSS</Link>
            <Link href="/#pricing" className="hover:text-[#212121] transition-colors">Fiyatlandırma</Link>
            <Link href="/privacy" className="hover:text-[#212121] transition-colors">Gizlilik</Link>
            <Link href="/terms" className="hover:text-[#212121] transition-colors">Kullanım Koşulları</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
