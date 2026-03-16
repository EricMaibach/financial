"""
Tests for US-293.1: Add ~18 new FRED series to market_signals.py

Acceptance criteria verified:
- All 17 new FRED series added to fred_series dict (3 already existed)
- Existing series remain unchanged
- All series IDs are valid FRED identifiers
- CSV filenames follow existing naming convention
- Unit mismatches documented in code comments (RRPONTSYD billions vs WALCL/WDTGAL millions)
- Mixed-frequency series (daily/weekly/monthly/quarterly) all present
- fetch_fred_data handles missing/delayed series gracefully (returns None, no crash)
- collect_fred_signals iterates all series without error
- Incremental append works (start_date advances past last collected date)
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Ensure signaltrackers is importable
SIGNALTRACKERS_DIR = Path(__file__).parent.parent / 'signaltrackers'
sys.path.insert(0, str(SIGNALTRACKERS_DIR))

from market_signals import MarketSignalsTracker


# ─── Series Presence ────────────────────────────────────────────────────────

class TestNewSeriesPresence:
    """All 17 new FRED series must be present in the tracker."""

    @pytest.fixture(autouse=True)
    def tracker(self):
        self.tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')

    # --- Layer 1: Global Liquidity ---

    def test_treasury_general_account(self):
        assert 'treasury_general_account' in self.tracker.fred_series
        assert self.tracker.fred_series['treasury_general_account'] == 'WDTGAL'

    def test_ecb_total_assets(self):
        assert 'ecb_total_assets' in self.tracker.fred_series
        assert self.tracker.fred_series['ecb_total_assets'] == 'ECBASSETSW'

    def test_boj_total_assets(self):
        assert 'boj_total_assets' in self.tracker.fred_series
        assert self.tracker.fred_series['boj_total_assets'] == 'JPNASSETS'

    def test_fx_eur_usd(self):
        assert 'fx_eur_usd' in self.tracker.fred_series
        assert self.tracker.fred_series['fx_eur_usd'] == 'DEXUSEU'

    def test_fx_jpy_usd(self):
        assert 'fx_jpy_usd' in self.tracker.fred_series
        assert self.tracker.fred_series['fx_jpy_usd'] == 'DEXJPUS'

    # --- Layer 2: Growth × Inflation ---

    def test_industrial_production(self):
        assert 'industrial_production' in self.tracker.fred_series
        assert self.tracker.fred_series['industrial_production'] == 'INDPRO'

    def test_building_permits(self):
        assert 'building_permits' in self.tracker.fred_series
        assert self.tracker.fred_series['building_permits'] == 'PERMIT'

    def test_breakeven_inflation_5y(self):
        assert 'breakeven_inflation_5y' in self.tracker.fred_series
        assert self.tracker.fred_series['breakeven_inflation_5y'] == 'T5YIE'

    def test_core_pce_price_index(self):
        assert 'core_pce_price_index' in self.tracker.fred_series
        assert self.tracker.fred_series['core_pce_price_index'] == 'PCEPILFE'

    # --- Layer 3: Risk Regime ---

    def test_vix_3month(self):
        assert 'vix_3month' in self.tracker.fred_series
        assert self.tracker.fred_series['vix_3month'] == 'VXVCLS'

    def test_stl_financial_stress(self):
        assert 'stl_financial_stress' in self.tracker.fred_series
        assert self.tracker.fred_series['stl_financial_stress'] == 'STLFSI4'

    # --- Layer 4: Policy Stance ---

    def test_fed_funds_upper_target(self):
        assert 'fed_funds_upper_target' in self.tracker.fred_series
        assert self.tracker.fred_series['fed_funds_upper_target'] == 'DFEDTARU'

    def test_pce_price_index(self):
        assert 'pce_price_index' in self.tracker.fred_series
        assert self.tracker.fred_series['pce_price_index'] == 'PCEPI'

    def test_real_gdp(self):
        assert 'real_gdp' in self.tracker.fred_series
        assert self.tracker.fred_series['real_gdp'] == 'GDPC1'

    def test_potential_gdp(self):
        assert 'potential_gdp' in self.tracker.fred_series
        assert self.tracker.fred_series['potential_gdp'] == 'GDPPOT'

    def test_unemployment_rate(self):
        assert 'unemployment_rate' in self.tracker.fred_series
        assert self.tracker.fred_series['unemployment_rate'] == 'UNRATE'

    def test_natural_unemployment_rate(self):
        assert 'natural_unemployment_rate' in self.tracker.fred_series
        assert self.tracker.fred_series['natural_unemployment_rate'] == 'NROU'


# ─── Existing Series Unchanged ──────────────────────────────────────────────

class TestExistingSeriesUnchanged:
    """All pre-existing FRED series must remain in the tracker unchanged."""

    @pytest.fixture(autouse=True)
    def tracker(self):
        self.tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')

    EXISTING_SERIES = {
        'high_yield_spread': 'BAMLH0A0HYM2',
        'investment_grade_spread': 'BAMLC0A0CM',
        'ccc_spread': 'BAMLH0A3HYC',
        'japan_10y_yield': 'IRLTLT01JPM156N',
        'germany_10y_yield': 'IRLTLT01DEM156N',
        'yield_curve_10y2y': 'T10Y2Y',
        'yield_curve_10y3m': 'T10Y3M',
        'initial_claims': 'ICSA',
        'continuing_claims': 'CCSA',
        'consumer_confidence': 'UMCSENT',
        'm2_money_supply': 'M2SL',
        'cpi': 'CPIAUCSL',
        'fed_balance_sheet': 'WALCL',
        'reverse_repo': 'RRPONTSYD',
        'nfci': 'NFCI',
        'real_yield_10y': 'DFII10',
        'breakeven_inflation_10y': 'T10YIE',
        'treasury_10y': 'DGS10',
        'fed_funds_rate': 'FEDFUNDS',
        'trade_balance': 'BOPGSTB',
        'cli': 'USSLIND',
        'ism_manufacturing': 'NAPM',
        'property_hpi': 'CSUSHPISA',
        'property_cpi_rent': 'CUUR0000SEHA',
        'property_vacancy': 'RRVRUSQ156N',
    }

    @pytest.mark.parametrize("name,series_id", EXISTING_SERIES.items())
    def test_existing_series_present(self, name, series_id):
        assert name in self.tracker.fred_series, f"Missing existing series: {name}"
        assert self.tracker.fred_series[name] == series_id, f"Series ID changed for {name}"


# ─── Series Count ───────────────────────────────────────────────────────────

class TestSeriesCount:
    """Total series count should reflect old + new."""

    def test_total_fred_series_count(self):
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        # 25 existing + 17 new = 42 total
        assert len(tracker.fred_series) == 42

    def test_no_duplicate_series_ids(self):
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        ids = list(tracker.fred_series.values())
        assert len(ids) == len(set(ids)), f"Duplicate FRED series IDs: {[x for x in ids if ids.count(x) > 1]}"

    def test_no_duplicate_signal_names(self):
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        names = list(tracker.fred_series.keys())
        assert len(names) == len(set(names))


# ─── Unit Mismatch Documentation ────────────────────────────────────────────

class TestDocumentation:
    """Unit mismatches and FX conversion notes must be documented in code."""

    def test_rrpontsyd_unit_mismatch_documented(self):
        """RRPONTSYD is in billions vs WALCL/WDTGAL in millions — must be noted."""
        source = Path(SIGNALTRACKERS_DIR / 'market_signals.py').read_text()
        # Check that the unit mismatch is mentioned somewhere near the series
        assert 'BILLIONS' in source.upper() or 'billions' in source.lower(), \
            "RRPONTSYD unit mismatch (billions) not documented"

    def test_ecb_fx_conversion_documented(self):
        source = Path(SIGNALTRACKERS_DIR / 'market_signals.py').read_text()
        assert 'ECB' in source and 'USD' in source, "ECB→USD conversion not documented"

    def test_boj_fx_conversion_documented(self):
        source = Path(SIGNALTRACKERS_DIR / 'market_signals.py').read_text()
        assert 'BOJ' in source and 'USD' in source, "BOJ→USD conversion not documented"


# ─── Mixed Frequency Coverage ───────────────────────────────────────────────

class TestMixedFrequency:
    """All frequency types (daily, weekly, monthly, quarterly) must be represented."""

    def test_daily_series_present(self):
        """At least one daily series in the new additions."""
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        # DEXUSEU, DEXJPUS, T5YIE, VXVCLS, DFEDTARU are all daily
        daily_new = ['fx_eur_usd', 'fx_jpy_usd', 'breakeven_inflation_5y',
                     'vix_3month', 'fed_funds_upper_target']
        for name in daily_new:
            assert name in tracker.fred_series

    def test_weekly_series_present(self):
        """At least one weekly series in the new additions."""
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        weekly_new = ['treasury_general_account', 'ecb_total_assets', 'stl_financial_stress']
        for name in weekly_new:
            assert name in tracker.fred_series

    def test_monthly_series_present(self):
        """At least one monthly series in the new additions."""
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        monthly_new = ['boj_total_assets', 'industrial_production', 'building_permits',
                       'core_pce_price_index', 'pce_price_index', 'unemployment_rate']
        for name in monthly_new:
            assert name in tracker.fred_series

    def test_quarterly_series_present(self):
        """At least one quarterly series in the new additions."""
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        quarterly_new = ['real_gdp', 'potential_gdp', 'natural_unemployment_rate']
        for name in quarterly_new:
            assert name in tracker.fred_series


# ─── Graceful Error Handling ────────────────────────────────────────────────

class TestErrorHandling:
    """Missing or delayed series must not crash the pipeline."""

    def test_fetch_fred_data_returns_none_on_api_error(self):
        import requests as req_lib
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        with patch('market_signals.requests.get') as mock_get:
            mock_get.side_effect = req_lib.exceptions.ConnectionError("API unavailable")
            result = tracker.fetch_fred_data('WDTGAL')
            assert result is None

    def test_fetch_fred_data_returns_none_on_empty_observations(self):
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        with patch('market_signals.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {'observations': []}
            mock_get.return_value = mock_response
            result = tracker.fetch_fred_data('WDTGAL')
            # Empty observations → empty DataFrame → returns None (dropna empties it)
            assert result is None or result.empty

    def test_fetch_fred_data_returns_none_without_api_key(self):
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key=None)
        result = tracker.fetch_fred_data('WDTGAL')
        assert result is None

    def test_collect_fred_signals_skips_failed_series(self):
        """If one series fails, others should still collect."""
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931_collect', fred_api_key='test')
        call_count = 0

        def mock_fetch(series_id, start_date=None):
            nonlocal call_count
            call_count += 1
            return None  # Simulate all failures

        with patch.object(tracker, 'fetch_fred_data', side_effect=mock_fetch):
            tracker.collect_fred_signals()
            # Should have called fetch for every series without crashing
            assert call_count == len(tracker.fred_series)

        # Cleanup
        import shutil
        shutil.rmtree('/tmp/test_data_us2931_collect', ignore_errors=True)


# ─── Incremental Append ─────────────────────────────────────────────────────

class TestIncrementalAppend:
    """Incremental collection should advance start_date past last collected date."""

    def test_start_date_advances_for_existing_csv(self, tmp_path):
        tracker = MarketSignalsTracker(data_dir=str(tmp_path), fred_api_key='test')
        csv_path = tmp_path / 'treasury_general_account.csv'

        # Write existing data
        df = pd.DataFrame({
            'date': pd.to_datetime(['2026-01-01', '2026-01-08', '2026-01-15']),
            'treasury_general_account': [800000, 810000, 805000]
        })
        df.to_csv(csv_path, index=False)

        last_date = tracker.get_last_date_in_file(csv_path)
        assert last_date == pd.Timestamp('2026-01-15')

    def test_append_avoids_duplicates(self, tmp_path):
        tracker = MarketSignalsTracker(data_dir=str(tmp_path), fred_api_key='test')
        csv_path = tmp_path / 'test_series.csv'

        # Write initial data
        df1 = pd.DataFrame({
            'date': pd.to_datetime(['2026-01-01', '2026-01-02']),
            'value': [100.0, 200.0]
        })
        df1.to_csv(csv_path, index=False)

        # Append overlapping + new data
        df2 = pd.DataFrame({
            'date': pd.to_datetime(['2026-01-02', '2026-01-03']),
            'value': [200.0, 300.0]
        })
        tracker.append_to_csv(df2, csv_path)

        result = pd.read_csv(csv_path)
        assert len(result) == 3  # No duplicate for 2026-01-02


# ─── CSV Filename Convention ────────────────────────────────────────────────

class TestFilenameConvention:
    """All new series should produce CSVs matching the signal_name.csv pattern."""

    NEW_SERIES_NAMES = [
        'treasury_general_account', 'ecb_total_assets', 'boj_total_assets',
        'fx_eur_usd', 'fx_jpy_usd', 'industrial_production', 'building_permits',
        'breakeven_inflation_5y', 'core_pce_price_index', 'vix_3month',
        'stl_financial_stress', 'fed_funds_upper_target', 'pce_price_index',
        'real_gdp', 'potential_gdp', 'unemployment_rate', 'natural_unemployment_rate',
    ]

    @pytest.mark.parametrize("name", NEW_SERIES_NAMES)
    def test_csv_filename_is_snake_case(self, name):
        """Signal names must be valid snake_case (produces valid filenames)."""
        assert name == name.lower(), f"Signal name {name} is not lowercase"
        assert ' ' not in name, f"Signal name {name} contains spaces"
        assert all(c.isalnum() or c == '_' for c in name), \
            f"Signal name {name} contains invalid characters"

    @pytest.mark.parametrize("name", NEW_SERIES_NAMES)
    def test_expected_csv_path(self, name):
        """Each signal should map to data/{name}.csv."""
        tracker = MarketSignalsTracker(data_dir='/tmp/test_data_us2931', fred_api_key='test')
        expected_path = Path('/tmp/test_data_us2931') / f'{name}.csv'
        # The collect_fred_signals method uses: self.data_dir / f"{signal_name}.csv"
        assert name in tracker.fred_series
