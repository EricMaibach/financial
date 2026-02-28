"""
Static verification tests for US-123.4: Navigation & Regime parity —
/credit stub, Credit nav, Dollar in Regime Implications.

Tests verify:
- /credit route registered in dashboard.py
- /divergence redirects to /credit (backward-compat)
- credit.html template exists, extends base.html, shows placeholder text
- base.html: Credit in Markets dropdown, dropdown order, active state includes 'credit'
- regime_implications_config.py: Dollar as 6th asset class in all 4 regimes
- Dollar signal values per regime (neutral/neutral/outperform/strong_outperform)
- Dollar annotations reference Post-Bretton Woods data (1971–2025)
- Dollar leading/lagging sectors are None in all regimes
- All 5 existing asset classes still present
- Total matrix is now 4 regimes × 6 asset classes = 24 entries

No Flask server, external APIs, or database required.
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


def get_base_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'base.html'))


def get_credit_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'credit.html'))


# ---------------------------------------------------------------------------
# credit.html — template existence and structure
# ---------------------------------------------------------------------------

class TestCreditTemplateExists(unittest.TestCase):
    """credit.html must exist in the templates directory."""

    def test_template_file_exists(self):
        path = os.path.join(TEMPLATES_DIR, 'credit.html')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


class TestCreditTemplateStructure(unittest.TestCase):
    """credit.html must extend base.html with required blocks."""

    def setUp(self):
        self.html = get_credit_html()

    def test_extends_base(self):
        self.assertIn("{% extends \"base.html\" %}", self.html)

    def test_has_title_block(self):
        self.assertIn("{% block title %}", self.html)

    def test_title_contains_credit(self):
        self.assertIn("Credit", self.html)

    def test_has_content_block(self):
        self.assertIn("{% block content %}", self.html)

    def test_has_page_header(self):
        self.assertIn("Credit Markets", self.html)

    def test_has_placeholder_text(self):
        self.assertIn("coming in a future release", self.html.lower())

    def test_placeholder_mentions_hy_spreads(self):
        self.assertIn("HY spreads", self.html)

    def test_placeholder_mentions_ig_spreads(self):
        self.assertIn("IG spreads", self.html)

    def test_placeholder_links_to_home(self):
        self.assertIn('href="/"', self.html)

    def test_no_javascript(self):
        self.assertNotIn('<script', self.html)

    def test_no_charts(self):
        self.assertNotIn('chart', self.html.lower())

    def test_endblock_present(self):
        self.assertIn("{% endblock %}", self.html)


# ---------------------------------------------------------------------------
# dashboard.py — /credit route registration
# ---------------------------------------------------------------------------

class TestCreditRouteInDashboard(unittest.TestCase):
    """dashboard.py must register the /credit route."""

    def setUp(self):
        self.src = get_dashboard_src()

    def test_credit_route_decorator(self):
        self.assertIn("@app.route('/credit')", self.src)

    def test_credit_function_defined(self):
        self.assertIn("def credit():", self.src)

    def test_credit_renders_template(self):
        # Find the credit function and verify it renders credit.html
        idx = self.src.find("def credit():")
        self.assertGreater(idx, 0)
        section = self.src[idx:idx + 200]
        self.assertIn("render_template('credit.html')", section)

    def test_credit_decorator_before_function(self):
        route_idx = self.src.find("@app.route('/credit')")
        func_idx = self.src.find("def credit():")
        self.assertGreater(func_idx, route_idx)


# ---------------------------------------------------------------------------
# dashboard.py — /divergence redirect to /credit
# ---------------------------------------------------------------------------

class TestDivergenceRedirectInDashboard(unittest.TestCase):
    """/divergence must redirect to credit endpoint."""

    def setUp(self):
        self.src = get_dashboard_src()

    def test_divergence_route_exists(self):
        self.assertIn("@app.route('/divergence')", self.src)

    def test_divergence_redirects_to_credit(self):
        self.assertIn("url_for('credit')", self.src)

    def test_divergence_uses_301_redirect(self):
        idx = self.src.find("def divergence():")
        self.assertGreater(idx, 0)
        section = self.src[idx:idx + 200]
        self.assertIn("code=301", section)

    def test_credit_route_registered_before_divergence(self):
        """credit() must be defined so url_for('credit') can resolve."""
        credit_idx = self.src.find("def credit():")
        divergence_idx = self.src.find("def divergence():")
        self.assertGreater(credit_idx, 0)
        self.assertGreater(divergence_idx, 0)
        self.assertLess(credit_idx, divergence_idx)


# ---------------------------------------------------------------------------
# base.html — Credit in Markets dropdown
# ---------------------------------------------------------------------------

class TestBaseHTMLCreditDropdownItem(unittest.TestCase):
    """base.html must include Credit as a Markets dropdown item."""

    def setUp(self):
        self.html = get_base_html()

    def test_credit_dropdown_item_present(self):
        self.assertIn('href="/credit"', self.html)

    def test_credit_active_class_conditional(self):
        self.assertIn("request.endpoint == 'credit'", self.html)

    def test_credit_label_text(self):
        self.assertIn('> Credit', self.html)

    def test_credit_icon_present(self):
        self.assertIn("bi-credit-card", self.html)


class TestBaseHTMLActiveStateIncludesCredit(unittest.TestCase):
    """Markets dropdown active state must include 'credit' endpoint."""

    def setUp(self):
        self.html = get_base_html()

    def test_active_state_includes_credit(self):
        self.assertIn("'credit'", self.html)

    def test_active_state_check_includes_equity_and_credit(self):
        # The active check for the parent dropdown should include both
        self.assertIn("'equity'", self.html)
        self.assertIn("'credit'", self.html)


class TestBaseHTMLDropdownOrder(unittest.TestCase):
    """Markets dropdown items must appear in: Credit, Equities, Rates, Safe Havens, Crypto, Dollar."""

    def setUp(self):
        self.html = get_base_html()
        # Extract just the dropdown menu block
        start = self.html.find('dropdown-menu dropdown-menu-dark')
        end = self.html.find('</ul>', start)
        self.dropdown = self.html[start:end]

    def test_credit_before_equities(self):
        self.assertLess(
            self.dropdown.find('/credit'),
            self.dropdown.find('/equity'),
        )

    def test_equities_before_rates(self):
        self.assertLess(
            self.dropdown.find('/equity'),
            self.dropdown.find('/rates'),
        )

    def test_rates_before_safe_havens(self):
        self.assertLess(
            self.dropdown.find('/rates'),
            self.dropdown.find('/safe-havens'),
        )

    def test_safe_havens_before_crypto(self):
        self.assertLess(
            self.dropdown.find('/safe-havens'),
            self.dropdown.find('/crypto'),
        )

    def test_crypto_before_dollar(self):
        self.assertLess(
            self.dropdown.find('/crypto'),
            self.dropdown.find('/dollar'),
        )

    def test_six_market_items_present(self):
        items = ['/credit', '/equity', '/rates', '/safe-havens', '/crypto', '/dollar']
        for item in items:
            self.assertIn(item, self.dropdown, f"Missing dropdown item: {item}")


class TestBaseHTMLParentDropdownActiveState(unittest.TestCase):
    """Parent Markets dropdown toggle active check must include all 6 endpoints."""

    def setUp(self):
        self.html = get_base_html()
        # Extract the dropdown toggle line
        start = self.html.find('dropdown-toggle')
        end = self.html.find('</a>', start)
        self.toggle_line = self.html[start:end + 5]

    def test_active_check_includes_equity(self):
        self.assertIn("'equity'", self.toggle_line)

    def test_active_check_includes_safe_havens(self):
        self.assertIn("'safe_havens'", self.toggle_line)

    def test_active_check_includes_crypto(self):
        self.assertIn("'crypto'", self.toggle_line)

    def test_active_check_includes_rates(self):
        self.assertIn("'rates'", self.toggle_line)

    def test_active_check_includes_dollar(self):
        self.assertIn("'dollar'", self.toggle_line)

    def test_active_check_includes_credit(self):
        self.assertIn("'credit'", self.toggle_line)


# ---------------------------------------------------------------------------
# regime_implications_config.py — Dollar as 6th asset class
# ---------------------------------------------------------------------------

class TestDollarAssetClassPresent(unittest.TestCase):
    """Dollar asset class must be present in all 4 regimes."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_dollar(self, regime_key):
        entries = [ac for ac in self.config[regime_key]['asset_classes'] if ac['key'] == 'dollar']
        self.assertEqual(len(entries), 1, f"Expected exactly 1 dollar entry in {regime_key}, got {len(entries)}")
        return entries[0]

    def test_dollar_in_bull(self):
        dollar = self._get_dollar('bull')
        self.assertEqual(dollar['key'], 'dollar')

    def test_dollar_in_neutral(self):
        dollar = self._get_dollar('neutral')
        self.assertEqual(dollar['key'], 'dollar')

    def test_dollar_in_bear(self):
        dollar = self._get_dollar('bear')
        self.assertEqual(dollar['key'], 'dollar')

    def test_dollar_in_recession_watch(self):
        dollar = self._get_dollar('recession_watch')
        self.assertEqual(dollar['key'], 'dollar')

    def test_dollar_display_name_bull(self):
        self.assertEqual(self._get_dollar('bull')['display_name'], 'Dollar')

    def test_dollar_display_name_neutral(self):
        self.assertEqual(self._get_dollar('neutral')['display_name'], 'Dollar')

    def test_dollar_display_name_bear(self):
        self.assertEqual(self._get_dollar('bear')['display_name'], 'Dollar')

    def test_dollar_display_name_recession_watch(self):
        self.assertEqual(self._get_dollar('recession_watch')['display_name'], 'Dollar')


class TestDollarSignalValues(unittest.TestCase):
    """Dollar signal values must match spec per regime."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_dollar_signal(self, regime_key):
        return next(ac['signal'] for ac in self.config[regime_key]['asset_classes'] if ac['key'] == 'dollar')

    def test_bull_dollar_signal_is_neutral(self):
        self.assertEqual(self._get_dollar_signal('bull'), 'neutral')

    def test_neutral_dollar_signal_is_neutral(self):
        self.assertEqual(self._get_dollar_signal('neutral'), 'neutral')

    def test_bear_dollar_signal_is_outperform(self):
        self.assertEqual(self._get_dollar_signal('bear'), 'outperform')

    def test_recession_watch_dollar_signal_is_strong_outperform(self):
        self.assertEqual(self._get_dollar_signal('recession_watch'), 'strong_outperform')


class TestDollarSignalValidity(unittest.TestCase):
    """Dollar signals must be in VALID_SIGNALS."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS, VALID_SIGNALS
        self.config = REGIME_IMPLICATIONS
        self.valid_signals = VALID_SIGNALS

    def test_all_dollar_signals_valid(self):
        for regime_key in ['bull', 'neutral', 'bear', 'recession_watch']:
            dollar = next(ac for ac in self.config[regime_key]['asset_classes'] if ac['key'] == 'dollar')
            self.assertIn(
                dollar['signal'], self.valid_signals,
                f"Invalid dollar signal '{dollar['signal']}' in {regime_key}"
            )


class TestDollarAnnotations(unittest.TestCase):
    """Dollar annotations must reference Post-Bretton Woods data (1971–2025)."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_dollar_annotation(self, regime_key):
        return next(ac['annotation'] for ac in self.config[regime_key]['asset_classes'] if ac['key'] == 'dollar')

    def test_bull_dollar_annotation_has_1971(self):
        self.assertIn('1971', self._get_dollar_annotation('bull'))

    def test_bull_dollar_annotation_has_2025(self):
        self.assertIn('2025', self._get_dollar_annotation('bull'))

    def test_neutral_dollar_annotation_has_1971(self):
        self.assertIn('1971', self._get_dollar_annotation('neutral'))

    def test_neutral_dollar_annotation_has_2025(self):
        self.assertIn('2025', self._get_dollar_annotation('neutral'))

    def test_bear_dollar_annotation_has_1971(self):
        self.assertIn('1971', self._get_dollar_annotation('bear'))

    def test_bear_dollar_annotation_has_2025(self):
        self.assertIn('2025', self._get_dollar_annotation('bear'))

    def test_recession_watch_dollar_annotation_has_1971(self):
        self.assertIn('1971', self._get_dollar_annotation('recession_watch'))

    def test_recession_watch_dollar_annotation_has_2025(self):
        self.assertIn('2025', self._get_dollar_annotation('recession_watch'))

    def test_bull_dollar_annotation_not_empty(self):
        self.assertGreater(len(self._get_dollar_annotation('bull')), 0)

    def test_neutral_dollar_annotation_not_empty(self):
        self.assertGreater(len(self._get_dollar_annotation('neutral')), 0)

    def test_bear_dollar_annotation_not_empty(self):
        self.assertGreater(len(self._get_dollar_annotation('bear')), 0)

    def test_recession_watch_dollar_annotation_not_empty(self):
        self.assertGreater(len(self._get_dollar_annotation('recession_watch')), 0)


class TestDollarSectorCallouts(unittest.TestCase):
    """Dollar must have None for leading/lagging sectors in all regimes."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_dollar(self, regime_key):
        return next(ac for ac in self.config[regime_key]['asset_classes'] if ac['key'] == 'dollar')

    def test_bull_dollar_no_leading_sectors(self):
        self.assertIsNone(self._get_dollar('bull')['leading_sectors'])

    def test_bull_dollar_no_lagging_sectors(self):
        self.assertIsNone(self._get_dollar('bull')['lagging_sectors'])

    def test_neutral_dollar_no_leading_sectors(self):
        self.assertIsNone(self._get_dollar('neutral')['leading_sectors'])

    def test_neutral_dollar_no_lagging_sectors(self):
        self.assertIsNone(self._get_dollar('neutral')['lagging_sectors'])

    def test_bear_dollar_no_leading_sectors(self):
        self.assertIsNone(self._get_dollar('bear')['leading_sectors'])

    def test_bear_dollar_no_lagging_sectors(self):
        self.assertIsNone(self._get_dollar('bear')['lagging_sectors'])

    def test_recession_watch_dollar_no_leading_sectors(self):
        self.assertIsNone(self._get_dollar('recession_watch')['leading_sectors'])

    def test_recession_watch_dollar_no_lagging_sectors(self):
        self.assertIsNone(self._get_dollar('recession_watch')['lagging_sectors'])


# ---------------------------------------------------------------------------
# regime_implications_config.py — 6 asset classes total
# ---------------------------------------------------------------------------

class TestAssetClassCountUpdated(unittest.TestCase):
    """Each regime must now have exactly 6 asset classes."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def test_bull_has_6_asset_classes(self):
        self.assertEqual(len(self.config['bull']['asset_classes']), 6)

    def test_neutral_has_6_asset_classes(self):
        self.assertEqual(len(self.config['neutral']['asset_classes']), 6)

    def test_bear_has_6_asset_classes(self):
        self.assertEqual(len(self.config['bear']['asset_classes']), 6)

    def test_recession_watch_has_6_asset_classes(self):
        self.assertEqual(len(self.config['recession_watch']['asset_classes']), 6)

    def test_full_matrix_24_entries(self):
        total = sum(len(regime['asset_classes']) for regime in self.config.values())
        self.assertEqual(total, 24)


# ---------------------------------------------------------------------------
# regime_implications_config.py — existing 5 asset classes still present
# ---------------------------------------------------------------------------

ORIGINAL_ASSET_CLASS_KEYS = ['equities', 'credit', 'rates', 'safe_havens', 'crypto']


class TestExistingAssetClassesPreserved(unittest.TestCase):
    """All 5 original asset classes must still be present in every regime."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def _get_keys(self, regime_key):
        return [ac['key'] for ac in self.config[regime_key]['asset_classes']]

    def test_bull_has_all_original_keys(self):
        keys = self._get_keys('bull')
        for k in ORIGINAL_ASSET_CLASS_KEYS:
            self.assertIn(k, keys, f"Missing '{k}' in bull asset classes")

    def test_neutral_has_all_original_keys(self):
        keys = self._get_keys('neutral')
        for k in ORIGINAL_ASSET_CLASS_KEYS:
            self.assertIn(k, keys, f"Missing '{k}' in neutral asset classes")

    def test_bear_has_all_original_keys(self):
        keys = self._get_keys('bear')
        for k in ORIGINAL_ASSET_CLASS_KEYS:
            self.assertIn(k, keys, f"Missing '{k}' in bear asset classes")

    def test_recession_watch_has_all_original_keys(self):
        keys = self._get_keys('recession_watch')
        for k in ORIGINAL_ASSET_CLASS_KEYS:
            self.assertIn(k, keys, f"Missing '{k}' in recession_watch asset classes")


class TestExpectedAssetClassOrder(unittest.TestCase):
    """Dollar must appear as the 6th (last) asset class in every regime."""

    def setUp(self):
        from regime_implications_config import REGIME_IMPLICATIONS
        self.config = REGIME_IMPLICATIONS

    def test_dollar_is_last_in_bull(self):
        keys = [ac['key'] for ac in self.config['bull']['asset_classes']]
        self.assertEqual(keys[-1], 'dollar')

    def test_dollar_is_last_in_neutral(self):
        keys = [ac['key'] for ac in self.config['neutral']['asset_classes']]
        self.assertEqual(keys[-1], 'dollar')

    def test_dollar_is_last_in_bear(self):
        keys = [ac['key'] for ac in self.config['bear']['asset_classes']]
        self.assertEqual(keys[-1], 'dollar')

    def test_dollar_is_last_in_recession_watch(self):
        keys = [ac['key'] for ac in self.config['recession_watch']['asset_classes']]
        self.assertEqual(keys[-1], 'dollar')


# ---------------------------------------------------------------------------
# regime_implications_config.py — docstring updated
# ---------------------------------------------------------------------------

class TestConfigDocstringUpdated(unittest.TestCase):
    """Config docstring/comment must mention 6 asset classes."""

    def setUp(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'regime_implications_config.py')
        with open(path, 'r') as f:
            self.src = f.read()

    def test_docstring_mentions_6_asset_classes(self):
        self.assertIn('6 asset classes', self.src)

    def test_old_5_asset_classes_comment_removed(self):
        # The header comment should say 6 not 5
        self.assertNotIn('4 regimes × 5 asset classes', self.src)


# ---------------------------------------------------------------------------
# base.html — no regressions to other nav items
# ---------------------------------------------------------------------------

class TestNavRegressions(unittest.TestCase):
    """Existing nav items must still be present after changes."""

    def setUp(self):
        self.html = get_base_html()

    def test_dashboard_nav_item_present(self):
        self.assertIn('href="/"', self.html)

    def test_explorer_nav_item_present(self):
        self.assertIn('href="/explorer"', self.html)

    def test_equity_dropdown_item_present(self):
        self.assertIn('href="/equity"', self.html)

    def test_rates_dropdown_item_present(self):
        self.assertIn('href="/rates"', self.html)

    def test_safe_havens_dropdown_item_present(self):
        self.assertIn('href="/safe-havens"', self.html)

    def test_crypto_dropdown_item_present(self):
        self.assertIn('href="/crypto"', self.html)

    def test_dollar_dropdown_item_present(self):
        self.assertIn('href="/dollar"', self.html)


if __name__ == '__main__':
    unittest.main()
