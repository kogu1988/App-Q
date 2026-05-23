import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Gizlilik Politikası & KVKK Aydınlatma Metni — Clarere",
  description:
    "Clarere'nun kişisel verileri nasıl işlediğini, KVKK kapsamındaki haklarınızı ve veri güvenliği uygulamalarımızı öğrenin.",
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-primary text-primary-foreground flex items-center justify-center text-sm font-black rounded-lg">
              Q
            </div>
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
          <h1 className="text-4xl font-black tracking-tight">Gizlilik Politikası</h1>
          <p className="text-muted-foreground text-lg">
            6698 Sayılı Kişisel Verilerin Korunması Kanunu (KVKK) Kapsamında Aydınlatma Metni
          </p>
          <p className="text-xs text-muted-foreground">Son güncelleme: 23 Mayıs 2026</p>
        </header>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">1. Veri Sorumlusu</h2>
          <p className="text-muted-foreground leading-relaxed">
            Bu aydınlatma metni, <strong className="text-foreground">Clarere</strong> platformunu işleten veri sorumlusu tarafından
            6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") madde 10 uyarınca hazırlanmıştır.
            Platform, Türkiye'deki kullanıcılara yapay zeka destekli sentetik pazar araştırması hizmetleri sunmaktadır.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">2. İşlenen Kişisel Veriler</h2>
          <p className="text-muted-foreground leading-relaxed">
            Platformu kullandığınızda aşağıdaki veriler işlenebilir:
          </p>
          <ul className="space-y-2 text-muted-foreground list-none">
            {[
              { label: "Kullanıcı adı", desc: "Platforma erişim ve araştırma kayıtları için." },
              { label: "E-posta adresi", desc: "Hesap yönetimi ve sistem bildirimleri için (Kurumsal planlar)." },
              { label: "Araştırma içerikleri", desc: "Oluşturduğunuz brief, mülakat planı ve sentez raporları." },
              { label: "Kullanım verileri", desc: "Simülasyon sayısı, token kullanımı, oturum bilgileri." },
              { label: "Teknik veriler", desc: "IP adresi, tarayıcı türü, erişim saati (güvenlik logları)." },
            ].map(({ label, desc }) => (
              <li key={label} className="flex gap-3 p-3 rounded-lg bg-muted/40">
                <span className="font-semibold text-foreground shrink-0">• {label}:</span>
                <span>{desc}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">3. Kişisel Verilerin İşlenme Amaçları</h2>
          <p className="text-muted-foreground leading-relaxed">
            Kişisel verileriniz aşağıdaki amaçlarla, KVKK'nın 5. ve 6. maddelerinde belirtilen hukuki sebeplere dayanılarak işlenmektedir:
          </p>
          <ul className="space-y-1 text-muted-foreground pl-4">
            <li>• Hizmetin sunulması ve araştırma workflow'unun yürütülmesi</li>
            <li>• Abonelik ve plan limiti yönetimi</li>
            <li>• Kullanıcı doğrulama ve güvenlik</li>
            <li>• Hizmet kalitesinin iyileştirilmesi (anonim istatistikler)</li>
            <li>• Yasal yükümlülüklerin yerine getirilmesi</li>
            <li>• Teknik destek ve müşteri hizmetleri</li>
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">4. Sentetik Veriler ve Gizlilik</h2>
          <div className="p-4 rounded-xl border border-border bg-muted/20 space-y-2">
            <p className="text-foreground font-semibold">Önemli: Sentetik Persona Verileri</p>
            <p className="text-muted-foreground leading-relaxed">
              Clarere'nun ürettiği sentetik personalar ve mülakat yanıtları, gerçek kişilere ait veriler değildir.
              Bu veriler, yapay zeka modelleri tarafından istatistiksel örüntüler kullanılarak üretilmiş
              kurgusal içeriklerdir. Hiçbir sentetik persona gerçek bir bireyi temsil etmez veya ona atıfta bulunmaz.
            </p>
          </div>
          <p className="text-muted-foreground leading-relaxed">
            Araştırma brief'lerinizde gerçek kişilerin isim, iletişim bilgisi veya kimlik bilgilerini
            paylaşmamanızı tavsiye ederiz. PII (Kişisel Tanımlayıcı Bilgi) maskeleme özelliği aktif olduğunda
            sistem bu tür verileri otomatik olarak filtreler.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">5. Veri Saklama Süreleri</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border border-border rounded-lg overflow-hidden">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold">Veri Türü</th>
                  <th className="text-left px-4 py-3 font-semibold">Saklama Süresi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  ["Araştırma raporları", "Hesap aktif olduğu sürece + 1 yıl"],
                  ["Kullanım logları", "6 ay"],
                  ["Güvenlik logları", "2 yıl (yasal zorunluluk)"],
                  ["E-posta adresi", "Hesap silinene kadar"],
                  ["Fatura kayıtları", "10 yıl (Türk Ticaret Kanunu)"],
                ].map(([type, duration]) => (
                  <tr key={type}>
                    <td className="px-4 py-3 text-foreground">{type}</td>
                    <td className="px-4 py-3 text-muted-foreground">{duration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">6. Veri Güvenliği</h2>
          <p className="text-muted-foreground leading-relaxed">
            Verilerinizi korumak için aşağıdaki teknik ve idari tedbirler uygulanmaktadır:
          </p>
          <ul className="space-y-1 text-muted-foreground pl-4">
            <li>• HTTPS/TLS ile şifrelenmiş veri iletimi</li>
            <li>• Veritabanı erişim kontrolü ve bağlantı havuzu güvenliği</li>
            <li>• Admin API'ye gizli anahtar (secret key) koruması</li>
            <li>• Rate limiting ile kaba kuvvet saldırılarına karşı koruma</li>
            <li>• Düzenli güvenlik denetimleri</li>
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">7. Üçüncü Taraflarla Veri Paylaşımı</h2>
          <p className="text-muted-foreground leading-relaxed">
            Kişisel verileriniz; açık rızanız olmaksızın üçüncü taraflarla pazarlama amaçlı paylaşılmaz.
            Hizmetin yürütülmesi için aşağıdaki kategorideki veri işleyenlerle çalışılmaktadır:
          </p>
          <ul className="space-y-1 text-muted-foreground pl-4">
            <li>• <strong className="text-foreground">Altyapı sağlayıcıları:</strong> Sunucu ve veritabanı hizmetleri (PostgreSQL, Redis)</li>
            <li>• <strong className="text-foreground">Yapay zeka sağlayıcıları:</strong> LLM inference için yerel/harici model sağlayıcıları</li>
            <li>• <strong className="text-foreground">Yasal makamlar:</strong> Türk hukuku kapsamında yasal taleplere uymak için</li>
          </ul>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">8. KVKK Kapsamındaki Haklarınız</h2>
          <p className="text-muted-foreground leading-relaxed">
            KVKK'nın 11. maddesi uyarınca aşağıdaki haklara sahipsiniz:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { hak: "Bilgi alma hakkı", desc: "Verilerinizin işlenip işlenmediğini öğrenme" },
              { hak: "Erişim hakkı", desc: "İşlenen verilerinize erişim talep etme" },
              { hak: "Düzeltme hakkı", desc: "Yanlış/eksik verilerin düzeltilmesini isteme" },
              { hak: "Silme hakkı", desc: "Belirli koşullarda verilerinizin silinmesini talep etme" },
              { hak: "İtiraz hakkı", desc: "Otomatik işleme dayalı kararlara itiraz etme" },
              { hak: "Şikâyet hakkı", desc: "KVKK İhlali için KVK Kurulu'na başvurma" },
            ].map(({ hak, desc }) => (
              <div key={hak} className="p-3 rounded-lg border border-border space-y-1">
                <p className="font-semibold text-sm text-foreground">{hak}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </div>
            ))}
          </div>
          <p className="text-muted-foreground text-sm">
            Haklarınızı kullanmak için:{" "}
            <a href="mailto:privacy@clarere.com" className="text-primary hover:underline">
              privacy@clarere.com
            </a>{" "}
            adresine yazılı başvuruda bulunabilirsiniz.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">9. Çerezler (Cookies)</h2>
          <p className="text-muted-foreground leading-relaxed">
            Clarere, oturum yönetimi için <strong className="text-foreground">localStorage</strong> kullanmaktadır.
            Geleneksel çerez (cookie) mekanizması şu an kullanılmamaktadır. Kullanıcı adı ve oturum bilgileri
            yalnızca tarayıcınızın yerel depolama alanında tutulur ve sunuculara gönderilmez.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold">10. Politika Güncellemeleri</h2>
          <p className="text-muted-foreground leading-relaxed">
            Bu gizlilik politikası, yasal değişiklikler veya hizmet güncellemeleri doğrultusunda
            değiştirilebilir. Önemli değişiklikler için kayıtlı kullanıcılar bilgilendirilecektir.
            Güncel versiyon her zaman bu sayfada yayınlanır.
          </p>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8 mt-16">
        <div className="max-w-4xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-black rounded">Q</div>
            <span>Clarere © 2026</span>
          </div>
          <div className="flex gap-6">
            <Link href="/" className="hover:text-foreground transition-colors">Ana Sayfa</Link>
            <Link href="/terms" className="hover:text-foreground transition-colors">Kullanım Şartları</Link>
            <Link href="/#pricing" className="hover:text-foreground transition-colors">Fiyatlandırma</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
