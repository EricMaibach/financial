"""
US-12.3.2: Global daily anonymous cap

Tests for:
- Global in-memory counter tracks total anonymous AI calls per day
- Counter resets at midnight UTC (date change)
- Default limit of 100, configurable via ANON_GLOBAL_DAILY_LIMIT
- Structured JSON response with limit_type: anonymous_global_daily
- Registered users bypass global cap
- Global cap checked before per-session limit (fail fast)
- Thread-safety of counter operations
- Silent failure on errors (never block requests)
- Integration with decorator and session limits
"""

import ast
import sys
import threading
from datetime import date, datetime, timezone
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
# AC1: Global counter tracks total anonymous AI calls per day
# ---------------------------------------------------------------------------

class TestGlobalCounterStructure:
    """Verify global counter infrastructure exists."""

    def test_global_counter_variable_exists(self):
        """Module-level global counter variable is defined."""
        assert '_global_count' in RATE_LIMITING_SOURCE

    def test_global_date_variable_exists(self):
        """Module-level global date variable for daily reset."""
        assert '_global_date' in RATE_LIMITING_SOURCE

    def test_global_lock_exists(self):
        """Thread lock for counter access is defined."""
        assert '_global_lock' in RATE_LIMITING_SOURCE
        assert 'threading' in RATE_LIMITING_SOURCE

    def test_check_global_function_exists(self):
        """check_global_anonymous_limit function is defined."""
        assert 'def check_global_anonymous_limit' in RATE_LIMITING_SOURCE

    def test_record_global_function_exists(self):
        """record_global_anonymous_usage function is defined."""
        assert 'def record_global_anonymous_usage' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC2: Default limit ~100 total anonymous AI calls per day
# ---------------------------------------------------------------------------

class TestDefaultLimit:
    """Verify default global cap value."""

    def test_default_limit_constant(self):
        """DEFAULT_GLOBAL_DAILY_LIMIT is set to 100."""
        assert 'DEFAULT_GLOBAL_DAILY_LIMIT = 100' in RATE_LIMITING_SOURCE

    def test_config_has_global_daily_limit(self):
        """Config class reads ANON_GLOBAL_DAILY_LIMIT from env."""
        assert 'ANON_GLOBAL_DAILY_LIMIT' in CONFIG_SOURCE
        assert "os.environ.get('ANON_GLOBAL_DAILY_LIMIT'" in CONFIG_SOURCE


# ---------------------------------------------------------------------------
# AC3: Counter resets at midnight UTC
# ---------------------------------------------------------------------------

class TestMidnightReset:
    """Verify counter resets when UTC date changes."""

    def test_reset_function_exists(self):
        """_reset_if_new_day function is defined."""
        assert 'def _reset_if_new_day' in RATE_LIMITING_SOURCE

    def test_reset_uses_utc(self):
        """Reset logic uses UTC timezone."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, '_reset_if_new_day')
        assert 'utc' in func_src.lower() or 'UTC' in func_src


# ---------------------------------------------------------------------------
# AC4: Configurable via environment variable or app config
# ---------------------------------------------------------------------------

class TestConfiguration:
    """Verify global cap is configurable."""

    @pytest.mark.skipif(not ENV_EXAMPLE_SOURCE, reason=".env.example not available in Docker")
    def test_env_example_documents_variable(self):
        """ANON_GLOBAL_DAILY_LIMIT is documented in .env.example."""
        assert 'ANON_GLOBAL_DAILY_LIMIT' in ENV_EXAMPLE_SOURCE

    def test_config_default_is_100(self):
        """Config falls back to 100 when env var not set."""
        # The config line: ANON_GLOBAL_DAILY_LIMIT = int(os.environ.get('ANON_GLOBAL_DAILY_LIMIT', 100))
        config_line = [l for l in CONFIG_SOURCE.splitlines() if 'ANON_GLOBAL_DAILY_LIMIT' in l and 'environ' in l][0]
        assert '100' in config_line


# ---------------------------------------------------------------------------
# AC5-6: Structured JSON response with signup encouragement
# ---------------------------------------------------------------------------

class TestResponseFormat:
    """Verify rate limit response structure."""

    def test_response_includes_limit_type(self):
        """Response includes limit_type: anonymous_global_daily."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        assert 'anonymous_global_daily' in func_src

    def test_response_includes_limited_flag(self):
        """Response includes limited: True."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        assert "'limited': True" in func_src or '"limited": True' in func_src

    def test_response_message_encourages_signup(self):
        """Response message mentions creating an account."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        assert 'account' in func_src.lower() or 'sign' in func_src.lower()

    def test_response_does_not_include_counter_value(self):
        """Response does not expose the internal counter value."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        # The response dict should not contain _global_count or current count
        assert '_global_count' not in func_src.split('return {')[1].split('}')[0] if 'return {' in func_src else True


# ---------------------------------------------------------------------------
# AC7: Registered users unaffected
# ---------------------------------------------------------------------------

class TestRegisteredUsersBypass:
    """Verify registered users bypass global cap."""

    def test_check_global_bypasses_authenticated(self):
        """check_global_anonymous_limit checks is_authenticated."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        assert 'is_authenticated' in func_src

    def test_record_global_bypasses_authenticated(self):
        """record_global_anonymous_usage checks is_authenticated."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'record_global_anonymous_usage')
        assert 'is_authenticated' in func_src


# ---------------------------------------------------------------------------
# Global cap checked before per-session limit
# ---------------------------------------------------------------------------

class TestCheckOrder:
    """Verify global cap is checked before per-session limit in decorator."""

    def test_decorator_checks_global_first(self):
        """In the decorator, check_global_anonymous_limit runs before check_anonymous_rate_limit."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'wrapped')
        # Fallback: search in the anonymous_rate_limit function body
        if not func_src:
            # Get full decorator source
            tree = ast.parse(RATE_LIMITING_SOURCE)
            lines = RATE_LIMITING_SOURCE.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                    func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                    break

        global_pos = func_src.find('check_global_anonymous_limit')
        session_pos = func_src.find('check_anonymous_rate_limit')
        assert global_pos != -1, "Global check not found in decorator"
        assert session_pos != -1, "Session check not found in decorator"
        assert global_pos < session_pos, "Global check must run before session check"


# ---------------------------------------------------------------------------
# Silent failure (never block requests due to errors)
# ---------------------------------------------------------------------------

class TestSilentFailure:
    """Verify rate limiting errors are caught and do not block requests."""

    def test_check_global_catches_exceptions(self):
        """check_global_anonymous_limit has exception handling."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_global_anonymous_limit')
        assert 'except Exception' in func_src or 'except:' in func_src
        assert 'return None' in func_src

    def test_record_global_catches_exceptions(self):
        """record_global_anonymous_usage has exception handling."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'record_global_anonymous_usage')
        assert 'except Exception' in func_src or 'except:' in func_src


# ---------------------------------------------------------------------------
# Decorator records both global and session usage
# ---------------------------------------------------------------------------

class TestDecoratorRecordsBoth:
    """Verify decorator records usage on both counters."""

    def test_decorator_records_global_usage(self):
        """Decorator calls record_global_anonymous_usage on success."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        lines = RATE_LIMITING_SOURCE.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        assert 'record_global_anonymous_usage' in func_src

    def test_decorator_still_records_session_usage(self):
        """Decorator still calls record_anonymous_usage on success."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        lines = RATE_LIMITING_SOURCE.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                func_src = '\n'.join(lines[node.lineno - 1:node.end_lineno])
                break
        assert 'record_anonymous_usage' in func_src


# ---------------------------------------------------------------------------
# Functional tests with Flask app context
# ---------------------------------------------------------------------------

class TestFunctionalGlobalCap:
    """Functional tests using Flask test infrastructure."""

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
        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 3  # low for testing
        app.config['ANON_SESSION_LIMIT_CHATBOT'] = 50  # high so session limit doesn't interfere
        app.config['ANON_SESSION_LIMIT_ANALYSIS'] = 50
        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return None

        return app

    def test_allows_within_global_limit(self, app):
        """Requests within the global limit are allowed."""
        import services.rate_limiting as rl

        with app.test_request_context():
            result = rl.check_global_anonymous_limit()
            assert result is None

    def test_blocks_at_global_limit(self, app):
        """Requests at the global limit are blocked."""
        import services.rate_limiting as rl

        with app.test_request_context():
            # Simulate reaching the limit
            for _ in range(3):
                rl.record_global_anonymous_usage()
            result = rl.check_global_anonymous_limit()
            assert result is not None
            assert result['limited'] is True
            assert result['limit_type'] == 'anonymous_global_daily'
            assert 'message' in result

    def test_first_call_initializes_counter(self, app):
        """First anonymous call of the day initializes counter correctly."""
        import services.rate_limiting as rl

        with app.test_request_context():
            assert rl._global_date is None
            rl.record_global_anonymous_usage()
            assert rl._global_count == 1
            assert rl._global_date == datetime.now(timezone.utc).date()

    def test_counter_at_exactly_limit(self, app):
        """Counter at exactly the limit — next call is rejected."""
        import services.rate_limiting as rl

        with app.test_request_context():
            for _ in range(3):
                rl.record_global_anonymous_usage()
            # At exactly the limit
            assert rl._global_count == 3
            result = rl.check_global_anonymous_limit()
            assert result is not None
            assert result['limited'] is True

    def test_authenticated_user_bypasses_global_cap(self, app):
        """Authenticated users are not affected by global cap."""
        import services.rate_limiting as rl

        mock_user = MagicMock()
        mock_user.is_authenticated = True

        with app.test_request_context():
            # Max out the global cap
            for _ in range(3):
                rl.record_global_anonymous_usage()

            with patch.object(rl, 'current_user', mock_user):
                result = rl.check_global_anonymous_limit()
                assert result is None

    def test_authenticated_user_does_not_increment_counter(self, app):
        """Authenticated user calls don't count toward global cap."""
        import services.rate_limiting as rl

        mock_user = MagicMock()
        mock_user.is_authenticated = True

        with app.test_request_context():
            with patch.object(rl, 'current_user', mock_user):
                rl.record_global_anonymous_usage()
                rl.record_global_anonymous_usage()
            # Counter should still be 0
            assert rl._global_count == 0

    def test_counter_resets_on_new_day(self, app):
        """Counter resets when the UTC date changes."""
        import services.rate_limiting as rl

        with app.test_request_context():
            # Use up the limit
            for _ in range(3):
                rl.record_global_anonymous_usage()
            assert rl._global_count == 3

            # Simulate date change
            yesterday = date(2020, 1, 1)
            with rl._global_lock:
                rl._global_date = yesterday

            # Next check should reset the counter
            result = rl.check_global_anonymous_limit()
            assert result is None
            assert rl._global_count == 0

    def test_zero_limit_blocks_immediately(self, app):
        """Config limit of 0 blocks all anonymous AI calls."""
        import services.rate_limiting as rl

        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 0
        with app.test_request_context():
            result = rl.check_global_anonymous_limit()
            assert result is not None
            assert result['limited'] is True

    def test_configurable_limit(self, app):
        """Changing ANON_GLOBAL_DAILY_LIMIT config changes behavior."""
        import services.rate_limiting as rl

        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 5
        with app.test_request_context():
            for _ in range(5):
                rl.record_global_anonymous_usage()
            result = rl.check_global_anonymous_limit()
            assert result is not None

    def test_global_cap_before_session_limit_in_decorator(self, app):
        """When global cap is hit, decorator returns global response (not session)."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-global-cap', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            # Max out global cap
            with app.test_request_context():
                for _ in range(3):
                    rl.record_global_anonymous_usage()

            resp = client.post('/test-global-cap')
            assert resp.status_code == 429
            data = resp.get_json()
            assert data['limit_type'] == 'anonymous_global_daily'

    def test_decorator_records_global_on_success(self, app):
        """Decorator increments global counter on successful response."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-global-record', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            resp = client.post('/test-global-record')
            assert resp.status_code == 200
            assert rl._global_count == 1

    def test_decorator_does_not_record_global_on_error(self, app):
        """Decorator does not increment global counter on error response."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-global-error', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_ANALYSIS)
        def test_view():
            return jsonify({'status': 'error'}), 500

        with app.test_client() as client:
            resp = client.post('/test-global-error')
            assert resp.status_code == 500
            assert rl._global_count == 0

    def test_session_and_global_both_enforced(self, app):
        """Both global and session limits are enforced simultaneously."""
        import services.rate_limiting as rl
        from flask import jsonify

        app.config['ANON_SESSION_LIMIT_CHATBOT'] = 2  # lower session limit
        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 10  # higher global limit

        @app.route('/test-both', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            # First 2 calls succeed
            for _ in range(2):
                resp = client.post('/test-both')
                assert resp.status_code == 200

            # 3rd call blocked by session limit (not global)
            resp = client.post('/test-both')
            assert resp.status_code == 429
            data = resp.get_json()
            assert data['limit_type'] == 'anonymous_session'

    def test_global_takes_precedence_when_both_exceeded(self, app):
        """When both limits would trigger, global response is returned (checked first)."""
        import services.rate_limiting as rl
        from flask import jsonify

        app.config['ANON_SESSION_LIMIT_CHATBOT'] = 1
        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 1

        @app.route('/test-precedence', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            # Use up both limits
            resp = client.post('/test-precedence')
            assert resp.status_code == 200

            # Both limits exceeded — global should take precedence
            resp = client.post('/test-precedence')
            assert resp.status_code == 429
            data = resp.get_json()
            assert data['limit_type'] == 'anonymous_global_daily'

    def test_thread_safety(self, app):
        """Multiple threads incrementing counter don't lose counts."""
        import services.rate_limiting as rl

        app.config['ANON_GLOBAL_DAILY_LIMIT'] = 10000

        errors = []

        def increment_many():
            try:
                with app.test_request_context():
                    for _ in range(100):
                        rl.record_global_anonymous_usage()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert rl._global_count == 1000

    def test_check_exception_returns_none(self, app):
        """check_global_anonymous_limit returns None on internal error."""
        import services.rate_limiting as rl

        with app.test_request_context():
            with patch.object(rl, '_get_global_daily_limit', side_effect=RuntimeError('boom')):
                result = rl.check_global_anonymous_limit()
                assert result is None

    def test_record_exception_is_silent(self, app):
        """record_global_anonymous_usage catches errors silently."""
        import services.rate_limiting as rl

        with app.test_request_context():
            with patch.object(rl, '_global_lock', side_effect=RuntimeError('boom')):
                # Should not raise
                rl.record_global_anonymous_usage()
