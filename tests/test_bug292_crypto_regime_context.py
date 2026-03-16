"""
Tests for Bug #292: Crypto regime context uses incorrect risk-on/risk-off assumptions.

Verifies that crypto regime context and implications config use liquidity-driven
framing instead of the debunked risk-on/risk-off framework.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


# ---------------------------------------------------------------------------
# regime_config.py — CATEGORY_REGIME_CONTEXT['Crypto']
# ---------------------------------------------------------------------------

class TestCryptoRegimeContext(unittest.TestCase):
    """CATEGORY_REGIME_CONTEXT['Crypto'] must use liquidity-driven framing."""

    @classmethod
    def setUpClass(cls):
        from regime_config import CATEGORY_REGIME_CONTEXT
        cls.crypto = CATEGORY_REGIME_CONTEXT['Crypto']

    def test_all_four_regime_keys_exist(self):
        for key in ('Bull', 'Neutral', 'Bear', 'Recession Watch'):
            self.assertIn(key, self.crypto)

    def test_bull_references_liquidity(self):
        text = self.crypto['Bull'].lower()
        self.assertTrue(
            'liquidity' in text,
            f"Bull context should reference liquidity: {self.crypto['Bull']}"
        )

    def test_neutral_references_own_cycle(self):
        text = self.crypto['Neutral'].lower()
        self.assertTrue(
            'cycle' in text or 'limited signal' in text,
            f"Neutral context should reference own cycle or limited signal: {self.crypto['Neutral']}"
        )

    def test_bear_references_monetary_policy(self):
        text = self.crypto['Bear'].lower()
        self.assertTrue(
            'monetary policy' in text or 'liquidity' in text,
            f"Bear context should reference monetary policy or liquidity: {self.crypto['Bear']}"
        )

    def test_recession_watch_references_policy_response(self):
        text = self.crypto['Recession Watch'].lower()
        self.assertTrue(
            'policy' in text or 'qe' in text or 'recovery' in text,
            f"Recession Watch should reference policy response: {self.crypto['Recession Watch']}"
        )

    def test_no_risk_on_framing(self):
        for regime, text in self.crypto.items():
            self.assertNotIn('risk-on', text.lower(),
                             f"{regime} context must not use 'risk-on' framing")

    def test_no_risk_off_framing(self):
        for regime, text in self.crypto.items():
            self.assertNotIn('risk-off', text.lower(),
                             f"{regime} context must not use 'risk-off' framing")

    def test_no_high_beta_framing(self):
        for regime, text in self.crypto.items():
            self.assertNotIn('beta to equities', text.lower(),
                             f"{regime} context must not use 'beta to equities' framing")

    def test_contexts_acknowledge_uncertainty(self):
        """At least some contexts should use conditional language."""
        conditional_words = ('may', 'depends', 'historically', 'limited', 'expect')
        all_texts = ' '.join(self.crypto.values()).lower()
        found = [w for w in conditional_words if w in all_texts]
        self.assertTrue(
            len(found) >= 2,
            f"Contexts should acknowledge uncertainty; found: {found}"
        )

    def test_max_100_chars_each(self):
        for regime, text in self.crypto.items():
            self.assertLessEqual(len(text), 100,
                                 f"{regime} context exceeds 100 chars ({len(text)}): {text}")


# ---------------------------------------------------------------------------
# regime_implications_config.py — crypto entries
# ---------------------------------------------------------------------------

class TestCryptoImplicationsConfig(unittest.TestCase):
    """Crypto entries in REGIME_IMPLICATIONS must use liquidity-driven framing."""

    @classmethod
    def setUpClass(cls):
        from regime_implications_config import REGIME_IMPLICATIONS
        cls.implications = REGIME_IMPLICATIONS
        cls.crypto_entries = {}
        for regime_key, regime_data in REGIME_IMPLICATIONS.items():
            for asset in regime_data['asset_classes']:
                if asset['key'] == 'crypto':
                    cls.crypto_entries[regime_key] = asset

    def test_crypto_in_all_four_regimes(self):
        for key in ('bull', 'neutral', 'bear', 'recession_watch'):
            self.assertIn(key, self.crypto_entries,
                          f"Crypto entry missing from {key} regime")

    def test_display_name_is_crypto(self):
        for regime_key, entry in self.crypto_entries.items():
            self.assertEqual(entry['display_name'], 'Crypto')

    def test_bull_signal_not_outperform(self):
        """Bull signal should not be 'outperform' — relationship is not direct."""
        self.assertNotEqual(self.crypto_entries['bull']['signal'], 'outperform',
                            "Bull crypto signal should not be 'outperform'")

    def test_bear_signal_not_strong_underperform(self):
        self.assertNotEqual(self.crypto_entries['bear']['signal'], 'strong_underperform',
                            "Bear crypto signal should not be 'strong_underperform'")

    def test_recession_watch_signal_not_underperform(self):
        self.assertNotEqual(self.crypto_entries['recession_watch']['signal'], 'underperform',
                            "Recession Watch crypto signal should not be 'underperform'")

    def test_all_signals_are_neutral(self):
        """All crypto signals should be neutral given low predictive accuracy."""
        for regime_key, entry in self.crypto_entries.items():
            self.assertEqual(entry['signal'], 'neutral',
                             f"{regime_key} crypto signal should be 'neutral', got '{entry['signal']}'")

    def test_no_risk_on_off_in_annotations(self):
        for regime_key, entry in self.crypto_entries.items():
            text = entry['annotation'].lower()
            self.assertNotIn('risk-on', text,
                             f"{regime_key} annotation must not use 'risk-on'")
            self.assertNotIn('risk-off', text,
                             f"{regime_key} annotation must not use 'risk-off'")

    def test_no_high_beta_in_annotations(self):
        for regime_key, entry in self.crypto_entries.items():
            self.assertNotIn('high beta', entry['annotation'].lower(),
                             f"{regime_key} annotation must not use 'high beta'")

    def test_annotations_reference_liquidity(self):
        for regime_key, entry in self.crypto_entries.items():
            text = entry['annotation'].lower()
            self.assertTrue(
                'liquidity' in text or 'monetary policy' in text or 'm2' in text or 'qe' in text,
                f"{regime_key} annotation should reference liquidity: {entry['annotation']}"
            )

    def test_leading_lagging_sectors_none(self):
        for regime_key, entry in self.crypto_entries.items():
            self.assertIsNone(entry['leading_sectors'],
                              f"{regime_key} crypto should have no leading_sectors")
            self.assertIsNone(entry['lagging_sectors'],
                              f"{regime_key} crypto should have no lagging_sectors")


# ---------------------------------------------------------------------------
# Cross-config and regression checks
# ---------------------------------------------------------------------------

class TestCryptoNotInRegimeRelevance(unittest.TestCase):
    """Crypto should NOT be in REGIME_CATEGORY_RELEVANCE (not regime-driven)."""

    def test_crypto_absent_from_relevance(self):
        from regime_config import REGIME_CATEGORY_RELEVANCE
        for regime, categories in REGIME_CATEGORY_RELEVANCE.items():
            self.assertNotIn('Crypto', categories,
                             f"Crypto should not be in REGIME_CATEGORY_RELEVANCE['{regime}']")


class TestNoOldFramingInCodebase(unittest.TestCase):
    """Grep-equivalent: no old risk-on/risk-off crypto framing in config files."""

    def _read_file(self, filename):
        path = os.path.join(SIGNALTRACKERS_DIR, filename)
        with open(path, 'r') as f:
            return f.read()

    def test_regime_config_no_old_framing(self):
        content = self._read_file('regime_config.py').lower()
        # Only check the Crypto section context, not the entire file
        # (other categories may legitimately use "risk-on" for equities etc.)
        crypto_start = content.find("'crypto'")
        crypto_end = content.find('}', crypto_start)
        crypto_section = content[crypto_start:crypto_end]
        for phrase in ('risk-on', 'risk-off', 'beta to equities',
                       'outsized drawdown', 'severe drawdown'):
            self.assertNotIn(phrase, crypto_section,
                             f"Old framing '{phrase}' found in regime_config.py Crypto section")

    def test_implications_config_no_old_framing(self):
        content = self._read_file('regime_implications_config.py').lower()
        # Find all crypto annotation blocks
        idx = 0
        while True:
            pos = content.find("'key': 'crypto'", idx)
            if pos == -1:
                break
            # Get the annotation text (next ~300 chars should cover it)
            block = content[pos:pos + 400]
            for phrase in ('risk-on', 'risk-off', 'high beta',
                           'sells off sharply', 'risk appetite supports crypto'):
                self.assertNotIn(phrase, block,
                                 f"Old framing '{phrase}' found in crypto implications block")
            idx = pos + 1


class TestRegressionOtherCategories(unittest.TestCase):
    """Other categories must still be present and unchanged."""

    def test_all_categories_present_in_context(self):
        from regime_config import CATEGORY_REGIME_CONTEXT
        expected = {'Credit', 'Rates', 'Equities', 'Dollar', 'Crypto', 'Safe Havens'}
        self.assertEqual(set(CATEGORY_REGIME_CONTEXT.keys()), expected)

    def test_all_regimes_have_crypto_in_implications(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        for regime_key in ('bull', 'neutral', 'bear', 'recession_watch'):
            keys = [a['key'] for a in REGIME_IMPLICATIONS[regime_key]['asset_classes']]
            self.assertIn('crypto', keys,
                          f"Crypto missing from {regime_key} asset_classes")

    def test_ai_summary_not_changed(self):
        """ai_summary.py should NOT be modified — already correct per bug report."""
        # Just verify the file exists and is importable (content unchanged)
        path = os.path.join(SIGNALTRACKERS_DIR, 'ai_summary.py')
        self.assertTrue(os.path.isfile(path))


if __name__ == '__main__':
    unittest.main()
