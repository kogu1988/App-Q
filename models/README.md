# Model Strategy

Clarere uses **DeepSeek API** as the primary LLM provider via an OpenAI-compatible client.

## Current Setup

| Rol | Model | Effort |
|-----|-------|--------|
| **Intake (Defne)** | `deepseek-flash` | `low` |
| **Interview (Persona)** | `deepseek-flash` | `high` |
| **Synthesis (Report)** | `deepseek-v4-pro` | `max` |

> **Model adı notu:** Önerilen ad **`deepseek-flash`**. Eski `deepseek-v4-flash` adı hâlâ kabul edilir ama ilgili model emekliye ayrıldı; istekler DeepSeek-V4.1-Flash tarafından karşılanır ve Flash fiyatından faturalanır.

## Environment

```env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_FLASH_MODEL=deepseek-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro
DEEPSEEK_REASONING_EFFORT=high   # low | high | max (rol bazlı override edilir)
```

## Key Features Enabled

- **Thinking Mode:** Active by default on both models. `reasoning_content` ayrı alanda gelir.
- **Role-based reasoning effort:** intake/routing `low`, interview/follow-up `high`, synthesis `max`. Daha düşük effort = daha az reasoning token = daha düşük maliyet.
- **user_id Isolation:** Each request carries a sanitized user ID for KVCache separation and content safety.
- **Prefix Caching:** DeepSeek's disk cache automatically caches common prompt prefixes. Sistem promptunun sabit blokları **başta** tutulur (persona-özel bloklar sonda) → cache-hit olasılığı artar.
- **Content-hash LLM cache:** Aynı (model, system, prompt, format, max_tokens) çağrısı tekrar API'ye gitmez (`LLM_CACHE_*`).
- **JSON Output:** Used in batch interviews to structure persona answers.
- **Rate Limits:** Flash = 2500 concurrent, Pro = 500 concurrent. Well above our needs.

## Provider Architecture

```
get_model_provider("flash")  → DeepSeekResearchModel(deepseek-flash)
get_model_provider("pro")    → DeepSeekResearchModel(deepseek-v4-pro)
get_model_provider("intake") → DeepSeekResearchModel(deepseek-flash)
```

The factory function (`providers.py`) maps aliases to models and accepts `effort=`. New model IDs can be set via environment variables without code changes.

## Cost Levers

1. **Off-peak saatler:** 01:00–04:00 ve 06:00–10:00 UTC dışı fiyatlar yarı yarıyadır. Ağır/batch işleri off-peak'e planlayın.
2. **Prefix cache:** Sabit sistem promptu başta → cache-hit ~50x ucuz.
3. **reasoning_effort:** Rol bazlı düşük effort.
4. **Content-hash cache:** Tekrarlı çağrıları elemine eder.
