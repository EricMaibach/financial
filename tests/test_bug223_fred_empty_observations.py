"""
Tests for Bug #223: market_signals.py crashes on empty FRED observations.

fetch_fred_data() must return None gracefully when FRED returns an empty
observations list or one that lacks the expected date/value columns, instead
of raising a KeyError that propagates up and aborts the entire data-collection
pipeline.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Static / structural tests
# ---------------------------------------------------------------------------


class TestFetchFredDataGuardPresent(unittest.TestCase):
    """fetch_fred_data() must have an empty-DataFrame guard before column selection."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('market_signals.py')

    def test_empty_guard_present(self):
        """Guard clause 'df.empty' must appear before df[['date', 'value']]."""
        self.assertIn('df.empty', self.src,
                      "Empty DataFrame guard missing from market_signals.py")

    def test_column_guard_present(self):
        """Guard must check 'date' not in df.columns."""
        self.assertIn("'date' not in df.columns", self.src,
                      "Column presence check for 'date' missing")

    def test_value_column_guard_present(self):
        """Guard must check 'value' not in df.columns."""
        self.assertIn("'value' not in df.columns", self.src,
                      "Column presence check for 'value' missing")

    def test_guard_returns_none(self):
        """Guard must return None, not raise."""
        src = self.src
        guard_pos = src.find("'date' not in df.columns")
        self.assertGreater(guard_pos, -1)
        # Within 200 chars after the guard, 'return None' must appear
        window = src[guard_pos:guard_pos + 200]
        self.assertIn('return None', window,
                      "Guard clause must 'return None' when columns are missing")


# ---------------------------------------------------------------------------
# Behavioural unit tests (mock requests)
# ---------------------------------------------------------------------------


class TestFetchFredDataEmptyObservations(unittest.TestCase):
    """fetch_fred_data() returns None, does not raise, for empty observations."""

    @classmethod
    def setUpClass(cls):
        from market_signals import MarketSignalsTracker
        cls.collector = MarketSignalsTracker.__new__(MarketSignalsTracker)
        cls.collector.fred_api_key = 'test_key'
        cls.collector.fred_base_url = 'https://api.stlouisfed.org/fred'

    def _mock_response(self, payload):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = payload
        return mock_resp

    @patch('market_signals.requests.get')
    def test_empty_observations_list_returns_none(self, mock_get):
        """FRED returns [] observations — must return None, not raise KeyError."""
        mock_get.return_value = self._mock_response({'observations': []})
        result = self.collector.fetch_fred_data('FEDFUNDS', start_date='2025-01-01')
        self.assertIsNone(result)

    @patch('market_signals.requests.get')
    def test_no_observations_key_returns_none(self, mock_get):
        """FRED response missing 'observations' key — must return None."""
        mock_get.return_value = self._mock_response({'count': 0})
        result = self.collector.fetch_fred_data('FEDFUNDS')
        self.assertIsNone(result)

    @patch('market_signals.requests.get')
    def test_observations_missing_date_column_returns_none(self, mock_get):
        """Observations rows without 'date' key — must return None."""
        mock_get.return_value = self._mock_response(
            {'observations': [{'realtime_start': '2025-01-01', 'value': '5.33'}]}
        )
        result = self.collector.fetch_fred_data('FEDFUNDS')
        self.assertIsNone(result)

    @patch('market_signals.requests.get')
    def test_observations_missing_value_column_returns_none(self, mock_get):
        """Observations rows without 'value' key — must return None."""
        mock_get.return_value = self._mock_response(
            {'observations': [{'date': '2025-01-01', 'realtime_start': '2025-01-01'}]}
        )
        result = self.collector.fetch_fred_data('FEDFUNDS')
        self.assertIsNone(result)

    @patch('market_signals.requests.get')
    def test_valid_observations_returns_dataframe(self, mock_get):
        """Normal non-empty observations must still return a valid DataFrame."""
        mock_get.return_value = self._mock_response({
            'observations': [
                {'date': '2025-01-01', 'value': '5.33'},
                {'date': '2025-01-02', 'value': '5.33'},
            ]
        })
        import pandas as pd
        result = self.collector.fetch_fred_data('FEDFUNDS')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('date', result.columns)
        self.assertIn('value', result.columns)
        self.assertEqual(len(result), 2)

    @patch('market_signals.requests.get')
    def test_empty_observations_does_not_raise(self, mock_get):
        """Critically: must NOT raise any exception on empty observations."""
        mock_get.return_value = self._mock_response({'observations': []})
        try:
            self.collector.fetch_fred_data('BOPGSTB', start_date='2026-03-06')
        except Exception as e:
            self.fail(f"fetch_fred_data raised unexpectedly: {e}")


if __name__ == '__main__':
    unittest.main()
