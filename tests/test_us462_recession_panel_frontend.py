"""
Static verification tests for US-146.2: Frontend — Recession Probability Panel
(Section 0.5 on the homepage).

Tests verify HTML structure, CSS layout (mobile stacked / tablet 3-column),
color coding, divergence alert, accessibility, security, and no regressions
to existing Section 0 content.

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
STATIC_DIR = os.path.join(SIGNALTRACKERS_DIR, 'static')
COMPONENTS_CSS_DIR = os.path.join(STATIC_DIR, 'css', 'components')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def get_index_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'index.html'))


def get_base_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'base.html'))


def get_recession_panel_css():
    return read_file(os.path.join(COMPONENTS_CSS_DIR, 'recession-panel.css'))


# ---------------------------------------------------------------------------
# CSS file — existence and structure
# ---------------------------------------------------------------------------

class TestRecessionPanelCSSExists(unittest.TestCase):
    """recession-panel.css must exist in the components directory."""

    def test_css_file_exists(self):
        path = os.path.join(COMPONENTS_CSS_DIR, 'recession-panel.css')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


class TestRecessionPanelCSSClasses(unittest.TestCase):
    """All required CSS classes must be declared in recession-panel.css."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_recession_panel_declared(self):
        self.assertIn('.recession-panel', self.css)

    def test_recession_panel_header_uses_standard_pattern(self):
        # Implementation uses the standard .section-header class per SignalTrackers pattern
        # rather than a custom .recession-panel__header class
        # Verify section-header is present in index.html
        html = get_index_html()
        idx = html.find('id="recession-panel-section"')
        section = html[idx:idx + 1000]
        self.assertIn('class="section-header', section)

    def test_recession_panel_toggle_declared(self):
        self.assertIn('.recession-panel__toggle', self.css)

    def test_recession_panel_content_declared(self):
        self.assertIn('.recession-panel__content', self.css)

    def test_recession_model_row_declared(self):
        self.assertIn('.recession-model-row', self.css)

    def test_recession_model_name_declared(self):
        self.assertIn('.recession-model-name', self.css)

    def test_recession_model_desc_declared(self):
        self.assertIn('.recession-model-desc', self.css)

    def test_recession_model_value_declared(self):
        self.assertIn('.recession-model-value', self.css)

    def test_recession_model_value_low_declared(self):
        self.assertIn('.recession-model-value--low', self.css)

    def test_recession_model_value_elevated_declared(self):
        self.assertIn('.recession-model-value--elevated', self.css)

    def test_recession_model_value_high_declared(self):
        self.assertIn('.recession-model-value--high', self.css)

    def test_recession_model_risk_label_declared(self):
        self.assertIn('.recession-model-risk-label', self.css)

    def test_recession_model_range_declared(self):
        self.assertIn('.recession-model-range', self.css)

    def test_recession_card_grid_declared(self):
        self.assertIn('.recession-card-grid', self.css)

    def test_recession_card_declared(self):
        self.assertIn('.recession-card', self.css)

    def test_recession_bar_track_declared(self):
        self.assertIn('.recession-bar-track', self.css)

    def test_recession_bar_fill_declared(self):
        self.assertIn('.recession-bar-fill', self.css)

    def test_recession_bar_marker_declared(self):
        self.assertIn('.recession-bar-marker', self.css)

    def test_recession_divergence_alert_declared(self):
        self.assertIn('.recession-divergence-alert', self.css)

    def test_recession_footer_declared(self):
        self.assertIn('.recession-footer', self.css)

    def test_recession_source_declared(self):
        self.assertIn('.recession-source', self.css)


class TestColorThresholds(unittest.TestCase):
    """Color thresholds must match the design spec exactly."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_low_color_is_success_700(self):
        # #15803D = success-700 (green)
        self.assertIn('#15803D', self.css)

    def test_elevated_color_is_warning_700(self):
        # #B45309 = warning-700 (amber)
        self.assertIn('#B45309', self.css)

    def test_high_color_is_danger_700(self):
        # #B91C1C = danger-700 (red)
        self.assertIn('#B91C1C', self.css)

    def test_low_class_uses_correct_hex(self):
        match = re.search(r'\.recession-model-value--low\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)', self.css)
        self.assertIsNotNone(match, "Could not find color in .recession-model-value--low")
        self.assertEqual(match.group(1).upper(), '#15803D')

    def test_elevated_class_uses_correct_hex(self):
        match = re.search(r'\.recession-model-value--elevated\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)', self.css)
        self.assertIsNotNone(match, "Could not find color in .recession-model-value--elevated")
        self.assertEqual(match.group(1).upper(), '#B45309')

    def test_high_class_uses_correct_hex(self):
        match = re.search(r'\.recession-model-value--high\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)', self.css)
        self.assertIsNotNone(match, "Could not find color in .recession-model-value--high")
        self.assertEqual(match.group(1).upper(), '#B91C1C')


class TestDivergenceAlertCSS(unittest.TestCase):
    """Divergence alert must use warning-100 background and warning-700 text."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_divergence_alert_warning_background(self):
        # #FEF3C7 = warning-100
        self.assertIn('#FEF3C7', self.css)

    def test_divergence_alert_warning_text_color(self):
        # #B45309 = warning-700 (same as elevated)
        self.assertIn('#B45309', self.css)

    def test_divergence_alert_has_border(self):
        # #FDE68A = warning-200 border
        self.assertIn('#FDE68A', self.css)


class TestMobileLayout(unittest.TestCase):
    """Mobile layout: toggle collapsed by default, content hidden."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_content_collapsed_by_default(self):
        """recession-panel__content must start with max-height: 0."""
        # Find .recession-panel__content block (before --expanded modifier)
        idx = self.css.find('.recession-panel__content {')
        self.assertGreater(idx, -1, ".recession-panel__content not found")
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('max-height: 0', block)

    def test_content_has_overflow_hidden(self):
        idx = self.css.find('.recession-panel__content {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('overflow: hidden', block)

    def test_content_has_max_height_transition(self):
        idx = self.css.find('.recession-panel__content {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('transition', block)
        self.assertIn('max-height', block)

    def test_expanded_modifier_has_large_max_height(self):
        self.assertIn('.recession-panel__content--expanded', self.css)
        idx = self.css.find('.recession-panel__content--expanded')
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('max-height', block)
        # Must have a large value (not 0)
        match = re.search(r'max-height:\s*(\d+)px', block)
        self.assertIsNotNone(match)
        self.assertGreater(int(match.group(1)), 100)

    def test_toggle_button_has_min_height_44(self):
        """Toggle button must meet 44px touch target minimum."""
        idx = self.css.find('.recession-panel__toggle {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('min-height: 44px', block)

    def test_chevron_rotates_when_expanded(self):
        """Chevron must rotate 180deg on [aria-expanded='true']."""
        self.assertIn('[aria-expanded="true"] .recession-panel__chevron', self.css)
        self.assertIn('rotate(180deg)', self.css)

    def test_chevron_transition_present(self):
        idx = self.css.find('.recession-panel__chevron {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('transition', block)

    def test_mobile_rows_shown_by_default(self):
        idx = self.css.find('.recession-model-rows {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('display: block', block)

    def test_card_grid_hidden_on_mobile(self):
        idx = self.css.find('.recession-card-grid {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('display: none', block)


class TestTabletLayout(unittest.TestCase):
    """Tablet+ layout: toggle hidden, content always visible, card grid shown."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_tablet_breakpoint_present(self):
        self.assertIn('@media (min-width: 768px)', self.css)

    def _tablet_block(self):
        idx = self.css.find('@media (min-width: 768px)')
        self.assertGreater(idx, -1)
        return self.css[idx:]

    def test_toggle_hidden_on_tablet(self):
        block = self._tablet_block()
        self.assertIn('.recession-panel__toggle', block)
        toggle_idx = block.find('.recession-panel__toggle')
        brace_start = block.find('{', toggle_idx)
        brace_end = block.find('}', brace_start)
        rule = block[brace_start:brace_end]
        self.assertIn('display: none', rule)

    def test_content_always_visible_on_tablet(self):
        block = self._tablet_block()
        self.assertIn('.recession-panel__content', block)
        cont_idx = block.find('.recession-panel__content')
        brace_start = block.find('{', cont_idx)
        brace_end = block.find('}', brace_start)
        rule = block[brace_start:brace_end]
        self.assertIn('max-height: none', rule)
        self.assertIn('overflow: visible', rule)

    def test_mobile_rows_hidden_on_tablet(self):
        block = self._tablet_block()
        self.assertIn('.recession-model-rows', block)
        idx = block.find('.recession-model-rows')
        brace_start = block.find('{', idx)
        brace_end = block.find('}', brace_start)
        rule = block[brace_start:brace_end]
        self.assertIn('display: none', rule)

    def test_card_grid_shown_on_tablet(self):
        block = self._tablet_block()
        self.assertIn('.recession-card-grid', block)
        idx = block.find('.recession-card-grid')
        brace_start = block.find('{', idx)
        brace_end = block.find('}', brace_start)
        rule = block[brace_start:brace_end]
        self.assertIn('display: grid', rule)

    def test_card_grid_three_columns(self):
        self.assertIn('repeat(3, 1fr)', self.css)

    def test_card_grid_gap_16px(self):
        self.assertIn('gap: 16px', self.css)

    def test_recession_card_border_radius_8px(self):
        idx = self.css.find('.recession-card {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('border-radius: 8px', block)

    def test_recession_card_padding_16px(self):
        idx = self.css.find('.recession-card {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('padding: 16px', block)

    def test_recession_card_has_border(self):
        idx = self.css.find('.recession-card {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('border:', block)


class TestBarTrackCSS(unittest.TestCase):
    """Confidence/probability bar track must have required styles."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_bar_track_height_8px(self):
        idx = self.css.find('.recession-bar-track {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('height: 8px', block)

    def test_bar_track_border_radius(self):
        idx = self.css.find('.recession-bar-track {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('border-radius', block)

    def test_bar_track_position_relative(self):
        idx = self.css.find('.recession-bar-track {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('position: relative', block)

    def test_bar_marker_is_circle(self):
        idx = self.css.find('.recession-bar-marker {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('border-radius: 50%', block)

    def test_bar_marker_has_white_border(self):
        idx = self.css.find('.recession-bar-marker {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('border:', block)
        self.assertIn('#ffffff', block.lower())

    def test_bar_fill_band_declared(self):
        self.assertIn('.recession-bar-fill--band', self.css)

    def test_regime_aware_bar_marker_colors(self):
        """Bar marker should use regime border colors for each regime state."""
        self.assertIn('regime-bull .recession-bar-marker', self.css)
        self.assertIn('regime-neutral .recession-bar-marker', self.css)
        self.assertIn('regime-bear .recession-bar-marker', self.css)
        self.assertIn('regime-recession .recession-bar-marker', self.css)

    def test_regime_aware_band_fill_colors(self):
        """Confidence band fill should use regime border color at opacity."""
        self.assertIn('regime-bull .recession-bar-fill--band', self.css)
        self.assertIn('regime-neutral .recession-bar-fill--band', self.css)
        self.assertIn('regime-bear .recession-bar-fill--band', self.css)
        self.assertIn('regime-recession .recession-bar-fill--band', self.css)


class TestRegimeAwareBorderCSS(unittest.TestCase):
    """Left border must use the current regime border color token."""

    def setUp(self):
        self.css = get_recession_panel_css()

    def test_panel_has_left_border(self):
        idx = self.css.find('.recession-panel {')
        self.assertGreater(idx, -1)
        block_start = self.css.find('{', idx)
        block_end = self.css.find('}', block_start)
        block = self.css[block_start:block_end]
        self.assertIn('border-left', block)

    def test_regime_bull_left_border_uses_token(self):
        self.assertIn('regime-bull', self.css)
        self.assertIn('var(--regime-bull-border)', self.css)

    def test_regime_neutral_left_border_uses_token(self):
        self.assertIn('var(--regime-neutral-border)', self.css)

    def test_regime_bear_left_border_uses_token(self):
        self.assertIn('var(--regime-bear-border)', self.css)

    def test_regime_recession_left_border_uses_token(self):
        self.assertIn('var(--regime-recession-border)', self.css)


# ---------------------------------------------------------------------------
# base.html — CSS link
# ---------------------------------------------------------------------------

class TestBaseHTMLCSSLink(unittest.TestCase):
    """base.html must link to recession-panel.css."""

    def setUp(self):
        self.html = get_base_html()

    def test_recession_panel_css_linked(self):
        self.assertIn('recession-panel.css', self.html)

    def test_recession_panel_css_linked_after_regime_card(self):
        regime_pos = self.html.find('regime-card.css')
        recession_pos = self.html.find('recession-panel.css')
        self.assertGreater(regime_pos, -1, 'regime-card.css not found in base.html')
        self.assertGreater(recession_pos, -1, 'recession-panel.css not found in base.html')
        self.assertGreater(recession_pos, regime_pos,
                           'recession-panel.css should appear after regime-card.css')


# ---------------------------------------------------------------------------
# index.html — HTML structure
# ---------------------------------------------------------------------------

class TestSectionPresence(unittest.TestCase):
    """Section 0.5 must be present in index.html."""

    def setUp(self):
        self.html = get_index_html()

    def test_recession_panel_section_present(self):
        self.assertIn('id="recession-panel-section"', self.html)

    def test_recession_panel_aria_label(self):
        self.assertIn('aria-label="Recession Probability"', self.html)

    def test_recession_panel_class_present(self):
        self.assertIn('class="recession-panel', self.html)

    def test_section_heading_text(self):
        self.assertIn('Recession Probability', self.html)

    def test_bi_bar_chart_steps_icon_used(self):
        self.assertIn('bi-bar-chart-steps', self.html)

    def test_section_uses_h3(self):
        # h3 is the standard section heading level
        self.assertIn('<h3', self.html)


class TestSectionPosition(unittest.TestCase):
    """Section 0.5 must appear between Section 0 and Section 1."""

    def setUp(self):
        self.html = get_index_html()

    def test_recession_section_appears_after_section_0(self):
        section0_pos = self.html.find('id="macro-regime-section"')
        recession_pos = self.html.find('id="recession-panel-section"')
        self.assertGreater(section0_pos, -1, 'Section 0 not found')
        self.assertGreater(recession_pos, -1, 'Section 0.5 not found')
        self.assertGreater(recession_pos, section0_pos,
                           'Recession panel must appear after macro-regime-section')

    def test_recession_section_appears_before_section_1(self):
        recession_pos = self.html.find('id="recession-panel-section"')
        section1_pos = self.html.find('id="market-conditions"')
        self.assertGreater(section1_pos, -1, 'Section 1 not found')
        self.assertGreater(section1_pos, recession_pos,
                           'Recession panel must appear before market-conditions section')

    def test_dom_order_section0_then_0_5_then_1(self):
        s0 = self.html.find('id="macro-regime-section"')
        s05 = self.html.find('id="recession-panel-section"')
        s1 = self.html.find('id="market-conditions"')
        self.assertGreater(s0, -1)
        self.assertGreater(s05, -1)
        self.assertGreater(s1, -1)
        self.assertLess(s0, s05)
        self.assertLess(s05, s1)


class TestConditionalRendering(unittest.TestCase):
    """Recession panel must be guarded by Jinja2 if recession_probability."""

    def setUp(self):
        self.html = get_index_html()

    def test_if_guard_present(self):
        self.assertIn('{% if recession_probability %}', self.html)

    def test_endif_comment_present(self):
        self.assertIn('/recession_probability', self.html)

    def test_regime_css_class_applied_conditionally(self):
        # The recession-panel div should conditionally include macro_regime.css_class
        # Look for the conditional in the div's class attribute
        self.assertIn('macro_regime.css_class', self.html)


class TestMobileModelRows(unittest.TestCase):
    """Mobile model rows must be present with correct structure."""

    def setUp(self):
        self.html = get_index_html()

    def test_model_rows_container_present(self):
        self.assertIn('class="recession-model-rows"', self.html)

    def test_ny_fed_model_row_present(self):
        self.assertIn('class="recession-model-row"', self.html)

    def test_ny_fed_row_name_present(self):
        self.assertIn('NY FED 12-MONTH LEADING', self.html)

    def test_chauvet_piger_row_name_present(self):
        self.assertIn('CHAUVET-PIGER COINCIDENT', self.html)

    def test_richmond_sos_row_name_present(self):
        self.assertIn('RICHMOND FED SOS INDICATOR', self.html)

    def test_model_row_body_present(self):
        self.assertIn('class="recession-model-row-body"', self.html)

    def test_model_desc_class_present(self):
        self.assertIn('class="recession-model-desc"', self.html)

    def test_model_value_class_present(self):
        self.assertIn('recession-model-value', self.html)

    def test_model_risk_label_class_present(self):
        self.assertIn('recession-model-risk-label', self.html)

    def test_ny_fed_confidence_range_shown(self):
        self.assertIn('recession-model-range', self.html)

    def test_regime_divider_used_between_rows(self):
        # regime-divider separates model rows
        self.assertIn('class="regime-divider"', self.html)

    def test_model_date_class_present(self):
        self.assertIn('recession-model-date', self.html)

    def test_css_color_class_applied_to_value(self):
        # Value must use color class like recession-model-value--{{ css_key }}
        self.assertIn('recession-model-value--{{ recession_probability.ny_fed_css }}', self.html)

    def test_css_color_class_applied_to_risk_label(self):
        self.assertIn('recession-model-risk-label recession-model-value--', self.html)


class TestTabletCardGrid(unittest.TestCase):
    """Tablet+ card grid must be present with correct structure."""

    def setUp(self):
        self.html = get_index_html()

    def test_card_grid_container_present(self):
        self.assertIn('class="recession-card-grid"', self.html)

    def test_ny_fed_card_present(self):
        self.assertIn('NY FED 12-MONTH', self.html)

    def test_chauvet_piger_card_present(self):
        self.assertIn('CHAUVET-PIGER', self.html)

    def test_richmond_card_present(self):
        self.assertIn('RICHMOND FED SOS', self.html)

    def test_recession_card_class_present(self):
        self.assertIn('class="recession-card"', self.html)

    def test_bar_track_present(self):
        self.assertIn('class="recession-bar-track"', self.html)

    def test_bar_fill_present(self):
        self.assertIn('class="recession-bar-fill', self.html)

    def test_bar_marker_present(self):
        self.assertIn('class="recession-bar-marker"', self.html)

    def test_ny_fed_band_fill_class_present(self):
        self.assertIn('recession-bar-fill--band', self.html)

    def test_bar_fill_uses_inline_style(self):
        # Bars use inline style for percentage positioning
        self.assertIn('style="left:', self.html)

    def test_card_ny_fed_guarded_by_jinja_if(self):
        # NY Fed card in tablet grid must be conditional
        idx = self.html.find('class="recession-card-grid"')
        card_grid_section = self.html[idx:idx + 3000]
        self.assertIn('recession_probability.ny_fed is defined', card_grid_section)


class TestDivergenceAlert(unittest.TestCase):
    """Divergence alert must be present and conditionally rendered."""

    def setUp(self):
        self.html = get_index_html()

    def test_divergence_alert_class_present(self):
        self.assertIn('class="recession-divergence-alert"', self.html)

    def test_divergence_alert_conditional_on_15pp(self):
        self.assertIn('recession_probability.divergence_pp >= 15', self.html)

    def test_divergence_alert_icon_aria_hidden(self):
        # Warning icon inside alert must be aria-hidden
        idx = self.html.find('class="recession-divergence-alert"')
        self.assertGreater(idx, -1)
        alert_block = self.html[idx:idx + 500]
        self.assertIn('aria-hidden="true"', alert_block)

    def test_divergence_alert_shows_divergence_pp_value(self):
        self.assertIn('recession_probability.divergence_pp', self.html)

    def test_no_empty_divergence_alert_when_below_threshold(self):
        # The divergence alert is inside {% if %}…{% endif %}, not always rendered
        idx = self.html.find('recession-divergence-alert')
        self.assertGreater(idx, -1)
        # Check that there's a Jinja2 if block controlling this element
        before_alert = self.html[:idx]
        # Find the last {% if %} before the alert — should contain divergence_pp >= 15
        last_if = before_alert.rfind('{% if')
        self.assertGreater(last_if, -1)
        if_statement = self.html[last_if:last_if + 100]
        self.assertIn('divergence_pp', if_statement)


class TestFooterElements(unittest.TestCase):
    """Footer interpretation and data source credit must be present."""

    def setUp(self):
        self.html = get_index_html()

    def test_recession_footer_class_present(self):
        self.assertIn('class="recession-footer"', self.html)

    def test_interpretation_text_rendered(self):
        self.assertIn('recession_probability.interpretation', self.html)

    def test_recession_source_class_present(self):
        self.assertIn('class="recession-source"', self.html)

    def test_source_credit_text_present(self):
        self.assertIn('Data: FRED API', self.html)

    def test_source_credit_includes_richmond(self):
        self.assertIn('Richmond Fed', self.html)

    def test_source_credit_includes_updated_date(self):
        self.assertIn('recession_probability.updated', self.html)

    def test_footer_separated_by_regime_divider(self):
        idx = self.html.find('class="recession-footer"')
        self.assertGreater(idx, -1)
        before_footer = self.html[:idx]
        # A regime-divider should appear just before the footer
        last_divider = before_footer.rfind('regime-divider')
        self.assertGreater(last_divider, -1)


class TestAccessibility(unittest.TestCase):
    """Toggle button must be accessible; bar track must be decorative."""

    def setUp(self):
        self.html = get_index_html()

    def test_toggle_button_id(self):
        self.assertIn('id="recession-panel-toggle"', self.html)

    def test_toggle_button_is_button_element(self):
        self.assertIn('<button', self.html)
        self.assertIn('id="recession-panel-toggle"', self.html)

    def test_toggle_aria_expanded_false_by_default(self):
        idx = self.html.find('id="recession-panel-toggle"')
        self.assertGreater(idx, -1)
        tag_end = self.html.find('>', idx)
        tag = self.html[idx - 200:tag_end]
        self.assertIn('aria-expanded="false"', tag)

    def test_toggle_aria_controls_points_to_content(self):
        idx = self.html.find('id="recession-panel-toggle"')
        self.assertGreater(idx, -1)
        tag_end = self.html.find('>', idx)
        tag = self.html[idx - 200:tag_end]
        self.assertIn('aria-controls="recession-panel-content"', tag)

    def test_content_div_has_matching_id(self):
        self.assertIn('id="recession-panel-content"', self.html)

    def test_bar_track_is_aria_hidden(self):
        # Confidence bars are decorative — value conveyed by text
        self.assertIn('class="recession-bar-track" aria-hidden="true"', self.html)

    def test_chevron_icon_aria_hidden(self):
        idx = self.html.find('id="recession-panel-toggle"')
        self.assertGreater(idx, -1)
        button_block = self.html[idx:idx + 500]
        self.assertIn('aria-hidden="true"', button_block)

    def test_section_uses_section_element(self):
        self.assertIn('<section', self.html)
        self.assertIn('aria-label="Recession Probability"', self.html)

    def test_risk_label_text_accompanies_color(self):
        # Both the value (color-coded) AND a text risk label must be present
        # The risk label is in recession-model-risk-label
        self.assertIn('recession-model-risk-label', self.html)
        # The risk label uses the same color class as the value
        self.assertIn('recession-model-risk-label recession-model-value--', self.html)


class TestSecurity(unittest.TestCase):
    """No | safe filter on user-facing string content."""

    def setUp(self):
        self.html = get_index_html()

    def _get_recession_section(self):
        start = self.html.find('id="recession-panel-section"')
        end = self.html.find('/recession_probability', start)
        return self.html[start:end]

    def test_interpretation_not_marked_safe(self):
        section = self._get_recession_section()
        idx = section.find('recession_probability.interpretation')
        self.assertGreater(idx, -1)
        surrounding = section[idx:idx + 50]
        self.assertNotIn('| safe', surrounding)

    def test_mobile_summary_not_marked_safe(self):
        section = self._get_recession_section()
        idx = section.find('mobile_summary')
        self.assertGreater(idx, -1)
        surrounding = section[idx:idx + 50]
        self.assertNotIn('| safe', surrounding)

    def test_no_inline_onclick_in_section(self):
        section = self._get_recession_section()
        self.assertNotIn('onclick=', section)

    def test_no_inline_onerror_in_section(self):
        section = self._get_recession_section()
        self.assertNotIn('onerror=', section)

    def test_divergence_pp_not_marked_safe(self):
        section = self._get_recession_section()
        idx = section.find('divergence_pp')
        if idx > -1:
            surrounding = section[idx:idx + 50]
            self.assertNotIn('| safe', surrounding)


class TestMobileSummaryText(unittest.TestCase):
    """Mobile summary text must be present in the toggle button."""

    def setUp(self):
        self.html = get_index_html()

    def test_summary_span_present(self):
        self.assertIn('class="recession-panel__summary"', self.html)

    def test_mobile_summary_field_rendered(self):
        self.assertIn('recession_probability.mobile_summary', self.html)

    def test_chevron_element_present(self):
        self.assertIn('recession-panel__chevron', self.html)

    def test_chevron_uses_bi_chevron_down(self):
        self.assertIn('bi-chevron-down', self.html)


class TestJavaScriptToggle(unittest.TestCase):
    """JavaScript toggle for the recession panel must be present."""

    def setUp(self):
        self.html = get_index_html()

    def test_recession_toggle_js_present(self):
        self.assertIn('recession-panel-toggle', self.html)

    def test_toggle_js_uses_aria_expanded(self):
        # Check toggle logic updates aria-expanded
        idx = self.html.find("'recession-panel-toggle'")
        if idx == -1:
            idx = self.html.find('"recession-panel-toggle"')
        self.assertGreater(idx, -1, "recession-panel-toggle reference not found in JS")
        js_block = self.html[idx:idx + 600]
        self.assertIn('aria-expanded', js_block)

    def test_toggle_js_adds_expanded_class(self):
        self.assertIn('recession-panel__content--expanded', self.html)

    def test_toggle_registered_in_domcontentloaded(self):
        self.assertIn('DOMContentLoaded', self.html)
        # Find the DOMContentLoaded block that contains the recession toggle
        # (uses find to get the first occurrence which contains the expansion toggles)
        dc_idx = self.html.find('DOMContentLoaded')
        self.assertGreater(dc_idx, -1)
        # The recession toggle should appear between this DOMContentLoaded and the next one
        next_dc_idx = self.html.find('DOMContentLoaded', dc_idx + 1)
        if next_dc_idx == -1:
            next_dc_idx = len(self.html)
        dc_block = self.html[dc_idx:next_dc_idx]
        self.assertIn('recession-panel-toggle', dc_block)


# ---------------------------------------------------------------------------
# Regression tests — Section 0 must still be intact
# ---------------------------------------------------------------------------

class TestSection0Regression(unittest.TestCase):
    """Section 0 (Macro Regime Score Panel) must not be affected."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_0_id_present(self):
        self.assertIn('id="macro-regime-section"', self.html)

    def test_section_0_aria_label_present(self):
        self.assertIn('aria-label="Macro Regime Score"', self.html)

    def test_section_0_macro_regime_guard_present(self):
        self.assertIn('{% if macro_regime %}', self.html)

    def test_section_0_regime_card_present(self):
        self.assertIn('class="regime-card', self.html)

    def test_section_0_regime_state_name_present(self):
        self.assertIn('regime-state-name', self.html)

    def test_section_0_signal_chips_present(self):
        self.assertIn('regime-signal-chips', self.html)


class TestSection1Regression(unittest.TestCase):
    """Section 1 (Market Conditions) must not be affected."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_1_id_present(self):
        self.assertIn('id="market-conditions"', self.html)

    def test_section_1_badges_grid_present(self):
        self.assertIn('id="market-badges"', self.html)

    def test_section_1_market_cards_present(self):
        self.assertIn('id="market-cards"', self.html)


if __name__ == '__main__':
    unittest.main()
