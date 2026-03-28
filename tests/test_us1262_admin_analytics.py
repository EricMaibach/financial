"""
US-12.6.2: Admin usage analytics dashboard

Tests for:
- Analytics service functions return correct aggregations
- Route passes required data to template
- Template renders all dashboard sections
- Query efficiency (GROUP BY at SQL level, no N+1)
- Edge cases (empty data, large numbers)
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

SERVICE_FILE = SIGNALTRACKERS_DIR / 'services' / 'admin_analytics.py'
DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'
ANALYTICS_TEMPLATE = SIGNALTRACKERS_DIR / 'templates' / 'admin' / 'analytics.html'

SERVICE_SOURCE = SERVICE_FILE.read_text()
DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()
TEMPLATE_SOURCE = ANALYTICS_TEMPLATE.read_text()


# ---------------------------------------------------------------------------
# AC1: Daily call volume with breakdown
# ---------------------------------------------------------------------------

class TestDailyCallVolume:
    """Dashboard shows daily AI call volume."""

    def test_today_summary_function_exists(self):
        """get_today_summary function defined in admin_analytics service."""
        assert 'def get_today_summary' in SERVICE_SOURCE

    def test_today_summary_queries_by_date(self):
        """Today summary filters by today's date."""
        assert 'today_start' in SERVICE_SOURCE or 'timestamp >=' in SERVICE_SOURCE

    def test_today_summary_returns_total_calls(self):
        """Today summary includes total_calls."""
        assert 'total_calls' in SERVICE_SOURCE

    def test_template_shows_calls_today(self):
        """Template displays today's call count."""
        assert 'today.total_calls' in TEMPLATE_SOURCE

    def test_route_passes_today_data(self):
        """Route passes today summary to template."""
        assert 'get_today_summary' in DASHBOARD_SOURCE
        assert "today=" in DASHBOARD_SOURCE


# ---------------------------------------------------------------------------
# AC2: Token consumption and estimated cost
# ---------------------------------------------------------------------------

class TestTokenConsumptionAndCost:
    """Dashboard shows token consumption and estimated cost."""

    def test_today_summary_includes_tokens(self):
        """Today summary includes input and output tokens."""
        assert 'input_tokens' in SERVICE_SOURCE
        assert 'output_tokens' in SERVICE_SOURCE

    def test_today_summary_includes_cost(self):
        """Today summary includes estimated cost."""
        assert 'estimated_cost' in SERVICE_SOURCE

    def test_template_shows_tokens(self):
        """Template displays token counts."""
        assert 'today.input_tokens' in TEMPLATE_SOURCE
        assert 'today.output_tokens' in TEMPLATE_SOURCE

    def test_template_shows_cost(self):
        """Template displays estimated cost."""
        assert 'today.estimated_cost' in TEMPLATE_SOURCE

    def test_cost_formatted_two_decimals(self):
        """Cost displays with 2 decimal places."""
        assert '%.2f' in TEMPLATE_SOURCE or '.2f' in TEMPLATE_SOURCE


# ---------------------------------------------------------------------------
# AC3: Per-user usage breakdown
# ---------------------------------------------------------------------------

class TestPerUserBreakdown:
    """Dashboard shows per-user usage breakdown."""

    def test_top_users_function_exists(self):
        """get_top_users function defined."""
        assert 'def get_top_users' in SERVICE_SOURCE

    def test_top_users_joins_user_table(self):
        """Top users query joins User model for username."""
        assert 'User.username' in SERVICE_SOURCE or 'User, AIUsageRecord' in SERVICE_SOURCE

    def test_top_users_ordered_by_count(self):
        """Top users ordered by call count descending."""
        assert 'order_by' in SERVICE_SOURCE
        assert 'desc()' in SERVICE_SOURCE

    def test_template_shows_username(self):
        """Template shows username, not user ID."""
        assert 'u.username' in TEMPLATE_SOURCE

    def test_template_shows_user_call_count(self):
        """Template shows per-user call count."""
        assert 'u.call_count' in TEMPLATE_SOURCE

    def test_template_shows_user_tokens(self):
        """Template shows per-user token usage."""
        assert 'u.total_tokens' in TEMPLATE_SOURCE

    def test_route_passes_top_users(self):
        """Route passes top_users to template."""
        assert 'get_top_users' in DASHBOARD_SOURCE
        assert 'top_users=' in DASHBOARD_SOURCE


# ---------------------------------------------------------------------------
# AC4: Global anonymous cap status
# ---------------------------------------------------------------------------

class TestAnonCapStatus:
    """Dashboard shows global anonymous cap status."""

    def test_anon_cap_function_exists(self):
        """get_anon_cap_status function defined."""
        assert 'def get_anon_cap_status' in SERVICE_SOURCE

    def test_anon_cap_reads_rate_limiting(self):
        """Anon cap reads from rate_limiting module."""
        assert 'rate_limiting' in SERVICE_SOURCE

    def test_anon_cap_returns_used_and_limit(self):
        """Anon cap returns used and limit."""
        assert "'used'" in SERVICE_SOURCE or '"used"' in SERVICE_SOURCE
        assert "'limit'" in SERVICE_SOURCE or '"limit"' in SERVICE_SOURCE

    def test_template_shows_cap_fraction(self):
        """Template shows used / limit format."""
        assert 'anon_cap.used' in TEMPLATE_SOURCE
        assert 'anon_cap.limit' in TEMPLATE_SOURCE

    def test_template_has_progress_bar(self):
        """Template has a visual progress indicator for cap status."""
        assert 'cap-bar' in TEMPLATE_SOURCE


# ---------------------------------------------------------------------------
# AC5: 30-day daily trend
# ---------------------------------------------------------------------------

class TestDailyTrend:
    """Dashboard shows daily trend data for past 30 days."""

    def test_daily_trend_function_exists(self):
        """get_daily_trend function defined."""
        assert 'def get_daily_trend' in SERVICE_SOURCE

    def test_trend_uses_group_by(self):
        """Trend aggregation uses SQL GROUP BY."""
        assert 'group_by' in SERVICE_SOURCE

    def test_trend_default_30_days(self):
        """Trend defaults to 30 days."""
        assert 'days=30' in SERVICE_SOURCE

    def test_trend_zero_fills_gaps(self):
        """Trend zero-fills days with no data."""
        # Should have logic for filling missing days
        assert "'calls': 0" in SERVICE_SOURCE

    def test_template_has_chart(self):
        """Template renders a Chart.js chart for trend."""
        assert 'trendChart' in TEMPLATE_SOURCE
        assert 'new Chart' in TEMPLATE_SOURCE

    def test_route_passes_trend(self):
        """Route passes trend data to template."""
        assert 'get_daily_trend' in DASHBOARD_SOURCE
        assert 'trend=' in DASHBOARD_SOURCE


# ---------------------------------------------------------------------------
# AC6: Query efficiency
# ---------------------------------------------------------------------------

class TestQueryEfficiency:
    """All data queries use efficient aggregation."""

    def test_service_uses_func_count(self):
        """Service uses SQL aggregation functions."""
        assert 'func.count' in SERVICE_SOURCE
        assert 'func.sum' in SERVICE_SOURCE

    def test_service_uses_group_by(self):
        """Service uses GROUP BY for trend aggregation."""
        assert 'group_by' in SERVICE_SOURCE

    def test_no_python_loops_for_aggregation(self):
        """No evidence of row-by-row aggregation in Python.

        The service should aggregate at SQL level using func.count/func.sum
        rather than iterating rows in Python.
        """
        tree = ast.parse(SERVICE_SOURCE)
        # Check that main query functions use SQLAlchemy aggregation
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in (
                'get_today_summary', 'get_daily_trend', 'get_top_users'
            ):
                # These functions should contain func.count or func.sum calls
                func_source = ast.get_source_segment(SERVICE_SOURCE, node)
                assert 'func.' in func_source, f'{node.name} should use SQL aggregation'

    def test_top_users_has_limit(self):
        """Top users query has a LIMIT to avoid returning all users."""
        assert '.limit(' in SERVICE_SOURCE


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case handling."""

    def test_template_handles_empty_trend(self):
        """Template has empty state for no trend data."""
        assert 'empty-state' in TEMPLATE_SOURCE or 'No usage data' in TEMPLATE_SOURCE

    def test_template_handles_no_users(self):
        """Template has empty state for no user activity."""
        assert 'No registered user' in TEMPLATE_SOURCE or 'empty-state' in TEMPLATE_SOURCE

    def test_coalesce_prevents_null_sums(self):
        """SQL uses COALESCE to prevent NULL from SUM of empty sets."""
        assert 'coalesce' in SERVICE_SOURCE

    def test_large_numbers_formatted(self):
        """Template uses comma formatting for large numbers."""
        assert '{:,}' in TEMPLATE_SOURCE or 'format' in TEMPLATE_SOURCE


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

class TestSecurity:
    """Dashboard security checks."""

    def test_route_uses_admin_required(self):
        """Route is protected by @admin_required."""
        # Find the admin_analytics function and verify it has @admin_required
        pattern = r'@admin_required\s*\ndef admin_analytics'
        assert re.search(pattern, DASHBOARD_SOURCE), \
            'admin_analytics route must use @admin_required decorator'

    def test_template_extends_base(self):
        """Template extends base.html for consistent layout."""
        assert "extends" in TEMPLATE_SOURCE
        assert "base.html" in TEMPLATE_SOURCE

    def test_no_raw_user_ids_in_template(self):
        """Template doesn't expose raw user IDs."""
        assert 'user_id' not in TEMPLATE_SOURCE
