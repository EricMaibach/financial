"""
Static verification tests for US-169.2: Credit Page — Regime-Conditioned Interpretation Block.

Tests verify:
- credit_interpretation_config.py exists with CREDIT_INTERPRETATIONS dict
- All 12 regime×bucket combinations are present
- 3 fallback ('unknown') combinations are present
- get_credit_interpretation() returns (text, bucket) for all valid inputs
- get_credit_interpretation() returns (None, None) when hy_percentile is None
- Bucket thresholds: <=25 → tight, 25–75 → normal, >75 → wide
- dashboard.py imports get_credit_interpretation and calls it in /credit route
- credit.html renders interpretation block with correct CSS and conditional logic
- No | safe filter on dynamic interpretation text (XSS guard)

No Flask server, database, or external APIs required.
"""

import os
import re
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)

TEMPLATES_DIR = os.path.join(SIGNALTRACKERS_DIR, 'templates')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def get_dashboard_src():
    return read_file(os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py'))


def get_credit_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'credit.html'))


# ---------------------------------------------------------------------------
# credit_interpretation_config.py — module-level tests
# ---------------------------------------------------------------------------

class TestCreditInterpretationConfigExists(unittest.TestCase):
    def test_config_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'credit_interpretation_config.py')
        self.assertTrue(os.path.isfile(path), "credit_interpretation_config.py not found")

    def test_config_importable(self):
        from credit_interpretation_config import CREDIT_INTERPRETATIONS  # noqa: F401

    def test_get_credit_interpretation_importable(self):
        from credit_interpretation_config import get_credit_interpretation  # noqa: F401


class TestCreditInterpretationsDict(unittest.TestCase):
    def setUp(self):
        from credit_interpretation_config import CREDIT_INTERPRETATIONS
        self.interps = CREDIT_INTERPRETATIONS

    def _assert_key(self, key):
        self.assertIn(key, self.interps, f"Missing key: {key}")
        text = self.interps[key]
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 20, f"Interpretation too short for key {key}")

    # --- Bull regime ---
    def test_bull_tight(self):
        self._assert_key(("Bull", "tight"))

    def test_bull_normal(self):
        self._assert_key(("Bull", "normal"))

    def test_bull_wide(self):
        self._assert_key(("Bull", "wide"))

    # --- Neutral regime ---
    def test_neutral_tight(self):
        self._assert_key(("Neutral", "tight"))

    def test_neutral_normal(self):
        self._assert_key(("Neutral", "normal"))

    def test_neutral_wide(self):
        self._assert_key(("Neutral", "wide"))

    # --- Bear regime ---
    def test_bear_tight(self):
        self._assert_key(("Bear", "tight"))

    def test_bear_normal(self):
        self._assert_key(("Bear", "normal"))

    def test_bear_wide(self):
        self._assert_key(("Bear", "wide"))

    # --- Recession Watch regime ---
    def test_recession_watch_tight(self):
        self._assert_key(("Recession Watch", "tight"))

    def test_recession_watch_normal(self):
        self._assert_key(("Recession Watch", "normal"))

    def test_recession_watch_wide(self):
        self._assert_key(("Recession Watch", "wide"))

    # --- Fallback (unknown) ---
    def test_unknown_tight(self):
        self._assert_key(("unknown", "tight"))

    def test_unknown_normal(self):
        self._assert_key(("unknown", "normal"))

    def test_unknown_wide(self):
        self._assert_key(("unknown", "wide"))

    def test_total_count_at_least_15(self):
        self.assertGreaterEqual(len(self.interps), 15,
                                "Expected at least 15 entries (12 regime + 3 fallback)")

    def test_all_texts_are_strings(self):
        for key, text in self.interps.items():
            self.assertIsInstance(text, str, f"Non-string value for key {key}")

    def test_all_texts_are_nonempty(self):
        for key, text in self.interps.items():
            self.assertTrue(text.strip(), f"Empty text for key {key}")


# ---------------------------------------------------------------------------
# get_credit_interpretation() — function logic tests
# ---------------------------------------------------------------------------

class TestGetCreditInterpretation(unittest.TestCase):
    def setUp(self):
        from credit_interpretation_config import get_credit_interpretation
        self.fn = get_credit_interpretation

    def test_returns_tuple(self):
        result = self.fn("Bull", 50.0)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_none_percentile_returns_none_none(self):
        text, bucket = self.fn("Bull", None)
        self.assertIsNone(text)
        self.assertIsNone(bucket)

    def test_none_regime_uses_unknown_fallback(self):
        text, bucket = self.fn(None, 50.0)
        self.assertIsNotNone(text)
        self.assertEqual(bucket, 'normal')

    def test_unknown_regime_string_uses_fallback(self):
        text, bucket = self.fn('Unknown', 50.0)
        self.assertIsNotNone(text)
        self.assertEqual(bucket, 'normal')

    # --- Bucket boundary tests ---
    def test_percentile_0_is_tight(self):
        _, bucket = self.fn("Bull", 0.0)
        self.assertEqual(bucket, 'tight')

    def test_percentile_25_is_tight(self):
        _, bucket = self.fn("Bull", 25.0)
        self.assertEqual(bucket, 'tight')

    def test_percentile_25_1_is_normal(self):
        _, bucket = self.fn("Bull", 25.1)
        self.assertEqual(bucket, 'normal')

    def test_percentile_50_is_normal(self):
        _, bucket = self.fn("Bull", 50.0)
        self.assertEqual(bucket, 'normal')

    def test_percentile_75_is_normal(self):
        _, bucket = self.fn("Bull", 75.0)
        self.assertEqual(bucket, 'normal')

    def test_percentile_75_1_is_wide(self):
        _, bucket = self.fn("Bull", 75.1)
        self.assertEqual(bucket, 'wide')

    def test_percentile_100_is_wide(self):
        _, bucket = self.fn("Bull", 100.0)
        self.assertEqual(bucket, 'wide')

    # --- All 4 regimes return text ---
    def test_bull_returns_text(self):
        text, _ = self.fn("Bull", 50.0)
        self.assertIsNotNone(text)
        self.assertIsInstance(text, str)

    def test_neutral_returns_text(self):
        text, _ = self.fn("Neutral", 50.0)
        self.assertIsNotNone(text)

    def test_bear_returns_text(self):
        text, _ = self.fn("Bear", 50.0)
        self.assertIsNotNone(text)

    def test_recession_watch_returns_text(self):
        text, _ = self.fn("Recession Watch", 90.0)
        self.assertIsNotNone(text)

    # --- Text is meaningful length ---
    def test_interpretation_text_is_substantial(self):
        text, _ = self.fn("Bull", 10.0)
        self.assertGreater(len(text), 50)


# ---------------------------------------------------------------------------
# dashboard.py — route integration tests
# ---------------------------------------------------------------------------

class TestDashboardCreditRoute(unittest.TestCase):
    def setUp(self):
        self.src = get_dashboard_src()

    def test_imports_get_credit_interpretation(self):
        self.assertIn('from credit_interpretation_config import get_credit_interpretation',
                      self.src)

    def test_credit_route_calls_get_credit_interpretation(self):
        self.assertIn('get_credit_interpretation(', self.src)

    def test_credit_interpretation_in_context(self):
        self.assertIn("'credit_interpretation'", self.src)

    def test_credit_interpretation_bucket_in_context(self):
        self.assertIn("'credit_interpretation_bucket'", self.src)

    def test_credit_interpretation_regime_in_context(self):
        self.assertIn("'credit_interpretation_regime'", self.src)

    def test_interpretation_block_has_try_except(self):
        # Interpretation lookup must be guarded so a regime cache miss won't 500
        # Look for the pattern: try block containing get_credit_interpretation
        interp_section = self.src[self.src.find('get_credit_interpretation('):]
        # There should be a try/except somewhere before the call
        before_call = self.src[:self.src.find('get_credit_interpretation(')]
        self.assertIn('try:', before_call.split('def credit()')[-1])

    def test_interpretation_defaults_to_none(self):
        # ctx dict or except block must initialize credit_interpretation to None
        self.assertRegex(self.src, r"credit_interpretation.*=.*None")


# ---------------------------------------------------------------------------
# credit.html — template rendering tests
# ---------------------------------------------------------------------------

class TestCreditHtmlInterpretationBlock(unittest.TestCase):
    def setUp(self):
        self.html = get_credit_html()

    def test_interpretation_conditional_present(self):
        self.assertIn('{% if credit_interpretation %}', self.html)

    def test_interpretation_variable_rendered(self):
        self.assertIn('{{ credit_interpretation }}', self.html)

    def test_regime_label_rendered(self):
        self.assertIn('credit_interpretation_regime', self.html)

    def test_bucket_label_rendered(self):
        self.assertIn('credit_interpretation_bucket', self.html)

    def test_category_credit_color_applied(self):
        # The block must use the --category-credit accent
        # Check within the interpretation block specifically
        interp_idx = self.html.find('{% if credit_interpretation %}')
        end_idx = self.html.find('{% endif %}', interp_idx)
        interp_block = self.html[interp_idx:end_idx]
        self.assertIn('--category-credit', interp_block)

    def test_no_safe_filter_on_interpretation(self):
        # Dynamic interpretation text must NOT use | safe (XSS prevention)
        # Check that {{ credit_interpretation | safe }} pattern is absent
        self.assertNotRegex(self.html, r'\{\{\s*credit_interpretation\s*\|\s*safe\s*\}\}')

    def test_block_appears_after_percentile_bars(self):
        pct_idx = self.html.find('percentile-row')
        interp_idx = self.html.find('credit-interpretation-block')
        self.assertGreater(interp_idx, pct_idx,
                           "Interpretation block should appear after percentile bars")

    def test_block_appears_before_collapsible_sections(self):
        interp_idx = self.html.find('{% if credit_interpretation %}')
        # Search for the first HTML div usage, not the CSS link reference
        collapsible_idx = self.html.find('<div class="collapsible-section"')
        self.assertGreater(collapsible_idx, 0, "No collapsible-section div found")
        self.assertLess(interp_idx, collapsible_idx,
                        "Interpretation block should appear before collapsible sections")

    def test_interpretation_block_has_lightbulb_icon(self):
        interp_idx = self.html.find('{% if credit_interpretation %}')
        end_idx = self.html.find('{% endif %}', interp_idx)
        interp_block = self.html[interp_idx:end_idx]
        self.assertIn('bi-lightbulb', interp_block)


if __name__ == '__main__':
    unittest.main()
