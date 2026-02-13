"""Add last_briefing_sent_date to alert preferences

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_briefing_sent_date column to alert_preferences table
    # This tracks the last date a briefing was sent to prevent duplicates
    op.add_column('alert_preferences', sa.Column('last_briefing_sent_date', sa.Date(), nullable=True))


def downgrade():
    # Remove last_briefing_sent_date column from alert_preferences table
    op.drop_column('alert_preferences', 'last_briefing_sent_date')
