# KVKK and Data Notes

This is not legal advice. App-Q should be reviewed by qualified counsel before commercial launch.

## Product Requirements

- Keep customer briefs and outputs local by default.
- Do not send prompts to external APIs unless explicitly configured.
- Do not log prompts or outputs by default.
- Keep `.env` out of version control.
- Separate sample data from customer data.
- Add deletion/export controls before multi-user use.

## Market Advantage

For Turkish B2B customers, data residency can be a major differentiator. Banks, telecoms, holdings, and regulated businesses may avoid foreign LLM APIs for product concepts, pricing strategy, or confidential research data.

## Training Data Rule

Avoid unauthorized scraping of social media, complaints, forums, or copyrighted commercial content. Prefer:

- licensed datasets
- first-party customer-approved examples
- zero-party research inputs
- synthetic augmentation based on allowed seed data

## Research Disclaimer

Synthetic personas can produce useful directional insight, but they do not experience real emotion, context, purchasing friction, or social pressure. App-Q reports should clearly recommend real-world validation for high-stakes decisions.
