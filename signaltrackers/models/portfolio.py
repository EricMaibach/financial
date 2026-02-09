"""
Portfolio Allocation Model

Database model for user portfolio allocations.
Replaces the file-based portfolio.json storage.
"""

import uuid
from datetime import datetime

from extensions import db


class PortfolioAllocation(db.Model):
    """Portfolio allocation model - one entry per asset in user's portfolio."""

    __tablename__ = 'portfolio_allocations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Asset details
    asset_type = db.Column(db.String(20), nullable=False)  # stock, etf, mutual_fund, crypto, gold, cash, etc.
    symbol = db.Column(db.String(20), nullable=True)  # Ticker symbol (for stocks/ETFs/mutual funds)
    name = db.Column(db.String(100), nullable=False)  # Display name
    percentage = db.Column(db.Float, nullable=False)  # Allocation percentage (0-100)

    # Timestamps
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'asset_type': self.asset_type,
            'symbol': self.symbol,
            'name': self.name,
            'percentage': self.percentage,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<PortfolioAllocation {self.name} ({self.percentage}%)>'
