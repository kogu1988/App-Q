# Clarere — S4 + S5 Refaktör Planı (Sprintlere Bölünmüş)

> **Kaynak:** `analyze_plan.md` §6 (S4 — Frontend mimari sadeleştirme) ve §7 (S5 — Backend mimari sadeleştirme)
> **Amaç:** Aşırı büyük modülleri, **davranışı değiştirmeden** test edilebilir parçalara ayırmak.
> **Kural:** Bu plan **yalnızca refaktördür.** Yeni özellik, yeni davranış veya metin değişikliği içermez. Her sprint sonunda sistem, öncekinden ayırt edilemez davranmalıdır.

---

## 0. Genel İlkeler

| İlke | Açıklama |
|---|---|
| **Davranış dondurma (behavior freeze)** | Public API sözleşmeleri, rapor çıktısı ve UI davranışı değişmez. |
| **Strangler + shim** | Eski modül, yeni parçaları **re-export eden bir ince katman** olarak kalır. Böylece yüzlerce import yeri tek seferde kırılmaz. |
| **Küçük, geri alınabilir adımlar** | Her sprint tek başına commit edilebilir ve geri alınabilir. |
| **Kanıt zorunlu** | Her sprint: testler yeşil + typecheck/lint temiz + (varsa) golden karşılaştırma. |
| **Özellik karıştırma yok** | Bir hata bulunursa ayrı bir düzeltme commit'i olarak işaretlenir; refaktöre karıştırılmaz. |
| **Satır hedefi** | Hedef: modül başına **< ~500 satır**; tek sorumluluk. |
| **Döngü yasağı** | Yeni paketler arasında import döngüsü olmamalı (`test_architecture.py` genişletilir). |

### Doğrulama demirbaşı (her sprintte aynı)

1. `python scripts/run_tests.py` → tüm süit yeşil.
2. `cd apps/frontend && npx tsc --noEmit && npx eslint` → temiz.
3. **Rapor golden karşılaştırması:** Bilinen bir çalışmanın `report_markdown` çıktısı öncesi/sonrası normalize edilerek birebir aynı olmalı.
4. **OpenAPI diff:** `/openapi.json` şeması değişmemeli (R6 için).
5. **E2E:** `e2e/tests/03-study-actions.spec.ts` geçmeli (Docker stack açıkken).

---

## 1. Sprint Haritası

| Sprint | Alan | Konu | Bağımlılık | Tahmin |
|---|---|---|---|---|
| **R1** | Frontend | Study detay — veri katmanı ayrımı | — | 3–4 gün |
| **R2** | Frontend | Study detay — sekme bileşenleri | R1 | 5–7 gün |
| **R3** | Frontend | Admin panel ayrımı | — | 4–5 gün |
| **R4** | Frontend | Landing/wizard/fiyat + tasarım tokenları | — | 4–5 gün |
| **R5** | Backend | `database.py` → paket | — | 4–5 gün |
| **R6** | Backend | `routers/client.py` → alt router'lar | R5 | 5–6 gün |
| **R7** | Backend | `analytics.py` → paket (+ reporting) | R5 | 5–6 gün |
| **R8** | Backend | `workflow.py` → paket + mapper/DTO + bağımlılık | R5, R7 | 5–7 gün |

Frontend (R1–R4) ve backend (R5–R8) blokları **birbirinden bağımsızdır**; kapasite varsa paralel yürütülebilir. Tek kişiyle **sıralı** ilerlenmesi önerilir: R1 → R2 → R5 → R6 → R7 → R8 → R3 → R4.

### Mevcut → Hedef satır sayıları

| Dosya | Şimdi | Hedef (en büyük parça) |
|---|---:|---:|
| `client/studies/[id]/page.tsx` | 2364 | < 350 |
| `admin/page.tsx` | 1470 | < 300 |
| `app/page.tsx` | 869 | < 350 |
| `client/new/page.tsx` | 620 | < 400 |
| `routers/client.py` | 1976 | < 350 |
| `routers/admin.py` | 612 | < 300 |
| `database.py` | 2034 | < 250 (shim) |
| `analytics.py` | 1585 | < 250 (shim) |
| `workflow.py` | 1392 | < 250 (shim) |
| `reporting.py` | 911 | < 400 |

---

## 2. Shıм (Shim) Stratejisi — Neden Kritik

Örnek: `packages/research_engine/database.py` yüzlerce yerde `from ...database import X` olarak kullanılıyor.

**Yaklaşım:**
1. `database.py` → `database/` paketine dönüştürülür.
2. Alt modüller: `connection.py`, `migrations.py`, `clients.py`, `studies.py`, `usage.py`, `events.py`, `personas.py`.
3. `database/__init__.py` **tüm eski isimleri re-export eder**:
   ```python
   from .connection import get_db, get_admin_db  # noqa: F401
   from .migrations import init_db                # noqa: F401
   # ...
   ```
4. Böylece hiçbir çağrı yeri değişmez; import yolları çalışmaya devam eder.
5. Taşıma tamamlandıktan sonra (opsiyonel, ayrı sprint) çağrı yerleri doğrudan alt modüle yönlendirilebilir.

Aynı desen `analytics/`, `workflow/` ve frontend'de `features/*` için uygulanır.

---

## 3. R1 — Study Detay: Veri Katmanı Ayrımı (Frontend)

**Hedef:** `studies/[id]/page.tsx` içindeki veri çekme, normalizasyon ve olay (event) mantığını UI'dan ayırmak. **Görsel değişiklik yok.**

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R1-1 | Çalışma detay verisi hook'u | `src/features/studies/hooks/use-study-detail.ts` |
| R1-2 | Tolerant veri normalizasyonu (dict/dataclass uyumu) | `src/features/studies/lib/normalize-study.ts` |
| R1-3 | Sentez/follow-up/copilot API çağrıları | `src/features/studies/api/studies-api.ts` |
| R1-4 | Funnel event çağrıları | mevcut `src/lib/events.ts` kullanımı hook içine taşınır |
| R1-5 | TypeScript tipleri | `src/features/studies/types.ts` (`StudyDetail`, `Persona`, `InterviewTurn` vb.) |

### Kabul kriterleri
- `page.tsx` yalnızca düzen (layout) + sekme yönlendirme içerir; `fetch` çağrısı kalmaz.
- `npx tsc --noEmit` + `eslint` temiz; görsel çıktı birebir aynı (Playwright ekran görüntüsü gözle karşılaştırılır).
- `page.tsx` satır sayısı **< 1800**.

### Risk / geri alma
Risk düşük. Geri alma: commit revert.

---

## 4. R2 — Study Detay: Sekme Bileşenleri (Frontend)

**Hedef:** 6 sekmeyi ve yardımcı görselleri bağımsız bileşenlere ayırmak.

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R2-1 | Özet & Hedefler sekmesi | `components/SummaryTab.tsx` |
| R2-2 | Personalar sekmesi (+ Big Five radar, SES×Stance tablosu) | `components/PersonasTab.tsx` |
| R2-3 | Senaryo sekmesi | `components/ScriptTab.tsx` |
| R2-4 | Mülakat kayıtları + transkript dialogu | `components/InterviewsTab.tsx`, `components/InterviewTranscriptDialog.tsx` |
| R2-5 | Kanıt zinciri sekmesi (+ FindingCard, DecisionCard) | `components/EvidenceTab.tsx`, `components/FindingCard.tsx` |
| R2-6 | Sentez raporu sekmesi (+ PSMChart, BrandHealth, ChannelBar, metrics) | `components/ReportTab.tsx`, `components/PSMChart.tsx`, `components/ReportMetricsCard.tsx` |
| R2-7 | Ortak biçimlendirme yardımcıları | `lib/format.ts` |
| R2-8 | Markdown renderer | `lib/render-markdown.tsx` |

### Kabul kriterleri
- `page.tsx` **< 350 satır**; her sekme dosyası **< 600 satır**.
- Tüm sekmeler dolu/çalışır (E2E `03-study-actions` geçer).
- Transkript dialogu, paywall, plan gate davranışı değişmez.

### Risk / geri alma
Orta risk (görsel regresyon). Geri alma: baz alınan ekran görüntüleriyle karşılaştırma; gerekirse ilgili sekme bileşenini tek başına revert.

---

## 5. R3 — Admin Panel Ayrımı (Frontend)

**Hedef:** `admin/page.tsx` (1470) içeriğini feature bileşenlerine bölmek.

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R3-1 | Admin veri hook'u + admin API istemcisi | `features/admin/hooks/use-admin.ts`, `features/admin/api/admin-api.ts` |
| R3-2 | Müşteri yönetimi sekmesi | `features/admin/components/ClientsTab.tsx` |
| R3-3 | Kullanım/maliyet sekmesi | `features/admin/components/UsageTab.tsx` |
| R3-4 | Persona havuzu sekmesi | `features/admin/components/PersonasTab.tsx` |
| R3-5 | Geri bildirim + audit log sekmesi | `features/admin/components/FeedbackTab.tsx` |
| R3-6 | Sistem konfigürasyonu sekmesi | `features/admin/components/ConfigTab.tsx` |
| R3-7 | Ürün event / funnel özeti | `features/admin/components/EventsTab.tsx` (`GET /product-events/summary`) |

### Kabul kriterleri
- `admin/page.tsx` **< 300 satır**.
- Admin auth (`X-Admin-Key`) davranışı değişmez; sekme geçişleri çalışır.
- Admin sayfası landing'den erişilemez durumda kalır.

### Risk / geri alma
Düşük-orta. Geri alma: commit revert.

---

## 6. R4 — Landing / Wizard / Fiyat + Tasarım Tokenları (Frontend)

**Hedef:** `page.tsx` (869) ve `client/new/page.tsx` (620) ayrımı + `DESIGN.md` ile token uyumu.

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R4-1 | Landing bölümleri | `features/landing/components/*` (hero, manifesto, use-case, SSS, iletişim) |
| R4-2 | Fiyatlandırma kartları + plan verisi (tek SSOT) | `features/pricing/plans.ts`, `features/pricing/PricingSection.tsx` |
| R4-3 | Wizard adım bileşenleri | `features/wizard/components/*` (Defne sohbeti, brief önizleme) |
| R4-4 | Tasarım tokenları (renk/radius/spacing) tek kaynak | `src/styles/tokens.css` + `DESIGN.md` uyumu |
| R4-5 | Kart yoğunluğunu azaltma (DESIGN “her şey kart olmasın” kuralı) | ilgili bölümler (görsel revizyon ayrı commit) |

> **Not:** R4-5 görsel bir iyileştirmedir; davranış dondurma kuralı gereği **ayrı commit** olarak yapılır ve metin/içerik değiştirmez.

### Kabul kriterleri
- `page.tsx` **< 350 satır**, `client/new/page.tsx` **< 400 satır**.
- Fiyat bilgisi tek dosyadan gelir (UI ile `plan_config`/`UNIT_ECONOMICS` tutarlı).
- Landing/wizard akışı E2E `02-research-flow` ile bozulmadan çalışır.

---

## 7. R5 — `database.py` → Paket (Backend)

**Hedef:** 2034 satırlık modülü sorumluluk bazında ayırmak; **import yolları değişmez.**

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R5-1 | Bağlantı havuzu + oturum yönetimi | `database/connection.py` |
| R5-2 | `init_db`, migration'lar, RLS/app-role | `database/migrations.py` |
| R5-3 | İstemci CRUD + plan/kota | `database/clients.py` |
| R5-4 | Çalışma (studies) CRUD | `database/studies.py` |
| R5-5 | Token kullanımı + maliyet | `database/usage.py` |
| R5-6 | Ürün event'leri (KPI) | `database/events.py` |
| R5-7 | Persona havuzu CRUD | `database/personas.py` |
| R5-8 | Re-export shim | `database/__init__.py` |

### Kabul kriterleri
- `database/` altındaki her dosya **< 500 satır**; `__init__.py` **< 250 satır**.
- Hiçbir çağrı yeri değişmedi (grep ile doğrula).
- `test_migrations.py`, `test_quota_atomicity.py`, `test_rls_*`, `test_product_events.py` yeşil.
- Import döngüsü yok.

### Risk / geri alma
Orta (DB kritik yol). Geri alma: `database.py`'ı geri getir, paketi kaldır (tek commit).

---

## 8. R6 — `routers/client.py` → Alt Router'lar (Backend)

**Hedef:** 1976 satırlık router'ı endpoint ailelerine ayırmak. **OpenAPI şeması değişmez.**

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R6-1 | Intake (Defne) | `routers/client/intake.py` |
| R6-2 | Research (senkron + job) | `routers/client/research.py` |
| R6-3 | Studies (liste/detay/findings/pdf/kaydet) | `routers/client/studies.py` |
| R6-4 | Follow-up + copilot + chat | `routers/client/interaction.py` |
| R6-5 | Privacy (export/delete) + feedback + events + contact | `routers/client/account.py` |
| R6-6 | Ortak bağımlılıklar (plan çözümü, quota, admin vb.) | `routers/client/deps.py` |
| R6-7 | Üst router birleştirme | `routers/client/__init__.py` |

### Kabul kriterleri
- Her alt router **< 400 satır**.
- `GET /openapi.json` diff'i **boş** (path/metot/şema aynı).
- Plan gate, kota, PII maskeleme davranışı değişmez.
- `test_plan_enforcement.py`, `test_blockers_p0.py` yeşil.

### Risk / geri alma
Yüksek (kritik API yolu). Geri alma: commit revert; OpenAPI diff'i kanıt olarak saklanır.

---

## 9. R7 — `analytics.py` → Paket (+ reporting ince ayarı) (Backend)

**Hedef:** 1585 satırlık analiz modülünü ayırmak; rapor çıktısı **birebir aynı** kalmalı.

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R7-1 | Bulgu çıkarımı + pain-point matrisi | `analytics/findings.py` |
| R7-2 | Fiyat (Van Westendorp) | `analytics/pricing.py` |
| R7-3 | Kanıt zinciri + karar katmanı | `analytics/evidence.py` |
| R7-4 | Harici kanıt (web corroboration) | `analytics/corroboration.py` |
| R7-5 | Rapor metrikleri | `analytics/metrics.py` |
| R7-6 | Rapor zenginleştirme (Pro LLM) | `analytics/enrichment.py` |
| R7-7 | `synthesize_report` orkestrasyonu | `analytics/synthesis.py` |
| R7-8 | Re-export shim | `analytics/__init__.py` |
| R7-9 | `reporting.py` alt bölümleri ayır | `reporting/markdown.py`, `reporting/html.py`, `reporting/__init__.py` |

### Kabul kriterleri
- Her dosya **< 500 satır**.
- **Golden test:** bilinen çalışmanın `report_markdown` çıktısı öncesi/sonrası birebir aynı.
- `test_reporting.py`, `test_van_westendorp.py`, `test_evidence_chain.py`, `test_decision_layer.py`, `test_report_metrics.py`, `test_web_corroboration.py` yeşil.

> **Not:** Rapor kalite metrikleri (`report_metrics`) ve uydurma-kaynak yasağı korunur.

---

## 10. R8 — `workflow.py` → Paket + Mapper/DTO + Bağımlılık (Backend)

**Hedef:** 1392 satırlık orkestrasyonu ayırmak; dict/dataclass dönüşümlerini tek katmana toplamak; bağımlılıkları sadeleştirmek.

### İş kalemleri

| ID | İş | Hedef dosya |
|---|---|---|
| R8-1 | Plan üretimi (objective, assumptions, script) | `workflow/planning.py` |
| R8-2 | Persona üretimi + bio zenginleştirme | `workflow/personas.py` |
| R8-3 | Mülakatlar (batch + stream) | `workflow/interviews.py` |
| R8-4 | Prompt kurulumu (ELEPHANT, kalite tamiri) | `workflow/prompts.py` |
| R8-5 | Re-export shim | `workflow/__init__.py` |
| R8-6 | DTO/mapper katmanı (dict ↔ dataclass ↔ API) | `mappers/*.py` |
| R8-7 | Tolerant alan okuma tek yerde | `mappers/tolerant.py` |
| R8-8 | Kullanılmayan bağımlılıkların ayıklanması | `requirements.txt` |
| R8-9 | `crawl4ai` opsiyonel bağımlılık grubu | `requirements-optional.txt` |
| R8-10 | Mimari testi: import döngüsü + katman kuralı | `test_architecture.py` genişletme |

### Kabul kriterleri
- Her dosya **< 500 satır**.
- **Golden test:** persona üretimi + mülakat prompt'u çıktısı davranışsal olarak aynı (deterministik persona testi yeşil).
- `requirements.txt` yalnızca gerçekten kullanılan paketleri içerir; backend imajı küçülür.
- `test_architecture.py` döngüsüzlüğü doğrular.

---

## 11. Sıralama ve Kilometre Taşları

| Sıra | Sprint | Çıktı |
|---|---|---|
| 1 | R1 | Study detay veri katmanı ayrıldı |
| 2 | R2 | Sekmeler bağımsız bileşen |
| 3 | R5 | DB paketi (shim) |
| 4 | R6 | API router'ları ayrıldı |
| 5 | R7 | Analiz paketi + golden |
| 6 | R8 | Workflow paketi + mapper + bağımlılık |
| 7 | R3 | Admin ayrıldı |
| 8 | R4 | Landing/wizard/token |

**Neden bu sıra:** Önce en çok dokunulan büyük dosyalar (study detay, DB, API) ele alınır; bunlar sonraki değişikliklerin maliyetini düşürür. Admin ve landing görece bağımsız olduğu için sona bırakılabilir.

---

## 12. Ölçüm ve Başarı Kriterleri

| Metrik | Önce | Hedef |
|---|---:|---:|
| En büyük dosya | 2364 | < 600 |
| 1000+ satır dosya sayısı | 4 (frontend) + 3 (backend) | 0 |
| Import döngüsü | bilinmiyor | 0 |
| Test sayısı | mevcut | Azalmaz (≥ mevcut) |
| CI durumu | yeşil | Yeşil kalır |
| Rapor çıktısı | — | Birebir aynı (golden) |
| OpenAPI şeması | — | Değişmez |

---

## 13. Riskler ve Azaltma

| Risk | Etki | Azaltma |
|---|---|---|
| Görsel regresyon (frontend) | Orta | Ekran görüntüsü baz karşılaştırması; sekme bazlı revert |
| Rapor çıktısı değişimi | Yüksek | Golden markdown testi; diff boş olmalı |
| API sözleşmesi değişimi | Yüksek | OpenAPI diff; boş olmalı |
| DB kritik yol kırılması | Yüksek | Shim ile import sabit; migration/RLS testleri |
| Aynı anda çok dosya | Orta | Sprint başına tek modül ailesi |
| Refaktör sırasında hata bulma | Orta | Hatayı ayrı commit'te düzelt; refaktöre karıştırma |
| Celery worker eski kodu çalıştırma | Orta | Backend değişikliğinde `api` + `celery_worker` birlikte rebuild |

---

## 14. Tanım: Bitmiş (Definition of Done)

Bir refaktör sprinti ancak şu koşullarda kapanır:

1. Hedef satır sayısına ulaşıldı.
2. `python scripts/run_tests.py` yeşil.
3. `npx tsc --noEmit` + `eslint` temiz.
4. Golden/OpenAPI karşılaştırması boş fark.
5. Davranış değişmedi (E2E veya ekran görüntüsü kanıtı).
6. Import döngüsü yok.
7. `MEMORY.md` güncellendi.
8. CI yeşil; commit + push.

---

## 15. Kapsam Dışı

- Yeni özellik geliştirme
- Performans optimizasyonu (ayrı iş)
- Metin/içerik değişiklikleri (S1–S3 ve S9'da yapıldı)
- Renk/görsel yeniden tasarım (yalnızca R4-5 sınırlı token uyumu)
- Canlıya geçiş (S10, ertelendi)
