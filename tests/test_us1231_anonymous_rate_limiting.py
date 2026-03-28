"""
US-12.3.1: Per-session anonymous rate limiting

Tests for:
- Anonymous session rate limit checking and enforcement
- Usage counter tracking via Flask session
- Registered users bypass anonymous limits
- Configurable limits via app config
- Structured JSON response format
- Decorator integration on AI endpoints
- Reusable decorator pattern
- Edge cases: first request, counter initialization, tampered sessions
"""

import ast
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'
RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
CONFIG_FILE = SIGNALTRACKERS_DIR / 'config.py'

DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()
RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
CONFIG_SOURCE = CONFIG_FILE.read_text()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_decorator_names(source: str, func_name: str) -> list:
    """Extract decorator names for a given function from source."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            decorators = []
            for d in node.decorator_list:
                if isinstance(d, ast.Call):
                    if isinstance(d.func, ast.Name):
                        decorators.append(d.func.id)
                    elif isinstance(d.func, ast.Attribute):
                        decorators.append(d.func.attr)
                elif isinstance(d, ast.Attribute):
                    decorators.append(d.attr)
                elif isinstance(d, ast.Name):
                    decorators.append(d.id)
            return decorators
    return []


# ---------------------------------------------------------------------------
# AC1: Session tracks usage counts
# ---------------------------------------------------------------------------

class TestSessionTracking:
    """Verify Flask session is used to track anonymous usage counts."""

    def test_rate_limiting_imports_session(self):
        """rate_limiting.py imports Flask session."""
        assert 'from flask import' in RATE_LIMITING_SOURCE
        assert 'session' in RATE_LIMITING_SOURCE

    def test_session_key_prefix_defined(self):
        """Session keys use a consistent prefix."""
        assert '_SESSION_KEY_PREFIX' in RATE_LIMITING_SOURCE

    def test_record_usage_increments_session(self):
        """record_anonymous_usage increments a session counter."""
        assert 'session[key] = session.get(key, 0) + 1' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC2: Default limits configured
# ---------------------------------------------------------------------------

class TestDefaultLimits:
    """Verify default limits: ~5 chatbot, ~2 analysis."""

    def test_default_chatbot_limit(self):
        """Default chatbot limit is 5."""
        assert "CATEGORY_CHATBOT: 5" in RATE_LIMITING_SOURCE or \
               "'chatbot': 5" in RATE_LIMITING_SOURCE

    def test_default_analysis_limit(self):
        """Default analysis limit is 2."""
        assert "CATEGORY_ANALYSIS: 2" in RATE_LIMITING_SOURCE or \
               "'analysis': 2" in RATE_LIMITING_SOURCE

    def test_config_has_anon_session_limits(self):
        """config.py defines ANON_SESSION_LIMIT_ variables."""
        assert 'ANON_SESSION_LIMIT_CHATBOT' in CONFIG_SOURCE
        assert 'ANON_SESSION_LIMIT_ANALYSIS' in CONFIG_SOURCE


# ---------------------------------------------------------------------------
# AC3: Limits configurable via environment variables
# ---------------------------------------------------------------------------

class TestConfigurableLimits:
    """Verify limits are configurable without code changes."""

    def test_config_reads_env_vars(self):
        """Config reads limits from environment variables."""
        assert "os.environ.get('ANON_SESSION_LIMIT_CHATBOT'" in CONFIG_SOURCE
        assert "os.environ.get('ANON_SESSION_LIMIT_ANALYSIS'" in CONFIG_SOURCE

    def test_rate_limiting_reads_app_config(self):
        """rate_limiting.py reads limits from app config."""
        assert 'current_app.config.get' in RATE_LIMITING_SOURCE

    def test_env_example_documents_limits(self):
        """The .env.example file documents the rate limit variables."""
        env_example_path = REPO_ROOT / '.env.example'
        if not env_example_path.exists():
            pytest.skip('.env.example not available in container')
        env_example = env_example_path.read_text()
        assert 'ANON_SESSION_LIMIT_CHATBOT' in env_example
        assert 'ANON_SESSION_LIMIT_ANALYSIS' in env_example


# ---------------------------------------------------------------------------
# AC4: Structured JSON response on limit hit
# ---------------------------------------------------------------------------

class TestRateLimitResponse:
    """Verify structured JSON response format."""

    def test_response_has_limited_field(self):
        """Rate limit response includes 'limited': True."""
        assert "'limited': True" in RATE_LIMITING_SOURCE

    def test_response_has_limit_type(self):
        """Rate limit response includes limit_type: 'anonymous_session'."""
        assert "'limit_type': 'anonymous_session'" in RATE_LIMITING_SOURCE

    def test_response_has_message(self):
        """Rate limit response includes a user-facing message."""
        assert "'message'" in RATE_LIMITING_SOURCE

    def test_response_has_category(self):
        """Rate limit response includes the category."""
        assert "'category': category" in RATE_LIMITING_SOURCE

    def test_decorator_returns_429(self):
        """Decorator returns HTTP 429 when limit exceeded."""
        assert '429' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC5: Signup encouragement message
# ---------------------------------------------------------------------------

class TestSignupMessage:
    """Verify the limit response encourages signup."""

    def test_message_mentions_account(self):
        """Limit message encourages creating an account."""
        # Check the message contains signup-related text
        assert 'account' in RATE_LIMITING_SOURCE.lower() or \
               'sign' in RATE_LIMITING_SOURCE.lower()


# ---------------------------------------------------------------------------
# AC6: Registered users bypass anonymous limits
# ---------------------------------------------------------------------------

class TestRegisteredUserBypass:
    """Verify authenticated users are not affected by anonymous limits."""

    def test_check_bypasses_authenticated_users(self):
        """check_anonymous_rate_limit returns None for authenticated users."""
        assert 'current_user.is_authenticated' in RATE_LIMITING_SOURCE

    def test_record_skips_authenticated_users(self):
        """record_anonymous_usage skips incrementing for authenticated users."""
        # Both check and record functions should check is_authenticated
        occurrences = RATE_LIMITING_SOURCE.count('current_user.is_authenticated')
        assert occurrences >= 2, \
            "Both check and record functions should check is_authenticated"


# ---------------------------------------------------------------------------
# AC7: Reusable decorator
# ---------------------------------------------------------------------------

class TestReusableDecorator:
    """Verify decorator is reusable and parameterized."""

    def test_decorator_exists(self):
        """anonymous_rate_limit decorator function is defined."""
        assert 'def anonymous_rate_limit(category)' in RATE_LIMITING_SOURCE

    def test_decorator_is_parameterized(self):
        """Decorator accepts a category parameter."""
        tree = ast.parse(RATE_LIMITING_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'anonymous_rate_limit':
                args = [a.arg for a in node.args.args]
                assert 'category' in args
                break
        else:
            pytest.fail("anonymous_rate_limit function not found")

    def test_decorator_uses_functools_wraps(self):
        """Decorator preserves function metadata with @wraps."""
        assert 'from functools import wraps' in RATE_LIMITING_SOURCE
        assert '@wraps(f)' in RATE_LIMITING_SOURCE

    def test_category_constants_exported(self):
        """Category constants are defined for reuse."""
        assert 'CATEGORY_CHATBOT' in RATE_LIMITING_SOURCE
        assert 'CATEGORY_ANALYSIS' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# Decorator applied to all AI endpoints
# ---------------------------------------------------------------------------

class TestEndpointDecoration:
    """Verify anonymous_rate_limit decorator is applied to all AI endpoints."""

    # Chatbot endpoints → CATEGORY_CHATBOT
    def test_chatbot_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_chatbot')
        assert 'anonymous_rate_limit' in decorators

    def test_section_opening_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_chatbot_section_opening')
        assert 'anonymous_rate_limit' in decorators

    # Summary/analysis endpoints → CATEGORY_ANALYSIS
    def test_ai_summary_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_summary')
        assert 'anonymous_rate_limit' in decorators

    def test_crypto_summary_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_crypto_summary')
        assert 'anonymous_rate_limit' in decorators

    def test_equity_summary_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_equity_summary')
        assert 'anonymous_rate_limit' in decorators

    def test_rates_summary_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_rates_summary')
        assert 'anonymous_rate_limit' in decorators

    def test_dollar_summary_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_dollar_summary')
        assert 'anonymous_rate_limit' in decorators

    def test_credit_summary_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_credit_summary')
        assert 'anonymous_rate_limit' in decorators

    def test_market_synthesis_endpoint_has_rate_limit(self):
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_market_synthesis')
        assert 'anonymous_rate_limit' in decorators


# ---------------------------------------------------------------------------
# Import wiring
# ---------------------------------------------------------------------------

class TestImportWiring:
    """Verify dashboard.py imports rate limiting components."""

    def test_dashboard_imports_decorator(self):
        assert 'from services.rate_limiting import' in DASHBOARD_SOURCE
        assert 'anonymous_rate_limit' in DASHBOARD_SOURCE

    def test_dashboard_imports_categories(self):
        assert 'CATEGORY_CHATBOT' in DASHBOARD_SOURCE
        assert 'CATEGORY_ANALYSIS' in DASHBOARD_SOURCE


# ---------------------------------------------------------------------------
# Security: silent failure pattern
# ---------------------------------------------------------------------------

class TestSilentFailure:
    """Verify rate limiting never breaks AI features on error."""

    def test_check_has_exception_handler(self):
        """check_anonymous_rate_limit catches all exceptions."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'check_anonymous_rate_limit')
        assert 'except Exception' in func_src
        assert 'return None' in func_src

    def test_record_has_exception_handler(self):
        """record_anonymous_usage catches all exceptions."""
        func_src = _get_function_source_from_file(RATE_LIMITING_SOURCE, 'record_anonymous_usage')
        assert 'except Exception' in func_src

    def test_non_ai_endpoints_not_decorated(self):
        """Page load routes (non-AI) are not decorated with rate limiting."""
        # The index/home route should NOT have the decorator
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'index')
        assert 'anonymous_rate_limit' not in decorators


def _get_function_source_from_file(source: str, func_name: str) -> str:
    """Extract a function's source from a source string."""
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            start = node.lineno - 1
            end = node.end_lineno
            return '\n'.join(lines[start:end])
    return ''


# ---------------------------------------------------------------------------
# Functional tests with Flask app context
# ---------------------------------------------------------------------------

class TestFunctionalRateLimiting:
    """Functional tests using Flask test infrastructure."""

    @pytest.fixture
    def app(self):
        """Create a minimal Flask app with LoginManager for testing."""
        from flask import Flask
        from flask_login import LoginManager
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['ANON_SESSION_LIMIT_CHATBOT'] = 3
        app.config['ANON_SESSION_LIMIT_ANALYSIS'] = 1
        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return None

        return app

    def test_check_allows_within_limit(self, app):
        """Requests within the limit are allowed."""
        import services.rate_limiting as rl

        with app.test_request_context():
            # Anonymous user (default with LoginManager, no login)
            result = rl.check_anonymous_rate_limit(rl.CATEGORY_CHATBOT)
            assert result is None

    def test_check_blocks_at_limit(self, app):
        """Requests at the limit are blocked."""
        import services.rate_limiting as rl
        from flask import session

        with app.test_request_context():
            session['rate_limit_chatbot'] = 3  # at the limit
            result = rl.check_anonymous_rate_limit(rl.CATEGORY_CHATBOT)
            assert result is not None
            assert result['limited'] is True
            assert result['limit_type'] == 'anonymous_session'
            assert result['category'] == 'chatbot'
            assert 'message' in result

    def test_check_allows_authenticated_user(self, app):
        """Authenticated users bypass limits entirely."""
        import services.rate_limiting as rl
        from flask import session

        mock_user = MagicMock()
        mock_user.is_authenticated = True

        with app.test_request_context():
            session['rate_limit_chatbot'] = 999  # way over limit
            with patch.object(rl, 'current_user', mock_user):
                result = rl.check_anonymous_rate_limit(rl.CATEGORY_CHATBOT)
                assert result is None

    def test_record_increments_counter(self, app):
        """Recording usage increments the session counter."""
        import services.rate_limiting as rl
        from flask import session

        with app.test_request_context():
            assert session.get('rate_limit_chatbot', 0) == 0
            rl.record_anonymous_usage(rl.CATEGORY_CHATBOT)
            assert session.get('rate_limit_chatbot') == 1
            rl.record_anonymous_usage(rl.CATEGORY_CHATBOT)
            assert session.get('rate_limit_chatbot') == 2

    def test_record_skips_authenticated_user(self, app):
        """Recording usage does nothing for authenticated users."""
        import services.rate_limiting as rl
        from flask import session

        mock_user = MagicMock()
        mock_user.is_authenticated = True

        with app.test_request_context():
            with patch.object(rl, 'current_user', mock_user):
                rl.record_anonymous_usage(rl.CATEGORY_CHATBOT)
                assert session.get('rate_limit_chatbot') is None

    def test_separate_category_counters(self, app):
        """Chatbot and analysis have independent counters."""
        import services.rate_limiting as rl
        from flask import session

        with app.test_request_context():
            # Use up all analysis budget (limit=1)
            rl.record_anonymous_usage(rl.CATEGORY_ANALYSIS)
            assert rl.check_anonymous_rate_limit(rl.CATEGORY_ANALYSIS) is not None
            # Chatbot should still be available
            assert rl.check_anonymous_rate_limit(rl.CATEGORY_CHATBOT) is None

    def test_decorator_blocks_and_returns_429(self, app):
        """Decorator returns 429 JSON response when limit exceeded."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-endpoint', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['rate_limit_chatbot'] = 3  # at the limit

            resp = client.post('/test-endpoint')
            assert resp.status_code == 429
            data = resp.get_json()
            assert data['limited'] is True

    def test_decorator_allows_and_records_on_success(self, app):
        """Decorator allows request and records usage on 2xx response."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-ok', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_CHATBOT)
        def test_ok_view():
            return jsonify({'status': 'success'})

        with app.test_client() as client:
            resp = client.post('/test-ok')
            assert resp.status_code == 200

            with client.session_transaction() as sess:
                assert sess.get('rate_limit_chatbot') == 1

    def test_decorator_skips_record_on_error(self, app):
        """Decorator does not record usage when endpoint returns error."""
        import services.rate_limiting as rl
        from flask import jsonify

        @app.route('/test-error', methods=['POST'])
        @rl.anonymous_rate_limit(rl.CATEGORY_ANALYSIS)
        def test_error_view():
            return jsonify({'status': 'error'}), 500

        with app.test_client() as client:
            resp = client.post('/test-error')
            assert resp.status_code == 500

            with client.session_transaction() as sess:
                assert sess.get('rate_limit_analysis', 0) == 0

    def test_first_request_initializes_counter(self, app):
        """First request in a new session starts counter at 0."""
        import services.rate_limiting as rl
        from flask import session

        with app.test_request_context():
            # No session key set — should allow
            assert 'rate_limit_chatbot' not in session
            result = rl.check_anonymous_rate_limit(rl.CATEGORY_CHATBOT)
            assert result is None
