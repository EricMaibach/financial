"""
Static and unit tests for US-208.1: Consolidate get_stats() into shared get_metric_stats()
and fix daily briefing 52-week gap.

Tests verify:
- get_metric_stats() is defined at module level in dashboard.py
- get_metric_stats() returns all 11 expected fields with correct values
- All 6 inline get_stats() definitions have been removed
- No stale field names (change_30d_pct, change_5d_pct) remain in dashboard.py
- Daily briefing (generate_market_summary) output contains 52w context for key assets
- Shared function handles edge cases: None df, too-short df, single-value series

No Flask server, database, or external APIs required.
"""

import os
import re
import sys
import unittest

import pandas as pd
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_dashboard():
    with open(os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py'), 'r') as f:
        return f.read()


def make_df(values, col='value'):
    """Build a minimal DataFrame with date + value columns."""
    dates = pd.date_range('2020-01-01', periods=len(values), freq='D')
    return pd.DataFrame({'date': dates, col: values})


# ---------------------------------------------------------------------------
# Structural tests — source-level checks
# ---------------------------------------------------------------------------

class TestGetMetricStatsStructural(unittest.TestCase):

    def setUp(self):
        self.src = read_dashboard()

    def test_module_level_function_defined(self):
        """get_metric_stats must be defined at module level (not inside another function)."""
        # Must appear as a top-level function (no leading spaces before def)
        self.assertIsNotNone(re.search(r'^def get_metric_stats\(df\):', self.src, re.MULTILINE))

    def test_no_inline_get_stats_remaining(self):
        """All inline def get_stats() definitions must be removed."""
        self.assertNotIn('def get_stats(', self.src,
                         "Inline 'def get_stats(' still present — should be removed")

    def test_no_stale_change_30d_pct_field(self):
        """Stale field name 'change_30d_pct' must not appear in dashboard.py."""
        self.assertNotIn("'change_30d_pct'", self.src,
                         "Stale field name change_30d_pct still referenced")

    def test_no_stale_change_5d_pct_field(self):
        """Stale field name 'change_5d_pct' must not appear in dashboard.py."""
        self.assertNotIn("'change_5d_pct'", self.src,
                         "Stale field name change_5d_pct still referenced")

    def test_get_metric_stats_used_in_market_summary(self):
        """generate_market_summary must call get_metric_stats."""
        market_summary_match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(market_summary_match, "generate_market_summary not found")
        body = market_summary_match.group(1)
        self.assertIn('get_metric_stats(', body,
                      "generate_market_summary does not call get_metric_stats")

    def test_get_metric_stats_used_in_crypto_summary(self):
        """generate_crypto_market_summary must call get_metric_stats."""
        match = re.search(
            r'def generate_crypto_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(match)
        self.assertIn('get_metric_stats(', match.group(1))

    def test_get_metric_stats_used_in_equity_summary(self):
        """generate_equity_market_summary must call get_metric_stats."""
        match = re.search(
            r'def generate_equity_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(match)
        self.assertIn('get_metric_stats(', match.group(1))

    def test_get_metric_stats_used_in_rates_summary(self):
        """generate_rates_market_summary must call get_metric_stats."""
        match = re.search(
            r'def generate_rates_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(match)
        self.assertIn('get_metric_stats(', match.group(1))

    def test_get_metric_stats_used_in_dollar_summary(self):
        """generate_dollar_market_summary must call get_metric_stats."""
        match = re.search(
            r'def generate_dollar_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(match)
        self.assertIn('get_metric_stats(', match.group(1))

    def test_get_metric_stats_used_in_credit_summary(self):
        """generate_credit_market_summary must call get_metric_stats."""
        match = re.search(
            r'def generate_credit_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(match)
        self.assertIn('get_metric_stats(', match.group(1))

    def test_daily_briefing_contains_52w_reference(self):
        """generate_market_summary must reference 52w data for key assets."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(match)
        body = match.group(1)
        self.assertIn('52w', body,
                      "generate_market_summary body should contain 52w range context")

    def test_daily_briefing_52w_high_present(self):
        """generate_market_summary must reference high_52w field."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        body = match.group(1)
        self.assertIn("stats['high_52w']", body)

    def test_daily_briefing_52w_low_present(self):
        """generate_market_summary must reference low_52w field."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        body = match.group(1)
        self.assertIn("stats['low_52w']", body)

    def test_get_metric_stats_returns_all_fields(self):
        """get_metric_stats must return a dict containing all 11 required field names."""
        required = {
            'current', 'percentile', 'change_1d', 'change_5d', 'change_30d',
            'pct_change_5d', 'pct_change_30d', 'high_52w', 'low_52w', 'min', 'max'
        }
        # Check by inspection of source
        for field in required:
            self.assertIn(f"'{field}'", self.src,
                          f"Field '{field}' not found in get_metric_stats return dict")


# ---------------------------------------------------------------------------
# Unit tests — get_metric_stats() correctness
# ---------------------------------------------------------------------------

class TestGetMetricStatsUnit(unittest.TestCase):

    def setUp(self):
        from dashboard import get_metric_stats
        self.fn = get_metric_stats

    def test_returns_none_for_none_input(self):
        self.assertIsNone(self.fn(None))

    def test_returns_none_for_single_row(self):
        df = make_df([100.0])
        self.assertIsNone(self.fn(df))

    def test_returns_none_for_empty_df(self):
        df = pd.DataFrame({'date': [], 'value': []})
        self.assertIsNone(self.fn(df))

    def test_all_fields_present(self):
        df = make_df(list(range(1, 50)))
        result = self.fn(df)
        self.assertIsNotNone(result)
        required = {
            'current', 'percentile', 'change_1d', 'change_5d', 'change_30d',
            'pct_change_5d', 'pct_change_30d', 'high_52w', 'low_52w', 'min', 'max'
        }
        for field in required:
            self.assertIn(field, result, f"Field '{field}' missing from result")

    def test_current_is_last_value(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        df = make_df(values)
        result = self.fn(df)
        self.assertAlmostEqual(result['current'], 50.0)

    def test_change_1d_correct(self):
        values = [10.0, 20.0, 35.0]
        df = make_df(values)
        result = self.fn(df)
        self.assertAlmostEqual(result['change_1d'], 15.0)  # 35 - 20

    def test_change_5d_correct(self):
        values = list(range(1, 12))  # 11 values: 1..11
        df = make_df(values)
        result = self.fn(df)
        # change_5d = last - 6th-from-end = 11 - 6 = 5
        self.assertAlmostEqual(result['change_5d'], 5.0)

    def test_change_30d_correct(self):
        values = list(range(1, 35))  # 34 values
        df = make_df(values)
        result = self.fn(df)
        # change_30d = last - 31st-from-end = 34 - 4 = 30
        self.assertAlmostEqual(result['change_30d'], 30.0)

    def test_pct_change_5d_correct(self):
        values = [100.0] * 10 + [110.0]  # 11 values, last is 110
        df = make_df(values)
        result = self.fn(df)
        # pct_change_5d = (110/100 - 1)*100 = 10.0
        self.assertAlmostEqual(result['pct_change_5d'], 10.0)

    def test_pct_change_30d_correct(self):
        # 32 values: index 0 = ignored, index 1..30 = 100.0, index 31 = 110.0
        # values[-31] = index 1 = 100.0 → pct_change_30d = (110/100 - 1)*100 = 10.0
        values = [999.0] + [100.0] * 30 + [110.0]  # 32 values
        df = make_df(values)
        result = self.fn(df)
        self.assertAlmostEqual(result['pct_change_30d'], 10.0)

    def test_percentile_at_maximum(self):
        values = list(range(1, 11))  # 1..10, current = 10
        df = make_df(values)
        result = self.fn(df)
        # 9 values < 10 out of 10 → 90th percentile
        self.assertAlmostEqual(result['percentile'], 90.0)

    def test_percentile_at_minimum(self):
        values = [1, 2, 3, 4, 5]
        df = make_df(values)
        # Override last value to be below everything by reversing
        df2 = make_df([5, 4, 3, 2, 1])
        result = self.fn(df2)
        # 0 values < 1 out of 5 → 0th percentile
        self.assertAlmostEqual(result['percentile'], 0.0)

    def test_high_52w_uses_tail_252(self):
        # 300 values: first 250 at 1000, last 50 at 100
        values = [1000.0] * 250 + [100.0] * 50
        df = make_df(values)
        result = self.fn(df)
        # Tail 252 = values[48:] → mix of 1000s and 100s; max = 1000
        self.assertAlmostEqual(result['high_52w'], 1000.0)

    def test_high_52w_full_when_short(self):
        # Only 100 rows → uses full history
        values = list(range(1, 101))  # 1..100
        df = make_df(values)
        result = self.fn(df)
        self.assertAlmostEqual(result['high_52w'], 100.0)
        self.assertAlmostEqual(result['low_52w'], 1.0)

    def test_min_max_are_all_time(self):
        values = [50.0, 10.0, 200.0, 100.0, 75.0]
        df = make_df(values)
        result = self.fn(df)
        self.assertAlmostEqual(result['min'], 10.0)
        self.assertAlmostEqual(result['max'], 200.0)

    def test_change_5d_zero_when_not_enough_rows(self):
        values = [10.0, 20.0, 30.0]  # only 3 rows
        df = make_df(values)
        result = self.fn(df)
        self.assertEqual(result['change_5d'], 0.0)
        self.assertEqual(result['pct_change_5d'], 0.0)

    def test_change_30d_zero_when_not_enough_rows(self):
        values = list(range(1, 15))  # 14 rows
        df = make_df(values)
        result = self.fn(df)
        self.assertEqual(result['change_30d'], 0.0)
        self.assertEqual(result['pct_change_30d'], 0.0)

    def test_handles_non_date_column_name(self):
        """Should find the value column regardless of its name."""
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        df = pd.DataFrame({'date': dates, 'sp500_price': [100.0, 101, 102, 103, 104]})
        result = self.fn(df)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['current'], 104.0)


# ---------------------------------------------------------------------------
# 52-week gap tests — daily briefing output
# ---------------------------------------------------------------------------

class TestDailyBriefing52wContext(unittest.TestCase):
    """Verify the daily briefing source contains 52w distance-from-high context."""

    def setUp(self):
        self.src = read_dashboard()

    def test_52w_context_sp500(self):
        """S&P 500 section in daily briefing should reference 52w range."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        body = match.group(1)
        # S&P 500 block should have a 52w line
        sp500_section = re.search(r'S&P 500.*?summary_parts\.append.*?52w', body, re.DOTALL)
        self.assertIsNotNone(sp500_section,
                             "S&P 500 section in generate_market_summary missing 52w context")

    def test_52w_context_bitcoin(self):
        """Bitcoin section in daily briefing should reference 52w range."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        body = match.group(1)
        btc_section = re.search(r'Bitcoin.*?summary_parts\.append.*?52w', body, re.DOTALL)
        self.assertIsNotNone(btc_section,
                             "Bitcoin section in generate_market_summary missing 52w context")

    def test_52w_context_gold(self):
        """Gold section in daily briefing should reference 52w range."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        body = match.group(1)
        gold_section = re.search(r'Gold.*?summary_parts\.append.*?52w', body, re.DOTALL)
        self.assertIsNotNone(gold_section,
                             "Gold section in generate_market_summary missing 52w context")

    def test_pct_from_52h_computation_present(self):
        """Daily briefing must compute percentage distance from 52-week high."""
        match = re.search(
            r'def generate_market_summary\(\)(.*?)^def \w', self.src,
            re.DOTALL | re.MULTILINE
        )
        body = match.group(1)
        self.assertIn('pct_from_52h', body,
                      "pct_from_52h computation missing from generate_market_summary")


if __name__ == '__main__':
    unittest.main()
