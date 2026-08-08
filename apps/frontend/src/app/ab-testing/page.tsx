import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Target, ShieldCheck, Zap, Layers, HelpCircle, Check, X, ArrowRight, BarChart2, MessageSquare, AlertCircle } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "A/B Test Simülasyon Platformu | Clarere AI",
  description: "Her A/B testi size hangi varyantın kazandığını söyler. Clarere size nedenini söyler. Sıfır trafik gereksinimi ile lansman öncesi sentetik A/B testi.",
};

export default function ABTestingPage() {
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
              A/B TEST SIMÜLASYONU
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
          TRAFİK BAĞIMSIZ A/B TESTLERİ
        </span>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-[#17171c] max-w-4xl mx-auto leading-[1.05] mb-8" id="hero-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
          Her A/B testi size hangi varyantın kazandığını söyler. <span className="text-[#ff7759]">Clarere size nedenini söyler.</span>
        </h1>
        <p className="text-lg sm:text-xl text-[#616161] max-w-2xl mx-auto leading-relaxed mb-10">
          İki varyantı yükleyin ve sadece kuru bir kazanan değil; kitlelerin neyi beğendiğini, neyden kafa karışıklığı yaşadığını gösteren yapılandırılmış bir araştırma raporu alın.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <Link
            href="/client"
            className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#17171c] text-[#ffffff] font-medium text-sm hover:opacity-90 transition-all text-center flex items-center justify-center gap-2"
            id="hero-cta-trial"
          >
            Sıfır Trafikle Test Et <ArrowRight size={14} />
          </Link>
          <Link
            href="/#pricing"
            className="w-full sm:w-auto px-6 py-3.5 rounded-full border border-[#d9d9dd] hover:border-[#17171c] text-[#17171c] font-medium text-sm transition-all text-center"
            id="hero-cta-pricing"
          >
            Planları Gör
          </Link>
        </div>
      </header>

      {/* Problems of Traditional A/B Testing */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">GELENEKSEL YÖNTEMLERİN PROBLEMİ</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Neden klasik A/B testleri yetersiz kalıyor?
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <div className="w-10 h-10 rounded-[4px] bg-[#b30000] flex items-center justify-center mb-6 shrink-0 text-white">
              <AlertCircle size={20} />
            </div>
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Sadece &quot;B Kazandı&quot; Çıkmazı</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Klasik testlerde istatistiksel bir dönüşüm artışı görebilirsiniz, ancak bir versiyonun neden daha iyi performans gösterdiğine dair derin bir davranışsal açıklama asla alamazsınız.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <div className="w-10 h-10 rounded-[4px] bg-[#b30000] flex items-center justify-center mb-6 shrink-0 text-white">
              <AlertCircle size={20} />
            </div>
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Sıfır Kalitatif İçgörü</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Tıklama oranları (CTR) ve dönüşüm grafikleri, kullanıcının sayfanın hangi paragrafında kafasının karıştığını veya fiyat tablosunda tam olarak neyi sorguladığını söyleyemez.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20 flex flex-col">
            <div className="w-10 h-10 rounded-[4px] bg-[#b30000] flex items-center justify-center mb-6 shrink-0 text-white">
              <AlertCircle size={20} />
            </div>
            <h3 className="text-lg font-bold text-[#17171c] mb-3">Lansman Öncesi Kısıtlılığı</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Trafiği henüz olmayan yeni bir açılış sayfasını test edemezsiniz; bu sebeple körü körüne canlıya çıkmak ve gerçek reklam bütçenizi denek olarak harcamak zorunda kalırsınız.
            </p>
          </div>
        </div>
      </section>

      {/* 5-Step Process (Horizontal Grid) */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">KARŞILAŞTIRMALI SÜREÇ</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            5 adımda varyant analizi
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-5 rounded-[8px] border border-[#d9d9dd] flex flex-col justify-between">
            <div>
              <span className="text-2xl font-mono font-extrabold text-[#ff7759] block mb-3">01</span>
              <h3 className="text-sm font-bold text-[#17171c] mb-1">Varyantları Yükleyin</h3>
              <p className="text-[11px] text-[#616161] leading-relaxed">
                Varyant URL&apos;lerini yapıştırın veya taslak ekran görüntülerini yükleyin (~1 dk).
              </p>
            </div>
            <span className="text-[10px] text-[#93939f] font-mono mt-3">SÜRE: ~1 DK</span>
          </div>

          <div className="p-5 rounded-[8px] border border-[#d9d9dd] flex flex-col justify-between">
            <div>
              <span className="text-2xl font-mono font-extrabold text-[#ff7759] block mb-3">02</span>
              <h3 className="text-sm font-bold text-[#17171c] mb-1">Test Amacını Seçin</h3>
              <p className="text-[11px] text-[#616161] leading-relaxed">
                Mesaj netliği, güvenilirlik, değer önerisi gibi kritik odak lenslerinden birini seçin (~1 dk).
              </p>
            </div>
            <span className="text-[10px] text-[#93939f] font-mono mt-3">SÜRE: ~1 DK</span>
          </div>

          <div className="p-5 rounded-[8px] border border-[#d9d9dd] flex flex-col justify-between">
            <div>
              <span className="text-2xl font-mono font-extrabold text-[#ff7759] block mb-3">03</span>
              <h3 className="text-sm font-bold text-[#17171c] mb-1">Bölünmüş Panel</h3>
              <p className="text-[11px] text-[#616161] leading-relaxed">
                Clarere her varyantı ayrı personayla görüşür. Tepkiler izoledir, bulaşma (contamination) olmaz (~3 dk).
              </p>
            </div>
            <span className="text-[10px] text-[#93939f] font-mono mt-3">SÜRE: ~3 DK</span>
          </div>

          <div className="p-5 rounded-[8px] border border-[#d9d9dd] flex flex-col justify-between">
            <div>
              <span className="text-2xl font-mono font-extrabold text-[#ff7759] block mb-3">04</span>
              <h3 className="text-sm font-bold text-[#17171c] mb-1">Sonuçları İzleyin</h3>
              <p className="text-[11px] text-[#616161] leading-relaxed">
                Her iki varyant, aynı homojen persona paneli tarafından davranışsal olarak puanlanır (~25 dk).
              </p>
            </div>
            <span className="text-[10px] text-[#93939f] font-mono mt-3">SÜRE: ~25 DK</span>
          </div>

          <div className="p-5 rounded-[8px] border border-[#d9d9dd] flex flex-col justify-between">
            <div>
              <span className="text-2xl font-mono font-extrabold text-[#ff7759] block mb-3">05</span>
              <h3 className="text-sm font-bold text-[#17171c] mb-1">Raporu Alın</h3>
              <p className="text-[11px] text-[#616161] leading-relaxed">
                Hassas kalitatif karşılaştırma, segment puanları ve doğrudan alıntılar içeren PDF rapor hazır.
              </p>
            </div>
            <span className="text-[10px] text-[#93939f] font-mono mt-3">SÜRE: ANINDA</span>
          </div>
        </div>
      </section>

      {/* Rapor İçeriği */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">RAPOR DETAYLARI</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Karar vermek için tasarlanmış zengin veri
          </h2>
          <p className="text-sm text-[#616161] mt-2">
            Simülasyon sonuçları, kuru sayılardan ibaret değildir. Sunumlarınızda doğrudan kullanabileceğiniz zengin materyaller teslim edilir.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20">
            <span className="font-mono text-[#ff7759] text-xs font-bold block mb-3">01 / METRİKLER</span>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Scorecard</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Netlik, güven, itiraz düzeyi ve harekete geçme isteği (CTA intent) üzerinden her iki varyant için detaylı 100 bazlı puanlama.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20">
            <span className="font-mono text-[#ff7759] text-xs font-bold block mb-3">02 / SEGMENTASYON</span>
            <h3 className="text-base font-bold text-[#17171c] mb-2">UX Denetim Kohortu</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Segment bazlı (örneğin: Laggard veya Innovator kitle profilleri) yorumlamalar. Hangi varyantın kime hitap ettiğini görün.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20">
            <span className="font-mono text-[#ff7759] text-xs font-bold block mb-3">03 / İÇGÖRÜ</span>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Pazar Uyumu Temaları</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Tıklama verilerinde ve CTR grafiklerinde asla göremeyeceğiniz; kitlede yankı uyandıran veya tamamen görmezden gelinen temalar.
            </p>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] bg-[#eeece7]/20">
            <span className="font-mono text-[#ff7759] text-xs font-bold block mb-3">04 / KANITLAR</span>
            <h3 className="text-base font-bold text-[#17171c] mb-2">Persona Alıntıları</h3>
            <p className="text-xs text-[#616161] leading-relaxed">
              Yönetim sunumlarında ve kreatif toplantılarda kullanabileceğiniz, sanal personaların ağzından çıkmış doğrudan çarpıcı mülakat alıntıları.
            </p>
          </div>
        </div>
      </section>

      {/* Neden Clarere A/B? */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">NEDEN CLARERE?</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Benzersiz A/B test simülasyon gücü
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-[8px] border border-[#d9d9dd] flex gap-4 items-start">
            <div className="w-8 h-8 rounded-[4px] bg-[#ff7759] text-white flex items-center justify-center shrink-0">
              <BarChart2 size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#17171c] mb-1">Trafik Değil, Görüşme Çalıştırır</h3>
              <p className="text-xs text-[#616161] leading-relaxed">
                Sistem, varyantlarınızı ortalama matematik modellerine değil; her biri kendine has Big Five kişilik özelliklerine sahip davranışsal personalara okutarak değerlendirir.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] flex gap-4 items-start">
            <div className="w-8 h-8 rounded-[4px] bg-[#ff7759] text-white flex items-center justify-center shrink-0">
              <Layers size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#17171c] mb-1">Tutum Çeşitliliği (Stance Diversity)</h3>
              <p className="text-xs text-[#616161] leading-relaxed">
                Raporlarda sadece olumlu geri bildirimleri değil, &quot;Bu sayfa kafa karıştırıcı, hemen çıkardım&quot; diyen skeptiklerin ve engelleyicilerin acımasız eleştirilerini de duyarsınız.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] flex gap-4 items-start">
            <div className="w-8 h-8 rounded-[4px] bg-[#ff7759] text-white flex items-center justify-center shrink-0">
              <ShieldCheck size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#17171c] mb-1">Web-Doğrulamalı Kanıtlar</h3>
              <p className="text-xs text-[#616161] leading-relaxed">
                Raporda yer alan her davranışsal bulgu, yapay zeka tarafından canlı web araştırmaları ve güncel pazar kıyaslamaları (benchmarks) ile doğrulanarak çapraz referanslanır.
              </p>
            </div>
          </div>

          <div className="p-6 rounded-[8px] border border-[#d9d9dd] flex gap-4 items-start">
            <div className="w-8 h-8 rounded-[4px] bg-[#ff7759] text-white flex items-center justify-center shrink-0">
              <MessageSquare size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#17171c] mb-1">Gözlem Odası (Talk to Research)</h3>
              <p className="text-xs text-[#616161] leading-relaxed">
                Rapor oluşturulduktan sonra bitmez. Talk to Research modülü ile &quot;Skeptikler neden Varyant A&apos;nın yıllık fiyat tablosunu kafa karıştırıcı buldu?&quot; gibi spesifik takip soruları sorabilirsiniz.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-b border-[#d9d9dd]">
        <div className="mb-12 max-w-3xl">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-2">KARŞILAŞTIRMA TABLOSU</span>
          <h2 className="text-3xl font-bold tracking-tight text-[#17171c]" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Araçlar Karşılaştırması
          </h2>
          <p className="text-sm text-[#616161] mt-2">
            Clarere simülasyon modelinin Optimizely veya UserTesting gibi geleneksel devlerle karşılaştırılması.
          </p>
        </div>

        <div className="overflow-x-auto rounded-[8px] border border-[#d9d9dd]">
          <table className="w-full text-sm border-collapse text-left">
            <thead>
              <tr className="border-b border-[#d9d9dd] bg-[#f5f4f1]">
                <th className="px-5 py-4 font-semibold text-[#93939f] text-xs">Boyut</th>
                <th className="px-5 py-4 font-semibold text-[#616161] text-xs">Optimizely / VWO</th>
                <th className="px-5 py-4 font-semibold text-[#616161] text-xs">UserTesting / Maze</th>
                <th className="px-5 py-4 font-bold text-[#003c33] text-xs bg-[#edfce9]/60 border-l border-r border-[#003c33]/20">Clarere Simülasyonu</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#f2f2f2] bg-white">
                <td className="px-5 py-4 font-bold text-[#17171c]">Hız</td>
                <td className="px-5 py-4 text-[#616161]">2-6 Hafta (Trafik bağımlı)</td>
                <td className="px-5 py-4 text-[#616161]">3-10 Gün (İşe alım bağımlı)</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">15-30 Dakika</td>
              </tr>
              <tr className="border-b border-[#f2f2f2] bg-[#fafafa]">
                <td className="px-5 py-4 font-bold text-[#17171c]">Trafik Gereksinimi</td>
                <td className="px-5 py-4 text-[#616161]">Evet (Sayfa yayında olmalı)</td>
                <td className="px-5 py-4 text-[#616161]">Hayır (Ama katılımcı lazım)</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">Sıfır Trafik</td>
              </tr>
              <tr className="border-b border-[#f2f2f2] bg-white">
                <td className="px-5 py-4 font-bold text-[#17171c]">&quot;Neden&quot;ini Söyler mi?</td>
                <td className="px-5 py-4 text-[#616161]">Hayır, sadece hangisi kazandı</td>
                <td className="px-5 py-4 text-[#616161]">Bazen (Derinlemesine sorulursa)</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">Evet (Hedef ve tutum bazlı)</td>
              </tr>
              <tr className="bg-[#fafafa]">
                <td className="px-5 py-4 font-bold text-[#17171c]">Çıktı Tipi</td>
                <td className="px-5 py-4 text-[#616161]">Dönüşüm grafik verisi</td>
                <td className="px-5 py-4 text-[#616161]">Kullanıcı kayıtları ve notlar</td>
                <td className="px-5 py-4 font-bold text-[#003c33] bg-[#edfce9]/40 border-l border-r border-[#003c33]/20">2.500 - 4.500 Kelimelik Rapor</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-[#17171c] text-[#ffffff] px-6 py-20 border-t border-[#d9d9dd] text-center">
        <div className="max-w-3xl mx-auto">
          <span className="mono-label text-[#ff7759] uppercase tracking-wider text-xs font-semibold font-mono block mb-4" id="cta-label">
            LANS-ÖNCESİ SENTETİK DENEME
          </span>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#ffffff] leading-[1.1] mb-6" id="cta-title" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
            Sayfanızı yayına almadan önce<br />kullanıcı tepkilerini ölçün
          </h2>
          <p className="text-base text-white/60 mb-10 max-w-md mx-auto">
            Hemen ücretsiz A/B test simülasyonunu başlatın. 2 araştırma hediye. Kredi kartı gerekmez.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-sm mx-auto">
            <Link
              href="/client"
              className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#ffffff] text-[#17171c] font-medium text-sm hover:opacity-90 transition-all text-center"
              id="cta-trial-btn"
            >
              Ücretsiz Başla (3 Günlük Deneme)
            </Link>
            <a
              href="mailto:clarere@clarere.com?subject=AB Test Demosu"
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
