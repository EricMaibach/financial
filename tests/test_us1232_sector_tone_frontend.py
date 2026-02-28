"""
Static verification tests for US-123.2: Frontend — Sector Management Tone Panel
(Section 1.5 on the homepage).

Tests verify HTML structure, CSS layout (mobile 2-col / tablet 3-col / desktop 4-col),
tone color mapping, sparkline dots, accessibility, progressive disclosure, and no
regressions to existing sections.

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


def get_sector_tone_css():
    return read_file(os.path.join(COMPONENTS_CSS_DIR, 'sector-tone.css'))


# ---------------------------------------------------------------------------
# CSS file — existence
# ---------------------------------------------------------------------------

class TestSectorToneCSSExists(unittest.TestCase):
    """sector-tone.css must exist in the components directory."""

    def test_css_file_exists(self):
        path = os.path.join(COMPONENTS_CSS_DIR, 'sector-tone.css')
        self.assertTrue(os.path.exists(path), f"Missing: {path}")


# ---------------------------------------------------------------------------
# base.html — CSS link
# ---------------------------------------------------------------------------

class TestBaseHTMLCSSLink(unittest.TestCase):
    """base.html must link sector-tone.css."""

    def setUp(self):
        self.html = get_base_html()

    def test_sector_tone_css_linked(self):
        self.assertIn("css/components/sector-tone.css", self.html)

    def test_sector_tone_css_link_uses_url_for(self):
        self.assertIn("url_for('static', filename='css/components/sector-tone.css')", self.html)


# ---------------------------------------------------------------------------
# CSS class declarations
# ---------------------------------------------------------------------------

class TestSectorToneCSSClasses(unittest.TestCase):
    """All required CSS classes must be declared in sector-tone.css."""

    def setUp(self):
        self.css = get_sector_tone_css()

    def test_sector_tone_panel_declared(self):
        self.assertIn('.sector-tone-panel', self.css)

    def test_sector_tone_header_row_declared(self):
        self.assertIn('.sector-tone-header-row', self.css)

    def test_sector_tone_header_right_declared(self):
        self.assertIn('.sector-tone-header-right', self.css)

    def test_sector_tone_regime_link_declared(self):
        self.assertIn('.sector-tone-regime-link', self.css)

    def test_sector_tone_toggle_declared(self):
        self.assertIn('.sector-tone-toggle', self.css)

    def test_sector_tone_toggle_label_declared(self):
        self.assertIn('.sector-tone-toggle-label', self.css)

    def test_sector_tone_chevron_declared(self):
        self.assertIn('.sector-tone-chevron', self.css)

    def test_sector_tone_content_declared(self):
        self.assertIn('.sector-tone-content', self.css)

    def test_sector_tone_content_expanded_declared(self):
        self.assertIn('.sector-tone-content--expanded', self.css)

    def test_sector_card_grid_declared(self):
        self.assertIn('.sector-card-grid', self.css)

    def test_sector_card_declared(self):
        self.assertIn('.sector-card', self.css)

    def test_sector_card_positive_declared(self):
        self.assertIn('.sector-card--positive', self.css)

    def test_sector_card_neutral_declared(self):
        self.assertIn('.sector-card--neutral', self.css)

    def test_sector_card_negative_declared(self):
        self.assertIn('.sector-card--negative', self.css)

    def test_sector_card_tone_row_declared(self):
        self.assertIn('.sector-card__tone-row', self.css)

    def test_sector_card_tone_icon_declared(self):
        self.assertIn('.sector-card__tone-icon', self.css)

    def test_sector_card_tone_icon_positive_declared(self):
        self.assertIn('.sector-card__tone-icon--positive', self.css)

    def test_sector_card_tone_icon_neutral_declared(self):
        self.assertIn('.sector-card__tone-icon--neutral', self.css)

    def test_sector_card_tone_icon_negative_declared(self):
        self.assertIn('.sector-card__tone-icon--negative', self.css)

    def test_sector_card_tone_label_declared(self):
        self.assertIn('.sector-card__tone-label', self.css)

    def test_sector_card_tone_label_positive_declared(self):
        self.assertIn('.sector-card__tone-label--positive', self.css)

    def test_sector_card_tone_label_neutral_declared(self):
        self.assertIn('.sector-card__tone-label--neutral', self.css)

    def test_sector_card_tone_label_negative_declared(self):
        self.assertIn('.sector-card__tone-label--negative', self.css)

    def test_sector_card_name_declared(self):
        self.assertIn('.sector-card__name', self.css)

    def test_sector_card_sparkline_declared(self):
        self.assertIn('.sector-card__sparkline', self.css)

    def test_sector_sparkline_dot_declared(self):
        self.assertIn('.sector-sparkline-dot', self.css)

    def test_sector_sparkline_dot_positive_declared(self):
        self.assertIn('.sector-sparkline-dot--positive', self.css)

    def test_sector_sparkline_dot_neutral_declared(self):
        self.assertIn('.sector-sparkline-dot--neutral', self.css)

    def test_sector_sparkline_dot_negative_declared(self):
        self.assertIn('.sector-sparkline-dot--negative', self.css)

    def test_sector_sparkline_dot_placeholder_declared(self):
        self.assertIn('.sector-sparkline-dot--placeholder', self.css)

    def test_sector_card_quarter_declared(self):
        self.assertIn('.sector-card__quarter', self.css)

    def test_sector_tone_footer_declared(self):
        self.assertIn('.sector-tone-footer', self.css)

    def test_sector_tone_empty_declared(self):
        self.assertIn('.sector-tone-empty', self.css)


# ---------------------------------------------------------------------------
# CSS colors per design spec
# ---------------------------------------------------------------------------

class TestSectorToneCSSColors(unittest.TestCase):
    """Tone colors must match the design spec exactly."""

    def setUp(self):
        self.css = get_sector_tone_css()

    # Positive: success-500 border, success-600 icon, success-700 text
    def test_positive_left_border_is_success_500(self):
        # success-500 = #22c55e
        match = re.search(
            r'\.sector-card--positive\s*\{[^}]*border-left-color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No border-left-color in .sector-card--positive")
        self.assertEqual(match.group(1).lower(), '#22c55e')

    def test_neutral_left_border_is_neutral_300(self):
        # neutral-300 = #d1d5db
        match = re.search(
            r'\.sector-card--neutral\s*\{[^}]*border-left-color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No border-left-color in .sector-card--neutral")
        self.assertEqual(match.group(1).lower(), '#d1d5db')

    def test_negative_left_border_is_danger_500(self):
        # danger-500 = #ef4444
        match = re.search(
            r'\.sector-card--negative\s*\{[^}]*border-left-color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No border-left-color in .sector-card--negative")
        self.assertEqual(match.group(1).lower(), '#ef4444')

    def test_positive_dot_is_success_500(self):
        # success-500 = #22c55e
        match = re.search(
            r'\.sector-sparkline-dot--positive\s*\{[^}]*background-color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No background-color in .sector-sparkline-dot--positive")
        self.assertEqual(match.group(1).lower(), '#22c55e')

    def test_neutral_dot_is_neutral_300(self):
        # neutral-300 = #d1d5db
        match = re.search(
            r'\.sector-sparkline-dot--neutral\s*\{[^}]*background-color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No background-color in .sector-sparkline-dot--neutral")
        self.assertEqual(match.group(1).lower(), '#d1d5db')

    def test_negative_dot_is_danger_500(self):
        # danger-500 = #ef4444
        match = re.search(
            r'\.sector-sparkline-dot--negative\s*\{[^}]*background-color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No background-color in .sector-sparkline-dot--negative")
        self.assertEqual(match.group(1).lower(), '#ef4444')

    def test_positive_icon_is_success_600(self):
        # success-600 = #16A34A
        match = re.search(
            r'\.sector-card__tone-icon--positive\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No color in .sector-card__tone-icon--positive")
        self.assertEqual(match.group(1).upper(), '#16A34A')

    def test_negative_icon_is_danger_600(self):
        # danger-600 = #dc2626
        match = re.search(
            r'\.sector-card__tone-icon--negative\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No color in .sector-card__tone-icon--negative")
        self.assertEqual(match.group(1).lower(), '#dc2626')

    def test_positive_label_is_success_700(self):
        # success-700 = #15803D (AA contrast)
        match = re.search(
            r'\.sector-card__tone-label--positive\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No color in .sector-card__tone-label--positive")
        self.assertEqual(match.group(1).upper(), '#15803D')

    def test_negative_label_is_danger_700(self):
        # danger-700 = #B91C1C (AA contrast)
        match = re.search(
            r'\.sector-card__tone-label--negative\s*\{[^}]*color:\s*(#[0-9a-fA-F]+)',
            self.css
        )
        self.assertIsNotNone(match, "No color in .sector-card__tone-label--negative")
        self.assertEqual(match.group(1).upper(), '#B91C1C')


# ---------------------------------------------------------------------------
# CSS responsive grid breakpoints
# ---------------------------------------------------------------------------

class TestSectorToneCSSResponsive(unittest.TestCase):
    """Grid must switch from 2-col (mobile) → 3-col (768px) → 4-col (1024px)."""

    def setUp(self):
        self.css = get_sector_tone_css()

    def test_mobile_grid_is_2_columns(self):
        # Base (mobile) grid must be 2 columns
        match = re.search(
            r'\.sector-card-grid\s*\{[^}]*grid-template-columns:\s*([^;]+)',
            self.css
        )
        self.assertIsNotNone(match, ".sector-card-grid base grid-template-columns not found")
        self.assertIn('repeat(2,', match.group(1).replace(' ', ''))

    def test_tablet_768px_breakpoint_exists(self):
        self.assertIn('@media (min-width: 768px)', self.css)

    def test_tablet_grid_is_3_columns(self):
        # Find 768px block and verify 3-col grid
        idx_media = self.css.find('@media (min-width: 768px)')
        self.assertGreater(idx_media, -1)
        tablet_block = self.css[idx_media:idx_media + 800]
        self.assertIn('repeat(3', tablet_block.replace(' ', ''))

    def test_desktop_1024px_breakpoint_exists(self):
        self.assertIn('@media (min-width: 1024px)', self.css)

    def test_desktop_grid_is_4_columns(self):
        # Find 1024px block and verify 4-col grid
        idx_media = self.css.find('@media (min-width: 1024px)')
        self.assertGreater(idx_media, -1)
        desktop_block = self.css[idx_media:idx_media + 400]
        self.assertIn('repeat(4', desktop_block.replace(' ', ''))

    def test_toggle_hidden_on_tablet(self):
        # .sector-tone-toggle must have display:none inside 768px+ block
        idx_media = self.css.find('@media (min-width: 768px)')
        tablet_block = self.css[idx_media:idx_media + 800]
        self.assertIn('.sector-tone-toggle', tablet_block)
        self.assertIn('display: none', tablet_block)

    def test_content_always_visible_on_tablet(self):
        # .sector-tone-content must have max-height: none inside 768px+ block
        idx_media = self.css.find('@media (min-width: 768px)')
        tablet_block = self.css[idx_media:idx_media + 800]
        self.assertIn('.sector-tone-content', tablet_block)
        self.assertIn('max-height: none', tablet_block)

    def test_content_collapsed_by_default_mobile(self):
        # Base .sector-tone-content must start at max-height: 0
        match = re.search(
            r'\.sector-tone-content\s*\{[^}]*max-height:\s*0',
            self.css
        )
        self.assertIsNotNone(match, ".sector-tone-content must start collapsed (max-height: 0)")

    def test_content_transition_200ms(self):
        # Transition must be 200ms ease-out per spec
        self.assertIn('200ms ease-out', self.css)

    def test_toggle_min_height_56px(self):
        # Toggle must meet AAA touch target (56px min-height)
        match = re.search(
            r'\.sector-tone-toggle\s*\{[^}]*min-height:\s*56px',
            self.css
        )
        self.assertIsNotNone(match, ".sector-tone-toggle must have min-height: 56px")

    def test_sparkline_dot_size_8px(self):
        # 8px circle per spec
        match = re.search(
            r'\.sector-sparkline-dot\s*\{[^}]*width:\s*8px',
            self.css
        )
        self.assertIsNotNone(match, ".sector-sparkline-dot must have width: 8px")


# ---------------------------------------------------------------------------
# index.html — section structure
# ---------------------------------------------------------------------------

class TestSectorToneHTMLSection(unittest.TestCase):
    """index.html must contain Section 1.5 in the correct location."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_comment_present(self):
        self.assertIn('Section 1.5', self.html)
        self.assertIn('Sector Management Tone', self.html)

    def test_section_has_aria_label(self):
        self.assertIn('aria-label="Sector Management Tone"', self.html)

    def test_section_has_id(self):
        self.assertIn('id="sector-tone-section"', self.html)

    def test_section_jinja_guard_present(self):
        # Section must be wrapped in {% if sector_management_tone %}
        self.assertIn('{% if sector_management_tone %}', self.html)

    def test_sector_tone_panel_class_present(self):
        self.assertIn('class="sector-tone-panel"', self.html)

    def test_section_uses_standard_section_header(self):
        # Must follow SignalTrackers standard section header pattern
        idx = self.html.find('id="sector-tone-section"')
        section = self.html[idx:idx + 2000]
        self.assertIn('class="section-header', section)
        self.assertIn('class="section-title"', section)

    def test_section_title_text(self):
        self.assertIn('Sector Management Tone', self.html)

    def test_section_header_right_quarter_year(self):
        # Quarter/year displayed in header right
        self.assertIn('sector-tone-header-right', self.html)
        self.assertIn('sector_management_tone.quarter', self.html)
        self.assertIn('sector_management_tone.year', self.html)

    def test_section_15_placed_after_section_1(self):
        # Section 1.5 must come after Section 1 (Market Conditions)
        idx_s1 = self.html.find('Section 1: Market Conditions')
        idx_s15 = self.html.find('Section 1.5')
        self.assertGreater(idx_s15, idx_s1,
                           "Section 1.5 must come after Section 1 (Market Conditions)")

    def test_section_15_placed_before_section_2(self):
        # Section 1.5 must come before Section 2 (Today's Market Briefing)
        idx_s15 = self.html.find('Section 1.5')
        idx_s2 = self.html.find('Section 2:')
        self.assertLess(idx_s15, idx_s2,
                        "Section 1.5 must come before Section 2")


# ---------------------------------------------------------------------------
# index.html — regime link
# ---------------------------------------------------------------------------

class TestSectorToneRegimeLink(unittest.TestCase):
    """Regime link must be present and guard on macro_regime."""

    def setUp(self):
        self.html = get_index_html()

    def test_regime_link_class_present(self):
        self.assertIn('sector-tone-regime-link', self.html)

    def test_regime_link_anchors_to_macro_regime_section(self):
        self.assertIn('href="#macro-regime-section"', self.html)

    def test_regime_link_text_present(self):
        self.assertIn('Interpret alongside current macro regime', self.html)

    def test_regime_link_guarded_by_macro_regime(self):
        # The link must only appear inside a {% if macro_regime %} block
        idx = self.html.find('sector-tone-regime-link')
        vicinity = self.html[max(0, idx - 300):idx]
        self.assertIn('{% if macro_regime %}', vicinity)


# ---------------------------------------------------------------------------
# index.html — mobile toggle button
# ---------------------------------------------------------------------------

class TestSectorToneMobileToggle(unittest.TestCase):
    """Mobile collapse toggle must follow SignalTrackers progressive disclosure pattern."""

    def setUp(self):
        self.html = get_index_html()

    def test_toggle_button_present(self):
        self.assertIn('id="sector-tone-toggle"', self.html)

    def test_toggle_has_aria_expanded_false(self):
        self.assertIn('aria-expanded="false"', self.html)

    def test_toggle_has_aria_controls(self):
        self.assertIn('aria-controls="sector-tone-content"', self.html)

    def test_toggle_class_present(self):
        self.assertIn('class="sector-tone-toggle"', self.html)

    def test_toggle_has_chevron_icon(self):
        self.assertIn('sector-tone-chevron', self.html)
        self.assertIn('bi-chevron-down', self.html)

    def test_toggle_text_show_sectors(self):
        self.assertIn('Show Sectors', self.html)

    def test_toggle_text_id_for_js(self):
        self.assertIn('id="sector-tone-toggle-text"', self.html)

    def test_toggle_lines_present(self):
        self.assertIn('sector-tone-toggle-line', self.html)

    def test_collapsible_content_div_present(self):
        self.assertIn('id="sector-tone-content"', self.html)

    def test_collapsible_content_class_present(self):
        self.assertIn('class="sector-tone-content"', self.html)

    def test_toggle_inside_data_available_block(self):
        # Toggle must be inside {% if sector_management_tone.data_available %} block
        idx = self.html.find('id="sector-tone-toggle"')
        vicinity = self.html[max(0, idx - 500):idx]
        self.assertIn('sector_management_tone.data_available', vicinity)


# ---------------------------------------------------------------------------
# index.html — sector cards
# ---------------------------------------------------------------------------

class TestSectorToneCards(unittest.TestCase):
    """Sector cards must use Jinja2 loop with correct structure."""

    def setUp(self):
        self.html = get_index_html()

    def test_sector_card_grid_present(self):
        self.assertIn('class="sector-card-grid"', self.html)

    def test_jinja_for_loop_over_sectors(self):
        self.assertIn('{% for sector in sector_management_tone.sectors %}', self.html)

    def test_for_loop_endfor(self):
        self.assertIn('{% endfor %}', self.html)

    def test_sector_card_tone_class_dynamic(self):
        # Card class must include dynamic tone: sector-card sector-card--{{ _tone }}
        self.assertIn('sector-card sector-card--{{ _tone }}', self.html)

    def test_tone_variable_set_from_current_tone(self):
        self.assertIn("{% set _tone = sector.current_tone %}", self.html)

    def test_tone_row_present(self):
        self.assertIn('sector-card__tone-row', self.html)

    def test_positive_icon_bi_arrow_up_short(self):
        self.assertIn('bi-arrow-up-short', self.html)

    def test_neutral_icon_bi_dash(self):
        self.assertIn('bi-dash', self.html)

    def test_negative_icon_bi_arrow_down_short(self):
        self.assertIn('bi-arrow-down-short', self.html)

    def test_positive_label_text(self):
        self.assertIn('>Positive<', self.html)

    def test_neutral_label_text(self):
        self.assertIn('>Neutral<', self.html)

    def test_negative_label_text(self):
        self.assertIn('>Negative<', self.html)

    def test_tone_icon_aria_hidden(self):
        # Icons must be aria-hidden (color alone is never sufficient — text also present)
        idx = self.html.find('sector-card__tone-icon')
        vicinity = self.html[idx:idx + 200]
        self.assertIn('aria-hidden="true"', vicinity)

    def test_sector_name_uses_short_name(self):
        # Card must display short_name (not full name)
        self.assertIn('sector-card__name', self.html)
        self.assertIn('sector.short_name', self.html)

    def test_sector_card_quarter_label_present(self):
        self.assertIn('sector-card__quarter', self.html)


# ---------------------------------------------------------------------------
# index.html — sparkline dots
# ---------------------------------------------------------------------------

class TestSectorToneSparkline(unittest.TestCase):
    """Sparkline must render 4 dots with placeholder support and ARIA."""

    def setUp(self):
        self.html = get_index_html()

    def test_sparkline_container_present(self):
        self.assertIn('sector-card__sparkline', self.html)

    def test_sparkline_aria_label_present(self):
        # aria-label on sparkline container
        idx = self.html.find('sector-card__sparkline')
        vicinity = self.html[idx:idx + 300]
        self.assertIn('aria-label=', vicinity)

    def test_sparkline_aria_label_uses_tone_labels(self):
        self.assertIn('_tone_labels | join', self.html)

    def test_placeholder_dots_rendered(self):
        self.assertIn('sector-sparkline-dot--placeholder', self.html)

    def test_placeholder_count_variable(self):
        self.assertIn('_placeholder_count', self.html)

    def test_placeholder_guard_uses_max_filter_or_calculation(self):
        # Must calculate placeholder_count = max(0, 4 - trend_len)
        self.assertIn('_placeholder_count', self.html)
        self.assertIn('_trend_len', self.html)

    def test_filled_dots_use_tone_class(self):
        self.assertIn('sector-sparkline-dot--{{ t.tone }}', self.html)

    def test_dots_have_aria_hidden(self):
        # Individual dots must be aria-hidden (covered by container aria-label)
        idx = self.html.find('sector-sparkline-dot sector-sparkline-dot--placeholder')
        vicinity = self.html[idx:idx + 200]
        self.assertIn('aria-hidden="true"', vicinity)

    def test_dots_have_title_tooltip(self):
        # Filled dots must have title for mouse hover tooltip
        self.assertIn("title=\"{{ t.quarter }} {{ t.year }}: {{ t.tone | title }}\"", self.html)

    def test_placeholder_dots_have_title(self):
        self.assertIn('title="Data not available"', self.html)

    def test_tone_labels_list_built_for_aria(self):
        # _tone_labels list must be constructed for aria-label
        self.assertIn('_tone_labels', self.html)
        # Must append placeholder markers and then actual tone labels
        self.assertIn("_tone_labels.append", self.html)


# ---------------------------------------------------------------------------
# index.html — educational footer
# ---------------------------------------------------------------------------

class TestSectorToneFooter(unittest.TestCase):
    """Educational footer must be present inside the collapsible content."""

    def setUp(self):
        self.html = get_index_html()

    def test_footer_class_present(self):
        self.assertIn('sector-tone-footer', self.html)

    def test_footer_has_info_circle_icon(self):
        idx = self.html.find('sector-tone-footer')
        vicinity = self.html[idx:idx + 400]
        self.assertIn('bi-info-circle', vicinity)

    def test_footer_mentions_finbert(self):
        self.assertIn('FinBERT', self.html)

    def test_footer_mentions_edgar(self):
        self.assertIn('EDGAR', self.html)

    def test_footer_mentions_sp500(self):
        self.assertIn('S&amp;P 500', self.html)

    def test_footer_not_individual_stock(self):
        self.assertIn('not individual stock analysis', self.html)

    def test_footer_inside_sector_tone_content(self):
        # Footer must be inside the collapsible div
        idx_content = self.html.find('id="sector-tone-content"')
        idx_footer = self.html.find('sector-tone-footer')
        self.assertGreater(idx_footer, idx_content,
                           "sector-tone-footer must appear after sector-tone-content opening")


# ---------------------------------------------------------------------------
# index.html — empty state
# ---------------------------------------------------------------------------

class TestSectorToneEmptyState(unittest.TestCase):
    """Empty state must render when data_available is False."""

    def setUp(self):
        self.html = get_index_html()

    def test_empty_state_class_present(self):
        self.assertIn('sector-tone-empty', self.html)

    def test_empty_state_has_info_icon(self):
        idx = self.html.find('sector-tone-empty')
        vicinity = self.html[idx:idx + 400]
        self.assertIn('bi-info-circle', vicinity)

    def test_empty_state_message_text(self):
        # Message about earnings season completing
        self.assertIn('earnings season completes', self.html)

    def test_empty_state_mentions_weeks(self):
        self.assertIn('weeks after quarter end', self.html)

    def test_empty_state_guarded_by_else(self):
        # Empty state must be inside the else branch of data_available
        idx_empty = self.html.find('sector-tone-empty')
        # Look backwards for {% else %} before the empty state
        vicinity = self.html[max(0, idx_empty - 400):idx_empty]
        self.assertIn('{% else %}', vicinity)

    def test_data_available_conditional_present(self):
        self.assertIn('sector_management_tone.data_available', self.html)


# ---------------------------------------------------------------------------
# index.html — JavaScript toggle wiring
# ---------------------------------------------------------------------------

class TestSectorToneJavaScript(unittest.TestCase):
    """JS toggle must be wired in the DOMContentLoaded block."""

    def setUp(self):
        self.html = get_index_html()

    def test_sector_tone_toggle_js_present(self):
        self.assertIn("getElementById('sector-tone-toggle')", self.html)

    def test_sector_tone_content_js_present(self):
        self.assertIn("getElementById('sector-tone-content')", self.html)

    def test_sector_tone_toggle_text_js_present(self):
        self.assertIn("getElementById('sector-tone-toggle-text')", self.html)

    def test_js_adds_expanded_class(self):
        self.assertIn('sector-tone-content--expanded', self.html)

    def test_js_updates_aria_expanded(self):
        # JS must set aria-expanded
        idx = self.html.find("getElementById('sector-tone-toggle')")
        vicinity = self.html[idx:idx + 600]
        self.assertIn('aria-expanded', vicinity)

    def test_js_updates_toggle_text_show(self):
        self.assertIn("'Show Sectors'", self.html)

    def test_js_updates_toggle_text_hide(self):
        self.assertIn("'Hide Sectors'", self.html)

    def test_js_toggle_inside_domcontentloaded(self):
        # JS for sector tone toggle must be inside DOMContentLoaded
        idx_dcl = self.html.find('DOMContentLoaded')
        idx_toggle = self.html.find("getElementById('sector-tone-toggle')")
        self.assertGreater(idx_toggle, idx_dcl,
                           "Sector tone toggle JS must be inside DOMContentLoaded")


# ---------------------------------------------------------------------------
# Accessibility checks
# ---------------------------------------------------------------------------

class TestSectorToneAccessibility(unittest.TestCase):
    """Accessibility requirements per spec."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_has_aria_label(self):
        self.assertIn('aria-label="Sector Management Tone"', self.html)

    def test_tone_icons_have_aria_hidden(self):
        # All tone icons must be aria-hidden (text label is always present)
        idx = self.html.find('sector-card__tone-icon')
        vicinity = self.html[idx:idx + 200]
        self.assertIn('aria-hidden="true"', vicinity)

    def test_sparkline_dots_individually_aria_hidden(self):
        idx = self.html.find('sector-sparkline-dot--placeholder')
        vicinity = self.html[idx:idx + 200]
        self.assertIn('aria-hidden="true"', vicinity)

    def test_sparkline_container_has_aria_label(self):
        idx = self.html.find('sector-card__sparkline')
        vicinity = self.html[idx:idx + 300]
        self.assertIn('aria-label=', vicinity)

    def test_toggle_chevron_is_aria_hidden(self):
        idx = self.html.find('sector-tone-chevron')
        vicinity = self.html[max(0, idx - 10):idx + 100]
        self.assertIn('aria-hidden="true"', vicinity)

    def test_color_not_used_alone_for_tone(self):
        # All three tones have both icon AND text label (never color alone)
        # Verify tone-label classes are all present
        self.assertIn('sector-card__tone-label--positive', self.html)
        self.assertIn('sector-card__tone-label--neutral', self.html)
        self.assertIn('sector-card__tone-label--negative', self.html)


# ---------------------------------------------------------------------------
# Regression guard — existing sections unaffected
# ---------------------------------------------------------------------------

class TestSectorToneNoRegressions(unittest.TestCase):
    """Existing sections must be unchanged."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_0_macro_regime_still_present(self):
        self.assertIn('id="macro-regime-section"', self.html)

    def test_section_05_recession_panel_still_present(self):
        self.assertIn('id="recession-panel-section"', self.html)

    def test_section_075_regime_implications_still_present(self):
        self.assertIn('id="regime-implications"', self.html)

    def test_section_1_market_conditions_still_present(self):
        self.assertIn('id="market-conditions"', self.html)

    def test_base_html_existing_css_links_intact(self):
        base = get_base_html()
        self.assertIn('regime-implications.css', base)
        self.assertIn('recession-panel.css', base)
        self.assertIn('regime-card.css', base)

    def test_sector_tone_css_added_after_regime_implications(self):
        # CSS links must be in order: regime-implications.css ... sector-tone.css
        base = get_base_html()
        idx_ri = base.find('regime-implications.css')
        idx_st = base.find('sector-tone.css')
        self.assertGreater(idx_st, idx_ri,
                           "sector-tone.css must come after regime-implications.css in base.html")


if __name__ == '__main__':
    unittest.main()
