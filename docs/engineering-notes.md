# App-Q — Mühendislik Notları

Bu belge App-Q'nun teknik kararlarını, model seçim kriterlerini, yerel donanım stratejisini, KVKK pozisyonunu ve öğrenme döngüsü tasarımını tek çatı altında toplar.

---

## 1. Yerel Sıfır Maliyetli MVP Stratejisi

App-Q, oyun PC'si veya Apple Silicon üzerinde sıfır maliyetle, sıralı (sequential) işleme kabul edilerek oluşturulabilir.

**Temel kural:** Her persona ayrı ayrı mülakata alınır, state persist edilir, bellek mümkün olduğunda serbest bırakılır.

### Donanım Stratejisi (RTX 4060 8GB referans)

- Aynı anda yalnızca **bir model** yüklü tutulur
- Sıralı persona mülakatı (paralel çalıştırma yok)
- GPU baskısı görünürse mülakatlar arasına kısa duraklama
- İlk aşamada küçük panel, büyük panel için batch job
- Model adaptör sınırı korunur (Ollama swap yapılabilir)

### Yerel Tech Stack

| Katman | Teknoloji |
|---|---|
| Model Server | Ollama |
| E-ticaret / B2C | Trendyol LLM GGUF (lisans doğrulandı) |
| B2B / Genel | Qwen 2.5 veya Kizagan-E4B GGUF |
| Persona Belleği | SQLite (ilk sürüm), pgvector (gelişmiş) |
| Orchestration | Python |
| UI | Next.js + FastAPI (Streamlit'ten migrate edildi) |

---

## 2. Model Seçim Kriterleri

Aday modeller şu kriterlere göre değerlendirilir:

- Türkçe doğallık (çeviri değil, native)
- Türkiye pazar bağlamı (e-ticaret + B2B jargonu)
- Şüpheciliğe ve fiyat hassasiyetine direnç
- Persona kısıtlarına uyum
- RTX 4060 sınıfı donanımda hız
- GGUF/quantized kullanılabilirliği
- Lisans ve ticari kullanım şartları

### Mevcut Model Benchmark Sonuçları

Detaylı değlendirme: [`model-benchmark-notes.md`](model-benchmark-notes.md)

**Mevcut routing:**
- `app-q-trendyol` → E-ticaret/B2C persona
- `app-q-kizagan-e4b` → B2B, fiyat itirazı, KVKK muhakemesi, sentez

**Reject edilenler:** `turkish-llama8b` (asistan mod kayması), `llama3-tr-ft` (halüsinasyon), `turkish-gemma9b` (RTX 4060'ta 40-56s/cevap — batch-only)

```powershell
.\.venv\Scripts\python.exe scripts\run_turkish_eval.py
# Çıktı: data/outputs/turkish-eval-results.jsonl
```

---

## 3. Anti-Sycophancy Tasarımı

Çift geçişli (dual-pass) üretim:

1. Persona cevabı üretir.
2. Gizli bir yargıç (judge), cevabın persona duruşunu ihlal edip etmediğini kontrol eder.
3. Cevap fazla uzlaşmacı veya jenerik ise daha sert prompt ile yeniden üretilir.

**Kural:** Yargıç olumsuzluğu zorlamaz; persona tutarlılığını ve yararlı anlaşmazlığı uygulatır.

---

## 4. Bellek Tasarımı (Pratik ACT-R Yaklaşımı)

Tam ACT-R yerine, pratik "yoksul adamın ACT-R'ı":

1. Her persona için her soru ve cevabı depola.
2. Yeni soruda yalnızca en alakalı önceki turları getir.
3. Prompt'a kısa bir tutarlılık notu ekle.
4. Persona kimliği ve bilgi sınırı sabit tutulsun.

SQLite ilk sürümü destekler. Anlamsal sorgulama gerekince ChromaDB eklenebilir.

> **Not:** Tam ACT-R implementasyonu backlog'da — bkz. `development_backlog.md` §ACT-R Working Memory.

---

## 5. Öğrenme Döngüsü (Learning Loop)

### Lansman Sonrası

Ham müşteri verisi doğrudan eğitimde kullanılmaz.

Önerilen döngü:
1. Müşteri onaylı araştırma oturumlarını yakala.
2. Hassas ticari bilgileri kaldır/maskele.
3. Brief, persona çıktıları, rapor bulgular ve kullanıcı geri bildirimlerini ayrı depola.
4. Operatör veya müşteri yararlı/zayıf/yanlış/jenerik bulguları işaretle.
5. Yüksek kaliteli örnekleri önce iç eval set'e çevir.
6. Yeterli onaylı veri oluşunca fine-tuning veri seti hazırla.

### Fine-Tuning Hazırlık Eşiği

- Model/provider baseline kararlı
- 100-300 yüksek kaliteli onaylı örnek
- Eval set regresyonu tespit edebilir
- Veri izni ve saklama kuralları tanımlı
- Çıktılar anonimleştirilmiş veya açıkça onaylanmış

**Erken iyileştirme:** Prompt, retrieval, persona şablonu, eval — LoRA/QLoRA öncesi.

### Geri Bildirim Sinyalleri

- Bulgu: yararlı / jenerik / yanlış
- Eksik persona segmenti
- Yanlış ton
- Zayıf Türkçe
- Gerçekçi olmayan fiyat varsayımı
- Müşteri düzenlediği rapor bölümü
- Gerçek dünya doğrulama sonucu

---

## 6. KVKK ve Veri Pozisyonu

> Bu yasal tavsiye değildir. Ticari lansman öncesinde nitelikli hukuk danışmanından görüş alınmalıdır.

### Ürün Gereksinimleri

- Müşteri brief'leri ve çıktıları varsayılan olarak yerel tutulur.
- Açıkça yapılandırılmadıkça promptlar harici API'lere gönderilmez.
- Varsayılan olarak prompt veya çıktı loglanmaz.
- `.env` version control dışında tutulur.
- Örnek veri müşteri verisinden ayrılır.
- Çok kullanıcılı kullanım öncesi silme/dışa aktarma kontrolleri eklenir.

### Pazar Avantajı

Türkiye B2B müşterileri için veri yerleşimi (data residency) önemli bir farklılaştırıcı olabilir. Bankalar, telekom, holdingler ve düzenlenmiş sektörler ürün konsepti, fiyatlandırma stratejisi ve gizli araştırma verileri için yabancı LLM API'leri kullanmaktan kaçınabilir.

### Eğitim Verisi Kuralı

Sosyal medya, şikayet siteleri, forumlar veya telif hakkıyla korunan ticari içeriklerin izinsiz scraping'inden kaçın. Tercih et:
- Lisanslı veri setleri
- Birinci taraf müşteri onaylı örnekler
- Sıfır taraflı araştırma girdileri
- İzin verilen tohum verilerden sentetik augmentasyon

### Güvenli Konumlandırma

`"Yerel/çevrimdışı-uyumlu mimari, sınır ötesi veri transferini ve üçüncü taraf API riskini azaltmak için tasarlandı."`

(Hukuki inceleme yapılmadıkça "%100 KVKK uyumlu" iddiasından kaçın.)

### Araştırma Feragatnamesi

Sentetik personalar yararlı yönlendirici içgörüler üretebilir; ancak gerçek duygu, bağlam, satın alma sürtünmesi veya sosyal baskı yaşamazlar. App-Q raporları yüksek riskli kararlar için gerçek dünya doğrulamasını açıkça önermelidir.
