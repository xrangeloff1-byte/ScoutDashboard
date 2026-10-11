"""Offline Scout dashboard: public research drafts and optional manually maintained records."""
import csv,datetime,html,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def read(name):
 p=ROOT/name
 if not p.exists(): return []
 with p.open(encoding="utf-8",newline="") as f: return list(csv.DictReader(f))
def e(s): return html.escape(str(s or ""),quote=True)
def item(name,sub,detail,tag):
 return '<article><div class="itemhead"><strong>'+e(name)+'</strong><span class="tag">'+e(tag)+'</span></div><small>'+e(sub)+'</small><p>'+e(detail)+'</p></article>'
def panel(title,desc,items,empty):
 return '<section><header><div><h2>'+title+'</h2><small>'+desc+'</small></div><b>'+str(len(items))+'</b></header>'+(''.join(items) if items else '<div class="empty">'+empty+'</div>')+'</section>'
def main():
 leads={r.get("domain","").lower():r for r in read("qualified_leads.csv")}
 contacts=read("draft_review.csv")
 drafts=[]
 for r in contacts:
  q=leads.get(r.get("domain","").lower(),{})
  if r.get("email") and q.get("inspection_status")=="FETCHED" and int(q.get("priority_score") or 0)>=25:
   drafts.append(item(r.get("business"),r.get("email"),(q.get("primary_finding") or q.get("observed_signal") or "")+" · "+q.get("recommended_service",""),"Review"))
 replies=[item(r.get("business") or r.get("from"),r.get("subject"),r.get("next_action"),"Reply") for r in read("replies.csv") if r.get("status","").lower() in ("needs_attention","unread","awaiting_reply")]
 clients=[item(r.get("business"),r.get("service"),r.get("next_action"),"Active") for r in read("clients.csv") if r.get("status","").lower() in ("active","in_progress")]
 tasks=[item(r.get("business"),r.get("task"),r.get("notes"),"Open") for r in read("client_tasks.csv") if r.get("status","").lower() not in ("done","closed","completed")]
 css="""*{box-sizing:border-box}body{margin:0;background:#0b111d;color:#f5f7fa;font:15px/1.5 system-ui,-apple-system,sans-serif}.wrap{max-width:1100px;margin:auto;padding:28px 20px 70px}.top{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:center}.brand{letter-spacing:3px;color:#c6ac78;font-size:12px;font-weight:800}.agent{background:#1a2637;border:1px solid #38465a;border-radius:12px;padding:10px 15px}.agent small{display:block;color:#aabbd0}h1{font-size:clamp(30px,5vw,48px);letter-spacing:-1px;margin:20px 0 2px}.intro{color:#9eb0c6;margin:0 0 28px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:22px}.stat,section{background:#131e2e;border:1px solid #2c3b51;border-radius:16px;padding:20px}.stat b{display:block;font-size:32px}.stat small,section small{color:#a5b5c8}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}section header{display:flex;justify-content:space-between;gap:14px;align-items:center;margin-bottom:18px}section h2{margin:0;font-size:19px}section header b{background:#2b3a50;padding:4px 11px;border-radius:40px}article{background:#1b293c;border:1px solid #33445b;padding:15px;border-radius:11px;margin-top:10px}article p{color:#b1c0d2;font-size:13px;overflow-wrap:anywhere;margin:7px 0 0}.itemhead{display:flex;justify-content:space-between;gap:8px}.tag{font-size:11px;background:#453b2b;color:#eed5a6;border-radius:40px;padding:3px 9px;white-space:nowrap}.empty{border:1px dashed #40516a;color:#a0b0c3;padding:20px;border-radius:11px}.foot{color:#91a3ba;font-size:12px;margin-top:24px}@media(max-width:720px){.grid{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.wrap{padding:20px 14px}}"""
 timestamp=datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %Y · %H:%M UTC")
 blocks=[("Drafts needing attention","Verified public email and website observation",drafts,"No qualifying drafts in this run."),("Replies needing attention","Manually imported correspondence — no live inbox sync",replies,"No reply records imported; mailbox status is unknown."),("Active clients","Manually maintained client records",clients,"No client records imported; client status is unknown."),("Work needing attention","Manually maintained outstanding tasks",tasks,"No task records imported; task status is unknown.")]
 page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cairnflow | Scout Command Center</title><style>'+css+'</style><main class="wrap"><div class="top"><div class="brand">CAIRNFLOW PRIVATE / SCOUT</div><div class="agent"><strong>John Laering</strong><small>Virtual Client Relations Agent</small></div></div><h1>Command Center</h1><p class="intro">Private review workspace · '+e(timestamp)+'</p><div class="stats">'+''.join('<div class="stat"><b>'+str(len(b[2]))+'</b><small>'+b[0]+'</small></div>' for b in blocks)+'</div><div class="grid">'+''.join(panel(*b) for b in blocks)+'</div><p class="foot">Review only. No emails sent. Publicly listed emails are not proof of deliverability. Website findings are preliminary. This is an offline snapshot, not a live CRM or inbox. To populate replies, clients and tasks, supply the corresponding CSV records and regenerate the dashboard.</p></main></html>'
 (ROOT/"scout_command_center.html").write_text(page,encoding="utf-8")
 print("Scout command center:",len(drafts),"drafts,",len(replies),"replies,",len(clients),"clients,",len(tasks),"tasks")
if __name__=="__main__": main()
