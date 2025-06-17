"""add notification message and user group

Revision ID: 10d0f6fafe00
Revises: b257114838b7
Create Date: 2025-06-16 19:57:21.034374

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "10d0f6fafe00"
down_revision: Union[str, None] = "b257114838b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications", sa.Column("user_group", sa.String(20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("notifications", "user_group")
