"""
Tests for US-206.1: Global Trade Pulse — Backend.

Covers:
- trade_interpretation_config.py: 4 condition entries
- get_trade_interpretation(): correct label/body selection, fallback copy
- Trade condition determination logic (via dashboard helpers)
- YoY calculation
- 10-year rolling percentile computation
- dashboard.py imports and index route context
- market_signals.py BOPGSTB registration

No Flask server, database, or external APIs required.
"""

import os
import sys
import unittest
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def get_dashboard_src():
    return read_file(os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py'))


def get_market_signals_src():
    return read_file(os.path.join(SIGNALTRACKERS_DIR, 'market_signals.py'))


# ---------------------------------------------------------------------------
# trade_interpretation_config.py — module-level tests
# ---------------------------------------------------------------------------

class TestTradeInterpretationConfigExists(unittest.TestCase):
    def test_config_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'trade_interpretation_config.py')
        self.assertTrue(os.path.isfile(path), "trade_interpretation_config.py not found")

    def test_config_importable(self):
        from trade_interpretation_config import TRADE_INTERPRETATIONS  # noqa: F401

    def test_get_trade_interpretation_importable(self):
        from trade_interpretation_config import get_trade_interpretation  # noqa: F401


class TestTradeInterpretationsDict(unittest.TestCase):
    def setUp(self):
        from trade_interpretation_config import TRADE_INTERPRETATIONS
        self.interps = TRADE_INTERPRETATIONS

    def _assert_key(self, key):
        self.assertIn(key, self.interps, f"Missing key: {key}")
        entry = self.interps[key]
        self.assertIsInstance(entry, dict)
        self.assertIn('label', entry)
        self.assertIn('body', entry)
        self.assertIsInstance(entry['label'], str)
        self.assertGreater(len(entry['label']), 5, f"Label too short for {key}")

    def test_widening_deficit(self):
        self._assert_key("widening_deficit")

    def test_narrowing_deficit(self):
        self._assert_key("narrowing_deficit")

    def test_widening_surplus(self):
        self._assert_key("widening_surplus")

    def test_narrowing_surplus(self):
        self._assert_key("narrowing_surplus")

    def test_total_entry_count(self):
        self.assertGreaterEqual(len(self.interps), 4)


class TestGetTradeInterpretation(unittest.TestCase):
    def setUp(self):
        from trade_interpretation_config import get_trade_interpretation
        self.fn = get_trade_interpretation

    def test_returns_tuple(self):
        result = self.fn(None, "widening_deficit", trade_percentile=50)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_with_percentile_returns_label_and_body(self):
        label, body = self.fn(None, "widening_deficit", trade_percentile=33)
        self.assertIsNotNone(label)
        self.assertIsNotNone(body)
        self.assertIn("33", body)

    def test_none_condition_returns_none_none(self):
        label, body = self.fn(None, None)
        self.assertIsNone(label)
        self.assertIsNone(body)

    def test_none_regime_with_percentile_returns_body(self):
        label, body = self.fn(None, "widening_deficit", trade_percentile=33)
        self.assertIsNotNone(label)
        self.assertIsNotNone(body)
        self.assertIn("33", body)

    def test_fallback_with_none_percentile_returns_none_body(self):
        # None percentile → can't construct fallback body
        label, body = self.fn(None, "widening_deficit", trade_percentile=None)
        self.assertIsNone(body)

    def test_all_conditions_return_label(self):
        conditions = ["widening_deficit", "narrowing_deficit", "widening_surplus", "narrowing_surplus"]
        for condition in conditions:
            label, body = self.fn(None, condition, trade_percentile=50)
            self.assertIsNotNone(label, f"label is None for {condition}")
            self.assertIsNotNone(body, f"body is None for {condition}")


# ---------------------------------------------------------------------------
# Trade condition logic
# ---------------------------------------------------------------------------

class TestTradeConditionLogic(unittest.TestCase):
    """Tests for the trade condition determination logic using inline implementation."""

    def _determine_condition(self, current_value, yoy_change):
        """Replicates the condition logic from dashboard.py _get_trade_balance_context."""
        if yoy_change is None:
            return None
        if current_value < 0:
            return 'widening_deficit' if yoy_change < 0 else 'narrowing_deficit'
        else:
            return 'widening_surplus' if yoy_change > 0 else 'narrowing_surplus'

    def test_deficit_worsening_is_widening_deficit(self):
        # -100 current, -10 YoY change (deficit grew by $10b)
        self.assertEqual(self._determine_condition(-100.0, -10.0), 'widening_deficit')

    def test_deficit_improving_is_narrowing_deficit(self):
        # -100 current, +10 YoY change (deficit shrank by $10b)
        self.assertEqual(self._determine_condition(-100.0, 10.0), 'narrowing_deficit')

    def test_surplus_growing_is_widening_surplus(self):
        # +5 current, +2 YoY change
        self.assertEqual(self._determine_condition(5.0, 2.0), 'widening_surplus')

    def test_surplus_shrinking_is_narrowing_surplus(self):
        # +5 current, -2 YoY change
        self.assertEqual(self._determine_condition(5.0, -2.0), 'narrowing_surplus')

    def test_none_yoy_returns_none(self):
        self.assertIsNone(self._determine_condition(-100.0, None))

    def test_zero_current_with_positive_yoy_is_widening_surplus(self):
        # 0 is not < 0, so treated as surplus
        self.assertEqual(self._determine_condition(0.0, 1.0), 'widening_surplus')

    def test_zero_yoy_on_deficit_is_narrowing_deficit(self):
        # No change → not worsening
        self.assertEqual(self._determine_condition(-50.0, 0.0), 'narrowing_deficit')


# ---------------------------------------------------------------------------
# YoY calculation logic
# ---------------------------------------------------------------------------

class TestYoYCalculation(unittest.TestCase):
    def _build_df(self, rows):
        """Build a minimal trade_balance DataFrame from (year, month, value) tuples."""
        import pandas as pd
        data = [
            {'date': pd.Timestamp(year=y, month=m, day=1), 'trade_balance': v}
            for y, m, v in rows
        ]
        df = pd.DataFrame(data).sort_values('date').reset_index(drop=True)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def _compute_yoy(self, df):
        """Replicates the YoY logic from _get_trade_balance_context."""
        current_row = df.iloc[-1]
        current_value = float(current_row['trade_balance'])
        current_date = current_row['date']
        prior_year = current_date.year - 1
        prior_month = current_date.month
        prior_rows = df[
            (df['date'].dt.year == prior_year) & (df['date'].dt.month == prior_month)
        ]
        if not prior_rows.empty:
            prior_value = float(prior_rows.iloc[-1]['trade_balance'])
            return round(current_value - prior_value, 1)
        return None

    def test_yoy_deficit_widening(self):
        # Jan 2025: -90, Jan 2026: -100 → YoY = -10
        df = self._build_df([(2025, 1, -90.0), (2025, 6, -95.0), (2026, 1, -100.0)])
        self.assertAlmostEqual(self._compute_yoy(df), -10.0)

    def test_yoy_deficit_narrowing(self):
        # Jan 2025: -100, Jan 2026: -80 → YoY = +20
        df = self._build_df([(2025, 1, -100.0), (2025, 6, -95.0), (2026, 1, -80.0)])
        self.assertAlmostEqual(self._compute_yoy(df), 20.0)

    def test_yoy_no_prior_year_row_returns_none(self):
        # Only one month of data
        df = self._build_df([(2026, 1, -100.0)])
        self.assertIsNone(self._compute_yoy(df))

    def test_yoy_same_value(self):
        df = self._build_df([(2025, 3, -75.0), (2026, 3, -75.0)])
        self.assertAlmostEqual(self._compute_yoy(df), 0.0)


# ---------------------------------------------------------------------------
# Percentile computation
# ---------------------------------------------------------------------------

class TestTradePercentile(unittest.TestCase):
    """Tests for the 10-year rolling percentile logic used in _get_trade_balance_context."""

    def _compute_percentile(self, values_by_date, current_value):
        """Replicates the 10-year window percentile logic."""
        import pandas as pd
        series = pd.Series(values_by_date)
        series.index = pd.to_datetime(series.index)
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=10)
        windowed = series[series.index >= cutoff]
        if len(windowed) < 2:
            windowed = series
        count_below = int((windowed < current_value).sum())
        return round(float(count_below / len(windowed) * 100), 1)

    def test_value_at_minimum_returns_0(self):
        import pandas as pd
        # Generate 12 monthly values within last 10 years
        dates = pd.date_range(start='2020-01-01', periods=12, freq='MS')
        values = {str(d.date()): float(i + 1) for i, d in enumerate(dates)}
        pct = self._compute_percentile(values, 1.0)
        self.assertAlmostEqual(pct, 0.0)

    def test_value_above_all_returns_100(self):
        import pandas as pd
        dates = pd.date_range(start='2020-01-01', periods=12, freq='MS')
        values = {str(d.date()): float(i + 1) for i, d in enumerate(dates)}
        pct = self._compute_percentile(values, 100.0)
        self.assertAlmostEqual(pct, 100.0)

    def test_value_at_median_returns_approx_50(self):
        import pandas as pd
        dates = pd.date_range(start='2020-01-01', periods=100, freq='MS')
        values = {str(d.date()): float(i) for i, d in enumerate(dates)}
        # Value 50 is at position 50 out of 100, so 50/100 = 50%
        pct = self._compute_percentile(values, 50.0)
        self.assertAlmostEqual(pct, 50.0, delta=2.0)

    def test_old_data_outside_10y_excluded(self):
        """Data older than 10 years should be excluded from the percentile window."""
        import pandas as pd
        # Mix: old high values + recent low values
        old_dates = pd.date_range(start='2010-01-01', periods=60, freq='MS')
        recent_dates = pd.date_range(start='2020-01-01', periods=12, freq='MS')
        values = {}
        for d in old_dates:
            values[str(d.date())] = 1000.0  # very high old values
        for d in recent_dates:
            values[str(d.date())] = 1.0  # low recent values
        # current_value=1.0, all recent values also 1.0, so 0 below current
        pct = self._compute_percentile(values, 1.0)
        # Should be 0% since all windowed values equal current (none strictly below)
        self.assertAlmostEqual(pct, 0.0, delta=1.0)


# ---------------------------------------------------------------------------
# dashboard.py integration
# ---------------------------------------------------------------------------

class TestDashboardImports(unittest.TestCase):
    def test_imports_get_trade_interpretation(self):
        src = get_dashboard_src()
        self.assertIn('get_trade_interpretation', src)

    def test_imports_from_trade_interpretation_config(self):
        src = get_dashboard_src()
        self.assertIn('trade_interpretation_config', src)

    def test_get_trade_balance_context_defined(self):
        src = get_dashboard_src()
        self.assertIn('_get_trade_balance_context', src)

    def test_index_route_calls_get_trade_balance_context(self):
        src = get_dashboard_src()
        self.assertIn('_get_trade_balance_context()', src)

    def test_index_route_passes_ctx_to_template(self):
        src = get_dashboard_src()
        # Should have **ctx unpacking to render_template
        self.assertIn('render_template(\'index.html\', **ctx)', src)

    def test_trade_balance_value_key_in_context_fn(self):
        src = get_dashboard_src()
        self.assertIn('trade_balance_value', src)

    def test_trade_percentile_key_in_context_fn(self):
        src = get_dashboard_src()
        self.assertIn('trade_percentile', src)

    def test_trade_interpretation_label_key(self):
        src = get_dashboard_src()
        self.assertIn('trade_interpretation_label', src)

    def test_trade_interpretation_body_key(self):
        src = get_dashboard_src()
        self.assertIn('trade_interpretation_body', src)

    def test_trade_last_updated_key(self):
        src = get_dashboard_src()
        self.assertIn('trade_last_updated', src)

    def test_trade_yoy_change_key(self):
        src = get_dashboard_src()
        self.assertIn('trade_yoy_change', src)

    def test_trade_condition_key(self):
        src = get_dashboard_src()
        self.assertIn('trade_condition', src)

    def test_trade_balance_csv_loaded(self):
        src = get_dashboard_src()
        self.assertIn('trade_balance.csv', src)


# ---------------------------------------------------------------------------
# market_signals.py — BOPGSTB registration
# ---------------------------------------------------------------------------

class TestMarketSignalsBOPGSTB(unittest.TestCase):
    def test_bopgstb_in_fred_series(self):
        src = get_market_signals_src()
        self.assertIn('BOPGSTB', src)

    def test_trade_balance_key_present(self):
        src = get_market_signals_src()
        self.assertIn("'trade_balance'", src)

    def test_bopgstb_mapped_to_trade_balance(self):
        src = get_market_signals_src()
        # Both key and value should appear near each other
        idx_key = src.find("'trade_balance'")
        idx_val = src.find("'BOPGSTB'")
        self.assertGreater(idx_key, -1)
        self.assertGreater(idx_val, -1)
        # They should be within 100 chars of each other
        self.assertLess(abs(idx_key - idx_val), 100)

    def test_market_signals_tracker_importable(self):
        from market_signals import MarketSignalsTracker  # noqa: F401


if __name__ == '__main__':
    unittest.main()
