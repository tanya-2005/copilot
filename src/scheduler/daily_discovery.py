"""
daily_discovery.py — the daily entry point (run by GitHub Actions).

Steps:
  1. Discover jobs from all enabled sources.
  2. Dedup against the database, persist genuinely new jobs.
  3. Score every new job against the master resume.
  4. For strong matches: generate tailored resume/cover letter/email,
     look up a contact, create an Application row (status=recommended).
  5. Notify on strong matches.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "discovery"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dedup"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "matching"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "documents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "contacts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "notifications"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ai"))

import client as ai_client
from settings import settings, load_sources_config, load_matching_config
from db import get_session
from models import Application, ApplicationStatus, RunType, RunLog

import runner as discovery_runner
import dedup_engine
import batch_matcher
import generate_for_job
import contact_finder
import notifier

CANDIDATE_NAME = os.environ.get("CANDIDATE_NAME", "the candidate")


def main():
    settings.validate_for(["DATABASE_URL", "OPENROUTER_API_KEY", "TAVILY_API_KEY"])
    client = ai_client.get_client()

    sources_config = load_sources_config()
    matching_config = load_matching_config()
    keywords = matching_config["roles"]["title_keywords"]
    excludes = matching_config["roles"]["exclude_keywords"]
    strong_threshold = matching_config["matching"]["strong_match_threshold"]
    min_threshold = matching_config["matching"]["min_log_threshold"]

    run_log_entry = {"jobs_found": 0, "jobs_new": 0, "errors": ""}

    with get_session() as session:
        run = RunLog(run_type=RunType.discovery, started_at=datetime.datetime.now(datetime.timezone.utc))
        session.add(run)
        session.flush()

        try:
            # --- 1. Discover ---
            print("=== Discovering jobs ===")
            raw_jobs = discovery_runner.run_all(client, sources_config, keywords, excludes)
            run_log_entry["jobs_found"] = len(raw_jobs)
            print(f"=== {len(raw_jobs)} total candidate postings found ===")

            # --- 2. Dedup + persist ---
            new_raw = dedup_engine.filter_new_jobs(session, raw_jobs)
            print(f"=== {len(new_raw)} are genuinely new ===")
            new_jobs = dedup_engine.persist_new_jobs(session, new_raw)
            run_log_entry["jobs_new"] = len(new_jobs)
            session.commit()

            if not new_jobs:
                print("No new jobs. Done.")
                run.finished_at = datetime.datetime.now(datetime.timezone.utc)
                run.jobs_found = run_log_entry["jobs_found"]
                run.jobs_new = 0
                session.commit()
                return

            # --- 3. Score ---
            print("=== Scoring new jobs ===")
            results = batch_matcher.score_unscored_jobs(session, client, new_jobs)
            session.commit()

            strong = [r for r in results if r["score"] >= strong_threshold]
            loggable = [r for r in results if r["score"] >= min_threshold]
            print(f"=== {len(strong)} strong match(es), {len(loggable)} above log threshold ===")

            # --- 4. Generate documents + find contact + create Application for strong matches ---
            resume = batch_matcher.get_master_resume(session)
            for r in strong:
                job = r["job"]
                print(f"Generating documents for: {job.title} @ {job.company.name if job.company else '?'}")
                generate_for_job.generate_documents_for_job(session, client, job, resume.text_content, CANDIDATE_NAME)
                contact_finder.find_and_persist_contact(session, client, job)

                app = Application(
                    job_id=job.id,
                    status=ApplicationStatus.recommended,
                    notes=r["reason"],
                )
                session.add(app)
            session.commit()

            # --- 5. Notify ---
            notifier.notify_strong_matches(strong)

            run.finished_at = datetime.datetime.now(datetime.timezone.utc)
            run.jobs_found = run_log_entry["jobs_found"]
            run.jobs_new = run_log_entry["jobs_new"]
            session.commit()

        except Exception as e:
            session.rollback()
            run.errors = str(e)
            run.finished_at = datetime.datetime.now(datetime.timezone.utc)
            session.add(run)
            session.commit()
            raise

    print("=== Done ===")


if __name__ == "__main__":
    main()
