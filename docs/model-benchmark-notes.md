# Model Benchmark Notes

## Method

Each candidate is tested with `data/evals/turkish_quality_eval.jsonl` through Ollama and scored manually on:

- Turkish naturalness
- persona consistency
- insight usefulness
- specificity
- hallucination risk
- report readiness

SSD rule: keep at most two useful local models after testing.

## Candidates

| Alias | Source | License | Role | Decision | Notes |
| --- | --- | --- | --- | --- | --- |
| `app-q-trendyol` | `bartowski/Trendyol-LLM-8b-chat-v2.0-GGUF` | Llama 3 | E-commerce/B2C reference | keep | Useful B2C baseline. Faster and cleaner than large candidates, but weak for final synthesis and needs judge-pass cleanup. |
| `app-q-turkish-llama8b` | `ytu-ce-cosmos/Turkish-Llama-8b-Instruct-v0.1-GGUF` | Llama 3 | General Turkish persona/B2B | reject | Natural Turkish, but frequently slips into assistant/explainer mode and produced unrealistic agency pricing. Removed after eval. |
| `app-q-turkish-gemma9b` | `ytu-ce-cosmos/Turkish-Gemma-9b-T1-GGUF` | Gemma | Turkish natural language/reporting | maybe | Rich Turkish, but leaked long `<think>` blocks and took 40-56s per answer on RTX 4060. Not suitable for persona loops; may be retested later for slow offline report rewriting if chain-of-thought stripping is added. Removed after eval. |
| `app-q-kizagan-e4b` | `mradermacher/Kizagan-E4B-Turkish-Reasoning-Model-i1-GGUF` | Apache-2.0 | Reasoning / B2B / synthesis candidate | keep | Best current general candidate: 2.6-8.0s per answer, direct Turkish, good KVKK/fiyat/güven objections, no visible reasoning leakage in this run. |
| `app-q-llama3-tr-ft` | `matrixportalx/Llama3-8B-Instruct-Turkish-Finetuned-GGUF` | To verify | Turkish instruction fine-tune | reject | Fast enough, but had awkward Turkish, irrelevant e-commerce details in agency context, and fabricated quote-like evidence in synthesis. Removed after eval. |

## Current Default

Default routing recommendation:

- `app-q-trendyol` for e-commerce/B2C persona reactions.
- `app-q-kizagan-e4b` for B2B skepticism, pricing objections, KVKK/güven reasoning, and report synthesis.

`app-q-turkish-gemma9b` should not be the default model on RTX 4060, but it should not be forgotten. Its latency is acceptable only for low-volume, offline batch synthesis jobs where a 1-5 minute final report rewrite is tolerable and `<think>` leakage is filtered.

Both retained models were also run through `scripts/run_sample.py` successfully after the eval pass.
