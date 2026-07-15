"""
stats.py — response-funnel numbers for the dashboard's stats view. Same
math as dashboard/app.py's Response stats tab: jobs with no Application
row are implicitly 'not_applied'.
"""
import os
import sys

from fastapi import APIRouter, Depends

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "storage"))

from models import Application, Job  # noqa: E402

from ..deps import get_db  # noqa: E402

router = APIRouter(tags=["stats"])


@router.get("/stats")
def get_stats(db=Depends(get_db)):
    counts: dict[str, int] = {}
    for (status,) in db.query(Application.status).all():
        counts[status.value] = counts.get(status.value, 0) + 1

    total_jobs = db.query(Job).count()
    without_application = total_jobs - sum(counts.values())
    if without_application > 0:
        counts["not_applied"] = counts.get("not_applied", 0) + without_application

    total_applied = (
        counts.get("applied", 0) + counts.get("interview", 0) + counts.get("offer", 0) + counts.get("rejected", 0)
    )
    interviewed = counts.get("interview", 0) + counts.get("offer", 0)
    interview_rate = round((interviewed / total_applied * 100), 1) if total_applied else 0.0

    return {
        "status_counts": counts,
        "total_jobs": total_jobs,
        "total_applied": total_applied,
        "interview_rate": interview_rate,
    }
