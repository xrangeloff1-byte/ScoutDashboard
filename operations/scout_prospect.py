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
# Bounded, sequential geographic expansion; stop once enough website-bearing businesses are found.
OVERPASS_ENDPOINTS = ("https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter", "https://overpass.nchc.org.tw/api/interpreter")
CENTERS = ((41.2565,-95.9345), (40.8136,-96.7026)) # Omaha and Lincoln; configurable later
RADII_METERS = (10000, 25000, 50000, 100000)
MIN_RESULTS = 8
def query_for_radius(radius):
    clauses = "\n".join(' node["craft"~"^(roofer|plumber|hvac|carpenter|builder|landscaper|electrician)$"](around:%d,%s,%s);' % (radius,lat,lon) for lat,lon in CENTERS)
    return "[out:json][timeout:15];\n(\n"+clauses+"\n);\nout tags 80;"


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
    found = {}
    failures = []
    for radius in RADII_METERS:
        payload = None
        data = urllib.parse.urlencode({"data":query_for_radius(radius)}).encode()
        for endpoint in OVERPASS_ENDPOINTS:
            req = urllib.request.Request(endpoint, data=data, headers={
                "User-Agent":"ScoutDashboardResearch/1.0 (review-only; GitHub Actions)",
                "Accept":"application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=22) as response:
                    payload = json.load(response)
                break
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
                failures.append(endpoint+": "+type(exc).__name__+" "+str(exc)[:100])
        if payload is None:
            continue
        for item in payload.get("elements", []):
            tags = item.get("tags") or {}
            name = (tags.get("name") or "").strip()
            website = normalize_website(tags.get("website") or tags.get("contact:website"))
            if not name or not website: continue
            url, host = website
            if host not in found:
                found[host] = {"business":name[:140],"website":url,"domain":host,
                    "source_query":"OpenStreetMap public business listing; search radius "+str(radius//1000)+" km",
                    "public_evidence":"OSM object "+str(item.get("type",""))+"/"+str(item.get("id",""))+
                    "; craft="+str(tags.get("craft",""))[:40],
                    "potential_service":"Evidence-backed website review",
                    "verification":"UNVERIFIED - verify business and website independently",
                    "contact_email":"","outreach_status":"RESEARCH_ONLY","review_status":"PENDING"}
        print("Scout radius "+str(radius//1000)+" km: "+str(len(found))+" unique businesses")
        if len(found)>=MIN_RESULTS: break
    if not found and failures:
        raise RuntimeError("Public Overpass search returned no businesses; errors: "+"; ".join(failures[:3]))
    yield from found.values()

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
        print("DISCOVERY WARNING: " + "; ".join(errors))
        if existing:
            print("Using previously discovered businesses; no new search results this run.")
    if not existing:
        print("DISCOVERY EMPTY: no website-bearing businesses found; inbox will be empty, not populated with unverified contacts")

if __name__ == "__main__":
    main()
