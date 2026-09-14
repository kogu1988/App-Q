"use client";

import { Reveal } from "@/features/landing/hooks/use-reveal";

/** SSS bölümü (refactor R4-1). */
export function FaqSection() {
  return (
  <section id="faq" className="bg-white surface-stone py-20 px-6 scroll-mt-16">
    <div className="max-w-3xl mx-auto">
      <Reveal>
        <p className="mono-label text-muted-text mb-3">Merak edilenler</p>
        <h2 className="display-section text-primary mb-10">Sıkça Sorulan Sorular</h2>
      </Reveal>

      <div className="space-y-0">
        {[
          {
            q: "Clarere nedir?",
            a: "Clarere, kullanıcı fikirlerini, açılış sayfası tasarımlarını ve mesajlarını yapılandırılmış kitle diyaloglarına dönüştürmek için yapay zeka kullanan bir kullanıcı araştırma platformudur. Gerçek dünyadaki demografik özellikleri ve davranışları yansıtan, yapay zeka tarafından oluşturulmuş katılımcılar olan \"sentetik personalar\" kullanarak Clarere, yüksek hız ve düşük maliyetle değerli içgörüler sunar. Bu sayede ekipler, geleneksel katılımcı bulma süreçleriyle ilişkili uzun bekleme süreleri olmadan konseptlerini doğrulayabilirler.",
          },
          {
            q: "Kullanıcı araştırma platformu nedir?",
            a: "Kullanıcı araştırma platformu; ürün ekiplerinin, UX tasarımcılarının ve pazarlamacıların hedef kitlelerinden geri bildirim toplamasına yardımcı olan bir yazılımdır. Bu platformlar genellikle işletmelerin bir ürünü geliştirmeye veya piyasaya sürmeye yatırım yapmadan önce kullanıcı ihtiyaçlarını, temel sorunlarını (pain points) ve davranışlarını anlamalarına yardımcı olmak için görüşmeler, anketler ve kullanılabilirlik testleri gibi etkinlikleri kolaylaştırır.",
          },
          {
            q: "Yapay zeka ile kullanıcı araştırması nasıl çalışır?",
            a: "Clarere gibi modern bir kullanıcı araştırma platformunda, yapay zeka araştırması katılımcı bulma ihtiyacını ortadan kaldırır. Araştırma hedeflerinizi ve hedef kitlenizi tanımlarsınız ve yapay zeka bu profillerle eşleşen sentetik personalar oluşturur. Platform daha sonra bu personalarla yapılandırılmış görüşmeleri simüle eder. Yapay zeka yaklaşık 2 dakika içinde bu konuşmaları eyleme dönüştürülebilir içgörüler halinde sentezleyerek ortak temaları, itirazları ve dil kalıplarını belirler.",
          },
          {
            q: "Clarere, kullanıcı görüşmelerinin yerini alabilir mi?",
            a: "Clarere, tamamen bir alternatif olmaktan ziyade geleneksel kullanıcı görüşmeleriyle birlikte kullanıldığında en iyi sonucu verir. Bir kullanıcı araştırma platformu olarak, haftalar yerine dakikalar içinde yanıtlara ihtiyaç duyduğunuzda, hızlı konsept doğrulama ve erken aşama yönlendirici geri bildirim sağlama konusunda mükemmeldir. Sentetik araştırma, hipotezleri test etmek ve mesajları geniş ölçekte iyileştirmek için harika olsa da, geliştirmenin ilerleyen aşamalarında derin duygusal nüansları ve beklenmedik uç durumları (edge cases) ortaya çıkarmak için canlı insan görüşmeleri altın standart olmaya devam etmektedir.",
          },
          {
            q: "Ne kadar sürede sonuç alabilirim?",
            a: "Katılımcıları bulmanın ve programlamanın 2-3 hafta sürebildiği geleneksel araştırmaların aksine, Clarere genellikle 2 dakikadan daha kısa bir sürede içgörülerin tam bir sentezini sunar. Bu durum, onu yapay zeka destekli bir kullanıcı araştırma platformu kullanarak araştırma yürütmenin en hızlı yollarından biri yapmaktadır.",
          },
          {
            q: "Metodoloji ne kadar güvenilir?",
            a: "Clarere'nin araştırma motoru; kişilik psikolojisi, bilişsel mimari ve kültürel boyut çerçevelerine dayanan çok katmanlı bir yapı üzerinde çalışır. Her bulgu kanıt zinciriyle persone ve soruya bağlanır; panel anti-dalkavukluk ve çeşitlilik denetimlerinden geçer. Bu çıktılar yönlendirici hipotezlerdir; istatistiksel temsil iddiası taşımaz ve yüksek riskli kararlar gerçek kullanıcı verisiyle doğrulanmalıdır.",
          },
          {
            q: "Hangi sektör ve ekipler için uygundur?",
            a: "Strateji ve kreatif ajanslar, B2B SaaS ürün ekipleri, e-ticaret kurucuları, büyüme pazarlamacıları ve konumlandırma / fiyatlandırma / mesajlaşma testlerini hızla çalıştırmak isteyen ürün yöneticileri için tasarlandı.",
          },
          {
            q: "Ücretsiz plan ne kadar süre kullanılabilir?",
            a: "Ücretsiz plan 1 ay boyunca ya da toplam 2 araştırma hakkı bitene kadar — hangisi önce dolarsa o zaman — kullanılabilir; 10 kişilik persona paneli içerir. Kart bilgisi gerekmez.",
          },
        ].map(({ q, a }, i) => (
          <Reveal key={i} delay={i * 40}>
            <details className="group border-b border-hairline py-1">
              <summary className="flex items-start justify-between py-4 cursor-pointer font-medium text-base text-primary hover:text-ink list-none gap-4">
                <span>{q}</span>
                <span className="text-muted-text group-open:rotate-45 transition-transform duration-200 text-xl font-light shrink-0 mt-0.5">+</span>
              </summary>
              <div className="pb-5 text-sm text-body-muted leading-relaxed max-w-2xl">
                {a}
              </div>
            </details>
          </Reveal>
        ))}
      </div>
    </div>
  </section>
  );
}
