"""
US-12.3.3: Per-user subscriber daily rate limits

Tests for:
- Paid subscribers have daily AI call limits by interaction type
- Default limits: ~25 chatbot messages/day, ~5 portfolio analyses/day
- Limits reset at midnight UTC (queries today's usage only)
- All limits are configurable via environment variables or app config
- Structured JSON response with limit_type: subscriber_daily
- No signup redirect — just shows reset message
- Usage counts integrate with metering system (ai_usage_records table)
- Anonymous users are NOT affected by subscriber limits
- All three rate limiting layers coexist
- Silent failure on errors (never block requests)

Updated in US-13.1.2: renamed registered → subscriber to reflect paid-only model.
"""

import ast
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
CONFIG_FILE = SIGNALTRACKERS_DIR / 'config.py'
ENV_EXAMPLE_FILE = REPO_ROOT / '.env.example'

RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
CONFIG_SOURCE = CONFIG_FILE.read_text()
ENV_EXAMPLE_SOURCE = ENV_EXAMPLE_FILE.read_text() if ENV_EXAMPLE_FILE.exists() else ''


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_function_source_from_file(source: str, func_name: str) -> str:
    """Extract the source of a named function from file source."""
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            start = node.lineno - 1
            end = node.end_lineno
            return '\n'.join(lines[start:end])
    return ''


# ---------------------------------------------------------------------------
# AC1: Subscribers have daily AI call limits by interaction type
# ---------------------------------------------------------------------------

class TestSubscriberLimitStructure:
    """Verify subscriber daily limit infrastructure exists."""

    def test_check_function_exists(self):
        """check_subscriber_daily_limit function is defined."""
        assert 'def check_subscriber_daily_limit' in RATE_LIMITING_SOURCE

    def test_default_limits_constant_exists(self):
        """DEFAULT_SUBSCRIBER_DAILY_LIMITS constant is defined."""
        assert 'DEFAULT_SUBSCRIBER_DAILY_LIMITS' in RATE_LIMITING_SOURCE

    def test_category_interaction_types_mapping_exists(self):
        """_CATEGORY_INTERACTION_TYPES mapping is defined."""
        assert '_CATEGORY_INTERACTION_TYPES' in RATE_LIMITING_SOURCE

    def test_chatbot_interaction_types_mapped(self):
        """Chatbot category maps to chatbot, section_ai, sentence_drill_in."""
        assert "'chatbot'" in RATE_LIMITING_SOURCE
        assert "'section_ai'" in RATE_LIMITING_SOURCE
        assert "'sentence_drill_in'" in RATE_LIMITING_SOURCE

    def test_analysis_interaction_types_mapped(self):
        """Analysis category maps to portfolio_analysis."""
        assert "'portfolio_analysis'" in RATE_LIMITING_SOURCE

    def test_get_subscriber_daily_limit_exists(self):
        """_get_subscriber_daily_limit helper function is defined."""
        assert 'def _get_subscriber_daily_limit' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC2: Default limits: ~25 chatbot messages/day, ~5 portfolio analyses/day
# ---------------------------------------------------------------------------

class TestDefaultSubscriberLimits:
    """Verify default subscriber daily limit values."""

    def test_default_chatbot_limit_is_25(self):
        """Default chatbot limit is 25."""
        import services.rate_limiting as rl
        assert rl.DEFAULT_SUBSCRIBER_DAILY_LIMITS[rl.CATEGORY_CHATBOT] == 25

    def test_default_analysis_limit_is_5(self):
        """Default analysis limit is 5."""
        import services.rate_limiting as rl
        assert rl.DEFAULT_SUBSCRIBER_DAILY_LIMITS[rl.CATEGORY_ANALYSIS] == 5


# ---------------------------------------------------------------------------
# AC3: Limits reset at midnight UTC
# ---------------------------------------------------------------------------

class TestMidnightUTCReset:
    """Verify limits use UTC date for daily reset."""

    def test_check_uses_utc(self):
        """check_subscriber_daily_limit uses UTC timezone."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'utc' in func_src.lower() or 'UTC' in func_src

    def test_queries_today_start(self):
        """check_subscriber_daily_limit filters by today's date."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        # Should calculate today's start timestamp
        assert 'hour=0' in func_src or 'today' in func_src


# ---------------------------------------------------------------------------
# AC4: All limits configurable via environment variables or app config
# ---------------------------------------------------------------------------

class TestConfiguration:
    """Verify subscriber daily limits are configurable."""

    def test_config_has_chatbot_limit(self):
        """Config class reads SUBSCRIBER_DAILY_LIMIT_CHATBOT from env."""
        assert 'SUBSCRIBER_DAILY_LIMIT_CHATBOT' in CONFIG_SOURCE
        assert "os.environ.get('SUBSCRIBER_DAILY_LIMIT_CHATBOT'" in CONFIG_SOURCE

    def test_config_has_analysis_limit(self):
        """Config class reads SUBSCRIBER_DAILY_LIMIT_ANALYSIS from env."""
        assert 'SUBSCRIBER_DAILY_LIMIT_ANALYSIS' in CONFIG_SOURCE
        assert "os.environ.get('SUBSCRIBER_DAILY_LIMIT_ANALYSIS'" in CONFIG_SOURCE

    def test_config_chatbot_default_is_25(self):
        """Config falls back to 25 for chatbot when env var not set."""
        # Config may be multi-line; find the block around SUBSCRIBER_DAILY_LIMIT_CHATBOT
        idx = CONFIG_SOURCE.index('SUBSCRIBER_DAILY_LIMIT_CHATBOT')
        block = CONFIG_SOURCE[idx:idx + 200]
        assert '25' in block

    def test_config_analysis_default_is_5(self):
        """Config falls back to 5 for analysis when env var not set."""
        idx = CONFIG_SOURCE.index('SUBSCRIBER_DAILY_LIMIT_ANALYSIS')
        block = CONFIG_SOURCE[idx:idx + 200]
        assert '5' in block

    @pytest.mark.skipif(not ENV_EXAMPLE_SOURCE, reason=".env.example not available in Docker")
    def test_env_example_documents_chatbot_limit(self):
        """SUBSCRIBER_DAILY_LIMIT_CHATBOT is documented in .env.example."""
        assert 'SUBSCRIBER_DAILY_LIMIT_CHATBOT' in ENV_EXAMPLE_SOURCE

    @pytest.mark.skipif(not ENV_EXAMPLE_SOURCE, reason=".env.example not available in Docker")
    def test_env_example_documents_analysis_limit(self):
        """SUBSCRIBER_DAILY_LIMIT_ANALYSIS is documented in .env.example."""
        assert 'SUBSCRIBER_DAILY_LIMIT_ANALYSIS' in ENV_EXAMPLE_SOURCE


# ---------------------------------------------------------------------------
# AC5: Structured JSON response with graceful message
# ---------------------------------------------------------------------------

class TestResponseFormat:
    """Verify rate limit response structure."""

    def test_response_includes_limited_flag(self):
        """Response includes limited: True."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert "'limited': True" in func_src or '"limited": True' in func_src

    def test_response_includes_limit_type(self):
        """Response includes limit_type: subscriber_daily."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'subscriber_daily' in func_src

    def test_response_includes_category(self):
        """Response includes the category field."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert "'category'" in func_src or '"category"' in func_src

    def test_response_message_mentions_reset(self):
        """Response message mentions limit resetting."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'reset' in func_src.lower()


# ---------------------------------------------------------------------------
# AC6: No signup redirect — just reset message
# ---------------------------------------------------------------------------

class TestNoSignupRedirect:
    """Verify subscriber limit response does not push signup."""

    def test_response_does_not_mention_signup(self):
        """Response message does not mention creating an account."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        # Extract just the message string
        assert 'account' not in func_src.lower() or 'Create' not in func_src


# ---------------------------------------------------------------------------
# AC7: Usage counts integrate with metering system (ai_usage_records)
# ---------------------------------------------------------------------------

class TestMeteringIntegration:
    """Verify subscriber limits query ai_usage_records table."""

    def test_queries_ai_usage_record_model(self):
        """check_subscriber_daily_limit imports and queries AIUsageRecord."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'AIUsageRecord' in func_src

    def test_queries_by_user_id(self):
        """Query filters by current user's ID."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'user_id' in func_src
        assert 'current_user' in func_src

    def test_queries_by_interaction_type(self):
        """Query filters by interaction type."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'interaction_type' in func_src

    def test_queries_by_timestamp(self):
        """Query filters by timestamp for today's records only."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'timestamp' in func_src


# ---------------------------------------------------------------------------
# Anonymous users NOT affected by subscriber limits
# ---------------------------------------------------------------------------

class TestAnonymousUnaffected:
    """Verify anonymous users bypass subscriber daily limits."""

    def test_check_returns_none_for_anonymous(self):
        """check_subscriber_daily_limit returns None for unauthenticated users."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'is_authenticated' in func_src


# ---------------------------------------------------------------------------
# All three layers coexist in decorator
# ---------------------------------------------------------------------------

class TestThreeLayerCoexistence:
    """Verify all three rate limiting layers work in the decorator."""

    def test_decorator_checks_subscriber_limit(self):
        """Decorator calls check_subscriber_daily_limit."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        lines = RATE_LIMITING_SOURCE.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        assert 'check_subscriber_daily_limit' in func_src

    def test_decorator_checks_all_three_layers(self):
        """Decorator contains checks for subscriber, global, and session limits."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        lines = RATE_LIMITING_SOURCE.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        assert 'check_subscriber_daily_limit' in func_src
        assert 'check_global_anonymous_limit' in func_src
        assert 'check_anonymous_rate_limit' in func_src

    def test_subscriber_check_before_anonymous_checks(self):
        """Subscriber daily check runs before anonymous checks in decorator."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        lines = RATE_LIMITING_SOURCE.splitlines()
        func_src = ''
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        subscriber_pos = func_src.find('check_subscriber_daily_limit')
        global_pos = func_src.find('check_global_anonymous_limit')
        session_pos = func_src.find('check_anonymous_rate_limit')
        assert subscriber_pos < global_pos < session_pos


# ---------------------------------------------------------------------------
# Silent failure (never block requests due to errors)
# ---------------------------------------------------------------------------

class TestSilentFailure:
    """Verify rate limiting errors are caught and do not block requests."""

    def test_check_catches_exceptions(self):
        """check_subscriber_daily_limit has exception handling."""
        func_src = _get_function_source_from_file(
            RATE_LIMITING_SOURCE, 'check_subscriber_daily_limit'
        )
        assert 'except Exception' in func_src or 'except:' in func_src
        assert 'return None' in func_src


# ---------------------------------------------------------------------------
# Functional tests with Flask app context + mocked DB
# ---------------------------------------------------------------------------

class TestFunctionalSubscriberLimits:
    """Functional tests using Flask test infrastructure with mocked DB."""

    @pytest.fixture(autouse=True)
    def reset_global_state(self):
        """Reset global counter before each test."""
        import services.rate_limiting as rl
        with rl._global_lock:
            rl._global_count = 0
            rl._global_date = None
        yield
        with rl._global_lock:
            rl._global_count = 0
            rl._global_date = None

    @pytest.fixture
    def app(self):
        """Create a minimal Flask app with LoginManager for testing."""
        from flask import Flask
        from flask_login import LoginManager
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['SUBSCRIBER_DAILY_LIMIT_CHATBOT'] = 3
        app.config['SUBSCRIBER_DAILY_LIMIT_ANALYSIS'] = 2
        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 1000
        app.config['ANON_SESSION_LIMIT_CHATBOT'] = 1000
        app.config['ANON_SESSION_LIMIT_ANALYSIS'] = 1000
        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return None

        return app

    @pytest.fixture
    def mock_auth_user(self):
        """Create a mock authenticated user with paid access."""
        user = MagicMock()
        user.is_authenticated = True
        user.id = 'test-user-123'
        user.has_paid_access = True
        return user

    @pytest.fixture
    def mock_db_and_model(self):
        """Set up mock db and AIUsageRecord in sys.modules to prevent import chain."""
        mock_ai_usage_module = MagicMock()
        mock_ai_record = MagicMock()
        mock_ai_usage_module.AIUsageRecord = mock_ai_record
        # Pre-populate sys.modules so 'from models.ai_usage import AIUsageRecord'
        # doesn't trigger the real import chain (which needs a real db for ORM)
        modules_patch = {
            'models.ai_usage': mock_ai_usage_module,
        }
        return mock_ai_record, modules_patch

    def _mock_usage_count(self, count):
        """Create a mock for db.session.query that returns a count."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = count
        mock_db = MagicMock()
        mock_db.session.query.return_value = mock_query
        mock_db.func = MagicMock()
        return mock_db

    def _make_mock_ai_module(self):
        """Create a mock ai_usage module with AIUsageRecord that supports SQLAlchemy ops."""
        mock_ai_module = MagicMock()
        # AIUsageRecord attributes need to support comparison operators for filter()
        mock_record = MagicMock()
        mock_record.timestamp.__ge__ = MagicMock(return_value=MagicMock())
        mock_record.user_id.__eq__ = MagicMock(return_value=MagicMock())
        mock_record.interaction_type.in_ = MagicMock(return_value=MagicMock())
        mock_ai_module.AIUsageRecord = mock_record
        return mock_ai_module

    def _patch_for_check(self, rl, mock_auth_user, count):
        """Context manager that patches db and model imports for check_subscriber_daily_limit."""
        mock_db = self._mock_usage_count(count)
        mock_ai_module = self._make_mock_ai_module()
        return (
            patch.object(rl, 'current_user', mock_auth_user),
            patch.dict('sys.modules', {'models.ai_usage': mock_ai_module}),
            patch('extensions.db', mock_db),
        )

    def test_allows_within_daily_limit(self, app, mock_auth_user):
        """Subscriber within daily limit is allowed."""
        import services.rate_limiting as rl

        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 2)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
            assert result is None

    def test_blocks_at_daily_limit(self, app, mock_auth_user):
        """Subscriber at daily limit is blocked."""
        import services.rate_limiting as rl

        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 3)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
            assert result is not None
            assert result['limited'] is True
            assert result['limit_type'] == 'subscriber_daily'
            assert result['category'] == 'chatbot'
            assert 'message' in result

    def test_blocks_over_daily_limit(self, app, mock_auth_user):
        """Subscriber over daily limit is blocked."""
        import services.rate_limiting as rl

        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 10)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
            assert result is not None
            assert result['limited'] is True

    def test_independent_category_limits(self, app, mock_auth_user):
        """Chatbot and analysis have independent counters."""
        import services.rate_limiting as rl

        mock_ai_module = self._make_mock_ai_module()

        with app.test_request_context():
            with patch.object(rl, 'current_user', mock_auth_user), \
                 patch.dict('sys.modules', {'models.ai_usage': mock_ai_module}):
                # Chatbot at limit (3)
                mock_db_chatbot = self._mock_usage_count(3)
                with patch('extensions.db', mock_db_chatbot):
                    chatbot_result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)

                # Analysis under limit (1 < 2)
                mock_db_analysis = self._mock_usage_count(1)
                with patch('extensions.db', mock_db_analysis):
                    analysis_result = rl.check_subscriber_daily_limit(rl.CATEGORY_ANALYSIS)

        assert chatbot_result is not None  # blocked
        assert analysis_result is None  # allowed

    def test_anonymous_user_returns_none(self, app):
        """Anonymous users bypass subscriber daily limits."""
        import services.rate_limiting as rl

        mock_anon = MagicMock()
        mock_anon.is_authenticated = False

        with app.test_request_context():
            with patch.object(rl, 'current_user', mock_anon):
                result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
                assert result is None

    def test_zero_usage_allows_full_budget(self, app, mock_auth_user):
        """New subscriber with zero usage gets full daily budget."""
        import services.rate_limiting as rl

        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 0)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
            assert result is None

    def test_configurable_limit(self, app, mock_auth_user):
        """Changing config value changes the limit."""
        import services.rate_limiting as rl

        app.config['SUBSCRIBER_DAILY_LIMIT_CHATBOT'] = 10
        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 5)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
            assert result is None

    def test_exception_returns_none(self, app, mock_auth_user):
        """check_subscriber_daily_limit returns None on internal error."""
        import services.rate_limiting as rl

        # Force an error by making db.session.query raise
        mock_db = MagicMock()
        mock_db.session.query.side_effect = RuntimeError('boom')
        mock_ai_module = MagicMock()

        with app.test_request_context():
            with patch.object(rl, 'current_user', mock_auth_user), \
                 patch.dict('sys.modules', {'models.ai_usage': mock_ai_module}), \
                 patch('extensions.db', mock_db):
                result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
                assert result is None

    def test_response_message_no_signup_redirect(self, app, mock_auth_user):
        """Rate limit response does not encourage signup (already subscribed)."""
        import services.rate_limiting as rl

        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 3)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)
            assert 'account' not in result['message'].lower()
            assert 'sign' not in result['message'].lower()
            assert 'reset' in result['message'].lower()

    def test_decorator_blocks_subscriber_at_limit(self, app, mock_auth_user):
        """Decorator returns 429 for subscriber at daily limit."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-sub-limit', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        limit_response = {
            'limited': True,
            'message': "You've reached your daily limit.",
            'limit_type': 'subscriber_daily',
            'category': 'chatbot',
        }

        with app.test_client() as client:
            with patch.object(rl, 'check_subscriber_daily_limit', return_value=limit_response):
                resp = client.post('/test-sub-limit')
                assert resp.status_code == 429
                data = resp.get_json()
                assert data['limit_type'] == 'subscriber_daily'

    def test_decorator_allows_subscriber_within_limit(self, app, mock_auth_user):
        """Decorator allows subscriber within daily limit."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-sub-allow', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            with patch.object(rl, 'check_subscriber_daily_limit', return_value=None), \
                 patch.object(rl, 'check_global_anonymous_limit', return_value=None), \
                 patch.object(rl, 'check_anonymous_rate_limit', return_value=None):
                resp = client.post('/test-sub-allow')
                assert resp.status_code == 200

    def test_subscriber_not_affected_by_anon_global_cap(self, app, mock_auth_user):
        """Subscriber is not blocked by the anonymous global cap."""
        import services.rate_limiting as rl
        from flask import jsonify

        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 1

        @app.route('/test-sub-anon-cap', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        # Max out anonymous global cap
        with app.test_request_context():
            for _ in range(5):
                rl.record_global_anonymous_usage()

        # Subscriber should still pass (subscriber check returns None,
        # global check returns None for authenticated users)
        with app.test_client() as client:
            with patch.object(rl, 'check_subscriber_daily_limit', return_value=None), \
                 patch.object(rl, 'current_user', mock_auth_user):
                resp = client.post('/test-sub-anon-cap')
                assert resp.status_code == 200

    def test_response_json_format_consistent(self, app, mock_auth_user):
        """Subscriber limit response has same structure as anonymous responses."""
        import services.rate_limiting as rl

        p1, p2, p3 = self._patch_for_check(rl, mock_auth_user, 3)
        with app.test_request_context(), p1, p2, p3:
            result = rl.check_subscriber_daily_limit(rl.CATEGORY_CHATBOT)

        # Same keys as anonymous responses
        assert 'limited' in result
        assert 'message' in result
        assert 'limit_type' in result
        assert isinstance(result['limited'], bool)
        assert isinstance(result['message'], str)
        assert isinstance(result['limit_type'], str)
