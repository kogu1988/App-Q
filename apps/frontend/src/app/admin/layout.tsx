import type { Metadata } from "next";

// Yönetici paneli — arama motorlarında görünmemeli
export const metadata: Metadata = {
  title: "App-Q Yönetici Paneli",
  robots: {
    index: false,
    follow: false,
    googleBot: { index: false, follow: false },
  },
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
