import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Target, ShieldCheck, Zap, ArrowRight, CheckCircle, Search, FileText } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Danışmanlar İçin Clarere | Kitle İçgörüleri",
  description: "Her müşteri toplantısına, onların hedef kitlesini zaten tanıyarak girin. Yeni sektörlerde hızlı uzmanlaşma ve kanıta dayalı öneriler.",
};

export default function ConsultantsPage() {
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
              DANIŞMANLAR İÇİN
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
          HEDEF KİTLEYİ TANIYARAK GİRİN
        </span>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-primary max-w-4xl mx-auto leading-[1.05] mb-8" id="hero-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          Her müşteri toplantısına hedef kitleyi <span className="text-coral">zaten tanıyarak</span> girin.
        </h1>
        <p className="text-lg sm:text-xl text-body-muted max-w-2xl mx-auto leading-relaxed mb-10">
          Yeni bir iş, bilmediğiniz bir sektör mü? İlk toplantıdan önce bir kullanıcı araştırması yapın. Sezgilerle değil, metodolojiyle desteklenen kitle içgörüleriyle masaya oturun.
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

      {/* Sorunlar */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">KARŞILAŞILAN ZORLUKLAR</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Danışmanların ve Geçici CMO&apos;ların Karşılaştığı Sorunlar
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">İçgüdüyle Başlamak</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Her işe &quot;48 saatte uzman ol&quot; baskısıyla başlanır. Masa başı araştırmalar ilk toplantınızın onuncu toplantıymış gibi hissettirmesini sağlamaz.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Güvenilirlik Boşluğu</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Önerileriniz arkasındaki kanıt kadar güçlüdür. &quot;Deneyimlerime dayanarak&quot; argümanı müşteri incelemesinde her zaman yeterli olmaz.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Araştırma Bütçesi Yokluğu</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              Müşteriler strateji için ödeme yapar, tam bir araştırma süreci için değil. En büyük stratejik avantajınız olan kitle içgörüsü için fatura kesemezsiniz.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col">
            <h3 className="text-lg font-bold text-primary mb-3">Jenerik Yapay Zeka Çıktıları</h3>
            <p className="text-sm text-body-muted leading-relaxed">
              ChatGPT&apos;ye sormak sizi diğer danışmanlardan farklı kılmaz; içgörü herkesinkine benzer olur ve stratejik derinlik kaybolur.
            </p>
          </div>
        </div>
      </section>

      {/* Kullanım Alanları */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">CLARERE KULLANIM ALANLARI</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Danışmanlar İçin Çözümler
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <Search size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Müşteri Keşfi</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              İlk toplantıdan (kickoff) önce müşterinizin kitlesini anlayın. Masaya oturmadan önce hipotezleri test edin.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <CheckCircle size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Kanıta Dayalı Öneriler</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Her öneriyi yapılandırılmış araştırmalarla destekleyin. &quot;Bana güvenin&quot; yerine kaynağı ve kanıtı gösterin.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <Target size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Rekabetçi Zeka</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Müşterinizin kitlesinin onları rakiplere karşı nasıl gördüğünü test edin. Konumlandırma açıklarını anlayın.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline">
            <div className="w-10 h-10 rounded-[4px] bg-pale-green text-deep-green flex items-center justify-center mb-4 shrink-0">
              <FileText size={20} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Araştırmayı Çıktı Olarak Sunma</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Yapılandırılmış araştırmayı faturalandırılabilir bir çıktıya dönüştürün. Danışmanlık tavsiyelerini dışa aktarılabilir raporlara çevirin.
            </p>
          </div>
        </div>
      </section>

      {/* İş Akışı Örneği */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="max-w-3xl mb-12">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">&quot;PAZARTESİ SABAHI AVANTAJI&quot;</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            İş Akışı Örneği
          </h2>
          <p className="text-body-muted text-sm mt-2">
            Clarere ile ilk müşteri toplantısına nasıl 10 adım önde girdiğinizi görün.
          </p>
        </div>

        <div className="relative pl-6 sm:pl-8 border-l border-hairline space-y-12 max-w-3xl">
          {/* Item 1 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-coral border-4 border-canvas" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-coral">CUMA 16:00</span>
              <span className="text-xs text-muted-text hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-primary">Yeni Bir İş</h3>
            </div>
            <p className="text-sm text-body-muted leading-relaxed">
              Hiç bilmediğiniz bir sağlık girişimiyle (startup) yeni bir iş başlar. Kickoff Pazartesi günüdür.
            </p>
          </div>

          {/* Item 2 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-coral border-4 border-canvas" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-coral">CUMA 16:15</span>
              <span className="text-xs text-muted-text hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-primary">Araştırma Başlatılır</h3>
            </div>
            <p className="text-sm text-body-muted leading-relaxed">
              Clarere çalışması başlatılır (Hedef kitle: 28-45 yaş, sağlık bilinci yüksek alıcılar). 12 persona oluşturulur ve görüşmeler yapılır.
            </p>
          </div>

          {/* Item 3 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-coral border-4 border-canvas" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-coral">CUMA 17:00</span>
              <span className="text-xs text-muted-text hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-primary">Rapor Teslim Edilir</h3>
            </div>
            <p className="text-sm text-body-muted leading-relaxed">
              Kritik bulgu: &quot;Mevzuata uygunluk (compliance) sinyalleri, özellik derinliğinden daha önemlidir.&quot;
            </p>
          </div>

          {/* Item 4 */}
          <div className="relative">
            <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-coral border-4 border-canvas" />
            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
              <span className="font-mono text-sm font-bold text-coral">PAZARTESİ 09:00</span>
              <span className="text-xs text-muted-text hidden sm:inline">·</span>
              <h3 className="text-base font-bold text-primary">Toplantı</h3>
            </div>
            <p className="text-sm text-body-muted leading-relaxed">
              Toplantıya müşterinin beklemediği bir hazırlıkla girersiniz. Sohbet &quot;tanışma&quot; aşamasından &quot;neler yapmalıyız&quot; aşamasına anında geçer.
            </p>
          </div>
        </div>
      </section>

      {/* Gelir Modeli */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">REKABETÇİ AVANTAJ VE GELİR MODELİ</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Araştırmayı faturalandırılabilir bir hizmete dönüştürün
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          <div className="p-8 rounded-[8px] border border-hairline bg-soft-stone/20 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-9 h-9 rounded-[4px] bg-deep-green flex items-center justify-center text-canvas">
                <ShieldCheck size={18} />
              </div>
              <h3 className="text-xl font-bold text-primary">Hazırlık Aracı Olarak</h3>
              <p className="text-sm text-body-muted leading-relaxed">
                Geleneksel paneller 5.000$ - 15.000$ maliyet yaratırken, Clarere aylık planlarla sınırsız hazırlık imkanı sunar. Stratejik kararlarınızı kendi maliyetleriniz içinde en aza indirerek güçlendirin.
              </p>
            </div>
          </div>

          <div className="p-8 rounded-[8px] border border-hairline bg-primary text-canvas flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-9 h-9 rounded-[4px] bg-coral flex items-center justify-center text-canvas">
                <Zap size={18} />
              </div>
              <h3 className="text-xl font-bold text-canvas">Faturalandırılabilir Çıktı</h3>
              <p className="text-sm text-white/70 leading-relaxed">
                Bir araştırmayı müşteriye 500$ - 1.500$ bandında faturalandırın. Platform maliyeti çalışma başına sadece 8$ - 20$&apos;dır. Ayda sadece 2 çalışma ile tüm abonelik maliyetinizi karşılayıp net kâr elde edebilirsiniz.
              </p>
            </div>
            <div className="pt-6 border-t border-white/10 mt-6 flex items-center justify-between text-sm">
              <span className="text-white/60">Rapor Başına Kâr</span>
              <span className="font-mono font-bold text-coral">98%</span>
            </div>
          </div>
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
                q: "Otorite kurmaya nasıl yardımcı olur?",
                a: "Görüşler yerine kanıtlarla ortaya çıkmak daha güçlüdür. Acı noktaları ve pazar dinamikleri hakkında en baştan güvenle konuşmanızı sağlar.",
              },
              {
                q: "İşimi ölçeklendirmeme yardımcı olur mu?",
                a: "Manuel araştırma ve sentez süresini azaltarak, ek yük getirmeden daha fazla müşteriye destek vermenizi sağlar.",
              },
              {
                q: "Niş kitlelerde nasıl yardımcı olur?",
                a: "Bilmediğiniz veya uzmanlık gerektiren pazarlarda, roller ve karar kalıpları etrafında hızlıca bilgi sahibi olmanızı sağlar.",
              },
              {
                q: "Metodoloji şeffaf mı?",
                a: "Evet, Clarere 'kapalı kutu' (black-box) çıktılar yerine metodoloji destekli, yapılandırılmış araştırmalar sunar; bu da önerilerinizin savunulabilir olmasını sağlar.",
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
            Rakiplerinizden Ayrışın
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
