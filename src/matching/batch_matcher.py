"""
batch_matcher.py — runs scorer.score_job over every Job that doesn't yet
have a JobMatch against the current master resume, and persists the result.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
from models import Job, JobMatch, Resume
import scorer


def get_master_resume(session) -> Resume:
    resume = session.query(Resume).filter_by(is_master=True).order_by(Resume.created_at.desc()).first()
    if not resume:
        raise RuntimeError("No master resume found. Run scripts/load_resume.py first.")
    return resume


def score_unscored_jobs(session, client, jobs: list) -> list:
    """jobs: list of Job ORM objects (typically the newly-discovered ones).
    Returns list of dicts: {job, score, reason}."""
    resume = get_master_resume(session)
    results = []

    for job in jobs:
        already = session.query(JobMatch).filter_by(job_id=job.id, resume_id=resume.id).first()
        if already:
            results.append({"job": job, "score": already.match_score, "reason": already.match_reason})
            continue

        result = scorer.score_job(
            client, resume.text_content, job.title, job.company.name if job.company else "",
            job.location or "", job.description_raw or ""
        )
        score = result.get("score", 0)
        reason = result.get("reason", "")

        match = JobMatch(
            job_id=job.id,
            resume_id=resume.id,
            match_score=score,
            match_reason=reason,
            matched_at=datetime.datetime.now(datetime.timezone.utc),
            ai_model_used=client.model,
        )
        session.add(match)
        results.append({"job": job, "score": score, "reason": reason})
        print(f"  [{score}] {job.company.name if job.company else '?'} — {job.title}")

    session.flush()
    return results
