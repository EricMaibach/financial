"""
Tests for US-4.1.4: Frontend — Category relevance dots on homepage badge-cards

Tests are static (no running server required). They verify:
- Template renders regime-relevance dots on flagged badge-cards
- Template uses _relevance / macro_regime.category_relevance (data-driven, not hardcoded)
- CSS defines .regime-dot and .badge-card.regime-highlighted correctly
- Regime config REGIME_CATEGORY_RELEVANCE covers all four regimes
- Edge cases: no regime, zero flags, all flags
"""

import os
import re
import sys
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'index.html')
CSS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css', 'components', 'regime-card.css')
REGIME_CONFIG = os.path.join(REPO_ROOT, 'signaltrackers', 'regime_config.py')


def _read(path):
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. Template — dot rendering logic
# ---------------------------------------------------------------------------

class TestTemplateDotRendering:
    def test_relevance_variable_set_from_macro_regime(self):
        """Template derives _relevance from macro_regime.category_relevance (not hardcoded)."""
        src = _read(INDEX_HTML)
        assert 'macro_regime.category_relevance' in src

    def test_regime_css_variable_set(self):
        """Template derives _regime_css from macro_regime.css_class."""
        src = _read(INDEX_HTML)
        assert 'macro_regime.css_class' in src

    def test_regime_state_variable_set(self):
        """Template derives _regime_state from macro_regime.state."""
        src = _read(INDEX_HTML)
        assert 'macro_regime.state' in src

    def test_graceful_degradation_no_macro_regime(self):
        """Template defaults relevance to [] when macro_regime is falsy."""
        src = _read(INDEX_HTML)
        # Pattern: _relevance = macro_regime.category_relevance if macro_regime else []
        assert 'else []' in src

    def test_credit_check_uses_relevance_variable(self):
        """Credit badge-card checks 'Credit' in _relevance (not hardcoded)."""
        src = _read(INDEX_HTML)
        assert "'Credit' in _relevance" in src

    def test_equities_check_uses_relevance_variable(self):
        src = _read(INDEX_HTML)
        assert "'Equities' in _relevance" in src

    def test_rates_check_uses_relevance_variable(self):
        src = _read(INDEX_HTML)
        assert "'Rates' in _relevance" in src

    def test_safe_havens_check_uses_relevance_variable(self):
        src = _read(INDEX_HTML)
        assert "'Safe Havens' in _relevance" in src

    def test_crypto_check_uses_relevance_variable(self):
        src = _read(INDEX_HTML)
        assert "'Crypto' in _relevance" in src

    def test_dollar_check_uses_relevance_variable(self):
        src = _read(INDEX_HTML)
        assert "'Dollar' in _relevance" in src


# ---------------------------------------------------------------------------
# 2. Template — regime-highlighted class on badge-cards
# ---------------------------------------------------------------------------

class TestTemplateBadgeHighlightClass:
    def test_regime_highlighted_class_applied_conditionally(self):
        """regime-highlighted class is conditionally added, not static on all cards."""
        src = _read(INDEX_HTML)
        assert 'regime-highlighted' in src

    def test_regime_highlighted_inside_jinja_conditional(self):
        """regime-highlighted is inside a Jinja2 if block."""
        src = _read(INDEX_HTML)
        # e.g.: "badge-card{% if 'Credit' in _relevance %} regime-highlighted{% endif %}"
        assert re.search(r'{%\s*if\s+\'\w[\w ]*\'\s+in\s+_relevance\s*%}\s*regime-highlighted', src)

    def test_all_six_cards_have_conditional_highlight(self):
        """All 6 badge-cards use conditional regime-highlighted class."""
        src = _read(INDEX_HTML)
        categories = ["'Credit'", "'Equities'", "'Rates'", "'Safe Havens'", "'Crypto'", "'Dollar'"]
        for cat in categories:
            assert cat in src, f"Missing relevance check for {cat}"


# ---------------------------------------------------------------------------
# 3. Template — dot span inside flagged cards
# ---------------------------------------------------------------------------

class TestTemplateDotSpan:
    def test_regime_dot_span_present_in_template(self):
        """regime-dot span is conditionally rendered inside badge-cards."""
        src = _read(INDEX_HTML)
        assert 'class="regime-dot' in src

    def test_regime_dot_uses_regime_css_class(self):
        """regime-dot span uses _regime_css variable for color class."""
        src = _read(INDEX_HTML)
        assert '{{ _regime_css }}' in src

    def test_regime_dot_is_aria_hidden(self):
        """regime-dot span is aria-hidden (decorative element)."""
        src = _read(INDEX_HTML)
        # Dot spans in badge-cards must be aria-hidden
        assert re.search(r'class="regime-dot[^"]*"[^>]*aria-hidden="true"', src)

    def test_regime_dot_inside_conditional_block(self):
        """Dot span is only rendered when category is in _relevance."""
        src = _read(INDEX_HTML)
        # Pattern: {% if '...' in _relevance %}<span class="regime-dot ...
        assert re.search(r'{%\s*if\s+\'\w[\w ]*\'\s+in\s+_relevance\s*%}\s*<span\s+class="regime-dot', src)


# ---------------------------------------------------------------------------
# 4. Template — tooltip and aria-label on highlighted cards
# ---------------------------------------------------------------------------

class TestTemplateTooltipAria:
    def test_title_tooltip_present_for_highlighted_cards(self):
        """title attribute (tooltip) is added to regime-highlighted badge-cards."""
        src = _read(INDEX_HTML)
        assert 'title="Highly relevant in current' in src

    def test_tooltip_includes_regime_state(self):
        """Tooltip text includes the dynamic regime state name."""
        src = _read(INDEX_HTML)
        assert 'Highly relevant in current {{ _regime_state }} regime' in src

    def test_aria_label_present_for_highlighted_cards(self):
        """aria-label is added to regime-highlighted badge-cards for screen readers."""
        src = _read(INDEX_HTML)
        assert 'aria-label=' in src
        # At least one of the categories should include regime relevance in aria-label
        assert 'Highly relevant in current {{ _regime_state }} regime' in src

    def test_tooltip_inside_conditional_block(self):
        """Tooltip/aria-label is only added when category is highlighted."""
        src = _read(INDEX_HTML)
        # title attribute should be inside a Jinja2 if block, not static on all cards
        # Check that it appears after an {% if ... in _relevance %} without an else before it
        assert re.search(r'{%\s*if\s+\'\w[\w ]*\'\s+in\s+_relevance\s*%}[^{]*title=', src)


# ---------------------------------------------------------------------------
# 5. CSS — .badge-card.regime-highlighted
# ---------------------------------------------------------------------------

class TestCSSBadgeHighlighted:
    def test_badge_card_regime_highlighted_has_position_relative(self):
        """badge-card.regime-highlighted has position: relative for dot anchoring."""
        src = _read(CSS_PATH)
        assert '.badge-card.regime-highlighted' in src
        # position: relative should appear after this selector
        idx = src.index('.badge-card.regime-highlighted')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'position: relative' in block

    def test_badge_card_regime_highlighted_rule_exists(self):
        src = _read(CSS_PATH)
        assert '.badge-card.regime-highlighted' in src


# ---------------------------------------------------------------------------
# 6. CSS — .badge-card .regime-dot (absolute positioning)
# ---------------------------------------------------------------------------

class TestCSSBadgeDot:
    def test_badge_card_dot_position_absolute(self):
        """Badge-card .regime-dot is absolutely positioned."""
        src = _read(CSS_PATH)
        assert '.badge-card .regime-dot' in src
        idx = src.index('.badge-card .regime-dot')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'position: absolute' in block

    def test_badge_card_dot_top_right_position(self):
        """Badge-card .regime-dot is positioned top-right."""
        src = _read(CSS_PATH)
        idx = src.index('.badge-card .regime-dot')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'top:' in block
        assert 'right:' in block

    def test_badge_card_dot_6px_width(self):
        """Badge-card .regime-dot is 6px wide."""
        src = _read(CSS_PATH)
        idx = src.index('.badge-card .regime-dot')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert '6px' in block

    def test_badge_card_dot_6px_height(self):
        """Badge-card .regime-dot is 6px tall."""
        src = _read(CSS_PATH)
        idx = src.index('.badge-card .regime-dot')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        # Height should be 6px (appears twice — width and height, or as shorthand)
        assert block.count('6px') >= 2 or ('height: 6px' in block)


# ---------------------------------------------------------------------------
# 7. CSS — regime dot color selectors (direct class coloring)
# ---------------------------------------------------------------------------

class TestCSSRegimeDotColors:
    def test_dot_bull_color_selector(self):
        """Defines color for .regime-dot.regime-bull (direct class, not descendant)."""
        src = _read(CSS_PATH)
        assert '.regime-dot.regime-bull' in src

    def test_dot_neutral_color_selector(self):
        src = _read(CSS_PATH)
        assert '.regime-dot.regime-neutral' in src

    def test_dot_bear_color_selector(self):
        src = _read(CSS_PATH)
        assert '.regime-dot.regime-bear' in src

    def test_dot_recession_color_selector(self):
        src = _read(CSS_PATH)
        assert '.regime-dot.regime-recession' in src

    def test_dot_bull_uses_bull_border_token(self):
        src = _read(CSS_PATH)
        idx = src.index('.regime-dot.regime-bull')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'regime-bull-border' in block

    def test_dot_bear_uses_bear_border_token(self):
        src = _read(CSS_PATH)
        idx = src.index('.regime-dot.regime-bear')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'regime-bear-border' in block

    def test_dot_neutral_uses_neutral_border_token(self):
        src = _read(CSS_PATH)
        idx = src.index('.regime-dot.regime-neutral')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'regime-neutral-border' in block

    def test_dot_recession_uses_recession_border_token(self):
        src = _read(CSS_PATH)
        idx = src.index('.regime-dot.regime-recession')
        block_end = src.index('}', idx)
        block = src[idx:block_end]
        assert 'regime-recession-border' in block


# ---------------------------------------------------------------------------
# 8. Regime config — REGIME_CATEGORY_RELEVANCE
# ---------------------------------------------------------------------------

class TestRegimeCategoryRelevance:
    def _import_config(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, 'signaltrackers'))
        from regime_config import REGIME_CATEGORY_RELEVANCE
        return REGIME_CATEGORY_RELEVANCE

    def test_regime_category_relevance_exists(self):
        config = self._import_config()
        assert config is not None

    def test_all_four_regimes_present(self):
        config = self._import_config()
        for regime in ('Bull', 'Neutral', 'Bear', 'Recession Watch'):
            assert regime in config, f"Missing regime: {regime}"

    def test_each_regime_has_list_value(self):
        config = self._import_config()
        for regime, cats in config.items():
            assert isinstance(cats, list), f"{regime} relevance must be a list"

    def test_each_regime_flags_fewer_than_all_six(self):
        """Threshold approach: not all 6 categories are flagged in any regime."""
        config = self._import_config()
        all_six = {'Credit', 'Equities', 'Rates', 'Safe Havens', 'Crypto', 'Dollar'}
        for regime, cats in config.items():
            assert set(cats) != all_six, (
                f"Regime {regime} flags all 6 categories — should use threshold approach"
            )

    def test_bear_regime_flags_credit(self):
        config = self._import_config()
        assert 'Credit' in config['Bear']

    def test_bear_regime_flags_rates(self):
        config = self._import_config()
        assert 'Rates' in config['Bear']

    def test_bear_regime_flags_safe_havens(self):
        config = self._import_config()
        assert 'Safe Havens' in config['Bear']

    def test_bull_regime_flags_equities(self):
        config = self._import_config()
        assert 'Equities' in config['Bull']

    def test_recession_watch_has_most_flags(self):
        """Recession Watch should flag >= 3 categories (most stressed regime)."""
        config = self._import_config()
        assert len(config['Recession Watch']) >= 3

    def test_category_names_are_valid(self):
        """All category names must be from the known set."""
        config = self._import_config()
        valid = {'Credit', 'Equities', 'Rates', 'Safe Havens', 'Crypto', 'Dollar'}
        for regime, cats in config.items():
            for cat in cats:
                assert cat in valid, f"Unknown category '{cat}' in regime '{regime}'"


# ---------------------------------------------------------------------------
# 9. Template — no regime fallback (zero-dot state)
# ---------------------------------------------------------------------------

class TestTemplateZeroDotFallback:
    def test_no_dots_when_macro_regime_none(self):
        """When macro_regime is None, _relevance = [] → no dots rendered."""
        src = _read(INDEX_HTML)
        # The else clause should set _relevance to an empty list
        assert 'else []' in src

    def test_no_regime_highlighted_class_when_empty_relevance(self):
        """When _relevance is empty, no regime-highlighted class is conditionally added."""
        src = _read(INDEX_HTML)
        # All 6 checks are inside {% if '...' in _relevance %} blocks
        # Ensure none of the badge-cards unconditionally have regime-highlighted
        badge_card_lines = [
            line for line in src.split('\n')
            if 'badge-card' in line and 'regime-highlighted' in line
        ]
        for line in badge_card_lines:
            # Every line with both badge-card and regime-highlighted must be inside a Jinja if
            assert '{%' in line or 'regime-highlighted' in line.split('badge-card')[0] or \
                re.search(r'badge-card\{%.*regime-highlighted', line), \
                f"Unconditional regime-highlighted found: {line}"

    def test_six_badge_cards_all_have_conditional_dot_logic(self):
        """All 6 badge-cards have conditional dot rendering."""
        src = _read(INDEX_HTML)
        required_checks = [
            "'Credit' in _relevance",
            "'Equities' in _relevance",
            "'Rates' in _relevance",
            "'Safe Havens' in _relevance",
            "'Crypto' in _relevance",
            "'Dollar' in _relevance",
        ]
        for check in required_checks:
            assert check in src, f"Missing conditional: {check}"


# ---------------------------------------------------------------------------
# 10. Template — structural integrity (existing badge-cards not broken)
# ---------------------------------------------------------------------------

class TestTemplateBadgeCardIntegrity:
    def test_all_six_data_categories_present(self):
        """All 6 data-category attributes are still present after modification."""
        src = _read(INDEX_HTML)
        categories = ['credit', 'equities', 'rates', 'havens', 'crypto', 'dollar']
        for cat in categories:
            assert f'data-category="{cat}"' in src, f"Missing data-category={cat}"

    def test_all_six_badge_status_ids_present(self):
        """All 6 badge-status element IDs are present."""
        src = _read(INDEX_HTML)
        ids = [
            'badge-credit-status', 'badge-equities-status', 'badge-rates-status',
            'badge-havens-status', 'badge-crypto-status', 'badge-dollar-status',
        ]
        for bid in ids:
            assert bid in src, f"Missing badge status ID: {bid}"

    def test_badge_labels_intact(self):
        """Badge label texts are unchanged."""
        src = _read(INDEX_HTML)
        for label in ['CREDIT', 'EQUITIES', 'RATES', 'SAFE HAVENS', 'CRYPTO', 'DOLLAR']:
            assert label in src, f"Missing badge label: {label}"

    def test_market_badges_grid_container_present(self):
        src = _read(INDEX_HTML)
        assert 'id="market-badges"' in src
