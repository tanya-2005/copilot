"""add insights table

Revision ID: c4d8a1f6e932
Revises: b6e21f9a4d17
Create Date: 2026-07-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c4d8a1f6e932"
down_revision: Union[str, None] = "b6e21f9a4d17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("period_days", sa.Integer, nullable=False),
        sa.Column("jobs_scored", sa.Integer, server_default="0"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("insights")
