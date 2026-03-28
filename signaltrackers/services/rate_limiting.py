"""
Anonymous Session Rate Limiting Service

Tracks per-session AI usage for anonymous users via Flask session.
Registered users bypass anonymous session limits.

Designed to be extended by US-12.3.2 (global daily cap) and
US-12.3.3 (per-user registered limits).
"""

import logging
from functools import wraps
from flask import jsonify, session, current_app
from flask_login import current_user

logger = logging.getLogger(__name__)

# Endpoint category constants
CATEGORY_CHATBOT = 'chatbot'
CATEGORY_ANALYSIS = 'analysis'

# Session keys for tracking usage counts
_SESSION_KEY_PREFIX = 'rate_limit_'

# Default limits (overridable via app config)
DEFAULT_LIMITS = {
    CATEGORY_CHATBOT: 5,
    CATEGORY_ANALYSIS: 2,
}


def _get_limit(category):
    """Get the configured limit for a category.

    Checks app config first (set from env vars), falls back to defaults.
    """
    config_key = f'ANON_SESSION_LIMIT_{category.upper()}'
    return current_app.config.get(config_key, DEFAULT_LIMITS.get(category, 0))


def _session_key(category):
    """Get the session storage key for a category counter."""
    return f'{_SESSION_KEY_PREFIX}{category}'


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
            }

        return None

    except Exception:
        # Never block a request due to rate limiting errors
        logger.exception('Anonymous rate limit check error (non-fatal)')
        return None


def anonymous_rate_limit(category):
    """Decorator that enforces anonymous session rate limits on an endpoint.

    Checks the limit before the request and records usage after a successful
    response (2xx status).

    Args:
        category: The endpoint category (CATEGORY_CHATBOT or CATEGORY_ANALYSIS).
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            limit_response = check_anonymous_rate_limit(category)
            if limit_response:
                return jsonify(limit_response), 429

            result = f(*args, **kwargs)

            # Record usage on successful responses
            # Flask views can return (response, status) tuples or Response objects
            status = 200
            if isinstance(result, tuple):
                status = result[1] if len(result) > 1 else 200
            if 200 <= status < 300:
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
