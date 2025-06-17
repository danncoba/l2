"""add messages to notification

Revision ID: c74a73a1995d
Revises: 12a6eb34d026
Create Date: 2025-06-16 06:21:28.769229

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c74a73a1995d"
down_revision: Union[str, None] = "12a6eb34d026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications", sa.Column("message", sa.Text, nullable=False, default="N/A")
    )


def downgrade() -> None:
    op.drop_column("notifications", "message")
