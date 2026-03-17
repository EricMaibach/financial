"""
Tests for Bug #313: append_to_csv creates duplicate rows for FRED series
with future-dated projections (e.g., NROU, GDPPOT).

The root cause was that append_to_csv deduped only against dates < today,
so future-dated projections passed through as "new" on every collection run.

The fix deduplicates against ALL existing dates (excluding today, which is
replaceable), preventing future dates from being re-appended.
"""

import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)

from market_signals import MarketSignalsTracker


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


class TestAppendToCsvSourceCode(unittest.TestCase):
    """Static checks: the old buggy pattern must not be present."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('market_signals.py')

    def test_no_less_than_today_filter_for_dedup(self):
        """The old pattern 'existing_df[...dt.normalize() < today]' used for dedup must be gone."""
        # The old buggy line was:
        #   existing_historical = existing_df[existing_df[date_column].dt.normalize() < today]
        # followed by dedup against existing_historical only.
        # The fix should not filter to < today for dedup purposes.
        self.assertNotIn('existing_historical = existing_df[existing_df[date_column].dt.normalize() < today]',
                         self.src)

    def test_dedup_against_existing_without_today(self):
        """The fix should dedup new data against existing dates excluding today (so today can be replaced)."""
        self.assertIn('existing_without_today', self.src)

    def test_today_row_excluded_before_dedup(self):
        """Today's row should be removed from existing before dedup so it can be refreshed."""
        self.assertIn('!= today', self.src)


class AppendToCsvTestBase(unittest.TestCase):
    """Base class with temp directory and tracker setup."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tracker = MarketSignalsTracker.__new__(MarketSignalsTracker)
        self.today = pd.Timestamp.now().normalize()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def csv_path(self, name='test.csv'):
        return Path(self.tmp_dir) / name

    def make_df(self, dates, values):
        return pd.DataFrame({'date': pd.to_datetime(dates), 'value': values})

    def read_csv(self, path):
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['date'])
        return df


class TestFutureDateDedup(AppendToCsvTestBase):
    """Core bug: future-dated projections must not be duplicated on re-append."""

    def test_future_dates_not_duplicated_on_second_run(self):
        """Running append_to_csv twice with same future data should not create duplicates."""
        path = self.csv_path()
        future_dates = ['2035-01-01', '2035-04-01', '2035-07-01', '2036-01-01']
        future_values = [4.2, 4.19, 4.18, 4.17]
        df = self.make_df(future_dates, future_values)

        self.tracker.append_to_csv(df, path)
        self.tracker.append_to_csv(df, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 4, "Should have exactly 4 rows, no duplicates")
        self.assertEqual(result['date'].nunique(), 4)

    def test_future_dates_idempotent_after_three_runs(self):
        """Even after 3 collection runs, no duplicates for future dates."""
        path = self.csv_path()
        df = self.make_df(['2035-01-01', '2036-10-01'], [4.2, 4.16])

        for _ in range(3):
            self.tracker.append_to_csv(df, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 2)

    def test_mixed_past_and_future_no_duplicates(self):
        """CSV with past + future dates: re-appending same data creates no duplicates."""
        path = self.csv_path()
        past_dates = ['2020-01-01', '2020-04-01']
        future_dates = ['2035-01-01', '2036-01-01']
        all_dates = past_dates + future_dates
        all_values = [4.4, 4.35, 4.2, 4.17]
        df = self.make_df(all_dates, all_values)

        self.tracker.append_to_csv(df, path)
        self.tracker.append_to_csv(df, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 4)

    def test_only_future_dates_csv(self):
        """CSV with ONLY future-dated rows — append should not duplicate any."""
        path = self.csv_path()
        df = self.make_df(['2030-01-01', '2031-01-01', '2032-01-01'], [1.0, 2.0, 3.0])

        self.tracker.append_to_csv(df, path)
        self.tracker.append_to_csv(df, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 3)


class TestTodayDataUpdate(AppendToCsvTestBase):
    """Today's data should be replaceable (updated, not duplicated)."""

    def test_today_data_updated_not_duplicated(self):
        """Re-appending today's data should replace it, not add a second row."""
        path = self.csv_path()
        today_str = self.today.strftime('%Y-%m-%d')

        df1 = self.make_df([today_str], [100.0])
        self.tracker.append_to_csv(df1, path)

        df2 = self.make_df([today_str], [101.0])
        self.tracker.append_to_csv(df2, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 1, "Should have exactly 1 row for today")
        self.assertAlmostEqual(result['value'].iloc[0], 101.0,
                               msg="Today's value should be updated to latest")

    def test_today_plus_future_both_handled(self):
        """Mixed today + future dates: today updated, future not duplicated."""
        path = self.csv_path()
        today_str = self.today.strftime('%Y-%m-%d')
        dates = [today_str, '2035-01-01', '2036-01-01']
        values = [100.0, 4.2, 4.17]

        df = self.make_df(dates, values)
        self.tracker.append_to_csv(df, path)

        # Second run with updated today value
        df2 = self.make_df(dates, [101.0, 4.2, 4.17])
        self.tracker.append_to_csv(df2, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 3, "3 dates: today + 2 future")
        today_row = result[result['date'].dt.normalize() == self.today]
        self.assertEqual(len(today_row), 1)
        self.assertAlmostEqual(today_row['value'].iloc[0], 101.0)

    def test_mixed_past_today_future(self):
        """CSV with past + today + future dates — all three categories handled correctly."""
        path = self.csv_path()
        today_str = self.today.strftime('%Y-%m-%d')

        # First write: past + future
        initial = self.make_df(['2020-01-01', '2020-07-01', '2035-01-01'], [4.4, 4.35, 4.2])
        self.tracker.append_to_csv(initial, path)

        # Second write: past + today + future (same past/future, new today)
        update = self.make_df(['2020-01-01', '2020-07-01', today_str, '2035-01-01'],
                              [4.4, 4.35, 100.0, 4.2])
        self.tracker.append_to_csv(update, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 4, "3 existing + 1 new (today)")
        self.assertEqual(result['date'].nunique(), 4)


class TestHistoricalDataPreservation(AppendToCsvTestBase):
    """Historical data must not be lost or altered."""

    def test_historical_data_unchanged(self):
        """Existing historical rows stay intact after append with future data."""
        path = self.csv_path()
        historical = self.make_df(['2020-01-01', '2020-04-01', '2020-07-01'], [4.4, 4.35, 4.3])
        self.tracker.append_to_csv(historical, path)

        # Append future data
        future = self.make_df(['2020-01-01', '2020-04-01', '2020-07-01', '2035-01-01'],
                              [4.4, 4.35, 4.3, 4.2])
        self.tracker.append_to_csv(future, path)

        result = self.read_csv(path)
        hist_rows = result[result['date'] < self.today]
        self.assertEqual(len(hist_rows), 3)
        self.assertAlmostEqual(hist_rows.iloc[0]['value'], 4.4)
        self.assertAlmostEqual(hist_rows.iloc[1]['value'], 4.35)
        self.assertAlmostEqual(hist_rows.iloc[2]['value'], 4.3)

    def test_new_genuinely_new_dates_appended(self):
        """Genuinely new dates (not in existing) are correctly appended."""
        path = self.csv_path()
        initial = self.make_df(['2020-01-01', '2020-04-01'], [4.4, 4.35])
        self.tracker.append_to_csv(initial, path)

        with_new = self.make_df(['2020-01-01', '2020-04-01', '2020-07-01'], [4.4, 4.35, 4.3])
        self.tracker.append_to_csv(with_new, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 3, "Should have 3 rows: 2 existing + 1 new")

    def test_subset_of_existing_no_rows_added(self):
        """New data that is a subset of existing data — no rows appended."""
        path = self.csv_path()
        initial = self.make_df(['2020-01-01', '2020-04-01', '2020-07-01'], [4.4, 4.35, 4.3])
        self.tracker.append_to_csv(initial, path)

        subset = self.make_df(['2020-01-01', '2020-04-01'], [4.4, 4.35])
        self.tracker.append_to_csv(subset, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 3, "No new rows should be added")


class TestSortOrder(AppendToCsvTestBase):
    """Sort order must be preserved after append."""

    def test_dates_ascending_after_append(self):
        """CSV should be sorted by date ascending after every append."""
        path = self.csv_path()
        initial = self.make_df(['2020-07-01', '2020-01-01'], [4.3, 4.4])
        self.tracker.append_to_csv(initial, path)

        result = self.read_csv(path)
        dates = result['date'].tolist()
        self.assertEqual(dates, sorted(dates))

    def test_sort_preserved_after_future_append(self):
        """Sort order correct with mix of past + future after append."""
        path = self.csv_path()
        initial = self.make_df(['2020-01-01', '2035-01-01'], [4.4, 4.2])
        self.tracker.append_to_csv(initial, path)

        update = self.make_df(['2020-01-01', '2025-06-01', '2035-01-01'], [4.4, 4.25, 4.2])
        self.tracker.append_to_csv(update, path)

        result = self.read_csv(path)
        dates = result['date'].tolist()
        self.assertEqual(dates, sorted(dates))


class TestEdgeCases(AppendToCsvTestBase):
    """Edge cases: empty/None input, first-time creation."""

    def test_none_input_no_crash(self):
        """None passed to append_to_csv — early return, no crash."""
        path = self.csv_path()
        self.tracker.append_to_csv(None, path)
        self.assertFalse(path.exists())

    def test_empty_dataframe_no_crash(self):
        """Empty DataFrame passed to append_to_csv — early return, no crash."""
        path = self.csv_path()
        self.tracker.append_to_csv(pd.DataFrame(), path)
        self.assertFalse(path.exists())

    def test_first_time_creation(self):
        """First-time CSV creation (no existing file) still works correctly."""
        path = self.csv_path()
        df = self.make_df(['2020-01-01', '2035-01-01'], [4.4, 4.2])
        self.tracker.append_to_csv(df, path)

        self.assertTrue(path.exists())
        result = self.read_csv(path)
        self.assertEqual(len(result), 2)

    def test_partial_overlap_only_new_added(self):
        """New data partially overlapping existing — only genuinely new rows appended."""
        path = self.csv_path()
        initial = self.make_df(['2020-01-01', '2020-04-01', '2035-01-01'], [4.4, 4.35, 4.2])
        self.tracker.append_to_csv(initial, path)

        overlap = self.make_df(['2020-04-01', '2020-07-01', '2035-01-01'], [4.35, 4.3, 4.2])
        self.tracker.append_to_csv(overlap, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 4, "3 original + 1 new (2020-07-01)")


class TestNrouSimulation(AppendToCsvTestBase):
    """Simulate the actual NROU scenario that triggered the bug."""

    def test_nrou_projection_scenario(self):
        """Simulate NROU: historical data + CBO projections out to 2036."""
        path = self.csv_path('natural_unemployment_rate.csv')

        # Initial collection: historical + projections
        dates = ['2020-01-01', '2020-04-01', '2020-07-01',
                 '2034-01-01', '2035-01-01', '2036-01-01', '2036-10-01']
        values = [4.41, 4.41, 4.51, 4.22, 4.20, 4.18, 4.16]
        df = self.make_df(dates, values)
        self.tracker.append_to_csv(df, path)

        # Second collection run (same data) — should NOT create duplicates
        self.tracker.append_to_csv(df, path)

        result = self.read_csv(path)
        self.assertEqual(len(result), 7, "No duplicates after second run")

        # Third collection run
        self.tracker.append_to_csv(df, path)
        result = self.read_csv(path)
        self.assertEqual(len(result), 7, "No duplicates after third run")

        # Verify no duplicate dates
        dupes = result[result.duplicated(subset='date', keep=False)]
        self.assertEqual(len(dupes), 0, "Zero duplicate date rows")

    def test_nrou_resample_no_crash(self):
        """After fix, resample().ffill() should work without ValueError."""
        path = self.csv_path('natural_unemployment_rate.csv')

        dates = ['2020-01-01', '2020-04-01', '2020-07-01', '2020-10-01',
                 '2035-01-01', '2036-01-01', '2036-10-01']
        values = [4.41, 4.41, 4.51, 4.50, 4.20, 4.18, 4.16]
        df = self.make_df(dates, values)

        # Simulate two collection runs
        self.tracker.append_to_csv(df, path)
        self.tracker.append_to_csv(df, path)

        result = self.read_csv(path)
        result = result.set_index('date')

        # This would crash with ValueError before the fix
        try:
            resampled = result.resample('MS').ffill()
            self.assertGreater(len(resampled), 0)
        except ValueError as e:
            self.fail(f"resample().ffill() crashed with: {e}")


class TestExistingDataClean(unittest.TestCase):
    """Verify that the actual natural_unemployment_rate.csv has no duplicates."""

    def test_no_duplicates_in_nrou_csv(self):
        """natural_unemployment_rate.csv should have zero duplicate date rows."""
        csv_path = os.path.join(SIGNALTRACKERS_DIR, 'data', 'natural_unemployment_rate.csv')
        if not os.path.exists(csv_path):
            self.skipTest("natural_unemployment_rate.csv not found")
        df = pd.read_csv(csv_path)
        dupes = df[df.duplicated(subset='date', keep=False)]
        self.assertEqual(len(dupes), 0, f"Found {len(dupes)} duplicate date rows")

    def test_no_duplicates_in_gdppot_csv(self):
        """gdp_potential.csv should have zero duplicate date rows (if it exists)."""
        csv_path = os.path.join(SIGNALTRACKERS_DIR, 'data', 'gdp_potential.csv')
        if not os.path.exists(csv_path):
            self.skipTest("gdp_potential.csv not found")
        df = pd.read_csv(csv_path)
        dupes = df[df.duplicated(subset='date', keep=False)]
        self.assertEqual(len(dupes), 0, f"Found {len(dupes)} duplicate date rows")


if __name__ == '__main__':
    unittest.main()
