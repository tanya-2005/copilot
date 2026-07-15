"""
ats_workday.py — pulls postings from a company's Workday-hosted careers
site via its CXS search API: the same, unauthenticated endpoint the
careers page's own search box calls. No login, no ToS concern.

Workday doesn't use a single "board token" like Greenhouse/Lever/Ashby —
each tenant has its own subdomain, host shard, and career-site name.
Encode all three into sources.yaml's board_token as "tenant/host/site",
e.g. "acme/wd5/External" for https://acme.wd5.myworkdayjobs.com/en-US/External.
Find these by opening the company's careers page and reading the URL (the
part before ".myworkdayjobs.com" is tenant.host, the path segment after
/en-US/ is the site).
"""
import re
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(__file__))
from base import RawJob, title_matches

HEADERS = {
    "User-Agent": "internship-copilot/1.0 (personal internship search tool)",
    "Content-Type": "application/json",
}
PAGE_SIZE = 20


def _fetch_description(base: str, tenant: str, site: str, external_path: str) -> str:
    """The search endpoint doesn't return full descriptions, so this is a
    second call — only made for jobs whose title already matched."""
    url = f"{base}/wday/cxs/{tenant}/{site}{external_path}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.json().get("jobPostingInfo", {}).get("jobDescription", "")
        return re.sub("<[^<]+?>", " ", html).strip()
    except Exception:
        return ""


def fetch(company_name: str, board_token: str, keywords: list, excludes: list) -> list:
    try:
        tenant, host, site = board_token.split("/")
    except ValueError:
        print(f"[workday] {company_name}: board_token must be 'tenant/host/site', got '{board_token}'")
        return []

    base = f"https://{tenant}.{host}.myworkdayjobs.com"
    api_url = f"{base}/wday/cxs/{tenant}/{site}/jobs"

    results = []
    offset = 0
    while True:
        try:
            resp = requests.post(
                api_url, headers=HEADERS, timeout=20,
                json={"limit": PAGE_SIZE, "offset": offset, "searchText": ""},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[workday] {company_name}: fetch failed ({e})")
            break

        postings = data.get("jobPostings", [])
        if not postings:
            break

        for p in postings:
            title = p.get("title", "")
            if not title_matches(title, keywords, excludes):
                continue
            path = p.get("externalPath", "")
            results.append(RawJob(
                title=title,
                company=company_name,
                location=p.get("locationsText", ""),
                url=f"{base}/en-US/{site}{path}",
                source="workday",
                external_id=(p.get("bulletFields") or [path])[0],
                description=_fetch_description(base, tenant, site, path) if path else "",
            ))

        offset += PAGE_SIZE
        if offset >= data.get("total", 0):
            break

    return results
