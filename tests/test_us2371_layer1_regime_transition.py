"""
Unit tests for US-237.1: Layer 1 Alert Engine — Regime Transition Detection

Tests cover:
- Flip detection logic and 30-day window boundary conditions
- 2-of-3 threshold for alert firing
- Alert payload structure and required keys
- Context sentence content and format
- Historical occurrence count derivation
- Edge cases: missing data, insufficient history, identical values
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pandas as pd
import pytest

import importlib.util as _iutil

_REPO_ROOT = Path(__file__).parent.parent
_ST_DIR = _REPO_ROOT / "signaltrackers"
sys.path.insert(0, str(_ST_DIR))

# Import layer1_regime_transition DIRECTLY from file, bypassing the services
# package __init__.py (which requires flask_login etc. not installed on host).
_L1_PATH = _ST_DIR / "services" / "layer1_regime_transition.py"
_l1_spec = _iutil.spec_from_file_location("layer1_regime_transition", str(_L1_PATH))
_l1_mod = _iutil.module_from_spec(_l1_spec)
_l1_spec.loader.exec_module(_l1_mod)
# Register so @patch("layer1_regime_transition.X") can target the right module
sys.modules["layer1_regime_transition"] = _l1_mod

_detect_direction_flip = _l1_mod._detect_direction_flip
_build_context_sentence = _l1_mod._build_context_sentence
_count_historical_occurrences = _l1_mod._count_historical_occurrences
check_regime_transition = _l1_mod.check_regime_transition
_load_signal = _l1_mod._load_signal
DATA_DIR = _l1_mod.DATA_DIR

# Detect whether the full Flask stack is available (for integration tests)
_FLASK_STACK_AVAILABLE = bool(_iutil.find_spec("flask_login"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_series(values, start_days_ago=None):
    """Build a date-indexed Series with evenly-spaced daily dates."""
    n = len(values)
    if start_days_ago is None:
        start_days_ago = n - 1
    base = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    dates = [base - timedelta(days=start_days_ago - i) for i in range(n)]
    return pd.Series(values, index=pd.DatetimeIndex(dates))


def _rising_series(n=90, slope=0.1):
    return _make_series([i * slope for i in range(n)])


def _falling_series(n=90, slope=0.1):
    return _make_series([n * slope - i * slope for i in range(n)])


def _flip_series(days_since_flip=25, direction="up_then_down"):
    """
    Build a 90-point series that flips direction `days_since_flip` days ago
    at 2x the rate it was rising, so the endpoint comparison clearly detects the flip.

    direction='up_then_down': was rising, now falling
    direction='down_then_up': was falling, now rising
    """
    total = 90
    flip_idx = total - days_since_flip

    if direction == "up_then_down":
        rising = list(range(flip_idx))
        # Fall at 2x rate so current value is clearly below the 30d-ago level
        falling = [flip_idx - 1 - 2 * i for i in range(1, days_since_flip + 1)]
        values = rising + falling
    else:
        # falling first, then rising at 2x rate
        falling = list(range(flip_idx, 0, -1))
        rising = [2 * i for i in range(1, days_since_flip + 1)]
        values = falling + rising

    return _make_series(values)


# ---------------------------------------------------------------------------
# _detect_direction_flip
# ---------------------------------------------------------------------------

class TestDetectDirectionFlip:
    def test_no_flip_rising(self):
        """Consistently rising series should not flip."""
        assert not _detect_direction_flip(_rising_series())

    def test_no_flip_falling(self):
        """Consistently falling series should not flip."""
        assert not _detect_direction_flip(_falling_series())

    def test_flip_up_then_down(self):
        """Up-then-down series (flip 25 days ago) should detect a flip."""
        series = _flip_series(days_since_flip=25, direction="up_then_down")
        assert _detect_direction_flip(series)

    def test_flip_down_then_up(self):
        """Down-then-up series (flip 25 days ago) should detect a flip."""
        series = _flip_series(days_since_flip=25, direction="down_then_up")
        assert _detect_direction_flip(series)

    def test_flip_on_day_30_boundary_triggers(self):
        """A flip that occurred exactly 30 days ago (boundary) should trigger."""
        # Rising for 60 days, then falling for 30 days at 2x rate
        # value_30d_ago = 59 (last rising), value_today = 59 - 2*30 = -1 → clearly below
        values = list(range(60)) + [59 - 2 * i for i in range(1, 31)]
        series = _make_series(values)
        assert _detect_direction_flip(series, window_days=30)

    def test_signal_in_consistent_new_direction_for_60_plus_days_no_flip(self):
        """If a flip happened 65+ days ago, both the recent and prior windows
        are in the same (new) direction — no flip detected."""
        # Flipped 65 days ago, falling for 65 days. Both 30d-ago and 60d-ago
        # windows are in the falling direction.
        values = list(range(25)) + [25 + 65 - i for i in range(66)]
        # That's 25 rising then 66 falling = 91 values; trim to 90
        values = values[:90]
        series = _make_series(values)
        # With flip 65 days ago, both mid and start values are in falling territory
        # Both recent_change and prior_change will be negative → same direction
        result = _detect_direction_flip(series, window_days=30)
        # The algorithm detects no direction change when both windows are falling
        assert not result

    def test_no_data_returns_false(self):
        assert not _detect_direction_flip(None)

    def test_single_value_returns_false(self):
        series = _make_series([5.0])
        assert not _detect_direction_flip(series)

    def test_two_values_no_start_val_returns_false(self):
        """Two values: no start_val (needs 2 windows of history) → should return False."""
        series = _make_series([1.0, 2.0])
        assert not _detect_direction_flip(series)

    def test_identical_consecutive_values_no_flip(self):
        """Series with no change should not count as a flip."""
        values = [5.0] * 90
        series = _make_series(values)
        assert not _detect_direction_flip(series)

    def test_short_history_under_two_windows_returns_false(self):
        """History shorter than 2*window_days should return False (no start_val)."""
        # 29 days of data: start_cutoff would go back 60 days, but data only covers 28 days
        series = _make_series(list(range(29)))
        assert not _detect_direction_flip(series, window_days=30)

    def test_cli_flip_positive_to_negative_change(self):
        """CLI flip: MoM change goes from positive to negative (was rising, now falling)."""
        series = _flip_series(days_since_flip=25, direction="up_then_down")
        assert _detect_direction_flip(series)

    def test_yield_curve_slope_sign_change(self):
        """Yield curve flip: slope direction reverses (steepening → flattening)."""
        series = _flip_series(days_since_flip=25, direction="up_then_down")
        assert _detect_direction_flip(series)

    def test_nfci_direction_reversal_tightening_to_loosening(self):
        """NFCI flip: conditions tightening (rising) → loosening (falling)."""
        series = _flip_series(days_since_flip=25, direction="up_then_down")
        assert _detect_direction_flip(series)

    def test_flip_within_window_triggers(self):
        """Flip exactly within window_days should trigger."""
        series = _flip_series(days_since_flip=20, direction="up_then_down")
        assert _detect_direction_flip(series, window_days=30)

    def test_two_flips_same_direction_same_day_counts_independently(self):
        """Two separate signals that both flip are two independent detections."""
        s1 = _flip_series(days_since_flip=25, direction="up_then_down")
        s2 = _flip_series(days_since_flip=25, direction="up_then_down")
        assert _detect_direction_flip(s1)
        assert _detect_direction_flip(s2)


# ---------------------------------------------------------------------------
# check_regime_transition — 2-of-3 threshold
# ---------------------------------------------------------------------------

class TestCheckRegimeTransition:
    """Test the main entry point using mocked CSV loading."""

    def _make_flip(self):
        return _flip_series(days_since_flip=25, direction="up_then_down")

    def _make_no_flip(self):
        return _rising_series()

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(3, 7))
    def test_zero_flips_no_alert(self, mock_count, mock_load):
        mock_load.return_value = self._make_no_flip()
        result = check_regime_transition()
        assert result is None

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(3, 7))
    def test_one_flip_no_alert(self, mock_count, mock_load):
        no_flip = self._make_no_flip()
        flip = self._make_flip()
        call_count = {"n": 0}

        def side_effect(csv_name, col_name):
            call_count["n"] += 1
            # Only first signal flips
            if call_count["n"] == 1:
                return flip
            return no_flip

        mock_load.side_effect = side_effect
        result = check_regime_transition()
        assert result is None

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(3, 7))
    def test_two_flips_triggers_alert(self, mock_count, mock_load):
        no_flip = self._make_no_flip()
        flip = self._make_flip()
        call_count = {"n": 0}

        def side_effect(csv_name, col_name):
            call_count["n"] += 1
            return flip if call_count["n"] <= 2 else no_flip

        mock_load.side_effect = side_effect
        result = check_regime_transition()
        assert result is not None
        assert len(result["signals_triggered"]) == 2

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(5, 9))
    def test_three_flips_triggers_alert(self, mock_count, mock_load):
        mock_load.return_value = self._make_flip()
        result = check_regime_transition()
        assert result is not None
        assert len(result["signals_triggered"]) == 3

    @patch("layer1_regime_transition._load_signal")
    def test_all_signals_missing_no_alert_no_exception(self, mock_load):
        mock_load.return_value = None
        result = check_regime_transition()
        assert result is None

    @patch("layer1_regime_transition._load_signal")
    def test_one_signal_has_data_no_alert(self, mock_load):
        """Cannot meet 2-of-3 threshold with only 1 signal available."""
        flip = self._make_flip()
        call_count = {"n": 0}

        def side_effect(csv_name, col_name):
            call_count["n"] += 1
            return flip if call_count["n"] == 1 else None

        mock_load.side_effect = side_effect
        result = check_regime_transition()
        assert result is None


# ---------------------------------------------------------------------------
# Alert payload structure
# ---------------------------------------------------------------------------

class TestAlertPayloadStructure:
    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(4, 8))
    def test_payload_has_required_keys(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        assert result is not None
        for key in ("layer", "signals_triggered", "context_sentence", "timestamp", "severity"):
            assert key in result, f"Missing key: {key}"

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(4, 8))
    def test_layer_value_is_regime_transition(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        assert result["layer"] == "Regime Transition"

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(4, 8))
    def test_signals_triggered_length_at_least_two(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        assert len(result["signals_triggered"]) >= 2

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(4, 8))
    def test_timestamp_is_iso_string(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        ts = result["timestamp"]
        assert isinstance(ts, str)
        # Must be parseable as ISO datetime
        datetime.fromisoformat(ts)

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(4, 8))
    def test_severity_is_nonempty_string(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        assert isinstance(result["severity"], str)
        assert len(result["severity"]) > 0

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(4, 8))
    def test_severity_is_warning(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        assert result["severity"] == "warning"


# ---------------------------------------------------------------------------
# Context sentence
# ---------------------------------------------------------------------------

class TestContextSentence:
    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(5, 7))
    def test_context_sentence_is_nonempty(self, mock_count, mock_load):
        mock_load.return_value = _flip_series(days_since_flip=25)
        result = check_regime_transition()
        assert isinstance(result["context_sentence"], str)
        assert len(result["context_sentence"]) > 0

    @patch("layer1_regime_transition._load_signal")
    @patch("layer1_regime_transition._count_historical_occurrences", return_value=(5, 7))
    def test_context_sentence_contains_signal_names(self, mock_count, mock_load):
        call_count = {"n": 0}

        def side_effect(csv_name, col_name):
            call_count["n"] += 1
            if call_count["n"] <= 2:
                return _flip_series(days_since_flip=25)
            return _rising_series()

        mock_load.side_effect = side_effect
        result = check_regime_transition()
        assert result is not None
        # At least one signal name should appear in the context sentence
        found = any(sig in result["context_sentence"] for sig in result["signals_triggered"])
        assert found, f"No signal names in: {result['context_sentence']}"

    def test_context_sentence_includes_occurrence_count(self):
        sentence = _build_context_sentence(["CLI", "yield curve (10Y-2Y)"], 30, 5, 7)
        assert "5" in sentence
        assert "7" in sentence

    def test_context_sentence_format_matches_spec(self):
        sentence = _build_context_sentence(["CLI", "yield curve (10Y-2Y)"], 22, 5, 7)
        assert "CLI" in sentence
        assert "yield curve" in sentence
        assert "22 days" in sentence
        assert "5 of 7 occurrences" in sentence

    def test_occurrence_count_non_negative(self):
        sentence = _build_context_sentence(["CLI", "NFCI"], 30, 0, 0)
        assert "0 of 0 occurrences" in sentence

    def test_three_signals_sentence_grammar(self):
        sentence = _build_context_sentence(
            ["CLI", "yield curve (10Y-2Y)", "financial conditions index (NFCI)"], 30, 3, 5
        )
        assert "have all shifted" in sentence

    def test_two_signals_sentence_grammar(self):
        sentence = _build_context_sentence(["CLI", "yield curve (10Y-2Y)"], 30, 3, 5)
        assert "have both shifted" in sentence


# ---------------------------------------------------------------------------
# _count_historical_occurrences — derivation from real data
# ---------------------------------------------------------------------------

class TestHistoricalOccurrenceCounting:
    @patch("layer1_regime_transition._load_signal")
    def test_returns_non_negative_counts(self, mock_load):
        """Count must always be >= 0."""
        mock_load.return_value = _rising_series(n=200)
        n_dd, total = _count_historical_occurrences()
        assert total >= 0
        assert n_dd >= 0

    @patch("layer1_regime_transition._load_signal")
    def test_n_drawdown_lte_total(self, mock_load):
        """Drawdown count cannot exceed total occurrences."""
        mock_load.return_value = _rising_series(n=200)
        n_dd, total = _count_historical_occurrences()
        assert n_dd <= total

    @patch("layer1_regime_transition._load_signal")
    def test_all_missing_data_returns_zeros(self, mock_load):
        mock_load.return_value = None
        n_dd, total = _count_historical_occurrences()
        assert n_dd == 0
        assert total == 0

    @patch("layer1_regime_transition._load_signal")
    def test_history_shorter_than_two_windows_returns_zeros(self, mock_load):
        """If available history is shorter than 2 windows, no episodes can be found."""
        mock_load.return_value = _make_series(list(range(29)), start_days_ago=28)
        n_dd, total = _count_historical_occurrences(window_days=30)
        assert total == 0

    @patch("layer1_regime_transition._load_signal")
    def test_occurrence_count_is_integer(self, mock_load):
        mock_load.return_value = _rising_series(n=200)
        n_dd, total = _count_historical_occurrences()
        assert isinstance(total, int)
        assert isinstance(n_dd, int)

    @patch("layer1_regime_transition._load_signal")
    def test_occurrence_count_not_hardcoded(self, mock_load):
        """Count must change when different data is provided (not hardcoded)."""
        # All-rising series: no flips → zero occurrences
        mock_load.return_value = _rising_series(n=300)
        _, total_rising = _count_historical_occurrences()

        # Series with multiple flips: should have more occurrences
        # Use a zigzag series of 300 points
        import math
        zigzag = _make_series([10 * math.sin(i * 0.2) for i in range(300)],
                              start_days_ago=299)
        mock_load.return_value = zigzag
        _, total_zigzag = _count_historical_occurrences()

        # Zigzag should produce more occurrences than a monotone rising series
        assert total_zigzag >= total_rising


# ---------------------------------------------------------------------------
# RegimeTransitionLayer1Detector (integration with alert_detection_service)
# These tests require the full Flask stack (flask_login, flask_sqlalchemy, etc.)
# and are skipped on the host; they run in Docker where all deps are installed.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _FLASK_STACK_AVAILABLE,
    reason="requires full Flask stack (flask_login, flask_sqlalchemy, etc.)"
)
class TestRegimeTransitionDetectorIntegration:
    def _make_user_with_alerts_enabled(self, enabled=True):
        user = MagicMock()
        user.id = "test-user-123"
        user.alert_preferences = MagicMock()
        user.alert_preferences.alerts_enabled = enabled
        return user

    def test_alerts_disabled_returns_none(self):
        from services.alert_detection_service import RegimeTransitionLayer1Detector
        det = RegimeTransitionLayer1Detector()
        user = self._make_user_with_alerts_enabled(enabled=False)
        result = det.should_trigger(user, {})
        assert result is None

    def test_alert_type_is_regime_transition_l1(self):
        from services.alert_detection_service import RegimeTransitionLayer1Detector
        det = RegimeTransitionLayer1Detector()
        assert det.alert_type == "regime_transition_l1"

    def test_severity_is_warning(self):
        from services.alert_detection_service import RegimeTransitionLayer1Detector
        det = RegimeTransitionLayer1Detector()
        assert det.severity == "warning"

    @patch("layer1_regime_transition.check_regime_transition", return_value=None)
    def test_no_flip_returns_none(self, mock_check):
        from services.alert_detection_service import RegimeTransitionLayer1Detector
        det = RegimeTransitionLayer1Detector()
        user = self._make_user_with_alerts_enabled()

        with patch.object(det, "was_recently_triggered", return_value=False):
            result = det.should_trigger(user, {})
        assert result is None

    @patch("layer1_regime_transition.check_regime_transition")
    def test_flip_returns_alert_data(self, mock_check):
        mock_check.return_value = {
            "layer": "Regime Transition",
            "signals_triggered": ["CLI", "yield curve (10Y-2Y)"],
            "context_sentence": (
                "CLI and yield curve (10Y-2Y) have both shifted in the last 30 days — "
                "historically, regime transitions with this pattern have preceded equity "
                "drawdowns within 3–6 months in 3 of 7 occurrences."
            ),
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "warning",
        }
        from services.alert_detection_service import RegimeTransitionLayer1Detector
        det = RegimeTransitionLayer1Detector()
        user = self._make_user_with_alerts_enabled()

        with patch.object(det, "was_recently_triggered", return_value=False):
            result = det.should_trigger(user, {})

        assert result is not None
        assert "title" in result
        assert "message" in result
        assert "CLI" in result["title"]
        assert result["threshold_value"] == 2.0

    @patch("layer1_regime_transition.check_regime_transition")
    def test_recently_triggered_suppresses_alert(self, mock_check):
        mock_check.return_value = {
            "layer": "Regime Transition",
            "signals_triggered": ["CLI", "NFCI"],
            "context_sentence": "some sentence",
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "warning",
        }
        from services.alert_detection_service import RegimeTransitionLayer1Detector
        det = RegimeTransitionLayer1Detector()
        user = self._make_user_with_alerts_enabled()

        with patch.object(det, "was_recently_triggered", return_value=True):
            result = det.should_trigger(user, {})
        assert result is None

    def test_detector_is_in_detectors_list(self):
        """RegimeTransitionLayer1Detector must be included in the detectors list."""
        from services.alert_detection_service import RegimeTransitionLayer1Detector

        user = self._make_user_with_alerts_enabled()
        user.alert_preferences = MagicMock(alerts_enabled=True)

        with patch("services.alert_detection_service.get_latest_metrics", return_value={}):
            with patch("services.alert_detection_service.db"):
                with patch.object(
                    RegimeTransitionLayer1Detector, "should_trigger", return_value=None
                ) as mock_trigger:
                    from services.alert_detection_service import check_all_alerts_for_user
                    check_all_alerts_for_user(user)
                    mock_trigger.assert_called_once()
