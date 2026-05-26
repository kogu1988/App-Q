import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Target, ShieldCheck, Layers, AlertCircle, ArrowRight } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "B2B SaaS | Clarere AI",
  description: "Konumlandırmayı kurucu sezgileriyle değil, gerçek alıcı sinyalleriyle doğrulayın. B2B SaaS ekipleri için lansman öncesi test simülasyonları.",
};

export default function B2BSaaSPage() {
  return (
    <div className="min-h-screen bg-[#ffffff] text-[#17171c] selection:bg-[#ff7759]/20 font-sans antialiased">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#ffffff]/90 backdrop-blur-md border-b border-[#d9d9dd] px-6 h-16 flex items-center justify-between">
        <div className="max-w-5xl mx-auto w-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-85 transition-opacity" id="nav-logo-link">
            <Logo size={24} strokeColor="#17171c" />
            <span className="font-semibold text-[#17171c] tracking-tight text-lg">Clarere</span>
          </Link>
          <div className="flex items-center gap-6">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-[2px] bg-[#edfce9] text-[#003c33] border border-[#003c33]/10 font-mono tracking-wider">
              B2B SAAS
            </span>
            <Link href="/" className="flex items-center gap-1 text-sm font-medium text-[#616161] hover:text-[#17171c] transition-colors" id="nav-back-link">
              <ArrowLeft size={14} />
              <span className="hidden sm:inline">Geri Dön</span>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center border-b border-[#d9d9dd]">
        <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-4" id="hero-tag">
          GERÇEK ALICI SİNYALLERİ
        </span>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-[#17171c] max-w-4xl mx-auto leading-[1.05] mb-8" id="hero-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          Konumlandırmayı kurucu sezgileriyle değil, <span className="text-[#ff7759]">gerçek alıcı sinyalleriyle</span> doğrulayın.
        </h1>
        <p className="text-lg sm:text-xl text-[#616161] max-w-2xl mx-auto leading-relaxed mb-10">
          Mühendislik kaynaklarını taahhüt etmeden önce; kurumsal (enterprise), KOBİ (SMB) ve girişim (startup) segmentlerinde mesajlarınızı, özelliklerinizi ve konumlandırma açılarınızı test edin.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <Link
            href="/client"
            className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#17171c] text-[#ffffff] font-medium text-sm hover:opacity-90 transition-all text-center flex items-center justify-center gap-2"
            id="hero-cta-trial"
          >
            Ücretsiz Dene <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      {/* B2B SaaS Ekiplerinin Karşılaştığı Sorunlar */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">KARŞILAŞILAN SORUNLAR</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            B2B SaaS ekipleri nerede tıkanıyor?
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Körlemesine İnşa Etmek</h3>
            <p className="text-sm text-[#616161] leading-relaxed">
              Kararlar pazarın görüşü alınmadan, şirket içi görüşlerle veriliyor. Ürününüz pazarın değil, odadaki en yüksek sesli yöneticinin fikrine göre şekilleniyor.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Lansman İçin Tek Şans</h3>
            <p className="text-sm text-[#616161] leading-relaxed">
              Lansman sonrası yeniden konumlandırma 6+ ay maliyet yaratıyor, ancak lansman öncesi 10.000$+ araştırma bütçesi bulunamıyor.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Geri Bildirim Yankı Odası</h3>
            <p className="text-sm text-[#616161] leading-relaxed">
              Sadece &quot;power user&quot; (yoğun kullanıcı) veya ayrılan (churned) kullanıcıları duyuyorsunuz; ortadaki sessiz çoğunluğun fikri alınamıyor.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Jenerik Yapay Zeka</h3>
            <p className="text-sm text-[#616161] leading-relaxed">
              ChatGPT&apos;den gelen &quot;hero&quot; metinleri her yerde aynı kalıpları kullanıyor ve ürününüzün farklılaşmasını engelliyor.
            </p>
          </div>
        </div>
      </section>

      {/* Kullanım Alanları */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">CLARERE B2B KULLANIM ALANLARI</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            SaaS ürününüz için yapay zeka validasyonu
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="p-6 rounded-[8px] border border-[#d9d9dd]">
            <div className="w-10 h-10 rounded-[4px] bg-[#edfce9] text-[#003c33] flex items-center justify-center mb-4 shrink-0">
              <Target size={20} />
            </div>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Konumlandırma Testi</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Ana sayfayı yeniden yazmadan önce, hangi değer önerisinin (value prop) gerçekten karşılık bulduğunu bulun.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd]">
            <div className="w-10 h-10 rounded-[4px] bg-[#edfce9] text-[#003c33] flex items-center justify-center mb-4 shrink-0">
              <Layers size={20} />
            </div>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Özellik Önceliklendirme</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Sprint planlamasından önce, kurumsal segmentin KOBİ&apos;ye karşı neyi gerçekten istediğini öğrenin.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd]">
            <div className="w-10 h-10 rounded-[4px] bg-[#edfce9] text-[#003c33] flex items-center justify-center mb-4 shrink-0">
              <ShieldCheck size={20} />
            </div>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Rekabetçi Algı</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Kendinizi rakiplerin yanında adayların gözünden görün; bilmediğiniz itirazları gün yüzüne çıkarın.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd]">
            <div className="w-10 h-10 rounded-[4px] bg-[#edfce9] text-[#003c33] flex items-center justify-center mb-4 shrink-0">
              <AlertCircle size={20} />
            </div>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Churn Önleme</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Risk altındaki kullanıcıların anketlerde söylemediği şeyleri simüle edilmiş görüşmelerle duyun.
            </p>
          </div>
        </div>
      </section>

      {/* Verimlilik ve Risk Yönetimi (Table) */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">VERİMLİLİK VE RİSK</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Maliyet & Doğruluk Karşılaştırması
          </h2>
          <p className="text-sm text-[#616161] mt-2">
            Tek bir yanlış bahisten kaçınmak, yıllık abonelik maliyetini defalarca amorti eder.
          </p>
        </div>

        <div className="overflow-x-auto rounded-[8px] border border-[#d9d9dd]">
          <table className="w-full text-sm border-collapse text-left">
            <thead>
              <tr className="border-b border-[#d9d9dd] bg-[#f5f4f1]">
                <th className="px-5 py-4 font-semibold text-[#93939f] text-xs">Metrik</th>
                <th className="px-5 py-4 font-bold text-[#003c33] text-xs bg-[#edfce9]/60 border-l border-r border-[#003c33]/20">Clarere Etkisi</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#f2f2f2] bg-white">
                <td className="px-5 py-4 font-bold text-[#17171c]">Doğruluk</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">Uzman benchmark&apos;ları ile %86 eşleşme; ChatGPT/Claude&apos;dan 7.5 kat daha isabetli sonuçlar.</td>
              </tr>
              <tr className="border-b border-[#f2f2f2] bg-[#fafafa]">
                <td className="px-5 py-4 font-bold text-[#17171c]">Hız</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">Sorudan rapora sadece 30 dakika.</td>
              </tr>
              <tr className="bg-white">
                <td className="px-5 py-4 font-bold text-[#17171c]">Maliyet Karşılaştırması</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">Yanlış konumlandırma bahsi: 100.000$+ mühendislik maliyeti.<br />Clarere validasyon çalışması: 8$ - 20$.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* SSS */}
      <section className="bg-white surface-stone py-20 px-6 border-b border-[#d9d9dd]">
        <div className="max-w-3xl mx-auto">
          <div className="mb-10">
            <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">MERAK EDİLENLER</span>
            <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
              Sıkça Sorulan Sorular
            </h2>
          </div>

          <div className="space-y-0">
            {[
              {
                q: "Ürün-Pazar Uyumu (PMF) için nasıl kullanılır?",
                a: "Farklı alıcı segmentlerinde değer önerilerini test ederek ölçeklenmeden önce nerede direnç olduğunu görmenizi sağlar.",
              },
              {
                q: "Karmaşık B2B satın alma komiteleriyle nasıl başa çıkar?",
                a: "Kullanıcılar, teknik değerlendiriciler ve karar vericiler gibi farklı rollerin konumlandırmanıza nasıl tepki verdiğini ayrı ayrı değerlendirmenize yardımcı olur.",
              },
              {
                q: "Sprint döngüsüne entegre edilebilir mi?",
                a: "Bir çalışma 30 dakikadan kısa sürdüğü için sprint planlama seanslarında veya ürün kararlarından hemen önce kullanılabilir.",
              },
            ].map(({ q, a }, i) => (
              <details key={i} className="group border-b border-[#d9d9dd] py-1">
                <summary className="flex items-start justify-between py-4 cursor-pointer font-medium text-base text-[#17171c] hover:text-[#212121] list-none gap-4">
                  <span>{q}</span>
                  <span className="text-[#93939f] group-open:rotate-45 transition-transform duration-200 text-xl font-light shrink-0 mt-0.5">+</span>
                </summary>
                <div className="pb-5 text-sm text-[#616161] leading-relaxed max-w-2xl">
                  {a}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-[#17171c] text-[#ffffff] px-6 py-20 border-t border-[#d9d9dd] text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#ffffff] leading-[1.1] mb-6" id="cta-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Aksiyon Çağrısı
          </h2>
          <p className="text-base text-white/60 mb-10 max-w-md mx-auto">
            3 günlük ücretsiz deneme (Kredi kartı gerekmez).
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-sm mx-auto">
            <Link
              href="/client"
              className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#ffffff] text-[#17171c] font-medium text-sm hover:opacity-90 transition-all text-center"
              id="cta-trial-btn"
            >
              Ücretsiz Denemeye Başla
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#d9d9dd] bg-[#ffffff] py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Logo size={24} strokeColor="#93939f" />
            <span className="text-sm text-[#93939f]">Clarere © 2026</span>
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-[#93939f]">
            <Link href="/guide" className="hover:text-[#17171c] transition-colors">Kullanım Kılavuzu</Link>
            <Link href="/#faq" className="hover:text-[#17171c] transition-colors">SSS</Link>
            <Link href="/#pricing" className="hover:text-[#17171c] transition-colors">Fiyatlandırma</Link>
            <Link href="/privacy" className="hover:text-[#17171c] transition-colors">Gizlilik</Link>
            <Link href="/terms" className="hover:text-[#17171c] transition-colors">Kullanım Koşulları</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
