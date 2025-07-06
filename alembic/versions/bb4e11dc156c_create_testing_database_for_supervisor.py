"""Create Testing database for supervisor

Revision ID: bb4e11dc156c
Revises: c366bd85da49
Create Date: 2025-07-06 11:43:17.092822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb4e11dc156c'
down_revision: Union[str, None] = 'c366bd85da49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
