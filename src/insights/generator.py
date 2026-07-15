"""
generator.py — periodic AI Insights: skills you're most often missing,
technologies that show up frequently in postings, companies you match well
with, concrete resume-improvement suggestions, and a short weekly summary.

Deliberately one AI call over the *aggregate* of recent job_matches (not
one call per job) — this runs weekly, not daily, so cost stays low while
still covering everything scored in the period.
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
from models import Application, Company, Job, JobMatch  # noqa: E402

DEFAULT_LOOKBACK_DAYS = 7

_EMPTY_REPORT = {
    "summary": "No jobs were scored in this period.",
    "missing_skills": [],
    "frequent_technologies": [],
    "strong_companies": [],
    "resume_suggestions": [],
}


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def _recent_matches(session, since: datetime.datetime):
    return (
        session.query(JobMatch, Job, Company)
        .join(Job, JobMatch.job_id == Job.id)
        .outerjoin(Company, Job.company_id == Company.id)
        .filter(JobMatch.matched_at >= since)
        .order_by(JobMatch.matched_at.desc())
        .all()
    )


def _application_status_counts(session, since: datetime.datetime) -> dict:
    rows = session.query(Application.status).filter(Application.updated_at >= since).all()
    counts: dict[str, int] = {}
    for (status,) in rows:
        counts[status.value] = counts.get(status.value, 0) + 1
    return counts


def generate_insights(session, client, lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> dict:
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)
    matches = _recent_matches(session, since)
    application_counts = _application_status_counts(session, since)

    if not matches:
        return {**_EMPTY_REPORT, "period_days": lookback_days, "jobs_scored": 0,
                "application_counts": application_counts}

    rows_text = "\n".join(
        f"- {company.name if company else '?'} | {job.title} | score={match.match_score} | {match.match_reason}"
        for match, job, company in matches
    )

    prompt = (
        f"You are analyzing a student's internship search over the last {lookback_days} days. "
        "Below is every job scored against their resume in that window (company, title, match "
        "score 0-100, and the one-line reason the score was given).\n\n"
        f"{rows_text}\n\n"
        f"Application status changes in this period: {json.dumps(application_counts)}\n\n"
        "Based only on this data, respond with ONLY a JSON object:\n"
        "{\n"
        '  "summary": "<2-3 sentence weekly summary of how the search is going>",\n'
        '  "missing_skills": ["<skill mentioned as missing/weak, most common first, max 8>"],\n'
        '  "frequent_technologies": ["<tech/tool that shows up often in these postings, max 8>"],\n'
        '  "strong_companies": ["<company name where scores were consistently high>"],\n'
        '  "resume_suggestions": ["<concrete, specific suggestion to improve match rate, max 5>"]\n'
        "}"
    )
    text = client.generate(prompt, max_tokens=1000)

    try:
        parsed = _extract_json(text)
    except Exception:
        parsed = {**_EMPTY_REPORT, "summary": "Could not parse model output for this period."}

    parsed["period_days"] = lookback_days
    parsed["jobs_scored"] = len(matches)
    parsed["application_counts"] = application_counts
    return parsed
