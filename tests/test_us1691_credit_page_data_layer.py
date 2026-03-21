"""
Static verification tests for US-169.1: Credit Page — Data Layer, Charts, and Percentile Engine.

Tests verify:
- calculate_percentile_rank() function exists and works correctly
- /credit route defined in dashboard.py passes percentile context
- credit.html template has chart markup, JS, percentile elements
- No user-controlled input piped into chart labels (no | safe on dynamic values)
- Stale stub content (coming in a future release) is absent
- Existing /credit route and /divergence redirect still present
- HY, IG, CCC chart canvases present in template
- HY-IG differential sparkline canvas present

No Flask server, external APIs, or database required.
"""

import os
import re
import sys
import unittest
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)

TEMPLATES_DIR = os.path.join(SIGNALTRACKERS_DIR, 'templates')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def get_dashboard_src():
    return read_file(os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py'))


def get_credit_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'credit.html'))


# ---------------------------------------------------------------------------
# calculate_percentile_rank — unit tests
# ---------------------------------------------------------------------------

def _extract_function(src, func_name):
    """Extract a top-level function definition from Python source text."""
    lines = src.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f'def {func_name}('):
            start = i
            break
    if start is None:
        return ''
    result = []
    for line in lines[start:]:
        if result and (line.startswith('def ') or line.startswith('@')):
            break
        result.append(line)
    return '\n'.join(result)


class TestCalculatePercentileRank(unittest.TestCase):
    """calculate_percentile_rank must be importable and behave correctly."""

    def setUp(self):
        self.src = get_dashboard_src()
        # Build an exec context with the function
        import pandas as _pd
        self._exec_globals = {'pd': _pd}
        # Extract both functions we need
        func_src = _extract_function(self.src, 'calculate_percentile_rank')
        exec(func_src, self._exec_globals)

    def _exec_percentile(self, series, current_value):
        return self._exec_globals['calculate_percentile_rank'](series, current_value)

    def test_function_defined_in_dashboard(self):
        self.assertIn('def calculate_percentile_rank(', self.src)

    def test_returns_float_0_to_100(self):
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        series.index = pd.date_range('2020-01-01', periods=5, freq='D')
        result = self._exec_percentile(series, 3.0)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 100.0)

    def test_current_value_below_all_returns_zero(self):
        series = pd.Series([5.0, 6.0, 7.0, 8.0])
        series.index = pd.date_range('2020-01-01', periods=4, freq='D')
        result = self._exec_percentile(series, 1.0)
        self.assertEqual(result, 0.0)

    def test_current_value_above_all_returns_100(self):
        series = pd.Series([1.0, 2.0, 3.0, 4.0])
        series.index = pd.date_range('2020-01-01', periods=4, freq='D')
        result = self._exec_percentile(series, 99.0)
        self.assertEqual(result, 100.0)

    def test_median_value_near_50th(self):
        # 10 values; current = 5 → 4 values below → 40th percentile
        series = pd.Series([float(i) for i in range(1, 11)])
        series.index = pd.date_range('2020-01-01', periods=10, freq='D')
        result = self._exec_percentile(series, 5.0)
        self.assertAlmostEqual(result, 40.0, places=0)

    def test_single_row_no_division_by_zero(self):
        series = pd.Series([3.0])
        series.index = pd.date_range('2020-01-01', periods=1, freq='D')
        # Should not raise, should return 0.0 or 100.0
        result = self._exec_percentile(series, 3.0)
        self.assertIn(result, [0.0, 100.0])

    def test_none_series_returns_none(self):
        result = self._exec_percentile(None, 3.0)
        self.assertIsNone(result)

    def test_empty_series_returns_none(self):
        series = pd.Series([], dtype=float)
        result = self._exec_percentile(series, 3.0)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# dashboard.py — /credit route passes percentile context
# ---------------------------------------------------------------------------

class TestCreditRouteDashboard(unittest.TestCase):
    """dashboard.py /credit route must pass percentile data to template."""

    def setUp(self):
        self.src = get_dashboard_src()

    def test_credit_route_decorator_present(self):
        self.assertIn("@app.route('/credit')", self.src)

    def test_credit_function_defined(self):
        self.assertIn("def credit():", self.src)

    def test_route_passes_hy_percentile(self):
        self.assertIn("hy_percentile", self.src)

    def test_route_passes_ig_percentile(self):
        self.assertIn("ig_percentile", self.src)

    def test_route_passes_hy_current_bps(self):
        self.assertIn("hy_current_bps", self.src)

    def test_route_passes_ig_current_bps(self):
        self.assertIn("ig_current_bps", self.src)

    def test_route_passes_ccc_current_bps(self):
        self.assertIn("ccc_current_bps", self.src)

    def test_route_loads_hy_csv(self):
        self.assertIn("high_yield_spread.csv", self.src)

    def test_route_loads_ig_csv(self):
        self.assertIn("investment_grade_spread.csv", self.src)

    def test_route_loads_ccc_csv(self):
        self.assertIn("ccc_spread.csv", self.src)

    def test_route_calls_calculate_percentile_rank(self):
        self.assertIn("calculate_percentile_rank(", self.src)

    def test_divergence_redirect_still_present(self):
        self.assertIn("@app.route('/divergence')", self.src)
        self.assertIn("redirect(url_for('credit')", self.src)

    def test_graceful_except_present(self):
        # Route must have try/except for graceful empty state
        credit_section = self.src[self.src.find("def credit():"):]
        credit_section = credit_section[:credit_section.find("\ndef ")]
        self.assertIn("except", credit_section)


# ---------------------------------------------------------------------------
# credit.html — template structure and content
# ---------------------------------------------------------------------------

class TestCreditTemplateDataDriven(unittest.TestCase):
    """credit.html must be a full data-driven template, not a stub."""

    def setUp(self):
        self.html = get_credit_html()

    def test_extends_base(self):
        self.assertIn('{% extends "base.html" %}', self.html)

    def test_title_block_present(self):
        self.assertIn("{% block title %}", self.html)

    def test_content_block_present(self):
        self.assertIn("{% block content %}", self.html)

    def test_extra_js_block_present(self):
        self.assertIn("{% block extra_js %}", self.html)

    def test_stub_text_absent(self):
        self.assertNotIn("coming in a future release", self.html.lower())

    def test_hy_spread_chart_canvas(self):
        self.assertIn('id="hy-spread-chart"', self.html)

    def test_ig_spread_chart_canvas(self):
        self.assertIn('id="ig-spread-chart"', self.html)

    def test_ccc_spread_chart_canvas(self):
        self.assertIn('id="ccc-spread-chart"', self.html)

    def test_hy_ig_diff_sparkline_canvas(self):
        self.assertIn('id="hy-ig-diff-chart"', self.html)

    def test_percentile_bar_element(self):
        self.assertIn("percentile-item__bar-fill", self.html)

    def test_category_credit_color_token(self):
        self.assertIn("--category-credit", self.html)

    def test_uses_category_credit_in_charts(self):
        # Chart border color must use the credit danger color
        self.assertIn("220,53,69", self.html)

    def test_page_category_is_credit(self):
        self.assertIn("page_category = 'Credit'", self.html)

    def test_regime_annotation_macro_used(self):
        self.assertIn("regime_annotation", self.html)

    def test_hy_percentile_jinja_var(self):
        self.assertIn("hy_percentile", self.html)

    def test_ig_percentile_jinja_var(self):
        self.assertIn("ig_percentile", self.html)

    def test_hy_current_bps_jinja_var(self):
        self.assertIn("hy_current_bps", self.html)

    def test_ig_current_bps_jinja_var(self):
        self.assertIn("ig_current_bps", self.html)

    def test_ccc_current_bps_jinja_var(self):
        self.assertIn("ccc_current_bps", self.html)

    def test_api_fetch_hy_spread(self):
        self.assertIn("/api/metrics/hy_spread", self.html)

    def test_api_fetch_ig_spread(self):
        self.assertIn("/api/metrics/ig_spread", self.html)

    def test_api_fetch_ccc_spread(self):
        self.assertIn("/api/metrics/ccc_spread", self.html)

    def test_collapsible_sections_present(self):
        self.assertIn("collapsible-section", self.html)

    def test_time_range_buttons_present(self):
        self.assertIn("data-timeframe", self.html)

    def test_key_stats_panel_present(self):
        self.assertIn("key-stats-panel", self.html)

    def test_hy_ig_differential_labeled(self):
        self.assertIn("HY–IG Differential", self.html)

    def test_no_unsafe_jinja_filter_on_dynamic_values(self):
        # No | safe on dynamic metric values (security: no XSS path)
        # Server-rendered values are only numeric (percentile, bps) — safe by construction
        # Verify: no raw user input piped to chart labels
        unsafe_patterns = re.findall(r'\{\{.*?\|\s*safe\s*\}\}', self.html)
        self.assertEqual(len(unsafe_patterns), 0,
                         f"Found | safe filters that could allow XSS: {unsafe_patterns}")

    def test_endblock_present(self):
        self.assertIn("{% endblock %}", self.html)


# ---------------------------------------------------------------------------
# _percentile_label helper
# ---------------------------------------------------------------------------

class TestPercentileLabelHelper(unittest.TestCase):
    """_percentile_label must return correct human-readable labels."""

    def setUp(self):
        self.src = get_dashboard_src()
        self._exec_globals = {}
        func_src = _extract_function(self.src, '_percentile_label')
        exec(func_src, self._exec_globals)

    def _exec_label(self, pct):
        return self._exec_globals['_percentile_label'](pct)

    def test_function_defined(self):
        self.assertIn('def _percentile_label(', self.src)

    def test_none_returns_unavailable(self):
        self.assertEqual(self._exec_label(None), 'unavailable')

    def test_5th_percentile_label(self):
        self.assertEqual(self._exec_label(5), 'near historical tights')

    def test_20th_percentile_label(self):
        self.assertEqual(self._exec_label(20), 'historically tight')

    def test_40th_percentile_label(self):
        self.assertEqual(self._exec_label(40), 'below median')

    def test_60th_percentile_label(self):
        self.assertEqual(self._exec_label(60), 'above median')

    def test_85th_percentile_label(self):
        self.assertEqual(self._exec_label(85), 'historically wide')

    def test_95th_percentile_label(self):
        self.assertEqual(self._exec_label(95), 'near historical wides')


if __name__ == '__main__':
    unittest.main()
