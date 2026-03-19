"""
Bug #343 — Responsive typography for desktop viewports.

Tests that all five affected CSS component files include @media breakpoints
that scale typography for larger viewports, consistent with the design system.
"""
import os
import re
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_DIR = os.path.join(REPO_ROOT, "signaltrackers", "static", "css", "components")


def _read_css(filename):
    path = os.path.join(CSS_DIR, filename)
    with open(path, "r") as f:
        return f.read()


# ─── helpers ────────────────────────────────────────────────────────

def _extract_media_blocks(css, min_width):
    """Extract all rule bodies inside @media (min-width: <min_width>px) blocks."""
    pattern = rf"@media\s*\(min-width:\s*{min_width}px\)\s*\{{(.*?)\n\}}"
    return re.findall(pattern, css, flags=re.DOTALL)


def _has_font_size_rule(blocks, selector):
    """Check if any media block contains a font-size rule for the given selector."""
    for block in blocks:
        # Look for selector followed by font-size within it
        sel_pattern = re.escape(selector) + r"\s*\{[^}]*font-size\s*:"
        if re.search(sel_pattern, block):
            return True
    return False


def _parse_font_size_rem(css_text, selector):
    """Extract the base (mobile) font-size value in rem for a selector.

    Strips @media blocks first to avoid matching scaled sizes.
    """
    # Remove @media blocks to get only base styles
    base_css = re.sub(r"@media\s*\([^)]*\)\s*\{.*?\n\}", "", css_text, flags=re.DOTALL)
    pattern = re.escape(selector) + r"\s*\{[^}]*font-size\s*:\s*([\d.]+)rem"
    m = re.search(pattern, base_css, flags=re.DOTALL)
    if m:
        return float(m.group(1))
    return None


# ═══ conditions-summary.css ═══════════════════════════════════════

class TestConditionsSummaryResponsive:
    """Verify responsive scaling in conditions-summary.css."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.css = _read_css("conditions-summary.css")
        self.blocks_768 = _extract_media_blocks(self.css, 768)
        self.blocks_1024 = _extract_media_blocks(self.css, 1024)

    def test_dimension_card_title_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".dimension-card__title")

    def test_dimension_card_title_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".dimension-card__title")

    def test_dimension_card_state_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".dimension-card__state")

    def test_dimension_card_state_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".dimension-card__state")

    def test_quadrant_label_svg_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".quadrant-label")

    def test_quadrant_name_label_svg_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".quadrant-name-label")

    def test_implications_thead_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".implications-table thead th")

    def test_implications_thead_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".implications-table thead th")

    def test_implications_tbody_th_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".implications-table tbody th")

    def test_implications_tbody_td_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".implications-table tbody td")

    def test_movers_strip_title_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".movers-strip__title")

    def test_risk_score_segments_scales_at_768(self):
        # Combined selector; check for risk-score-bar__segments
        found = any("risk-score-bar__segments" in b and "font-size" in b for b in self.blocks_768)
        assert found

    def test_hero_name_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".quadrant-hero__name")

    def test_base_dimension_card_title_is_small(self):
        """Base font-size for .dimension-card__title should be 0.6875rem (11px)."""
        assert _parse_font_size_rem(self.css, ".dimension-card__title") == 0.6875

    def test_metric_row_scales_at_768(self):
        # Check for dimension-metric-row__label or __value in 768 block
        found = any("dimension-metric-row__label" in b and "font-size" in b for b in self.blocks_768)
        assert found


# ═══ conditions-strip.css ═════════════════════════════════════════

class TestConditionsStripResponsive:
    """Verify responsive scaling in conditions-strip.css."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.css = _read_css("conditions-strip.css")
        self.blocks_1024 = _extract_media_blocks(self.css, 1024)

    def test_strip_name_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".conditions-strip__name")

    def test_strip_dim_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".conditions-strip__dim")

    def test_strip_context_text_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".conditions-strip__context-text")

    def test_base_name_is_0875rem(self):
        assert _parse_font_size_rem(self.css, ".conditions-strip__name") == 0.875

    def test_base_dim_is_0875rem(self):
        assert _parse_font_size_rem(self.css, ".conditions-strip__dim") == 0.875


# ═══ regime-pill.css ══════════════════════════════════════════════

class TestRegimePillResponsive:
    """Verify responsive scaling in regime-pill.css."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.css = _read_css("regime-pill.css")
        self.blocks_768 = _extract_media_blocks(self.css, 768)

    def test_pill_uses_rem_not_px(self):
        """Regime pill should use rem units, not fixed px."""
        # Find the base .regime-pill font-size — should be rem, not px
        m = re.search(r"\.regime-pill\s*\{[^}]*font-size\s*:\s*([\d.]+)(rem|px)", self.css, flags=re.DOTALL)
        assert m is not None
        assert m.group(2) == "rem", f"Expected rem units, got {m.group(2)}"

    def test_pill_base_size_is_075rem(self):
        assert _parse_font_size_rem(self.css, ".regime-pill") == 0.75

    def test_pill_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".regime-pill")


# ═══ regime-implications.css ══════════════════════════════════════

class TestRegimeImplicationsResponsive:
    """Verify responsive scaling in regime-implications.css."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.css = _read_css("regime-implications.css")
        self.blocks_768 = _extract_media_blocks(self.css, 768)
        self.blocks_1024 = _extract_media_blocks(self.css, 1024)

    def test_card_label_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".implication-card-label")

    def test_card_label_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".implication-card-label")

    def test_sectors_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".implication-sectors")

    def test_sectors_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".implication-sectors")

    def test_footer_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".regime-implications-footer")

    def test_footer_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".regime-implications-footer")

    def test_annotation_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".implication-annotation")

    def test_base_card_label_is_075rem(self):
        assert _parse_font_size_rem(self.css, ".implication-card-label") == 0.75

    def test_base_annotation_is_0875rem(self):
        assert _parse_font_size_rem(self.css, ".implication-annotation") == 0.875


# ═══ sector-tone.css ══════════════════════════════════════════════

class TestSectorToneResponsive:
    """Verify responsive scaling in sector-tone.css."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.css = _read_css("sector-tone.css")
        self.blocks_768 = _extract_media_blocks(self.css, 768)
        self.blocks_1024 = _extract_media_blocks(self.css, 1024)

    def test_header_right_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".sector-tone-header-right")

    def test_header_right_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".sector-tone-header-right")

    def test_regime_link_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".sector-tone-regime-link")

    def test_regime_link_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".sector-tone-regime-link")

    def test_quarter_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".sector-card__quarter")

    def test_quarter_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".sector-card__quarter")

    def test_footer_scales_at_768(self):
        assert _has_font_size_rule(self.blocks_768, ".sector-tone-footer")

    def test_footer_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".sector-tone-footer")

    def test_tone_label_scales_at_1024(self):
        assert _has_font_size_rule(self.blocks_1024, ".sector-card__tone-label")

    def test_base_header_right_is_075rem(self):
        assert _parse_font_size_rem(self.css, ".sector-tone-header-right") == 0.75

    def test_base_footer_is_075rem(self):
        assert _parse_font_size_rem(self.css, ".sector-tone-footer") == 0.75


# ═══ Cross-cutting: no font size below 12px ═══════════════════════

class TestMinimumFontSize:
    """No font-size should drop below 0.75rem (12px) at any breakpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.files = [
            "conditions-summary.css",
            "conditions-strip.css",
            "regime-pill.css",
            "regime-implications.css",
            "sector-tone.css",
        ]

    def test_no_font_below_075rem_in_desktop_breakpoints(self):
        """All rem font sizes in desktop breakpoints should be >= 0.75rem."""
        for filename in self.files:
            css = _read_css(filename)
            # Check only sizes inside @media blocks (desktop-scaled values)
            blocks_768 = _extract_media_blocks(css, 768)
            blocks_1024 = _extract_media_blocks(css, 1024)
            for block in blocks_768 + blocks_1024:
                matches = re.findall(r"font-size\s*:\s*([\d.]+)rem", block)
                for m in matches:
                    val = float(m)
                    assert val >= 0.75, (
                        f"{filename}: scaled font-size {val}rem ({val * 16}px) is below minimum 0.75rem (12px)"
                    )

    def test_no_font_below_10px(self):
        """All px font sizes should be >= 10px (SVG text at small sizes is acceptable at 10px)."""
        for filename in self.files:
            css = _read_css(filename)
            matches = re.findall(r"font-size\s*:\s*(\d+)px", css)
            for m in matches:
                val = int(m)
                assert val >= 10, (
                    f"{filename}: font-size {val}px is below minimum 10px"
                )


# ═══ Mobile unchanged: base styles preserved ═════════════════════

class TestMobileBasePreserved:
    """Base (mobile) font sizes should remain unchanged."""

    def test_conditions_summary_dimension_title_base(self):
        css = _read_css("conditions-summary.css")
        assert _parse_font_size_rem(css, ".dimension-card__title") == 0.6875

    def test_conditions_summary_dimension_state_base(self):
        css = _read_css("conditions-summary.css")
        assert _parse_font_size_rem(css, ".dimension-card__state") == 0.8125

    def test_conditions_strip_name_base(self):
        css = _read_css("conditions-strip.css")
        assert _parse_font_size_rem(css, ".conditions-strip__name") == 0.875

    def test_regime_pill_base(self):
        css = _read_css("regime-pill.css")
        assert _parse_font_size_rem(css, ".regime-pill") == 0.75

    def test_implication_card_label_base(self):
        css = _read_css("regime-implications.css")
        assert _parse_font_size_rem(css, ".implication-card-label") == 0.75

    def test_sector_tone_footer_base(self):
        css = _read_css("sector-tone.css")
        assert _parse_font_size_rem(css, ".sector-tone-footer") == 0.75
