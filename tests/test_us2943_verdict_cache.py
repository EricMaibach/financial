"""
Tests for market conditions engine: asset expectations, cache output, and integration.

Updated for US-314.1: verdict classifier removed; quadrant is the headline.

Tests cover:
1. Asset class expectations tables
2. compute_market_conditions() integration (quadrant as headline)
3. Cache output format and I/O
4. Realistic scenario tests
5. Edge cases
6. Market conditions history
7. NROU deduplication
"""

import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# Ensure signaltrackers is importable
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
if SIGNALTRACKERS_DIR not in sys.path:
    sys.path.insert(0, SIGNALTRACKERS_DIR)

from market_conditions import (
    _build_asset_expectations,
    _QUADRANT_EXPECTATIONS,
    compute_market_conditions,
    update_market_conditions_cache,
    get_market_conditions,
    _load_conditions_history,
    _save_conditions_history,
    _append_conditions_history,
    get_conditions_history,
    MARKET_CONDITIONS_CACHE_FILE,
    MARKET_CONDITIONS_HISTORY_FILE,
    MarketConditionsResult,
    LiquidityResult,
    QuadrantResult,
    RiskResult,
    PolicyResult,
)


# ============================================================================
# 1. Asset Class Expectations
# ============================================================================

class TestAssetExpectations:
    """Test the expectations table logic."""

    def test_goldilocks_calm_expanding(self):
        """Best case: Goldilocks + Calm + Expanding."""
        exps = _build_asset_expectations('Goldilocks', 'Expanding', 'Calm')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['sp500']['direction'] == 'positive'
        assert by_asset['treasuries']['direction'] == 'positive'
        assert by_asset['gold']['direction'] == 'neutral'
        assert by_asset['bitcoin']['direction'] == 'positive'
        assert by_asset['sp500']['conviction'] == 'high'
        assert by_asset['sp500']['magnitude'] == 'moderate'

    def test_stagflation_stressed(self):
        """Worst case: Stagflation + Stressed."""
        exps = _build_asset_expectations('Stagflation', 'Strongly Contracting', 'Stressed')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['sp500']['direction'] == 'negative'
        assert by_asset['sp500']['conviction'] == 'override'
        assert by_asset['treasuries']['direction'] == 'negative'
        assert by_asset['treasuries']['magnitude'] == 'weak'
        assert by_asset['gold']['direction'] == 'positive'
        assert by_asset['gold']['conviction'] == 'override'
        assert by_asset['bitcoin']['direction'] == 'negative'
        assert by_asset['bitcoin']['magnitude'] == 'weak'
        assert by_asset['bitcoin']['conviction'] == 'override'

    def test_reflation_normal(self):
        exps = _build_asset_expectations('Reflation', 'Neutral', 'Normal')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['sp500']['direction'] == 'positive'
        assert by_asset['treasuries']['direction'] == 'negative'
        assert by_asset['gold']['direction'] == 'positive'

    def test_deflation_risk(self):
        exps = _build_asset_expectations('Deflation Risk', 'Contracting', 'Elevated')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['sp500']['direction'] == 'negative'
        assert by_asset['treasuries']['direction'] == 'positive'
        assert by_asset['gold']['direction'] == 'neutral'
        assert by_asset['sp500']['conviction'] == 'low'

    def test_stressed_overrides_sp500_to_negative(self):
        """Even in Goldilocks (sp500 positive), Stressed forces sp500 negative."""
        exps = _build_asset_expectations('Goldilocks', 'Expanding', 'Stressed')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['sp500']['direction'] == 'negative'
        assert by_asset['sp500']['conviction'] == 'override'

    def test_all_quadrants_return_four_assets(self):
        for quad in _QUADRANT_EXPECTATIONS:
            exps = _build_asset_expectations(quad, 'Neutral', 'Normal')
            assert len(exps) == 4
            assets = {e['asset'] for e in exps}
            assert assets == {'sp500', 'treasuries', 'gold', 'bitcoin'}

    def test_liquidity_magnitude_mapping(self):
        """Each liquidity state produces a different magnitude."""
        magnitudes = set()
        for liq_state in ['Strongly Expanding', 'Expanding', 'Neutral', 'Contracting', 'Strongly Contracting']:
            exps = _build_asset_expectations('Goldilocks', liq_state, 'Normal')
            magnitudes.add(exps[0]['magnitude'])
        assert len(magnitudes) == 5  # All different

    def test_risk_conviction_mapping(self):
        """Each risk state produces a different conviction (except Stressed override)."""
        convictions = set()
        for risk_state in ['Calm', 'Normal', 'Elevated']:
            exps = _build_asset_expectations('Goldilocks', 'Neutral', risk_state)
            convictions.add(exps[0]['conviction'])
        assert len(convictions) == 3

    def test_bitcoin_expanding_liquidity_positive(self):
        """Bitcoin direction positive when liquidity is Expanding."""
        exps = _build_asset_expectations('Goldilocks', 'Expanding', 'Normal')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['bitcoin']['direction'] == 'positive'
        assert by_asset['bitcoin']['magnitude'] == 'moderate'
        assert by_asset['bitcoin']['conviction'] == 'standard'

    def test_bitcoin_strongly_expanding_positive(self):
        exps = _build_asset_expectations('Goldilocks', 'Strongly Expanding', 'Calm')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['bitcoin']['direction'] == 'positive'
        assert by_asset['bitcoin']['magnitude'] == 'strong'

    def test_bitcoin_neutral_liquidity_neutral(self):
        exps = _build_asset_expectations('Stagflation', 'Neutral', 'Normal')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['bitcoin']['direction'] == 'neutral'

    def test_bitcoin_contracting_liquidity_negative(self):
        exps = _build_asset_expectations('Reflation', 'Contracting', 'Elevated')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['bitcoin']['direction'] == 'negative'
        assert by_asset['bitcoin']['magnitude'] == 'reduced'

    def test_bitcoin_strongly_contracting_negative(self):
        exps = _build_asset_expectations('Deflation Risk', 'Strongly Contracting', 'Normal')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['bitcoin']['direction'] == 'negative'
        assert by_asset['bitcoin']['magnitude'] == 'weak'

    def test_bitcoin_stressed_override(self):
        """Stressed risk → bitcoin gets weak magnitude and override conviction."""
        exps = _build_asset_expectations('Goldilocks', 'Expanding', 'Stressed')
        by_asset = {e['asset']: e for e in exps}
        assert by_asset['bitcoin']['magnitude'] == 'weak'
        assert by_asset['bitcoin']['conviction'] == 'override'

    def test_bitcoin_independent_of_quadrant(self):
        """Bitcoin direction depends on liquidity, not quadrant."""
        for quad in _QUADRANT_EXPECTATIONS:
            exps = _build_asset_expectations(quad, 'Expanding', 'Normal')
            by_asset = {e['asset']: e for e in exps}
            assert by_asset['bitcoin']['direction'] == 'positive'


# ============================================================================
# 2. compute_market_conditions() Integration
# ============================================================================

def _mock_liquidity(state='Expanding', score=0.8):
    return LiquidityResult(state=state, score=score, as_of='2025-01-15')


def _mock_quadrant(quadrant='Goldilocks', growth=0.5, inflation=-0.3):
    return QuadrantResult(
        quadrant=quadrant, growth_composite=growth,
        inflation_composite=inflation, raw_quadrant=quadrant,
        stable=True, as_of='2025-01-15',
    )


def _mock_risk(state='Normal', score=2):
    return RiskResult(
        state=state, score=score, vix_score=1,
        term_structure_score=0, correlation_score=1,
        as_of='2025-01-15',
    )


def _mock_policy(stance='Neutral', direction='Paused'):
    return PolicyResult(
        stance=stance, direction=direction, taylor_gap=0.3,
        taylor_prescribed=4.5, actual_rate=4.8,
        as_of='2025-01-15',
    )


class TestComputeMarketConditions:
    """Integration tests — quadrant is the headline classification."""

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_goldilocks_quadrant(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Strongly Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Goldilocks'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_stagflation_quadrant(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Contracting')
        mock_quad.return_value = _mock_quadrant('Stagflation')
        mock_risk.return_value = _mock_risk('Elevated')
        mock_pol.return_value = _mock_policy('Restrictive')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Stagflation'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_reflation_quadrant(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Reflation')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Reflation'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_deflation_risk_quadrant(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Neutral')
        mock_quad.return_value = _mock_quadrant('Deflation Risk')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Deflation Risk'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_no_verdict_fields(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Result should NOT have verdict or verdict_score fields."""
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions()
        assert result is not None
        assert not hasattr(result, 'verdict')
        assert not hasattr(result, 'verdict_score')

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_no_mapped_score_fields(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Result should NOT have dimension mapped score fields (removed with verdict)."""
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions()
        assert result is not None
        assert not hasattr(result, 'liquidity_mapped')
        assert not hasattr(result, 'quadrant_mapped')
        assert not hasattr(result, 'risk_mapped')
        assert not hasattr(result, 'policy_mapped')

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_missing_liquidity_returns_none(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = None
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        assert compute_market_conditions() is None

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_missing_quadrant_returns_none(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = None
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        assert compute_market_conditions() is None

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_missing_risk_defaults_to_normal(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = None
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions()
        assert result is not None
        assert result.risk_state == 'Normal'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_missing_policy_defaults_to_neutral(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = None

        result = compute_market_conditions()
        assert result is not None
        assert result.policy_stance == 'Neutral'
        assert result.policy_direction == 'Paused'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_result_has_asset_expectations(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions()
        assert result is not None
        assert len(result.asset_expectations) == 4
        assets = {e['asset'] for e in result.asset_expectations}
        assert assets == {'sp500', 'treasuries', 'gold', 'bitcoin'}

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_as_of_uses_today_not_dimension_dates(self, mock_liq, mock_quad, mock_risk, mock_pol):
        from datetime import date as _date

        mock_liq.return_value = _mock_liquidity()
        mock_liq.return_value.as_of = '2025-01-10'
        mock_quad.return_value = _mock_quadrant()
        mock_quad.return_value.as_of = '2025-01-15'
        mock_risk.return_value = _mock_risk()
        mock_risk.return_value.as_of = '2025-01-12'
        mock_pol.return_value = _mock_policy()
        mock_pol.return_value.as_of = '2025-01-08'

        result = compute_market_conditions()
        assert result is not None
        assert result.as_of == str(_date.today())

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_as_of_uses_explicit_date_for_backtest(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions('2024-06-15')
        assert result is not None
        assert result.as_of == '2024-06-15'


# ============================================================================
# 3. Cache I/O
# ============================================================================

class TestCacheIO:
    """Test cache write and read."""

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_write_and_read(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_history = f.name

        try:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', tmp_path), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp_history):
                cache_data = update_market_conditions_cache()
                assert cache_data is not None
                assert cache_data['quadrant'] == 'Goldilocks'
                assert 'verdict' not in cache_data
                assert 'verdict_score' not in cache_data
                assert 'dimensions' in cache_data
                assert 'asset_expectations' in cache_data
                assert 'updated_at' in cache_data

                # Read back from history (bug #337: consolidated)
                loaded = get_market_conditions()
                assert loaded is not None
                assert loaded['quadrant'] == 'Goldilocks'
        finally:
            for p in (tmp_path, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_structure(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        mock_liq.return_value = _mock_liquidity('Neutral')
        mock_quad.return_value = _mock_quadrant('Reflation')
        mock_risk.return_value = _mock_risk('Elevated')
        mock_pol.return_value = _mock_policy('Restrictive')

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_history = f.name

        try:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', tmp_path), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp_history):
                cache_data = update_market_conditions_cache()

                # Verify all required keys (no verdict)
                assert 'quadrant' in cache_data
                assert 'verdict' not in cache_data
                assert 'verdict_score' not in cache_data
                assert 'dimensions' in cache_data
                assert 'asset_expectations' in cache_data
                assert 'as_of' in cache_data
                assert 'updated_at' in cache_data

                # Verify dimension structure (no mapped_score)
                dims = cache_data['dimensions']
                assert 'liquidity' in dims
                assert 'quadrant' in dims
                assert 'risk' in dims
                assert 'policy' in dims

                assert dims['liquidity']['state'] == 'Neutral'
                assert 'mapped_score' not in dims['liquidity']
                assert dims['quadrant']['state'] == 'Reflation'
                assert dims['risk']['state'] == 'Elevated'
                assert dims['policy']['stance'] == 'Restrictive'
                assert dims['policy']['direction'] == 'Paused'

                # Verify asset expectations
                assert len(cache_data['asset_expectations']) == 4
        finally:
            for p in (tmp_path, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)

    @patch('market_conditions.compute_liquidity')
    def test_cache_update_returns_none_when_no_data(self, mock_liq):
        mock_liq.return_value = None
        with patch('market_conditions.compute_quadrant', return_value=None):
            result = update_market_conditions_cache()
            assert result is None

    def test_get_cache_returns_none_when_missing(self):
        with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', '/nonexistent/path.json'), \
             patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', '/nonexistent/hist.json'):
            assert get_market_conditions() is None


# ============================================================================
# 4. Scenario Tests (Realistic Combinations)
# ============================================================================

class TestRealisticScenarios:
    """End-to-end scenario tests with realistic dimension combinations."""

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_2020_march_crash(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """COVID crash: contracting liquidity, stagflation, stressed risk."""
        mock_liq.return_value = _mock_liquidity('Contracting')
        mock_quad.return_value = _mock_quadrant('Stagflation')
        mock_risk.return_value = _mock_risk('Stressed', score=7)
        mock_pol.return_value = _mock_policy('Accommodative', 'Easing')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Stagflation'
        # S&P 500 expectation should be negative (Stressed override)
        sp = next(e for e in result.asset_expectations if e['asset'] == 'sp500')
        assert sp['direction'] == 'negative'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_2021_recovery(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Post-COVID recovery: expanding liquidity, reflation, calm risk."""
        mock_liq.return_value = _mock_liquidity('Strongly Expanding')
        mock_quad.return_value = _mock_quadrant('Reflation')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Reflation'
        sp = next(e for e in result.asset_expectations if e['asset'] == 'sp500')
        assert sp['direction'] == 'positive'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_2022_tightening(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Rate hike cycle: contracting liquidity, stagflation, elevated risk, restrictive."""
        mock_liq.return_value = _mock_liquidity('Contracting')
        mock_quad.return_value = _mock_quadrant('Stagflation')
        mock_risk.return_value = _mock_risk('Elevated')
        mock_pol.return_value = _mock_policy('Restrictive', 'Tightening')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Stagflation'
        # Stagflation expectations
        sp = next(e for e in result.asset_expectations if e['asset'] == 'sp500')
        assert sp['direction'] == 'negative'
        treas = next(e for e in result.asset_expectations if e['asset'] == 'treasuries')
        assert treas['direction'] == 'negative'  # Stagflation → bonds down too

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_goldilocks_mild(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Goldilocks with neutral everything else."""
        mock_liq.return_value = _mock_liquidity('Neutral')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Neutral')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Goldilocks'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_deflation_risk_accommodative(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Deflation risk but accommodative policy."""
        mock_liq.return_value = _mock_liquidity('Neutral')
        mock_quad.return_value = _mock_quadrant('Deflation Risk')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Deflation Risk'
        treas = next(e for e in result.asset_expectations if e['asset'] == 'treasuries')
        assert treas['direction'] == 'positive'  # Flight to safety in deflation


# ============================================================================
# 5. Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_both_risk_and_policy_missing(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Both risk and policy unavailable → both default to neutral."""
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = None
        mock_pol.return_value = None

        result = compute_market_conditions()
        assert result is not None
        assert result.quadrant == 'Goldilocks'
        assert result.risk_state == 'Normal'
        assert result.policy_stance == 'Neutral'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_as_of_date_passthrough(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """as_of_date argument is forwarded to dimension engines."""
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        compute_market_conditions('2024-06-15')
        mock_liq.assert_called_once_with('2024-06-15')
        mock_quad.assert_called_once_with('2024-06-15')
        mock_risk.assert_called_once_with('2024-06-15')
        mock_pol.assert_called_once_with('2024-06-15')

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_result_dataclass_fields(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Verify all expected fields on the result dataclass."""
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions()
        assert result is not None
        # Quadrant headline
        assert hasattr(result, 'quadrant')
        # Supporting dimensions
        assert hasattr(result, 'liquidity_state')
        assert hasattr(result, 'risk_state')
        assert hasattr(result, 'policy_stance')
        assert hasattr(result, 'policy_direction')
        # Expectations and metadata
        assert hasattr(result, 'asset_expectations')
        assert hasattr(result, 'as_of')
        # No verdict fields
        assert not hasattr(result, 'verdict')
        assert not hasattr(result, 'verdict_score')
        assert not hasattr(result, 'liquidity_mapped')
        assert not hasattr(result, 'quadrant_mapped')
        assert not hasattr(result, 'risk_mapped')
        assert not hasattr(result, 'policy_mapped')


# ============================================================================
# 6. Market Conditions History
# ============================================================================

class TestConditionsHistory:
    """Test the append-only daily history file."""

    def test_load_empty_when_no_file(self):
        with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', '/nonexistent/path.json'):
            assert _load_conditions_history() == {}

    def test_load_empty_on_corrupt_file(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            f.write('not valid json{{{')
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                assert _load_conditions_history() == {}
        finally:
            os.unlink(tmp)

    def test_save_and_load_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                data = {'2025-01-15': {'quadrant': 'Goldilocks'}}
                _save_conditions_history(data)
                loaded = _load_conditions_history()
                assert loaded == data
        finally:
            os.unlink(tmp)

    def test_append_creates_entry(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                cache_data = {
                    'quadrant': 'Goldilocks',
                    'dimensions': {'liquidity': {'state': 'Expanding'}},
                    'asset_expectations': [{'asset': 'sp500', 'direction': 'positive'}],
                    'as_of': '2025-01-15',
                }
                _append_conditions_history(cache_data)
                history = _load_conditions_history()
                assert '2025-01-15' in history
                assert history['2025-01-15']['quadrant'] == 'Goldilocks'
                assert 'verdict' not in history['2025-01-15']
        finally:
            os.unlink(tmp)

    def test_append_overwrites_same_day(self):
        """Running twice on the same day overwrites (idempotent)."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                base = {
                    'quadrant': 'Reflation',
                    'dimensions': {},
                    'asset_expectations': [],
                    'as_of': '2025-01-15',
                }
                _append_conditions_history(base)

                updated = dict(base, quadrant='Goldilocks')
                _append_conditions_history(updated)

                history = _load_conditions_history()
                assert len(history) == 1
                assert history['2025-01-15']['quadrant'] == 'Goldilocks'
        finally:
            os.unlink(tmp)

    def test_append_accumulates_different_days(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                for day in ['2025-01-15', '2025-01-16', '2025-01-17']:
                    _append_conditions_history({
                        'quadrant': 'Reflation',
                        'dimensions': {},
                        'asset_expectations': [],
                        'as_of': day,
                    })
                history = _load_conditions_history()
                assert len(history) == 3
                assert set(history.keys()) == {'2025-01-15', '2025-01-16', '2025-01-17'}
        finally:
            os.unlink(tmp)

    def test_append_skips_missing_as_of(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                _append_conditions_history({'quadrant': 'Goldilocks'})
                history = _load_conditions_history()
                assert len(history) == 0
        finally:
            os.unlink(tmp)

    def test_history_entry_has_expected_keys(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                _append_conditions_history({
                    'quadrant': 'Stagflation',
                    'dimensions': {'liquidity': {'state': 'Contracting'}},
                    'asset_expectations': [{'asset': 'sp500'}],
                    'as_of': '2025-02-01',
                    'updated_at': '2025-02-01T12:00:00Z',
                })
                entry = _load_conditions_history()['2025-02-01']
                assert 'quadrant' in entry
                assert 'dimensions' in entry
                assert 'asset_expectations' in entry
                # verdict should NOT be in history
                assert 'verdict' not in entry
                assert 'verdict_score' not in entry
                # updated_at IS stored (bug #337 — needed for staleness)
                assert 'updated_at' in entry
                # growth_score and inflation_score at top level (bug #337)
                assert 'growth_score' in entry
                assert 'inflation_score' in entry
                assert 'raw_quadrant' in entry
        finally:
            os.unlink(tmp)

    def test_get_conditions_history_public_api(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                _save_conditions_history({'2025-01-15': {'quadrant': 'Goldilocks'}})
                result = get_conditions_history()
                assert '2025-01-15' in result
        finally:
            os.unlink(tmp)

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_update_appends_history(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        """update_market_conditions_cache() should also append to history."""
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_cache = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_history = f.name

        try:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', tmp_cache), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp_history):
                update_market_conditions_cache()
                history = _load_conditions_history()
                assert len(history) == 1
                date_key = list(history.keys())[0]
                assert history[date_key]['quadrant'] == 'Goldilocks'
                assert 'verdict' not in history[date_key]
        finally:
            for p in (tmp_cache, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_update_preserves_existing_history(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        """History from previous days should not be overwritten."""
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_cache = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            json.dump({'2025-01-10': {'quadrant': 'Stagflation'}}, f)
            tmp_history = f.name

        try:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', tmp_cache), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp_history):
                update_market_conditions_cache()
                history = _load_conditions_history()
                assert len(history) == 2
                assert '2025-01-10' in history
                assert history['2025-01-10']['quadrant'] == 'Stagflation'
        finally:
            for p in (tmp_cache, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)


# ============================================================================
# 7. NROU Duplicate Date Handling
# ============================================================================

class TestNROUDeduplication:
    """Test that compute_policy() handles duplicate NROU dates."""

    @patch('market_conditions._load_csv')
    def test_nrou_duplicates_do_not_crash(self, mock_load):
        """NROU series with duplicate dates should not raise ValueError."""
        import pandas as pd
        import numpy as np

        dates_unrate = pd.date_range('2020-01-01', periods=36, freq='MS')
        dates_nrou = pd.date_range('2020-01-01', periods=12, freq='QS')
        # Duplicate one date
        dates_nrou_dup = dates_nrou.append(pd.DatetimeIndex([dates_nrou[0]]))
        nrou_vals = list(np.full(12, 4.0)) + [4.0]

        def load_csv_side_effect(key):
            if key == 'pce_price_index':
                df = pd.DataFrame({
                    'date': dates_unrate,
                    'pce_price_index': np.linspace(110, 120, 36),
                })
                return df
            elif key == 'unemployment_rate':
                df = pd.DataFrame({
                    'date': dates_unrate,
                    'unemployment_rate': np.full(36, 3.5),
                })
                return df
            elif key == 'natural_unemployment_rate':
                df = pd.DataFrame({
                    'date': dates_nrou_dup,
                    'natural_unemployment_rate': nrou_vals,
                })
                return df
            elif key == 'fed_funds_rate':
                df = pd.DataFrame({
                    'date': dates_unrate,
                    'fed_funds_rate': np.full(36, 5.0),
                })
                return df
            return None

        mock_load.side_effect = load_csv_side_effect

        from market_conditions import compute_policy
        # Should not raise ValueError about duplicate labels
        result = compute_policy('2022-12-01')
        # Result may be None due to insufficient data for Taylor Rule,
        # but the important thing is no crash
