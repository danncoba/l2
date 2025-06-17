"""add statuses to both notifications and matrix_chats

Revision ID: f5d6d331092e
Revises: c5f75b9c4939
Create Date: 2025-06-17 07:39:13.622538

"""

import enum
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f5d6d331092e"
down_revision: Union[str, None] = "c5f75b9c4939"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class NotificationType(enum.Enum):
    UNREAD = "UNREAD"
    READ = "READ"


class ChatType(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


def upgrade() -> None:
    op.add_column("notifications", sa.Column("status", sa.String(20), nullable=False))
    op.add_column("matrix_chats", sa.Column("status", sa.String(20), nullable=False))


def downgrade() -> None:
    op.drop_column("matrix_chats", "status")
    op.drop_column("notifications", "status")
