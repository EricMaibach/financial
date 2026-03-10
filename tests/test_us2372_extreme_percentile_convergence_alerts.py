"""
Unit tests for US-237.2: Layer 2 & 3 Alert Engines
  - Layer 2: Extreme Percentile Detection
  - Layer 3: Multi-Signal Convergence

Tests cover all acceptance criteria, QA test-plan cases, boundary conditions,
momentum filter, payload structure, and edge cases.
"""
import sys
import importlib.util as _iutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path setup — load modules directly to bypass Flask-stack package imports
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_ST_DIR = _REPO_ROOT / "signaltrackers"
sys.path.insert(0, str(_ST_DIR))

# Load layer2_extreme_percentile directly from file
_L2_PATH = _ST_DIR / "services" / "layer2_extreme_percentile.py"
_l2_spec = _iutil.spec_from_file_location("layer2_extreme_percentile", str(_L2_PATH))
_l2_mod = _iutil.module_from_spec(_l2_spec)
_l2_spec.loader.exec_module(_l2_mod)
sys.modules["layer2_extreme_percentile"] = _l2_mod

# Expose Layer 2 symbols
_calculate_percentile_10y = _l2_mod._calculate_percentile_10y
_passes_momentum_filter = _l2_mod._passes_momentum_filter
_count_historical_occurrences_extreme = _l2_mod._count_historical_occurrences_extreme
_build_context_sentence_l2 = _l2_mod._build_context_sentence
check_extreme_percentile = _l2_mod.check_extreme_percentile
_load_signal = _l2_mod._load_signal

# Load layer3_convergence directly from file — must patch the import of layer2 symbols
sys.modules["services"] = MagicMock()
sys.modules["services.layer2_extreme_percentile"] = _l2_mod

_L3_PATH = _ST_DIR / "services" / "layer3_convergence.py"
_l3_spec = _iutil.spec_from_file_location("layer3_convergence", str(_L3_PATH))
_l3_mod = _iutil.module_from_spec(_l3_spec)
_l3_spec.loader.exec_module(_l3_mod)
sys.modules["layer3_convergence"] = _l3_mod

# Expose Layer 3 symbols
check_convergence = _l3_mod.check_convergence
_build_context_sentence_l3 = _l3_mod._build_context_sentence
_count_historical_convergence_occurrences = _l3_mod._count_historical_convergence_occurrences

# Detect whether the full Flask stack is available (for integration tests)
_FLASK_STACK_AVAILABLE = bool(_iutil.find_spec("flask_login"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_series(values, end_days_ago=0):
    """Build a date-indexed float Series with evenly-spaced daily dates ending today-end_days_ago."""
    n = len(values)
    base = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    base = base - timedelta(days=end_days_ago)
    dates = [base - timedelta(days=n - 1 - i) for i in range(n)]
    return pd.Series([float(v) for v in values], index=pd.DatetimeIndex(dates))


def _uniform_series(n=500, lo=0, hi=100):
    """Uniform series 0..n-1, enough history for 10yr window to have content."""
    import numpy as np
    values = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    return _make_series(values)


def _series_with_90day_value(current_pct, days_ago_pct, days_ago=45, n=500):
    """
    Build a series where:
    - The current (last) value is at `current_pct`-th percentile of the series
    - The value `days_ago` days ago is at `days_ago_pct`-th percentile

    Strategy: use a sorted series of n values.  The current value is the
    n*current_pct/100-th element; the value days_ago is set separately via
    manipulation to produce the desired percentile at that date.
    """
    import numpy as np
    base_values = list(range(n))
    # The series has n evenly-spaced values; percentile of value v ≈ v/n*100
    current_val = current_pct / 100 * n
    series = _make_series(base_values)
    # Replace the last value with the desired current value
    series.iloc[-1] = current_val
    # Replace the value at `days_ago` position with the desired historical value
    # (days_ago positions from the end)
    desired_hist_val = days_ago_pct / 100 * n
    idx = len(series) - 1 - days_ago
    if 0 <= idx < len(series):
        series.iloc[idx] = desired_hist_val
    return series


# ---------------------------------------------------------------------------
# Tests: _calculate_percentile_10y
# ---------------------------------------------------------------------------

class TestCalculatePercentile10y:

    def test_returns_none_for_none_series(self):
        assert _calculate_percentile_10y(None, 50) is None

    def test_returns_none_for_empty_series(self):
        assert _calculate_percentile_10y(pd.Series([], dtype=float), 50) is None

    def test_single_element_at_or_above_returns_100(self):
        s = _make_series([5])
        assert _calculate_percentile_10y(s, 5) == 100.0

    def test_single_element_below_returns_0(self):
        s = _make_series([5])
        assert _calculate_percentile_10y(s, 3) == 0.0

    def test_50th_percentile(self):
        s = _uniform_series(n=100)
        # value at 50th pct should be ~50 (out of 0..99)
        val = s.quantile(0.50)
        pct = _calculate_percentile_10y(s, val)
        assert pct is not None
        assert 45 <= pct <= 55

    def test_90th_percentile_returns_90(self):
        # Series 0..99, value=90 → 90 values below → 90.0%
        s = _make_series(list(range(100)))
        pct = _calculate_percentile_10y(s, 90)
        assert pct == 90.0

    def test_90th_percentile_is_high_extreme(self):
        s = _make_series(list(range(100)))
        pct = _calculate_percentile_10y(s, 90)
        assert pct >= 90.0  # is_high_extreme condition

    def test_89th_percentile_is_not_high_extreme(self):
        s = _make_series(list(range(100)))
        pct = _calculate_percentile_10y(s, 89)
        assert pct < 90.0

    def test_10th_percentile_is_low_extreme(self):
        s = _make_series(list(range(100)))
        pct = _calculate_percentile_10y(s, 10)
        assert pct == 10.0  # ≤ 10 → low extreme

    def test_11th_percentile_is_not_low_extreme(self):
        s = _make_series(list(range(100)))
        pct = _calculate_percentile_10y(s, 11)
        assert pct > 10.0

    def test_uses_10yr_window_not_20yr(self):
        """Series longer than 10 years: only last 10 years are used."""
        # Build 15 years of daily data; old values are very low, recent values are high
        import numpy as np
        n_old = 365 * 5   # 5 years of zeros
        n_new = 365 * 10  # 10 years of 0..1
        old_vals = [0.0] * n_old
        new_vals = list(range(n_new))
        all_vals = old_vals + new_vals
        base = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        dates = [base - timedelta(days=len(all_vals) - 1 - i) for i in range(len(all_vals))]
        s = pd.Series(all_vals, index=pd.DatetimeIndex(dates))

        # With 10yr window: the 0..3649 range is used; value=0 is at a low percentile
        pct_10yr = _calculate_percentile_10y(s, 0)
        # If using 20yr window, 0 would be tied with many zeros → higher percentile
        # 10yr window has no zeros (except maybe the boundary) → 0 is at ~0th pct
        assert pct_10yr is not None
        assert pct_10yr < 5  # 0 is near the bottom of the 10yr window

    def test_falls_back_to_full_history_when_short(self):
        """If fewer than 10 years of data, uses full history."""
        s = _make_series(list(range(50)))  # ~50 days of data
        pct = _calculate_percentile_10y(s, 25)
        assert pct == 50.0  # 25 values below 25 out of 50


# ---------------------------------------------------------------------------
# Tests: _passes_momentum_filter — Layer 2
# ---------------------------------------------------------------------------

class TestMomentumFilter:
    """
    Series construction notes:
    - We use _make_series([float(i) for i in range(n)]) → rising values 0.0..n-1.0
    - In a rising series, each value is the MAX of its sub-history → ~99th pct
    - For filter to PASS: set a specific window value to a small number
    - For filter to FAIL: leave window values as-is (all naturally at ~99th pct)

    For position k (0-indexed) in a series of n values:
      sub-history size = k+1; original values 0..k-1 and original at k
      percentile of value v at position k = count(< v in {0,...,k-1,v}) / (k+1) * 100
      For v < k: count(< v) = v → pct = v / (k+1) * 100
      For pct ≤ 70%: v ≤ 0.70 * (k+1)
    """

    def test_at_95th_pct_was_at_low_pct_45_days_ago_fires(self):
        """Test plan case 1: 45 days ago was at a low percentile → filter passes."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n    # current: 95th pct
        # Position -46 = position 454; sub-history has 455 values
        # For ≤70th pct: v ≤ 0.70 * 455 = 318.5 → use 1.0 (clearly below 70th)
        series.iloc[-46] = 1.0        # ~0.2th pct in sub-history → filter passes
        assert _passes_momentum_filter(series) is True

    def test_at_95th_pct_all_window_values_high_no_fire(self):
        """Test plan case 2: all 90-day window values at top of sub-history → filter fails.

        A rising series has each value at ~99th pct in its sub-history.
        Setting the current value to a high extreme but leaving the window intact
        means all window values are already at ~99th pct (the filter fails).
        """
        n = 500
        series = _make_series(list(range(n)))
        # Current is 95th pct; don't touch window values — they're all naturally at ~99th pct
        series.iloc[-1] = 0.95 * n
        # Confirm: the value at position 454 (iloc[-46]) is 454.0 in sub-history of 455 → 99.8%
        assert _passes_momentum_filter(series) is False

    def test_crossed_70th_exactly_90_days_ago_fires(self):
        """Test plan case 3: at exactly 70th pct at day 90 (boundary, inclusive) → fires.

        Position -91 = position n-91 (the first day of the 90-day window).
        Sub-history size there = n-91+1 = n-90.
        For 70th pct: v = 0.70 * (n-90) = 0.70 * 410 = 287.0 (for n=500).
        287.0/410*100 = 69.97% ≤ 70% → filter passes.
        """
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n            # current: high extreme
        # Set the boundary value (exactly 90 days ago = iloc[-91] = position 409)
        # to the 70th percentile of its sub-history (410 values: 0..408 + this value)
        series.iloc[-91] = 0.70 * 410         # ≈70th pct in sub-history of 410 → passes
        assert _passes_momentum_filter(series) is True

    def test_crossed_70th_91_days_ago_no_fire(self):
        """Test plan case 4: only position -92 (outside window) is low → filter fails.

        The window is positions -1 through -91 (today through today-90).
        An unmodified rising series has all window values at ~99th pct → filter fails.
        """
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n    # current: high extreme
        # Position -92 (outside window) is low — but it's NOT in the lookback window
        series.iloc[-92] = 1.0        # very low, but outside the 90-day window
        # All values INSIDE the window remain at their original high levels (~99th pct)
        assert _passes_momentum_filter(series) is False

    def test_low_extreme_was_at_low_pct_30_days_ago_fires(self):
        """Test plan case 5: at 5th pct AND 30 days ago was at a low percentile → fires."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.05 * n   # low extreme
        # Position -31 = position 469; sub-history has 470 values
        # Use value 1.0 → 1/470*100 = 0.2% ≤ 70% → filter passes
        series.iloc[-31] = 1.0
        assert _passes_momentum_filter(series) is True

    def test_returns_false_for_none(self):
        assert _passes_momentum_filter(None) is False

    def test_returns_false_for_single_element(self):
        s = _make_series([50])
        assert _passes_momentum_filter(s) is False


# ---------------------------------------------------------------------------
# Tests: Layer 2 check_extreme_percentile
# ---------------------------------------------------------------------------

class TestLayer2ExtremePercentile:

    def _mock_signals(self, pct_map):
        """
        Given a dict {label: (current_pct, days_ago_pct, days_ago_value)},
        return a list of (csv_name, col_name, label) tuples and a side_effect
        for mocking _load_signal that returns configured series.
        """
        pass  # see individual tests

    def _build_signal_series(self, current_pct, below70_in_window=True, n=500):
        """
        Build a series where:
        - Current value is at current_pct (as % of n)
        - If below70_in_window=True: one window value is very low (clearly ≤70th pct sub-history)
        - If below70_in_window=False: all window values stay at original rising values (~99th pct)

        Note: In a rising float series, every value is at ~99th pct in its sub-history.
        For filter to pass, we must SET a window value to a small number.
        For filter to fail, leave window values as-is.
        """
        values = list(range(n))
        series = _make_series(values)
        series.iloc[-1] = float(current_pct) / 100 * n
        if below70_in_window:
            # Set a value 45 days ago to be very small — clearly ≤70th pct in sub-history
            # Position -46: sub-history has n-45 values; value=1.0 → ~0.2% pct
            series.iloc[-46] = 1.0
        # else: leave window intact (all values naturally at ~99th pct → filter fails)
        return series

    def test_indicator_at_95th_pct_with_momentum_fires(self):
        """95th pct + was below 70th within 90 days → alert fires."""
        series = self._build_signal_series(95, below70_in_window=True)
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1

    def test_indicator_at_50th_pct_no_fire(self):
        """Test plan: at 50th pct → no alert."""
        series = self._build_signal_series(50, below70_in_window=True)
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert results == []

    def test_indicator_at_91st_pct_fires(self):
        """91st pct is above the 90th threshold → fires."""
        series = self._build_signal_series(91, below70_in_window=True)
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1

    def test_indicator_at_exactly_90th_pct_fires(self):
        """90th pct exactly → boundary inclusive → fires."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.90 * n   # 90th pct
        series.iloc[-46] = 1.0       # clearly ≤70th pct in sub-history → momentum passes
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1

    def test_indicator_at_89th_pct_no_fire(self):
        """89th pct → below threshold → no fire."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.89 * n   # 89th pct (below 90 threshold)
        series.iloc[-46] = 1.0
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert results == []

    def test_indicator_at_exactly_10th_pct_fires(self):
        """10th pct exactly → boundary inclusive → fires.

        With a 500-element float series [0..499], setting current = 50.0:
          count(< 50.0) = 50 → percentile = 10.0% ≤ 10% → is_low_extreme = True
        The current value (10% in its own full-history sub-history) also passes
        the momentum filter since 10% ≤ 70%.  No other modifications needed.
        """
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.10 * n   # 50.0 → count(< 50) = 50 → exactly 10th pct
        # Do NOT add a low window value — current value itself passes momentum filter
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1

    def test_indicator_at_11th_pct_no_fire(self):
        """11th pct → above low extreme threshold → no fire."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.11 * n   # 11th pct (above 10 threshold)
        series.iloc[-46] = 1.0
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert results == []

    def test_at_95th_but_momentum_fails_no_fire(self):
        """95th pct but window values all at ~99th pct (rising series) → filter fails → no fire."""
        series = self._build_signal_series(95, below70_in_window=False)
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert results == []

    def test_at_5th_pct_with_momentum_fires(self):
        """Low extreme (5th pct) + low window value → momentum passes → fires."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.05 * n  # 5th pct (low extreme)
        series.iloc[-31] = 1.0      # very low → ≤70th pct in sub-history → passes
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1

    def _make_firing_series(self, n=500):
        """Standard series that will fire Layer 2: 90th+ pct with low momentum value."""
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n  # 95th pct
        series.iloc[-46] = 1.0      # clearly below 70th → momentum passes
        return series

    def test_each_indicator_checked_independently(self):
        """Multiple Layer 2 alerts can fire in one run."""
        call_count = [0]

        def mock_load(csv_name, col_name):
            call_count[0] += 1
            return self._make_firing_series()

        with patch.object(_l2_mod, '_load_signal', side_effect=mock_load):
            results = check_extreme_percentile()

        # All 5 signals should have been checked
        assert call_count[0] == 5
        # All 5 should have fired
        assert len(results) == 5

    def test_payload_structure_layer(self):
        """Payload must include key 'layer' = 'Extreme Percentile'."""
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1
        assert results[0]['layer'] == 'Extreme Percentile'

    def test_payload_has_signals_triggered(self):
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert 'signals_triggered' in p
            assert isinstance(p['signals_triggered'], list)
            assert len(p['signals_triggered']) >= 1

    def test_payload_has_current_percentile(self):
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert 'current_percentile' in p
            assert isinstance(p['current_percentile'], float)

    def test_payload_has_context_sentence(self):
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert 'context_sentence' in p
            assert isinstance(p['context_sentence'], str)
            assert len(p['context_sentence']) > 0

    def test_payload_has_timestamp(self):
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert 'timestamp' in p
            datetime.fromisoformat(p['timestamp'])

    def test_payload_has_severity(self):
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert 'severity' in p
            assert p['severity'] in ('info', 'warning', 'critical')

    def test_context_sentence_contains_occurrence_count(self):
        """Context sentence must include a historical occurrence count (integer ≥ 0)."""
        import re
        series = self._make_firing_series()
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert re.search(r'\d+', p['context_sentence']), \
                "Context sentence must contain a numeric occurrence count"

    def test_no_data_for_any_indicator_returns_empty(self):
        """All signals missing → empty list, no exception."""
        with patch.object(_l2_mod, '_load_signal', return_value=None):
            results = check_extreme_percentile()
        assert results == []

    def test_single_data_point_handled_gracefully(self):
        """Single data point → percentile handled (0.0 or 100.0)."""
        s = _make_series([99999])  # single extreme high value
        with patch.object(_l2_mod, '_load_signal', return_value=s):
            # should not raise
            results = check_extreme_percentile()
        assert isinstance(results, list)

    def test_uses_10yr_window_not_20yr(self):
        """Percentile must use 10-year window (verified via _calculate_percentile_10y)."""
        # This is an acceptance-criteria test — verify the function is called
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n
        series.iloc[-46] = 0.50 * n
        with patch.object(_l2_mod, '_calculate_percentile_10y',
                          wraps=_l2_mod._calculate_percentile_10y) as mock_pct:
            with patch.object(_l2_mod, '_load_signal', return_value=series):
                check_extreme_percentile()
        assert mock_pct.called, "_calculate_percentile_10y must be used (not reimplemented)"


# ---------------------------------------------------------------------------
# Tests: Layer 3 check_convergence
# ---------------------------------------------------------------------------

class TestLayer3Convergence:

    def _make_signal_configs_with_pcts(self, percentiles):
        """
        Build signal configs and mock _load_signal to return series that produce
        the desired percentiles.

        percentiles: list of floats (one per signal, 0–100)
        """
        configs = [
            ("s1.csv", "s1", "Signal 1"),
            ("s2.csv", "s2", "Signal 2"),
            ("s3.csv", "s3", "Signal 3"),
            ("s4.csv", "s4", "Signal 4"),
            ("s5.csv", "s5", "Signal 5"),
        ][:len(percentiles)]

        def mock_load(csv_name, col_name):
            idx = int(col_name[1]) - 1
            pct = percentiles[idx]
            n = 100
            # For pct=80: value=80 → 80 values below → 80th pct
            s = _make_series(list(range(n)))
            s.iloc[-1] = pct  # raw value == pct for uniform 0..99 series
            return s

        return configs, mock_load

    def test_3_risk_off_indicators_fires(self):
        """Test plan: 3 all >75th pct (risk-off) → alert fires."""
        configs, loader = self._make_signal_configs_with_pcts([85, 85, 85])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None

    def test_4_risk_off_indicators_fires(self):
        """Test plan: 4 all >75th → alert fires."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84, 86])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None

    def test_3_risk_on_indicators_fires(self):
        """Test plan: 3 all <25th pct (risk-on) → alert fires."""
        configs, loader = self._make_signal_configs_with_pcts([10, 15, 20])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None

    def test_mixed_direction_no_fire(self):
        """Test plan: 2 risk-off + 1 risk-on → mixed direction → no alert."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 10])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is None

    def test_only_2_risk_off_no_fire(self):
        """Test plan: 2 risk-off (not 3) → below threshold → no alert."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is None

    def test_1_risk_off_2_neutral_no_fire(self):
        """Test plan: 1 risk-off + 2 neutral → no alert."""
        configs, loader = self._make_signal_configs_with_pcts([80, 50, 55])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is None

    def test_3_signals_2_risk_off_1_neutral_no_fire(self):
        """Test plan: 2 risk-off + 1 neutral (between 25–75) → no alert."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 50])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is None

    def test_payload_layer_field(self):
        """Payload layer = 'Multi-Signal Convergence'."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert result['layer'] == 'Multi-Signal Convergence'

    def test_payload_signals_triggered_length_at_least_3(self):
        """signals_triggered list has ≥ 3 entries when alert fires."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert len(result['signals_triggered']) >= 3

    def test_payload_context_sentence_with_occurrence_count(self):
        """Context sentence contains a numeric occurrence count."""
        import re
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert re.search(r'\d+', result['context_sentence'])

    def test_payload_has_timestamp(self):
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        datetime.fromisoformat(result['timestamp'])

    def test_payload_has_severity(self):
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert result['severity'] in ('info', 'warning', 'critical')

    def test_exactly_3_in_stress_fires(self):
        """Boundary: exactly 3 indicators in stress territory → fires."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84, 50, 50])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert len(result['signals_triggered']) >= 3

    def test_exactly_2_in_stress_no_fire(self):
        """Boundary: exactly 2 in stress territory → does NOT fire."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 50, 50, 50])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is None

    def test_no_data_returns_none(self):
        """All signals missing → None, no exception."""
        configs = [("s1.csv", "s1", "Signal 1"), ("s2.csv", "s2", "Signal 2")]
        with patch.object(_l3_mod, '_load_signal', return_value=None):
            result = check_convergence(configs)
        assert result is None

    def test_occurrence_count_not_hardcoded(self):
        """Occurrence count must come from historical computation, not a literal."""
        # Verify _count_historical_convergence_occurrences is called
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            with patch.object(_l3_mod, '_count_historical_convergence_occurrences',
                              wraps=_l3_mod._count_historical_convergence_occurrences) as mock_count:
                check_convergence(configs)
        assert mock_count.called, "Occurrence count must be computed dynamically"

    def test_direction_risk_off_label_in_context(self):
        """Context sentence mentions 'risk-off' when all signals are high."""
        configs, loader = self._make_signal_configs_with_pcts([80, 82, 84])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert 'risk-off' in result['context_sentence']

    def test_direction_risk_on_label_in_context(self):
        """Context sentence mentions 'risk-on' when all signals are low."""
        configs, loader = self._make_signal_configs_with_pcts([10, 12, 14])
        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert 'risk-on' in result['context_sentence']

    def test_defaults_to_standard_5_signals(self):
        """check_convergence() with no args uses the 5 standard indicators."""
        with patch.object(_l3_mod, '_load_signal', return_value=None):
            result = check_convergence()
        # Should complete without error even when all signals are unavailable
        assert result is None


# ---------------------------------------------------------------------------
# Tests: Shared / Percentile reuse (acceptance criteria)
# ---------------------------------------------------------------------------

class TestPercentileReuse:

    def test_layer2_calls_calculate_percentile_10y(self):
        """Layer 2 must reuse _calculate_percentile_10y, not reimplementing it."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n
        series.iloc[-46] = 1.0
        with patch.object(_l2_mod, '_calculate_percentile_10y',
                          wraps=_l2_mod._calculate_percentile_10y) as mock_pct:
            with patch.object(_l2_mod, '_load_signal', return_value=series):
                check_extreme_percentile()
        assert mock_pct.called

    def test_layer3_calls_calculate_percentile_10y(self):
        """Layer 3 must reuse _calculate_percentile_10y, not reimplementing it."""
        configs = [("s1.csv", "s1", "Signal 1"), ("s2.csv", "s2", "Sig 2"),
                   ("s3.csv", "s3", "Sig 3")]
        n = 100

        def loader(csv_name, col_name):
            s = _make_series(list(range(n)))
            s.iloc[-1] = 80
            return s

        with patch.object(_l3_mod, '_calculate_percentile_10y',
                          wraps=_l3_mod._calculate_percentile_10y) as mock_pct:
            with patch.object(_l3_mod, '_load_signal', side_effect=loader):
                check_convergence(configs)
        assert mock_pct.called

    def test_empty_series_returns_none_not_exception(self):
        """Passing None/empty series to percentile function returns None, no exception."""
        assert _calculate_percentile_10y(None, 50) is None
        assert _calculate_percentile_10y(pd.Series([], dtype=float), 50) is None

    def test_single_data_point_percentile_returns_float(self):
        """Single data point returns 0.0 or 100.0."""
        s = _make_series([42])
        result = _calculate_percentile_10y(s, 42)
        assert result in (0.0, 100.0)

    def test_series_shorter_than_10yr_uses_full_history(self):
        """Series shorter than 10 years: falls back to full available history."""
        # 200 data points (~200 days — well under 10 years)
        s = _make_series(list(range(200)))
        pct = _calculate_percentile_10y(s, 100)
        # 100 out of 200 are below 100 → 50th pct
        assert pct == 50.0


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_layer2_all_no_data_returns_empty_list(self):
        with patch.object(_l2_mod, '_load_signal', return_value=None):
            result = check_extreme_percentile()
        assert result == []

    def test_layer2_4_of_5_signals_available_still_evaluates(self):
        """Only 4 of 5 signals available → Layer 2 evaluates the 4 available."""
        call_count = [0]
        n = 500

        def loader(csv_name, col_name):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # first signal unavailable
            s = _make_series(list(range(n)))
            s.iloc[-1] = 0.95 * n  # high extreme
            s.iloc[-46] = 1.0      # clearly ≤70th pct → momentum passes
            return s

        with patch.object(_l2_mod, '_load_signal', side_effect=loader):
            result = check_extreme_percentile()
        assert call_count[0] == 5
        assert len(result) == 4  # 4 available, all fire

    def test_layer3_3_available_signals_all_extreme_fires(self):
        """Only 3 signals available, all in stress → fires (boundary: 3 is minimum)."""
        configs = [("s1.csv", "s1", "Sig 1"), ("s2.csv", "s2", "Sig 2"),
                   ("s3.csv", "s3", "Sig 3")]
        n = 100

        def loader(csv_name, col_name):
            s = _make_series(list(range(n)))
            s.iloc[-1] = 80  # >75th → risk-off
            return s

        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None

    def test_layer2_single_data_point_no_exception(self):
        s = _make_series([99999])
        with patch.object(_l2_mod, '_load_signal', return_value=s):
            result = check_extreme_percentile()
        assert isinstance(result, list)

    def test_layer3_2_in_stress_no_fire(self):
        """Boundary: exactly 2 in stress → does NOT fire."""
        configs = [("s1.csv", "s1", "Sig 1"), ("s2.csv", "s2", "Sig 2"),
                   ("s3.csv", "s3", "Sig 3")]
        call_count = [0]

        def loader(csv_name, col_name):
            call_count[0] += 1
            n = 100
            s = _make_series(list(range(n)))
            if call_count[0] <= 2:
                s.iloc[-1] = 80  # risk-off
            else:
                s.iloc[-1] = 50  # neutral
            return s

        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: Security
# ---------------------------------------------------------------------------

class TestSecurity:

    def test_context_sentences_do_not_include_raw_html(self):
        """Context sentences must not contain HTML tags."""
        sentence = _build_context_sentence_l2("HY credit spreads", 95.0, 5)
        assert '<' not in sentence
        assert '>' not in sentence

    def test_layer3_context_sentence_no_html(self):
        sentence = _build_context_sentence_l3(["Signal A", "Signal B", "Signal C"],
                                               "risk-off", 3)
        assert '<' not in sentence
        assert '>' not in sentence


# ---------------------------------------------------------------------------
# Tests: Performance (mocked)
# ---------------------------------------------------------------------------

class TestPerformance:

    def test_layer2_completes_within_2_seconds(self):
        """Layer 2 across 5 indicators on 10yr daily data completes < 2s (mocked)."""
        import time
        n = 365 * 10  # ~10 years of daily data
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n   # high extreme
        series.iloc[-46] = 1.0       # clearly ≤70th pct → momentum passes

        with patch.object(_l2_mod, '_load_signal', return_value=series):
            start = time.time()
            check_extreme_percentile()
            elapsed = time.time() - start

        assert elapsed < 2.0, f"Layer 2 took {elapsed:.2f}s — exceeds 2s limit"

    def test_layer3_convergence_check_is_fast(self):
        """Layer 3 convergence check completes quickly for 5 indicators."""
        import time
        n = 100
        configs = [("s1.csv", "s1", f"Sig {i}") for i in range(5)]

        def loader(csv_name, col_name):
            s = _make_series(list(range(n)))
            s.iloc[-1] = 80
            return s

        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            start = time.time()
            check_convergence(configs)
            elapsed = time.time() - start

        assert elapsed < 2.0, f"Layer 3 took {elapsed:.2f}s — exceeds 2s limit"


# ---------------------------------------------------------------------------
# Tests: Payload format matches US-237.1 spec
# ---------------------------------------------------------------------------

class TestPayloadFormat:

    def test_layer2_payload_matches_us2371_format(self):
        """Output format matches US-237.1: {layer, signals_triggered, context_sentence, timestamp, severity}."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n
        series.iloc[-46] = 1.0
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        assert len(results) >= 1
        p = results[0]
        required_keys = {'layer', 'signals_triggered', 'context_sentence', 'timestamp', 'severity'}
        assert required_keys.issubset(p.keys())

    def test_layer3_payload_matches_us2371_format(self):
        """Output format matches US-237.1: {layer, signals_triggered, context_sentence, timestamp, severity}."""
        configs = [("s1.csv", "s1", "Sig 1"), ("s2.csv", "s2", "Sig 2"),
                   ("s3.csv", "s3", "Sig 3")]
        n = 100

        def loader(csv_name, col_name):
            s = _make_series(list(range(n)))
            s.iloc[-1] = 80
            return s

        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        required_keys = {'layer', 'signals_triggered', 'context_sentence', 'timestamp', 'severity'}
        assert required_keys.issubset(result.keys())

    def test_layer2_signals_triggered_is_list(self):
        """signals_triggered must be a list even for single-signal alerts."""
        n = 500
        series = _make_series(list(range(n)))
        series.iloc[-1] = 0.95 * n
        series.iloc[-46] = 1.0
        with patch.object(_l2_mod, '_load_signal', return_value=series):
            results = check_extreme_percentile()
        for p in results:
            assert isinstance(p['signals_triggered'], list)

    def test_layer3_signals_triggered_is_list(self):
        configs = [("s1.csv", "s1", "Sig 1"), ("s2.csv", "s2", "Sig 2"),
                   ("s3.csv", "s3", "Sig 3")]
        n = 100

        def loader(csv_name, col_name):
            s = _make_series(list(range(n)))
            s.iloc[-1] = 80
            return s

        with patch.object(_l3_mod, '_load_signal', side_effect=loader):
            result = check_convergence(configs)
        assert result is not None
        assert isinstance(result['signals_triggered'], list)
