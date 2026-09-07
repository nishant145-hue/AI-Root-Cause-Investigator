"""add execution analytics to investigations

Revision ID: 7209193b8be9
Revises: b34ea81fde6e
Create Date: 2026-08-19 16:34:19.635324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '7209193b8be9'
down_revision: Union[str, Sequence[str], None] = 'b34ea81fde6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "investigations",
        sa.Column(
            "execution_analytics",
            sa.JSON(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE investigations
        SET execution_analytics = '{}'::json
        WHERE execution_analytics IS NULL
        """
    )

    op.alter_column(
        "investigations",
        "execution_analytics",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column(
        "investigations",
        "execution_analytics",
    )
