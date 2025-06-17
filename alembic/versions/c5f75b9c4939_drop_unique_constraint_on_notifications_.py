"""Drop unique constraint on notifications chat uuid

Revision ID: c5f75b9c4939
Revises: dbbee43a9430
Create Date: 2025-06-16 20:17:21.654158

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c5f75b9c4939"
down_revision: Union[str, None] = "dbbee43a9430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("notifications_chat_uuid_idx", "notifications")


def downgrade() -> None:
    op.create_index(
        "notifications_chat_uuid_idx", "notifications", ["chat_uuid"], unique=True
    )
