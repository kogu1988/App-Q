# App-Q — Kapsamlı Test Planı

**Versiyon:** 1.0 — 2026-05-23  
**Kapsam:** research_engine, FastAPI backend, Next.js frontend, Akademik Sentez entegrasyonu  
**Referans:** `docs/feature_inventory.md` (54 özellik), `docs/development_backlog.md` (tamamlanan sprintler)

---

## Test Katmanları

```
Unit Tests        → packages/research_engine/tests/
Integration Tests → tests/integration/
E2E Tests         → tests/e2e/ (Playwright)
Quality Gates     → .agent/scripts/checklist.py
```

---

## Katman 1 — Unit Tests (Python / pytest)

### T1.1 — `reframe_user_input()` — Input Reframing

**Dosya:** `packages/research_engine/tests/test_intake.py`  
**İlgili commit:** `5d37ece`  

| Test ID | Senaryo | Girdi | Beklenen çıktı | Tip |
|---------|---------|-------|----------------|-----|
| T1.1.1 | Yüksek kesinlik — satış garantisi | `"Bu ürün kesinlikle çok satacak"` | `(reframed_str, True)` | Happy path |
| T1.1.2 | Yüksek kesinlik — "herkes" | `"Herkes bu uygulamayı sevecek"` | `(reframed_str, True)` | Happy path |
| T1.1.3 | Onay arayan soru eki | `"Bu fiyat iyi değil mi?"` | `(reframed_str, True)` | Happy path |
| T1.1.4 | Nötr ifade — reframe yok | `"Fiyatlandırma nasıl olmalı?"` | `(same_str, False)` | Edge case |
| T1.1.5 | Boş string | `""` | `("", False)` — crash yok | Edge case |
| T1.1.6 | Tek kelime | `"Satacak"` | `("Satacak", False)` veya `(reframed, True)` | Edge case |
| T1.1.7 | Türkçe karakter içeren kesinlik | `"Ürünümüz mutlaka beğenilecek"` | `(reframed_str, True)` | Happy path |
| T1.1.8 | Reframe notu assistant_reply'a ekli mi? | `process_intake_chat()` mock | `"[Defne Notu:"` içeriyor | Integration |

```python
# packages/research_engine/tests/test_intake.py
import pytest
from packages.research_engine.intake import reframe_user_input

class TestReframeUserInput:
    def test_satis_garantisi_reframe_edilir(self):
        result, was_reframed = reframe_user_input("Bu urun kesinlikle cok satacak")
        assert was_reframed is True
        assert result != "Bu urun kesinlikle cok satacak"
        assert len(result) > 10

    def test_notr_ifade_dokunulmaz(self):
        text = "Fiyatlandirma nasil olmali?"
        result, was_reframed = reframe_user_input(text)
        assert was_reframed is False
        assert result == text

    def test_bos_string_crash_yapmaz(self):
        result, was_reframed = reframe_user_input("")
        assert was_reframed is False
        assert result == ""

    def test_herkes_ifadesi_reframe_edilir(self):
        result, was_reframed = reframe_user_input("Herkes bu uygulamayi sevecek")
        assert was_reframed is True

    def test_onay_arayan_soru_reframe_edilir(self):
        result, was_reframed = reframe_user_input("Bu tasarim iyi degil mi?")
        assert was_reframed is True
```

---

### T1.2 — `build_elephant_system_prompt()` — ELEPHANT Anti-Sycophancy

**Dosya:** `packages/research_engine/tests/test_workflow.py`

| Test ID | Senaryo | Agreeableness | Beklenen | Tip |
|---------|---------|---------------|----------|-----|
| T1.2.1 | Yüksek Agreeableness (Innovator) | 70 | `"ELEPHANT"` + ek uyarı içeriyor | Happy path |
| T1.2.2 | Standart Agreeableness (Mainstream) | 55 | `"ELEPHANT"` içeriyor, ek uyarı yok | Happy path |
| T1.2.3 | Düşük Agreeableness (Skeptic) | 28 | `"ELEPHANT"` + güçlü red izni | Happy path |
| T1.2.4 | traits dict boş | `{}` | Default 60 kullanılır, crash yok | Edge case |
| T1.2.5 | traits None | `None` | Default 60 kullanılır, crash yok | Edge case |
| T1.2.6 | Sınır değer 40 | 40 | Standart prompt (< 40 dalı değil) | Edge case |
| T1.2.7 | Sınır değer 65 | 65 | Standart prompt (> 65 dalı değil) | Edge case |
| T1.2.8 | Min karakter uzunluğu | herhangi | `len(prompt) >= 300` | Kalite |

---

### T1.3 — `persona_traits()` — Agreeableness Kalibrasyonu

| Test ID | Senaryo | Beklenen | Tip |
|---------|---------|----------|-----|
| T1.3.1 | Innovator agreeableness_mod = +4 | `STANCE_PROFILE["Innovator"]["agreeableness_mod"] == 4` | **Regression** |
| T1.3.2 | Skeptic agreeableness_mod = -10 | `STANCE_PROFILE["Skeptic"]["agreeableness_mod"] == -10` | **Regression** |
| T1.3.3 | Tüm trait değerleri 1-100 arasında | `all(1 <= v <= 100 for v in traits.values())` | Invariant |
| T1.3.4 | Innovator > Skeptic Agreeableness | `innovator_traits["Agreeableness"] > skeptic_traits["Agreeableness"]` | Happy path |
| T1.3.5 | Skeptic > Innovator Neuroticism | `skeptic_traits["Neuroticism"] > innovator_traits["Neuroticism"]` | Happy path |

---

### T1.4 — `quality.py` — Bias Detection + RFI

| Test ID | Senaryo | Beklenen | Tip |
|---------|---------|----------|-----|
| T1.4.1 | Straight-lining — 3 özdeş cevap | `detect_straight_lining() == True` | Happy path |
| T1.4.2 | Straight-lining yok — 3 farklı cevap | `detect_straight_lining() == False` | Happy path |
| T1.4.3 | Acquiescence — Skeptic + olumlu yoğunluk | `detect_acquiescence() == True` | Happy path |
| T1.4.4 | Acquiescence — Champion + olumlu — False | `detect_acquiescence() == False` | Edge case |
| T1.4.5 | Social desirability — klişe dolu cevap | `detect_social_desirability() == True` | Happy path |
| T1.4.6 | RFI skoru 0-1 arasında | `0.0 <= rfi["rfi"] <= 1.0` | Invariant |
| T1.4.7 | RFI validity threshold 0.65 | `rfi["valid"] == True` (yeterli bulgularla) | Happy path |

---

### T1.5 — `compute_research_quality()` — Kalite Skorlama

| Test ID | Senaryo | Beklenen | Tip |
|---------|---------|----------|-----|
| T1.5.1 | Boş mülakat | skor >= 0, crash yok | Edge case |
| T1.5.2 | Bias bayraklı persona | skor düşer | Regression |
| T1.5.3 | `meta_tone` flag varsa | `-10` puan cezası uygulanır | Happy path |
| T1.5.4 | Grade "green" koşulları | score >= 80 AND meta == 0 AND bias == {} | Happy path |
| T1.5.5 | Skor her zaman 0-100 aralığında | Herhangi girdi | `0 <= score <= 100` | Invariant |

---

## Katman 2 — Integration Tests (FastAPI + pytest)

### T2.1 — `/api/client/intake/chat` — Defne Sohbet Endpoint'i

| Test ID | Senaryo | Beklenen | Tip |
|---------|---------|----------|-----|
| T2.1.1 | Yüksek kesinlik → reframe notu görünür | `"[Defne Notu:"` string'i `assistant_reply`'da | **Yeni özellik** |
| T2.1.2 | Normal mesaj → reframe notu yok | `"[Defne Notu:"` string'i YOK | Happy path |
| T2.1.3 | Boş mesaj | HTTP 422 veya graceful hata | Error case |
| T2.1.4 | Model hata fırlatır | `current_brief` döner, crash yok | Error case |
| T2.1.5 | A/B test modu | `app_mode="ab_test"` — `variant_a/b` hedefleniyor | Happy path |

---

### T2.2 — `/api/client/interviews/stream` — SSE Mülakat Stream

| Test ID | Senaryo | Beklenen | Tip |
|---------|---------|----------|-----|
| T2.2.1 | Persona başına ELEPHANT promptu farklı mı? | Skeptic ve Innovator prompt uzunlukları farklı | **Regression** |
| T2.2.2 | 2. turdan itibaren `turn_memory` var mı? | 2. prompt'ta `"Son yanıtlarından"` string'i | **Yeni özellik** |
| T2.2.3 | `persona_start` eventi tetikleniyor mu? | SSE'de `"persona_start"` | Happy path |
| T2.2.4 | `meta_tone` → retry tetikleniyor mu? | Mock: `"asistan olarak"` cevap → `"retry"` eventi | Happy path |
| T2.2.5 | Model exception → graceful hata eventi | `"persona_error"` eventi döner | Error case |

---

### T2.3 — `/api/client/studies` — Araştırma CRUD

| Test ID | HTTP | Senaryo | Beklenen | Tip |
|---------|------|---------|----------|-----|
| T2.3.1 | POST | Yeni araştırma oluştur | HTTP 200 + `study_id` | Happy path |
| T2.3.2 | GET | Araştırma listele | Liste döner | Happy path |
| T2.3.3 | GET | Geçersiz `study_id` | HTTP 404 | Error case |
| T2.3.4 | PATCH | Arşivle | `status="archived"` | Happy path |
| T2.3.5 | GET | Arşivlenen listede görünmez mi? | Listeden çıkarılmış | Happy path |

---

### T2.4 — `/api/admin` — Güvenlik ve Admin

| Test ID | Senaryo | Beklenen | Tip |
|---------|---------|----------|-----|
| T2.4.1 | `ADMIN_SECRET_KEY` olmadan admin | HTTP 401 / 403 | **Security** |
| T2.4.2 | İstemci oluştur | HTTP 200 + `client_id` | Happy path |
| T2.4.3 | Sistem konfigürasyonu kaydet | HTTP 200 | Happy path |
| T2.4.4 | Sistem konfigürasyonu oku | Kaydedilen değerler döner | Happy path |
| T2.4.5 | Persona havuzu listele | Liste döner | Happy path |

---

## Katman 3 — E2E Tests (Playwright)

**Dosya:** `tests/e2e/test_research_flow.spec.ts`  
**Ön koşul:** Frontend port 3001, Backend port 8000 çalışıyor  
**Komut:** `npx playwright test`

### T3.1 — Uçtan Uca Araştırma Akışı

| Test ID | Adım | Beklenen | Tip |
|---------|------|----------|-----|
| T3.1.1 | "Yeni Araştırma" tıkla | Defne sohbet ekranı açılır | Happy path |
| T3.1.2 | "Bu ürün kesinlikle satacak" yaz | `"[Defne Notu:"` görünür | **Input Reframing** |
| T3.1.3 | Brief doldur → Plan Onayla | Persona paneli görünür | Happy path |
| T3.1.4 | Araştırmayı başlat | Cevaplar gerçek zamanlı akar (SSE) | Happy path |
| T3.1.5 | Mülakat tamamlanır | Rapor detay ekranına geçiş | Happy path |
| T3.1.6 | RFI kartı görünür mü? | Skor veya uyarı rozeti | Happy path |
| T3.1.7 | PDF indir | Dosya indirilir | Happy path |

### T3.2 — A/B Test Akışı

| Test ID | Adım | Beklenen | Tip |
|---------|------|----------|-----|
| T3.2.1 | A/B mod tetikle | `variant_a/b` Defne'den sorulur | Happy path |
| T3.2.2 | İki varyant gir | Brief tamamlanır | Happy path |
| T3.2.3 | Simülasyon başlar | Her persona iki varyantı karşılaştırır | Happy path |
| T3.2.4 | Raporda varyant karşılaştırması | "Varyant A"/"Varyant B" bulgularda | Happy path |

### T3.3 — Admin Paneli Güvenlik

| Test ID | Adım | Beklenen | Tip |
|---------|------|----------|-----|
| T3.3.1 | Admin giriş (geçerli key) | Giriş başarılı | Happy path |
| T3.3.2 | Admin giriş (yanlış key) | Erişim reddedilir | **Security** |
| T3.3.3 | İstemci listesi açılır | Tablo görünür | Happy path |
| T3.3.4 | Sistem konfigürasyonu kaydet | Bildirim görünür | Happy path |

---

## Katman 4 — Quality Gates

**Komut:** `python .agent/scripts/checklist.py .`

| Kontrol | Araç | Başarı Kriteri |
|---------|------|---------------|
| Lint — research_engine | `lint_runner.py` | 0 hata |
| Unit test coverage | `pytest --cov` | **>= %70** |
| Security scan | `security_scan.py` | CRITICAL: 0, HIGH: 0 |
| UX audit | `ux_audit.py` | 0 kritik |
| SEO kontrol | `seo_checker.py` | meta, title, robots mevcut |

---

## Tüm Komutlar

```powershell
# Unit testler
.\.venv\Scripts\pytest packages/research_engine/tests/ -v

# Belirli test dosyası
.\.venv\Scripts\pytest packages/research_engine/tests/test_intake.py -v

# Coverage raporu
.\.venv\Scripts\pytest packages/research_engine/tests/ --cov=packages/research_engine --cov-report=term-missing

# Integration testler (backend çalışmalı)
.\.venv\Scripts\pytest tests/integration/ -v

# E2E testler (frontend + backend çalışmalı)
npx playwright test tests/e2e/ --headed

# Full checklist
.\.venv\Scripts\python .agent/scripts/checklist.py .
```

---

## Öncelik Sırası

```
🔴 Kritik (Şimdi çalıştır)
  T1.1 — reframe_user_input()          [Yeni, sıfır test mevcut]
  T1.2 — build_elephant_system_prompt() [Yeni, sıfır test mevcut]
  T1.3 — Agreeableness regression       [Değer değişti: +8 → +4]

🟡 Yüksek
  T1.4 — quality.py bias detection      [Mevcut, doğrulama]
  T2.1 — Intake API + reframe notu      [Integration]
  T2.2 — Stream turn memory             [Yeni, integration]

🟢 Orta
  T3.1 — Uçtan uca akış                [E2E]
  T4.1 — Quality gates                  [Çalıştır, rapor al]
```

---

## Sprint Kapanma Kriterleri

| Kriter | Hedef |
|--------|-------|
| Unit test geçiş oranı | **%100** |
| research_engine coverage | **>= %70** |
| `reframe_user_input()` 8 vaka | **%100 geçmeli** |
| `build_elephant_system_prompt()` 8 vaka | **%100 geçmeli** |
| Agreeableness regression | Innovator=+4, Skeptic=-10 **sabit** |
| Integration — reframe notu | **Görünür** (T2.1.1) |
| E2E — temel akış | **T3.1.1–T3.1.6 geçmeli** |
| Security scan | **CRITICAL: 0** |

---

## Kapsam Dışı (Backlog Bekliyor)

| Alan | Durum |
|------|-------|
| `analytics.py` Reflection katmanı | S4 backlog — implement edilmedi |
| ACT-R DB kalıcı bellek | S5 backlog — DB şeması yok |
| Frontend Agreeableness görüntüsü | S4 backlog — render yapılmadı |
| Hofstede kültürel boyutlar | Çok-pazar sonrası |
| LoRA/fine-tuning döngüsü | Üretim sonrası |

---

*Bu test planı `docs/development_backlog.md` ile senkronize edilmelidir. Yeni sprint tamamlandığında test bölümü güncellenmeli.*
