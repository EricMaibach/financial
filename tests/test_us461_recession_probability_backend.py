"""
Static verification tests for US-146.1: Backend data layer — fetch and process
three recession probability models.

These tests verify the implementation without requiring a live Flask server,
external API calls, or live market data. They exercise the pure-Python logic
directly and inspect source files for structural correctness.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Module structure tests
# ---------------------------------------------------------------------------


class TestModuleExists(unittest.TestCase):
    """recession_probability.py must exist in signaltrackers/."""

    def test_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'recession_probability.py')
        self.assertTrue(os.path.isfile(path), 'recession_probability.py not found')


class TestModuleImports(unittest.TestCase):
    """Module must import without error."""

    def test_import_success(self):
        import recession_probability
        self.assertIsNotNone(recession_probability)

    def test_get_recession_probability_function(self):
        from recession_probability import get_recession_probability
        self.assertTrue(callable(get_recession_probability))

    def test_update_recession_probability_function(self):
        from recession_probability import update_recession_probability
        self.assertTrue(callable(update_recession_probability))


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants(unittest.TestCase):
    """Required constants must be defined with correct values."""

    def setUp(self):
        import recession_probability as rp
        self.rp = rp

    def test_ny_fed_direct_url_defined(self):
        self.assertTrue(hasattr(self.rp, '_NY_FED_DIRECT_URL'))

    def test_ny_fed_direct_url_is_string(self):
        self.assertIsInstance(self.rp._NY_FED_DIRECT_URL, str)

    def test_ny_fed_direct_url_points_to_ny_fed(self):
        self.assertIn('newyorkfed.org', self.rp._NY_FED_DIRECT_URL)

    def test_ny_fed_direct_url_ends_with_xls(self):
        self.assertIn('allmonth.xls', self.rp._NY_FED_DIRECT_URL)

    def test_ny_fed_series_removed(self):
        # Bug #153: NY_FED_SERIES removed — NY Fed is fetched directly, not from FRED
        self.assertFalse(hasattr(self.rp, 'NY_FED_SERIES'))

    def test_chauvet_piger_series_defined(self):
        self.assertTrue(hasattr(self.rp, 'CHAUVET_PIGER_SERIES'))

    def test_chauvet_piger_series_is_string(self):
        self.assertIsInstance(self.rp.CHAUVET_PIGER_SERIES, str)

    def test_divergence_threshold_defined(self):
        self.assertTrue(hasattr(self.rp, 'DIVERGENCE_THRESHOLD'))

    def test_divergence_threshold_value(self):
        self.assertEqual(self.rp.DIVERGENCE_THRESHOLD, 15.0)

    def test_cache_file_constant_defined(self):
        self.assertTrue(hasattr(self.rp, 'CACHE_FILE'))

    def test_cache_file_in_data_dir(self):
        path = str(self.rp.CACHE_FILE)
        self.assertIn('data', path)
        self.assertIn('recession_probability', path)

    def test_ny_fed_ci_width_defined(self):
        self.assertTrue(hasattr(self.rp, '_NY_FED_CI_WIDTH'))

    def test_ny_fed_ci_width_value(self):
        self.assertAlmostEqual(self.rp._NY_FED_CI_WIDTH, 13.0)


class TestConstantsInSource(unittest.TestCase):
    """Key constants must appear literally in the source file."""

    def setUp(self):
        self.src = read_source('recession_probability.py')

    def test_divergence_threshold_literal(self):
        self.assertIn('DIVERGENCE_THRESHOLD', self.src)

    def test_ny_fed_ci_width_literal(self):
        self.assertIn('13.0', self.src)

    def test_cache_file_literal(self):
        self.assertIn('recession_probability_cache.json', self.src)

    def test_get_recession_probability_defined(self):
        self.assertIn('def get_recession_probability', self.src)

    def test_update_recession_probability_defined(self):
        self.assertIn('def update_recession_probability', self.src)

    def test_ny_fed_direct_url_literal(self):
        self.assertIn('_NY_FED_DIRECT_URL', self.src)
        self.assertIn('allmonth.xls', self.src)

    def test_fetch_ny_fed_direct_function_defined(self):
        self.assertIn('def _fetch_ny_fed_direct', self.src)

    def test_ny_fed_series_constant_removed(self):
        # Bug #153: NY_FED_SERIES no longer present
        self.assertNotIn("NY_FED_SERIES = 'RECPROUSM156N'", self.src)


# ---------------------------------------------------------------------------
# Risk label tests
# ---------------------------------------------------------------------------


class TestRiskLabel(unittest.TestCase):
    """_risk_label() must classify values per spec thresholds."""

    def setUp(self):
        from recession_probability import _risk_label
        self.fn = _risk_label

    def test_zero_is_low(self):
        self.assertEqual(self.fn(0.0), 'Low')

    def test_below_15_is_low(self):
        self.assertEqual(self.fn(14.9), 'Low')

    def test_exactly_15_is_elevated(self):
        self.assertEqual(self.fn(15.0), 'Elevated')

    def test_between_15_and_35_is_elevated(self):
        self.assertEqual(self.fn(28.9), 'Elevated')

    def test_below_35_is_elevated(self):
        self.assertEqual(self.fn(34.9), 'Elevated')

    def test_exactly_35_is_high(self):
        self.assertEqual(self.fn(35.0), 'High')

    def test_above_35_is_high(self):
        self.assertEqual(self.fn(60.0), 'High')

    def test_100_is_high(self):
        self.assertEqual(self.fn(100.0), 'High')


class TestRiskCssClass(unittest.TestCase):
    """_risk_css_class() must return lowercase risk label."""

    def setUp(self):
        from recession_probability import _risk_css_class
        self.fn = _risk_css_class

    def test_low_returns_low(self):
        self.assertEqual(self.fn(5.0), 'low')

    def test_elevated_returns_elevated(self):
        self.assertEqual(self.fn(20.0), 'elevated')

    def test_high_returns_high(self):
        self.assertEqual(self.fn(40.0), 'high')


# ---------------------------------------------------------------------------
# Confidence interval tests
# ---------------------------------------------------------------------------


class TestNyFedConfidenceInterval(unittest.TestCase):
    """NY Fed confidence interval must be ±13pp, clamped to [0, 100]."""

    def _run_update_with_values(self, ny_val, cp_val=None, sos_val=None):
        """Run update_recession_probability with mocked fetch functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (ny_val, '2025-12-01') if ny_val is not None else (None, None)
                            mock_fred.return_value = (cp_val, '2025-12-01') if cp_val is not None else (None, None)
                            mock_sos.return_value = (sos_val, '2026-01-10') if sos_val is not None else (None, None)

                            from recession_probability import update_recession_probability
                            update_recession_probability()

                            if cache_path.exists():
                                with open(cache_path) as f:
                                    return json.load(f)
                            return None

    def test_ny_fed_lower_is_minus_13(self):
        data = self._run_update_with_values(ny_val=28.9, cp_val=4.2)
        self.assertIsNotNone(data)
        self.assertAlmostEqual(data['ny_fed_lower'], 28.9 - 13.0, places=0)

    def test_ny_fed_upper_is_plus_13(self):
        data = self._run_update_with_values(ny_val=28.9, cp_val=4.2)
        self.assertIsNotNone(data)
        self.assertAlmostEqual(data['ny_fed_upper'], 28.9 + 13.0, places=0)

    def test_ny_fed_lower_clamped_to_zero(self):
        # Value 5.0 → lower = max(0, 5.0 - 13.0) = 0.0
        data = self._run_update_with_values(ny_val=5.0, cp_val=4.2)
        self.assertIsNotNone(data)
        self.assertEqual(data['ny_fed_lower'], 0.0)

    def test_ny_fed_upper_clamped_to_100(self):
        # Value 95.0 → upper = min(100, 95.0 + 13.0) = 100.0
        data = self._run_update_with_values(ny_val=95.0, cp_val=4.2)
        self.assertIsNotNone(data)
        self.assertEqual(data['ny_fed_upper'], 100.0)


# ---------------------------------------------------------------------------
# Divergence computation tests
# ---------------------------------------------------------------------------


class TestDivergenceComputation(unittest.TestCase):
    """divergence_pp must equal max–min across all available models (1 decimal)."""

    def _run_update_with_values(self, ny_val, cp_val=None, sos_val=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (ny_val, '2025-12-01') if ny_val is not None else (None, None)
                            mock_fred.return_value = (cp_val, '2025-12-01') if cp_val is not None else (None, None)
                            mock_sos.return_value = (sos_val, '2026-01-10') if sos_val is not None else (None, None)

                            from recession_probability import update_recession_probability
                            update_recession_probability()

                            if cache_path.exists():
                                with open(cache_path) as f:
                                    return json.load(f)
                            return None

    def test_divergence_three_models(self):
        # max=28.9, min=0.8, spread=28.1
        data = self._run_update_with_values(ny_val=28.9, cp_val=4.2, sos_val=0.8)
        self.assertIsNotNone(data)
        self.assertAlmostEqual(data['divergence_pp'], 28.1, places=0)

    def test_divergence_two_models(self):
        # max=28.9, min=4.2, spread=24.7
        data = self._run_update_with_values(ny_val=28.9, cp_val=4.2)
        self.assertIsNotNone(data)
        self.assertAlmostEqual(data['divergence_pp'], 24.7, places=0)

    def test_divergence_single_model_is_zero(self):
        # Only one model available — no spread
        data = self._run_update_with_values(ny_val=28.9, cp_val=None)
        self.assertIsNotNone(data)
        self.assertEqual(data['divergence_pp'], 0.0)

    def test_divergence_same_values_is_zero(self):
        data = self._run_update_with_values(ny_val=10.0, cp_val=10.0)
        self.assertIsNotNone(data)
        self.assertEqual(data['divergence_pp'], 0.0)


# ---------------------------------------------------------------------------
# Graceful degradation tests
# ---------------------------------------------------------------------------


class TestGracefulDegradation(unittest.TestCase):
    """Individual model failures must not prevent others from rendering."""

    def _run_update(self, ny_val, cp_val, sos_val):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (ny_val, '2025-12-01') if ny_val is not None else (None, None)
                            mock_fred.return_value = (cp_val, '2025-12-01') if cp_val is not None else (None, None)
                            mock_sos.return_value = (sos_val, '2026-01-10') if sos_val is not None else (None, None)

                            from recession_probability import update_recession_probability
                            update_recession_probability()

                            if cache_path.exists():
                                with open(cache_path) as f:
                                    return json.load(f)
                            return None

    def test_cp_missing_ny_fed_still_present(self):
        data = self._run_update(ny_val=28.9, cp_val=None, sos_val=None)
        self.assertIsNotNone(data)
        self.assertIn('ny_fed', data)
        self.assertNotIn('chauvet_piger', data)

    def test_ny_fed_missing_cp_still_present(self):
        data = self._run_update(ny_val=None, cp_val=4.2, sos_val=None)
        self.assertIsNotNone(data)
        self.assertIn('chauvet_piger', data)
        self.assertNotIn('ny_fed', data)
        self.assertNotIn('ny_fed_lower', data)
        self.assertNotIn('ny_fed_upper', data)

    def test_sos_present_when_available(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=0.8)
        self.assertIsNotNone(data)
        self.assertIn('richmond_sos', data)

    def test_all_fail_cache_not_written(self):
        # All models return None — cache should NOT be written
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct', return_value=(None, None)):
                    with patch('recession_probability._fetch_fred_latest', return_value=(None, None)):
                        with patch('recession_probability._fetch_richmond_sos', return_value=(None, None)):
                            from recession_probability import update_recession_probability
                            update_recession_probability()
            self.assertFalse(cache_path.exists(), 'Cache should not be written if all models fail')

    def test_ny_fed_fields_absent_when_model_unavailable(self):
        data = self._run_update(ny_val=None, cp_val=4.2, sos_val=None)
        self.assertNotIn('ny_fed', data)
        self.assertNotIn('ny_fed_lower', data)
        self.assertNotIn('ny_fed_upper', data)


# ---------------------------------------------------------------------------
# Risk label per-model field tests
# ---------------------------------------------------------------------------


class TestPerModelRiskFields(unittest.TestCase):
    """Each available model must include risk label and CSS class in cache."""

    def _run_update(self, ny_val, cp_val, sos_val):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (ny_val, '2025-12-01') if ny_val is not None else (None, None)
                            mock_fred.return_value = (cp_val, '2025-12-01') if cp_val is not None else (None, None)
                            mock_sos.return_value = (sos_val, '2026-01-10') if sos_val is not None else (None, None)

                            from recession_probability import update_recession_probability
                            update_recession_probability()

                            if cache_path.exists():
                                with open(cache_path) as f:
                                    return json.load(f)
                            return None

    def test_ny_fed_risk_label_present(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=None)
        self.assertIn('ny_fed_risk', data)
        self.assertEqual(data['ny_fed_risk'], 'Elevated')

    def test_ny_fed_css_class_present(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=None)
        self.assertIn('ny_fed_css', data)
        self.assertEqual(data['ny_fed_css'], 'elevated')

    def test_chauvet_piger_risk_label_low(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=None)
        self.assertEqual(data['chauvet_piger_risk'], 'Low')

    def test_chauvet_piger_css_class_low(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=None)
        self.assertEqual(data['chauvet_piger_css'], 'low')

    def test_richmond_sos_risk_high(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=40.0)
        self.assertEqual(data['richmond_sos_risk'], 'High')

    def test_richmond_sos_css_high(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2, sos_val=40.0)
        self.assertEqual(data['richmond_sos_css'], 'high')


# ---------------------------------------------------------------------------
# Interpretation string tests
# ---------------------------------------------------------------------------


class TestBuildInterpretation(unittest.TestCase):
    """Interpretation string must follow rules-based spec guidance."""

    def setUp(self):
        from recession_probability import _build_interpretation
        self.fn = _build_interpretation

    def test_returns_string(self):
        result = self.fn({'ny_fed': 28.9, 'chauvet_piger': 4.2, 'richmond_sos': 0.8})
        self.assertIsInstance(result, str)

    def test_non_empty(self):
        result = self.fn({'ny_fed': 28.9, 'chauvet_piger': 4.2})
        self.assertGreater(len(result), 10)

    def test_all_none_returns_unavailable_message(self):
        result = self.fn({'ny_fed': None, 'chauvet_piger': None, 'richmond_sos': None})
        self.assertIn('unavailable', result.lower())

    def test_low_risk_interpretation_contains_low_language(self):
        result = self.fn({'ny_fed': 5.0, 'chauvet_piger': 3.0})
        result_lower = result.lower()
        self.assertTrue(
            'low' in result_lower or 'expansion' in result_lower,
            f'Expected low-risk language in: {result}',
        )

    def test_elevated_risk_interpretation_contains_elevated_language(self):
        result = self.fn({'ny_fed': 28.9, 'chauvet_piger': 4.2})
        result_lower = result.lower()
        self.assertTrue(
            'elevated' in result_lower or 'growing' in result_lower or 'uncertainty' in result_lower,
            f'Expected elevated-risk language in: {result}',
        )

    def test_high_risk_interpretation_contains_high_language(self):
        result = self.fn({'ny_fed': 50.0, 'chauvet_piger': 45.0})
        result_lower = result.lower()
        self.assertTrue(
            'high' in result_lower or 'risk' in result_lower,
            f'Expected high-risk language in: {result}',
        )

    def test_divergent_models_noted_in_interpretation(self):
        # 28pp spread between models should trigger divergence note
        result = self.fn({'ny_fed': 30.0, 'chauvet_piger': 2.0})
        result_lower = result.lower()
        self.assertTrue(
            'diverg' in result_lower or 'disagree' in result_lower or 'uncertainty' in result_lower,
            f'Expected divergence language in: {result}',
        )

    def test_aligned_models_noted_in_interpretation(self):
        # Low spread should note alignment
        result = self.fn({'ny_fed': 5.0, 'chauvet_piger': 6.0})
        result_lower = result.lower()
        self.assertTrue(
            'align' in result_lower or 'agree' in result_lower or 'low' in result_lower,
            f'Expected alignment language in: {result}',
        )

    def test_avoids_absolute_language_will(self):
        result = self.fn({'ny_fed': 28.9, 'chauvet_piger': 4.2})
        self.assertNotIn(' will ', result.lower())

    def test_single_model_returns_non_empty(self):
        result = self.fn({'ny_fed': 28.9, 'chauvet_piger': None})
        self.assertGreater(len(result), 10)


# ---------------------------------------------------------------------------
# Mobile summary string tests
# ---------------------------------------------------------------------------


class TestMobileSummary(unittest.TestCase):
    """mobile_summary field must follow spec format."""

    def _run_update(self, ny_val, cp_val, sos_val=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (ny_val, '2025-12-01') if ny_val is not None else (None, None)
                            mock_fred.return_value = (cp_val, '2025-12-01') if cp_val is not None else (None, None)
                            mock_sos.return_value = (sos_val, '2026-01-10') if sos_val is not None else (None, None)

                            from recession_probability import update_recession_probability
                            update_recession_probability()

                            if cache_path.exists():
                                with open(cache_path) as f:
                                    return json.load(f)
                            return None

    def test_mobile_summary_present(self):
        data = self._run_update(ny_val=28.9, cp_val=4.2)
        self.assertIn('mobile_summary', data)

    def test_diverging_summary_label(self):
        # 24.7pp spread ≥ 15 → "diverging"
        data = self._run_update(ny_val=28.9, cp_val=4.2)
        self.assertIn('diverging', data['mobile_summary'].lower())

    def test_aligned_summary_label(self):
        # Small spread → "aligned"
        data = self._run_update(ny_val=5.0, cp_val=6.0)
        self.assertIn('aligned', data['mobile_summary'].lower())

    def test_multiple_risk_levels_shown_with_separator(self):
        # ny_fed=28.9 (Elevated), cp_val=4.2 (Low) → "Low–Elevated"
        data = self._run_update(ny_val=28.9, cp_val=4.2)
        summary = data['mobile_summary']
        self.assertTrue(
            'Low' in summary and 'Elevated' in summary,
            f'Expected both risk levels in: {summary}',
        )

    def test_single_risk_level_no_separator(self):
        # Both low → just "Low"
        data = self._run_update(ny_val=5.0, cp_val=7.0)
        summary = data['mobile_summary']
        self.assertTrue(
            summary.startswith('Low'),
            f'Expected single risk level prefix in: {summary}',
        )


# ---------------------------------------------------------------------------
# Cache round-trip tests
# ---------------------------------------------------------------------------


class TestCacheRoundTrip(unittest.TestCase):
    """get_recession_probability() must return what update_recession_probability() wrote."""

    def test_cache_round_trip_all_models(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (28.9, '2025-12-01')
                            mock_fred.return_value = (4.2, '2025-12-01')
                            mock_sos.return_value = (0.8, '2026-01-10')

                            from recession_probability import (
                                update_recession_probability,
                                get_recession_probability,
                            )
                            update_recession_probability()
                            result = get_recession_probability()

            self.assertIsNotNone(result)
            self.assertAlmostEqual(result['ny_fed'], 28.9, places=0)
            self.assertAlmostEqual(result['chauvet_piger'], 4.2, places=0)
            self.assertAlmostEqual(result['richmond_sos'], 0.8, places=0)
            self.assertIn('updated', result)
            self.assertIn('interpretation', result)

    def test_get_returns_none_when_no_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                from recession_probability import get_recession_probability
                result = get_recession_probability()
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# FRED fetcher structure tests (source inspection)
# ---------------------------------------------------------------------------


class TestFredFetcherSource(unittest.TestCase):
    """_fetch_fred_latest must follow FRED API patterns established in market_signals.py."""

    def setUp(self):
        self.src = read_source('recession_probability.py')

    def test_uses_fred_api_url(self):
        self.assertIn('fred/series/observations', self.src)

    def test_uses_fred_api_key_env_var(self):
        self.assertIn('FRED_API_KEY', self.src)

    def test_has_timeout(self):
        self.assertIn('timeout=', self.src)

    def test_handles_request_exception(self):
        self.assertIn('RequestException', self.src)

    def test_skips_missing_values(self):
        # FRED uses '.' for missing values — must be handled
        self.assertIn("'.'", self.src)

    def test_sort_order_desc_for_latest(self):
        self.assertIn('desc', self.src)


# ---------------------------------------------------------------------------
# Dashboard integration tests (source inspection)
# ---------------------------------------------------------------------------


class TestDashboardIntegration(unittest.TestCase):
    """dashboard.py must import and wire up the recession probability module."""

    def setUp(self):
        self.src = read_source('dashboard.py')

    def test_imports_get_recession_probability(self):
        self.assertIn('get_recession_probability', self.src)

    def test_imports_update_recession_probability(self):
        self.assertIn('update_recession_probability', self.src)

    def test_imports_from_recession_probability_module(self):
        self.assertIn('from recession_probability import', self.src)

    def test_context_processor_defined(self):
        self.assertIn('inject_recession_probability', self.src)

    def test_context_processor_returns_recession_probability(self):
        self.assertIn("'recession_probability'", self.src)

    def test_update_called_in_run_data_collection(self):
        # update_recession_probability() must be called inside run_data_collection
        # Check it appears after the update_macro_regime call (order matters)
        macro_pos = self.src.find('update_macro_regime()')
        recession_pos = self.src.find('update_recession_probability()')
        self.assertGreater(macro_pos, 0, 'update_macro_regime() not found in dashboard.py')
        self.assertGreater(recession_pos, 0, 'update_recession_probability() not found in dashboard.py')
        self.assertGreater(
            recession_pos, macro_pos,
            'update_recession_probability() must be called AFTER update_macro_regime()',
        )

    def test_update_wrapped_in_try_except(self):
        # The update call must be non-fatal (same pattern as update_macro_regime)
        # Check there's a try block close to the update call
        src_slice = self.src[max(0, self.src.find('update_recession_probability()') - 200):]
        self.assertIn('try:', src_slice[:400])

    def test_context_processor_has_try_except(self):
        # inject_recession_probability must have graceful error handling
        proc_src = self.src[self.src.find('def inject_recession_probability'):]
        proc_src = proc_src[:proc_src.find('\ndef ', 5)]
        self.assertIn('try:', proc_src)
        self.assertIn('except', proc_src)


# ---------------------------------------------------------------------------
# Per-model update date tests
# ---------------------------------------------------------------------------


class TestPerModelDates(unittest.TestCase):
    """Per-model update dates must be stored in cache (spec requirement)."""

    def _run_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'recession_probability_cache.json'
            with patch('recession_probability.CACHE_FILE', cache_path):
                with patch('recession_probability._fetch_ny_fed_direct') as mock_ny:
                    with patch('recession_probability._fetch_fred_latest') as mock_fred:
                        with patch('recession_probability._fetch_richmond_sos') as mock_sos:
                            mock_ny.return_value = (28.9, '2025-12-01')
                            mock_fred.return_value = (4.2, '2025-11-01')
                            mock_sos.return_value = (0.8, '2026-01-10')

                            from recession_probability import update_recession_probability
                            update_recession_probability()

                            if cache_path.exists():
                                with open(cache_path) as f:
                                    return json.load(f)
                            return None

    def test_ny_fed_date_stored(self):
        data = self._run_update()
        self.assertIn('ny_fed_date', data)
        self.assertIn('2025-12-01', data['ny_fed_date'])

    def test_chauvet_piger_date_stored(self):
        data = self._run_update()
        self.assertIn('chauvet_piger_date', data)
        self.assertIn('2025-11-01', data['chauvet_piger_date'])

    def test_richmond_sos_date_stored(self):
        data = self._run_update()
        self.assertIn('richmond_sos_date', data)
        self.assertIn('2026-01-10', data['richmond_sos_date'])

    def test_updated_display_formatted(self):
        data = self._run_update()
        self.assertIn('updated', data)
        self.assertGreater(len(data['updated']), 0)


# ---------------------------------------------------------------------------
# Bug #154: Richmond Fed SOS — URL, column, and date parsing fixes
# ---------------------------------------------------------------------------


def _make_richmond_df(date_serial, sos_val, threshold=0.2):
    """Create a mock DataFrame matching the confirmed Richmond Fed file layout.

    Column 0: Date (Excel serial integer)
    Column 1: SOS indicator (float)
    Column 2: Recession Threshold (constant, always 0.2)
    """
    import pandas as pd
    return pd.DataFrame({0: [date_serial], 1: [sos_val], 2: [threshold]})


def _call_fetch_richmond_sos_with_df(mock_df):
    """Call _fetch_richmond_sos() with mocked HTTP response and pandas read_excel."""
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.content = b'fake xlsx bytes'
    with patch('recession_probability.requests.get', return_value=mock_resp):
        with patch('pandas.read_excel', return_value=mock_df):
            from recession_probability import _fetch_richmond_sos
            return _fetch_richmond_sos()


class TestBug154RichmondSosUrl(unittest.TestCase):
    """Bug #154 Fix 1: URL must be updated to the confirmed working endpoint."""

    def setUp(self):
        self.src = read_source('recession_probability.py')

    def test_correct_url_in_source(self):
        self.assertIn('RichmondFedOrg/assets/data/sos_recession_indicator.xlsx', self.src)

    def test_old_broken_url_removed(self):
        self.assertNotIn('survey_of_manufacturing_activity/2024/sos_indicator.xlsx', self.src)

    def test_fetch_makes_get_to_correct_url(self):
        mock_df = _make_richmond_df(46060, 0.058)
        with patch('recession_probability.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = b'fake xlsx bytes'
            mock_get.return_value = mock_resp
            with patch('pandas.read_excel', return_value=mock_df):
                from recession_probability import _fetch_richmond_sos
                _fetch_richmond_sos()
        call_url = mock_get.call_args[0][0]
        self.assertIn('sos_recession_indicator.xlsx', call_url)
        self.assertNotIn('sos_indicator.xlsx', call_url.replace('sos_recession_indicator.xlsx', ''))


class TestBug154RichmondSosColumn(unittest.TestCase):
    """Bug #154 Fix 2: Must read column 1 (SOS indicator), not column -1 (Threshold constant)."""

    def test_returns_sos_value_not_threshold_constant(self):
        # SOS=0.058, Threshold=0.2 — must return 0.058, not 0.2
        val, _ = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.058))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.058, places=3)

    def test_does_not_return_threshold_constant(self):
        val, _ = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.058))
        self.assertIsNotNone(val)
        self.assertNotAlmostEqual(val, 0.2, places=3)

    def test_sos_value_0_point_3_high_risk(self):
        val, _ = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.3))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.3, places=3)

    def test_sos_value_0_point_1_low_risk(self):
        val, _ = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.1))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.1, places=3)

    def test_sos_value_exactly_0_point_2_not_confused_with_threshold(self):
        # SOS of 0.2 is valid data (at recession threshold) — not the Threshold column
        val, _ = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.2, threshold=0.2))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.2, places=3)

    def test_iloc_1_in_source_for_prob_val(self):
        src = read_source('recession_probability.py')
        # Confirm the column-1 read is present in source
        self.assertIn('iloc[1]', src)


class TestBug154RichmondSosDateParsing(unittest.TestCase):
    """Bug #154 Fix 3: Date column is Excel serial integer — must convert to ISO string."""

    def test_serial_46060_converts_to_2026_02_07(self):
        _, date_str = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.058))
        self.assertEqual(date_str, '2026-02-07')

    def test_serial_44927_converts_to_2023_01_01(self):
        _, date_str = _call_fetch_richmond_sos_with_df(_make_richmond_df(44927, 0.1))
        self.assertEqual(date_str, '2023-01-01')

    def test_date_not_raw_serial_string(self):
        _, date_str = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.058))
        self.assertIsNotNone(date_str)
        # Must not return the raw integer as a string
        self.assertNotEqual(date_str, '46060')
        self.assertNotEqual(date_str, '46059')

    def test_date_format_is_yyyy_mm_dd(self):
        _, date_str = _call_fetch_richmond_sos_with_df(_make_richmond_df(46060, 0.058))
        self.assertIsNotNone(date_str)
        import re
        self.assertRegex(date_str, r'^\d{4}-\d{2}-\d{2}$')

    def test_datetime_timedelta_in_source(self):
        src = read_source('recession_probability.py')
        self.assertIn('timedelta', src)
        self.assertIn('1899', src)


class TestBug154RichmondSosGracefulDegradation(unittest.TestCase):
    """Graceful degradation must still work after the Bug #154 fixes."""

    def test_network_error_returns_none_none(self):
        with patch('recession_probability.requests.get',
                   side_effect=Exception('network error')):
            from recession_probability import _fetch_richmond_sos
            val, date_str = _fetch_richmond_sos()
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_http_error_returns_none_none(self):
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError('404')
        with patch('recession_probability.requests.get', return_value=mock_resp):
            from recession_probability import _fetch_richmond_sos
            val, date_str = _fetch_richmond_sos()
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_empty_dataframe_returns_none_none(self):
        import pandas as pd
        empty_df = pd.DataFrame({0: [], 1: [], 2: []})
        val, date_str = _call_fetch_richmond_sos_with_df(empty_df)
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_parsing_exception_returns_none_none(self):
        mock_resp = MagicMock()
        mock_resp.content = b'not a valid xlsx file'
        with patch('recession_probability.requests.get', return_value=mock_resp):
            with patch('pandas.read_excel', side_effect=Exception('parse error')):
                from recession_probability import _fetch_richmond_sos
                val, date_str = _fetch_richmond_sos()
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_nan_sos_rows_skipped(self):
        # Last row has NaN in SOS — should use second-to-last non-null row
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            0: [44927, 46060],
            1: [0.1, np.nan],
            2: [0.2, 0.2],
        })
        val, date_str = _call_fetch_richmond_sos_with_df(df)
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.1, places=3)

    def test_single_row_returns_correctly(self):
        import pandas as pd
        df = pd.DataFrame({0: [44927], 1: [0.07], 2: [0.2]})
        val, date_str = _call_fetch_richmond_sos_with_df(df)
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.07, places=3)


class TestBug154SecurityAndPerformance(unittest.TestCase):
    """Security and performance checks for Bug #154 fixes."""

    def setUp(self):
        self.src = read_source('recession_probability.py')

    def test_url_is_string_constant_not_user_input(self):
        # The URL must be a module-level constant, not built from external input
        self.assertIn('_RICHMOND_SOS_URL', self.src)
        # Constant must be a literal string definition
        self.assertIn("_RICHMOND_SOS_URL = (", self.src)

    def test_timeout_set_on_request(self):
        self.assertIn('timeout=', self.src)

    def test_read_excel_uses_header_0(self):
        self.assertIn('header=0', self.src)


# ---------------------------------------------------------------------------
# Bug #153: NY Fed direct XLS fetcher — replacing FRED-based approach
# ---------------------------------------------------------------------------


def _make_ny_fed_df(rec_prob, date=None):
    """Create a mock DataFrame matching the NY Fed allmonth.xls layout.

    The NY Fed file has a Date column (first) and a Rec_prob column (0.0–1.0 scale).
    """
    import pandas as pd
    from datetime import datetime as dt
    date_val = date if date is not None else dt(2026, 1, 1)
    return pd.DataFrame({'Date': [date_val], 'Rec_prob': [rec_prob]})


def _call_fetch_ny_fed_direct_with_df(mock_df):
    """Call _fetch_ny_fed_direct() with mocked HTTP response and pandas read_excel."""
    mock_resp = MagicMock()
    mock_resp.content = b'fake xls bytes'
    with patch('recession_probability.requests.get', return_value=mock_resp):
        with patch('pandas.read_excel', return_value=mock_df):
            from recession_probability import _fetch_ny_fed_direct
            return _fetch_ny_fed_direct()


class TestBug153NyFedDirectUrl(unittest.TestCase):
    """Bug #153: URL must point directly to the NY Fed XLS file."""

    def setUp(self):
        self.src = read_source('recession_probability.py')

    def test_ny_fed_direct_url_in_source(self):
        self.assertIn('_NY_FED_DIRECT_URL', self.src)

    def test_url_is_ny_fed_domain(self):
        self.assertIn('newyorkfed.org', self.src)

    def test_url_is_allmonth_xls(self):
        self.assertIn('allmonth.xls', self.src)

    def test_ny_fed_series_constant_removed(self):
        # Bug #153: NY_FED_SERIES was pointing to RECPROUSM156N (wrong — that's Chauvet-Piger)
        # It is now removed; NY Fed uses _fetch_ny_fed_direct() instead
        self.assertNotIn("NY_FED_SERIES = ", self.src)

    def test_fetch_ny_fed_direct_function_in_source(self):
        self.assertIn('def _fetch_ny_fed_direct', self.src)

    def test_update_calls_fetch_ny_fed_direct(self):
        # update_recession_probability must call _fetch_ny_fed_direct(), not _fetch_fred_latest(NY_FED_SERIES)
        self.assertIn('_fetch_ny_fed_direct()', self.src)

    def test_rec_prob_column_name_in_source(self):
        self.assertIn('Rec_prob', self.src)

    def test_scale_conversion_in_source(self):
        # Must multiply by 100 to convert 0–1 scale to percent
        self.assertIn('* 100', self.src)

    def test_fetch_makes_get_to_correct_url(self):
        mock_df = _make_ny_fed_df(0.062)
        with patch('recession_probability.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = b'fake xls bytes'
            mock_get.return_value = mock_resp
            with patch('pandas.read_excel', return_value=mock_df):
                from recession_probability import _fetch_ny_fed_direct
                _fetch_ny_fed_direct()
        call_url = mock_get.call_args[0][0]
        self.assertIn('newyorkfed.org', call_url)
        self.assertIn('allmonth.xls', call_url)


class TestBug153NyFedDirectValue(unittest.TestCase):
    """Bug #153: _fetch_ny_fed_direct must convert Rec_prob from 0–1 to percent."""

    def test_converts_0_point_062_to_6_point_2_pct(self):
        val, _ = _call_fetch_ny_fed_direct_with_df(_make_ny_fed_df(0.062))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 6.2, places=1)

    def test_converts_0_point_30_to_30_pct(self):
        val, _ = _call_fetch_ny_fed_direct_with_df(_make_ny_fed_df(0.30))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 30.0, places=1)

    def test_converts_0_point_0_to_0_pct(self):
        val, _ = _call_fetch_ny_fed_direct_with_df(_make_ny_fed_df(0.0))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 0.0, places=1)

    def test_converts_1_point_0_to_100_pct(self):
        val, _ = _call_fetch_ny_fed_direct_with_df(_make_ny_fed_df(1.0))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 100.0, places=1)

    def test_returns_last_row_value(self):
        import pandas as pd
        from datetime import datetime as dt
        df = pd.DataFrame({
            'Date': [dt(2025, 11, 1), dt(2025, 12, 1)],
            'Rec_prob': [0.10, 0.15],
        })
        val, _ = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 15.0, places=1)

    def test_skips_nan_rec_prob_rows(self):
        import pandas as pd
        import numpy as np
        from datetime import datetime as dt
        df = pd.DataFrame({
            'Date': [dt(2025, 11, 1), dt(2025, 12, 1)],
            'Rec_prob': [0.10, np.nan],
        })
        val, _ = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 10.0, places=1)

    def test_value_is_distinct_from_chauvet_piger(self):
        # The key bug: before fix, ny_fed == chauvet_piger (both used same FRED series).
        # After fix, ny_fed comes from a completely different source (_fetch_ny_fed_direct).
        src = read_source('recession_probability.py')
        # Confirm NY Fed fetch no longer uses RECPROUSM156N (Chauvet-Piger's series)
        self.assertNotIn("_fetch_fred_latest(NY_FED_SERIES)", src)
        self.assertIn("_fetch_ny_fed_direct()", src)


class TestBug153NyFedDirectDate(unittest.TestCase):
    """Bug #153: _fetch_ny_fed_direct must return ISO date string from the Date column."""

    def test_timestamp_date_converted_to_iso(self):
        import pandas as pd
        from datetime import datetime as dt
        df = pd.DataFrame({'Date': [dt(2026, 1, 1)], 'Rec_prob': [0.062]})
        _, date_str = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIsNotNone(date_str)
        self.assertIn('2026', date_str)

    def test_date_format_is_yyyy_mm_dd(self):
        import pandas as pd
        import re
        from datetime import datetime as dt
        df = pd.DataFrame({'Date': [dt(2025, 12, 1)], 'Rec_prob': [0.05]})
        _, date_str = _call_fetch_ny_fed_direct_with_df(df)
        self.assertRegex(date_str, r'^\d{4}-\d{2}-\d{2}$')

    def test_latest_row_date_returned(self):
        import pandas as pd
        from datetime import datetime as dt
        df = pd.DataFrame({
            'Date': [dt(2025, 11, 1), dt(2025, 12, 1)],
            'Rec_prob': [0.10, 0.15],
        })
        _, date_str = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIn('2025-12', date_str)


class TestBug153NyFedDirectGracefulDegradation(unittest.TestCase):
    """_fetch_ny_fed_direct must handle all failure modes gracefully."""

    def test_network_error_returns_none_none(self):
        with patch('recession_probability.requests.get',
                   side_effect=Exception('network error')):
            from recession_probability import _fetch_ny_fed_direct
            val, date_str = _fetch_ny_fed_direct()
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_http_error_returns_none_none(self):
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError('404')
        with patch('recession_probability.requests.get', return_value=mock_resp):
            from recession_probability import _fetch_ny_fed_direct
            val, date_str = _fetch_ny_fed_direct()
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_missing_rec_prob_column_returns_none_none(self):
        import pandas as pd
        df = pd.DataFrame({'Date': ['2026-01-01'], 'WrongColumn': [0.06]})
        val, date_str = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_empty_dataframe_returns_none_none(self):
        import pandas as pd
        df = pd.DataFrame({'Date': [], 'Rec_prob': []})
        val, date_str = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_parsing_exception_returns_none_none(self):
        mock_resp = MagicMock()
        mock_resp.content = b'not a valid xls file'
        with patch('recession_probability.requests.get', return_value=mock_resp):
            with patch('pandas.read_excel', side_effect=Exception('parse error')):
                from recession_probability import _fetch_ny_fed_direct
                val, date_str = _fetch_ny_fed_direct()
        self.assertIsNone(val)
        self.assertIsNone(date_str)

    def test_all_rec_prob_nan_returns_none_none(self):
        import pandas as pd
        import numpy as np
        from datetime import datetime as dt
        df = pd.DataFrame({'Date': [dt(2026, 1, 1)], 'Rec_prob': [np.nan]})
        val, date_str = _call_fetch_ny_fed_direct_with_df(df)
        self.assertIsNone(val)
        self.assertIsNone(date_str)


class TestBug153SecurityAndPerformance(unittest.TestCase):
    """Security and performance checks for the NY Fed direct fetcher."""

    def setUp(self):
        self.src = read_source('recession_probability.py')

    def test_url_is_module_level_constant(self):
        self.assertIn('_NY_FED_DIRECT_URL = (', self.src)

    def test_timeout_set_on_ny_fed_request(self):
        # NY Fed file is larger — should use a reasonable timeout
        self.assertIn('timeout=', self.src)

    def test_ny_fed_url_uses_https(self):
        import recession_probability as rp
        self.assertTrue(rp._NY_FED_DIRECT_URL.startswith('https://'))


if __name__ == '__main__':
    unittest.main()
