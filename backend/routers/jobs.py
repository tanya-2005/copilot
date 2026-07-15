"""
jobs.py — job listing/detail, generated documents, and contact lookup.
Read-only except for the download endpoint, which only reads too — writes
go through applications.py.
"""
import io
import json
import os
import sys
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "storage"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "documents"))

from models import Application, Company, Contact, GeneratedDocument, Job, JobMatch  # noqa: E402
import exporters  # noqa: E402

from ..deps import get_db  # noqa: E402
from .. import schemas  # noqa: E402

router = APIRouter(tags=["jobs"])


def _job_row(job: Job, company: Optional[Company], match: Optional[JobMatch], app: Optional[Application]) -> dict:
    return {
        "id": job.id,
        "company": company.name if company else "?",
        "title": job.title,
        "location": job.location,
        "remote_type": job.remote_type.value if job.remote_type else "unknown",
        "url": job.url,
        "source": job.source.value,
        "date_discovered": job.date_discovered,
        "date_posted": job.date_posted,
        "score": match.match_score if match else None,
        "reason": match.match_reason if match else None,
        "status": app.status.value if app else "not_applied",
    }


def _jobs_query(db):
    return (
        db.query(Job, Company, JobMatch, Application)
        .outerjoin(Company, Job.company_id == Company.id)
        .outerjoin(JobMatch, JobMatch.job_id == Job.id)
        .outerjoin(Application, Application.job_id == Job.id)
    )


@router.get("/jobs", response_model=list[schemas.JobOut])
def list_jobs(
    status: Optional[list[str]] = Query(None, description="Filter to one or more application statuses"),
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    db=Depends(get_db),
):
    rows = [_job_row(job, company, match, app) for job, company, match, app in _jobs_query(db).all()]

    if status:
        rows = [r for r in rows if r["status"] in status]
    if min_score is not None:
        rows = [r for r in rows if r["score"] is not None and r["score"] >= min_score]
    if search:
        needle = search.lower()
        rows = [r for r in rows if needle in r["company"].lower() or needle in r["title"].lower()]

    rows.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    return rows


@router.get("/jobs/{job_id}", response_model=schemas.JobDetail)
def get_job(job_id: UUID, db=Depends(get_db)):
    row = _jobs_query(db).filter(Job.id == job_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    job, company, match, app = row
    data = _job_row(job, company, match, app)
    data["description_raw"] = job.description_raw
    return data


@router.get("/jobs/{job_id}/documents")
def list_documents(job_id: UUID, db=Depends(get_db)):
    if not db.query(Job.id).filter_by(id=job_id).first():
        raise HTTPException(status_code=404, detail="Job not found")

    docs = db.query(GeneratedDocument).filter_by(job_id=job_id).all()
    out = []
    for d in docs:
        content = d.content_text
        if d.doc_type.value in ("resume", "recruiter_email") and content:
            try:
                content = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass
        out.append({"id": d.id, "doc_type": d.doc_type.value, "content": content, "generated_at": d.generated_at})
    return out


@router.get("/jobs/{job_id}/documents/{doc_type}/download")
def download_document(job_id: UUID, doc_type: str, db=Depends(get_db)):
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    doc = (
        db.query(GeneratedDocument)
        .filter_by(job_id=job_id, doc_type=doc_type)
        .order_by(GeneratedDocument.version.desc())
        .first()
    )
    if not doc or not doc.content_text:
        raise HTTPException(status_code=404, detail="Document not found")

    company_name = job.company.name if job.company else job.title
    data = exporters.build_docx_bytes(doc_type, doc.content_text, company_name, job.title)
    filename = f"{doc_type}_{company_name}_{job.title}.docx".replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/jobs/{job_id}/contact", response_model=Optional[schemas.ContactOut])
def get_contact(job_id: UUID, db=Depends(get_db)):
    contact = db.query(Contact).filter_by(job_id=job_id).first()
    if not contact:
        return None
    return {
        "name": contact.name,
        "title": contact.title,
        "email": contact.email,
        "linkedin_url": contact.linkedin_url,
        "source": contact.source,
        "confidence": contact.confidence.value if contact.confidence else None,
    }
