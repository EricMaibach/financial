"""
User Model

Database model for user accounts with secure password hashing.
"""

import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    settings = db.relationship(
        'UserSettings',
        backref='user',
        uselist=False,
        lazy=True,
        cascade='all, delete-orphan'
    )
    portfolio_allocations = db.relationship(
        'PortfolioAllocation',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()

    def __repr__(self):
        return f'<User {self.username}>'
