"""add_ai_actions_to_investigation_history_enum

Revision ID: 8cc8f0c5112d
Revises: 4a309eadde28
Create Date: 2026-08-06 19:03:44.181422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = "xxxxxxxx"
down_revision = "4a309eadde28"   # use your generated value
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TYPE investigationaction
        ADD VALUE IF NOT EXISTS 'AI_INVESTIGATION_STARTED';
        """
    )

    op.execute(
        """
        ALTER TYPE investigationaction
        ADD VALUE IF NOT EXISTS 'AI_INVESTIGATION_COMPLETED';
        """
    )

    op.execute(
        """
        ALTER TYPE investigationaction
        ADD VALUE IF NOT EXISTS 'AI_INVESTIGATION_FAILED';
        """
    )


def downgrade():
    # PostgreSQL doesn't support removing enum values directly.
    pass