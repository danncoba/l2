"""add foreign keys to users_skills

Revision ID: b173209e592e
Revises: b4461e71a2ca
Create Date: 2025-06-15 13:07:46.529685

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b173209e592e"
down_revision: Union[str, None] = "b4461e71a2ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "users_skills_skill_id_fkey", "users_skills", "skills", ["skill_id"], ["id"]
    )
    op.create_foreign_key(
        "users_skills_user_id_fkey", "users_skills", "users", ["user_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("users_skills_user_id_fkey", "users_skills")
    op.drop_constraint("users_skills_skill_id_fkey", "users_skills")
