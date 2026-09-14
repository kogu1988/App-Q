import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Target, ArrowRight, BarChart2, MessageSquare, PenTool } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Growth Marketers | Clarere AI",
  description: "Kitleye harcama yapmadan önce kancayı test edin. Açılış sayfalarınızı, reklam kreatiflerinizi ve mesajlarınızı kitle segmentleri genelinde doğrulayın.",
};

export default function GrowthMarketersPage() {
  return (
    <div className="min-h-screen bg-canvas text-primary selection:bg-coral/20 font-sans antialiased">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-canvas/90 backdrop-blur-md border-b border-hairline px-6 h-16 flex items-center justify-between">
        <div className="max-w-5xl mx-auto w-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-85 transition-opacity" id="nav-logo-link">
            <Logo size={24} className="text-primary" />
            <span className="font-semibold text-primary tracking-tight text-lg">Clarere</span>
          </Link>
          <div className="flex items-center gap-6">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-[2px] bg-pale-green text-deep-green border border-deep-green/10 font-mono tracking-wider">
              GROWTH MARKETERS
            </span>
            <Link href="/" className="flex items-center gap-1 text-sm font-medium text-body-muted hover:text-primary transition-colors" id="nav-back-link">
              <ArrowLeft size={14} />
              <span className="hidden sm:inline">Geri Dön</span>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center border-b border-hairline">
        <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-4" id="hero-tag">
          KANCAYI (HOOK) TEST EDİN
        </span>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-primary max-w-4xl mx-auto leading-[1.05] mb-8" id="hero-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          Kitleye para harcamadan önce <span className="text-coral">kancayı</span> test edin.
        </h1>
        <p className="text-lg sm:text-xl text-body-muted max-w-2xl mx-auto leading-relaxed mb-10">
          Trafiğe bir dolar bile harcamadan önce; açılış sayfalarınızı, reklam kreatiflerinizi ve mesajlarınızı kitle segmentleri genelinde doğrulayın.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <Link
            href="/client"
            className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-primary text-canvas font-medium text-sm hover:opacity-90 transition-all text-center flex items-center justify-center gap-2"
            id="hero-cta-trial"
          >
            Ücretsiz Dene <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      {/* Büyüme Ekiplerinin Karşılaştığı Sorunlar */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">KARŞILAŞILAN SORUNLAR</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Büyüme ekipleri nerede bütçe kaybediyor?
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Öğrenmek İçin Harcamak</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Çoğu ekip neyin işe yaradığını öğrenmek için ücretli trafiğe güvenir. Her başarısız testte ortalama 2.000$ - 5.000$ reklam bütçesi boşa gider.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Sezgilere Dayalı Metinler</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Başlıklar, kitlenin gerçekten neye tepki vereceğine göre değil, şirket içi toplantılarda kulağa hoş gelenlere göre seçilir.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Tek Mesaj Çıkmazı</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Kurumsal alıcıya da startup kurucusuna da aynı mesaj gönderilir; oysa ikisi tamamen farklı şeyler bekler.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Jenerik Yapay Zeka Metinleri</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Rakiplerle aynı varsayılan yapay zeka çıktılarını kullanmak, markanızın farklılaşmasını engeller ve CTR düşüşüne neden olur.
            </p>
          </div>
        </div>
      </section>

      {/* Kullanım Alanları */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">CLARERE BÜYÜME ÇÖZÜMLERİ</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Growth Marketer&apos;lar için sentetik testler
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <BarChart2 size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">A/B Testi</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Ücretli trafik basmadan önce hangi sayfanın dönüştüreceğini bulun. İki varyant yükleyin, itirazları ve tercih nedenlerini öğrenin.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <MessageSquare size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Mesajlaşma Testi</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              5 farklı başlığı farklı segmentler (Enterprise, SMB, Startup) üzerinde test edin. Takım tercihine göre değil, kitle tepkisine göre seçim yapın.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <PenTool size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Kreatif (Creative)</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Prodüksiyon maliyetlerine girmeden önce reklam konseptlerini doğrulayın. Hangi açının yankı uyandıracağını önceden bilin.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <Target size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Segmentasyon</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Bir dolar bile harcamadan önce her segmentin nasıl düşündüğünü (motivasyonlar, itirazlar, karar tetikleyicileri) anlayın.
            </p>
          </div>
        </div>
      </section>

      {/* Verimlilik ve Risk Yönetimi (Table) */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">EKONOMİ VE VERİMLİLİK</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Matematik Çok Basit
          </h2>
          <p className="text-sm text-body-muted mt-2">
            Bir aylık başarısızlık payı yakalamak, tüm yıllık abonelik maliyetini karşılar.
          </p>
        </div>

        <div className="overflow-x-auto rounded-[8px] border border-hairline">
          <table className="w-full text-sm border-collapse text-left">
            <thead>
              <tr className="border-b border-hairline bg-muted-surface">
                <th className="px-5 py-4 font-semibold text-muted-text text-xs">Metrik</th>
                <th className="px-5 py-4 font-semibold text-body-muted text-xs">Geleneksel A/B Testi</th>
                <th className="px-5 py-4 font-bold text-deep-green text-xs bg-pale-green/60 border-l border-r border-deep-green/20">Clarere Çalışması</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-card-border bg-white">
                <td className="px-5 py-4 font-bold text-primary">Maliyet</td>
                <td className="px-5 py-4 text-body-muted">2.000$ - 5.000$ reklam harcaması + prodüksiyon</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">Çalışma başına 8$ - 20$</td>
              </tr>
              <tr className="border-b border-card-border bg-gray-surface">
                <td className="px-5 py-4 font-bold text-primary">Hız</td>
                <td className="px-5 py-4 text-body-muted">İstatistiksel anlamlılık için 2-4 hafta</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">Sonuçlar 2 dakikada hazır</td>
              </tr>
              <tr className="bg-white">
                <td className="px-5 py-4 font-bold text-primary">Kapasite</td>
                <td className="px-5 py-4 text-body-muted">Bütçe sınırı nedeniyle en fazla 1-2 başlık</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">Bir başarısız reklam fiyatına 10 farklı başlık test edilebilir</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* SSS */}
      <section className="bg-white surface-stone py-20 px-6 border-b border-hairline">
        <div className="max-w-3xl mx-auto">
          <div className="mb-10">
            <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">MERAK EDİLENLER</span>
            <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
              Sıkça Sorulan Sorular
            </h2>
          </div>

          <div className="space-y-0">
            {[
              {
                q: "Dönüşüm Oranı Optimizasyonu (CRO) için nasıl yardımcı olur?",
                a: "Canlı veriler neyin çalışmadığını söyler ama \"neden\"ini söylemez. Clarere, bilişsel sürtünmeleri ve zayıf değer önerilerini anında tespit eder.",
              },
              {
                q: "Reklam metinlerini test edebilir miyim?",
                a: "Evet, binlerce gösterim (impressions) beklemeden dakikalar içinde kalitatif analiz yapabilirsiniz.",
              },
              {
                q: "Yeni kitle segmentleri belirleyebilir miyim?",
                a: "Geniş bir persona yelpazesi oluşturarak, hangi demografik özelliklerin veya kişilik tiplerinin ürününüze daha güçlü çekildiğini görebilirsiniz.",
              },
              {
                q: "Huninin (Funnel) farklı aşamaları için nasıl çalışır?",
                a: "ToFu (Huninin üstü) için netlik ve merakı; BoFu (Huninin altı) için ise son itirazları ve korkuları simüle edilmiş görüşmelerle test edebilirsiniz.",
              },
            ].map(({ q, a }, i) => (
              <details key={i} className="group border-b border-hairline py-1">
                <summary className="flex items-start justify-between py-4 cursor-pointer font-medium text-base text-primary hover:text-ink list-none gap-4">
                  <span>{q}</span>
                  <span className="text-muted-text group-open:rotate-45 transition-transform duration-200 text-xl font-light shrink-0 mt-0.5">+</span>
                </summary>
                <div className="pb-5 text-sm text-body-muted leading-relaxed max-w-2xl">
                  {a}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-canvas px-6 py-20 border-t border-hairline text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-canvas leading-[1.1] mb-6" id="cta-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Bütçenizi Boşa Harcamayın
          </h2>
          <p className="text-base text-white/60 mb-10 max-w-md mx-auto">
            1 aylık ücretsiz deneme (Kredi kartı gerekmez).
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-sm mx-auto">
            <Link
              href="/client"
              className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-canvas text-primary font-medium text-sm hover:opacity-90 transition-all text-center"
              id="cta-trial-btn"
            >
              Ücretsiz Denemeye Başla
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-hairline bg-canvas py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Logo size={24} className="text-muted-text" />
            <span className="text-sm text-muted-text">Clarere © 2026</span>
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-text">
            <Link href="/guide" className="hover:text-primary transition-colors">Kullanım Kılavuzu</Link>
            <Link href="/#faq" className="hover:text-primary transition-colors">SSS</Link>
            <Link href="/privacy" className="hover:text-primary transition-colors">Gizlilik</Link>
            <Link href="/terms" className="hover:text-primary transition-colors">Kullanım Koşulları</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
