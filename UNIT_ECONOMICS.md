# Clarere — Birim Ekonomi (COGS) Notu

> **Tarih:** 2026-09-13 · **Kapsam:** DeepSeek API maliyeti vs plan fiyatları
> **Durum:** Tahmin modeli (gerçek token sayaçları `token_usage` tablosunda birikmektedir; bu not varsayımsaldır).

## 1. Sağlayıcı fiyatları (DeepSeek, 1M token başına USD)

| | Flash cache-hit | Flash cache-miss | Flash çıktı | Pro cache-hit | Pro cache-miss | Pro çıktı |
|---|---|---|---|---|---|---|
| **Off-peak** | $0.003 | $0.15 | $0.60 | $0.022 | $0.66 | $1.98 |
| **Peak** | $0.006 | $0.30 | $1.20 | $0.044 | $1.32 | $3.96 |

- **Peak saatler:** 01:00–04:00 ve 06:00–10:00 UTC (Pzt–Cum). Diğer tüm saatler **off-peak = yarı fiyat**.
- **Cache-hit**, cache-miss'e göre ~50x ucuz → **prefix caching maliyeti belirleyen ana kaldıraç**.
- Context 1M / max output 384K → `max_tokens` sınırı darboğaz değil.

## 2. Araştırma başına token modeli (senkron akış, 10 persona)

| Aşama | Model | Girdi | Çıktı | Not |
|---|---|---|---|---|
| Defne intake | Flash | ~5 K | ~1.5 K | çok turlu; system prefix cache'lenir |
| Plan / reframing | Flash | ~1.5 K | ~1 K | |
| Batch mülakat (10 persona) | Flash | ~19 K | ~1.5 K | system prefix paylaşımlı → yüksek cache-hit |
| Sentez zenginleştirme | Pro | ~4 K | ~1.5 K | `effort=max` |
| **Toplam** | | **Flash ~26 K / Pro ~4 K** | **Flash ~4 K / Pro ~1.5 K** | |

### Araştırma başına COGS (tahmin)

| Senaryo | Flash | Pro | **Toplam** |
|---|---|---|---|
| Off-peak, cache yok | $0.0063 | $0.0056 | **~$0.012** |
| Peak, cache yok | $0.0126 | $0.0112 | **~$0.024** |
| Off-peak, %60 prefix cache | ~$0.004 | ~$0.004 | **~$0.008** |

### Async "Research Studio" koşusu (10 persona + 10 Pro kodlama + denetim döngüleri)

| Senaryo | **Toplam** |
|---|---|
| Off-peak | **~$0.020** |
| Peak | **~$0.040** |

> Adversarial döngü, echo yeniden üretimi ve retry'lar maliyeti çarpan etkisiyle artırır; LLM içerik-hash cache + `reasoning_effort` + prefix cache bunları ciddi azaltır.

## 3. Plan fiyatları ve marj

| Plan | Fiyat | Kota | COGS (off-peak) | Brüt marj |
|---|---|---|---|---|
| Free | $0 | 2 araştırma veya 1 ay | ~$0.016–0.024 | — (edinim maliyeti) |
| Flex (tek seferlik) | $49 | 3 araştırma | ~$0.036 | **~99.9%** |
| Starter | $69/ay ($55 yıllık) | 10 araştırma | ~$0.12 | **~99.8%** |
| Pro | $169/ay ($135 yıllık) | sınırsız (fair-use ~100) | ~$1.2–2.0 | **~99%** |
| Enterprise | özel | sınırsız + yerel model | — | — |

**Sonuç:** COGS brüt marjı bağlayan kısıt **değil** — en kötü senaryoda (10x aşım + peak) bile marj %90'ın üzerinde kalır.

## 4. Gerçek kısıtlar (COGS değil)

1. **DeepSeek rate limit / eşzamanlılık** (Flash 2500, Pro 500) → eşzamanlı yük yönetimi.
2. **Free plan kötüye kullanımı** (2 araştırma sınırı) → mevcut kota guard'ları kritik.
3. **Yeniden koşular**: retry, adversarial döngü, echo regen → token çarpanı.

## 5. Öneriler

1. **Admin maliyet panelindeki `DEEPSEEK_PRICE_*` env'lerini** güncel off-peak/peak değerleriyle eşle (panel tahmini doğru olsun).
2. **Ağır/batch işleri (async, benchmark) off-peak'e** planla → %50 tasarruf.
3. Prefix cache'i koru: sistem promptunu **sabit tut, başa al** (mülakat promptu bu prensiple düzenlendi).
4. `reasoning_effort` rol bazlı kal: intake/routing `low`, mülakat `high`, sentez `max`.
