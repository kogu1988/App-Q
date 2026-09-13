# Clarere — Rekabet Analizi

## Doğrudan Rakipler (Sentetik Persona Araştırması)

| Platform | Ne Yapar | Güçlü Yönü | Zayıf Yönü |
|---|---|---|---|
| **Synthetic Users** | AI personalarla ürün testi | 1000+ kişilik paneller, İngilizce pazar lideri | Türkiye yok, fiyat bazlı değil, metodoloji şeffaf değil |
| **PersonaGen / GPT wrappers** | "5 persona oluştur, sor" | Hızlı, ucuz | Sıfır metodoloji, dalkavukluk, herkes aynı şeyi söyler |
| **Clarere (biz)** | Bilimsel temelli sentetik araştırma | Türkiye odağı, metodoloji, anti-dalkavukluk, fiyat analizi | Küçük ekip, yeni marka |

## Dolaylı Rakipler (Geleneksel Araştırma)

| Platform | Ne Yapar | vs Clarere |
|---|---|---|
| **UserTesting** | Gerçek kullanıcı testi | Onlar: gerçek insan. Biz: dakikalar içinde ön hipotez, ~$0.01–0.04 |
| **Maze** | Prototip testi | Onlar: UX metrikleri. Biz: pazar + fiyat araştırması |
| **Typeform / SurveyMonkey** | Anket | Onlar: ölçeklenebilir. Biz: derinlemesine mülakat simülasyonu |
| **ChatGPT (düz prompt)** | "Bu ürün hakkında ne düşünürsün?" | Onlar: bedava. Biz: hipotez-kör tasarım, kanıt zinciri, anti-dalkavukluk denetimi |

## Türkiye Pazarı

| Durum | Detay |
|---|---|
| **Yerel rakip yok** | Türkiye odaklı sentetik araştırma yapan başka platform yok |
| **En büyük rakip: Excel + ChatGPT** | İnsanlar prompt yazıp kendileri analiz ediyor |
| **Ajanslar manuel yapıyor** | 4-6 hafta, 50K+ TL proje başı |

## Clarere'nin Avantajı

| Avantaj | Neden Önemli |
|---|---|
| 🔬 **Metodolojik çerçeve** | Persona paneli ve bulgular davranış bilimi çerçevelerine dayanır; kanıt zinciriyle izlenir |
| 🇹🇷 **Türkiye odağı** | TÜAD SES, Hofstede TR, KVKK, BDDK, taksit refleksleri |
| 💰 **Birim ekonomisi** | Araştırma başına ~$0.01–0.04. UserTesting: $50-200 |
| ⚡ **Hız** | Dakikalar. Geleneksel: 4-6 hafta |
| 🛡️ **Anti-dalkavukluk** | Personalar "hayır" diyebiliyor; panelde Skeptic zorunlu |

## Clarere'nin Zayıf Yönü

| Zayıflık | Çözüm |
|---|---|
| Yeni marka, bilinirlik yok | SEO landing sayfaları hazır, içerik pazarlaması |
| DeepSeek bağımlılığı (tek provider) | Enterprise'ta yerel modellere geçiş planı var |
| Gerçek insan değil (algı sorunu) | "Yönlendirici hipotez" olarak konumlandır, gerçek araştırma öncesi filtre |
| Ekip küçük | Şimdilik yeterli, büyüdükçe scale |

## Konumlandırma

```
GERÇEK İNSAN                     SENTETİK
     │                              │
     │   UserTesting                │   Clarere ← BİZ BURADAYIZ
     │   Maze                       │   Synthetic Users
     │   Anket şirketleri           │   ChatGPT wrapper'lar
     │                              │
     └──────────────────────────────┘
        Haftalar / Binlerce TL       Dakikalar / Kuruşlar
```

**Clarere = Davranış bilimi çerçeveleri + Türkiye odağı + dakikalar içinde ön hipotez + ~$0.01–0.04.**
Bu kombinasyonu yapan başka bir yerli platform bilinmiyor.

---

## 🗳️ Siyasi Parti / Seçim Araştırması

### Neden Clarere?

Geleneksel anket şirketleri: 2-4 hafta, 100K+ TL, örneklem sorunu, sosyal beğeni yanlılığı (insanlar anketörlere gerçek fikrini söylemez).

Clarere sentetik seçmen paneli:
- **SES × Rogers × coğrafi dağılım** ile temsili panel
- **ELEPHANT** sayesinde seçmenler "doğru cevabı" değil **gerçek fikrini** söyler
- **Dakikalar içinde** sonuç, araştırma başına **~$0.01–0.04** model maliyeti
- Parti programı, aday algısı, vaat testi, kriz senaryosu simülasyonu

### Örnek Kullanım Senaryoları

| Senaryo | Defne Brief Örneği |
|---|---|
| **Aday algısı** | "X partisinin belediye başkan adayı hakkında İstanbul'daki C2-DE seçmen ne düşünüyor?" |
| **Vaat testi** | "Emekliye 5000 TL seyyanen zam vaadini 55+ seçmen nasıl karşılar?" |
| **Kriz simülasyonu** | "Adayın geçmişteki X açıklaması seçmenin oy tercihini nasıl etkiler?" |
| **Kararsız seçmen** | "İki parti arasında kararsız bir seçmenin kırılma noktası nedir?" |

### Mevcut Altyapıda Gereken Değişiklik

| Bileşen | Durum |
|---|---|
| SES × Rogers matrisi | ✅ Zaten var (AB/C1/C2/DE × 5 stance) |
| Hofstede TR kültürel kalibrasyon | ✅ Zaten var |
| Anti-dalkavukluk (ELEPHANT) | ✅ Kritik — seçmen gerçeği söylemeli |
| Siyasi brief/intake prompt'u | ⚠️ Yeni wizard_prompt eklenmeli (admin panelden) |
| Hassas içerik filtresi | ⚠️ Siyasi nefret söylemi için guardrail genişletilmeli |
| Seçmen persona havuzu | ⚠️ TÜİK seçmen profilleriyle önceden oluşturulmalı |

### Rakiplere Karşı Avantaj

| | Geleneksel Anket | Clarere |
|---|---|---|
| Sosyal beğeni yanlılığı | ❌ Yüksek | ✅ ELEPHANT ile minimize |
| Hız | 2-4 hafta | 2 dakika |
| Maliyet | 100K+ TL | ~$0.01–0.04 |
| Örneklem | Saha bağımlı | TÜİK oranlarına uygun matris |
| Tekrar edilebilirlik | Düşük | Sonsuz (her seferinde yeni panel) |
