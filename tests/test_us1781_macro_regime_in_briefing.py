"""
Static verification tests for US-178.1: Wire Macro Regime & Recession Probability
into AI Briefing Pipeline.

Verifies that generate_market_summary() in dashboard.py enriches the market
data summary string with macro regime state and recession probability model
values, and that the enriched string flows through to generate_daily_summary()
in ai_summary.py without changes.

All tests are static (source-code analysis) or use only modules that can be
imported without Flask (regime_detection, recession_probability,
regime_implications_config).
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Static / structural tests — dashboard.py
# ---------------------------------------------------------------------------


class TestStaticImports(unittest.TestCase):
    """Imports for regime and recession enrichment must be present."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_get_macro_regime_imported(self):
        self.assertIn('get_macro_regime', self.src,
                      'get_macro_regime not found in dashboard.py')

    def test_get_recession_probability_imported(self):
        self.assertIn('get_recession_probability', self.src,
                      'get_recession_probability not found in dashboard.py')

    def test_regime_implications_imported(self):
        self.assertIn('REGIME_IMPLICATIONS', self.src,
                      'REGIME_IMPLICATIONS not found in dashboard.py')


class TestStaticEnrichmentBlocks(unittest.TestCase):
    """Enrichment headings and patterns must exist in generate_market_summary()."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_macro_regime_section_heading(self):
        self.assertIn('## MACRO REGIME', self.src,
                      '## MACRO REGIME heading missing from generate_market_summary()')

    def test_recession_section_heading(self):
        self.assertIn('## RECESSION PROBABILITY MODELS', self.src,
                      '## RECESSION PROBABILITY MODELS heading missing')

    def test_regime_confidence_accessed_via_get(self):
        self.assertIn("regime.get('confidence')", self.src,
                      "confidence must be accessed via .get('confidence') — never .format(:.0%)")

    def test_regime_state_unknown_guard(self):
        self.assertIn("'Unknown'", self.src,
                      "Guard for 'Unknown' regime state missing in dashboard.py")

    def test_regime_state_none_guard(self):
        self.assertIn("regime.get('state')", self.src,
                      "regime.get('state') guard missing")

    def test_ny_fed_correct_key(self):
        self.assertIn("recession.get('ny_fed')", self.src,
                      "'ny_fed' key not used — must not use 'ny_fed_12m'")

    def test_ny_fed_12m_not_used_as_key(self):
        self.assertNotIn("recession.get('ny_fed_12m')", self.src,
                         "Wrong key 'ny_fed_12m' found — correct key is 'ny_fed'")

    def test_chauvet_piger_key_used(self):
        self.assertIn("recession.get('chauvet_piger')", self.src,
                      "'chauvet_piger' key not used in recession block")

    def test_richmond_sos_key_used(self):
        self.assertIn("recession.get('richmond_sos')", self.src,
                      "'richmond_sos' key not used in recession block")

    def test_ny_fed_risk_label_used(self):
        self.assertIn("ny_fed_risk", self.src,
                      "ny_fed_risk label not used in recession block")

    def test_chauvet_piger_risk_label_used(self):
        self.assertIn("chauvet_piger_risk", self.src,
                      "chauvet_piger_risk label not used in recession block")

    def test_richmond_sos_risk_label_used(self):
        self.assertIn("richmond_sos_risk", self.src,
                      "richmond_sos_risk label not used in recession block")

    def test_regime_exception_guard(self):
        self.assertIn('pass  # Skip if regime data unavailable', self.src,
                      'Exception guard missing for regime enrichment block')

    def test_recession_exception_guard(self):
        self.assertIn('pass  # Skip if recession data unavailable', self.src,
                      'Exception guard missing for recession enrichment block')

    def test_regime_implications_get_used_safely(self):
        self.assertIn("REGIME_IMPLICATIONS.get(regime", self.src,
                      "REGIME_IMPLICATIONS must be accessed via .get() to avoid KeyError")

    def test_regime_implications_label_in_output(self):
        self.assertIn("Regime implications:", self.src,
                      "'Regime implications:' string not found in generate_market_summary()")

    def test_model_parts_list_used(self):
        self.assertIn('model_parts', self.src,
                      'model_parts list not found in recession enrichment block')


class TestStaticOrdering(unittest.TestCase):
    """Enrichment blocks must appear after prediction markets in source order."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_macro_regime_after_prediction_markets(self):
        pred_pos = self.src.find('## PREDICTION MARKETS (Kalshi)')
        regime_pos = self.src.find('## MACRO REGIME')
        self.assertGreater(regime_pos, pred_pos,
                           '## MACRO REGIME must appear after ## PREDICTION MARKETS in source')

    def test_recession_after_regime(self):
        regime_pos = self.src.find('## MACRO REGIME')
        recession_pos = self.src.find('## RECESSION PROBABILITY MODELS')
        self.assertGreater(recession_pos, regime_pos,
                           '## RECESSION PROBABILITY MODELS must appear after ## MACRO REGIME')

    def test_enrichment_before_return_statement(self):
        """Both blocks must appear before the return of generate_market_summary."""
        pred_pos = self.src.find('## PREDICTION MARKETS (Kalshi)')
        return_pos = self.src.find('return "\\n".join(summary_parts)', pred_pos)
        recession_pos = self.src.find('## RECESSION PROBABILITY MODELS', pred_pos)
        self.assertGreater(return_pos, recession_pos,
                           'Recession block must appear before return in generate_market_summary()')


# ---------------------------------------------------------------------------
# Static tests — ai_summary.py flow unchanged
# ---------------------------------------------------------------------------


class TestAiSummaryFlow(unittest.TestCase):
    """ai_summary.py must pass market_data_summary through to the prompt unchanged."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('ai_summary.py')

    def test_generate_daily_summary_signature(self):
        self.assertIn('def generate_daily_summary(market_data_summary', self.src,
                      'generate_daily_summary must accept market_data_summary as first positional arg')

    def test_market_data_summary_interpolated_in_prompt(self):
        self.assertIn('{market_data_summary}', self.src,
                      '{market_data_summary} interpolation not found in ai_summary.py prompt')


# ---------------------------------------------------------------------------
# Direct module tests — regime_detection.get_macro_regime()
# ---------------------------------------------------------------------------


class TestGetMacroRegimeReturnShape(unittest.TestCase):
    """get_macro_regime() must return the expected dict shape or None."""

    def test_import_succeeds(self):
        from regime_detection import get_macro_regime
        self.assertTrue(callable(get_macro_regime))

    def test_returns_none_when_no_cache(self):
        """Without a cache file, get_macro_regime() returns None."""
        from regime_detection import get_macro_regime
        import regime_detection as rd
        original = rd.CACHE_FILE
        try:
            rd.CACHE_FILE = Path('/tmp/nonexistent_regime_cache_xyz_us1781.json')
            result = get_macro_regime()
            self.assertIsNone(result)
        finally:
            rd.CACHE_FILE = original

    def test_returns_dict_with_expected_keys(self):
        """With a valid cache, returns dict with state, confidence, updated_at."""
        from regime_detection import get_macro_regime
        import regime_detection as rd
        original = rd.CACHE_FILE
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({
                    'state': 'Bear',
                    'confidence': 'High',
                    'updated_at': '2026-03-04T12:00:00+00:00'
                }, f)
                tmp_path = f.name
            rd.CACHE_FILE = Path(tmp_path)
            result = get_macro_regime()
            self.assertIsNotNone(result)
            self.assertIn('state', result)
            self.assertIn('confidence', result)
            self.assertIn('updated_at', result)
        finally:
            rd.CACHE_FILE = original
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_confidence_is_string_not_float(self):
        """confidence must be a string ('High'/'Medium'/'Low') not a float."""
        from regime_detection import get_macro_regime
        import regime_detection as rd
        original = rd.CACHE_FILE
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({
                    'state': 'Bull',
                    'confidence': 'Medium',
                    'updated_at': '2026-03-04T12:00:00+00:00'
                }, f)
                tmp_path = f.name
            rd.CACHE_FILE = Path(tmp_path)
            result = get_macro_regime()
            self.assertIsInstance(result['confidence'], str,
                                  "confidence must be str — cannot use :.0% format specifier on it")
        finally:
            rd.CACHE_FILE = original
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Direct module tests — recession_probability.get_recession_probability()
# ---------------------------------------------------------------------------


class TestGetRecessionProbabilityReturnShape(unittest.TestCase):
    """get_recession_probability() must return the expected dict shape or None."""

    def test_import_succeeds(self):
        from recession_probability import get_recession_probability
        self.assertTrue(callable(get_recession_probability))

    def test_returns_none_when_no_cache(self):
        from recession_probability import get_recession_probability
        import recession_probability as rp
        original = rp.CACHE_FILE
        try:
            rp.CACHE_FILE = Path('/tmp/nonexistent_recession_cache_xyz_us1781.json')
            result = get_recession_probability()
            self.assertIsNone(result)
        finally:
            rp.CACHE_FILE = original

    def test_returns_dict_with_model_keys(self):
        """With a valid cache, returns dict with ny_fed, chauvet_piger, richmond_sos."""
        from recession_probability import get_recession_probability
        import recession_probability as rp
        original = rp.CACHE_FILE
        tmp_path = None
        try:
            cache_data = {
                'updated_at': '2026-03-04T12:00:00+00:00',
                'ny_fed': 18.5,
                'ny_fed_risk': 'Low',
                'chauvet_piger': 22.0,
                'chauvet_piger_risk': 'Elevated',
                'richmond_sos': 12.0,
                'richmond_sos_risk': 'Low',
            }
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(cache_data, f)
                tmp_path = f.name
            rp.CACHE_FILE = Path(tmp_path)
            result = get_recession_probability()
            self.assertIsNotNone(result)
            self.assertIn('ny_fed', result)
            self.assertIn('ny_fed_risk', result)
            self.assertIn('chauvet_piger', result)
            self.assertIn('chauvet_piger_risk', result)
            self.assertIn('richmond_sos', result)
            self.assertIn('richmond_sos_risk', result)
        finally:
            rp.CACHE_FILE = original
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_key_is_ny_fed_not_ny_fed_12m(self):
        """Cache uses 'ny_fed' key — not 'ny_fed_12m'. Callers must use 'ny_fed'."""
        from recession_probability import get_recession_probability
        import recession_probability as rp
        original = rp.CACHE_FILE
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({'ny_fed': 20.0, 'ny_fed_risk': 'Low'}, f)
                tmp_path = f.name
            rp.CACHE_FILE = Path(tmp_path)
            result = get_recession_probability()
            self.assertIn('ny_fed', result,
                          "Key 'ny_fed' must be present — do not rename to 'ny_fed_12m'")
            self.assertNotIn('ny_fed_12m', result,
                             "'ny_fed_12m' must not appear as a cache key")
        finally:
            rp.CACHE_FILE = original
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Direct module tests — REGIME_IMPLICATIONS structure
# ---------------------------------------------------------------------------


class TestRegimeImplicationsStructure(unittest.TestCase):
    """REGIME_IMPLICATIONS must contain the four regime keys used at runtime."""

    @classmethod
    def setUpClass(cls):
        from regime_implications_config import REGIME_IMPLICATIONS
        cls.ri = REGIME_IMPLICATIONS

    def test_bull_key_present(self):
        self.assertIn('bull', self.ri)

    def test_bear_key_present(self):
        self.assertIn('bear', self.ri)

    def test_neutral_key_present(self):
        self.assertIn('neutral', self.ri)

    def test_asset_classes_present(self):
        for regime in ('bull', 'bear', 'neutral'):
            self.assertIn('asset_classes', self.ri[regime],
                          f"'asset_classes' missing from REGIME_IMPLICATIONS['{regime}']")

    def test_asset_classes_have_display_name_and_signal(self):
        for regime in ('bull', 'bear', 'neutral'):
            for ac in self.ri[regime]['asset_classes']:
                self.assertIn('display_name', ac,
                              f"'display_name' missing from asset class in {regime}")
                self.assertIn('signal', ac,
                              f"'signal' missing from asset class in {regime}")

    def test_get_on_missing_regime_returns_empty(self):
        """REGIME_IMPLICATIONS.get('DefinitelyNotARegime', {}) returns {} without error."""
        result = self.ri.get('DefinitelyNotARegime', {})
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------


class TestSecurityConstraints(unittest.TestCase):
    """Enrichment block must not introduce unsafe patterns."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_no_eval_on_cache_values(self):
        macro_regime_block_start = self.src.find('# Macro Regime State')
        recession_block_start = self.src.find('# Recession Probability Models')
        return_pos = self.src.find('return "\\n".join(summary_parts)', max(macro_regime_block_start, recession_block_start))
        block = self.src[macro_regime_block_start:return_pos]
        self.assertNotIn('eval(', block,
                         'eval() found in regime/recession enrichment block')

    def test_regime_state_used_only_as_dict_key(self):
        """regime['state'] must not appear inside | safe Jinja2 filter (not in template context)."""
        # dashboard.py doesn't render regime state with | safe in generate_market_summary
        # (it's a text string builder, not a template renderer)
        macro_block_start = self.src.find('# Macro Regime State')
        return_pos = self.src.find("return \"\\n\".join(summary_parts)", macro_block_start)
        block = self.src[macro_block_start:return_pos]
        self.assertNotIn('| safe', block,
                         "| safe filter found in regime enrichment block — state must not be rendered unsanitised")


if __name__ == '__main__':
    unittest.main()
