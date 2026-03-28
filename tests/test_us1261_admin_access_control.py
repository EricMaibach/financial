"""
US-12.6.1: Admin access control and analytics route

Tests for:
- @admin_required decorator exists and checks authentication then is_admin
- /admin/analytics route is registered
- Admin nav link visible only to admin users
- Existing admin routes refactored to use @admin_required
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

DECORATORS_FILE = SIGNALTRACKERS_DIR / 'decorators.py'
DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'
BASE_TEMPLATE = SIGNALTRACKERS_DIR / 'templates' / 'base.html'
ANALYTICS_TEMPLATE = SIGNALTRACKERS_DIR / 'templates' / 'admin' / 'analytics.html'

DECORATORS_SOURCE = DECORATORS_FILE.read_text()
DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()
BASE_TEMPLATE_SOURCE = BASE_TEMPLATE.read_text()
ANALYTICS_TEMPLATE_SOURCE = ANALYTICS_TEMPLATE.read_text()


# ---------------------------------------------------------------------------
# AC1: @admin_required decorator
# ---------------------------------------------------------------------------

class TestAdminRequiredDecorator:
    """Verify the admin_required decorator exists and has correct logic."""

    def test_decorator_file_exists(self):
        """decorators.py exists in signaltrackers/."""
        assert DECORATORS_FILE.exists()

    def test_decorator_function_defined(self):
        """admin_required function is defined."""
        assert 'def admin_required' in DECORATORS_SOURCE

    def test_checks_is_authenticated(self):
        """Decorator checks current_user.is_authenticated."""
        assert 'is_authenticated' in DECORATORS_SOURCE

    def test_checks_is_admin(self):
        """Decorator checks current_user.is_admin."""
        assert 'is_admin' in DECORATORS_SOURCE

    def test_redirects_anonymous_to_login(self):
        """Anonymous users are redirected to login."""
        assert "redirect" in DECORATORS_SOURCE
        assert "login" in DECORATORS_SOURCE

    def test_aborts_403_for_non_admin(self):
        """Non-admin authenticated users get 403."""
        assert '403' in DECORATORS_SOURCE

    def test_uses_wraps(self):
        """Decorator uses functools.wraps to preserve function metadata."""
        assert '@wraps' in DECORATORS_SOURCE

    def test_authentication_checked_before_admin(self):
        """is_authenticated is checked before is_admin to avoid AttributeError."""
        auth_pos = DECORATORS_SOURCE.find('is_authenticated')
        admin_pos = DECORATORS_SOURCE.find('is_admin')
        assert auth_pos < admin_pos, "Must check is_authenticated before is_admin"

    def test_decorator_is_importable(self):
        """admin_required can be imported from decorators module."""
        from decorators import admin_required
        assert callable(admin_required)


# ---------------------------------------------------------------------------
# AC2: Admin analytics route
# ---------------------------------------------------------------------------

class TestAdminAnalyticsRoute:
    """Verify /admin/analytics route is registered."""

    def test_route_defined_in_dashboard(self):
        """Dashboard registers /admin/analytics route."""
        assert "'/admin/analytics'" in DASHBOARD_SOURCE

    def test_route_uses_admin_required(self):
        """Route uses @admin_required decorator (not manual is_admin check)."""
        # Find the analytics route and check surrounding context (route + decorators + function def)
        route_pos = DASHBOARD_SOURCE.find("'/admin/analytics'")
        context = DASHBOARD_SOURCE[max(0, route_pos - 100):route_pos + 200]
        assert '@admin_required' in context

    def test_route_renders_template(self):
        """Route returns a rendered template."""
        # Find the admin_analytics function body
        func_start = DASHBOARD_SOURCE.find('def admin_analytics')
        func_end = DASHBOARD_SOURCE.find('\ndef ', func_start + 1)
        if func_end == -1:
            func_end = DASHBOARD_SOURCE.find('\n@app.route', func_start + 1)
        func_body = DASHBOARD_SOURCE[func_start:func_end]
        assert 'render_template' in func_body

    def test_analytics_template_exists(self):
        """Admin analytics template file exists."""
        assert ANALYTICS_TEMPLATE.exists()

    def test_analytics_template_extends_base(self):
        """Analytics template extends base.html."""
        assert '{% extends "base.html" %}' in ANALYTICS_TEMPLATE_SOURCE


# ---------------------------------------------------------------------------
# AC3: Admin nav link
# ---------------------------------------------------------------------------

class TestAdminNavLink:
    """Verify admin nav link visibility logic in base template."""

    def test_admin_analytics_link_in_template(self):
        """Base template contains link to admin_analytics."""
        assert "admin_analytics" in BASE_TEMPLATE_SOURCE

    def test_link_behind_is_admin_check(self):
        """Admin link is conditionally shown based on is_admin."""
        assert 'current_user.is_admin' in BASE_TEMPLATE_SOURCE

    def test_link_inside_authenticated_block(self):
        """Admin link only appears within the authenticated user section."""
        # The admin link should be inside the is_authenticated block
        auth_block_start = BASE_TEMPLATE_SOURCE.find('current_user.is_authenticated')
        admin_link_pos = BASE_TEMPLATE_SOURCE.find('admin_analytics')
        assert auth_block_start < admin_link_pos, \
            "Admin link must be inside the authenticated user block"

    def test_link_url_correct(self):
        """Nav link uses url_for('admin_analytics')."""
        assert "url_for('admin_analytics')" in BASE_TEMPLATE_SOURCE


# ---------------------------------------------------------------------------
# AC4: Existing admin routes use @admin_required
# ---------------------------------------------------------------------------

class TestExistingAdminRoutesRefactored:
    """Verify existing admin routes use @admin_required instead of manual checks."""

    def test_trigger_alert_check_uses_decorator(self):
        """trigger_alert_check uses @admin_required."""
        route_pos = DASHBOARD_SOURCE.find("'/admin/trigger-alert-check'")
        context = DASHBOARD_SOURCE[max(0, route_pos - 500):route_pos]
        assert '@admin_required' in context

    def test_trigger_daily_briefing_uses_decorator(self):
        """trigger_daily_briefing uses @admin_required."""
        route_pos = DASHBOARD_SOURCE.find("'/admin/trigger-daily-briefing'")
        context = DASHBOARD_SOURCE[max(0, route_pos - 500):route_pos]
        assert '@admin_required' in context

    def test_no_manual_is_admin_check_in_admin_routes(self):
        """Admin routes no longer use manual 'if not current_user.is_admin' checks."""
        # Find the admin endpoints section
        admin_section_start = DASHBOARD_SOURCE.find('# Admin endpoints')
        admin_section = DASHBOARD_SOURCE[admin_section_start:]
        # There should be no manual is_admin checks within route functions
        assert 'if not current_user.is_admin' not in admin_section
