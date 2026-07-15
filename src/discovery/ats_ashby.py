"""
ats_ashby.py — pulls postings from Ashby's public job-board API.
Docs: https://developers.ashbyhq.com/reference/jobboardapi (public, unauthenticated)
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(__file__))
from base import RawJob, title_matches

HEADERS = {"User-Agent": "internship-copilot/1.0 (personal internship search tool)"}


def fetch(company_name: str, board_token: str, keywords: list, excludes: list) -> list:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
    except Exception as e:
        print(f"[ashby] {company_name}: fetch failed ({e})")
        return []

    results = []
    for j in jobs:
        title = j.get("title", "")
        if not title_matches(title, keywords, excludes):
            continue
        results.append(RawJob(
            title=title,
            company=company_name,
            location=j.get("location", ""),
            url=j.get("jobUrl", j.get("applyUrl", "")),
            source="ashby",
            external_id=str(j.get("id", "")),
            description=j.get("descriptionPlain", j.get("description", "")),
        ))
    return results
