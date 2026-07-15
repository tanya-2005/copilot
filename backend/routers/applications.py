"""
applications.py — the one write path for application status/notes. Mirrors
what dashboard/app.py's status_update_widget() does: create the Application
row on first status change, set applied_at automatically when moving to
'applied'.
"""
import datetime
import os
import sys
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "storage"))

from models import Application, ApplicationStatus, Job  # noqa: E402

from ..deps import get_db  # noqa: E402
from .. import schemas  # noqa: E402

router = APIRouter(tags=["applications"])

VALID_STATUSES = {s.value for s in ApplicationStatus}


@router.patch("/applications/{job_id}")
def update_application(job_id: UUID, body: schemas.ApplicationUpdate, db=Depends(get_db)):
    if not db.query(Job.id).filter_by(id=job_id).first():
        raise HTTPException(status_code=404, detail="Job not found")

    app = db.query(Application).filter_by(job_id=job_id).first()
    if not app:
        app = Application(job_id=job_id, status=ApplicationStatus.not_applied)
        db.add(app)

    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status '{body.status}'")
        app.status = ApplicationStatus(body.status)
        if body.status == "applied" and not app.applied_at:
            app.applied_at = datetime.datetime.now(datetime.timezone.utc)

    if body.notes is not None:
        app.notes = body.notes

    app.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()

    return {"status": app.status.value, "notes": app.notes}
