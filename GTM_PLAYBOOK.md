# Clarere — GTM Playbook (Pilot, Fiyat Doğrulama, Funnel)

> **Kapsam:** Sprint 9 çıktısı. Pilot program kiti, fiyat doğrulama planı, Free→paid funnel deneyi ve KPI dashboard tanımı.
> **İlke:** Uydurma hedef/rakam yoktur. Ölçüm, gerçek kullanıcı davranışıyla doğrulanır.

---

## 1. Pilot Program Kiti

### Amaç

Ürünün gerçek brief'lerle değer üretip üretmediğini, hangi noktada takıldığını ve ödeme isteğini ölçmek.

### Kapsam

| Alan | Karar |
|---|---|
| Katılımcı | 5–10 tasarım partneri (ajans, B2B SaaS ürün ekibi, danışman) |
| Süre | 4 hafta |
| Brief | Partner başına 3 gerçek araştırma brief'i |
| Plan | Pilot boyunca Starter seviyesi erişim (ücretsiz) |
| Beklenti | Partnerler çıktıyı gerçek bir karar sürecinde kullanır |

### Partner'den istenenler

1. Gerçek (yakında karar verilecek) brief'ler.
2. Her rapor sonrası 10 dakikalık geri bildirim görüşmesi.
3. Raporu kendi iş akışında kullanıp kullanmadığının kaydı.
4. En az bir bulguyu gerçek kullanıcı/satış verisiyle doğrulama.

### Başarı kriterleri (çıkış kapısı)

| Metrik | Hedef |
|---|---|
| Brief → tamamlanan araştırma | ≥ %90 |
| Rapor sonrası "yararlı" işareti | ≥ %70 |
| Gerçek kararda kullanım | ≥ %50 partner |
| Gerçek veriyle doğrulanan bulgu | ≥ 1 / partner |
| Ödemeye istek (anahtar kelime testi) | ≥ %40 partner |

### Çıktılar

- Yanıt/karşı-kanıt istatistikleri (`report_metrics`).
- KPI funnel (`/api/admin/product-events/summary`).
- Partner geri bildirim özeti (feedbacks).

---

## 2. Fiyat Doğrulama Planı

### Neden

`UNIT_ECONOMICS.md` LLM COGS'un bağlayıcı olmadığını gösteriyor. Asıl soru **ödeme isteği**dir. Fiyat, maliyetten değil değerden türetilmeli.

### Yöntem (görüşme tabanlı, Van Westendorp uyarlaması)

Her partnerle, bir raporu inceledikten **sonra**:

1. "Bu raporu bugün hiç yapamadığınız bir iş için kullandınız mı?"
2. "Bu çıktıyı üretmek için normalde ne kadar zaman/bütçe harcarız?"
3. **4 fiyat sorusu:**
   - Hangi fiyattan sonra "çok pahalı, almam"?
   - Hangi fiyattan sonra "pahalı ama düşünürüm"?
   - Hangi fiyat "makul/işlek"?
   - Hangi fiyat "çok ucuz, kalitesiz görünür"?
4. "Yıllık ödemede %20 indirim anlamlı mı?"
5. "Hangi özellik eksikse bu fiyatı ödemezsiniz?"

### Mevcut fiyat çerçevesi (doğrulanacak)

| Plan | Fiyat | Model |
|---|---|---|
| Free | $0 | 2 araştırma veya 1 ay |
| Flex | $49 | Tek seferlik, 3 araştırma |
| Starter | $69/ay ($55/ay yıllık) | 10 araştırma/ay |
| Pro | $169/ay ($135/ay yıllık) | Sınırsız (fair-use) |
| Enterprise | Özel | Kurumsal |

### Karar kuralı

- Medyan OPP, mevcut fiyatın ±%30 bandındaysa → fiyat korunur.
- OPP belirgin yüksekse → Starter/Pro kademesi yukarı çekilir.
- Flex ile Starter arasında anlamlı değer farkı görülmezse → Flex kaldırılır veya yeniden konumlanır.

---

## 3. Free → Paid Funnel Deneyi

### Funnel aşamaları (ölçülen event'ler)

```
wizard_started            → Araştırma sihirbazı başlatıldı
research_started          → Araştırma çalıştırıldı
research_completed        → Araştırma tamamlandı
study_detail_viewed       → Çalışma incelendi
report_tab_viewed         → Rapor sekmesi açıldı
paywall_viewed            → Paywall görüldü (ücretsiz plan)
upgrade_cta_viewed        → Yükseltme sayfası görüldü
upgrade_cta_clicked       → Yükseltme CTA tıklandı
report_synthesized        → Rapor üretildi
pdf_export_clicked        → PDF istendi
```

### Hipotezler

| # | Hipotez | Ölçüm | Süre |
|---|---|---|---|
| H1 | Buzlu rapor önizlemesi, "yaklaştı" hissiyle upgrade oranını artırır | `paywall_viewed → upgrade_cta_clicked` | 2 hafta |
| H2 | "2 araştırma hakkı veya 1 ay" mesajı, "ilk 2 ücretsiz"den daha çok dönüştürür | A/B metin, `upgrade_cta_clicked` | 2 hafta |
| H3 | Kısmi (blurlu) rapor + net CTA, tam blok'tan daha iyi | `report_tab_viewed → upgrade_cta_clicked` | 2 hafta |
| H4 | İlk tamamlanan araştırmadan sonra gösterilen CTA daha etkili | `research_completed` sonrası dönüşüm | 2 hafta |

### Ölçüm notu

- Oranlar küçük örneklemde gürültülüdür; yorumda **mutlak sayılar** da raporlanır.
- Backend event'leri `product_events` tablosundadır; istemci event'leri beyaz liste ile sınırlıdır.

---

## 4. KPI Dashboard Tanımı

### Edinim (Acquisition)

- Landing → `wizard_started`
- SEO landing → kayıt
- Kanal bazında (kaynak UTM) başlangıç

### Aktivasyon (Activation)

- `wizard_started` → `research_completed` (tamamlama oranı)
- İlk brief tamamlama süresi
- İlk rapor görüntüleme oranı

### Değer (Value)

- `report_tab_viewed` → `pdf_export_clicked`
- Kanıt genişletme oranı
- Follow-up / copilot kullanımı
- Kabul edilen öneri sayısı (feedback)

### Gelir (Revenue)

- `upgrade_cta_viewed` → `upgrade_cta_clicked` → checkout → ödeme
- Plan bazında ARPA
- Refund / churn

### Araştırma Kalitesi (Quality)

- Bulgu başına kanıt (`evidence_per_finding`)
- Kaynaksız bulgu sayısı
- Karşı kanıt oranı (`refuting_ratio`)
- Yanıt tamamlanma oranı (`answer_completion_rate`)
- Degradasyon notu oranı
- Harici kanıt kaynağı sayısı

> Kaynak: `report_metrics` (rapor bazlı) + `product_events` (davranış) + `feedbacks` (kabul).

---

## 5. Yatırımcı Deck Tutarlılığı

`SUNUM.md` Sprint 2'de USD/Paddle ile hizalandı. Deck yayımlanmadan önce kontrol listesi:

- [ ] Tüm fiyatlar USD ve güncel plan tablosuyla uyumlu
- [ ] Ödeme sağlayıcı = Paddle (Stripe değil)
- [ ] Kanıtsız bilimsel/istatistiksel iddia yok
- [ ] "Gerçek kullanıcı yerine geçer" iddiası yerine "hipotez/triage" konumlandırması
- [ ] Birim ekonomi tablosu `UNIT_ECONOMICS.md` ile tutarlı
- [ ] Yol haritası gerçekçi (canlıya geçiş ertelendi)

---

## 6. Sıradaki Adımlar

1. 5–10 tasarım partneri seç (S10 / canlı sonrası).
2. Pilot kitini uygula; 4 hafta ölç.
3. Fiyat görüşmelerini yap; medyan OPP'ye göre karar ver.
4. Funnel hipotezlerini A/B ile test et.
5. `REKABET.md` doğrulama görev listesini tamamla; ancak ondan sonra karşılaştırma iddiası yayımla.
