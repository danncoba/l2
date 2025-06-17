"""create skills table

Revision ID: 96ad56939ede
Revises: 837849ed54e7
Create Date: 2025-06-13 20:00:20.661680

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "96ad56939ede"
down_revision: Union[str, None] = "837849ed54e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grades",
        sa.Column("id", sa.BigInteger, nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("value", sa.Integer, nullable=False, unique=True),
        sa.Column("deleted", sa.Boolean, nullable=False, default=False),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("grades")
    pass
