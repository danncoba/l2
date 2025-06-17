"""create chat for matrix validation

Revision ID: b257114838b7
Revises: c74a73a1995d
Create Date: 2025-06-16 07:52:18.915721

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b257114838b7"
down_revision: Union[str, None] = "c74a73a1995d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "matrix_chats",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("skill_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_foreign_key(
        "matrix_chats_user_id_fkey", "matrix_chats", "users", ["user_id"], ["id"]
    )
    op.create_foreign_key(
        "matrix_chats_skill_id_fkey", "matrix_chats", "skills", ["skill_id"], ["id"]
    )
    op.create_index(
        "matrix_chats_user_skill_id_idx",
        "matrix_chats",
        ["user_id", "skill_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("matrix_chats")
