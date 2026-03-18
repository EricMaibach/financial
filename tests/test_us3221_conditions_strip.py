"""
Tests for US-322.1: Conditions strip component — quadrant headline, mobile expand,
Crypto liquidity-led.

Acceptance criteria verified:
- Conditions strip renders on all 11 pages
- Desktop: quadrant headline + Liquidity, Risk, Policy inline
- Crypto page: Liquidity leads, quadrant secondary
- Mobile: collapsed with toggle, expand panel
- Quadrant colors: Goldilocks (teal), Reflation (blue), Deflation Risk (amber), Stagflation (red)
- Reads from market_conditions_cache.json
- Graceful fallback if cache missing/stale
- Old _regime_strip.html replaced completely
- Accessibility (ARIA attributes)
"""

import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

SIGNALTRACKERS_DIR = Path(__file__).parent.parent / 'signaltrackers'
sys.path.insert(0, str(SIGNALTRACKERS_DIR))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_conditions_cache(
    quadrant='Goldilocks',
    liquidity='Expanding',
    risk='Calm',
    policy_stance='Accommodative',
    policy_direction='Easing',
    hours_ago=1,
):
    """Build a market_conditions_cache dict."""
    updated = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return {
        'quadrant': quadrant,
        'dimensions': {
            'liquidity': {'state': liquidity},
            'quadrant': {'state': quadrant},
            'risk': {'state': risk},
            'policy': {
                'stance': policy_stance,
                'direction': policy_direction,
            },
        },
        'asset_expectations': {},
        'as_of': '2026-03-17',
        'updated_at': updated.isoformat(),
    }


@pytest.fixture
def client():
    from dashboard import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ─── Context Processor ───────────────────────────────────────────────────────

class TestContextProcessor:
    """Verify inject_market_conditions context processor."""

    def test_fresh_cache_injected(self, client):
        cache = _make_conditions_cache(hours_ago=1)
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            assert resp.status_code == 200
            assert b'GOLDILOCKS' in resp.data

    def test_stale_cache_shows_unavailable(self, client):
        cache = _make_conditions_cache(hours_ago=49)
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            assert resp.status_code == 200
            assert b'CONDITIONS UNAVAILABLE' in resp.data

    def test_missing_cache_shows_unavailable(self, client):
        with patch('dashboard.get_market_conditions', return_value=None):
            resp = client.get('/')
            assert resp.status_code == 200
            assert b'CONDITIONS UNAVAILABLE' in resp.data

    def test_exception_shows_unavailable(self, client):
        with patch('dashboard.get_market_conditions', side_effect=Exception('boom')):
            resp = client.get('/')
            assert resp.status_code == 200
            assert b'CONDITIONS UNAVAILABLE' in resp.data


# ─── Strip Renders on All 11 Pages ───────────────────────────────────────────

ALL_PAGES = [
    '/',           # homepage
    '/credit',
    '/rates',
    '/equity',
    '/dollar',
    '/crypto',
    '/safe-havens',
    '/property',
    '/explorer',
    '/news',
]

# Portfolio requires login — tested separately
PORTFOLIO_PATH = '/portfolio'


class TestStripRendersOnAllPages:
    """Conditions strip should render on every page when cache is available."""

    @pytest.mark.parametrize('path', ALL_PAGES)
    def test_strip_present(self, client, path):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get(path)
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'conditions-strip' in html
            # Crypto uses LIQUIDITY headline, others use GOLDILOCKS
            if path == '/crypto':
                assert 'LIQUIDITY' in html
            else:
                assert 'GOLDILOCKS' in html

    @pytest.mark.parametrize('path', ALL_PAGES)
    def test_strip_fallback_on_all_pages(self, client, path):
        with patch('dashboard.get_market_conditions', return_value=None):
            resp = client.get(path)
            assert resp.status_code == 200
            html = resp.data.decode()
            assert 'conditions-strip' in html
            assert 'CONDITIONS UNAVAILABLE' in html


# ─── Desktop Layout ──────────────────────────────────────────────────────────

class TestDesktopLayout:
    """Desktop layout: quadrant headline + inline dimensions."""

    def test_quadrant_headline(self, client):
        cache = _make_conditions_cache(quadrant='Reflation')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'REFLATION' in html

    def test_liquidity_dimension_shown(self, client):
        cache = _make_conditions_cache(liquidity='Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            # Display label: "Expanding ↑"
            assert 'Expanding ↑' in html

    def test_risk_dimension_shown(self, client):
        cache = _make_conditions_cache(risk='Elevated')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'Elevated' in html

    def test_policy_dimension_shown(self, client):
        cache = _make_conditions_cache(policy_direction='Tightening')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            # Display label: "Tightening ↓"
            assert 'Tightening ↓' in html

    def test_separator_present(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'conditions-strip__separator' in html


# ─── Crypto Page Variant ─────────────────────────────────────────────────────

class TestCryptoPageVariant:
    """Crypto page: Liquidity leads as headline, quadrant is secondary."""

    def test_liquidity_leads_headline(self, client):
        cache = _make_conditions_cache(liquidity='Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            assert 'LIQUIDITY: EXPANDING' in html

    def test_strongly_expanding_label(self, client):
        cache = _make_conditions_cache(liquidity='Strongly Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            assert 'LIQUIDITY: EXPANDING ↑↑' in html

    def test_quadrant_as_secondary(self, client):
        cache = _make_conditions_cache(quadrant='Stagflation', liquidity='Contracting')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            # Quadrant should appear as a secondary dimension
            assert 'Stagflation' in html
            # Headline should be Liquidity, not quadrant
            assert 'LIQUIDITY: CONTRACTING' in html

    def test_liquidity_color_class(self, client):
        cache = _make_conditions_cache(liquidity='Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            assert 'conditions-strip--liq-expanding' in html

    def test_contracting_color_class(self, client):
        cache = _make_conditions_cache(liquidity='Contracting')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            assert 'conditions-strip--liq-contracting' in html

    def test_neutral_color_class(self, client):
        cache = _make_conditions_cache(liquidity='Neutral')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            assert 'conditions-strip--liq-neutral' in html

    def test_non_crypto_page_uses_quadrant_class(self, client):
        """Non-crypto pages should use quadrant color, not liquidity color."""
        cache = _make_conditions_cache(quadrant='Goldilocks', liquidity='Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert 'conditions-strip--goldilocks' in html
            assert 'conditions-strip--liq-expanding' not in html


# ─── Mobile Layout ────────────────────────────────────────────────────────────

class TestMobileLayout:
    """Mobile: collapsed with toggle, expand panel."""

    def test_toggle_button_present(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'conditions-strip__toggle' in html
            assert 'aria-expanded="false"' in html
            assert 'aria-controls="conditions-strip-expand"' in html

    def test_expand_panel_hidden_by_default(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'id="conditions-strip-expand"' in html
            assert 'hidden' in html

    def test_expand_panel_has_dimension_rows(self, client):
        cache = _make_conditions_cache(risk='Normal', policy_direction='Paused')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'conditions-strip__expand-row' in html
            assert 'conditions-strip__expand-label' in html
            assert 'conditions-strip__expand-value' in html

    def test_toggle_not_shown_in_fallback(self, client):
        with patch('dashboard.get_market_conditions', return_value=None):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'conditions-strip__toggle' not in html

    def test_mobile_toggle_min_height(self):
        """CSS should set 44px min-height for touch target."""
        css_path = SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css'
        css = css_path.read_text()
        assert 'min-height: 44px' in css

    def test_chevron_present(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'conditions-strip__chevron' in html


# ─── Quadrant Colors ─────────────────────────────────────────────────────────

class TestQuadrantColors:
    """Each quadrant maps to the correct CSS class."""

    @pytest.mark.parametrize('quadrant,css_class', [
        ('Goldilocks', 'conditions-strip--goldilocks'),
        ('Reflation', 'conditions-strip--reflation'),
        ('Deflation Risk', 'conditions-strip--deflation-risk'),
        ('Stagflation', 'conditions-strip--stagflation'),
    ])
    def test_quadrant_css_class(self, client, quadrant, css_class):
        cache = _make_conditions_cache(quadrant=quadrant)
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/rates')
            html = resp.data.decode()
            assert css_class in html

    def test_css_defines_quadrant_colors(self):
        css_path = SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css'
        css = css_path.read_text()
        assert '--quadrant-goldilocks: #0D9488' in css
        assert '--quadrant-reflation: #1E40AF' in css
        assert '--quadrant-deflation: #CA8A04' in css
        assert '--quadrant-stagflation: #DC2626' in css

    def test_css_defines_liquidity_colors(self):
        css_path = SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css'
        css = css_path.read_text()
        assert '--liq-expanding: #2563EB' in css
        assert '--liq-neutral: #64748B' in css
        assert '--liq-contracting: #D97706' in css


# ─── Display Labels ──────────────────────────────────────────────────────────

class TestDisplayLabels:
    """Verify display label mapping for compactness."""

    @pytest.mark.parametrize('state,expected', [
        ('Strongly Expanding', 'Expanding ↑↑'),
        ('Expanding', 'Expanding ↑'),
        ('Neutral', 'Neutral'),
        ('Contracting', 'Contracting ↓'),
        ('Strongly Contracting', 'Contracting ↓↓'),
    ])
    def test_liquidity_labels(self, client, state, expected):
        cache = _make_conditions_cache(liquidity=state)
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert expected in html

    @pytest.mark.parametrize('state,expected', [
        ('Calm', 'Calm'),
        ('Normal', 'Normal'),
        ('Elevated', 'Elevated'),
        ('Stressed', 'Stressed'),
    ])
    def test_risk_labels(self, client, state, expected):
        cache = _make_conditions_cache(risk=state)
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert expected in html

    @pytest.mark.parametrize('direction,expected', [
        ('Easing', 'Easing ↑'),
        ('Paused', 'Paused'),
        ('Tightening', 'Tightening ↓'),
    ])
    def test_policy_labels(self, client, direction, expected):
        cache = _make_conditions_cache(policy_direction=direction)
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            assert expected in html


# ─── Accessibility ────────────────────────────────────────────────────────────

class TestAccessibility:
    """ARIA attributes and semantic HTML."""

    def test_role_complementary(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'role="complementary"' in html

    def test_aria_label_on_strip(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'aria-label="Market conditions for this page"' in html

    def test_dot_aria_hidden(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'conditions-strip__dot' in html
            assert 'aria-hidden="true"' in html

    def test_aria_live_polite(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'aria-live="polite"' in html

    def test_toggle_aria_expanded(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'aria-expanded="false"' in html

    def test_toggle_aria_controls(self, client):
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'aria-controls="conditions-strip-expand"' in html

    def test_fallback_has_role_complementary(self, client):
        with patch('dashboard.get_market_conditions', return_value=None):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'role="complementary"' in html


# ─── Security ─────────────────────────────────────────────────────────────────

class TestSecurity:
    """No unescaped dynamic content (XSS prevention)."""

    def test_no_safe_filter_on_dynamic_values(self):
        """Template must not use | safe on cache-sourced values."""
        tpl_path = SIGNALTRACKERS_DIR / 'templates' / '_conditions_strip.html'
        content = tpl_path.read_text()
        # Find any instance of safe filter on variables (not comments)
        lines = [l for l in content.split('\n') if '| safe' in l and not l.strip().startswith('{#')]
        assert len(lines) == 0, f"Found | safe filter on: {lines}"


# ─── Template Migration ──────────────────────────────────────────────────────

class TestTemplateMigration:
    """Old _regime_strip.html is no longer included anywhere."""

    def test_no_regime_strip_includes(self):
        """No template should include _regime_strip.html."""
        templates_dir = SIGNALTRACKERS_DIR / 'templates'
        for tpl in templates_dir.glob('*.html'):
            content = tpl.read_text()
            # Skip the conditions strip itself (has comment referencing old file)
            if tpl.name == '_conditions_strip.html':
                continue
            assert '_regime_strip.html' not in content, \
                f"{tpl.name} still includes _regime_strip.html"

    def test_conditions_strip_on_all_pages(self):
        """All 11 pages should include _conditions_strip.html."""
        templates_dir = SIGNALTRACKERS_DIR / 'templates'
        expected_pages = [
            'index.html', 'credit.html', 'rates.html', 'equity.html',
            'dollar.html', 'crypto.html', 'safe_havens.html', 'property.html',
            'explorer.html', 'news.html', 'portfolio.html',
        ]
        for page in expected_pages:
            content = (templates_dir / page).read_text()
            assert '_conditions_strip.html' in content, \
                f"{page} does not include _conditions_strip.html"

    def test_crypto_page_has_liquidity_leads_flag(self):
        """Crypto page must set conditions_strip_liquidity_leads = true."""
        content = (SIGNALTRACKERS_DIR / 'templates' / 'crypto.html').read_text()
        assert 'conditions_strip_liquidity_leads = true' in content

    def test_non_crypto_pages_no_liquidity_leads(self):
        """Non-crypto pages should not set the liquidity_leads flag."""
        templates_dir = SIGNALTRACKERS_DIR / 'templates'
        non_crypto = [
            'index.html', 'credit.html', 'rates.html', 'equity.html',
            'dollar.html', 'safe_havens.html', 'property.html',
            'explorer.html', 'news.html', 'portfolio.html',
        ]
        for page in non_crypto:
            content = (templates_dir / page).read_text()
            assert 'conditions_strip_liquidity_leads' not in content, \
                f"{page} should not set conditions_strip_liquidity_leads"


# ─── CSS Component ────────────────────────────────────────────────────────────

class TestCSSComponent:
    """Verify conditions-strip.css exists and has required styles."""

    def test_css_file_exists(self):
        css_path = SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css'
        assert css_path.exists()

    def test_css_linked_in_base(self):
        base = (SIGNALTRACKERS_DIR / 'templates' / 'base.html').read_text()
        assert 'conditions-strip.css' in base

    def test_responsive_breakpoint(self):
        css = (SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css').read_text()
        assert '@media (min-width: 768px)' in css

    def test_desktop_hides_toggle(self):
        css = (SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css').read_text()
        # In the 768px+ media query, toggle should be display: none
        assert 'conditions-strip__toggle' in css

    def test_desktop_shows_dimensions(self):
        css = (SIGNALTRACKERS_DIR / 'static' / 'css' / 'components' / 'conditions-strip.css').read_text()
        assert 'conditions-strip__dimensions' in css


# ─── Edge Cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Handle partial data and missing fields gracefully."""

    def test_missing_policy_direction(self, client):
        cache = _make_conditions_cache()
        cache['dimensions']['policy'] = {'stance': 'Neutral'}  # no direction
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            assert resp.status_code == 200

    def test_missing_risk_state(self, client):
        cache = _make_conditions_cache()
        cache['dimensions']['risk'] = {}  # no state
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            assert resp.status_code == 200

    def test_empty_string_values(self, client):
        cache = _make_conditions_cache(
            quadrant='', liquidity='', risk='', policy_direction=''
        )
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            assert resp.status_code == 200

    def test_unknown_quadrant_renders(self, client):
        cache = _make_conditions_cache(quadrant='Unknown Future State')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            assert resp.status_code == 200
            assert b'UNKNOWN FUTURE STATE' in resp.data

    def test_toggle_js_present(self, client):
        """Toggle script should be included in the rendered page."""
        cache = _make_conditions_cache()
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/')
            html = resp.data.decode()
            assert 'conditions-strip__toggle' in html
            assert 'aria-expanded' in html


# ─── Crypto Mobile Expand ────────────────────────────────────────────────────

class TestCryptoMobileExpand:
    """Crypto mobile expand should show Quadrant instead of Liquidity."""

    def test_crypto_expand_shows_quadrant(self, client):
        cache = _make_conditions_cache(quadrant='Goldilocks', liquidity='Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/crypto')
            html = resp.data.decode()
            # In the expand panel, should show "Quadrant" label
            assert '>Quadrant<' in html

    def test_non_crypto_expand_shows_liquidity(self, client):
        cache = _make_conditions_cache(quadrant='Goldilocks', liquidity='Expanding')
        with patch('dashboard.get_market_conditions', return_value=cache):
            resp = client.get('/credit')
            html = resp.data.decode()
            # In the expand panel, should show "Liquidity" label
            assert '>Liquidity<' in html
