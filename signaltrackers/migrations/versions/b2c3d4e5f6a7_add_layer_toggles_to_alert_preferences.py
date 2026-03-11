"""Add layer_1_enabled, layer_2_enabled, layer_3_enabled to alert_preferences

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-10 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('alert_preferences', sa.Column('layer_1_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('alert_preferences', sa.Column('layer_2_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('alert_preferences', sa.Column('layer_3_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column('alert_preferences', 'layer_3_enabled')
    op.drop_column('alert_preferences', 'layer_2_enabled')
    op.drop_column('alert_preferences', 'layer_1_enabled')
