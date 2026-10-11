# Scout free GitHub Actions migration

Use **Actions → Scout Free Research (review only) → Run workflow** to test.
A weekday schedule runs at 14:15 UTC. GitHub schedules may be delayed or skipped.

The job makes at most one small OpenStreetMap Overpass query per run, inspects candidate
business sites, and uploads a research-only artifact. No paid search keys are needed.
Results may be empty or temporarily unavailable. Respect OSM/Overpass fair-use limits.
No emails are sent, no Gmail drafts are created, and no repository secrets are required.

Old Serper/Gmail draft workflows are manual-only to prevent redundant scheduled runs.
Cloudflare is **not** automatically disabled: after a successful GitHub run, manually
remove its cron trigger to stop the old failing hourly executions. Do not delete
Cloudflare until you've verified the new workflow. This change never touches Beatrice.

Free use depends on GitHub's published limits and public Overpass service availability.
