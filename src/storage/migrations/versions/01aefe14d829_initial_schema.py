"""initial schema

Revision ID: 01aefe14d829
Revises:
Create Date: 2026-07-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "01aefe14d829"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ats_type = postgresql.ENUM(
    "greenhouse", "lever", "ashby", "rss", "web_search", "apify", "manual",
    name="atstype", create_type=False
)
remote_type = postgresql.ENUM("remote", "onsite", "hybrid", "unknown", name="remotetype", create_type=False)
doc_type = postgresql.ENUM("resume", "cover_letter", "recruiter_email", name="doctype", create_type=False)
confidence_type = postgresql.ENUM("high", "medium", "low", name="confidence", create_type=False)
application_status = postgresql.ENUM(
    "not_applied", "recommended", "ready_to_apply", "applied",
    "interview", "offer", "rejected", "withdrawn",
    name="applicationstatus", create_type=False
)
applied_via = postgresql.ENUM("auto", "manual", name="appliedvia", create_type=False)
notification_channel = postgresql.ENUM("email", "telegram", name="notificationchannel", create_type=False)
run_type = postgresql.ENUM("discovery", "matching", "apply_check", "reminder_check", name="runtype", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in [ats_type, remote_type, doc_type, confidence_type,
                       application_status, applied_via, notification_channel, run_type]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("ats_type", ats_type, nullable=False),
        sa.Column("board_token", sa.String, nullable=True),
        sa.Column("career_page_url", sa.String, nullable=True),
        sa.Column("apify_actor_id", sa.String, nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("source", ats_type, nullable=False),
        sa.Column("external_id", sa.String, nullable=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("location", sa.String, nullable=True),
        sa.Column("remote_type", remote_type, server_default="unknown"),
        sa.Column("url", sa.String, nullable=False, unique=True),
        sa.Column("description_raw", sa.Text, nullable=True),
        sa.Column("description_hash", sa.String, nullable=True),
        sa.Column("date_posted", sa.Date, nullable=True),
        sa.Column("date_discovered", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("company_id", "external_id", name="uq_company_external_id"),
    )
    op.create_index("ix_jobs_description_hash", "jobs", ["description_hash"])

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_label", sa.String, nullable=False),
        sa.Column("file_path", sa.String, nullable=True),
        sa.Column("text_content", sa.Text, nullable=False),
        sa.Column("is_master", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("match_score", sa.Integer, nullable=False),
        sa.Column("match_reason", sa.Text, nullable=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ai_model_used", sa.String, nullable=True),
        sa.UniqueConstraint("job_id", "resume_id", name="uq_job_resume"),
    )

    op.create_table(
        "generated_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("doc_type", doc_type, nullable=False),
        sa.Column("file_path", sa.String, nullable=True),
        sa.Column("content_text", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("email", sa.String, nullable=True),
        sa.Column("linkedin_url", sa.String, nullable=True),
        sa.Column("source", sa.String, nullable=True),
        sa.Column("confidence", confidence_type, nullable=True),
        sa.Column("found_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False, unique=True),
        sa.Column("status", application_status, nullable=False, server_default="not_applied"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_via", applied_via, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "follow_ups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("completed", sa.Boolean, server_default=sa.false()),
    )

    op.create_table(
        "notifications_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "run_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_type", run_type, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jobs_found", sa.Integer, server_default="0"),
        sa.Column("jobs_new", sa.Integer, server_default="0"),
        sa.Column("errors", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("run_log")
    op.drop_table("notifications_log")
    op.drop_table("follow_ups")
    op.drop_table("applications")
    op.drop_table("contacts")
    op.drop_table("generated_documents")
    op.drop_table("job_matches")
    op.drop_table("resumes")
    op.drop_table("jobs")
    op.drop_table("companies")

    bind = op.get_bind()
    for enum_type in [run_type, notification_channel, applied_via, application_status,
                       confidence_type, doc_type, remote_type, ats_type]:
        enum_type.drop(bind, checkfirst=True)
