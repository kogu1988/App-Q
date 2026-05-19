# Local Zero-Cost Plan

This note summarizes the second planning report and adapts it into App-Q implementation decisions.

## Core Assumption

App-Q can be built as a zero-cost local MVP on a gaming PC or Apple Silicon machine by accepting sequential processing instead of enterprise-grade concurrency.

Enterprise systems may interview many synthetic personas in parallel. The local MVP should interview personas one by one, persist state, release memory where possible, and continue with the next persona.

## Local Tech Stack

- Model server: Ollama
- Consumer/e-commerce model direction: Trendyol LLM GGUF, if license and hardware checks pass
- B2B/general model direction: Qwen 2.5 family GGUF, if license and hardware checks pass
- Persona memory: SQLite first, optional ChromaDB later
- Orchestration: plain Python
- UI direction: Streamlit for the first local operator UI
- API direction: FastAPI remains useful as a clean internal service boundary

## Hardware Strategy

Default local mode:

- one model loaded at a time
- sequential persona interviews
- short pauses between interviews if GPU pressure appears
- small panel first, larger panel as a batch job
- model adapter boundary retained so Ollama can be swapped later

## MVP Implementation Implications

The next MVP should prioritize:

- Ollama provider adapter
- `sentetik-tr-motor` model configuration notes
- local persona dictionary tuned for Turkish segments
- sequential interview runner
- memory store abstraction
- hidden judge pass for anti-sycophancy
- Streamlit operator UI
- Markdown/PDF report export

## Memory Design

Use a practical "poor man's ACT-R" before overengineering:

1. Store every question and answer per persona.
2. On a new question, retrieve only the most relevant prior turns.
3. Add a short consistency note to the prompt.
4. Keep persona identity and knowledge boundary fixed.

SQLite can support the first version. ChromaDB can be added when semantic retrieval is required.

## Anti-Sycophancy Design

Use dual-pass generation:

1. Persona generates an answer.
2. A hidden judge checks whether the answer violates the persona stance.
3. If the answer is too agreeable or generic, regenerate with a stricter prompt.

The judge should not force negativity. It should enforce persona consistency and useful disagreement.

## Commercial Path

The most realistic first business model is productized service, not SaaS self-serve:

- customer sends concept, page, Figma summary, or campaign brief
- operator runs App-Q locally
- report is delivered within 24 to 48 hours
- positioning emphasizes private, local, offline-capable research workflow

Avoid absolute legal claims such as "100% KVKK compliant" unless reviewed by counsel. Safer wording:

"Local/offline-capable architecture designed to reduce cross-border data transfer and third-party API exposure."

## Important Corrections

- Offline operation can reduce data-transfer risk, but it does not automatically guarantee KVKK compliance.
- Trendyol LLM may be strong for e-commerce, but B2B use should be routed to a more general model.
- GGUF availability, license, and commercial terms must be verified before model download or commercial use.
- Visual UX testing should start with text descriptions; vision models can be added later if hardware allows.
