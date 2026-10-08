# Scout Prospecting V1

The workflow runs on weekdays and manually via GitHub Actions > Scout Prospect Research > Run workflow.
Set repository secret `SERPER_API_KEY` to enable live Serper search. If unset, a zero-lead report is generated; no fabricated prospects.
After the run, download the `scout-prospect-review` artifact to see `prospects.csv` and `prospect_report.md`.
Prospects are only search-result candidates. Review their sites, validate the actual problem, and confirm service feasibility before offering anything.
No automated website scraping, contact harvesting, or outbound emails. Gmail connected to ChatGPT is not a GitHub Actions credential.
Results are artifacts, not committed into this public repository. Each run starts a new queue; retain reviewed leads in a private CRM.
For production, add approved business email OAuth, suppression lists, rate limits, human approval, and private persistent CRM storage.
Beatrice is not used or modified.
