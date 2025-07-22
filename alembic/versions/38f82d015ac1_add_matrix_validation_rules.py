"""Add matrix validation rules

Revision ID: 38f82d015ac1
Revises: 2d7005215343
Create Date: 2025-07-22 16:09:29.018824

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "38f82d015ac1"
down_revision: Union[str, None] = "2d7005215343"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matrix_skill_knowledgebase", sa.Column("rules", sa.Text, nullable=True)
    )
    op.execute(
        "UPDATE matrix_skill_knowledgebase SET rules = 'sample' WHERE rules IS NULL"
    )
    op.alter_column("matrix_skill_knowledgebase", "rules", nullable=False)


def downgrade() -> None:
    op.drop_column("matrix_skill_knowledgebase", "rules")
