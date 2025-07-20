"""Create Matrix Validations knowledge base

Revision ID: 2d7005215343
Revises: 445004fcbe95
Create Date: 2025-07-20 09:21:41.553727

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2d7005215343"
down_revision: Union[str, None] = "445004fcbe95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matrix_skill_knowledgebase",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("skill_id", sa.BigInteger, nullable=False),
        sa.Column("difficulty_level", sa.SmallInteger, nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column("options", sa.JSON, nullable=True),
        sa.Column("question_type", sa.String(20), nullable=False),
        sa.Column("is_code_question", sa.Boolean, nullable=False, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "matrix_knowledgebase_skill_level_idx",
        "matrix_skill_knowledgebase",
        ["skill_id", "difficulty_level"],
    )
    op.create_foreign_key(
        "matrix_skill_skill_id_fk_id",
        "matrix_skill_knowledgebase",
        "skills",
        ["skill_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_table("matrix_skill_knowledgebase")
