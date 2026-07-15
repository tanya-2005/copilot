"""
runner.py — calls every enabled discovery source and returns one
deduplicated (by URL) list of RawJob objects. Dedup against the DATABASE
happens later in dedup/dedup_engine.py — this is just cross-source dedup
within a single run (e.g. the same job showing up via both its ATS and a
web search hit).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import ats_greenhouse
import ats_lever
import ats_ashby
import ats_workday
import ats_smartrecruiters
import web_search_source

ATS_FETCHERS = {
    "greenhouse": ats_greenhouse.fetch,
    "lever": ats_lever.fetch,
    "ashby": ats_ashby.fetch,
    "workday": ats_workday.fetch,
    "smartrecruiters": ats_smartrecruiters.fetch,
}


def run_all(client, sources_config: dict, keywords: list, excludes: list) -> list:
    all_jobs = []

    for c in sources_config.get("companies", []):
        fetcher = ATS_FETCHERS.get(c["ats"])
        if not fetcher:
            print(f"[warn] unknown ats '{c['ats']}' for {c['name']}, skipping")
            continue
        found = fetcher(c["name"], c["board_token"], keywords, excludes)
        print(f"[{c['ats']}] {c['name']}: {len(found)} matching posting(s)")
        all_jobs.extend(found)

    wd = sources_config.get("web_discovery", {})
    if wd.get("enabled"):
        found = web_search_source.fetch(client, wd["queries"], wd.get("max_results_per_query", 8))
        all_jobs.extend(found)

    return _dedup_by_url(all_jobs)


def _dedup_by_url(jobs: list) -> list:
    seen = set()
    out = []
    for j in jobs:
        u = (j.url or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(j)
    return out
