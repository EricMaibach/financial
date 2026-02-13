"""
Briefing Email Service

Handles generation and delivery of daily briefing emails.
Aggregates market data, AI summaries, and user alerts into a comprehensive email.
"""

from datetime import datetime, timedelta
import pytz
from flask import current_app
from services.email_service import send_email
from models.user import User
from models.alert import AlertPreference, Alert
from ai_summary import get_latest_summary
from extensions import db
import logging

logger = logging.getLogger(__name__)


def get_market_briefing_content():
    """
    Fetch AI-generated market briefing

    Returns:
        dict: Contains html, text, and synthesis keys, or None if unavailable
    """
    summary = get_latest_summary()
    if not summary:
        return None

    # Convert to HTML paragraphs
    narrative = summary.get('narrative', '')
    if narrative:
        paragraphs = narrative.split('\n\n')
        briefing_html = ''.join(
            f'<p style="margin: 0 0 15px 0;">{para}</p>'
            for para in paragraphs if para.strip()
        )
    else:
        briefing_html = ''

    briefing_text = narrative

    return {
        'html': briefing_html,
        'text': briefing_text,
        'synthesis': summary.get('one_liner', 'Market conditions update')
    }


def get_market_conditions_summary():
    """
    Get status for 6 market dimensions

    TODO: Implement logic to determine status from actual metrics

    Returns:
        list: List of condition dicts with icon, name, status, badge_color, text_color
    """
    # Placeholder data - will be replaced with actual metric analysis
    return [
        {'icon': '🏦', 'name': 'Credit', 'status': 'Moderate Risk', 'badge_color': '#fff3cd', 'text_color': '#856404'},
        {'icon': '📈', 'name': 'Equity', 'status': 'Neutral', 'badge_color': '#e2e3e5', 'text_color': '#383d41'},
        {'icon': '📊', 'name': 'Rates', 'status': 'Elevated Risk', 'badge_color': '#f8d7da', 'text_color': '#721c24'},
        {'icon': '💵', 'name': 'Dollar', 'status': 'Moderate Calm', 'badge_color': '#d1ecf1', 'text_color': '#0c5460'},
        {'icon': '🛡️', 'name': 'Safe Havens', 'status': 'Elevated Calm', 'badge_color': '#d4edda', 'text_color': '#155724'},
        {'icon': '₿', 'name': 'Crypto', 'status': 'Neutral', 'badge_color': '#e2e3e5', 'text_color': '#383d41'},
    ]


def get_top_movers(limit=5):
    """
    Get top movers from What's Moving Today

    TODO: Implement actual logic from homepage to find metrics with largest percentile changes

    Args:
        limit: Number of top movers to return

    Returns:
        list: List of mover dicts with name, value, percentile, change, change_arrow, change_color
    """
    # Placeholder data - will be replaced with actual metric analysis
    return [
        {
            'name': 'VIX',
            'value': '28.5',
            'percentile': 85,
            'change_arrow': '↑',
            'change': '+5.2',
            'change_color': '#dc3545'
        },
        {
            'name': 'High Yield Spread',
            'value': '276 bp',
            'percentile': 42,
            'change_arrow': '↓',
            'change': '-3 bp',
            'change_color': '#28a745'
        },
        {
            'name': 'Gold',
            'value': '$4,523',
            'percentile': 98,
            'change_arrow': '↑',
            'change': '+1.2%',
            'change_color': '#dc3545'
        },
    ]


def get_user_triggered_alerts(user_id, hours=24):
    """
    Get alerts triggered in last N hours for a user

    Args:
        user_id: User ID to fetch alerts for
        hours: Number of hours to look back (default: 24)

    Returns:
        list: List of alert dicts
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    alerts = Alert.query.filter(
        Alert.user_id == user_id,
        Alert.triggered_at >= cutoff
    ).order_by(Alert.triggered_at.desc()).all()

    return [alert.to_dict() for alert in alerts]


def get_portfolio_analysis_snippet(user):
    """
    Get 1-2 sentence portfolio context for user

    TODO: Integrate with existing portfolio AI analysis from ai_summary.py

    Args:
        user: User object

    Returns:
        str: Portfolio analysis text, or None if not applicable
    """
    # Check if user wants portfolio analysis
    if not user.alert_preferences.include_portfolio_analysis:
        return None

    # Check if user has portfolio allocations
    if not user.portfolio_allocations.count():
        return None

    # Placeholder - will integrate with db_get_latest_portfolio_summary(user.id)
    return "Your 60/40 portfolio is moderately positioned for current risk-off conditions. Consider reviewing equity allocation if VIX remains elevated."


def send_daily_briefing_to_user(user):
    """
    Send daily briefing email to a single user

    Args:
        user: User object to send briefing to

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        prefs = user.alert_preferences

        # Check if briefing is enabled
        if not prefs.daily_briefing_enabled or prefs.briefing_frequency == 'off':
            logger.debug(f"User {user.id}: Daily briefing disabled")
            return False

        # Deduplication: Check if briefing already sent today (in user's timezone)
        user_tz = pytz.timezone(prefs.briefing_timezone)
        today_user_tz = datetime.now(user_tz).date()

        if prefs.last_briefing_sent_date == today_user_tz:
            logger.debug(f"User {user.id}: Briefing already sent today ({today_user_tz})")
            return False

        # Get content
        briefing = get_market_briefing_content()
        if not briefing:
            logger.warning(f"User {user.id}: No market briefing available")
            return False

        conditions = get_market_conditions_summary()
        top_movers = get_top_movers()
        triggered_alerts = get_user_triggered_alerts(user.id)
        portfolio_analysis = get_portfolio_analysis_snippet(user)

        eastern = pytz.timezone('US/Eastern')
        # Prepare template context
        base_url = current_app.config['BASE_URL']
        context = {
            'user': user,
            'briefing_date': datetime.now(eastern).strftime('%A, %B %d, %Y'),
            'market_briefing_html': briefing['html'],
            'market_briefing_text': briefing['text'],
            'market_synthesis': briefing['synthesis'],
            'market_conditions': conditions,
            'top_movers': top_movers,
            'triggered_alerts': triggered_alerts,
            'include_portfolio': prefs.include_portfolio_analysis,
            'portfolio_analysis': portfolio_analysis,
            'dashboard_url': base_url,
            'unsubscribe_url': f"{base_url}/unsubscribe/{user.id}"
        }

        # Send email
        subject = f"Your SignalTrackers Daily Briefing - {datetime.now(eastern).strftime('%b %d')}"
        success = send_email(
            to=user.email,
            subject=subject,
            template_html='email/daily_briefing.html',
            template_txt='email/daily_briefing.txt',
            **context
        )

        if success:
            # Update last sent date to prevent duplicates
            prefs.last_briefing_sent_date = today_user_tz
            db.session.commit()
            logger.info(f"Daily briefing sent to user {user.id} ({user.email})")
        else:
            logger.error(f"Failed to send daily briefing to user {user.id} ({user.email})")

        return success

    except Exception as e:
        logger.error(f"Failed to send daily briefing to user {user.id}: {str(e)}", exc_info=True)
        return False
