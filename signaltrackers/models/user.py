"""
User Model

Database model for user accounts with secure password hashing
and Stripe subscription tracking.
"""

import enum
import uuid
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class SubscriptionStatus(enum.Enum):
    """Well-defined subscription states for paid subscribers."""
    ACTIVE = 'active'
    PAST_DUE = 'past_due'
    CANCELED = 'canceled'
    NONE = 'none'


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
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Stripe subscription fields
    stripe_customer_id = db.Column(
        db.String(255), unique=True, nullable=True, index=True
    )
    subscription_status = db.Column(
        db.String(20), nullable=False, default=SubscriptionStatus.NONE.value
    )
    subscription_end_date = db.Column(db.DateTime, nullable=True)

    # Relationships
    portfolio_allocations = db.relationship(
        'PortfolioAllocation',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def has_paid_access(self):
        """Determine if user has paid subscriber access.

        Business rules:
        - active: full paid access
        - past_due: retain access (Stripe is retrying payment)
        - canceled: retain access until subscription_end_date passes
        - none: no paid access
        """
        status = self.subscription_status
        if status in (SubscriptionStatus.ACTIVE.value, SubscriptionStatus.PAST_DUE.value):
            return True
        if status == SubscriptionStatus.CANCELED.value:
            if self.subscription_end_date is None:
                return False
            now = datetime.now(timezone.utc)
            end = self.subscription_end_date
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            return now < end
        return False

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()

    def create_default_alert_preferences(self):
        """Create default alert preferences for new user."""
        from models.alert import AlertPreference

        if not self.alert_preferences:
            prefs = AlertPreference(user_id=self.id)
            db.session.add(prefs)
            db.session.commit()

        return self.alert_preferences

    def __repr__(self):
        return f'<User {self.username}>'
