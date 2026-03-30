"""
US-12.4.1: Open AI routes for anonymous access

Tests for:
- @login_required removed from AI routes (chatbot, section AI, portfolio AI)
- Portfolio CRUD routes still require @login_required
- Portfolio AI analysis handles anonymous users gracefully
- Rate limiting decorators remain on all AI routes
- Authenticated users unaffected
"""

import ast
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'
DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()


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
# AC1: @login_required removed from chatbot route
# ---------------------------------------------------------------------------

class TestChatbotRouteOpen:
    """Chatbot route must not require login."""

    def test_chatbot_no_login_required(self):
        """api_chatbot has no @login_required decorator."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_chatbot')
        assert 'login_required' not in decorators

    def test_chatbot_has_rate_limit(self):
        """api_chatbot has @anonymous_rate_limit decorator."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_chatbot')
        assert 'anonymous_rate_limit' in decorators

    def test_section_opening_no_login_required(self):
        """api_chatbot_section_opening has no @login_required."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_chatbot_section_opening')
        assert 'login_required' not in decorators

    def test_section_opening_has_rate_limit(self):
        """api_chatbot_section_opening has @anonymous_rate_limit."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_chatbot_section_opening')
        assert 'anonymous_rate_limit' in decorators


# ---------------------------------------------------------------------------
# AC2: @login_required removed from section AI routes
# ---------------------------------------------------------------------------

class TestSectionAIRoutesOpen:
    """All 7 section AI generate routes must not require login."""

    SECTION_AI_FUNCS = [
        'api_generate_summary',
        'api_generate_crypto_summary',
        'api_generate_equity_summary',
        'api_generate_rates_summary',
        'api_generate_dollar_summary',
        'api_generate_credit_summary',
        'api_generate_market_synthesis',
    ]

    @pytest.mark.parametrize('func_name', SECTION_AI_FUNCS)
    def test_no_login_required(self, func_name):
        """Section AI route has no @login_required."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'login_required' not in decorators, \
            f'{func_name} still has @login_required'

    @pytest.mark.parametrize('func_name', SECTION_AI_FUNCS)
    def test_has_rate_limit(self, func_name):
        """Section AI route has @anonymous_rate_limit."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'anonymous_rate_limit' in decorators, \
            f'{func_name} missing @anonymous_rate_limit'


# ---------------------------------------------------------------------------
# AC3: @login_required removed from portfolio AI analysis route
# ---------------------------------------------------------------------------

class TestPortfolioAIRouteOpen:
    """Portfolio AI analysis route must not require login."""

    def test_portfolio_generate_no_login_required(self):
        """api_generate_portfolio_summary has no @login_required."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_portfolio_summary')
        assert 'login_required' not in decorators

    def test_portfolio_generate_has_rate_limit(self):
        """api_generate_portfolio_summary has @anonymous_rate_limit."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, 'api_generate_portfolio_summary')
        assert 'anonymous_rate_limit' in decorators


# ---------------------------------------------------------------------------
# AC4: AI routes detect auth status and pass appropriate context
# ---------------------------------------------------------------------------

class TestAnonymousContextHandling:
    """AI routes handle anonymous vs authenticated users."""

    def test_portfolio_generate_checks_is_authenticated(self):
        """Portfolio generate route checks current_user.is_authenticated."""
        # Find the function body and check for auth detection
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_generate_portfolio_summary':
                func_source = ast.get_source_segment(DASHBOARD_SOURCE, node)
                assert 'is_authenticated' in func_source, \
                    'Portfolio generate must check authentication status'
                return
        pytest.fail('api_generate_portfolio_summary not found')

    def test_anonymous_portfolio_returns_helpful_message(self):
        """Anonymous portfolio AI returns a helpful signup message."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_generate_portfolio_summary':
                func_source = ast.get_source_segment(DASHBOARD_SOURCE, node)
                assert 'anonymous' in func_source.lower(), \
                    'Portfolio generate must handle anonymous case'
                assert 'subscribe' in func_source.lower() or 'account' in func_source.lower() or 'sign' in func_source.lower(), \
                    'Anonymous response should mention subscribing or creating an account'
                return
        pytest.fail('api_generate_portfolio_summary not found')

    def test_chatbot_metering_checks_auth(self):
        """Chatbot metering only records for authenticated users."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_chatbot':
                func_source = ast.get_source_segment(DASHBOARD_SOURCE, node)
                assert 'current_user.is_authenticated' in func_source, \
                    'Chatbot must check auth before metering'
                return
        pytest.fail('api_chatbot not found')


# ---------------------------------------------------------------------------
# AC5: Anonymous users identified by session cookie
# ---------------------------------------------------------------------------

class TestSessionIdentification:
    """Anonymous users use session cookie for rate limiting."""

    def test_rate_limiting_uses_session(self):
        """Rate limiting service uses Flask session."""
        rate_limiting_source = (SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py').read_text()
        assert 'session' in rate_limiting_source, \
            'Rate limiting must use Flask session for anonymous tracking'


# ---------------------------------------------------------------------------
# AC6: Portfolio CRUD routes still require login
# ---------------------------------------------------------------------------

class TestPortfolioCRUDProtected:
    """Portfolio data routes must keep @login_required."""

    PROTECTED_FUNCS = [
        'api_portfolio_get',
        'api_portfolio_add',
        'api_portfolio_update',
        'api_portfolio_delete',
        'api_portfolio_validate',
        'api_portfolio_summary',
    ]

    @pytest.mark.parametrize('func_name', PROTECTED_FUNCS)
    def test_portfolio_crud_requires_login(self, func_name):
        """Portfolio CRUD route has @login_required."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'login_required' in decorators, \
            f'{func_name} must keep @login_required'


# ---------------------------------------------------------------------------
# AC7: Authenticated users completely unaffected
# ---------------------------------------------------------------------------

class TestAuthenticatedUsersUnaffected:
    """Authenticated user paths must remain intact."""

    def test_portfolio_generate_still_uses_user_id(self):
        """Portfolio generate still uses current_user.id for auth users."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_generate_portfolio_summary':
                func_source = ast.get_source_segment(DASHBOARD_SOURCE, node)
                assert 'current_user.id' in func_source, \
                    'Authenticated path must still use current_user.id'
                return
        pytest.fail('api_generate_portfolio_summary not found')

    def test_portfolio_generate_still_calls_db(self):
        """Portfolio generate still calls db_get_portfolio_summary_for_ai."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_generate_portfolio_summary':
                func_source = ast.get_source_segment(DASHBOARD_SOURCE, node)
                assert 'db_get_portfolio_summary_for_ai' in func_source, \
                    'Authenticated path must still load user portfolio'
                return
        pytest.fail('api_generate_portfolio_summary not found')

    def test_portfolio_generate_metering_for_auth(self):
        """Portfolio generate still records metering for authenticated users."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_generate_portfolio_summary':
                func_source = ast.get_source_segment(DASHBOARD_SOURCE, node)
                assert 'record_usage' in func_source, \
                    'Metering must still be recorded for authenticated users'
                return
        pytest.fail('api_generate_portfolio_summary not found')


# ---------------------------------------------------------------------------
# AC8: No regression — rate limiting decorators present on all AI routes
# ---------------------------------------------------------------------------

class TestRateLimitingIntact:
    """All AI routes must retain rate limiting decorators."""

    ALL_AI_FUNCS = [
        'api_chatbot',
        'api_chatbot_section_opening',
        'api_generate_summary',
        'api_generate_crypto_summary',
        'api_generate_equity_summary',
        'api_generate_rates_summary',
        'api_generate_dollar_summary',
        'api_generate_credit_summary',
        'api_generate_market_synthesis',
        'api_generate_portfolio_summary',
    ]

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_rate_limit_decorator_present(self, func_name):
        """AI route has @anonymous_rate_limit decorator."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'anonymous_rate_limit' in decorators, \
            f'{func_name} must have @anonymous_rate_limit'
