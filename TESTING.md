# Clarere — Test Rehberi

Bu dosya testleri nasıl çalıştıracağını, hangi testlerin hangi ortama ihtiyaç duyduğunu ve CI yapısını açıklar.

---

## 1. Hızlı başlangıç

### Tek komut (önerilen)

```bash
python scripts/run_tests.py
```

Bu script:
1. Postgres erişimini kontrol eder.
2. Erişilemiyorsa Docker ile geçici bir `socat` port-forward (`localhost:5433 → postgres:5432`) kurar.
3. Tam backend süitini uygun ortam değişkenleriyle çalıştırır.
4. Kurduğu forward'ı temizler.

Ek pytest argümanı geçirmek için:

```bash
python scripts/run_tests.py -- -k cache -v
```

DB olmadan (CI-benzeri) çalıştırma:

```bash
python scripts/run_tests.py --no-db
```

### Frontend

```bash
cd apps/frontend
npx tsc --noEmit   # tip kontrolü
npx eslint         # lint
```

---

## 2. Test katmanları

| Katman | Konum | Ortam gereksinimi |
|---|---|---|
| Backend birim/entegrasyon | `packages/research_engine/tests/` | Postgres (DB-gated testler için) |
| E2E (Playwright) | `e2e/tests/` | Docker stack + (gerçek akış için) `DEEPSEEK_API_KEY` |
| PDF yapısal | `test_pdf_golden.py` | Yok (xhtml2pdf kurulu ise) |
| LLM önbellek | `test_llm_cache.py` | Yok |

### DB-gated testler

Bazı testler canlı Postgres gerektirir ve DB yoksa `skip` olur (ör. `test_migrations`, `test_quota_atomicity`, `test_product_events`, `test_rls_*`, `test_persona_traits::test_13_10`). CI'da bu testler atlanır; yerelde `run_tests.py` ile çalışır.

---

## 3. CI (GitHub Actions)

`.github/workflows/ci.yml` — her push/PR'da:

| İş | İçerik |
|---|---|
| Backend (pytest) | `requirements-dev.txt` kurulumu + `pytest -q`; sonuç **job summary**'ye yazılır (test sayısı SSOT) |
| Frontend (typecheck + lint) | `npm ci` + `tsc --noEmit` + `eslint` |

**Test sayısı SSOT:** Dokümanlarda sabit sayı tutulmaz; güncel sayı CI job özetinden okunur.

### E2E (`e2e.yml`)

- Elle (`workflow_dispatch`) veya haftalık (Pazartesi 04:30 UTC, off-peak) çalışır.
- `DEEPSEEK_API_KEY` secret'i **tanımlı değilse sessizce atlanır** (yeşil geçer) — push/PR CI'ı bloklamaz.

**E2E'yi etkinleştirmek için (tek seferlik, kullanıcı aksiyonu):**
1. GitHub → Settings → Secrets and variables → Actions.
2. `DEEPSEEK_API_KEY` secret'ini ekle.
3. Actions → "E2E (Playwright)" → Run workflow.

Yerelde çalıştırma (Docker stack açıkken):

```bash
cd e2e && npx playwright test
```

---

## 4. Stack gerektiren testler (manuel / E2E hattı)

Aşağıdakiler Docker yığını veya özel altyapı gerektirir; birim süitinde çalışmaz:

| Test | Neden | Nasıl doğrulanır |
|---|---|---|
| **Mobil görsel regresyon** | Tarayıcı + viewport gerekir | `e2e/` içinde 375px/768px ekran görüntüsü karşılaştırması |
| **Yük/eşzamanlılık** | Çok sayıda eşzamanlı istek | Docker stack + `k6`/`locust` ile API'ye yük |
| **Celery retry / idempotency** | Redis broker + worker gerekir | Aynı job'ı iki kez tetikle, çıktının tekilleştiğini doğrula |
| **Paddle webhook (canlı)** | Paddle sandbox/live hesabı | `scripts/setup_paddle_catalog.py` + sandbox event |
| **Backup / restore** | Gerçek DB + cron | `scripts/backup_db.sh` çalıştır, geri yükle |

Bu testler S7 kapsamında **belgelenmiştir**; altyapı hazır olduğunda (S10 / Docker CI) otomatikleştirilir.

---

## 5. Regresyon korunacak değerler

Aşağıdaki test dosyaları kasıtlı olarak "koruma" amaçlıdır — ürünün farklılaştırıcı özelliklerini kilitler:

- `test_stance_diversity.py` — Skeptic zorunluluğu, Largest Remainder
- `test_persona_traits.py` — Openness/Agreeableness kalibrasyonu, panel boyutu, determinizm
- `test_hypothesis_blind.py` — hipotez-körlük
- `test_evidence_chain.py` / `test_decision_layer.py` — kanıt zinciri ve karar katmanı
- `test_web_corroboration.py` — **uydurma dış kanıt üretilmemesi**
- `test_web_corroboration.py` / `test_degradation_and_tenant.py` — graceful degradation
- `test_blockers_p0.py` — JWT/admin/CORS guard'ları, Paddle imza, fiyat tablosu
- `test_report_metrics.py` — rapor kalite metrikleri
- `test_llm_cache.py` — maliyet önbelleği
