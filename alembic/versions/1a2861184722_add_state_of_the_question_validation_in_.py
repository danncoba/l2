"""Add state of the question validation in user validation_questions

Revision ID: 1a2861184722
Revises: 0314d4f7b771
Create Date: 2025-07-28 08:22:20.456517

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1a2861184722"
down_revision: Union[str, None] = "0314d4f7b771"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_validation_questions", sa.Column("status", sa.String(100), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("user_validation_questions", "status")
