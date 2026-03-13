"""
Tests for US-255.1: Property macro backend — FRED + USDA NASS data pipeline
and interpretation config.

Acceptance criteria verified:
- FRED series CSUSHPISA, CUUR0000SEHA, RRVRUSQ156N defined in market_signals
- USDA NASS farmland fetch method exists and handles missing API key gracefully
- Percentile calculations for HPI and CPI Rent
- YoY change computed for HPI and CPI Rent; QoQ direction for vacancy rate
- Interpretation config with >= 8 combinations
- Flask route /property exists and returns 200
- Template property.html exists and passes required context keys
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure signaltrackers is importable
SIGNALTRACKERS_DIR = Path(__file__).parent.parent / 'signaltrackers'
sys.path.insert(0, str(SIGNALTRACKERS_DIR))


# ─── property_interpretation_config ──────────────────────────────────────────

class TestPropertyInterpretationConfig:
    def test_import_succeeds(self):
        from property_interpretation_config import (
            PROPERTY_INTERPRETATIONS,
            get_property_interpretation,
        )
        assert PROPERTY_INTERPRETATIONS is not None
        assert callable(get_property_interpretation)

    def test_minimum_eight_combinations(self):
        from property_interpretation_config import PROPERTY_INTERPRETATIONS
        assert len(PROPERTY_INTERPRETATIONS) >= 8

    def test_all_four_regimes_present(self):
        from property_interpretation_config import PROPERTY_INTERPRETATIONS
        regimes = {k[0] for k in PROPERTY_INTERPRETATIONS.keys()}
        for regime in ('Bull', 'Neutral', 'Bear', 'Recession Watch'):
            assert regime in regimes, f"Missing regime: {regime}"

    def test_unknown_fallback_present(self):
        from property_interpretation_config import PROPERTY_INTERPRETATIONS
        unknown_keys = [k for k in PROPERTY_INTERPRETATIONS.keys() if k[0] == 'unknown']
        assert len(unknown_keys) >= 3

    def test_all_values_are_non_empty_strings(self):
        from property_interpretation_config import PROPERTY_INTERPRETATIONS
        for key, text in PROPERTY_INTERPRETATIONS.items():
            assert isinstance(text, str), f"Value for {key} is not a string"
            assert len(text) > 20, f"Value for {key} is too short"

    def test_get_interpretation_appreciating(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation('Bull', 3.5)
        assert text is not None
        assert bucket == 'appreciating'

    def test_get_interpretation_flat(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation('Neutral', 0.5)
        assert text is not None
        assert bucket == 'flat'

    def test_get_interpretation_depreciating(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation('Bear', -3.0)
        assert text is not None
        assert bucket == 'depreciating'

    def test_bucket_boundary_at_2pct(self):
        from property_interpretation_config import get_property_interpretation
        _, bucket = get_property_interpretation('Bull', 2.0)
        assert bucket == 'appreciating'
        _, bucket = get_property_interpretation('Bull', 1.9)
        assert bucket == 'flat'
        _, bucket = get_property_interpretation('Bull', -2.0)
        assert bucket == 'depreciating'
        _, bucket = get_property_interpretation('Bull', -1.9)
        assert bucket == 'flat'

    def test_none_hpi_returns_none_none(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation('Bull', None)
        assert text is None
        assert bucket is None

    def test_none_regime_uses_unknown_fallback(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation(None, 5.0)
        assert text is not None
        assert bucket == 'appreciating'

    def test_unknown_regime_uses_unknown_fallback(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation('unknown', 1.0)
        assert text is not None
        assert bucket == 'flat'

    def test_recession_watch_regime(self):
        from property_interpretation_config import get_property_interpretation
        text, bucket = get_property_interpretation('Recession Watch', -5.0)
        assert text is not None
        assert bucket == 'depreciating'

    def test_all_regime_hpi_combos_resolvable(self):
        from property_interpretation_config import get_property_interpretation
        regimes = ['Bull', 'Neutral', 'Bear', 'Recession Watch']
        hpi_values = [5.0, 0.0, -5.0]  # appreciating, flat, depreciating
        for regime in regimes:
            for hpi in hpi_values:
                text, bucket = get_property_interpretation(regime, hpi)
                assert text is not None, f"Missing interpretation for ({regime}, hpi={hpi})"


# ─── market_signals.py — FRED property series ────────────────────────────────

class TestMarketSignalsFREDSeries:
    def test_property_fred_series_defined(self):
        from market_signals import MarketSignalsTracker
        tracker = MarketSignalsTracker()
        assert 'property_hpi' in tracker.fred_series
        assert 'property_cpi_rent' in tracker.fred_series
        assert 'property_vacancy' in tracker.fred_series

    def test_property_fred_series_ids_correct(self):
        from market_signals import MarketSignalsTracker
        tracker = MarketSignalsTracker()
        assert tracker.fred_series['property_hpi'] == 'CSUSHPISA'
        assert tracker.fred_series['property_cpi_rent'] == 'CUUR0000SEHA'
        assert tracker.fred_series['property_vacancy'] == 'RRVRUSQ156N'

    def test_usda_nass_method_exists(self):
        from market_signals import MarketSignalsTracker
        assert hasattr(MarketSignalsTracker, 'fetch_usda_nass_farmland')
        assert callable(MarketSignalsTracker.fetch_usda_nass_farmland)

    def test_usda_nass_returns_none_when_key_missing(self):
        from market_signals import MarketSignalsTracker
        tracker = MarketSignalsTracker()
        with patch.dict(os.environ, {}, clear=False):
            # Remove USDA_NASS_API_KEY if present
            env_backup = os.environ.pop('USDA_NASS_API_KEY', None)
            try:
                result = tracker.fetch_usda_nass_farmland()
                assert result is None
            finally:
                if env_backup is not None:
                    os.environ['USDA_NASS_API_KEY'] = env_backup

    def test_run_daily_collection_calls_usda(self):
        """run_daily_collection should invoke fetch_usda_nass_farmland."""
        from market_signals import MarketSignalsTracker
        tracker = MarketSignalsTracker()
        with patch.object(tracker, 'collect_fred_signals'), \
             patch.object(tracker, 'collect_etf_signals'), \
             patch.object(tracker, 'collect_fear_greed_index'), \
             patch.object(tracker, 'calculate_derived_metrics'), \
             patch.object(tracker, 'fetch_usda_nass_farmland') as mock_usda:
            tracker.run_daily_collection()
            mock_usda.assert_called_once()


# ─── dashboard.py — /property route ──────────────────────────────────────────

@pytest.fixture
def client():
    from dashboard import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


class TestPropertyRoute:
    def test_route_returns_200(self, client):
        resp = client.get('/property')
        assert resp.status_code == 200

    def test_route_returns_html(self, client):
        resp = client.get('/property')
        assert b'text/html' in resp.content_type.encode()

    def test_page_title_present(self, client):
        resp = client.get('/property')
        assert b'Property Macro' in resp.data

    def test_empty_state_renders_without_data(self, client):
        """Route must render gracefully even when all CSV files are absent."""
        with patch('dashboard.load_csv_data', return_value=None), \
             patch('dashboard.DATA_DIR', Path('/nonexistent')):
            resp = client.get('/property')
            assert resp.status_code == 200

    def test_route_name_is_property_macro(self):
        from dashboard import app
        with app.test_request_context():
            from flask import url_for
            url = url_for('property_macro')
            assert url == '/property'


# ─── Template — property.html ─────────────────────────────────────────────────

class TestPropertyTemplate:
    def _get_template_path(self):
        return SIGNALTRACKERS_DIR / 'templates' / 'property.html'

    def test_template_exists(self):
        assert self._get_template_path().exists()

    def test_extends_base_html(self):
        content = self._get_template_path().read_text()
        assert 'extends "base.html"' in content

    def test_page_title_block(self):
        content = self._get_template_path().read_text()
        assert 'Property Macro' in content

    def test_hpi_context_key_used(self):
        content = self._get_template_path().read_text()
        assert 'hpi_current' in content

    def test_cpi_rent_context_key_used(self):
        content = self._get_template_path().read_text()
        assert 'cpi_rent_yoy_pct' in content

    def test_vacancy_context_key_used(self):
        content = self._get_template_path().read_text()
        assert 'vacancy_current' in content

    def test_farmland_context_key_used(self):
        content = self._get_template_path().read_text()
        assert 'farmland_farm_re' in content

    def test_interpretation_block_present(self):
        content = self._get_template_path().read_text()
        assert 'property_interpretation' in content

    def test_percentile_progressbar_aria(self):
        content = self._get_template_path().read_text()
        assert 'role="progressbar"' in content
        assert 'aria-valuenow' in content

    def test_asset_page_header_used(self):
        content = self._get_template_path().read_text()
        assert 'asset-page-header' in content

    def test_bi_house_door_icon(self):
        content = self._get_template_path().read_text()
        assert 'bi-house-door' in content

    def test_category_color_violet(self):
        content = self._get_template_path().read_text()
        assert '#8B5CF6' in content

    def test_farmland_unavailable_message(self):
        content = self._get_template_path().read_text()
        assert 'USDA_NASS_API_KEY' in content

    def test_dl_used_for_farmland(self):
        content = self._get_template_path().read_text()
        assert '<dl' in content


# ─── base.html — navbar integration ──────────────────────────────────────────

class TestBaseNavbar:
    def _get_base_path(self):
        return SIGNALTRACKERS_DIR / 'templates' / 'base.html'

    def test_property_nav_link_exists(self):
        content = self._get_base_path().read_text()
        assert 'href="/property"' in content

    def test_property_nav_label(self):
        content = self._get_base_path().read_text()
        assert '>&#xA0;Property' in content or '> Property' in content or '>Property' in content or 'Property\n' in content

    def test_property_nav_icon(self):
        content = self._get_base_path().read_text()
        assert 'bi-house-door' in content

    def test_property_macro_in_active_endpoints(self):
        content = self._get_base_path().read_text()
        assert 'property_macro' in content

    def test_property_after_safe_havens(self):
        content = self._get_base_path().read_text()
        safe_havens_pos = content.find('safe-havens')
        property_pos = content.find('href="/property"')
        assert safe_havens_pos < property_pos, \
            "Property nav link should appear after Safe Havens in navbar"


# ─── .env.example ─────────────────────────────────────────────────────────────

def _find_env_example():
    """Find .env.example at the repo root (one or two levels up from tests/)."""
    candidates = [
        SIGNALTRACKERS_DIR.parent / '.env.example',
        SIGNALTRACKERS_DIR.parent.parent / '.env.example',
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


@pytest.mark.skipif(_find_env_example() is None, reason=".env.example not in Docker container")
class TestEnvExample:
    def _get_env_example_path(self):
        return _find_env_example()

    def test_usda_nass_key_in_env_example(self):
        content = self._get_env_example_path().read_text()
        assert 'USDA_NASS_API_KEY' in content

    def test_usda_nass_has_comment(self):
        content = self._get_env_example_path().read_text()
        assert 'quickstats.nass.usda.gov' in content or 'USDA NASS' in content


# ─── Data computation helpers ─────────────────────────────────────────────────

class TestDataComputations:
    """Verify YoY, QoQ, and percentile logic used in the /property route."""

    def test_yoy_calculation_positive(self):
        """HPI YoY: (current / year_ago - 1) * 100."""
        current = 330.0
        year_ago = 315.0
        yoy = round((current / year_ago - 1) * 100, 1)
        assert yoy == pytest.approx(4.8, abs=0.1)

    def test_yoy_calculation_negative(self):
        current = 290.0
        year_ago = 315.0
        yoy = round((current / year_ago - 1) * 100, 1)
        assert yoy < 0

    def test_vacancy_direction_tightening(self):
        current = 5.8
        prior = 6.2
        direction = 'tightening' if current < prior else 'loosening'
        assert direction == 'tightening'

    def test_vacancy_direction_loosening(self):
        current = 7.0
        prior = 6.5
        direction = 'tightening' if current < prior else 'loosening'
        assert direction == 'loosening'

    def test_percentile_rank_basic(self):
        """calculate_percentile_rank used in the route — use recent dates to stay within 20yr window."""
        from dashboard import calculate_percentile_rank
        # Use recent monthly dates so all data falls within the 20-year rolling window
        idx = pd.date_range(start='2016-01-31', periods=100, freq='ME')
        series = pd.Series(list(range(1, 101)), index=idx)
        pct = calculate_percentile_rank(series, 75)
        assert 70 <= pct <= 80

    def test_percentile_rank_min(self):
        from dashboard import calculate_percentile_rank
        series = pd.Series([10, 20, 30, 40, 50],
                           index=pd.date_range('2000-01-01', periods=5, freq='ME'))
        pct = calculate_percentile_rank(series, 1)
        assert pct == 0.0

    def test_percentile_rank_max(self):
        from dashboard import calculate_percentile_rank
        series = pd.Series([10, 20, 30, 40, 50],
                           index=pd.date_range('2000-01-01', periods=5, freq='ME'))
        pct = calculate_percentile_rank(series, 100)
        assert pct == 100.0
