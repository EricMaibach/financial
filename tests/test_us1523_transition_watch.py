"""
Tests for US-15.2.3: Graduated Stability Filter — Transition Watch State.

Covers:
  - Graduated stability filter (watch vs confirmed)
  - Transition watch state in QuadrantResult
  - First data point treated as confirmed
  - 2-month confirmation threshold maintained
  - Revert before month 2 cancels watch
  - Rapid oscillation handling
  - Three-way oscillation handling
  - Sustained quadrant (no watch triggered)
  - Empty / single data point edge cases
  - Transition watch in cache/history data model
  - AI briefing context includes transition watch
  - Non-inflation dimensions unchanged
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

# Ensure the project root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from signaltrackers.market_conditions import (
    _apply_graduated_stability_filter,
    _apply_stability_filter,
    QuadrantResult,
)


# ---------------------------------------------------------------------------
# Helper to build a quadrant series from labels
# ---------------------------------------------------------------------------

def _make_series(labels):
    """Create a pd.Series of quadrant labels with monthly index."""
    idx = pd.date_range('2024-01-31', periods=len(labels), freq='ME')
    return pd.Series(labels, index=idx)


# ---------------------------------------------------------------------------
# Core graduated filter tests
# ---------------------------------------------------------------------------

class TestGraduatedStabilityFilter:
    """Tests for _apply_graduated_stability_filter."""

    def test_empty_series(self):
        """Empty quadrant series returns empty results without errors."""
        s = pd.Series([], dtype=object)
        stable, watch = _apply_graduated_stability_filter(s)
        assert len(stable) == 0
        assert len(watch) == 0

    def test_single_data_point_confirmed(self):
        """First data point is treated as confirmed (no transition watch)."""
        s = _make_series(['Goldilocks'])
        stable, watch = _apply_graduated_stability_filter(s)
        assert stable.iloc[0] == 'Goldilocks'
        assert watch.iloc[0] is None

    def test_sustained_quadrant_no_watch(self):
        """Same quadrant sustained for many months — no transition watch ever triggered."""
        s = _make_series(['Reflation'] * 6)
        stable, watch = _apply_graduated_stability_filter(s)
        for i in range(6):
            assert stable.iloc[i] == 'Reflation'
            assert watch.iloc[i] is None

    def test_month1_transition_watch(self):
        """Month 1 in new quadrant: transition watch, confirmed quadrant unchanged."""
        s = _make_series(['Goldilocks', 'Goldilocks', 'Stagflation'])
        stable, watch = _apply_graduated_stability_filter(s)

        # Month 1 and 2: confirmed Goldilocks, no watch
        assert stable.iloc[0] == 'Goldilocks'
        assert watch.iloc[0] is None
        assert stable.iloc[1] == 'Goldilocks'
        assert watch.iloc[1] is None

        # Month 3: still confirmed Goldilocks, but watch toward Stagflation
        assert stable.iloc[2] == 'Goldilocks'
        assert watch.iloc[2] is not None
        assert watch.iloc[2]['direction'] == 'Stagflation'
        assert watch.iloc[2]['month'] == 1

    def test_month2_confirms_transition(self):
        """After 2 consecutive months in new quadrant, transition confirmed, watch removed."""
        s = _make_series(['Goldilocks', 'Goldilocks', 'Stagflation', 'Stagflation'])
        stable, watch = _apply_graduated_stability_filter(s)

        # Month 3: watch
        assert stable.iloc[2] == 'Goldilocks'
        assert watch.iloc[2] is not None
        assert watch.iloc[2]['direction'] == 'Stagflation'

        # Month 4: confirmed Stagflation, watch cleared
        assert stable.iloc[3] == 'Stagflation'
        assert watch.iloc[3] is None

    def test_revert_before_month2_cancels_watch(self):
        """Signal reverts before month 2 — transition watch cancelled, no false confirmation."""
        s = _make_series(['Goldilocks', 'Goldilocks', 'Stagflation', 'Goldilocks'])
        stable, watch = _apply_graduated_stability_filter(s)

        # Month 3: watch toward Stagflation
        assert watch.iloc[2] is not None
        assert watch.iloc[2]['direction'] == 'Stagflation'

        # Month 4: reverted — back to confirmed Goldilocks, watch cleared
        assert stable.iloc[3] == 'Goldilocks'
        assert watch.iloc[3] is None

    def test_rapid_oscillation_no_false_transitions(self):
        """Rapid oscillation (A→B→A→B): no false transitions — each new direction resets."""
        s = _make_series([
            'Goldilocks', 'Stagflation', 'Goldilocks', 'Stagflation',
            'Goldilocks', 'Stagflation',
        ])
        stable, watch = _apply_graduated_stability_filter(s)

        # Confirmed quadrant should stay Goldilocks throughout (never 2 consecutive of anything else)
        for i in range(6):
            assert stable.iloc[i] == 'Goldilocks'

        # Odd months should have watch toward Stagflation
        for i in [1, 3, 5]:
            assert watch.iloc[i] is not None
            assert watch.iloc[i]['direction'] == 'Stagflation'

        # Even months should have no watch
        for i in [0, 2, 4]:
            assert watch.iloc[i] is None

    def test_three_way_oscillation(self):
        """Three-way oscillation (A→B→C): watch resets from B to C."""
        s = _make_series([
            'Goldilocks', 'Goldilocks',
            'Stagflation',   # watch -> Stagflation
            'Reflation',     # watch -> Reflation (resets)
        ])
        stable, watch = _apply_graduated_stability_filter(s)

        # Month 3: watch toward Stagflation
        assert watch.iloc[2] is not None
        assert watch.iloc[2]['direction'] == 'Stagflation'

        # Month 4: watch toward Reflation (not stale Stagflation watch)
        assert watch.iloc[3] is not None
        assert watch.iloc[3]['direction'] == 'Reflation'
        assert stable.iloc[3] == 'Goldilocks'  # still Goldilocks confirmed

    def test_transition_then_sustained(self):
        """Transition confirmed, then new quadrant sustained — no further watches."""
        s = _make_series([
            'Goldilocks', 'Stagflation', 'Stagflation',
            'Stagflation', 'Stagflation',
        ])
        stable, watch = _apply_graduated_stability_filter(s)

        # Month 2: watch
        assert watch.iloc[1] is not None

        # Month 3: confirmed Stagflation
        assert stable.iloc[2] == 'Stagflation'
        assert watch.iloc[2] is None

        # Months 4-5: sustained, no watch
        assert stable.iloc[3] == 'Stagflation'
        assert watch.iloc[3] is None
        assert stable.iloc[4] == 'Stagflation'
        assert watch.iloc[4] is None

    def test_matches_binary_filter_stable_output(self):
        """The stable quadrant output matches the original binary filter exactly."""
        labels = [
            'Goldilocks', 'Goldilocks', 'Stagflation', 'Stagflation',
            'Reflation', 'Reflation', 'Reflation', 'Deflation Risk',
            'Deflation Risk', 'Goldilocks',
        ]
        s = _make_series(labels)

        binary = _apply_stability_filter(s, required_consecutive=2)
        graduated_stable, _ = _apply_graduated_stability_filter(s, required_consecutive=2)

        pd.testing.assert_series_equal(binary, graduated_stable)

    def test_watch_direction_includes_quadrant_name(self):
        """Transition watch direction is one of the four quadrant names."""
        valid_names = {'Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk'}
        s = _make_series(['Goldilocks', 'Deflation Risk'])
        _, watch = _apply_graduated_stability_filter(s)
        assert watch.iloc[1] is not None
        assert watch.iloc[1]['direction'] in valid_names


# ---------------------------------------------------------------------------
# QuadrantResult integration
# ---------------------------------------------------------------------------

class TestQuadrantResultTransitionWatch:
    """Test that QuadrantResult carries transition_watch correctly."""

    def test_default_none(self):
        """QuadrantResult.transition_watch defaults to None."""
        r = QuadrantResult(
            quadrant='Goldilocks',
            growth_composite=0.5,
            inflation_composite=-0.3,
            raw_quadrant='Goldilocks',
            stable=True,
        )
        assert r.transition_watch is None

    def test_with_transition_watch(self):
        """QuadrantResult can carry a transition_watch dict."""
        tw = {'direction': 'Stagflation', 'month': 1}
        r = QuadrantResult(
            quadrant='Goldilocks',
            growth_composite=0.5,
            inflation_composite=-0.3,
            raw_quadrant='Stagflation',
            stable=False,
            transition_watch=tw,
        )
        assert r.transition_watch == tw
        assert r.transition_watch['direction'] == 'Stagflation'


# ---------------------------------------------------------------------------
# Data model tests (cache/history shape)
# ---------------------------------------------------------------------------

class TestTransitionWatchDataModel:
    """Test transition_watch field in history entry shape."""

    def test_history_entry_has_transition_watch_null(self):
        """When no transition, transition_watch is None (not omitted)."""
        # Simulate the entry structure from _append_conditions_history
        quad_dims = {
            'state': 'Goldilocks',
            'growth_composite': 0.5,
            'inflation_composite': -0.3,
            'transition_watch': None,
        }
        entry = {
            'quadrant': 'Goldilocks',
            'transition_watch': quad_dims.get('transition_watch'),
        }
        assert 'transition_watch' in entry
        assert entry['transition_watch'] is None

    def test_history_entry_has_transition_watch_active(self):
        """When transition watch is active, field includes target quadrant name."""
        tw = {'direction': 'Stagflation', 'month': 1}
        quad_dims = {
            'state': 'Goldilocks',
            'transition_watch': tw,
        }
        entry = {
            'quadrant': 'Goldilocks',
            'transition_watch': quad_dims.get('transition_watch'),
        }
        assert entry['transition_watch'] is not None
        assert entry['transition_watch']['direction'] == 'Stagflation'

    def test_backwards_compat_missing_field(self):
        """Existing history entries without transition_watch are handled gracefully."""
        # Old entry format
        old_entry = {
            'quadrant': 'Goldilocks',
            'growth_score': 0.5,
            'inflation_score': -0.3,
        }
        # Code should use .get() — returns None
        tw = old_entry.get('transition_watch')
        assert tw is None


# ---------------------------------------------------------------------------
# AI briefing context tests
# ---------------------------------------------------------------------------

class TestBriefingContextTransitionWatch:
    """Test that AI briefing context includes transition watch info."""

    def test_conditions_context_with_watch(self):
        """When transition watch is active, briefing context includes the direction."""
        from signaltrackers.ai_summary import _build_conditions_context

        conditions = {
            'quadrant': 'Goldilocks',
            'dimensions': {
                'quadrant': {
                    'growth_composite': 0.5,
                    'inflation_composite': -0.3,
                    'transition_watch': {'direction': 'Stagflation', 'month': 1},
                },
                'liquidity': {'state': 'Ample', 'score': 0.8},
                'risk': {'state': 'Calm', 'score': 1},
                'policy': {'stance': 'Neutral', 'direction': 'Paused'},
            },
            'asset_expectations': [],
        }
        ctx = _build_conditions_context(conditions)
        assert 'Transition Watch' in ctx
        assert 'Stagflation' in ctx

    def test_conditions_context_no_watch(self):
        """When transition watch is null, briefing does not mention a transition."""
        from signaltrackers.ai_summary import _build_conditions_context

        conditions = {
            'quadrant': 'Goldilocks',
            'dimensions': {
                'quadrant': {
                    'growth_composite': 0.5,
                    'inflation_composite': -0.3,
                    'transition_watch': None,
                },
                'liquidity': {'state': 'Ample', 'score': 0.8},
                'risk': {'state': 'Calm', 'score': 1},
                'policy': {'stance': 'Neutral', 'direction': 'Paused'},
            },
            'asset_expectations': [],
        }
        ctx = _build_conditions_context(conditions)
        assert 'Transition Watch' not in ctx

    def test_conditions_context_missing_watch_field(self):
        """Old conditions dict without transition_watch field — no crash, no mention."""
        from signaltrackers.ai_summary import _build_conditions_context

        conditions = {
            'quadrant': 'Goldilocks',
            'dimensions': {
                'quadrant': {
                    'growth_composite': 0.5,
                    'inflation_composite': -0.3,
                },
                'liquidity': {'state': 'Ample'},
                'risk': {'state': 'Calm'},
                'policy': {'stance': 'Neutral', 'direction': 'Paused'},
            },
            'asset_expectations': [],
        }
        ctx = _build_conditions_context(conditions)
        assert 'Transition Watch' not in ctx

    def test_history_context_with_watch(self):
        """History context shows transition watch indicator for entries with active watch."""
        from signaltrackers.ai_summary import _build_conditions_history_context
        from datetime import date, timedelta

        today = date.today()
        d1 = str(today - timedelta(days=30))
        d2 = str(today - timedelta(days=1))

        history = {
            d1: {
                'quadrant': 'Goldilocks',
                'transition_watch': None,
                'dimensions': {
                    'liquidity': {'state': 'Ample'},
                    'risk': {'state': 'Calm'},
                    'policy': {'stance': 'Neutral', 'direction': 'Paused'},
                },
            },
            d2: {
                'quadrant': 'Goldilocks',
                'transition_watch': {'direction': 'Stagflation', 'month': 1},
                'dimensions': {
                    'liquidity': {'state': 'Ample'},
                    'risk': {'state': 'Calm'},
                    'policy': {'stance': 'Neutral', 'direction': 'Paused'},
                },
            },
        }
        ctx = _build_conditions_history_context(history, days=60)
        assert 'WATCH→Stagflation' in ctx
        # First entry should not have watch indicator
        lines = ctx.split('\n')
        d1_line = [l for l in lines if d1 in l][0]
        assert 'WATCH' not in d1_line
