"""add login attempt tracking

Revision ID: b34ea81fde6e
Revises: d014bb37ffef
Create Date: 2026-08-09 22:10:09.384225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'b34ea81fde6e'
down_revision: Union[str, Sequence[str], None] = 'd014bb37ffef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "locked_until",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute(
        "UPDATE users "
        "SET failed_login_attempts = 0 "
        "WHERE failed_login_attempts IS NULL"
    )

    op.alter_column(
        "users",
        "failed_login_attempts",
        existing_type=sa.Integer(),
        nullable=False,
    )

def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
