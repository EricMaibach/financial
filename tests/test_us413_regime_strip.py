"""
Tests for US-4.1.3: Frontend — Detail page regime strip and signal annotations

Tests are static (no running server required). They verify:
- The context processor injects category_regime_context and signal_regime_annotations
- The regime strip partial renders correctly for each page category
- Regime annotations are present in all 5 detail templates
- CSS contains the required styles for strip and annotation components
- JS contains the initRegimeAnnotations function
"""

import os
import re
import sys
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(REPO_ROOT, 'signaltrackers', 'templates')
CSS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css', 'components', 'regime-card.css')
JS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'js', 'dashboard.js')
DASHBOARD_PY = os.path.join(REPO_ROOT, 'signaltrackers', 'dashboard.py')
REGIME_CONFIG = os.path.join(REPO_ROOT, 'signaltrackers', 'regime_config.py')


def _read(path):
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. Context processor — dashboard.py
# ---------------------------------------------------------------------------

class TestContextProcessor:
    def test_imports_category_regime_context(self):
        src = _read(DASHBOARD_PY)
        assert 'CATEGORY_REGIME_CONTEXT' in src

    def test_context_processor_returns_category_regime_context(self):
        src = _read(DASHBOARD_PY)
        assert "'category_regime_context': CATEGORY_REGIME_CONTEXT" in src

    def test_context_processor_returns_signal_regime_annotations(self):
        src = _read(DASHBOARD_PY)
        assert "'signal_regime_annotations': SIGNAL_REGIME_ANNOTATIONS" in src

    def test_context_processor_returns_macro_regime(self):
        src = _read(DASHBOARD_PY)
        assert "'macro_regime': regime" in src

    def test_inject_macro_regime_function_exists(self):
        src = _read(DASHBOARD_PY)
        assert 'def inject_macro_regime' in src


# ---------------------------------------------------------------------------
# 2. Regime config — CATEGORY_REGIME_CONTEXT
# ---------------------------------------------------------------------------

class TestRegimeConfig:
    def test_category_regime_context_has_all_categories(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, 'signaltrackers'))
        from regime_config import CATEGORY_REGIME_CONTEXT
        required = {'Rates', 'Equities', 'Dollar', 'Crypto', 'Safe Havens', 'Credit'}
        for cat in required:
            assert cat in CATEGORY_REGIME_CONTEXT, f"Missing category: {cat}"

    def test_category_regime_context_has_all_regimes(self):
        from regime_config import CATEGORY_REGIME_CONTEXT
        regimes = {'Bull', 'Neutral', 'Bear', 'Recession Watch'}
        for cat, sentences in CATEGORY_REGIME_CONTEXT.items():
            for regime in regimes:
                assert regime in sentences, f"Missing regime {regime} for category {cat}"

    def test_category_sentences_within_100_chars(self):
        from regime_config import CATEGORY_REGIME_CONTEXT
        for cat, sentences in CATEGORY_REGIME_CONTEXT.items():
            for regime, text in sentences.items():
                assert len(text) <= 100, (
                    f"Category '{cat}' regime '{regime}' sentence too long "
                    f"({len(text)} chars): {text!r}"
                )

    def test_signal_regime_annotations_exist(self):
        from regime_config import SIGNAL_REGIME_ANNOTATIONS
        required_signals = [
            'treasury_10y', 'yield_curve_10y2y', 'yield_curve_10y3m',
            'real_yield_10y', 'breakeven_inflation_10y', 'fed_funds_rate',
            'sp500', 'vix', 'dollar_index', 'gold',
            'fed_balance_sheet', 'nfci', 'm2_money_supply',
        ]
        for sig in required_signals:
            assert sig in SIGNAL_REGIME_ANNOTATIONS, f"Missing signal: {sig}"

    def test_signal_annotations_within_100_chars(self):
        from regime_config import SIGNAL_REGIME_ANNOTATIONS
        for sig, regime_map in SIGNAL_REGIME_ANNOTATIONS.items():
            for regime, text in regime_map.items():
                assert len(text) <= 100, (
                    f"Signal '{sig}' regime '{regime}' annotation too long "
                    f"({len(text)} chars): {text!r}"
                )


# ---------------------------------------------------------------------------
# 3. Regime strip partial — _regime_strip.html
# ---------------------------------------------------------------------------

class TestRegimeStripPartial:
    def test_partial_exists(self):
        path = os.path.join(TEMPLATES_DIR, '_regime_strip.html')
        assert os.path.exists(path)

    def test_partial_checks_macro_regime(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert '{% if macro_regime %}' in src

    def test_partial_uses_page_category(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'page_category' in src

    def test_partial_uses_category_regime_context(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'category_regime_context' in src

    def test_partial_has_regime_strip_element(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'class="regime-strip' in src

    def test_partial_has_regime_dot(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'regime-strip__dot' in src

    def test_partial_has_regime_name(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'regime-strip__name' in src

    def test_partial_has_context_sentence(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'regime-strip__context' in src

    def test_partial_has_aria_label(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'aria-label=' in src

    def test_partial_has_role_complementary(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_regime_strip.html'))
        assert 'role="complementary"' in src


# ---------------------------------------------------------------------------
# 4. Macros partial — _macros.html
# ---------------------------------------------------------------------------

class TestMacrosPartial:
    def test_macros_file_exists(self):
        path = os.path.join(TEMPLATES_DIR, '_macros.html')
        assert os.path.exists(path)

    def test_regime_annotation_macro_defined(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'macro regime_annotation' in src

    def test_macro_uses_signal_regime_annotations(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'signal_regime_annotations' in src

    def test_macro_uses_macro_regime_state(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'macro_regime.state' in src

    def test_macro_has_toggle_button(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'regime-annotation__toggle' in src

    def test_macro_has_aria_expanded(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'aria-expanded' in src

    def test_macro_has_annotation_text(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'regime-annotation__text' in src

    def test_macro_has_chevron_svg(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'regime-annotation__chevron' in src

    def test_macro_has_info_icon(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        assert 'bi-info-circle' in src

    def test_macro_conditional_on_empty_text(self):
        src = _read(os.path.join(TEMPLATES_DIR, '_macros.html'))
        # Macro should only render if annotation text is non-empty
        assert '{% if _text %}' in src


# ---------------------------------------------------------------------------
# 5. Detail page templates — strip present
# ---------------------------------------------------------------------------

DETAIL_PAGES = {
    'rates.html': 'Rates',
    'equity.html': 'Equities',
    'dollar.html': 'Dollar',
    'crypto.html': 'Crypto',
    'safe_havens.html': 'Safe Havens',
}


class TestDetailPageStrip:
    @pytest.mark.parametrize("template,category", DETAIL_PAGES.items())
    def test_template_includes_regime_strip(self, template, category):
        src = _read(os.path.join(TEMPLATES_DIR, template))
        assert "{% include '_regime_strip.html' %}" in src

    @pytest.mark.parametrize("template,category", DETAIL_PAGES.items())
    def test_template_sets_page_category(self, template, category):
        src = _read(os.path.join(TEMPLATES_DIR, template))
        assert f"page_category = '{category}'" in src

    @pytest.mark.parametrize("template,category", DETAIL_PAGES.items())
    def test_template_imports_regime_annotation_macro(self, template, category):
        src = _read(os.path.join(TEMPLATES_DIR, template))
        assert "from '_macros.html' import regime_annotation" in src

    @pytest.mark.parametrize("template,category", DETAIL_PAGES.items())
    def test_strip_after_header(self, template, category):
        src = _read(os.path.join(TEMPLATES_DIR, template))
        header_pos = src.find('</header>')
        strip_pos = src.find("{% include '_regime_strip.html' %}")
        content_grid_pos = src.find('<div class="content-grid">')
        assert header_pos < strip_pos, "Strip must come after </header>"
        assert strip_pos < content_grid_pos, "Strip must come before content-grid"


# ---------------------------------------------------------------------------
# 6. Detail page templates — annotations present
# ---------------------------------------------------------------------------

EXPECTED_ANNOTATIONS = {
    'rates.html': [
        'treasury_10y', 'yield_curve_10y2y', 'yield_curve_10y3m',
        'real_yield_10y', 'breakeven_inflation_10y', 'fed_funds_rate',
    ],
    'equity.html': ['sp500', 'vix'],
    'dollar.html': ['dollar_index'],
    'crypto.html': ['fed_balance_sheet', 'nfci', 'm2_money_supply'],
    'safe_havens.html': ['gold', 'real_yield_10y', 'breakeven_inflation_10y'],
}


class TestDetailPageAnnotations:
    @pytest.mark.parametrize("template,signals", EXPECTED_ANNOTATIONS.items())
    def test_template_has_all_expected_annotations(self, template, signals):
        src = _read(os.path.join(TEMPLATES_DIR, template))
        for sig in signals:
            assert f"regime_annotation('{sig}')" in src, (
                f"Template {template} missing annotation for signal '{sig}'"
            )


# ---------------------------------------------------------------------------
# 7. CSS — regime-card.css
# ---------------------------------------------------------------------------

class TestCSS:
    def test_css_has_regime_strip_class(self):
        src = _read(CSS_PATH)
        assert '.regime-strip {' in src

    def test_css_has_regime_strip_badge(self):
        src = _read(CSS_PATH)
        assert '.regime-strip__badge {' in src

    def test_css_has_regime_strip_dot(self):
        src = _read(CSS_PATH)
        assert '.regime-strip__dot {' in src

    def test_css_has_regime_strip_name(self):
        src = _read(CSS_PATH)
        assert '.regime-strip__name {' in src

    def test_css_has_regime_strip_context(self):
        src = _read(CSS_PATH)
        assert '.regime-strip__context {' in src

    def test_css_has_regime_strip_separator(self):
        src = _read(CSS_PATH)
        assert '.regime-strip__separator {' in src

    def test_css_strip_colors_all_four_regimes(self):
        src = _read(CSS_PATH)
        for regime in ('bull', 'neutral', 'bear', 'recession'):
            assert f'.regime-strip.regime-{regime} .regime-strip__dot' in src
            assert f'.regime-strip.regime-{regime} .regime-strip__name' in src

    def test_css_strip_responsive_separator(self):
        """Separator visible at 768px+ only."""
        src = _read(CSS_PATH)
        assert 'min-width: 768px' in src
        # After 768px block, separator should display block
        tablet_block = src[src.index('min-width: 768px'):]
        assert '.regime-strip__separator' in tablet_block

    def test_css_has_regime_annotation_class(self):
        src = _read(CSS_PATH)
        assert '.regime-annotation {' in src

    def test_css_annotation_has_left_border(self):
        src = _read(CSS_PATH)
        annot_idx = src.index('.regime-annotation {')
        block = src[annot_idx:annot_idx + 200]
        assert 'border-left' in block

    def test_css_annotation_has_border_radius(self):
        src = _read(CSS_PATH)
        annot_idx = src.index('.regime-annotation {')
        block = src[annot_idx:annot_idx + 200]
        assert 'border-radius' in block

    def test_css_annotation_colors_all_four_regimes(self):
        src = _read(CSS_PATH)
        for regime in ('bull', 'neutral', 'bear', 'recession'):
            assert f'.regime-annotation.regime-{regime} {{' in src

    def test_css_annotation_toggle_button(self):
        src = _read(CSS_PATH)
        assert '.regime-annotation__toggle {' in src

    def test_css_annotation_toggle_min_height_44px(self):
        src = _read(CSS_PATH)
        toggle_idx = src.index('.regime-annotation__toggle {')
        block = src[toggle_idx:toggle_idx + 300]
        assert 'min-height: 44px' in block

    def test_css_annotation_label(self):
        src = _read(CSS_PATH)
        assert '.regime-annotation__label {' in src

    def test_css_annotation_text_collapsed_by_default(self):
        src = _read(CSS_PATH)
        text_idx = src.index('.regime-annotation__text {')
        block = src[text_idx:text_idx + 200]
        assert 'max-height: 0' in block

    def test_css_annotation_text_visible_when_expanded(self):
        src = _read(CSS_PATH)
        assert '.regime-annotation.is-expanded .regime-annotation__text' in src

    def test_css_annotation_text_transition(self):
        src = _read(CSS_PATH)
        text_idx = src.index('.regime-annotation__text {')
        block = src[text_idx:text_idx + 300]
        assert 'transition' in block

    def test_css_annotation_toggle_hidden_tablet_plus(self):
        src = _read(CSS_PATH)
        # After the 768px media query, toggle should be hidden
        tablet_section = src[src.rindex('@media (min-width: 768px)'):]
        assert '.regime-annotation__toggle' in tablet_section
        assert 'display: none' in tablet_section

    def test_css_annotation_text_max_height_none_tablet_plus(self):
        src = _read(CSS_PATH)
        tablet_section = src[src.rindex('@media (min-width: 768px)'):]
        assert 'max-height: none' in tablet_section

    def test_css_has_reduced_motion_rule(self):
        src = _read(CSS_PATH)
        assert 'prefers-reduced-motion' in src

    def test_css_chevron_rotation_on_expanded(self):
        src = _read(CSS_PATH)
        assert '.regime-annotation__toggle[aria-expanded="true"] .regime-annotation__chevron' in src
        assert 'rotate(180deg)' in src


# ---------------------------------------------------------------------------
# 8. JavaScript — dashboard.js
# ---------------------------------------------------------------------------

class TestJS:
    def test_init_regime_annotations_function_exists(self):
        src = _read(JS_PATH)
        assert 'function initRegimeAnnotations' in src

    def test_init_regime_annotations_called_on_domcontentloaded(self):
        src = _read(JS_PATH)
        # Find DOMContentLoaded handler and verify it calls initRegimeAnnotations
        dom_idx = src.index('DOMContentLoaded')
        block = src[dom_idx:dom_idx + 300]
        assert 'initRegimeAnnotations' in block

    def test_js_toggles_aria_expanded(self):
        src = _read(JS_PATH)
        fn_idx = src.index('function initRegimeAnnotations')
        block = src[fn_idx:fn_idx + 400]
        assert 'aria-expanded' in block

    def test_js_toggles_is_expanded_class(self):
        src = _read(JS_PATH)
        fn_idx = src.index('function initRegimeAnnotations')
        block = src[fn_idx:fn_idx + 600]
        assert 'is-expanded' in block

    def test_js_selects_toggle_buttons(self):
        src = _read(JS_PATH)
        fn_idx = src.index('function initRegimeAnnotations')
        block = src[fn_idx:fn_idx + 400]
        assert 'regime-annotation__toggle' in block
