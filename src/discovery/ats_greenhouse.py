"""
ats_greenhouse.py — pulls postings from Greenhouse's public, unauthenticated
job-board API. No login, no ToS concern: this endpoint is designed for
public consumption (it's what powers companies' own careers pages).
Docs: https://developers.greenhouse.io/job-board.html
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(__file__))
from base import RawJob, title_matches

HEADERS = {"User-Agent": "internship-copilot/1.0 (personal internship search tool)"}


def fetch(company_name: str, board_token: str, keywords: list, excludes: list) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
    except Exception as e:
        print(f"[greenhouse] {company_name}: fetch failed ({e})")
        return []

    results = []
    for j in jobs:
        title = j.get("title", "")
        if not title_matches(title, keywords, excludes):
            continue
        location = (j.get("location") or {}).get("name", "")
        results.append(RawJob(
            title=title,
            company=company_name,
            location=location,
            url=j.get("absolute_url", ""),
            source="greenhouse",
            external_id=str(j.get("id", "")),
            description=j.get("content", ""),
        ))
    return results
