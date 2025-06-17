"""create users_skills

Revision ID: a9688ba832d9
Revises: b0b6fbddc845
Create Date: 2025-06-14 07:20:32.455452

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a9688ba832d9"
down_revision: Union[str, None] = "b0b6fbddc845"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users_skills",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("skill_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_id", "grade_id"),
        sa.Index("user_grades_idx", "grade_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("users_skills")
