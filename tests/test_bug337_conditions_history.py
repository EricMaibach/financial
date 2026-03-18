"""
Tests for bug #337: market conditions history consolidation.

Covers:
1. History entries include growth_score and inflation_score at top level
2. get_market_conditions() reads from history (not separate cache file)
3. Backfill logic when history is sparse
4. Legacy cache fallback
"""

import json
import os
import sys
import tempfile
from datetime import date, datetime, timezone
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Ensure signaltrackers is importable
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
if SIGNALTRACKERS_DIR not in sys.path:
    sys.path.insert(0, SIGNALTRACKERS_DIR)

from market_conditions import (
    _append_conditions_history,
    _load_conditions_history,
    _save_conditions_history,
    _backfill_history_if_needed,
    get_market_conditions,
    get_conditions_history,
    update_market_conditions_cache,
    MARKET_CONDITIONS_CACHE_FILE,
    MARKET_CONDITIONS_HISTORY_FILE,
    LiquidityResult,
    QuadrantResult,
    RiskResult,
    PolicyResult,
)


# ============================================================================
# Helpers
# ============================================================================

def _mock_liquidity(state='Expanding', score=0.8):
    return LiquidityResult(state=state, score=score, as_of='2025-06-15')


def _mock_quadrant(quadrant='Goldilocks', growth=0.5, inflation=-0.3):
    return QuadrantResult(
        quadrant=quadrant, growth_composite=growth,
        inflation_composite=inflation, raw_quadrant=quadrant,
        stable=True, as_of='2025-06-15',
    )


def _mock_risk(state='Normal', score=2):
    return RiskResult(
        state=state, score=score, vix_score=1,
        term_structure_score=0, correlation_score=1,
        as_of='2025-06-15',
    )


def _mock_policy(stance='Neutral', direction='Paused'):
    return PolicyResult(
        stance=stance, direction=direction, taylor_gap=0.3,
        taylor_prescribed=4.5, actual_rate=4.8,
        as_of='2025-06-15',
    )


def _make_cache_data(quadrant='Goldilocks', growth=0.085, inflation=-0.204,
                     as_of='2025-06-15'):
    """Build a cache_data dict as produced by update_market_conditions_cache."""
    return {
        'quadrant': quadrant,
        'dimensions': {
            'liquidity': {'state': 'Neutral', 'score': 0.0},
            'quadrant': {
                'state': quadrant,
                'growth_composite': growth,
                'inflation_composite': inflation,
            },
            'risk': {'state': 'Normal', 'score': 2},
            'policy': {'stance': 'Neutral', 'direction': 'Paused'},
        },
        'asset_expectations': [{'asset': 'sp500', 'direction': 'positive'}],
        'as_of': as_of,
        'updated_at': f'{as_of}T12:00:00+00:00',
    }


# ============================================================================
# 1. History entries include composite scores
# ============================================================================

class TestHistoryCompositeScores:
    """Verify growth_score and inflation_score are persisted at top level."""

    def test_append_stores_growth_and_inflation_scores(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                cache_data = _make_cache_data(growth=0.085, inflation=-0.204)
                _append_conditions_history(cache_data)
                entry = _load_conditions_history()['2025-06-15']
                assert entry['growth_score'] == 0.085
                assert entry['inflation_score'] == -0.204
        finally:
            os.unlink(tmp)

    def test_append_stores_raw_quadrant(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                cache_data = _make_cache_data(quadrant='Reflation')
                _append_conditions_history(cache_data)
                entry = _load_conditions_history()['2025-06-15']
                assert entry['raw_quadrant'] == 'Reflation'
        finally:
            os.unlink(tmp)

    def test_append_stores_updated_at(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                cache_data = _make_cache_data()
                _append_conditions_history(cache_data)
                entry = _load_conditions_history()['2025-06-15']
                assert 'updated_at' in entry
                assert '2025-06-15' in entry['updated_at']
        finally:
            os.unlink(tmp)

    def test_append_preserves_dimensions(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                cache_data = _make_cache_data()
                _append_conditions_history(cache_data)
                entry = _load_conditions_history()['2025-06-15']
                assert 'dimensions' in entry
                assert 'liquidity' in entry['dimensions']
                assert 'quadrant' in entry['dimensions']
                assert 'risk' in entry['dimensions']
                assert 'policy' in entry['dimensions']
        finally:
            os.unlink(tmp)

    def test_append_with_missing_quadrant_dims_sets_none(self):
        """When dimensions.quadrant is absent, scores should be None."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp):
                cache_data = {
                    'quadrant': 'Goldilocks',
                    'dimensions': {'liquidity': {'state': 'Expanding'}},
                    'asset_expectations': [],
                    'as_of': '2025-06-15',
                }
                _append_conditions_history(cache_data)
                entry = _load_conditions_history()['2025-06-15']
                assert entry['growth_score'] is None
                assert entry['inflation_score'] is None
        finally:
            os.unlink(tmp)


# ============================================================================
# 2. get_market_conditions() reads from history
# ============================================================================

class TestGetMarketConditionsFromHistory:
    """Verify consolidated read path."""

    def test_reads_latest_entry_from_history(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            history = {
                '2025-06-14': {'quadrant': 'Reflation', 'dimensions': {},
                               'asset_expectations': [], 'updated_at': '2025-06-14T12:00:00Z'},
                '2025-06-15': {'quadrant': 'Goldilocks', 'dimensions': {},
                               'asset_expectations': [], 'updated_at': '2025-06-15T12:00:00Z'},
            }
            with open(tmp, 'w') as fh:
                json.dump(history, fh)

            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', '/nonexistent'):
                result = get_market_conditions()
                assert result is not None
                assert result['quadrant'] == 'Goldilocks'
                assert result['as_of'] == '2025-06-15'
        finally:
            os.unlink(tmp)

    def test_returns_expected_shape(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            history = {
                '2025-06-15': {
                    'quadrant': 'Goldilocks',
                    'dimensions': {'liquidity': {'state': 'Neutral'}},
                    'asset_expectations': [{'asset': 'sp500'}],
                    'updated_at': '2025-06-15T12:00:00+00:00',
                },
            }
            with open(tmp, 'w') as fh:
                json.dump(history, fh)

            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', '/nonexistent'):
                result = get_market_conditions()
                # Must have all keys that the context processor expects
                assert 'quadrant' in result
                assert 'dimensions' in result
                assert 'asset_expectations' in result
                assert 'as_of' in result
                assert 'updated_at' in result
        finally:
            os.unlink(tmp)

    def test_falls_back_to_legacy_cache(self):
        """When history is empty, reads from old cache file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            json.dump({'quadrant': 'Stagflation', 'as_of': '2025-06-10',
                       'updated_at': '2025-06-10T12:00:00Z',
                       'dimensions': {}, 'asset_expectations': []}, f)
            tmp_cache = f.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_history = f.name  # empty file

        try:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', tmp_cache), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp_history):
                result = get_market_conditions()
                assert result is not None
                assert result['quadrant'] == 'Stagflation'
        finally:
            for p in (tmp_cache, tmp_history):
                if os.path.exists(p):
                    os.unlink(p)

    def test_returns_none_when_both_missing(self):
        with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', '/nonexistent/cache.json'), \
             patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', '/nonexistent/hist.json'):
            assert get_market_conditions() is None


# ============================================================================
# 3. Backfill logic
# ============================================================================

class TestBackfillHistory:
    """Verify _backfill_history_if_needed() populates sparse history."""

    def _make_quadrant_df(self, n_months=13):
        """Create a mock quadrant history DataFrame."""
        dates = pd.date_range(end='2025-05-31', periods=n_months, freq='ME')
        n = len(dates)
        return pd.DataFrame({
            'date': dates,
            'growth': [0.1 + i * 0.01 for i in range(n)],
            'inflation': [-0.2 + i * 0.005 for i in range(n)],
            'raw_quadrant': ['Goldilocks'] * n,
            'quadrant': ['Goldilocks'] * n,
        })

    def _make_liquidity_df(self, n_months=13):
        dates = pd.date_range(end='2025-05-31', periods=n_months, freq='ME')
        n = len(dates)
        return pd.DataFrame({
            'date': dates,
            'score': [0.5 + i * 0.02 for i in range(n)],
            'state': ['Neutral'] * n,
        })

    def _make_risk_df(self, n_months=13):
        dates = pd.date_range(end='2025-05-31', periods=n_months, freq='ME')
        n = len(dates)
        return pd.DataFrame({
            'date': dates,
            'score': [2] * n,
            'state': ['Normal'] * n,
        })

    def _make_policy_df(self, n_months=13):
        dates = pd.date_range(end='2025-05-31', periods=n_months, freq='ME')
        n = len(dates)
        return pd.DataFrame({
            'date': dates,
            'stance': ['Neutral'] * n,
            'direction': ['Paused'] * n,
        })

    def test_backfill_populates_empty_history(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history', return_value=self._make_quadrant_df()), \
                 patch('market_conditions.compute_liquidity_history', return_value=self._make_liquidity_df()), \
                 patch('market_conditions.compute_risk_history', return_value=self._make_risk_df()), \
                 patch('market_conditions.compute_policy_history', return_value=self._make_policy_df()):
                _backfill_history_if_needed(min_entries=12)
                history = _load_conditions_history()
                assert len(history) >= 12
        finally:
            os.unlink(tmp)

    def test_backfill_skips_when_sufficient_entries(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            # Write 15 existing entries
            history = {f'2025-{i:02d}-15': {'quadrant': 'Goldilocks'} for i in range(1, 13)}
            history.update({f'2024-{i:02d}-15': {'quadrant': 'Reflation'} for i in range(10, 13)})
            json.dump(history, f)
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history') as mock_quad:
                _backfill_history_if_needed(min_entries=12)
                mock_quad.assert_not_called()
        finally:
            os.unlink(tmp)

    def test_backfill_does_not_overwrite_existing(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            existing_date = '2025-05-31'
            json.dump({existing_date: {'quadrant': 'Stagflation', 'custom': True}}, f)
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history', return_value=self._make_quadrant_df()), \
                 patch('market_conditions.compute_liquidity_history', return_value=self._make_liquidity_df()), \
                 patch('market_conditions.compute_risk_history', return_value=self._make_risk_df()), \
                 patch('market_conditions.compute_policy_history', return_value=self._make_policy_df()):
                _backfill_history_if_needed(min_entries=12)
                history = _load_conditions_history()
                # Existing entry preserved
                assert history[existing_date]['quadrant'] == 'Stagflation'
                assert history[existing_date].get('custom') is True
        finally:
            os.unlink(tmp)

    def test_backfill_entries_have_composite_scores(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history', return_value=self._make_quadrant_df()), \
                 patch('market_conditions.compute_liquidity_history', return_value=self._make_liquidity_df()), \
                 patch('market_conditions.compute_risk_history', return_value=self._make_risk_df()), \
                 patch('market_conditions.compute_policy_history', return_value=self._make_policy_df()):
                _backfill_history_if_needed(min_entries=12)
                history = _load_conditions_history()
                for dt_str, entry in history.items():
                    assert 'growth_score' in entry, f'Missing growth_score for {dt_str}'
                    assert 'inflation_score' in entry, f'Missing inflation_score for {dt_str}'
                    assert isinstance(entry['growth_score'], float)
                    assert isinstance(entry['inflation_score'], float)
        finally:
            os.unlink(tmp)

    def test_backfill_entries_have_all_dimensions(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history', return_value=self._make_quadrant_df()), \
                 patch('market_conditions.compute_liquidity_history', return_value=self._make_liquidity_df()), \
                 patch('market_conditions.compute_risk_history', return_value=self._make_risk_df()), \
                 patch('market_conditions.compute_policy_history', return_value=self._make_policy_df()):
                _backfill_history_if_needed(min_entries=12)
                history = _load_conditions_history()
                for dt_str, entry in history.items():
                    dims = entry['dimensions']
                    assert 'quadrant' in dims
                    assert 'liquidity' in dims
                    assert 'risk' in dims
                    assert 'policy' in dims
        finally:
            os.unlink(tmp)

    def test_backfill_handles_missing_liquidity(self):
        """Backfill works even when liquidity history is unavailable."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history', return_value=self._make_quadrant_df()), \
                 patch('market_conditions.compute_liquidity_history', return_value=None), \
                 patch('market_conditions.compute_risk_history', return_value=None), \
                 patch('market_conditions.compute_policy_history', return_value=None):
                _backfill_history_if_needed(min_entries=12)
                history = _load_conditions_history()
                assert len(history) >= 12
                # Quadrant dims should still be present
                for entry in history.values():
                    assert 'quadrant' in entry['dimensions']
                    # Other dimensions absent when history is None
                    assert 'liquidity' not in entry['dimensions']
        finally:
            os.unlink(tmp)

    def test_backfill_handles_no_quadrant_history(self):
        """No backfill when quadrant history unavailable."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            with patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', tmp), \
                 patch('market_conditions.compute_quadrant_history', return_value=None), \
                 patch('market_conditions.compute_liquidity_history', return_value=None), \
                 patch('market_conditions.compute_risk_history', return_value=None), \
                 patch('market_conditions.compute_policy_history', return_value=None):
                _backfill_history_if_needed(min_entries=12)
                history = _load_conditions_history()
                assert len(history) == 0
        finally:
            os.unlink(tmp)


# ============================================================================
# 4. Integration: update_market_conditions_cache writes to history
# ============================================================================

class TestUpdateWritesToHistory:
    """Verify that update_market_conditions_cache() only writes to history,
    not a separate cache file."""

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_no_separate_cache_file_written(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, 'cache.json')
            history_path = os.path.join(tmpdir, 'history.json')

            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', cache_path), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', history_path):
                update_market_conditions_cache()

                # History should exist with one entry
                assert os.path.exists(history_path)
                with open(history_path) as fh:
                    history = json.load(fh)
                assert len(history) == 1

                # Cache file should NOT be written
                assert not os.path.exists(cache_path)

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_history_entry_has_scores(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant(growth=0.123, inflation=-0.456)
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, 'cache.json')
            history_path = os.path.join(tmpdir, 'history.json')

            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', cache_path), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', history_path):
                update_market_conditions_cache()
                history = _load_conditions_history()
                entry = list(history.values())[0]
                assert entry['growth_score'] == 0.123
                assert entry['inflation_score'] == -0.456

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_get_market_conditions_reads_after_update(self, mock_liq, mock_quad, mock_risk, mock_pol, _mock_backfill):
        """Full round-trip: update → get reads from history."""
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant('Stagflation', growth=-0.5, inflation=0.8)
        mock_risk.return_value = _mock_risk('Stressed', 6)
        mock_pol.return_value = _mock_policy('Restrictive', 'Tightening')

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, 'cache.json')
            history_path = os.path.join(tmpdir, 'history.json')

            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', cache_path), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', history_path):
                update_market_conditions_cache()
                result = get_market_conditions()
                assert result is not None
                assert result['quadrant'] == 'Stagflation'
                assert 'dimensions' in result
                assert 'asset_expectations' in result
                assert 'updated_at' in result


# ============================================================================
# 5. Update triggers backfill
# ============================================================================

class TestUpdateTriggersBackfill:
    """Verify update_market_conditions_cache calls _backfill_history_if_needed."""

    @patch('market_conditions._backfill_history_if_needed')
    @patch('market_conditions.compute_policy')
    @patch('market_conditions.compute_risk')
    @patch('market_conditions.compute_quadrant')
    @patch('market_conditions.compute_liquidity')
    def test_backfill_called_after_append(self, mock_liq, mock_quad, mock_risk, mock_pol, mock_backfill):
        mock_liq.return_value = _mock_liquidity()
        mock_quad.return_value = _mock_quadrant()
        mock_risk.return_value = _mock_risk()
        mock_pol.return_value = _mock_policy()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('market_conditions.MARKET_CONDITIONS_CACHE_FILE', os.path.join(tmpdir, 'c.json')), \
                 patch('market_conditions.MARKET_CONDITIONS_HISTORY_FILE', os.path.join(tmpdir, 'h.json')):
                update_market_conditions_cache()
                mock_backfill.assert_called_once()
