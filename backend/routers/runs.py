"""
runs.py — manual triggers for the same entry points GitHub Actions calls on
a schedule (src/scheduler/*.py), so the dashboard can kick off a run without
waiting for the next cron tick or opening the Actions tab.

IMPORTANT: /runs/apply calls apply_approved.main(), which can submit a real
application (currently: simple Lever postings only) for anything you've
marked 'ready_to_apply'. It is exactly as consequential as the existing
"Apply to Approved Applications" GitHub Actions button — this just gives the
frontend an equivalent, so keep it behind whatever auth the frontend adds
before this is exposed beyond localhost.
"""
import os
import sys

from fastapi import APIRouter, BackgroundTasks, Depends

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "scheduler"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "storage"))

import daily_discovery  # noqa: E402
import reminder_check  # noqa: E402
import apply_approved  # noqa: E402
import weekly_insights  # noqa: E402
from models import RunLog  # noqa: E402

from ..deps import get_db  # noqa: E402

router = APIRouter(tags=["runs"])


@router.post("/runs/discovery")
def trigger_discovery(background_tasks: BackgroundTasks):
    background_tasks.add_task(daily_discovery.main)
    return {"status": "started", "run": "discovery"}


@router.post("/runs/reminders")
def trigger_reminders(background_tasks: BackgroundTasks):
    background_tasks.add_task(reminder_check.main)
    return {"status": "started", "run": "reminders"}


@router.post("/runs/apply")
def trigger_apply(background_tasks: BackgroundTasks):
    background_tasks.add_task(apply_approved.main)
    return {"status": "started", "run": "apply"}


@router.post("/runs/insights")
def trigger_insights(background_tasks: BackgroundTasks):
    background_tasks.add_task(weekly_insights.main)
    return {"status": "started", "run": "insights"}


@router.get("/runs")
def recent_runs(limit: int = 10, db=Depends(get_db)):
    runs = db.query(RunLog).order_by(RunLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "run_type": r.run_type.value,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "jobs_found": r.jobs_found,
            "jobs_new": r.jobs_new,
            "errors": r.errors,
        }
        for r in runs
    ]
