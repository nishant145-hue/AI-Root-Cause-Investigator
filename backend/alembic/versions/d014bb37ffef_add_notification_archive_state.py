"""add notification archive state

Revision ID: GENERATED_BY_ALEMBIC
Revises: cd1f07015f86
Create Date: 2026-08-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "d014bb37ffef"
down_revision: Union[str, Sequence[str], None] = "cd1f07015f86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notification archive state."""

    op.add_column(
        "notifications",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "archived_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_notifications_is_archived"),
        "notifications",
        ["is_archived"],
        unique=False,
    )

    # Existing notifications are active.
    # Remove the temporary database default after initialization.
    op.alter_column(
        "notifications",
        "is_archived",
        server_default=None,
    )


def downgrade() -> None:
    """Remove notification archive state."""

    op.drop_index(
        op.f("ix_notifications_is_archived"),
        table_name="notifications",
    )

    op.drop_column(
        "notifications",
        "archived_at",
    )

    op.drop_column(
        "notifications",
        "is_archived",
    )