"""Evidence-based, review-only business outreach. Standard library only; never sends email."""
import csv
import html
import re
import ssl
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent
FIELDS = ["business","website","contact_email","contact_source","name_source","opportunity","evidence_url","evidence","status","subject","draft"]
AGENT = "ScoutResearch/3.0 (public business website review)"
NONCUSTOMERS = ("association","chamber of commerce","trade group","trade association","nonprofit","non-profit","directory","marketplace","business listing","find a contractor","best roofing","top roofing","national association")
BUSINESS_TERMS = ("roof","hvac","heating","cooling","plumb","restor","remodel","construction","contract","landscap","concrete","builder","mechanical","foundation")
def likely_customer(name, host):
    low = (name + " " + host).lower()
    return not any(x in low for x in NONCUSTOMERS) and any(x in low for x in BUSINESS_TERMS)

BLOCKED = {"yelp.com","angi.com","bbb.org","houzz.com","facebook.com","linkedin.com","yellowpages.com","mapquest.com","homeadvisor.com","chamberofcommerce.com","buildzoom.com","thumbtack.com","porch.com","expertise.com","threebestrated.com"}
GENERIC = {"home","homepage","welcome","contact us","about us","services","roofing","contractors","commercial roofing","roofing contractor"}
def blocked(host):
    return any(host == b or host.endswith("." + b) for b in BLOCKED)
def usable_name(name, host):
    n = clean_name(name)
    low = n.casefold().strip(" .!")
    if not n or low in GENERIC or len(n) < 4 or len(n) > 70: return False
    if any(word in low for word in ("top 10", "best companies", "near me", "directory", "reviews", "find a contractor")): return False
    return True

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = False
        self.titles = []
        self.headings = []
        self.heading = False
        self.links = []
        self.text = []
        self.forms = 0
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title": self.title = True
        if tag == "form": self.forms += 1
        if tag == "h1": self.heading = True
        if tag == "a" and d.get("href"): self.links.append(d["href"])
    def handle_endtag(self, tag):
        if tag == "title": self.title = False
        if tag == "h1": self.heading = False
    def handle_data(self, data):
        s = " ".join(data.split())
        if s:
            if self.title: self.titles.append(s)
            if self.heading: self.headings.append(s)
            self.text.append(s)
def fetch(url):
    p = urlparse(url)
    if p.scheme != "https" or not p.hostname or p.port not in (None, 443):
        raise ValueError("Only standard HTTPS websites allowed")
    req = urllib.request.Request(url, headers={"User-Agent":AGENT,"Accept":"text/html"})
    with urllib.request.urlopen(req, timeout=7, context=ssl.create_default_context()) as response:
        final = response.geturl()
        if urlparse(final).scheme != "https" or urlparse(final).hostname != p.hostname:
            raise ValueError("Cross-host redirect not accepted")
        if "text/html" not in response.headers.get("Content-Type","").lower():
            raise ValueError("Not an HTML page")
        raw = response.read(350000).decode("utf-8", errors="replace")
    page = Page()
    page.feed(raw)
    return page
def clean_name(s):
    s = re.split(r"\s+[|–—]\s+|\s+-\s+",s or "")[0]
    return " ".join(html.unescape(s).split())[:90]
def emails(page, host):
    found = []
    for link in page.links:
        if link.lower().startswith("mailto:"):
            email = link[7:].split("?")[0].strip().lower()
            if re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", email):
                found.append(email)
    return sorted(set(found), key=lambda e: (not e.endswith("@"+host), e))
def inspect(lead):
    url = (lead.get("website") or "").strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host or parsed.scheme != "https" or blocked(host): return None
    home = "https://" + host + "/"
    try:
        page = fetch(home)
    except (ValueError, OSError, urllib.error.URLError) as exc:
        return {"business":clean_name(lead.get("business")),"website":home,"contact_email":"","contact_source":"",
                "name_source":"","opportunity":"Manual website review","evidence_url":home,
                "evidence":f"Website unavailable for automated inspection: {type(exc).__name__}",
                "status":"MANUAL_VERIFICATION_REQUIRED","subject":"","draft":""}
    title = clean_name(" ".join(page.titles))
    h1 = clean_name(" ".join(page.headings))
    name = next((n for n in (h1, title) if usable_name(n, host) and likely_customer(n, host)), "")
    name_source = home if name else ""
    if not name:
        return {"business":clean_name(lead.get("business")),"website":home,"contact_email":"",
                "contact_source":"","name_source":"","opportunity":"Manual company verification",
                "evidence_url":home,"evidence":"No reliable company name detected on homepage",
                "status":"NAME_VERIFICATION_REQUIRED","subject":"","draft":""}
    contact = ""
    contact_source = ""
    for link in page.links:
        if link.lower().startswith("mailto:"):
            matches = emails(page, host)
            if matches:
                contact = matches[0]
                contact_source = home
                break
    contact_links = []
    for link in page.links:
        path = urlparse(link).path.lower()
        if "contact" in path or "about" in path:
            target = urljoin(home, link)
            if urlparse(target).hostname == host and target not in contact_links:
                contact_links.append(target)
    for target in contact_links[:2]:
        if contact: break
        try:
            sub = fetch(target)
            matches = emails(sub, host)
            if matches: contact, contact_source = matches[0], target
        except (ValueError, OSError, urllib.error.URLError):
            pass
    paths = [urlparse(x).path.lower() for x in page.links]
    has_contact = any("contact" in p or "quote" in p or "estimate" in p for p in paths)
    if not has_contact and page.forms == 0:
        opportunity = "Check visibility of quote and contact options"
        evidence = "No homepage HTML form or contact/quote/estimate link was detected; other inquiry options may exist."
        priority = 3
    elif page.forms:
        opportunity = "Review existing inquiry form for friction"
        evidence = f"Homepage HTML contains {page.forms} form element(s); no usability test has been performed."
        priority = 2
    else:
        opportunity = "Review existing contact and quote journey"
        evidence = "Homepage links to contact, quote, or estimate information; its usability has not been tested."
        priority = 1
    status = "HUMAN_REVIEW_REQUIRED" if contact and name_source != "Search result (unverified)" else "CONTACT_OR_NAME_REVIEW_REQUIRED"
    subject = f"Question about {name[:55]} website inquiries"
    draft = (f"Hello {name} team,\n\nI was looking at your website ({home}) and noticed "
             f"this observable detail: {evidence} "
             "I haven't completed a usability audit, so I wouldn't want to assume anything is broken. "
             "Would you be open to a short, no-cost review with practical recommendations? "
             "If it isn't useful, there's no obligation.\n\nBest,\nScout")
    return {"business":name,"website":home,"contact_email":contact,"contact_source":contact_source,
            "name_source":name_source,"opportunity":opportunity,"evidence_url":home,
            "evidence":evidence,"status":status,"subject":subject,"draft":draft,"_priority":priority}
def main():
    source = ROOT/"prospects.csv"
    if not source.exists(): raise SystemExit("prospects.csv missing")
    with source.open(newline="",encoding="utf-8") as f: leads = list(csv.DictReader(f))
    rows, seen = [], set()
    for lead in leads[:80]:
        host = (urlparse(lead.get("website") or "").hostname or "").lower().removeprefix("www.")
        if not host or host in seen or blocked(host) or not likely_customer(lead.get("business", ""), host): continue
        seen.add(host)
        result = inspect(lead)
        if result: rows.append(result)
        if len(rows) >= 35: break
    eligible = [r for r in rows if r["draft"]]
    # Prefer verified public business contacts; preserve evidence and review-only status.
    selected = sorted(eligible, key=lambda r: (not bool(r["contact_email"]), -r.get("_priority", 0), r["business"].casefold()))[:5]
    selected = [{k: v for k, v in row.items() if k in FIELDS} for row in selected]
    with (ROOT/"outreach_review.csv").open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(selected)
    ready = sum(bool(r["contact_email"]) for r in selected)
    total_contacts = sum(bool(r["contact_email"]) for r in rows)
    manual_review = len(rows) - len(eligible)
    (ROOT/"outreach_report.md").write_text(
        f"# Scout Evidence-Based Outreach Review\n\nProspects in source: {len(leads)}\n"
        f"Websites inspected: {len(rows)}\nOffline drafts prepared: {len(selected)}\n"
        f"Public business emails found: {total_contacts}\nEmails in selected drafts: {ready}\nManual verification required: {manual_review}\nEmails sent: 0\n\n"
        "Names and email addresses come from inspected company pages where available. "
        "All findings are preliminary, require human review, and do not establish actual defects. "
        "No Gmail drafts or messages were created.\n",encoding="utf-8")
    print(f"Scout: {len(rows)} websites inspected; {len(selected)} offline drafts; {total_contacts} public emails ({ready} selected); 0 sent")
if __name__ == "__main__": main()
