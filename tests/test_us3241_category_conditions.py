"""Tests for US-324.1: Category page conditions migration.

Tests cover:
1. conditions_config.py — context sentences, signal annotations, helpers
2. Context processor injection of new config data
3. _conditions_strip.html — category context sentence rendering
4. _macros.html — quadrant-based signal annotation rendering
5. Relocated panels — recession on credit, sector tone + trade pulse on equity
6. Equity route now passes trade balance context
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
if SIGNALTRACKERS_DIR not in sys.path:
    sys.path.insert(0, SIGNALTRACKERS_DIR)


# ═══════════════════════════════════════════════════════════════════════════
# Section 1: conditions_config.py unit tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryConditionsContext:
    """Test CATEGORY_CONDITIONS_CONTEXT structure and completeness."""

    def setup_method(self):
        from conditions_config import CATEGORY_CONDITIONS_CONTEXT
        self.ctx = CATEGORY_CONDITIONS_CONTEXT

    def test_seven_categories_present(self):
        expected = {'Credit', 'Rates', 'Equities', 'Dollar', 'Crypto', 'Safe Havens', 'Property'}
        assert set(self.ctx.keys()) == expected

    def test_twelve_entries_per_category(self):
        for cat, entries in self.ctx.items():
            assert len(entries) == 12, f"{cat} has {len(entries)} entries, expected 12"

    def test_all_quadrant_liquidity_combos(self):
        quadrants = ['Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk']
        liquidities = ['Expanding', 'Neutral', 'Contracting']
        for cat in self.ctx:
            for q in quadrants:
                for liq in liquidities:
                    key = (q, liq)
                    assert key in self.ctx[cat], f"Missing {key} in {cat}"

    def test_all_sentences_non_empty_strings(self):
        for cat, entries in self.ctx.items():
            for key, sentence in entries.items():
                assert isinstance(sentence, str), f"{cat} {key} is not a string"
                assert len(sentence) > 10, f"{cat} {key} sentence too short"

    def test_total_84_sentences(self):
        total = sum(len(entries) for entries in self.ctx.values())
        assert total == 84

    def test_crypto_sentences_mention_liquidity(self):
        """Crypto context sentences should emphasize liquidity as primary driver."""
        for key, sentence in self.ctx['Crypto'].items():
            sentence_lower = sentence.lower()
            assert 'liquidity' in sentence_lower or 'm2' in sentence_lower or 'qe' in sentence_lower, \
                f"Crypto sentence for {key} doesn't mention liquidity: {sentence}"


class TestSignalConditionsAnnotations:
    """Test SIGNAL_CONDITIONS_ANNOTATIONS structure and completeness."""

    def setup_method(self):
        from conditions_config import SIGNAL_CONDITIONS_ANNOTATIONS
        self.annotations = SIGNAL_CONDITIONS_ANNOTATIONS

    def test_nineteen_signals_present(self):
        assert len(self.annotations) == 19

    def test_expected_signal_keys(self):
        expected = {
            'high_yield_spread', 'investment_grade_spread', 'ccc_spread',
            'yield_curve_10y2y', 'yield_curve_10y3m', 'treasury_10y',
            'nfci', 'initial_claims', 'continuing_claims', 'consumer_confidence',
            'vix', 'gold', 'real_yield_10y', 'breakeven_inflation_10y',
            'sp500', 'fed_funds_rate', 'fed_balance_sheet', 'm2_money_supply',
            'dollar_index',
        }
        assert set(self.annotations.keys()) == expected

    def test_four_quadrants_per_signal(self):
        quadrants = {'Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk'}
        for signal, entries in self.annotations.items():
            assert set(entries.keys()) == quadrants, f"{signal} missing quadrants"

    def test_total_76_annotations(self):
        total = sum(len(entries) for entries in self.annotations.values())
        assert total == 76

    def test_all_annotations_non_empty(self):
        for signal, entries in self.annotations.items():
            for q, text in entries.items():
                assert isinstance(text, str) and len(text) > 5, \
                    f"{signal}/{q} annotation too short"

    def test_annotations_start_with_signal_icon(self):
        """Each annotation should start with ✓, ─, or ▲."""
        valid_prefixes = ('\u2713', '\u2500', '\u25b2')
        for signal, entries in self.annotations.items():
            for q, text in entries.items():
                assert text[0] in valid_prefixes, \
                    f"{signal}/{q} doesn't start with signal icon: {text[:5]}"


class TestLiquiditySimplification:
    """Test the liquidity state simplification helper."""

    def test_strongly_expanding(self):
        from conditions_config import get_simplified_liquidity
        assert get_simplified_liquidity('Strongly Expanding') == 'Expanding'

    def test_expanding(self):
        from conditions_config import get_simplified_liquidity
        assert get_simplified_liquidity('Expanding') == 'Expanding'

    def test_neutral(self):
        from conditions_config import get_simplified_liquidity
        assert get_simplified_liquidity('Neutral') == 'Neutral'

    def test_contracting(self):
        from conditions_config import get_simplified_liquidity
        assert get_simplified_liquidity('Contracting') == 'Contracting'

    def test_strongly_contracting(self):
        from conditions_config import get_simplified_liquidity
        assert get_simplified_liquidity('Strongly Contracting') == 'Contracting'

    def test_unknown_defaults_to_neutral(self):
        from conditions_config import get_simplified_liquidity
        assert get_simplified_liquidity('Unknown') == 'Neutral'


class TestGetCategoryConditionsContext:
    """Test the context sentence lookup helper."""

    def test_valid_lookup(self):
        from conditions_config import get_category_conditions_context
        result = get_category_conditions_context('Credit', 'Goldilocks', 'Expanding')
        assert 'carry trades' in result.lower()

    def test_strongly_expanding_maps_to_expanding(self):
        from conditions_config import get_category_conditions_context
        result = get_category_conditions_context('Credit', 'Goldilocks', 'Strongly Expanding')
        assert result == get_category_conditions_context('Credit', 'Goldilocks', 'Expanding')

    def test_unknown_category_returns_empty(self):
        from conditions_config import get_category_conditions_context
        result = get_category_conditions_context('Unknown', 'Goldilocks', 'Expanding')
        assert result == ''

    def test_unknown_quadrant_returns_empty(self):
        from conditions_config import get_category_conditions_context
        result = get_category_conditions_context('Credit', 'Unknown', 'Expanding')
        assert result == ''


# ═══════════════════════════════════════════════════════════════════════════
# Section 2: Flask template integration tests
# ═══════════════════════════════════════════════════════════════════════════

def _make_mock_conditions(quadrant='Goldilocks', liquidity='Expanding',
                          risk='Calm', policy_dir='Easing'):
    """Build a mock market_conditions dict."""
    return {
        'quadrant': quadrant,
        'dimensions': {
            'quadrant': {'state': quadrant, 'growth_composite': 0.5, 'inflation_composite': -0.3},
            'liquidity': {'state': liquidity, 'score': 0.8},
            'risk': {'state': risk, 'score': 2},
            'policy': {'direction': policy_dir, 'stance': 'Accommodative', 'taylor_gap': -1.5},
        },
        'as_of': '2026-03-18',
        'updated_at': '2026-03-18T12:00:00+00:00',
    }


def _make_mock_recession():
    """Build a mock recession_probability dict."""
    return {
        'ny_fed': 15.2,
        'ny_fed_css': 'low',
        'ny_fed_risk': 'Low',
        'ny_fed_lower': 10.0,
        'ny_fed_upper': 20.0,
        'ny_fed_date': 'Feb 2026',
        'chauvet_piger': 2.1,
        'chauvet_piger_css': 'low',
        'chauvet_piger_risk': 'Low',
        'chauvet_piger_date': 'Jan 2026',
        'richmond_sos': 5.0,
        'richmond_sos_css': 'low',
        'richmond_sos_risk': 'Low',
        'richmond_sos_date': 'Mar 2026',
        'mobile_summary': 'Low risk across all models',
        'interpretation': 'All three models agree: recession risk is low.',
        'divergence_pp': 5.0,
        'updated': 'Mar 2026',
    }


def _make_mock_sector_tone():
    """Build a mock sector_management_tone dict."""
    return {
        'data_available': True,
        'quarter': 'Q4',
        'year': 2025,
        'sectors': [
            {
                'name': 'Information Technology',
                'short_name': 'Tech',
                'current_tone': 'positive',
                'trend': [
                    {'quarter': 'Q3', 'year': 2025, 'tone': 'positive'},
                    {'quarter': 'Q4', 'year': 2025, 'tone': 'positive'},
                ],
            },
            {
                'name': 'Energy',
                'short_name': 'Energy',
                'current_tone': 'negative',
                'trend': [
                    {'quarter': 'Q3', 'year': 2025, 'tone': 'neutral'},
                    {'quarter': 'Q4', 'year': 2025, 'tone': 'negative'},
                ],
            },
        ],
    }


@pytest.fixture
def app():
    """Create Flask test app with mocked dependencies."""
    with patch('dashboard.get_macro_regime', return_value=None), \
         patch('dashboard.get_recession_probability', return_value=None), \
         patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
         patch('dashboard.get_sector_management_tone', return_value=None):
        from dashboard import app as flask_app
        flask_app.config['TESTING'] = True
        flask_app.config['WTF_CSRF_ENABLED'] = False
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestConditionsStripContextSentence:
    """Test that category context sentence appears below conditions strip."""

    def test_credit_page_shows_context_sentence(self, client):
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html
        assert 'conditions-strip__context-text' in html

    def test_rates_page_shows_context_sentence(self, client):
        resp = client.get('/rates')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html

    def test_equity_page_shows_context_sentence(self, client):
        resp = client.get('/equity')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html

    def test_dollar_page_shows_context_sentence(self, client):
        resp = client.get('/dollar')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html

    def test_crypto_page_shows_context_sentence(self, client):
        resp = client.get('/crypto')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html

    def test_safe_havens_page_shows_context_sentence(self, client):
        resp = client.get('/safe-havens')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html

    def test_property_page_shows_context_sentence(self, client):
        resp = client.get('/property')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html

    def test_goldilocks_expanding_credit_sentence(self, client):
        """Verify the actual sentence content for Credit in Goldilocks/Expanding."""
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'carry trades supported' in html

    def test_context_has_aria_label(self, client):
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'Conditions context for Credit' in html

    def test_homepage_no_context_sentence(self, client):
        """Homepage shouldn't show a category context sentence (no page_category)."""
        with patch('dashboard.get_conditions_history', return_value=None), \
             patch('dashboard.load_csv_data', return_value=None):
            resp = client.get('/')
            html = resp.data.decode()
            # The homepage conditions strip should NOT have the context paragraph
            # because page_category is not set on the homepage
            assert 'conditions-strip__context-text' not in html


class TestConditionsStripVariousQuadrants:
    """Test context sentences change with different quadrant/liquidity states."""

    def _get_html(self, quadrant, liquidity, path):
        conditions = _make_mock_conditions(quadrant=quadrant, liquidity=liquidity)
        with patch('dashboard.get_market_conditions', return_value=conditions):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get(path)
            return resp.data.decode()

    def test_stagflation_contracting_credit(self):
        html = self._get_html('Stagflation', 'Contracting', '/credit')
        assert 'underestimate risk' in html.lower()

    def test_deflation_risk_expanding_rates(self):
        html = self._get_html('Deflation Risk', 'Expanding', '/rates')
        assert 'flight to safety' in html.lower()

    def test_reflation_neutral_equities(self):
        html = self._get_html('Reflation', 'Neutral', '/equity')
        assert 'cyclicals' in html.lower()

    def test_strongly_expanding_maps_to_expanding(self):
        """Strongly Expanding should map to the same sentence as Expanding."""
        html = self._get_html('Goldilocks', 'Strongly Expanding', '/credit')
        assert 'carry trades supported' in html


class TestSignalAnnotationsMacro:
    """Test _macros.html uses quadrant-based annotations."""

    def test_credit_page_has_conditions_context_label(self, client):
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'Conditions Context' in html

    def test_credit_page_no_regime_context_label(self, client):
        """Should NOT say 'Regime Context' anymore."""
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'Regime Context' not in html

    def test_annotation_text_present_for_hy_spread(self, client):
        """Check that HY spread annotation appears on credit page."""
        resp = client.get('/credit')
        html = resp.data.decode()
        # In Goldilocks, HY annotation starts with ✓
        assert 'Tight spreads expected in Goldilocks' in html


# ═══════════════════════════════════════════════════════════════════════════
# Section 3: Relocated panels
# ═══════════════════════════════════════════════════════════════════════════

class TestRecessionPanelOnCreditPage:
    """Test recession probability panel relocated to credit page."""

    def test_recession_panel_present_when_data_available(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=_make_mock_recession()), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'recession-panel-section' in html
            assert 'Recession Probability' in html

    def test_recession_panel_shows_model_names(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=_make_mock_recession()), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'NY FED' in html
            assert 'CHAUVET-PIGER' in html
            assert 'RICHMOND FED SOS' in html

    def test_recession_panel_has_interpretation(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=_make_mock_recession()), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'recession risk is low' in html

    def test_recession_panel_has_why_three_models(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=_make_mock_recession()), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'Why three models?' in html

    def test_recession_panel_hidden_when_no_data(self, client):
        """Panel should not appear when recession_probability is None."""
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'recession-panel-section' not in html

    def test_recession_panel_ai_section_btn(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=_make_mock_recession()), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'data-section-id="recession-panel-section"' in html


class TestSectorToneOnEquityPage:
    """Test sector management tone panel relocated to equity page."""

    def test_sector_tone_present_when_data_available(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=_make_mock_sector_tone()), \
             patch('dashboard.load_csv_data', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/equity')
            html = resp.data.decode()
            assert 'sector-tone-section' in html
            assert 'Sector Management Tone' in html

    def test_sector_tone_shows_sectors(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=_make_mock_sector_tone()), \
             patch('dashboard.load_csv_data', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/equity')
            html = resp.data.decode()
            assert 'Tech' in html
            assert 'Energy' in html

    def test_sector_tone_toggle_button(self):
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=_make_mock_sector_tone()), \
             patch('dashboard.load_csv_data', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/equity')
            html = resp.data.decode()
            assert 'sector-tone-toggle' in html
            assert 'Show Sectors' in html

    def test_sector_tone_empty_state(self):
        empty_tone = {
            'data_available': False,
            'quarter': 'Q1',
            'year': 2026,
        }
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=empty_tone), \
             patch('dashboard.load_csv_data', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/equity')
            html = resp.data.decode()
            assert 'sector-tone-empty' in html


class TestTradePulseOnEquityPage:
    """Test trade pulse panel relocated to equity page."""

    def test_trade_pulse_present_when_data_available(self):
        import pandas as pd
        import numpy as np
        dates = pd.date_range('2020-01-01', periods=120, freq='MS')
        df = pd.DataFrame({
            'date': dates,
            'trade_balance': np.random.uniform(-80, -60, len(dates)),
        })
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None), \
             patch('dashboard.load_csv_data', return_value=df):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/equity')
            html = resp.data.decode()
            assert 'trade-pulse-section' in html
            assert 'Global Trade Pulse' in html

    def test_trade_pulse_hidden_when_no_data(self):
        """Panel should not appear when no trade balance data."""
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=_make_mock_conditions()), \
             patch('dashboard.get_sector_management_tone', return_value=None), \
             patch('dashboard.load_csv_data', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/equity')
            html = resp.data.decode()
            assert 'trade-pulse-section' not in html

    def test_equity_route_returns_200(self, client):
        resp = client.get('/equity')
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# Section 4: Context processor tests
# ═══════════════════════════════════════════════════════════════════════════

class TestContextProcessorInjection:
    """Test that new config data is injected via context processor."""

    def test_signal_conditions_annotations_injected(self, client):
        resp = client.get('/credit')
        html = resp.data.decode()
        # The annotation text from SIGNAL_CONDITIONS_ANNOTATIONS should appear
        assert 'Conditions Context' in html

    def test_category_conditions_context_injected(self, client):
        resp = client.get('/credit')
        html = resp.data.decode()
        assert 'conditions-strip__context' in html


# ═══════════════════════════════════════════════════════════════════════════
# Section 5: CSS classes and styling
# ═══════════════════════════════════════════════════════════════════════════

class TestConditionsStripCSS:
    """Test that CSS file contains required styles."""

    def test_context_class_in_css(self):
        css_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'conditions-strip.css')
        with open(css_path) as f:
            css = f.read()
        assert '.conditions-strip__context' in css
        assert '.conditions-strip__context-text' in css

    def test_context_text_is_italic(self):
        css_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'conditions-strip.css')
        with open(css_path) as f:
            css = f.read()
        assert 'font-style: italic' in css

    def test_context_text_is_sm(self):
        css_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'conditions-strip.css')
        with open(css_path) as f:
            css = f.read()
        assert '0.875rem' in css  # text-sm


# ═══════════════════════════════════════════════════════════════════════════
# Section 6: Edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test graceful handling of missing/incomplete data."""

    def test_no_conditions_data_no_context_sentence(self):
        """When market_conditions is None, no context sentence should appear."""
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=None), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'conditions-strip__context' not in html
            assert 'CONDITIONS UNAVAILABLE' in html

    def test_conditions_without_quadrant_dimension(self):
        """Handle missing quadrant dimension gracefully."""
        conditions = _make_mock_conditions()
        conditions['dimensions']['quadrant'] = None
        with patch('dashboard.get_macro_regime', return_value=None), \
             patch('dashboard.get_recession_probability', return_value=None), \
             patch('dashboard.get_market_conditions', return_value=conditions), \
             patch('dashboard.get_sector_management_tone', return_value=None):
            from dashboard import app as flask_app
            flask_app.config['TESTING'] = True
            client = flask_app.test_client()
            resp = client.get('/credit')
            # Should not crash
            assert resp.status_code == 200
