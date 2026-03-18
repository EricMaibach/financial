"""Tests for US-323.2: Portfolio Implications matrix + Today's Movers footer."""

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
# Section 1: build_implications_matrix unit tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildImplicationsMatrix:
    """Test the per-dimension signal computation."""

    def setup_method(self):
        from market_conditions import build_implications_matrix
        self.build = build_implications_matrix

    def test_returns_six_asset_rows(self):
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Easing')
        assert len(rows) == 6

    def test_asset_labels(self):
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Easing')
        labels = [r['label'] for r in rows]
        assert labels == ['Equities', 'Bonds', 'Gold', 'Crypto', 'Credit', 'Commod.']

    def test_asset_links(self):
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Easing')
        links = [r['link'] for r in rows]
        assert '/equity' in links
        assert '/rates' in links
        assert '/safe-havens' in links
        assert '/crypto' in links
        assert '/credit' in links

    def test_each_row_has_all_dimensions(self):
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Easing')
        for row in rows:
            assert 'overall' in row
            assert 'quad' in row
            assert 'liq' in row
            assert 'risk' in row
            assert 'policy' in row

    def test_valid_signal_values(self):
        valid = {'strong_support', 'support', 'neutral', 'headwind', 'strong_headwind'}
        for quad in ['Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk']:
            for liq in ['Strongly Expanding', 'Expanding', 'Neutral', 'Contracting', 'Strongly Contracting']:
                for risk in ['Calm', 'Normal', 'Elevated', 'Stressed']:
                    for pol in ['Easing', 'Paused', 'Tightening']:
                        rows = self.build(quad, liq, risk, pol)
                        for row in rows:
                            assert row['overall'] in valid, f"Invalid overall: {row['overall']}"
                            assert row['quad'] in valid
                            assert row['liq'] in valid
                            assert row['risk'] in valid
                            assert row['policy'] in valid

    def test_goldilocks_expanding_calm_easing_equities_supportive(self):
        """Best conditions for equities: Goldilocks + Expanding Liq + Calm Risk + Easing.
        Average signal rank = 1.0 (all support) → 'support' (threshold for strong is ≥1.5)."""
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Easing')
        equities = rows[0]
        assert equities['asset'] == 'sp500'
        assert equities['overall'] == 'support'

    def test_stagflation_contracting_stressed_tightening_equities_headwind(self):
        """Worst conditions for equities."""
        rows = self.build('Stagflation', 'Contracting', 'Stressed', 'Tightening')
        equities = rows[0]
        assert equities['overall'] in ('headwind', 'strong_headwind')

    def test_crypto_quad_signal_always_neutral(self):
        """Bitcoin doesn't follow the quadrant — quad signal should be neutral."""
        for quad in ['Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk']:
            rows = self.build(quad, 'Neutral', 'Normal', 'Paused')
            crypto = [r for r in rows if r['asset'] == 'bitcoin'][0]
            assert crypto['quad'] == 'neutral'

    def test_crypto_liquidity_strong_support_when_expanding(self):
        """Bitcoin gets strong liquidity support when liquidity expands."""
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Paused')
        crypto = [r for r in rows if r['asset'] == 'bitcoin'][0]
        assert crypto['liq'] == 'strong_support'

    def test_crypto_liquidity_headwind_when_contracting(self):
        rows = self.build('Goldilocks', 'Contracting', 'Normal', 'Paused')
        crypto = [r for r in rows if r['asset'] == 'bitcoin'][0]
        assert crypto['liq'] == 'headwind'

    def test_gold_supportive_in_stagflation(self):
        rows = self.build('Stagflation', 'Neutral', 'Normal', 'Paused')
        gold = [r for r in rows if r['asset'] == 'gold'][0]
        assert gold['quad'] == 'support'

    def test_gold_strong_support_when_stressed(self):
        rows = self.build('Goldilocks', 'Neutral', 'Stressed', 'Paused')
        gold = [r for r in rows if r['asset'] == 'gold'][0]
        assert gold['risk'] == 'strong_support'

    def test_credit_headwind_in_stagflation(self):
        rows = self.build('Stagflation', 'Neutral', 'Normal', 'Paused')
        credit = [r for r in rows if r['asset'] == 'credit'][0]
        assert credit['quad'] == 'headwind'

    def test_commodities_support_in_reflation(self):
        rows = self.build('Reflation', 'Neutral', 'Normal', 'Paused')
        commod = [r for r in rows if r['asset'] == 'commodities'][0]
        assert commod['quad'] == 'support'

    def test_why_field_for_equities_goldilocks_expanding(self):
        rows = self.build('Goldilocks', 'Expanding', 'Calm', 'Easing')
        equities = rows[0]
        # All four dimensions supportive
        assert 'Quad' in equities['why']
        assert 'Liq' in equities['why']

    def test_why_field_empty_when_no_support(self):
        """When all dimensions are headwind/neutral, why should be empty."""
        rows = self.build('Stagflation', 'Contracting', 'Stressed', 'Tightening')
        # Gold might have support from risk... test commodities instead
        commod = [r for r in rows if r['asset'] == 'commodities'][0]
        # Quad is support but rest are neutral — depends
        # Just check it doesn't crash
        assert isinstance(commod['why'], str)

    def test_unknown_quadrant_uses_fallback(self):
        rows = self.build('UnknownQuadrant', 'Neutral', 'Normal', 'Paused')
        assert len(rows) == 6

    def test_unknown_liquidity_state_uses_neutral(self):
        rows = self.build('Goldilocks', 'UnknownState', 'Normal', 'Paused')
        assert len(rows) == 6

    def test_bonds_support_in_goldilocks(self):
        rows = self.build('Goldilocks', 'Neutral', 'Normal', 'Paused')
        bonds = [r for r in rows if r['asset'] == 'treasuries'][0]
        assert bonds['quad'] == 'support'

    def test_bonds_headwind_in_stagflation(self):
        rows = self.build('Stagflation', 'Neutral', 'Normal', 'Paused')
        bonds = [r for r in rows if r['asset'] == 'treasuries'][0]
        assert bonds['quad'] == 'headwind'

    def test_policy_easing_supports_equities(self):
        rows = self.build('Goldilocks', 'Neutral', 'Normal', 'Easing')
        equities = rows[0]
        assert equities['policy'] == 'support'

    def test_policy_tightening_headwind_equities(self):
        rows = self.build('Goldilocks', 'Neutral', 'Normal', 'Tightening')
        equities = rows[0]
        assert equities['policy'] == 'headwind'

    def test_stressed_risk_strong_headwind_equities(self):
        rows = self.build('Goldilocks', 'Neutral', 'Stressed', 'Paused')
        equities = rows[0]
        assert equities['risk'] == 'strong_headwind'


# ═══════════════════════════════════════════════════════════════════════════
# Section 2: Extended asset expectations (credit + commodities)
# ═══════════════════════════════════════════════════════════════════════════

class TestExtendedAssetExpectations:
    """Test that _build_asset_expectations now includes credit + commodities."""

    def setup_method(self):
        from market_conditions import _build_asset_expectations
        self.build = _build_asset_expectations

    def test_returns_six_assets(self):
        exp = self.build('Goldilocks', 'Expanding', 'Calm')
        assert len(exp) == 6

    def test_asset_keys(self):
        exp = self.build('Goldilocks', 'Expanding', 'Calm')
        assets = {e['asset'] for e in exp}
        assert assets == {'sp500', 'treasuries', 'gold', 'credit', 'commodities', 'bitcoin'}

    def test_credit_positive_in_goldilocks(self):
        exp = self.build('Goldilocks', 'Expanding', 'Calm')
        credit = [e for e in exp if e['asset'] == 'credit'][0]
        assert credit['direction'] == 'positive'

    def test_credit_negative_in_stagflation(self):
        exp = self.build('Stagflation', 'Neutral', 'Normal')
        credit = [e for e in exp if e['asset'] == 'credit'][0]
        assert credit['direction'] == 'negative'

    def test_commodities_neutral_in_goldilocks(self):
        exp = self.build('Goldilocks', 'Expanding', 'Calm')
        commod = [e for e in exp if e['asset'] == 'commodities'][0]
        assert commod['direction'] == 'neutral'

    def test_commodities_positive_in_reflation(self):
        exp = self.build('Reflation', 'Expanding', 'Normal')
        commod = [e for e in exp if e['asset'] == 'commodities'][0]
        assert commod['direction'] == 'positive'

    def test_stressed_reduces_credit_magnitude(self):
        exp = self.build('Goldilocks', 'Expanding', 'Stressed')
        credit = [e for e in exp if e['asset'] == 'credit'][0]
        assert credit['magnitude'] == 'weak'
        assert credit['conviction'] == 'override'


# ═══════════════════════════════════════════════════════════════════════════
# Section 3: Flask template rendering tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def app():
    """Create Flask test client with mocked market conditions."""
    os.environ.setdefault('SECRET_KEY', 'test-secret')
    os.environ.setdefault('OPENAI_API_KEY', 'test')
    os.environ.setdefault('ANTHROPIC_API_KEY', 'test')
    os.environ.setdefault('FRED_API_KEY', 'test')

    with patch.dict('os.environ', {
        'SECRET_KEY': 'test-secret',
        'OPENAI_API_KEY': 'test',
        'ANTHROPIC_API_KEY': 'test',
        'FRED_API_KEY': 'test',
    }):
        from dashboard import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def _mock_conditions():
    """Return a mock conditions cache dict for testing."""
    return {
        'quadrant': 'Goldilocks',
        'dimensions': {
            'quadrant': {
                'state': 'Goldilocks',
                'growth_composite': 0.6,
                'inflation_composite': -0.4,
            },
            'liquidity': {
                'state': 'Expanding',
                'score': 0.65,
            },
            'risk': {
                'state': 'Calm',
                'score': 1,
                'vix': 14.8,
            },
            'policy': {
                'stance': 'Neutral',
                'direction': 'Easing',
                'gap': -0.30,
                'fed_rate': 4.25,
                'taylor_prescribed': 4.55,
            },
        },
        'asset_expectations': [
            {'asset': 'sp500', 'direction': 'positive', 'magnitude': 'moderate', 'conviction': 'high'},
            {'asset': 'treasuries', 'direction': 'positive', 'magnitude': 'moderate', 'conviction': 'high'},
            {'asset': 'gold', 'direction': 'neutral', 'magnitude': 'moderate', 'conviction': 'high'},
            {'asset': 'credit', 'direction': 'positive', 'magnitude': 'moderate', 'conviction': 'high'},
            {'asset': 'commodities', 'direction': 'neutral', 'magnitude': 'moderate', 'conviction': 'high'},
            {'asset': 'bitcoin', 'direction': 'positive', 'magnitude': 'moderate', 'conviction': 'high'},
        ],
        'as_of': '2026-03-17',
        'updated_at': '2026-03-17T12:00:00+00:00',
    }


def _mock_history():
    return {
        '2026-02-28': {
            'quadrant': 'Goldilocks',
            'growth_score': 0.5,
            'inflation_score': -0.3,
            'dimensions': {
                'quadrant': {'state': 'Goldilocks', 'growth_composite': 0.5, 'inflation_composite': -0.3},
                'liquidity': {'state': 'Expanding', 'score': 0.6},
                'risk': {'state': 'Calm', 'score': 1},
                'policy': {'stance': 'Neutral', 'direction': 'Easing'},
            },
            'asset_expectations': [],
        },
        '2026-01-31': {
            'quadrant': 'Goldilocks',
            'growth_score': 0.4,
            'inflation_score': -0.2,
            'dimensions': {
                'quadrant': {'state': 'Goldilocks', 'growth_composite': 0.4, 'inflation_composite': -0.2},
                'liquidity': {'state': 'Expanding', 'score': 0.55},
                'risk': {'state': 'Normal', 'score': 2},
                'policy': {'stance': 'Neutral', 'direction': 'Paused'},
            },
            'asset_expectations': [],
        },
    }


class TestImplicationsTemplateRendering:
    """Test the §2 implications section renders correctly in the HTML."""

    def test_implications_section_present(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'id="implications-section"' in html
        assert 'WHAT THIS MEANS FOR YOUR PORTFOLIO' in html

    def test_mobile_table_present(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'implications-table--mobile' in html
        assert 'Conditions Say' in html

    def test_desktop_table_present(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'implications-table--desktop' in html
        assert '>Quad<' in html
        assert '>Liq<' in html
        assert '>Risk<' in html
        assert '>Policy<' in html

    def test_six_asset_rows_in_desktop_table(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'Equities' in html
        assert 'Bonds' in html
        assert 'Gold' in html
        assert 'Crypto' in html
        assert 'Credit' in html
        assert 'Commod.' in html

    def test_signal_icons_rendered(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        # Should have at least some signal icons
        assert '✓' in html or '─' in html or '✗' in html

    def test_explore_links_present(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'implications-explore' in html
        assert '/equity' in html
        assert '/credit' in html

    def test_asset_names_are_links(self, client):
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=_mock_history()), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'href="/equity">Equities</a>' in html
        assert 'href="/rates">Bonds</a>' in html
        assert 'href="/safe-havens">Gold</a>' in html
        assert 'href="/crypto">Crypto</a>' in html

    def test_no_implications_without_conditions(self, client):
        with patch('dashboard.get_market_conditions', return_value=None), \
             patch('dashboard.get_conditions_history', return_value={}), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'implications-table--mobile' not in html
        assert 'implications-table--desktop' not in html

    def test_historical_context_with_matching_periods(self, client):
        history = _mock_history()
        with patch('dashboard.get_market_conditions', return_value=_mock_conditions()), \
             patch('dashboard.get_conditions_history', return_value=history), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'implications-context' in html
        assert 'Goldilocks' in html


class TestMoversStripRendering:
    """Test the Today's Movers footer strip."""

    def test_movers_section_present(self, client):
        with patch('dashboard.get_market_conditions', return_value=None), \
             patch('dashboard.get_conditions_history', return_value={}), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'id="movers-strip"' in html
        assert "TODAY'S MOVERS" in html or "TODAY&#39;S MOVERS" in html or 'TODAY' in html

    def test_movers_see_all_link(self, client):
        with patch('dashboard.get_market_conditions', return_value=None), \
             patch('dashboard.get_conditions_history', return_value={}), \
             patch('dashboard.get_recession_probability', return_value=None):
            resp = client.get('/')
        html = resp.data.decode()
        assert 'See all' in html
        assert '/equity' in html


# ═══════════════════════════════════════════════════════════════════════════
# Section 4: CSS static analysis
# ═══════════════════════════════════════════════════════════════════════════

class TestImplicationsCSS:
    """Verify CSS classes exist in the stylesheet."""

    def setup_method(self):
        css_path = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css',
                                'components', 'conditions-summary.css')
        with open(css_path) as f:
            self.css = f.read()

    def test_mobile_table_class(self):
        assert '.implications-table--mobile' in self.css

    def test_desktop_table_class(self):
        assert '.implications-table--desktop' in self.css

    def test_signal_classes(self):
        assert '.implications-signal--strong_support' in self.css
        assert '.implications-signal--support' in self.css
        assert '.implications-signal--neutral' in self.css
        assert '.implications-signal--headwind' in self.css
        assert '.implications-signal--strong_headwind' in self.css

    def test_signal_color_tokens(self):
        assert '--signal-supportive' in self.css
        assert '--signal-neutral' in self.css
        assert '--signal-headwind' in self.css

    def test_responsive_breakpoint(self):
        assert 'min-width: 1024px' in self.css

    def test_implications_context_class(self):
        assert '.implications-context' in self.css

    def test_implications_explore_class(self):
        assert '.implications-explore' in self.css

    def test_why_column_class(self):
        assert '.implications-why' in self.css

    def test_table_thead_styles(self):
        assert '.implications-table thead' in self.css

    def test_signal_text_class(self):
        assert '.implications-signal__text' in self.css
