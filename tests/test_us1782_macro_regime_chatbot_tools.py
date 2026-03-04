"""
Tests for US-178.2: Wire Macro Regime & Recession Probability into Chatbot Tool Layer.

Verifies:
- METRIC_INFO contains entries for macro_regime and recession_probability
- execute_list_metrics() includes both in its response
- execute_get_metric_data('macro_regime') reads cache and returns regime data
- execute_get_metric_data('recession_probability') reads cache and returns model data
- Both functions return a clean error dict when cache is absent
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Static / structural tests
# ---------------------------------------------------------------------------


class TestStaticStructure(unittest.TestCase):
    """Source-code checks: new functions and METRIC_INFO keys must be present."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('metric_tools.py')

    def test_get_macro_regime_data_function_defined(self):
        self.assertIn('def _get_macro_regime_data(', self.src)

    def test_get_recession_probability_data_function_defined(self):
        self.assertIn('def _get_recession_probability_data(', self.src)

    def test_macro_regime_special_case_in_execute_get(self):
        self.assertIn("metric_id == 'macro_regime'", self.src)

    def test_recession_probability_special_case_in_execute_get(self):
        self.assertIn("metric_id == 'recession_probability'", self.src)

    def test_macro_regime_in_metric_info(self):
        self.assertIn("'macro_regime'", self.src)

    def test_recession_probability_in_metric_info(self):
        self.assertIn("'recession_probability'", self.src)

    def test_cache_based_metrics_set_defined(self):
        self.assertIn('cache_based_metrics', self.src)

    def test_macro_regime_included_in_cache_set(self):
        self.assertIn("'macro_regime'", self.src)

    def test_regime_implications_imported_in_get_macro_regime(self):
        self.assertIn('REGIME_IMPLICATIONS', self.src)


# ---------------------------------------------------------------------------
# Functional tests: METRIC_INFO and list_available_metrics
# ---------------------------------------------------------------------------


class TestMetricInfoEntries(unittest.TestCase):
    """METRIC_INFO must contain the two new macro metrics."""

    def setUp(self):
        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        self.mt = mt

    def test_macro_regime_in_metric_info(self):
        self.assertIn('macro_regime', self.mt.METRIC_INFO)

    def test_recession_probability_in_metric_info(self):
        self.assertIn('recession_probability', self.mt.METRIC_INFO)

    def test_macro_regime_category(self):
        self.assertEqual(self.mt.METRIC_INFO['macro_regime']['category'], 'Macro')

    def test_recession_probability_category(self):
        self.assertEqual(self.mt.METRIC_INFO['recession_probability']['category'], 'Macro')

    def test_macro_regime_description_not_empty(self):
        self.assertTrue(len(self.mt.METRIC_INFO['macro_regime']['description']) > 10)

    def test_recession_probability_description_not_empty(self):
        self.assertTrue(len(self.mt.METRIC_INFO['recession_probability']['description']) > 10)


class TestListMetricsIncludesNewMetrics(unittest.TestCase):
    """execute_list_metrics() must include macro_regime and recession_probability."""

    def setUp(self):
        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        self.mt = mt

    def test_macro_regime_in_list_metrics(self):
        result = json.loads(self.mt.execute_list_metrics())
        all_ids = [
            m['id']
            for metrics in result['metrics_by_category'].values()
            for m in metrics
        ]
        self.assertIn('macro_regime', all_ids)

    def test_recession_probability_in_list_metrics(self):
        result = json.loads(self.mt.execute_list_metrics())
        all_ids = [
            m['id']
            for metrics in result['metrics_by_category'].values()
            for m in metrics
        ]
        self.assertIn('recession_probability', all_ids)


# ---------------------------------------------------------------------------
# Functional tests: execute_get_metric_data — macro_regime
# ---------------------------------------------------------------------------


SAMPLE_REGIME_CACHE = {
    'state': 'Bull',
    'confidence': 'High',
    'trend': 'improving',
    'updated_at': '2026-03-04T10:00:00+00:00',
    'confidence_history': [0.7, 0.8, 0.9],
    'confidence_sparkline_points': [0.7, 0.8, 0.9],
}

SAMPLE_RECESSION_CACHE = {
    'ny_fed': 12.3,
    'ny_fed_lower': 0.0,
    'ny_fed_upper': 25.3,
    'ny_fed_date': '2026-02-01',
    'ny_fed_risk': 'Low',
    'ny_fed_css': 'low',
    'chauvet_piger': 8.5,
    'chauvet_piger_date': '2026-01-01',
    'chauvet_piger_risk': 'Low',
    'chauvet_piger_css': 'low',
    'richmond_sos': 22.0,
    'richmond_sos_date': '2026-01-01',
    'richmond_sos_risk': 'Elevated',
    'richmond_sos_css': 'elevated',
    'divergence_pp': 13.5,
}


class TestGetMacroRegimeWithCache(unittest.TestCase):
    """execute_get_metric_data('macro_regime') with a valid cache file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cache_path = Path(self.tmpdir) / 'macro_regime_cache.json'
        cache_path.write_text(json.dumps(SAMPLE_REGIME_CACHE))

        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        mt.DATA_DIR = Path(self.tmpdir)
        self.mt = mt

    def test_returns_valid_json(self):
        result = self.mt.execute_get_metric_data('macro_regime')
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)

    def test_no_error_key(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertNotIn('error', result)

    def test_metric_id(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertEqual(result['metric_id'], 'macro_regime')

    def test_state_returned(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertEqual(result['state'], 'Bull')

    def test_confidence_returned(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertEqual(result['confidence'], 'High')

    def test_trend_returned(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertEqual(result['trend'], 'improving')

    def test_updated_at_returned(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertIn('updated_at', result)

    def test_implications_key_present(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertIn('implications', result)

    def test_implications_is_dict(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertIsInstance(result['implications'], dict)

    def test_description_present(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertIn('description', result)

    def test_category_present(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertEqual(result['category'], 'Macro')


class TestGetMacroRegimeCacheMissing(unittest.TestCase):
    """execute_get_metric_data('macro_regime') when cache does not exist."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        mt.DATA_DIR = Path(self.tmpdir)
        self.mt = mt

    def test_returns_error_when_cache_absent(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertIn('error', result)

    def test_error_message_mentions_cache(self):
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        self.assertIn('cache', result['error'].lower())


# ---------------------------------------------------------------------------
# Functional tests: execute_get_metric_data — recession_probability
# ---------------------------------------------------------------------------


class TestGetRecessionProbabilityWithCache(unittest.TestCase):
    """execute_get_metric_data('recession_probability') with a valid cache file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        cache_path = Path(self.tmpdir) / 'recession_probability_cache.json'
        cache_path.write_text(json.dumps(SAMPLE_RECESSION_CACHE))

        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        mt.DATA_DIR = Path(self.tmpdir)
        self.mt = mt

    def test_returns_valid_json(self):
        result = self.mt.execute_get_metric_data('recession_probability')
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)

    def test_no_error_key(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertNotIn('error', result)

    def test_metric_id(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertEqual(result['metric_id'], 'recession_probability')

    def test_data_key_present(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('data', result)

    def test_ny_fed_present_in_data(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('ny_fed', result['data'])

    def test_ny_fed_value(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertAlmostEqual(result['data']['ny_fed'], 12.3)

    def test_ny_fed_risk_present(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertEqual(result['data']['ny_fed_risk'], 'Low')

    def test_chauvet_piger_present(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('chauvet_piger', result['data'])

    def test_richmond_sos_present(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('richmond_sos', result['data'])

    def test_richmond_sos_risk_elevated(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertEqual(result['data']['richmond_sos_risk'], 'Elevated')

    def test_description_present(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('description', result)

    def test_category_present(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertEqual(result['category'], 'Macro')


class TestGetRecessionProbabilityCacheMissing(unittest.TestCase):
    """execute_get_metric_data('recession_probability') when cache does not exist."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        mt.DATA_DIR = Path(self.tmpdir)
        self.mt = mt

    def test_returns_error_when_cache_absent(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('error', result)

    def test_error_message_mentions_cache(self):
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        self.assertIn('cache', result['error'].lower())


# ---------------------------------------------------------------------------
# execute_metric_function dispatcher tests
# ---------------------------------------------------------------------------


class TestExecuteMetricFunctionDispatch(unittest.TestCase):
    """execute_metric_function correctly dispatches to the new handlers."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        import importlib
        import signaltrackers.metric_tools as mt
        importlib.reload(mt)
        mt.DATA_DIR = Path(self.tmpdir)
        self.mt = mt

    def test_dispatches_macro_regime(self):
        result = json.loads(self.mt.execute_metric_function(
            'get_metric_data', {'metric_id': 'macro_regime'}
        ))
        # Cache absent → error; either way it must be a dict, not a CSV 404
        self.assertIsInstance(result, dict)
        if 'error' in result:
            self.assertIn('cache', result['error'].lower())

    def test_dispatches_recession_probability(self):
        result = json.loads(self.mt.execute_metric_function(
            'get_metric_data', {'metric_id': 'recession_probability'}
        ))
        self.assertIsInstance(result, dict)
        if 'error' in result:
            self.assertIn('cache', result['error'].lower())

    def test_macro_regime_not_treated_as_csv_miss(self):
        """macro_regime should NOT return the generic 'not found' error."""
        result = json.loads(self.mt.execute_get_metric_data('macro_regime'))
        if 'error' in result:
            self.assertNotIn('not found', result['error'])

    def test_recession_probability_not_treated_as_csv_miss(self):
        """recession_probability should NOT return the generic 'not found' error."""
        result = json.loads(self.mt.execute_get_metric_data('recession_probability'))
        if 'error' in result:
            self.assertNotIn('not found', result['error'])


if __name__ == '__main__':
    unittest.main()
