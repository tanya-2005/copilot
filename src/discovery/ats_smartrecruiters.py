"""
ats_smartrecruiters.py — pulls postings from SmartRecruiters' public
postings API (the same endpoint SmartRecruiters' own embeddable "jobs
widget" uses). No login, no ToS concern.
Docs: https://developers.smartrecruiters.com/docs/postings-api

board_token is the company identifier from the careers URL, e.g.
jobs.smartrecruiters.com/<CompanyName> -> board_token: "<CompanyName>".
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(__file__))
from base import RawJob, title_matches

HEADERS = {"User-Agent": "internship-copilot/1.0 (personal internship search tool)"}


def _location_str(loc: dict) -> str:
    if not loc:
        return ""
    if loc.get("remote"):
        return "Remote"
    parts = [p for p in (loc.get("city"), loc.get("region"), loc.get("country")) if p]
    return ", ".join(parts)


def _fetch_description(board_token: str, posting_id: str) -> str:
    """The postings list endpoint doesn't include the full description, so
    this is a second call — only made for jobs whose title already matched,
    to keep the extra API calls proportional to real candidates."""
    url = f"https://api.smartrecruiters.com/v1/companies/{board_token}/postings/{posting_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        sections = resp.json().get("jobAd", {}).get("sections", {})
        return "\n\n".join(
            s.get("text", "") for s in sections.values() if isinstance(s, dict) and s.get("text")
        )
    except Exception:
        return ""


def fetch(company_name: str, board_token: str, keywords: list, excludes: list) -> list:
    url = f"https://api.smartrecruiters.com/v1/companies/{board_token}/postings"
    try:
        resp = requests.get(url, headers=HEADERS, params={"limit": 100}, timeout=20)
        resp.raise_for_status()
        postings = resp.json().get("content", [])
    except Exception as e:
        print(f"[smartrecruiters] {company_name}: fetch failed ({e})")
        return []

    results = []
    for p in postings:
        title = p.get("name", "")
        if not title_matches(title, keywords, excludes):
            continue
        posting_id = str(p.get("id", ""))
        results.append(RawJob(
            title=title,
            company=company_name,
            location=_location_str(p.get("location")),
            url=p.get("postingUrl") or p.get("applyUrl", ""),
            source="smartrecruiters",
            external_id=posting_id,
            description=_fetch_description(board_token, posting_id) if posting_id else "",
        ))
    return results
