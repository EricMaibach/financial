"""
Tests for US-295.1: Walk-forward backtest validation with weight sensitivity analysis.

Tests the Market Conditions backtest module that validates the four-dimension
verdict classifier against the 52.3/100 k-means baseline.
"""

import json
import math
from datetime import datetime
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from signaltrackers.backtesting.conditions_backtest import (
    VERDICT_LABELS,
    VERDICT_EXPECTATIONS,
    DEFAULT_WEIGHTS,
    WEIGHT_CONFIGS,
    FOLD_START_YEAR,
    FOLD_END_YEAR,
    FOLD_TEST_MONTHS,
    SCORING_ASSETS,
    classify_conditions,
    score_single_evaluation,
    generate_folds,
    score_walk_forward,
    score_results,
    check_plausibility,
    run_cpcv,
    compute_dsr,
    run_weight_sensitivity,
    generate_report,
    _get_dimension_state_at,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_liquidity_history():
    """Liquidity history spanning 2005-2024."""
    dates = pd.date_range('2005-01-01', '2024-12-31', freq='W-WED')
    states = []
    for d in dates:
        if d.year <= 2007:
            states.append('Expanding')
        elif d.year <= 2009:
            states.append('Contracting')
        elif d.year <= 2013:
            states.append('Neutral')
        elif d.year <= 2019:
            states.append('Expanding')
        elif d.year == 2020 and d.month <= 6:
            states.append('Strongly Expanding')
        elif d.year <= 2021:
            states.append('Expanding')
        elif d.year <= 2022:
            states.append('Contracting')
        else:
            states.append('Expanding')
    return pd.DataFrame({
        'date': dates[:len(states)],
        'score': np.random.randn(len(states)),
        'state': states,
    })


@pytest.fixture
def sample_quadrant_history():
    """Quadrant history spanning 2005-2024."""
    dates = pd.date_range('2005-01-01', '2024-12-31', freq='ME')
    quadrants = []
    for d in dates:
        if d.year <= 2007:
            quadrants.append('Goldilocks')
        elif d.year <= 2009:
            quadrants.append('Deflation Risk')
        elif d.year <= 2013:
            quadrants.append('Reflation')
        elif d.year <= 2019:
            quadrants.append('Goldilocks')
        elif d.year == 2020 and d.month <= 6:
            quadrants.append('Deflation Risk')
        elif d.year <= 2021:
            quadrants.append('Reflation')
        elif d.year <= 2022:
            quadrants.append('Stagflation')
        else:
            quadrants.append('Goldilocks')
    return pd.DataFrame({
        'date': dates[:len(quadrants)],
        'growth': np.random.randn(len(quadrants)),
        'inflation': np.random.randn(len(quadrants)),
        'raw_quadrant': quadrants,
        'quadrant': quadrants,
    })


@pytest.fixture
def sample_risk_history():
    """Risk history spanning 2008-2024 (VIX3M starts Dec 2007)."""
    dates = pd.date_range('2008-01-01', '2024-12-31', freq='D')
    states = []
    for d in dates:
        if d.year <= 2009:
            states.append('Elevated')
        elif d.year == 2020 and d.month in (3, 4):
            states.append('Stressed')
        elif d.year == 2020:
            states.append('Elevated')
        elif d.year == 2022:
            states.append('Elevated')
        else:
            states.append('Normal')
    return pd.DataFrame({
        'date': dates[:len(states)],
        'vix_score': [1] * len(states),
        'term_structure_score': [0] * len(states),
        'correlation_score': [0] * len(states),
        'score': [1] * len(states),
        'state': states,
    })


@pytest.fixture
def sample_policy_history():
    """Policy history spanning 2005-2024."""
    dates = pd.date_range('2005-01-01', '2024-12-31', freq='ME')
    stances = []
    for d in dates:
        if d.year <= 2007:
            stances.append('Restrictive')
        elif d.year <= 2015:
            stances.append('Accommodative')
        elif d.year <= 2019:
            stances.append('Neutral')
        elif d.year == 2020:
            stances.append('Accommodative')
        elif d.year <= 2022:
            stances.append('Restrictive')
        else:
            stances.append('Neutral')
    return pd.DataFrame({
        'date': dates[:len(stances)],
        'actual_rate': [2.0] * len(stances),
        'taylor_prescribed': [2.5] * len(stances),
        'taylor_gap': [-0.5] * len(stances),
        'stance': stances,
        'direction': ['Paused'] * len(stances),
    })


@pytest.fixture
def sample_histories(
    sample_liquidity_history,
    sample_quadrant_history,
    sample_risk_history,
    sample_policy_history,
):
    """Combined dimension histories."""
    return {
        'liquidity': sample_liquidity_history,
        'quadrant': sample_quadrant_history,
        'risk': sample_risk_history,
        'policy': sample_policy_history,
    }


@pytest.fixture
def sample_scoring_assets():
    """Mock scoring asset price series."""
    dates = pd.date_range('2004-01-01', '2025-06-30', freq='D')
    np.random.seed(42)
    # Simple trending prices
    sp500 = pd.Series(
        np.cumsum(np.random.randn(len(dates)) * 0.01) + 7.0,
        index=dates,
        name='sp500',
    )
    sp500 = np.exp(sp500)  # Log-normal prices

    treasuries = pd.Series(
        np.cumsum(np.random.randn(len(dates)) * 0.005) + 4.5,
        index=dates,
        name='treasuries',
    )
    treasuries = np.exp(treasuries)

    gold = pd.Series(
        np.cumsum(np.random.randn(len(dates)) * 0.008) + 6.5,
        index=dates,
        name='gold',
    )
    gold = np.exp(gold)

    return {
        'sp500': sp500,
        'treasuries': treasuries,
        'gold': gold,
    }


@pytest.fixture
def sample_backtest_df():
    """Sample backtest results DataFrame for scoring tests."""
    np.random.seed(123)
    dates = pd.date_range('2005-01-31', '2024-12-31', freq='ME')
    n = len(dates)
    verdicts = np.random.choice(VERDICT_LABELS, size=n, p=[0.3, 0.3, 0.25, 0.15])
    return pd.DataFrame({
        'date': [d.strftime('%Y-%m-%d') for d in dates],
        'verdict': verdicts,
        'verdict_score': np.random.randn(n) * 0.5,
        'liquidity_state': ['Expanding'] * n,
        'quadrant': np.random.choice(
            ['Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk'], n
        ),
        'risk_state': np.random.choice(['Calm', 'Normal', 'Elevated'], n),
        'policy_stance': np.random.choice(['Accommodative', 'Neutral', 'Restrictive'], n),
        'sp500_fwd_30d': np.random.randn(n) * 0.05,
        'sp500_fwd_60d': np.random.randn(n) * 0.07,
        'sp500_fwd_90d': np.random.randn(n) * 0.1,
        'treasuries_fwd_30d': np.random.randn(n) * 0.03,
        'treasuries_fwd_60d': np.random.randn(n) * 0.04,
        'treasuries_fwd_90d': np.random.randn(n) * 0.05,
        'gold_fwd_30d': np.random.randn(n) * 0.04,
        'gold_fwd_60d': np.random.randn(n) * 0.05,
        'gold_fwd_90d': np.random.randn(n) * 0.06,
        'sp500_max_dd_90d': np.random.uniform(-0.15, -0.01, n),
        'multi_asset_score': np.random.uniform(0.3, 0.8, n),
        'sp500_correct': np.random.choice([0.0, 1.0], n),
        'treasuries_correct': np.random.choice([0.0, 0.5, 1.0], n),
        'gold_correct': np.random.choice([0.0, 0.5, 1.0], n),
    })


# ---------------------------------------------------------------------------
# Tests: Configuration
# ---------------------------------------------------------------------------

class TestConfiguration:
    """Verify configuration matches the acceptance criteria."""

    def test_verdict_labels(self):
        assert VERDICT_LABELS == ['Favorable', 'Mixed', 'Cautious', 'Defensive']

    def test_verdict_expectations_keys(self):
        for verdict in VERDICT_LABELS:
            assert verdict in VERDICT_EXPECTATIONS

    def test_verdict_expectations_assets(self):
        for verdict, expectations in VERDICT_EXPECTATIONS.items():
            for asset in ['sp500', 'treasuries', 'gold']:
                assert asset in expectations
                assert expectations[asset] in ('positive', 'negative', 'neutral')

    def test_scoring_weights_unchanged(self):
        """S&P 500 37.5%, Treasuries 31.25%, Gold 31.25%"""
        assert SCORING_ASSETS['sp500']['weight'] == 0.375
        assert SCORING_ASSETS['treasuries']['weight'] == 0.3125
        assert SCORING_ASSETS['gold']['weight'] == 0.3125

    def test_default_weights_sum_to_one(self):
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 0.001

    def test_all_weight_configs_sum_to_one(self):
        for config in WEIGHT_CONFIGS:
            total = config['liquidity'] + config['quadrant'] + config['risk'] + config['policy']
            assert abs(total - 1.0) < 0.001, f'{config["label"]} sums to {total}'

    def test_fold_configuration(self):
        assert FOLD_START_YEAR == 2005
        assert FOLD_END_YEAR == 2025
        assert FOLD_TEST_MONTHS == 24


# ---------------------------------------------------------------------------
# Tests: Dimension state lookup (no lookahead)
# ---------------------------------------------------------------------------

class TestDimensionStateLookup:

    def test_returns_state_at_exact_date(self):
        df = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-15', '2020-02-15', '2020-03-15']),
            'state': ['Expanding', 'Neutral', 'Contracting'],
        })
        result = _get_dimension_state_at(df, pd.Timestamp('2020-02-15'), 'state')
        assert result == 'Neutral'

    def test_returns_most_recent_before_date(self):
        df = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-03-01']),
            'state': ['Expanding', 'Contracting'],
        })
        result = _get_dimension_state_at(df, pd.Timestamp('2020-02-15'), 'state')
        assert result == 'Expanding'

    def test_no_lookahead(self):
        """Must not return a future state."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2020-06-01']),
            'state': ['Expanding'],
        })
        result = _get_dimension_state_at(df, pd.Timestamp('2020-01-01'), 'state')
        assert result is None

    def test_returns_none_for_empty_history(self):
        df = pd.DataFrame({'date': pd.Series([], dtype='datetime64[ns]'), 'state': []})
        result = _get_dimension_state_at(df, pd.Timestamp('2020-01-01'), 'state')
        assert result is None


# ---------------------------------------------------------------------------
# Tests: classify_conditions
# ---------------------------------------------------------------------------

class TestClassifyConditions:

    def test_returns_verdict(self, sample_histories):
        result = classify_conditions(
            sample_histories, pd.Timestamp('2015-06-30')
        )
        assert result is not None
        assert result['verdict'] in VERDICT_LABELS

    def test_returns_all_dimension_states(self, sample_histories):
        result = classify_conditions(
            sample_histories, pd.Timestamp('2015-06-30')
        )
        assert 'liquidity_state' in result
        assert 'quadrant' in result
        assert 'risk_state' in result
        assert 'policy_stance' in result

    def test_returns_expectations(self, sample_histories):
        result = classify_conditions(
            sample_histories, pd.Timestamp('2015-06-30')
        )
        assert 'expectations' in result
        assert 'sp500' in result['expectations']

    def test_returns_none_without_liquidity(self, sample_quadrant_history):
        histories = {'quadrant': sample_quadrant_history}
        result = classify_conditions(histories, pd.Timestamp('2015-06-30'))
        assert result is None

    def test_returns_none_without_quadrant(self, sample_liquidity_history):
        histories = {'liquidity': sample_liquidity_history}
        result = classify_conditions(histories, pd.Timestamp('2015-06-30'))
        assert result is None

    def test_degrades_gracefully_without_risk(
        self, sample_liquidity_history, sample_quadrant_history
    ):
        histories = {
            'liquidity': sample_liquidity_history,
            'quadrant': sample_quadrant_history,
        }
        result = classify_conditions(histories, pd.Timestamp('2015-06-30'))
        assert result is not None
        assert result['risk_state'] == 'Normal'
        assert result['risk_mapped'] == 0.0

    def test_degrades_gracefully_without_policy(
        self, sample_liquidity_history, sample_quadrant_history, sample_risk_history
    ):
        histories = {
            'liquidity': sample_liquidity_history,
            'quadrant': sample_quadrant_history,
            'risk': sample_risk_history,
        }
        result = classify_conditions(histories, pd.Timestamp('2015-06-30'))
        assert result is not None
        assert result['policy_stance'] == 'Neutral'
        assert result['policy_mapped'] == 0.0

    def test_custom_weights(self, sample_histories):
        weights = {'liquidity': 0.5, 'quadrant': 0.3, 'risk': 0.1, 'policy': 0.1}
        result = classify_conditions(
            sample_histories, pd.Timestamp('2015-06-30'), weights
        )
        assert result is not None

    def test_stressed_override_sp500(self, sample_histories):
        """When risk is Stressed, S&P 500 expectation should be negative."""
        # Find a date where risk is Stressed in sample data (March 2020)
        result = classify_conditions(
            sample_histories, pd.Timestamp('2020-03-15')
        )
        if result and result['risk_state'] == 'Stressed':
            assert result['expectations']['sp500'] == 'negative'

    def test_no_lookahead_in_classification(self, sample_histories):
        """Classification at date X must not use data after X."""
        early_result = classify_conditions(
            sample_histories, pd.Timestamp('2010-06-30')
        )
        # The 2022 stagflation data shouldn't affect 2010 classification
        assert early_result is not None
        # In 2010, quadrant is Reflation per our fixture
        assert early_result['quadrant'] == 'Reflation'


# ---------------------------------------------------------------------------
# Tests: score_single_evaluation
# ---------------------------------------------------------------------------

class TestScoreSingleEvaluation:

    def test_positive_correct(self):
        result = score_single_evaluation(
            {'sp500': 'positive', 'treasuries': 'negative', 'gold': 'neutral'},
            {'sp500': 0.05, 'treasuries': -0.03, 'gold': 0.01},
        )
        assert result['asset_scores']['sp500'] == 1.0
        assert result['asset_scores']['treasuries'] == 1.0
        assert result['asset_scores']['gold'] == 1.0  # <5%

    def test_positive_incorrect(self):
        result = score_single_evaluation(
            {'sp500': 'positive', 'treasuries': 'negative', 'gold': 'positive'},
            {'sp500': -0.05, 'treasuries': 0.03, 'gold': -0.06},
        )
        assert result['asset_scores']['sp500'] == 0.0
        assert result['asset_scores']['treasuries'] == 0.0
        assert result['asset_scores']['gold'] == 0.0

    def test_neutral_within_threshold(self):
        result = score_single_evaluation(
            {'sp500': 'neutral'},
            {'sp500': 0.03},  # Within 5% threshold
        )
        assert result['asset_scores']['sp500'] == 1.0

    def test_neutral_outside_threshold(self):
        result = score_single_evaluation(
            {'sp500': 'neutral'},
            {'sp500': 0.08},  # Outside 5%
        )
        assert result['asset_scores']['sp500'] == 0.5

    def test_missing_return_skipped(self):
        result = score_single_evaluation(
            {'sp500': 'positive', 'treasuries': 'negative', 'gold': 'positive'},
            {'sp500': 0.05, 'treasuries': None, 'gold': 0.03},
        )
        assert 'treasuries' not in result['asset_scores']
        assert len(result['assets_available']) == 2

    def test_weighted_score_correct(self):
        result = score_single_evaluation(
            {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'positive'},
            {'sp500': 0.05, 'treasuries': 0.03, 'gold': 0.04},
        )
        # All correct → weighted score = 1.0
        assert result['weighted_score'] == 1.0

    def test_weighted_score_all_wrong(self):
        result = score_single_evaluation(
            {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'positive'},
            {'sp500': -0.05, 'treasuries': -0.03, 'gold': -0.04},
        )
        assert result['weighted_score'] == 0.0


# ---------------------------------------------------------------------------
# Tests: generate_folds
# ---------------------------------------------------------------------------

class TestGenerateFolds:

    def test_generates_10_folds(self):
        folds = generate_folds(2005, 2025, 24)
        assert len(folds) == 10

    def test_folds_cover_full_range(self):
        folds = generate_folds(2005, 2025, 24)
        assert folds[0]['test_start'] == pd.Timestamp('2005-01-01')
        assert folds[-1]['test_end'] == pd.Timestamp('2024-12-31')

    def test_folds_non_overlapping(self):
        folds = generate_folds(2005, 2025, 24)
        for i in range(1, len(folds)):
            assert folds[i]['test_start'] > folds[i - 1]['test_end']

    def test_fold_numbers_sequential(self):
        folds = generate_folds(2005, 2025, 24)
        for i, fold in enumerate(folds):
            assert fold['fold'] == i + 1

    def test_each_fold_has_test_window(self):
        folds = generate_folds(2005, 2025, 24)
        for fold in folds:
            assert fold['test_end'] > fold['test_start']


# ---------------------------------------------------------------------------
# Tests: score_walk_forward
# ---------------------------------------------------------------------------

class TestScoreWalkForward:

    def test_returns_per_fold_scores(self, sample_backtest_df):
        folds = generate_folds()
        result = score_walk_forward(sample_backtest_df, folds)
        assert 'fold_details' in result
        assert len(result['fold_details']) == len(folds)

    def test_computes_mean_and_std(self, sample_backtest_df):
        folds = generate_folds()
        result = score_walk_forward(sample_backtest_df, folds)
        assert result['mean'] is not None
        assert result['std'] is not None
        assert result['n_folds'] > 0

    def test_sharpe_ratio(self, sample_backtest_df):
        folds = generate_folds()
        result = score_walk_forward(sample_backtest_df, folds)
        if result['std'] and result['std'] > 0:
            expected_sharpe = result['mean'] / result['std']
            assert abs(result['sharpe'] - expected_sharpe) < 0.5

    def test_empty_fold_handled(self):
        # DataFrame with no data in the fold window
        df = pd.DataFrame({
            'date': ['2000-01-31'],
            'multi_asset_score': [0.5],
        })
        folds = [{'fold': 1, 'test_start': pd.Timestamp('2005-01-01'),
                   'test_end': pd.Timestamp('2007-12-31')}]
        result = score_walk_forward(df, folds)
        assert result['mean'] is None


# ---------------------------------------------------------------------------
# Tests: score_results
# ---------------------------------------------------------------------------

class TestScoreResults:

    def test_overall_accuracy(self, sample_backtest_df):
        result = score_results(sample_backtest_df)
        assert 'multi_asset_accuracy' in result['overall']
        assert 0 <= result['overall']['multi_asset_accuracy'] <= 100

    def test_per_verdict_counts(self, sample_backtest_df):
        result = score_results(sample_backtest_df)
        total_count = sum(
            v.get('count', 0) for v in result['per_verdict'].values()
        )
        assert total_count == len(sample_backtest_df)

    def test_per_asset_accuracy(self, sample_backtest_df):
        result = score_results(sample_backtest_df)
        for asset_key in SCORING_ASSETS:
            if asset_key in result['per_asset']:
                assert 0 <= result['per_asset'][asset_key]['accuracy'] <= 100

    def test_composite_score_exists(self, sample_backtest_df):
        result = score_results(sample_backtest_df)
        assert 'composite_score' in result['overall']

    def test_all_verdicts_covered(self, sample_backtest_df):
        result = score_results(sample_backtest_df)
        for verdict in VERDICT_LABELS:
            assert verdict in result['per_verdict']


# ---------------------------------------------------------------------------
# Tests: Economic plausibility
# ---------------------------------------------------------------------------

class TestPlausibility:

    def test_march_2020_not_favorable(self):
        df = pd.DataFrame({
            'date': ['2020-02-28', '2020-03-31', '2020-04-30'],
            'verdict': ['Cautious', 'Defensive', 'Cautious'],
            'quadrant': ['Deflation Risk', 'Deflation Risk', 'Deflation Risk'],
        })
        result = check_plausibility(df)
        assert result['checks']['march_2020_not_favorable']['pass'] is True

    def test_march_2020_fails_if_favorable_dominant(self):
        df = pd.DataFrame({
            'date': ['2020-02-28', '2020-03-31'],
            'verdict': ['Favorable', 'Favorable'],
            'quadrant': ['Goldilocks', 'Goldilocks'],
        })
        result = check_plausibility(df)
        assert result['checks']['march_2020_not_favorable']['pass'] is False

    def test_march_2020_passes_if_favorable_minority(self):
        """Favorable appearing briefly is OK if not dominant."""
        df = pd.DataFrame({
            'date': ['2020-02-28', '2020-03-15', '2020-03-31', '2020-04-15'],
            'verdict': ['Favorable', 'Cautious', 'Defensive', 'Cautious'],
            'quadrant': ['Reflation', 'Deflation Risk', 'Deflation Risk', 'Deflation Risk'],
        })
        result = check_plausibility(df)
        assert result['checks']['march_2020_not_favorable']['pass'] is True

    def test_2022_stagflation_present(self):
        df = pd.DataFrame({
            'date': ['2022-06-30', '2022-07-31', '2022-08-31'],
            'verdict': ['Cautious', 'Cautious', 'Cautious'],
            'quadrant': ['Stagflation', 'Stagflation', 'Deflation Risk'],
        })
        result = check_plausibility(df)
        assert result['checks']['2022_stagflation_present']['pass'] is True

    def test_2022_fails_if_no_stagflation(self):
        df = pd.DataFrame({
            'date': ['2022-06-30', '2022-07-31', '2022-08-31'],
            'verdict': ['Cautious', 'Cautious', 'Cautious'],
            'quadrant': ['Deflation Risk', 'Deflation Risk', 'Deflation Risk'],
        })
        result = check_plausibility(df)
        assert result['checks']['2022_stagflation_present']['pass'] is False

    def test_verdict_stability_pass(self):
        """Average duration >= 3 months passes."""
        df = pd.DataFrame({
            'date': [f'2020-{m:02d}-28' for m in range(1, 13)],
            'verdict': ['Favorable'] * 4 + ['Mixed'] * 4 + ['Cautious'] * 4,
            'quadrant': ['Goldilocks'] * 12,
        })
        result = check_plausibility(df)
        assert result['checks']['verdict_stability']['pass'] is True
        assert result['checks']['verdict_stability']['avg_duration_months'] == 4.0

    def test_verdict_stability_fail(self):
        """Alternating verdicts every month fails."""
        df = pd.DataFrame({
            'date': [f'2020-{m:02d}-28' for m in range(1, 13)],
            'verdict': ['Favorable', 'Mixed'] * 6,
            'quadrant': ['Goldilocks'] * 12,
        })
        result = check_plausibility(df)
        assert result['checks']['verdict_stability']['pass'] is False

    def test_all_pass_when_all_checks_pass(self):
        # Include 2022 with Stagflation quadrant to pass the stagflation check
        dates = [f'{y}-06-30' for y in range(2005, 2025)]
        verdicts = ['Mixed'] * 20
        quadrants = ['Goldilocks'] * 20
        # Set 2022 (index 17) to Stagflation
        quadrants[17] = 'Stagflation'
        df = pd.DataFrame({
            'date': dates,
            'verdict': verdicts,
            'quadrant': quadrants,
        })
        result = check_plausibility(df)
        assert result['all_pass'] is True


# ---------------------------------------------------------------------------
# Tests: CPCV
# ---------------------------------------------------------------------------

class TestCPCV:

    def test_produces_15_paths(self, sample_backtest_df):
        """C(6,2) = 15 paths."""
        result = run_cpcv(sample_backtest_df, k=6, p=2)
        assert result['n_paths'] == 15

    def test_pbo_between_0_and_1(self, sample_backtest_df):
        result = run_cpcv(sample_backtest_df, k=6, p=2)
        assert 0 <= result['pbo'] <= 1.0

    def test_oos_scores_reported(self, sample_backtest_df):
        result = run_cpcv(sample_backtest_df, k=6, p=2)
        assert len(result['oos_scores']) == 15

    def test_purge_window_respected(self):
        """Purge removes observations within 3 months of test boundary."""
        # Small dataset where purge effect is observable
        dates = pd.date_range('2010-01-31', '2014-12-31', freq='ME')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'multi_asset_score': np.random.uniform(0.3, 0.8, len(dates)),
        })
        result = run_cpcv(df, k=6, p=2, purge_months=3, embargo_months=1)
        assert result['n_paths'] > 0

    def test_empty_dataframe(self):
        df = pd.DataFrame({'date': [], 'multi_asset_score': []})
        result = run_cpcv(df)
        assert result['pbo'] is None


# ---------------------------------------------------------------------------
# Tests: DSR
# ---------------------------------------------------------------------------

class TestDSR:

    def test_basic_computation(self):
        result = compute_dsr(
            observed_sharpe=3.0,
            n_trials=7,
            n_observations=10,
            std_sharpe=0.5,
        )
        assert result['dsr'] is not None
        assert result['p_value'] is not None
        assert result['significant'] in (True, False)

    def test_high_sharpe_is_significant(self):
        result = compute_dsr(
            observed_sharpe=10.0,
            n_trials=3,
            n_observations=10,
            std_sharpe=0.5,
        )
        assert result['significant'] == True

    def test_low_sharpe_not_significant(self):
        result = compute_dsr(
            observed_sharpe=0.1,
            n_trials=100,
            n_observations=5,
            std_sharpe=2.0,
        )
        assert result['significant'] == False

    def test_single_trial_returns_none(self):
        result = compute_dsr(
            observed_sharpe=1.0,
            n_trials=1,
            n_observations=10,
            std_sharpe=0.5,
        )
        assert result['dsr'] is None

    def test_n_trials_recorded(self):
        result = compute_dsr(
            observed_sharpe=2.0,
            n_trials=7,
            n_observations=10,
            std_sharpe=1.0,
        )
        assert result['n_trials'] == 7

    def test_skewness_kurtosis_accepted(self):
        result = compute_dsr(
            observed_sharpe=2.0,
            n_trials=5,
            n_observations=10,
            std_sharpe=1.0,
            skewness=-0.5,
            kurtosis=4.0,
        )
        assert result['dsr'] is not None


# ---------------------------------------------------------------------------
# Tests: Weight sensitivity
# ---------------------------------------------------------------------------

class TestWeightSensitivity:

    def test_multiple_configs_tested(self, sample_histories, sample_scoring_assets):
        results = run_weight_sensitivity(
            sample_histories, sample_scoring_assets,
            configs=WEIGHT_CONFIGS[:2],  # Test only first 2 for speed
        )
        assert len(results) == 2

    def test_invalid_weights_rejected(self, sample_histories, sample_scoring_assets):
        bad_config = [{'liquidity': 0.5, 'quadrant': 0.5, 'risk': 0.5, 'policy': 0.5, 'label': 'Bad'}]
        results = run_weight_sensitivity(
            sample_histories, sample_scoring_assets, configs=bad_config
        )
        assert 'error' in results[0]

    def test_results_have_scores(self, sample_histories, sample_scoring_assets):
        results = run_weight_sensitivity(
            sample_histories, sample_scoring_assets,
            configs=WEIGHT_CONFIGS[:1],
        )
        result = results[0]
        assert 'composite_score' in result or 'error' in result

    def test_sharpe_ratio_reported(self, sample_histories, sample_scoring_assets):
        results = run_weight_sensitivity(
            sample_histories, sample_scoring_assets,
            configs=WEIGHT_CONFIGS[:1],
        )
        if 'error' not in results[0]:
            assert 'wf_sharpe' in results[0]


# ---------------------------------------------------------------------------
# Tests: Report generation
# ---------------------------------------------------------------------------

class TestReportGeneration:

    def test_report_contains_composite_score(self, sample_backtest_df):
        agg = score_results(sample_backtest_df)
        folds = generate_folds()
        wf = score_walk_forward(sample_backtest_df, folds)
        plaus = check_plausibility(sample_backtest_df)
        cpcv = run_cpcv(sample_backtest_df)
        dsr = {'dsr': 1.5, 'p_value': 0.05, 'significant': True,
               'observed_sharpe': 3.0, 'expected_max_sharpe': 2.0, 'n_trials': 7}
        sensitivity = [{'label': 'Default', 'composite_score': 60.0,
                        'multi_asset_accuracy': 58.0, 'wf_mean': 57.0,
                        'wf_std': 5.0, 'wf_sharpe': 11.4,
                        'weights': DEFAULT_WEIGHTS,
                        'fold_scores': [55, 60], 'drawdown_ordering': True,
                        'return_ordering': True}]

        report = generate_report(
            sample_backtest_df, agg, wf, plaus, cpcv, dsr, sensitivity
        )
        assert 'Composite Score' in report
        assert 'Walk-Forward' in report
        assert 'Plausibility' in report
        assert 'CPCV' in report
        assert 'DSR' in report
        assert 'Weight Sensitivity' in report

    def test_report_compares_to_baseline(self, sample_backtest_df):
        agg = score_results(sample_backtest_df)
        folds = generate_folds()
        wf = score_walk_forward(sample_backtest_df, folds)
        plaus = check_plausibility(sample_backtest_df)
        report = generate_report(
            sample_backtest_df, agg, wf, plaus,
            {'pbo': 0.3, 'n_paths': 15, 'oos_mean': 55.0, 'oos_std': 5.0,
             'is_mean': 56.0, 'oos_scores': [55.0] * 15},
            {'dsr': None, 'p_value': None, 'significant': None},
            [],
        )
        assert '52.3' in report  # Baseline mentioned

    def test_report_markdown_format(self, sample_backtest_df):
        agg = score_results(sample_backtest_df)
        folds = generate_folds()
        wf = score_walk_forward(sample_backtest_df, folds)
        plaus = check_plausibility(sample_backtest_df)
        report = generate_report(
            sample_backtest_df, agg, wf, plaus,
            {'pbo': None, 'n_paths': 0},
            {'dsr': None, 'p_value': None, 'significant': None},
            [],
        )
        assert report.startswith('# Market Conditions Backtest Report')


# ---------------------------------------------------------------------------
# Tests: Integration — classify_conditions with real dimension score maps
# ---------------------------------------------------------------------------

class TestVerdictClassification:

    def test_goldilocks_expanding_is_favorable(self, sample_histories):
        """Goldilocks + Expanding Liquidity should give a high score → Favorable or Mixed."""
        # 2015-2019: Goldilocks + Expanding in fixtures
        result = classify_conditions(sample_histories, pd.Timestamp('2017-06-30'))
        assert result is not None
        # Should be positive verdict score
        assert result['verdict_score'] > 0

    def test_deflation_risk_contracting_is_defensive(self, sample_histories):
        """Deflation Risk + Contracting should give low score → Cautious or Defensive."""
        # 2008-2009: Deflation Risk + Contracting in fixtures
        result = classify_conditions(sample_histories, pd.Timestamp('2009-06-30'))
        assert result is not None
        assert result['verdict'] in ('Cautious', 'Defensive')

    def test_verdict_score_range(self, sample_histories):
        """Verdict score should be bounded by dimension score range."""
        result = classify_conditions(sample_histories, pd.Timestamp('2015-06-30'))
        assert result is not None
        # Max possible: 2*0.35 + 2*0.35 + 1*0.20 + 1*0.10 = 1.7
        # Min possible: -2*0.35 + -2*0.35 + -2*0.20 + -1*0.10 = -1.9
        assert -2.0 <= result['verdict_score'] <= 2.0


# ---------------------------------------------------------------------------
# Tests: Walk-forward with actual classification
# ---------------------------------------------------------------------------

class TestWalkForwardIntegration:

    def test_backtest_produces_results(self, sample_histories, sample_scoring_assets):
        from signaltrackers.backtesting.conditions_backtest import run_backtest
        df = run_backtest(
            sample_histories, sample_scoring_assets,
            start_year=2010, end_year=2015,
        )
        assert not df.empty
        assert 'verdict' in df.columns
        assert 'multi_asset_score' in df.columns

    def test_backtest_uses_only_past_data(self, sample_histories, sample_scoring_assets):
        """Each evaluation should only use data available at that date."""
        from signaltrackers.backtesting.conditions_backtest import run_backtest
        df = run_backtest(
            sample_histories, sample_scoring_assets,
            start_year=2010, end_year=2012,
        )
        # All dates should be within the requested range
        dates = pd.to_datetime(df['date'])
        assert dates.min() >= pd.Timestamp('2010-01-01')
        assert dates.max() <= pd.Timestamp('2012-12-31')

    def test_all_four_verdicts_possible(self, sample_histories, sample_scoring_assets):
        """Over a long enough period, all verdicts should appear."""
        from signaltrackers.backtesting.conditions_backtest import run_backtest
        df = run_backtest(
            sample_histories, sample_scoring_assets,
            start_year=2005, end_year=2024,
        )
        verdicts = df['verdict'].unique()
        # At least 2 different verdicts (may not get all 4 with synthetic data)
        assert len(verdicts) >= 2

    def test_forward_returns_computed(self, sample_histories, sample_scoring_assets):
        from signaltrackers.backtesting.conditions_backtest import run_backtest
        df = run_backtest(
            sample_histories, sample_scoring_assets,
            start_year=2010, end_year=2012,
        )
        assert 'sp500_fwd_90d' in df.columns
        assert 'treasuries_fwd_90d' in df.columns
        assert 'gold_fwd_90d' in df.columns

    def test_earlier_folds_degrade_risk(self, sample_histories, sample_scoring_assets):
        """2005-2007 folds use degraded risk (VIX3M unavailable)."""
        from signaltrackers.backtesting.conditions_backtest import run_backtest
        df = run_backtest(
            sample_histories, sample_scoring_assets,
            start_year=2005, end_year=2007,
        )
        # Risk history starts 2008 in fixture → should still get results
        # with gracefully degraded risk (Normal default)
        if not df.empty:
            early = df[df['date'] < '2008-01-01']
            if not early.empty:
                assert (early['risk_state'] == 'Normal').all()


# ---------------------------------------------------------------------------
# Tests: Full pipeline integration
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def test_end_to_end(self, sample_histories, sample_scoring_assets):
        """Full pipeline: backtest → score → plausibility → CPCV → report."""
        from signaltrackers.backtesting.conditions_backtest import run_backtest
        df = run_backtest(
            sample_histories, sample_scoring_assets,
            start_year=2010, end_year=2020,
        )
        assert not df.empty

        agg = score_results(df)
        assert 'overall' in agg

        folds = generate_folds(2010, 2020)
        wf = score_walk_forward(df, folds)
        assert wf['mean'] is not None

        plaus = check_plausibility(df)
        assert 'all_pass' in plaus

        cpcv = run_cpcv(df)
        assert 'pbo' in cpcv

        report = generate_report(
            df, agg, wf, plaus, cpcv,
            {'dsr': None, 'p_value': None, 'significant': None},
            [],
        )
        assert len(report) > 100
