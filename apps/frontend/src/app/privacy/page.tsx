import type { Metadata } from "next";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import Logo from "@/components/logo";

export const metadata: Metadata = {
  title: "Gizlilik Politikası & KVKK Aydınlatma Metni — Clarere",
  description:
    "Clarere&apos;nin kişisel verileri nasıl işlediğini, KVKK ve GDPR kapsamındaki haklarınızı ve veri güvenliği uygulamalarımızı öğrenin.",
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
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
            Gizlilik Politikası & KVKK Aydınlatma Metni
          </h1>
          <p className="text-lg text-body-muted leading-relaxed">
            Clarere olarak kişisel bilgilerinizin güvenliğini sağlamayı taahhüt ediyoruz. Bu politika, hizmetlerimizi kullandığınızda bilgilerinizin nasıl toplandığını, kullanıldığını, paylaşıldığını ve korunduğunu açıklar.
          </p>
          <p className="text-xs text-body-muted mt-4">Son güncelleme: 12 Eylül 2026</p>
        </header>

        {/* Policy Sections */}
        <div className="space-y-12">
          
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">1. Beta Sürüm Bildirimi</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Sitemiz ve ilgili hizmetlerimiz şu anda erken beta aşamasındadır; hatalar, eksiklikler veya tamamlanmamış özellikler içerebilir. Site, yalnızca ön kullanım, test ve değerlendirme amaçlıdır. Ürünün tam olarak piyasaya sürüleceği veya belirli özelliklerin kalıcı olacağı garanti edilmez.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">2. Biz Kimiz?</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              <strong className="text-primary">Clarere</strong>, yapay zeka öncelikli bir kullanıcı test ve araştırma platformudur. Bir finans kuruluşu veya danışmanlık hizmeti değiliz; sitemizdeki hiçbir şey finansal tavsiye niteliği taşımaz. Sitede sunulan yapay zeka personaları kurgusaldır ve gerçek kişilerin yerine geçmez.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">3. Toplanan Bilgiler</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Hizmetlerimizi kullandığınızda veya platforma kayıt olduğunuzda aşağıdaki kategorideki kişisel verileriniz işlenmektedir:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-4">
              <div className="p-5 border border-hairline rounded-sm bg-white">
                <span className="mono-label text-coral block mb-2 font-semibold">İLETİŞİM BİLGİLERİ</span>
                <strong className="text-primary font-semibold block mb-1 text-sm">E-Posta Adresi</strong>
                <p className="text-xs text-body-muted leading-relaxed">Bekleme listesine katıldığınızda, hesap açtığınızda veya bizimle iletişime geçtiğinizde e-posta adresiniz toplanır.</p>
              </div>
              <div className="p-5 border border-hairline rounded-sm bg-white">
                <span className="mono-label text-coral block mb-2 font-semibold">ARAŞTIRMA BİLGİLERİ</span>
                <strong className="text-primary font-semibold block mb-1 text-sm">Landing Page & Brief Verileri</strong>
                <p className="text-xs text-body-muted leading-relaxed">Analiz edilmesi için gönderdiğiniz web site URL&apos;leri, araştırma brief&apos;leri ve bu içeriklerden elde edilen analizler toplanır.</p>
              </div>
              <div className="p-5 border border-hairline rounded-sm bg-white">
                <span className="mono-label text-coral block mb-2 font-semibold">TEKNİK KAYITLAR</span>
                <strong className="text-primary font-semibold block mb-1 text-sm">Kullanım ve Maliyet Kayıtları</strong>
                <p className="text-xs text-body-muted leading-relaxed">Hesabınıza ait araştırma sayısı, kullanılan token miktarı ve tahmini maliyet; hizmetin sunulması ve plan limitlerinin uygulanması amacıyla kaydedilir. Reklam veya üçüncü taraf izleme aracı kullanılmaz.</p>
              </div>
              <div className="p-5 border border-hairline rounded-sm bg-white">
                <span className="mono-label text-coral block mb-2 font-semibold">HATA İZLEME</span>
                <strong className="text-primary font-semibold block mb-1 text-sm">Teknik Hata Kayıtları</strong>
                <p className="text-xs text-body-muted leading-relaxed">Sunucu hatalarını teşhis etmek için Sentry üzerinden teknik hata kayıtları tutulur. Kişisel verilerin hata kayıtlarına aktarımı devre dışıdır; form alanlarına yazdığınız metinler kaydedilmez.</p>
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">4. Verilerin Kullanım Amaçları</h2>
            <div className="space-y-4">
              <div className="flex items-start gap-3 border-b border-hairline pb-4">
                <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                <div className="text-sm text-body-muted">
                  <strong className="text-primary block mb-0.5">İletişim ve Destek</strong>
                  Sizinle beta davetleri, platform güncellemeleri, faturalandırma ve teknik yardım konularında iletişim kurmak.
                </div>
              </div>
              <div className="flex items-start gap-3 border-b border-hairline pb-4">
                <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                <div className="text-sm text-body-muted">
                  <strong className="text-primary block mb-0.5">Hizmet Sağlama</strong>
                  Talep ettiğiniz yapay zeka tabanlı sentetik pazar araştırmalarını, mülakat simülasyonlarını ve sentez raporlarını üretmek.
                </div>
              </div>
              <div className="flex items-start gap-3 border-b border-hairline pb-4">
                <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                <div className="text-sm text-body-muted">
                  <strong className="text-primary block mb-0.5">Hata Giderme & Optimizasyon</strong>
                  Platformdaki teknik aksaklıkları tespit edip gidermek, kullanıcı akışlarını ve arayüz deneyimini daha akıcı hale getirmek.
                </div>
              </div>
              <div className="flex items-start gap-3 pb-2">
                <CheckCircle2 size={16} className="text-deep-green shrink-0 mt-1" />
                <div className="text-sm text-body-muted">
                  <strong className="text-primary block mb-0.5">Güvenlik ve Uyum</strong>
                  Platformun kötüye kullanımını, bot saldırılarını engellemek ve yasal mevzuata tam uyum sağlamak.
                </div>
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">5. İşleme Dayanakları (KVKK / GDPR Hukuki Sebepleri)</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Kişisel verileriniz, 6698 sayılı KVKK ve GDPR kapsamında aşağıdaki hukuki dayanaklara göre işlenmektedir:
            </p>
            <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
              <li><strong>Açık Rıza (Consent):</strong> Form doldurarak, bültene katılarak veya bekleme listesine girerek paylaştığınız veriler açık rızanıza dayanır.</li>
              <li><strong>Sözleşmenin İfası (Contractual Necessity):</strong> Üyelik sözleşmesi kapsamındaki hizmetlerin (simülasyonlar, raporlar) tarafınıza sunulabilmesi için veri işlenmesinin zorunlu olması.</li>
              <li><strong>Meşru Menfaat (Legitimate Interests):</strong> Sitemizin güvenliğini sağlamak, siber saldırıları önlemek ve hizmet kalitesini artırmak için meşru menfaatimiz kapsamındaki işlemler.</li>
              <li><strong>Yasal Yükümlülükler (Legal Obligation):</strong> Kanun koyucu ve resmi makamların (KVKK, BTK vb.) zorunlu kıldığı idari ve teknik gerekliliklere uyulması.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">6. Verilerin Paylaşılması</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Clarere, kişisel verilerinizi üçüncü şahıslara satmaz veya kiralamaz. Verileriniz sadece aşağıdaki durumlarda ve amaçlarla sınırlı olarak paylaşılabilir:
            </p>
            <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
              <li><strong>Hizmet Sağlayıcılar (Alt İşleyiciler):</strong> Ödeme: <strong>Paddle</strong> (merchant of record) · Büyük dil modeli: <strong>DeepSeek API</strong> · Veritabanı ve barındırma: kendi sunucumuz (self-hosted) veya yönetilen bulut sağlayıcı · İşlemsel e-posta: <strong>Resend</strong> · Hata izleme: <strong>Sentry</strong>. Aktif barındırma sağlayıcıları dağıtım kararına göre değişebilir; güncel listeyi talep üzerine ve bu sayfada ilan ederiz. Bu sağlayıcılar yalnızca hizmeti sunmak için gereken veriyle sınırlıdır ve verileriniz hiçbir koşulda satılmaz veya kiralanmaz.</li>
              <li><strong>Yasal Zorunluluklar:</strong> Bir mahkeme kararı, savcılık talebi veya yürürlükteki yasal süreçlerin zorunlu kıldığı durumlarda yetkili resmi makamlarla.</li>
              <li><strong>Şirket Yapısı Değişiklikleri:</strong> Şirket birleşmesi, devri veya varlık satışı gibi yapısal durumlarda veriler, gizlilik taahhüdü korunarak halef kuruluşa aktarılabilir.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">6A. Veri Akışı Özeti</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Hangi verinin hangi bileşene gittiğini şeffaf şekilde özetliyoruz:
            </p>
            <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
              <li><strong>Araştırma brief&apos;i ve ürün fikri →</strong> Büyük dil modeli (DeepSeek API). Model çağrısı için gereklidir; bir PII maskeleme katmanı (telefon/e-posta/TC) bu veriyi gönderim öncesi temizler. İsim/lokasyon gibi alanlar için yerel NER modeli yalnızca kurumsal planda devreye girer.</li>
              <li><strong>Ödeme bilgisi →</strong> Paddle (merchant of record). Clarere kart bilgisi <strong>saklamaz</strong>; ödeme Paddle altyapısında işlenir.</li>
              <li><strong>Araştırma çıktıları ve raporlar →</strong> Kendi veritabanımız. KVKK kapsamındaki indirme ve silme haklarınızı hesabınızdan self-servis kullanabilirsiniz.</li>
              <li><strong>Teknik hata kayıtları →</strong> Sentry (kişisel veri gönderimi devre dışı).</li>
              <li><strong>İşlemsel e-postalar →</strong> Resend.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">7. Uluslararası Veri Transferleri</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Kullanılan bulut altyapısı ve analiz araçlarının doğası gereği verileriniz, ikamet ettiğiniz ülke dışındaki (örneğin ABD veya AB ülkeleri) güvenli veri merkezlerinde saklanabilir. Bu tür transferlerde, KVKK Kurul kararları ve GDPR Standart Sözleşme Maddeleri (SCC) gibi uluslararası yasal koruma mekanizmaları ve şifreleme yöntemleri eksiksiz olarak uygulanır.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">8. Veri Saklama Süresi</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Bilgileriniz, toplama amacına hizmet ettiği sürece saklanır. Bekleme listesinden çıktığınızda veya üyelik hesabınızı sildiğinizde veriler güvenli bir şekilde silinir veya tamamen anonim hale getirilir.
            </p>
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-sm border border-hairline rounded-sm overflow-hidden">
                <thead className="bg-soft-stone">
                  <tr>
                    <th className="text-left px-4 py-3 font-semibold text-primary">Veri Türü</th>
                    <th className="text-left px-4 py-3 font-semibold text-primary">Saklama Süresi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline bg-white">
                  {[
                    ["Araştırma Raporları & Brief&apos;ler", "Hesap aktif olduğu sürece + 1 yıl"],
                    ["Kullanım ve Maliyet Kayıtları", "12 ay"],
                    ["Güvenlik Logları (Erişim kayıtları)", "2 yıl (5651 sayılı kanun gereği)"],
                    ["E-Posta Adresi", "Hesap aktif olduğu sürece"],
                    ["Ödeme & Fatura Kayıtları", "10 yıl (Türk Ticaret Kanunu gereği)"],
                  ].map(([type, duration]) => (
                    <tr key={type} className="hover:bg-soft-stone/20 transition-colors">
                      <td className="px-4 py-3 text-ink font-medium">{type}</td>
                      <td className="px-4 py-3 text-body-muted">{duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">9. Güvenlik Önlemleri</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Kişisel verilerinizin yetkisiz erişime, kayba veya kötüye kullanıma karşı korunması için Clarere en yüksek sektör standartlarında teknik tedbirler uygulamaktadır:
            </p>
            <ul className="space-y-2 text-sm text-body-muted pl-5 list-disc leading-relaxed">
              <li>Verileriniz tarayıcınız ile sunucularımız arasında aktarılırken <strong>HTTPS ve TLS 1.3 şifreleme protokolleri</strong> ile korunur.</li>
              <li>Veritabanı düzeyinde gelişmiş erişim kontrolleri (IAM) ve ağ izolasyonu sağlanmıştır.</li>
              <li>Kaba kuvvet (brute force) saldırılarını ve bot trafiğini önlemek için aktif rate-limiting algoritmaları devrededir.</li>
              <li>Ekibimizden sadece kısıtlı ve yetkilendirilmiş personel, destek amaçlı veri kontrolleri gerçekleştirebilir.</li>
              <li><em>Not: İnternet üzerinden yapılan hiçbir aktarım yöntemi %100 güvenli değildir. Bu nedenle tüm güvenlik önlemlerimize rağmen risklerin tamamen sıfırlanamayacağını hatırlatırız.</em></li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">10. Haklarınız (KVKK ve GDPR Kapsamında)</h2>
            <p className="text-body-muted leading-relaxed text-sm mb-4">
              Kişisel verilerinizin sahibi olarak, mevzuat uyarınca aşağıdaki yasal haklara sahipsiniz:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { title: "Bilgi Alma & Erişim", desc: "Kişisel verilerinizin işlenip işlenmediğini öğrenme ve bilgi talep etme." },
                { title: "Düzeltme (Correction)", desc: "Hatalı veya eksik kişisel verilerinizin güncellenmesini isteme." },
                { title: "Silme & Unutulma", desc: "Belirli yasal şartlar oluştuğunda verilerinizin sistemlerimizden silinmesini isteme." },
                { title: "İşlemeyi Sınırlandırma", desc: "Veri işleme faaliyetinin geçici veya kalıcı olarak durdurulmasını talep etme." },
                { title: "Veri Taşınabilirliği", desc: "İşlenen verilerinizi yaygın, okunabilir dijital formatta talep etme." },
                { title: "Rızayı Geri Çekme", desc: "Açık rızanıza dayanarak yapılan veri işlemelerini istediğiniz zaman durdurma." },
              ].map(({ title, desc }) => (
                <div key={title} className="p-4 border border-hairline rounded-sm bg-white">
                  <strong className="text-primary font-semibold block mb-1 text-sm">{title}</strong>
                  <p className="text-xs text-body-muted leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">10A. Haklarınızı Self-Servis Kullanma</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              KVKK/GDPR kapsamındaki <strong>veri taşınabilirliği</strong> ve <strong>silme</strong> haklarınızı hesabınızdan doğrudan kullanabilirsiniz:
            </p>
            <ul className="space-y-3 text-sm text-body-muted list-disc pl-5 leading-relaxed">
              <li><strong>Verilerimi indir:</strong> Hesabınıza ait tüm veriler (araştırmalar, mülakatlar, raporlar, geri bildirimler, kullanım kayıtları) makine-okunur JSON biçiminde indirilir.</li>
              <li><strong>Hesabımı sil:</strong> Aktif bir aboneliğiniz varsa önce Paddle üzerinden iptal edilir; ardından kişisel verileriniz sistemlerimizden silinir.</li>
              <li>Silme talebiniz; fatura/vergi mevzuatı gibi yasal saklama yükümlülüğü bulunan kayıtlar hariç olmak üzere en kısa sürede yerine getirilir.</li>
              <li>Bu haklarınızı arayüzden kullanamıyorsanız <a href="mailto:hiclarere@clarere.com" className="text-coral hover:underline font-semibold font-mono">hiclarere@clarere.com</a> adresine yazabilirsiniz.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">10B. Çerezler ve Yerel Depolama</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Clarere yalnızca oturum yönetimi için gerekli teknik verileri kullanır: tarayıcınızda tutulan bir oturum işareti çerezi ve oturum tokenı için yerel depolama (localStorage). Reklam veya üçüncü taraf izleme çerezi kullanılmaz.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">11. Politika Güncellemeleri</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Yasal, operasyonel veya sistemsel değişiklikler doğrultusunda bu Gizlilik Politikası zaman zaman güncellenebilir. Önemli bir değişiklik yapıldığında kayıtlı kullanıcılarımıza e-posta yoluyla veya platform içinde belirgin bir duyuruyla bildirim yapılacaktır. Güncel politika her zaman bu sayfada erişilebilir durumda olacaktır.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-xl font-bold text-primary tracking-tight">12. İletişim ve Başvuru</h2>
            <p className="text-body-muted leading-relaxed text-sm">
              Gizlilik politikamızla ilgili her türlü soru, görüş veya KVKK/GDPR kapsamındaki haklarınızın kullanımı yönündeki talepleriniz için bizimle doğrudan iletişime geçebilirsiniz:
            </p>
            <div className="p-5 border border-hairline rounded-sm bg-soft-stone mt-4">
              <p className="text-ink text-sm font-medium">Clarere Veri Güvenliği Ekibi</p>
              <p className="text-body-muted text-xs mt-1">E-Posta: <a href="mailto:hiclarere@clarere.com" className="text-coral hover:underline font-semibold font-mono">hiclarere@clarere.com</a></p>
            </div>
          </section>

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
            <Link href="/terms" className="hover:text-primary transition-colors">Kullanım Şartları</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
