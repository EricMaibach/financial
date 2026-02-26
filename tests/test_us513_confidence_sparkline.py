"""
Static verification tests for US-5.1.3: Add 14-day confidence sparkline to regime card.

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
# HTML — Mobile sparkline block
# ---------------------------------------------------------------------------

class TestMobileSparklineHTML(unittest.TestCase):
    """Mobile-only sparkline block must be present in index.html."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_regime_sparkline_mobile_class_present(self):
        """Mobile sparkline wrapper must use regime-sparkline-mobile class."""
        self.assertIn('regime-sparkline-mobile', self.html)

    def test_mobile_sparkline_guarded_by_confidence_history(self):
        """Mobile sparkline must be guarded by confidence_history length check."""
        self.assertIn('macro_regime.confidence_history', self.html)
        self.assertIn('confidence_history | length >= 3', self.html)

    def test_mobile_sparkline_has_section_div(self):
        """Mobile block must contain regime-sparkline-section div."""
        self.assertIn('regime-sparkline-section', self.html)

    def test_mobile_sparkline_has_label(self):
        """Mobile block must contain regime-sparkline-label div."""
        self.assertIn('regime-sparkline-label', self.html)
        self.assertIn('14-Day Confidence Trend', self.html)

    def test_mobile_sparkline_has_svg(self):
        """Mobile block must contain an SVG element."""
        self.assertIn('regime-sparkline', self.html)
        self.assertIn('<svg', self.html)

    def test_mobile_svg_viewbox(self):
        """SVG viewBox must be '0 0 100 32'."""
        self.assertIn('viewBox="0 0 100 32"', self.html)

    def test_mobile_svg_preserve_aspect_ratio(self):
        """SVG must have preserveAspectRatio='none'."""
        self.assertIn('preserveAspectRatio="none"', self.html)

    def test_mobile_svg_role_img(self):
        """SVG must have role='img' for accessibility."""
        self.assertIn('role="img"', self.html)

    def test_mobile_svg_aria_label(self):
        """SVG must have aria-label='14-day confidence trend'."""
        self.assertIn('aria-label="14-day confidence trend"', self.html)

    def test_mobile_svg_title_element(self):
        """SVG must contain a <title> element with accessible text."""
        self.assertIn('<title>14-day confidence trend</title>', self.html)

    def test_mobile_sparkline_has_polyline(self):
        """SVG must contain a polyline element."""
        self.assertIn('<polyline', self.html)

    def test_mobile_polyline_fill_none(self):
        """Polyline must have fill='none'."""
        self.assertIn('fill="none"', self.html)

    def test_mobile_polyline_stroke_current_color(self):
        """Polyline must use stroke='currentColor' for regime-aware coloring."""
        self.assertIn('stroke="currentColor"', self.html)

    def test_mobile_polyline_stroke_width(self):
        """Polyline stroke-width must be 2."""
        self.assertIn('stroke-width="2"', self.html)

    def test_mobile_polyline_stroke_linecap(self):
        """Polyline must have stroke-linecap='round'."""
        self.assertIn('stroke-linecap="round"', self.html)

    def test_mobile_polyline_stroke_linejoin(self):
        """Polyline must have stroke-linejoin='round'."""
        self.assertIn('stroke-linejoin="round"', self.html)

    def test_mobile_polyline_points_from_backend(self):
        """Polyline points must be populated from confidence_sparkline_points."""
        self.assertIn('confidence_sparkline_points', self.html)
        self.assertIn('points="{{ macro_regime.confidence_sparkline_points }}"', self.html)

    def test_mobile_sparkline_has_divider_above(self):
        """Mobile sparkline block must have a divider above it."""
        # The divider is inside the regime-sparkline-mobile wrapper
        html = self.html
        mobile_start = html.find('regime-sparkline-mobile')
        mobile_end = html.find('</div>', mobile_start + 200)
        # Find the section that includes the mobile block
        block_region = html[mobile_start:mobile_start + 800]
        self.assertIn('regime-divider', block_region)


# ---------------------------------------------------------------------------
# HTML — Tablet+ sparkline inside state panel
# ---------------------------------------------------------------------------

class TestTabletSparklineHTML(unittest.TestCase):
    """Sparkline must also appear inside .regime-state-panel for tablet+."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_sparkline_section_inside_state_panel(self):
        """regime-sparkline-section must appear inside regime-state-panel."""
        state_panel_start = self.html.find('class="regime-state-panel"')
        self.assertNotEqual(state_panel_start, -1, 'regime-state-panel not found')
        # Find the closing of the state panel div
        state_panel_end = self.html.find('</div>\n            </div>', state_panel_start)
        if state_panel_end == -1:
            state_panel_end = state_panel_start + 2000
        panel_region = self.html[state_panel_start:state_panel_end]
        self.assertIn('regime-sparkline-section', panel_region)

    def test_tablet_sparkline_guarded_by_confidence_history(self):
        """Tablet sparkline inside state panel must also check confidence_history length."""
        state_panel_start = self.html.find('class="regime-state-panel"')
        panel_region = self.html[state_panel_start:state_panel_start + 2000]
        self.assertIn('confidence_history', panel_region)
        self.assertIn('confidence_history | length >= 3', panel_region)

    def test_two_sparkline_placements_exist(self):
        """Both mobile and tablet+ sparkline placements must exist (two SVG elements)."""
        self.assertEqual(self.html.count('<svg class="regime-sparkline"'), 2)

    def test_two_polyline_placements_exist(self):
        """Both mobile and tablet+ SVGs must have polyline elements."""
        self.assertEqual(self.html.count('<polyline'), 2)

    def test_both_placements_have_title(self):
        """Both SVG elements must have <title> accessibility text."""
        self.assertEqual(self.html.count('<title>14-day confidence trend</title>'), 2)

    def test_both_placements_use_sparkline_points(self):
        """Both placements must reference confidence_sparkline_points."""
        self.assertEqual(self.html.count('confidence_sparkline_points'), 2)

    def test_mobile_block_comes_after_summary_mobile(self):
        """Mobile sparkline wrapper must appear AFTER regime-summary-mobile in template."""
        summary_mobile_pos = self.html.find('regime-summary-mobile')
        sparkline_mobile_pos = self.html.find('regime-sparkline-mobile')
        self.assertNotEqual(summary_mobile_pos, -1, 'regime-summary-mobile not found')
        self.assertNotEqual(sparkline_mobile_pos, -1, 'regime-sparkline-mobile not found')
        self.assertGreater(
            sparkline_mobile_pos, summary_mobile_pos,
            'regime-sparkline-mobile must come after regime-summary-mobile'
        )


# ---------------------------------------------------------------------------
# HTML — No-JS, no interactivity requirements
# ---------------------------------------------------------------------------

class TestSparklineNoJavaScript(unittest.TestCase):
    """Sparkline must be static SVG — no JavaScript required."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_sparkline_section_has_no_onclick(self):
        """Sparkline section must not have onclick handlers."""
        sparkline_idx = self.html.find('regime-sparkline-section')
        # Check the region around the sparkline for onclick
        region = self.html[sparkline_idx:sparkline_idx + 600]
        self.assertNotIn('onclick', region)

    def test_sparkline_svg_has_no_js_handlers(self):
        """SVG sparkline must not have JavaScript event attributes."""
        sparkline_idx = self.html.find('<svg class="regime-sparkline"')
        region = self.html[sparkline_idx:sparkline_idx + 400]
        self.assertNotIn('onmouseover', region)
        self.assertNotIn('onclick', region)
        self.assertNotIn('addEventListener', region)


# ---------------------------------------------------------------------------
# CSS — Sparkline classes
# ---------------------------------------------------------------------------

class TestSparklineCSS(unittest.TestCase):
    """regime-card.css must contain all sparkline styles."""

    def setUp(self):
        self.css = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css')
        )

    def test_regime_sparkline_mobile_class_defined(self):
        """.regime-sparkline-mobile CSS class must exist."""
        self.assertIn('.regime-sparkline-mobile', self.css)

    def test_regime_sparkline_section_class_defined(self):
        """.regime-sparkline-section CSS class must exist."""
        self.assertIn('.regime-sparkline-section', self.css)

    def test_sparkline_section_padding(self):
        """Sparkline section must have 12px 0 padding."""
        self.assertIn('padding: 12px 0', self.css)

    def test_regime_sparkline_label_class_defined(self):
        """.regime-sparkline-label CSS class must exist."""
        self.assertIn('.regime-sparkline-label', self.css)

    def test_sparkline_label_font_size(self):
        """Sparkline label must use text-xs (0.75rem)."""
        # Find the label block
        label_idx = self.css.find('.regime-sparkline-label')
        label_block = self.css[label_idx:label_idx + 200]
        self.assertIn('0.75rem', label_block)

    def test_sparkline_label_uppercase(self):
        """Sparkline label must be uppercase."""
        label_idx = self.css.find('.regime-sparkline-label')
        label_block = self.css[label_idx:label_idx + 200]
        self.assertIn('uppercase', label_block)

    def test_sparkline_label_letter_spacing(self):
        """Sparkline label must have letter-spacing for readability."""
        label_idx = self.css.find('.regime-sparkline-label')
        label_block = self.css[label_idx:label_idx + 200]
        self.assertIn('letter-spacing', label_block)

    def test_sparkline_label_neutral_500_color(self):
        """Sparkline label must use neutral-500 color (#6b7280)."""
        label_idx = self.css.find('.regime-sparkline-label')
        label_block = self.css[label_idx:label_idx + 200]
        self.assertIn('#6b7280', label_block)

    def test_regime_sparkline_class_defined(self):
        """.regime-sparkline CSS class must exist."""
        self.assertIn('.regime-sparkline', self.css)

    def test_sparkline_display_block(self):
        """Sparkline must be display:block."""
        sparkline_idx = self.css.find('\n.regime-sparkline {')
        sparkline_block = self.css[sparkline_idx:sparkline_idx + 200]
        self.assertIn('display: block', sparkline_block)

    def test_sparkline_width_full(self):
        """Sparkline must be full-width (width: 100%)."""
        sparkline_idx = self.css.find('\n.regime-sparkline {')
        sparkline_block = self.css[sparkline_idx:sparkline_idx + 200]
        self.assertIn('width: 100%', sparkline_block)

    def test_sparkline_height_32px_mobile(self):
        """Sparkline height must be 32px on mobile."""
        sparkline_idx = self.css.find('\n.regime-sparkline {')
        sparkline_block = self.css[sparkline_idx:sparkline_idx + 200]
        self.assertIn('height: 32px', sparkline_block)

    def test_bull_regime_sparkline_color(self):
        """Bull regime sparkline must use bull border color token."""
        self.assertIn('.regime-bull .regime-sparkline', self.css)
        bull_idx = self.css.find('.regime-bull .regime-sparkline')
        bull_block = self.css[bull_idx:bull_idx + 100]
        self.assertIn('--regime-bull-border', bull_block)

    def test_neutral_regime_sparkline_color(self):
        """Neutral regime sparkline must use neutral border color token."""
        self.assertIn('.regime-neutral .regime-sparkline', self.css)
        neutral_idx = self.css.find('.regime-neutral .regime-sparkline')
        neutral_block = self.css[neutral_idx:neutral_idx + 100]
        self.assertIn('--regime-neutral-border', neutral_block)

    def test_bear_regime_sparkline_color(self):
        """Bear regime sparkline must use bear border color token."""
        self.assertIn('.regime-bear .regime-sparkline', self.css)
        bear_idx = self.css.find('.regime-bear .regime-sparkline')
        bear_block = self.css[bear_idx:bear_idx + 100]
        self.assertIn('--regime-bear-border', bear_block)

    def test_recession_regime_sparkline_color(self):
        """Recession regime sparkline must use recession border color token."""
        self.assertIn('.regime-recession .regime-sparkline', self.css)
        recession_idx = self.css.find('.regime-recession .regime-sparkline')
        recession_block = self.css[recession_idx:recession_idx + 100]
        self.assertIn('--regime-recession-border', recession_block)

    def test_sparkline_color_uses_color_property(self):
        """Regime sparkline must set 'color' (not 'stroke') so currentColor works."""
        # Look for 'color: var(--regime-...-border)' pattern
        self.assertIn('color: var(--regime-bull-border)', self.css)
        self.assertIn('color: var(--regime-neutral-border)', self.css)
        self.assertIn('color: var(--regime-bear-border)', self.css)
        self.assertIn('color: var(--regime-recession-border)', self.css)


# ---------------------------------------------------------------------------
# CSS — Responsive overrides (768px media query)
# ---------------------------------------------------------------------------

class TestSparklineCSSResponsive(unittest.TestCase):
    """Sparkline responsive CSS must hide mobile block and increase height on tablet+."""

    def setUp(self):
        self.css = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css')
        )

    def _get_sparkline_media_block(self):
        """Extract the 768px media block that contains sparkline rules.

        Sparkline overrides are merged into the annotation 768px block (the last one),
        so rfind finds it correctly.
        """
        idx = self.css.rfind('@media (min-width: 768px)')
        self.assertNotEqual(idx, -1, '768px media query not found')
        return self.css[idx:idx + 600]

    def test_sparkline_media_query_exists(self):
        """A 768px media query must contain sparkline overrides."""
        media_block = self._get_sparkline_media_block()
        self.assertIn('regime-sparkline', media_block)

    def test_mobile_sparkline_hidden_on_tablet(self):
        """regime-sparkline-mobile must be display:none at 768px+."""
        media_block = self._get_sparkline_media_block()
        self.assertIn('regime-sparkline-mobile', media_block)
        self.assertIn('display: none', media_block)

    def test_sparkline_height_36px_on_tablet(self):
        """Sparkline height must increase to 36px at 768px+."""
        media_block = self._get_sparkline_media_block()
        self.assertIn('36px', media_block)


# ---------------------------------------------------------------------------
# HTML — Existing elements not broken (regression guard)
# ---------------------------------------------------------------------------

class TestNoRegressions(unittest.TestCase):
    """Existing regime card elements must still be present after US-5.1.3 changes."""

    def setUp(self):
        self.html = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        )

    def test_regime_card_still_has_state_row(self):
        """Regime state row must still be present."""
        self.assertIn('regime-state-row', self.html)

    def test_regime_card_still_has_trend_row_mobile(self):
        """Mobile trend row from US-5.1.2 must still be present."""
        self.assertIn('regime-trend-mobile', self.html)

    def test_regime_card_still_has_trend_row_panel(self):
        """Tablet+ trend row from US-5.1.2 must still be present."""
        self.assertIn('regime-trend-panel', self.html)

    def test_regime_card_still_has_summary_mobile(self):
        """Mobile summary block must still be present."""
        self.assertIn('regime-summary-mobile', self.html)

    def test_regime_card_still_has_signal_chips(self):
        """Signal chips section must still be present."""
        self.assertIn('regime-signal-chips', self.html)

    def test_regime_card_still_has_divider_lg(self):
        """Large divider before signal chips must still be present."""
        self.assertIn('regime-divider-lg', self.html)

    def test_macro_regime_guard_still_present(self):
        """Top-level {% if macro_regime %} guard must still wrap all content."""
        self.assertIn('{% if macro_regime %}', self.html)

    def test_section_aria_label_unchanged(self):
        """Section aria-label must still be 'Macro Regime Score'."""
        self.assertIn('aria-label="Macro Regime Score"', self.html)

    def test_body_2col_still_present(self):
        """Two-column layout container must still be present."""
        self.assertIn('regime-body-2col', self.html)

    def test_state_panel_still_present(self):
        """State panel (left column on tablet+) must still be present."""
        self.assertIn('regime-state-panel', self.html)


# ---------------------------------------------------------------------------
# CSS — Existing classes not broken (regression guard)
# ---------------------------------------------------------------------------

class TestCSSNoRegressions(unittest.TestCase):
    """Existing regime-card.css classes must still be present after US-5.1.3."""

    def setUp(self):
        self.css = read_file(
            os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'regime-card.css')
        )

    def test_regime_trend_row_still_defined(self):
        """.regime-trend-row must still be defined (US-5.1.2)."""
        self.assertIn('.regime-trend-row', self.css)

    def test_regime_trend_mobile_still_defined(self):
        """.regime-trend-mobile must still be defined (US-5.1.2)."""
        self.assertIn('.regime-trend-mobile', self.css)

    def test_regime_trend_panel_still_defined(self):
        """.regime-trend-panel must still be defined (US-5.1.2)."""
        self.assertIn('.regime-trend-panel', self.css)

    def test_regime_confidence_high_still_defined(self):
        """.regime-confidence-high must still be defined."""
        self.assertIn('.regime-confidence-high', self.css)

    def test_regime_body_2col_still_defined(self):
        """.regime-body-2col must still be defined."""
        self.assertIn('.regime-body-2col', self.css)

    def test_regime_signal_chips_still_defined(self):
        """.regime-signal-chips must still be defined."""
        self.assertIn('.regime-signal-chips', self.css)

    def test_regime_design_tokens_still_defined(self):
        """CSS design tokens for all four regimes must still be present."""
        self.assertIn('--regime-bull-border', self.css)
        self.assertIn('--regime-bear-border', self.css)
        self.assertIn('--regime-neutral-border', self.css)
        self.assertIn('--regime-recession-border', self.css)


if __name__ == '__main__':
    unittest.main()
