"""
US-13.2.2: Remove Anonymous AI Trial

Tests for:
- @login_required added to all AI routes (chatbot, section AI, portfolio AI)
- @anonymous_rate_limit decorators preserved (layer, don't delete)
- AI UI elements hidden for anonymous users via template conditionals
- Phase 12 anonymous-to-signup redirect flow removed (anonymous users simply don't see AI buttons)
- Registered users retain full AI access with daily rate limits
- SITE_MODE config controls subscriber daily limit behavior
- Unauthorized API handler returns JSON 401 for API routes
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
EXTENSIONS_FILE = SIGNALTRACKERS_DIR / 'extensions.py'
EXTENSIONS_SOURCE = EXTENSIONS_FILE.read_text()
CONFIG_FILE = SIGNALTRACKERS_DIR / 'config.py'
CONFIG_SOURCE = CONFIG_FILE.read_text()
RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
ENV_EXAMPLE_FILE = REPO_ROOT / '.env.example'
ENV_EXAMPLE_SOURCE = ENV_EXAMPLE_FILE.read_text()


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


# All AI route functions
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


# ---------------------------------------------------------------------------
# AC1: All AI routes require @login_required
# ---------------------------------------------------------------------------

class TestAIRoutesRequireLogin:
    """All AI routes must have @login_required to block anonymous access."""

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_login_required_present(self, func_name):
        """AI route has @login_required decorator."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'login_required' in decorators, \
            f'{func_name} must have @login_required'

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_rate_limit_still_present(self, func_name):
        """AI route retains @anonymous_rate_limit (layer, don't delete)."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'anonymous_rate_limit' in decorators, \
            f'{func_name} must retain @anonymous_rate_limit'

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_login_required_before_rate_limit(self, func_name):
        """@login_required comes before @anonymous_rate_limit in decorator stack."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        login_idx = decorators.index('login_required')
        rate_idx = decorators.index('anonymous_rate_limit')
        # In Python, decorators are applied bottom-up, so login_required
        # appearing before anonymous_rate_limit means it executes first
        assert login_idx < rate_idx, \
            f'{func_name}: @login_required must be stacked before @anonymous_rate_limit'


# ---------------------------------------------------------------------------
# AC2: AI UI elements hidden for anonymous users
# ---------------------------------------------------------------------------

class TestAIUIHiddenForAnonymous:
    """AI interaction elements use template conditionals for auth check."""

    def _read_template(self, name):
        return (SIGNALTRACKERS_DIR / 'templates' / name).read_text()

    def test_chatbot_fab_wrapped_in_auth_check(self):
        """Chatbot FAB is inside {% if current_user.is_authenticated %}."""
        base = self._read_template('base.html')
        fab_idx = base.find('id="chatbot-fab"')
        assert fab_idx != -1, 'Chatbot FAB not found in base.html'
        # Check that an auth conditional appears before the FAB
        before_fab = base[:fab_idx]
        last_if = before_fab.rfind('{% if current_user.is_authenticated %}')
        last_endif = before_fab.rfind('{% endif %}')
        assert last_if != -1, 'No auth conditional before chatbot FAB'
        assert last_if > last_endif, \
            'Auth conditional must be open (not closed) before chatbot FAB'

    def test_chatbot_panel_wrapped_in_auth_check(self):
        """Chatbot panel is inside {% if current_user.is_authenticated %}."""
        base = self._read_template('base.html')
        panel_idx = base.find('id="chatbot-panel"')
        assert panel_idx != -1, 'Chatbot panel not found'
        before_panel = base[:panel_idx]
        last_if = before_panel.rfind('{% if current_user.is_authenticated %}')
        last_endif = before_panel.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    def test_briefing_toolbar_wrapped_in_auth_check(self):
        """AI briefing toolbar is inside auth conditional."""
        base = self._read_template('base.html')
        toolbar_idx = base.find('id="ai-briefing-toolbar"')
        assert toolbar_idx != -1
        before = base[:toolbar_idx]
        last_if = before.rfind('{% if current_user.is_authenticated %}')
        last_endif = before.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    def test_mobile_pill_wrapped_in_auth_check(self):
        """AI briefing mobile pill is inside auth conditional."""
        base = self._read_template('base.html')
        pill_idx = base.find('id="ai-briefing-confirm-pill"')
        assert pill_idx != -1
        before = base[:pill_idx]
        last_if = before.rfind('{% if current_user.is_authenticated %}')
        last_endif = before.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    def test_ai_js_scripts_wrapped_in_auth_check(self):
        """AI JavaScript files are only loaded for authenticated users."""
        base = self._read_template('base.html')
        chatbot_js_idx = base.find('chatbot.js')
        assert chatbot_js_idx != -1
        before = base[:chatbot_js_idx]
        last_if = before.rfind('{% if current_user.is_authenticated %}')
        last_endif = before.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    @pytest.mark.parametrize('template,section_id', [
        ('index.html', 'briefing-section'),
        ('index.html', 'conditions-section'),
        ('rates.html', 'asset-rates'),
        ('dollar.html', 'asset-dollar'),
        ('crypto.html', 'asset-crypto'),
        ('safe_havens.html', 'asset-safe-havens'),
        ('credit.html', 'asset-credit'),
        ('credit.html', 'recession-panel-section'),
        ('equity.html', 'asset-equity'),
        ('equity.html', 'sector-tone-section'),
        ('equity.html', 'trade-pulse-section'),
        ('property.html', 'asset-property'),
    ])
    def test_section_ai_btn_wrapped_in_auth_check(self, template, section_id):
        """Section AI buttons use auth conditional."""
        html = self._read_template(template)
        btn_pattern = f'data-section-id="{section_id}"'
        btn_idx = html.find(btn_pattern)
        assert btn_idx != -1, f'Button {section_id} not found in {template}'
        # Check the line containing the button has the auth conditional
        line_start = html.rfind('\n', 0, btn_idx) + 1
        line = html[line_start:html.find('\n', btn_idx)]
        assert '{% if current_user.is_authenticated %}' in line, \
            f'Button {section_id} in {template} not wrapped in auth conditional'


# ---------------------------------------------------------------------------
# AC3: Phase 12 infrastructure preserved (layer, don't delete)
# ---------------------------------------------------------------------------

class TestPhase12InfrastructurePreserved:
    """Phase 12 anonymous rate limiting code must remain in codebase."""

    def test_anonymous_rate_limit_decorator_exists(self):
        """anonymous_rate_limit decorator function still exists."""
        assert 'def anonymous_rate_limit' in RATE_LIMITING_SOURCE

    def test_check_anonymous_rate_limit_exists(self):
        """check_anonymous_rate_limit function still exists."""
        assert 'def check_anonymous_rate_limit' in RATE_LIMITING_SOURCE

    def test_check_global_anonymous_limit_exists(self):
        """check_global_anonymous_limit function still exists."""
        assert 'def check_global_anonymous_limit' in RATE_LIMITING_SOURCE

    def test_session_tracking_exists(self):
        """Session-based rate tracking code still present."""
        assert '_SESSION_KEY_PREFIX' in RATE_LIMITING_SOURCE

    def test_global_daily_limit_exists(self):
        """Global daily anonymous cap code still present."""
        assert 'DEFAULT_GLOBAL_DAILY_LIMIT' in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC4: SITE_MODE config and subscriber daily limits
# ---------------------------------------------------------------------------

class TestSiteModeConfig:
    """SITE_MODE controls access model and rate limit behavior."""

    def test_site_mode_in_config(self):
        """SITE_MODE config variable exists."""
        assert 'SITE_MODE' in CONFIG_SOURCE

    def test_site_mode_default_invite_only(self):
        """SITE_MODE defaults to 'invite_only'."""
        assert "SITE_MODE = os.environ.get('SITE_MODE', 'invite_only')" in CONFIG_SOURCE

    def test_site_mode_in_env_example(self):
        """SITE_MODE documented in .env.example."""
        assert 'SITE_MODE' in ENV_EXAMPLE_SOURCE

    def test_rate_limiting_checks_site_mode(self):
        """Subscriber daily limit check uses SITE_MODE."""
        assert 'SITE_MODE' in RATE_LIMITING_SOURCE

    def test_invite_only_skips_paid_access_check(self):
        """In invite_only mode, all authenticated users get subscriber limits."""
        assert "site_mode != 'invite_only'" in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC5: Unauthorized API handler returns JSON 401
# ---------------------------------------------------------------------------

class TestUnauthorizedHandler:
    """API routes return JSON 401, page routes redirect to login."""

    def test_unauthorized_handler_defined(self):
        """Custom unauthorized handler is registered."""
        assert 'unauthorized_handler' in EXTENSIONS_SOURCE

    def test_api_routes_return_json(self):
        """Handler checks for /api/ prefix to return JSON."""
        assert "/api/" in EXTENSIONS_SOURCE

    def test_api_returns_401(self):
        """Handler returns 401 for API routes."""
        assert '401' in EXTENSIONS_SOURCE


# ---------------------------------------------------------------------------
# AC6: Portfolio CRUD routes still require login
# ---------------------------------------------------------------------------

class TestPortfolioCRUDStillProtected:
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
# AC7: Daily briefing remains visible to anonymous users
# ---------------------------------------------------------------------------

class TestDailyBriefingStillVisible:
    """Pre-generated daily briefing is not behind auth check."""

    def test_briefing_narrative_not_auth_gated(self):
        """Briefing narrative div is not wrapped in auth conditional."""
        index_html = (SIGNALTRACKERS_DIR / 'templates' / 'index.html').read_text()
        narrative_idx = index_html.find('id="briefing-narrative"')
        if narrative_idx == -1:
            narrative_idx = index_html.find('briefing-narrative')
        if narrative_idx == -1:
            # Briefing content may use different ID — check for briefing section
            narrative_idx = index_html.find('id="briefing-section"')
        assert narrative_idx != -1, 'Briefing section not found in index.html'
        # The section itself should NOT be inside an auth conditional
        # (only the AI button within it should be)
        before = index_html[:narrative_idx]
        # Count open auth ifs vs endifs
        opens = before.count('{% if current_user.is_authenticated %}')
        closes = before.count('{% endif %}')
        assert opens <= closes, \
            'Briefing section must not be inside an auth conditional block'
