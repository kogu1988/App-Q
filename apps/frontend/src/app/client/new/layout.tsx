import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Yeni Araştırma Başlat — Clarere",
  description: "Sentetik personalarla yeni bir pazar araştırması veya A/B testi başlatın. Ürün fikrinizi doğrulayın.",
};

export default function NewResearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
