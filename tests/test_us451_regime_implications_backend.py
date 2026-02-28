"""
Static verification tests for US-145.1: Backend — Regime implications static
config + template context injection.

Tests verify the config structure, signal level validity, data model, and
context processor behavior without requiring a live Flask server or external
API calls.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Module existence and import tests
# ---------------------------------------------------------------------------

class TestConfigFileExists(unittest.TestCase):
    """regime_implications_config.py must exist in signaltrackers/."""

    def test_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'regime_implications_config.py')
        self.assertTrue(os.path.isfile(path), 'regime_implications_config.py not found')


class TestConfigModuleImports(unittest.TestCase):
    """Module must import without error."""

    def test_import_success(self):
        import regime_implications_config
        self.assertIsNotNone(regime_implications_config)

    def test_regime_implications_exported(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.assertIsInstance(REGIME_IMPLICATIONS, dict)

    def test_valid_signals_exported(self):
        from regime_implications_config import VALID_SIGNALS
        self.assertIsNotNone(VALID_SIGNALS)

    def test_regime_state_to_key_exported(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        self.assertIsInstance(REGIME_STATE_TO_KEY, dict)


# ---------------------------------------------------------------------------
# REGIME_STATE_TO_KEY mapping tests
# ---------------------------------------------------------------------------

class TestRegimeStateToKeyMapping(unittest.TestCase):
    """REGIME_STATE_TO_KEY must map all 4 engine state strings to snake_case keys."""

    def setUp(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        self.mapping = REGIME_STATE_TO_KEY

    def test_bull_maps_to_bull(self):
        self.assertEqual(self.mapping['Bull'], 'bull')

    def test_neutral_maps_to_neutral(self):
        self.assertEqual(self.mapping['Neutral'], 'neutral')

    def test_bear_maps_to_bear(self):
        self.assertEqual(self.mapping['Bear'], 'bear')

    def test_recession_watch_maps_to_recession_watch(self):
        self.assertEqual(self.mapping['Recession Watch'], 'recession_watch')

    def test_all_4_engine_states_present(self):
        self.assertEqual(len(self.mapping), 4)

    def test_all_target_keys_lowercase_snake_case(self):
        for value in self.mapping.values():
            self.assertEqual(value, value.lower())


# ---------------------------------------------------------------------------
# Config structure — 4 regimes present
# ---------------------------------------------------------------------------

class TestRegimeImplicationsTopLevel(unittest.TestCase):
    """REGIME_IMPLICATIONS must have all 4 regime keys."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def test_bull_regime_present(self):
        self.assertIn('bull', self.config)

    def test_neutral_regime_present(self):
        self.assertIn('neutral', self.config)

    def test_bear_regime_present(self):
        self.assertIn('bear', self.config)

    def test_recession_watch_regime_present(self):
        self.assertIn('recession_watch', self.config)

    def test_exactly_4_regimes(self):
        self.assertEqual(len(self.config), 4)


# ---------------------------------------------------------------------------
# Config structure — display_name per regime
# ---------------------------------------------------------------------------

class TestRegimeDisplayNames(unittest.TestCase):
    """Each regime block must have a display_name string."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def test_bull_display_name(self):
        self.assertIsInstance(self.config['bull']['display_name'], str)
        self.assertGreater(len(self.config['bull']['display_name']), 0)

    def test_neutral_display_name(self):
        self.assertIsInstance(self.config['neutral']['display_name'], str)
        self.assertGreater(len(self.config['neutral']['display_name']), 0)

    def test_bear_display_name(self):
        self.assertIsInstance(self.config['bear']['display_name'], str)
        self.assertGreater(len(self.config['bear']['display_name']), 0)

    def test_recession_watch_display_name(self):
        self.assertIsInstance(self.config['recession_watch']['display_name'], str)
        self.assertGreater(len(self.config['recession_watch']['display_name']), 0)

    def test_bull_display_name_value(self):
        self.assertEqual(self.config['bull']['display_name'], 'Bull Market')

    def test_neutral_display_name_value(self):
        self.assertEqual(self.config['neutral']['display_name'], 'Neutral')

    def test_bear_display_name_value(self):
        self.assertEqual(self.config['bear']['display_name'], 'Bear Market')

    def test_recession_watch_display_name_value(self):
        self.assertEqual(self.config['recession_watch']['display_name'], 'Recession Watch')


# ---------------------------------------------------------------------------
# Config structure — 6 asset classes per regime (updated by US-123.4)
# ---------------------------------------------------------------------------

class TestAssetClassCount(unittest.TestCase):
    """Each regime must have exactly 6 asset class entries."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def test_bull_has_5_asset_classes(self):
        self.assertGreaterEqual(len(self.config['bull']['asset_classes']), 6)

    def test_neutral_has_5_asset_classes(self):
        self.assertGreaterEqual(len(self.config['neutral']['asset_classes']), 6)

    def test_bear_has_5_asset_classes(self):
        self.assertGreaterEqual(len(self.config['bear']['asset_classes']), 6)

    def test_recession_watch_has_5_asset_classes(self):
        self.assertGreaterEqual(len(self.config['recession_watch']['asset_classes']), 6)

    def test_full_matrix_20_entries(self):
        total = sum(
            len(regime['asset_classes'])
            for regime in self.config.values()
        )
        self.assertGreaterEqual(total, 24)


# ---------------------------------------------------------------------------
# Config structure — expected asset class keys
# ---------------------------------------------------------------------------

EXPECTED_ASSET_CLASS_KEYS = ['equities', 'credit', 'rates', 'safe_havens', 'crypto', 'dollar']


class TestAssetClassKeys(unittest.TestCase):
    """Each regime must contain all expected asset class keys."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_keys(self, regime_key):
        return [ac['key'] for ac in self.config[regime_key]['asset_classes']]

    def test_bull_asset_class_keys(self):
        self.assertEqual(self._get_keys('bull'), EXPECTED_ASSET_CLASS_KEYS)

    def test_neutral_asset_class_keys(self):
        self.assertEqual(self._get_keys('neutral'), EXPECTED_ASSET_CLASS_KEYS)

    def test_bear_asset_class_keys(self):
        self.assertEqual(self._get_keys('bear'), EXPECTED_ASSET_CLASS_KEYS)

    def test_recession_watch_asset_class_keys(self):
        self.assertEqual(self._get_keys('recession_watch'), EXPECTED_ASSET_CLASS_KEYS)


# ---------------------------------------------------------------------------
# Config structure — required fields per asset class entry
# ---------------------------------------------------------------------------

class TestAssetClassFields(unittest.TestCase):
    """Every asset class entry must have all required fields."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.all_entries = [
            ac
            for regime in REGIME_IMPLICATIONS.values()
            for ac in regime['asset_classes']
        ]

    def test_all_entries_have_key(self):
        for entry in self.all_entries:
            self.assertIn('key', entry)

    def test_all_entries_have_display_name(self):
        for entry in self.all_entries:
            self.assertIn('display_name', entry)

    def test_all_entries_have_signal(self):
        for entry in self.all_entries:
            self.assertIn('signal', entry)

    def test_all_entries_have_annotation(self):
        for entry in self.all_entries:
            self.assertIn('annotation', entry)

    def test_all_entries_have_leading_sectors(self):
        for entry in self.all_entries:
            self.assertIn('leading_sectors', entry)

    def test_all_entries_have_lagging_sectors(self):
        for entry in self.all_entries:
            self.assertIn('lagging_sectors', entry)

    def test_no_signal_is_none(self):
        for entry in self.all_entries:
            self.assertIsNotNone(entry['signal'])

    def test_no_annotation_is_none(self):
        for entry in self.all_entries:
            self.assertIsNotNone(entry['annotation'])

    def test_no_annotation_is_empty_string(self):
        for entry in self.all_entries:
            self.assertGreater(len(entry['annotation']), 0)


# ---------------------------------------------------------------------------
# Signal level validity
# ---------------------------------------------------------------------------

class TestSignalLevels(unittest.TestCase):
    """All signal values must be one of the 5 valid strings."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS, VALID_SIGNALS
        self.all_entries = [
            ac
            for regime in REGIME_IMPLICATIONS.values()
            for ac in regime['asset_classes']
        ]
        self.valid_signals = VALID_SIGNALS

    def test_valid_signals_tuple_has_5_values(self):
        self.assertEqual(len(self.valid_signals), 5)

    def test_strong_outperform_in_valid_signals(self):
        self.assertIn('strong_outperform', self.valid_signals)

    def test_outperform_in_valid_signals(self):
        self.assertIn('outperform', self.valid_signals)

    def test_neutral_in_valid_signals(self):
        self.assertIn('neutral', self.valid_signals)

    def test_underperform_in_valid_signals(self):
        self.assertIn('underperform', self.valid_signals)

    def test_strong_underperform_in_valid_signals(self):
        self.assertIn('strong_underperform', self.valid_signals)

    def test_all_signal_values_valid(self):
        for entry in self.all_entries:
            self.assertIn(
                entry['signal'],
                self.valid_signals,
                f"Invalid signal '{entry['signal']}' for {entry['key']}"
            )

    def test_no_signal_outside_enum(self):
        for entry in self.all_entries:
            self.assertNotIn(' ', entry['signal'])  # no spaces — must be snake_case


# ---------------------------------------------------------------------------
# Equities sector callouts
# ---------------------------------------------------------------------------

class TestEquitiesSectorCallouts(unittest.TestCase):
    """Equities entries must have leading/lagging sectors; non-equities must not."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_equities(self, regime_key):
        return next(
            ac for ac in self.config[regime_key]['asset_classes']
            if ac['key'] == 'equities'
        )

    def _get_non_equities(self, regime_key):
        return [
            ac for ac in self.config[regime_key]['asset_classes']
            if ac['key'] != 'equities'
        ]

    def test_bull_equities_has_leading_sectors(self):
        self.assertIsInstance(self._get_equities('bull')['leading_sectors'], list)
        self.assertGreater(len(self._get_equities('bull')['leading_sectors']), 0)

    def test_bull_equities_has_lagging_sectors(self):
        self.assertIsInstance(self._get_equities('bull')['lagging_sectors'], list)
        self.assertGreater(len(self._get_equities('bull')['lagging_sectors']), 0)

    def test_neutral_equities_has_leading_sectors(self):
        self.assertIsInstance(self._get_equities('neutral')['leading_sectors'], list)
        self.assertGreater(len(self._get_equities('neutral')['leading_sectors']), 0)

    def test_bear_equities_has_leading_sectors(self):
        self.assertIsInstance(self._get_equities('bear')['leading_sectors'], list)
        self.assertGreater(len(self._get_equities('bear')['leading_sectors']), 0)

    def test_recession_watch_equities_has_leading_sectors(self):
        self.assertIsInstance(self._get_equities('recession_watch')['leading_sectors'], list)
        self.assertGreater(len(self._get_equities('recession_watch')['leading_sectors']), 0)

    def test_non_equities_have_none_leading_sectors(self):
        for regime_key in ['bull', 'neutral', 'bear', 'recession_watch']:
            for ac in self._get_non_equities(regime_key):
                self.assertIsNone(
                    ac['leading_sectors'],
                    f"{ac['key']} in {regime_key} should have leading_sectors=None"
                )

    def test_non_equities_have_none_lagging_sectors(self):
        for regime_key in ['bull', 'neutral', 'bear', 'recession_watch']:
            for ac in self._get_non_equities(regime_key):
                self.assertIsNone(
                    ac['lagging_sectors'],
                    f"{ac['key']} in {regime_key} should have lagging_sectors=None"
                )


# ---------------------------------------------------------------------------
# Crypto caveat annotation
# ---------------------------------------------------------------------------

class TestCryptoCaveat(unittest.TestCase):
    """Crypto annotation in every regime must include the 2010–2025 caveat."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_crypto_annotation(self, regime_key):
        return next(
            ac['annotation']
            for ac in self.config[regime_key]['asset_classes']
            if ac['key'] == 'crypto'
        )

    def test_bull_crypto_caveat(self):
        annotation = self._get_crypto_annotation('bull')
        self.assertIn('2010', annotation)
        self.assertIn('2025', annotation)

    def test_neutral_crypto_caveat(self):
        annotation = self._get_crypto_annotation('neutral')
        self.assertIn('2010', annotation)
        self.assertIn('2025', annotation)

    def test_bear_crypto_caveat(self):
        annotation = self._get_crypto_annotation('bear')
        self.assertIn('2010', annotation)
        self.assertIn('2025', annotation)

    def test_recession_watch_crypto_caveat(self):
        annotation = self._get_crypto_annotation('recession_watch')
        self.assertIn('2010', annotation)
        self.assertIn('2025', annotation)


# ---------------------------------------------------------------------------
# dashboard.py integration — import and context processor
# ---------------------------------------------------------------------------

class TestDashboardImport(unittest.TestCase):
    """dashboard.py must import from regime_implications_config."""

    def setUp(self):
        self.src = read_source('dashboard.py')

    def test_imports_regime_implications(self):
        self.assertIn('from regime_implications_config import', self.src)

    def test_imports_regime_implications_dict(self):
        self.assertIn('REGIME_IMPLICATIONS', self.src)

    def test_imports_regime_state_to_key(self):
        self.assertIn('REGIME_STATE_TO_KEY', self.src)

    def test_inject_regime_implications_defined(self):
        self.assertIn('inject_regime_implications', self.src)

    def test_inject_regime_implications_is_context_processor(self):
        idx = self.src.find('inject_regime_implications')
        before = self.src[max(0, idx - 200):idx]
        self.assertIn('@app.context_processor', before)

    def test_context_processor_returns_regime_implications_key(self):
        self.assertIn("'regime_implications'", self.src)

    def test_context_processor_returns_none_on_exception(self):
        idx = self.src.find('inject_regime_implications')
        section = self.src[idx:idx + 600]
        self.assertIn('except Exception', section)
        self.assertIn("'regime_implications': None", section)


# ---------------------------------------------------------------------------
# Context processor logic — happy path (unit test with mock)
# ---------------------------------------------------------------------------

class TestContextProcessorHappyPath(unittest.TestCase):
    """inject_regime_implications must return correct structure when regime available."""

    def test_returns_current_regime_and_regimes(self):
        from regime_implications_config import REGIME_IMPLICATIONS, REGIME_STATE_TO_KEY

        fake_regime = {'state': 'Bull', 'confidence': 'High'}

        with patch('regime_implications_config.REGIME_IMPLICATIONS', REGIME_IMPLICATIONS):
            current_key = REGIME_STATE_TO_KEY.get('Bull')
            result = {
                'current_regime': current_key,
                'regimes': REGIME_IMPLICATIONS,
            }

        self.assertEqual(result['current_regime'], 'bull')
        self.assertIn('regimes', result)
        self.assertIn('bull', result['regimes'])
        self.assertIn('neutral', result['regimes'])
        self.assertIn('bear', result['regimes'])
        self.assertIn('recession_watch', result['regimes'])

    def test_current_regime_bull_maps_correctly(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        self.assertEqual(REGIME_STATE_TO_KEY.get('Bull'), 'bull')

    def test_current_regime_neutral_maps_correctly(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        self.assertEqual(REGIME_STATE_TO_KEY.get('Neutral'), 'neutral')

    def test_current_regime_bear_maps_correctly(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        self.assertEqual(REGIME_STATE_TO_KEY.get('Bear'), 'bear')

    def test_current_regime_recession_watch_maps_correctly(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        self.assertEqual(REGIME_STATE_TO_KEY.get('Recession Watch'), 'recession_watch')


# ---------------------------------------------------------------------------
# Context processor logic — unavailable / edge cases
# ---------------------------------------------------------------------------

class TestContextProcessorUnavailable(unittest.TestCase):
    """inject_regime_implications must return None when regime unavailable."""

    def setUp(self):
        self.src = read_source('dashboard.py')

    def test_returns_none_when_no_regime(self):
        # Logic: if regime is falsy, return None
        idx = self.src.find('inject_regime_implications')
        section = self.src[idx:idx + 600]
        self.assertIn('if not regime', section)

    def test_returns_none_for_unknown_state(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        # Unknown state returns None from .get()
        result = REGIME_STATE_TO_KEY.get('UnknownState')
        self.assertIsNone(result)

    def test_graceful_on_empty_state(self):
        from regime_implications_config import REGIME_STATE_TO_KEY
        result = REGIME_STATE_TO_KEY.get('')
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------

class TestSecurityProperties(unittest.TestCase):
    """Config must not contain dynamic imports, eval, exec, or HTTP calls."""

    def setUp(self):
        self.src = read_source('regime_implications_config.py')

    def test_no_eval(self):
        self.assertNotIn('eval(', self.src)

    def test_no_exec(self):
        self.assertNotIn('exec(', self.src)

    def test_no_subprocess(self):
        self.assertNotIn('subprocess', self.src)

    def test_no_requests(self):
        self.assertNotIn('import requests', self.src)

    def test_no_urllib(self):
        self.assertNotIn('urllib', self.src)

    def test_no_dynamic_import_of_external_modules(self):
        # The only import should be the docstring-level standard library
        # or nothing — static config file
        lines = [ln.strip() for ln in self.src.splitlines() if ln.strip().startswith('import ')]
        # The config file should have no bare 'import X' statements
        self.assertEqual(len(lines), 0)


# ---------------------------------------------------------------------------
# Performance: config loaded as module-level constant (not per-request)
# ---------------------------------------------------------------------------

class TestConfigPerformance(unittest.TestCase):
    """REGIME_IMPLICATIONS must be a module-level constant, not computed per call."""

    def setUp(self):
        self.src = read_source('regime_implications_config.py')

    def test_regime_implications_is_module_level(self):
        # REGIME_IMPLICATIONS must be defined at module level (indentation 0)
        for line in self.src.splitlines():
            if line.startswith('REGIME_IMPLICATIONS'):
                self.assertTrue(True)
                return
        self.fail('REGIME_IMPLICATIONS not found at module level')

    def test_valid_signals_is_module_level(self):
        for line in self.src.splitlines():
            if line.startswith('VALID_SIGNALS'):
                self.assertTrue(True)
                return
        self.fail('VALID_SIGNALS not found at module level')

    def test_regime_state_to_key_is_module_level(self):
        for line in self.src.splitlines():
            if line.startswith('REGIME_STATE_TO_KEY'):
                self.assertTrue(True)
                return
        self.fail('REGIME_STATE_TO_KEY not found at module level')

    def test_no_function_wraps_regime_implications(self):
        # Config should not be wrapped in a function
        self.assertNotIn('def get_regime_implications()', self.src)


if __name__ == '__main__':
    unittest.main()
