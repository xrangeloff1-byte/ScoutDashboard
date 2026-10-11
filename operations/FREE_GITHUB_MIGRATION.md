# Scout free GitHub Actions migration

**Scheduled job:** Actions → Scout Automatic Draft Preparation (weekdays 15:30 UTC). Other Scout workflows are manual-only. GitHub schedules may be delayed or skipped.

**Free discovery:** OpenStreetMap business listings via the community Overpass API. One bounded Omaha/Lincoln query per run, at most 25 new leads. Attribution: © OpenStreetMap contributors. Service availability and usage limits are not guaranteed; existing results are preserved on temporary failures.

**Website review:** Existing Scout qualification and inspection scripts analyze public business websites. Findings are preliminary and must be verified before outreach.

**Gmail drafts (no sending):** Existing operations/scout_autodrafts.py is retained. With GitHub Secrets GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN and repository Variables SCOUT_SENDER_NAME, SCOUT_BUSINESS_CONTACT, the workflow may create up to five Gmail drafts per run. Without OAuth configuration, only local review files are prepared. No messages are sent.

**Cost and privacy:** No paid Serper API required. Standard GitHub Actions runners for public repositories are currently free under GitHub terms; Overpass is a free community service subject to fair-use and outages. Do not commit credentials. This is a public repository; be careful with logs and artifact contents. Artifacts expire after seven days.

**Cloudflare:** This pull request does not delete or disable the old Cloudflare Worker. After the GitHub job is verified, remove the Cloudflare cron trigger to avoid duplicate/failing runs.

**Beatrice:** Untouched.

## Verification after merge
1. Open Actions → Scout Automatic Draft Preparation → Run workflow.
2. Inspect the run log and the uploaded prospect/draft-review files.
3. If Gmail OAuth is configured, check that the expected Gmail drafts exist and no emails were sent.
4. Disable the old Cloudflare cron only after the new workflow passes.

This migration does not authorize sending client outreach.
