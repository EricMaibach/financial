"""
US-13.1.2: Subscription Data Model

Tests for:
- User model has stripe_customer_id, subscription_status, subscription_end_date fields
- subscription_status uses well-defined enum values: active, past_due, canceled, none
- Default values are sensible for new users
- Business rules for has_paid_access property
- Phase 12 "registered free" rate limit concept is removed/repurposed
- Migration structure
- Security: stripe_customer_id not exposed in templates
"""

import ast
import enum
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

USER_MODEL_FILE = SIGNALTRACKERS_DIR / 'models' / 'user.py'
RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
CONFIG_FILE = SIGNALTRACKERS_DIR / 'config.py'
MIGRATIONS_DIR = SIGNALTRACKERS_DIR / 'migrations' / 'versions'

USER_MODEL_SOURCE = USER_MODEL_FILE.read_text()
RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
CONFIG_SOURCE = CONFIG_FILE.read_text()


# ---------------------------------------------------------------------------
# Functional Tests — User Model Fields
# ---------------------------------------------------------------------------

class TestUserModelFields:
    """Verify subscription fields exist on User model."""

    def test_stripe_customer_id_field(self):
        """User model has stripe_customer_id field."""
        assert 'stripe_customer_id' in USER_MODEL_SOURCE

    def test_subscription_status_field(self):
        """User model has subscription_status field."""
        assert 'subscription_status' in USER_MODEL_SOURCE

    def test_subscription_end_date_field(self):
        """User model has subscription_end_date field."""
        assert 'subscription_end_date' in USER_MODEL_SOURCE

    def test_subscription_status_enum_defined(self):
        """SubscriptionStatus enum is defined with correct values."""
        from models.user import SubscriptionStatus
        assert issubclass(SubscriptionStatus, enum.Enum)
        values = {s.value for s in SubscriptionStatus}
        assert values == {'active', 'past_due', 'canceled', 'none'}

    def test_subscription_status_accepts_active(self):
        """subscription_status accepts 'active'."""
        from models.user import SubscriptionStatus
        assert SubscriptionStatus.ACTIVE.value == 'active'

    def test_subscription_status_accepts_past_due(self):
        """subscription_status accepts 'past_due'."""
        from models.user import SubscriptionStatus
        assert SubscriptionStatus.PAST_DUE.value == 'past_due'

    def test_subscription_status_accepts_canceled(self):
        """subscription_status accepts 'canceled'."""
        from models.user import SubscriptionStatus
        assert SubscriptionStatus.CANCELED.value == 'canceled'

    def test_subscription_status_accepts_none(self):
        """subscription_status accepts 'none'."""
        from models.user import SubscriptionStatus
        assert SubscriptionStatus.NONE.value == 'none'

    def test_default_subscription_status(self):
        """Default subscription_status for new users is 'none'."""
        from models.user import SubscriptionStatus
        # Check that the model column uses SubscriptionStatus.NONE.value as default
        assert "default=SubscriptionStatus.NONE.value" in USER_MODEL_SOURCE

    def test_default_subscription_end_date_is_null(self):
        """Default subscription_end_date is nullable (None)."""
        assert 'subscription_end_date' in USER_MODEL_SOURCE
        assert 'nullable=True' in USER_MODEL_SOURCE.split('subscription_end_date')[1].split(')')[0]

    def test_default_stripe_customer_id_is_null(self):
        """Default stripe_customer_id is nullable (None)."""
        # Find the full column definition (multi-line)
        start = USER_MODEL_SOURCE.index('stripe_customer_id')
        # Find the closing paren of the outer db.Column(...)
        depth, end = 0, start
        for i, c in enumerate(USER_MODEL_SOURCE[start:], start):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        col_def = USER_MODEL_SOURCE[start:end + 1]
        assert 'nullable=True' in col_def

    def test_stripe_customer_id_is_unique(self):
        """stripe_customer_id has unique constraint."""
        start = USER_MODEL_SOURCE.index('stripe_customer_id')
        depth, end = 0, start
        for i, c in enumerate(USER_MODEL_SOURCE[start:], start):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        col_def = USER_MODEL_SOURCE[start:end + 1]
        assert 'unique=True' in col_def

    def test_stripe_customer_id_is_indexed(self):
        """stripe_customer_id is indexed for fast lookups."""
        start = USER_MODEL_SOURCE.index('stripe_customer_id')
        depth, end = 0, start
        for i, c in enumerate(USER_MODEL_SOURCE[start:], start):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        col_def = USER_MODEL_SOURCE[start:end + 1]
        assert 'index=True' in col_def


# ---------------------------------------------------------------------------
# Database Migration Tests
# ---------------------------------------------------------------------------

class TestMigration:
    """Verify migration adds subscription fields correctly."""

    def test_migration_file_exists(self):
        """Migration file for subscription fields exists."""
        migration_files = list(MIGRATIONS_DIR.glob('*subscription*'))
        assert len(migration_files) == 1

    def test_migration_adds_stripe_customer_id(self):
        """Migration adds stripe_customer_id column."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert 'stripe_customer_id' in source

    def test_migration_adds_subscription_status(self):
        """Migration adds subscription_status column."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert 'subscription_status' in source

    def test_migration_adds_subscription_end_date(self):
        """Migration adds subscription_end_date column."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert 'subscription_end_date' in source

    def test_migration_has_server_default_for_status(self):
        """Migration sets server_default='none' for subscription_status."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert "server_default='none'" in source

    def test_migration_is_reversible(self):
        """Migration has both upgrade() and downgrade() functions."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert 'def upgrade()' in source
        assert 'def downgrade()' in source

    def test_migration_downgrade_drops_columns(self):
        """Downgrade drops all three new columns."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        tree = ast.parse(source)
        lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'downgrade':
                downgrade_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        assert 'stripe_customer_id' in downgrade_src
        assert 'subscription_status' in downgrade_src
        assert 'subscription_end_date' in downgrade_src

    def test_migration_checks_existing_columns(self):
        """Migration handles case where columns already exist."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert 'existing_columns' in source or 'inspector' in source

    def test_migration_creates_unique_index(self):
        """Migration creates unique index on stripe_customer_id."""
        migration = list(MIGRATIONS_DIR.glob('*subscription*'))[0]
        source = migration.read_text()
        assert 'ix_users_stripe_customer_id' in source
        assert 'unique=True' in source


# ---------------------------------------------------------------------------
# Business Rules Tests — has_paid_access
# ---------------------------------------------------------------------------

class TestHasPaidAccess:
    """Verify has_paid_access property implements business rules."""

    def test_has_paid_access_property_exists(self):
        """User model has has_paid_access property."""
        assert 'has_paid_access' in USER_MODEL_SOURCE
        assert '@property' in USER_MODEL_SOURCE

    def test_active_has_paid_access(self):
        """User with subscription_status=active has paid access."""
        user = MagicMock()
        user.subscription_status = 'active'
        user.subscription_end_date = None

        from models.user import User
        assert User.has_paid_access.fget(user) is True

    def test_past_due_has_paid_access(self):
        """User with subscription_status=past_due has paid access (grace period)."""
        user = MagicMock()
        user.subscription_status = 'past_due'
        user.subscription_end_date = None

        from models.user import User
        assert User.has_paid_access.fget(user) is True

    def test_canceled_future_end_date_has_paid_access(self):
        """User with canceled status but future end date retains paid access."""
        user = MagicMock()
        user.subscription_status = 'canceled'
        user.subscription_end_date = datetime.now(timezone.utc) + timedelta(days=7)

        from models.user import User
        assert User.has_paid_access.fget(user) is True

    def test_canceled_past_end_date_no_paid_access(self):
        """User with canceled status and past end date does NOT have paid access."""
        user = MagicMock()
        user.subscription_status = 'canceled'
        user.subscription_end_date = datetime.now(timezone.utc) - timedelta(days=1)

        from models.user import User
        assert User.has_paid_access.fget(user) is False

    def test_canceled_null_end_date_no_paid_access(self):
        """User with canceled status and null end date is treated as expired."""
        user = MagicMock()
        user.subscription_status = 'canceled'
        user.subscription_end_date = None

        from models.user import User
        assert User.has_paid_access.fget(user) is False

    def test_none_status_no_paid_access(self):
        """User with subscription_status=none does NOT have paid access."""
        user = MagicMock()
        user.subscription_status = 'none'
        user.subscription_end_date = None

        from models.user import User
        assert User.has_paid_access.fget(user) is False

    def test_all_null_fields_no_paid_access(self):
        """User with all subscription fields at defaults behaves as no-access."""
        user = MagicMock()
        user.subscription_status = 'none'
        user.subscription_end_date = None
        user.stripe_customer_id = None

        from models.user import User
        assert User.has_paid_access.fget(user) is False

    def test_canceled_with_naive_datetime_end_date(self):
        """Canceled user with naive datetime end_date is handled gracefully."""
        user = MagicMock()
        user.subscription_status = 'canceled'
        # Naive datetime (no tzinfo) — should be treated as UTC
        user.subscription_end_date = datetime.utcnow() + timedelta(days=7)

        from models.user import User
        assert User.has_paid_access.fget(user) is True


# ---------------------------------------------------------------------------
# Phase 12 "Registered Free" Removal Tests
# ---------------------------------------------------------------------------

class TestRegisteredFreeRemoval:
    """Verify Phase 12 'registered free' rate limit concept is removed/repurposed."""

    def test_no_registered_free_tier_in_rate_limiting(self):
        """No code path treats a registered user as 'free tier'."""
        # The rate limiting module should use 'subscriber' terminology, not 'registered'
        assert 'DEFAULT_SUBSCRIBER_DAILY_LIMITS' in RATE_LIMITING_SOURCE
        assert 'DEFAULT_REGISTERED_DAILY_LIMITS' not in RATE_LIMITING_SOURCE

    def test_subscriber_limit_check_exists(self):
        """Rate limiter uses check_subscriber_daily_limit (not registered)."""
        assert 'def check_subscriber_daily_limit' in RATE_LIMITING_SOURCE
        assert 'def check_registered_daily_limit' not in RATE_LIMITING_SOURCE

    def test_subscriber_limit_checks_paid_access(self):
        """Rate limiter checks has_paid_access before applying subscriber limits."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        lines = RATE_LIMITING_SOURCE.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'check_subscriber_daily_limit':
                func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        assert 'has_paid_access' in func_src

    def test_anonymous_rate_limiting_unchanged(self):
        """Anonymous user rate limiting functions still exist."""
        assert 'def check_anonymous_rate_limit' in RATE_LIMITING_SOURCE
        assert 'def check_global_anonymous_limit' in RATE_LIMITING_SOURCE

    def test_config_uses_subscriber_naming(self):
        """Config uses SUBSCRIBER_DAILY_LIMIT_* (not REGISTERED)."""
        assert 'SUBSCRIBER_DAILY_LIMIT_CHATBOT' in CONFIG_SOURCE
        assert 'SUBSCRIBER_DAILY_LIMIT_ANALYSIS' in CONFIG_SOURCE

    def test_config_backward_compat_with_registered_env_vars(self):
        """Config falls back to REGISTERED_DAILY_LIMIT_* env vars for backward compat."""
        assert 'REGISTERED_DAILY_LIMIT_CHATBOT' in CONFIG_SOURCE
        assert 'REGISTERED_DAILY_LIMIT_ANALYSIS' in CONFIG_SOURCE

    def test_no_free_account_in_rate_limit_messages(self):
        """Rate limit messages no longer reference 'free account'."""
        assert 'free account' not in RATE_LIMITING_SOURCE.lower()

    def test_rate_limit_messages_use_subscribe(self):
        """Rate limit messages direct users to subscribe."""
        assert 'Subscribe' in RATE_LIMITING_SOURCE or 'subscribe' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# Security Tests
# ---------------------------------------------------------------------------

class TestSecurity:
    """Verify stripe_customer_id is not exposed in templates."""

    def test_stripe_customer_id_not_in_templates(self):
        """stripe_customer_id is not rendered in any template."""
        templates_dir = SIGNALTRACKERS_DIR / 'templates'
        for template_file in templates_dir.rglob('*.html'):
            content = template_file.read_text()
            assert 'stripe_customer_id' not in content, \
                f"stripe_customer_id found in {template_file.name}"

    def test_stripe_customer_id_not_in_js(self):
        """stripe_customer_id is not exposed in JavaScript files."""
        js_dir = SIGNALTRACKERS_DIR / 'static' / 'js'
        if js_dir.exists():
            for js_file in js_dir.rglob('*.js'):
                content = js_file.read_text()
                assert 'stripe_customer_id' not in content, \
                    f"stripe_customer_id found in {js_file.name}"


# ---------------------------------------------------------------------------
# Acceptance Criteria Verification
# ---------------------------------------------------------------------------

class TestAcceptanceCriteria:
    """Direct verification of all acceptance criteria."""

    def test_ac_stripe_customer_id_field(self):
        """AC: User model has a stripe_customer_id field linking to Stripe Customer."""
        assert 'stripe_customer_id' in USER_MODEL_SOURCE
        # Verify it's a db.Column definition — look at the full line
        for line in USER_MODEL_SOURCE.splitlines():
            if 'stripe_customer_id' in line and 'db.Column' in line:
                break
        else:
            # May be on a separate line from db.Column; just verify both exist nearby
            assert 'stripe_customer_id = db.Column(' in USER_MODEL_SOURCE

    def test_ac_subscription_status_field(self):
        """AC: User model has a subscription_status field tracking states."""
        assert 'subscription_status' in USER_MODEL_SOURCE

    def test_ac_subscription_end_date_field(self):
        """AC: User model has a subscription_end_date field."""
        assert 'subscription_end_date' in USER_MODEL_SOURCE

    def test_ac_subscription_status_well_defined(self):
        """AC: Subscription status values are well-defined (enum) — not arbitrary strings."""
        from models.user import SubscriptionStatus
        assert issubclass(SubscriptionStatus, enum.Enum)
        assert len(list(SubscriptionStatus)) == 4

    def test_ac_can_query_subscription_status(self):
        """AC: Application can query a user's subscription status for access decisions."""
        assert 'has_paid_access' in USER_MODEL_SOURCE

    def test_ac_registered_free_removed(self):
        """AC: Phase 12's 'registered free' concept is cleanly replaced."""
        assert 'DEFAULT_REGISTERED_DAILY_LIMITS' not in RATE_LIMITING_SOURCE
        assert 'check_registered_daily_limit' not in RATE_LIMITING_SOURCE

    def test_ac_models_init_exports_subscription_status(self):
        """SubscriptionStatus is exported from models package."""
        init_source = (SIGNALTRACKERS_DIR / 'models' / '__init__.py').read_text()
        assert 'SubscriptionStatus' in init_source
