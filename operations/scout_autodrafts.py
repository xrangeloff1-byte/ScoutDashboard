"""Scout V3: verified-contact research and Gmail draft creation ONLY. Never sends mail."""
import base64, csv, email.message, json, os, pathlib, re, urllib.parse, urllib.request
from html.parser import HTMLParser

ROOT=pathlib.Path(__file__).resolve().parent
IN=ROOT/"qualified_leads.csv"
OUT=ROOT/"draft_review.csv"
REPORT=ROOT/"draft_review.md"
MAX_DRAFTS=min(max(int(os.getenv("SCOUT_MAX_DRAFTS","5")),0),10)
class Contacts(HTMLParser):
    def __init__(self):
        super().__init__(); self.emails=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag!="a": return
        href=dict(attrs).get("href","")
        if href.lower().startswith("mailto:"):
            address=urllib.parse.unquote(href[7:].split("?")[0]).strip()
            self.emails.append(address)
        if any(w in href.lower() for w in ("contact","about")): self.links.append(href)
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ScoutResearch/1.0","Accept":"text/html"})
    with urllib.request.urlopen(req,timeout=8) as res:
        if res.url.split("/")[2].lower()!=urllib.parse.urlparse(url).netloc.lower(): return ""
        if "text/html" not in res.headers.get("Content-Type","").lower(): return ""
        return res.read(160000).decode("utf-8","replace")
def find_contact(domain):
    # Only public mailto links on the same business homepage; no scraping hidden data.
    if not re.fullmatch(r"[a-z0-9.-]+",domain,re.I): return "", "invalid_domain"
    try:
        parser=Contacts();parser.feed(fetch("https://"+domain+"/"))
        for address in parser.emails:
            if re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[a-z]{2,}",address,re.I) and address.lower().split("@")[1]==domain.lower():
                return address,"public_homepage_mailto"
        return "","no_same_domain_public_mailto"
    except Exception as e: return "","lookup_"+type(e).__name__
def make_message(row):
    name=(row.get("business") or row["domain"]).strip()
    subject="A quick website question for "+name
    body=("Hello,\n\nI came across "+name+" while researching local service businesses. "
          "Cairnflow Private helps with practical website improvements, including clearer service pages, "
          "mobile-friendly presentation and customer inquiry forms.\n\n"
          "Would you be interested in a short, no-obligation website review? "
          "I'd share suggestions before proposing any work.\n\n"
          "Best,\n"+os.environ["SCOUT_SENDER_NAME"]+"\nCairnflow Private\n"
          +os.environ["SCOUT_BUSINESS_CONTACT"]+"\n"
          "If you'd prefer no further messages, reply 'no thanks' and I'll respect that.\n")
    return subject,body
def gmail_draft(to,subject,body,token):
    msg=email.message.EmailMessage()
    msg["To"]=to;msg["Subject"]=subject;msg.set_content(body)
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    req=urllib.request.Request("https://gmail.googleapis.com/gmail/v1/users/me/drafts",
        data=json.dumps({"message":{"raw":raw}}).encode(),
        headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=20) as res: return json.load(res)["id"]
def refresh_token():
    required=("GMAIL_CLIENT_ID","GMAIL_CLIENT_SECRET","GMAIL_REFRESH_TOKEN")
    if not all(os.getenv(k) for k in required): return ""
    data=urllib.parse.urlencode({"client_id":os.environ["GMAIL_CLIENT_ID"],
      "client_secret":os.environ["GMAIL_CLIENT_SECRET"],
      "refresh_token":os.environ["GMAIL_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data,method="POST")
    with urllib.request.urlopen(req,timeout=20) as res: return json.load(res)["access_token"]
def main():
    if not IN.exists(): raise SystemExit("Run qualification first")
    with IN.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    token=""
    configured=all(os.getenv(k) for k in ("SCOUT_SENDER_NAME","SCOUT_BUSINESS_CONTACT","GMAIL_CLIENT_ID","GMAIL_CLIENT_SECRET","GMAIL_REFRESH_TOKEN"))
    if configured:
        try: token=refresh_token()
        except Exception as e: print("Gmail OAuth unavailable:",type(e).__name__)
    result=[];made=0;used=set()
    for row in rows:
        domain=row.get("domain","").strip().lower()
        if not domain or domain in used: continue
        used.add(domain)
        address,source=find_contact(domain)
        item={"business":row.get("business",""),"domain":domain,"email":address,
              "contact_source":source,"score":row.get("priority_score",""),
              "status":"NO_PUBLIC_SAME_DOMAIN_EMAIL" if not address else "REVIEW_REQUIRED",
              "gmail_draft_id":""}
        if address and int(row.get("priority_score") or 0)>=25 and made<MAX_DRAFTS:
            if token:
                subject,body=make_message(row)
                try:
                    item["gmail_draft_id"]=gmail_draft(address,subject,body,token)
                    item["status"]="GMAIL_DRAFT_CREATED_UNSENT";made+=1
                except Exception as e: item["status"]="GMAIL_ERROR_"+type(e).__name__
            else: item["status"]="AWAITING_GMAIL_OAUTH_AND_SENDER_DETAILS"
        result.append(item)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["business","domain","email","contact_source","score","status","gmail_draft_id"]);w.writeheader();w.writerows(result)
    REPORT.write_text("# Scout Gmail draft review\n\n"
        +f"Businesses reviewed: {len(result)}\nDrafts created (unsent): {made}\nEmails sent: 0\n"
        +f"Gmail OAuth and sender details configured: {configured}\n\n"
        +"Only same-domain mailto addresses found on public homepages are considered. "
        +"These addresses and the proposed messages require manual verification before sending. "
        +"Do not use automated sending without separate authorization and compliance checks.\n",encoding="utf-8")
    print(f"Scout autodrafts: {len(result)} businesses, {sum(bool(x['email']) for x in result)} public contacts, {made} Gmail drafts, 0 sent")
if __name__=="__main__": main()
