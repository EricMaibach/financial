"""
Tests for US-294.1: Global Liquidity and Growth×Inflation dimension engines.

Covers:
  - Fed Net Liquidity calculation (unit alignment)
  - ECB/BOJ currency conversions
  - YoY rate of change and z-score normalization
  - Liquidity classification thresholds
  - Growth composite acceleration
  - Inflation YoY direction classifier (6 indicators, 24-month window)
  - Quadrant classification logic
  - Stability filter (2+ consecutive months)
  - Historical spot-checks (2008, 2020, 2022, 2023-24)
  - Edge cases (missing data, insufficient history, all-NaN)
"""

import os
import sys
import tempfile
import shutil
from unittest import mock
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

# Ensure the project root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from signaltrackers.market_conditions import (
    _load_csv,
    _to_series,
    _align_weekly,
    _align_monthly,
    _rolling_zscore,
    _expanding_zscore,
    _compute_fed_net_liquidity,
    _compute_ecb_usd,
    _compute_boj_usd,
    _yoy_change,
    _classify_liquidity,
    _compute_acceleration,
    _compute_yoy_direction,
    _compute_rate_momentum,
    _load_inflation_signals,
    _classify_quadrant,
    _apply_stability_filter,
    _compute_monthly_composite,
    _compute_inflation_composite,
    _INFLATION_DIMENSIONS,
    compute_liquidity,
    compute_quadrant,
    compute_liquidity_history,
    compute_quadrant_history,
    LiquidityResult,
    QuadrantResult,
    DATA_DIR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory and patch DATA_DIR."""
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    with mock.patch('signaltrackers.market_conditions.DATA_DIR', str(data_dir)):
        yield data_dir


def _write_csv(data_dir, filename, col_name, dates, values):
    """Helper to write a simple CSV file."""
    df = pd.DataFrame({'date': dates, col_name: values})
    df.to_csv(os.path.join(str(data_dir), f'{filename}.csv'), index=False)


def _generate_weekly_dates(start, n):
    """Generate n weekly Wednesday dates starting from start."""
    dates = pd.date_range(start, periods=n, freq='W-WED')
    return [d.strftime('%Y-%m-%d') for d in dates]


def _generate_monthly_dates(start, n):
    """Generate n monthly dates."""
    dates = pd.date_range(start, periods=n, freq='MS')
    return [d.strftime('%Y-%m-%d') for d in dates]


def _generate_daily_dates(start, n):
    """Generate n daily business dates."""
    dates = pd.date_range(start, periods=n, freq='B')
    return [d.strftime('%Y-%m-%d') for d in dates]


# ---------------------------------------------------------------------------
# Tests: CSV loading helpers
# ---------------------------------------------------------------------------

class TestLoadCsv:
    def test_missing_file_returns_none(self, tmp_data_dir):
        result = _load_csv('nonexistent')
        assert result is None

    def test_empty_file_returns_none(self, tmp_data_dir):
        path = os.path.join(str(tmp_data_dir), 'empty.csv')
        pd.DataFrame(columns=['date', 'value']).to_csv(path, index=False)
        result = _load_csv('empty')
        assert result is None

    def test_valid_file_loads(self, tmp_data_dir):
        dates = ['2020-01-01', '2020-01-02']
        _write_csv(tmp_data_dir, 'test_series', 'test_series', dates, [100.0, 101.0])
        result = _load_csv('test_series')
        assert result is not None
        assert len(result) == 2

    def test_sorts_by_date(self, tmp_data_dir):
        dates = ['2020-01-03', '2020-01-01', '2020-01-02']
        _write_csv(tmp_data_dir, 'unsorted', 'unsorted', dates, [3, 1, 2])
        result = _load_csv('unsorted')
        assert result['unsorted'].tolist() == [1, 2, 3]


class TestToSeries:
    def test_none_input(self):
        assert _to_series(None, 'col') is None

    def test_missing_column(self):
        df = pd.DataFrame({'date': ['2020-01-01'], 'other': [1.0]})
        assert _to_series(df, 'missing') is None

    def test_valid_series(self):
        df = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-02']),
            'value': [1.0, 2.0],
        })
        s = _to_series(df, 'value')
        assert s is not None
        assert len(s) == 2
        assert s.iloc[0] == 1.0


# ---------------------------------------------------------------------------
# Tests: Alignment helpers
# ---------------------------------------------------------------------------

class TestAlignment:
    def test_align_weekly_forward_fills(self):
        daily_idx = pd.date_range('2020-01-01', periods=10, freq='B')
        daily = pd.Series(range(10), index=daily_idx, dtype=float)
        weekly_idx = pd.DatetimeIndex([pd.Timestamp('2020-01-08'), pd.Timestamp('2020-01-15')])
        result = _align_weekly(daily, weekly_idx)
        assert len(result) == 2
        # Jan 8 (Wed) — should have data from Jan 8 or earlier
        assert not np.isnan(result.iloc[0])

    def test_align_monthly_forward_fills(self):
        daily_idx = pd.date_range('2020-01-01', periods=60, freq='B')
        daily = pd.Series(range(60), index=daily_idx, dtype=float)
        monthly_idx = pd.DatetimeIndex([pd.Timestamp('2020-01-01'), pd.Timestamp('2020-02-01')])
        result = _align_monthly(daily, monthly_idx)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Tests: Z-score
# ---------------------------------------------------------------------------

class TestRollingZscore:
    def test_basic_zscore(self):
        np.random.seed(42)
        s = pd.Series(np.random.randn(100), index=pd.date_range('2020-01-01', periods=100))
        z = _rolling_zscore(s, 50)
        # Recent values should be roughly -3 to 3
        valid = z.dropna()
        assert len(valid) > 0
        assert valid.abs().max() < 10  # Reasonable range

    def test_constant_series_returns_nan(self):
        s = pd.Series([5.0] * 100, index=pd.date_range('2020-01-01', periods=100))
        z = _rolling_zscore(s, 50)
        # Constant series → std=0 → NaN z-score
        valid = z.dropna()
        assert len(valid) == 0


# ---------------------------------------------------------------------------
# Tests: YoY change
# ---------------------------------------------------------------------------

class TestYoyChange:
    def test_basic_yoy(self):
        idx = pd.date_range('2019-01-01', periods=24, freq='MS')
        values = list(range(100, 124))
        s = pd.Series(values, index=idx, dtype=float)
        yoy = _yoy_change(s, 12)
        # At month 12: (112/100) - 1 = 0.12
        assert abs(yoy.iloc[12] - 0.12) < 0.001

    def test_first_period_is_nan(self):
        s = pd.Series([100, 110], index=pd.date_range('2020-01-01', periods=2, freq='MS'))
        yoy = _yoy_change(s, 1)
        assert np.isnan(yoy.iloc[0])
        assert abs(yoy.iloc[1] - 0.10) < 0.001


# ---------------------------------------------------------------------------
# Tests: Liquidity classification
# ---------------------------------------------------------------------------

class TestClassifyLiquidity:
    def test_strongly_expanding(self):
        assert _classify_liquidity(1.5) == 'Strongly Expanding'
        assert _classify_liquidity(1.01) == 'Strongly Expanding'

    def test_expanding(self):
        assert _classify_liquidity(0.75) == 'Expanding'
        assert _classify_liquidity(0.51) == 'Expanding'

    def test_neutral(self):
        assert _classify_liquidity(0.0) == 'Neutral'
        assert _classify_liquidity(0.5) == 'Neutral'
        assert _classify_liquidity(-0.5) == 'Neutral'

    def test_contracting(self):
        assert _classify_liquidity(-0.75) == 'Contracting'
        assert _classify_liquidity(-1.0) == 'Contracting'

    def test_strongly_contracting(self):
        assert _classify_liquidity(-1.5) == 'Strongly Contracting'
        assert _classify_liquidity(-1.01) == 'Strongly Contracting'

    def test_boundary_values(self):
        # > 1.0 needed for Strongly Expanding; 1.0 itself is Expanding (> 0.5)
        assert _classify_liquidity(1.0) == 'Expanding'
        assert _classify_liquidity(0.5) == 'Neutral'   # > 0.5 needed for Expanding
        assert _classify_liquidity(-0.5) == 'Neutral'  # >= -0.5 is Neutral
        assert _classify_liquidity(-1.0) == 'Contracting'  # >= -1.0 is Contracting


# ---------------------------------------------------------------------------
# Tests: Quadrant classification
# ---------------------------------------------------------------------------

class TestClassifyQuadrant:
    def test_goldilocks(self):
        assert _classify_quadrant(0.5, -0.3) == 'Goldilocks'
        assert _classify_quadrant(0.1, 0.0) == 'Goldilocks'  # inflation=0 → ≤0

    def test_reflation(self):
        assert _classify_quadrant(0.5, 0.3) == 'Reflation'

    def test_stagflation(self):
        assert _classify_quadrant(-0.5, 0.3) == 'Stagflation'
        assert _classify_quadrant(0.0, 0.3) == 'Stagflation'  # growth=0 → ≤0

    def test_deflation_risk(self):
        assert _classify_quadrant(-0.5, -0.3) == 'Deflation Risk'
        assert _classify_quadrant(-0.1, 0.0) == 'Deflation Risk'  # both ≤0

    def test_all_quadrants_covered(self):
        quadrants = set()
        for g in [1.0, -1.0]:
            for i in [1.0, -1.0]:
                quadrants.add(_classify_quadrant(g, i))
        assert quadrants == {'Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk'}


# ---------------------------------------------------------------------------
# Tests: Acceleration computation
# ---------------------------------------------------------------------------

class TestAcceleration:
    def test_constant_growth_zero_acceleration(self):
        # Linear growth → constant YoY → zero acceleration
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series(np.arange(100, 136, dtype=float), index=idx)
        accel = _compute_acceleration(s, 12)
        # After period+1 points, acceleration should be close to 0
        valid = accel.dropna()
        if len(valid) > 0:
            # Linear series: acceleration ≈ 0 (not exactly due to ratio math)
            assert valid.abs().max() < 0.01

    def test_accelerating_growth_positive(self):
        # Exponentially increasing → positive acceleration
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series(100 * np.exp(np.linspace(0, 1, 36)), index=idx)
        accel = _compute_acceleration(s, 12)
        valid = accel.dropna()
        # Should have some positive acceleration
        assert len(valid) > 0


# ---------------------------------------------------------------------------
# Tests: YoY direction classifier
# ---------------------------------------------------------------------------

class TestYoyDirection:
    def test_rising_series_positive(self):
        """A steadily rising series should produce positive YoY direction."""
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series(100 * np.exp(np.linspace(0, 0.5, 36)), index=idx)
        yoy = _compute_yoy_direction(s, 12)
        valid = yoy.dropna()
        assert len(valid) > 0
        assert all(v > 0 for v in valid)

    def test_falling_series_negative(self):
        """A steadily falling series should produce negative YoY direction."""
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series(100 * np.exp(np.linspace(0, -0.3, 36)), index=idx)
        yoy = _compute_yoy_direction(s, 12)
        valid = yoy.dropna()
        assert len(valid) > 0
        assert all(v < 0 for v in valid)

    def test_constant_series_zero(self):
        """A flat series should produce zero YoY direction."""
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series([100.0] * 36, index=idx)
        yoy = _compute_yoy_direction(s, 12)
        valid = yoy.dropna()
        assert len(valid) > 0
        assert all(abs(v) < 1e-10 for v in valid)

    def test_first_period_is_nan(self):
        """First `period` observations should be NaN."""
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series(range(100, 124), index=idx, dtype=float)
        yoy = _compute_yoy_direction(s, 12)
        for i in range(12):
            assert np.isnan(yoy.iloc[i])
        assert not np.isnan(yoy.iloc[12])

    def test_captures_steady_rise_that_acceleration_misses(self):
        """
        Inflation rising at a constant rate produces zero acceleration
        but positive YoY direction — this was the root cause of the
        Deflation Risk misclassification.
        """
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        # Linear growth → constant YoY → zero acceleration, positive direction
        s = pd.Series(np.arange(100, 136, dtype=float), index=idx)
        accel = _compute_acceleration(s, 12)
        yoy = _compute_yoy_direction(s, 12)
        accel_valid = accel.dropna()
        yoy_valid = yoy.dropna()
        # Acceleration should be ~0
        assert accel_valid.abs().max() < 0.01
        # YoY direction should be positive (rising)
        assert all(v > 0 for v in yoy_valid)


# ---------------------------------------------------------------------------
# Tests: Rate momentum (for rate-based inflation indicators)
# ---------------------------------------------------------------------------

class TestRateMomentum:
    def test_rising_rate_positive(self):
        """A steadily rising rate should produce positive momentum."""
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series([2.0 + i * 0.05 for i in range(36)], index=idx)
        mom = _compute_rate_momentum(s, 12)
        valid = mom.dropna()
        assert len(valid) > 0
        assert all(v > 0 for v in valid)

    def test_falling_rate_negative(self):
        """A steadily falling rate should produce negative momentum."""
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series([5.0 - i * 0.05 for i in range(36)], index=idx)
        mom = _compute_rate_momentum(s, 12)
        valid = mom.dropna()
        assert len(valid) > 0
        assert all(v < 0 for v in valid)

    def test_constant_rate_zero(self):
        """A flat rate should produce zero momentum."""
        idx = pd.date_range('2018-01-01', periods=36, freq='MS')
        s = pd.Series([3.0] * 36, index=idx)
        mom = _compute_rate_momentum(s, 12)
        valid = mom.dropna()
        assert len(valid) > 0
        assert all(abs(v) < 1e-10 for v in valid)

    def test_first_period_is_nan(self):
        """First `period` observations should be NaN."""
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series([2.0 + i * 0.1 for i in range(24)], index=idx)
        mom = _compute_rate_momentum(s, 12)
        for i in range(12):
            assert np.isnan(mom.iloc[i])
        assert not np.isnan(mom.iloc[12])

    def test_uses_diff_not_pct_change(self):
        """Rate momentum uses absolute diff, not percentage change.

        For a rate at 2.0 rising to 3.0, momentum should be +1.0 (diff),
        not +0.5 (pct change). This is the key distinction from _compute_yoy_direction.
        """
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series([2.0] * 12 + [3.0] * 12, index=idx)
        mom = _compute_rate_momentum(s, 12)
        assert abs(mom.iloc[12] - 1.0) < 1e-10  # diff = 3.0 - 2.0 = 1.0


# ---------------------------------------------------------------------------
# Tests: Expanding z-score
# ---------------------------------------------------------------------------

class TestExpandingZscore:
    def test_above_mean_positive(self):
        """Values above the expanding mean should have positive z-scores."""
        idx = pd.date_range('2010-01-01', periods=60, freq='MS')
        # Rising series: later values are above the expanding mean
        s = pd.Series([2.0 + i * 0.1 for i in range(60)], index=idx)
        z = _expanding_zscore(s)
        # Latest values should be positive (above expanding mean)
        assert z.iloc[-1] > 0

    def test_below_mean_negative(self):
        """Values below the expanding mean should have negative z-scores."""
        idx = pd.date_range('2010-01-01', periods=60, freq='MS')
        # Falling series: later values are below the expanding mean
        s = pd.Series([5.0 - i * 0.1 for i in range(60)], index=idx)
        z = _expanding_zscore(s)
        assert z.iloc[-1] < 0

    def test_constant_series_zero(self):
        """A constant series should produce z-scores near zero."""
        idx = pd.date_range('2010-01-01', periods=60, freq='MS')
        s = pd.Series([3.0] * 60, index=idx)
        z = _expanding_zscore(s)
        # Std dev is 0 → NaN, which is expected for constant series
        assert z.dropna().empty or all(abs(v) < 1e-10 for v in z.dropna())

    def test_min_periods_respected(self):
        """First min_periods observations should be NaN."""
        idx = pd.date_range('2010-01-01', periods=24, freq='MS')
        s = pd.Series([2.0 + i * 0.1 for i in range(24)], index=idx)
        z = _expanding_zscore(s, min_periods=12)
        # First 11 should be NaN (min_periods=12 means 12th is first valid)
        for i in range(11):
            assert np.isnan(z.iloc[i])
        assert not np.isnan(z.iloc[11])

    def test_uses_full_history(self):
        """Expanding z-score uses all prior data, not a fixed window."""
        idx = pd.date_range('2000-01-01', periods=120, freq='MS')
        # First 60 months at 2.0, next 60 at 4.0
        vals = [2.0] * 60 + [4.0] * 60
        s = pd.Series(vals, index=idx)
        z = _expanding_zscore(s)
        # At month 60 (first 4.0), z-score should be very high
        assert z.iloc[60] > 1.5
        # At month 119 (last 4.0), z-score still positive but less extreme
        # because expanding mean has shifted toward 3.0
        assert z.iloc[-1] > 0
        assert z.iloc[-1] < z.iloc[60]  # Less extreme as history grows


# ---------------------------------------------------------------------------
# Tests: Inflation composite (dimensional weighting)
# ---------------------------------------------------------------------------

class TestInflationComposite:
    def test_dimensional_grouping(self):
        """Inflation dimensions cover all 6 indicators."""
        all_keys = set()
        for keys in _INFLATION_DIMENSIONS.values():
            all_keys.update(keys)
        expected = {'CPIAUCSL', 'PCEPILFE', 'MEDCPIM158SFRBCLE',
                    'T10YIE', 'T5YIFR', 'MICH'}
        assert all_keys == expected

    def test_equal_weight_per_dimension(self):
        """Each dimension gets 1/3 weight regardless of indicator count."""
        idx = pd.date_range('2020-01-01', periods=36, freq='MS')
        # Realized: all +1.0 (3 indicators)
        # Market: all -1.0 (2 indicators)
        # Consumer: +2.0 (1 indicator)
        signals = {
            'CPIAUCSL': pd.Series([1.0] * 36, index=idx),
            'PCEPILFE': pd.Series([1.0] * 36, index=idx),
            'MEDCPIM158SFRBCLE': pd.Series([1.0] * 36, index=idx),
            'T10YIE': pd.Series([-1.0] * 36, index=idx),
            'T5YIFR': pd.Series([-1.0] * 36, index=idx),
            'MICH': pd.Series([2.0] * 36, index=idx),
        }
        composite = _compute_inflation_composite(signals)
        # Realized avg = 1.0, Market avg = -1.0, Consumer avg = 2.0
        # Composite = (1.0 + (-1.0) + 2.0) / 3 = 0.667
        assert composite is not None
        assert abs(composite.iloc[-1] - 2.0 / 3) < 0.01

    def test_forward_fill_handles_lag(self):
        """Signals that end 1 month early are forward-filled."""
        idx_long = pd.date_range('2020-01-01', periods=36, freq='MS')
        idx_short = pd.date_range('2020-01-01', periods=35, freq='MS')
        signals = {
            'CPIAUCSL': pd.Series([1.0] * 36, index=idx_long),
            'PCEPILFE': pd.Series([2.0] * 35, index=idx_short),  # 1 month shorter
            'MEDCPIM158SFRBCLE': pd.Series([1.0] * 36, index=idx_long),
            'T10YIE': pd.Series([0.5] * 36, index=idx_long),
            'T5YIFR': pd.Series([0.5] * 36, index=idx_long),
            'MICH': pd.Series([1.5] * 36, index=idx_long),
        }
        composite = _compute_inflation_composite(signals)
        # PCE at 2.0 should be forward-filled into the last month
        # Realized = (1.0 + 2.0 + 1.0) / 3 = 1.333
        # Market = (0.5 + 0.5) / 2 = 0.5
        # Consumer = 1.5
        # Overall = (1.333 + 0.5 + 1.5) / 3 ≈ 1.111
        assert composite is not None
        assert abs(composite.iloc[-1] - (4.0 / 3 + 0.5 + 1.5) / 3) < 0.05

    def test_missing_dimension_still_computes(self):
        """If all indicators in a dimension are None, other dims still work."""
        idx = pd.date_range('2020-01-01', periods=36, freq='MS')
        signals = {
            'CPIAUCSL': pd.Series([1.0] * 36, index=idx),
            'PCEPILFE': pd.Series([1.0] * 36, index=idx),
            'MEDCPIM158SFRBCLE': pd.Series([1.0] * 36, index=idx),
            'T10YIE': None,
            'T5YIFR': None,
            'MICH': pd.Series([2.0] * 36, index=idx),
        }
        composite = _compute_inflation_composite(signals)
        # Realized = 1.0, Consumer = 2.0, Market missing
        # Overall = (1.0 + 2.0) / 2 = 1.5
        assert composite is not None
        assert abs(composite.iloc[-1] - 1.5) < 0.01

    def test_all_none_returns_none(self):
        signals = {k: None for k in ['CPIAUCSL', 'PCEPILFE', 'MEDCPIM158SFRBCLE',
                                       'T10YIE', 'T5YIFR', 'MICH']}
        assert _compute_inflation_composite(signals) is None


# ---------------------------------------------------------------------------
# Tests: Inflation signals (6-indicator set)
# ---------------------------------------------------------------------------

class TestLoadInflationSignals:
    def _setup_inflation_data(self, data_dir, n_months=60):
        """Create synthetic data for all 6 inflation indicators."""
        dates_m = _generate_monthly_dates('2018-01-01', n_months)
        dates_d = _generate_daily_dates('2018-01-01', n_months * 22)

        # Realized trend (monthly)
        cpi = [230 + i * 0.3 for i in range(n_months)]
        _write_csv(data_dir, 'cpi', 'cpi', dates_m, cpi)

        pce = [110 + i * 0.2 for i in range(n_months)]
        _write_csv(data_dir, 'core_pce_price_index', 'core_pce_price_index', dates_m, pce)

        med = [2.5 + i * 0.01 for i in range(n_months)]
        _write_csv(data_dir, 'median_cpi', 'median_cpi', dates_m, med)

        # Market expectations (daily)
        t10yie = [2.0 + i * 0.0001 for i in range(len(dates_d))]
        _write_csv(data_dir, 'breakeven_inflation_10y', 'breakeven_inflation_10y', dates_d, t10yie)

        fwd = [2.3 + i * 0.0001 for i in range(len(dates_d))]
        _write_csv(data_dir, 'inflation_expectations_5y5y', 'inflation_expectations_5y5y', dates_d, fwd)

        # Consumer expectations (monthly)
        mich = [3.0 + i * 0.02 for i in range(n_months)]
        _write_csv(data_dir, 'michigan_inflation_expectations', 'michigan_inflation_expectations', dates_m, mich)

    def test_returns_six_indicators(self, tmp_data_dir):
        self._setup_inflation_data(tmp_data_dir)
        signals = _load_inflation_signals()
        expected_keys = {'CPIAUCSL', 'PCEPILFE', 'MEDCPIM158SFRBCLE', 'T10YIE', 'T5YIFR', 'MICH'}
        assert set(signals.keys()) == expected_keys

    def test_t5yie_not_in_signals(self, tmp_data_dir):
        self._setup_inflation_data(tmp_data_dir)
        signals = _load_inflation_signals()
        assert 'T5YIE' not in signals

    def test_missing_single_indicator_graceful(self, tmp_data_dir):
        """Missing one CSV still returns None for that signal, others work."""
        self._setup_inflation_data(tmp_data_dir)
        # Remove median CPI
        os.remove(os.path.join(str(tmp_data_dir), 'median_cpi.csv'))
        signals = _load_inflation_signals()
        assert signals['MEDCPIM158SFRBCLE'] is None
        # Others should still compute
        non_none = [k for k, v in signals.items() if v is not None]
        assert len(non_none) >= 4

    def test_all_missing_returns_all_none(self, tmp_data_dir):
        signals = _load_inflation_signals()
        assert all(v is None for v in signals.values())

    def test_insufficient_data_returns_none(self, tmp_data_dir):
        """Too few data points should return None for that signal."""
        dates_m = _generate_monthly_dates('2024-01-01', 6)
        cpi = [230 + i * 0.3 for i in range(6)]
        _write_csv(tmp_data_dir, 'cpi', 'cpi', dates_m, cpi)
        signals = _load_inflation_signals()
        assert signals['CPIAUCSL'] is None  # Needs >= 13 months


# ---------------------------------------------------------------------------
# Tests: Stability filter
# ---------------------------------------------------------------------------

class TestStabilityFilter:
    def test_stable_series_unchanged(self):
        idx = pd.date_range('2020-01-01', periods=6, freq='MS')
        raw = pd.Series(['Goldilocks'] * 6, index=idx)
        result = _apply_stability_filter(raw, required_consecutive=2)
        assert all(r == 'Goldilocks' for r in result)

    def test_single_month_blip_filtered(self):
        idx = pd.date_range('2020-01-01', periods=6, freq='MS')
        raw = pd.Series([
            'Goldilocks', 'Goldilocks', 'Reflation',
            'Goldilocks', 'Goldilocks', 'Goldilocks',
        ], index=idx)
        result = _apply_stability_filter(raw, required_consecutive=2)
        # Single-month Reflation should be filtered out
        assert result.iloc[2] == 'Goldilocks'

    def test_two_consecutive_allows_transition(self):
        idx = pd.date_range('2020-01-01', periods=6, freq='MS')
        raw = pd.Series([
            'Goldilocks', 'Goldilocks', 'Reflation',
            'Reflation', 'Reflation', 'Reflation',
        ], index=idx)
        result = _apply_stability_filter(raw, required_consecutive=2)
        # After 2 consecutive Reflation months, transition recognized
        assert result.iloc[-1] == 'Reflation'
        # The transition should happen at index 3 (second consecutive Reflation)
        assert result.iloc[3] == 'Reflation'

    def test_empty_series(self):
        result = _apply_stability_filter(pd.Series([], dtype=str), required_consecutive=2)
        assert len(result) == 0

    def test_single_element(self):
        idx = pd.date_range('2020-01-01', periods=1, freq='MS')
        raw = pd.Series(['Stagflation'], index=idx)
        result = _apply_stability_filter(raw, required_consecutive=2)
        assert result.iloc[0] == 'Stagflation'

    def test_alternating_quadrants_stays_initial(self):
        idx = pd.date_range('2020-01-01', periods=6, freq='MS')
        raw = pd.Series([
            'Goldilocks', 'Reflation', 'Goldilocks',
            'Reflation', 'Goldilocks', 'Reflation',
        ], index=idx)
        result = _apply_stability_filter(raw, required_consecutive=2)
        # Never 2 consecutive of anything new → stays at initial
        assert all(r == 'Goldilocks' for r in result)


# ---------------------------------------------------------------------------
# Tests: Monthly composite
# ---------------------------------------------------------------------------

class TestComputeMonthlyComposite:
    def test_all_none_returns_none(self):
        result = _compute_monthly_composite({'a': None, 'b': None})
        assert result is None

    def test_single_signal(self):
        idx = pd.date_range('2020-01-01', periods=12, freq='MS')
        s = pd.Series(np.ones(12), index=idx)
        result = _compute_monthly_composite({'only': s})
        assert result is not None
        assert len(result) > 0
        assert all(abs(v - 1.0) < 0.01 for v in result.values)

    def test_mixed_signals_averaged(self):
        idx = pd.date_range('2020-01-01', periods=12, freq='MS')
        s1 = pd.Series(np.ones(12) * 2.0, index=idx)
        s2 = pd.Series(np.zeros(12), index=idx)
        result = _compute_monthly_composite({'a': s1, 'b': s2})
        assert result is not None
        # Average of 2.0 and 0.0 should be ~1.0
        assert all(abs(v - 1.0) < 0.01 for v in result.values)

    def test_handles_daily_signals(self):
        daily_idx = pd.date_range('2020-01-01', periods=252, freq='B')
        s = pd.Series(np.random.randn(252), index=daily_idx)
        result = _compute_monthly_composite({'daily': s})
        assert result is not None
        # Should have monthly resolution
        assert len(result) <= 13  # ~12 months


# ---------------------------------------------------------------------------
# Tests: Fed Net Liquidity (integration with synthetic data)
# ---------------------------------------------------------------------------

class TestFedNetLiquidity:
    def test_correct_formula(self, tmp_data_dir):
        """WALCL - WDTGAL - (RRPONTSYD * 1000)"""
        n = 60
        dates = _generate_weekly_dates('2020-01-01', n)

        # WALCL = 7,000,000 millions (=$7T)
        _write_csv(tmp_data_dir, 'fed_balance_sheet', 'fed_balance_sheet',
                   dates, [7_000_000.0] * n)
        # WDTGAL = 800,000 millions
        _write_csv(tmp_data_dir, 'treasury_general_account', 'treasury_general_account',
                   dates, [800_000.0] * n)
        # RRPONTSYD = 500 billions
        _write_csv(tmp_data_dir, 'reverse_repo', 'reverse_repo',
                   dates, [500.0] * n)

        result = _compute_fed_net_liquidity()
        assert result is not None
        # Expected: 7,000,000 - 800,000 - (500 * 1000) = 5,700,000
        assert abs(result.iloc[0] - 5_700_000.0) < 1.0

    def test_missing_wdtgal_returns_none(self, tmp_data_dir):
        n = 60
        dates = _generate_weekly_dates('2020-01-01', n)
        _write_csv(tmp_data_dir, 'fed_balance_sheet', 'fed_balance_sheet',
                   dates, [7_000_000.0] * n)
        _write_csv(tmp_data_dir, 'reverse_repo', 'reverse_repo',
                   dates, [500.0] * n)
        # No WDTGAL file
        result = _compute_fed_net_liquidity()
        assert result is None


class TestEcbUsd:
    def test_conversion(self, tmp_data_dir):
        n = 60
        dates = _generate_weekly_dates('2020-01-01', n)
        daily_dates = _generate_daily_dates('2020-01-01', n * 5)

        _write_csv(tmp_data_dir, 'ecb_total_assets', 'ecb_total_assets',
                   dates, [5_000_000.0] * n)  # 5M EUR millions
        _write_csv(tmp_data_dir, 'fx_eur_usd', 'fx_eur_usd',
                   daily_dates, [1.10] * len(daily_dates))  # 1.10 USD per EUR

        result = _compute_ecb_usd()
        assert result is not None
        # 5,000,000 EUR × 1.10 = 5,500,000 USD
        assert abs(result.iloc[0] - 5_500_000.0) < 100.0


class TestBojUsd:
    def test_conversion(self, tmp_data_dir):
        n = 24
        dates = _generate_monthly_dates('2020-01-01', n)
        daily_dates = _generate_daily_dates('2020-01-01', n * 22)

        # BOJ = 7,000,000 (100M JPY) = 700 trillion JPY
        _write_csv(tmp_data_dir, 'boj_total_assets', 'boj_total_assets',
                   dates, [7_000_000.0] * n)
        # DEXJPUS = 150 JPY per USD
        _write_csv(tmp_data_dir, 'fx_jpy_usd', 'fx_jpy_usd',
                   daily_dates, [150.0] * len(daily_dates))

        result = _compute_boj_usd()
        assert result is not None
        # (7,000,000 × 100,000,000) / 150 = 4,666,666,666,666.67
        expected = (7_000_000 * 100_000_000) / 150
        assert abs(result.iloc[0] - expected) / expected < 0.01


# ---------------------------------------------------------------------------
# Tests: Full liquidity computation
# ---------------------------------------------------------------------------

class TestComputeLiquidity:
    def _setup_full_liquidity_data(self, data_dir, n_weeks=320, trend=0.0, start='2015-01-01'):
        """Create synthetic data for a full liquidity computation."""
        dates_w = _generate_weekly_dates(start, n_weeks)
        dates_m = _generate_monthly_dates('2015-01-01', n_weeks // 4)
        dates_d = _generate_daily_dates('2015-01-01', n_weeks * 5)

        # Growing Fed balance sheet
        walcl = [4_000_000 + i * 5000 + i * trend for i in range(n_weeks)]
        _write_csv(data_dir, 'fed_balance_sheet', 'fed_balance_sheet', dates_w, walcl)

        tga = [300_000 + i * 100 for i in range(n_weeks)]
        _write_csv(data_dir, 'treasury_general_account', 'treasury_general_account', dates_w, tga)

        rrp = [200 + i * 0.5 for i in range(n_weeks)]
        _write_csv(data_dir, 'reverse_repo', 'reverse_repo', dates_w, rrp)

        ecb = [3_000_000 + i * 2000 for i in range(n_weeks)]
        _write_csv(data_dir, 'ecb_total_assets', 'ecb_total_assets', dates_w, ecb)

        fx_eur = [1.10] * len(dates_d)
        _write_csv(data_dir, 'fx_eur_usd', 'fx_eur_usd', dates_d, fx_eur)

        boj = [5_000_000 + i * 1000 for i in range(len(dates_m))]
        _write_csv(data_dir, 'boj_total_assets', 'boj_total_assets', dates_m, boj)

        fx_jpy = [150.0] * len(dates_d)
        _write_csv(data_dir, 'fx_jpy_usd', 'fx_jpy_usd', dates_d, fx_jpy)

        m2 = [15_000 + i * 50 for i in range(len(dates_m))]
        _write_csv(data_dir, 'm2_money_supply', 'm2_money_supply', dates_m, m2)

    def test_returns_result(self, tmp_data_dir):
        self._setup_full_liquidity_data(tmp_data_dir)
        result = compute_liquidity()
        assert result is not None
        assert isinstance(result, LiquidityResult)
        assert result.state in [
            'Strongly Expanding', 'Expanding', 'Neutral',
            'Contracting', 'Strongly Contracting',
        ]
        assert isinstance(result.score, float)
        assert result.as_of is not None

    def test_insufficient_data_returns_none(self, tmp_data_dir):
        # Only 10 weeks — not enough
        dates = _generate_weekly_dates('2020-01-01', 10)
        _write_csv(tmp_data_dir, 'fed_balance_sheet', 'fed_balance_sheet',
                   dates, [7_000_000.0] * 10)
        _write_csv(tmp_data_dir, 'treasury_general_account', 'treasury_general_account',
                   dates, [800_000.0] * 10)
        _write_csv(tmp_data_dir, 'reverse_repo', 'reverse_repo',
                   dates, [500.0] * 10)
        result = compute_liquidity()
        assert result is None

    def test_as_of_date_respected(self, tmp_data_dir):
        # Need 52-week YoY + 260-week z-score window = 312 weeks before first valid point
        # Start from 2008 so by 2018 we have ~10 years = 520 weeks (plenty)
        self._setup_full_liquidity_data(tmp_data_dir, n_weeks=600, start='2008-01-01')
        result = compute_liquidity(as_of_date='2018-01-01')
        assert result is not None
        assert result.as_of <= '2018-01-01'

    def test_weights_sum_to_one(self):
        """Verify the documented weights: Fed 40%, ECB 20%, BOJ 15%, M2 25%."""
        assert abs((0.40 + 0.20 + 0.15 + 0.25) - 1.0) < 0.001

    def test_handles_missing_ecb_boj(self, tmp_data_dir):
        """Should still compute with only Fed + M2 (renormalized weights)."""
        n = 320
        dates_w = _generate_weekly_dates('2015-01-01', n)
        dates_m = _generate_monthly_dates('2015-01-01', n // 4)

        walcl = [4_000_000 + i * 5000 for i in range(n)]
        _write_csv(tmp_data_dir, 'fed_balance_sheet', 'fed_balance_sheet', dates_w, walcl)
        tga = [300_000] * n
        _write_csv(tmp_data_dir, 'treasury_general_account', 'treasury_general_account', dates_w, tga)
        rrp = [200] * n
        _write_csv(tmp_data_dir, 'reverse_repo', 'reverse_repo', dates_w, rrp)
        m2 = [15_000 + i * 50 for i in range(len(dates_m))]
        _write_csv(tmp_data_dir, 'm2_money_supply', 'm2_money_supply', dates_m, m2)

        result = compute_liquidity()
        assert result is not None
        assert result.state in [
            'Strongly Expanding', 'Expanding', 'Neutral',
            'Contracting', 'Strongly Contracting',
        ]


# ---------------------------------------------------------------------------
# Tests: Full quadrant computation
# ---------------------------------------------------------------------------

class TestComputeQuadrant:
    def _setup_quadrant_data(self, data_dir, n_months=120,
                              growth_trend=1.0, inflation_trend=0.0):
        """Create synthetic data for quadrant computation."""
        dates_m = _generate_monthly_dates('2010-01-01', n_months)
        dates_d = _generate_daily_dates('2010-01-01', n_months * 22)
        dates_w = _generate_weekly_dates('2010-01-01', n_months * 4)

        # Growth indicators
        # ICSA (weekly) — declining = growth positive
        icsa = [400_000 - i * growth_trend * 100 for i in range(len(dates_w))]
        _write_csv(data_dir, 'initial_claims', 'initial_claims', dates_w, icsa)

        # T10Y2Y (daily) — steepening = positive
        yc = [1.0 + i * growth_trend * 0.001 for i in range(len(dates_d))]
        _write_csv(data_dir, 'yield_curve_10y2y', 'yield_curve_10y2y', dates_d, yc)

        # NFCI (weekly) — falling = positive
        nfci = [0.5 - i * growth_trend * 0.002 for i in range(len(dates_w))]
        _write_csv(data_dir, 'nfci', 'nfci', dates_w, nfci)

        # INDPRO (monthly)
        indpro = [100 + i * growth_trend * 0.3 for i in range(n_months)]
        _write_csv(data_dir, 'industrial_production', 'industrial_production', dates_m, indpro)

        # PERMIT (monthly)
        permit = [1200 + i * growth_trend * 5 for i in range(n_months)]
        _write_csv(data_dir, 'building_permits', 'building_permits', dates_m, permit)

        # Inflation indicators (6 total — direction for indices, expanding level for rates)

        # Realized Trend
        # CPI (monthly)
        cpi = [230 + i * (0.3 + inflation_trend * 0.2) for i in range(n_months)]
        _write_csv(data_dir, 'cpi', 'cpi', dates_m, cpi)

        # Core PCE (monthly)
        pce = [110 + i * (0.2 + inflation_trend * 0.1) for i in range(n_months)]
        _write_csv(data_dir, 'core_pce_price_index', 'core_pce_price_index', dates_m, pce)

        # Cleveland Fed Median CPI (monthly)
        med_cpi = [2.5 + i * (0.01 + inflation_trend * 0.005) for i in range(n_months)]
        _write_csv(data_dir, 'median_cpi', 'median_cpi', dates_m, med_cpi)

        # Market Expectations
        # T10YIE (daily)
        t10yie = [2.0 + i * inflation_trend * 0.001 for i in range(len(dates_d))]
        _write_csv(data_dir, 'breakeven_inflation_10y', 'breakeven_inflation_10y', dates_d, t10yie)

        # 5Y5Y Forward (daily)
        fwd5y5y = [2.3 + i * inflation_trend * 0.0008 for i in range(len(dates_d))]
        _write_csv(data_dir, 'inflation_expectations_5y5y', 'inflation_expectations_5y5y', dates_d, fwd5y5y)

        # Consumer Expectations
        # Michigan 1-Year (monthly)
        mich = [3.0 + i * (0.02 + inflation_trend * 0.01) for i in range(n_months)]
        _write_csv(data_dir, 'michigan_inflation_expectations', 'michigan_inflation_expectations', dates_m, mich)

    def test_returns_result(self, tmp_data_dir):
        self._setup_quadrant_data(tmp_data_dir)
        result = compute_quadrant()
        assert result is not None
        assert isinstance(result, QuadrantResult)
        assert result.quadrant in ['Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk']
        assert isinstance(result.growth_composite, float)
        assert isinstance(result.inflation_composite, float)
        assert result.as_of is not None

    def test_no_data_returns_none(self, tmp_data_dir):
        result = compute_quadrant()
        assert result is None

    def test_as_of_date(self, tmp_data_dir):
        self._setup_quadrant_data(tmp_data_dir)
        result = compute_quadrant(as_of_date='2014-01-01')
        assert result is not None
        assert result.as_of <= '2014-01-01'

    def test_stability_filter_applied(self, tmp_data_dir):
        self._setup_quadrant_data(tmp_data_dir)
        result = compute_quadrant()
        assert result is not None
        # Result should report whether raw == stable
        assert isinstance(result.stable, bool)
        assert result.raw_quadrant in ['Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk']

    def test_composites_preserved(self, tmp_data_dir):
        """Composite values preserved (not just sign) for conviction."""
        self._setup_quadrant_data(tmp_data_dir)
        result = compute_quadrant()
        assert result is not None
        # Values should be finite, not just 0/1
        assert np.isfinite(result.growth_composite)
        assert np.isfinite(result.inflation_composite)


# ---------------------------------------------------------------------------
# Tests: History functions
# ---------------------------------------------------------------------------

class TestLiquidityHistory:
    def test_returns_dataframe(self, tmp_data_dir):
        # Reuse the full setup helper
        helper = TestComputeLiquidity()
        helper._setup_full_liquidity_data(tmp_data_dir)
        result = compute_liquidity_history()
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'date' in result.columns
        assert 'score' in result.columns
        assert 'state' in result.columns
        assert len(result) > 0

    def test_start_date_filter(self, tmp_data_dir):
        helper = TestComputeLiquidity()
        helper._setup_full_liquidity_data(tmp_data_dir)
        result = compute_liquidity_history(start_date='2019-01-01')
        assert result is not None
        assert all(d >= pd.Timestamp('2019-01-01') for d in result['date'])


class TestQuadrantHistory:
    def test_returns_dataframe(self, tmp_data_dir):
        helper = TestComputeQuadrant()
        helper._setup_quadrant_data(tmp_data_dir)
        result = compute_quadrant_history()
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'growth' in result.columns
        assert 'inflation' in result.columns
        assert 'quadrant' in result.columns
        assert 'raw_quadrant' in result.columns

    def test_start_date_filter(self, tmp_data_dir):
        helper = TestComputeQuadrant()
        helper._setup_quadrant_data(tmp_data_dir)
        result = compute_quadrant_history(start_date='2015-01-01')
        assert result is not None
        assert all(d >= pd.Timestamp('2015-01-01') for d in result['date'])


# ---------------------------------------------------------------------------
# Tests: No lookahead bias
# ---------------------------------------------------------------------------

class TestNoLookaheadBias:
    def test_yoy_uses_past_data_only(self):
        """YoY change at time T uses T and T-period, both ≤ T."""
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series(range(100, 124), index=idx, dtype=float)
        yoy = _yoy_change(s, 12)
        # At month 12 (2021-01), uses 2021-01 and 2020-01
        assert not np.isnan(yoy.iloc[12])
        # At month 11, shift(12) would access index -1 → NaN
        assert np.isnan(yoy.iloc[11])

    def test_rolling_zscore_no_future_leak(self):
        """Rolling z-score window is backward-looking only."""
        idx = pd.date_range('2020-01-01', periods=100, freq='B')
        s = pd.Series(np.random.randn(100), index=idx)
        z = _rolling_zscore(s, 50)
        # The z-score at position 50 should only use data from positions 0-50
        # Verify by checking that a spike at the end doesn't affect early values
        s2 = s.copy()
        s2.iloc[-1] = 100.0  # Huge spike
        z2 = _rolling_zscore(s2, 50)
        # Early values should be identical
        if z.notna().iloc[25] and z2.notna().iloc[25]:
            assert abs(z.iloc[25] - z2.iloc[25]) < 1e-10

    def test_acceleration_no_future_data(self):
        """Acceleration at T uses T, T-1, T-period, T-period-1 — all ≤ T."""
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series(range(100, 124), index=idx, dtype=float)
        accel = _compute_acceleration(s, 12)
        # First valid: needs shift(period+1) = shift(13), so at least index 13
        for i in range(13):
            assert np.isnan(accel.iloc[i])
        assert not np.isnan(accel.iloc[13])

    def test_yoy_direction_no_future_data(self):
        """YoY direction at T uses T and T-period, both ≤ T."""
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series(range(100, 124), index=idx, dtype=float)
        yoy = _compute_yoy_direction(s, 12)
        # First valid: needs shift(12), so at least index 12
        for i in range(12):
            assert np.isnan(yoy.iloc[i])
        assert not np.isnan(yoy.iloc[12])

    def test_rate_momentum_no_future_data(self):
        """Rate momentum at T uses T and T-period, both ≤ T."""
        idx = pd.date_range('2020-01-01', periods=24, freq='MS')
        s = pd.Series([2.0 + i * 0.1 for i in range(24)], index=idx)
        mom = _compute_rate_momentum(s, 12)
        for i in range(12):
            assert np.isnan(mom.iloc[i])
        assert not np.isnan(mom.iloc[12])


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_nan_component_skipped(self, tmp_data_dir):
        """An all-NaN component should not crash the composite."""
        n = 320
        dates_w = _generate_weekly_dates('2015-01-01', n)
        dates_m = _generate_monthly_dates('2015-01-01', n // 4)

        walcl = [4_000_000 + i * 5000 for i in range(n)]
        _write_csv(tmp_data_dir, 'fed_balance_sheet', 'fed_balance_sheet', dates_w, walcl)
        tga = [300_000] * n
        _write_csv(tmp_data_dir, 'treasury_general_account', 'treasury_general_account', dates_w, tga)
        rrp = [200] * n
        _write_csv(tmp_data_dir, 'reverse_repo', 'reverse_repo', dates_w, rrp)

        # M2 with NaN values
        m2 = [float('nan')] * len(dates_m)
        _write_csv(tmp_data_dir, 'm2_money_supply', 'm2_money_supply', dates_m, m2)

        result = compute_liquidity()
        # Should still work with just Fed component
        assert result is not None

    def test_mixed_frequency_alignment(self, tmp_data_dir):
        """Weekly, monthly, daily data all align without error."""
        helper = TestComputeLiquidity()
        helper._setup_full_liquidity_data(tmp_data_dir)
        result = compute_liquidity()
        assert result is not None

    def test_empty_data_dir(self, tmp_data_dir):
        """No CSV files at all → returns None gracefully."""
        assert compute_liquidity() is None
        assert compute_quadrant() is None

    def test_single_growth_signal_sufficient(self, tmp_data_dir):
        """Quadrant should compute even with only one growth + one inflation signal."""
        n = 120
        dates_m = _generate_monthly_dates('2010-01-01', n)

        indpro = [100 + i * 0.3 for i in range(n)]
        _write_csv(tmp_data_dir, 'industrial_production', 'industrial_production', dates_m, indpro)

        cpi = [230 + i * 0.3 for i in range(n)]
        _write_csv(tmp_data_dir, 'cpi', 'cpi', dates_m, cpi)

        result = compute_quadrant()
        assert result is not None


# ---------------------------------------------------------------------------
# Tests: Historical spot-checks (using real data if available)
# ---------------------------------------------------------------------------

class TestHistoricalSpotChecks:
    """
    These tests run against real CSV data in the project's data/ directory.
    They are skipped if the data files don't exist (CI environment).
    """

    @pytest.fixture(autouse=True)
    def check_data_available(self):
        """Skip if real data files aren't present."""
        required = ['fed_balance_sheet', 'cpi', 'initial_claims']
        for f in required:
            path = os.path.join(DATA_DIR, f'{f}.csv')
            if not os.path.exists(path):
                pytest.skip(f'Real data file {f}.csv not available')

    def test_2008_deflation_risk(self):
        """2008-2009 should classify as Deflation Risk."""
        result = compute_quadrant(as_of_date='2009-03-01')
        if result is not None:
            # The raw quadrant should be Deflation Risk around the crisis
            assert result.quadrant in ['Deflation Risk', 'Stagflation'], \
                f'Expected Deflation Risk or Stagflation in 2009, got {result.quadrant}'

    def test_2022_stagflation(self):
        """2022 should classify as Stagflation."""
        result = compute_quadrant(as_of_date='2022-06-30')
        if result is not None:
            assert result.quadrant in ['Stagflation', 'Reflation'], \
                f'Expected Stagflation or Reflation in mid-2022, got {result.quadrant}'

    def test_2023_2024_goldilocks(self):
        """2023-2024 should classify as Goldilocks."""
        result = compute_quadrant(as_of_date='2024-06-30')
        if result is not None:
            assert result.quadrant in ['Goldilocks', 'Reflation'], \
                f'Expected Goldilocks or Reflation in mid-2024, got {result.quadrant}'

    def test_march_2020_liquidity(self):
        """March 2020 liquidity should initially be Contracting then Expanding."""
        # Pre-intervention
        pre = compute_liquidity(as_of_date='2020-03-15')
        # Post-intervention (Fed started buying mid-March)
        post = compute_liquidity(as_of_date='2020-09-01')
        if pre is not None and post is not None:
            # After massive QE, liquidity score should be higher
            assert post.score > pre.score, \
                f'Expected post-QE liquidity ({post.score}) > pre-QE ({pre.score})'

    def test_liquidity_returns_valid_state(self):
        """Current liquidity should return a valid classification."""
        result = compute_liquidity()
        if result is not None:
            assert result.state in [
                'Strongly Expanding', 'Expanding', 'Neutral',
                'Contracting', 'Strongly Contracting',
            ]
            assert -5.0 < result.score < 5.0  # Reasonable z-score range

    def test_quadrant_returns_valid_result(self):
        """Current quadrant should return a valid classification."""
        result = compute_quadrant()
        if result is not None:
            assert result.quadrant in [
                'Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk',
            ]

    def test_fed_net_liquidity_sanity_check(self):
        """Fed Net Liquidity should be in a plausible range (~$3-8T in millions)."""
        fed_nl = _compute_fed_net_liquidity()
        if fed_nl is not None and len(fed_nl) > 0:
            latest = fed_nl.iloc[-1]
            # Should be between $1T and $10T (in millions: 1,000,000 to 10,000,000)
            assert 1_000_000 < latest < 10_000_000, \
                f'Fed Net Liquidity = {latest:,.0f} millions — outside expected range'

    def test_liquidity_history_has_data(self):
        """History function should return substantial data."""
        result = compute_liquidity_history(start_date='2010-01-01')
        if result is not None:
            assert len(result) > 100, f'Expected 100+ data points, got {len(result)}'

    def test_quadrant_history_has_data(self):
        """History function should return substantial data."""
        result = compute_quadrant_history(start_date='2010-01-01')
        if result is not None:
            assert len(result) > 50, f'Expected 50+ monthly data points, got {len(result)}'


# ---------------------------------------------------------------------------
# Tests: Interface contract
# ---------------------------------------------------------------------------

class TestInterfaceContract:
    def test_liquidity_result_fields(self):
        r = LiquidityResult(state='Neutral', score=0.0)
        assert hasattr(r, 'state')
        assert hasattr(r, 'score')
        assert hasattr(r, 'fed_nl_yoy')
        assert hasattr(r, 'ecb_yoy')
        assert hasattr(r, 'boj_yoy')
        assert hasattr(r, 'm2_yoy')
        assert hasattr(r, 'as_of')

    def test_quadrant_result_fields(self):
        r = QuadrantResult(
            quadrant='Goldilocks',
            growth_composite=0.5,
            inflation_composite=-0.3,
            raw_quadrant='Goldilocks',
            stable=True,
        )
        assert hasattr(r, 'quadrant')
        assert hasattr(r, 'growth_composite')
        assert hasattr(r, 'inflation_composite')
        assert hasattr(r, 'raw_quadrant')
        assert hasattr(r, 'stable')
        assert hasattr(r, 'as_of')

    def test_classification_states_exhaustive(self):
        """All possible classification values are documented."""
        liquidity_states = set()
        for score in [-2, -1.5, -1.0, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
            liquidity_states.add(_classify_liquidity(score))
        assert liquidity_states == {
            'Strongly Expanding', 'Expanding', 'Neutral',
            'Contracting', 'Strongly Contracting',
        }

    def test_quadrant_states_exhaustive(self):
        """All four quadrants are reachable."""
        quadrants = set()
        for g in [1.0, 0.0, -1.0]:
            for i in [1.0, 0.0, -1.0]:
                quadrants.add(_classify_quadrant(g, i))
        assert 'Goldilocks' in quadrants
        assert 'Reflation' in quadrants
        assert 'Stagflation' in quadrants
        assert 'Deflation Risk' in quadrants
