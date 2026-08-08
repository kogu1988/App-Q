import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Kullanım Koşulları — Clarere",
  description:
    "Clarere platformunu kullanmadan önce lütfen kullanım koşullarını okuyunuz. Hizmet kapsamı, sorumluluk sınırları ve tarafların hak ve yükümlülükleri.",
  robots: { index: true, follow: true },
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-canvas text-ink selection:bg-coral/20 font-sans">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-canvas/90 backdrop-blur-md border-b border-hairline px-6 h-16 flex items-center justify-between">
        <div className="max-w-4xl mx-auto w-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-85 transition-opacity">
            <Logo size={24} strokeColor="#17171c" />
            <span className="font-semibold text-primary tracking-tight text-lg">Clarere</span>
          </Link>
          <Link href="/" className="text-sm font-medium text-body-muted hover:text-primary transition-colors">
            ← Ana Sayfa
          </Link>
        </div>
      </nav>

      {/* Main Content Container */}
      <main className="max-w-4xl mx-auto px-6 py-16 sm:py-24 animate-in fade-in slide-in-from-bottom-4 duration-500">
        
        {/* Header */}
        <header className="mb-16 border-b border-hairline pb-8">
          <h1 className="display-section text-primary font-bold mb-4">
            Kullanım Koşulları
          </h1>
          <p className="text-lg text-body-muted leading-relaxed">
            Clarere platformunu ve ilgili sentetik pazar araştırması simülasyonu hizmetlerini kullanarak aşağıdaki tüm yasal koşulları kabul etmiş sayılırsınız.
          </p>
          <p className="text-xs text-body-muted mt-4 font-mono">Son güncelleme: 27 Mayıs 2026</p>
        </header>

        {/* Policy Sections */}
        <div className="space-y-12">
          
          {/* 1. Sorumluluk Reddi */}
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">1. Sorumluluk Reddi (Disclaimer)</h2>
            <div className="p-6 bg-soft-stone rounded-sm border border-hairline space-y-4">
              <span className="mono-label text-coral block font-semibold">⚠️ BETA SÜRÜMÜ BİLDİRİMİ (BETA VERSION NOTICE)</span>
              <p className="text-ink text-xs leading-relaxed">
                Sitemiz, platformumuz and ilgili araştırma hizmetleri şu anda erken <strong>BETA aşamasındadır</strong>; yazılımsal hatalar, bilgi eksiklikleri veya tamamlanmamış özellikler içerebilir. Platform, yalnızca ön kullanım, test, deneme ve bilimsel kalibrasyon değerlendirmesi amaçlıdır. Platformun tam sürümle piyasaya çıkacağı veya mevcut belirli özelliklerin kalıcı olacağı garanti edilmez.
              </p>
              <p className="text-ink text-xs leading-relaxed">
                <strong>Kendi Riskinizle Kullanım (USE AT YOUR OWN RISK):</strong> Platformu kullanarak, teknik kesintiler dahil tüm olası operasyonel riskleri peşinen kabul etmiş olursunuz. Ürün deneyseldir ve nihai ticari/kritik kararlar için tek başına bu siteye güvenilmemelidir.
              </p>
              <p className="text-ink text-xs leading-relaxed">
                <strong>Veri Gizliliği:</strong> Kullanıcı verileri Gizlilik Politikamıza uygun olarak işlenir. Finansal bilgiler veya T.C. kimlik numaraları gibi kritik hassas kişisel verileri platforma yüklememeniz önemle tavsiye edilir.
              </p>
            </div>
          </section>

          {/* 2. Hizmet Şartları */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">2. Hizmet Şartları ve Kabulü</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Bu şartlar, kullanıcı ile <strong className="text-primary">Clarere</strong> arasında akdedilmiş yasal bir sözleşmedir. Siteye erişerek veya hizmetleri kullanarak bu şartlara ve ek belgemiz olan Gizlilik Politikasına bağlı kalmayı kabul edersiniz. Koşulları kabul etmiyorsanız Platformu kullanmamalısınız.
            </p>
          </section>

          {/* 3. Değişiklikler */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">3. Koşullardaki Değişiklikler</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Clarere, bu koşulları önceden bildirmeksizin dilediği zaman güncelleme veya değiştirme hakkını saklı tutar. Maddi ve esaslı değişikliklerde, kayıtlı kullanıcılara 30 gün önceden e-posta veya sistem içi bildirim yapılmasına gayret edilir. Değişikliklerden sonra Platformu kullanmaya devam etmeniz, yeni koşulları kabul ettiğiniz anlamına gelir.
            </p>
          </section>

          {/* 4. Kullanıcı Kaydı */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">4. Kullanıcı Kaydı ve Hesap Güvenliği</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Platformdaki bazı özellikleri (brief oluşturma, simülasyon çalıştırma, rapor havuzu) kullanabilmek için e-posta ile kayıt olmanız gerekebilir. Sağladığınız bilgilerin doğruluğundan, şifre gizliliğinden ve hesabınız altında gerçekleşen tüm aktivitelerden tamamen siz sorumlusunuz. Uygunsuz, aldatıcı veya marka ihlali içeren kullanıcı adlarını/hesaplarını geri alma veya değiştirme hakkımız saklıdır.
            </p>
          </section>

          {/* 5. Reşit Olmayanlar */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">5. Reşit Olmayanlar</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Clarere platformu ve sentetik araştırma simülasyonları yalnızca <strong>18 yaş ve üzeri</strong> kullanıcılara yöneliktir. 18 yaşın altındaki kişilerin siteyi kullanmasına veya üyelik açmasına izin verilmez.
            </p>
          </section>

          {/* 6. Hizmetlerin Doğası */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">6. Hizmetlerin Niteliği ve Kapsamı</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Şu anki beta aşamasında Platform, kullanıcıların ürün fikirlerine yönelik sentetik kitle reaksiyonlarını ve pazar bariyerlerini test etmelerine olanak tanıyan deneysel bir simülatördür. Raporlar ve mülakat simülasyonları yön gösterici hipotezlerden ibaret olup; yasal, finansal, vergi veya yatırım tavsiyesi olarak değerlendirilemez.
            </p>
          </section>

          {/* 7. Ödemeler ve Ücretlendirme */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">7. Ödemeler ve Gelecekteki Ücretler</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong>Beta Erişimi:</strong> Erken test aşamasında (Beta), Platform tarafından sağlanan temel deneme simülasyonları için herhangi bir abonelik veya işlem ücreti talep edilmez.
            </p>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong>Gelecekteki Ücretli Modeller:</strong> İlerleyen dönemlerde ücretli ticari planlara veya limitli kredi paketlerine geçilmesi durumunda, kullanıcılara fiyatlandırma değişiklikleri en az 30 gün önceden bildirilecektir.
            </p>
          </section>

          {/* 8. Kullanıcı Beyanları */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">8. Kullanıcı Beyan ve Taahhütleri</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Platformu kullanan her üye; sağladığı tüm verilerin doğru olduğunu, yasal ehliyetinin bulunduğunu, siteyi bot, crawler, script veya izin verilmeyen herhangi bir otomatik veri çekme (scraping) yöntemiyle kullanmayacağını ve platform çıktılarını doğrudan nihai yatırım/vergi tavsiyesi olarak yansıtmayacağını taahhüt eder.
            </p>
          </section>

          {/* 9 & 10. Kabul Edilebilir ve Yasaklı Kullanımlar */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">9 & 10. Kabul Edilebilir ve Yasaklı Kullanımlar</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Aşağıdaki eylemlerin gerçekleştirilmesi kesinlikle yasaktır ve tespiti halinde derhal hesap feshine yol açar:
            </p>
            <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
              <li>Platform altyapısına, kodlarına veya simülasyon algoritmalarına tersine mühendislik (reverse engineering) uygulamak veya kaynak kodunu çözmeye çalışmak.</li>
              <li>İzin verilmeyen otomatik araçlarla (web botları, crawlers) sistemden veri çekmek.</li>
              <li>API uçlarını aşırı yüklemek, DDoS girişiminde bulunmak veya sunucu bütünlüğünü bozmak.</li>
              <li>Araştırma brief alanlarına hassas kişisel verileri (KVKK/GDPR özel nitelikli kişisel veriler, finansal bilgiler, T.C. kimlik no) yüklemek veya simüle etmek.</li>
              <li>Clarere markasını, telif hakkı logolarını veya patent ibarelerini Platform raporlarından kaldırmak ya da değiştirmek.</li>
            </ul>
          </section>

          {/* 11. Üçüncü Taraf Bağlantıları */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">11. Üçüncü Taraf Bağlantıları</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Platform, canlı pazar araştırması için üçüncü taraf arama motorlarına veya dış web sitelerine bağlantılar içerebilir. Clarere, bu sitelerin içeriklerinden, doğruluğundan veya gizlilik uygulamalarından sorumlu değildir; bu bağlantıların kullanımıyla ilgili tüm risk kullanıcıya aittir.
            </p>
          </section>

          {/* 12. Gizlilik ve Sır Saklama */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">12. Gizlilik ve Sır Saklama (Confidentiality)</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Taraflar (Kullanıcı ve Clarere), Platform vasıtasıyla edindikleri birbirlerine ait gizli ticari bilgileri, iş planlarını, simülasyon kodlarını ve metodolojik formülleri izinsiz olarak üçüncü şahıslarla paylaşmamayı kabul ederler. Bu gizlilik yükümlülüğü, hesabın kapatılmasından veya Platform kullanımının sona ermesinden itibaren <strong>5 yıl boyunca</strong> yürürlükte kalmaya devam eder.
            </p>
          </section>

          {/* 13. Fikri Mülkiyet Hakları */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">13. Fikri Mülkiyet Hakları</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Clarere platformunun tüm tasarımı, kaynak kodları, veri modelleri, Grounded Simulation metodolojisi, ACT-R bellek entegrasyonu ve Research Fidelity Index (RFI) algoritmaları Clarere&apos;in tescilli fikri mülkiyetindedir. Kullanıcıya yalnızca simülasyon çalıştırmak ve kişisel/kurumsal rapor üretmek amacıyla iptal edilebilir, devredilemez şahsi bir kullanım lisansı verilir. Platforma ilettiğiniz geri bildirimler (feedback) ve öneriler, Clarere tarafından dünya çapında, ücretsiz ve sınırsız olarak sistemi geliştirmek amacıyla kullanılabilir.
            </p>
          </section>

          {/* 14 & 15. Sorumluluğun Sınırlandırılması */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">14 & 15. Sorumluluğun Sınırlandırılması</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Platform ve tüm simülasyon içerikleri kullanıcıya <strong>&quot;OLDUĞU GİBİ&quot; (AS IS)</strong> esasıyla sunulmaktadır. Clarere; kar kaybı, veri kaybı, pazar başarısızlığı veya dolaylı/tesadüfi zararlardan ötürü hiçbir koşulda sorumlu tutulamaz. Clarere&apos;in kullanıcıya karşı doğabilecek toplam hukuki sorumluluğu, kullanıcının Platformu kullanmak için son 3 ayda ödediği toplam tutarı (şu anki beta aşaması için sıfır) aşamaz.
            </p>
          </section>

          {/* 16. Tazminat */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">16. Tazminat (Indemnification)</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Kullanıcının bu koşulları ihlal etmesi, yanlış bilgi sunması veya üçüncü şahısların (veya patentlerin) fikri mülkiyet haklarını Platform üzerinde çiğnemesi durumunda doğacak tüm yasal, idari ve maddi zararlar tamamen ihlalde bulunan kullanıcı tarafından karşılanacaktır.
            </p>
          </section>

          {/* 17. Fesih */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">17. Fesih (Termination)</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Kullanım koşullarının ihlal edilmesi, bot kullanımı veya sistem güvenliğini tehdit eden eylemlerin tespiti durumunda Clarere, önceden bildirim yapmaksızın kullanıcının Platforma erişimini dilediği an askıya alma veya kalıcı olarak sonlandırma hakkını saklı tutar.
            </p>
          </section>

          {/* 18. Uyuşmazlıkların Çözümü */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">18. Uyuşmazlıkların Çözümü ve Yetkili Mahkeme</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong>Barışçıl Çözüm:</strong> Koşullardan doğabilecek tüm uyuşmazlıklarda öncelikle taraflar iyi niyetli bir çözüm için <a href="mailto:hiclarere@clarere.com" className="text-coral hover:underline font-semibold font-mono">hiclarere@clarere.com</a> adresine yazılı bildirim yaparak ortak bir noktada buluşmaya gayret edecektir.
            </p>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong>Yetkili Mahkeme ve Kanun:</strong> 30 gün içerisinde barışçıl yollarla çözülemeyen uyuşmazlıkların giderilmesinde <strong>Türkiye Cumhuriyeti (T.C.) Yasaları</strong> geçerli olacak ve uyuşmazlıkların çözümünde münhasıran <strong>İstanbul (Çağlayan) Mahkemeleri ve İcra Daireleri</strong> yetkili kılınacaktır.
            </p>
          </section>

          {/* 19. Genel Şartlar */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">19. Genel Hükümler</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong>Mücbir Sebep:</strong> Deprem, doğal afet, savaş, genel internet kesintisi veya veri merkezi yangınları gibi Clarere&apos;in makul kontrolü dışındaki durumlarda hizmet duraklamalarından Platform sorumlu tutulamaz.
            </p>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong>Zamanaşımı:</strong> Platform kullanımından doğacak her türlü hak talebi ve dava açma süresi, olayın vuku bulduğu tarihten itibaren <strong>1 (bir) yıl</strong> ile sınırlıdır; bu süreden sonra hak talebi zamanaşımına uğrar.
            </p>
          </section>

          {/* 20. İletişim */}
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-primary tracking-tight">20. İletişim Bilgileri</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Bu kullanım koşullarına ilişkin her türlü soru, bildirim veya yasal talepleriniz için bizimle doğrudan iletişime geçebilirsiniz:
            </p>
            <div className="p-5 border border-hairline rounded-sm bg-soft-stone mt-4">
              <p className="text-ink text-sm font-medium">Clarere Destek Ekibi</p>
              <p className="text-body-muted text-xs mt-1">E-Posta: <a href="mailto:hiclarere@clarere.com" className="text-coral hover:underline font-semibold font-mono">hiclarere@clarere.com</a></p>
            </div>
          </section>

        </div>

        <div className="pt-8 border-t border-hairline text-xs text-body-muted font-mono leading-relaxed">
          * Clarere deneysel bir pazar simülasyonu ürünüdür ve üretim ortamında körü körüne kullanıma henüz tam hazır değildir. Riskleri değerlendirerek kullanınız.
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-hairline py-8 mt-16">
        <div className="max-w-4xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-body-muted">
          <div className="flex items-center gap-2">
            <Logo size={24} strokeColor="#93939f" />
            <span>Clarere © 2026</span>
          </div>
          <div className="flex gap-6">
            <Link href="/" className="hover:text-primary transition-colors">Ana Sayfa</Link>
            <Link href="/privacy" className="hover:text-primary transition-colors">Gizlilik Politikası</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
