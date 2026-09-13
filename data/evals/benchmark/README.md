# Bağımsız Benchmark — RFI Kalibrasyonu

> **Durum:** 🟡 **Kısmen hazır (harness kurulu).** Gerçek veri ve bağımsız insan değerlendirici bekliyor.
> **İlke:** Bu dizinde **uydurma veri YOKTUR ve üretilmez.** Tüm `human_*` alanları gerçek uzman/insan tarafından doldurulur.

---

## 1. Amaç

Clarere'nin sentetik bulgularının, **bağımsız insan (uzman) bulgularıyla** ne ölçüde örtüştüğünü ölçmek ve `benchmark.py` içindeki RFI eşiklerini **gerçek veriyle kalibre etmek**.

Hedef: en az **20 gerçek brief** + her biri için uzman referansı + **2 bağımsız değerlendirici**.

---

## 2. Veri akışı

```
1. Gerçek brief'ler                       -> gerçek ürün/pazar araştırma soruları
2. Clarere çalışması çalıştırılır         -> study_id elde edilir
3. python scripts/benchmark_collect.py    -> Vaka iskeleti (llm_findings dolu, human_* boş)
4. Uzman human_findings / critical /      -> İNSAN tarafından doldurulur
   contradictions doldurur
5. İki değerlendirici kör tema eşleme     -> evaluator_a.json / evaluator_b.json
6. python scripts/benchmark_report.py     -> RFI + Cohen's kappa özeti
7. summary.json                           -> İddia değil, ölçüm özeti
```

---

## 3. Kör Tema Eşleme Protokolü

İnsan bulguları toplandıktan sonra, Clarere bulguları ile insan bulguları arasında **eşleşme** değerlendirilir.

**Kurallar:**
1. Değerlendiriciler, hangi bulgunun Clarere'ye hangisinin insana ait olduğunu **bilmez** (karışık sunum, rastgele sıra).
2. Her çift için karar: `match` / `partial` / `no_match`.
3. Değerlendiriciler **birbirinden bağımsız** çalışır; tartışmaz.
4. Etiket tanımları önceden yazılıdır (aşağıda) ve ölçüm sırasında değiştirilmez.

| Etiket | Tanım |
|---|---|
| `match` | Aynı temayı/olguyu aynı yönde anlatıyor |
| `partial` | Temayı kısmen paylaşıyor veya farklı yönde vurguluyor |
| `no_match` | Farklı tema |

**Uyum:** İki değerlendiricinin etiketleri arasında **Cohen's kappa** hesaplanır (`cohens_kappa`). Kappa < 0.60 ise protokol/etiket tanımı revize edilir; ölçüm güvenilir sayılmaz.

---

## 4. Vaka Şeması (`cases/<study_id>.json`)

```json
{
  "id": "study_xxx",
  "name": "Gerçek brief adı",
  "category": "kategori",
  "brief": { "...": "gerçek brief özeti" },
  "llm_findings": [ { "title": "...", "summary": "...", "category": "...", "confidence": 0.7 } ],
  "human_findings": [ { "title": "...", "summary": "...", "category": "..." } ],
  "critical": ["insan tarafından kritik işaretlenen bulgu metinleri"],
  "contradictions": [ ["bulgu A", "bulgu B"] ],
  "synthetic_validation": {
    "validated_by": ["kullanıcı görüşmesi", "satış verisi"],
    "method": "real_user_interview | sales_data | field_study | none",
    "notes": ""
  }
}
```

- `llm_findings`: `benchmark_collect.py` üretir (Clarere çıktısı).
- `human_findings`, `critical`, `contradictions`, `synthetic_validation`: **uzman doldurur**.

---

## 5. Değerlendirici Etiket Dosyaları

`evaluator_a.json` ve `evaluator_b.json`: aynı uzunlukta etiket listeleri.

```json
["match", "partial", "no_match", "match"]
```

`benchmark_report.py`, iki dosya varsa otomatik karşılaştırıp kappa'yı raporlar.

---

## 6. Kalibrasyon (S8-3)

`benchmark.py` içindeki benzerlik eşikleri şu an **varsayılandır**:

| Sabit | Değer | Rol |
|---|---|---|
| `_THEME_MATCH_THRESHOLD` | 0.30 | Tema eşleşmesi eşiği |
| `_CRITICAL_MATCH_THRESHOLD` | 0.25 | Kritik bulgu eşiği |
| `_CONTRADICTION_MATCH_THRESHOLD` | 0.25 | Çelişki eşiği |

20 vaka toplandıktan sonra, insan etiketleriyle karşılaştırılarak bu eşikler **ampirik olarak** ayarlanır (yanlış pozitif/negatif dengesi). Kalibrasyondan önce "varsayılan" olarak anılmalıdır.

---

## 7. Yayımlama Kuralı (S8-7)

- Yalnızca `summary.json` **özet** olarak yayımlanabilir.
- İfadeler **ölçüm diliyle** olmalıdır: "X vakada ortalama RFI = Y (min–max)".
- "İnsan kalitesinde", "bilimsel olarak kanıtlanmış" gibi ifadeler kullanılmaz.
- Vaka sayısı, kategori dağılımı ve değerlendirici uyumu (kappa) şeffaf paylaşılır.

---

## 8. Durum ve Sıradaki Adımlar

| Adım | Durum |
|---|---|
| Harness (collect + report + kappa) | ✅ Hazır |
| Kör tema eşleme protokolü | ✅ Belgeli |
| 20 gerçek brief | ⏳ Bekliyor (dış veri) |
| Uzman `human_findings` | ⏳ Bekliyor (insan) |
| İki bağımsız değerlendirici | ⏳ Bekliyor (insan) |
| Eşik kalibrasyonu | ⏳ Veri sonrası |
| `summary.json` yayımı | ⏳ Veri sonrası |

> Bu adımlar tamamlanana kadar hiçbir yerde "bağımsız bilimsel doğrulama" iddiası kullanılmaz.
