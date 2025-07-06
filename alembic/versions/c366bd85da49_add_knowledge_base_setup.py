"""Add knowledge base setup

Revision ID: c366bd85da49
Revises: 64ef4c73b0ef
Create Date: 2025-07-04 08:00:18.866743

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import UUID
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "c366bd85da49"
down_revision: Union[str, None] = "64ef4c73b0ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'knowledge_base',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('area', sa.String(255), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create index for vector similarity search
    op.execute("""
               CREATE INDEX IF NOT EXISTS idx_embeddings_cosine
                   ON knowledge_base USING ivfflat (embedding vector_cosine_ops)
                   WITH (lists = 100)
               """)


def downgrade() -> None:
    op.drop_table('knowledge_base')
    op.execute('DROP EXTENSION IF EXISTS vector')
