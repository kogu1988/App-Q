import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, FlaskConical, Target, AlertTriangle, Lightbulb, XCircle } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Kullanım Kılavuzu | Clarere",
  description: "Clarere Sentetik Pazar Araştırması Platformu Kullanım Kılavuzu. Sistemin işleyişi ve Defne ile etkileşim rehberi.",
};

export default function GuidePage() {
  return (
    <div className="min-h-screen bg-[#f5f4f1] text-[#212121] selection:bg-[#ff7759]/20 font-sans">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-border px-6 h-14 flex items-center justify-between">
        <div className="max-w-4xl mx-auto w-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Logo size={24} strokeColor="#17171c" />
            <span className="font-semibold text-[#17171c] tracking-tight">Clarere</span>
          </Link>
          <Link href="/" className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft size={16} />
            Ana Sayfaya Dön
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="max-w-4xl mx-auto px-6 py-16 sm:py-20 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="mb-12">
          <p className="text-[#ff7759] font-bold text-sm tracking-wider uppercase mb-3">Rehber</p>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#17171c] mb-6">
            Clarere Kullanım Kılavuzu
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed">
            Ürün fikirlerinizi koda veya üretime dökmeden önce nasıl test edebileceğinizi, sistemin sınırlarını ve Araştırma Mimarı &quot;Defne&quot; ile nasıl konuşmanız gerektiğini öğrenin.
          </p>
        </div>

        <div className="space-y-12">
          
          {/* Section 1 */}
          <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-border">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-[#edfce9] text-[#003c33] flex items-center justify-center shrink-0">
                <Target size={20} />
              </div>
              <h2 className="text-2xl font-bold text-[#17171c]">Sistem Aslında Nedir ve Ne İşe Yarar?</h2>
            </div>
            <div className="prose prose-stone max-w-none text-muted-foreground leading-relaxed">
              <p>
                Clarere, aylar süren ve yüksek bütçeler gerektiren geleneksel pazar araştırması (fokus grupları, anketler, derinlemesine mülakatlar) süreçlerini <strong>dakikalara indiren bir simülasyon aracıdır.</strong>
              </p>
              <p>Sistem temelde 3 aşamadan oluşur:</p>
              <ul className="space-y-2 mt-4">
                <li><strong className="text-foreground">1. Brief Oluşturma (Defne):</strong> Fikrinizi dinler, boşlukları bulur ve araştırma hedefini netleştirir.</li>
                <li><strong className="text-foreground">2. Sentetik Mülakatlar:</strong> Hedef kitlenizi temsil eden yapay zeka destekli sanal tüketiciler oluşturur ve onlarla röportaj yapar.</li>
                <li><strong className="text-foreground">3. Sentez Raporu:</strong> Tüm mülakatları analiz ederek pazar fırsatları, itirazlar ve fiyatlandırma tavsiyeleri sunar.</li>
              </ul>
              <div className="mt-6 p-4 bg-[#f5f4f1] rounded-xl border border-border flex gap-3 items-start">
                <Lightbulb size={20} className="text-[#ff7759] shrink-0 mt-0.5" />
                <p className="m-0 text-sm">
                  <strong>En İyi Kullanım Senaryosu:</strong> Aklınızda yeni bir ürün fikri var ancak insanların buna para verip vermeyeceğinden emin değilsiniz. Koda veya üretime dökmeden önce Clarere&apos;de fikrinizi çarpıştırın ve hipotezlerinizi doğrulayın.
                </p>
              </div>
            </div>
          </section>

          {/* Section 2 */}
          <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-border">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                <AlertTriangle size={20} />
              </div>
              <h2 className="text-2xl font-bold text-[#17171c]">Sistemin Sınırları: Neyi Yapar, Neyi Yapmaz?</h2>
            </div>
            
            <div className="grid sm:grid-cols-2 gap-8">
              <div>
                <h3 className="font-semibold text-lg text-foreground mb-4 flex items-center gap-2">
                  <CheckCircle2 size={18} className="text-emerald-600" /> Neyi Yapar?
                </h3>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li><strong>Fikrinizi Keskinleştirir:</strong> Zayıf veya eksik kurgulanmış iş modellerindeki mantık hatalarını bulur.</li>
                  <li><strong>İtirazları Önceden Yakalar:</strong> Müşterilerin ürününüzü satın almama bahanelerini simüle eder.</li>
                  <li><strong>A/B Testi Yapar:</strong> İki farklı mesajı farklı personalara sunarak tepkilerini ölçer.</li>
                  <li><strong>Kör Noktaları Aydınlatır:</strong> Aklınıza gelmeyen yepyeni bir kullanım senaryosu önerebilir.</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg text-foreground mb-4 flex items-center gap-2">
                  <XCircle size={18} className="text-red-500" /> Neyi YAPMAZ?
                </h3>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li><strong>Gerçek İnsanların Yerine Geçmez:</strong> Sentetik personalar harika bir ilk adımdır ancak gerçek insanların öngörülemez davranışlarının %100 aynısı değildir. <em>Clarere çok güçlü hipotezler sunar, ancak nihai karar pazarda test edilmelidir.</em></li>
                  <li><strong>İstatistik Veritabanı Değildir:</strong> Sistem <em>kalitatif</em> (niteliksel) araştırma üzerine uzmanlaşmıştır, kesin istatistikler vermez.</li>
                  <li><strong>Yatırım Tavsiyesi Vermez:</strong> Simülasyon sonuçları ticari garantiler içermez.</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Section 3 */}
          <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-border">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <FlaskConical size={20} />
              </div>
              <h2 className="text-2xl font-bold text-[#17171c]">Araştırma Mimarı &quot;Defne&quot; ile İletişim</h2>
            </div>
            <div className="prose prose-stone max-w-none text-muted-foreground leading-relaxed">
              <p>
                Defne basit bir chat botunuz değildir; o sizin <strong>Kıdemli Pazar Araştırması Mimarınızdır.</strong> Fikrinizi pohpohlamak yerine onu zorlayarak gerçeği bulmaya çalışır.
              </p>
              
              <div className="mt-6 space-y-6">
                <div>
                  <h4 className="text-foreground font-semibold">Defne&apos;ye Nasıl Bilgi Verilmeli?</h4>
                  <ul className="mt-2 space-y-1">
                    <li><strong>Dürüst Olun:</strong> Fikrinizin zayıf yönlerini saklamayın. <em>&quot;Bu kısmı nasıl yapacağımı henüz bilmiyorum&quot;</em> demekten çekinmeyin.</li>
                    <li><strong>Hedef Kitleyi Daraltın:</strong> Hedef kitleniz &quot;Herkes&quot; olamaz. <br/>
                      <span className="text-red-500 mr-2 text-sm">❌</span> <em>&quot;Kedisi olanlar&quot;</em> <br/>
                      <span className="text-emerald-600 mr-2 text-sm">✅</span> <em>&quot;Büyükşehirlerde yaşayan, çalışan ve evcil hayvan sağlığına para harcayan 30-45 yaş bireyler.&quot;</em>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="text-foreground font-semibold">Defne&apos;nin Sorularına Nasıl Cevap Verilmeli?</h4>
                  <ul className="mt-2 space-y-1">
                    <li><strong>Savunmacı Olmayın:</strong> Defne sizi zorluyorsa amacı fikrinizi çürütmek değil, pazardaki zorluklara hazırlamaktır.</li>
                    <li><strong>&quot;Sen Ne Önerirsin?&quot; Taktiği:</strong> Cevabı bilmiyorsanız, <em>&quot;Emin değilim, sen ne tür bir özellik önerirdin?&quot;</em> diyerek onun analitik zekasını kullanın.</li>
                  </ul>
                </div>
              </div>

              {/* Example Chat */}
              <div className="mt-8 bg-[#f5f4f1] rounded-xl p-5 border border-border text-sm">
                <h4 className="font-bold text-foreground mb-4">Pratik İletişim Örneği</h4>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <span className="font-bold text-foreground w-16 shrink-0">Siz:</span>
                    <span className="text-muted-foreground">&quot;Evcil hayvanların aşılarını takip eden bir uygulama fikrim var.&quot;</span>
                  </div>
                  <div className="flex gap-3">
                    <span className="font-bold text-[#ff7759] w-16 shrink-0">Defne:</span>
                    <span className="text-muted-foreground">&quot;Peki potansiyel kullanıcılar şu an bu ihtiyacı nasıl karşılıyor? Sizin farkınız ne olacak?&quot;</span>
                  </div>
                  <div className="flex gap-3">
                    <span className="font-bold text-red-500 w-16 shrink-0">Kötü Yanıt:</span>
                    <span className="text-muted-foreground">&quot;Şu an kağıda yazıyorlar. Bizimki dijital, herkes indirecek.&quot; <br/><em className="text-xs opacity-70">(Sığ bir cevap, Defne&apos;yi tatmin etmez.)</em></span>
                  </div>
                  <div className="flex gap-3">
                    <span className="font-bold text-emerald-600 w-16 shrink-0">İyi Yanıt:</span>
                    <span className="text-muted-foreground">&quot;Şu an veterinerin verdiği karneleri kullanıyorlar ama kaybediyorlar. Farkımız mama bittiğinde otomatik sipariş veren bir entegrasyon olması. Ancak fiyat modelinden emin değilim, sence nasıl olmalı?&quot; <br/><em className="text-xs opacity-70">(Detaylı, zayıf noktayı itiraf eden harika bir cevap.)</em></span>
                  </div>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
