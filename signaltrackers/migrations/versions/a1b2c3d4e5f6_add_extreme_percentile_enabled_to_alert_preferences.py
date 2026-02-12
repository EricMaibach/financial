"""Add extreme_percentile_enabled to alert preferences

Revision ID: a1b2c3d4e5f6
Revises: efc9d72df5b4
Create Date: 2026-02-11 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'efc9d72df5b4'
branch_labels = None
depends_on = None


def upgrade():
    # Add extreme_percentile_enabled column to alert_preferences table
    # Set default to True for existing users
    op.add_column('alert_preferences', sa.Column('extreme_percentile_enabled', sa.Boolean(), nullable=False, server_default='1'))


def downgrade():
    # Remove extreme_percentile_enabled column from alert_preferences table
    op.drop_column('alert_preferences', 'extreme_percentile_enabled')
