"""
followups.py — reminder list/create/complete. Mirrors the dashboard's
Follow-ups tab: creating a reminder for a job with no Application yet
implicitly creates one with status 'applied' (you only follow up on things
you've applied to).
"""
import os
import sys
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "storage"))

from models import Application, ApplicationStatus, Company, FollowUp, Job  # noqa: E402

from ..deps import get_db  # noqa: E402
from .. import schemas  # noqa: E402

router = APIRouter(tags=["followups"])


def _followup_row(fu: FollowUp, job: Job, company: Company) -> dict:
    return {
        "id": fu.id,
        "company": company.name if company else "?",
        "title": job.title,
        "due_date": fu.due_date,
        "note": fu.note,
        "completed": fu.completed,
    }


@router.get("/followups", response_model=list[schemas.FollowUpOut])
def list_followups(include_completed: bool = False, db=Depends(get_db)):
    q = (
        db.query(FollowUp, Job, Company)
        .join(Application, FollowUp.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .outerjoin(Company, Job.company_id == Company.id)
    )
    if not include_completed:
        q = q.filter(FollowUp.completed.is_(False))
    return [_followup_row(fu, job, company) for fu, job, company in q.all()]


@router.post("/followups", response_model=schemas.FollowUpOut)
def create_followup(body: schemas.FollowUpCreate, db=Depends(get_db)):
    job = db.query(Job).filter_by(id=body.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    app = db.query(Application).filter_by(job_id=body.job_id).first()
    if not app:
        app = Application(job_id=body.job_id, status=ApplicationStatus.applied)
        db.add(app)
        db.flush()

    fu = FollowUp(application_id=app.id, due_date=body.due_date, note=body.note)
    db.add(fu)
    db.commit()
    db.refresh(fu)

    return _followup_row(fu, job, job.company)


@router.patch("/followups/{followup_id}/complete")
def complete_followup(followup_id: UUID, db=Depends(get_db)):
    fu = db.query(FollowUp).filter_by(id=followup_id).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    fu.completed = True
    db.commit()
    return {"completed": True}
