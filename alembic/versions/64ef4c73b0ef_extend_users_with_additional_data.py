"""extend users with additional data

Revision ID: 64ef4c73b0ef
Revises: 2f248cd8a97c
Create Date: 2025-06-26 07:28:32.090433

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "64ef4c73b0ef"
down_revision: Union[str, None] = "2f248cd8a97c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("description", sa.Text, nullable=True))
    op.add_column("users", sa.Column("profile_pic", sa.String, nullable=True))
    op.add_column("users", sa.Column("city", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("address", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("phone_number", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("additional_data", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("users", "additional_data")
    op.drop_column("users", "phone_number")
    op.drop_column("users", "address")
    op.drop_column("users", "city")
    op.drop_column("users", "profile_pic")
    op.drop_column("users", "description")
