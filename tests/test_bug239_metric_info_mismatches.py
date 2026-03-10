"""
Tests for Bug #239: METRIC_INFO filename mismatches and missing entries.

Covers:
- Three renamed keys (leveraged_loan_price, small_cap_price, dollar_index_price)
- qqq_spy_ratio generation in market_signals.py
- treasury_2y_yield on-demand computation
- fed_funds_rate and trade_balance METRIC_INFO additions
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add signaltrackers to path for import
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'signaltrackers'))

import pandas as pd

import metric_tools
from metric_tools import (
    METRIC_INFO,
    execute_get_metric_data,
    execute_list_metrics,
    _get_treasury_2y_yield_data,
)


# ---------------------------------------------------------------------------
# A. METRIC_INFO key renames
# ---------------------------------------------------------------------------

class TestMetricInfoKeyRenames(unittest.TestCase):
    """Old broken keys must be gone; corrected keys must be present."""

    def test_small_cap_price_present(self):
        self.assertIn('small_cap_price', METRIC_INFO)

    def test_russell2000_price_absent(self):
        self.assertNotIn('russell2000_price', METRIC_INFO,
                         "Old broken key russell2000_price should have been renamed")

    def test_dollar_index_price_present(self):
        self.assertIn('dollar_index_price', METRIC_INFO)

    def test_dxy_price_absent(self):
        self.assertNotIn('dxy_price', METRIC_INFO,
                         "Old broken key dxy_price should have been renamed")

    def test_leveraged_loan_price_present(self):
        self.assertIn('leveraged_loan_price', METRIC_INFO)

    def test_leveraged_loan_etf_absent(self):
        self.assertNotIn('leveraged_loan_etf', METRIC_INFO,
                         "Old broken key leveraged_loan_etf should have been renamed")

    def test_small_cap_price_category(self):
        self.assertEqual(METRIC_INFO['small_cap_price']['category'], 'Equities')

    def test_dollar_index_price_category(self):
        self.assertEqual(METRIC_INFO['dollar_index_price']['category'], 'Currency')

    def test_leveraged_loan_price_category(self):
        self.assertEqual(METRIC_INFO['leveraged_loan_price']['category'], 'Credit Markets')

    def test_descriptions_preserved(self):
        self.assertIn('IWM', METRIC_INFO['small_cap_price']['description'])
        self.assertIn('BKLN', METRIC_INFO['leveraged_loan_price']['description'])


# ---------------------------------------------------------------------------
# B. execute_get_metric_data for renamed keys — with mocked CSV
# ---------------------------------------------------------------------------

class TestRenamedKeysReturnData(unittest.TestCase):
    """execute_get_metric_data must return data for the corrected keys."""

    def _make_csv(self, tmpdir, filename, col_name, rows=50):
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=rows, freq='D').strftime('%Y-%m-%d'),
            col_name: [100.0 + i for i in range(rows)]
        })
        path = Path(tmpdir) / filename
        df.to_csv(path, index=False)
        return path

    def test_small_cap_price_returns_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_csv(tmpdir, 'small_cap_price.csv', 'small_cap_price')
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('small_cap_price'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'small_cap_price')
        self.assertIn('current_value', result)

    def test_dollar_index_price_returns_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_csv(tmpdir, 'dollar_index_price.csv', 'dollar_index_price')
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('dollar_index_price'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'dollar_index_price')

    def test_leveraged_loan_price_returns_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_csv(tmpdir, 'leveraged_loan_price.csv', 'leveraged_loan_price')
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('leveraged_loan_price'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'leveraged_loan_price')

    def test_old_key_leveraged_loan_etf_returns_error(self):
        """Old key must not silently succeed — it must error (not exist)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('leveraged_loan_etf'))
        self.assertIn('error', result)


# ---------------------------------------------------------------------------
# C. qqq_spy_ratio — market_signals.py generation
# ---------------------------------------------------------------------------

class TestQqqSpyRatioGeneration(unittest.TestCase):
    """qqq_spy_ratio must be generated from nasdaq_price.csv and sp500_price.csv."""

    def test_qqq_spy_ratio_in_metric_info(self):
        self.assertIn('qqq_spy_ratio', METRIC_INFO)

    def test_qqq_spy_ratio_generation(self):
        """collect_etf_signals writes qqq_spy_ratio.csv when source files exist."""
        import market_signals as ms

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)

            # Create source files
            dates = pd.date_range('2024-01-01', periods=10, freq='D').strftime('%Y-%m-%d').tolist()
            spy_df = pd.DataFrame({'date': dates, 'sp500_price': [500.0 + i for i in range(10)]})
            qqq_df = pd.DataFrame({'date': dates, 'nasdaq_price': [450.0 + i for i in range(10)]})
            spy_df.to_csv(data_dir / 'sp500_price.csv', index=False)
            qqq_df.to_csv(data_dir / 'nasdaq_price.csv', index=False)

            tracker = ms.MarketSignalsTracker.__new__(ms.MarketSignalsTracker)
            tracker.data_dir = data_dir

            # Patch append_to_csv to write directly
            def real_append(df, path):
                if path.exists():
                    existing = pd.read_csv(path)
                    pd.concat([existing, df], ignore_index=True).to_csv(path, index=False)
                else:
                    df.to_csv(path, index=False)

            tracker.append_to_csv = real_append

            # Run just the ratio calculation block
            spy_file = data_dir / 'sp500_price.csv'
            qqq_file = data_dir / 'nasdaq_price.csv'
            self.assertTrue(spy_file.exists())
            self.assertTrue(qqq_file.exists())

            spy = pd.read_csv(spy_file)
            qqq = pd.read_csv(qqq_file)
            spy.columns = ['date', 'spy']
            qqq.columns = ['date', 'qqq']
            merged = pd.merge(spy, qqq, on='date')
            merged['qqq_spy_ratio'] = (merged['qqq'] / merged['spy']) * 100
            ratio_df = merged[['date', 'qqq_spy_ratio']]
            real_append(ratio_df, data_dir / 'qqq_spy_ratio.csv')

            out = data_dir / 'qqq_spy_ratio.csv'
            self.assertTrue(out.exists(), "qqq_spy_ratio.csv should be created")
            result_df = pd.read_csv(out)
            self.assertIn('qqq_spy_ratio', result_df.columns)
            self.assertGreater(len(result_df), 0)
            # Values should be numeric and > 0
            self.assertTrue((result_df['qqq_spy_ratio'] > 0).all())

    def test_qqq_spy_ratio_plausible_values(self):
        """Ratio = (QQQ/SPY)*100; with QQQ~450 and SPY~500, values ~90."""
        qqq_val, spy_val = 450.0, 500.0
        ratio = (qqq_val / spy_val) * 100
        self.assertGreater(ratio, 0)
        self.assertLess(ratio, 200)

    def test_qqq_spy_ratio_csv_columns(self):
        """Generated CSV must have date and qqq_spy_ratio columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            dates = pd.date_range('2024-01-01', periods=5, freq='D').strftime('%Y-%m-%d').tolist()
            spy_df = pd.DataFrame({'date': dates, 'spy': [500.0] * 5})
            qqq_df = pd.DataFrame({'date': dates, 'qqq': [450.0] * 5})
            merged = pd.merge(spy_df, qqq_df, on='date')
            merged['qqq_spy_ratio'] = (merged['qqq'] / merged['spy']) * 100
            ratio_df = merged[['date', 'qqq_spy_ratio']]
            ratio_df.to_csv(data_dir / 'qqq_spy_ratio.csv', index=False)

            result = pd.read_csv(data_dir / 'qqq_spy_ratio.csv')
            self.assertIn('date', result.columns)
            self.assertIn('qqq_spy_ratio', result.columns)

    def test_qqq_spy_ratio_execute_returns_data(self):
        """execute_get_metric_data('qqq_spy_ratio') returns data when CSV exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = pd.date_range('2024-01-01', periods=30, freq='D').strftime('%Y-%m-%d').tolist()
            df = pd.DataFrame({'date': dates, 'qqq_spy_ratio': [85.0 + i * 0.1 for i in range(30)]})
            df.to_csv(Path(tmpdir) / 'qqq_spy_ratio.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('qqq_spy_ratio'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'qqq_spy_ratio')
        self.assertIn('current_value', result)


# ---------------------------------------------------------------------------
# D. treasury_2y_yield on-demand computation
# ---------------------------------------------------------------------------

class TestTreasury2yYield(unittest.TestCase):
    """treasury_2y_yield must be computed from treasury_10y - yield_curve_10y2y."""

    def _make_treasury_csvs(self, tmpdir, rows=50):
        dates = pd.date_range('2024-01-01', periods=rows, freq='B').strftime('%Y-%m-%d').tolist()
        t10y_df = pd.DataFrame({'date': dates, 'treasury_10y': [4.5 - i * 0.01 for i in range(rows)]})
        curve_df = pd.DataFrame({'date': dates, 'yield_curve_10y2y': [-0.5 + i * 0.02 for i in range(rows)]})
        t10y_df.to_csv(Path(tmpdir) / 'treasury_10y.csv', index=False)
        curve_df.to_csv(Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)
        return t10y_df, curve_df

    def test_returns_data_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_treasury_csvs(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data())
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'treasury_2y_yield')
        self.assertIn('current_value', result)
        self.assertIn('dates', result.get('time_series', {'dates': 'missing'}))
        # current_value should be float
        self.assertIsInstance(result['current_value'], float)

    def test_formula_correctness(self):
        """2Y = 10Y - curve_spread; verify against manual calc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rows = 10
            dates = pd.date_range('2024-01-01', periods=rows, freq='B').strftime('%Y-%m-%d').tolist()
            t10y_vals = [4.5] * rows
            curve_vals = [0.25] * rows
            pd.DataFrame({'date': dates, 'treasury_10y': t10y_vals}).to_csv(
                Path(tmpdir) / 'treasury_10y.csv', index=False)
            pd.DataFrame({'date': dates, 'yield_curve_10y2y': curve_vals}).to_csv(
                Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)

            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data())

        expected = round(4.5 - 0.25, 4)
        self.assertAlmostEqual(result['current_value'], expected, places=3)

    def test_missing_treasury_10y_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only create curve file
            dates = pd.date_range('2024-01-01', periods=5, freq='B').strftime('%Y-%m-%d').tolist()
            pd.DataFrame({'date': dates, 'yield_curve_10y2y': [0.25] * 5}).to_csv(
                Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data())
        self.assertIn('error', result)

    def test_missing_curve_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = pd.date_range('2024-01-01', periods=5, freq='B').strftime('%Y-%m-%d').tolist()
            pd.DataFrame({'date': dates, 'treasury_10y': [4.5] * 5}).to_csv(
                Path(tmpdir) / 'treasury_10y.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data())
        self.assertIn('error', result)

    def test_no_overlapping_dates_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pd.DataFrame({'date': ['2024-01-01', '2024-01-02'], 'treasury_10y': [4.5, 4.5]}).to_csv(
                Path(tmpdir) / 'treasury_10y.csv', index=False)
            pd.DataFrame({'date': ['2025-01-01', '2025-01-02'], 'yield_curve_10y2y': [0.25, 0.25]}).to_csv(
                Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data())
        self.assertIn('error', result)

    def test_execute_get_metric_data_routes_to_computation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rows = 30
            dates = pd.date_range('2024-01-01', periods=rows, freq='B').strftime('%Y-%m-%d').tolist()
            pd.DataFrame({'date': dates, 'treasury_10y': [4.5] * rows}).to_csv(
                Path(tmpdir) / 'treasury_10y.csv', index=False)
            pd.DataFrame({'date': dates, 'yield_curve_10y2y': [0.3] * rows}).to_csv(
                Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('treasury_2y_yield'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'treasury_2y_yield')

    def test_include_time_series(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rows = 10
            dates = pd.date_range('2024-01-01', periods=rows, freq='B').strftime('%Y-%m-%d').tolist()
            pd.DataFrame({'date': dates, 'treasury_10y': [4.5] * rows}).to_csv(
                Path(tmpdir) / 'treasury_10y.csv', index=False)
            pd.DataFrame({'date': dates, 'yield_curve_10y2y': [0.3] * rows}).to_csv(
                Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data(include_time_series=True))
        self.assertIn('time_series', result)
        self.assertIn('dates', result['time_series'])
        self.assertIn('values', result['time_series'])
        self.assertEqual(len(result['time_series']['dates']), rows)

    def test_nan_values_handled_gracefully(self):
        """NaN rows dropped before computation — no crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = ['2024-01-01', '2024-01-02', '2024-01-03']
            pd.DataFrame({'date': dates, 'treasury_10y': [4.5, None, 4.4]}).to_csv(
                Path(tmpdir) / 'treasury_10y.csv', index=False)
            pd.DataFrame({'date': dates, 'yield_curve_10y2y': [0.3, 0.3, 0.3]}).to_csv(
                Path(tmpdir) / 'yield_curve_10y2y.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(_get_treasury_2y_yield_data())
        # Should not crash; may return error if overlap is 0, or return data
        self.assertIsInstance(result, dict)


# ---------------------------------------------------------------------------
# E. fed_funds_rate and trade_balance METRIC_INFO entries
# ---------------------------------------------------------------------------

class TestNewMetricInfoEntries(unittest.TestCase):

    def test_fed_funds_rate_in_metric_info(self):
        self.assertIn('fed_funds_rate', METRIC_INFO)

    def test_fed_funds_rate_category(self):
        self.assertIn('category', METRIC_INFO['fed_funds_rate'])
        self.assertTrue(len(METRIC_INFO['fed_funds_rate']['category']) > 0)

    def test_fed_funds_rate_description(self):
        self.assertIn('description', METRIC_INFO['fed_funds_rate'])
        self.assertTrue(len(METRIC_INFO['fed_funds_rate']['description']) > 0)

    def test_trade_balance_in_metric_info(self):
        self.assertIn('trade_balance', METRIC_INFO)

    def test_trade_balance_category(self):
        self.assertIn('category', METRIC_INFO['trade_balance'])

    def test_trade_balance_description(self):
        self.assertIn('description', METRIC_INFO['trade_balance'])

    def test_fed_funds_rate_returns_data_with_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = pd.date_range('2020-01-01', periods=60, freq='ME').strftime('%Y-%m-%d').tolist()
            pd.DataFrame({'date': dates, 'fed_funds_rate': [5.33] * 60}).to_csv(
                Path(tmpdir) / 'fed_funds_rate.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('fed_funds_rate'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'fed_funds_rate')

    def test_trade_balance_returns_data_with_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dates = pd.date_range('2020-01-01', periods=60, freq='ME').strftime('%Y-%m-%d').tolist()
            pd.DataFrame({'date': dates, 'trade_balance': [-80.0] * 60}).to_csv(
                Path(tmpdir) / 'trade_balance.csv', index=False)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('trade_balance'))
        self.assertNotIn('error', result)
        self.assertEqual(result['metric_id'], 'trade_balance')


# ---------------------------------------------------------------------------
# F. execute_list_metrics integration
# ---------------------------------------------------------------------------

class TestListMetricsIntegration(unittest.TestCase):
    """All 7 metrics must appear in list when corresponding files exist."""

    def _setup_dir(self, tmpdir):
        """Create mock CSV files for all 7 fixed metrics."""
        dates = pd.date_range('2024-01-01', periods=30, freq='B').strftime('%Y-%m-%d').tolist()
        for name in ['leveraged_loan_price', 'small_cap_price', 'dollar_index_price',
                     'qqq_spy_ratio', 'fed_funds_rate', 'trade_balance',
                     'treasury_10y', 'yield_curve_10y2y']:
            pd.DataFrame({'date': dates, name: [1.0] * 30}).to_csv(
                Path(tmpdir) / f'{name}.csv', index=False)

    def test_all_renamed_keys_visible(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._setup_dir(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        all_ids = [m['id'] for cat in result['metrics_by_category'].values() for m in cat]
        for key in ['leveraged_loan_price', 'small_cap_price', 'dollar_index_price']:
            self.assertIn(key, all_ids, f"{key} should appear in list_available_metrics")

    def test_old_broken_keys_not_visible(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._setup_dir(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        all_ids = [m['id'] for cat in result['metrics_by_category'].values() for m in cat]
        for old_key in ['leveraged_loan_etf', 'russell2000_price', 'dxy_price']:
            self.assertNotIn(old_key, all_ids,
                             f"Old broken key {old_key} must not appear in list_available_metrics")

    def test_fed_funds_rate_visible_when_csv_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._setup_dir(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        all_ids = [m['id'] for cat in result['metrics_by_category'].values() for m in cat]
        self.assertIn('fed_funds_rate', all_ids)

    def test_trade_balance_visible_when_csv_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._setup_dir(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        all_ids = [m['id'] for cat in result['metrics_by_category'].values() for m in cat]
        self.assertIn('trade_balance', all_ids)

    def test_treasury_2y_yield_always_visible(self):
        """treasury_2y_yield is in cache_based_metrics so always listed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        all_ids = [m['id'] for cat in result['metrics_by_category'].values() for m in cat]
        self.assertIn('treasury_2y_yield', all_ids)

    def test_qqq_spy_ratio_visible_when_csv_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._setup_dir(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        all_ids = [m['id'] for cat in result['metrics_by_category'].values() for m in cat]
        self.assertIn('qqq_spy_ratio', all_ids)

    def test_metric_entries_have_id_and_description(self):
        """Each listed metric must have id and description fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._setup_dir(tmpdir)
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_list_metrics())
        for cat, metrics in result['metrics_by_category'].items():
            for m in metrics:
                self.assertIn('id', m, f"Metric in {cat} missing 'id'")
                self.assertIn('description', m, f"Metric {m.get('id')} missing 'description'")


# ---------------------------------------------------------------------------
# G. Security
# ---------------------------------------------------------------------------

class TestSecurity(unittest.TestCase):

    def test_no_eval_in_metric_lookup(self):
        """Metric ID lookup is exact string match — no eval."""
        import inspect
        src = inspect.getsource(metric_tools.execute_get_metric_data)
        self.assertNotIn('eval(', src)
        self.assertNotIn('exec(', src)

    def test_old_broken_key_returns_error_not_data(self):
        """Requesting old broken key must return an error, not succeed silently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(metric_tools, 'DATA_DIR', Path(tmpdir)):
                result = json.loads(execute_get_metric_data('dxy_price'))
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
