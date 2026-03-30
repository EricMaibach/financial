"""
US-13.1.4: Subscription Lifecycle & Access Control

Tests for:
- Centralized access control via user_has_paid_access()
- Rate limiting correctly differentiates paid vs unpaid authenticated users
- All subscription states (active, past_due, canceled, none) handled correctly
- Grace periods: past_due retains access, canceled retains until end_date
- Downgrade: expired subscribers treated as anonymous
- Edge cases: null end_date, boundary dates, status transitions
"""

import ast
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

USER_MODEL_FILE = SIGNALTRACKERS_DIR / 'models' / 'user.py'
RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'

USER_MODEL_SOURCE = USER_MODEL_FILE.read_text()
RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(status='none', end_date=None):
    """Create a mock user with subscription fields."""
    user = MagicMock()
    user.is_authenticated = True
    user.subscription_status = status
    user.subscription_end_date = end_date

    # Wire up has_paid_access using the real property logic
    from models.user import User
    user.has_paid_access = User.has_paid_access.fget(user)

    return user


def _get_function_source(source, func_name):
    """Extract function source from a module source string."""
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return '\n'.join(lines[node.lineno - 1:node.end_lineno])
    return ''


# ---------------------------------------------------------------------------
# Centralized Access Control — user_has_paid_access
# ---------------------------------------------------------------------------

class TestCentralizedAccessControl:
    """Verify a centralized access check function exists and is used."""

    def test_user_has_paid_access_function_exists(self):
        """rate_limiting.py exports a user_has_paid_access function."""
        assert 'def user_has_paid_access' in RATE_LIMITING_SOURCE

    def test_user_has_paid_access_checks_authentication(self):
        """user_has_paid_access checks is_authenticated."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'user_has_paid_access')
        assert 'is_authenticated' in func_src

    def test_user_has_paid_access_checks_paid_access(self):
        """user_has_paid_access checks has_paid_access property."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'user_has_paid_access')
        assert 'has_paid_access' in func_src

    def test_user_has_paid_access_importable(self):
        """user_has_paid_access is importable by other modules."""
        assert 'user_has_paid_access' in DASHBOARD_SOURCE


# ---------------------------------------------------------------------------
# Rate Limiting Uses Paid Access (Not Just is_authenticated)
# ---------------------------------------------------------------------------

class TestRateLimitingUsesPaidAccess:
    """Verify rate limiting functions use has_paid_access, not just is_authenticated."""

    def test_check_global_limit_uses_paid_access(self):
        """check_global_anonymous_limit uses user_has_paid_access, not is_authenticated."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        assert 'user_has_paid_access()' in func_src
        assert 'current_user.is_authenticated' not in func_src

    def test_record_global_usage_uses_paid_access(self):
        """record_global_anonymous_usage uses user_has_paid_access, not is_authenticated."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'record_global_anonymous_usage')
        assert 'user_has_paid_access()' in func_src
        assert 'current_user.is_authenticated' not in func_src

    def test_check_anonymous_limit_uses_paid_access(self):
        """check_anonymous_rate_limit uses user_has_paid_access, not is_authenticated."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'check_anonymous_rate_limit')
        assert 'user_has_paid_access()' in func_src
        assert 'current_user.is_authenticated' not in func_src

    def test_record_anonymous_usage_uses_paid_access(self):
        """record_anonymous_usage uses user_has_paid_access, not is_authenticated."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'record_anonymous_usage')
        assert 'user_has_paid_access()' in func_src
        assert 'current_user.is_authenticated' not in func_src

    def test_subscriber_daily_limit_uses_paid_access(self):
        """check_subscriber_daily_limit uses user_has_paid_access."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit')
        assert 'user_has_paid_access()' in func_src

    def test_no_scattered_is_authenticated_in_rate_functions(self):
        """Rate limiting functions don't use bare is_authenticated for access gating."""
        functions_to_check = [
            'check_global_anonymous_limit',
            'record_global_anonymous_usage',
            'check_anonymous_rate_limit',
            'record_anonymous_usage',
            'check_subscriber_daily_limit',
        ]
        for func_name in functions_to_check:
            func_src = _get_function_source(RATE_LIMITING_SOURCE, func_name)
            assert 'current_user.is_authenticated' not in func_src, \
                f"{func_name} still uses current_user.is_authenticated directly"


# ---------------------------------------------------------------------------
# Access Control by Subscription Status
# ---------------------------------------------------------------------------

class TestAccessByStatus:
    """Verify has_paid_access returns correct results for each status."""

    def test_active_has_access(self):
        """Active subscriber has full paid-tier access."""
        user = _make_user(status='active')
        assert user.has_paid_access is True

    def test_past_due_has_access(self):
        """Past-due subscriber retains access (Stripe retry grace period)."""
        user = _make_user(status='past_due')
        assert user.has_paid_access is True

    def test_canceled_future_end_date_has_access(self):
        """Canceled subscriber with future end date retains access."""
        future = datetime.now(timezone.utc) + timedelta(days=14)
        user = _make_user(status='canceled', end_date=future)
        assert user.has_paid_access is True

    def test_canceled_past_end_date_no_access(self):
        """Canceled subscriber past end date has no access."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = _make_user(status='canceled', end_date=past)
        assert user.has_paid_access is False

    def test_canceled_null_end_date_no_access(self):
        """Canceled with null end_date treated as expired (safe default)."""
        user = _make_user(status='canceled', end_date=None)
        assert user.has_paid_access is False

    def test_none_status_no_access(self):
        """User with no subscription has no paid access."""
        user = _make_user(status='none')
        assert user.has_paid_access is False

    def test_anonymous_user_no_access(self):
        """Anonymous (unauthenticated) user has no paid access."""
        user = MagicMock()
        user.is_authenticated = False
        user.subscription_status = 'none'
        user.subscription_end_date = None
        # Anonymous users don't reach has_paid_access in real code,
        # but user_has_paid_access() handles them
        from models.user import User
        user.has_paid_access = User.has_paid_access.fget(user)
        assert user.has_paid_access is False


# ---------------------------------------------------------------------------
# Grace Period Tests — Past Due
# ---------------------------------------------------------------------------

class TestPastDueGracePeriod:
    """Verify past_due users retain full access during Stripe retries."""

    def test_past_due_retains_access_immediately(self):
        """User retains access immediately after payment failure."""
        user = _make_user(status='past_due')
        assert user.has_paid_access is True

    def test_past_due_retains_access_regardless_of_end_date(self):
        """Past_due status grants access even if end_date is past."""
        past = datetime.now(timezone.utc) - timedelta(days=5)
        user = _make_user(status='past_due', end_date=past)
        assert user.has_paid_access is True

    def test_past_due_with_null_end_date(self):
        """Past_due with null end_date still has access."""
        user = _make_user(status='past_due', end_date=None)
        assert user.has_paid_access is True


# ---------------------------------------------------------------------------
# Grace Period Tests — Cancellation
# ---------------------------------------------------------------------------

class TestCancellationGracePeriod:
    """Verify canceled users retain access until subscription_end_date."""

    def test_access_retained_during_billing_period(self):
        """Canceled user retains access during remaining billing period."""
        future = datetime.now(timezone.utc) + timedelta(days=25)
        user = _make_user(status='canceled', end_date=future)
        assert user.has_paid_access is True

    def test_access_revoked_after_end_date(self):
        """Access revoked after subscription_end_date passes."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        user = _make_user(status='canceled', end_date=past)
        assert user.has_paid_access is False

    def test_naive_datetime_handled_as_utc(self):
        """Naive datetime end_date is treated as UTC."""
        # Naive future datetime
        future_naive = datetime.utcnow() + timedelta(days=7)
        user = _make_user(status='canceled', end_date=future_naive)
        assert user.has_paid_access is True

        # Naive past datetime
        past_naive = datetime.utcnow() - timedelta(days=1)
        user2 = _make_user(status='canceled', end_date=past_naive)
        assert user2.has_paid_access is False


# ---------------------------------------------------------------------------
# Downgrade Experience Tests
# ---------------------------------------------------------------------------

class TestDowngradeExperience:
    """Verify downgraded users are treated as anonymous for AI features."""

    def test_expired_subscriber_treated_as_anonymous_in_rate_limiting(self):
        """Expired subscriber should NOT bypass anonymous rate limits."""
        # The rate limiting functions use user_has_paid_access() which returns
        # False for expired subscribers, meaning they fall through to
        # anonymous rate limiting — same as first-time visitors.
        user = _make_user(status='canceled',
                          end_date=datetime.now(timezone.utc) - timedelta(days=1))
        assert user.has_paid_access is False

    def test_none_status_treated_as_anonymous_in_rate_limiting(self):
        """User with no subscription treated as anonymous for rate limiting."""
        user = _make_user(status='none')
        assert user.has_paid_access is False

    def test_rate_limiter_docstring_states_unpaid_as_anonymous(self):
        """Module docstring documents that unpaid users are treated as anonymous."""
        assert 'Registered users without active subscription: treated as anonymous' \
            in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases for subscription lifecycle access control."""

    def test_active_to_past_due_to_active_no_interruption(self):
        """Payment recovery: active → past_due → active. Access never lost."""
        user = _make_user(status='active')
        assert user.has_paid_access is True

        # Payment fails
        user2 = _make_user(status='past_due')
        assert user2.has_paid_access is True

        # Payment recovered
        user3 = _make_user(status='active')
        assert user3.has_paid_access is True

    def test_active_to_canceled_to_active_access_restored(self):
        """Resubscription: active → canceled → active. Access restored."""
        user = _make_user(status='active')
        assert user.has_paid_access is True

        # Canceled but within billing period
        future = datetime.now(timezone.utc) + timedelta(days=10)
        user2 = _make_user(status='canceled', end_date=future)
        assert user2.has_paid_access is True

        # Resubscribed
        user3 = _make_user(status='active')
        assert user3.has_paid_access is True

    def test_past_due_extended_period(self):
        """User stays past_due for extended Stripe retry period — still has access."""
        user = _make_user(status='past_due')
        assert user.has_paid_access is True


# ---------------------------------------------------------------------------
# Performance / Security
# ---------------------------------------------------------------------------

class TestPerformanceSecurity:
    """Access check is local (no Stripe API calls) and not spoofable."""

    def test_access_check_uses_local_db_not_stripe(self):
        """user_has_paid_access checks local model property, not Stripe API."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE, 'user_has_paid_access')
        assert 'stripe' not in func_src.lower()

    def test_has_paid_access_reads_model_fields_only(self):
        """has_paid_access reads subscription_status and subscription_end_date only."""
        func_src = _get_function_source(USER_MODEL_SOURCE, 'has_paid_access')
        assert 'self.subscription_status' in func_src
        assert 'self.subscription_end_date' in func_src
        # No external API calls or imports in the function body
        assert 'import' not in func_src.split('"""')[-1]
        assert 'requests.get' not in func_src
        assert 'stripe.' not in func_src.lower()

    def test_subscription_status_not_settable_via_request(self):
        """subscription_status is a db column, not a request parameter."""
        # The field is a db.Column, not read from request
        assert 'db.Column' in USER_MODEL_SOURCE.split('subscription_status')[0].split('\n')[-1] \
            or 'subscription_status = db.Column' in USER_MODEL_SOURCE


# ---------------------------------------------------------------------------
# Acceptance Criteria Verification
# ---------------------------------------------------------------------------

class TestAcceptanceCriteria:
    """Direct verification of all acceptance criteria from the user story."""

    def test_ac_active_subscribers_full_access(self):
        """AC: Active subscribers have full paid-tier access to all AI features."""
        user = _make_user(status='active')
        assert user.has_paid_access is True

    def test_ac_past_due_retains_access(self):
        """AC: Subscribers with past_due status retain full access."""
        user = _make_user(status='past_due')
        assert user.has_paid_access is True

    def test_ac_canceled_retains_until_end_date(self):
        """AC: Canceled subscribers retain full access until subscription_end_date."""
        future = datetime.now(timezone.utc) + timedelta(days=7)
        user = _make_user(status='canceled', end_date=future)
        assert user.has_paid_access is True

    def test_ac_expired_canceled_downgraded(self):
        """AC: After subscription_end_date, canceled subscribers are downgraded."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = _make_user(status='canceled', end_date=past)
        assert user.has_paid_access is False

    def test_ac_downgraded_same_as_anonymous(self):
        """AC: Downgraded users see same experience as first-time anonymous visitor."""
        # Both none-status and expired-canceled have no paid access
        none_user = _make_user(status='none')
        expired_user = _make_user(
            status='canceled',
            end_date=datetime.now(timezone.utc) - timedelta(days=1)
        )
        assert none_user.has_paid_access is False
        assert expired_user.has_paid_access is False

    def test_ac_centralized_access_check(self):
        """AC: Access control is centralized — one function determines paid access."""
        # user_has_paid_access exists as the centralized check
        assert 'def user_has_paid_access' in RATE_LIMITING_SOURCE
        # It's used in all rate limiting functions (no scattered is_authenticated)
        for func_name in ['check_global_anonymous_limit', 'check_anonymous_rate_limit',
                          'record_global_anonymous_usage', 'record_anonymous_usage',
                          'check_subscriber_daily_limit']:
            func_src = _get_function_source(RATE_LIMITING_SOURCE, func_name)
            assert 'user_has_paid_access()' in func_src, \
                f"{func_name} does not use centralized user_has_paid_access()"

    def test_ac_subscription_status_queryable(self):
        """AC: Subscription status is queryable for other features."""
        # has_paid_access property on User model
        assert '@property' in USER_MODEL_SOURCE
        assert 'def has_paid_access' in USER_MODEL_SOURCE
        # user_has_paid_access importable from rate_limiting
        assert 'def user_has_paid_access' in RATE_LIMITING_SOURCE

    def test_ac_failed_payment_eventual_downgrade(self):
        """AC: User whose payment fails is eventually downgraded after Stripe deletes sub."""
        # When Stripe deletes: webhook sets status to canceled with end_date
        # After end_date passes: has_paid_access returns False
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = _make_user(status='canceled', end_date=past)
        assert user.has_paid_access is False
