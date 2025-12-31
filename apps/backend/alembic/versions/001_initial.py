"""initial

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Admin users
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_users_id'), 'admin_users', ['id'], unique=False)
    op.create_index(op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=True)

    # KB Categories
    op.create_table(
        'kb_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kb_categories_id'), 'kb_categories', ['id'], unique=False)
    op.create_index(op.f('ix_kb_categories_title'), 'kb_categories', ['title'], unique=False)

    # KB QA
    op.create_table(
        'kb_qa',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('answer', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['kb_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kb_qa_id'), 'kb_qa', ['id'], unique=False)
    op.create_index(op.f('ix_kb_qa_category_id'), 'kb_qa', ['category_id'], unique=False)
    op.create_index(op.f('ix_kb_qa_question'), 'kb_qa', ['question'], unique=False)

    # Chat logs
    op.create_table(
        'chat_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('bot_message', sa.Text(), nullable=False),
        sa.Column('sources_json', sa.JSON(), nullable=True),
        sa.Column('refused', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_logs_id'), 'chat_logs', ['id'], unique=False)
    op.create_index(op.f('ix_chat_logs_session_id'), 'chat_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_chat_logs_created_at'), 'chat_logs', ['created_at'], unique=False)

    # Website sources
    op.create_table(
        'website_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('base_url', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('last_crawled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('crawl_status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_website_sources_id'), 'website_sources', ['id'], unique=False)
    op.create_index(op.f('ix_website_sources_base_url'), 'website_sources', ['base_url'], unique=True)

    # Website pages
    op.create_table(
        'website_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('website_source_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['website_source_id'], ['website_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_website_pages_id'), 'website_pages', ['id'], unique=False)
    op.create_index(op.f('ix_website_pages_website_source_id'), 'website_pages', ['website_source_id'], unique=False)
    op.create_index(op.f('ix_website_pages_content_hash'), 'website_pages', ['content_hash'], unique=False)
    op.create_index('idx_website_source_url', 'website_pages', ['website_source_id', 'url'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_website_source_url', table_name='website_pages')
    op.drop_index(op.f('ix_website_pages_content_hash'), table_name='website_pages')
    op.drop_index(op.f('ix_website_pages_website_source_id'), table_name='website_pages')
    op.drop_index(op.f('ix_website_pages_id'), table_name='website_pages')
    op.drop_table('website_pages')
    op.drop_index(op.f('ix_website_sources_base_url'), table_name='website_sources')
    op.drop_index(op.f('ix_website_sources_id'), table_name='website_sources')
    op.drop_table('website_sources')
    op.drop_index(op.f('ix_chat_logs_created_at'), table_name='chat_logs')
    op.drop_index(op.f('ix_chat_logs_session_id'), table_name='chat_logs')
    op.drop_index(op.f('ix_chat_logs_id'), table_name='chat_logs')
    op.drop_table('chat_logs')
    op.drop_index(op.f('ix_kb_qa_question'), table_name='kb_qa')
    op.drop_index(op.f('ix_kb_qa_category_id'), table_name='kb_qa')
    op.drop_index(op.f('ix_kb_qa_id'), table_name='kb_qa')
    op.drop_table('kb_qa')
    op.drop_index(op.f('ix_kb_categories_title'), table_name='kb_categories')
    op.drop_index(op.f('ix_kb_categories_id'), table_name='kb_categories')
    op.drop_table('kb_categories')
    op.drop_index(op.f('ix_admin_users_username'), table_name='admin_users')
    op.drop_index(op.f('ix_admin_users_id'), table_name='admin_users')
    op.drop_table('admin_users')

