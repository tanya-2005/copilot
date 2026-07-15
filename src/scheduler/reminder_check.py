"""
reminder_check.py — checks for FollowUp rows due today (or overdue) and
not yet completed, and sends a notification. Run daily via GitHub Actions,
separately from the discovery run.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "notifications"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "storage"))

from settings import settings
from db import get_session
from models import FollowUp, Application, Job, Company
import notifier


def main():
    settings.validate_for(["DATABASE_URL"])
    today = datetime.date.today()

    with get_session() as session:
        due = (
            session.query(FollowUp, Application, Job, Company)
            .join(Application, FollowUp.application_id == Application.id)
            .join(Job, Application.job_id == Job.id)
            .outerjoin(Company, Job.company_id == Company.id)
            .filter(FollowUp.completed == False, FollowUp.due_date <= today)  # noqa: E712
            .all()
        )

        followups = [
            {
                "company": company.name if company else "?",
                "role": job.title,
                "due_date": fu.due_date.isoformat(),
                "note": fu.note or "",
            }
            for fu, app, job, company in due
        ]

        print(f"{len(followups)} follow-up(s) due")
        notifier.notify_due_followups(followups)


if __name__ == "__main__":
    main()
