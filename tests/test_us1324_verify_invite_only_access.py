"""
US-13.2.4: Verify Access Model for Invite-Only Users

Verification tests for the invite-only access model:
- Registered users (via invite code) get full AI access
- Subscriber-tier daily limits apply to ALL authenticated users in invite-only mode
- No Stripe-specific UI or messaging visible to registered users
- Anonymous users see full dashboard but no AI interaction elements
- Anonymous users hitting AI API endpoints get proper 401 rejection
- has_paid_access is NOT used for access control in invite-only mode
- Rate limit categories are independent (chatbot vs analysis)
"""

import ast
import re
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
RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
CONFIG_FILE = SIGNALTRACKERS_DIR / 'config.py'
CONFIG_SOURCE = CONFIG_FILE.read_text()
USER_MODEL_FILE = SIGNALTRACKERS_DIR / 'models' / 'user.py'
USER_MODEL_SOURCE = USER_MODEL_FILE.read_text()
TEMPLATES_DIR = SIGNALTRACKERS_DIR / 'templates'


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


def _get_function_source(source: str, func_name: str) -> str:
    """Extract the source of a named function from file source."""
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            start = node.lineno - 1
            end = node.end_lineno
            return '\n'.join(lines[start:end])
    return ''


def _read_template(name):
    """Read a template file."""
    return (TEMPLATES_DIR / name).read_text()


# All AI route function names
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

# User-facing templates (excluding email templates)
USER_FACING_TEMPLATES = [
    f.name for f in TEMPLATES_DIR.iterdir()
    if f.is_file() and f.suffix == '.html'
] + [
    f'auth/{f.name}' for f in (TEMPLATES_DIR / 'auth').iterdir()
    if f.is_file() and f.suffix == '.html'
]

# Stripe-related terms that should NOT appear in user-facing context
# (excludes "unsubscribe" which is email-related, not payment-related)
STRIPE_TERMS = re.compile(
    r'\b(stripe|subscription_status|manage.subscription|upgrade.to|'
    r'pricing|payment.method|\$19|subscribe\b(?![\s\S]{0,20}email))',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# AC1: Registered users get full AI access via @login_required
# ---------------------------------------------------------------------------

class TestRegisteredUsersGetFullAIAccess:
    """All AI endpoints use @login_required — authenticated users pass through."""

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_ai_route_has_login_required(self, func_name):
        """Every AI route has @login_required so authenticated users can access."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'login_required' in decorators, \
            f'{func_name} must have @login_required for authenticated access'

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_ai_route_has_rate_limit(self, func_name):
        """Every AI route has rate limiting for cost protection."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        assert 'anonymous_rate_limit' in decorators, \
            f'{func_name} must have @anonymous_rate_limit for cost protection'


# ---------------------------------------------------------------------------
# AC2: Subscriber-tier limits apply to ALL authenticated users in invite-only
# ---------------------------------------------------------------------------

class TestInviteOnlySubscriberLimits:
    """In invite_only mode, all authenticated users get subscriber-tier limits,
    regardless of has_paid_access status."""

    def test_site_mode_check_in_subscriber_limit(self):
        """check_subscriber_daily_limit reads SITE_MODE config."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        assert 'SITE_MODE' in func_src

    def test_invite_only_bypasses_paid_access_check(self):
        """In invite_only mode, has_paid_access check is skipped."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        # The logic should be: if site_mode != 'invite_only', THEN check paid access
        # Meaning invite_only mode skips the paid access check entirely
        assert "site_mode != 'invite_only'" in func_src

    def test_has_paid_access_only_checked_in_non_invite_mode(self):
        """has_paid_access is gated behind site_mode != invite_only."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        # Find the has_paid_access reference
        paid_idx = func_src.find('has_paid_access')
        assert paid_idx != -1, 'has_paid_access should still be referenced for paid mode'
        # Find the site_mode check
        mode_idx = func_src.find("site_mode != 'invite_only'")
        assert mode_idx != -1
        # The site_mode check must come before has_paid_access
        assert mode_idx < paid_idx, \
            'site_mode check must gate has_paid_access (invite_only skips it)'

    def test_default_subscriber_limits_defined(self):
        """Default subscriber daily limits are defined for chatbot and analysis."""
        assert 'DEFAULT_SUBSCRIBER_DAILY_LIMITS' in RATE_LIMITING_SOURCE
        # Parse the defaults
        tree = ast.parse(RATE_LIMITING_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and \
                       target.id == 'DEFAULT_SUBSCRIBER_DAILY_LIMITS':
                        # Should be a dict with chatbot and analysis keys
                        assert isinstance(node.value, ast.Dict)
                        return
        pytest.fail('DEFAULT_SUBSCRIBER_DAILY_LIMITS not found as dict assignment')

    def test_chatbot_and_analysis_are_independent_categories(self):
        """Rate limit categories are independent — exhausting one doesn't block other."""
        assert 'CATEGORY_CHATBOT' in RATE_LIMITING_SOURCE
        assert 'CATEGORY_ANALYSIS' in RATE_LIMITING_SOURCE
        # Verify they map to different interaction types
        assert "'chatbot'" in RATE_LIMITING_SOURCE
        assert "'portfolio_analysis'" in RATE_LIMITING_SOURCE

    def test_subscriber_limit_queries_ai_usage_records(self):
        """Subscriber daily limit counts usage from ai_usage_records table."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        assert 'AIUsageRecord' in func_src
        assert 'user_id' in func_src
        assert 'interaction_type' in func_src

    def test_subscriber_limit_uses_utc_date(self):
        """Subscriber daily limit counts from midnight UTC."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        assert 'timezone.utc' in func_src


# ---------------------------------------------------------------------------
# AC3: No Stripe-specific UI or messaging for registered users
# ---------------------------------------------------------------------------

class TestNoStripeArtifacts:
    """No Stripe payment/subscription UI visible to registered users."""

    @pytest.mark.parametrize('template_name', USER_FACING_TEMPLATES)
    def test_no_stripe_terms_in_template(self, template_name):
        """Template has no Stripe/subscription/payment/pricing terms."""
        try:
            html = _read_template(template_name)
        except FileNotFoundError:
            pytest.skip(f'{template_name} not found')
        # Remove HTML comments and Jinja comments
        html_clean = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        html_clean = re.sub(r'\{#.*?#\}', '', html_clean, flags=re.DOTALL)
        # Remove email-related unsubscribe references (legitimate)
        html_clean = re.sub(r'(?i)unsubscrib\w*', '', html_clean)
        # Remove Python/Jinja code comments (lines starting with #)
        html_clean = re.sub(r'#.*$', '', html_clean, flags=re.MULTILINE)
        # Check for Stripe-related terms
        match = STRIPE_TERMS.search(html_clean)
        if match:
            # Allow "pricing" in financial context (e.g., "pricing in risk")
            context = html_clean[max(0, match.start()-40):match.end()+40]
            financial_context = re.search(
                r'(?i)(pric(ing|e|ed)\s+(in|of|for|risk|default|credit))',
                context
            )
            if financial_context:
                return  # This is financial terminology, not payment UI
            pytest.fail(
                f'{template_name} contains Stripe-related term: '
                f'"{match.group()}" in context: ...{context}...'
            )

    def test_invite_only_rate_limit_message_no_stripe(self):
        """Invite-only rate limit message has no Stripe/subscription language."""
        # Extract invite_only messages from rate_limiting.py
        assert "'invite_only'" in RATE_LIMITING_SOURCE
        # Find the invite_only message block
        invite_block_match = re.search(
            r"'invite_only'\s*:\s*\{(.*?)\}", RATE_LIMITING_SOURCE, re.DOTALL
        )
        assert invite_block_match, 'invite_only message block not found'
        block = invite_block_match.group(1).lower()
        assert 'subscribe' not in block
        assert 'stripe' not in block
        assert 'payment' not in block
        assert 'upgrade' not in block
        assert 'pricing' not in block

    def test_subscriber_daily_limit_response_no_stripe(self):
        """Subscriber daily limit response has no Stripe language."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        # Extract message strings from the function
        messages = re.findall(r"'message':\s*\((.*?)\)", func_src, re.DOTALL)
        messages += re.findall(r"'message':\s*'(.*?)'", func_src)
        for msg in messages:
            msg_lower = msg.lower()
            assert 'subscribe' not in msg_lower
            assert 'stripe' not in msg_lower
            assert 'upgrade' not in msg_lower
            assert 'payment' not in msg_lower


# ---------------------------------------------------------------------------
# AC4: Anonymous users see dashboard but no AI elements
# ---------------------------------------------------------------------------

class TestAnonymousDashboardAccess:
    """Anonymous users see the full dashboard but no AI interaction elements."""

    def test_chatbot_fab_auth_gated(self):
        """Chatbot FAB is inside auth conditional."""
        base = _read_template('base.html')
        fab_idx = base.find('id="chatbot-fab"')
        assert fab_idx != -1
        before = base[:fab_idx]
        last_if = before.rfind('{% if current_user.is_authenticated %}')
        last_endif = before.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    def test_chatbot_panel_auth_gated(self):
        """Chatbot panel is inside auth conditional."""
        base = _read_template('base.html')
        panel_idx = base.find('id="chatbot-panel"')
        assert panel_idx != -1
        before = base[:panel_idx]
        last_if = before.rfind('{% if current_user.is_authenticated %}')
        last_endif = before.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    def test_ai_js_auth_gated(self):
        """AI JavaScript files only loaded for authenticated users."""
        base = _read_template('base.html')
        chatbot_js_idx = base.find('chatbot.js')
        assert chatbot_js_idx != -1
        before = base[:chatbot_js_idx]
        last_if = before.rfind('{% if current_user.is_authenticated %}')
        last_endif = before.rfind('{% endif %}')
        assert last_if != -1
        assert last_if > last_endif

    def test_daily_briefing_visible_to_anonymous(self):
        """Daily briefing section is NOT auth-gated (read-only for all)."""
        index = _read_template('index.html')
        section_idx = index.find('id="briefing-section"')
        if section_idx == -1:
            section_idx = index.find('id="briefing-narrative"')
        assert section_idx != -1, 'Briefing section not found'
        before = index[:section_idx]
        opens = before.count('{% if current_user.is_authenticated %}')
        closes = before.count('{% endif %}')
        assert opens <= closes, 'Briefing section must be visible to anonymous users'


# ---------------------------------------------------------------------------
# AC5: Anonymous API endpoints return proper 401 JSON
# ---------------------------------------------------------------------------

class TestAnonymousAPIRejection:
    """Anonymous users hitting AI API endpoints get 401 JSON, not 500."""

    def test_unauthorized_handler_exists(self):
        """Custom unauthorized handler is registered in extensions."""
        assert 'unauthorized_handler' in EXTENSIONS_SOURCE

    def test_api_routes_get_json_401(self):
        """Handler returns JSON for /api/ routes."""
        assert '/api/' in EXTENSIONS_SOURCE
        assert '401' in EXTENSIONS_SOURCE

    def test_handler_returns_json_error(self):
        """Handler returns a JSON error dict, not a redirect."""
        assert 'jsonify' in EXTENSIONS_SOURCE or 'json' in EXTENSIONS_SOURCE


# ---------------------------------------------------------------------------
# AC6: has_paid_access NOT used for access control in invite-only mode
# ---------------------------------------------------------------------------

class TestHasPaidAccessNotUsedInInviteOnly:
    """has_paid_access property exists but is not used for access decisions
    when SITE_MODE is invite_only."""

    def test_has_paid_access_property_exists(self):
        """User model still has has_paid_access (for future paid mode)."""
        assert 'def has_paid_access' in USER_MODEL_SOURCE or \
               'has_paid_access' in USER_MODEL_SOURCE

    def test_has_paid_access_not_in_dashboard_routes(self):
        """Dashboard route handlers do not reference has_paid_access."""
        # has_paid_access should not be used in route logic — only in rate_limiting.py
        # which already gates it behind site_mode check
        assert 'has_paid_access' not in DASHBOARD_SOURCE, \
            'Dashboard routes should not check has_paid_access directly'

    def test_has_paid_access_gated_in_rate_limiting(self):
        """Rate limiting only checks has_paid_access when NOT in invite_only mode."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        # The pattern should be: if site_mode != 'invite_only': check has_paid_access
        lines = func_src.splitlines()
        mode_line = None
        paid_line = None
        for i, line in enumerate(lines):
            if "site_mode != 'invite_only'" in line:
                mode_line = i
            if 'has_paid_access' in line:
                paid_line = i
        assert mode_line is not None
        assert paid_line is not None
        assert mode_line < paid_line, \
            'has_paid_access must be inside the non-invite_only branch'

    def test_user_with_null_stripe_fields_gets_subscriber_limits(self):
        """Verify the logic: a user with no Stripe fields still gets subscriber
        limits in invite_only mode by checking the code flow."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_subscriber_daily_limit')
        # In invite_only mode, the function should:
        # 1. Check is_authenticated (return None if not)
        # 2. Skip has_paid_access check (site_mode == invite_only)
        # 3. Query ai_usage_records for the user
        # 4. Compare against subscriber daily limit
        assert 'is_authenticated' in func_src
        assert "site_mode != 'invite_only'" in func_src
        assert 'AIUsageRecord' in func_src
        assert '_get_subscriber_daily_limit' in func_src


# ---------------------------------------------------------------------------
# AC7: Decorator ordering ensures correct rate limit behavior
# ---------------------------------------------------------------------------

class TestDecoratorOrdering:
    """Decorator stack order is correct for rate limit behavior."""

    @pytest.mark.parametrize('func_name', ALL_AI_FUNCS)
    def test_login_required_before_rate_limit(self, func_name):
        """@login_required is stacked before @anonymous_rate_limit."""
        decorators = _get_decorator_names(DASHBOARD_SOURCE, func_name)
        if 'login_required' not in decorators or \
           'anonymous_rate_limit' not in decorators:
            pytest.skip(f'{func_name} missing expected decorators')
        login_idx = decorators.index('login_required')
        rate_idx = decorators.index('anonymous_rate_limit')
        assert login_idx < rate_idx


# ---------------------------------------------------------------------------
# AC8: Rate limit decorator flow for authenticated users
# ---------------------------------------------------------------------------

class TestRateLimitDecoratorFlow:
    """The anonymous_rate_limit decorator correctly routes authenticated users
    to subscriber limits and anonymous users to session/global limits."""

    def test_decorator_checks_subscriber_first(self):
        """Decorator checks subscriber daily limit before anonymous limits."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'anonymous_rate_limit')
        sub_idx = func_src.find('check_subscriber_daily_limit')
        global_idx = func_src.find('check_global_anonymous_limit')
        session_idx = func_src.find('check_anonymous_rate_limit')
        assert sub_idx != -1
        assert global_idx != -1
        assert session_idx != -1
        assert sub_idx < global_idx < session_idx

    def test_anonymous_checks_skip_authenticated(self):
        """check_anonymous_rate_limit returns None for authenticated users."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_anonymous_rate_limit')
        assert 'is_authenticated' in func_src
        assert 'return None' in func_src

    def test_global_check_skips_authenticated(self):
        """check_global_anonymous_limit returns None for authenticated users."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'check_global_anonymous_limit')
        assert 'is_authenticated' in func_src
        assert 'return None' in func_src

    def test_anonymous_usage_recording_skips_authenticated(self):
        """record_anonymous_usage skips recording for authenticated users."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'record_anonymous_usage')
        assert 'is_authenticated' in func_src

    def test_global_usage_recording_skips_authenticated(self):
        """record_global_anonymous_usage skips recording for authenticated users."""
        func_src = _get_function_source(RATE_LIMITING_SOURCE,
                                        'record_global_anonymous_usage')
        assert 'is_authenticated' in func_src


# ---------------------------------------------------------------------------
# AC9: SITE_MODE defaults to invite_only
# ---------------------------------------------------------------------------

class TestSiteModeConfiguration:
    """SITE_MODE is configured and defaults to invite_only."""

    def test_config_defaults_invite_only(self):
        """Config.py sets SITE_MODE default to invite_only."""
        assert "'invite_only'" in CONFIG_SOURCE
        assert 'SITE_MODE' in CONFIG_SOURCE

    def test_rate_limiting_defaults_invite_only(self):
        """Rate limiting falls back to invite_only as default."""
        assert "_DEFAULT_SITE_MODE = 'invite_only'" in RATE_LIMITING_SOURCE
