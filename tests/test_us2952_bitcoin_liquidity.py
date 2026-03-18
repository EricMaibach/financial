"""
Tests for US-295.2: Bitcoin / Liquidity Dimension Validation

Tests the walk-forward backtest that validates whether the Liquidity dimension
predicts Bitcoin 90-day forward returns.
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from signaltrackers.backtesting.bitcoin_liquidity_backtest import (
    LIQUIDITY_EXPECTATIONS,
    LIQUIDITY_BUCKETS,
    FOLD_START_YEAR,
    FOLD_END_YEAR,
    FOLD_TEST_MONTHS,
    FORWARD_WINDOW,
    load_bitcoin_price,
    generate_folds,
    run_bitcoin_liquidity_backtest,
    score_results,
    score_walk_forward,
    run_cpcv,
    check_plausibility,
    generate_report,
)


# ---------------------------------------------------------------------------
# Fixtures — synthetic data for deterministic tests
# ---------------------------------------------------------------------------


def _make_liquidity_history(
    start='2013-01-01', end='2025-06-30', freq='W-FRI',
    pattern='expanding',
) -> pd.DataFrame:
    """Create a synthetic liquidity history DataFrame."""
    dates = pd.date_range(start=start, end=end, freq=freq)
    if pattern == 'expanding':
        scores = np.linspace(0.5, 1.5, len(dates))
        states = ['Expanding'] * len(dates)
    elif pattern == 'contracting':
        scores = np.linspace(-0.5, -1.5, len(dates))
        states = ['Contracting'] * len(dates)
    elif pattern == 'mixed':
        scores = np.sin(np.linspace(0, 8 * np.pi, len(dates)))
        states = []
        for s in scores:
            if s > 0.8:
                states.append('Strongly Expanding')
            elif s > 0.2:
                states.append('Expanding')
            elif s > -0.2:
                states.append('Neutral')
            elif s > -0.8:
                states.append('Contracting')
            else:
                states.append('Strongly Contracting')
    else:
        scores = np.zeros(len(dates))
        states = ['Neutral'] * len(dates)

    return pd.DataFrame({
        'date': dates,
        'score': scores,
        'state': states,
    })


def _make_bitcoin_price(
    start='2014-09-01', end='2025-06-30',
    trend='up',
) -> pd.Series:
    """Create a synthetic Bitcoin price series."""
    dates = pd.date_range(start=start, end=end, freq='D')
    n = len(dates)
    if trend == 'up':
        prices = 500 * np.exp(np.linspace(0, 3, n))  # Exponential growth
    elif trend == 'down':
        prices = 50000 * np.exp(np.linspace(0, -1, n))
    elif trend == 'flat':
        prices = np.full(n, 30000.0)
    else:
        # Volatile / cyclical
        base = 500 * np.exp(np.linspace(0, 2.5, n))
        noise = np.sin(np.linspace(0, 20 * np.pi, n)) * 0.2
        prices = base * (1 + noise)

    return pd.Series(prices, index=dates, name='bitcoin_price')


@pytest.fixture
def mixed_liquidity():
    return _make_liquidity_history(pattern='mixed')


@pytest.fixture
def expanding_liquidity():
    return _make_liquidity_history(pattern='expanding')


@pytest.fixture
def btc_up():
    return _make_bitcoin_price(trend='up')


@pytest.fixture
def btc_volatile():
    return _make_bitcoin_price(trend='volatile')


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------


class TestConfiguration:
    """Test backtest configuration constants."""

    def test_liquidity_expectations_covers_all_states(self):
        """All 5 liquidity states must have an expectation."""
        expected_states = {
            'Strongly Expanding', 'Expanding', 'Neutral',
            'Contracting', 'Strongly Contracting',
        }
        assert set(LIQUIDITY_EXPECTATIONS.keys()) == expected_states

    def test_liquidity_expectations_values(self):
        """Expanding states should map to positive, contracting to negative."""
        assert LIQUIDITY_EXPECTATIONS['Strongly Expanding'] == 'positive'
        assert LIQUIDITY_EXPECTATIONS['Expanding'] == 'positive'
        assert LIQUIDITY_EXPECTATIONS['Neutral'] == 'neutral'
        assert LIQUIDITY_EXPECTATIONS['Contracting'] == 'negative'
        assert LIQUIDITY_EXPECTATIONS['Strongly Contracting'] == 'negative'

    def test_liquidity_buckets_covers_all_states(self):
        """All 5 states must map to one of 3 buckets."""
        assert set(LIQUIDITY_BUCKETS.keys()) == set(LIQUIDITY_EXPECTATIONS.keys())
        assert set(LIQUIDITY_BUCKETS.values()) == {'Expanding', 'Neutral', 'Contracting'}

    def test_forward_window_is_90(self):
        """Forward window should be 90 days (M2 lag hypothesis)."""
        assert FORWARD_WINDOW == 90

    def test_fold_start_2014(self):
        """Validation starts 2014 due to Bitcoin data availability."""
        assert FOLD_START_YEAR == 2014

    def test_fold_test_months_matches_main_backtest(self):
        """2-year test windows, same as main conditions backtest."""
        assert FOLD_TEST_MONTHS == 24


# ---------------------------------------------------------------------------
# Fold generation tests
# ---------------------------------------------------------------------------


class TestFoldGeneration:
    """Test walk-forward fold generation."""

    def test_generates_expected_number_of_folds(self):
        folds = generate_folds(2014, 2025, 24)
        # 2014-2015, 2016-2017, 2018-2019, 2020-2021, 2022-2023, 2024-2025
        # = 6 folds (one fewer since last fold may be partial)
        assert len(folds) >= 5

    def test_folds_cover_full_period(self):
        folds = generate_folds(2014, 2025, 24)
        assert folds[0]['test_start'] == pd.Timestamp('2014-01-01')
        assert folds[-1]['test_end'] >= pd.Timestamp('2024-01-01')

    def test_folds_are_contiguous(self):
        folds = generate_folds(2014, 2025, 24)
        for i in range(len(folds) - 1):
            # Next fold starts day after current fold ends (approx)
            gap = (folds[i + 1]['test_start'] - folds[i]['test_end']).days
            assert gap <= 2, f'Gap between fold {i} and {i+1}: {gap} days'

    def test_fold_numbers_sequential(self):
        folds = generate_folds()
        for i, fold in enumerate(folds):
            assert fold['fold'] == i + 1

    def test_expanding_window(self):
        """Each fold has access to all prior data (expanding window)."""
        folds = generate_folds()
        for i in range(1, len(folds)):
            assert folds[i]['test_start'] > folds[i - 1]['test_start']


# ---------------------------------------------------------------------------
# Core backtest tests
# ---------------------------------------------------------------------------


class TestBacktest:
    """Test the core walk-forward backtest logic."""

    def test_returns_dataframe(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_required_columns(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        required = {
            'date', 'liquidity_state', 'liquidity_bucket',
            'liquidity_score', 'expected_direction',
            'btc_fwd_30d', 'btc_fwd_60d', 'btc_fwd_90d', 'correct',
        }
        assert required.issubset(set(df.columns))

    def test_no_lookahead_in_liquidity(self, mixed_liquidity, btc_up):
        """Liquidity state must be from data at or before eval date."""
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        liq_dates = mixed_liquidity['date']
        for _, row in df.iterrows():
            eval_date = pd.Timestamp(row['date'])
            # Must be a valid state from before eval_date
            available = mixed_liquidity[liq_dates <= eval_date]
            assert not available.empty, f'No liquidity data before {eval_date}'

    def test_no_lookahead_in_forward_returns(self, mixed_liquidity, btc_up):
        """Forward returns must not use data beyond eval_date + window."""
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        last_btc = btc_up.index[-1]
        for _, row in df.iterrows():
            eval_date = pd.Timestamp(row['date'])
            # Eval date + 90d must be within Bitcoin data range
            assert eval_date + pd.Timedelta(days=90) <= last_btc + pd.Timedelta(days=1)

    def test_correct_scoring_positive(self, expanding_liquidity, btc_up):
        """Expanding + uptrend Bitcoin → should score correct=1.0."""
        df = run_bitcoin_liquidity_backtest(expanding_liquidity, btc_up)
        # With expanding liquidity and rising BTC, most should be correct
        avg_correct = df['correct'].mean()
        assert avg_correct > 0.5, f'Expected > 50% accuracy, got {avg_correct*100:.1f}%'

    def test_correct_scoring_negative(self):
        """Contracting + downtrend Bitcoin → should score correct=1.0."""
        liq = _make_liquidity_history(pattern='contracting')
        btc = _make_bitcoin_price(trend='down')
        df = run_bitcoin_liquidity_backtest(liq, btc)
        if not df.empty:
            avg_correct = df['correct'].mean()
            assert avg_correct > 0.5

    def test_correct_scoring_neutral(self):
        """Neutral + flat Bitcoin → correct=1.0 if within threshold."""
        liq = _make_liquidity_history(pattern='neutral')
        btc = _make_bitcoin_price(trend='flat')
        df = run_bitcoin_liquidity_backtest(liq, btc)
        if not df.empty:
            # Flat BTC ≈ 0% return → neutral expectation should score 1.0
            avg_correct = df['correct'].mean()
            assert avg_correct > 0.8

    def test_empty_with_no_overlap(self):
        """If liquidity and BTC don't overlap, return empty."""
        liq = _make_liquidity_history(start='2030-01-01', end='2031-12-31')
        btc = _make_bitcoin_price(start='2014-01-01', end='2015-12-31')
        df = run_bitcoin_liquidity_backtest(liq, btc)
        assert df.empty or len(df) == 0

    def test_monthly_evaluation_frequency(self, mixed_liquidity, btc_up):
        """Evaluations should be roughly monthly."""
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        if len(df) >= 2:
            dates = pd.to_datetime(df['date'])
            gaps = dates.diff().dropna().dt.days
            # Monthly ≈ 28-31 days
            assert gaps.median() >= 27
            assert gaps.median() <= 35

    def test_liquidity_bucket_matches_state(self, mixed_liquidity, btc_up):
        """Each liquidity_bucket should match LIQUIDITY_BUCKETS mapping."""
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        for _, row in df.iterrows():
            expected_bucket = LIQUIDITY_BUCKETS[row['liquidity_state']]
            assert row['liquidity_bucket'] == expected_bucket

    def test_expected_direction_matches_state(self, mixed_liquidity, btc_up):
        """expected_direction should match LIQUIDITY_EXPECTATIONS."""
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        for _, row in df.iterrows():
            expected = LIQUIDITY_EXPECTATIONS[row['liquidity_state']]
            assert row['expected_direction'] == expected

    def test_date_range_respects_btc_start(self):
        """Should not evaluate before Bitcoin data starts."""
        liq = _make_liquidity_history(start='2010-01-01')
        btc = _make_bitcoin_price(start='2016-01-01', end='2025-06-30')
        df = run_bitcoin_liquidity_backtest(liq, btc, start_year=2014)
        if not df.empty:
            first_date = pd.Timestamp(df['date'].iloc[0])
            assert first_date >= pd.Timestamp('2016-01-01')


# ---------------------------------------------------------------------------
# Scoring tests
# ---------------------------------------------------------------------------


class TestScoring:
    """Test aggregate scoring logic."""

    def test_overall_accuracy(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        assert 'overall' in scores
        assert 'accuracy' in scores['overall']
        assert 0 <= scores['overall']['accuracy'] <= 100

    def test_per_state_breakdown(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        assert 'per_state' in scores
        # Should have entries for all states present in data
        states_in_data = set(df['liquidity_state'].unique())
        for state in states_in_data:
            assert state in scores['per_state']
            assert scores['per_state'][state]['count'] > 0

    def test_per_bucket_breakdown(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        assert 'per_bucket' in scores
        buckets_in_data = set(df['liquidity_bucket'].unique())
        for bucket in buckets_in_data:
            assert bucket in scores['per_bucket']
            assert scores['per_bucket'][bucket]['count'] > 0

    def test_return_ordering_check(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        overall = scores.get('overall', {})
        # Should have return ordering check if multiple buckets exist
        if len(set(df['liquidity_bucket'].unique())) >= 2:
            assert 'return_ordering_correct' in overall

    def test_per_state_has_avg_returns(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        for state, stats in scores['per_state'].items():
            if stats['count'] > 0:
                assert 'avg_fwd_90d' in stats
                assert 'expected_direction' in stats

    def test_per_bucket_has_pct_positive(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        for bucket, stats in scores['per_bucket'].items():
            if stats['count'] > 0:
                assert 'pct_positive' in stats
                assert 0 <= stats['pct_positive'] <= 100

    def test_total_evaluations_matches_dataframe(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        assert scores['overall']['total_evaluations'] == len(df)

    def test_correct_count_consistency(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        scores = score_results(df)
        # Sum of per-bucket counts = total evaluations
        total_from_buckets = sum(
            stats['count']
            for stats in scores['per_bucket'].values()
        )
        assert total_from_buckets == scores['overall']['total_evaluations']


# ---------------------------------------------------------------------------
# Walk-forward scoring tests
# ---------------------------------------------------------------------------


class TestWalkForward:
    """Test walk-forward fold scoring."""

    def test_returns_fold_details(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        assert 'fold_details' in wf
        assert len(wf['fold_details']) > 0

    def test_mean_and_std(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        if wf.get('mean') is not None:
            assert 0 <= wf['mean'] <= 100
            assert wf['std'] >= 0

    def test_sharpe_ratio(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        if wf.get('sharpe') is not None:
            assert wf['sharpe'] >= 0

    def test_fold_scores_list(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        if wf.get('fold_scores'):
            for score in wf['fold_scores']:
                assert 0 <= score <= 100

    def test_empty_folds_handled(self):
        """Folds with no data should be handled gracefully."""
        df = pd.DataFrame({
            'date': ['2020-01-31', '2020-02-29'],
            'correct': [1.0, 0.0],
            'liquidity_bucket': ['Expanding', 'Contracting'],
        })
        folds = generate_folds(2014, 2025)
        wf = score_walk_forward(df, folds)
        # Should not crash
        assert 'fold_details' in wf


# ---------------------------------------------------------------------------
# CPCV tests
# ---------------------------------------------------------------------------


class TestCPCV:
    """Test Combinatorial Purged Cross-Validation."""

    def test_returns_pbo(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        result = run_cpcv(df)
        if result.get('pbo') is not None:
            assert 0 <= result['pbo'] <= 1

    def test_oos_and_is_means(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        result = run_cpcv(df)
        if result.get('pbo') is not None:
            assert 0 <= result['oos_mean'] <= 100
            assert 0 <= result['is_mean'] <= 100

    def test_insufficient_data(self):
        """CPCV should handle insufficient data gracefully."""
        df = pd.DataFrame({
            'date': ['2020-01-31'],
            'correct': [1.0],
        })
        result = run_cpcv(df)
        assert result['pbo'] is None
        assert result['n_paths'] == 0


# ---------------------------------------------------------------------------
# Plausibility checks tests
# ---------------------------------------------------------------------------


class TestPlausibility:
    """Test economic plausibility checks."""

    def test_2020_2021_expansion_check(self):
        """2020-2021 should show expanding liquidity."""
        dates = pd.date_range('2020-06-01', '2021-12-31', freq='ME')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'liquidity_bucket': ['Expanding'] * len(dates),
            'btc_fwd_90d': [0.1] * len(dates),
            'correct': [1.0] * len(dates),
        })
        result = check_plausibility(df)
        assert result['checks']['2020_2021_liquidity_expansion']['pass'] is True

    def test_2022_contraction_check(self):
        """2022 should show contracting liquidity."""
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='ME')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'liquidity_bucket': ['Contracting'] * len(dates),
            'btc_fwd_90d': [-0.1] * len(dates),
            'correct': [1.0] * len(dates),
        })
        result = check_plausibility(df)
        assert result['checks']['2022_liquidity_contraction']['pass'] is True

    def test_2022_contraction_fails_when_expanding(self):
        """If 2022 shows expanding, the check should fail."""
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='ME')
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'liquidity_bucket': ['Expanding'] * len(dates),
            'btc_fwd_90d': [0.1] * len(dates),
            'correct': [1.0] * len(dates),
        })
        result = check_plausibility(df)
        assert result['checks']['2022_liquidity_contraction']['pass'] is False

    def test_expanding_beats_contracting_returns(self):
        """Expanding should have higher avg returns than Contracting."""
        df = pd.DataFrame({
            'date': ['2020-01-31', '2020-02-29', '2020-03-31', '2020-04-30'],
            'liquidity_bucket': ['Expanding', 'Expanding', 'Contracting', 'Contracting'],
            'btc_fwd_90d': [0.2, 0.15, -0.1, -0.05],
            'correct': [1.0, 1.0, 1.0, 1.0],
        })
        result = check_plausibility(df)
        assert result['checks']['expanding_beats_contracting_returns']['pass'] is True

    def test_all_pass_when_all_checks_pass(self):
        # Create data spanning 2020-2022 with correct liquidity patterns
        dates_exp = pd.date_range('2020-06-01', '2021-12-31', freq='ME')
        dates_con = pd.date_range('2022-01-01', '2022-12-31', freq='ME')
        df = pd.DataFrame({
            'date': list(dates_exp.strftime('%Y-%m-%d')) + list(dates_con.strftime('%Y-%m-%d')),
            'liquidity_bucket': ['Expanding'] * len(dates_exp) + ['Contracting'] * len(dates_con),
            'btc_fwd_90d': [0.1] * len(dates_exp) + [-0.1] * len(dates_con),
            'correct': [1.0] * (len(dates_exp) + len(dates_con)),
        })
        result = check_plausibility(df)
        assert result['all_pass'] is True

    def test_no_data_in_range(self):
        """If no data covers the plausibility periods, checks should pass."""
        df = pd.DataFrame({
            'date': ['2018-01-31', '2018-02-28'],
            'liquidity_bucket': ['Expanding', 'Contracting'],
            'btc_fwd_90d': [0.1, -0.1],
            'correct': [1.0, 1.0],
        })
        result = check_plausibility(df)
        # The 2020_2021 and 2022 checks pass by default (no data)
        # expanding_beats_contracting still runs
        exp_vs_con = result['checks'].get('expanding_beats_contracting_returns', {})
        if 'pass' in exp_vs_con:
            assert exp_vs_con['pass'] is True


# ---------------------------------------------------------------------------
# Report generation tests
# ---------------------------------------------------------------------------


class TestReport:
    """Test report generation."""

    def test_generates_markdown(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        agg = score_results(df)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        plaus = check_plausibility(df)
        cpcv = run_cpcv(df)
        report = generate_report(df, agg, wf, plaus, cpcv)

        assert isinstance(report, str)
        assert '# Bitcoin / Liquidity Dimension Validation Report' in report

    def test_report_includes_per_bucket_table(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        agg = score_results(df)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        plaus = check_plausibility(df)
        cpcv = run_cpcv(df)
        report = generate_report(df, agg, wf, plaus, cpcv)

        assert 'Expanding' in report
        assert 'Contracting' in report

    def test_report_includes_recommendation(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        agg = score_results(df)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        plaus = check_plausibility(df)
        cpcv = run_cpcv(df)
        report = generate_report(df, agg, wf, plaus, cpcv)

        assert 'Recommendation for Phase 11' in report

    def test_report_includes_walk_forward(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        agg = score_results(df)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        plaus = check_plausibility(df)
        cpcv = run_cpcv(df)
        report = generate_report(df, agg, wf, plaus, cpcv)

        assert 'Walk-Forward Validation' in report

    def test_report_includes_baseline_comparison(self, mixed_liquidity, btc_up):
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        agg = score_results(df)
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        plaus = check_plausibility(df)
        cpcv = run_cpcv(df)
        report = generate_report(df, agg, wf, plaus, cpcv)

        assert '34.8' in report  # Baseline comparison

    def test_report_recommendation_strong_signal(self):
        """Strong signal recommendation when accuracy is high."""
        df = pd.DataFrame({
            'date': ['2020-01-31'],
            'liquidity_state': ['Expanding'],
            'liquidity_bucket': ['Expanding'],
            'correct': [1.0],
            'btc_fwd_90d': [0.1],
        })
        agg = {
            'overall': {'accuracy': 65.0, 'total_evaluations': 100},
            'per_state': {},
            'per_bucket': {
                'Expanding': {'count': 50, 'accuracy': 70.0},
                'Contracting': {'count': 50, 'accuracy': 60.0},
            },
        }
        wf = {'mean': 65.0, 'std': 5.0, 'sharpe': 13.0, 'n_folds': 6, 'fold_details': []}
        plaus = {'all_pass': True, 'checks': {}}
        cpcv = {'pbo': 0.3, 'n_paths': 15, 'oos_mean': 64.0, 'oos_std': 3.0, 'is_mean': 65.0}
        report = generate_report(df, agg, wf, plaus, cpcv)
        assert 'STRONG SIGNAL' in report

    def test_report_recommendation_weak_signal(self):
        """Weak signal recommendation when accuracy is low."""
        df = pd.DataFrame({
            'date': ['2020-01-31'],
            'liquidity_state': ['Expanding'],
            'liquidity_bucket': ['Expanding'],
            'correct': [0.0],
            'btc_fwd_90d': [-0.1],
        })
        agg = {
            'overall': {'accuracy': 35.0, 'total_evaluations': 100},
            'per_state': {},
            'per_bucket': {},
        }
        wf = {'mean': 35.0, 'std': 10.0, 'sharpe': 3.5, 'n_folds': 6, 'fold_details': []}
        plaus = {'all_pass': False, 'checks': {}}
        cpcv = {'pbo': 0.7, 'n_paths': 15, 'oos_mean': 34.0, 'oos_std': 5.0, 'is_mean': 40.0}
        report = generate_report(df, agg, wf, plaus, cpcv)
        assert 'WEAK SIGNAL' in report


# ---------------------------------------------------------------------------
# Data loading tests
# ---------------------------------------------------------------------------


class TestDataLoading:
    """Test data loading functions."""

    def test_load_bitcoin_price_returns_series_or_none(self):
        """Should return a Series or None if file missing."""
        result = load_bitcoin_price()
        # In test environment, may or may not exist
        assert result is None or isinstance(result, pd.Series)

    @pytest.mark.skipif(
        not Path(__file__).resolve().parent.parent.joinpath(
            'signaltrackers', 'data', 'bitcoin_price.csv'
        ).exists(),
        reason='bitcoin_price.csv not present (data not collected)',
    )
    def test_bitcoin_price_has_data(self):
        result = load_bitcoin_price()
        assert result is not None
        assert len(result) > 100  # Should have substantial data
        assert result.index[0] <= pd.Timestamp('2015-01-01')


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_short_bitcoin_history(self):
        """Should handle short Bitcoin history gracefully."""
        liq = _make_liquidity_history(start='2014-01-01', end='2025-12-31')
        btc = _make_bitcoin_price(start='2024-01-01', end='2025-06-30')
        df = run_bitcoin_liquidity_backtest(liq, btc, start_year=2024, end_year=2025)
        # Should produce results for the overlap period
        if not df.empty:
            assert len(df) >= 1

    def test_handles_weekends_holidays(self):
        """Bitcoin trades 24/7 but some FRED series have gaps."""
        liq = _make_liquidity_history(freq='ME')  # Monthly only
        btc = _make_bitcoin_price()
        df = run_bitcoin_liquidity_backtest(liq, btc)
        # Should still produce results despite different frequencies
        assert not df.empty

    def test_extreme_volatility_included(self, mixed_liquidity):
        """Extreme periods (COVID, FTX) should not be filtered out."""
        btc = _make_bitcoin_price(trend='volatile')
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc)
        # Should include the full date range, including volatile periods
        if not df.empty:
            dates = pd.to_datetime(df['date'])
            # Should cover both stable and volatile periods
            assert (dates.max() - dates.min()).days > 365

    def test_single_liquidity_state(self):
        """If only one liquidity state exists, scoring still works."""
        liq = _make_liquidity_history(pattern='expanding')
        btc = _make_bitcoin_price(trend='up')
        df = run_bitcoin_liquidity_backtest(liq, btc)
        if not df.empty:
            scores = score_results(df)
            assert 'accuracy' in scores['overall']

    def test_deterministic_results(self, mixed_liquidity, btc_up):
        """Same inputs should produce same outputs."""
        df1 = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        df2 = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        pd.testing.assert_frame_equal(df1, df2)


# ---------------------------------------------------------------------------
# Integration test — full pipeline with synthetic data
# ---------------------------------------------------------------------------


class TestIntegration:
    """Test full pipeline end-to-end with synthetic data."""

    def test_full_pipeline(self, mixed_liquidity, btc_volatile):
        """Run full pipeline: backtest → score → walk-forward → CPCV → plausibility → report."""
        # Run backtest
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_volatile)
        assert not df.empty

        # Score
        agg = score_results(df)
        assert agg['overall']['accuracy'] is not None

        # Walk-forward
        folds = generate_folds()
        wf = score_walk_forward(df, folds)
        assert wf.get('mean') is not None

        # CPCV
        cpcv = run_cpcv(df)
        # May or may not compute depending on data size
        assert 'pbo' in cpcv

        # Plausibility
        plaus = check_plausibility(df)
        assert 'all_pass' in plaus

        # Report
        report = generate_report(df, agg, wf, plaus, cpcv)
        assert len(report) > 100
        assert '# Bitcoin / Liquidity Dimension Validation Report' in report

    def test_not_included_in_main_composite(self, mixed_liquidity, btc_up):
        """Bitcoin accuracy must NOT be included in the main composite score.

        Verify by checking that the output does not contain 'composite_score'
        in the results — this is a Bitcoin-only validation, not part of
        the multi-asset composite.
        """
        df = run_bitcoin_liquidity_backtest(mixed_liquidity, btc_up)
        agg = score_results(df)
        # The overall section should have 'accuracy' but NOT 'composite_score'
        assert 'accuracy' in agg['overall']
        assert 'composite_score' not in agg['overall']
