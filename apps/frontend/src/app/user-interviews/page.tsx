import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Zap, Brain, Layers, ArrowRight } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Kullanıcı Görüşme Platformu | Clarere AI",
  description: "Kimseyi işe almadan (recruiting) kullanıcı görüşmeleri yapın. Düşünen, itiraz eden ve bağımsız görüşleri olan yapay zeka personaları dakikalar içinde hazır.",
};

export default function UserInterviewsPage() {
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
              MÜLAKAT PLATFORMU
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
          KATILIMCI BULMA SÜRECİNE SON
        </span>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-primary max-w-4xl mx-auto leading-[1.05] mb-8" id="hero-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          Kimseyi işe almadan kullanıcı görüşmeleri yapın.
        </h1>
        <p className="text-lg sm:text-xl text-body-muted max-w-2xl mx-auto leading-relaxed mb-10">
          Düşünen, itiraz eden ve bağımsız görüşleri olan yapay zeka personaları dakikalar içinde hazır. Panel yok, planlama yok, teşvik ödemesi yok.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <Link
            href="/client"
            className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-primary text-canvas font-medium text-sm hover:opacity-90 transition-all text-center flex items-center justify-center gap-2"
            id="hero-cta-trial"
          >
            Ücretsiz Başla (2 Araştırma Hediye) <ArrowRight size={14} />
          </Link>
          <Link
            href="/#pricing"
            className="w-full sm:w-auto px-6 py-3.5 rounded-full border border-hairline hover:border-primary text-primary font-medium text-sm transition-all text-center"
            id="hero-cta-pricing"
          >
            Planları İncele
          </Link>
        </div>

        {/* Statistics highlights */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20 text-left">
            <span className="text-sm font-semibold text-body-muted block mb-1">Geleneksel Mülakatlar</span>
            <div className="text-3xl font-bold text-error font-mono mb-2">4-8 Hafta / $30.000</div>
            <p className="text-xs text-body-muted leading-relaxed">
              Katılımcı bulma, planlama, mülakat moderasyonu ve teşvik ödemeleri haftalarca sürer ve ajans bütçelerini tüketir.
            </p>
          </div>
          <div className="p-6 rounded-[8px] border border-hairline bg-pale-green/30 text-left">
            <span className="text-sm font-semibold text-deep-green block mb-1">Kritik Gerçeklik</span>
            <div className="text-3xl font-bold text-deep-green font-mono mb-2">Araştırmasız Karar</div>
            <p className="text-xs text-body-muted leading-relaxed">
              Ürün kararlarının önemli bir bölümü, bütçe ve zaman kısıtlılıkları sebebiyle kullanıcı araştırması ve mülakatlar yapılmadan alınır.
            </p>
          </div>
        </div>
      </header>

      {/* 4 Steps Section */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">2 DAKİKADA RAPORA GİDEN YOL</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            4 adımda mülakat sürecinizi başlatın
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="p-6 rounded-[8px] border border-hairline bg-canvas hover:border-coral/40 transition-all flex flex-col justify-between">
            <div>
              <span className="text-3xl font-mono font-extrabold text-coral block mb-4">01</span>
              <h3 className="text-base font-bold text-primary mb-2">Araştırma Hedefini Belirleyin</h3>
              <p className="text-xs text-body-muted leading-relaxed">
                Hedefinizi ve hipotezinizi söyleyin. Platform, personaların yanıtlarına göre değişen dinamik dallanma mantığına (branching logic) sahip bir mülakat senaryosu hazırlar.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-canvas hover:border-coral/40 transition-all flex flex-col justify-between">
            <div>
              <span className="text-3xl font-mono font-extrabold text-coral block mb-4">02</span>
              <h3 className="text-base font-bold text-primary mb-2">Yapay Zeka Paneli Oluşturun</h3>
              <p className="text-xs text-body-muted leading-relaxed">
                Rol, deneyim, bağlam ve kültürel arka plan seçin. 10 kişilik standart sentetik tüketici paneli otomatik olarak yapılandırılır (kurumsal planlarda özelleştirilebilir).
              </p>
            </div>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-canvas hover:border-coral/40 transition-all flex flex-col justify-between">
            <div>
              <span className="text-3xl font-mono font-extrabold text-coral block mb-4">03</span>
              <h3 className="text-base font-bold text-primary mb-2">Görüşmeleri Başlatın</h3>
              <p className="text-xs text-body-muted leading-relaxed">
                Her persona izole oturumlarda görüşülür. Sizin gizli hedefinizi veya hipotezlerinizi göremezler; bu sayede &quot;yaranma&quot; (sycophancy) ve &quot;grup düşüncesi&quot; (groupthink) engellenir.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-canvas hover:border-coral/40 transition-all flex flex-col justify-between">
            <div>
              <span className="text-3xl font-mono font-extrabold text-coral block mb-4">04</span>
              <h3 className="text-base font-bold text-primary mb-2">Sentez Raporunuzu Alın</h3>
              <p className="text-xs text-body-muted leading-relaxed">
                Mülakatlardan elde edilen ortak temalar, doğrudan alıntılar ve web doğrulamaları hasmâne denetimden (adversarial review) geçirilerek güvenilir PDF rapor halinde teslim edilir.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Methodology Section */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">BİLİMSEL ALTYAPI VE METODOLOJİ</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Sadece bir yapay zeka chatbot&apos;u değil
          </h2>
          <p className="text-sm text-body-muted mt-2">
            Clarere sentetik mülakat motoru, basit LLM promptlarının çok ötesinde, psikometrik ve davranışsal kurallara dayalı bilimsel bir mimariyle tasarlanmıştır.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20">
            <div className="w-8 h-8 rounded-[4px] bg-deep-green flex items-center justify-center text-white mb-4">
              <Layers size={16} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Context Isolation (İzole Bağlam)</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Sentetik personaların sizin araştırma hedefinizi ve onaylanmasını beklediğiniz hipotezleri görmesi engellenir. Bu sayede yapay zekanın en büyük sorunu olan onaylama yanlılığı (sycophancy bias) mimari düzeyde büyük ölçüde azaltılır.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20">
            <div className="w-8 h-8 rounded-[4px] bg-deep-green flex items-center justify-center text-white mb-4">
              <Brain size={16} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Cognitive Memory (Bilişsel Bellek)</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Personalar mülakat süresince kendi geçmiş ifadelerini ve tutarlılıklarını korur. Ancak bu hafıza, insan bilişsel yapısını taklit edecek şekilde zamanla solma (fading memory decay) ve sınırlı dikkat odağı ile modellenmiştir.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-hairline bg-soft-stone/20">
            <div className="w-8 h-8 rounded-[4px] bg-deep-green flex items-center justify-center text-white mb-4">
              <Zap size={16} />
            </div>
            <h3 className="text-base font-bold text-primary mb-2">Stance Diversity (Tutum Çeşitliliği)</h3>
            <p className="text-xs text-body-muted leading-relaxed">
              Sentetik paneliniz sadece onaylayan seslerden oluşmaz. Kurulan kitle algoritmik olarak dengelenir; böylece her panelde mutlaka şampiyonlar, pragmatistler, skeptikler ve agresif engelleyiciler yer alır.
            </p>
          </div>
        </div>
      </section>

      {/* Comparison Table Section */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-hairline">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">KARŞILAŞTIRMALI ANALİZ</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Araştırma Yöntemlerinin Kıyası
          </h2>
          <p className="text-sm text-body-muted mt-2">
            Clarere ile geleneksel mülakatları ve anket araçlarını hız, maliyet ve kalite ekseninde karşılaştırın.
          </p>
        </div>

        {/* Table layout */}
        <div className="overflow-x-auto rounded-[8px] border border-hairline">
          <table className="w-full text-sm border-collapse text-left">
            <thead>
              <tr className="border-b border-hairline bg-muted-surface">
                <th className="px-5 py-4 font-semibold text-muted-text text-xs">Metrik / Özellik</th>
                <th className="px-5 py-4 font-semibold text-body-muted text-xs">Geleneksel Paneller</th>
                <th className="px-5 py-4 font-semibold text-body-muted text-xs">Anket Araçları</th>
                <th className="px-5 py-4 font-bold text-deep-green text-xs bg-pale-green/60 border-l border-r border-deep-green/20">Clarere Görüşmeleri</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-card-border bg-white">
                <td className="px-5 py-4 font-bold text-primary">Hız</td>
                <td className="px-5 py-4 text-body-muted">2-6 Hafta</td>
                <td className="px-5 py-4 text-body-muted">Günler / Haftalar</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">2 Dakikanın Altında</td>
              </tr>
              <tr className="border-b border-card-border bg-gray-surface">
                <td className="px-5 py-4 font-bold text-primary">Maliyet</td>
                <td className="px-5 py-4 text-body-muted">$5.000 - $30.000</td>
                <td className="px-5 py-4 text-body-muted">$500 - $5.000</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">Aylık Planlar (Sınırsız)</td>
              </tr>
              <tr className="border-b border-card-border bg-white">
                <td className="px-5 py-4 font-bold text-primary">Yanlılık Önleme</td>
                <td className="px-5 py-4 text-body-muted">Sadece görüşmeci eğitimiyle</td>
                <td className="px-5 py-4 text-body-muted">Yok (Manipülatif sorular)</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">Hipoteze-kör, Tutum diversitesi</td>
              </tr>
              <tr className="bg-gray-surface">
                <td className="px-5 py-4 font-bold text-primary">İterasyon Hızı</td>
                <td className="px-5 py-4 text-body-muted">Tur başına haftalar</td>
                <td className="px-5 py-4 text-body-muted">Günler</td>
                <td className="px-5 py-4 font-bold text-deep-green bg-pale-green/40 border-l border-r border-deep-green/20">Dakikalar İçinde</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* SSS Section */}
      <section className="max-w-3xl mx-auto px-6 py-20">
        <div className="mb-12 text-center">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-2">MERAK EDİLENLER</span>
          <h2 className="text-3xl font-bold tracking-tight text-primary" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Mülakat Platformu SSS
          </h2>
        </div>

        <div className="space-y-1">
          {[
            {
              q: "Clarere sentetik personalarla nasıl görüşme yapar?",
              a: "Clarere, kişilik psikolojisi (OCEAN / Big Five), demografi ve yerel kültürel kodları taşıyan sanal kitle profilleri kurar. Yapay zeka moderatörümüz, bu kitlelerle önceden belirlenen senaryo ekseninde birebir ve canlı mülakatlar gerçekleştirerek her bir aşamayı kayıt altına alır.",
            },
            {
              q: "ChatGPT mülakatlarından temel farkı nedir?",
              a: "ChatGPT jenerik eğitim verisiyle cevap verir ve kullanıcının yönlendirmelerine yaranma eğilimi (sycophancy) gösterir. Clarere ise bağımsız çalışan çoklu sentetik ajan mimarisini kullanır. Personalar hipotezlerinizi bilmez, kendi aralarında fikir birliği sağlamaya zorlanmaz; bu sayede grup düşüncesi engellenir ve aykırı pazar itirazları gün yüzüne çıkar.",
            },
            {
              q: "Sentetik mülakat verilerinin doğruluk payı nedir?",
              a: "Sentetik görüşmeler yönlendirici hipotezler üretir; istatistiksel temsil iddiası taşımaz. Clarere çıktıları, gerçek kullanıcı araştırmasının yerini almak yerine onu daha odaklı planlamanıza yardımcı olur. Yüksek riskli kararlar gerçek kullanıcı, satış veya saha verisiyle doğrulanmalıdır.",
            },
            {
              q: "Yapay zeka moderatörü mülakatlarda derinlemesine takip soruları sorar mı?",
              a: "Evet. Clarere moderatör ajanları statik bir anket okuyucusu değildir. Sentetik katılımcı mülakat sırasında pazar açısından anlamlı veya sıra dışı bir cümle sarf ettiğinde, moderatör otomatik olarak senaryodan bağımsız 'neden' soruları yönlendirerek derinleşir (probing follow-ups).",
            },
          ].map(({ q, a }, idx) => (
            <details key={idx} className="group border-b border-hairline py-1" id={`faq-details-${idx}`}>
              <summary className="flex items-start justify-between py-4 cursor-pointer font-medium text-base text-primary hover:text-coral list-none gap-4">
                <span>{q}</span>
                <span className="text-muted-text group-open:rotate-45 transition-transform duration-200 text-xl font-light shrink-0 mt-0.5">+</span>
              </summary>
              <div className="pb-5 text-sm text-body-muted leading-relaxed max-w-2xl">
                {a}
              </div>
            </details>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-canvas px-6 py-20 border-t border-hairline text-center">
        <div className="max-w-3xl mx-auto">
          <span className="mono-label text-coral uppercase tracking-wider text-xs font-semibold font-mono block mb-4" id="cta-label">
            İLK SENTETİK MÜLAKATINI BAŞLAT
          </span>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-canvas leading-[1.1] mb-6" id="cta-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Zaman kaybetmeden<br />kitle içgörülerinizi toplayın
          </h2>
          <p className="text-base text-white/60 mb-10 max-w-md mx-auto">
            Hemen ücretsiz denemenizi başlatın. 2 araştırma tamamen hediye. Kredi kartı veya taahhüt gerekmez.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-sm mx-auto">
            <Link
              href="/client"
              className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-canvas text-primary font-medium text-sm hover:opacity-90 transition-all text-center"
              id="cta-trial-btn"
            >
              Ücretsiz Başlat (1 Aylık Deneme)
            </Link>
            <a
              href="mailto:hiclarere@clarere.com?subject=Görüşme Platformu Demosu"
              className="w-full sm:w-auto px-6 py-3.5 rounded-full border border-white/20 hover:border-white text-white font-medium text-sm transition-all text-center"
              id="cta-mail-btn"
            >
              Kurumsal Demo Talebi
            </a>
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
