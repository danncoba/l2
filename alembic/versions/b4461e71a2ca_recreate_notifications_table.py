"""recreate notifications table

Revision ID: b4461e71a2ca
Revises: 539ee750dac3
Create Date: 2025-06-14 14:54:49.480323

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4461e71a2ca"
down_revision: Union[str, None] = "539ee750dac3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
