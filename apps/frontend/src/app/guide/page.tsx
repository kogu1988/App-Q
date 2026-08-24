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
    <div className="min-h-screen bg-canvas text-ink selection:bg-coral/20 font-sans">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-canvas/90 backdrop-blur-md border-b border-hairline px-6 h-16 flex items-center justify-between">
        <div className="max-w-4xl mx-auto w-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-85 transition-opacity">
            <Logo size={24} strokeColor="#17171c" />
            <span className="font-semibold text-primary tracking-tight text-lg">Clarere</span>
          </Link>
          <Link href="/" className="flex items-center gap-1.5 text-sm font-medium text-body-muted hover:text-primary transition-colors">
            <ArrowLeft size={16} />
            Ana Sayfaya Dön
          </Link>
        </div>
      </nav>

      {/* Main Content Container */}
      <div className="max-w-4xl mx-auto px-6 py-16 sm:py-24 animate-in fade-in slide-in-from-bottom-4 duration-500">
        
        {/* Hero Header */}
        <div className="mb-16">
          <span className="mono-label text-coral block mb-3 font-semibold">Kılavuz</span>
          <h1 className="display-section text-primary font-bold mb-6">
            Clarere Kullanım Kılavuzu
          </h1>
          <p className="text-lg text-body-muted max-w-2xl leading-relaxed">
            Ürün fikirlerinizi koda veya üretime dökmeden önce nasıl test edebileceğinizi, sistemin sınırlarını ve Araştırma Mimarı &quot;Defne&quot; ile nasıl konuşmanız gerektiğini öğrenin.
          </p>
        </div>

        <div className="space-y-16">
          
          {/* Section 1: Sistem Aslında Nedir? */}
          <section className="py-12 border-t border-hairline space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full border border-hairline text-deep-green flex items-center justify-center shrink-0">
                <Target size={20} />
              </div>
              <div>
                <span className="mono-label text-coral block mb-0.5">GENEL BAKIŞ</span>
                <h2 className="text-2xl font-bold text-primary tracking-tight">Sistem Aslında Nedir ve Ne İşe Yarar?</h2>
              </div>
            </div>
            
            <div className="prose prose-stone max-w-none text-body-muted leading-relaxed space-y-4">
              <p>
                Clarere, aylar süren ve yüksek bütçeler gerektiren geleneksel pazar araştırması (fokus grupları, anketler, derinlemesine mülakatlar) süreçlerini <strong className="text-primary">dakikalara indiren bir simülasyon aracıdır.</strong>
              </p>
              <p>Sistem temelde 3 aşamadan oluşur:</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-6">
                <div className="p-5 rounded-sm border border-hairline bg-white">
                  <span className="mono-label text-coral block mb-2 font-semibold">AŞAMA 1</span>
                  <strong className="text-primary font-semibold text-base block mb-1">Brief Oluşturma (Defne)</strong>
                  <p className="text-sm text-body-muted leading-relaxed">Fikrinizi dinler, boşlukları bulur ve araştırma hedefini netleştirir.</p>
                </div>
                <div className="p-5 rounded-sm border border-hairline bg-white">
                  <span className="mono-label text-coral block mb-2 font-semibold">AŞAMA 2</span>
                  <strong className="text-primary font-semibold text-base block mb-1">Sentetik Mülakatlar</strong>
                  <p className="text-sm text-body-muted leading-relaxed">Hedef kitlenizi temsil eden yapay zeka destekli sanal tüketiciler oluşturur ve onlarla röportaj yapar.</p>
                </div>
                <div className="p-5 rounded-sm border border-hairline bg-white">
                  <span className="mono-label text-coral block mb-2 font-semibold">AŞAMA 3</span>
                  <strong className="text-primary font-semibold text-base block mb-1">Sentez Raporu</strong>
                  <p className="text-sm text-body-muted leading-relaxed">Tüm mülakatları analiz ederek pazar fırsatları, itirazlar ve fiyatlandırma tavsiyeleri sunar.</p>
                </div>
              </div>

              <div className="mt-8 p-6 bg-soft-stone rounded-sm border border-hairline flex gap-4 items-start">
                <Lightbulb size={20} className="text-coral shrink-0 mt-0.5" />
                <div className="text-sm text-ink leading-relaxed">
                  <strong className="text-primary block mb-1">En İyi Kullanım Senaryosu:</strong> 
                  Aklınızda yeni bir ürün fikri var ancak insanların buna para verip vermeyeceğinden emin değilsiniz. Koda veya üretime dökmeden önce Clarere&apos;de fikrinizi çarpıştırın ve hipotezlerinizi doğrulayın.
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: Bilimsel Metodoloji */}
          <section className="py-12 border-t border-hairline space-y-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full border border-hairline text-deep-green flex items-center justify-center shrink-0">
                <FlaskConical size={20} />
              </div>
              <div>
                <span className="mono-label text-coral block mb-0.5">METODOLOJİ</span>
                <h2 className="text-2xl font-bold text-primary tracking-tight">Davranış Bilimine Dayalı Araştırma</h2>
              </div>
            </div>

            <div className="prose prose-stone max-w-none text-body-muted leading-relaxed space-y-6">
              <div>
                <h3 className="font-semibold text-lg text-primary mb-2">1. Giriş: Davranış Bilimine Dayalı Metodoloji</h3>
                <p>
                  Clarere, sadece yapay zeka komutlarından (prompts) ibaret olmayan, arkasında <strong className="text-primary">davranış bilimlerine dayalı güçlü akademik temeller</strong> barındıran bilimsel bir platformdur. Platformdaki her mimari karar, hakemli kaynaklara ve bilişsel psikoloji teorilerine dayandırılmıştır.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-primary mb-4">2. Yapay Zeka Araştırmalarının Başarısızlık Nedenleri ve Clarere Çözümleri</h3>
                <p className="mb-4">
                  Geleneksel LLM rol yapma (roleplay) yaklaşımlarında karşılaşılan yaygın araştırma hatalarını çözmek için Clarere şu bilimsel düzeltmeleri uygular:
                </p>
                
                <div className="grid sm:grid-cols-2 gap-6">
                  <div className="p-6 rounded-sm border border-hairline bg-white">
                    <strong className="text-primary font-semibold text-base block mb-2">Kişilik Derinliği (Personality Depth)</strong>
                    <span className="text-xs font-mono text-error block mb-2">❌ Standart Sorun: Modeller klişelerden beslenir.</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">Clarere Çözümü:</strong> 100&apos;den fazla akademik makale referansıyla; Big Five NEO-PI-R alt-boyutları, Rogers&apos;ın Teknoloji Benimseme Eğrisi ve ACT-R bilişsel mimarisi üzerine inşa edilen zeminli personalar kullanılır.
                    </p>
                  </div>

                  <div className="p-6 rounded-sm border border-hairline bg-white">
                    <strong className="text-primary font-semibold text-base block mb-2">Hafıza ve Tutarlılık (Memory & Coherence)</strong>
                    <span className="text-xs font-mono text-error block mb-2">❌ Standart Sorun: Personanın ilerleyen sorularda kendiyle çelişmesi.</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">Clarere Çözümü:</strong> Epistemik ve anlamsal bellek sistemleri ile personanın neyi bilip bilmediğini açıkça gösteren <em className="text-primary font-mono text-xs">Provenance Cards</em> altyapısı devrededir.
                    </p>
                  </div>

                  <div className="p-6 rounded-sm border border-hairline bg-white">
                    <strong className="text-primary font-semibold text-base block mb-2">Onay Yanlılığı (Confirmation Bias / Sycophancy)</strong>
                    <span className="text-xs font-mono text-error block mb-2">❌ Standart Sorun: Yapay zekanın hipotezinizi doğrulamaya çalışması.</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">Clarere Çözümü:</strong> <em className="text-primary font-mono text-xs">Context Isolation</em> (Bağlam İzolasyonu) sayesinde personalar araştırmanın arkasındaki ana hipotezi veya başarı kriterlerini asla göremez.
                    </p>
                  </div>

                  <div className="p-6 rounded-sm border border-hairline bg-white">
                    <strong className="text-primary font-semibold text-base block mb-2">Panel Çeşitliliği (Diversity Engineering)</strong>
                    <span className="text-xs font-mono text-error block mb-2">❌ Standart Sorun: Hepsi aynı fikirde olan, aşırı uyumlu profil yığını.</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">Clarere Çözümü:</strong> <em className="text-primary font-mono text-xs">Stance Diversity Engine</em> ile panelde Şampiyonlar (%15), Pragmatistler (%35), Skeptikler (%20), Engelleyiciler (%15) ve Gözlemciler (%15) istatistiksel Largest Remainder matrisine göre atanır.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-primary mb-4">3. Araştırma Çıktıları: Ne Alıyorsunuz?</h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3 border-b border-hairline pb-4">
                    <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                    <div className="text-sm text-body-muted">
                      <strong className="text-primary block mb-0.5">Varsayımları Zorlayan Cevaplar</strong>
                      Skeptikler ve muhaliflerden gelen gerçekçi itirazlar (Örn: <em className="font-mono text-xs text-[#616161]">&quot;Fiyatlandırma çok karmaşık&quot;</em>, <em className="font-mono text-xs text-[#616161]">&quot;KVKK ve SSO entegrasyonu yoksa bakmam bile&quot;</em>).
                    </div>
                  </div>
                  <div className="flex items-start gap-3 border-b border-hairline pb-4">
                    <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                    <div className="text-sm text-body-muted">
                      <strong className="text-primary block mb-0.5">Sunuma Hazır Raporlar</strong>
                      Yönetici özeti, tema analizi, kanıt zinciri ve önceliklendirilmiş öneriler içeren dışa aktarılabilir raporlar.
                    </div>
                  </div>
                  <div className="flex items-start gap-3 border-b border-hairline pb-4">
                    <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                    <div className="text-sm text-body-muted">
                      <strong className="text-primary block mb-0.5">Kritik Eleştiri</strong>
                      Piyasaya çıkmadan önce en sert eleştirmenlerinizi (şüpheciler, kafası karışık olanlar) simüle ederek açıkları kapatır.
                    </div>
                  </div>
                  <div className="flex items-start gap-3 pb-2">
                    <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                    <div className="text-sm text-body-muted">
                      <strong className="text-primary block mb-0.5">Hata ve Yanlılık Kontrolü</strong>
                      <em className="text-primary font-mono text-xs">Adversarial Review</em> (hasmane kalite denetimi) ile yanlılıklar ve kanıt zinciri doğruluğu anlık olarak denetlenir.
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-primary mb-4">4. Bilimsel Kanıtlar ve Karşılaştırma</h3>
                <div className="grid sm:grid-cols-2 gap-6 text-sm">
                  <div className="p-6 border border-hairline rounded-sm bg-soft-stone">
                    <span className="mono-label text-coral block mb-2 font-semibold">YÜKSEK DOĞRULUK</span>
                    <p className="text-ink font-medium leading-relaxed">
                      Clarere, uzman araştırma ekiplerinin aylar süren çalışmalarındaki kritik pazar bulgularının <strong className="text-primary">%86'sını 2 dakikadan kısa sürede</strong> yakalar.
                    </p>
                  </div>
                  <div className="p-6 border border-hairline rounded-sm bg-soft-stone">
                    <span className="mono-label text-coral block mb-2 font-semibold">AKADEMİK VALİDASYON</span>
                    <p className="text-ink font-medium leading-relaxed">
                      Baymard Institute ve Nielsen Norman Group (NNg) insan bulgularına karşı <strong className="text-primary">9 farklı sektörde gerçekleştirilen 46 bağımsız çalışma</strong> ile test edilmiş ve doğrulanmıştır.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-primary mb-4">5. Arka Plandaki 14 İnovatif Sistem</h3>
                <p className="mb-4">Simülasyon hatalarını ve yapay zeka dalkavukluğunu aşmak için tasarlanmış entegre sistemlerden bazıları:</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 border border-hairline rounded-sm bg-white">
                    <strong className="text-primary font-semibold block mb-1 text-sm">Context Isolation</strong>
                    <p className="text-body-muted leading-relaxed">Personanın hipotezleri bilmesini engelleyerek yaranma çabasını (sycophancy) sıfırlar.</p>
                  </div>
                  <div className="p-4 border border-hairline rounded-sm bg-white">
                    <strong className="text-primary font-semibold block mb-1 text-sm">Realistic Memory</strong>
                    <p className="text-body-muted leading-relaxed">Gerçek insan belleğini modeller; &quot;bilmiyorum&quot; diyebilen ve anıları sönümlenen ACT-R tabanlı bellek yapısı.</p>
                  </div>
                  <div className="p-4 border border-hairline rounded-sm bg-white">
                    <strong className="text-primary font-semibold block mb-1 text-sm">Stance Diversity</strong>
                    <p className="text-body-muted leading-relaxed">Matris tahsisiyle her panelde mutlaka itiraz eden ve şüphe duyan alternatif seslerin bulunmasını sağlar.</p>
                  </div>
                  <div className="p-4 border border-hairline rounded-sm bg-white">
                    <strong className="text-primary font-semibold block mb-1 text-sm">Sycophancy Detector</strong>
                    <p className="text-body-muted leading-relaxed">Fazla uyumlu yanıtları gerçek zamanlı tespit eder ve personayı Zero-Sum Bet (finansal risk taahhüdü) ile sınayarak dürüstlüğe zorlar.</p>
                  </div>
                  <div className="p-4 border border-hairline rounded-sm bg-white">
                    <strong className="text-primary font-semibold block mb-1 text-sm">6-Stage Review</strong>
                    <p className="text-body-muted leading-relaxed">Rapor sunulmadan önce tema çıkarma, web pazar araştırması ve hasmane kalite denetimi gibi 6 farklı ajan katmanından geçer.</p>
                  </div>
                  <div className="p-4 border border-hairline rounded-sm bg-white">
                    <strong className="text-primary font-semibold block mb-1 text-sm">Cultural Dimensions</strong>
                    <p className="text-body-muted leading-relaxed">Hofstede&apos;in 6D kültürel boyut modeli ile yerel satın alma ve işlem reflekslerini hesaba katar.</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-primary mb-4">6. Sezgisel Olmayan Etkiler ve Araştırma Bulguları</h3>
                <p className="mb-4">Clarere&apos;in kendi sistem and metodoloji araştırmalarından elde edilen şaşırtıcı bilimsel bulgular:</p>
                <div className="space-y-4">
                  <div className="flex gap-4 border-b border-hairline pb-4">
                    <span className="mono-label text-coral font-bold shrink-0 mt-0.5">BULGU 1</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">Daha fazla hesaplama (compute) bazen sonuçları kötüleştirir:</strong> Aşırı akıl yürütme (reasoning) döngüleri personaların aşırı düşünmesine ve gerçek hayattaki hızlı tepkilerden uzaklaşmasına sebep olabilir.
                    </p>
                  </div>
                  <div className="flex gap-4 border-b border-hairline pb-4">
                    <span className="mono-label text-coral font-bold shrink-0 mt-0.5">BULGU 2</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">&quot;Uzman&quot; personaların doğruluğu daha düşük olabilir:</strong> Kendi alanında aşırı uzman olarak tanımlanan profiller, gerçek dünyadaki genel tüketici bariyerlerini gözden kaçırma eğilimindedir.
                    </p>
                  </div>
                  <div className="flex gap-4 pb-2">
                    <span className="mono-label text-coral font-bold shrink-0 mt-0.5">BULGU 3</span>
                    <p className="text-sm text-body-muted leading-relaxed">
                      <strong className="text-primary">10 turluk bir mülakat sohbeti, bazen tek bir hedefe odaklanmış turlardan daha verimsiz olabilir:</strong> Uzun görüşmelerde ACT-R bellek aşınması ve bilişsel sapma birikmesi yaşanabilir. Bu yüzden Clarere, Cowan çalışma belleği limiti olan 4 aktif anı sınırını katı şekilde uygular.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Sistemin Sınırları */}
          <section className="py-12 border-t border-hairline space-y-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full border border-hairline text-error flex items-center justify-center shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div>
                <span className="mono-label text-coral block mb-0.5">SINIRLAR</span>
                <h2 className="text-2xl font-bold text-primary tracking-tight">Sistemin Sınırları: Neyi Yapar, Neyi Yapmaz?</h2>
              </div>
            </div>
            
            <div className="grid sm:grid-cols-2 gap-8">
              <div className="p-6 border border-hairline rounded-sm bg-white">
                <h3 className="font-semibold text-lg text-primary flex items-center gap-2 mb-4">
                  <CheckCircle2 size={18} className="text-deep-green shrink-0" />
                  <span>Neyi Yapar?</span>
                </h3>
                <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
                  <li><strong className="text-primary">Fikrinizi Keskinleştirir:</strong> Zayıf veya eksik kurgulanmış iş modellerindeki mantık hatalarını bulur.</li>
                  <li><strong className="text-primary">İtirazları Önceden Yakalar:</strong> Müşterilerin ürününüzü satın almama bahanelerini simüle eder.</li>
                  <li><strong className="text-primary">A/B Testi Yapar:</strong> İki farklı mesajı farklı personalara sunarak tepkilerini ölçer.</li>
                  <li><strong className="text-primary">Kör Noktaları Aydınlatır:</strong> Aklınıza gelmeyen yepyeni bir kullanım senaryosu önerebilir.</li>
                </ul>
              </div>
              
              <div className="p-6 border border-hairline rounded-sm bg-white">
                <h3 className="font-semibold text-lg text-primary flex items-center gap-2 mb-4">
                  <XCircle size={18} className="text-error shrink-0" />
                  <span>Neyi YAPMAZ?</span>
                </h3>
                <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
                  <li><strong className="text-primary">Gerçek İnsanların Yerine Geçmez:</strong> Sentetik personalar harika bir ilk adımdır ancak gerçek insanların öngörülemez davranışlarının %100 aynısı değildir. <em>Clarere çok güçlü hipotezler sunar, ancak nihai karar pazarda test edilmelidir.</em></li>
                  <li><strong className="text-primary">İstatistik Veritabanı Değildir:</strong> Sistem <em>kalitatif</em> (niteliksel) araştırma üzerine uzmanlaşmıştır, kesin istatistikler vermez.</li>
                  <li><strong className="text-primary">Yatırım Tavsiyesi Vermez:</strong> Simülasyon sonuçları ticari garantiler içermez.</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Section 4: Araştırma Mimarı Defne ile İletişim */}
          <section className="py-12 border-t border-hairline space-y-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full border border-hairline text-primary flex items-center justify-center shrink-0">
                <FlaskConical size={20} />
              </div>
              <div>
                <span className="mono-label text-coral block mb-0.5">İLETİŞİM REHBERİ</span>
                <h2 className="text-2xl font-bold text-primary tracking-tight">Araştırma Mimarı &quot;Defne&quot; ile İletişim</h2>
              </div>
            </div>
            
            <div className="prose prose-stone max-w-none text-body-muted leading-relaxed space-y-6">
              <p>
                Defne basit bir chat botunuz değildir; o sizin <strong className="text-primary">Kıdemli Pazar Araştırması Mimarınızdır.</strong> Fikrinizi pohpohlamak yerine onu zorlayarak gerçeği bulmaya çalışır.
              </p>
              
              <div className="grid sm:grid-cols-2 gap-8">
                <div className="p-6 rounded-sm border border-hairline bg-white">
                  <h4 className="text-primary font-semibold mb-3">Defne&apos;ye Nasıl Bilgi Verilmeli?</h4>
                  <ul className="space-y-3 text-sm text-body-muted">
                    <li className="flex items-start gap-2">
                      <span className="text-deep-green font-bold shrink-0 mt-0.5">✓</span>
                      <span><strong>Dürüst Olun:</strong> Fikrinizin zayıf yönlerini saklamayın. <em>&quot;Bu kısmı nasıl yapacağımı henüz bilmiyorum&quot;</em> demekten çekinmeyin.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-deep-green font-bold shrink-0 mt-0.5">✓</span>
                      <span>
                        <strong>Hedef Kitleyi Daraltın:</strong> Hedef kitleniz &quot;Herkes&quot; olamaz.
                        <span className="block mt-2 space-y-1">
                          <span className="text-error font-medium block">❌ Kötü: &quot;Kedisi olanlar&quot;</span>
                          <span className="text-deep-green font-medium block">✅ İyi: &quot;Büyükşehirlerde yaşayan, çalışan ve evcil hayvan sağlığına para harcayan 30-45 yaş bireyler.&quot;</span>
                        </span>
                      </span>
                    </li>
                  </ul>
                </div>
                
                <div className="p-6 rounded-sm border border-hairline bg-white">
                  <h4 className="text-primary font-semibold mb-3">Defne&apos;nin Sorularına Nasıl Cevap Verilmeli?</h4>
                  <ul className="space-y-3 text-sm text-body-muted">
                    <li className="flex items-start gap-2">
                      <span className="text-deep-green font-bold shrink-0 mt-0.5">✓</span>
                      <span><strong>Savunmacı Olmayın:</strong> Defne sizi zorluyorsa amacı fikrinizi çürütmek değil, pazardaki zorluklara hazırlamaktır.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-deep-green font-bold shrink-0 mt-0.5">✓</span>
                      <span><strong>&quot;Sen Ne Önerirsin?&quot; Taktiği:</strong> Cevabı bilmiyorsanız, <em>&quot;Emin değilim, sen ne tür bir özellik önerirdin?&quot;</em> diyerek onun analitik zekasını kullanın.</span>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Console Mockup Turn */}
              <div className="mt-8 bg-primary text-white rounded-sm p-6 border border-ink text-sm font-sans relative overflow-hidden">
                <div className="absolute top-0 right-0 p-3 flex gap-1.5 opacity-25">
                  <div className="w-2 h-2 rounded-full bg-white"></div>
                  <div className="w-2 h-2 rounded-full bg-white"></div>
                  <div className="w-2 h-2 rounded-full bg-white"></div>
                </div>
                
                <div className="flex items-center gap-2 mb-6 border-b border-ink/40 pb-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                  <span className="mono-label text-[10px] tracking-wider text-muted-text">Simüle Edilen İletişim Konsolu</span>
                </div>

                <div className="space-y-6">
                  {/* User Turn */}
                  <div className="flex gap-3">
                    <span className="mono-label text-[10px] text-coral shrink-0 w-16 mt-1">KULLANICI</span>
                    <div className="bg-ink/30 border border-ink/50 rounded-sm p-3 text-white/90">
                      &quot;Evcil hayvanların aşılarını takip eden bir uygulama fikrim var.&quot;
                    </div>
                  </div>
                  
                  {/* Agent Turn */}
                  <div className="flex gap-3">
                    <span className="mono-label text-[10px] text-emerald-400 shrink-0 w-16 mt-1">DEFNE</span>
                    <div className="bg-[#003c33]/40 border border-deep-green rounded-sm p-3 text-white/95">
                      &quot;Peki potansiyel kullanıcılar şu an bu ihtiyacı nasıl karşılıyor? Sizin farkınız ne olacak?&quot;
                    </div>
                  </div>

                  {/* Bad Turn */}
                  <div className="flex gap-3">
                    <span className="mono-label text-[10px] text-error shrink-0 w-16 mt-1">SIĞ CEVAP</span>
                    <div className="bg-error/10 border border-error/30 rounded-sm p-3 text-white/80">
                      &quot;Şu an kağıda yazıyorlar. Bizimki dijital, herkes indirecek.&quot;
                      <span className="block mt-2 text-[11px] text-error/80 italic font-mono">Defne bu yanıtı sığ bulur ve sizi derinleştirmeye zorlar.</span>
                    </div>
                  </div>

                  {/* Good Turn */}
                  <div className="flex gap-3">
                    <span className="mono-label text-[10px] text-emerald-400 shrink-0 w-16 mt-1">ZENGİN CEVAP</span>
                    <div className="bg-deep-green/30 border border-deep-green/60 rounded-sm p-3 text-white/95">
                      &quot;Şu an veterinerin verdiği karneleri kullanıyorlar ama kaybediyorlar. Farkımız mama bittiğinde otomatik sipariş veren bir entegrasyon olması. Ancak fiyat modelinden emin değilim, sence nasıl olmalı?&quot;
                      <span className="block mt-2 text-[11px] text-emerald-400/85 italic font-mono">Detaylı, zayıf noktayı itiraf eden harika bir cevap.</span>
                    </div>
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
