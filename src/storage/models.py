"""
models.py — SQLAlchemy ORM models. One class per table from the
architecture doc's schema section. Keep this file as the single source of
truth for the schema; migrations (in migrations/versions/) are generated
from changes here via Alembic, never written by hand against a live DB.
"""
import enum
import datetime
import uuid

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, Date, DateTime, ForeignKey,
    Enum, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid_col():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# ---------------------------------------------------------------- enums
class AtsType(str, enum.Enum):
    greenhouse = "greenhouse"
    lever = "lever"
    ashby = "ashby"
    workday = "workday"
    smartrecruiters = "smartrecruiters"
    rss = "rss"
    web_search = "web_search"
    apify = "apify"
    manual = "manual"


class RemoteType(str, enum.Enum):
    remote = "remote"
    onsite = "onsite"
    hybrid = "hybrid"
    unknown = "unknown"


class DocType(str, enum.Enum):
    resume = "resume"
    cover_letter = "cover_letter"
    recruiter_email = "recruiter_email"


class Confidence(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ApplicationStatus(str, enum.Enum):
    not_applied = "not_applied"
    recommended = "recommended"
    ready_to_apply = "ready_to_apply"
    applied = "applied"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"
    withdrawn = "withdrawn"


class AppliedVia(str, enum.Enum):
    auto = "auto"
    manual = "manual"


class NotificationChannel(str, enum.Enum):
    email = "email"
    telegram = "telegram"


class RunType(str, enum.Enum):
    discovery = "discovery"
    matching = "matching"
    apply_check = "apply_check"
    reminder_check = "reminder_check"


# ---------------------------------------------------------------- tables
class Company(Base):
    __tablename__ = "companies"

    id = _uuid_col()
    name = Column(String, nullable=False)
    ats_type = Column(Enum(AtsType), nullable=False)
    board_token = Column(String, nullable=True)
    career_page_url = Column(String, nullable=True)
    apify_actor_id = Column(String, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobs = relationship("Job", back_populates="company")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("company_id", "external_id", name="uq_company_external_id"),)

    id = _uuid_col()
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    source = Column(Enum(AtsType), nullable=False)
    external_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    remote_type = Column(Enum(RemoteType), default=RemoteType.unknown)
    url = Column(String, unique=True, nullable=False)
    description_raw = Column(Text, nullable=True)
    description_hash = Column(String, nullable=True, index=True)
    date_posted = Column(Date, nullable=True)
    date_discovered = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    company = relationship("Company", back_populates="jobs")
    matches = relationship("JobMatch", back_populates="job")
    documents = relationship("GeneratedDocument", back_populates="job")
    contacts = relationship("Contact", back_populates="job")
    application = relationship("Application", back_populates="job", uselist=False)


class Resume(Base):
    __tablename__ = "resumes"

    id = _uuid_col()
    version_label = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    text_content = Column(Text, nullable=False)
    is_master = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    matches = relationship("JobMatch", back_populates="resume")


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("job_id", "resume_id", name="uq_job_resume"),)

    id = _uuid_col()
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    match_score = Column(Integer, nullable=False)
    match_reason = Column(Text, nullable=True)
    matched_at = Column(DateTime(timezone=True), server_default=func.now())
    ai_model_used = Column(String, nullable=True)

    job = relationship("Job", back_populates="matches")
    resume = relationship("Resume", back_populates="matches")


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = _uuid_col()
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    doc_type = Column(Enum(DocType), nullable=False)
    file_path = Column(String, nullable=True)
    content_text = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="documents")


class Contact(Base):
    __tablename__ = "contacts"

    id = _uuid_col()
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    confidence = Column(Enum(Confidence), nullable=True)
    found_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="contacts")


class Application(Base):
    __tablename__ = "applications"

    id = _uuid_col()
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), unique=True, nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.not_applied, nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    applied_via = Column(Enum(AppliedVia), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    job = relationship("Job", back_populates="application")
    follow_ups = relationship("FollowUp", back_populates="application")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = _uuid_col()
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    due_date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)

    application = relationship("Application", back_populates="follow_ups")


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id = _uuid_col()
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())


class RunLog(Base):
    __tablename__ = "run_log"

    id = _uuid_col()
    run_type = Column(Enum(RunType), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    errors = Column(Text, nullable=True)


class Insight(Base):
    """One periodic AI Insights report: skills gaps, frequently-requested
    tech, companies matched well, resume suggestions, and a weekly summary —
    computed over the trailing `period_days` of job_matches/applications.
    `content` holds the full report as JSON (see src/insights/generator.py)."""
    __tablename__ = "insights"

    id = _uuid_col()
    period_days = Column(Integer, nullable=False)
    jobs_scored = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
