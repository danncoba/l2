"""add configs table

Revision ID: 2f248cd8a97c
Revises: 08c1583d7bbc
Create Date: 2025-06-25 12:29:53.741040

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f248cd8a97c"
down_revision: Union[str, None] = "08c1583d7bbc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "configs",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("matrix_cadence", sa.String(10), nullable=False),
        sa.Column("matrix_interval", sa.BigInteger, nullable=False),
        sa.Column("matrix_duration", sa.BigInteger, nullable=False),
        sa.Column("matrix_ending_at", sa.BigInteger, nullable=False),
        sa.Column("matrix_starting_at", sa.BigInteger, nullable=False),
        sa.Column("matrix_reminders", sa.Boolean, nullable=False, default=False),
        sa.Column("reminders_format", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("configs")
