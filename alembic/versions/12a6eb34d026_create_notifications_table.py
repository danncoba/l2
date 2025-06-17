"""create notifications table

Revision ID: 12a6eb34d026
Revises: b173209e592e
Create Date: 2025-06-15 13:16:53.142369

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import BigInteger

# revision identifiers, used by Alembic.
revision: str = "12a6eb34d026"
down_revision: Union[str, None] = "b173209e592e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id", BigInteger, nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("notification_type", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("chat_uuid", sa.UUID, nullable=True),
    )
    op.create_foreign_key(
        "notifications_user_id_fkey", "notifications", "users", ["user_id"], ["id"]
    )
    op.create_index(
        "notifications_user_id_idx", "notifications", ["user_id"], unique=False
    )
    op.create_index(
        "notifications_chat_uuid_idx", "notifications", ["chat_uuid"], unique=True
    )


def downgrade() -> None:
    op.drop_table("notifications")
