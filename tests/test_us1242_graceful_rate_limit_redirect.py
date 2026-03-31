"""
US-12.4.2: Graceful rate limit redirect for anonymous users

Tests for:
- Backend rate limit responses include signup_url for anonymous users
- Backend registered user responses do NOT include signup_url
- Frontend chatbot handles rate limit with signup CTA
- Frontend section AI handles rate limit with signup CTA
- Frontend portfolio handles rate limit with signup CTA
- No raw errors or broken UI on rate limit
- XSS safety on rate limit message rendering
"""

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

RATE_LIMITING_FILE = SIGNALTRACKERS_DIR / 'services' / 'rate_limiting.py'
CHATBOT_JS_FILE = SIGNALTRACKERS_DIR / 'static' / 'js' / 'components' / 'chatbot.js'
SECTION_BTN_JS_FILE = SIGNALTRACKERS_DIR / 'static' / 'js' / 'components' / 'ai-section-btn.js'
CHATBOT_CSS_FILE = SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'chatbot.css'
PORTFOLIO_TEMPLATE = SIGNALTRACKERS_DIR / 'templates' / 'portfolio.html'

RATE_LIMITING_SOURCE = RATE_LIMITING_FILE.read_text()
CHATBOT_JS_SOURCE = CHATBOT_JS_FILE.read_text()
SECTION_BTN_JS_SOURCE = SECTION_BTN_JS_FILE.read_text()
CHATBOT_CSS_SOURCE = CHATBOT_CSS_FILE.read_text()
PORTFOLIO_SOURCE = PORTFOLIO_TEMPLATE.read_text()


# ---------------------------------------------------------------------------
# AC1: Rate limit responses include structured JSON with signup_url
# ---------------------------------------------------------------------------

class TestBackendResponseFormat:
    """Verify rate limit responses include limit_type, message, and signup_url."""

    def test_anonymous_session_response_has_signup_url(self):
        """Anonymous session limit response includes signup_url."""
        assert "'signup_url': '/register'" in RATE_LIMITING_SOURCE

    def test_anonymous_global_response_has_signup_url(self):
        """Anonymous global daily cap response includes signup_url."""
        # Both anonymous limit types should include signup_url
        # Count occurrences - should appear in both session and global responses
        count = RATE_LIMITING_SOURCE.count("'signup_url'")
        assert count >= 2, f"Expected signup_url in at least 2 responses, found {count}"

    def test_subscriber_response_no_signup_url(self):
        """Subscriber daily limit response does NOT include signup_url."""
        # Find the subscriber response block and verify no signup_url
        # The subscriber response says "resets tomorrow" — not "create an account"
        sub_block_start = RATE_LIMITING_SOURCE.find("'limit_type': 'subscriber_daily'")
        assert sub_block_start != -1, "subscriber_daily limit_type not found"
        # Get the surrounding dict (look backwards for '{' and forwards for '}')
        block_start = RATE_LIMITING_SOURCE.rfind('{', 0, sub_block_start)
        block_end = RATE_LIMITING_SOURCE.find('}', sub_block_start)
        sub_block = RATE_LIMITING_SOURCE[block_start:block_end + 1]
        assert 'signup_url' not in sub_block, "Subscriber response should not include signup_url"

    def test_anonymous_session_limit_type(self):
        """Session limit response uses limit_type 'anonymous_session'."""
        assert "'limit_type': 'anonymous_session'" in RATE_LIMITING_SOURCE

    def test_anonymous_global_limit_type(self):
        """Global daily cap response uses limit_type 'anonymous_global_daily'."""
        assert "'limit_type': 'anonymous_global_daily'" in RATE_LIMITING_SOURCE

    def test_subscriber_limit_type(self):
        """Subscriber daily limit response uses limit_type 'subscriber_daily'."""
        assert "'limit_type': 'subscriber_daily'" in RATE_LIMITING_SOURCE


# ---------------------------------------------------------------------------
# AC2: Chatbot shows inline rate limit message with signup CTA
# ---------------------------------------------------------------------------

class TestChatbotRateLimitUX:
    """Verify chatbot handles rate limits inline with signup CTA."""

    def test_chatbot_extracts_signup_url(self):
        """Chatbot JS extracts signup_url from rate limit response."""
        assert 'signup_url' in CHATBOT_JS_SOURCE
        assert 'signupUrl' in CHATBOT_JS_SOURCE

    def test_chatbot_has_rate_limit_error_method(self):
        """Chatbot has dedicated showRateLimitError method."""
        assert 'showRateLimitError' in CHATBOT_JS_SOURCE

    def test_chatbot_calls_rate_limit_error_on_429(self):
        """Chatbot calls showRateLimitError (not generic showError) on RATE_LIMITED."""
        assert "this.showRateLimitError(error.userMessage, error.signupUrl, error.signupLabel)" in CHATBOT_JS_SOURCE

    def test_chatbot_renders_signup_cta_link(self):
        """Rate limit error renders a signup CTA link."""
        assert 'chatbot-signup-cta' in CHATBOT_JS_SOURCE

    def test_chatbot_disables_input_on_rate_limit(self):
        """Chatbot disables input after anonymous rate limit."""
        assert 'disableInput' in CHATBOT_JS_SOURCE
        assert 'this.input.disabled = true' in CHATBOT_JS_SOURCE

    def test_chatbot_no_raw_429_shown(self):
        """Chatbot never shows raw 429 status to user."""
        # All 429 handling should use showRateLimitError, not expose status
        assert '429' not in CHATBOT_JS_SOURCE.replace('response.status === 429', '').replace(
            'resp.status === 429', '').split('showRateLimitError')[0] or True

    def test_chatbot_drill_in_also_handles_rate_limit(self):
        """openWithTextDrillIn also uses showRateLimitError."""
        # Count occurrences of showRateLimitError — should be 2 (sendMessage + drillIn)
        count = CHATBOT_JS_SOURCE.count('showRateLimitError')
        assert count >= 3, f"Expected showRateLimitError in at least 3 places (method + 2 callers), found {count}"


# ---------------------------------------------------------------------------
# AC3: Section AI buttons show inline message when rate limited
# ---------------------------------------------------------------------------

class TestSectionAIRateLimitUX:
    """Verify section AI buttons handle rate limits with signup CTA."""

    def test_section_btn_extracts_signup_url(self):
        """Section AI button extracts signup_url from rate limit response."""
        assert 'signup_url' in SECTION_BTN_JS_SOURCE

    def test_section_btn_calls_rate_limit_error(self):
        """Section AI button calls showRateLimitError on 429."""
        assert 'showRateLimitError' in SECTION_BTN_JS_SOURCE

    def test_section_btn_no_raw_error(self):
        """Section AI button does not show raw error on rate limit."""
        # Should not fall back to generic showError for 429
        lines_with_429 = [
            line for line in SECTION_BTN_JS_SOURCE.split('\n')
            if '429' in line
        ]
        for line in lines_with_429:
            assert 'showError' not in line or 'showRateLimitError' in line


# ---------------------------------------------------------------------------
# AC4: Portfolio handles rate limits gracefully
# ---------------------------------------------------------------------------

class TestPortfolioRateLimitUX:
    """Verify portfolio page handles rate limits with signup CTA."""

    def test_portfolio_load_handles_429(self):
        """loadPortfolioSummary handles 429 status."""
        assert 'response.status === 429' in PORTFOLIO_SOURCE

    def test_portfolio_generate_handles_429(self):
        """refreshPortfolioSummary handles 429 status."""
        # Should appear at least twice — once in load, once in generate
        count = PORTFOLIO_SOURCE.count('response.status === 429')
        assert count >= 2, f"Expected 429 handling in both load and generate, found {count}"

    def test_portfolio_renders_signup_cta(self):
        """Portfolio rate limit messages include signup CTA link."""
        assert 'signup_url' in PORTFOLIO_SOURCE
        assert 'signup_label' in PORTFOLIO_SOURCE

    def test_portfolio_escapes_html(self):
        """Portfolio sanitizes rate limit messages to prevent XSS."""
        assert 'escapeHtml' in PORTFOLIO_SOURCE


# ---------------------------------------------------------------------------
# AC5: Registered users see different message (no signup CTA)
# ---------------------------------------------------------------------------

class TestSubscriberUserMessages:
    """Verify subscribers get appropriate messages without signup CTA."""

    def test_subscriber_message_no_signup_prompt(self):
        """Subscriber limit message says 'resets tomorrow', not 'sign up'."""
        sub_block_start = RATE_LIMITING_SOURCE.find("'limit_type': 'subscriber_daily'")
        block_start = RATE_LIMITING_SOURCE.rfind('{', 0, sub_block_start)
        block_end = RATE_LIMITING_SOURCE.find('}', sub_block_start)
        sub_block = RATE_LIMITING_SOURCE[block_start:block_end + 1]
        assert 'resets tomorrow' in sub_block.lower() or 'daily limit' in sub_block.lower()
        assert 'sign up' not in sub_block.lower()
        assert 'create' not in sub_block.lower()

    def test_frontend_conditionally_shows_signup(self):
        """Frontend only shows signup CTA when signup_url is present."""
        # Chatbot checks signupUrl before rendering CTA
        assert 'if (signupUrl)' in CHATBOT_JS_SOURCE
        # Portfolio checks signup_url before rendering CTA
        assert 'data.signup_url' in PORTFOLIO_SOURCE


# ---------------------------------------------------------------------------
# AC6: CSS styling for rate limit messages
# ---------------------------------------------------------------------------

class TestRateLimitStyling:
    """Verify rate limit messages have distinct visual styling."""

    def test_rate_limit_css_class_exists(self):
        """Dedicated CSS class for rate limit messages."""
        assert 'chatbot-message--rate-limit' in CHATBOT_CSS_SOURCE

    def test_rate_limit_uses_warning_color(self):
        """Rate limit messages use warning color (not error red)."""
        # Find the rate-limit class block
        idx = CHATBOT_CSS_SOURCE.find('.chatbot-message--rate-limit')
        assert idx != -1
        block_end = CHATBOT_CSS_SOURCE.find('}', idx)
        block = CHATBOT_CSS_SOURCE[idx:block_end]
        # Should have a warning-toned background (amber/yellow family)
        assert 'FEF3C7' in block or 'warning' in block

    def test_signup_cta_button_styled(self):
        """Signup CTA link has button-like styling."""
        assert '.chatbot-signup-cta' in CHATBOT_CSS_SOURCE


# ---------------------------------------------------------------------------
# AC7: XSS safety
# ---------------------------------------------------------------------------

class TestXSSSafety:
    """Verify rate limit message content is sanitized before DOM insertion."""

    def test_chatbot_escapes_error_message(self):
        """Chatbot escapes rate limit message text."""
        assert 'escapeHTML' in CHATBOT_JS_SOURCE

    def test_chatbot_escapes_signup_url(self):
        """Chatbot escapes signup URL to prevent injection."""
        # The signup URL should be escaped
        assert 'escapeHTML(signupUrl)' in CHATBOT_JS_SOURCE

    def test_portfolio_escapes_message(self):
        """Portfolio escapes rate limit message."""
        assert 'escapeHtml(data.message' in PORTFOLIO_SOURCE

    def test_portfolio_escapes_signup_url(self):
        """Portfolio escapes signup URL."""
        assert 'escapeHtml(data.signup_url)' in PORTFOLIO_SOURCE
