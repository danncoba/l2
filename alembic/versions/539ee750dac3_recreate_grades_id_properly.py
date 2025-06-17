"""recreate grades id properly

Revision ID: 539ee750dac3
Revises: a9688ba832d9
Create Date: 2025-06-14 11:52:28.592061

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "539ee750dac3"
down_revision: Union[str, None] = "a9688ba832d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("grades", "id")
    op.add_column("grades", sa.Column("id", sa.BigInteger, primary_key=True))
    pass


def downgrade() -> None:
    op.drop_column("grades", "id")
    op.add_column("grades", sa.Column("id", sa.BigInteger))
    pass
