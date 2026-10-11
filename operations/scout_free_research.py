"""Free, bounded OpenStreetMap business discovery. Research only; no outreach."""
import csv
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.request
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "prospects.csv"
REPORT = ROOT / "prospect_report.md"
FIELDS = ["business","website","domain","source_query","public_evidence",
          "potential_service","verification","contact_email","outreach_status","review_status"]
# One small city/category request per run. No paid search service or account.
LOCATIONS = [
    ("Omaha", 41.2565, -95.9345),
    ("Lincoln", 40.8136, -96.7026),
]
CATEGORIES = ["roofing", "plumber", "hvac", "landscaper", "construction"]
BLOCKED = {"facebook.com","instagram.com","yelp.com","linkedin.com","google.com"}
def safe_site(raw):
    if not raw: return ""
    if not raw.startswith(("https://","http://")): raw = "https://" + raw
    p = urlparse(raw)
    host = (p.hostname or "").lower().removeprefix("www.")
    if p.scheme != "https" or not host or p.username or p.password or p.port not in (None,443):
        return ""
    if not ("." in host and all(c.isalnum() or c in ".-" for c in host)): return ""
    if any(host == b or host.endswith("."+b) for b in BLOCKED): return ""
    return "https://" + host + "/"
def discover(city, lat, lon, category):
    # Public OSM Overpass data; minimal bounding radius and request count.
    query = f'[out:json][timeout:20];nwr(around:6000,{lat},{lon})["name"]["website"];out tags 35;'
    req = urllib.request.Request(
        "https://overpass.kumi.systems/api/interpreter",
        data=urllib.parse.urlencode({"data":query}).encode(),
        headers={"User-Agent":"ScoutDashboardResearch/1.0 (noncommercial review-only; GitHub Actions)"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    rows = []
    for item in payload.get("elements", []):
        tags = item.get("tags", {})
        label = " ".join((tags.get("name") or "").split())[:140]
        text = " ".join(str(tags.get(k,"")) for k in ("craft","shop","office","name")).lower()
        match = {
            "roofing": ("roof",),
            "plumber": ("plumb",),
            "hvac": ("hvac","heating","cooling"),
            "landscaper": ("landscap","garden"),
            "construction": ("construct","builder","remodel"),
        }[category]
        if not label or not any(x in text for x in match): continue
        site = safe_site(tags.get("website") or tags.get("contact:website") or "")
        if not site: continue
        rows.append({"business":label,"website":site,"domain":urlparse(site).hostname,
                     "source_query":f"OpenStreetMap {city} {category}",
                     "public_evidence":f"OSM element {item.get('type')}/{item.get('id')} has name and website tags; business identity unverified",
                     "potential_service":"Website review / mobile usability / lead capture",
                     "verification":"UNVERIFIED - human review required",
                     "contact_email":"","outreach_status":"RESEARCH_ONLY","review_status":"PENDING"})
    return rows
def main():
    existing = {}
    if OUT.exists():
        with OUT.open(newline="",encoding="utf-8") as f:
            existing = {r["domain"]:r for r in csv.DictReader(f) if r.get("domain")}
    # Rotate deterministically each UTC day, limiting free public endpoint use.
    index = dt.datetime.now(dt.timezone.utc).date().toordinal()
    city,lat,lon = LOCATIONS[index % len(LOCATIONS)]
    category = CATEGORIES[(index // len(LOCATIONS)) % len(CATEGORIES)]
    errors = []
    new = 0
    try:
        for row in discover(city,lat,lon,category):
            if row["domain"] not in existing:
                existing[row["domain"]] = row
                new += 1
    except Exception as exc:
        errors.append(f"Public data unavailable: {type(exc).__name__}: {exc}")
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore")
        w.writeheader()
        w.writerows(list(existing.values())[:200])
    lines = ["# Scout Free Research Report","",
             f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
             f"Source: OpenStreetMap / Overpass; {city} {category}",
             f"Prospects: {len(existing)}; new this run: {new}",
             "Emails sent: 0; Gmail drafts created: 0; paid search calls: 0","",
             "OSM records are unverified candidate businesses, not verified website defects.",""]
    lines += [f"- {r['business']} — {r['website']} (review required)" for r in list(existing.values())[:30]]
    lines += ["", *errors]
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"Scout free research: {len(existing)} candidates, {new} new; {len(errors)} source errors")
    # A temporary public-data outage should be visible but must not cause expensive retries.
if __name__ == "__main__":
    main()
