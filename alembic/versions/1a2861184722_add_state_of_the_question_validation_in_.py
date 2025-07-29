"""Add state of the question validation in user validation_questions

Revision ID: 1a2861184722
Revises: 0314d4f7b771
Create Date: 2025-07-28 08:22:20.456517

"""
import uuid
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
        "user_validation_questions",
        sa.Column("status",
                  sa.String(100),
                  nullable=True,
                  default="pending")
    )
    op.add_column(
        "user_validation_questions",
        sa.Column("question_uuid",
                  sa.String(100),
                  default=uuid.uuid4(),
                  nullable=True)
    )
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("UPDATE user_validation_questions SET status = 'pending';")
    op.execute("UPDATE user_validation_questions SET question_uuid = uuid_generate_v4();")
    op.alter_column("user_validation_questions", "status", nullable=False)
    op.alter_column("user_validation_questions", "question_uuid", nullable=False)


def downgrade() -> None:
    op.drop_column("user_validation_questions", "question_uuid")
    op.drop_column("user_validation_questions", "status")
