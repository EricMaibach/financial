"""Add ai_usage_records table

Revision ID: g2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g2a3b4c5d6e7'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'ai_usage_records' not in inspector.get_table_names():
        op.create_table(
            'ai_usage_records',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('interaction_type', sa.String(30), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('input_tokens', sa.Integer(), nullable=True),
            sa.Column('output_tokens', sa.Integer(), nullable=True),
            sa.Column('cache_read_tokens', sa.Integer(), nullable=True),
            sa.Column('cache_creation_tokens', sa.Integer(), nullable=True),
            sa.Column('model', sa.String(100), nullable=False),
            sa.Column('estimated_cost', sa.Numeric(precision=12, scale=8), nullable=False),
        )
    # Create indexes if they don't already exist (table may have been created by db.create_all())
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('ai_usage_records')}
    if 'ix_ai_usage_records_user_id' not in existing_indexes:
        op.create_index('ix_ai_usage_records_user_id', 'ai_usage_records', ['user_id'])
    if 'ix_ai_usage_records_interaction_type' not in existing_indexes:
        op.create_index('ix_ai_usage_records_interaction_type', 'ai_usage_records', ['interaction_type'])
    if 'ix_ai_usage_records_timestamp' not in existing_indexes:
        op.create_index('ix_ai_usage_records_timestamp', 'ai_usage_records', ['timestamp'])
    if 'ix_ai_usage_records_user_type_time' not in existing_indexes:
        op.create_index('ix_ai_usage_records_user_type_time', 'ai_usage_records', ['user_id', 'interaction_type', 'timestamp'])


def downgrade():
    op.drop_index('ix_ai_usage_records_user_type_time', table_name='ai_usage_records')
    op.drop_index('ix_ai_usage_records_timestamp', table_name='ai_usage_records')
    op.drop_index('ix_ai_usage_records_interaction_type', table_name='ai_usage_records')
    op.drop_index('ix_ai_usage_records_user_id', table_name='ai_usage_records')
    op.drop_table('ai_usage_records')
