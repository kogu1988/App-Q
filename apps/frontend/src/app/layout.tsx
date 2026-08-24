import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const spaceMono = Space_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});


export const metadata: Metadata = {
  title: "Clarere — Yapay Zeka Destekli Sentetik Pazar Araştırması",
  description:
    "Gerçek kullanıcıya ihtiyaç duymadan, gerçek içgörüler elde edin. Clarere, sentetik personalarla anında kullanıcı mülakatı ve A/B testi yapmanızı sağlar.",
  icons: {
    icon: [
      { url: "/logo.svg", type: "image/svg+xml" },
      { url: "/logo.ico", sizes: "32x32" },
    ],
  },
  keywords: [
    "pazar araştırması yapay zeka",
    "sentetik persona simülasyonu",
    "ürün fikri test etme",
    "türkiye pazar araştırma platformu",
    "B2B müşteri araştırması",
    "Van Westendorp fiyat analizi",
    "Rogers Diffusion benimseme",
    "sentetik pazar araştırması",
    "persona simülasyonu",
    "Grounded Simulation",
  ],
  openGraph: {
    title: "Clarere — Yapay Zeka Destekli Sentetik Pazar Araştırması",
    description:
      "Gerçek kullanıcıya ihtiyaç duymadan, gerçek içgörüler elde edin. Clarere, sentetik personalarla anında kullanıcı mülakatı ve A/B testi yapmanızı sağlar.",
    type: "website",
    locale: "tr_TR",
    siteName: "Clarere",
    images: [
      {
        url: "/og-image.svg",
        width: 1200,
        height: 630,
        alt: "Clarere — Sentetik Pazar Araştırması Platformu",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Clarere — Sentetik Pazar Araştırması",
    description:
      "Gerçek kullanıcıya ihtiyaç duymadan, gerçek içgörüler elde edin. Clarere, sentetik personalarla anında kullanıcı mülakatı ve A/B testi yapmanızı sağlar.",
    images: ["/og-image.svg"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
};

// SoftwareApplication JSON-LD Schema — Google Rich Results + AI arama görünürlüğü
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Clarere",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: "https://clarere.com",
  description:
    "Türkiye odaklı yapay zeka destekli sentetik pazar araştırma platformu. Rogers Diffusion, OCEAN psikometri ve Van Westendorp metodolojisiyle gerçek mülakata gerek kalmadan ürün fikirlerini test eder.",
  inLanguage: "tr-TR",
  offers: [
    {
      "@type": "Offer",
      name: "Free Plan",
      price: "0",
      priceCurrency: "TRY",
      description: "2 araştırma, 10 persona, temel rapor",
    },
    {
      "@type": "Offer",
      name: "Research Pack (Flex)",
      price: "1990",
      priceCurrency: "TRY",
      description: "3 araştırma (tek seferlik), A/B test, takip sorusu",
    },
    {
      "@type": "Offer",
      name: "Starter Plan",
      price: "2690",
      priceCurrency: "TRY",
      priceSpecification: {
        "@type": "UnitPriceSpecification",
        price: "2690",
        priceCurrency: "TRY",
        unitText: "MON",
      },
      description: "10 araştırma/ay, 10 persona, PDF rapor, Van Westendorp",
    },
    {
      "@type": "Offer",
      name: "Pro Plan",
      price: "6790",
      priceCurrency: "TRY",
      priceSpecification: {
        "@type": "UnitPriceSpecification",
        price: "6790",
        priceCurrency: "TRY",
        unitText: "MON",
      },
      description: "Sınırsız araştırma, White-label, B2B modu, Marka Sağlığı",
    },
    {
      "@type": "Offer",
      name: "Enterprise Plan",
      description: "Özelleştirilmiş kurumsal çözüm — fiyat için iletişime geçin",
    },
  ],
};

// FAQPage JSON-LD — Google Rich Snippets + GEO (AI arama görünürlüğü)
const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "Clarere nedir?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Clarere, yapıy zeka destekli sentetik pazar araştırması platformudur. Gerçek mülakat ve katılımcı rekrutümanı gerektirmeden, bilimsel olarak zemine oturtulmuş sentetik persona panelleriyle ürün fikirlerinizi, fiyatlandırmanızı ve mesajlaşmanızı test edersiniz.",
      },
    },
    {
      "@type": "Question",
      name: "Sentetik araştırma gerçek müşteri araştırmasının yerini tutar mı?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Hayır. Clarere bir hipotez ve araştırma triage aracıdır. Gerçek pazar testlerinden önce zaman ve büdçe kaybını azaltmak için kullanılır; gerçek müşteri araştırmasının yerini almaz. Platform çıktıları istatistiksel güven iddiasında bulunmaz.",
      },
    },
    {
      "@type": "Question",
      name: "Metodoloji ne kadar güvenilir?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Clarere, Grounded Simulation mimarisini (Bilal, 2026) kullanır. Bağımsız akademik değlendirmede 46 çalışmada ortalama Araştırma Bütünlüğü Endeksi (RFI) = 0.815 elde edilmiştir. 23 kör UX araştırmacısının değlendirmesinde sistem uzman referans bulgularının %93\'lüne ulaşmış; değerlendiricilerin %65'i sistemin çıktısını insan üretimi olarak tanımlamıştır.",
      },
    },
    {
      "@type": "Question",
      name: "Van Westendorp analizi ne işe yarar?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Van Westendorp Fiyat Duyarlılığı Modeli, sentetik katılımcılar aracılığıyla çok pahalı / pahalı / ucuz / çok ucuz eşiklerini hesaplar. Optimal Fiyat Noktası (OPP) ve Kabul Edilebilir Fiyat Aralığı (IPP) çıktıları, fiyatlandırma kararınızı sayısal veriye dayandırmanızı sağlar.",
      },
    },
    {
      "@type": "Question",
      name: "Hangi sektör ve ekipler için uygundur?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Strateji ve kreatif ajanslar, B2B SaaS ürün ekipleri, e-ticaret kurucuları, büyme pazarlamacıları ve konumlandırma / fiyatlandırma / mesajlaşma testlerini hızla çalıştırmak isteyen ürün yöneticileri için tasarlandı.",
      },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${spaceGrotesk.variable} ${spaceMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <Script
          id="schema-software"
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
          strategy="afterInteractive"
        />
        <Script
          id="schema-faq"
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
          strategy="afterInteractive"
        />
      </body>
    </html>
  );
}
