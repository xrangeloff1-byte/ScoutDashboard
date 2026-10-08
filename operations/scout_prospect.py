"""Scout prospect discovery: public search snippets -> review-only lead queue.
No emails are sent. Requires SERPER_API_KEY for live discovery.
"""
import csv
import datetime as dt
import json
import os
import pathlib
import re
import urllib.request
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "prospects.csv"
REPORT = ROOT / "prospect_report.md"
QUERIES = [
    "Omaha Nebraska independent roofing contractor website",
    "Omaha Nebraska independent landscaping business website",
    "Omaha Nebraska local plumbing company website",
    "Lincoln Nebraska small HVAC contractor website",
]
BLOCKED = {"facebook.com", "instagram.com", "yelp.com", "angi.com", "bbb.org",
           "yellowpages.com", "linkedin.com", "mapquest.com", "homeadvisor.com"}

def domain(url):
    host = (urlparse(url).hostname or "").lower()
    return host.removeprefix("www.")

def candidates(payload, query):
    for item in payload.get("organic", []):
        url = item.get("link", "")
        host = domain(url)
        if not host or any(host == x or host.endswith("." + x) for x in BLOCKED):
            continue
        if not url.startswith(("http://", "https://")):
            continue
        yield {
            "business": item.get("title", "").strip()[:140],
            "website": url,
            "domain": host,
            "source_query": query,
            "public_evidence": item.get("snippet", "").strip()[:400],
            "potential_service": "Website review / mobile usability / lead capture",
            "verification": "UNVERIFIED - inspect website before alleging any issue",
            "contact_email": "",
            "outreach_status": "RESEARCH_ONLY",
            "review_status": "PENDING",
        }

def search(query, key):
    body = json.dumps({"q": query, "num": 10}).encode()
    request = urllib.request.Request(
        "https://google.serper.dev/search", data=body,
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)

def main():
    key = os.environ.get("SERPER_API_KEY", "").strip()
    existing = {}
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("domain"):
                    existing[row["domain"]] = row
    new = 0
    errors = []
    if key:
        for query in QUERIES:
            try:
                for row in candidates(search(query, key), query):
                    if row["domain"] not in existing:
                        existing[row["domain"]] = row
                        new += 1
            except Exception as exc:
                errors.append(f"{query}: {type(exc).__name__}: {exc}")
    fields = ["business", "website", "domain", "source_query", "public_evidence",
              "potential_service", "verification", "contact_email",
              "outreach_status", "review_status"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing.values())
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Scout Prospect Report", "", f"Generated: {today}",
             f"Prospects in queue: {len(existing)}", f"New this run: {new}",
             f"Search configured: {'yes' if key else 'no - add SERPER_API_KEY'}",
             "", "## Review queue", "",
             "These are possible leads, not verified website problems. No outreach sent.", ""]
    for row in list(existing.values())[:30]:
        lines.append(f"- {row['business']} — {row['website']} — {row['review_status']}")
    if errors:
        lines.extend(["", "## Search errors", *["- " + e for e in errors]])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scout: {len(existing)} prospects, {new} new; {len(errors)} search errors")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
