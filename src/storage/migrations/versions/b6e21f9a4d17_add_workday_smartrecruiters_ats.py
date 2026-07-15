"""add workday and smartrecruiters ats types

Revision ID: b6e21f9a4d17
Revises: 01aefe14d829
Create Date: 2026-07-14

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b6e21f9a4d17"
down_revision: Union[str, None] = "01aefe14d829"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE atstype ADD VALUE IF NOT EXISTS 'workday'")
    op.execute("ALTER TYPE atstype ADD VALUE IF NOT EXISTS 'smartrecruiters'")


def downgrade() -> None:
    # Postgres has no direct "remove enum value" operation; downgrading
    # would require rebuilding the type. Left as a no-op — additive-only
    # enum migrations are the accepted tradeoff here.
    pass
