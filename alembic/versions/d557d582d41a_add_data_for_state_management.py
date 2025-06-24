"""add data for state management

Revision ID: d557d582d41a
Revises: f5d6d331092e
Create Date: 2025-06-24 07:25:04.810645

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d557d582d41a"
down_revision: Union[str, None] = "f5d6d331092e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "runnables",
        sa.Column("thread_id", sa.UUID(), primary_key=True),
        sa.Column("recursion_limit", sa.Integer(), nullable=False),
        sa.Column("max_concurrency", sa.Integer(), nullable=True),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("run_name", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("thread_id"),
    )
    op.create_index("runnables_run_id_idx", "runnables", ["run_id"], unique=True)

    op.create_table(
        "runnables_metadata",
        sa.Column("metadata_id", sa.UUID(), primary_key=True),
        sa.Column("thread_id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("metadata_id"),
    )
    op.create_foreign_key(
        "runnables_metadata_thread_id_fkey",
        "runnables_metadata",
        "runnables",
        ["thread_id"],
        ["thread_id"],
    )
    op.create_index(
        "runnables_metadata_run_id_idx", "runnables_metadata", ["run_id"], unique=False
    )
    op.create_index(
        "runnables_metadata_key_idx", "runnables_metadata", ["key"], unique=False
    )

    op.create_table(
        "runnables_tags",
        sa.Column("tag_id", sa.UUID(), primary_key=True),
        sa.Column("thread_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.create_foreign_key(
        "runnables_tags_thread_id_fkey",
        "runnables_tags",
        "runnables",
        ["thread_id"],
        ["thread_id"],
    )
    op.create_index(
        "runnables_tags_thread_id_idx", "runnables_tags", ["thread_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("runnables_tags")
    op.drop_table("runnables_metadata")
    op.drop_table("runnables")
