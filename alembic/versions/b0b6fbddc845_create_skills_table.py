"""create skills table

Revision ID: b0b6fbddc845
Revises: 96ad56939ede
Create Date: 2025-06-14 07:10:27.304808

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import BigInteger

# revision identifiers, used by Alembic.
revision: str = "b0b6fbddc845"
down_revision: Union[str, None] = "96ad56939ede"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", BigInteger(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], ["skills.id"]),
        sa.Index("idx_skills_parent_id", "parent_id"),
    )


def downgrade() -> None:
    op.drop_table("skills")
