"""add nullable to notification user_id when sending group notification

Revision ID: dbbee43a9430
Revises: 10d0f6fafe00
Create Date: 2025-06-16 20:11:22.779716

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dbbee43a9430"
down_revision: Union[str, None] = "10d0f6fafe00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("notifications", "user_id", nullable=True)


def downgrade() -> None:
    op.alter_column("notifications", "user_id", nullable=False)
