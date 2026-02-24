"""
Static verification tests for US-4.1.1: Backend — Macro regime calculation engine.

These tests verify the implementation without requiring a live Flask server,
external API calls, or a trained k-means model. They inspect source files and
exercise the pure-Python logic directly.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def read_file(path):
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# regime_config.py tests
# ---------------------------------------------------------------------------

class TestRegimeConfigFileExists(unittest.TestCase):
    """regime_config.py must exist."""

    def test_regime_config_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'regime_config.py')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


class TestRegimeConfigStructure(unittest.TestCase):
    """regime_config.py must define all required constants."""

    def setUp(self):
        import regime_config as rc
        self.rc = rc

    def test_valid_regimes_tuple(self):
        """VALID_REGIMES must be a tuple of exactly 4 states."""
        self.assertIsInstance(self.rc.VALID_REGIMES, tuple)
        self.assertEqual(len(self.rc.VALID_REGIMES), 4)
        self.assertIn('Bull', self.rc.VALID_REGIMES)
        self.assertIn('Neutral', self.rc.VALID_REGIMES)
        self.assertIn('Bear', self.rc.VALID_REGIMES)
        self.assertIn('Recession Watch', self.rc.VALID_REGIMES)

    def test_regime_metadata_has_all_states(self):
        """REGIME_METADATA must have entries for all four regime states."""
        for state in self.rc.VALID_REGIMES:
            self.assertIn(state, self.rc.REGIME_METADATA, f"Missing state: {state}")

    def test_regime_metadata_has_required_keys(self):
        """Each entry in REGIME_METADATA must have icon, css_class, summary, highlighted_signals."""
        for state, meta in self.rc.REGIME_METADATA.items():
            self.assertIn('icon', meta, f"{state} missing 'icon'")
            self.assertIn('css_class', meta, f"{state} missing 'css_class'")
            self.assertIn('summary', meta, f"{state} missing 'summary'")
            self.assertIn('highlighted_signals', meta, f"{state} missing 'highlighted_signals'")

    def test_regime_summaries_max_200_chars(self):
        """Plain-language summaries must be ≤ 200 characters."""
        for state, meta in self.rc.REGIME_METADATA.items():
            summary = meta['summary']
            self.assertLessEqual(
                len(summary), 200,
                f"{state} summary too long ({len(summary)} chars): {summary}"
            )

    def test_highlighted_signals_count(self):
        """Each regime must have 2–4 highlighted signals."""
        for state, meta in self.rc.REGIME_METADATA.items():
            signals = meta['highlighted_signals']
            self.assertGreaterEqual(len(signals), 2, f"{state}: too few highlighted signals")
            self.assertLessEqual(len(signals), 4, f"{state}: too many highlighted signals")

    def test_highlighted_signals_never_empty_list(self):
        """Highlighted signals must never be an empty list."""
        for state, meta in self.rc.REGIME_METADATA.items():
            self.assertTrue(len(meta['highlighted_signals']) > 0, f"{state} has no signals")

    def test_category_regime_context_has_all_categories(self):
        """CATEGORY_REGIME_CONTEXT must have 6 categories."""
        expected = {'Credit', 'Rates', 'Equities', 'Dollar', 'Crypto', 'Safe Havens'}
        actual = set(self.rc.CATEGORY_REGIME_CONTEXT.keys())
        self.assertEqual(actual, expected)

    def test_category_regime_context_has_all_regimes(self):
        """Each category must have context for all 4 regimes."""
        for category, contexts in self.rc.CATEGORY_REGIME_CONTEXT.items():
            for state in self.rc.VALID_REGIMES:
                self.assertIn(state, contexts, f"Missing regime '{state}' in category '{category}'")

    def test_category_context_strings_max_100_chars(self):
        """Category context sentences must be ≤ 100 characters."""
        for category, contexts in self.rc.CATEGORY_REGIME_CONTEXT.items():
            for state, sentence in contexts.items():
                self.assertLessEqual(
                    len(sentence), 100,
                    f"{category}/{state} context too long ({len(sentence)}): {sentence}"
                )

    def test_category_context_count(self):
        """Must have exactly 6 × 4 = 24 category context strings."""
        count = sum(len(v) for v in self.rc.CATEGORY_REGIME_CONTEXT.values())
        self.assertEqual(count, 24)

    def test_signal_annotations_max_100_chars(self):
        """Signal annotation strings must be ≤ 100 characters."""
        for signal, annotations in self.rc.SIGNAL_REGIME_ANNOTATIONS.items():
            for state, annotation in annotations.items():
                self.assertLessEqual(
                    len(annotation), 100,
                    f"{signal}/{state} annotation too long ({len(annotation)}): {annotation}"
                )

    def test_signal_annotations_has_all_four_regimes(self):
        """Each signal annotation entry must have all four regime states."""
        for signal, annotations in self.rc.SIGNAL_REGIME_ANNOTATIONS.items():
            for state in self.rc.VALID_REGIMES:
                self.assertIn(
                    state, annotations,
                    f"Signal '{signal}' missing annotation for regime '{state}'"
                )

    def test_regime_category_relevance_has_all_states(self):
        """REGIME_CATEGORY_RELEVANCE must have entries for all four regime states."""
        for state in self.rc.VALID_REGIMES:
            self.assertIn(state, self.rc.REGIME_CATEGORY_RELEVANCE)

    def test_regime_category_relevance_values_are_lists(self):
        """REGIME_CATEGORY_RELEVANCE values must be lists of category names."""
        valid_categories = {'Credit', 'Rates', 'Equities', 'Dollar', 'Crypto', 'Safe Havens'}
        for state, categories in self.rc.REGIME_CATEGORY_RELEVANCE.items():
            self.assertIsInstance(categories, list, f"{state} relevance is not a list")
            for cat in categories:
                self.assertIn(cat, valid_categories, f"Unknown category '{cat}' in {state}")

    def test_regime_category_relevance_not_all_six(self):
        """Not all six categories should be flagged for Bull or Neutral (threshold-based)."""
        for state in ('Bull', 'Neutral'):
            categories = self.rc.REGIME_CATEGORY_RELEVANCE[state]
            self.assertLess(
                len(categories), 6,
                f"{state} regime should not flag all 6 categories"
            )

    def test_regime_classification_features_defined(self):
        """REGIME_CLASSIFICATION_FEATURES must map metric keys to FRED series IDs."""
        features = self.rc.REGIME_CLASSIFICATION_FEATURES
        self.assertIsInstance(features, dict)
        self.assertGreater(len(features), 0)
        for key, fred_id in features.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(fred_id, str)
            self.assertTrue(len(fred_id) > 0, f"Empty FRED ID for {key}")


# ---------------------------------------------------------------------------
# regime_detection.py tests
# ---------------------------------------------------------------------------

class TestRegimeDetectionFileExists(unittest.TestCase):
    """regime_detection.py must exist."""

    def test_regime_detection_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'regime_detection.py')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


class TestGetMacroRegime(unittest.TestCase):
    """get_macro_regime() must return correct structure or None."""

    def test_returns_none_when_no_cache(self):
        """get_macro_regime() returns None when cache file doesn't exist."""
        from regime_detection import get_macro_regime, CACHE_FILE
        with patch.object(Path, 'exists', return_value=False):
            result = get_macro_regime()
        self.assertIsNone(result)

    def test_returns_dict_when_cache_exists(self):
        """get_macro_regime() returns a dict from cache."""
        import regime_detection as rd
        sample = {
            'state': 'Bear',
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'confidence': 'High',
        }
        with patch.object(rd, '_load_cache', return_value=sample):
            result = rd.get_macro_regime()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['state'], 'Bear')

    def test_returned_dict_has_required_keys(self):
        """get_macro_regime() result must have state, updated_at, confidence."""
        import regime_detection as rd
        sample = {
            'state': 'Neutral',
            'updated_at': '2026-02-24T00:00:00+00:00',
            'confidence': 'Medium',
        }
        with patch.object(rd, '_load_cache', return_value=sample):
            result = rd.get_macro_regime()
        self.assertIn('state', result)
        self.assertIn('updated_at', result)
        self.assertIn('confidence', result)

    def test_state_must_be_valid_regime(self):
        """state in cached dict must be one of the four valid regimes."""
        import regime_detection as rd
        from regime_config import VALID_REGIMES
        sample = {
            'state': 'Bull',
            'updated_at': '2026-02-24T00:00:00+00:00',
            'confidence': 'Low',
        }
        with patch.object(rd, '_load_cache', return_value=sample):
            result = rd.get_macro_regime()
        self.assertIn(result['state'], VALID_REGIMES)

    def test_confidence_is_none_or_valid_string(self):
        """confidence field must be 'High', 'Medium', 'Low', or None."""
        import regime_detection as rd
        for conf in ('High', 'Medium', 'Low', None):
            sample = {
                'state': 'Bull',
                'updated_at': '2026-02-24T00:00:00+00:00',
                'confidence': conf,
            }
            with patch.object(rd, '_load_cache', return_value=sample):
                result = rd.get_macro_regime()
            self.assertEqual(result['confidence'], conf)


class TestRuleBasedRegime(unittest.TestCase):
    """_rule_based_regime() must produce correct classifications."""

    def setUp(self):
        from regime_detection import _rule_based_regime
        self.classify = _rule_based_regime

    def test_high_stress_is_recession(self):
        """Very high HY spread + inverted curve → Recession Watch."""
        result = self.classify({
            'high_yield_spread': 750,   # >600 → +3
            'yield_curve_10y2y': -1.0,  # <-0.5 → +3
            'nfci': 0.8,               # >0.5 → +2
        })
        self.assertEqual(result, 'Recession Watch')

    def test_moderate_stress_is_bear(self):
        """Moderate stress indicators → Bear."""
        result = self.classify({
            'high_yield_spread': 500,   # >450 → +2
            'yield_curve_10y2y': -0.3,  # <0 → +1
            'nfci': 0.3,               # >0 → +1
        })
        self.assertEqual(result, 'Bear')

    def test_low_stress_is_bull(self):
        """Low stress indicators → Bull."""
        result = self.classify({
            'high_yield_spread': 250,   # <300 → 0
            'yield_curve_10y2y': 1.5,   # >0 → 0
            'nfci': -0.5,              # <0 → 0
            'initial_claims': 200,     # <300 → 0
        })
        self.assertEqual(result, 'Bull')

    def test_handles_missing_fields_gracefully(self):
        """_rule_based_regime must handle missing dict keys without raising."""
        # Partial data — should still return a valid state
        result = self.classify({'high_yield_spread': 400})
        self.assertIn(result, ('Bull', 'Neutral', 'Bear', 'Recession Watch'))

    def test_returns_one_of_four_valid_states(self):
        """Rule-based classification always returns one of the four valid states."""
        from regime_config import VALID_REGIMES
        for scenario in [
            {},
            {'high_yield_spread': 300},
            {'yield_curve_10y2y': -0.5},
            {'high_yield_spread': 700, 'yield_curve_10y2y': -1.5},
        ]:
            result = self.classify(scenario)
            self.assertIn(result, VALID_REGIMES, f"Invalid state '{result}' for {scenario}")


class TestUpdateMacroRegime(unittest.TestCase):
    """update_macro_regime() must update the cache correctly."""

    def test_returns_none_on_no_data(self):
        """update_macro_regime() returns None when no data is available."""
        import regime_detection as rd
        with patch.object(rd, '_load_feature_data', return_value=None):
            result = rd.update_macro_regime()
        self.assertIsNone(result)

    def test_returns_regime_dict_on_success(self):
        """update_macro_regime() returns a valid regime dict on success."""
        import pandas as pd
        import numpy as np
        import regime_detection as rd
        from regime_config import VALID_REGIMES

        # Generate synthetic 5-year monthly data for all features
        dates = pd.date_range('2021-01-31', periods=60, freq='ME')
        np.random.seed(42)
        synthetic_data = pd.DataFrame({
            'high_yield_spread': np.abs(np.random.normal(400, 100, 60)),
            'yield_curve_10y2y': np.random.normal(0, 0.5, 60),
            'nfci': np.random.normal(0, 0.3, 60),
            'initial_claims': np.abs(np.random.normal(250, 50, 60)),
            'fed_funds_rate': np.random.uniform(0, 5.5, 60),
        }, index=dates)

        with patch.object(rd, '_load_feature_data', return_value=synthetic_data), \
             patch.object(rd, '_save_cache', return_value=None):
            result = rd.update_macro_regime()

        self.assertIsNotNone(result)
        self.assertIn('state', result)
        self.assertIn('updated_at', result)
        self.assertIn('confidence', result)
        self.assertIn(result['state'], VALID_REGIMES)

    def test_regime_calculation_isolates_failure(self):
        """Failure in regime calculation should not crash — returns None."""
        import regime_detection as rd
        with patch.object(rd, '_load_feature_data', side_effect=RuntimeError('test error')):
            result = rd.update_macro_regime()
        self.assertIsNone(result)

    def test_cache_is_written_on_success(self):
        """update_macro_regime() must call _save_cache on success."""
        import pandas as pd
        import numpy as np
        import regime_detection as rd

        dates = pd.date_range('2021-01-31', periods=60, freq='ME')
        np.random.seed(7)
        synthetic_data = pd.DataFrame({
            'high_yield_spread': np.abs(np.random.normal(350, 80, 60)),
            'yield_curve_10y2y': np.random.normal(0.2, 0.4, 60),
            'nfci': np.random.normal(-0.1, 0.3, 60),
            'initial_claims': np.abs(np.random.normal(230, 40, 60)),
            'fed_funds_rate': np.random.uniform(0, 5, 60),
        }, index=dates)

        with patch.object(rd, '_load_feature_data', return_value=synthetic_data), \
             patch.object(rd, '_save_cache') as mock_save:
            rd.update_macro_regime()

        mock_save.assert_called_once()
        saved_arg = mock_save.call_args[0][0]
        self.assertIn('state', saved_arg)
        self.assertIn('updated_at', saved_arg)


class TestCacheRoundTrip(unittest.TestCase):
    """_save_cache and _load_cache must round-trip correctly."""

    def test_cache_round_trip(self):
        """Saved regime dict should be identical to loaded dict."""
        import regime_detection as rd

        sample = {
            'state': 'Neutral',
            'updated_at': '2026-02-24T12:00:00+00:00',
            'confidence': 'High',
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cache = rd.CACHE_FILE
            rd.CACHE_FILE = Path(tmpdir) / 'macro_regime_cache.json'
            try:
                rd._save_cache(sample)
                loaded = rd._load_cache()
            finally:
                rd.CACHE_FILE = original_cache

        self.assertEqual(loaded, sample)

    def test_load_cache_returns_none_on_missing_file(self):
        """_load_cache returns None when the cache file does not exist."""
        import regime_detection as rd
        original = rd.CACHE_FILE
        rd.CACHE_FILE = Path('/tmp/nonexistent_regime_cache_xyz.json')
        try:
            result = rd._load_cache()
        finally:
            rd.CACHE_FILE = original
        self.assertIsNone(result)

    def test_load_cache_handles_corrupt_json(self):
        """_load_cache returns None on malformed JSON."""
        import regime_detection as rd
        with tempfile.TemporaryDirectory() as tmpdir:
            corrupt_path = Path(tmpdir) / 'macro_regime_cache.json'
            corrupt_path.write_text('NOT VALID JSON {{{')
            original = rd.CACHE_FILE
            rd.CACHE_FILE = corrupt_path
            try:
                result = rd._load_cache()
            finally:
                rd.CACHE_FILE = original
        self.assertIsNone(result)


class TestGetRegimeConfig(unittest.TestCase):
    """get_regime_config() must return complete config for all regimes."""

    def test_returns_dict_with_all_keys(self):
        """get_regime_config() must return all required config keys."""
        from regime_detection import get_regime_config
        config = get_regime_config()
        required = {
            'REGIME_METADATA', 'CATEGORY_REGIME_CONTEXT',
            'SIGNAL_REGIME_ANNOTATIONS', 'REGIME_CATEGORY_RELEVANCE', 'VALID_REGIMES'
        }
        for key in required:
            self.assertIn(key, config, f"Missing key: {key}")

    def test_valid_regimes_has_four_states(self):
        """VALID_REGIMES in returned config must have exactly four states."""
        from regime_detection import get_regime_config
        config = get_regime_config()
        self.assertEqual(len(config['VALID_REGIMES']), 4)


class TestDashboardIntegration(unittest.TestCase):
    """dashboard.py must import and call regime functions."""

    def test_regime_detection_imported_in_dashboard(self):
        """dashboard.py must import get_macro_regime and update_macro_regime."""
        dashboard_path = os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        content = read_file(dashboard_path)
        self.assertIn('get_macro_regime', content)
        self.assertIn('update_macro_regime', content)

    def test_inject_macro_regime_context_processor_present(self):
        """dashboard.py must have inject_macro_regime context processor."""
        dashboard_path = os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        content = read_file(dashboard_path)
        self.assertIn('inject_macro_regime', content)
        self.assertIn('@app.context_processor', content)

    def test_update_macro_regime_called_in_run_data_collection(self):
        """run_data_collection must call update_macro_regime."""
        dashboard_path = os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        content = read_file(dashboard_path)
        self.assertIn('update_macro_regime()', content)

    def test_macro_regime_in_context(self):
        """inject_macro_regime must inject 'macro_regime' key."""
        dashboard_path = os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        content = read_file(dashboard_path)
        self.assertIn("'macro_regime'", content)


class TestSecurityConstraints(unittest.TestCase):
    """Security checks for the regime detection implementation."""

    def test_no_user_input_in_regime_calculation(self):
        """regime_detection.py must not use request object or user input."""
        detection_path = os.path.join(SIGNALTRACKERS_DIR, 'regime_detection.py')
        content = read_file(detection_path)
        # No Flask request object — this is a backend-only calculation
        self.assertNotIn('from flask import', content,
                         "regime_detection.py should not import Flask directly")

    def test_static_config_has_no_eval_calls(self):
        """regime_config.py must not contain eval() or exec() calls."""
        config_path = os.path.join(SIGNALTRACKERS_DIR, 'regime_config.py')
        content = read_file(config_path)
        self.assertNotIn('eval(', content)
        self.assertNotIn('exec(', content)

    def test_detection_has_no_eval_calls(self):
        """regime_detection.py must not contain eval() or exec() calls."""
        detection_path = os.path.join(SIGNALTRACKERS_DIR, 'regime_detection.py')
        content = read_file(detection_path)
        self.assertNotIn('eval(', content)
        self.assertNotIn('exec(', content)


class TestRequirementsUpdated(unittest.TestCase):
    """requirements.txt must include scikit-learn."""

    def test_scikit_learn_in_requirements(self):
        """requirements.txt must include scikit-learn."""
        req_path = os.path.join(SIGNALTRACKERS_DIR, 'requirements.txt')
        content = read_file(req_path)
        self.assertIn('scikit-learn', content)


if __name__ == '__main__':
    unittest.main()
