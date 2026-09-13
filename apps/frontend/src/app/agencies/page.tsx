import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Target, ShieldCheck, Zap, Coins, Clock, ArrowRight } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Ajanslar İçin Clarere | Sunum ve Strateji Gücü",
  description: "ChatGPT'nin müşterinizin hedef kitlesi hakkında ne düşündüğünü sunmayı bırakın. 2 dakikada gerçekçi sentetik kitle araştırması yapın ve her sunuma (pitch) gerçek içgörülerle girin.",
};

export default function AgenciesPage() {
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
              AJANSLAR İÇİN
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
          PITCH SÜREÇLERİNDE FARK YARATIN
        </span>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-[#17171c] max-w-4xl mx-auto leading-[1.05] mb-8" id="hero-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          ChatGPT&apos;nin müşterinizin hedef kitlesi hakkında ne düşündüğünü sunmayı bırakın.
        </h1>
        <p className="text-lg sm:text-xl text-[#616161] max-w-2xl mx-auto leading-relaxed mb-10">
          2 dakikada yapılandırılmış bir kitle çalışması yapın ve her sunuma (pitch) gerçek kitle içgörülerinden elde edilen kanıtlarla girin.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <Link
            href="/client"
            className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#17171c] text-[#ffffff] font-medium text-sm hover:opacity-90 transition-all text-center flex items-center justify-center gap-2"
            id="hero-cta-trial"
          >
            Hemen Başla <ArrowRight size={14} />
          </Link>
          <a
            href="mailto:hiclarere@clarere.com?subject=Ajans Talebi"
            className="w-full sm:w-auto px-6 py-3.5 rounded-full border border-[#d9d9dd] hover:border-[#17171c] text-[#17171c] font-medium text-sm transition-all text-center"
            id="hero-cta-mail"
          >
            Özel Teklif Alın
          </a>
        </div>

        {/* Problem/Solution Card */}
        <div className="mt-16 p-6 sm:p-8 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/30 text-left max-w-4xl mx-auto flex flex-col md:flex-row gap-6 items-start">
          <div className="md:w-1/3">
            <span className="mono-label text-[#ff7759] text-[10px] uppercase font-mono tracking-wider block mb-2">Karşılaşılan Zorluk</span>
            <h2 className="text-lg font-bold text-[#17171c]">Brief elinize dün ulaştı ve sadece 10 gününüz mü var?</h2>
          </div>
          <div className="md:w-2/3 text-sm text-[#616161] leading-relaxed space-y-3">
            <p>
              Geleneksel pazar araştırmaları haftalar sürer ve binlerce liralık bütçe gerektirir. Bütçenin olmadığı veya zamanın kısıtlı olduğu durumlarda ajanslar genellikle jenerik ChatGPT çıktılarından devşirme yüzeysel stratejiler sunmak zorunda kalır.
            </p>
            <p className="text-[#17171c] font-semibold">
              Clarere, bu kısır döngüyü kırarak 2 dakika içinde bilimsel altyapıya dayanan, alıntılanabilir sentetik mülakatlar ve A/B test raporları üretir.
            </p>
          </div>
        </div>
      </header>

      {/* Features Grid */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">AJANSLAR İÇİN ÖNE ÇIKANLAR</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Stratejinizi kanıtlarla destekleyin
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-[8px] border border-[#d9d9dd] hover:border-[#ff7759]/40 transition-all flex flex-col">
            <div className="w-10 h-10 rounded-[4px] bg-[#ff7759] flex items-center justify-center mb-6 shrink-0 text-[#ffffff]">
              <Target size={20} />
            </div>
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Sektör Zekası (Domain Intelligence)</h3>
            <p className="text-sm text-[#616161] leading-relaxed flex-1">
              Brief elinize dün geçmiş olsa bile, o pazarda yıllardır faaliyet gösteriyormuşçasına bilgi sahibi olun. 12 farklı demografik ve davranışsal sentetik persona ile derinlemesine kitle reflekslerini saniyeler içinde analiz edin.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] hover:border-[#ff7759]/40 transition-all flex flex-col">
            <div className="w-10 h-10 rounded-[4px] bg-[#ff7759] flex items-center justify-center mb-6 shrink-0 text-[#ffffff]">
              <ShieldCheck size={20} />
            </div>
            <h3 className="text-lg font-bold text-[#17171c] mb-3">White-Label Raporlar</h3>
            <p className="text-sm text-[#616161] leading-relaxed flex-1">
              Müşterilerinizin doğruluğunu asla sorgulayamayacağı, tamamen kaynaklandırılmış ve sunuma hazır zengin PDF raporlar. Çıktılarınızı kendi ajans logonuz ve renklerinizle kişiselleştirerek doğrudan müşterinize sunun.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] hover:border-[#ff7759]/40 transition-all flex flex-col">
            <div className="w-10 h-10 rounded-[4px] bg-[#ff7759] flex items-center justify-center mb-6 shrink-0 text-[#ffffff]">
              <Clock size={20} />
            </div>
            <h3 className="text-lg font-bold text-[#17171c] mb-3">2 Dakikalık Sprintler</h3>
            <p className="text-sm text-[#616161] leading-relaxed flex-1">
              Pazartesi sabahı gelen ani bir brief için salı sabahına kadar kanıta dayalı, gerçek alıntılarla süslenmiş bir strateji belgesi oluşturun. Hızınızla rakiplerinizin günlerce süren araştırmalarını ekarte edin.
            </p>
          </div>
        </div>
      </section>

      {/* 72-Hour Sprint (Vertical Timeline) */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="max-w-3xl mb-12">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">İŞ AKIŞI ÖRNEĞİ</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            72 Saatlik Pitch Sprinti
          </h2>
          <p className="text-[#616161] text-sm mt-2">
            Clarere ile geleneksel bir ajansın haftalar süren pazar araştırması döngüsünü 3 güne sığdırabilirsiniz.
          </p>
        </div>

        {/* Timeline Layout */}
        <div className="relative pl-6 sm:pl-8 border-l border-[#d9d9dd] space-y-12 max-w-3xl">
          {/* Item 1 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-[#ff7759] border-4 border-[#ffffff]" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-[#ff7759]">PAZARTESİ 09:00</span>
              <span className="text-xs text-[#93939f] hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-[#17171c]">Yeni Brief ve Bilinmeyen Sektör</h3>
            </div>
            <p className="text-sm text-[#616161] leading-relaxed">
              Ajansınıza daha önce hiç çalışmadığınız bir sektörden (örneğin: biyoteknoloji tabanlı bir fitness girişimi) acil bir konkur/pitch brief&apos;i gelir. Hedef kitleyi ve onların dilini çözmek için strateji ekibinin elinde hiçbir veri yoktur.
            </p>
          </div>

          {/* Item 2 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-[#ff7759] border-4 border-[#ffffff]" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-[#ff7759]">PAZARTESİ 10:15</span>
              <span className="text-xs text-[#93939f] hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-[#17171c]">Clarere Raporu ve Kritik İçgörüler</h3>
            </div>
            <p className="text-sm text-[#616161] leading-relaxed">
              Clarere üzerinde 12 sentetik personadan oluşan pazar panelini kurarsınız. 2 dakika sonra rapor teslim edilir. Personaların cevaplarından kritik bir bulgu ortaya çıkar: <em className="text-[#17171c] font-semibold not-italic">&quot;Kullanıcılar için fitness özellik listelerinden ziyade, veri güvenliği sinyalleri satın almada 1. sıradadır.&quot;</em>
            </p>
          </div>

          {/* Item 3 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-[#ff7759] border-4 border-[#ffffff]" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-[#ff7759]">SALI SABAHI</span>
              <span className="text-xs text-[#93939f] hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-[#17171c]">Kanıta Dayalı Sunum ve Onay</h3>
            </div>
            <p className="text-sm text-[#616161] leading-relaxed">
              Müşteriye rakiplerinizin aksine Google aramalarından derlenmiş klişeler yerine, Clarere panelindeki gerçekçi alıntılarla desteklenmiş veri odaklı bir strateji sunarsınız. Güven odaklı bu nokta atışı yaklaşım sayesinde ajans konkurdan galibiyetle ayrılır.
            </p>
          </div>
        </div>
      </section>

      {/* Revenue & Gelir Modeli */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">İŞ MODELİ VE GELİR</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Araştırmayı lüks olmaktan çıkarın, gelire dönüştürün
          </h2>
          <p className="text-sm text-[#616161] mt-2">
            Clarere sadece konkur kazanmanızı sağlamaz, aynı zamanda ajansınız için yeni bir faturalandırılabilir gelir kalemi oluşturur.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          {/* Card 1: Maliyet Boyutu */}
          <div className="p-8 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-9 h-9 rounded-[4px] bg-[#003c33] flex items-center justify-center text-[#ffffff]">
                <Coins size={18} />
              </div>
              <h3 className="text-xl font-bold text-[#17171c]">100 Kat Daha Düşük Maliyet</h3>
              <p className="text-sm text-[#616161] leading-relaxed">
                Geleneksel panellerde ve fokus gruplarında araştırma başına 5.000$ - 15.000$ arasında maliyetler oluşurken, Clarere bu gücü aylık abonelik paketleri sayesinde son derece makul bir seviyeye indirir. Strateji maliyetlerinizi minimuma çekerek kârlılığınızı artırın.
              </p>
            </div>
            <div className="pt-6 border-t border-[#d9d9dd] mt-6 flex items-center justify-between text-sm">
              <span className="text-[#616161]">Geleneksel Panel</span>
              <span className="font-mono font-bold text-[#b30000]">5.000$ - 15.000$</span>
            </div>
          </div>

          {/* Card 2: Gelir Boyutu */}
          <div className="p-8 rounded-[8px] border border-[#d9d9dd] bg-[#17171c] text-[#ffffff] flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-9 h-9 rounded-[4px] bg-[#ff7759] flex items-center justify-center text-[#ffffff]">
                <Zap size={18} />
              </div>
              <h3 className="text-xl font-bold text-[#ffffff]">Yeni Bir Gelir Kalemi</h3>
              <p className="text-sm text-white/70 leading-relaxed">
                Araştırma raporlarını müşterilerinize katma değerli birer strateji paketi olarak faturalandırın. Platform maliyeti 8$ - 20$ bandında olan bir sentetik çalışmayı müşteriye markalı bir çıktı olarak satarak, ayda sadece 2 çalışma ile tüm platform abonelik maliyetinizi amorti edip kâra geçebilirsiniz.
              </p>
            </div>
            <div className="pt-6 border-t border-white/10 mt-6 flex items-center justify-between text-sm">
              <span className="text-white/60">Rapor Başına Gelir Fırsatı</span>
              <span className="font-mono font-bold text-[#ff7759]">₺5.000 - ₺15.000</span>
            </div>
          </div>
        </div>
      </section>

      {/* SSS Modülü */}
      <section className="max-w-3xl mx-auto px-6 py-20">
        <div className="mb-12 text-center">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">MERAK EDİLENLER</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Ajanslar İçin Sıkça Sorulan Sorular
          </h2>
        </div>

        <div className="space-y-1">
          {[
            {
              q: "Pitch / Konkur süreçlerinde nasıl yardımcı olur?",
              a: "Geleneksel sunumlardaki 'bize göre, içgüdülerimize göre' savunmalarının yerini gerçekçi kanıtlarla doldurmanızı sağlar. Toplantılara hedef kitlenin spesifik itirazlarını, marka algılarını ve net mesaj analizlerini bilerek girer, müşterinize rakiplerinizin sunamayacağı bir pazar gerçekliği sunarsınız.",
            },
            {
              q: "Mevcut araştırma departmanımızın yerini mi alır?",
              a: "Kesinlikle hayır. Clarere bir ikame değil, araştırma departmanınız için bir güç çarpanıdır (force multiplier). Hızlı fikir doğrulama, erken aşama kitle reflekslerini anlama gibi operasyonel süreçleri üstlenerek kıdemli araştırmacılarınızın daha derin, niteliksel ve insan odaklı büyük stratejilere odaklanmasını sağlar.",
            },
            {
              q: "Hangi sektörlerde ve ülkelerde çalışmaktadır?",
              a: "Clarere altyapısı, 37 farklı sektör ve 69 ülkede davranış bilimleri modeliyle aktiftir. Daha önce hiç çalışmadığınız niş pazarlarda bile ilgili kitlenin satın alma alışkanlıklarına ve kültürel reflekslerine (taksit eğilimleri, pazarlık yaklaşımları vs.) dakikalar içinde adapte olursunuz.",
            },
            {
              q: "Clarere üzerinde yaratıcı testler (creative testing) yapılabilir mi?",
              a: "Evet. Konseptlerinizi, reklam mesajlarınızı, açılış sayfası metin taslaklarınızı ve konumlandırma alternatiflerinizi hedef sentetik kitleye doğrudan sunarak, hangisinin itirazları en aza indirdiğini ve en yüksek satın alma motivasyonunu tetiklediğini test edebilirsiniz.",
            },
          ].map(({ q, a }, idx) => (
            <details key={idx} className="group border-b border-[#d9d9dd] py-1" id={`faq-details-${idx}`}>
              <summary className="flex items-start justify-between py-4 cursor-pointer font-medium text-base text-[#17171c] hover:text-[#ff7759] list-none gap-4">
                <span>{q}</span>
                <span className="text-[#93939f] group-open:rotate-45 transition-transform duration-200 text-xl font-light shrink-0 mt-0.5">+</span>
              </summary>
              <div className="pb-5 text-sm text-[#616161] leading-relaxed max-w-2xl">
                {a}
              </div>
            </details>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-[#17171c] text-[#ffffff] px-6 py-20 border-t border-[#d9d9dd] text-center">
        <div className="max-w-3xl mx-auto">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-4" id="cta-label">
            AJANSINIZI BİR ADIM ÖNE TAŞIYIN
          </span>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#ffffff] leading-[1.1] mb-6" id="cta-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Bir sonraki sunumunuza<br />veri odaklı kanıtlarla girin
          </h2>
          <p className="text-base text-white/60 mb-10 max-w-md mx-auto">
            Hemen ücretsiz deneme başlatın veya ajans ekibiniz için özel bir entegrasyon toplantısı talep edin.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-sm mx-auto">
            <Link
              href="/client"
              className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#ffffff] text-[#17171c] font-medium text-sm hover:opacity-90 transition-all text-center"
              id="cta-trial-btn"
            >
              Ücretsiz Başlat
            </Link>
            <a
              href="mailto:hiclarere@clarere.com?subject=Ajans Demo Talebi"
              className="w-full sm:w-auto px-6 py-3.5 rounded-full border border-white/20 hover:border-white text-white font-medium text-sm transition-all text-center"
              id="cta-mail-btn"
            >
              Demo Görüşmesi Yapın
            </a>
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
            <Link href="/privacy" className="hover:text-[#17171c] transition-colors">Gizlilik</Link>
            <Link href="/terms" className="hover:text-[#17171c] transition-colors">Kullanım Koşulları</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
