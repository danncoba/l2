"""empty message

Revision ID: 4b0251629883
Revises: 38f82d015ac1, user_validation_questions
Create Date: 2025-07-25 07:28:27.694302

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b0251629883"
down_revision: Union[str, None] = ("38f82d015ac1", "user_validation_questions")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
