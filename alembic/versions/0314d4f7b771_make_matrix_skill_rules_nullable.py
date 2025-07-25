"""Make matrix skill rules nullable

Revision ID: 0314d4f7b771
Revises: 4b0251629883
Create Date: 2025-07-25 07:28:54.723961

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0314d4f7b771"
down_revision: Union[str, None] = "4b0251629883"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("matrix_skill_knowledgebase", "rules", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("matrix_skill_knowledgebase", "rules", nullable=False)
