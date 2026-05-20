# App-Q Architecture

## Design Principles

- Model-agnostic: the research workflow must work before any specific LLM is attached.
- Isolated personas: each persona receives only the brief and its own memory.
- Evidence-first: every finding should point to interview evidence.
- Defensive research: the system should resist sycophancy and avoid overconfidence.
- Local-first: sensitive customer inputs should stay local by default.

## Components

### API

FastAPI backend exposing research workflow endpoints.

Planned endpoints:

- `GET /health`
- `POST /research/run`
- `POST /brief/questions`
- `POST /personas/generate`
- `POST /interviews/run`
- `POST /reports/generate`

### Research Engine

The research engine owns:

- brief parsing
- clarifying question generation
- persona panel generation
- stance distribution
- interview orchestration
- synthesis and report generation

### Model Provider

The provider interface hides the selected model implementation.

Initial providers:

- `mock`: deterministic local provider for pipeline testing
- `ollama`: single local Ollama model
- `ollama-router`: two-model local router; B2C/e-commerce prompts use `app-q-trendyol`, general B2B/pricing/KVKK/synthesis prompts use `app-q-kizagan-e4b`

Future providers:

- `transformers`: local Hugging Face model
- `llama_cpp`: local GGUF model
- `vllm`: GPU server
- `http`: private inference endpoint

## Persona Panel

Default stance distribution:

- Champion: 15%
- Pragmatist: 35%
- Skeptic: 20%
- Blocker: 15%
- Observer: 15%

Small MVP panels will approximate this distribution with 5 to 12 personas.

## Quality Controls

- Ask clarifying questions before research if brief is incomplete.
- Keep each persona context isolated.
- Require personas to state uncertainty when outside their knowledge boundary.
- Cap confidence language in generated reports.
- Include limitations and suggested real-world validation.

## Local MVP Mode

The zero-cost local version should use sequential processing. Personas are interviewed one at a time, and the system stores each interview before moving to the next persona. This reduces VRAM pressure and makes the project feasible on hobbyist hardware.

The first local UI can be Streamlit, while FastAPI remains the internal service boundary. This keeps the operator workflow simple without locking the project into a single interface.

## Learning Loop

Production data should flow into a controlled feedback store only when approved. Raw customer briefs must not be treated as training data by default.

Safe path:

1. Collect explicit feedback on report usefulness.
2. Redact sensitive details.
3. Add approved examples to evals.
4. Use evals to compare local models and prompt changes.
5. Prepare LoRA/QLoRA fine-tuning only after enough clean examples exist.
