"""Add subscription fields to users table

Revision ID: h3a4b5c6d7e8
Revises: g2a3b4c5d6e7
Create Date: 2026-03-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h3a4b5c6d7e8'
down_revision = 'g2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('users')}

    if 'stripe_customer_id' not in existing_columns:
        op.add_column('users', sa.Column(
            'stripe_customer_id', sa.String(255), nullable=True
        ))
    if 'subscription_status' not in existing_columns:
        op.add_column('users', sa.Column(
            'subscription_status', sa.String(20), nullable=False,
            server_default='none'
        ))
    if 'subscription_end_date' not in existing_columns:
        op.add_column('users', sa.Column(
            'subscription_end_date', sa.DateTime(), nullable=True
        ))

    # Create indexes if they don't already exist
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('users')}
    if 'ix_users_stripe_customer_id' not in existing_indexes:
        op.create_index(
            'ix_users_stripe_customer_id', 'users', ['stripe_customer_id'],
            unique=True
        )


def downgrade():
    op.drop_index('ix_users_stripe_customer_id', table_name='users')
    op.drop_column('users', 'subscription_end_date')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_customer_id')
