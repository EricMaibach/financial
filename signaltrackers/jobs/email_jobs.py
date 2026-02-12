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
        from services.briefing_email_service import send_daily_briefing_to_user

        logger.info("Starting daily briefing email job...")

        current_time_utc = datetime.utcnow()

        # Get all users with briefings enabled
        users_to_email = User.query.join(AlertPreference).filter(
            AlertPreference.daily_briefing_enabled == True,
            AlertPreference.briefing_frequency == 'daily'
        ).all()

        sent_count = 0
        for user in users_to_email:
            prefs = user.alert_preferences

            # Check if it's time for this user's briefing (within this hour)
            user_tz = pytz.timezone(prefs.briefing_timezone)
            user_time = current_time_utc.astimezone(user_tz)

            # Send if current hour matches user's preferred hour
            if user_time.hour == prefs.briefing_time.hour:
                if send_daily_briefing_to_user(user):
                    sent_count += 1

        logger.info(f"Daily briefing job completed. Sent {sent_count} emails.")

    except Exception as e:
        logger.error(f"Error sending daily briefings: {str(e)}", exc_info=True)
        # Don't raise - let job continue on next execution


def send_daily_briefings_wrapper():
    """Wrapper to run job with app context"""
    # Import here to avoid circular imports
    from dashboard import app

    with app.app_context():
        send_daily_briefings()
