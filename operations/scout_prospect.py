"""Scout free prospect research from OpenStreetMap community data.
Review-only. No paid search, email sending, or Gmail operations.
Overpass is a public, best-effort service: honor its usage policy and failures.
"""
import csv
import datetime as dt
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "prospects.csv"
REPORT = ROOT / "prospect_report.md"
FIELDS = ["business","website","domain","source_query","public_evidence","potential_service","verification","contact_email","outreach_status","review_status"]
BLOCKED = {"facebook.com","instagram.com","yelp.com","angi.com","bbb.org","yellowpages.com","linkedin.com","mapquest.com","homeadvisor.com","houzz.com","thumbtack.com"}
# Small, bounded query for Omaha/Lincoln-area service businesses.
OVERPASS_ENDPOINTS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")
QUERY = """[out:json][timeout:20];
(
 nwr["craft"~"^(roofer|plumber|hvac|carpenter|builder|landscaper|electrician)$"](around:20000,41.2565,-95.9345);
 nwr["craft"~"^(roofer|plumber|hvac|carpenter|builder|landscaper|electrician)$"](around:12000,40.8136,-96.7026);
);
out tags 80;"""

def normalize_website(raw):
    raw = (raw or "").strip()
    if not raw or len(raw) > 400: return None
    if not re.match(r"^https?://", raw, re.I): raw = "https://" + raw
    p = urllib.parse.urlparse(raw)
    host = (p.hostname or "").lower().removeprefix("www.")
    if p.scheme != "https" or not host or not re.fullmatch(r"[a-z0-9.-]+", host):
        return None
    if p.username or p.password or p.port not in (None,443): return None
    if not "." in host or any(host == x or host.endswith("." + x) for x in BLOCKED): return None
    return "https://" + host + "/", host

def discover():
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    payload = None
    failures = []
    for endpoint in OVERPASS_ENDPOINTS:
        req = urllib.request.Request(endpoint, data=data, headers={
            "User-Agent": "ScoutDashboardResearch/1.0 (review-only; GitHub Actions)",
            "Accept": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                payload = json.load(response)
            break
        except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
            failures.append(endpoint + ": " + type(exc).__name__ + " " + str(exc)[:120])
    if payload is None:
        raise RuntimeError("All free Overpass endpoints failed: " + "; ".join(failures))
    for item in payload.get("elements", []):
        tags = item.get("tags") or {}
        name = (tags.get("name") or "").strip()
        website = normalize_website(tags.get("website") or tags.get("contact:website"))
        if not name or not website: continue
        url, host = website
        yield {"business":name[:140], "website":url, "domain":host,
               "source_query":"OpenStreetMap public business listing",
               "public_evidence":"OSM object "+str(item.get("type",""))+"/"+str(item.get("id",""))+
                                 "; craft="+str(tags.get("craft",""))[:40],
               "potential_service":"Website and inquiry-path review",
               "verification":"UNVERIFIED - verify business and website independently",
               "contact_email":"", "outreach_status":"RESEARCH_ONLY", "review_status":"PENDING"}

def main():
    existing = {}
    if OUT.exists():
        with OUT.open(newline="",encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("domain"): existing[row["domain"]] = row
    new = 0
    errors = []
    try:
        for row in discover():
            if row["domain"] not in existing and new < 25:
                existing[row["domain"]] = row
                new += 1
    except (OSError, ValueError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        errors.append(type(exc).__name__ + ": " + str(exc)[:180])
    with OUT.open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing.values())
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Scout Free Prospect Report", "", "Generated: "+now,
             "Source: OpenStreetMap via public Overpass API (attribution: © OpenStreetMap contributors)",
             "Existing and new leads are unverified; human review required.",
             "Prospects: "+str(len(existing)), "New this run: "+str(new),
             "Emails sent: 0", "", "## Review queue", ""]
    lines += ["- "+r.get("business","")+" — "+r.get("website","") for r in list(existing.values())[:30]]
    if errors:
        lines += ["", "## Discovery warning (existing leads preserved)", *["- "+e for e in errors]]
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("Scout free research: "+str(len(existing))+" leads; "+str(new)+" new; "+str(len(errors))+" warnings")
    if errors:
        print("DISCOVERY ERROR: " + "; ".join(errors))
        raise SystemExit(1)
    if not existing:
        print("DISCOVERY EMPTY: no website-bearing businesses found; inspect source and filters")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
