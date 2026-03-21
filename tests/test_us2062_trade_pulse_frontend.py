"""
Tests for US-206.2: Global Trade Pulse — Frontend: Homepage Panel Implementation
"""
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
INDEX_HTML = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
BASE_HTML = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'base.html')
TRADE_PULSE_CSS = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'trade-pulse.css')


def get_index_html():
    with open(INDEX_HTML, 'r') as f:
        return f.read()


def get_base_html():
    with open(BASE_HTML, 'r') as f:
        return f.read()


def get_trade_pulse_css():
    with open(TRADE_PULSE_CSS, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# CSS file presence & content
# ---------------------------------------------------------------------------
class TestTradePulseCSSFile(unittest.TestCase):
    """CSS file trade-pulse.css exists and defines the required classes."""

    def setUp(self):
        self.css = get_trade_pulse_css()

    def test_css_file_exists(self):
        self.assertTrue(os.path.exists(TRADE_PULSE_CSS))

    def test_toggle_class_defined(self):
        self.assertIn('.trade-pulse-toggle', self.css)

    def test_content_class_defined(self):
        self.assertIn('.trade-pulse-content', self.css)

    def test_content_expanded_class_defined(self):
        self.assertIn('.trade-pulse-content--expanded', self.css)

    def test_content_collapsed_by_default(self):
        # max-height: 0 for collapsed state
        self.assertIn('max-height: 0', self.css)

    def test_toggle_hidden_on_tablet(self):
        # toggle hidden at 768px+
        self.assertIn('min-width: 768px', self.css)
        self.assertIn('display: none', self.css)

    def test_content_always_visible_on_tablet(self):
        self.assertIn('max-height: none', self.css)

    def test_percentile_bar_track_class(self):
        self.assertIn('.trade-pulse-pct-bar-track', self.css)

    def test_percentile_bar_fill_class(self):
        self.assertIn('.trade-pulse-pct-bar-fill', self.css)

    def test_category_trade_token(self):
        self.assertIn('--category-trade', self.css)
        self.assertIn('#0D9488', self.css)

    def test_bar_height_8px(self):
        self.assertIn('height: 8px', self.css)

    def test_bar_border_radius_4px(self):
        self.assertIn('border-radius: 4px', self.css)

    def test_trade_pulse_grid_class(self):
        self.assertIn('.trade-pulse-grid', self.css)

    def test_grid_two_column_on_tablet(self):
        self.assertIn('flex-direction: row', self.css)


# ---------------------------------------------------------------------------
# base.html — CSS link
# ---------------------------------------------------------------------------
class TestTradePulseCSSLink(unittest.TestCase):
    """base.html loads trade-pulse.css."""

    def setUp(self):
        self.html = get_base_html()

    def test_css_link_present(self):
        self.assertIn('trade-pulse.css', self.html)

    def test_css_link_uses_url_for(self):
        self.assertIn("url_for('static', filename='css/components/trade-pulse.css')", self.html)


# ---------------------------------------------------------------------------
# index.html — section structure
# ---------------------------------------------------------------------------
class TestTradePulseSectionStructure(unittest.TestCase):
    """Trade Pulse section present in index.html with correct structure."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_id_present(self):
        self.assertIn('id="trade-pulse-section"', self.html)

    def test_section_aria_label(self):
        self.assertIn('aria-label="Global Trade Pulse"', self.html)

    def test_section_title_global_trade_pulse(self):
        self.assertIn('Global Trade Pulse', self.html)

    def test_section_subtitle_fred_bopgstb(self):
        self.assertIn('FRED BOPGSTB', self.html)

    def test_section_guarded_by_trade_balance_value(self):
        # Section should only render when trade_balance_value is not none
        self.assertIn('trade_balance_value is not none', self.html)

    def test_section_placed_after_market_conditions(self):
        market_pos = self.html.find('id="market-conditions"')
        trade_pos = self.html.find('id="trade-pulse-section"')
        self.assertGreater(trade_pos, market_pos,
                           "Trade Pulse section must appear after market-conditions")

    def test_section_placed_before_briefing(self):
        trade_pos = self.html.find('id="trade-pulse-section"')
        briefing_pos = self.html.find('id="briefing-section"')
        self.assertLess(trade_pos, briefing_pos,
                        "Trade Pulse section must appear before briefing-section")


# ---------------------------------------------------------------------------
# index.html — trade_balance_value display
# ---------------------------------------------------------------------------
class TestTradePulseMetricPanel(unittest.TestCase):
    """Metric panel renders current value, period, and YoY badge."""

    def setUp(self):
        self.html = get_index_html()

    def test_trade_balance_value_rendered(self):
        self.assertIn('trade_balance_value', self.html)

    def test_negative_value_uses_minus_sign(self):
        # Negative trade balance uses &minus; for correct rendering
        self.assertIn('&minus;', self.html)

    def test_value_formatted_with_1_decimal(self):
        self.assertIn('"%.1f"', self.html)

    def test_trade_balance_period_rendered(self):
        self.assertIn('trade_balance_period', self.html)

    def test_yoy_direction_up_arrow(self):
        self.assertIn("trade_yoy_direction == 'up'", self.html)

    def test_yoy_up_uses_success_color(self):
        # Success color for upward YoY
        idx = self.html.find("trade_yoy_direction == 'up'")
        block = self.html[idx:idx + 300]
        self.assertIn('#16A34A', block)

    def test_yoy_down_uses_danger_color(self):
        # Danger color for downward YoY
        idx = self.html.find("trade_yoy_direction == 'up'")
        block = self.html[idx:idx + 400]
        self.assertIn('#DC2626', block)

    def test_yoy_arrow_icon_aria_hidden(self):
        self.assertIn('aria-hidden="true"', self.html)

    def test_prior_year_computed_from_period(self):
        # Jinja2 computes prior year by subtracting 1 from period year
        self.assertIn("_period_parts[1]|int - 1", self.html)

    def test_current_value_font_mono(self):
        idx = self.html.find('trade-pulse-current-value')
        block = self.html[idx:idx + 300]
        self.assertIn('monospace', block)

    def test_yoy_guarded_by_not_none(self):
        self.assertIn('trade_yoy_change is not none', self.html)

    def test_yoy_min_tap_target(self):
        # YoY badge row has min-height for tap target
        idx = self.html.find('trade_yoy_direction')
        block = self.html[max(0, idx - 200):idx + 50]
        self.assertIn('min-height:44px', block)


# ---------------------------------------------------------------------------
# index.html — percentile bar
# ---------------------------------------------------------------------------
class TestTradePulsePercentileBar(unittest.TestCase):
    """Percentile bar renders with correct accessibility and color logic."""

    def setUp(self):
        self.html = get_index_html()

    def test_percentile_bar_role_progressbar(self):
        self.assertIn('role="progressbar"', self.html)

    def test_aria_valuenow(self):
        self.assertIn('aria-valuenow=', self.html)

    def test_aria_valuemin_0(self):
        self.assertIn('aria-valuemin="0"', self.html)

    def test_aria_valuemax_100(self):
        self.assertIn('aria-valuemax="100"', self.html)

    def test_aria_label_on_bar(self):
        idx = self.html.find('role="progressbar"')
        block = self.html[idx:idx + 300]
        self.assertIn('aria-label="Trade balance at', block)

    def test_percentile_guarded_by_not_none(self):
        self.assertIn('trade_percentile is not none', self.html)

    def test_percentile_value_displayed(self):
        self.assertIn('trade_percentile|round|int', self.html)

    def test_percentile_label_shows_pct(self):
        self.assertIn('th pct.', self.html)

    def test_five_tier_color_logic(self):
        # 0-25: danger; 26-40: warning; 41-60: neutral; 61-75: info; 76+: success
        self.assertIn('_pct <= 25', self.html)
        self.assertIn('_pct <= 40', self.html)
        self.assertIn('_pct <= 60', self.html)
        self.assertIn('_pct <= 75', self.html)

    def test_danger_color_for_low_percentile(self):
        idx = self.html.find('_pct <= 25')
        block = self.html[idx:idx + 100]
        self.assertIn('#DC2626', block)

    def test_warning_color_for_below_avg_percentile(self):
        idx = self.html.find('_pct <= 40')
        block = self.html[idx:idx + 100]
        self.assertIn('#CA8A04', block)

    def test_success_color_for_high_percentile(self):
        self.assertIn('#16A34A', self.html)

    def test_info_color_for_above_avg_percentile(self):
        self.assertIn('#0284C7', self.html)

    def test_weaker_label_when_below_50(self):
        self.assertIn('Weaker than', self.html)

    def test_stronger_label_when_above_50(self):
        self.assertIn('Stronger than', self.html)

    def test_10_year_range_label(self):
        self.assertIn('10-year range', self.html)

    def test_bar_uses_pct_bar_track_class(self):
        self.assertIn('class="trade-pulse-pct-bar-track"', self.html)

    def test_fill_uses_pct_bar_fill_class(self):
        self.assertIn('class="trade-pulse-pct-bar-fill"', self.html)


# ---------------------------------------------------------------------------
# index.html — interpretation block
# ---------------------------------------------------------------------------
class TestTradePulseInterpretationBlock(unittest.TestCase):
    """Regime-conditioned interpretation block renders correctly."""

    def setUp(self):
        self.html = get_index_html()

    def test_interpretation_guarded_by_body(self):
        self.assertIn('trade_interpretation_body', self.html)

    def test_category_trade_color_on_left_border(self):
        idx = self.html.find('trade_interpretation_body')
        block = self.html[idx:idx + 500]
        self.assertIn('#0D9488', block)

    def test_lightbulb_icon_present(self):
        self.assertIn('bi-lightbulb-fill', self.html)

    def test_lightbulb_icon_aria_hidden(self):
        idx = self.html.find('bi-lightbulb-fill')
        block = self.html[idx:idx + 100]
        self.assertIn('aria-hidden="true"', block)

    def test_interpretation_label_rendered(self):
        self.assertIn('trade_interpretation_label', self.html)

    def test_interpretation_label_uppercase(self):
        # span wrapping interpretation label has uppercase style
        idx = self.html.find('trade_interpretation_label')
        block = self.html[max(0, idx - 300):idx + 50]
        self.assertIn('text-transform:uppercase', block)

    def test_interpretation_label_letter_spacing(self):
        # span wrapping interpretation label has letter-spacing
        idx = self.html.find('trade_interpretation_label')
        block = self.html[max(0, idx - 300):idx + 50]
        self.assertIn('letter-spacing', block)

    def test_interpretation_body_rendered(self):
        self.assertIn('trade_interpretation_body', self.html)

    def test_interpretation_body_line_height(self):
        # p tag wrapping {{ trade_interpretation_body }} has line-height
        idx = self.html.rfind('trade_interpretation_body')  # last occurrence = rendering
        block = self.html[max(0, idx - 200):idx + 50]
        self.assertIn('line-height:1.65', block)

    def test_neutral_50_background(self):
        self.assertIn('#FAFBFC', self.html)

    def test_left_border_4px(self):
        self.assertIn('border-left:4px solid #0D9488', self.html)


# ---------------------------------------------------------------------------
# index.html — data freshness line
# ---------------------------------------------------------------------------
class TestTradePulseDataFreshness(unittest.TestCase):
    """Data freshness line renders correctly."""

    def setUp(self):
        self.html = get_index_html()

    def test_last_updated_label(self):
        self.assertIn('Last Updated:', self.html)

    def test_trade_last_updated_variable(self):
        self.assertIn('trade_last_updated', self.html)

    def test_fred_bopgstb_source(self):
        # Data freshness line references FRED BOPGSTB
        idx = self.html.find('Last Updated:')
        block = self.html[idx:idx + 100]
        self.assertIn('FRED BOPGSTB', block)

    def test_freshness_guarded_by_not_none(self):
        # {% if trade_last_updated %} guard should exist somewhere in the file
        self.assertIn('if trade_last_updated', self.html)


# ---------------------------------------------------------------------------
# index.html — mobile collapse toggle
# ---------------------------------------------------------------------------
class TestTradePulseMobileToggle(unittest.TestCase):
    """Mobile collapse toggle button present and correctly wired."""

    def setUp(self):
        self.html = get_index_html()

    def test_toggle_button_id(self):
        self.assertIn('id="trade-pulse-toggle"', self.html)

    def test_toggle_aria_expanded_false(self):
        idx = self.html.find('id="trade-pulse-toggle"')
        block = self.html[max(0, idx - 100):idx + 300]
        self.assertIn('aria-expanded="false"', block)

    def test_toggle_aria_controls(self):
        idx = self.html.find('id="trade-pulse-toggle"')
        block = self.html[max(0, idx - 100):idx + 300]
        self.assertIn('aria-controls="trade-pulse-content"', block)

    def test_toggle_text_id(self):
        self.assertIn('id="trade-pulse-toggle-text"', self.html)

    def test_toggle_default_text(self):
        self.assertIn('View Trade Data', self.html)

    def test_chevron_icon_present(self):
        self.assertIn('trade-pulse-chevron', self.html)

    def test_content_div_id(self):
        self.assertIn('id="trade-pulse-content"', self.html)

    def test_content_uses_collapse_class(self):
        self.assertIn('class="trade-pulse-content"', self.html)

    def test_toggle_lines_present(self):
        self.assertIn('class="trade-pulse-toggle-line"', self.html)

    def test_js_toggle_handler_present(self):
        self.assertIn('trade-pulse-toggle', self.html)
        self.assertIn('trade-pulse-content--expanded', self.html)

    def test_js_expanded_adds_class(self):
        idx = self.html.find('trade-pulse-content--expanded')
        block = self.html[max(0, idx - 100):idx + 200]
        self.assertIn('classList.add', block)

    def test_js_collapsed_removes_class(self):
        idx = self.html.rfind('trade-pulse-content--expanded')
        block = self.html[max(0, idx - 50):idx + 100]
        self.assertIn('classList.remove', block)


# ---------------------------------------------------------------------------
# index.html — quick-nav integration
# ---------------------------------------------------------------------------
class TestTradePulseQuickNav(unittest.TestCase):
    """Trade pill added to desktop nav and mobile sheet."""

    def setUp(self):
        self.html = get_index_html()

    def test_desktop_trade_pill_present(self):
        self.assertIn('data-target="#trade-pulse-section"', self.html)
        # Check it's in section-quick-nav__pill context
        idx = self.html.find('data-target="#trade-pulse-section"')
        block = self.html[max(0, idx - 200):idx + 100]
        self.assertTrue(
            'section-quick-nav__pill' in block or 'section-quick-nav-sheet__item' in block,
            "Trade target should be in nav pill or sheet item"
        )

    def test_desktop_trade_pill_label(self):
        # Both desktop pill and mobile sheet should show "Trade"
        count = self.html.count('data-target="#trade-pulse-section"')
        self.assertGreaterEqual(count, 2, "Trade target should appear in both desktop nav and mobile sheet")

    def test_desktop_pill_after_markets(self):
        # Trade pill should come after Markets pill in desktop nav
        markets_pos = self.html.find('data-target="#market-conditions"')
        trade_pos = self.html.find('data-target="#trade-pulse-section"')
        self.assertGreater(trade_pos, markets_pos,
                           "Trade pill should appear after Markets in nav")

    def test_desktop_pill_before_briefing(self):
        # Trade pill should come before Briefing pill
        trade_pos = self.html.find('data-target="#trade-pulse-section"')
        briefing_pos = self.html.find('data-target="#briefing-section"')
        self.assertLess(trade_pos, briefing_pos,
                        "Trade pill should appear before Briefing in nav")

    def test_mobile_sheet_trade_item_present(self):
        self.assertIn('section-quick-nav-sheet__item', self.html)
        # The mobile sheet uses the same data-target
        idx = self.html.rfind('data-target="#trade-pulse-section"')
        block = self.html[max(0, idx - 100):idx + 100]
        self.assertIn('section-quick-nav-sheet__item', block)

    def test_trade_pill_text_is_trade(self):
        # Check that a button with data-target="#trade-pulse-section" contains "Trade" text
        idx = self.html.find('data-target="#trade-pulse-section"')
        # data-target attribute is ~35 chars; read enough to get the button text
        block = self.html[idx:idx + 60]
        self.assertIn('Trade', block)


# ---------------------------------------------------------------------------
# index.html — accessibility requirements
# ---------------------------------------------------------------------------
class TestTradePulseAccessibility(unittest.TestCase):
    """Key accessibility requirements satisfied."""

    def setUp(self):
        self.html = get_index_html()

    def test_section_has_aria_label(self):
        self.assertIn('aria-label="Global Trade Pulse"', self.html)

    def test_progressbar_role_on_percentile_bar(self):
        self.assertIn('role="progressbar"', self.html)

    def test_progressbar_aria_valuenow(self):
        self.assertIn('aria-valuenow=', self.html)

    def test_progressbar_aria_valuemin(self):
        self.assertIn('aria-valuemin="0"', self.html)

    def test_progressbar_aria_valuemax(self):
        self.assertIn('aria-valuemax="100"', self.html)

    def test_progressbar_aria_label(self):
        idx = self.html.find('role="progressbar"')
        block = self.html[idx:idx + 300]
        self.assertIn('aria-label=', block)

    def test_decorative_icons_aria_hidden(self):
        # YoY arrow icons and lightbulb should be aria-hidden
        # Count aria-hidden occurrences in trade pulse section
        section_start = self.html.find('id="trade-pulse-section"')
        section_end = self.html.find('<!-- Section 2:', section_start)
        if section_end == -1:
            section_end = section_start + 5000
        section = self.html[section_start:section_end]
        self.assertIn('aria-hidden="true"', section)

    def test_toggle_aria_expanded_attribute(self):
        self.assertIn('aria-expanded="false"', self.html)
        # JS sets aria-expanded dynamically (may use single or double quotes)
        self.assertTrue(
            'setAttribute("aria-expanded"' in self.html or
            "setAttribute('aria-expanded'" in self.html,
            "JS should call setAttribute for aria-expanded"
        )


if __name__ == '__main__':
    unittest.main()
