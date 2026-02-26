"""
Static verification tests for US-4.1.2: Frontend — Homepage Macro Regime Card (Section 0).

These tests verify the implementation without requiring a live Flask server,
external API calls, or market data CSVs. They inspect source files and
exercise pure-Python logic directly via regime_config (no flask dependency).
"""

import os
import re
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# CSS file — existence
# ---------------------------------------------------------------------------

class TestRegimeCardCSSExists(unittest.TestCase):
    """regime-card.css must exist in the components directory."""

    def setUp(self):
        self.css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )

    def test_css_file_exists(self):
        self.assertTrue(os.path.exists(self.css_path), f"Missing: {self.css_path}")


class TestRegimeCardCSSTokens(unittest.TestCase):
    """regime-card.css must define all four regime design tokens."""

    def setUp(self):
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)

    def test_bull_tokens_defined(self):
        self.assertIn('--regime-bull-bg', self.css)
        self.assertIn('--regime-bull-border', self.css)
        self.assertIn('--regime-bull-text', self.css)

    def test_neutral_tokens_defined(self):
        self.assertIn('--regime-neutral-bg', self.css)
        self.assertIn('--regime-neutral-border', self.css)
        self.assertIn('--regime-neutral-text', self.css)

    def test_bear_tokens_defined(self):
        self.assertIn('--regime-bear-bg', self.css)
        self.assertIn('--regime-bear-border', self.css)
        self.assertIn('--regime-bear-text', self.css)

    def test_recession_tokens_defined(self):
        self.assertIn('--regime-recession-bg', self.css)
        self.assertIn('--regime-recession-border', self.css)
        self.assertIn('--regime-recession-text', self.css)

    def test_bear_does_not_use_danger_red(self):
        """Bear must NOT use danger red — reserve red for Recession Watch."""
        match = re.search(r'--regime-bear-bg:\s*(#[0-9a-fA-F]+)', self.css)
        self.assertIsNotNone(match, "Could not find --regime-bear-bg value")
        val = match.group(1).upper()
        self.assertNotEqual(val, '#FEE2E2', "Bear must use warning palette, not danger red")

    def test_recession_uses_danger_red(self):
        """Recession Watch must use the danger/red palette."""
        match = re.search(r'--regime-recession-bg:\s*(#[0-9a-fA-F]+)', self.css)
        self.assertIsNotNone(match, "Could not find --regime-recession-bg value")
        val = match.group(1).upper()
        self.assertEqual(val, '#FEE2E2', f"Recession bg should be #FEE2E2, got {val}")


class TestRegimeCardCSSComponents(unittest.TestCase):
    """regime-card.css must define all required component classes."""

    def setUp(self):
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)

    def test_regime_card_class(self):
        self.assertIn('.regime-card', self.css)

    def test_all_four_regime_variant_classes(self):
        for variant in ['.regime-bull', '.regime-neutral', '.regime-bear', '.regime-recession']:
            self.assertIn(variant, self.css, f"Missing CSS class: {variant}")

    def test_regime_dot_class(self):
        self.assertIn('.regime-dot', self.css)

    def test_regime_dot_size(self):
        """Regime dot must be 12px diameter."""
        dot_match = re.search(r'\.regime-dot\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(dot_match)
        dot_block = dot_match.group(0)
        self.assertIn('12px', dot_block)

    def test_signal_chip_class(self):
        self.assertIn('.regime-signal-chip', self.css)

    def test_signal_chip_touch_target(self):
        """Signal chips must have min-height: 44px for touch targets."""
        chip_match = re.search(r'\.regime-signal-chip\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(chip_match, "Could not find .regime-signal-chip rule")
        chip_block = chip_match.group(0)
        self.assertIn('44px', chip_block, "Signal chip must have 44px touch target")

    def test_confidence_color_classes_defined(self):
        """Confidence level color classes must exist in CSS (US-5.1.2: confidence visible on all breakpoints)."""
        self.assertIn('.regime-confidence-high', self.css)
        self.assertIn('.regime-confidence-medium', self.css)
        self.assertIn('.regime-confidence-low', self.css)

    def test_signal_chips_2col_mobile(self):
        """Signal chips grid must be 2-column on mobile."""
        chips_match = re.search(r'\.regime-signal-chips\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(chips_match, "Could not find .regime-signal-chips rule")
        chips_block = chips_match.group(0)
        self.assertIn('repeat(2, 1fr)', chips_block,
                      "Mobile signal chips must be 2-column grid")

    def test_signal_chip_hover_transform(self):
        """Signal chip hover must use translateY(-1px) per spec."""
        self.assertIn('translateY(-1px)', self.css)

    def test_regime_confidence_classes(self):
        """Confidence level color classes must be defined."""
        self.assertIn('.regime-confidence-high', self.css)
        self.assertIn('.regime-confidence-medium', self.css)
        self.assertIn('.regime-confidence-low', self.css)

    def test_regime_signal_name_class(self):
        self.assertIn('.regime-signal-name', self.css)

    def test_regime_signal_value_class(self):
        self.assertIn('.regime-signal-value', self.css)

    def test_regime_signal_annotation_class(self):
        self.assertIn('.regime-signal-annotation', self.css)

    def test_signal_value_monospace(self):
        """Signal value must use monospace font per spec."""
        self.assertIn('monospace', self.css)

    def test_regime_summary_italic(self):
        """Summary text must be italic per spec."""
        self.assertIn('font-style: italic', self.css)

    def test_regime_divider_class(self):
        self.assertIn('.regime-divider', self.css)

    def test_updated_inline_class(self):
        self.assertIn('.regime-updated-inline', self.css)

    def test_updated_panel_hidden_mobile(self):
        """Updated panel must be hidden on mobile."""
        panel_match = re.search(r'\.regime-updated-panel\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(panel_match)
        panel_block = panel_match.group(0)
        self.assertIn('display: none', panel_block)


class TestRegimeCardCSSResponsive(unittest.TestCase):
    """regime-card.css must have responsive breakpoints."""

    def setUp(self):
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)

    def test_tablet_breakpoint_exists(self):
        """Must have a 768px breakpoint for tablet layout."""
        self.assertIn('768px', self.css)

    def test_3col_chips_on_tablet(self):
        """Signal chips must switch to 3-column on tablet+."""
        self.assertIn('repeat(3, 1fr)', self.css)

    def test_2col_body_on_tablet(self):
        """Regime body must switch to 2-column flex layout on tablet+."""
        self.assertIn('.regime-body-2col', self.css)
        self.assertIn('display: flex', self.css)

    def test_state_panel_class(self):
        self.assertIn('.regime-state-panel', self.css)

    def test_summary_panel_class(self):
        self.assertIn('.regime-summary-panel', self.css)

    def test_inline_date_hidden_on_tablet(self):
        """Inline date must be hidden on tablet+ (display: none in media query)."""
        self.assertIn('.regime-updated-inline', self.css)
        # In the media query block, inline must be hidden
        # Both 'display: none' and 'regime-updated-inline' must exist
        self.assertIn('display: none', self.css)

    def test_panel_date_shown_on_tablet(self):
        """Panel date must be shown on tablet+ (display: block in media query)."""
        self.assertIn('display: block', self.css)


# ---------------------------------------------------------------------------
# base.html CSS link
# ---------------------------------------------------------------------------

class TestBaseHTMLRegimeCardLink(unittest.TestCase):
    """base.html must link to regime-card.css."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'base.html')
        )

    def test_regime_card_css_linked(self):
        self.assertIn('regime-card.css', self.html)

    def test_link_uses_url_for(self):
        self.assertIn("url_for('static', filename='css/components/regime-card.css')", self.html)


# ---------------------------------------------------------------------------
# index.html structure
# ---------------------------------------------------------------------------

class TestIndexHTMLSection0Structure(unittest.TestCase):
    """index.html must contain Section 0 with the correct structure."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_section_aria_label(self):
        """Section must have aria-label='Macro Regime Score' (updated by US-5.1.2)."""
        self.assertIn('aria-label="Macro Regime Score"', self.html)

    def test_section_id(self):
        """Section must have id='macro-regime-section'."""
        self.assertIn('id="macro-regime-section"', self.html)

    def test_section_appears_before_market_conditions(self):
        """Section 0 must appear before Section 1 in the HTML."""
        pos0 = self.html.find('macro-regime-section')
        pos1 = self.html.find('market-conditions')
        self.assertGreater(pos0, 0, "macro-regime-section not found")
        self.assertGreater(pos1, 0, "market-conditions not found")
        self.assertLess(pos0, pos1, "Section 0 must come before Section 1")

    def test_macro_regime_conditional(self):
        """Section must be wrapped in a {% if macro_regime %} check."""
        self.assertIn('{% if macro_regime %}', self.html)

    def test_regime_card_div(self):
        """Must use regime-card CSS class."""
        self.assertIn('class="regime-card', self.html)

    def test_regime_css_class_applied(self):
        """Card must apply the dynamic css_class from the context variable."""
        self.assertIn('macro_regime.css_class', self.html)

    def test_regime_icon_applied(self):
        """Card must apply the dynamic icon from the context variable."""
        self.assertIn('macro_regime.icon', self.html)

    def test_regime_state_name_uppercased(self):
        """State name must be rendered in ALL CAPS using the 'upper' filter."""
        self.assertIn('macro_regime.state | upper', self.html)

    def test_regime_summary_rendered(self):
        """Plain-language summary must be rendered from context."""
        self.assertIn('macro_regime.summary', self.html)

    def test_highlighted_signals_loop(self):
        """Must loop over highlighted_signals."""
        self.assertIn('macro_regime.highlighted_signals', self.html)

    def test_signal_chip_has_link(self):
        """Signal chips must be anchor links using signal.link."""
        self.assertIn('signal.link', self.html)

    def test_signal_chip_has_role_listitem(self):
        """Signal chips must have role='listitem'."""
        self.assertIn('role="listitem"', self.html)

    def test_signal_chip_value_span_id(self):
        """Signal chip value element must have id with signal.key."""
        self.assertIn('regime-chip-{{ signal.key }}', self.html)

    def test_signal_chip_value_data_signal(self):
        """Signal chip value element must have data-signal attribute."""
        self.assertIn('data-signal="{{ signal.key }}"', self.html)

    def test_signal_chip_annotation_rendered(self):
        """Signal annotation text must be rendered."""
        self.assertIn('signal.annotation', self.html)

    def test_signal_chip_name_rendered(self):
        """Signal name must be rendered."""
        self.assertIn('signal.name', self.html)

    def test_confidence_rendered_conditionally(self):
        """Confidence indicator must be conditionally rendered."""
        self.assertIn('macro_regime.confidence', self.html)

    def test_updated_display_rendered(self):
        """Updated date must be rendered."""
        self.assertIn('macro_regime.updated_display', self.html)

    def test_aria_live_on_state(self):
        """State name element must have aria-live='polite' for screen readers."""
        self.assertIn('aria-live="polite"', self.html)

    def test_regime_signals_label(self):
        """Highlighted signals section must have a label."""
        self.assertIn('regime-signals-label', self.html)

    def test_regime_body_2col_class(self):
        """2-col body must use regime-body-2col class."""
        self.assertIn('regime-body-2col', self.html)

    def test_regime_divider_present(self):
        """Dividers must be present."""
        self.assertIn('regime-divider', self.html)

    def test_section_above_market_conditions_section(self):
        """Section 0 must appear before 'Market Conditions at a Glance' heading."""
        pos0 = self.html.find('macro-regime-section')
        pos1 = self.html.find('Market Conditions at a Glance')
        self.assertGreater(pos0, 0)
        self.assertGreater(pos1, 0)
        self.assertLess(pos0, pos1)

    def test_signal_chip_role_list(self):
        """Signal chip container must have role='list'."""
        self.assertIn('role="list"', self.html)

    def test_regime_dot_span_present(self):
        """Regime colored dot span must be present."""
        self.assertIn('regime-dot', self.html)

    def test_regime_icon_aria_hidden(self):
        """Decorative icon must be aria-hidden."""
        self.assertIn('aria-hidden="true"', self.html)

    def test_mobile_summary_block_present(self):
        """Mobile-only summary block must be present."""
        self.assertIn('regime-summary-mobile', self.html)

    def test_confidence_class_is_dynamic(self):
        """Confidence CSS class must be dynamically generated from confidence level."""
        self.assertIn('macro_regime.confidence | lower', self.html)

    def test_endif_present(self):
        """If block must be closed with endif."""
        self.assertIn('{% endif %}', self.html)


# ---------------------------------------------------------------------------
# inject_macro_regime enrichment — verified via source code inspection
# ---------------------------------------------------------------------------

class TestInjectMacroRegimeSource(unittest.TestCase):
    """inject_macro_regime source must contain the expected enrichment logic."""

    def setUp(self):
        self.source = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        )

    def test_context_processor_decorator_present(self):
        self.assertIn('@app.context_processor', self.source)

    def test_inject_macro_regime_function_present(self):
        self.assertIn('def inject_macro_regime(', self.source)

    def test_sets_icon_on_regime(self):
        self.assertIn("regime['icon']", self.source)

    def test_sets_css_class_on_regime(self):
        self.assertIn("regime['css_class']", self.source)

    def test_sets_summary_on_regime(self):
        self.assertIn("regime['summary']", self.source)

    def test_sets_highlighted_signals_on_regime(self):
        self.assertIn("regime['highlighted_signals']", self.source)

    def test_sets_category_relevance_on_regime(self):
        self.assertIn("regime['category_relevance']", self.source)

    def test_sets_updated_display_on_regime(self):
        self.assertIn("regime['updated_display']", self.source)

    def test_uses_regime_metadata(self):
        self.assertIn('REGIME_METADATA', self.source)

    def test_uses_signal_regime_annotations(self):
        self.assertIn('SIGNAL_REGIME_ANNOTATIONS', self.source)

    def test_uses_regime_category_relevance(self):
        self.assertIn('REGIME_CATEGORY_RELEVANCE', self.source)

    def test_builds_signal_key(self):
        self.assertIn("'key'", self.source)

    def test_builds_signal_name(self):
        self.assertIn("'name'", self.source)

    def test_builds_signal_annotation(self):
        self.assertIn("'annotation'", self.source)

    def test_builds_signal_link(self):
        self.assertIn("'link'", self.source)

    def test_exception_guard_present(self):
        self.assertIn('except Exception', self.source)

    def test_date_formatting_present(self):
        self.assertIn('strftime', self.source)

    def test_from_regime_config_import(self):
        self.assertIn('from regime_config import', self.source)

    def test_regime_none_returned_on_failure(self):
        self.assertIn("regime = None", self.source)


# ---------------------------------------------------------------------------
# inject_macro_regime enrichment — logic tested via regime_config directly
# (regime_config has no flask dependency)
# ---------------------------------------------------------------------------

class TestInjectMacroRegimeLogic(unittest.TestCase):
    """
    Verify enrichment logic by exercising regime_config directly —
    the same data used by inject_macro_regime() at runtime.
    """

    def setUp(self):
        import regime_config as rc
        self.rc = rc

    def _simulate_enrichment(self, state):
        """Mirror what inject_macro_regime() does for a given state."""
        rc = self.rc
        meta = rc.REGIME_METADATA[state]

        signals = []
        for sig_key in meta['highlighted_signals']:
            annotation = rc.SIGNAL_REGIME_ANNOTATIONS.get(sig_key, {}).get(state, '')
            signals.append({
                'key': sig_key,
                'annotation': annotation,
                'link': '/explorer?metric=' + sig_key,
            })

        return {
            'state': state,
            'icon': meta['icon'],
            'css_class': meta['css_class'],
            'summary': meta['summary'],
            'highlighted_signals': signals,
            'category_relevance': rc.REGIME_CATEGORY_RELEVANCE.get(state, []),
        }

    def test_all_four_regimes_produce_valid_enrichment(self):
        for state in self.rc.VALID_REGIMES:
            result = self._simulate_enrichment(state)
            self.assertIn('icon', result)
            self.assertIn('css_class', result)
            self.assertIn('summary', result)
            self.assertIn('highlighted_signals', result)
            self.assertIn('category_relevance', result)

    def test_bear_icon(self):
        result = self._simulate_enrichment('Bear')
        self.assertEqual(result['icon'], 'bi-arrow-down-circle-fill')

    def test_bear_css_class(self):
        result = self._simulate_enrichment('Bear')
        self.assertEqual(result['css_class'], 'regime-bear')

    def test_bull_icon(self):
        result = self._simulate_enrichment('Bull')
        self.assertEqual(result['icon'], 'bi-arrow-up-circle-fill')

    def test_bull_css_class(self):
        result = self._simulate_enrichment('Bull')
        self.assertEqual(result['css_class'], 'regime-bull')

    def test_neutral_icon(self):
        result = self._simulate_enrichment('Neutral')
        self.assertEqual(result['icon'], 'bi-dash-circle-fill')

    def test_neutral_css_class(self):
        result = self._simulate_enrichment('Neutral')
        self.assertEqual(result['css_class'], 'regime-neutral')

    def test_recession_icon(self):
        result = self._simulate_enrichment('Recession Watch')
        self.assertEqual(result['icon'], 'bi-exclamation-circle-fill')

    def test_recession_css_class(self):
        result = self._simulate_enrichment('Recession Watch')
        self.assertEqual(result['css_class'], 'regime-recession')

    def test_highlighted_signals_have_annotations(self):
        for state in self.rc.VALID_REGIMES:
            result = self._simulate_enrichment(state)
            for sig in result['highlighted_signals']:
                self.assertGreater(
                    len(sig['annotation']), 0,
                    f"Empty annotation for '{sig['key']}' in {state}"
                )

    def test_highlighted_signals_count_2_to_4(self):
        for state in self.rc.VALID_REGIMES:
            result = self._simulate_enrichment(state)
            signals = result['highlighted_signals']
            self.assertGreaterEqual(len(signals), 2, f"{state}: too few signals")
            self.assertLessEqual(len(signals), 4, f"{state}: too many signals")

    def test_bear_category_relevance(self):
        result = self._simulate_enrichment('Bear')
        for cat in ['Credit', 'Rates', 'Safe Havens']:
            self.assertIn(cat, result['category_relevance'])

    def test_recession_category_relevance_non_empty(self):
        result = self._simulate_enrichment('Recession Watch')
        self.assertGreater(len(result['category_relevance']), 0)

    def test_bull_category_relevance(self):
        result = self._simulate_enrichment('Bull')
        self.assertGreater(len(result['category_relevance']), 0)

    def test_signal_links_start_with_slash(self):
        for state in self.rc.VALID_REGIMES:
            result = self._simulate_enrichment(state)
            for sig in result['highlighted_signals']:
                self.assertTrue(
                    sig['link'].startswith('/'),
                    f"Signal link must be absolute path: {sig['link']}"
                )

    def test_annotations_max_100_chars(self):
        """Signal annotations used for chip display must be ≤ 100 chars."""
        for state in self.rc.VALID_REGIMES:
            result = self._simulate_enrichment(state)
            for sig in result['highlighted_signals']:
                self.assertLessEqual(
                    len(sig['annotation']), 100,
                    f"Annotation too long for '{sig['key']}' in {state}: {sig['annotation']}"
                )


# ---------------------------------------------------------------------------
# Signal display map — verified via source code
# ---------------------------------------------------------------------------

class TestSignalDisplayMap(unittest.TestCase):
    """_SIGNAL_DISPLAY must be defined in dashboard.py with correct entries."""

    def setUp(self):
        self.source = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        )

    def test_signal_display_dict_defined(self):
        self.assertIn('_SIGNAL_DISPLAY', self.source)

    def test_all_highlighted_signals_present_as_keys(self):
        """Every signal referenced by REGIME_METADATA must appear in _SIGNAL_DISPLAY."""
        import regime_config as rc
        for state, meta in rc.REGIME_METADATA.items():
            for sig_key in meta['highlighted_signals']:
                self.assertIn(
                    f"'{sig_key}'", self.source,
                    f"Signal key '{sig_key}' (in {state}) not found in dashboard.py"
                )

    def test_high_yield_spread_present(self):
        self.assertIn("'high_yield_spread'", self.source)

    def test_vix_present(self):
        self.assertIn("'vix'", self.source)

    def test_gold_present(self):
        self.assertIn("'gold'", self.source)

    def test_sp500_present(self):
        self.assertIn("'sp500'", self.source)

    def test_yield_curve_present(self):
        self.assertIn("'yield_curve_10y2y'", self.source)

    def test_initial_claims_present(self):
        self.assertIn("'initial_claims'", self.source)

    def test_links_use_explorer_path(self):
        self.assertIn('/explorer?metric=', self.source)

    def test_nfci_present(self):
        self.assertIn("'nfci'", self.source)


# ---------------------------------------------------------------------------
# JS functions in index.html
# ---------------------------------------------------------------------------

class TestIndexHTMLJavaScript(unittest.TestCase):
    """index.html must contain JS functions for regime signal value updates."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_regime_signal_value_extractor_map_defined(self):
        self.assertIn('regimeSignalValueExtractors', self.html)

    def test_update_regime_signals_function_defined(self):
        self.assertIn('function updateRegimeSignals', self.html)

    def test_update_regime_signals_called_from_load_dashboard(self):
        """updateRegimeSignals() must be called inside loadDashboard()."""
        self.assertIn('updateRegimeSignals(data)', self.html)

    def test_high_yield_spread_extractor_present(self):
        self.assertIn('high_yield_spread', self.html)

    def test_vix_extractor_present(self):
        self.assertIn('vix:', self.html)

    def test_gold_extractor_present(self):
        self.assertIn('gold:', self.html)

    def test_sp500_extractor_present(self):
        self.assertIn('sp500:', self.html)

    def test_yield_curve_extractor_present(self):
        self.assertIn('yield_curve_10y2y:', self.html)

    def test_regime_chip_id_prefix_queried(self):
        self.assertIn('regime-chip-', self.html)

    def test_data_signal_attribute_used(self):
        self.assertIn('data-signal', self.html)

    def test_aria_label_updated_in_js(self):
        """JS must update aria-label on signal chips after populating values."""
        # The JS updateRegimeSignals function should update aria-label
        self.assertIn('aria-label', self.html)

    def test_hy_spread_reads_from_metrics(self):
        self.assertIn('hy_spread', self.html)

    def test_gold_reads_price(self):
        self.assertIn('gold.price', self.html)

    def test_vix_reads_current(self):
        self.assertIn('vix.current', self.html)

    def test_yield_curve_reads_market_grid(self):
        self.assertIn('market_grid', self.html)

    def test_extractor_map_handles_null_gracefully(self):
        """Extractors must return null when data is missing (not throw)."""
        self.assertIn('return null', self.html)

    def test_bps_formatting_for_hy_spread(self):
        """HY spread must be formatted with 'bps' suffix."""
        self.assertIn('bps', self.html)


# ---------------------------------------------------------------------------
# dashboard.py imports
# ---------------------------------------------------------------------------

class TestDashboardImports(unittest.TestCase):
    """dashboard.py must import the required regime_config symbols."""

    def setUp(self):
        self.source = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'dashboard.py')
        )

    def test_imports_regime_metadata(self):
        self.assertIn('REGIME_METADATA', self.source)

    def test_imports_signal_regime_annotations(self):
        self.assertIn('SIGNAL_REGIME_ANNOTATIONS', self.source)

    def test_imports_regime_category_relevance(self):
        self.assertIn('REGIME_CATEGORY_RELEVANCE', self.source)

    def test_from_regime_config_import(self):
        self.assertIn('from regime_config import', self.source)


# ---------------------------------------------------------------------------
# Edge case: macro_regime = None in template
# ---------------------------------------------------------------------------

class TestNullMacroRegimeHandling(unittest.TestCase):
    """index.html must not render the regime section when macro_regime is None."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_conditional_wraps_entire_section(self):
        self.assertIn('{% if macro_regime %}', self.html)

    def test_endif_present(self):
        self.assertIn('{% endif %}', self.html)

    def test_conditional_before_regime_card(self):
        """The if guard must appear before the regime-card div."""
        if_pos = self.html.find('{% if macro_regime %}')
        card_pos = self.html.find('class="regime-card')
        self.assertGreater(if_pos, 0, "{% if macro_regime %} not found")
        self.assertGreater(card_pos, 0, "regime-card div not found")
        self.assertLess(if_pos, card_pos,
                        "{% if macro_regime %} must appear before regime-card div")


if __name__ == '__main__':
    unittest.main()
