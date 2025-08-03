"""update vlidation question with status and grade

Revision ID: e22d2ed15ec5
Revises: 1a2861184722
Create Date: 2025-08-03 12:09:35.606540

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e22d2ed15ec5"
down_revision: Union[str, None] = "1a2861184722"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_validation_questions",
        sa.Column("answer_correct", sa.Boolean, nullable=True, default=False),
    )
    # Can be PENDING, WAITING_ADMIN, VALIDATED
    op.execute("UPDATE user_validation_questions SET answer_correct=False")
    op.alter_column("user_validation_questions", "answer_correct", nullable=False)


def downgrade() -> None:
    op.drop_column("user_validation_questions", "answer_correct")
