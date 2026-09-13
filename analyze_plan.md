# Clarere — Analiz Bulgularını Kapama Planı

> **Kaynak:** `claude_analyse.md` (13 Eylül 2026 — PM + Senior Full-Stack durum analizi)  
> **Amaç:** Analizdeki bulguları sprintlere bölerek, ölçülebilir kabul kriterleriyle kapatmak  
> **Kapsam notu:** Canlı sunucu/deploy, Paddle live, domain, Resend/Sentry ve Enterprise yerel model işleri kullanıcı tarafından **ertelendi**. Bu plan yalnızca ertelenmiş dış-etmen işlerini "bağımlı" olarak işaretler; yerelde kapatılabilen her bulgu plana dahildir.

---

## 0. Kullanım Kılavuzu

### Öncelik kodları

| Kod | Anlam | Zamanlama |
|---|---|---|
| **P0** | Public launch veya hukuki/itibar riski | İlk 2 hafta |
| **P1** | Beta kalitesi, bakım ve ölçüm | 3–8. hafta |
| **P2** | Ürün savunulabilirliği ve kanıt derinliği | 8–16. hafta |
| **P3** | Ertelenmiş / dış bağımlı | Altyapı kararı sonrası |

### Bağımlılık kodları

| Kod | Anlam |
|---|---|
| 🟢 | Yerelde tamamen kapatılabilir |
| 🟡 | Kısmen yerel; final doğrulama gerçek ortam gerektirir |
| 🔴 | Yalnızca canlı sunucu/ödeme/domain sonrası kapatılabilir (ertelenmiş) |

### Sprint yapısı

- Her sprint 1–2 hafta.
- Her sprintin **çıkış kriteri** olmadan bir sonraki sprinte geçilmez.
- Çıktıların tamamı CI'da veya tanımlı bir doğrulama komutuyla kanıtlanır.
- Doküman değişiklikleri de test kadar zorunludur (SSOT kuralı).

---

## 1. Sprint Haritası (Özet)

| Sprint | Süre | Odak | Öncelik | Bağımlılık |
|---|---:|---|---|---|
| **S1** | 1 hafta | Güven, bilimsel iddia ve içerik temizliği | P0 | 🟢 |
| **S2** | 1 hafta | Doküman & fiyat SSOT tutarlılığı | P0 | 🟢 |
| **S3** | 2 hafta | Rapor kalitesi, veri etiketleme ve ölçüm altyapısı | P0/P1 | 🟢/🟡 |
| **S4** | 2 hafta | Frontend mimari sadeleştirme | P1 | 🟢 |
| **S5** | 2 hafta | Backend mimari sadeleştirme | P1 | 🟢 |
| **S6** | 2 hafta | Güvenlik, KVKK ve prod hazırlık (yerel kısımlar) | P0/P1 | 🟢/🟡 |
| **S7** | 1,5 hafta | Test derinliği ve CI determinizmi | P1 | 🟢 |
| **S8** | 3–4 hafta | Bağımsız benchmark ve RFI kalibrasyonu | P2 | 🟡 |
| **S9** | 1 hafta | Rekabet, GTM ve pilot program paketi | P2 | 🟢 |
| **S10** | 1–2 hafta | Launch readiness (ertelenmiş dış işler) | P3 | 🔴 |

S1–S7 tamamen yerelde kapatılabilir. S8 kısmen dış veriye bağlıdır. S9 yereldir. S10 ertelenmiştir.

---

## 2. Bulgu → Sprint İzlenebilirlik Matrisi

| Analiz bölümü / bulgu | Sprint |
|---|---|
| §3.5 Free plan mesaj tutarsızlığı | S3 |
| §3.6 Rapor ürünü metrikleri | S3 |
| §4.1 İyi yapılanlar (korunacak) | Tüm sprintler (regresyon) |
| §4.2 Bilimsel iddia riskleri | S1, S8 |
| §4.2 RFI sınırı | S1, S8 |
| §4.2 Van Westendorp sınırı | S1, S3 |
| §4.3 Metodolojik tutarlılık (stance, panel boyutu) | S2, S3 |
| §5.2 Büyük frontend dosyaları | S4 |
| §5.3 Tasarım sistemi | S4 |
| §5.4 Frontend README boilerplate | S1 |
| §5.5 İçerik kalitesi (yazım, iddia) | S1 |
| §6.2 Backend monolitleri | S5 |
| §6.3 Model/domain tutarlılığı (dict/dataclass) | S5 |
| §6.4 Mock Crawl4AI riski | S1 |
| §6.5 WebSocket bare except | S6 |
| §6.6 Bağımlılık yönetimi | S5, S6 |
| §7.1 Güvenlik güçlü yönleri (korunacak) | S6 (regresyon) |
| §7.2 Açık güvenlik/KVKK riskleri | S1, S6, S10 |
| §8.2 Doküman drift / test sayıları | S2 |
| §8.3 Test kapsamı boşlukları | S7 |
| §8.4 Test komutu gözlemi | S7 |
| §9.2 Production blocker'ları | S10 |
| §9.3 Altyapı planı tutarsızlığı | S2 |
| §10.1 Kritik drift örnekleri | S2 |
| §10.2 Doküman düzeltmeleri | S2 |
| §11 Rekabet analizi derinliği | S9 |
| §12 Birim ekonomi eksikleri | S2, S9 |
| §13 P0 maddeleri | S1, S2, S6, S7 |
| §13 P1 maddeleri | S3, S4, S5, S7 |
| §13 P2 maddeleri | S8 |
| §13 P3 maddeleri | S10 |
| §14 90 günlük plan | Tüm sprintler |
| §15 KPI önerisi | S3, S9 |

---

## 3. S1 — Güven, Bilimsel İddia ve İçerik Temizliği

**Süre:** 1 hafta · **Öncelik:** P0 · **Bağımlılık:** 🟢

### Hedef

Dışa dönük tüm metinlerde doğrulanamayan bilimsel/teknik iddiaları kaldırmak veya kanıt seviyesine göre yeniden yazmak; yazım hatalarını ve yanlış teknik ifadeleri temizlemek; mock verinin rapora sızmasını engellemek.

### İş kalemleri

| ID | İş | Dosya(lar) | Kabul kriteri |
|---|---|---|---|
| S1-1 | Public JSON-LD ve FAQ bilimsel iddialarını gözden geçir | `apps/frontend/src/app/layout.tsx` | Kanıtsız sayısal/kesin iddia kalmadı; doğrulanabilir olanlara kaynak referansı eklendi veya temkinli dile çevrildi |
| S1-2 | “Gerçek kullanıcı olmadan gerçek içgörü” söylemini triage/hipotez diliyle uyumla | `layout.tsx`, `page.tsx`, `SUNUM.md`, `REKABET.md` | Tüm yüzeylerde aynı temkinli konumlandırma |
| S1-3 | “%100 yerel veri lokalizasyonu / KVKK uyumlu” iddiasını düzelt | `upgrade/page.tsx`, `terms/page.tsx`, `privacy/page.tsx` | Aktif mimariye uymayan kesin iddia yok; alt işleyen/veri akışı doğru anlatıldı |
| S1-4 | Yazım hatalarını temizle | `layout.tsx`, tüm `src/app/**/page.tsx` | “yapıy zeka”, “büdçe”, “büyme”, “değlendirmede”, “Clarere'nun” vb. düzeltildi |
| S1-5 | RFI yorum dilini temkinlileştir | `packages/research_engine/benchmark.py` | “Üretime hazır” gibi kesin ifadeler “yüksek referans uyumu” ile değiştirildi |
| S1-6 | Van Westendorp sentetik uyarısını güçlendir | `reporting.py`, `analytics.py`, rapor UI | Her PSM bölümünde “sentetik panel, istatistiksel temsil değildir” notu |
| S1-7 | Mock Crawl4AI içeriğinin production'a girmesini engelle | `search.py` | Production'da mock metin döndürülmez; boş sonuç + degradation note |
| S1-8 | Harici kanıt kaynak metadata standardı | `search.py`, `analytics.py` | URL, başlık, domain, tarih, erişim zamanı kaydedilir |
| S1-9 | Frontend README'yi Clarere'ye özgüle | `apps/frontend/README.md` | Port, env, proxy, test, komut bilgisi doğru; boilerplate kaldırıldı |
| S1-10 | API key rotation durumunu doğrula | `.env` (yerel), operasyon notu | Anahtar döndürülmüş; hiçbir doküman/repo'da secret yok |

### Doğrulama

- `npx tsc --noEmit` + `npx eslint` temiz.
- Metin taraması: yasaklı iddia listesi için grep çalıştırılır ve boş döner.
- Yazım kontrolü: public sayfalar manuel/gözle denetlenir.
- Mock arama testi: `test_web_corroboration.py` mock kapalı senaryoyla genişletilir.

### Çıkış kriteri

Doğrulanamayan bilimsel iddia ve aktif mimariye aykırı veri iddiası sıfır; mock kanıt production yolunda imkânsız; README boilerplate yok.

---

## 4. S2 — Doküman & Fiyat SSOT Tutarlılığı

**Süre:** 1 hafta · **Öncelik:** P0 · **Bağımlılık:** 🟢

### Hedef

Tüm dokümanlarda model adı, timeout, test sayısı, panel boyutu, fiyat para birimi, ödeme sağlayıcı ve altyapı planını tek kaynağa bağlamak.

### İş kalemleri

| ID | İş | Dosya(lar) | Kabul kriteri |
|---|---|---|---|
| S2-1 | Model adlarını güncelle | `README.md`, `models/README.md` | `deepseek-flash` / `deepseek-v4-pro`; effort rolleri doğru |
| S2-2 | Timeout ve limit değerlerini hizala | `README.md` | Kod ile birebir (120 sn vb.) |
| S2-3 | Test sayısını tek SSOT'ye indir | `README.md`, `MEMORY.md` | README güncel doğrulama tablosu; MEMORY tarihsel günlük + tek “Current State” |
| S2-4 | Test sayısını otomatik raporla | `scripts/`, CI | CI çıktısından test sayısı güncellenir veya badge üretilir |
| S2-5 | Fiyatları USD'ye çevir | `SUNUM.md` | TL fiyat kalmadı; UNIT_ECONOMICS ve UI ile aynı |
| S2-6 | Stripe → Paddle düzelt | `SUNUM.md` | Ödeme sağlayıcı tüm yüzeylerde Paddle |
| S2-7 | Panel boyutu tutarlılığı | `README.md`, `MEMORY.md`, `plan_config.py` | 10 persona vaadi tüm yerlerde aynı |
| S2-8 | Altyapı statü matrisi | `server_plan.md`, `README.md` | Aktif/ertelenmiş/alternatif net etiketli |
| S2-9 | Birim ekonomi eksik kalemleri | `UNIT_ECONOMICS.md` | Paddle komisyonu, sabit giderler, bio çağrısı, destek maliyeti |
| S2-10 | API referansı model sütunu | `README.md` | `/synthesize` model satırı gerçeği yansıtır |

### Doğrulama

- Doküman drift kontrol script'i: belirli değerler (model adı, timeout, fiyat) tüm dosyalarda aranır.
- README komutları yerelde çalıştırılır.

### Çıkış kriteri

§10.1 tablosundaki tüm drift satırları kapandı; tek fiyat para birimi; tek ödeme sağlayıcı; tek panel boyutu; tek altyapı statüsü.

---

## 5. S3 — Rapor Kalitesi, Veri Etiketleme ve Ölçüm Altyapısı

**Süre:** 2 hafta · **Öncelik:** P0/P1 · **Bağımlılık:** 🟢/🟡

### Hedef

Raporu yalnız uzun değil, ölçülebilir ve etiketli hale getirmek; Free plan mesajını netleştirmek; ürün KPI event'lerini kurmak.

### İş kalemleri

| ID | İş | Dosya(lar) | Kabul kriteri |
|---|---|---|---|
| S3-1 | Rapor kalite metrikleri | `analytics.py`, `research_findings` | Bulgu başına benzersiz persona, karşı kanıt oranı, tekrar öneri oranı hesaplanır |
| S3-2 | Veri kökeni etiketleme | `reporting.py`, rapor UI | Her bölüm “sentetik / harici / algoritmik” etiketli |
| S3-3 | Kaynaksız iddia kontrolü | `analytics.py` | Harici kanıt gereken bulgular için uyarı |
| S3-4 | Free plan mesaj netliği | `page.tsx`, `upgrade/page.tsx`, `studies/[id]/page.tsx` | “Araştırma hakkı” vs “rapor erişimi” ayrımı tüm yüzeylerde tutarlı |
| S3-5 | KPI event şeması | Backend + frontend telemetri katmanı | Acquisition/Activation/Value/Revenue/Quality event'leri tanımlı ve loglanır |
| S3-6 | Funnel ölçümü | `client.py`, admin | Free limit → upgrade CTA → checkout başlatma oranı izlenir |
| S3-7 | Metodolojik tutarlılık notu | `README.md`, rapor | Stance çeşitliliğinin nüfus temsili olmadığı açıkça yazılır |
| S3-8 | Rapor kabul metrikleri | `MEMORY.md`, admin | Uzman yararlılık işaretleme akışı tanımlı |

### Doğrulama

- Rapor örnek çalışması üzerinden metrik çıktıları doğrulanır.
- KPI event'leri test ortamında tetiklenip kaydedilir.
- Free → paid mesaj tutarlılığı UI denetimiyle doğrulanır.

### Çıkış kriteri

Rapor bölümleri veri kökenine göre etiketli; Free/paid mesajı çelişkisiz; temel KPI'lar ölçülebilir.

---

## 6. S4 — Frontend Mimari Sadeleştirme

**Süre:** 2 hafta · **Öncelik:** P1 · **Bağımlılık:** 🟢

### Hedef

Aşırı büyük frontend dosyalarını feature bazlı, test edilebilir parçalara ayırmak; davranışı değiştirmeden bakım maliyetini düşürmek.

### İş kalemleri

| ID | İş | Hedef yapı | Kabul kriteri |
|---|---|---|---|
| S4-1 | Study detayını parçala (2309 satır) | `features/studies/components/*` + `hooks/use-study-detail.ts` | Ana davranış ve görünüm aynı; dosya başına < ~400 satır |
| S4-2 | Sekmeleri bağımsız bileşen yap | `SummaryTab`, `PersonaPanel`, `ScriptTab`, `InterviewsTab`, `EvidenceTab`, `ReportTab` | Her sekme ayrı dosyada |
| S4-3 | Transkript dialogunu ayır | `InterviewTranscriptDialog.tsx` | Dialog izole ve test edilebilir |
| S4-4 | Veri normalizasyonu ayır | `lib/study-normalizers.ts` | UI içindeki toleranslı alan okuma/kaydetme UI'dan çıkarıldı |
| S4-5 | Admin panelini parçala (1470 satır) | `features/admin/*` | Modül başına < ~400 satır |
| S4-6 | Landing fiyatlandırmayı ayır | `features/pricing/*` | Fiyat kartları tek bileşen, veri tek kaynak |
| S4-7 | Tasarım token drift'ini birleştir | `globals.css`, token dosyası | `DESIGN.md` ile uyumlu tek token kaynağı |
| S4-8 | Kart yoğunluğunu azalt | Study/admin ekranları | DESIGN “her şey kart olmasın” kuralına uyum |

### Doğrulama

- `npx tsc --noEmit` + `npx eslint` temiz.
- Playwright `03-study-actions` geçer.
- Görsel regresyon: sekmeler ve rapor ekran görüntüleri karşılaştırılır.
- Satır sayısı kontrolü.

### Çıkış kriteri

Kritik frontend dosyaları modüler; davranış ve görünüm değişmedi; CI yeşil.

---

## 7. S5 — Backend Mimari Sadeleştirme

**Süre:** 2 hafta · **Öncelik:** P1 · **Bağımlılık:** 🟢

### Hedef

Monolitik backend modüllerini sorumluluk bazında ayırmak; API/domain/persistence sınırını netleştirmek; bağımlılıkları sadeleştirmek.

### İş kalemleri

| ID | İş | Hedef yapı | Kabul kriteri |
|---|---|---|---|
| S5-1 | DB katmanını böl (1954 satır) | `database/{clients,studies,usage,migrations,connection}.py` | Tüm import'lar güncel; testler yeşil |
| S5-2 | Client router'ı böl (1917 satır) | `routers/{intake,research,studies,privacy,billing,billing_webhook}.py` | Endpoint sözleşmeleri değişmedi |
| S5-3 | Analytics'i böl (1534 satır) | `analytics/{findings,pricing,quality,report_enrichment}.py` | Rapor çıktısı bit birebir aynı |
| S5-4 | Workflow'u böl (1355 satır) | `workflow/{personas,interviews,prompts,planning}.py` | Araştırma akışı aynı sonucu üretir |
| S5-5 | DTO/mapper katmanı | `mappers/*` | dict/dataclass dönüşümleri tek yerde |
| S5-6 | Tolerant alan okumayı standartlaştır | `mappers`, `models.py` | `_g()` benzeri geçici çözümler azaltıldı |
| S5-7 | Kullanılmayan analytics bağımlılıklarını ayıkla | `requirements.txt` | Kullanılmayan paket yok veya opsiyonel gruba taşındı |
| S5-8 | crawl4ai opsiyonel bağımlılık | `requirements*.txt` | Ayrı optional grubu veya resmi devre dışı |

### Doğrulama

- Tam pytest süiti yeşil.
- Public API sözleşmeleri (OpenAPI) diff'i.
- Rapor üretimi örnek çalışmayla karşılaştırılır.

### Çıkış kriteri

Ana modüller < ~600 satır; testler yeşil; öffentliche API değişmedi; bağımlılıklar sadeleşti.

---

## 8. S6 — Güvenlik, KVKK ve Prod Hazırlığı (Yerel Kısımlar)

**Süre:** 2 hafta · **Öncelik:** P0/P1 · **Bağımlılık:** 🟢/🟡

### Hedef

Canlıya bağımlı olmayan güvenlik ve uyum işlerini kapatmak; prod konfigürasyonunu test edilebilir hale getirmek.

### İş kalemleri

| ID | İş | Dosya(lar) | Kabul kriteri |
|---|---|---|---|
| S6-1 | Bare `except: pass` temizliği | `client.py` WebSocket | Yalnız beklenen istisnalar yakalanır, diğerleri loglanır |
| S6-2 | Production config guard testleri | `jwt_utils.py`, `main.py`, `admin.py` | Eksik secret/CORS ile uygulama açılmaz; test edildi |
| S6-3 | RLS gerçek DB testi | `tests/test_rls_org_sharing.py` | Tenant/org izolasyonu DB'de doğrulandı |
| S6-4 | Rate limit dağıtık uyumu | `main.py`, Redis | Redis-backed limit doğrulandı |
| S6-5 | PII maskeleme kapsamı gözden geçir | `privacy.py` | Enterprise NER gate ve regex fallback test edildi |
| S6-6 | KVKK veri akışı dokümanı | `privacy/page.tsx`, doküman | Hangi veri nereye gidiyor, saklama, alt işleyen |
| S6-7 | Hukuki metin inceleme notu | `terms/page.tsx` | Fikri mülkiyet/gizlilik ifadeleri hukuk incelemesine işaretli |
| S6-8 | Secret hijyen kontrolü | tüm doküman/repo | Hardcoded secret yok (secret scanning) |
| S6-9 | Dependency audit | CI | pip-audit + npm audit temiz |

### Doğrulama

- Güvenlik testleri + secret scanning.
- Prod benzeri env ile lokal başlatma testi.
- `pip-audit` ve `npm audit` çıktıları temiz.

### Çıkış kriteri

Yerel olarak doğrulanabilen güvenlik ve uyum işleri kapandı; kalan maddeler S10'a devredildi.

---

## 9. S7 — Test Derinliği ve CI Determinizmi

**Süre:** 1,5 hafta · **Öncelik:** P1 · **Bağımlılık:** 🟢

### Hedef

Test kapsamındaki boşlukları kapatmak ve test/doğrulama komutlarını tek, deterministik akışa indirmek.

### İş kalemleri

| ID | İş | Kabul kriteri |
|---|---|---|
| S7-1 | Tek test komutu standardı | `make test` veya eşdeğer; DB-forward otomatik |
| S7-2 | PDF golden/snapshot testi | PDF içeriği regresyona karşı korunur |
| S7-3 | Mobile görsel regresyon | Study/rapor 375px ve 768px kontrol edilir |
| S7-4 | Celery retry/idempotency testi | Aynı job tekrar çalıştırıldığında tutarlı |
| S7-5 | Concurrency/load testi | N eşzamanlı araştırma stabil |
| S7-6 | LLM cache regresyon testi | Cache-hit/cache-miss davranışı doğru |
| S7-7 | Model drift testi | Aynı brief sabit çıktı yapısı üretir |
| S7-8 | E2E secret gate dokümantasyonu | E2E tetikleme adımları net |

### Doğrulama

- Tam süit + E2E + yeni testler yeşil.
- Test süresi ölçülür ve belgelenir.

### Çıkış kriteri

Testler tek komutla ve deterministik çalışır; kritik UI/PDF/queue akışları regresyona karşı korunur.

---

## 10. S8 — Bağımsız Benchmark ve RFI Kalibrasyonu

**Süre:** 3–4 hafta · **Öncelik:** P2 · **Bağımlılık:** 🟡

### Hedef

Bilimsel iddiaları bağımsız, tekrarlanabilir kanıtla desteklemek; RFI'yı gerçek veriyle kalibre etmek.

### İş kalemleri

| ID | İş | Kabul kriteri |
|---|---|---|
| S8-1 | 20 gerçek brief + uzman referans | Karşılaştırmalı veri seti oluşturuldu |
| S8-2 | Kör tema eşleme protokolü | İki bağımsız değerlendirici, önceden kayıtlı kriter |
| S8-3 | RFI eşik kalibrasyonu | Eşikler ampirik veriyle güncellendi |
| S8-4 | Semantic benzerlik iyileştirmesi | Karakter/Jaccard yerine veya yanında daha güçlü yöntem değerlendirildi |
| S8-5 | Sentetik → gerçek doğrulama oranı | Ölçülür ve raporlanır |
| S8-6 | Persona tekrar üretilebilirliği | Aynı ayarlarla panel tutarlılığı ölçülür |
| S8-7 | Benchmark public özet | Kanıt seviyesine uygun, temkinli bir özet yayımlanabilir |

### Doğrulama

- Benchmark tekrarlanabilir script ile çalışır.
- Sonuçlar sürüm bazlı saklanır.

### Çıkış kriteri

RFI ve kalite iddiaları bağımsız veriyle desteklenir; iddialar kanıt seviyesiyle uyumludur.

---

## 11. S9 — Rekabet, GTM ve Pilot Program Paketi

**Süre:** 1 hafta · **Öncelik:** P2 · **Bağımlılık:** 🟢

### Hedef

Satış ve pilot programı için doğrulanabilir rekabet analizi, fiyat doğrulama planı ve ölçüm paketi hazırlamak.

### İş kalemleri

| ID | İş | Kabul kriteri |
|---|---|---|
| S9-1 | Derin rekabet matrisi | Kategori + boyut bazlı, kaynaklı |
| S9-2 | Fiyat doğrulama planı | Görüşme soruları + willingness-to-pay testi |
| S9-3 | Pilot program kiti | Kapsam, süre, ölçüm, sorumluluk |
| S9-4 | Yatırımcı deck düzeltmesi | USD, Paddle, gerçekçi iddialar |
| S9-5 | KPI dashboard tanımı | Edinim→değer→gelir→kalite zinciri |
| S9-6 | Free → paid funnel deneyi tasarımı | Hipotez + ölçüm + süre |

### Doğrulama

- Rekabet iddiaları kaynaklı.
- Fiyatçılama planı ölçülebilir.

### Çıkış kriteri

Satış ekibi/pilot programı doğrulanabilir materyalle çalışabilir.

---

## 12. S10 — Launch Readiness (Ertelenmiş Dış İşler)

**Süre:** 1–2 hafta · **Öncelik:** P3 · **Bağımlılık:** 🔴

> Bu sprint **canlı sunucu/domain/ödeme kararı verilmeden başlatılamaz**. Kullanıcı kararı beklenmektedir; plana yalnızca izlenebilirlik için dahil edilmiştir.

### İş kalemleri

| ID | İş | Kabul kriteri |
|---|---|---|
| S10-1 | Deploy (VPS/Neon/Vercel veya onaylı mimari) | Sağlık endpoint'i yeşil |
| S10-2 | Domain + TLS | HTTPS ve kanonik yönlendirme çalışır |
| S10-3 | Production JWT/CORS/secrets | Prod env ile uygulama açılır |
| S10-4 | Paddle live catalog + webhook | Gerçek ödeme lifecycle testi |
| S10-5 | Backup cron + restore tatbikatı | Geri yükleme doğrulandı |
| S10-6 | Sentry + Resend | Gerçek hata ve e-posta teslimi |
| S10-7 | Load/uptime testi | Kapasite ve izleme doğrulandı |
| S10-8 | Incident playbook + SLA | Süreç belgeli |

### Çıkış kriteri

Sistem canlıda doğrulandı; operasyon ve geri dönüş süreçleri hazır.

---

## 13. Koruma Altına Alınacak Güçlü Yönler (Regresyon Kuralı)

Aşağıdakiler hiçbir sprintte bozulmamalıdır:

- Hipotez-kör mülakat davranışı
- Skeptic zorunluluğu ve stance diversity
- ELEPHANT anti-sycophancy promptu
- Big Five / NEO-PI-R atamalarının bütünlüğü
- SES × Rogers kotası
- Kanıt zinciri ve karar katmanı
- Echo ve acquiescence kontrolleri
- Persona izolasyonu
- Atomik kota ve plan gate'leri
- Prompt prefix-cache sırası
- Rol bazlı reasoning effort
- PII maskeleme ve KVKK export/delete
- RLS tenant/org izolasyonu

Her sprint sonunda bu liste için regresyon testleri yeşil olmalıdır.

---

## 14. Sprint Çıkış Kapısı (Definition of Done)

Bir sprint yalnızca aşağıdakilerin tümü sağlandığında kapanır:

1. İş kalemlerinin kabul kriterleri karşılandı.
2. `npx tsc --noEmit` ve `npx eslint` temiz.
3. Backend test süiti yeşil (ilgili sprint testleri dahil).
4. CI yeşil.
5. Yeni/değişen davranış için test eklendi.
6. İlgili dokümanlar güncellendi (SSOT kuralı).
7. `MEMORY.md` güncellendi.
8. Regresyon listesi (§13) bozulmadı.
9. Değişiklikler commit'lendi ve push edildi.

---

## 15. Riskler ve Azaltma

| Risk | Etki | Azaltma |
|---|---|---|
| Refaktör sırasında davranış kaybı | Yüksek | Sprint öncesi snapshot testleri + örnek çalışma karşılaştırması |
| Bilimsel iddia temizliğinde aşırı silme | Orta | İddialar kanıtlanırsa geri eklenir; kaynak referansı koşulu |
| Celery worker eski kod çalıştırma | Yüksek | Her backend değişikliğinde api + worker birlikte rebuild |
| Frontend rebuild gereksinimi | Orta | Her UI değişikliğinde imaj yeniden derlenir |
| E2E maliyeti | Orta | Manuel/haftalık gate; hazırlık testleri fake model |
| Benchmark dış veriye bağımlı | Orta | Uzman erişimi paralel planlanır |
| Sprint kapsam kayması | Orta | Kabul kriteri dışı iş bir sonraki sprint'e |

---

## 16. Ölçüm ve Raporlama

Her sprint sonunda güncellenecek metrikler:

- Açılan/kapanan bulgu sayısı (bu planın ID'leri)
- Test sayısı ve süresi
- CI durumu
- Ortalama dosya boyutu (refaktör sprintlerinde)
- Rapor kalite metrikleri (S3+)
- Benchmark ve RFI değerleri (S8+)
- Free → paid funnel (S3+)

---

## 17. Başlangıç Sırası

1. **S1 → S2** (P0 güven ve tutarlılık; hızlı ve yüksek etkili)
2. **S3 → S6** (ölçüm, refaktör ve güvenlik; paralel yürütülebilir kısımlar var)
3. **S7 → S9** (test derinliği, kanıt ve GTM)
4. **S8** bağımsız uzman verisi toplanırken paralel ilerleyebilir
5. **S10** yalnızca kullanıcı altyapı kararı sonrası

---

## 18. Ertelenen / Kapsam Dışı

- Enterprise yerel Türkçe LLM ve fine-tuning
- Embedding/persona vektör havuzu
- Yerel NER altyapısı
- Canlı sunucu, domain, Paddle live, Resend, Sentry
- Siyasi araştırma dikeyi

Bu maddeler kullanıcı açıkça istemedikçe plana dahil edilmez.
