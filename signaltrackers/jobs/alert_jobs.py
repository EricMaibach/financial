from flask import current_app
import logging

logger = logging.getLogger(__name__)


def check_alert_thresholds():
    """
    Background job to check all alert thresholds
    Runs every 15 minutes
    """
    try:
        logger.info("Starting alert threshold check...")

        # Import here to avoid circular imports
        from services.alert_detection_service import check_all_users_alerts

        results = check_all_users_alerts()

        logger.info(
            f"Alert check completed: {results['total_alerts']} alerts created "
            f"for {results['users_alerted']} users ({results['users_checked']} checked)"
        )

    except Exception as e:
        logger.error(f"Error checking alert thresholds: {str(e)}", exc_info=True)
        # Don't raise - let job continue on next execution


def check_alert_thresholds_wrapper():
    """Wrapper to run job with app context"""
    # Import here to avoid circular imports
    from dashboard import app

    with app.app_context():
        check_alert_thresholds()
