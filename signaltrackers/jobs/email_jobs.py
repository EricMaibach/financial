from flask import current_app
import logging
from datetime import datetime, time
import pytz

logger = logging.getLogger(__name__)

def send_daily_briefings():
    """
    Background job to send daily briefing emails
    Runs daily, checks user timezone preferences
    """
    try:
        from models.user import User
        from models.alert import AlertPreference

        logger.info("Starting daily briefing email job...")

        # Get current hour in UTC
        current_hour_utc = datetime.utcnow().hour

        # Find users whose briefing time matches current hour (accounting for timezone)
        # TODO: Implement in US-1.3.4
        # This is a placeholder for now

        logger.info("Daily briefing email job completed")

    except Exception as e:
        logger.error(f"Error sending daily briefings: {str(e)}", exc_info=True)
        # Don't raise - let job continue on next execution


def send_daily_briefings_wrapper():
    """Wrapper to run job with app context"""
    # Import here to avoid circular imports
    from dashboard import app

    with app.app_context():
        send_daily_briefings()
