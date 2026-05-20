# App-Q

Codename: App-Q

App-Q is a Turkey-focused synthetic persona research MVP. It is designed to take a product or market research brief, ask clarifying questions, create isolated personas, simulate structured interviews, and produce evidence-linked market insights.

This repository is intentionally model-agnostic. The first milestone runs with a deterministic mock provider so the research workflow can be tested before downloading or hosting a large language model.

## Goals

- Build an Articos-like research flow for Turkish market research.
- Keep model, data, logs, and generated reports isolated under this project.
- Support local or private model hosting later, including Trendyol LLM candidates.
- Avoid positioning synthetic research as a replacement for real human validation.

## Initial Architecture

```text
apps/
  api/                  FastAPI backend
  web/                  Frontend placeholder
packages/
  research_engine/      Persona, interview, synthesis workflow
  prompts/              Prompt templates and research rules
data/
  samples/              Example briefs
  outputs/              Generated reports
  evals/                Quality test cases
docs/
  product-plan.md
  architecture.md
  kvkk-notes.md
models/
  README.md             Model strategy and download notes
```

## First Milestone

1. Create a working backend API.
2. Run a sample research project end-to-end using the mock model.
3. Verify the output structure: personas, interview evidence, findings, risks, price notes, and recommendations.
4. Add a real model provider only after the workflow is stable.

## Current Setup

The project currently has:

- isolated Python environment: `.venv`
- FastAPI backend skeleton
- deterministic mock model provider
- sample brief: `data/samples/first-brief.json`
- generated sample report: `data/outputs/sample-report.json`

## Run Locally

From `C:\Projeler\App-Q`:

```powershell
.\.venv\Scripts\python.exe scripts\run_sample.py
```

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Start the local operator UI:

```powershell
.\.venv\Scripts\python.exe -m streamlit run apps\operator\streamlit_app.py
```

Operator UI outputs are written to:

```text
data/outputs/operator-report.md
data/outputs/operator-report.json
```

Use Ollama instead of the mock model:

```powershell
$env:APP_MODEL_PROVIDER="ollama"
$env:APP_MODEL_ID="sentetik-tr-motor"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
.\.venv\Scripts\python.exe scripts\check_ollama.py
.\.venv\Scripts\python.exe -m streamlit run apps\operator\streamlit_app.py
```

Run Turkish model quality evals:

```powershell
.\.venv\Scripts\python.exe scripts\run_turkish_eval.py
```

Eval results are written to:

```text
data/outputs/evals/{model_alias}.jsonl
```

## Safety Positioning

App-Q outputs directional hypotheses, not statistically representative market research. High-risk decisions should be validated with real users, sales data, or field research.
