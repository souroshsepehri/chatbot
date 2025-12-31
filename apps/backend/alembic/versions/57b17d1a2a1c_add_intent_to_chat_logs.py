"""add_intent_to_chat_logs

Revision ID: 57b17d1a2a1c
Revises: 002
Create Date: 2025-12-30 20:07:47.049319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57b17d1a2a1c'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('chat_logs', sa.Column('intent', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_logs', 'intent')

