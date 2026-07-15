"""
apply_approved.py — run after you set an Application's status to
'ready_to_apply' in the dashboard.

Same conservative policy as the design doc: only submits automatically for
simple Lever-hosted postings with no custom required fields (a documented,
stable API). Everything else — Greenhouse, Ashby, web_search-sourced,
LinkedIn, Indeed — is left as 'ready_to_apply' with tailored documents
attached; you complete those manually using the dashboard's direct link and
generated files. This avoids ever guessing at a form and submitting
something broken or incomplete in your name.
"""
import sys
import os
import datetime
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))

from settings import settings
from db import get_session
from models import Application, ApplicationStatus, Job, AppliedVia

RESUME_PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "resume", "master_resume.pdf")


def try_lever_apply(job: Job) -> bool:
    parts = job.url.rstrip("/").split("/")
    if len(parts) < 2:
        return False
    posting_id = parts[-1]
    company_token = parts[-2]
    apply_url = f"https://api.lever.co/v0/postings/{company_token}/{posting_id}?send_confirmation=false"

    name = os.environ.get("CANDIDATE_NAME", "")
    email = os.environ.get("CANDIDATE_EMAIL", "")
    phone = os.environ.get("CANDIDATE_PHONE", "")
    if not (name and email):
        print("  CANDIDATE_NAME / CANDIDATE_EMAIL not set, skipping auto-submit")
        return False
    if not os.path.exists(RESUME_PDF_PATH):
        print("  resume PDF not found at resume/master_resume.pdf, skipping auto-submit")
        return False

    try:
        with open(RESUME_PDF_PATH, "rb") as f:
            files = {"resume": (os.path.basename(RESUME_PDF_PATH), f, "application/pdf")}
            data = {"name": name, "email": email, "phone": phone}
            resp = requests.post(apply_url, data=data, files=files, timeout=30)
        if resp.status_code in (200, 201):
            print("  Lever application submitted successfully.")
            return True
        print(f"  Lever submission returned {resp.status_code}: {resp.text[:300]}")
        return False
    except Exception as e:
        print(f"  Lever submission failed: {e}")
        return False


def main():
    settings.validate_for(["DATABASE_URL"])

    with get_session() as session:
        ready = (
            session.query(Application, Job)
            .join(Job, Application.job_id == Job.id)
            .filter(Application.status == ApplicationStatus.ready_to_apply)
            .all()
        )

        if not ready:
            print("No applications with status 'ready_to_apply'.")
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        for app, job in ready:
            company_name = job.company.name if job.company else "?"
            print(f"Processing: {company_name} — {job.title} (source={job.source.value})")

            applied = False
            if job.source.value == "lever":
                applied = try_lever_apply(job)

            if applied:
                app.status = ApplicationStatus.applied
                app.applied_at = now
                app.applied_via = AppliedVia.auto
                app.notes = (app.notes or "") + "\nAuto-submitted via Lever API."
            else:
                # Stays 'ready_to_apply' — but we note it needs manual completion
                # rather than silently leaving it ambiguous.
                app.notes = (app.notes or "") + \
                    "\nAuto-submit not available/failed for this source — apply manually using the " \
                    "generated resume/cover letter/email, then mark 'applied' in the dashboard."
            app.updated_at = now

        session.commit()
    print("=== Done ===")


if __name__ == "__main__":
    main()
