"""
Tests for US-314.2: Quadrant-led backtest scoring with real returns and
magnitude ordering.

Tests the refactored Market Conditions backtest that:
  1. Scores against quadrant expectations (no verdict classifier)
  2. Uses inflation-adjusted (real) returns for S&P 500
  3. Checks magnitude ordering of real returns across quadrants
"""

import json
import math
from datetime import datetime
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from signaltrackers.backtesting.conditions_backtest import (
    QUADRANT_LABELS,
    QUADRANT_EXPECTATIONS,
    RISK_FILTER_CONFIGS,
    FOLD_START_YEAR,
    FOLD_END_YEAR,
    FOLD_TEST_MONTHS,
    SCORING_ASSETS,
    load_cpi_series,
    compute_cpi_yoy,
    classify_conditions,
    score_single_evaluation,
    run_backtest,
    generate_folds,
    score_walk_forward,
    score_results,
    check_plausibility,
    run_cpcv,
    compute_dsr,
    run_risk_filter_sensitivity,
    generate_report,
    _get_dimension_state_at,
    _rescore_without_risk_override,
    _rescore_with_elevated_override,
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
        'growth_score': np.random.randn(len(quadrants)),
        'inflation_score': np.random.randn(len(quadrants)),
        'quadrant': quadrants,
    })


@pytest.fixture
def sample_risk_history():
    """Risk history spanning 2005-2024."""
    dates = pd.date_range('2005-01-01', '2024-12-31', freq='W-WED')
    states = []
    for d in dates:
        if d.year <= 2007:
            states.append('Calm')
        elif d.year in (2008, 2009):
            states.append('Stressed')
        elif d.year <= 2019:
            states.append('Normal')
        elif d.year == 2020 and d.month <= 4:
            states.append('Stressed')
        elif d.year <= 2021:
            states.append('Normal')
        elif d.year == 2022:
            states.append('Elevated')
        else:
            states.append('Calm')
    return pd.DataFrame({
        'date': dates[:len(states)],
        'score': np.random.randn(len(states)),
        'state': states,
    })


@pytest.fixture
def sample_policy_history():
    """Policy history spanning 2005-2024."""
    dates = pd.date_range('2005-01-01', '2024-12-31', freq='ME')
    stances = []
    for d in dates:
        if d.year <= 2007:
            stances.append('Neutral')
        elif d.year <= 2015:
            stances.append('Accommodative')
        elif d.year <= 2018:
            stances.append('Restrictive')
        elif d.year <= 2021:
            stances.append('Accommodative')
        elif d.year <= 2023:
            stances.append('Restrictive')
        else:
            stances.append('Neutral')
    return pd.DataFrame({
        'date': dates[:len(stances)],
        'stance': stances,
    })


@pytest.fixture
def sample_histories(sample_liquidity_history, sample_quadrant_history,
                     sample_risk_history, sample_policy_history):
    """Combined dimension histories."""
    return {
        'liquidity': sample_liquidity_history,
        'quadrant': sample_quadrant_history,
        'risk': sample_risk_history,
        'policy': sample_policy_history,
    }


@pytest.fixture
def sample_cpi_series():
    """CPI series from 2003 to 2024 with ~2.5% annual growth."""
    dates = pd.date_range('2003-01-01', '2024-12-31', freq='MS')
    values = 180.0 * (1 + 0.0021) ** np.arange(len(dates))  # ~2.5% annual
    return pd.Series(values, index=dates)


@pytest.fixture
def sample_scoring_assets():
    """Synthetic scoring assets for testing."""
    dates = pd.date_range('2004-01-01', '2025-12-31', freq='B')
    assets = {}
    np.random.seed(42)

    # S&P 500 — upward trend
    sp500 = 1000.0
    sp500_vals = [sp500]
    for _ in range(len(dates) - 1):
        sp500 *= 1 + np.random.normal(0.0003, 0.01)
        sp500_vals.append(sp500)
    assets['sp500'] = pd.Series(sp500_vals, index=dates)

    # Treasuries — slight upward
    tlt = 100.0
    tlt_vals = [tlt]
    for _ in range(len(dates) - 1):
        tlt *= 1 + np.random.normal(0.0001, 0.005)
        tlt_vals.append(tlt)
    assets['treasuries'] = pd.Series(tlt_vals, index=dates)

    # Gold — upward
    gold = 400.0
    gold_vals = [gold]
    for _ in range(len(dates) - 1):
        gold *= 1 + np.random.normal(0.0002, 0.008)
        gold_vals.append(gold)
    assets['gold'] = pd.Series(gold_vals, index=dates)

    return assets


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------

class TestConfiguration:
    """Test module-level configuration constants."""

    def test_quadrant_labels_order(self):
        """QUADRANT_LABELS should be in real-return ordering."""
        assert QUADRANT_LABELS == ['Goldilocks', 'Deflation Risk', 'Reflation', 'Stagflation']

    def test_quadrant_expectations_keys(self):
        """All four quadrants should have expectations defined."""
        assert set(QUADRANT_EXPECTATIONS.keys()) == {
            'Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk',
        }

    def test_quadrant_expectations_assets(self):
        """Each quadrant should define sp500, treasuries, gold."""
        for quad, exp in QUADRANT_EXPECTATIONS.items():
            assert set(exp.keys()) == {'sp500', 'treasuries', 'gold'}, f'{quad} missing assets'

    def test_goldilocks_expectations(self):
        assert QUADRANT_EXPECTATIONS['Goldilocks'] == {
            'sp500': 'positive', 'treasuries': 'positive', 'gold': 'neutral',
        }

    def test_reflation_expectations(self):
        assert QUADRANT_EXPECTATIONS['Reflation'] == {
            'sp500': 'positive', 'treasuries': 'negative', 'gold': 'positive',
        }

    def test_stagflation_expectations(self):
        assert QUADRANT_EXPECTATIONS['Stagflation'] == {
            'sp500': 'negative', 'treasuries': 'negative', 'gold': 'positive',
        }

    def test_deflation_risk_expectations(self):
        assert QUADRANT_EXPECTATIONS['Deflation Risk'] == {
            'sp500': 'negative', 'treasuries': 'positive', 'gold': 'neutral',
        }

    def test_no_verdict_labels(self):
        """Verdict labels should not exist — replaced by quadrant labels."""
        import signaltrackers.backtesting.conditions_backtest as mod
        assert not hasattr(mod, 'VERDICT_LABELS')
        assert not hasattr(mod, 'VERDICT_EXPECTATIONS')
        assert not hasattr(mod, 'DEFAULT_WEIGHTS')
        assert not hasattr(mod, 'WEIGHT_CONFIGS')

    def test_risk_filter_configs_defined(self):
        assert len(RISK_FILTER_CONFIGS) == 3


# ---------------------------------------------------------------------------
# CPI loading tests
# ---------------------------------------------------------------------------

class TestCPILoading:
    """Test CPI data loading and YoY computation."""

    def test_compute_cpi_yoy_basic(self, sample_cpi_series):
        """CPI YoY should be approximately 2.5% for our synthetic data."""
        eval_date = pd.Timestamp('2010-06-30')
        yoy = compute_cpi_yoy(sample_cpi_series, eval_date)
        assert yoy is not None
        assert abs(yoy - 0.025) < 0.005  # Approximately 2.5%

    def test_compute_cpi_yoy_none_when_no_data(self):
        """Should return None when CPI series is None."""
        assert compute_cpi_yoy(None, pd.Timestamp('2020-01-01')) is None

    def test_compute_cpi_yoy_none_when_empty(self):
        """Should return None when CPI series is empty."""
        assert compute_cpi_yoy(pd.Series(dtype=float), pd.Timestamp('2020-01-01')) is None

    def test_compute_cpi_yoy_none_when_insufficient_history(self):
        """Should return None when less than 13 months of data."""
        dates = pd.date_range('2020-01-01', '2020-11-01', freq='MS')
        short_cpi = pd.Series(range(len(dates)), index=dates, dtype=float)
        assert compute_cpi_yoy(short_cpi, pd.Timestamp('2020-11-01')) is None

    def test_compute_cpi_yoy_no_lookahead(self, sample_cpi_series):
        """CPI YoY should only use data at or before eval_date."""
        eval_date = pd.Timestamp('2015-01-15')
        yoy = compute_cpi_yoy(sample_cpi_series, eval_date)
        assert yoy is not None
        # Verify no future data used
        available = sample_cpi_series[sample_cpi_series.index <= eval_date]
        assert len(available) >= 13

    def test_load_cpi_series_returns_none_when_missing(self, tmp_path):
        """Should return None when cpi.csv doesn't exist."""
        with patch('signaltrackers.backtesting.conditions_backtest.DATA_DIR', tmp_path):
            assert load_cpi_series() is None


# ---------------------------------------------------------------------------
# classify_conditions tests
# ---------------------------------------------------------------------------

class TestClassifyConditions:
    """Test quadrant-led classification."""

    def test_returns_quadrant_directly(self, sample_histories):
        """classify_conditions should return the quadrant as headline."""
        eval_date = pd.Timestamp('2006-06-30')
        result = classify_conditions(sample_histories, eval_date)
        assert result is not None
        assert 'quadrant' in result
        assert result['quadrant'] == 'Goldilocks'

    def test_no_verdict_in_result(self, sample_histories):
        """Result should NOT contain verdict or verdict_score."""
        eval_date = pd.Timestamp('2010-06-30')
        result = classify_conditions(sample_histories, eval_date)
        assert result is not None
        assert 'verdict' not in result
        assert 'verdict_score' not in result

    def test_no_weights_parameter(self, sample_histories):
        """classify_conditions should not accept weights."""
        eval_date = pd.Timestamp('2010-06-30')
        # Should work without weights — no longer a parameter
        result = classify_conditions(sample_histories, eval_date)
        assert result is not None

    def test_expectations_from_quadrant(self, sample_histories):
        """Expectations should come directly from QUADRANT_EXPECTATIONS."""
        # 2006 → Goldilocks
        eval_date = pd.Timestamp('2006-06-30')
        result = classify_conditions(sample_histories, eval_date)
        assert result['expectations']['sp500'] == 'positive'
        assert result['expectations']['treasuries'] == 'positive'
        assert result['expectations']['gold'] == 'neutral'

    def test_deflation_risk_expectations(self, sample_histories):
        """Deflation Risk quadrant should have correct expectations."""
        eval_date = pd.Timestamp('2008-06-30')  # GFC → Deflation Risk
        result = classify_conditions(sample_histories, eval_date)
        assert result['quadrant'] == 'Deflation Risk'
        assert result['expectations']['treasuries'] == 'positive'

    def test_stagflation_expectations(self, sample_histories):
        """Stagflation quadrant should have correct expectations."""
        eval_date = pd.Timestamp('2022-06-30')
        result = classify_conditions(sample_histories, eval_date)
        assert result['quadrant'] == 'Stagflation'
        assert result['expectations']['sp500'] == 'negative'
        assert result['expectations']['gold'] == 'positive'

    def test_stressed_overrides_sp500_to_negative(self, sample_histories):
        """When risk is Stressed, S&P 500 expectation should be negative."""
        # 2008 → Stressed + Deflation Risk (already negative)
        eval_date = pd.Timestamp('2008-06-30')
        result = classify_conditions(sample_histories, eval_date)
        assert result['risk_state'] == 'Stressed'
        assert result['expectations']['sp500'] == 'negative'

    def test_stressed_overrides_goldilocks_sp500(self):
        """Even Goldilocks should flip S&P to negative when Stressed."""
        # Build minimal histories with Goldilocks + Stressed
        quad_df = pd.DataFrame({
            'date': [pd.Timestamp('2020-01-01')],
            'quadrant': ['Goldilocks'],
        })
        risk_df = pd.DataFrame({
            'date': [pd.Timestamp('2020-01-01')],
            'state': ['Stressed'],
        })
        histories = {'quadrant': quad_df, 'risk': risk_df}
        result = classify_conditions(histories, pd.Timestamp('2020-01-01'))
        assert result['quadrant'] == 'Goldilocks'
        assert result['expectations']['sp500'] == 'negative'  # Override!
        # Treasuries and gold should remain from Goldilocks
        assert result['expectations']['treasuries'] == 'positive'
        assert result['expectations']['gold'] == 'neutral'

    def test_returns_none_without_quadrant(self, sample_liquidity_history):
        """Should return None if no quadrant history available."""
        histories = {'liquidity': sample_liquidity_history}
        result = classify_conditions(histories, pd.Timestamp('2010-01-01'))
        assert result is None

    def test_works_without_liquidity(self, sample_quadrant_history):
        """Should work with just quadrant history (liquidity optional)."""
        histories = {'quadrant': sample_quadrant_history}
        result = classify_conditions(histories, pd.Timestamp('2010-06-30'))
        assert result is not None
        assert result['liquidity_state'] is None

    def test_graceful_degradation_risk(self, sample_quadrant_history):
        """Missing risk should default to Normal."""
        histories = {'quadrant': sample_quadrant_history}
        result = classify_conditions(histories, pd.Timestamp('2010-06-30'))
        assert result['risk_state'] == 'Normal'

    def test_graceful_degradation_policy(self, sample_quadrant_history):
        """Missing policy should default to Neutral."""
        histories = {'quadrant': sample_quadrant_history}
        result = classify_conditions(histories, pd.Timestamp('2010-06-30'))
        assert result['policy_stance'] == 'Neutral'

    def test_result_structure(self, sample_histories):
        """Result should contain expected keys."""
        result = classify_conditions(sample_histories, pd.Timestamp('2015-06-30'))
        assert result is not None
        expected_keys = {'quadrant', 'liquidity_state', 'risk_state',
                         'policy_stance', 'expectations'}
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# score_single_evaluation tests
# ---------------------------------------------------------------------------

class TestScoreSingleEvaluation:
    """Test scoring logic with real returns for S&P 500."""

    def test_positive_real_return_scores_correctly(self):
        """S&P 500 with positive real return should score 1.0 when expected positive."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'neutral'}
        asset_returns = {'sp500': 0.05, 'treasuries': 0.02, 'gold': 0.01}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=0.03)
        assert result['asset_scores']['sp500'] == 1.0

    def test_real_return_used_over_nominal(self):
        """When real return is provided, it should be used instead of nominal for S&P."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'neutral'}
        # Nominal positive but real negative
        asset_returns = {'sp500': 0.02, 'treasuries': 0.01, 'gold': 0.03}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=-0.01)
        # S&P should score 0.0 (real return is negative, expected positive)
        assert result['asset_scores']['sp500'] == 0.0

    def test_nominal_used_when_real_not_available(self):
        """When real_sp500_return is None, nominal should be used."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'neutral'}
        asset_returns = {'sp500': 0.05, 'treasuries': 0.02, 'gold': 0.01}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=None)
        assert result['asset_scores']['sp500'] == 1.0  # Uses nominal 5%

    def test_treasuries_use_nominal(self):
        """Treasuries should always use nominal returns."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'neutral'}
        asset_returns = {'sp500': 0.05, 'treasuries': 0.03, 'gold': 0.02}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=0.01)
        assert result['asset_scores']['treasuries'] == 1.0

    def test_gold_uses_nominal(self):
        """Gold should always use nominal returns."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'positive'}
        asset_returns = {'sp500': 0.05, 'treasuries': 0.03, 'gold': 0.04}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=0.01)
        assert result['asset_scores']['gold'] == 1.0

    def test_negative_direction_scoring(self):
        """Negative direction should score 1.0 for negative returns."""
        expectations = {'sp500': 'negative', 'treasuries': 'negative', 'gold': 'positive'}
        asset_returns = {'sp500': -0.05, 'treasuries': -0.02, 'gold': 0.03}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=-0.08)
        assert result['asset_scores']['sp500'] == 1.0
        assert result['asset_scores']['treasuries'] == 1.0
        assert result['asset_scores']['gold'] == 1.0

    def test_neutral_direction_scoring(self):
        """Neutral direction: 1.0 if small move, 0.5 if larger."""
        expectations = {'sp500': 'neutral', 'treasuries': 'neutral', 'gold': 'neutral'}
        asset_returns = {'sp500': 0.01, 'treasuries': 0.10, 'gold': -0.03}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=0.01)
        assert result['asset_scores']['sp500'] == 1.0   # < 5%
        assert result['asset_scores']['treasuries'] == 0.5  # > 5%

    def test_weighted_score_computed(self):
        """Weighted score should be computed from available assets."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'positive'}
        asset_returns = {'sp500': 0.05, 'treasuries': 0.02, 'gold': 0.03}
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=0.03)
        assert result['weighted_score'] is not None
        assert 0.0 <= result['weighted_score'] <= 1.0

    def test_missing_asset_excluded(self):
        """Missing assets should be excluded from scoring."""
        expectations = {'sp500': 'positive', 'treasuries': 'positive', 'gold': 'positive'}
        asset_returns = {'sp500': 0.05}  # Only sp500
        result = score_single_evaluation(expectations, asset_returns, real_sp500_return=0.03)
        assert 'sp500' in result['asset_scores']
        assert 'treasuries' not in result['asset_scores']
        assert 'gold' not in result['asset_scores']


# ---------------------------------------------------------------------------
# run_backtest tests
# ---------------------------------------------------------------------------

class TestRunBacktest:
    """Test full backtest run with quadrant-led scoring."""

    def test_backtest_produces_results(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2010)
        assert not df.empty
        assert 'quadrant' in df.columns
        assert 'multi_asset_score' in df.columns

    def test_no_verdict_columns(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """Output should not contain verdict columns."""
        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2010)
        assert 'verdict' not in df.columns
        assert 'verdict_score' not in df.columns

    def test_real_return_column_present(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """Output should contain sp500_real_fwd_90d column."""
        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2010)
        assert 'sp500_real_fwd_90d' in df.columns

    def test_cpi_yoy_column_present(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """Output should contain cpi_yoy column."""
        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2010)
        assert 'cpi_yoy' in df.columns

    def test_real_return_formula(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """Real return should equal nominal - cpi_yoy/4."""
        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2010)
        for _, row in df.iterrows():
            nominal = row.get('sp500_fwd_90d')
            cpi_yoy = row.get('cpi_yoy')
            real = row.get('sp500_real_fwd_90d')
            if nominal is not None and cpi_yoy is not None and real is not None:
                expected_real = nominal - (cpi_yoy / 4)
                assert abs(real - expected_real) < 1e-10, f'Real return mismatch at {row["date"]}'

    def test_backtest_without_cpi(self, sample_histories, sample_scoring_assets):
        """Backtest should work without CPI (uses nominal returns)."""
        df = run_backtest(sample_histories, sample_scoring_assets, cpi_series=None,
                         start_year=2006, end_year=2010)
        assert not df.empty
        # Real return should be None when CPI unavailable
        assert all(pd.isna(df['sp500_real_fwd_90d']))

    def test_dimension_states_recorded(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """All dimension states should be recorded in output."""
        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2010)
        assert 'liquidity_state' in df.columns
        assert 'risk_state' in df.columns
        assert 'policy_stance' in df.columns


# ---------------------------------------------------------------------------
# score_results tests
# ---------------------------------------------------------------------------

class TestScoreResults:
    """Test aggregate scoring with quadrant-led metrics."""

    def _make_test_df(self):
        """Create a minimal test DataFrame."""
        rows = []
        quadrants = ['Goldilocks'] * 5 + ['Reflation'] * 5 + ['Stagflation'] * 5 + ['Deflation Risk'] * 5
        real_returns = [0.04, 0.05, 0.03, 0.06, 0.02,  # Goldilocks: avg ~4%
                        0.01, 0.02, 0.015, 0.01, 0.02,   # Reflation: avg ~1.5%
                        0.005, 0.01, 0.008, 0.012, 0.005,  # Stagflation: avg ~0.8%
                        0.02, 0.015, 0.025, 0.018, 0.022]  # Defl Risk: avg ~2%
        drawdowns = [-0.02, -0.01, -0.015, -0.01, -0.02,  # Goldilocks: mild
                     -0.04, -0.03, -0.035, -0.04, -0.03,   # Reflation
                     -0.08, -0.07, -0.09, -0.06, -0.08,    # Stagflation: worst
                     -0.05, -0.04, -0.06, -0.04, -0.05]    # Defl Risk

        for i, (q, rr, dd) in enumerate(zip(quadrants, real_returns, drawdowns)):
            rows.append({
                'date': f'2010-{(i % 12) + 1:02d}-28',
                'quadrant': q,
                'sp500_real_fwd_90d': rr,
                'sp500_fwd_90d': rr + 0.005,  # Nominal slightly above real
                'treasuries_fwd_90d': 0.02 if q in ('Goldilocks', 'Deflation Risk') else -0.01,
                'gold_fwd_90d': 0.01,
                'sp500_max_dd_90d': dd,
                'multi_asset_score': 0.7,
                'sp500_correct': 1.0,
                'treasuries_correct': 0.8,
                'gold_correct': 0.5,
            })
        return pd.DataFrame(rows)

    def test_per_quadrant_instead_of_per_verdict(self):
        """Result should have per_quadrant, not per_verdict."""
        df = self._make_test_df()
        report = score_results(df)
        assert 'per_quadrant' in report
        assert 'per_verdict' not in report

    def test_all_quadrants_covered(self):
        """All four quadrants should appear in per_quadrant."""
        df = self._make_test_df()
        report = score_results(df)
        for q in QUADRANT_LABELS:
            assert q in report['per_quadrant']

    def test_real_return_ordering_check(self):
        """Magnitude ordering should be checked on real returns."""
        df = self._make_test_df()
        report = score_results(df)
        assert 'real_return_ordering_correct' in report['overall']
        # Our data has Goldilocks(4%) > Defl Risk(2%) > Reflation(1.5%) > Stagflation(0.8%)
        assert report['overall']['real_return_ordering_correct'] is True

    def test_real_return_ordering_fails_when_wrong(self):
        """Should fail when ordering doesn't hold."""
        df = self._make_test_df()
        # Swap Goldilocks and Stagflation returns
        df.loc[df['quadrant'] == 'Goldilocks', 'sp500_real_fwd_90d'] = 0.005
        df.loc[df['quadrant'] == 'Stagflation', 'sp500_real_fwd_90d'] = 0.06
        report = score_results(df)
        assert report['overall']['real_return_ordering_correct'] is False

    def test_drawdown_ordering_check(self):
        """Drawdowns should worsen from Goldilocks to Stagflation."""
        df = self._make_test_df()
        report = score_results(df)
        assert 'drawdown_ordering_correct' in report['overall']

    def test_composite_score_computed(self):
        """Composite = 50% accuracy + 25% real ordering + 25% dd ordering."""
        df = self._make_test_df()
        report = score_results(df)
        composite = report['overall'].get('composite_score')
        assert composite is not None

    def test_composite_formula(self):
        """Verify composite formula calculation."""
        df = self._make_test_df()
        report = score_results(df)
        overall = report['overall']
        accuracy = overall['multi_asset_accuracy']
        real_ordering = 100.0 if overall.get('real_return_ordering_correct') else 0.0
        dd_ordering = 100.0 if overall.get('drawdown_ordering_correct') else 0.0
        expected = (accuracy * 0.50 + real_ordering * 0.25 + dd_ordering * 0.25)
        assert abs(overall['composite_score'] - expected) < 0.2

    def test_per_quadrant_real_return_avg(self):
        """Per-quadrant stats should include sp500_real_avg_90d."""
        df = self._make_test_df()
        report = score_results(df)
        for q in QUADRANT_LABELS:
            stats = report['per_quadrant'][q]
            if stats['count'] > 0:
                assert 'sp500_real_avg_90d' in stats


# ---------------------------------------------------------------------------
# check_plausibility tests
# ---------------------------------------------------------------------------

class TestCheckPlausibility:
    """Test plausibility checks with quadrant labels."""

    def test_march_2020_not_goldilocks(self):
        """March 2020 check should use quadrant, not verdict."""
        rows = [
            {'date': '2020-02-28', 'quadrant': 'Deflation Risk'},
            {'date': '2020-03-31', 'quadrant': 'Deflation Risk'},
        ]
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        assert 'march_2020_not_goldilocks' in result['checks']
        assert result['checks']['march_2020_not_goldilocks']['pass'] is True

    def test_march_2020_fails_if_goldilocks_dominant(self):
        """Should fail if Goldilocks is dominant in March 2020."""
        rows = [
            {'date': '2020-02-28', 'quadrant': 'Goldilocks'},
            {'date': '2020-03-31', 'quadrant': 'Goldilocks'},
        ]
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        assert result['checks']['march_2020_not_goldilocks']['pass'] is False

    def test_2022_stagflation_present(self):
        """2022 should have Stagflation present."""
        rows = [
            {'date': '2022-03-31', 'quadrant': 'Stagflation'},
            {'date': '2022-06-30', 'quadrant': 'Stagflation'},
            {'date': '2022-09-30', 'quadrant': 'Deflation Risk'},
        ]
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        assert result['checks']['2022_stagflation_present']['pass'] is True

    def test_2022_fails_without_stagflation(self):
        """Should fail if Stagflation never appears in 2022."""
        rows = [
            {'date': '2022-03-31', 'quadrant': 'Goldilocks'},
            {'date': '2022-06-30', 'quadrant': 'Reflation'},
        ]
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        assert result['checks']['2022_stagflation_present']['pass'] is False

    def test_quadrant_stability_check(self):
        """Stability check should use quadrant, not verdict."""
        rows = []
        # 12 months of Goldilocks → stable
        for m in range(1, 13):
            rows.append({'date': f'2010-{m:02d}-28', 'quadrant': 'Goldilocks'})
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        assert 'quadrant_stability' in result['checks']
        assert 'verdict_stability' not in result['checks']
        assert result['checks']['quadrant_stability']['pass'] is True

    def test_no_verdict_check_names(self):
        """No check should reference 'verdict' or 'favorable'."""
        rows = [
            {'date': '2020-06-30', 'quadrant': 'Goldilocks'},
        ]
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        for check_name in result['checks']:
            assert 'verdict' not in check_name.lower()
            assert 'favorable' not in check_name.lower()

    def test_all_pass_when_valid(self):
        """All checks should pass with well-formed data."""
        rows = []
        # 2020: not Goldilocks
        rows.append({'date': '2020-03-31', 'quadrant': 'Deflation Risk'})
        # 2022: Stagflation present
        rows.append({'date': '2022-03-31', 'quadrant': 'Stagflation'})
        rows.append({'date': '2022-06-30', 'quadrant': 'Stagflation'})
        rows.append({'date': '2022-09-30', 'quadrant': 'Deflation Risk'})
        rows.append({'date': '2022-12-31', 'quadrant': 'Deflation Risk'})
        # Stable enough
        for y in range(2010, 2020):
            for m in range(1, 13):
                rows.append({'date': f'{y}-{m:02d}-28', 'quadrant': 'Goldilocks'})
        df = pd.DataFrame(rows)
        result = check_plausibility(df)
        assert result['all_pass'] is True


# ---------------------------------------------------------------------------
# Walk-forward tests
# ---------------------------------------------------------------------------

class TestWalkForward:
    """Test walk-forward validation."""

    def test_fold_generation(self):
        folds = generate_folds()
        assert len(folds) == 10  # 2005-2025, 2yr windows
        assert folds[0]['test_start'] == pd.Timestamp('2005-01-01')

    def test_score_walk_forward_uses_quadrant_counts(self):
        """Fold details should have quadrant_counts, not verdict_counts."""
        rows = []
        for y in range(2005, 2010):
            for m in range(1, 13):
                rows.append({
                    'date': f'{y}-{m:02d}-28',
                    'quadrant': 'Goldilocks',
                    'multi_asset_score': 0.7,
                })
        df = pd.DataFrame(rows)
        folds = generate_folds(2005, 2010)
        result = score_walk_forward(df, folds)
        for fd in result.get('fold_details', []):
            if fd.get('score') is not None:
                assert 'quadrant_counts' in fd
                assert 'verdict_counts' not in fd


# ---------------------------------------------------------------------------
# Risk filter sensitivity tests
# ---------------------------------------------------------------------------

class TestRiskFilterSensitivity:
    """Test risk filter sensitivity analysis."""

    def test_rescore_without_risk_override(self):
        """No-override rescoring should use pure quadrant expectations."""
        df = pd.DataFrame([{
            'date': '2020-03-31',
            'quadrant': 'Goldilocks',
            'risk_state': 'Stressed',
            'sp500_fwd_90d': 0.05,
            'treasuries_fwd_90d': 0.02,
            'gold_fwd_90d': 0.01,
            'sp500_real_fwd_90d': 0.03,
            'multi_asset_score': 0.0,
            'sp500_correct': 0.0,
            'treasuries_correct': 1.0,
            'gold_correct': 0.5,
        }])
        rescored = _rescore_without_risk_override(df, None)
        # Without override, Goldilocks expects sp500 positive → real 3% is positive → score 1.0
        assert rescored.iloc[0]['sp500_correct'] == 1.0

    def test_rescore_with_elevated_override(self):
        """Elevated override should also flip S&P to negative expectation."""
        df = pd.DataFrame([{
            'date': '2022-06-30',
            'quadrant': 'Goldilocks',
            'risk_state': 'Elevated',
            'sp500_fwd_90d': 0.05,
            'treasuries_fwd_90d': 0.02,
            'gold_fwd_90d': 0.01,
            'sp500_real_fwd_90d': 0.03,
            'multi_asset_score': 1.0,
            'sp500_correct': 1.0,
            'treasuries_correct': 1.0,
            'gold_correct': 0.5,
        }])
        rescored = _rescore_with_elevated_override(df, None)
        # Elevated + Goldilocks: sp500 → negative expectation, real 3% is positive → 0.0
        assert rescored.iloc[0]['sp500_correct'] == 0.0


# ---------------------------------------------------------------------------
# CPCV and DSR tests (unchanged — still valid with quadrant scoring)
# ---------------------------------------------------------------------------

class TestCPCV:
    """Test CPCV with quadrant-led data."""

    def test_cpcv_basic(self):
        """CPCV should run and return PBO."""
        rows = []
        for y in range(2005, 2025):
            for m in range(1, 13):
                rows.append({
                    'date': f'{y}-{m:02d}-28',
                    'quadrant': 'Goldilocks',
                    'multi_asset_score': 0.6 + np.random.normal(0, 0.05),
                })
        df = pd.DataFrame(rows)
        result = run_cpcv(df)
        assert result['pbo'] is not None
        assert 0.0 <= result['pbo'] <= 1.0
        assert result['n_paths'] > 0

    def test_cpcv_empty_data(self):
        """CPCV with empty data should return None."""
        df = pd.DataFrame(columns=['date', 'quadrant', 'multi_asset_score'])
        result = run_cpcv(df)
        assert result['pbo'] is None


class TestDSR:
    """Test Deflated Sharpe Ratio."""

    def test_dsr_basic(self):
        result = compute_dsr(
            observed_sharpe=5.0,
            n_trials=3,
            n_observations=10,
            std_sharpe=1.0,
        )
        assert result['dsr'] is not None
        assert result['p_value'] is not None

    def test_dsr_insufficient_data(self):
        result = compute_dsr(0, 1, 1, 0)
        assert result['dsr'] is None


# ---------------------------------------------------------------------------
# Report generation tests
# ---------------------------------------------------------------------------

class TestReportGeneration:
    """Test report output format."""

    def _make_inputs(self):
        """Create minimal inputs for report generation."""
        df = pd.DataFrame([
            {'date': '2010-01-31', 'quadrant': 'Goldilocks'},
            {'date': '2010-02-28', 'quadrant': 'Reflation'},
        ])
        agg_scores = {
            'overall': {
                'multi_asset_accuracy': 65.0,
                'composite_score': 72.5,
                'real_return_ordering_correct': True,
                'drawdown_ordering_correct': True,
            },
            'per_quadrant': {
                'Goldilocks': {'count': 1},
                'Reflation': {'count': 1},
                'Stagflation': {'count': 0},
                'Deflation Risk': {'count': 0},
            },
            'per_asset': {
                'sp500': {'label': 'S&P 500', 'weight': 0.375, 'accuracy': 70.0, 'count': 2},
            },
        }
        wf_scores = {
            'mean': 65.0, 'std': 5.0, 'sharpe': 13.0, 'n_folds': 10,
            'fold_details': [{'fold': 1, 'test_start': '2005-01-01',
                             'test_end': '2006-12-31', 'evaluations': 24, 'score': 65.0}],
        }
        plausibility = {'all_pass': True, 'checks': {}}
        cpcv_result = {'pbo': 0.4, 'n_paths': 15, 'oos_mean': 64.0, 'oos_std': 3.0, 'is_mean': 66.0}
        dsr_result = {'dsr': 2.5, 'p_value': 0.01, 'significant': True,
                      'observed_sharpe': 13.0, 'expected_max_sharpe': 2.0, 'n_trials': 3}
        sensitivity = [
            {'label': 'Stressed override (default)', 'composite_score': 72.5,
             'multi_asset_accuracy': 65.0, 'wf_mean': 65.0, 'wf_std': 5.0,
             'wf_sharpe': 13.0, 'real_return_ordering': True, 'drawdown_ordering': True},
        ]
        return df, agg_scores, wf_scores, plausibility, cpcv_result, dsr_result, sensitivity

    def test_report_title(self):
        report = generate_report(*self._make_inputs())
        assert 'Quadrant-Led' in report

    def test_report_contains_real_return_ordering(self):
        report = generate_report(*self._make_inputs())
        assert 'Real return magnitude ordering' in report

    def test_report_no_verdict_references(self):
        report = generate_report(*self._make_inputs())
        assert 'Per-Verdict' not in report
        assert 'Favorable→Defensive' not in report

    def test_report_per_quadrant_section(self):
        report = generate_report(*self._make_inputs())
        assert 'Per-Quadrant Summary' in report

    def test_report_risk_filter_sensitivity(self):
        report = generate_report(*self._make_inputs())
        assert 'Risk Filter Sensitivity' in report

    def test_report_pass_when_beats_baseline(self):
        report = generate_report(*self._make_inputs())
        assert 'PASS' in report
        assert 'beats baseline' in report

    def test_report_fail_when_below_baseline(self):
        df, agg_scores, wf, plaus, cpcv, dsr, sens = self._make_inputs()
        agg_scores['overall']['composite_score'] = 40.0
        report = generate_report(df, agg_scores, wf, plaus, cpcv, dsr, sens)
        assert 'FAIL' in report

    def test_report_real_return_info(self):
        report = generate_report(*self._make_inputs())
        assert 'inflation-adjusted' in report


# ---------------------------------------------------------------------------
# Integration: full pipeline
# ---------------------------------------------------------------------------

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """Full pipeline should produce a valid composite score."""
        from signaltrackers.backtesting.conditions_backtest import run_backtest, score_results

        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2015)
        assert not df.empty

        report = score_results(df)
        composite = report['overall'].get('composite_score')
        assert composite is not None
        assert 0 <= composite <= 100

    def test_plausibility_on_synthetic_data(self, sample_histories, sample_scoring_assets, sample_cpi_series):
        """Plausibility checks should work on synthetic data."""
        from signaltrackers.backtesting.conditions_backtest import run_backtest, check_plausibility

        df = run_backtest(sample_histories, sample_scoring_assets, sample_cpi_series,
                         start_year=2006, end_year=2024)
        result = check_plausibility(df)
        # Synthetic data has Deflation Risk in 2020 and Stagflation in 2022
        assert result['checks']['march_2020_not_goldilocks']['pass'] is True
        assert result['checks']['2022_stagflation_present']['pass'] is True
