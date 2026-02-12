"""
Alert Models

Database models for user alert preferences and alert history.
"""

from datetime import datetime

from extensions import db


class AlertPreference(db.Model):
    """User preferences for alerts and daily briefing."""

    __tablename__ = 'alert_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)

    # Daily briefing preferences
    daily_briefing_enabled = db.Column(db.Boolean, default=True, nullable=False)
    briefing_frequency = db.Column(db.String(20), default='daily', nullable=False)  # 'daily', 'weekly', 'off'
    briefing_time = db.Column(db.Time, default=datetime.strptime('07:00', '%H:%M').time(), nullable=False)  # Default 7 AM
    briefing_timezone = db.Column(db.String(50), default='America/New_York', nullable=False)
    include_portfolio_analysis = db.Column(db.Boolean, default=True, nullable=False)

    # Alert preferences
    alerts_enabled = db.Column(db.Boolean, default=True, nullable=False)

    # Smart alert thresholds (None = disabled)
    vix_threshold_25 = db.Column(db.Boolean, default=True, nullable=False)
    vix_threshold_30 = db.Column(db.Boolean, default=True, nullable=False)
    credit_spread_threshold_50bp = db.Column(db.Boolean, default=True, nullable=False)
    yield_curve_inversion = db.Column(db.Boolean, default=True, nullable=False)
    equity_breadth_deterioration = db.Column(db.Boolean, default=True, nullable=False)
    extreme_percentile_enabled = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('alert_preferences', uselist=False))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AlertPreference user_id={self.user_id}>'


class Alert(db.Model):
    """Alert history/audit trail."""

    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # 'vix_spike', 'credit_spread', etc.
    title = db.Column(db.String(200), nullable=False)  # "VIX crossed 30 threshold"
    message = db.Column(db.Text, nullable=True)  # Optional detailed message
    severity = db.Column(db.String(20), default='info', nullable=False)  # 'info', 'warning', 'critical'

    # Metric context
    metric_name = db.Column(db.String(100), nullable=True)
    metric_value = db.Column(db.Float, nullable=True)
    threshold_value = db.Column(db.Float, nullable=True)

    # Status tracking
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('alerts', lazy='dynamic'))

    def __repr__(self):
        return f'<Alert {self.alert_type} user_id={self.user_id}>'

    def to_dict(self):
        """Serialize alert for API/UI."""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'severity': self.severity,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold_value': self.threshold_value,
            'triggered_at': self.triggered_at.isoformat(),
            'email_sent': self.email_sent,
            'read': self.read
        }
