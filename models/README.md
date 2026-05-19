# Model Strategy

Do not download large models until the MVP pipeline is working with the `mock` provider.

## Candidate Direction

Trendyol LLM candidates are relevant because App-Q targets Turkish market and e-commerce research. Before use, verify:

- license
- commercial usage terms
- hardware requirements
- context length
- quantized availability
- inference speed
- Turkish reasoning quality
- Turkish naturalness in client-facing outputs
- persona consistency in longer interviews
- quality of skeptical and price-sensitive answers

## Current Local Hardware Target

Development target:

- RTX 4060
- Intel i7
- 32 GB RAM

This is suitable for the App-Q local MVP if persona interviews run sequentially. Prefer 7B/8B quantized models first. Avoid loading multiple models at the same time.

## Local Runtime Options

- `transformers`: easiest for experimentation, heavier dependency footprint.
- `llama.cpp` / GGUF: practical for quantized local inference.
- `Ollama`: pragmatic local API wrapper for GGUF-based models.
- `vLLM`: best for GPU server throughput.
- private HTTP endpoint: cleanest integration once hosting is decided.

## Suggested Local Sequence

1. Keep using `mock` until the workflow is stable.
2. Add an `ollama` provider adapter.
3. Test with a small local model.
4. Verify Trendyol LLM GGUF availability, license, and hardware fit.
5. Create a local model alias such as `sentetik-tr-motor`.
6. Route e-commerce research to Trendyol-oriented models and B2B/SaaS research to a more general model.

## Ollama Mode

Set:

```powershell
$env:APP_MODEL_PROVIDER="ollama"
$env:APP_MODEL_ID="sentetik-tr-motor"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
```

Check connectivity:

```powershell
.\.venv\Scripts\python.exe scripts\check_ollama.py
```

If Ollama is not running or the model alias does not exist, App-Q should fail with a readable provider error instead of crashing the UI.

## Turkish Quality Gate

Before a model becomes the default provider, run `data/evals/turkish_quality_eval.jsonl` manually and score each answer.

Minimum acceptable result:

- no broken Turkish
- no generic assistant tone
- clear persona stance
- concrete Turkey-market details
- useful objection or recommendation

Models that are fluent but too agreeable should not be used without the judge pass.

## Model Provider Boundary

The application should call `ResearchModel.generate(...)` and avoid provider-specific calls outside the model adapter.
