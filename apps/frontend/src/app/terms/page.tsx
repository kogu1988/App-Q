import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Kullanım Koşulları — Clarere",
  description:
    "Clarere platformunu kullanmadan önce lütfen kullanım koşullarını okuyunuz. Hizmet kapsamı, sorumluluk sınırları ve tarafların hak ve yükümlülükleri.",
  robots: { index: true, follow: true },
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/logo.png" alt="Clarere" className="h-8 w-auto object-contain" />
            <span className="font-bold text-lg tracking-tight">Clarere</span>
          </Link>
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            ← Ana Sayfa
          </Link>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-16 space-y-12">
        <header className="space-y-4 pb-8 border-b border-border">
          <h1 className="text-4xl font-black tracking-tight">Kullanım Koşulları</h1>
          <p className="text-muted-foreground text-lg">
            Clarere platformunu kullanarak aşağıdaki koşulları kabul etmiş sayılırsınız.
          </p>
          <p className="text-xs text-muted-foreground">Son güncelleme: 23 Mayıs 2026</p>
        </header>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">1. Taraflar ve Kapsam</h2>
          <p className="text-muted-foreground leading-relaxed">
            Bu kullanım koşulları, <strong className="text-foreground">Clarere</strong> platformu
            ("Platform") ile platformu kullanan bireysel veya kurumsal kullanıcılar ("Kullanıcı")
            arasındaki hukuki ilişkiyi düzenlemektedir. Platforma erişerek veya herhangi bir
            özelliğini kullanarak bu koşulları kabul etmiş sayılırsınız.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">2. Hizmetin Tanımı</h2>
          <p className="text-muted-foreground leading-relaxed">
            Clarere, <strong className="text-foreground">yapay zeka destekli sentetik pazar araştırması</strong> platformudur.
            Platform; araştırma brief'i alımı, sentetik persona oluşturma, mülakat simülasyonu ve
            rapor sentezi hizmetleri sunar.
          </p>
          <div className="p-4 rounded-xl border border-border bg-muted/20 space-y-2">
            <p className="text-foreground font-semibold text-sm">⚠️ Önemli Kapsam Bildirimi</p>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Clarere bir <strong className="text-foreground">hipotez ve araştırma triage aracıdır</strong>.
              Gerçek müşteri araştırmasının yerini almaz; gerçek pazar testlerinden önce zaman ve
              bütçe kaybını azaltmak amacıyla kullanılır. Platform çıktıları, istatistiksel güven
              iddiasında bulunmaz; kararlar için referans, gerçek araştırma için başlangıç noktası
              olarak değerlendirilmelidir.
            </p>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">3. Sentetik Veriler ve Metodoloji</h2>
          <p className="text-muted-foreground leading-relaxed">
            Platform, aşağıdaki bilimsel çerçevelere dayanan <em>Grounded Simulation</em> mimarisini kullanır:
          </p>
          <ul className="space-y-1 text-muted-foreground pl-4">
            <li>• <strong className="text-foreground">OCEAN / Big Five psikometri</strong> — NEO-PI-R 30 facet annotasyonuyla persona oluşturma</li>
            <li>• <strong className="text-foreground">Rogers Diffusion of Innovation</strong> — benimseme stance dağılımı (Innovator, Early Adopter, Mainstream, Laggard, Skeptic)</li>
            <li>• <strong className="text-foreground">Van Westendorp Fiyat Duyarlılığı Modeli</strong> — optimal fiyat noktası (OPP/IPP) analizi</li>
            <li>• <strong className="text-foreground">Adversarial Review</strong> — bias denetimi, kanıt zinciri doğrulama</li>
            <li>• <strong className="text-foreground">Research Fidelity Index (RFI)</strong> — 6 bileşenli araştırma kalite skoru (Bilal, 2026)</li>
          </ul>
          <p className="text-muted-foreground leading-relaxed">
            Üretilen sentetik personalar ve mülakat yanıtları kurgusal içeriklerdir; gerçek bireylerle
            herhangi bir bağlantısı yoktur.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">4. Kullanıcı Yükümlülükleri</h2>
          <p className="text-muted-foreground leading-relaxed">
            Platform kullanıcıları aşağıdaki koşullara uymayı kabul eder:
          </p>
          <ul className="space-y-2 text-muted-foreground">
            {[
              "Platformu yalnızca meşru araştırma ve iş geliştirme amaçlarıyla kullanmak",
              "Araştırma brief'lerine gerçek kişilere ait kimlik, iletişim veya hassas kişisel veriler girmemek",
              "Platform çıktılarını kesinleşmiş gerçekler veya istatistiksel kanıt olarak sunmamak",
              "Belirlenen simülasyon ve token limitlerini aşmamak",
              "Sistemin güvenliğini, bütünlüğünü veya performansını tehlikeye atacak işlemler yapmamak",
              "Platform içeriğini, raporlarını veya üretilen materyalleri kendi ürünü gibi satmamak veya yeniden dağıtmamak (Enterprise planı hariç)",
            ].map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-primary shrink-0">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">5. Plan Limitleri ve Hizmet Kotaları</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold">Plan</th>
                  <th className="text-left px-4 py-3 font-semibold">Simülasyon</th>
                  <th className="text-left px-4 py-3 font-semibold">Token Limiti</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  ["Free", "2 / ay", "50.000"],
                  ["Starter", "10 / ay", "200.000"],
                  ["Pro", "50 / ay", "1.000.000"],
                  ["Enterprise", "Sınırsız*", "50.000.000"],
                ].map(([plan, sim, token]) => (
                  <tr key={plan}>
                    <td className="px-4 py-3 font-medium text-foreground">{plan}</td>
                    <td className="px-4 py-3 text-muted-foreground">{sim}</td>
                    <td className="px-4 py-3 text-muted-foreground">{token}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-muted-foreground">
            * Enterprise sınırsız kotası adil kullanım (fair use) politikasına tabidir.
            Kullanılmayan simülasyon hakları bir sonraki döneme devretmez.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">6. Fikri Mülkiyet ve Çalışma Algoritmasının Korunması</h2>

          <div className="space-y-4 text-muted-foreground">
            <div className="p-4 rounded-xl border border-border bg-muted/20">
              <p className="font-semibold text-foreground mb-2">Tescilli Teknoloji ve Ticari Sır</p>
              <p className="leading-relaxed text-sm">
                Clarere'nun çalışma algoritması — persona oluşturma motoru, mülakat simülasyon
                katmanı, sentez pipeline'ı, anti-sycophancy mekanizması ve Research Fidelity
                Index (RFI) puanlama sistemi dahil olmak üzere tüm bileşenleri — platform
                sahibinin <strong className="text-foreground">ticari sırrını ve tescilli
                teknolojisini</strong> oluşturmaktadır. Bu bileşenler Türkiye Cumhuriyeti
                hukuku kapsamında ticari sır olarak korunmaktadır.
              </p>
            </div>

            <p className="leading-relaxed">
              <strong className="text-foreground">Korunan bileşenler:</strong>
            </p>
            <ul className="space-y-1.5 pl-4 text-sm">
              {[
                "Grounded Simulation mimarisi ve birden fazla bilimsel çerçeveyi entegre eden katmanlı yapı",
                "OCEAN / Big Five + Rogers Diffusion + Hofstede kültürel boyutlarını birleştiren persona üretim algoritması",
                "ACT-R bilişsel hafıza modelini uygulayan mülakat simülasyon motoru",
                "Anti-sycophancy dedektörü ve gizli yargıç mekanizması",
                "6 bileşenli Research Fidelity Index (PGR, CNS, AC, PCal, PR, CRA) hesaplama metodolojisi",
                "Adversarial Review pipeline'ı (bias audit, evidence chain validation, double-simulation check)",
                "LLM sistem promptları ve persona yönlendirme şablonları",
                "Semantik soru önbelleği ve çift model yönlendirme sistemi",
              ].map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-primary shrink-0">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <p className="leading-relaxed">
              <strong className="text-foreground">Yasak eylemler:</strong> Kullanıcılar platform
              altyapısına yetkisiz erişim sağlayamaz, tersine mühendislik (reverse engineering)
              uygulayamaz, sistem promptlarını veya API yanıtlarını analiz ederek algoritmayı
              yeniden üretemez, çalışma mekanizmasını rakip ürünlerde kullanamaz veya bu bilgileri
              üçüncü şahıslarla paylaşamaz.
            </p>

            <p className="leading-relaxed">
              <strong className="text-foreground">Kullanıcı içeriği:</strong> Kullanıcının
              platforma yüklediği araştırma brief'leri ve oluşturulan raporlar kullanıcıya aittir.
              Clarere bu içerikleri üçüncü taraflarla paylaşmaz; yalnızca hizmet iyileştirmesi
              için anonim istatistiksel veriler kullanabilir.
            </p>

            <p className="leading-relaxed">
              <strong className="text-foreground">İhlal halinde:</strong> Bu maddenin ihlali
              halinde Platform, yasal yollara başvurma ve uğradığı zararları talep etme hakkını
              saklı tutar. Hukuki ihlaller için yetkili mahkeme İstanbul mahkemeleridir.
            </p>
          </div>
        </section>


        <section className="space-y-4">
          <h2 className="text-xl font-bold">7. Sorumluluk Sınırları</h2>
          <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50/30 dark:bg-amber-950/10 space-y-2">
            <p className="font-semibold text-sm text-amber-800 ">Yasal Uyarı</p>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Clarere, platform çıktılarının (raporlar, persona yanıtları, fiyat analizi) doğruluğunu
              garanti etmez. Sentetik araştırma bulguları, yatırım kararı, yasal süreç, tıbbi tavsiye
              veya benzeri kritik kararlar için tek kaynak olarak kullanılamaz. Platform, kullanıcının
              bu koşulları ihlal etmesinden veya platform çıktılarını yanlış yorumlamasından doğan
              zararlardan sorumlu tutulamaz.
            </p>
          </div>
          <p className="text-muted-foreground leading-relaxed">
            Platformun azami sorumluluğu, herhangi bir olay veya talep için son 3 aya ait abonelik
            ücretiyle sınırlıdır.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">8. Hizmet Durdurma ve Hesap İptali</h2>
          <p className="text-muted-foreground leading-relaxed">
            Clarere, aşağıdaki durumlarda kullanıcı hesabını geçici olarak askıya alabilir veya
            kalıcı olarak iptal edebilir:
          </p>
          <ul className="space-y-1 text-muted-foreground pl-4">
            <li>• Bu koşulların ihlali</li>
            <li>• Sistemin kötüye kullanımı veya platform güvenliğine yönelik eylemler</li>
            <li>• Ödeme yükümlülüklerinin yerine getirilmemesi</li>
            <li>• Yasal mevzuat gereklilikleri</li>
          </ul>
          <p className="text-muted-foreground leading-relaxed">
            Hesap iptali durumunda mevcut dönem ücreti iade edilmez. Kullanıcı verilerinin
            30 gün içinde talep edilmesi gerekmektedir.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">9. Uygulanacak Hukuk</h2>
          <p className="text-muted-foreground leading-relaxed">
            Bu koşullar Türkiye Cumhuriyeti hukukuna tabidir. Taraflar arasında doğabilecek
            uyuşmazlıkların çözümünde <strong className="text-foreground">İstanbul</strong> mahkemeleri
            ve icra daireleri yetkilidir.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">10. Koşullardaki Değişiklikler</h2>
          <p className="text-muted-foreground leading-relaxed">
            Clarere bu koşulları önceden bildirmeksizin güncelleyebilir. Önemli değişiklikler
            için kayıtlı kullanıcılar 30 gün önceden bilgilendirilir. Değişikliklerden sonra
            platformu kullanmaya devam etmeniz, yeni koşulları kabul ettiğiniz anlamına gelir.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">11. İletişim</h2>
          <p className="text-muted-foreground">
            Kullanım koşullarına ilişkin sorularınız için:{" "}
            <a href="mailto:legal@clarere.com" className="text-primary hover:underline">
              legal@clarere.com
            </a>
          </p>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8 mt-16">
        <div className="max-w-4xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Clarere" className="h-6 w-auto object-contain" />
            <span>Clarere © 2026</span>
          </div>
          <div className="flex gap-6">
            <Link href="/" className="hover:text-foreground transition-colors">Ana Sayfa</Link>
            <Link href="/privacy" className="hover:text-foreground transition-colors">Gizlilik Politikası</Link>
            <Link href="/#pricing" className="hover:text-foreground transition-colors">Fiyatlandırma</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
