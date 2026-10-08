"""Build five review-only outreach drafts from Scout's prospect CSV. No emails sent."""
import csv
from pathlib import Path
from urllib.parse import urlparse

root = Path(__file__).resolve().parent
source = root / "prospects.csv"
if not source.exists():
    raise SystemExit("Run prospect research or download prospects.csv first.")
with source.open(newline="", encoding="utf-8") as f:
    prospects = list(csv.DictReader(f))
seen, rows = set(), []
for lead in prospects:
    name = (lead.get("business") or "").strip()
    website = (lead.get("website") or "").strip()
    host = (urlparse(website).hostname or "").removeprefix("www.")
    if not name or not host or host in seen:
        continue
    seen.add(host)
    email = (lead.get("contact_email") or "").strip()
    rows.append({
        "business": name, "website": website, "contact_email": email,
        "status": "CONTACT_REVIEW_REQUIRED" if not email else "HUMAN_REVIEW_REQUIRED",
        "subject": f"Website inquiry experience for {name[:60]}",
        "draft": (f"Hello {name} team,\n\nI work with service businesses to make their "
                  "websites easier to use and improve how customers request quotes. "
                  "Would you be open to a brief, no-obligation review of your mobile "
                  "website and inquiry experience? I'd share specific findings before "
                  "proposing any changes.\n\nBest,\nScout"),
    })
    if len(rows) == 5:
        break
with (root / "outreach_review.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["business", "website", "contact_email", "status", "subject", "draft"])
    writer.writeheader()
    writer.writerows(rows)
(root / "outreach_report.md").write_text(
    f"# Scout Outreach Review\n\nProspects in source: {len(prospects)}\n"
    f"Offline drafts prepared: {len(rows)}\nEmails sent: 0\n"
    "No website issues or contact addresses have been independently verified.\n",
    encoding="utf-8")
print(f"Scout: {len(rows)} offline drafts created; 0 emails sent")
