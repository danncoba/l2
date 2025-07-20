"""Create Messages for everything

Revision ID: 445004fcbe95
Revises: bb4e11dc156c
Create Date: 2025-07-14 22:24:42.707564

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "445004fcbe95"
down_revision: Union[str, None] = "bb4e11dc156c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_groups",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("group", sa.String(100), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("message_group_id", sa.BigInteger, nullable=False),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("message_groups")
