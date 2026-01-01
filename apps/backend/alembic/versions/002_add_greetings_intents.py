"""add greetings and intents

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Greetings table
    op.create_table(
        'greetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_greetings_id'), 'greetings', ['id'], unique=False)
    
    # Intents table
    op.create_table(
        'intents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('keywords', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_intents_id'), 'intents', ['id'], unique=False)
    op.create_index(op.f('ix_intents_name'), 'intents', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_intents_name'), table_name='intents')
    op.drop_index(op.f('ix_intents_id'), table_name='intents')
    op.drop_table('intents')
    op.drop_index(op.f('ix_greetings_id'), table_name='greetings')
    op.drop_table('greetings')





