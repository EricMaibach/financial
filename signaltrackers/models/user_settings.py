"""
User Settings Model

Stores user preferences. API key columns are deprecated (BYOK removed in Phase 12)
and will be dropped in US-12.1.3 migration.
"""

from datetime import datetime

from extensions import db


class UserSettings(db.Model):
    """User settings."""

    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )

    # Deprecated — kept for US-12.1.3 migration compatibility
    ai_provider = db.Column(db.String(20), default='openai')
    openai_api_key_encrypted = db.Column(db.LargeBinary, nullable=True)
    anthropic_api_key_encrypted = db.Column(db.LargeBinary, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserSettings user_id={self.user_id}>'
