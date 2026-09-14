/**
 * Landing fiyatlandırma verisi — TEK KAYNAK (refactor R4-2).
 *
 * Değerler backend plan kataloğu ile (plan_config / Paddle fiyatları) tutarlı
 * tutulmalıdır. UI bu dosyadan okur; başka yerde plan/fiyat literalı olmamalıdır.
 */

export const PLAN_PRICES: Record<string, { monthly: number | null; annual: number | null }> = {
  "Free": { monthly: 0, annual: 0 },
  "Research Pack": { monthly: 49, annual: 49 },
  "Starter": { monthly: 69, annual: 55 },
  "Pro": { monthly: 169, annual: 135 },
  "Enterprise": { monthly: null, annual: null },
};

// ── Plan data ───────────────────────────────────────────────────────────────

export const PLAN_META = [
  {
    name: "Free",
    description: "Ücretsiz başlayın, fikrinizi test edin.",
    cta: "Ücretsiz Başla",
    ctaHref: "/client?plan=free",
    highlight: false,
    hasBillingToggle: false,
    isOneTime: false,
    limits: [
      "1 ay ücretsiz deneme veya 2 araştırma",
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
      "Araştırma başına 3 'Araştırmayla Konuş' sorgusu",
      "Kurumsal düzeyde araştırma raporu",
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
      "Araştırma başına 3 'Araştırmayla Konuş'",
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
    ctaHref: "mailto:hiclarere@clarere.com?subject=Enterprise Plan Talebi",
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

export const FEATURES = [
  { label: "Pazar Araştırması Modu", plans: [true, true, true, true, true] },
  { label: "A/B Test Modu", plans: [false, true, true, true, true] },
  { label: "Gerçek Zamanlı Streaming", plans: [false, true, true, true, true] },
  { label: "PDF Rapor", plans: [false, true, true, true, true] },
  { label: "Van Westendorp Analizi", plans: [true, true, true, true, true] },
  { label: "B2B Persona Modu", plans: [false, false, false, true, true] },
  { label: "Adversarial Review", plans: [true, true, true, true, true] },
  { label: "Research Fidelity Index (RFI)", plans: [true, true, true, true, true] },
  { label: "Marka Sağlığı Analizi", plans: [false, false, false, true, true] },
  { label: "SES Cross-Tab Analizi", plans: [false, true, true, true, true] },
  { label: "Özel Persona Havuzu", plans: [false, false, false, false, true] },
  { label: "Çok Kullanıcılı Organizasyon", plans: [false, false, false, false, true] },
  { label: "White-label Raporlar", plans: [false, false, false, true, true] },
  { label: "Audit Log", plans: [false, false, false, false, true] },
];
