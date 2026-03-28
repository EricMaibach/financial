"""
AI Rate Limiting Service

Three layers of rate limiting:
1. Global daily cap — total anonymous AI calls across all sessions per day (US-12.3.2)
2. Per-session limits — per-session caps by endpoint category (US-12.3.1)
3. Registered daily limits — per-user daily caps by category (US-12.3.3)

Anonymous users: layers 1 + 2.
Registered users: layer 3 only (bypass anonymous limits).
"""

import logging
import threading
from datetime import datetime, timezone
from functools import wraps
from flask import jsonify, session, current_app
from flask_login import current_user

logger = logging.getLogger(__name__)

# Endpoint category constants
CATEGORY_CHATBOT = 'chatbot'
CATEGORY_ANALYSIS = 'analysis'

# Session keys for tracking usage counts
_SESSION_KEY_PREFIX = 'rate_limit_'

# Default anonymous session limits (overridable via app config)
DEFAULT_LIMITS = {
    CATEGORY_CHATBOT: 5,
    CATEGORY_ANALYSIS: 2,
}

# Default global daily anonymous cap
DEFAULT_GLOBAL_DAILY_LIMIT = 100

# Default registered user daily limits (overridable via app config)
DEFAULT_REGISTERED_DAILY_LIMITS = {
    CATEGORY_CHATBOT: 25,
    CATEGORY_ANALYSIS: 5,
}

# Maps rate limit categories to ai_usage_records interaction_types
_CATEGORY_INTERACTION_TYPES = {
    CATEGORY_CHATBOT: ['chatbot', 'section_ai', 'sentence_drill_in'],
    CATEGORY_ANALYSIS: ['portfolio_analysis'],
}

# ---------------------------------------------------------------------------
# Global daily anonymous counter (in-memory, resets at midnight UTC)
# ---------------------------------------------------------------------------
_global_lock = threading.Lock()
_global_count = 0
_global_date = None  # UTC date of the current counter window


def _get_limit(category):
    """Get the configured limit for a category.

    Checks app config first (set from env vars), falls back to defaults.
    """
    config_key = f'ANON_SESSION_LIMIT_{category.upper()}'
    return current_app.config.get(config_key, DEFAULT_LIMITS.get(category, 0))


def _session_key(category):
    """Get the session storage key for a category counter."""
    return f'{_SESSION_KEY_PREFIX}{category}'


def _get_global_daily_limit():
    """Get the configured global daily anonymous cap.

    Checks app config first (ANON_GLOBAL_DAILY_LIMIT env var), falls back to default.
    """
    return current_app.config.get('ANON_GLOBAL_DAILY_LIMIT', DEFAULT_GLOBAL_DAILY_LIMIT)


def _reset_if_new_day():
    """Reset the global counter if the UTC date has changed.

    Must be called while holding _global_lock.
    """
    global _global_count, _global_date
    today = datetime.now(timezone.utc).date()
    if _global_date != today:
        _global_count = 0
        _global_date = today


def check_global_anonymous_limit():
    """Check if the global daily anonymous cap has been reached.

    Returns:
        None if the request is allowed.
        A dict with rate limit response data if the global cap is hit.
    """
    try:
        if current_user.is_authenticated:
            return None

        limit = _get_global_daily_limit()

        with _global_lock:
            _reset_if_new_day()
            if _global_count >= limit:
                return {
                    'limited': True,
                    'message': (
                        'Our free AI features have reached their daily limit. '
                        'Create a free account to get guaranteed access and '
                        'higher limits.'
                    ),
                    'limit_type': 'anonymous_global_daily',
                    'signup_url': '/register',
                }

        return None

    except Exception:
        logger.exception('Global anonymous rate limit check error (non-fatal)')
        return None


def record_global_anonymous_usage():
    """Increment the global daily anonymous counter.

    Call this AFTER a successful AI response is generated.
    """
    try:
        if current_user.is_authenticated:
            return

        with _global_lock:
            _reset_if_new_day()
            global _global_count
            _global_count += 1

    except Exception:
        logger.exception('Global anonymous rate limit record error (non-fatal)')


def check_anonymous_rate_limit(category):
    """Check if the current anonymous session has exceeded its rate limit.

    Args:
        category: The endpoint category (CATEGORY_CHATBOT or CATEGORY_ANALYSIS).

    Returns:
        None if the request is allowed.
        A dict with rate limit response data if the request should be blocked.
    """
    try:
        # Registered users bypass anonymous session limits
        if current_user.is_authenticated:
            return None

        limit = _get_limit(category)
        key = _session_key(category)
        current_count = session.get(key, 0)

        if current_count >= limit:
            return {
                'limited': True,
                'message': (
                    'You\'ve reached your free session limit for this feature. '
                    'Create a free account to get higher limits and a '
                    'personalized experience.'
                ),
                'limit_type': 'anonymous_session',
                'category': category,
                'signup_url': '/register',
            }

        return None

    except Exception:
        # Never block a request due to rate limiting errors
        logger.exception('Anonymous rate limit check error (non-fatal)')
        return None


def _get_registered_daily_limit(category):
    """Get the configured registered user daily limit for a category.

    Checks app config first (set from env vars), falls back to defaults.
    """
    config_key = f'REGISTERED_DAILY_LIMIT_{category.upper()}'
    return current_app.config.get(
        config_key, DEFAULT_REGISTERED_DAILY_LIMITS.get(category, 0)
    )


def check_registered_daily_limit(category):
    """Check if the current registered user has exceeded their daily limit.

    Queries ai_usage_records for today's usage count by interaction type.

    Args:
        category: The endpoint category (CATEGORY_CHATBOT or CATEGORY_ANALYSIS).

    Returns:
        None if the request is allowed.
        A dict with rate limit response data if the daily limit is hit.
    """
    try:
        if not current_user.is_authenticated:
            return None

        from extensions import db
        from models.ai_usage import AIUsageRecord

        limit = _get_registered_daily_limit(category)
        interaction_types = _CATEGORY_INTERACTION_TYPES.get(category, [])

        if not interaction_types or limit <= 0:
            return None

        # Count today's usage (UTC) across all interaction types for this category
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        count = db.session.query(db.func.count(AIUsageRecord.id)).filter(
            AIUsageRecord.user_id == current_user.id,
            AIUsageRecord.interaction_type.in_(interaction_types),
            AIUsageRecord.timestamp >= today_start,
        ).scalar() or 0

        if count >= limit:
            return {
                'limited': True,
                'message': (
                    "You've reached your daily limit for this feature. "
                    "Your limit resets tomorrow at midnight UTC."
                ),
                'limit_type': 'registered_daily',
                'category': category,
            }

        return None

    except Exception:
        logger.exception('Registered daily rate limit check error (non-fatal)')
        return None


def anonymous_rate_limit(category):
    """Decorator that enforces rate limits on an endpoint.

    For anonymous users (check order, fail fast):
    1. Global daily anonymous cap (US-12.3.2)
    2. Per-session limit (US-12.3.1)

    For registered users:
    3. Per-user daily limit (US-12.3.3)

    Records usage on anonymous counters after a successful response (2xx status).
    Registered user usage is recorded by the metering system (usage_metering.py).

    Args:
        category: The endpoint category (CATEGORY_CHATBOT or CATEGORY_ANALYSIS).
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Registered users: check daily limit
            registered_limit = check_registered_daily_limit(category)
            if registered_limit:
                return jsonify(registered_limit), 429

            # Anonymous users: global cap check first (fail fast)
            global_limit = check_global_anonymous_limit()
            if global_limit:
                return jsonify(global_limit), 429

            # Anonymous users: per-session check
            limit_response = check_anonymous_rate_limit(category)
            if limit_response:
                return jsonify(limit_response), 429

            result = f(*args, **kwargs)

            # Record anonymous usage on successful responses
            # Flask views can return (response, status) tuples or Response objects
            status = 200
            if isinstance(result, tuple):
                status = result[1] if len(result) > 1 else 200
            if 200 <= status < 300:
                record_global_anonymous_usage()
                record_anonymous_usage(category)

            return result
        return wrapped
    return decorator


def record_anonymous_usage(category):
    """Increment the anonymous session usage counter for a category.

    Call this AFTER a successful AI response is generated (not before).

    Args:
        category: The endpoint category (CATEGORY_CHATBOT or CATEGORY_ANALYSIS).
    """
    try:
        if current_user.is_authenticated:
            return

        key = _session_key(category)
        session[key] = session.get(key, 0) + 1

    except Exception:
        # Never break AI features due to rate limiting errors
        logger.exception('Anonymous rate limit record error (non-fatal)')
