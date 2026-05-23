"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, X, BarChart2, FlaskConical, ShieldCheck, Zap, Brain, FileText } from "lucide-react";

// ── Pricing config ─────────────────────────────────────────────────────────────

const MONTHLY_PRICES: Record<string, number | null> = {
  Free: 0,
  Starter: 990,
  Pro: 2990,
  Enterprise: null,
};

function annualPrice(monthly: number) {
  // 1 ay bedava = 11 ay öde, 12 ay kullan
  return monthly * 11;
}

function monthlyEquivalent(monthly: number) {
  return Math.round((monthly * 11) / 12);
}


// ── Plan verisi ────────────────────────────────────────────────────────────────

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
    ctaHref: "mailto:hello@appq.ai",
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

export default function HomePage() {
  // Per-kart faturalama durumu: her plan kendi toggle'ına sahip
  const [cardBilling, setCardBilling] = useState<Record<string, "monthly" | "annual">>({});
  const getBilling = (name: string) => cardBilling[name] ?? "monthly";
  const toggleBilling = (name: string) =>
    setCardBilling((prev) => ({ ...prev, [name]: prev[name] === "annual" ? "monthly" : "annual" }));

  return (
    <div className="min-h-screen bg-background text-foreground">

      {/* ── NAV ─────────────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-primary text-primary-foreground flex items-center justify-center text-sm font-black rounded-lg">
              Q
            </div>
            <span className="font-bold text-lg tracking-tight">App-Q</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Yönetim
            </Link>
            <Link
              href="/client"
              className="text-sm font-semibold px-4 py-1.5 rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
            >
              Giriş Yap
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ────────────────────────────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center space-y-6">
        <div className="inline-flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-accent bg-accent/10 px-3 py-1 rounded-full">
          Grounded Simulation Metodolojisi
        </div>
        <h1 className="text-5xl sm:text-6xl font-black tracking-tight leading-tight">
          Gerçek mülakatlardan önce<br />
          <span className="text-primary">sentetik panel</span> kur.
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Rogers Diffusion + OCEAN psikometrisi + Adversarial Review ile
          ürün fikirlerinizi AI destekli tüketici panelleriyle test edin.
          Saatler içinde karar alınabilir içgörü.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            href="/client"
            className="px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-base hover:opacity-90 transition-opacity shadow-md"
          >
            Ücretsiz Başla →
          </Link>
          <a
            href="#pricing"
            className="px-6 py-3 rounded-xl border border-border text-base font-medium hover:bg-muted transition-colors"
          >
            Planları Gör
          </a>
        </div>
      </section>

      {/* ── FEATURE HIGHLIGHTS ──────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="text-center mb-10 space-y-2">
          <h2 className="text-2xl font-black tracking-tight">Nasıl Çalışır?</h2>
          <p className="text-sm text-muted-foreground">Defne'den sentez raporuna — 6 adımda AI destekli araştırma.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURE_HIGHLIGHTS.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="p-6 rounded-2xl border border-border bg-card hover:border-accent/50 hover:shadow-md transition-all duration-300 space-y-3"
            >
              <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
                <Icon size={20} className="text-accent" />
              </div>
              <h3 className="font-bold text-base">{title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>


      {/* ── PRICING ─────────────────────────────────────────────────────────── */}
      <section id="pricing" className="max-w-6xl mx-auto px-6 pb-24 space-y-12 scroll-mt-16">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-black tracking-tight">Planlar & Fiyatlandırma</h2>
          <p className="text-muted-foreground">İstediğin zaman yükselt veya düşür. Gizli ücret yok.</p>
        </div>

        {/* Plan Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {PLAN_META.map((plan) => {
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
              <div
                key={plan.name}
                className={`relative rounded-2xl border p-6 flex flex-col gap-4 transition-all duration-300 ${
                  plan.highlight
                    ? "border-primary bg-primary/5 shadow-xl shadow-primary/10 scale-[1.02]"
                    : "border-border bg-card hover:shadow-md hover:border-border/80"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-primary text-primary-foreground text-xs font-bold tracking-wider uppercase shadow">
                    En Popüler
                  </div>
                )}
                <div>
                  <h3 className="text-lg font-bold">{plan.name}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{plan.description}</p>
                </div>

                {/* Per-card billing toggle */}
                {plan.hasBillingToggle && (
                  <div className="flex items-center gap-1 p-0.5 bg-muted rounded-lg border border-border/70 self-start">
                    <button
                      onClick={() => toggleBilling(plan.name)}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                        !isAnnual
                          ? "bg-background text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Aylık
                    </button>
                    <button
                      onClick={() => toggleBilling(plan.name)}
                      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                        isAnnual
                          ? "bg-background text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Yıllık
                      <span className="text-[9px] font-bold bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 px-1 py-0.5 rounded-full leading-none">
                        -8%
                      </span>
                    </button>
                  </div>
                )}

                <div className="space-y-0.5">
                  <div className="flex items-end gap-1">
                    <span className="text-3xl font-black">{priceDisplay}</span>
                    <span className="text-sm text-muted-foreground mb-0.5">{periodDisplay}</span>
                  </div>
                  {showAnnual && monthlyPx && (
                    <p className="text-xs text-green-600 dark:text-green-400 font-medium">
                      Aylık ₺{monthlyEquivalent(monthlyPx).toLocaleString("tr-TR")} &mdash; 1 ay bedava
                    </p>
                  )}
                </div>
                <ul className="space-y-1.5 flex-1">
                  {plan.limits.map((l) => (
                    <li key={l} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Check size={13} className="text-green-500 shrink-0" />
                      {l}
                    </li>
                  ))}
                  <li className="flex items-center gap-2 text-xs text-muted-foreground/60 pt-1 border-t border-border/40 mt-1">
                    <X size={11} className="text-muted-foreground/40 shrink-0" />
                    Kullanılmayan haklar devretmez
                  </li>
                </ul>
                <Link
                  href={plan.ctaHref}
                  className={`text-center text-sm font-semibold py-2.5 rounded-xl transition-all ${
                    plan.highlight
                      ? "bg-primary text-primary-foreground hover:opacity-90 shadow"
                      : "bg-muted hover:bg-muted/70 text-foreground"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            );
          })}
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto rounded-2xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left px-5 py-3.5 font-semibold text-muted-foreground">Özellik</th>
                {PLAN_META.map((p) => (
                  <th
                    key={p.name}
                    className={`text-center px-4 py-3.5 font-bold ${p.highlight ? "text-primary" : "text-foreground"}`}
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
                  className={`border-b border-border/50 ${i % 2 === 0 ? "bg-background" : "bg-muted/20"}`}
                >
                  <td className="px-5 py-3 font-medium text-foreground">{f.label}</td>
                  {f.plans.map((has, j) => (
                    <td key={j} className="px-4 py-3 text-center">
                      {has
                        ? <Check size={15} className="text-green-500 mx-auto" />
                        : <X size={15} className="text-muted-foreground/30 mx-auto" />}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          Tüm fiyatlar KDV hariçtir. Yıllık faturalamalarda %20 indirim uygulanır.
        </p>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────────────── */}
      <footer className="border-t border-border py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-black rounded">Q</div>
            <span>App-Q © 2026</span>
          </div>
          <div className="flex gap-6">
            <Link href="/admin" className="hover:text-foreground transition-colors">Yönetim Paneli</Link>
            <Link href="/client" className="hover:text-foreground transition-colors">Danışan Portalı</Link>
            <Link href="/#pricing" className="hover:text-foreground transition-colors">Fiyatlandırma</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
