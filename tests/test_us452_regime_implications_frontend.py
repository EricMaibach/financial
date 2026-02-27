"""
Static verification tests for US-145.2: Frontend — Regime Implications Panel
(Section 0.75 on the homepage).

Tests verify:
- CSS file existence and required class declarations
- HTML structure: section wrapper, header, mobile subtitle, toggle, tablist/tabpanel
- Signal icons, signal labels, border classes for all 5 signals
- Sector callouts (equities only)
- Mobile regime switcher chips
- Educational footer
- Progressive disclosure toggle (56px min-height, chevron, max-height pattern)
- Tablet+ tab bar (tab/tabpanel ARIA, hidden inactive panels)
- Keyboard navigation attributes (tabindex, arrow key handling in JS)
- base.html CSS/JS links
- Graceful guard: {% if regime_implications %} wraps section
- No regressions to existing Section 0 / 0.5 content

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
JS_DIR = os.path.join(STATIC_DIR, 'js')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def get_index_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'index.html'))


def get_base_html():
    return read_file(os.path.join(TEMPLATES_DIR, 'base.html'))


def get_regime_implications_css():
    return read_file(os.path.join(COMPONENTS_CSS_DIR, 'regime-implications.css'))


def get_regime_implications_js():
    return read_file(os.path.join(JS_DIR, 'regime-implications.js'))


def get_section_075(html):
    """Extract Section 0.75 block from index.html."""
    start = html.find('<!-- Section 0.75:')
    end = html.find('<!-- Section 1:', start)
    return html[start:end]


# ---------------------------------------------------------------------------
# CSS file — existence
# ---------------------------------------------------------------------------

class TestRegimeImplicationsCSSExists(unittest.TestCase):
    """regime-implications.css must exist in the components directory."""

    def test_css_file_exists(self):
        path = os.path.join(COMPONENTS_CSS_DIR, 'regime-implications.css')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


# ---------------------------------------------------------------------------
# CSS — required class declarations
# ---------------------------------------------------------------------------

class TestRegimeImplicationsCSSClasses(unittest.TestCase):
    """All required CSS classes must be declared in regime-implications.css."""

    def setUp(self):
        self.css = get_regime_implications_css()

    def test_panel_container_declared(self):
        self.assertIn('.regime-implications-panel', self.css)

    def test_mobile_subtitle_declared(self):
        self.assertIn('.regime-implications-subtitle', self.css)

    def test_mobile_toggle_declared(self):
        self.assertIn('.regime-implications-toggle', self.css)

    def test_toggle_label_declared(self):
        self.assertIn('.regime-implications-toggle-label', self.css)

    def test_chevron_declared(self):
        self.assertIn('.regime-implications-chevron', self.css)

    def test_collapsible_content_declared(self):
        self.assertIn('.regime-implications-content', self.css)

    def test_content_expanded_modifier_declared(self):
        self.assertIn('.regime-implications-content--expanded', self.css)

    def test_tab_bar_declared(self):
        self.assertIn('.regime-tab-bar', self.css)

    def test_regime_tab_declared(self):
        self.assertIn('.regime-tab', self.css)

    def test_tab_star_declared(self):
        self.assertIn('.regime-tab-star', self.css)

    def test_tab_star_not_aria_selected_controlled(self):
        """Star must NOT be shown/hidden via aria-selected — it's static HTML on the current-regime tab only."""
        self.assertNotIn('[aria-selected="true"] .regime-tab-star', self.css)

    def test_card_grid_declared(self):
        self.assertIn('.implication-card-grid', self.css)

    def test_implication_card_declared(self):
        self.assertIn('.implication-card', self.css)

    def test_card_label_declared(self):
        self.assertIn('.implication-card-label', self.css)

    def test_signal_row_declared(self):
        self.assertIn('.implication-signal-row', self.css)

    def test_signal_label_declared(self):
        self.assertIn('.implication-signal-label', self.css)

    def test_annotation_declared(self):
        self.assertIn('.implication-annotation', self.css)

    def test_sectors_declared(self):
        self.assertIn('.implication-sectors', self.css)

    def test_regime_switcher_declared(self):
        self.assertIn('.regime-switcher', self.css)

    def test_regime_switcher_chip_declared(self):
        self.assertIn('.regime-switcher-chip', self.css)

    def test_regime_switcher_chip_hidden_declared(self):
        self.assertIn('.regime-switcher-chip--hidden', self.css)

    def test_footer_declared(self):
        self.assertIn('.regime-implications-footer', self.css)


class TestRegimeImplicationsCSSSignalBorders(unittest.TestCase):
    """Signal border color classes for all 5 levels."""

    def setUp(self):
        self.css = get_regime_implications_css()

    def test_strong_outperform_border(self):
        self.assertIn('.implication-card--strong_outperform', self.css)

    def test_outperform_border(self):
        self.assertIn('.implication-card--outperform', self.css)

    def test_neutral_border(self):
        self.assertIn('.implication-card--neutral', self.css)

    def test_underperform_border(self):
        self.assertIn('.implication-card--underperform', self.css)

    def test_strong_underperform_border(self):
        self.assertIn('.implication-card--strong_underperform', self.css)


class TestRegimeImplicationsCSSSignalColors(unittest.TestCase):
    """Signal icon and text label color classes."""

    def setUp(self):
        self.css = get_regime_implications_css()

    def test_signal_icon_strong_outperform(self):
        self.assertIn('.signal-icon--strong_outperform', self.css)

    def test_signal_icon_outperform(self):
        self.assertIn('.signal-icon--outperform', self.css)

    def test_signal_icon_neutral(self):
        self.assertIn('.signal-icon--neutral', self.css)

    def test_signal_icon_underperform(self):
        self.assertIn('.signal-icon--underperform', self.css)

    def test_signal_icon_strong_underperform(self):
        self.assertIn('.signal-icon--strong_underperform', self.css)

    def test_signal_text_strong_outperform(self):
        self.assertIn('.implication-signal--strong_outperform', self.css)

    def test_signal_text_outperform(self):
        self.assertIn('.implication-signal--outperform', self.css)

    def test_signal_text_neutral(self):
        self.assertIn('.implication-signal--neutral', self.css)

    def test_signal_text_underperform(self):
        self.assertIn('.implication-signal--underperform', self.css)

    def test_signal_text_strong_underperform(self):
        self.assertIn('.implication-signal--strong_underperform', self.css)

    def test_underperform_text_uses_warning_700(self):
        """Underperform text must use warning-700 (#B45309) for AA contrast per spec."""
        css = self.css
        idx = css.find('.implication-signal--underperform')
        block = css[idx:idx + 60]
        self.assertIn('#B45309', block)

    def test_strong_underperform_text_uses_danger_700(self):
        """Strong Underperform text must use danger-700 (#B91C1C) for AA contrast per spec."""
        css = self.css
        idx = css.find('.implication-signal--strong_underperform')
        block = css[idx:idx + 60]
        self.assertIn('#B91C1C', block)


class TestRegimeImplicationsCSSTabColors(unittest.TestCase):
    """Regime tab active border colors per spec."""

    def setUp(self):
        self.css = get_regime_implications_css()

    def test_bull_tab_active_color(self):
        self.assertIn('.regime-tab--bull[aria-selected="true"]', self.css)
        # success-600
        idx = self.css.find('.regime-tab--bull[aria-selected="true"]')
        block = self.css[idx:idx + 120]
        self.assertIn('#16A34A', block)

    def test_neutral_tab_active_color(self):
        self.assertIn('.regime-tab--neutral[aria-selected="true"]', self.css)
        idx = self.css.find('.regime-tab--neutral[aria-selected="true"]')
        block = self.css[idx:idx + 120]
        self.assertIn('#3B82F6', block)

    def test_bear_tab_active_color(self):
        self.assertIn('.regime-tab--bear[aria-selected="true"]', self.css)
        idx = self.css.find('.regime-tab--bear[aria-selected="true"]')
        block = self.css[idx:idx + 120]
        self.assertIn('#D97706', block)

    def test_recession_watch_tab_active_color(self):
        self.assertIn('.regime-tab--recession_watch[aria-selected="true"]', self.css)
        idx = self.css.find('.regime-tab--recession_watch[aria-selected="true"]')
        block = self.css[idx:idx + 120]
        self.assertIn('#DC2626', block)


class TestRegimeImplicationsCSSMobileCollapse(unittest.TestCase):
    """Progressive disclosure collapse must follow max-height pattern."""

    def setUp(self):
        self.css = get_regime_implications_css()

    def test_content_collapses_with_max_height_0(self):
        idx = self.css.find('.regime-implications-content {')
        block = self.css[idx:idx + 120]
        self.assertIn('max-height: 0', block)

    def test_content_hides_overflow(self):
        idx = self.css.find('.regime-implications-content {')
        block = self.css[idx:idx + 120]
        self.assertIn('overflow: hidden', block)

    def test_content_transition_200ms(self):
        idx = self.css.find('.regime-implications-content {')
        block = self.css[idx:idx + 120]
        self.assertIn('200ms', block)

    def test_toggle_min_height_56px(self):
        idx = self.css.find('.regime-implications-toggle {')
        block = self.css[idx:idx + 200]
        self.assertIn('56px', block)

    def test_chevron_rotates_on_expand(self):
        self.assertIn('[aria-expanded="true"] .regime-implications-chevron', self.css)
        idx = self.css.find('[aria-expanded="true"] .regime-implications-chevron')
        block = self.css[idx:idx + 120]
        self.assertIn('rotate(180deg)', block)


class TestRegimeImplicationsCSSTabletOverrides(unittest.TestCase):
    """Tablet+ media query must show tabs, 3-col grid, hide mobile elements."""

    def setUp(self):
        self.css = get_regime_implications_css()
        tablet_start = self.css.find('@media (min-width: 768px)')
        self.tablet_block = self.css[tablet_start:]

    def test_tablet_media_query_present(self):
        self.assertIn('@media (min-width: 768px)', self.css)

    def test_mobile_toggle_hidden_on_tablet(self):
        self.assertIn('.regime-implications-toggle', self.tablet_block)
        idx = self.tablet_block.find('.regime-implications-toggle {')
        block = self.tablet_block[idx:idx + 80]
        self.assertIn('display: none', block)

    def test_mobile_subtitle_hidden_on_tablet(self):
        self.assertIn('.regime-implications-subtitle', self.tablet_block)

    def test_content_always_visible_on_tablet(self):
        idx = self.tablet_block.find('.regime-implications-content {')
        block = self.tablet_block[idx:idx + 100]
        self.assertIn('max-height: none', block)

    def test_tab_bar_shown_on_tablet(self):
        idx = self.tablet_block.find('.regime-tab-bar {')
        block = self.tablet_block[idx:idx + 80]
        self.assertIn('display: flex', block)

    def test_card_grid_3col_on_tablet(self):
        idx = self.tablet_block.find('.implication-card-grid {')
        block = self.tablet_block[idx:idx + 120]
        self.assertIn('repeat(3, 1fr)', block)

    def test_mobile_switcher_hidden_on_tablet(self):
        idx = self.tablet_block.find('.regime-switcher {')
        block = self.tablet_block[idx:idx + 80]
        self.assertIn('display: none', block)


# ---------------------------------------------------------------------------
# JS file — existence and key patterns
# ---------------------------------------------------------------------------

class TestRegimeImplicationsJSExists(unittest.TestCase):
    """regime-implications.js must exist."""

    def test_js_file_exists(self):
        path = os.path.join(JS_DIR, 'regime-implications.js')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


class TestRegimeImplicationsJSBehavior(unittest.TestCase):
    """JS must contain key interaction logic."""

    def setUp(self):
        self.js = get_regime_implications_js()

    def test_domcontentloaded_listener(self):
        self.assertIn('DOMContentLoaded', self.js)

    def test_mobile_toggle_click_handler(self):
        self.assertIn('regime-implications-toggle', self.js)
        self.assertIn('aria-expanded', self.js)

    def test_content_expanded_class_toggled(self):
        self.assertIn('regime-implications-content--expanded', self.js)

    def test_switch_regime_function_present(self):
        self.assertIn('switchRegime', self.js)

    def test_tab_hidden_attribute_toggled(self):
        self.assertIn('removeAttribute', self.js)
        self.assertIn('setAttribute', self.js)
        self.assertIn("'hidden'", self.js)

    def test_aria_selected_updated(self):
        self.assertIn('aria-selected', self.js)

    def test_tabindex_updated(self):
        self.assertIn('tabindex', self.js)

    def test_arrow_key_navigation(self):
        self.assertIn('ArrowRight', self.js)
        self.assertIn('ArrowLeft', self.js)

    def test_switcher_chip_click_handler(self):
        self.assertIn('regime-switcher', self.js)
        self.assertIn('data-regime', self.js)

    def test_chip_hidden_class_toggled(self):
        self.assertIn('regime-switcher-chip--hidden', self.js)

    def test_subtitle_updated_on_switch(self):
        self.assertIn('regime-implications-subtitle', self.js)

    def test_toggle_label_updated(self):
        self.assertIn('View Implications', self.js)
        self.assertIn('Hide', self.js)


# ---------------------------------------------------------------------------
# base.html — CSS and JS links
# ---------------------------------------------------------------------------

class TestBaseHTMLLinks(unittest.TestCase):
    """base.html must link regime-implications.css and regime-implications.js."""

    def setUp(self):
        self.html = get_base_html()

    def test_css_linked_in_base(self):
        self.assertIn('regime-implications.css', self.html)

    def test_js_linked_in_base(self):
        self.assertIn('regime-implications.js', self.html)

    def test_css_linked_after_recession_panel_css(self):
        recession_idx = self.html.find('recession-panel.css')
        regime_idx = self.html.find('regime-implications.css')
        self.assertGreater(regime_idx, recession_idx,
                           "regime-implications.css should appear after recession-panel.css")

    def test_js_linked_after_chatbot_js(self):
        chatbot_idx = self.html.find('chatbot.js')
        regime_idx = self.html.find('regime-implications.js')
        self.assertGreater(regime_idx, chatbot_idx,
                           "regime-implications.js should appear after chatbot.js")


# ---------------------------------------------------------------------------
# index.html — Section 0.75 structure
# ---------------------------------------------------------------------------

class TestSectionExists(unittest.TestCase):
    """Section 0.75 must exist in index.html."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_comment_present(self):
        self.assertIn('<!-- Section 0.75:', self.html)

    def test_section_regime_implications_id(self):
        self.assertIn('id="regime-implications"', self.html)

    def test_section_aria_label(self):
        self.assertIn('aria-label="Regime Implications"', self.html)

    def test_section_guarded_by_if(self):
        s = get_section_075(self.html)
        self.assertIn('{% if regime_implications %}', s)

    def test_section_endif_present(self):
        s = get_section_075(self.html)
        self.assertIn('{% endif %}{# /regime_implications #}', s)

    def test_section_placed_between_05_and_1(self):
        idx_05 = self.html.find('<!-- Section 0.5:')
        idx_075 = self.html.find('<!-- Section 0.75:')
        idx_1 = self.html.find('<!-- Section 1:')
        self.assertGreater(idx_075, idx_05)
        self.assertLess(idx_075, idx_1)


class TestSectionHeader(unittest.TestCase):
    """Section header must use the standard SignalTrackers pattern."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_section_title_class_present(self):
        self.assertIn('class="section-title"', self.s)

    def test_regime_implications_label_present(self):
        self.assertIn('Regime Implications', self.s)

    def test_section_header_div_present(self):
        self.assertIn('class="section-header', self.s)

    def test_section_title_has_icon(self):
        # Should have a Bootstrap icon in the h3
        self.assertIn('<i class="bi bi-', self.s)


class TestMobileSubtitle(unittest.TestCase):
    """Mobile subtitle must render current regime display name."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_subtitle_element_present(self):
        self.assertIn('regime-implications-subtitle', self.s)

    def test_subtitle_uses_current_regime_display_name(self):
        self.assertIn("regime_implications.regimes[regime_implications.current_regime].display_name", self.s)

    def test_subtitle_includes_historical_patterns_text(self):
        self.assertIn('Historical patterns', self.s)

    def test_subtitle_has_id(self):
        self.assertIn('id="regime-implications-subtitle"', self.s)


class TestMobileToggle(unittest.TestCase):
    """Mobile toggle button must follow the progressive disclosure pattern."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_toggle_button_present(self):
        self.assertIn('id="regime-implications-toggle"', self.s)

    def test_toggle_aria_expanded_false_default(self):
        idx = self.s.find('id="regime-implications-toggle"')
        button_block = self.s[idx:idx + 300]
        self.assertIn('aria-expanded="false"', button_block)

    def test_toggle_aria_controls(self):
        idx = self.s.find('id="regime-implications-toggle"')
        button_block = self.s[idx:idx + 300]
        self.assertIn('aria-controls="regime-implications-content"', button_block)

    def test_toggle_label_view_implications(self):
        self.assertIn('View Implications', self.s)

    def test_toggle_label_has_id(self):
        self.assertIn('id="regime-implications-toggle-label"', self.s)

    def test_chevron_icon_present(self):
        self.assertIn('bi-chevron-down regime-implications-chevron', self.s)

    def test_chevron_aria_hidden(self):
        idx = self.s.find('regime-implications-chevron')
        # Find the nearest aria-hidden in the chevron element
        block = self.s[max(0, idx - 50):idx + 80]
        self.assertIn('aria-hidden="true"', block)


class TestCollapsibleContent(unittest.TestCase):
    """Collapsible content div must have correct id and classes."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_content_div_id(self):
        self.assertIn('id="regime-implications-content"', self.s)

    def test_content_div_class(self):
        self.assertIn('class="regime-implications-content"', self.s)


class TestTabBar(unittest.TestCase):
    """Tablet+ tab bar must use ARIA tablist pattern."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_tablist_role_present(self):
        self.assertIn('role="tablist"', self.s)

    def test_tablist_aria_label(self):
        self.assertIn('aria-label="Regime phases"', self.s)

    def test_tab_role_present(self):
        self.assertIn('role="tab"', self.s)

    def test_tab_aria_selected_template(self):
        self.assertIn("aria-selected=", self.s)
        self.assertIn("_is_active", self.s)

    def test_tab_aria_controls_template(self):
        self.assertIn('aria-controls="regime-panel-{{ key }}"', self.s)

    def test_tab_tabindex_template(self):
        self.assertIn("tabindex=", self.s)

    def test_tab_id_template(self):
        self.assertIn('id="regime-tab-{{ key }}"', self.s)

    def test_tab_star_element(self):
        self.assertIn('regime-tab-star', self.s)

    def test_tab_star_conditional_on_current_regime(self):
        """Star must only render on the current regime tab (guarded by _is_active)."""
        self.assertIn('_is_active', self.s)
        # Star span is inside an {% if _is_active %} block, not unconditionally rendered
        idx = self.s.find('regime-tab-star')
        # The if _is_active guard must appear before the star span in the tab button loop
        if_idx = self.s.rfind('if _is_active', 0, idx)
        self.assertGreater(if_idx, -1, "regime-tab-star must be inside {% if _is_active %} block")

    def test_tab_bar_iterates_all_regimes(self):
        self.assertIn('regime_implications.regimes.items()', self.s)


class TestTabPanels(unittest.TestCase):
    """Tab panels must have correct ARIA attributes."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_tabpanel_role_present(self):
        self.assertIn('role="tabpanel"', self.s)

    def test_tabpanel_id_template(self):
        self.assertIn('id="regime-panel-{{ key }}"', self.s)

    def test_tabpanel_aria_labelledby_template(self):
        self.assertIn('aria-labelledby="regime-tab-{{ key }}"', self.s)

    def test_inactive_panels_use_hidden_attribute(self):
        # Must use `hidden` (not display:none) to hide inactive panels
        self.assertIn('{% if not _is_active %}hidden{% endif %}', self.s)

    def test_panels_iterate_all_regimes(self):
        # Should appear twice (tab bar + panels)
        count = self.s.count('regime_implications.regimes.items()')
        self.assertGreaterEqual(count, 2)


class TestAssetClassCards(unittest.TestCase):
    """Asset class cards must render signal, annotation, and sector callouts."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_implication_card_class_uses_signal(self):
        self.assertIn('implication-card implication-card--{{ ac.signal }}', self.s)

    def test_card_label_uses_display_name_upper(self):
        self.assertIn('ac.display_name | upper', self.s)

    def test_card_label_class_present(self):
        self.assertIn('implication-card-label', self.s)

    def test_signal_row_class_present(self):
        self.assertIn('implication-signal-row', self.s)

    def test_signal_icons_all_five(self):
        self.assertIn('bi-arrow-up-right-circle-fill', self.s)
        self.assertIn('bi-arrow-up-right', self.s)
        self.assertIn('bi-dash-circle', self.s)
        self.assertIn('bi-arrow-down-right', self.s)
        self.assertIn('bi-arrow-down-right-circle-fill', self.s)

    def test_signal_icons_aria_hidden(self):
        # All icons must be aria-hidden
        for icon in ['bi-arrow-up-right-circle-fill', 'bi-arrow-up-right',
                     'bi-dash-circle', 'bi-arrow-down-right', 'bi-arrow-down-right-circle-fill']:
            idx = self.s.find(icon)
            self.assertNotEqual(idx, -1, f"Icon {icon} not found")
            # Search a wider window — aria-hidden may come after the icon class
            block = self.s[idx:idx + 100]
            self.assertIn('aria-hidden="true"', block)

    def test_signal_label_class_uses_signal(self):
        self.assertIn('implication-signal-label implication-signal--{{ ac.signal }}', self.s)

    def test_signal_label_text_strong_outperform(self):
        self.assertIn('Strong Outperform', self.s)

    def test_signal_label_text_outperform(self):
        self.assertIn('Outperform', self.s)

    def test_signal_label_text_neutral(self):
        self.assertIn('Neutral', self.s)

    def test_signal_label_text_underperform(self):
        self.assertIn('Underperform', self.s)

    def test_signal_label_text_strong_underperform(self):
        self.assertIn('Strong Underperform', self.s)

    def test_annotation_class_present(self):
        self.assertIn('implication-annotation', self.s)

    def test_annotation_uses_ac_annotation(self):
        self.assertIn('{{ ac.annotation }}', self.s)

    def test_sector_callouts_guarded_by_if(self):
        self.assertIn('{% if ac.leading_sectors %}', self.s)

    def test_leading_sectors_rendered(self):
        self.assertIn('implication-sectors-leading', self.s)
        self.assertIn("ac.leading_sectors | join(' · ')", self.s)

    def test_lagging_sectors_rendered(self):
        self.assertIn('implication-sectors-lagging', self.s)
        self.assertIn("ac.lagging_sectors | join(' · ')", self.s)

    def test_sectors_container_class(self):
        self.assertIn('implication-sectors', self.s)


class TestMobileRegimeSwitcher(unittest.TestCase):
    """Mobile regime switcher chips must render for non-current regimes."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_switcher_container_id(self):
        self.assertIn('id="regime-switcher"', self.s)

    def test_switcher_class(self):
        self.assertIn('class="regime-switcher"', self.s)

    def test_switcher_label_text(self):
        self.assertIn('View other regimes:', self.s)

    def test_chips_container_class(self):
        self.assertIn('regime-switcher-chips', self.s)

    def test_chip_data_regime_attribute(self):
        self.assertIn('data-regime="{{ key }}"', self.s)

    def test_chip_data_regime_name_attribute(self):
        self.assertIn('data-regime-name="{{ regime_data.display_name }}"', self.s)

    def test_current_chip_gets_hidden_class(self):
        self.assertIn('regime-switcher-chip--hidden', self.s)
        self.assertIn("key == regime_implications.current_regime", self.s)

    def test_chips_iterate_all_regimes(self):
        # Find the switcher chip loop
        idx = self.s.find('regime-switcher-chips')
        switcher_block = self.s[idx:idx + 500]
        self.assertIn('regime_implications.regimes.items()', switcher_block)


class TestEducationalFooter(unittest.TestCase):
    """Educational footer / disclaimer must be present."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_footer_class_present(self):
        self.assertIn('regime-implications-footer', self.s)

    def test_footer_info_icon(self):
        self.assertIn('bi-info-circle', self.s)

    def test_footer_fred_md_reference(self):
        self.assertIn('FRED-MD', self.s)

    def test_footer_not_investment_advice(self):
        self.assertIn('Not investment advice', self.s)

    def test_footer_historical_pattern_text(self):
        self.assertIn('historical averages', self.s)


# ---------------------------------------------------------------------------
# Security — no XSS risk from template variables in this section
# ---------------------------------------------------------------------------

class TestXSSSafety(unittest.TestCase):
    """Template output must use Jinja2 auto-escaping (no |safe on user data)."""

    def setUp(self):
        self.s = get_section_075(get_index_html())

    def test_annotation_not_marked_safe(self):
        # ac.annotation must NOT be marked |safe (static data, but defense-in-depth)
        idx = self.s.find('{{ ac.annotation }}')
        self.assertNotEqual(idx, -1)
        # Verify no |safe follows it
        nearby = self.s[idx:idx + 30]
        self.assertNotIn('|safe', nearby)

    def test_display_name_in_subtitle_not_marked_safe(self):
        idx = self.s.find('.display_name }}')
        nearby = self.s[max(0, idx - 5):idx + 30]
        self.assertNotIn('|safe', nearby)


# ---------------------------------------------------------------------------
# Regression — existing sections not broken
# ---------------------------------------------------------------------------

class TestRegressionSection0Intact(unittest.TestCase):
    """Section 0 (Macro Regime Score) must still be present."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_0_comment_present(self):
        self.assertIn('<!-- Section 0:', self.html)

    def test_regime_card_still_present(self):
        self.assertIn('id="regime-implications"', self.html)
        # Section 0 uses macro_regime
        self.assertIn('{% if macro_regime %}', self.html)


class TestRegressionSection05Intact(unittest.TestCase):
    """Section 0.5 (Recession Probability) must still be present."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_05_comment_present(self):
        self.assertIn('<!-- Section 0.5:', self.html)

    def test_recession_panel_still_present(self):
        self.assertIn('class="recession-panel', self.html)


class TestSectionOrdering(unittest.TestCase):
    """Sections must appear in the correct order in index.html."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_0_before_05(self):
        self.assertLess(
            self.html.find('<!-- Section 0:'),
            self.html.find('<!-- Section 0.5:')
        )

    def test_section_05_before_075(self):
        self.assertLess(
            self.html.find('<!-- Section 0.5:'),
            self.html.find('<!-- Section 0.75:')
        )

    def test_section_075_before_1(self):
        self.assertLess(
            self.html.find('<!-- Section 0.75:'),
            self.html.find('<!-- Section 1:')
        )


if __name__ == '__main__':
    unittest.main()
