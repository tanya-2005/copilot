"""
contact_finder.py — best-effort search for a publicly-listed recruiter or
hiring-manager contact for a given company/role, using the AI client's web
search grounding (see src/ai/client.py) over public sources only (company
website, public LinkedIn search results, press pages). Never logs into
LinkedIn or any other site, never scrapes private/gated data. Results are
explicitly confidence-rated — treat 'low' as "worth a Google, not worth
trusting blindly."
"""
import sys
import os
import json
import re
import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
from models import Contact, Confidence


def find_contact(client, company: str, role_title: str) -> dict:
    prompt = (
        f"Search the web for a recruiter, university/campus recruiter, or engineering/product "
        f"hiring manager at {company} who would plausibly be relevant to a '{role_title}' internship "
        "application. Use only publicly available information (company website team/about pages, "
        "public press mentions, public conference bios). Do not attempt to access LinkedIn profile "
        "pages that require login — only use what's visible in public search results/snippets.\n\n"
        "If you find a plausible contact, rate your confidence:\n"
        "- high: name + role + public email or clearly public LinkedIn URL found\n"
        "- medium: name + role found, but no direct contact method\n"
        "- low: only a general pattern (e.g. company uses firstname@company.com) or a guess\n\n"
        "If nothing plausible is found, say so.\n\n"
        "Respond with ONLY a JSON object:\n"
        '{"found": true/false, "name": "...", "title": "...", "email": "...", '
        '"linkedin_url": "...", "source": "...", "confidence": "high|medium|low"}'
    )
    search_query = f"{company} recruiter OR campus recruiter OR hiring manager {role_title} internship"
    try:
        text = client.generate(prompt, max_tokens=600, use_search=True, search_query=search_query)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {"found": False}
        return json.loads(match.group(0))
    except Exception as e:
        print(f"[contact_finder] {company}: failed ({e})")
        return {"found": False}


def find_and_persist_contact(session, client, job) -> None:
    company_name = job.company.name if job.company else ""
    result = find_contact(client, company_name, job.title)
    if not result.get("found"):
        return

    conf_map = {"high": Confidence.high, "medium": Confidence.medium, "low": Confidence.low}
    contact = Contact(
        job_id=job.id,
        name=result.get("name") or None,
        title=result.get("title") or None,
        email=result.get("email") or None,
        linkedin_url=result.get("linkedin_url") or None,
        source=result.get("source") or "web_search",
        confidence=conf_map.get(result.get("confidence"), Confidence.low),
        found_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(contact)
    session.flush()
