# Feedback Data

This directory is reserved for approved learning-loop data.

Do not store raw customer data here by default.

Use only:

- anonymized sessions
- customer-approved examples
- operator-labeled outputs
- real-world validation notes

Future schema:

```json
{
  "session_id": "local-id",
  "consent": "approved_for_eval",
  "brief_redacted": "...",
  "persona_id": "p3",
  "question": "...",
  "model_answer": "...",
  "operator_label": "useful|generic|wrong|unsafe",
  "operator_note": "...",
  "final_edited_answer": "...",
  "tags": ["pricing", "skeptic"]
}
```
