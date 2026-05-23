import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";
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
  title: "App-Q — Yapay Zeka Destekli Sentetik Pazar Araştırması",
  description:
    "Gerçek mülakata gerek kalmadan AI destekli sentetik panellerle ürün fikirlerinizi test edin. Rogers Diffusion + Van Westendorp + OCEAN metodolojisiyle saatler içinde içgörü.",
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
    title: "App-Q — Yapay Zeka Destekli Sentetik Pazar Araştırması",
    description:
      "Gerçek mülakata gerek kalmadan AI destekli sentetik panellerle ürün fikirlerinizi test edin.",
    type: "website",
    locale: "tr_TR",
    siteName: "App-Q",
    images: [
      {
        url: "https://appq.ai/og-image.png",
        width: 1200,
        height: 630,
        alt: "App-Q — Sentetik Pazar Araştırması Platformu",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "App-Q — Sentetik Pazar Araştırması",
    description:
      "Rogers Diffusion + OCEAN + Van Westendorp ile AI destekli tüketici panel simülasyonu.",
    images: ["https://appq.ai/og-image.png"],
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
  name: "App-Q",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: "https://appq.ai",
  description:
    "Türkiye odaklı yapay zeka destekli sentetik pazar araştırma platformu. Rogers Diffusion, OCEAN psikometri ve Van Westendorp metodolojisiyle gerçek mülakata gerek kalmadan ürün fikirlerini test eder.",
  inLanguage: "tr-TR",
  offers: [
    {
      "@type": "Offer",
      name: "Free Plan",
      price: "0",
      priceCurrency: "TRY",
      description: "2 araştırma/ay, 3 persona, temel rapor",
    },
    {
      "@type": "Offer",
      name: "Starter Plan",
      price: "990",
      priceCurrency: "TRY",
      priceSpecification: {
        "@type": "UnitPriceSpecification",
        price: "990",
        priceCurrency: "TRY",
        unitText: "MON",
      },
      description: "10 araştırma/ay, 5 persona, PDF rapor, Van Westendorp",
    },
    {
      "@type": "Offer",
      name: "Pro Plan",
      price: "2990",
      priceCurrency: "TRY",
      priceSpecification: {
        "@type": "UnitPriceSpecification",
        price: "2990",
        priceCurrency: "TRY",
        unitText: "MON",
      },
      description: "Sınırsız araştırma, A/B Test, Adversarial Review, RFI skoru",
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
      name: "App-Q nedir?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "App-Q, yapıy zeka destekli sentetik pazar araştırması platformudur. Gerçek mülakat ve katılımcı rekrutümanı gerektirmeden, bilimsel olarak zemine oturtulmuş sentetik persona panelleriyle ürün fikirlerinizi, fiyatlandırmanızı ve mesajlaşmanızı test edersiniz.",
      },
    },
    {
      "@type": "Question",
      name: "Sentetik araştırma gerçek müşteri araştırmasının yerini tutar mı?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Hayır. App-Q bir hipotez ve araştırma triage aracıdır. Gerçek pazar testlerinden önce zaman ve büdçe kaybını azaltmak için kullanılır; gerçek müşteri araştırmasının yerini almaz. Platform çıktıları istatistiksel güven iddiasında bulunmaz.",
      },
    },
    {
      "@type": "Question",
      name: "Metodoloji ne kadar güvenilir?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "App-Q, Grounded Simulation mimarisini (Bilal, 2026) kullanır. Bağımsız akademik değlendirmede 46 çalışmada ortalama Araştırma Bütünlüğü Endeksi (RFI) = 0.815 elde edilmiştir. 23 kör UX araştırmacısının değlendirmesinde sistem uzman referans bulgularının %93\'lüne ulaşmış; değerlendiricilerin %65'i sistemin çıktısını insan üretimi olarak tanımlamıştır.",
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
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
