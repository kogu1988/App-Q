# PLAN-intake-persona.md
# Yapılandırılmış Dinamik Intake (Çözüm A) ve Psikometrik OCEAN / Yerel Dinamik Modelleme (Çözüm B) Planı

Bu plan, **App-Q** sentetik pazar araştırması platformunda keşif sihirbazı Defne'nin sohbet akışını kontrol eden **Dinamik Intake Yönetimi (Çözüm A)** ve sanal katılımcıların davranışlarını yönlendiren **Psikometrik OCEAN / Yerel Dinamik Modelleme (Çözüm B)** mimarilerinin uçtan uca entegrasyonunu ve doğrulamasını hedefler.

---

## 📋 Genel Bakış ve Hedefler

### Çözüm A: Dinamik Intake Yönetimi (Döngü Önleme ve Akıllı Durum Kontrolü)
*   **Problem:** Kullanıcıyla yapılan intake görüşmesinde Defne asistanı bazen aynı araştırma kategorisinde (örneğin rakip analizi veya fiyatlandırma) takılı kalıp dairesel sorular yöneltebiliyor veya kullanıcının "rakip analizi istemiyorum" gibi yönlendirmelerini atlayabiliyordu.
*   **Hedef:** `DiscoveryLoopGuard` motorunun yeteneklerini artırarak, brief'teki eksik alanları (`idea`, `title`, `target_users`, `expected_price`, `success_metric`, `discovery_channels`) dinamik olarak takip eden bir durum makinesi (state machine) gibi çalışmasını sağlamak. Döngü veya tamamlanma eşiği (maksimum 10 tur) tespit edildiğinde, görüşmeyi akıcı bir şekilde bir sonraki konuya yönlendirmek ya da otomatik brief sentezi yaparak simülasyonu tetiklemek.

### Çözüm B: OCEAN ve Yerel Dinamiklerin Modellemeye Katkısı (Grounded Simulation)
*   **Problem:** Sanal kullanıcıların (personas) LLM tabanlı simülasyon yanıtları bazen çok jenerik ve dalkavukça olabiliyor, Türkiye pazarının veya belirli bir SES (Sosyo-Ekonomik Statü) grubunun yerel reflekslerini tam yansıtamıyordu.
*   **Hedef:** `workflow.py` içindeki `build_elephant_system_prompt` yapısını zenginleştirerek; Big Five/OCEAN trait'lerinin, Hofstede kültürel boyutlarının (UAI, PDI, IDV) ve TÜAD 2025 SES profillerinin persona promptlarına inandırıcı, ampirik ve yerel unsurlarla enjekte edilmesini sağlamak. Örneğin, Ceren Çetin gibi bir İstanbul poodles-owner tablosunda WhatsApp vet grupları kullanımı, KVKK/güvenlik şüpheciliği ve TL bazlı Van Westendorp fiyat hassasiyeti yanıt tarzına deterministik yansımalıdır.

---

## ⚙️ Proje Tipi ve Teknoloji Yığını

*   **Proje Tipi:** `WEB` + `BACKEND` (Next.js Monorepo & Python FastAPI/Research-Engine)
*   **Teknoloji Yığını:**
    *   **Backend:** Python 3.11+, Pydantic, re (RegEx), JSON Parser, PyTest.
    *   **Frontend:** Next.js 14+ (App Router), Tailwind CSS v4, React Hook Form.

---

## 🚀 Başarı Kriterleri

1.  **Döngü Tespiti ve Kurtarma:** Defne asistanı circular questioning tespit ettiğinde doğrudan bir sonraki doldurulmamış brief alanına geçmeli ve diyalog 10 turu aştığında `extract_complete_brief` fallback mekanizması hatasız çalışmalıdır.
2.  **Deterministik OCEAN Prompt Enjeksiyonu:** Oluşturulan her sentetik persona promptunda OCEAN facet değerleri (`neo_facets`), TÜAD 2025 SES grubu etiketleri (`AB`, `C1`, `C2`, `DE`) ve Hofstede kültürel parametreleri eksiksiz bulunmalıdır.
3.  **Yerel Çıktı Kararlılığı:** Persona unit test senaryolarında, Türk personalarının jenerik yapay zeka kalıpları (örneğin "Yapay zeka olarak...") içermediği ve TL bazlı fiyat aralıklarını gerçekçi olarak telaffuz ettiği doğrulanmalıdır.
4.  **Tüm Testlerin Geçmesi:** Projede yer alan pytest unit testleri ve frontend statik linters (`npx tsc --noEmit`) 0 hata ile çalışmalıdır.

---

## 📂 Planlanan Değişiklik Haritası ve Dosyalar

```
c:\Users\oguzk\.gemini\antigravity\scratch\projeler\App-Q\
├── packages/
│   └── research_engine/
│       ├── intake.py              # [MODIFY] Akıllı DiscoveryLoopGuard, sonraki soru seçici
│       ├── workflow.py            # [MODIFY] build_elephant_system_prompt, yerel prompt blokları
│       └── tests/
│           ├── test_intake.py     # [MODIFY] Circular questioning ve recovery testleri
│           └── test_workflow.py   # [MODIFY] OCEAN, SES kota ve yerel prompt doğrulama testleri
```

---

## 📝 Detaylı Görev Dağılımı ve İş Akışı

### Faz 1: Backend Geliştirmeleri (Çözüm A - Dinamik Intake)

#### Görev 1.1: `intake.py` Akıllı Soru Seçici Entegrasyonu
*   **Gerekçe:** Loop tespiti anında veya normal akışta bir sonraki soruya karar verirken statik eşleşme yerine brief alanlarının doluluk oranını izleyen dinamik bir mekanizma kurgulamak.
*   **Ajan:** `backend-specialist` | **Skill:** `clean-code`
*   **INPUT:** `packages/research_engine/intake.py`
*   **OUTPUT:** `packages/research_engine/intake.py` içinde `get_next_strategic_question` metodu ve geliştirilmiş `guard_turn`.
*   **VERIFY:** `DiscoveryLoopGuard` motoru, circular questioning tespit ettiği turn'de asistan cevabını `updated_brief` içinde eksik olan ilk alanın sorusuyla (örn: `expected_price`) ezer.

#### Görev 1.2: `test_intake.py` unit testlerinin zenginleştirilmesi
*   **Gerekçe:** Döngü kurtarma (recovery) senaryolarını simüle ederek LoopGuard'ın kararlılığını kanıtlamak.
*   **Ajan:** `test-engineer` | **Skill:** `testing-patterns`
*   **INPUT:** `packages/research_engine/tests/test_intake.py`
*   **OUTPUT:** Yeni recovery ve circular questioning pytest senaryoları.
*   **VERIFY:** `pytest packages/research_engine/tests/test_intake.py` komutu başarıyla geçmelidir.

---

### Faz 2: Psikometrik ve Yerel Modelleme (Çözüm B - Grounded Simulation)

#### Görev 2.1: `workflow.py` Kültürel ve OCEAN Prompt Katmanının Geliştirilmesi
*   **Gerekçe:** Türk sentetik kullanıcılarının gerçekçi davranmasını sağlamak amacıyla, prompt katmanını yerel alışkanlıklarla (WhatsApp veteriner grupları, basılı karne alışkanlığı, KVKK hassasiyeti vb.) donatmak.
*   **Ajan:** `backend-specialist` | **Skill:** `clean-code`
*   **INPUT:** `packages/research_engine/workflow.py`
*   **OUTPUT:** `build_elephant_system_prompt` fonksiyonunun yerel pazar dinamikleri (`HOFSTEDE_TURKEY_PROMPT` ve SES profilleri ile) genişletilmiş hali.
*   **VERIFY:** `build_elephant_system_prompt(persona)` çağrıldığında dönen string içinde Hofstede kültürel blokları ve OCEAN facet parametreleri yer almalıdır.

#### Görev 2.2: `test_workflow.py` Test Kapsamının Zenginleştirilmesi
*   **Gerekçe:** Persona promptlarının anti-dalkavukluk kurallarına, OCEAN etiketlerine ve Hofstede kota dağılımlarına uyumunu doğrulamak.
*   **Ajan:** `test-engineer` | **Skill:** `testing-patterns`
*   **INPUT:** `packages/research_engine/tests/` altındaki workflow testleri.
*   **OUTPUT:** Persona prompt içeriğini ve Big Five korelasyonunu denetleyen yeni testler.
*   **VERIFY:** `pytest packages/research_engine/tests/` tüm testlerin yeşil yanması.

---

## 🏁 Faz X: Nihai Doğrulama ve Uyumluluk Kontrolleri

Tüm geliştirmeler tamamlandıktan sonra, projenin yeşil duruma geçmesi için şu adımlar işletilecektir:

*   **P0: Lint ve Tip Kontrolleri:**
    ```bash
    npx tsc --noEmit (Frontend tarafında)
    ```
*   **P0: Güvenlik Taraması:**
    ```bash
    python .agent/skills/vulnerability-scanner/scripts/security_scan.py .
    ```
*   **P1: UX & Tasarım Denetimi (Moratoryum Uyumu):**
    *   [ ] Arayüz kodlarında hiçbir mor/violet tonu (`#8B5CF6`, `#7C3AED` vb.) kullanılmamış olmalıdır.
    *   [ ] Switch animasyonlarında ve hover efektlerinde glitch/genişleme-daralma olmaksızın smooth geçişler sağlanmış olmalıdır.
*   **P2: E2E ve Genel Sistem Doğrulaması:**
    ```bash
    python .agent/scripts/verify_all.py .
    ```

---

## ✅ PHASE X COMPLETE
*(Bu alan, Faz X doğrulamaları yapıldıktan sonra doldurulup imzalanacaktır.)*
- Lint: [x] Pass
- Security: [x] Pass
- Build: [x] Pass
- Date: [2026-05-24]
