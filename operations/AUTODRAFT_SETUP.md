# Scout V3 — hands-off research to Gmail drafts (never sends)

Workflow: GitHub Actions > **Scout Automatic Draft Preparation**. It runs on weekdays and can also be triggered manually. It discovers businesses, inspects homepage HTML, ranks candidates, looks only for explicit public `mailto:` links with email domains matching the business website, and attempts to create **up to five unsent Gmail drafts** per run.

## Configuration

1. Existing GitHub Actions secret: `SERPER_API_KEY`.
2. Create a Google Cloud project, enable Gmail API, configure OAuth consent, and obtain an **offline OAuth refresh token** authorized for `https://www.googleapis.com/auth/gmail.compose`. Use a secure OAuth consent flow. Never paste credentials in issues, commits, chat or workflow logs.
3. Add GitHub Actions repository secrets `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, and `GMAIL_REFRESH_TOKEN`. The ChatGPT Gmail connection is independent of GitHub Actions and cannot be reused as a token.
4. Add GitHub Actions repository **variables** `SCOUT_SENDER_NAME` (actual approved human sender identity) and `SCOUT_BUSINESS_CONTACT` (accurate business contact information including postal address where required). These must be truthful.
5. Run workflow and check `scout-autodrafts-review` artifact; open Gmail Drafts to review/edit and manually press Send.

Without OAuth and sender configuration, the workflow still researches contacts and reports that drafts are pending; it **does not** silently pretend to create Gmail drafts.

**Caution:** Drafts are created again on each run for eligible businesses. Do not schedule with OAuth enabled until a persistent deduplication and opt-out mechanism is added. The schedule is active but only generates Gmail drafts after secrets and variables are supplied. For initial setup, leave `GMAIL_REFRESH_TOKEN` unset until duplicate suppression is built.

Public mailto addresses can still be inappropriate for solicitation. Review recipient relevance, site findings, anti-spam law, opt-outs and any restrictions. No sending is implemented, and no fully autonomous outreach is authorized by this workflow.
