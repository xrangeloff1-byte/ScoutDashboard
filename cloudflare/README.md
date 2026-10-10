# Scout Cloudflare monitor — deployment

This is a **read-only monitor**, not a Python lead-generation engine. It checks GitHub Actions in **ScoutDashboard** (not Beatrice) and avoids the broken `SCOUT_V3_RANKED_REPORT.md` request. It does not send emails, make sales, or modify trading code.

## Deploy on Cloudflare (one-time)

1. Open your existing Cloudflare Worker **scout-automation**, click **Edit code**.
2. Replace `worker.js` with the contents of `cloudflare/worker.js` from this repository. Deploy.
3. Keep the hourly Cron Trigger (`0 * * * *`). The `scheduled` handler logs each check.
4. Visit `https://<your-worker>.workers.dev/status`. Expect JSON with three workflow statuses, or an explicit GitHub error.
5. For the public ScoutDashboard repository, no GitHub token is required. If you add one, name the Cloudflare secret `GITHUB_TOKEN`; never paste it into code or commit it.

The workflow runs can be inspected directly in GitHub Actions. Cloudflare's free tier limits and GitHub Actions usage limits still apply. The existing GitHub Actions Python workflows continue to run separately. No Beatrice files are changed.

## Important
- Do not use the Beatrice-only path `scout/SCOUT_V3_RANKED_REPORT.md` in this Worker. That file exists in **PybotBeatrice**, not ScoutDashboard.
- The earlier 404 occurred while fetching the V3 report; a root `/status` HTTP 200 alone did not demonstrate successful monitoring.
- This migration only moves monitoring to Cloudflare; moving Python research and Gmail draft preparation requires a separate implementation and credentials. Outbound messages remain disabled.
