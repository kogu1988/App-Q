"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, X, BarChart2, FlaskConical, ShieldCheck, Zap, Brain, FileText, ArrowRight } from "lucide-react";
import Logo from "@/components/logo";

// ── Pricing config ──────────────────────────────────────────────────────────

const PLAN_PRICES: Record<string, { monthly: number | null; annual: number | null }> = {
  "Free": { monthly: 0, annual: 0 },
  "Research Pack": { monthly: 1990, annual: 1990 },
  "Starter": { monthly: 2690, annual: 2150 },
  "Pro": { monthly: 6790, annual: 5430 },
  "Enterprise": { monthly: null, annual: null },
};

// ── Plan data ───────────────────────────────────────────────────────────────

const PLAN_META = [
  {
    name: "Free",
    description: "Ücretsiz başlayın, fikrinizi test edin.",
    cta: "Ücretsiz Başla",
    ctaHref: "/client?plan=free",
    highlight: false,
    hasBillingToggle: false,
    isOneTime: false,
    limits: [
      "2 araştırma hakkı",
      "10 kişilik persona paneli",
      "Adversarial kalite denetimi",
      "Araştırma Bütünlük Endeksi (RFI)",
      "Temel raporlama",
    ],
  },
  {
    name: "Research Pack",
    description: "Taahhütsüz tek seferlik projeler için. Ödediğin kadar kullan.",
    cta: "Paket Satın Al",
    ctaHref: "/client?plan=flex",
    highlight: false,
    hasBillingToggle: false,
    isOneTime: true,
    limits: [
      "3 araştırma — süre sınırı yok",
      "Kullanıcı mülakatları",
      "A/B testleri",
      "Mülakat taslağı iyileştirme",
      "Araştırma başına 3 takip sorusu",
      "Sınırsız 'Araştırmayla Konuş' sorgusu",
      "Kurumsal düzeyde araştırma raporu",
      "White-label (Markasız) raporlar",
      "Rapor paylaşımı",
    ],
  },
  {
    name: "Starter",
    description: "Solo founder'lar ve küçük ekipler için ideal.",
    cta: "Starter ile Başla",
    ctaHref: "/client?plan=starter",
    highlight: false,
    hasBillingToggle: true,
    isOneTime: false,
    limits: [
      "Ayda 10 araştırma hakkı",
      "Kullanıcı mülakatları",
      "A/B testleri",
      "Mülakat taslağı iyileştirme",
      "Araştırma başına 3 takip (probing)",
      "Araştırma başına 2 'Araştırmayla Konuş'",
      "Kurumsal düzeyde araştırma raporu",
      "Rapor paylaşımı",
    ],
  },
  {
    name: "Pro",
    description: "Ajanslar ve ürün ekipleri için tam analitik güç.",
    cta: "Pro ile Başla",
    ctaHref: "/client?plan=pro",
    highlight: true,
    hasBillingToggle: true,
    isOneTime: false,
    limits: [
      "Starter planındaki her şey, artı:",
      "Sınırsız araştırma sayısı",
      "Sınırsız takip sorusu (probing)",
      "Sınırsız 'Araştırmayla Konuş' sorgusu",
      "White-label (Markasız) raporlar",
    ],
  },
  {
    name: "Enterprise",
    description: "En karmaşık ihtiyaçlarınız için tamamen özelleştirilmiş çözümler.",
    cta: "Bize Ulaşın",
    ctaHref: "mailto:hello@clarere.com?subject=Enterprise Plan Talebi",
    highlight: false,
    hasBillingToggle: false,
    isOneTime: false,
    limits: [
      "İşinize özel tamamen özelleştirilmiş araştırma",
      "Atanmış destek & özel metodoloji",
      "Sınır olmadan ölçeklendirme esnekliği",
      "İş akışınıza göre özel kapsamlandırma",
    ],
  },
];

const FEATURES = [
  { label: "Pazar Araştırması Modu", plans: [true, true, true, true, true] },
  { label: "A/B Test Modu", plans: [false, true, true, true, true] },
  { label: "Gerçek Zamanlı Streaming", plans: [false, true, true, true, true] },
  { label: "PDF Rapor", plans: [false, true, true, true, true] },
  { label: "Van Westendorp Analizi", plans: [true, true, true, true, true] },
  { label: "B2B Persona Modu", plans: [false, false, false, true, true] },
  { label: "Adversarial Review", plans: [true, true, true, true, true] },
  { label: "Research Fidelity Index (RFI)", plans: [true, true, true, true, true] },
  { label: "Marka Sağlığı Analizi", plans: [false, false, false, true, true] },
  { label: "Özel Persona Havuzu", plans: [false, false, false, false, true] },
  { label: "White-label Raporlar", plans: [true, false, true, true] },
  { label: "Audit Log", plans: [false, false, false, true] },
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

// ── Scroll-aware hook ────────────────────────────────────────────────────────

function useScrolled(threshold = 60) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > threshold);
    handler();
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, [threshold]);
  return scrolled;
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function HomePage() {
  const [cardBilling, setCardBilling] = useState<Record<string, "monthly" | "annual">>({});
  const getBilling = (name: string) => cardBilling[name] ?? "monthly";
  const toggleBilling = (name: string) =>
    setCardBilling((prev) => ({ ...prev, [name]: prev[name] === "annual" ? "monthly" : "annual" }));
  const scrolled = useScrolled();
  const router = useRouter();
  const navigateTo = (href: string) => { router.push(href); };

  return (
    <div className="min-h-screen text-ink antialiased font-heading">

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
            <span
              onClick={() => navigateTo("/admin")}
              className={`text-sm transition-colors duration-300 hidden md:block hover:opacity-100 relative group py-1 cursor-pointer ${scrolled ? "text-muted-text" : "text-white/70"}`}
              role="link"
            >
              Yönetim
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

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      {/* min-h-screen: full viewport, announcement bar pushes content down naturally */}
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
                className="btn-text-link text-white/75 no-underline text-sm relative group py-1"
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
                <span>RFI Skoru 0.815</span>
                <span className="text-white/20">·</span>
                <span>46 araştırma alanında test edildi</span>
                <span className="text-white/20">·</span>
                <span>%93 tema doğruluğu</span>
                <span className="text-white/20">·</span>
                <span>Türkiye odaklı TÜAD 2025 veri seti</span>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── MANIFESTO / BRAND STORY SECTION (ASIMETRIK SOL-SABIT AKIŞ) ───────── */}
      <section className="bg-white py-24 px-6 border-b border-[#d9d9dd] relative">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-12 md:gap-16">
          
          {/* Left sticky column */}
          <div className="md:w-5/12 md:sticky md:top-28 self-start space-y-4">
            <p className="mono-label text-[#ff7759] uppercase tracking-wider text-xs">Manifesto</p>
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-[#17171c] leading-tight" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
              Fikrinizin parlaması için gereken berraklık.
            </h2>
            <div className="w-12 h-1 bg-[#ff7759] mt-6" />
          </div>
          
          {/* Right scrolling narrative column */}
          <div className="md:w-7/12 space-y-12">
            
            <Reveal>
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-[#17171c] tracking-tight">Sislerin Ötesinde Bir Fikir</h3>
                <p className="text-[#616161] text-base leading-relaxed">
                  Her büyük ürün, bir sisin içinde başlar. Zihninizdeki fikir parlaktır ama onu başkalarının gözünden görmeye çalıştığınız anda şekiller bulanıklaşır. Mülakatlar, anketler, A/B testleri… Hepsi sizi netliğe götürmesi gerekirken sürecin kendisi yeni bir gürültü yaratır.
                </p>
              </div>
            </Reveal>

            <Reveal delay={60}>
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-[#17171c] tracking-tight">Clarere: Berraklaşmak</h3>
                <p className="text-[#616161] text-base leading-relaxed">
                  Clarere işte tam burada devreye girer. Latince <em className="text-[#ff7759] not-italic font-semibold">“parlamak, berraklaşmak”</em> anlamından gelen ismimiz, vaadimizin ta kendisidir. Gerçek kullanıcıların karmaşasına, lojistiğine ve belirsizliğine takılmadan, yapay zekânın ürettiği sentetik personalarla fikrinizin üzerindeki sisi dağıtmanızı sağlarız.
                </p>
              </div>
            </Reveal>

            <Reveal delay={120}>
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-[#17171c] tracking-tight">Canlı ve Düşünen Profiller</h3>
                <p className="text-[#616161] text-base leading-relaxed">
                  Artık sorularınız havada asılı kalmaz. Karşınızda konuşan, düşünen, itiraz eden, heyecanlanan insan profilleri vardır. Onlar zihninizin karanlık köşelerine ışık tutar; siz fark etmediğiniz ihtiyaçları, duymadığınız itirazları onlardan duyarsınız.
                </p>
              </div>
            </Reveal>

            <Reveal delay={180}>
              <div className="pt-6 border-t border-[#d9d9dd] space-y-4">
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

      {/* ── DARK FEATURE BAND ─────────────────────────────────────────── */}
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
            <p className="mono-label text-[#edfce9]/60 mb-4">Nasıl çalışır?</p>
            <h2 className="display-section text-white mb-3">
              6 adımda AI araştırma
            </h2>
            <p className="text-lg text-white/60 mb-12 max-w-xl">Defne&apos;den sentez raporuna — bilimsel altyapı ile desteklenen tam araştırma akışı.</p>
          </Reveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch">
            {FEATURE_HIGHLIGHTS.map(({ icon: Icon, title, desc }, i) => (
              <Reveal key={title} delay={i * 60} className="h-full">
                <div
                  className="h-full p-6 rounded-[8px] border border-white/10 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu flex flex-col bg-white/[0.04] group md:hover:border-[#ff7759]/40 md:hover:scale-[1.01] md:hover:bg-white/[0.06]"
                >
                  <div className="w-9 h-9 rounded-[4px] flex items-center justify-center mb-4 shrink-0 transition-transform duration-300 md:group-hover:scale-110 bg-coral">
                    <Icon size={18} color="#fff" />
                  </div>
                  <h3 className="text-white font-semibold text-base mb-2 shrink-0 transition-colors duration-300 md:group-hover:text-[#ff7759]">{title}</h3>
                  <p className="text-white/55 text-sm leading-relaxed flex-1">{desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ──────────────────────────────────────────────────────── */}
      <section id="pricing" className="bg-white max-w-full px-6 py-24 scroll-mt-16">
        <div className="max-w-6xl mx-auto">
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
            const prices = PLAN_PRICES[plan.name];
            const isVariable = prices.monthly === null;
            const isAnnual = getBilling(plan.name) === "annual";
            const showAnnual = isAnnual && plan.hasBillingToggle && prices.annual;

            const priceDisplay = isVariable
              ? "Özel"
              : showAnnual
                ? `₺${prices.annual!.toLocaleString("tr-TR")}`
                : `₺${prices.monthly!.toLocaleString("tr-TR")}`;

            const periodDisplay = isVariable 
              ? "" 
              : plan.isOneTime 
                ? " / paket" 
                : "/ay";

            return (
              <Reveal key={plan.name} delay={idx * 60}>
                <div
                  className={`relative rounded-[8px] border p-6 flex flex-col gap-4 h-full transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu ${plan.highlight
                      ? "border-[#17171c] bg-[#17171c] text-white shadow-xl md:hover:border-[#ff7759] md:hover:shadow-[0_16px_40px_-16px_rgba(0,0,0,0.15)] md:hover:scale-[1.01]"
                      : "border-[#d9d9dd] bg-white md:hover:border-[#ff7759]/50 md:hover:shadow-[0_12px_32px_-12px_rgba(0,0,0,0.08)] md:hover:scale-[1.01]"
                    }`}
                >
                  {plan.highlight && (
                    <div
                      className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-xs font-bold tracking-wider uppercase bg-coral text-white"
                    >
                      En Popüler
                    </div>
                  )}

                  {plan.isOneTime && (
                    <div
                      className={`absolute top-3 right-3 px-2.5 py-0.5 rounded-full text-[9px] font-bold tracking-wider uppercase ${
                        plan.highlight 
                          ? "bg-white/10 text-white border border-white/20" 
                          : "bg-coral/10 text-coral border border-coral/20"
                      }`}
                    >
                      Tek Seferlik
                    </div>
                  )}

                  <div>
                    <h3 className="text-base font-semibold mb-0.5">{plan.name}</h3>
                    <p className={`text-xs ${plan.highlight ? "text-white/55" : "text-[#93939f]"}`}>{plan.description}</p>
                  </div>

                  {/* Billing toggle */}
                  {plan.hasBillingToggle && (
                    <div
                      className={`flex items-center gap-0.5 p-0.5 self-start rounded-full border ${plan.highlight ? "border-white/20 bg-white/10" : "border-[#d9d9dd] bg-[#f5f4f1]"
                        }`}
                    >
                      <button
                        onClick={() => toggleBilling(plan.name)}
                        className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${!isAnnual
                            ? plan.highlight ? "bg-white text-[#17171c] shadow-sm" : "bg-white text-[#17171c] shadow-sm"
                            : plan.highlight ? "text-white/50" : "text-[#93939f]"
                          }`}
                      >
                        Aylık
                      </button>
                      <button
                        onClick={() => toggleBilling(plan.name)}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${isAnnual
                            ? plan.highlight ? "bg-white text-[#17171c] shadow-sm" : "bg-white text-[#17171c] shadow-sm"
                            : plan.highlight ? "text-white/50" : "text-[#93939f]"
                          }`}
                      >
                        Yıllık
                        <span className="text-[9px] font-bold bg-[#ff7759] text-white px-1 py-0.5 rounded-full leading-none">
                          -20%
                        </span>
                      </button>
                    </div>
                  )}

                  <div>
                    <div className="flex items-end gap-1">
                      <span className="text-3xl font-bold tracking-tight tracking-tighter">{priceDisplay}</span>
                      <span className={`text-sm mb-0.5 ${plan.highlight ? "text-white/55" : "text-[#93939f]"}`}>{periodDisplay}</span>
                    </div>
                    <p
                      className="text-xs mt-1 transition-opacity duration-300 min-h-[16px]"
                      style={{ color: plan.highlight ? "#edfce9" : "#003c33" }}
                    >
                      {plan.isOneTime
                        ? "Ömür boyu kullanım, taahhüt yok"
                        : isVariable
                          ? "Gereksinimlerinize göre kapsam"
                          : showAnnual
                            ? `Yıllık faturalandırılır (toplam ₺${(prices.annual! * 12).toLocaleString("tr-TR")})`
                            : `Aylık faturalandırılır`
                      }
                    </p>
                  </div>

                  <ul className="space-y-1.5 flex-1">
                    {plan.limits.map((l) => (
                      <li key={l} className={`flex items-start gap-2 text-sm ${plan.highlight ? "text-white/80" : "text-[#616161]"}`}>
                        <Check size={13} color={plan.highlight ? "#edfce9" : "#003c33"} className="shrink-0 mt-1" />
                        <span className="leading-tight">{l}</span>
                      </li>
                    ))}
                    {plan.isOneTime && (
                      <li className={`flex items-center gap-2 text-xs pt-1 border-t mt-1 ${plan.highlight ? "border-white/10 text-white/30" : "border-[#d9d9dd] text-[#93939f]/60"}`}>
                        <Check size={11} className="shrink-0" color={plan.highlight ? "#edfce9" : "#003c33"} />
                        Kullanım süresi sınırı yoktur
                      </li>
                    )}
                    {!plan.isOneTime && !isVariable && (
                      <li className={`flex items-center gap-2 text-xs pt-1 border-t mt-1 ${plan.highlight ? "border-white/10 text-white/30" : "border-[#d9d9dd] text-[#93939f]/60"}`}>
                        <X size={11} className="shrink-0" />
                        Kullanılmayan haklar devretmez
                      </li>
                    )}
                  </ul>

                  <Link
                    href={plan.ctaHref}
                    className={`text-center text-sm font-medium py-2.5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu md:hover:scale-[1.02] md:active:scale-[0.98] ${plan.highlight
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
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────────── */}
      <section id="faq" className="bg-white surface-stone py-20 px-6 scroll-mt-16">
        <div className="max-w-3xl mx-auto">
          <Reveal>
            <p className="mono-label text-[#93939f] mb-3">Merak edilenler</p>
            <h2 className="display-section text-[#17171c] mb-10">Sıkça Sorulan Sorular</h2>
          </Reveal>

          <div className="space-y-0">
            {[
              {
                q: "Clarere nedir?",
                a: "Clarere, kullanıcı fikirlerini, açılış sayfası tasarımlarını ve mesajlarını yapılandırılmış kitle diyaloglarına dönüştürmek için yapay zeka kullanan bir kullanıcı araştırma platformudur. Gerçek dünyadaki demografik özellikleri ve davranışları yansıtan, yapay zeka tarafından oluşturulmuş katılımcılar olan \"sentetik personalar\" kullanarak Clarere, yüksek hız ve düşük maliyetle değerli içgörüler sunar. Bu sayede ekipler, geleneksel katılımcı bulma süreçleriyle ilişkili uzun bekleme süreleri olmadan konseptlerini doğrulayabilirler.",
              },
              {
                q: "Kullanıcı araştırma platformu nedir?",
                a: "Kullanıcı araştırma platformu; ürün ekiplerinin, UX tasarımcılarının ve pazarlamacıların hedef kitlelerinden geri bildirim toplamasına yardımcı olan bir yazılımdır. Bu platformlar genellikle işletmelerin bir ürünü geliştirmeye veya piyasaya sürmeye yatırım yapmadan önce kullanıcı ihtiyaçlarını, temel sorunlarını (pain points) ve davranışlarını anlamalarına yardımcı olmak için görüşmeler, anketler ve kullanılabilirlik testleri gibi etkinlikleri kolaylaştırır.",
              },
              {
                q: "Yapay zeka ile kullanıcı araştırması nasıl çalışır?",
                a: "Clarere gibi modern bir kullanıcı araştırma platformunda, yapay zeka araştırması katılımcı bulma ihtiyacını ortadan kaldırır. Araştırma hedeflerinizi ve hedef kitlenizi tanımlarsınız ve yapay zeka bu profillerle eşleşen sentetik personalar oluşturur. Platform daha sonra bu personalarla yapılandırılmış görüşmeleri veya açılış sayfası testlerini simüle eder. Yapay zeka yaklaşık 30 dakika içinde bu konuşmaları eyleme dönüştürülebilir içgörüler halinde sentezleyerek ortak temaları, itirazları ve dil kalıplarını belirler.",
              },
              {
                q: "Clarere, kullanıcı görüşmelerinin yerini alabilir mi?",
                a: "Clarere, tamamen bir alternatif olmaktan ziyade geleneksel kullanıcı görüşmeleriyle birlikte kullanıldığında en iyi sonucu verir. Bir kullanıcı araştırma platformu olarak, haftalar yerine dakikalar içinde yanıtlara ihtiyaç duyduğunuzda, hızlı konsept doğrulama ve erken aşama yönlendirici geri bildirim sağlama konusunda mükemmeldir. Sentetik araştırma, hipotezleri test etmek ve mesajları geniş ölçekte iyileştirmek için harika olsa da, geliştirmenin ilerleyen aşamalarında derin duygusal nüansları ve beklenmedik uç durumları (edge cases) ortaya çıkarmak için canlı insan görüşmeleri altın standart olmaya devam etmektedir.",
              },
              {
                q: "Ne kadar sürede sonuç alabilirim?",
                a: "Katılımcıları bulmanın ve programlamanın 2-3 hafta sürebildiği geleneksel araştırmaların aksine, Clarere genellikle 30 dakikadan daha kısa bir sürede içgörülerin tam bir sentezini sunar. Bu durum, onu yapay zeka destekli bir kullanıcı araştırma platformu kullanarak araştırma yürütmenin en hızlı yollarından biri yapmaktadır.",
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
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-white text-[#17171c] font-medium text-sm hover:bg-white/90 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] transform-gpu group md:hover:scale-[1.02] md:active:scale-[0.98]"
            >
              Ücretsiz Başla <ArrowRight size={14} className="transition-transform duration-300 md:group-hover:translate-x-1" />
            </Link>
          </Reveal>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-[#d9d9dd] bg-white py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Logo size={24} strokeColor="#93939f" />
            <span className="text-sm text-[#93939f]">Clarere © 2026</span>
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-[#93939f]">
            <span onClick={() => navigateTo("/guide")} className="hover:text-[#212121] transition-colors cursor-pointer" role="link">Kullanım Kılavuzu</span>
            <span onClick={() => navigateTo("/#faq")} className="hover:text-[#212121] transition-colors cursor-pointer" role="link">SSS</span>
            <span onClick={() => navigateTo("/privacy")} className="hover:text-[#212121] transition-colors cursor-pointer" role="link">Gizlilik</span>
            <span onClick={() => navigateTo("/terms")} className="hover:text-[#212121] transition-colors cursor-pointer" role="link">Kullanım Koşulları</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
