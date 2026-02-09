"""
Portfolio Summary Model

Database model for user-specific AI portfolio analysis summaries.
"""

import uuid
from datetime import datetime

from extensions import db


class PortfolioSummary(db.Model):
    """AI-generated portfolio analysis summary - one per user per day."""

    __tablename__ = 'portfolio_summaries'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Summary content
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD format
    summary = db.Column(db.Text, nullable=False)
    portfolio_context = db.Column(db.Text, nullable=True)  # Snapshot of portfolio at generation time

    # Timestamps
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint: one summary per user per day
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'date': self.date,
            'summary': self.summary,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'portfolio_context': self.portfolio_context
        }

    def __repr__(self):
        return f'<PortfolioSummary user_id={self.user_id} date={self.date}>'
