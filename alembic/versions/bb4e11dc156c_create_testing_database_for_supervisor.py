"""Create Testing database for supervisor

Revision ID: bb4e11dc156c
Revises: c366bd85da49
Create Date: 2025-07-06 11:43:17.092822

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bb4e11dc156c"
down_revision: Union[str, None] = "c366bd85da49"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_supervisor_matrix",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("skill_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_foreign_key(
        "supervisor_matrix_user_id",
        "test_supervisor_matrix",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "supervisor_matrix_skill_id",
        "test_supervisor_matrix",
        "skills",
        ["skill_id"],
        ["id"],
    )
    op.create_index(
        "test_supervisor_matrix_skill_id_idx",
        "matrix_chats",
        ["user_id", "skill_id"],
        unique=False,
    )

    op.create_table(
        "text_supervisor_welcome_msg",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("supervisor_matrix_id", sa.UUID(), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
    )
    op.create_foreign_key(
        "welcome_msg_supervisor_matrix_fkey_id",
        "text_supervisor_welcome_msg",
        "test_supervisor_matrix",
        ["supervisor_matrix_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_table("test_supervisor_matrix")
    pass
