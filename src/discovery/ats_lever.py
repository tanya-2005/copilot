"""
ats_lever.py — pulls postings from Lever's public postings API.
Docs: https://github.com/lever/postings-api (public, unauthenticated, read-only)
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(__file__))
from base import RawJob, title_matches

HEADERS = {"User-Agent": "internship-copilot/1.0 (personal internship search tool)"}


def fetch(company_name: str, board_token: str, keywords: list, excludes: list) -> list:
    url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        jobs = resp.json()
    except Exception as e:
        print(f"[lever] {company_name}: fetch failed ({e})")
        return []

    results = []
    for j in jobs:
        title = j.get("text", "")
        if not title_matches(title, keywords, excludes):
            continue
        location = (j.get("categories") or {}).get("location", "")
        results.append(RawJob(
            title=title,
            company=company_name,
            location=location,
            url=j.get("hostedUrl", ""),
            source="lever",
            external_id=str(j.get("id", "")),
            description=(j.get("descriptionPlain") or j.get("description") or ""),
        ))
    return results
