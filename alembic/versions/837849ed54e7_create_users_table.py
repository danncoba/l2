"""create users table

Revision ID: 837849ed54e7
Revises:
Create Date: 2025-06-13 19:55:32.707284

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "837849ed54e7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(100), nullable=False, unique=True),
        sa.Column("password", sa.String(100), nullable=False),
        sa.Column("is_admin", sa.Boolean, nullable=False, default=False),
    )


def downgrade() -> None:
    op.drop_table("users")
