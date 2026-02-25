"""
Static verification tests for US-5.1.2: Add trend direction row and fix confidence
visibility on mobile.

Tests inspect source files without requiring a live Flask server or market data.
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Section title update — AC: "Current Macro Regime" → "Macro Regime Score"
# ---------------------------------------------------------------------------

class TestSectionTitleUpdate(unittest.TestCase):
    """Section 0 title must be updated to 'Macro Regime Score'."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_h3_reads_macro_regime_score(self):
        """h3 text must read 'Macro Regime Score'."""
        self.assertIn('Macro Regime Score', self.html)

    def test_old_title_not_present(self):
        """Old title 'Current Macro Regime' must not appear (except in comments)."""
        # Strip comments before checking
        html_no_comments = re.sub(r'<!--.*?-->', '', self.html, flags=re.DOTALL)
        self.assertNotIn('Current Macro Regime', html_no_comments)

    def test_section_aria_label_updated(self):
        """Section aria-label must be 'Macro Regime Score'."""
        self.assertIn('aria-label="Macro Regime Score"', self.html)

    def test_section_id_unchanged(self):
        """Section id must remain 'macro-regime-section'."""
        self.assertIn('id="macro-regime-section"', self.html)

    def test_globe_icon_preserved(self):
        """Globe2 icon must still be present in the section header."""
        self.assertIn('bi-globe2', self.html)


# ---------------------------------------------------------------------------
# Trend row — HTML structure
# ---------------------------------------------------------------------------

class TestTrendRowHTMLStructure(unittest.TestCase):
    """index.html must contain the trend direction row with correct structure."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_trend_row_class_present(self):
        """regime-trend-row class must be present in the template."""
        self.assertIn('regime-trend-row', self.html)

    def test_mobile_variant_class_present(self):
        """Mobile-only trend row variant must use regime-trend-mobile class."""
        self.assertIn('regime-trend-mobile', self.html)

    def test_panel_variant_class_present(self):
        """Tablet+-only trend row variant must use regime-trend-panel class."""
        self.assertIn('regime-trend-panel', self.html)

    def test_trend_row_has_aria_label(self):
        """Trend row must have aria-label conveying trend value."""
        self.assertIn('aria-label="Trend: {{ macro_regime.trend | title }}"', self.html)

    def test_trend_conditional_guard(self):
        """Trend row must be guarded by {% if macro_regime.trend %}."""
        self.assertIn('macro_regime.trend', self.html)

    def test_trend_arrow_class_present(self):
        """regime-trend-arrow class must be present."""
        self.assertIn('regime-trend-arrow', self.html)

    def test_trend_arrow_modifier_dynamic(self):
        """Trend arrow modifier class must be dynamic (uses macro_regime.trend)."""
        self.assertIn('regime-trend-arrow--{{ macro_regime.trend }}', self.html)

    def test_improving_arrow_icon(self):
        """Improving trend must reference 'up-right' for bi-arrow-up-right icon."""
        # Template: class="bi bi-arrow-{{ 'up-right' if ... }}"
        self.assertIn("'up-right'", self.html)

    def test_stable_arrow_icon(self):
        """Stable trend must use bi-arrow-right icon."""
        # The template logic: 'right' if stable
        self.assertIn("'right'", self.html)

    def test_deteriorating_arrow_icon(self):
        """Deteriorating trend must reference 'down-right' for bi-arrow-down-right icon."""
        # Template: class="bi bi-arrow-{{ ... else 'down-right' }}"
        self.assertIn("'down-right'", self.html)

    def test_arrow_logic_inline_conditional(self):
        """Arrow icon is selected by Jinja2 inline if-else conditional."""
        self.assertIn("'up-right' if macro_regime.trend == 'improving'", self.html)

    def test_trend_confidence_class_present(self):
        """Trend row must include regime-trend-confidence for the confidence label."""
        self.assertIn('regime-trend-confidence', self.html)

    def test_confidence_uses_dynamic_color_class(self):
        """Confidence span must apply dynamic color class from confidence level."""
        self.assertIn('regime-confidence-{{ macro_regime.confidence | lower }}', self.html)

    def test_confidence_label_text(self):
        """Confidence span must render 'Confidence: {{ macro_regime.confidence }}'."""
        self.assertIn('Confidence: {{ macro_regime.confidence }}', self.html)

    def test_confidence_nested_conditional(self):
        """Confidence must be guarded inside trend row with {% if macro_regime.confidence %}."""
        # Both {% if macro_regime.trend %} and {% if macro_regime.confidence %} must exist
        self.assertIn('{% if macro_regime.trend %}', self.html)
        self.assertIn('{% if macro_regime.confidence %}', self.html)

    def test_arrow_icon_aria_hidden(self):
        """Decorative arrow icon must have aria-hidden='true'."""
        self.assertIn('aria-hidden="true"', self.html)


class TestTrendRowPlacement(unittest.TestCase):
    """Trend rows must appear in the correct DOM positions."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_mobile_trend_row_before_body_2col(self):
        """Mobile trend row must appear before regime-body-2col."""
        pos_mobile = self.html.find('regime-trend-mobile')
        pos_2col = self.html.find('regime-body-2col')
        self.assertGreater(pos_mobile, 0, "regime-trend-mobile not found")
        self.assertGreater(pos_2col, 0, "regime-body-2col not found")
        self.assertLess(pos_mobile, pos_2col,
                        "Mobile trend row must come before the 2-col body block")

    def test_mobile_trend_row_after_state_row(self):
        """Mobile trend row must appear after regime-state-row."""
        pos_state_row = self.html.find('regime-state-row')
        pos_mobile = self.html.find('regime-trend-mobile')
        self.assertGreater(pos_state_row, 0)
        self.assertGreater(pos_mobile, 0)
        self.assertLess(pos_state_row, pos_mobile,
                        "State row must come before mobile trend row")

    def test_panel_trend_row_inside_state_panel(self):
        """Tablet+ trend row must appear inside regime-state-panel."""
        pos_state_panel = self.html.find('regime-state-panel')
        pos_panel = self.html.find('regime-trend-panel')
        # The panel trend row must appear after regime-state-panel opens
        self.assertGreater(pos_state_panel, 0, "regime-state-panel not found")
        self.assertGreater(pos_panel, 0, "regime-trend-panel not found")
        self.assertLess(pos_state_panel, pos_panel,
                        "Tablet+ trend row must appear inside state-panel block")

    def test_two_trend_row_instances_exist(self):
        """Both mobile and panel trend row variants must exist."""
        count = self.html.count('regime-trend-row')
        self.assertGreaterEqual(count, 2,
                                "Both regime-trend-mobile and regime-trend-panel must be present")


# ---------------------------------------------------------------------------
# CSS — trend row classes
# ---------------------------------------------------------------------------

class TestTrendRowCSS(unittest.TestCase):
    """regime-card.css must define trend row classes per spec."""

    def setUp(self):
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)

    def test_regime_trend_row_defined(self):
        """Base .regime-trend-row class must be defined."""
        self.assertIn('.regime-trend-row', self.css)

    def test_trend_row_uses_flex(self):
        """.regime-trend-row must use display: flex."""
        match = re.search(r'\.regime-trend-row\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match, ".regime-trend-row block not found")
        self.assertIn('display: flex', match.group(0))

    def test_trend_row_gap_defined(self):
        """.regime-trend-row must set gap (for space between arrow and confidence)."""
        match = re.search(r'\.regime-trend-row\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('gap:', match.group(0))

    def test_trend_row_margin_top_defined(self):
        """.regime-trend-row must have margin-top to separate from state row."""
        match = re.search(r'\.regime-trend-row\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('margin-top:', match.group(0))

    def test_regime_trend_arrow_defined(self):
        """.regime-trend-arrow class must be defined."""
        self.assertIn('.regime-trend-arrow', self.css)

    def test_trend_arrow_font_size(self):
        """.regime-trend-arrow must set font-size: 0.875rem (14px)."""
        match = re.search(r'\.regime-trend-arrow\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match, ".regime-trend-arrow block not found")
        self.assertIn('0.875rem', match.group(0))

    def test_trend_arrow_font_weight(self):
        """.regime-trend-arrow must set font-weight: 500."""
        match = re.search(r'\.regime-trend-arrow\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('font-weight: 500', match.group(0))

    def test_improving_color_defined(self):
        """.regime-trend-arrow--improving must use #16A34A (success-600)."""
        self.assertIn('.regime-trend-arrow--improving', self.css)
        match = re.search(r'\.regime-trend-arrow--improving\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('#16A34A', match.group(0))

    def test_stable_color_defined(self):
        """.regime-trend-arrow--stable must use #6b7280 (neutral-500)."""
        self.assertIn('.regime-trend-arrow--stable', self.css)
        match = re.search(r'\.regime-trend-arrow--stable\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('#6b7280', match.group(0))

    def test_deteriorating_color_defined(self):
        """.regime-trend-arrow--deteriorating must use #DC2626 (danger-600)."""
        self.assertIn('.regime-trend-arrow--deteriorating', self.css)
        match = re.search(r'\.regime-trend-arrow--deteriorating\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('#DC2626', match.group(0))

    def test_regime_trend_confidence_defined(self):
        """.regime-trend-confidence class must be defined."""
        self.assertIn('.regime-trend-confidence', self.css)

    def test_trend_confidence_font_size(self):
        """.regime-trend-confidence must use 0.875rem font-size."""
        match = re.search(r'\.regime-trend-confidence\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match, ".regime-trend-confidence block not found")
        self.assertIn('0.875rem', match.group(0))

    def test_trend_confidence_font_weight(self):
        """.regime-trend-confidence must use font-weight: 500."""
        match = re.search(r'\.regime-trend-confidence\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('font-weight: 500', match.group(0))

    def test_confidence_no_display_none_on_mobile(self):
        """Confidence must NOT have display:none on mobile (fixed in US-5.1.2)."""
        # The old .regime-confidence { display: none } must be gone
        # Verify: .regime-trend-confidence does NOT have display:none in its base block
        match = re.search(r'\.regime-trend-confidence\s*\{[^}]+\}', self.css, re.DOTALL)
        if match:
            self.assertNotIn('display: none', match.group(0),
                             ".regime-trend-confidence must not be hidden on mobile")

    def test_trend_mobile_class_defined(self):
        """.regime-trend-mobile must be defined (mobile-visible variant)."""
        self.assertIn('.regime-trend-mobile', self.css)

    def test_trend_panel_class_defined(self):
        """.regime-trend-panel must be defined (tablet+-visible variant)."""
        self.assertIn('.regime-trend-panel', self.css)

    def test_trend_panel_hidden_on_mobile(self):
        """.regime-trend-panel must be display:none on mobile."""
        match = re.search(r'\.regime-trend-panel\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match, ".regime-trend-panel base rule not found")
        self.assertIn('display: none', match.group(0))


class TestTrendRowCSSResponsive(unittest.TestCase):
    """Trend row responsive behavior at 768px breakpoint."""

    def setUp(self):
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)
        # Find the first 768px @media block start position and extract content after it.
        # We check that the responsive overrides appear after the breakpoint marker.
        idx = self.css.find('@media (min-width: 768px)')
        self.css_after_breakpoint = self.css[idx:] if idx != -1 else ''

    def test_768px_breakpoint_exists(self):
        self.assertIn('768px', self.css)

    def test_trend_mobile_hidden_at_tablet(self):
        """.regime-trend-mobile must be set to display:none in the 768px media block."""
        self.assertIn('.regime-trend-mobile', self.css_after_breakpoint,
                      ".regime-trend-mobile not found after 768px media query")
        # Find the rule and verify display:none
        match = re.search(r'\.regime-trend-mobile\s*\{[^}]+\}',
                          self.css_after_breakpoint, re.DOTALL)
        self.assertIsNotNone(match, ".regime-trend-mobile rule not found in responsive block")
        self.assertIn('display: none', match.group(0))

    def test_trend_panel_shown_at_tablet(self):
        """.regime-trend-panel must be set to display:flex in the 768px media block."""
        self.assertIn('.regime-trend-panel', self.css_after_breakpoint,
                      ".regime-trend-panel not found after 768px media query")
        # Find the rule and verify display:flex
        match = re.search(r'\.regime-trend-panel\s*\{[^}]+\}',
                          self.css_after_breakpoint, re.DOTALL)
        self.assertIsNotNone(match, ".regime-trend-panel rule not found in responsive block")
        self.assertIn('display: flex', match.group(0))


# ---------------------------------------------------------------------------
# Confidence color tokens still defined (used by regime-trend-confidence)
# ---------------------------------------------------------------------------

class TestConfidenceColorTokens(unittest.TestCase):
    """Confidence color classes must still be defined (now used by .regime-trend-confidence)."""

    def setUp(self):
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)

    def test_confidence_high_color(self):
        """High confidence must use #15803D (success-700)."""
        self.assertIn('.regime-confidence-high', self.css)
        match = re.search(r'\.regime-confidence-high\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('#15803D', match.group(0))

    def test_confidence_medium_color(self):
        """Medium confidence must use #A16207 (warning-700)."""
        self.assertIn('.regime-confidence-medium', self.css)
        match = re.search(r'\.regime-confidence-medium\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('#A16207', match.group(0))

    def test_confidence_low_color(self):
        """Low confidence must use #B91C1C (danger-700)."""
        self.assertIn('.regime-confidence-low', self.css)
        match = re.search(r'\.regime-confidence-low\s*\{[^}]+\}', self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('#B91C1C', match.group(0))


# ---------------------------------------------------------------------------
# No regressions — existing regime card elements preserved
# ---------------------------------------------------------------------------

class TestNoRegressions(unittest.TestCase):
    """Existing US-4.1.2 regime card elements must be unchanged."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )
        css_path = os.path.join(
            SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css'
        )
        self.css = read_file(css_path)

    def test_section_id_present(self):
        self.assertIn('id="macro-regime-section"', self.html)

    def test_regime_card_class_present(self):
        self.assertIn('class="regime-card', self.html)

    def test_regime_state_row_present(self):
        self.assertIn('regime-state-row', self.html)

    def test_regime_body_2col_present(self):
        self.assertIn('regime-body-2col', self.html)

    def test_regime_state_panel_present(self):
        self.assertIn('regime-state-panel', self.html)

    def test_regime_summary_mobile_present(self):
        self.assertIn('regime-summary-mobile', self.html)

    def test_regime_signal_chips_present(self):
        self.assertIn('regime-signal-chips', self.html)

    def test_signal_chip_2col_mobile_unchanged(self):
        """2-col chip grid on mobile must still exist."""
        self.assertIn('repeat(2, 1fr)', self.css)

    def test_signal_chip_3col_tablet_unchanged(self):
        """3-col chip grid on tablet+ must still exist."""
        self.assertIn('repeat(3, 1fr)', self.css)

    def test_regime_design_tokens_unchanged(self):
        """All four regime design token families must still be defined."""
        self.assertIn('--regime-bull-bg', self.css)
        self.assertIn('--regime-bear-bg', self.css)
        self.assertIn('--regime-neutral-bg', self.css)
        self.assertIn('--regime-recession-bg', self.css)

    def test_regime_divider_present(self):
        self.assertIn('regime-divider', self.html)

    def test_highlighted_signals_loop_present(self):
        self.assertIn('macro_regime.highlighted_signals', self.html)

    def test_signal_chip_role_listitem(self):
        self.assertIn('role="listitem"', self.html)

    def test_macro_regime_conditional_guard(self):
        self.assertIn('{% if macro_regime %}', self.html)


if __name__ == '__main__':
    unittest.main()
