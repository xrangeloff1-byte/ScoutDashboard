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
        super().__init__(); self.emails=[]; self.links=[]; self.phones=[]; self.forms=0; self.form_fields=set()
    def handle_starttag(self,tag,attrs):
        if tag=="form": self.forms+=1
        if tag in ("input","textarea"):
            a=dict(attrs)
            if tag=="textarea" or a.get("type","").lower()=="email" or any(x in a.get("name","").lower() for x in ("message","email","inquiry","comment")):
                self.form_fields.add(tag+":"+a.get("name",""))
        if tag!="a": return
        href=dict(attrs).get("href","")
        if href.lower().startswith("tel:"):
            self.phones.append(urllib.parse.unquote(href[4:].split("?")[0]).strip())
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
    # Review only explicitly published business mailto links on the homepage
    # and at most two same-domain contact/about pages. Never infer an address.
    if not re.fullmatch(r"[a-z0-9.-]+",domain,re.I): return "", "invalid_domain","",""
    try:
        origin="https://"+domain+"/"
        home=Contacts();home.feed(fetch(origin))
        pages=[("public_homepage_mailto",origin,home)]
        checked=set()
        for link in home.links:
            url=urllib.parse.urljoin(origin,link)
            parsed=urllib.parse.urlparse(url)
            if parsed.scheme!="https" or parsed.hostname!=domain or url in checked: continue
            if len(checked)>=2: break
            checked.add(url)
            try:
                p=Contacts();p.feed(fetch(url));pages.append(("public_contact_page_mailto",url,p))
            except Exception: pass
        fallback_form=""
        fallback_phone=""
        for source,page_url,parser in pages:
            if (parser.forms and parser.form_fields and not fallback_form
                and not any(word in urllib.parse.urlparse(page_url).path.lower() for word in ("/career","/jobs","/employment","/apply"))):
                fallback_form=page_url
            if parser.phones and not fallback_phone: fallback_phone=parser.phones[0]
            for address in parser.emails:
                address=address.strip()
                if re.fullmatch(r"[^\\s@<>]+@[^\\s@<>]+\\.[a-z]{2,}",address,re.I) and address.lower().split("@")[1]==domain.lower():
                    return address,source,fallback_form,fallback_phone
        return "","no_same_domain_public_mailto",fallback_form,fallback_phone
    except Exception as e: return "","lookup_"+type(e).__name__,"",""
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
def existing_draft_recipients(token):
    """Fail closed if Gmail draft history cannot be checked."""
    recipients=set()
    page=""
    while True:
        url="https://gmail.googleapis.com/gmail/v1/users/me/drafts?maxResults=100"
        if page: url+="&pageToken="+urllib.parse.quote(page)
        req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token})
        with urllib.request.urlopen(req,timeout=20) as res: data=json.load(res)
        for draft in data.get("drafts",[]):
            detail="https://gmail.googleapis.com/gmail/v1/users/me/drafts/"+urllib.parse.quote(draft["id"])+"?format=metadata"
            req=urllib.request.Request(detail,headers={"Authorization":"Bearer "+token})
            with urllib.request.urlopen(req,timeout=20) as res: info=json.load(res)
            headers={h["name"].lower():h["value"] for h in info.get("message",{}).get("payload",{}).get("headers",[])}
            if headers.get("subject","").startswith("A quick website question for "):
                for address in re.findall(r"[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+\\.[A-Za-z]{2,}",headers.get("to","")):
                    recipients.add(address.lower())
        page=data.get("nextPageToken","")
        if not page: break
    return recipients

def main():
    if not IN.exists(): raise SystemExit("Run qualification first")
    with IN.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    token=""
    configured=all(os.getenv(k) for k in ("SCOUT_SENDER_NAME","SCOUT_BUSINESS_CONTACT","GMAIL_CLIENT_ID","GMAIL_CLIENT_SECRET","GMAIL_REFRESH_TOKEN"))
    if configured:
        try: token=refresh_token()
        except Exception as e: print("Gmail OAuth unavailable:",type(e).__name__)
    previous=set()
    if token:
        try: previous=existing_draft_recipients(token)
        except Exception as e:
            print('Cannot verify existing Gmail drafts; refusing to create duplicates:',type(e).__name__)
            token=''
    result=[];made=0;used=set()
    for row in rows:
        domain=row.get("domain","").strip().lower()
        if not domain or domain in used: continue
        if domain in ("app.sublynk.com",) or domain.startswith("app."): continue
        used.add(domain)
        address,source,form_url,phone=find_contact(domain)
        item={"business":row.get("business",""),"domain":domain,"email":address,
              "contact_source":source,"contact_form":form_url,"business_phone":phone,"score":row.get("priority_score",""),
              "status":("REVIEW_REQUIRED" if address else "CONTACT_FORM_AVAILABLE" if form_url else "PHONE_AVAILABLE" if phone else "NO_VERIFIED_CONTACT"),
              "gmail_draft_id":""}
        if address and address.lower() in previous:
            item['status']='EXISTING_GMAIL_DRAFT_SKIPPED'
        elif address and int(row.get("priority_score") or 0)>=25 and made<MAX_DRAFTS:
            if token:
                subject,body=make_message(row)
                try:
                    item["gmail_draft_id"]=gmail_draft(address,subject,body,token)
                    item["status"]="GMAIL_DRAFT_CREATED_UNSENT";made+=1;previous.add(address.lower())
                except Exception as e: item["status"]="GMAIL_ERROR_"+type(e).__name__
            else: item["status"]="AWAITING_GMAIL_OAUTH_AND_SENDER_DETAILS"
        if form_url and not address:
            item["form_message"]=make_message(row)[1] if all(os.getenv(k) for k in ("SCOUT_SENDER_NAME","SCOUT_BUSINESS_CONTACT")) else ""
        else: item["form_message"]=""
        result.append(item)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["business","domain","email","contact_source","contact_form","business_phone","form_message","score","status","gmail_draft_id"]);w.writeheader();w.writerows(result)
    REPORT.write_text("# Scout Gmail draft review\n\n"
        +f"Businesses reviewed: {len(result)}\nDrafts created (unsent): {made}\nEmails sent: 0\n"
        +f"Gmail OAuth and sender details configured: {configured}\n\n"
        +"Contact research checks published same-domain email links, forms with message/email fields, and telephone links on public pages. Form links are review-only; no forms are submitted. "
        +"These addresses and the proposed messages require manual verification before sending. "
        +"Do not use automated sending without separate authorization and compliance checks.\n",encoding="utf-8")
    print(f"Scout autodrafts: {len(result)} businesses, {sum(bool(x['email']) for x in result)} public contacts, {made} Gmail drafts, 0 sent")
if __name__=="__main__": main()
