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
    "Gerçek mülakatlardan önce sentetik tüketici panelleriyle ürün fikirlerinizi test edin. Rogers Diffusion, OCEAN psikometri ve Grounded Simulation metodolojisiyle saatler içinde karar alınabilir içgörü.",
  keywords: ["sentetik pazar araştırması", "yapay zeka", "persona simülasyonu", "Van Westendorp", "Rogers Diffusion"],
  openGraph: {
    title: "App-Q — Yapay Zeka Destekli Sentetik Pazar Araştırması",
    description:
      "Gerçek mülakatlardan önce sentetik tüketici panelleriyle ürün fikirlerinizi test edin.",
    type: "website",
    locale: "tr_TR",
    siteName: "App-Q",
  },
  twitter: {
    card: "summary_large_image",
    title: "App-Q — Sentetik Pazar Araştırması",
    description: "Rogers Diffusion + OCEAN psikometrisi ile AI destekli tüketici panel simülasyonu.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
