"""Scout V4: deterministic, free, bounded diagnostic triage from existing passive evidence.
No network calls, paid services, active security scans or email sending.
"""
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "qualified_leads.csv"
OUTPUT = ROOT / "diagnostic_findings.json"

RULES = (
    ("inquiry_path", ("contact/quote link or form",), "Customer inquiry path review", 5,
     "Verify that customers can easily request a quote or contact the business."),
    ("thin_content", ("limited html text",), "Complete website makeover assessment", 5,
     "Review rendered pages and service coverage before proposing a full redesign."),
    ("mobile_viewport", ("viewport meta tag",), "Mobile experience review", 4,
     "Check the rendered site on a mobile viewport and assess usability."),
    ("image_accessibility", ("no alt attribute", "lack alt attributes"), "Image accessibility review", 4,
     "Check whether informative images need meaningful alternative text."),
    ("page_structure", ("no h1 heading",), "Content hierarchy review", 3,
     "Review visible headings and page structure."),
    ("search_snippet", ("meta description",), "Search presentation review", 2,
     "Review page snippets and search presentation."),
    ("security_headers", ("csp response header", "x-content-type-options"), "HTTP configuration review", 1,
     "Confirm intended security configuration; absence alone is not a vulnerability."),
)

def main():
    if not SOURCE.exists():
        raise SystemExit("Missing qualified_leads.csv")
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        leads = list(csv.DictReader(stream))
    findings = []
    for lead in leads:
        if lead.get("inspection_status") != "FETCHED":
            continue
        evidence = (lead.get("observed_signal") or "")
        for part in (s.strip() for s in evidence.split(";") if s.strip()):
            lower = part.lower()
            match = next((r for r in RULES if any(term in lower for term in r[1])), None)
            if match is None:
                continue
            code, _, service, impact, next_step = match
            findings.append({
                "business": lead.get("business", ""),
                "domain": lead.get("domain", ""),
                "finding_id": code,
                "observed_evidence": part,
                "suggested_service": service,
                "impact_priority": impact,
                "confidence": "preliminary_html_http_observation",
                "verification_step": next_step,
                "authorized_security_test": False,
            })
    findings.sort(key=lambda f: (-f["impact_priority"], f["domain"], f["finding_id"]))
    OUTPUT.write_text(json.dumps({
        "mode": "public_prospect_research",
        "limitations": "Preliminary passive HTML/HTTP observations only; no browser verification or penetration testing.",
        "findings": findings,
    }, indent=2) + "\n", encoding="utf-8")
    print("Scout V4 diagnostic triage:", len(findings), "preliminary findings across",
          len({f["domain"] for f in findings}), "sites; no network requests")

if __name__ == "__main__":
    main()
