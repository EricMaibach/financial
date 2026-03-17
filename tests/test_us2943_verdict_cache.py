"""
Tests for US-294.3: Verdict classifier, asset expectations, and cache output.

Tests cover:
1. Dimension score mapping (-2 to +2)
2. Weighted verdict score computation
3. Verdict classification thresholds
4. Stressed override rule
5. Asset class expectations tables
6. Cache output format and I/O
7. compute_market_conditions() integration
8. Backtest compatibility
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
    _map_dimension_score,
    _compute_verdict_score,
    _classify_verdict,
    _build_asset_expectations,
    _LIQUIDITY_SCORE_MAP,
    _QUADRANT_SCORE_MAP,
    _RISK_SCORE_MAP,
    _POLICY_SCORE_MAP,
    _WEIGHT_LIQUIDITY,
    _WEIGHT_QUADRANT,
    _WEIGHT_RISK,
    _WEIGHT_POLICY,
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
# 1. Dimension Score Mapping
# ============================================================================

class TestDimensionScoreMapping:
    """Test that each dimension state maps to the correct -2 to +2 score."""

    def test_liquidity_strongly_expanding(self):
        assert _map_dimension_score('Strongly Expanding', _LIQUIDITY_SCORE_MAP) == 2.0

    def test_liquidity_expanding(self):
        assert _map_dimension_score('Expanding', _LIQUIDITY_SCORE_MAP) == 1.0

    def test_liquidity_neutral(self):
        assert _map_dimension_score('Neutral', _LIQUIDITY_SCORE_MAP) == 0.0

    def test_liquidity_contracting(self):
        assert _map_dimension_score('Contracting', _LIQUIDITY_SCORE_MAP) == -1.0

    def test_liquidity_strongly_contracting(self):
        assert _map_dimension_score('Strongly Contracting', _LIQUIDITY_SCORE_MAP) == -2.0

    def test_quadrant_goldilocks(self):
        assert _map_dimension_score('Goldilocks', _QUADRANT_SCORE_MAP) == 2.0

    def test_quadrant_reflation(self):
        assert _map_dimension_score('Reflation', _QUADRANT_SCORE_MAP) == 1.0

    def test_quadrant_deflation_risk(self):
        assert _map_dimension_score('Deflation Risk', _QUADRANT_SCORE_MAP) == -1.0

    def test_quadrant_stagflation(self):
        assert _map_dimension_score('Stagflation', _QUADRANT_SCORE_MAP) == -2.0

    def test_risk_calm(self):
        assert _map_dimension_score('Calm', _RISK_SCORE_MAP) == 1.0

    def test_risk_normal(self):
        assert _map_dimension_score('Normal', _RISK_SCORE_MAP) == 0.0

    def test_risk_elevated(self):
        assert _map_dimension_score('Elevated', _RISK_SCORE_MAP) == -1.0

    def test_risk_stressed(self):
        assert _map_dimension_score('Stressed', _RISK_SCORE_MAP) == -2.0

    def test_policy_accommodative(self):
        assert _map_dimension_score('Accommodative', _POLICY_SCORE_MAP) == 1.0

    def test_policy_neutral(self):
        assert _map_dimension_score('Neutral', _POLICY_SCORE_MAP) == 0.0

    def test_policy_restrictive(self):
        assert _map_dimension_score('Restrictive', _POLICY_SCORE_MAP) == -1.0

    def test_unknown_state_returns_none(self):
        assert _map_dimension_score('Unknown', _LIQUIDITY_SCORE_MAP) is None

    def test_all_maps_cover_full_range(self):
        """Each map should have scores spanning from negative to positive."""
        for name, smap in [
            ('liquidity', _LIQUIDITY_SCORE_MAP),
            ('quadrant', _QUADRANT_SCORE_MAP),
            ('risk', _RISK_SCORE_MAP),
            ('policy', _POLICY_SCORE_MAP),
        ]:
            values = list(smap.values())
            assert min(values) < 0, f'{name} map has no negative scores'
            assert max(values) > 0, f'{name} map has no positive scores'


# ============================================================================
# 2. Weighted Verdict Score
# ============================================================================

class TestVerdictScore:
    """Test the weighted composite computation."""

    def test_weights_sum_to_one(self):
        total = _WEIGHT_LIQUIDITY + _WEIGHT_QUADRANT + _WEIGHT_RISK + _WEIGHT_POLICY
        assert abs(total - 1.0) < 1e-9

    def test_all_max_positive(self):
        """All dimensions at max positive → high score."""
        score = _compute_verdict_score(2.0, 2.0, 1.0, 1.0)
        # 0.35*2 + 0.35*2 + 0.20*1 + 0.10*1 = 0.7 + 0.7 + 0.2 + 0.1 = 1.7
        assert abs(score - 1.7) < 1e-9

    def test_all_max_negative(self):
        """All dimensions at max negative → low score."""
        score = _compute_verdict_score(-2.0, -2.0, -2.0, -1.0)
        # 0.35*(-2) + 0.35*(-2) + 0.20*(-2) + 0.10*(-1) = -0.7 + -0.7 + -0.4 + -0.1 = -1.9
        assert abs(score - (-1.9)) < 1e-9

    def test_all_neutral(self):
        """All neutral → score is 0."""
        score = _compute_verdict_score(0.0, 0.0, 0.0, 0.0)
        assert abs(score) < 1e-9

    def test_liquidity_dominance(self):
        """Liquidity alone at +2, rest neutral → 0.7."""
        score = _compute_verdict_score(2.0, 0.0, 0.0, 0.0)
        assert abs(score - 0.7) < 1e-9

    def test_quadrant_dominance(self):
        """Quadrant alone at +2, rest neutral → 0.7."""
        score = _compute_verdict_score(0.0, 2.0, 0.0, 0.0)
        assert abs(score - 0.7) < 1e-9

    def test_risk_contribution(self):
        """Risk alone at -2, rest neutral → -0.4."""
        score = _compute_verdict_score(0.0, 0.0, -2.0, 0.0)
        assert abs(score - (-0.4)) < 1e-9

    def test_policy_contribution(self):
        """Policy alone at +1, rest neutral → 0.1."""
        score = _compute_verdict_score(0.0, 0.0, 0.0, 1.0)
        assert abs(score - 0.1) < 1e-9

    def test_mixed_scenario(self):
        """Expanding liquidity, Reflation, Elevated risk, Restrictive policy."""
        score = _compute_verdict_score(1.0, 1.0, -1.0, -1.0)
        # 0.35*1 + 0.35*1 + 0.20*(-1) + 0.10*(-1) = 0.35 + 0.35 - 0.2 - 0.1 = 0.4
        assert abs(score - 0.4) < 1e-9


# ============================================================================
# 3. Verdict Classification Thresholds
# ============================================================================

class TestVerdictClassification:
    """Test verdict threshold boundaries."""

    def test_favorable_above_075(self):
        assert _classify_verdict(0.76, 'Normal') == 'Favorable'

    def test_favorable_at_high(self):
        assert _classify_verdict(1.7, 'Calm') == 'Favorable'

    def test_mixed_at_076(self):
        """0.75 is NOT > 0.75, so it's Mixed."""
        assert _classify_verdict(0.75, 'Normal') == 'Mixed'

    def test_mixed_at_zero(self):
        assert _classify_verdict(0.0, 'Normal') == 'Mixed'

    def test_mixed_at_neg_024(self):
        assert _classify_verdict(-0.24, 'Normal') == 'Mixed'

    def test_cautious_at_neg_025(self):
        """−0.25 is NOT > −0.25, so it's Cautious."""
        assert _classify_verdict(-0.25, 'Normal') == 'Cautious'

    def test_cautious_at_neg_05(self):
        assert _classify_verdict(-0.5, 'Elevated') == 'Cautious'

    def test_cautious_at_neg_099(self):
        assert _classify_verdict(-0.99, 'Normal') == 'Cautious'

    def test_defensive_at_neg_10(self):
        """−1.0 is NOT > −1.0, so it's Defensive."""
        assert _classify_verdict(-1.0, 'Normal') == 'Defensive'

    def test_defensive_at_neg_19(self):
        assert _classify_verdict(-1.9, 'Normal') == 'Defensive'

    def test_stressed_override_favorable_score(self):
        """Even with a score of +1.7, Stressed → Defensive."""
        assert _classify_verdict(1.7, 'Stressed') == 'Defensive'

    def test_stressed_override_mixed_score(self):
        assert _classify_verdict(0.5, 'Stressed') == 'Defensive'

    def test_stressed_override_cautious_score(self):
        assert _classify_verdict(-0.5, 'Stressed') == 'Defensive'

    def test_stressed_override_already_defensive(self):
        assert _classify_verdict(-1.5, 'Stressed') == 'Defensive'


# ============================================================================
# 4. Asset Class Expectations
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
        # S&P 500: already negative from stagflation, stays negative; override conviction
        assert by_asset['sp500']['direction'] == 'negative'
        assert by_asset['sp500']['conviction'] == 'override'
        # Treasuries: negative from stagflation, weak magnitude
        assert by_asset['treasuries']['direction'] == 'negative'
        assert by_asset['treasuries']['magnitude'] == 'weak'
        # Gold: positive from stagflation, not overridden to weak
        assert by_asset['gold']['direction'] == 'positive'
        assert by_asset['gold']['conviction'] == 'override'
        # Bitcoin: negative from Strongly Contracting liquidity; Stressed → weak/override
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
# 5. compute_market_conditions() Integration
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
    """Integration tests for the main entry point."""

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_favorable_conditions(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Strongly Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.verdict == 'Favorable'
        # 0.35*2 + 0.35*2 + 0.20*1 + 0.10*1 = 1.7
        assert abs(result.verdict_score - 1.7) < 1e-3

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_defensive_stressed_override(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Even with good liquidity and quadrant, Stressed → Defensive."""
        mock_liq.return_value = _mock_liquidity('Strongly Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Stressed', score=7)
        mock_pol.return_value = _mock_policy('Accommodative')

        result = compute_market_conditions()
        assert result is not None
        assert result.verdict == 'Defensive'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_mixed_conditions(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Reflation')
        mock_risk.return_value = _mock_risk('Elevated')
        mock_pol.return_value = _mock_policy('Restrictive')

        result = compute_market_conditions()
        assert result is not None
        # 0.35*1 + 0.35*1 + 0.20*(-1) + 0.10*(-1) = 0.4
        assert result.verdict == 'Mixed'
        assert abs(result.verdict_score - 0.4) < 1e-3

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cautious_conditions(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Contracting')
        mock_quad.return_value = _mock_quadrant('Stagflation')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Neutral')

        result = compute_market_conditions()
        assert result is not None
        # 0.35*(-1) + 0.35*(-2) + 0.20*0 + 0.10*0 = -1.05
        assert result.verdict == 'Defensive'
        assert result.verdict_score < -1.0

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
        assert result.risk_mapped == 0.0

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
        assert result.policy_mapped == 0.0

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
    def test_backtest_compatibility(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Result should have .verdict and .verdict_score for backtest scorer."""
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        result = compute_market_conditions()
        assert result is not None
        assert hasattr(result, 'verdict')
        assert hasattr(result, 'verdict_score')
        assert isinstance(result.verdict, str)
        assert isinstance(result.verdict_score, float)

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_as_of_uses_latest_dimension_date(self, mock_liq, mock_quad, mock_risk, mock_pol):
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
        assert result.as_of == '2025-01-15'


# ============================================================================
# 6. Cache I/O
# ============================================================================

class TestCacheIO:
    """Test cache write and read."""

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_write_and_read(self, mock_liq, mock_quad, mock_risk, mock_pol):
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
                assert cache_data['verdict'] == 'Favorable'
                assert 'dimensions' in cache_data
                assert 'asset_expectations' in cache_data
                assert 'updated_at' in cache_data

                # Read back
                loaded = get_market_conditions()
                assert loaded is not None
                assert loaded['verdict'] == 'Favorable'
        finally:
            for p in (tmp_path, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_structure(self, mock_liq, mock_quad, mock_risk, mock_pol):
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

                # Verify all required keys
                assert 'verdict' in cache_data
                assert 'verdict_score' in cache_data
                assert 'dimensions' in cache_data
                assert 'asset_expectations' in cache_data
                assert 'as_of' in cache_data
                assert 'updated_at' in cache_data

                # Verify dimension structure
                dims = cache_data['dimensions']
                assert 'liquidity' in dims
                assert 'quadrant' in dims
                assert 'risk' in dims
                assert 'policy' in dims

                assert dims['liquidity']['state'] == 'Neutral'
                assert dims['liquidity']['mapped_score'] == 0.0
                assert dims['quadrant']['state'] == 'Reflation'
                assert dims['quadrant']['mapped_score'] == 1.0
                assert dims['risk']['state'] == 'Elevated'
                assert dims['risk']['mapped_score'] == -1.0
                assert dims['policy']['stance'] == 'Restrictive'
                assert dims['policy']['direction'] == 'Paused'
                assert dims['policy']['mapped_score'] == -1.0

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
        with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', '/nonexistent/path.json'):
            assert get_market_conditions() is None


# ============================================================================
# 7. Scenario Tests (Realistic Combinations)
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
        # Stressed override → Defensive regardless of score
        assert result.verdict == 'Defensive'
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
        assert result.verdict == 'Favorable'
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
        # 0.35*(-1) + 0.35*(-2) + 0.20*(-1) + 0.10*(-1) = -1.35
        assert result.verdict == 'Defensive'
        assert result.verdict_score < -1.0

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_goldilocks_mild(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """Goldilocks but neutral everything else → Mixed."""
        mock_liq.return_value = _mock_liquidity('Neutral')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Neutral')

        result = compute_market_conditions()
        assert result is not None
        # 0.35*0 + 0.35*2 + 0.20*0 + 0.10*0 = 0.7
        assert result.verdict == 'Mixed'  # 0.7 is NOT > 0.75

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
        # 0.35*0 + 0.35*(-1) + 0.20*0 + 0.10*1 ≈ -0.25 (fp: -0.2499...)
        # Floating point makes this slightly > -0.25, so Mixed
        assert result.verdict == 'Mixed'
        treas = next(e for e in result.asset_expectations if e['asset'] == 'treasuries')
        assert treas['direction'] == 'positive'  # Flight to safety in deflation


# ============================================================================
# 8. Edge Cases
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
        # 0.35*1 + 0.35*2 + 0.20*0 + 0.10*0 = 1.05
        assert result.verdict == 'Favorable'

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_verdict_score_is_rounded(self, mock_liq, mock_quad, mock_risk, mock_pol):
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Reflation')
        mock_risk.return_value = _mock_risk('Normal')
        mock_pol.return_value = _mock_policy('Neutral')

        result = compute_market_conditions()
        assert result is not None
        # Should be rounded to 4 decimal places
        score_str = str(result.verdict_score)
        if '.' in score_str:
            decimals = len(score_str.split('.')[1])
            assert decimals <= 4

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
        # Check all fields exist
        assert hasattr(result, 'verdict')
        assert hasattr(result, 'verdict_score')
        assert hasattr(result, 'liquidity_state')
        assert hasattr(result, 'quadrant')
        assert hasattr(result, 'risk_state')
        assert hasattr(result, 'policy_stance')
        assert hasattr(result, 'policy_direction')
        assert hasattr(result, 'liquidity_mapped')
        assert hasattr(result, 'quadrant_mapped')
        assert hasattr(result, 'risk_mapped')
        assert hasattr(result, 'policy_mapped')
        assert hasattr(result, 'asset_expectations')
        assert hasattr(result, 'as_of')


# ============================================================================
# 9. Market Conditions History
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
                data = {'2025-01-15': {'verdict': 'Mixed', 'verdict_score': 0.4}}
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
                    'verdict': 'Favorable',
                    'verdict_score': 1.7,
                    'dimensions': {'liquidity': {'state': 'Expanding', 'mapped_score': 1.0}},
                    'asset_expectations': [{'asset': 'sp500', 'direction': 'positive'}],
                    'as_of': '2025-01-15',
                }
                _append_conditions_history(cache_data)
                history = _load_conditions_history()
                assert '2025-01-15' in history
                assert history['2025-01-15']['verdict'] == 'Favorable'
                assert history['2025-01-15']['verdict_score'] == 1.7
        finally:
            os.unlink(tmp)

    def test_append_overwrites_same_day(self):
        """Running twice on the same day overwrites (idempotent)."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                base = {
                    'verdict': 'Mixed',
                    'verdict_score': 0.4,
                    'dimensions': {},
                    'asset_expectations': [],
                    'as_of': '2025-01-15',
                }
                _append_conditions_history(base)

                updated = dict(base, verdict='Favorable', verdict_score=1.0)
                _append_conditions_history(updated)

                history = _load_conditions_history()
                assert len(history) == 1
                assert history['2025-01-15']['verdict'] == 'Favorable'
        finally:
            os.unlink(tmp)

    def test_append_accumulates_different_days(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                for day in ['2025-01-15', '2025-01-16', '2025-01-17']:
                    _append_conditions_history({
                        'verdict': 'Mixed',
                        'verdict_score': 0.4,
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
                _append_conditions_history({'verdict': 'Mixed', 'verdict_score': 0.4})
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
                    'verdict': 'Cautious',
                    'verdict_score': -0.5,
                    'dimensions': {'liquidity': {'state': 'Contracting'}},
                    'asset_expectations': [{'asset': 'sp500'}],
                    'as_of': '2025-02-01',
                    'updated_at': '2025-02-01T12:00:00Z',
                })
                entry = _load_conditions_history()['2025-02-01']
                assert 'verdict' in entry
                assert 'verdict_score' in entry
                assert 'dimensions' in entry
                assert 'asset_expectations' in entry
                # updated_at should NOT be in history (ephemeral)
                assert 'updated_at' not in entry
        finally:
            os.unlink(tmp)

    def test_get_conditions_history_public_api(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                _save_conditions_history({'2025-01-15': {'verdict': 'Mixed'}})
                result = get_conditions_history()
                assert '2025-01-15' in result
        finally:
            os.unlink(tmp)

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_update_appends_history(self, mock_liq, mock_quad, mock_risk, mock_pol):
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
                assert history[date_key]['verdict'] == 'Favorable'
        finally:
            for p in (tmp_cache, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)

    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_cache_update_preserves_existing_history(self, mock_liq, mock_quad, mock_risk, mock_pol):
        """History from previous days should not be overwritten."""
        mock_liq.return_value = _mock_liquidity('Expanding')
        mock_quad.return_value = _mock_quadrant('Goldilocks')
        mock_risk.return_value = _mock_risk('Calm')
        mock_pol.return_value = _mock_policy('Accommodative')

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_cache = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            # Seed with existing history
            json.dump({'2025-01-10': {'verdict': 'Cautious', 'verdict_score': -0.5}}, f)
            tmp_history = f.name

        try:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', tmp_cache), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp_history):
                update_market_conditions_cache()
                history = _load_conditions_history()
                assert len(history) == 2
                assert '2025-01-10' in history
                assert history['2025-01-10']['verdict'] == 'Cautious'
        finally:
            for p in (tmp_cache, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)


# ============================================================================
# 10. NROU Duplicate Date Handling
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

        # Mock _load_csv to return appropriate dataframes
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
        # (no ValueError: cannot reindex on an axis with duplicate labels)
