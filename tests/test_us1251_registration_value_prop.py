"""Tests for US-12.5.1: Registration page value proposition and feature benefits."""

import pytest
import re
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'signaltrackers'))


# ---------------------------------------------------------------------------
# Fixture: read the register template once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def register_html():
    template_path = os.path.join(
        os.path.dirname(__file__), '..', 'signaltrackers', 'templates', 'auth', 'register.html'
    )
    with open(template_path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Headline
# ---------------------------------------------------------------------------

class TestHeadline:
    """Registration page displays a compelling headline above the form."""

    def test_headline_text_present(self, register_html):
        assert "Unlock the Full Power of MacroClarity" in register_html

    def test_headline_is_h2(self, register_html):
        assert re.search(r'<h2[^>]*>.*Unlock the Full Power', register_html, re.DOTALL)

    def test_headline_has_icon(self, register_html):
        assert re.search(r'bi-graph-up-arrow.*Unlock', register_html, re.DOTALL)

    def test_headline_appears_before_form(self, register_html):
        headline_pos = register_html.index("Unlock the Full Power")
        form_pos = register_html.index('<form method="POST"')
        assert headline_pos < form_pos


# ---------------------------------------------------------------------------
# Value Proposition Paragraph
# ---------------------------------------------------------------------------

class TestValueProposition:
    """Brief value proposition paragraph explains what registered users get."""

    def test_value_prop_paragraph_present(self, register_html):
        assert "subscribe" in register_html.lower()

    def test_value_prop_mentions_market_intelligence(self, register_html):
        assert "market intelligence" in register_html.lower()

    def test_value_prop_mentions_investment_decisions(self, register_html):
        assert "investment decisions" in register_html.lower()

    def test_value_prop_appears_before_form(self, register_html):
        prop_pos = register_html.lower().index("subscribe")
        form_pos = register_html.index('<form method="POST"')
        assert prop_pos < form_pos


# ---------------------------------------------------------------------------
# Feature Benefits Badges
# ---------------------------------------------------------------------------

class TestFeatureBenefits:
    """Concise feature benefits list with the three required items."""

    def test_ai_powered_analysis_badge(self, register_html):
        assert "AI-powered analysis" in register_html

    def test_portfolio_tracking_badge(self, register_html):
        assert "Portfolio tracking" in register_html

    def test_saved_preferences_badge(self, register_html):
        assert "Saved preferences" in register_html

    def test_three_badges_present(self, register_html):
        count = register_html.count("badge bg-primary bg-opacity-10")
        assert count == 3

    def test_badges_use_bootstrap_icons(self, register_html):
        assert "bi-chat-dots" in register_html
        assert "bi-briefcase" in register_html
        assert "bi-sliders" in register_html

    def test_badges_appear_before_form(self, register_html):
        badge_pos = register_html.index("AI-powered analysis")
        form_pos = register_html.index('<form method="POST"')
        assert badge_pos < form_pos


# ---------------------------------------------------------------------------
# Form Fields Unchanged
# ---------------------------------------------------------------------------

class TestFormFieldsUnchanged:
    """Existing registration form fields and validation are completely unchanged."""

    def test_username_field_present(self, register_html):
        assert 'id="username"' in register_html

    def test_username_minlength(self, register_html):
        assert 'minlength="3"' in register_html

    def test_username_maxlength(self, register_html):
        assert 'maxlength="80"' in register_html

    def test_email_field_present(self, register_html):
        assert 'id="email"' in register_html
        assert 'type="email"' in register_html

    def test_password_field_present(self, register_html):
        assert 'id="password"' in register_html

    def test_password_minlength(self, register_html):
        assert re.search(r'id="password"[^>]*minlength="8"', register_html)

    def test_confirm_password_field(self, register_html):
        assert 'id="confirm_password"' in register_html

    def test_csrf_token_present(self, register_html):
        assert 'name="csrf_token"' in register_html

    def test_submit_button_present(self, register_html):
        assert 'type="submit"' in register_html
        assert "Create Account" in register_html

    def test_login_link_present(self, register_html):
        assert "Already have an account?" in register_html
        assert "Login here" in register_html

    def test_flash_messages_support(self, register_html):
        assert "get_flashed_messages" in register_html
        assert "alert-dismissible" in register_html


# ---------------------------------------------------------------------------
# Design System Consistency
# ---------------------------------------------------------------------------

class TestDesignSystemConsistency:
    """Page uses existing design system classes — no custom one-off styles."""

    def test_uses_bootstrap_grid(self, register_html):
        assert "col-md-8" in register_html
        assert "col-lg-6" in register_html

    def test_card_shadow_class(self, register_html):
        assert "card shadow" in register_html

    def test_dark_card_header(self, register_html):
        assert "card-header bg-dark text-white" in register_html

    def test_no_inline_styles_in_value_prop(self, register_html):
        # Extract the value prop section (between text-center and card shadow)
        start = register_html.index("text-center mb-4")
        end = register_html.index("card shadow")
        value_prop_section = register_html[start:end]
        assert 'style="' not in value_prop_section

    def test_responsive_badge_layout(self, register_html):
        assert "flex-column flex-sm-row" in register_html


# ---------------------------------------------------------------------------
# Responsive Layout
# ---------------------------------------------------------------------------

class TestResponsiveLayout:
    """Page works correctly on desktop, tablet, and mobile viewports."""

    def test_badges_stack_vertically_on_mobile(self, register_html):
        # flex-column = vertical on mobile, flex-sm-row = horizontal on sm+
        assert "d-flex flex-column flex-sm-row" in register_html

    def test_column_responsive_breakpoints(self, register_html):
        assert "col-md-8" in register_html
        assert "col-lg-6" in register_html


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

class TestSecurity:
    """No XSS vectors or template injection in new content."""

    def test_no_safe_filter_on_static_content(self, register_html):
        # Value prop section should not use |safe since it's static text
        start = register_html.index("text-center mb-4")
        end = register_html.index("card shadow")
        value_prop_section = register_html[start:end]
        assert "|safe" not in value_prop_section

    def test_csrf_token_in_form(self, register_html):
        assert 'name="csrf_token"' in register_html

    def test_form_posts_to_register(self, register_html):
        assert "url_for('register')" in register_html


# ---------------------------------------------------------------------------
# Rate Limit Redirect Flow
# ---------------------------------------------------------------------------

class TestRateLimitRedirectFlow:
    """Anonymous users redirected from AI rate limits land on this page."""

    def test_signup_url_points_to_register(self):
        """Rate limiting service sends anonymous users to /register."""
        rate_limiting_path = os.path.join(
            os.path.dirname(__file__), '..', 'signaltrackers', 'services', 'rate_limiting.py'
        )
        with open(rate_limiting_path, 'r') as f:
            content = f.read()
        assert "signup_url" in content
        assert "/register" in content
