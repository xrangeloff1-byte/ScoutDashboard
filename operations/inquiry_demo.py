#!/usr/bin/env python3
"""Offline demo inquiry assistant. No emails, outreach, payments or external APIs."""
from dataclasses import dataclass
import json,re,sys

@dataclass
class Business:
    name:str
    phone:str
    email:str
    hours:str
    service_area:str
    faq:dict

def answer(b, question):
    """Only answer based on approved FAQ text; otherwise escalate."""
    q=re.sub(r"[^a-z0-9 ]","",question.lower()).strip()
    for topic,detail in b.faq.items():
        terms=topic.lower().split()
        if terms and all(term in q for term in terms):
            return {"status":"answered","message":detail}
    return {"status":"human_review","message":f"Thanks for contacting {b.name}. Our team will review your question and respond. For direct assistance: {b.email}."}

def demo():
    b=Business("Example Home Services","(000) 000-0000","example@example.com","Mon–Fri, 9am–5pm","Example City",
        {"business hours":"We're available Monday through Friday, 9am to 5pm.",
         "service area":"We currently serve Example City."})
    prompts=["What are your business hours?","Do you offer emergency service?"]
    for q in prompts:print(json.dumps({"question":q,**answer(b,q)}))
if __name__=="__main__":demo()
