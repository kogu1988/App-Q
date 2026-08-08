# Model Strategy

Clarere uses **DeepSeek API** as the primary LLM provider via OpenAI-compatible client.

## Current Setup

| Rolle | Model | Effort |
|-------|-------|--------|
| **Intake (Defne)** | `deepseek-v4-flash` | Default |
| **Interview (Persona)** | `deepseek-v4-flash` | Default |
| **Synthesis (Report)** | `deepseek-v4-pro` | High (thinking mode) |

## Environment

```env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro
```

## Key Features Enabled

- **Thinking Mode:** Active by default on both models. Pro model always reasons at "high" effort or above.
- **user_id Isolation:** Each request carries a sanitized user ID for KVCache separation and content safety.
- **Context Caching:** DeepSeek's disk cache automatically caches common prompt prefixes — subsequent similar requests are faster and cheaper.
- **JSON Output:** Used in batch interviews to structure persona answers.
- **Rate Limits:** Flash = 2500 concurrent, Pro = 500 concurrent. Well above our needs (max 6 concurrent requests per research).

## Provider Architecture

```
get_model_provider("flash")  → DeepSeekResearchModel(deepseek-v4-flash)
get_model_provider("pro")    → DeepSeekResearchModel(deepseek-v4-pro)
get_model_provider("intake") → DeepSeekResearchModel(deepseek-v4-flash)
```

The factory function (`providers.py`) maps aliases to models. New model IDs can be set via environment variables without code changes.
