# PLAN-design-token-fix.md
# Tasarım Token Uyum Düzeltmeleri — DESIGN.md → Cohere Kimliği

## Hedef
Panel kodlarındaki `indigo` Tailwind renklerini globals.css'teki Cohere token'larına
(`action-blue #1863dc`, `primary #17171c`, `focus-blue #4c6ee6`) eşleştir.
Gradient yüzey yasağını uygula. Font ve buton kimliğini güçlendir.

## Kapsam (B — Orta)
- ✅ Kritik: indigo → action-blue/primary, gradient kaldır
- ✅ Orta: pill butonlar, font class'ları, mono-label tablo başlıkları
- ❌ MVP-dışı: radius tutarsızlığı (düşük öncelik)

## Etkilenen Dosyalar
| Dosya | Sorun | Değişiklik |
|---|---|---|
| `studies/[id]/page.tsx` | 4 gradient + 30 text-indigo + 24 bg-indigo + 22 border-indigo | Cohere token'larına taşı |
| `admin/page.tsx` | 2 text-indigo + ring-indigo + FeedbackTable focus ring | token'larına taşı |

## Değiştirme Haritası

### Renk Eşlemesi
| Eski | Yeni | Neden |
|---|---|---|
| `text-indigo-600` (aktif/vurgulu UI) | `text-[#1863dc]` (action-blue) | Cohere editorial link rengi |
| `text-indigo-400` (dark mode) | `text-[#4c6ee6]` (focus-blue) | dark mode uyumu |
| `bg-indigo-600`, `from-indigo-500 to-blue-600` (buton/baloncuk bg) | `bg-primary` + `text-primary-foreground` | Cohere near-black surface |
| `bg-indigo-50/20`, `bg-indigo-950/10` (soft bg) | `bg-[#f1f5ff]/40` (pale-blue) | Cohere pale-blue wash |
| `border-indigo-200`, `border-indigo-100` | `border-[#e5e7eb]` (border-light) | Cohere border token |
| `border-indigo-900/20`, `border-indigo-900/40` | `border-[rgba(24,99,220,0.15)]` | dark mode action-blue translucent |
| `ring-indigo-400` (focus) | `ring-[#4c6ee6]` (focus-blue) | Cohere focus ring token |
| `hover:text-indigo-600` | `hover:text-[#1863dc]` | tutarlılık |
| `hover:border-indigo-200` | `hover:border-[#e5e7eb]` | tutarlılık |

### Gradient Kaldırma
| Eski | Yeni |
|---|---|
| `bg-gradient-to-br from-indigo-500 to-blue-600 dark:from-indigo-600 dark:to-blue-700` | `bg-primary text-primary-foreground` |
| `bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700` | `btn-pill-primary` |
| `bg-gradient-to-r from-indigo-50/60 to-transparent dark:from-indigo-950/20` | `bg-[#f1f5ff]/60 dark:bg-[#071829]/20` |

## Faz X Doğrulama
- [ ] `npx tsc --noEmit` → 0 hata
- [ ] Sayfada renk tutarlılığı görsel kontrol
- [ ] Tüm `text-indigo`, `bg-indigo`, `border-indigo` temizlendi
