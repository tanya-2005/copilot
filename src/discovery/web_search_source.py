"""
web_search_source.py — uses the AI client's web search grounding (see
src/ai/client.py) to find postings outside the curated ATS company list
(LinkedIn public postings, Wellfound, Indeed, YC Jobs, and any career page
not manually added). Best-effort and less structured than the ATS APIs, but
widens coverage. Read-only — never logs in or submits anything.
"""
import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(__file__))
from base import RawJob


def fetch(client, queries: list, max_results_per_query: int) -> list:
    all_results = []
    for q in queries:
        prompt = (
            f"Search the web for: {q}\n\n"
            f"Find up to {max_results_per_query} REAL, currently-live internship job postings "
            "matching this query (roles like SDE intern, software engineering intern, tech intern, "
            "product intern, or product analyst intern; summer internships; remote or onsite, any location). "
            "Only include postings you can find an actual URL for via search — do not invent listings.\n\n"
            "Respond with ONLY a JSON array (no markdown fences, no commentary), where each element is:\n"
            '{"title": "...", "company": "...", "location": "...", "url": "..."}\n'
            "If you find nothing relevant, respond with an empty JSON array: []"
        )
        try:
            text = client.generate(prompt, max_tokens=2000, use_search=True, search_query=q)
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if not match:
                print(f"[web_search] query '{q}': no JSON array found")
                continue
            parsed = json.loads(match.group(0))
            for item in parsed:
                all_results.append(RawJob(
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    location=item.get("location", ""),
                    url=item.get("url", ""),
                    source="web_search",
                ))
            print(f"[web_search] query '{q}': {len(parsed)} result(s)")
        except Exception as e:
            print(f"[web_search] query '{q}' failed: {e}")
    return all_results
