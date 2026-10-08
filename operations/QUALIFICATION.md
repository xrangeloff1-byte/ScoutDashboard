# Scout V2 — qualification and draft workflow

Use GitHub Actions > **Scout Research and Qualify** > **Run workflow** on `main`.
The workflow uses `SERPER_API_KEY`, discovers public business candidates, attempts a conservative HTML-only homepage inspection, scores preliminary metadata signals, and generates up to 10 unsent personalized outreach drafts.

Download the `scout-qualified-review` artifact for `qualified_leads.csv`, `qualification_report.md` and `outreach_drafts.md`.

**Important:** Missing metadata in fetched HTML is not proof of a problem. JavaScript-rendered sites and redirects may prevent inspection. Scores indicate research priority only. Independently verify any observation in a browser before telling a business about it.

No automated email sending, contact harvesting, or sales claims. A human must review leads, sender identity, deliverability, opt-outs and service feasibility. ChatGPT's Gmail connector does not give GitHub Actions permission to send mail.

This workflow is separate from Beatrice. It does not modify trading code or secrets.
