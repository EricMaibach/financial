"""
Static verification tests for US-5.1.1: Extend regime engine with trend direction
and confidence history.

These tests verify the implementation without requiring a live Flask server,
external API calls, or a trained k-means model. They exercise the pure-Python
logic directly and inspect source files for structural correctness.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Constants presence tests
# ---------------------------------------------------------------------------


class TestConstants(unittest.TestCase):
    """Required constants must be present in regime_detection.py."""

    def setUp(self):
        import regime_detection as rd
        self.rd = rd

    def test_trend_delta_threshold_defined(self):
        self.assertTrue(
            hasattr(self.rd, 'TREND_DELTA_THRESHOLD'),
            'TREND_DELTA_THRESHOLD not defined in regime_detection',
        )

    def test_trend_delta_threshold_value(self):
        self.assertAlmostEqual(self.rd.TREND_DELTA_THRESHOLD, 0.05)

    def test_confidence_history_file_constant(self):
        self.assertTrue(hasattr(self.rd, 'CONFIDENCE_HISTORY_FILE'))

    def test_confidence_history_file_in_data_dir(self):
        path = str(self.rd.CONFIDENCE_HISTORY_FILE)
        self.assertIn('data', path)
        self.assertIn('confidence_history', path)


class TestConstantsInSource(unittest.TestCase):
    """TREND_DELTA_THRESHOLD must appear literally in the source."""

    def setUp(self):
        src_path = os.path.join(SIGNALTRACKERS_DIR, 'regime_detection.py')
        self.src = read_file(src_path)

    def test_threshold_constant_literal_in_source(self):
        self.assertIn('TREND_DELTA_THRESHOLD', self.src)

    def test_threshold_value_literal_in_source(self):
        self.assertIn('0.05', self.src)

    def test_confidence_history_file_literal(self):
        self.assertIn('confidence_history', self.src)


# ---------------------------------------------------------------------------
# compute_trend() tests
# ---------------------------------------------------------------------------


class TestComputeTrendFunctionExists(unittest.TestCase):
    """compute_trend must be a named function, not inline logic."""

    def test_function_is_callable(self):
        import regime_detection as rd
        self.assertTrue(callable(getattr(rd, 'compute_trend', None)))


class TestComputeTrendInsufficientData(unittest.TestCase):
    """Fewer than 4 points → always 'stable'."""

    def setUp(self):
        from regime_detection import compute_trend
        self.compute_trend = compute_trend

    def test_empty_list_returns_stable(self):
        self.assertEqual(self.compute_trend([]), 'stable')

    def test_one_point_returns_stable(self):
        self.assertEqual(self.compute_trend([0.9]), 'stable')

    def test_two_points_returns_stable(self):
        self.assertEqual(self.compute_trend([0.9, 0.9]), 'stable')

    def test_three_points_returns_stable(self):
        self.assertEqual(self.compute_trend([0.9, 0.9, 0.9]), 'stable')

    def test_exactly_four_points_computes_normally(self):
        # 4 points: avg_3day and avg_alltime are computed
        result = self.compute_trend([0.5, 0.5, 0.9, 0.9])
        self.assertIn(result, ('improving', 'stable', 'deteriorating'))


class TestComputeTrendDirections(unittest.TestCase):
    """Trend direction computed correctly from rolling averages."""

    def setUp(self):
        from regime_detection import compute_trend
        self.compute_trend = compute_trend

    def test_improving_when_delta_exceeds_threshold(self):
        # 3-day avg = 0.9; 10-day avg ≈ 0.53 → delta ≈ +0.37 >> 0.05
        history = [0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.9, 0.9, 0.9]
        self.assertEqual(self.compute_trend(history), 'improving')

    def test_deteriorating_when_delta_below_negative_threshold(self):
        # 3-day avg = 0.2; 10-day avg ≈ 0.67 → delta ≈ -0.47 << -0.05
        history = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.2, 0.2, 0.2]
        self.assertEqual(self.compute_trend(history), 'deteriorating')

    def test_stable_when_delta_within_threshold(self):
        # All same values → delta = 0
        history = [0.5] * 10
        self.assertEqual(self.compute_trend(history), 'stable')

    def test_stable_when_delta_at_positive_boundary(self):
        # The code uses strict greater-than (delta > 0.05), so a delta that
        # is very slightly under the threshold should yield 'stable'.
        # Use a value 0.001 below threshold: delta ≈ 0.049 < 0.05 → stable.
        # history: 7 points at 0.5, last 3 at 0.549  → delta = 0.549 - ~0.502 ≈ 0.047
        history = [0.5] * 7 + [0.549] * 3
        result = self.compute_trend(history)
        self.assertEqual(result, 'stable')

    def test_stable_when_delta_at_negative_boundary(self):
        # delta slightly above -0.05: delta ≈ -0.047 > -0.05 → stable
        history = [0.5] * 7 + [0.451] * 3
        result = self.compute_trend(history)
        self.assertEqual(result, 'stable')

    def test_improving_just_above_threshold(self):
        # delta = 0.051 > 0.05 → improving
        x = (5.0 - 0.551 * 3) / 7
        history = [x] * 7 + [0.551] * 3
        result = self.compute_trend(history)
        self.assertEqual(result, 'improving')

    def test_deteriorating_just_below_negative_threshold(self):
        # delta = -0.051 < -0.05 → deteriorating
        x = (5.0 - 0.449 * 3) / 7
        history = [x] * 7 + [0.449] * 3
        result = self.compute_trend(history)
        self.assertEqual(result, 'deteriorating')

    def test_fewer_than_10_points_uses_all_available_for_10day_avg(self):
        # With 6 points, avg_10day should use all 6 (not zero-pad)
        # High recent values → improving
        history = [0.2, 0.3, 0.9, 0.9, 0.9, 0.9]
        result = self.compute_trend(history)
        self.assertEqual(result, 'improving')

    def test_exactly_10_points_uses_full_10day(self):
        history = [0.5] * 10
        self.assertEqual(self.compute_trend(history), 'stable')

    def test_return_values_are_valid_strings(self):
        for history in [
            [0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.9, 0.9, 0.9],
            [0.9] * 10,
            [0.5] * 10,
        ]:
            result = self.compute_trend(history)
            self.assertIn(result, ('improving', 'stable', 'deteriorating'))


# ---------------------------------------------------------------------------
# compute_sparkline_points() tests
# ---------------------------------------------------------------------------


class TestComputeSparklineFunctionExists(unittest.TestCase):
    def test_function_is_callable(self):
        import regime_detection as rd
        self.assertTrue(callable(getattr(rd, 'compute_sparkline_points', None)))


class TestComputeSparklineInsufficientData(unittest.TestCase):
    def setUp(self):
        from regime_detection import compute_sparkline_points
        self.compute = compute_sparkline_points

    def test_empty_list_returns_empty_string(self):
        self.assertEqual(self.compute([]), '')

    def test_one_point_returns_empty_string(self):
        self.assertEqual(self.compute([0.5]), '')

    def test_two_points_returns_empty_string(self):
        self.assertEqual(self.compute([0.5, 0.5]), '')

    def test_three_points_returns_non_empty(self):
        result = self.compute([0.5, 0.5, 0.5])
        self.assertNotEqual(result, '')


class TestComputeSparklineCoordinates(unittest.TestCase):
    def setUp(self):
        from regime_detection import compute_sparkline_points
        self.compute = compute_sparkline_points

    def _parse_points(self, points_str):
        """Parse 'x,y x,y ...' into list of (float, float) tuples."""
        result = []
        for pair in points_str.strip().split():
            x_str, y_str = pair.split(',')
            result.append((float(x_str), float(y_str)))
        return result

    def test_three_points_produces_three_coordinate_pairs(self):
        result = self.compute([0.5, 0.5, 0.5])
        pairs = self._parse_points(result)
        self.assertEqual(len(pairs), 3)

    def test_fourteen_points_produces_fourteen_pairs(self):
        result = self.compute([0.5] * 14)
        pairs = self._parse_points(result)
        self.assertEqual(len(pairs), 14)

    def test_first_point_x_is_zero(self):
        result = self.compute([0.9, 0.5, 0.2])
        pairs = self._parse_points(result)
        self.assertAlmostEqual(pairs[0][0], 0.0, places=1)

    def test_last_point_x_is_viewbox_width(self):
        result = self.compute([0.9, 0.5, 0.2])
        pairs = self._parse_points(result)
        self.assertAlmostEqual(pairs[-1][0], 100.0, places=1)

    def test_y_inverted_high_confidence_at_top(self):
        # confidence 1.0 → y = 32 - (1.0 * 32) = 0.0 (top)
        result = self.compute([1.0, 0.5, 0.0])
        pairs = self._parse_points(result)
        self.assertAlmostEqual(pairs[0][1], 0.0, places=1)  # confidence 1.0

    def test_y_inverted_low_confidence_at_bottom(self):
        # confidence 0.0 → y = 32 - (0.0 * 32) = 32.0 (bottom)
        result = self.compute([1.0, 0.5, 0.0])
        pairs = self._parse_points(result)
        self.assertAlmostEqual(pairs[2][1], 32.0, places=1)  # confidence 0.0

    def test_y_midpoint_confidence_half(self):
        # confidence 0.5 → y = 32 - (0.5 * 32) = 16.0
        result = self.compute([0.5, 0.5, 0.5])
        pairs = self._parse_points(result)
        for _, y in pairs:
            self.assertAlmostEqual(y, 16.0, places=1)

    def test_coordinates_formatted_to_one_decimal_place(self):
        result = self.compute([0.5, 0.5, 0.5])
        for pair_str in result.split():
            x_str, y_str = pair_str.split(',')
            # Should have exactly one decimal place
            self.assertRegex(x_str, r'^\d+\.\d$', f'Unexpected format: {x_str}')
            self.assertRegex(y_str, r'^\d+\.\d$', f'Unexpected format: {y_str}')

    def test_output_is_space_separated_string(self):
        result = self.compute([0.9, 0.5, 0.2])
        # Should contain commas within pairs but no extra structure
        self.assertIsInstance(result, str)
        pairs = result.split(' ')
        for pair in pairs:
            self.assertIn(',', pair)

    def test_all_identical_values_no_exception(self):
        # Flat line: should not raise ZeroDivisionError
        try:
            result = self.compute([0.5] * 14)
            self.assertNotEqual(result, '')
        except Exception as exc:
            self.fail(f'compute_sparkline_points raised with identical values: {exc}')

    def test_viewbox_14_points_x_spacing(self):
        result = self.compute([0.5] * 14)
        pairs = self._parse_points(result)
        # x step = 100 / 13 ≈ 7.69...
        for i, (x, _) in enumerate(pairs):
            expected_x = round((i / 13) * 100, 1)
            self.assertAlmostEqual(x, expected_x, places=1)


# ---------------------------------------------------------------------------
# Confidence history persistence tests
# ---------------------------------------------------------------------------


class TestConfidenceHistoryPersistence(unittest.TestCase):
    """_load_confidence_history() and _save_confidence_history() behaviour."""

    def setUp(self):
        import regime_detection as rd
        self.rd = rd

    def test_load_returns_empty_dict_when_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / 'nonexistent.json'
            with patch.object(self.rd, 'CONFIDENCE_HISTORY_FILE', fake_path):
                result = self.rd._load_confidence_history()
        self.assertEqual(result, {})

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / 'confidence_history.json'
            with patch.object(self.rd, 'CONFIDENCE_HISTORY_FILE', fake_path):
                data = {'2026-01-01': 0.9, '2026-01-02': 0.5}
                self.rd._save_confidence_history(data)
                result = self.rd._load_confidence_history()
        self.assertEqual(result, data)

    def test_loaded_values_are_floats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / 'confidence_history.json'
            with open(fake_path, 'w') as f:
                json.dump({'2026-01-01': 0.9}, f)
            with patch.object(self.rd, 'CONFIDENCE_HISTORY_FILE', fake_path):
                result = self.rd._load_confidence_history()
        self.assertIsInstance(result['2026-01-01'], float)

    def test_file_path_within_data_dir(self):
        path = str(self.rd.CONFIDENCE_HISTORY_FILE)
        self.assertIn('signaltrackers', path)
        self.assertIn('data', path)


# ---------------------------------------------------------------------------
# update_macro_regime() integration tests (with mocks)
# ---------------------------------------------------------------------------


class TestUpdateMacroRegimeNewFields(unittest.TestCase):
    """update_macro_regime() must include trend, confidence_history, sparkline_points."""

    def setUp(self):
        import regime_detection as rd
        self.rd = rd

    def _mock_update(self, confidence='High', extra_history=None):
        """Run update_macro_regime() with mocked classification in a temp dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cache = Path(tmpdir) / 'macro_regime_cache.json'
            tmp_history = Path(tmpdir) / 'confidence_history.json'

            if extra_history:
                with open(tmp_history, 'w') as f:
                    json.dump(extra_history, f)

            with (
                patch.object(self.rd, 'CACHE_FILE', tmp_cache),
                patch.object(self.rd, 'CONFIDENCE_HISTORY_FILE', tmp_history),
                patch.object(self.rd, '_load_feature_data') as mock_data,
                patch.object(self.rd, '_kmeans_regime') as mock_kmeans,
            ):
                import pandas as pd
                # Provide a non-empty DataFrame so the function proceeds
                mock_data.return_value = pd.DataFrame({'a': [1, 2, 3]})
                mock_kmeans.return_value = ('Bear', confidence)

                result = self.rd.update_macro_regime()

        return result

    def test_result_contains_trend_key(self):
        result = self._mock_update()
        self.assertIn('trend', result)

    def test_result_contains_confidence_history_key(self):
        result = self._mock_update()
        self.assertIn('confidence_history', result)

    def test_result_contains_confidence_sparkline_points_key(self):
        result = self._mock_update()
        self.assertIn('confidence_sparkline_points', result)

    def test_confidence_history_is_list(self):
        result = self._mock_update()
        self.assertIsInstance(result['confidence_history'], list)

    def test_confidence_history_empty_on_first_call(self):
        # First call → only 1 data point → history list returns []
        result = self._mock_update()
        self.assertEqual(result['confidence_history'], [])

    def test_confidence_history_values_in_range(self):
        # Pre-populate 14 days of history
        extra = {f'2026-01-{i:02d}': 0.5 for i in range(1, 15)}
        result = self._mock_update(extra_history=extra)
        for val in result['confidence_history']:
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_confidence_history_at_most_14_entries(self):
        extra = {f'2026-01-{i:02d}': 0.5 for i in range(1, 20)}
        result = self._mock_update(extra_history=extra)
        self.assertLessEqual(len(result['confidence_history']), 14)

    def test_same_date_not_duplicated(self):
        """Calling update twice on same date should not add a duplicate entry."""
        import regime_detection as rd
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cache = Path(tmpdir) / 'macro_regime_cache.json'
            tmp_history = Path(tmpdir) / 'confidence_history.json'

            import pandas as pd
            with (
                patch.object(rd, 'CACHE_FILE', tmp_cache),
                patch.object(rd, 'CONFIDENCE_HISTORY_FILE', tmp_history),
                patch.object(rd, '_load_feature_data') as mock_data,
                patch.object(rd, '_kmeans_regime') as mock_kmeans,
            ):
                mock_data.return_value = pd.DataFrame({'a': [1, 2, 3]})
                mock_kmeans.return_value = ('Bear', 'High')
                rd.update_macro_regime()
                rd.update_macro_regime()

            result = rd._load_confidence_history()
            # Should have at most 1 entry for today
            self.assertLessEqual(len(result), 1)

    def test_trend_is_valid_string(self):
        result = self._mock_update()
        self.assertIn(result['trend'], ('improving', 'stable', 'deteriorating'))

    def test_sparkline_points_is_string(self):
        result = self._mock_update()
        self.assertIsInstance(result['confidence_sparkline_points'], str)

    def test_sparkline_empty_when_fewer_than_3_history_points(self):
        result = self._mock_update()
        # 0–2 history points → sparkline points string is ''
        self.assertEqual(result['confidence_sparkline_points'], '')

    def test_sparkline_non_empty_with_sufficient_history(self):
        extra = {f'2026-01-{i:02d}': 0.5 for i in range(1, 14)}  # 13 days
        result = self._mock_update(extra_history=extra)
        self.assertNotEqual(result['confidence_sparkline_points'], '')

    def test_existing_state_and_confidence_unchanged(self):
        result = self._mock_update(confidence='High')
        self.assertEqual(result['state'], 'Bear')
        self.assertEqual(result['confidence'], 'High')

    def test_none_confidence_skips_history_entry(self):
        result = self._mock_update(confidence=None)
        self.assertEqual(result['confidence_history'], [])

    def test_confidence_history_oldest_first(self):
        # Populate history with dates in a specific order, verify list is sorted
        extra = {
            '2026-01-03': 0.9,
            '2026-01-01': 0.2,
            '2026-01-02': 0.5,
        }
        result = self._mock_update(extra_history=extra)
        if len(result['confidence_history']) >= 3:
            # Oldest (0.2) should be first, newest (0.9) last (before today's appended)
            self.assertEqual(result['confidence_history'][0], 0.2)


# ---------------------------------------------------------------------------
# Regression tests — existing fields unchanged
# ---------------------------------------------------------------------------


class TestExistingFieldsUnchanged(unittest.TestCase):
    """Existing regime dict fields must still be present."""

    def test_state_key_present(self):
        import regime_detection as rd
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cache = Path(tmpdir) / 'macro_regime_cache.json'
            tmp_history = Path(tmpdir) / 'confidence_history.json'

            import pandas as pd
            with (
                patch.object(rd, 'CACHE_FILE', tmp_cache),
                patch.object(rd, 'CONFIDENCE_HISTORY_FILE', tmp_history),
                patch.object(rd, '_load_feature_data') as mock_data,
                patch.object(rd, '_kmeans_regime') as mock_kmeans,
            ):
                mock_data.return_value = pd.DataFrame({'a': [1, 2, 3]})
                mock_kmeans.return_value = ('Bull', 'High')
                result = rd.update_macro_regime()

        self.assertIn('state', result)
        self.assertIn('updated_at', result)
        self.assertIn('confidence', result)

    def test_get_macro_regime_returns_none_or_dict(self):
        import regime_detection as rd
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / 'missing.json'
            with patch.object(rd, 'CACHE_FILE', fake_path):
                result = rd.get_macro_regime()
        self.assertIsNone(result)

    def test_update_macro_regime_returns_dict_or_none(self):
        import regime_detection as rd
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cache = Path(tmpdir) / 'cache.json'
            tmp_history = Path(tmpdir) / 'history.json'
            import pandas as pd
            with (
                patch.object(rd, 'CACHE_FILE', tmp_cache),
                patch.object(rd, 'CONFIDENCE_HISTORY_FILE', tmp_history),
                patch.object(rd, '_load_feature_data') as mock_data,
                patch.object(rd, '_kmeans_regime') as mock_kmeans,
            ):
                mock_data.return_value = pd.DataFrame({'a': [1, 2, 3]})
                mock_kmeans.return_value = ('Neutral', 'Medium')
                result = rd.update_macro_regime()
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()
