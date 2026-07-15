"""
schemas.py — Pydantic request/response models for the API. Mirrors the
SQLAlchemy models in src/storage/models.py but only exposes what a frontend
actually needs (e.g. company name, not company_id).
"""
import datetime
import uuid
from typing import Optional

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID
    company: str
    title: str
    location: Optional[str] = None
    remote_type: str
    url: str
    source: str
    date_discovered: datetime.datetime
    date_posted: Optional[datetime.date] = None
    score: Optional[int] = None
    reason: Optional[str] = None
    status: str


class JobDetail(JobOut):
    description_raw: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class FollowUpCreate(BaseModel):
    job_id: uuid.UUID
    due_date: datetime.date
    note: str = "Follow up on application"


class FollowUpOut(BaseModel):
    id: uuid.UUID
    company: str
    title: str
    due_date: datetime.date
    note: Optional[str] = None
    completed: bool


class ContactOut(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[str] = None
