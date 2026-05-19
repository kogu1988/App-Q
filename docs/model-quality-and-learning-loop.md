# Model Quality and Learning Loop

App-Q has two non-negotiable model requirements:

1. Turkish output quality must be strong enough for professional market research reports.
2. The product must be able to improve from real usage data after launch.

## Turkish Quality Requirements

The model must produce Turkish that is:

- natural, not translation-like
- specific to Turkey's market context
- capable of e-commerce and B2B vocabulary
- able to express skepticism, price sensitivity, and practical objections
- consistent across long multi-turn persona interviews
- suitable for client-facing reports after light editing

## Model Selection Criteria

Candidate models should be evaluated on:

- Turkish fluency
- Turkish consumer behavior realism
- e-commerce vocabulary
- B2B/SaaS reasoning
- resistance to sycophancy
- ability to follow persona constraints
- speed on RTX 4060 class hardware
- GGUF/quantized availability
- license and commercial usage terms

## Evaluation Set

App-Q should maintain a small Turkish eval set before any model is adopted.

Minimum eval categories:

- e-commerce checkout objection
- price/package sensitivity
- marketplace seller workflow
- agency pitch research
- B2B SaaS positioning
- KVKK/privacy concern
- skeptical persona pushback
- report synthesis from persona quotes

Each model run should be manually scored from 1 to 5 on:

- Turkish naturalness
- persona consistency
- insight usefulness
- specificity
- hallucination risk
- report-readiness

Run the eval set with:

```powershell
.\.venv\Scripts\python.exe scripts\run_turkish_eval.py
```

The script writes JSONL results to `data/outputs/turkish-eval-results.jsonl`. Manual scores should be filled after reviewing the answers.

## Learning Loop After Launch

Production usage can improve App-Q, but raw customer data must not be directly used for training by default.

Recommended loop:

1. Capture customer-approved research sessions.
2. Remove or mask sensitive commercial information.
3. Store brief, persona outputs, report findings, and user feedback separately.
4. Ask the operator or customer to mark useful, weak, wrong, or generic findings.
5. Convert high-quality examples into an internal eval set first.
6. Only after enough approved data exists, prepare a fine-tuning dataset.

## Feedback Data Types

Useful feedback signals:

- finding marked useful
- finding marked generic
- finding marked wrong
- missing persona segment
- wrong tone
- poor Turkish wording
- unrealistic price assumption
- customer-edited final report section
- real-world validation result

## Fine-Tuning Readiness

Fine-tuning should wait until:

- model/provider baseline is stable
- at least 100 to 300 high-quality approved examples exist
- eval set can detect regression
- data consent and retention rules are defined
- outputs are anonymized or explicitly approved

Early improvement should rely on prompt, retrieval, persona templates, and evals before LoRA/QLoRA training.
