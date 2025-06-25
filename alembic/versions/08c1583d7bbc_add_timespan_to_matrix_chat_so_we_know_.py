"""add timespan to matrix chat so we know the timeframe we're looking at

Revision ID: 08c1583d7bbc
Revises: d557d582d41a
Create Date: 2025-06-24 21:29:56.636672

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "08c1583d7bbc"
down_revision: Union[str, None] = "d557d582d41a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matrix_chats", sa.Column("timespan_start", sa.BigInteger, nullable=True)
    )
    op.add_column(
        "matrix_chats", sa.Column("timespan_end", sa.BigInteger, nullable=True)
    )
    op.execute("UPDATE matrix_chats SET timespan_start = 1750793567")
    op.execute("UPDATE matrix_chats SET timespan_end = 1750793567")
    op.alter_column("matrix_chats", "timespan_start", nullable=False)
    op.alter_column("matrix_chats", "timespan_end", nullable=False)


def downgrade() -> None:
    op.drop_column("matrix_chats", "timespan_end")
    op.drop_column("matrix_chats", "timespan_start")
