import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
