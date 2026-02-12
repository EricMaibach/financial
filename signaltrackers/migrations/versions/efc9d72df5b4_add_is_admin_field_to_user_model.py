"""Add is_admin field to User model

Revision ID: efc9d72df5b4
Revises: 
Create Date: 2026-02-11 20:30:00.656368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'efc9d72df5b4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove is_admin column from users table
    op.drop_column('users', 'is_admin')
