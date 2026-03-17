"""
Market Conditions Backtest — Quadrant-Led Walk-Forward Validation

Scores the quadrant classification engine directly against forward asset
returns.  The quadrant IS the headline — each quadrant has clear asset
expectations (from MARKET-CONDITIONS-FRAMEWORK.md § 5).

Key scoring changes (US-314.2):
  1. Score against quadrant expectations, not a verdict classifier.
  2. S&P 500 scored on inflation-adjusted (real) 90-day returns.
  3. Magnitude ordering test: Goldilocks real > Defl Risk > Reflation > Stagflation.
  4. Treasuries and Gold scored on nominal directional accuracy per quadrant.

Usage:
    PYTHONPATH=signaltrackers python3 signaltrackers/backtesting/conditions_backtest.py

Output is written to signaltrackers/backtesting/results/
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Reuse data loading and forward-return functions from existing backtest
from signaltrackers.backtesting.regime_backtest import (
    SCORING_ASSETS,
    NEUTRAL_THRESHOLD,
    load_csv,
    load_scoring_assets,
    compute_forward_return,
    compute_max_drawdown,
)

# Market conditions engine (quadrant-led; no verdict in engine)
from signaltrackers.market_conditions import (
    compute_liquidity_history,
    compute_quadrant_history,
    compute_risk_history,
    compute_policy_history,
)

warnings.filterwarnings('ignore', category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(__file__).resolve().parent / 'results'

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FORWARD_WINDOWS = [30, 60, 90]
EVAL_FREQUENCY_MONTHS = 1

# Quadrant labels in expected real-return ordering (best → worst)
QUADRANT_LABELS = ['Goldilocks', 'Deflation Risk', 'Reflation', 'Stagflation']

# Walk-forward fold configuration
FOLD_START_YEAR = 2005
FOLD_END_YEAR = 2025
FOLD_TEST_MONTHS = 24  # 2-year test windows

# ---------------------------------------------------------------------------
# Quadrant-led expectations (from MARKET-CONDITIONS-FRAMEWORK.md § 5)
# ---------------------------------------------------------------------------

# Directional expectations per quadrant — used for Treasuries and Gold scoring.
# S&P 500 is scored via magnitude ordering of real returns, not direction.
QUADRANT_EXPECTATIONS = {
    'Goldilocks': {
        'sp500': 'positive',
        'treasuries': 'positive',
        'gold': 'neutral',
    },
    'Reflation': {
        'sp500': 'positive',
        'treasuries': 'negative',
        'gold': 'positive',
    },
    'Stagflation': {
        'sp500': 'negative',
        'treasuries': 'negative',
        'gold': 'positive',
    },
    'Deflation Risk': {
        'sp500': 'negative',
        'treasuries': 'positive',
        'gold': 'neutral',
    },
}


# ---------------------------------------------------------------------------
# CPI loading for real-return calculation
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


def load_cpi_series() -> Optional[pd.Series]:
    """
    Load CPI data and return a DatetimeIndex-ed Series.

    Used to compute YoY inflation for real-return adjustment.
    """
    cpi_path = DATA_DIR / 'cpi.csv'
    if not cpi_path.exists():
        return None
    df = pd.read_csv(cpi_path)
    if df.empty or len(df.columns) < 2:
        return None
    df.columns = ['date', 'value']
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).set_index('date').sort_index()
    return df['value']


def compute_cpi_yoy(cpi_series: pd.Series, eval_date: pd.Timestamp) -> Optional[float]:
    """
    Compute annualized CPI YoY% at eval_date (no lookahead).

    Returns a decimal (e.g. 0.03 for 3% inflation) or None.
    """
    if cpi_series is None or cpi_series.empty:
        return None

    # Most recent CPI observation at or before eval_date
    available = cpi_series[cpi_series.index <= eval_date]
    if len(available) < 13:  # Need 12+ months of history
        return None

    current = available.iloc[-1]
    # YoY: compare to observation ~12 months ago
    one_year_ago = eval_date - pd.DateOffset(months=12)
    past = cpi_series[cpi_series.index <= one_year_ago]
    if past.empty:
        return None

    past_val = past.iloc[-1]
    if past_val == 0:
        return None

    return (current - past_val) / past_val


# ---------------------------------------------------------------------------
# History precomputation — load all dimension histories once
# ---------------------------------------------------------------------------


def load_dimension_histories(
    start_date: str = '2003-01-01',
) -> dict[str, pd.DataFrame]:
    """
    Load all four dimension histories. Returns dict of DataFrames.
    Each has a 'date' column and dimension-specific columns.
    """
    print('Loading dimension histories...')
    histories = {}

    liq = compute_liquidity_history(start_date)
    if liq is not None and not liq.empty:
        histories['liquidity'] = liq
        print(f'  Liquidity: {len(liq)} points, {liq["date"].iloc[0].strftime("%Y-%m-%d")} to {liq["date"].iloc[-1].strftime("%Y-%m-%d")}')
    else:
        print('  WARNING: No liquidity history available')

    quad = compute_quadrant_history(start_date)
    if quad is not None and not quad.empty:
        histories['quadrant'] = quad
        print(f'  Quadrant: {len(quad)} points, {quad["date"].iloc[0].strftime("%Y-%m-%d")} to {quad["date"].iloc[-1].strftime("%Y-%m-%d")}')
    else:
        print('  WARNING: No quadrant history available')

    risk = compute_risk_history(start_date)
    if risk is not None and not risk.empty:
        histories['risk'] = risk
        print(f'  Risk: {len(risk)} points, {risk["date"].iloc[0].strftime("%Y-%m-%d")} to {risk["date"].iloc[-1].strftime("%Y-%m-%d")}')
    else:
        print('  WARNING: No risk history available')

    policy = compute_policy_history(start_date)
    if policy is not None and not policy.empty:
        histories['policy'] = policy
        print(f'  Policy: {len(policy)} points, {policy["date"].iloc[0].strftime("%Y-%m-%d")} to {policy["date"].iloc[-1].strftime("%Y-%m-%d")}')
    else:
        print('  WARNING: No policy history available')

    return histories


def _get_dimension_state_at(
    history_df: pd.DataFrame,
    eval_date: pd.Timestamp,
    state_col: str,
) -> Optional[str]:
    """
    Get the dimension state at or just before eval_date (no lookahead).
    Uses forward-fill logic: takes the most recent observation <= eval_date.
    """
    mask = history_df['date'] <= eval_date
    subset = history_df[mask]
    if subset.empty:
        return None
    return subset.iloc[-1][state_col]


def classify_conditions(
    histories: dict[str, pd.DataFrame],
    eval_date: pd.Timestamp,
) -> Optional[dict]:
    """
    Classify market conditions at eval_date using precomputed histories.

    The quadrant is the headline classification. Expectations come
    directly from QUADRANT_EXPECTATIONS — no verdict classifier.

    Risk state 'Stressed' overrides S&P 500 expectation to negative.
    """
    # Get quadrant state (required)
    quad_state = None
    if 'quadrant' in histories:
        quad_state = _get_dimension_state_at(histories['quadrant'], eval_date, 'quadrant')
    if quad_state is None:
        return None

    # Get liquidity state (optional, context only)
    liq_state = None
    if 'liquidity' in histories:
        liq_state = _get_dimension_state_at(histories['liquidity'], eval_date, 'state')

    # Risk state (graceful degradation)
    risk_state = 'Normal'
    if 'risk' in histories:
        rs = _get_dimension_state_at(histories['risk'], eval_date, 'state')
        if rs is not None:
            risk_state = rs

    # Policy state (graceful degradation)
    policy_stance = 'Neutral'
    if 'policy' in histories:
        ps = _get_dimension_state_at(histories['policy'], eval_date, 'stance')
        if ps is not None:
            policy_stance = ps

    # Expectations directly from quadrant
    expectations = dict(QUADRANT_EXPECTATIONS.get(
        quad_state, QUADRANT_EXPECTATIONS['Goldilocks']
    ))

    # Stressed override: S&P 500 → negative regardless of quadrant
    if risk_state == 'Stressed':
        expectations['sp500'] = 'negative'

    return {
        'quadrant': quad_state,
        'liquidity_state': liq_state,
        'risk_state': risk_state,
        'policy_stance': policy_stance,
        'expectations': expectations,
    }


# ---------------------------------------------------------------------------
# Per-evaluation scoring
# ---------------------------------------------------------------------------


def score_single_evaluation(
    expectations: dict[str, str],
    asset_returns: dict[str, Optional[float]],
    real_sp500_return: Optional[float] = None,
) -> dict:
    """
    Score a single evaluation against forward returns.

    S&P 500 is scored on directional accuracy using *real* (inflation-adjusted)
    returns.  Treasuries and Gold use nominal returns per quadrant expectations.
    """
    asset_scores = {}
    weighted_sum = 0.0
    weight_sum = 0.0

    for asset_key, config in SCORING_ASSETS.items():
        # Use real return for S&P 500, nominal for everything else
        if asset_key == 'sp500' and real_sp500_return is not None:
            ret = real_sp500_return
        else:
            ret = asset_returns.get(asset_key)

        if ret is None:
            continue

        direction = expectations.get(asset_key, 'neutral')
        weight = config['weight']

        if direction == 'positive':
            score = 1.0 if ret > 0 else 0.0
        elif direction == 'negative':
            score = 1.0 if ret < 0 else 0.0
        elif direction == 'neutral':
            score = 1.0 if abs(ret) < NEUTRAL_THRESHOLD else 0.5
        else:
            continue

        asset_scores[asset_key] = score
        weighted_sum += score * weight
        weight_sum += weight

    weighted_score = weighted_sum / weight_sum if weight_sum > 0 else None

    return {
        'asset_scores': asset_scores,
        'weighted_score': round(weighted_score, 4) if weighted_score is not None else None,
        'assets_available': list(asset_scores.keys()),
    }


# ---------------------------------------------------------------------------
# Walk-forward backtest
# ---------------------------------------------------------------------------


def generate_eval_dates(
    start_year: int,
    end_year: int,
) -> list[pd.Timestamp]:
    """Generate monthly evaluation dates for the given range."""
    return list(pd.date_range(
        start=f'{start_year}-01-01',
        end=f'{end_year}-12-31',
        freq=f'{EVAL_FREQUENCY_MONTHS}ME',
    ))


def generate_folds(
    start_year: int = FOLD_START_YEAR,
    end_year: int = FOLD_END_YEAR,
    test_months: int = FOLD_TEST_MONTHS,
) -> list[dict]:
    """
    Generate walk-forward expanding window folds.

    Returns list of dicts with 'fold', 'test_start', 'test_end' keys.
    Training data is everything before test_start (expanding window).
    """
    folds = []
    test_start_year = start_year
    step_years = test_months // 12
    fold_num = 1

    while test_start_year < end_year:
        test_end_year = min(test_start_year + step_years, end_year)

        folds.append({
            'fold': fold_num,
            'test_start': pd.Timestamp(f'{test_start_year}-01-01'),
            'test_end': pd.Timestamp(f'{test_end_year}-01-01') - pd.Timedelta(days=1),
        })

        test_start_year = test_end_year
        fold_num += 1

    return folds


def run_backtest(
    histories: dict[str, pd.DataFrame],
    scoring_assets: dict[str, pd.Series],
    cpi_series: Optional[pd.Series] = None,
    start_year: int = FOLD_START_YEAR,
    end_year: int = FOLD_END_YEAR,
) -> pd.DataFrame:
    """
    Run the conditions backtest over all evaluation dates.

    Returns DataFrame with one row per evaluation date including
    quadrant, dimension states, forward returns (nominal + real), and scores.
    """
    # Need 90 days of forward data
    last_dates = [s.index[-1] for s in scoring_assets.values()]
    last_data = min(last_dates)
    end_date = min(pd.Timestamp(f'{end_year}-12-31'), last_data - pd.Timedelta(days=90))
    start_date = pd.Timestamp(f'{start_year}-01-01')

    eval_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq=f'{EVAL_FREQUENCY_MONTHS}ME',
    )

    rows = []
    for eval_date in eval_dates:
        result = classify_conditions(histories, eval_date)
        if result is None:
            continue

        row = {
            'date': eval_date.strftime('%Y-%m-%d'),
            'quadrant': result['quadrant'],
            'liquidity_state': result['liquidity_state'],
            'risk_state': result['risk_state'],
            'policy_stance': result['policy_stance'],
        }

        # Forward returns (nominal)
        asset_returns_90d = {}
        for asset_key, price_series in scoring_assets.items():
            for w in FORWARD_WINDOWS:
                ret = compute_forward_return(price_series, eval_date, w)
                row[f'{asset_key}_fwd_{w}d'] = ret
                if w == 90:
                    asset_returns_90d[asset_key] = ret

        # S&P 500 real return = nominal - (cpi_yoy / 4) for 90-day window
        sp500_nominal_90d = asset_returns_90d.get('sp500')
        real_sp500_90d = None
        cpi_yoy = compute_cpi_yoy(cpi_series, eval_date)
        row['cpi_yoy'] = cpi_yoy

        if sp500_nominal_90d is not None and cpi_yoy is not None:
            real_sp500_90d = sp500_nominal_90d - (cpi_yoy / 4)
        row['sp500_real_fwd_90d'] = real_sp500_90d

        # S&P 500 max drawdown
        if 'sp500' in scoring_assets:
            row['sp500_max_dd_90d'] = compute_max_drawdown(
                scoring_assets['sp500'], eval_date, 90
            )

        # Score using quadrant expectations + real returns for S&P 500
        eval_score = score_single_evaluation(
            result['expectations'], asset_returns_90d,
            real_sp500_return=real_sp500_90d,
        )
        row['multi_asset_score'] = eval_score['weighted_score']
        for asset_key, score in eval_score['asset_scores'].items():
            row[f'{asset_key}_correct'] = score

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Walk-forward fold scoring
# ---------------------------------------------------------------------------


def score_walk_forward(
    df: pd.DataFrame,
    folds: list[dict],
) -> dict:
    """
    Score each walk-forward fold separately.

    Returns dict with per-fold scores, overall mean, std, and Sharpe-like ratio.
    """
    fold_scores = []
    fold_details = []

    for fold in folds:
        mask = (
            (df['date'] >= fold['test_start'].strftime('%Y-%m-%d'))
            & (df['date'] <= fold['test_end'].strftime('%Y-%m-%d'))
        )
        fold_df = df[mask]

        if fold_df.empty:
            fold_details.append({
                'fold': fold['fold'],
                'test_start': fold['test_start'].strftime('%Y-%m-%d'),
                'test_end': fold['test_end'].strftime('%Y-%m-%d'),
                'evaluations': 0,
                'score': None,
            })
            continue

        valid_scores = fold_df['multi_asset_score'].dropna()
        if valid_scores.empty:
            continue

        fold_score = float(valid_scores.mean()) * 100
        fold_scores.append(fold_score)

        # Per-quadrant counts in this fold
        quadrant_counts = fold_df['quadrant'].value_counts().to_dict()

        fold_details.append({
            'fold': fold['fold'],
            'test_start': fold['test_start'].strftime('%Y-%m-%d'),
            'test_end': fold['test_end'].strftime('%Y-%m-%d'),
            'evaluations': int(len(valid_scores)),
            'score': round(fold_score, 1),
            'quadrant_counts': quadrant_counts,
        })

    if not fold_scores:
        return {'fold_details': fold_details, 'mean': None, 'std': None, 'sharpe': None}

    mean_score = float(np.mean(fold_scores))
    std_score = float(np.std(fold_scores, ddof=1)) if len(fold_scores) > 1 else 0.0
    sharpe = mean_score / std_score if std_score > 0 else float('inf')

    return {
        'fold_details': fold_details,
        'fold_scores': [round(s, 1) for s in fold_scores],
        'mean': round(mean_score, 1),
        'std': round(std_score, 1),
        'sharpe': round(sharpe, 2),
        'n_folds': len(fold_scores),
    }


# ---------------------------------------------------------------------------
# Per-verdict and per-asset scoring
# ---------------------------------------------------------------------------


def score_results(df: pd.DataFrame) -> dict:
    """
    Compute aggregate accuracy metrics with quadrant-led scoring.

    Composite = 50% multi-asset accuracy + 25% real-return ordering + 25% drawdown ordering.
    """
    report = {
        'overall': {},
        'per_quadrant': {},
        'per_asset': {},
    }

    # Overall multi-asset score
    valid_scores = df['multi_asset_score'].dropna()
    if not valid_scores.empty:
        report['overall']['multi_asset_accuracy'] = round(
            float(valid_scores.mean()) * 100, 1
        )
        report['overall']['total_evaluations'] = int(len(valid_scores))

    # Per-asset accuracy
    for asset_key, config in SCORING_ASSETS.items():
        col = f'{asset_key}_correct'
        if col not in df.columns:
            continue
        valid = df[col].dropna()
        if valid.empty:
            continue
        report['per_asset'][asset_key] = {
            'label': config['label'],
            'weight': config['weight'],
            'accuracy': round(float(valid.mean()) * 100, 1),
            'count': int(len(valid)),
        }

    # Per-quadrant statistics
    for quadrant in QUADRANT_LABELS:
        mask = df['quadrant'] == quadrant
        subset = df[mask]
        if subset.empty:
            report['per_quadrant'][quadrant] = {'count': 0}
            continue

        stats = {'count': int(len(subset))}

        quad_scores = subset['multi_asset_score'].dropna()
        if not quad_scores.empty:
            stats['multi_asset_accuracy'] = round(
                float(quad_scores.mean()) * 100, 1
            )

        # Per-asset returns and accuracy for this quadrant
        for asset_key in SCORING_ASSETS:
            for w in FORWARD_WINDOWS:
                col = f'{asset_key}_fwd_{w}d'
                if col in subset.columns:
                    valid = subset[col].dropna()
                    if not valid.empty:
                        stats[f'{asset_key}_avg_{w}d'] = round(
                            float(valid.mean()) * 100, 2
                        )

            correct_col = f'{asset_key}_correct'
            if correct_col in subset.columns:
                valid = subset[correct_col].dropna()
                if not valid.empty:
                    stats[f'{asset_key}_accuracy'] = round(
                        float(valid.mean()) * 100, 1
                    )

        # S&P 500 real return average for this quadrant
        if 'sp500_real_fwd_90d' in subset.columns:
            real_valid = subset['sp500_real_fwd_90d'].dropna()
            if not real_valid.empty:
                stats['sp500_real_avg_90d'] = round(
                    float(real_valid.mean()) * 100, 2
                )

        # S&P 500 drawdown
        dd_col = 'sp500_max_dd_90d'
        if dd_col in subset.columns:
            dd_valid = subset[dd_col].dropna()
            if not dd_valid.empty:
                stats['sp500_avg_max_dd_90d'] = round(float(dd_valid.mean()) * 100, 2)
                stats['sp500_worst_max_dd_90d'] = round(float(dd_valid.min()) * 100, 2)

        report['per_quadrant'][quadrant] = stats

    # Magnitude ordering: real S&P 500 returns should follow QUADRANT_LABELS order
    # Goldilocks > Deflation Risk > Reflation > Stagflation
    quadrant_real_returns = {}
    for q in QUADRANT_LABELS:
        ret = report['per_quadrant'].get(q, {}).get('sp500_real_avg_90d')
        if ret is not None:
            quadrant_real_returns[q] = ret
    if len(quadrant_real_returns) >= 3:
        ordered = [quadrant_real_returns.get(q) for q in QUADRANT_LABELS if q in quadrant_real_returns]
        report['overall']['real_return_ordering_correct'] = all(
            ordered[i] >= ordered[i + 1] for i in range(len(ordered) - 1)
        )
        report['overall']['sp500_real_avg_90d_by_quadrant'] = quadrant_real_returns

    # Drawdown ordering: should worsen Goldilocks → Stagflation
    quadrant_drawdowns = {}
    for q in QUADRANT_LABELS:
        dd = report['per_quadrant'].get(q, {}).get('sp500_avg_max_dd_90d')
        if dd is not None:
            quadrant_drawdowns[q] = dd
    if len(quadrant_drawdowns) >= 3:
        ordered = [quadrant_drawdowns.get(q) for q in QUADRANT_LABELS if q in quadrant_drawdowns]
        report['overall']['drawdown_ordering_correct'] = all(
            ordered[i] >= ordered[i + 1] for i in range(len(ordered) - 1)
        )
        report['overall']['sp500_avg_max_dd_by_quadrant'] = quadrant_drawdowns

    # Composite score: 50% accuracy + 25% real-return ordering + 25% drawdown ordering
    scores = []
    score_weights = []
    if 'multi_asset_accuracy' in report['overall']:
        scores.append(report['overall']['multi_asset_accuracy'])
        score_weights.append(0.50)
    if report['overall'].get('real_return_ordering_correct') is not None:
        scores.append(100.0 if report['overall']['real_return_ordering_correct'] else 0.0)
        score_weights.append(0.25)
    if report['overall'].get('drawdown_ordering_correct') is not None:
        scores.append(100.0 if report['overall']['drawdown_ordering_correct'] else 0.0)
        score_weights.append(0.25)

    if scores and sum(score_weights) > 0:
        composite = sum(s * w for s, w in zip(scores, score_weights)) / sum(score_weights)
        report['overall']['composite_score'] = round(composite, 1)

    return report


# ---------------------------------------------------------------------------
# Economic plausibility checks
# ---------------------------------------------------------------------------


def check_plausibility(df: pd.DataFrame) -> dict:
    """
    Hard-fail plausibility checks.

    Returns dict with pass/fail for each check and details.
    """
    checks = {}

    # Check 1: March 2020 must NOT have Goldilocks as DOMINANT quadrant
    mar_2020 = df[
        (df['date'] >= '2020-02-15') & (df['date'] <= '2020-04-15')
    ]
    if not mar_2020.empty:
        quad_counts = mar_2020['quadrant'].value_counts()
        dominant = quad_counts.index[0] if not quad_counts.empty else None
        checks['march_2020_not_goldilocks'] = {
            'pass': dominant != 'Goldilocks',
            'dominant_quadrant': dominant,
            'quadrants_found': mar_2020['quadrant'].unique().tolist(),
            'quadrant_distribution': quad_counts.to_dict(),
        }
    else:
        checks['march_2020_not_goldilocks'] = {
            'pass': True,
            'note': 'No evaluation dates in range',
        }

    # Check 2: 2022 must have Stagflation present
    year_2022 = df[
        (df['date'] >= '2022-01-01') & (df['date'] <= '2022-12-31')
    ]
    if not year_2022.empty:
        quad_counts = year_2022['quadrant'].value_counts()
        quadrants_present = quad_counts.index.tolist()
        checks['2022_stagflation_present'] = {
            'pass': 'Stagflation' in quadrants_present,
            'quadrants_found': quadrants_present,
            'quadrant_distribution': quad_counts.to_dict(),
        }
    else:
        checks['2022_stagflation_present'] = {
            'pass': True,
            'note': 'No evaluation dates in range',
        }

    # Check 3: Quadrant stability — average duration ≥ 3 months
    if not df.empty:
        df_sorted = df.sort_values('date').reset_index(drop=True)
        durations = []
        current_quad = df_sorted.iloc[0]['quadrant']
        current_start = 0
        for i in range(1, len(df_sorted)):
            if df_sorted.iloc[i]['quadrant'] != current_quad:
                durations.append(i - current_start)
                current_quad = df_sorted.iloc[i]['quadrant']
                current_start = i
        durations.append(len(df_sorted) - current_start)

        avg_duration = float(np.mean(durations)) if durations else 0.0
        checks['quadrant_stability'] = {
            'pass': avg_duration >= 3.0,
            'avg_duration_months': round(avg_duration, 1),
            'total_transitions': len(durations) - 1,
            'min_duration': int(min(durations)) if durations else 0,
            'max_duration': int(max(durations)) if durations else 0,
        }

    all_pass = all(c.get('pass', False) for c in checks.values())
    return {
        'all_pass': all_pass,
        'checks': checks,
    }


# ---------------------------------------------------------------------------
# CPCV — Combinatorial Purged Cross-Validation
# ---------------------------------------------------------------------------


def run_cpcv(
    df: pd.DataFrame,
    k: int = 6,
    p: int = 2,
    purge_months: int = 3,
    embargo_months: int = 1,
) -> dict:
    """
    Run Combinatorial Purged Cross-Validation.

    Splits the full dataset into k time-ordered groups, uses C(k,p) combinations
    where p groups form the test set. Purges observations within purge_months
    of test boundaries and embargoes embargo_months after test boundaries.

    Returns dict with PBO (probability of backtest overfitting) and
    distribution of out-of-sample scores.
    """
    df_sorted = df.sort_values('date').reset_index(drop=True)
    dates = pd.to_datetime(df_sorted['date'])
    n = len(df_sorted)

    # Split into k time-ordered groups
    group_size = n // k
    groups = []
    for i in range(k):
        start_idx = i * group_size
        end_idx = start_idx + group_size if i < k - 1 else n
        groups.append(list(range(start_idx, end_idx)))

    # Generate all C(k,p) combinations of test groups
    test_combos = list(combinations(range(k), p))

    oos_scores = []  # Out-of-sample scores
    is_scores = []   # In-sample scores

    for combo in test_combos:
        test_indices = set()
        for g in combo:
            test_indices.update(groups[g])

        train_indices = set(range(n)) - test_indices

        # Purge: remove training observations within purge_months of test boundaries
        purge_days = purge_months * 30
        embargo_days = embargo_months * 30

        test_dates = dates.iloc[sorted(test_indices)]
        if test_dates.empty:
            continue

        test_start = test_dates.min()
        test_end = test_dates.max()

        purged_train = set()
        for idx in train_indices:
            obs_date = dates.iloc[idx]
            # Purge if within purge_months before test start
            if (test_start - pd.Timedelta(days=purge_days)) <= obs_date < test_start:
                continue
            # Embargo if within embargo_months after test end
            if test_end < obs_date <= (test_end + pd.Timedelta(days=embargo_days)):
                continue
            purged_train.add(idx)

        # Score test set
        test_df = df_sorted.iloc[sorted(test_indices)]
        test_scores = test_df['multi_asset_score'].dropna()
        if test_scores.empty:
            continue
        oos_score = float(test_scores.mean())

        # Score train set
        train_df = df_sorted.iloc[sorted(purged_train)]
        train_scores = train_df['multi_asset_score'].dropna()
        if train_scores.empty:
            continue
        is_score = float(train_scores.mean())

        oos_scores.append(oos_score)
        is_scores.append(is_score)

    if not oos_scores:
        return {'pbo': None, 'n_paths': 0}

    # PBO = fraction of paths where OOS < IS (overfit)
    n_overfit = sum(1 for oos, ins in zip(oos_scores, is_scores) if oos < ins)
    pbo = n_overfit / len(oos_scores)

    return {
        'pbo': round(pbo, 3),
        'n_paths': len(oos_scores),
        'oos_mean': round(float(np.mean(oos_scores)) * 100, 1),
        'oos_std': round(float(np.std(oos_scores)) * 100, 1),
        'is_mean': round(float(np.mean(is_scores)) * 100, 1),
        'oos_scores': [round(s * 100, 1) for s in oos_scores],
    }


# ---------------------------------------------------------------------------
# DSR — Deflated Sharpe Ratio
# ---------------------------------------------------------------------------


def compute_dsr(
    observed_sharpe: float,
    n_trials: int,
    n_observations: int,
    std_sharpe: float,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> dict:
    """
    Compute the Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014).

    Tests whether the observed Sharpe ratio is statistically significant
    after correcting for the number of trials.

    Returns dict with DSR value, expected max Sharpe under null, and p-value.
    """
    if n_trials <= 1 or n_observations <= 1 or std_sharpe <= 0:
        return {'dsr': None, 'p_value': None, 'significant': None}

    # Expected maximum Sharpe ratio under the null (multiple testing correction)
    # E[max(SR)] ≈ std_SR * ((1 - γ) * Φ^(-1)(1 - 1/N) + γ * Φ^(-1)(1 - 1/(N*e)))
    # Simplified: E[max(SR)] ≈ sqrt(2 * ln(N)) - (ln(π) + ln(ln(N))) / (2 * sqrt(2 * ln(N)))
    ln_n = math.log(max(n_trials, 2))
    expected_max_sr = (
        math.sqrt(2 * ln_n)
        - (math.log(math.pi) + math.log(ln_n)) / (2 * math.sqrt(2 * ln_n))
    ) * std_sharpe

    # Adjust Sharpe for skewness and kurtosis
    # SR* = SR * sqrt(1 + (skew/6)*SR - ((kurtosis-3)/24)*SR^2)
    sr_adj = observed_sharpe
    adj_factor = 1.0 + (skewness / 6.0) * observed_sharpe - ((kurtosis - 3.0) / 24.0) * observed_sharpe ** 2
    if adj_factor > 0:
        sr_adj = observed_sharpe * math.sqrt(adj_factor)

    # DSR = Φ((SR* - E[max(SR)]) * sqrt(n-1) / sqrt(1 - skew*SR* + ((kurtosis-3)/4)*SR*^2))
    denom_sq = 1.0 - skewness * sr_adj + ((kurtosis - 3.0) / 4.0) * sr_adj ** 2
    if denom_sq <= 0:
        denom_sq = 1.0

    z_score = (sr_adj - expected_max_sr) * math.sqrt(max(n_observations - 1, 1)) / math.sqrt(denom_sq)

    # p-value from standard normal CDF
    from scipy.stats import norm
    p_value = 1.0 - norm.cdf(z_score)

    return {
        'dsr': round(z_score, 4),
        'p_value': round(float(p_value), 4),
        'significant': bool(p_value <= 0.05),
        'observed_sharpe': round(observed_sharpe, 4),
        'expected_max_sharpe': round(expected_max_sr, 4),
        'n_trials': n_trials,
        'n_observations': n_observations,
    }


# ---------------------------------------------------------------------------
# Risk filter sensitivity analysis
# ---------------------------------------------------------------------------

# Configurations test how Stressed-override affects scoring.
# Each config defines which risk states receive the Stressed S&P 500 override.
RISK_FILTER_CONFIGS = [
    {'label': 'No risk filter (quadrant only)', 'stressed_override': False},
    {'label': 'Stressed override (default)', 'stressed_override': True},
    {'label': 'Elevated+Stressed override', 'elevated_override': True},
]


def run_risk_filter_sensitivity(
    histories: dict[str, pd.DataFrame],
    scoring_assets: dict[str, pd.Series],
    cpi_series: Optional[pd.Series] = None,
    start_year: int = FOLD_START_YEAR,
    end_year: int = FOLD_END_YEAR,
) -> list[dict]:
    """
    Test how risk-state filtering affects quadrant-led scoring.

    Since the quadrant directly determines expectations (no weights to vary),
    sensitivity analysis focuses on the impact of risk overrides.
    """
    folds = generate_folds(start_year, end_year)
    results = []

    for config in RISK_FILTER_CONFIGS:
        label = config['label']
        print(f'  Testing: {label}...')

        df = run_backtest(histories, scoring_assets, cpi_series, start_year, end_year)
        if df.empty:
            results.append({'label': label, 'error': 'No results'})
            continue

        # Apply risk filter variant
        if not config.get('stressed_override', True):
            # No override: re-score without Stressed S&P override
            df = _rescore_without_risk_override(df, cpi_series)
        elif config.get('elevated_override', False):
            # Elevated+Stressed: expand override to Elevated risk
            df = _rescore_with_elevated_override(df, cpi_series)

        wf_scores = score_walk_forward(df, folds)
        agg_scores = score_results(df)

        results.append({
            'label': label,
            'composite_score': agg_scores['overall'].get('composite_score'),
            'multi_asset_accuracy': agg_scores['overall'].get('multi_asset_accuracy'),
            'wf_mean': wf_scores.get('mean'),
            'wf_std': wf_scores.get('std'),
            'wf_sharpe': wf_scores.get('sharpe'),
            'fold_scores': wf_scores.get('fold_scores', []),
            'real_return_ordering': agg_scores['overall'].get('real_return_ordering_correct'),
            'drawdown_ordering': agg_scores['overall'].get('drawdown_ordering_correct'),
        })

    return results


def _rescore_without_risk_override(df: pd.DataFrame, cpi_series: Optional[pd.Series]) -> pd.DataFrame:
    """Re-score using pure quadrant expectations (no Stressed override)."""
    df = df.copy()
    for idx, row in df.iterrows():
        quadrant = row['quadrant']
        expectations = dict(QUADRANT_EXPECTATIONS.get(quadrant, QUADRANT_EXPECTATIONS['Goldilocks']))
        # No Stressed override applied

        real_sp500 = row.get('sp500_real_fwd_90d')
        asset_returns = {}
        for asset_key in SCORING_ASSETS:
            col = f'{asset_key}_fwd_90d'
            if col in df.columns:
                asset_returns[asset_key] = row[col]

        eval_score = score_single_evaluation(expectations, asset_returns, real_sp500_return=real_sp500)
        df.at[idx, 'multi_asset_score'] = eval_score['weighted_score']
        for asset_key, score in eval_score['asset_scores'].items():
            df.at[idx, f'{asset_key}_correct'] = score
    return df


def _rescore_with_elevated_override(df: pd.DataFrame, cpi_series: Optional[pd.Series]) -> pd.DataFrame:
    """Re-score with Elevated+Stressed both overriding S&P to negative."""
    df = df.copy()
    for idx, row in df.iterrows():
        quadrant = row['quadrant']
        risk_state = row['risk_state']
        expectations = dict(QUADRANT_EXPECTATIONS.get(quadrant, QUADRANT_EXPECTATIONS['Goldilocks']))

        if risk_state in ('Stressed', 'Elevated'):
            expectations['sp500'] = 'negative'

        real_sp500 = row.get('sp500_real_fwd_90d')
        asset_returns = {}
        for asset_key in SCORING_ASSETS:
            col = f'{asset_key}_fwd_90d'
            if col in df.columns:
                asset_returns[asset_key] = row[col]

        eval_score = score_single_evaluation(expectations, asset_returns, real_sp500_return=real_sp500)
        df.at[idx, 'multi_asset_score'] = eval_score['weighted_score']
        for asset_key, score in eval_score['asset_scores'].items():
            df.at[idx, f'{asset_key}_correct'] = score
    return df


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_report(
    df: pd.DataFrame,
    agg_scores: dict,
    wf_scores: dict,
    plausibility: dict,
    cpcv_result: dict,
    dsr_result: dict,
    sensitivity: list[dict],
    baseline_score: float = 52.3,
) -> str:
    """Generate comprehensive markdown backtest report."""
    lines = []
    lines.append('# Market Conditions Backtest Report (Quadrant-Led)')
    lines.append(f'\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'Evaluation period: {df["date"].iloc[0]} to {df["date"].iloc[-1]}')
    lines.append(f'Total evaluations: {len(df)}')
    lines.append(f'Baseline (k-means): {baseline_score}/100')
    lines.append('')
    lines.append('Scoring: S&P 500 uses real (inflation-adjusted) returns. '
                 'Treasuries and Gold use nominal directional accuracy.')

    # === Overall Score ===
    overall = agg_scores.get('overall', {})
    composite = overall.get('composite_score')
    if composite is not None:
        delta = composite - baseline_score
        status = 'PASS' if delta > 0 else 'FAIL'
        lines.append(f'\n## Overall Composite Score: {composite}/100 ({status}: {"+" if delta > 0 else ""}{delta:.1f} vs baseline)')
        lines.append('')
        lines.append('Components:')
        if 'multi_asset_accuracy' in overall:
            lines.append(f'- Multi-asset accuracy (50% weight): {overall["multi_asset_accuracy"]}%')
        if 'real_return_ordering_correct' in overall:
            ret_order = 'PASS' if overall['real_return_ordering_correct'] else 'FAIL'
            lines.append(f'- Real return magnitude ordering Goldilocks→Stagflation (25% weight): {ret_order}')
        if 'drawdown_ordering_correct' in overall:
            dd_order = 'PASS' if overall['drawdown_ordering_correct'] else 'FAIL'
            lines.append(f'- Drawdown ordering Goldilocks→Stagflation (25% weight): {dd_order}')

    # === Walk-Forward Results ===
    lines.append('\n## Walk-Forward Validation')
    lines.append('')
    if wf_scores.get('mean') is not None:
        lines.append(f'- Mean fold score: {wf_scores["mean"]}%')
        lines.append(f'- Std deviation: {wf_scores["std"]}%')
        lines.append(f'- Sharpe-like ratio: {wf_scores["sharpe"]}')
        lines.append(f'- Number of folds: {wf_scores["n_folds"]}')

    lines.append('')
    lines.append('| Fold | Period | Evaluations | Score |')
    lines.append('|------|--------|-------------|-------|')
    for fd in wf_scores.get('fold_details', []):
        score_str = f'{fd["score"]}%' if fd.get('score') is not None else '—'
        lines.append(
            f'| {fd["fold"]} | {fd["test_start"]} to {fd["test_end"]} | '
            f'{fd["evaluations"]} | {score_str} |'
        )

    # === Per-Asset Accuracy ===
    lines.append('\n## Per-Asset Accuracy')
    lines.append('')
    lines.append('| Asset | Weight | Accuracy | Evaluations |')
    lines.append('|-------|--------|----------|-------------|')
    for asset_key in SCORING_ASSETS:
        stats = agg_scores['per_asset'].get(asset_key, {})
        if not stats:
            continue
        lines.append(
            f'| {stats["label"]} | {stats["weight"]:.0%} | '
            f'{stats["accuracy"]}% | {stats["count"]} |'
        )

    # === Per-Quadrant Summary ===
    lines.append('\n## Per-Quadrant Summary')
    lines.append('')
    lines.append('| Quadrant | Count | Multi-Asset Accuracy | S&P 500 Real Avg 90d | S&P 500 Avg Max DD |')
    lines.append('|----------|-------|---------------------|----------------------|-------------------|')
    for quadrant in QUADRANT_LABELS:
        stats = agg_scores['per_quadrant'].get(quadrant, {})
        count = stats.get('count', 0)
        if count == 0:
            lines.append(f'| {quadrant} | 0 | — | — | — |')
            continue
        ma = stats.get('multi_asset_accuracy', '—')
        sp_real = stats.get('sp500_real_avg_90d', '—')
        sp_dd = stats.get('sp500_avg_max_dd_90d', '—')
        fmt = lambda v: f'{v}%' if isinstance(v, (int, float)) else v
        lines.append(
            f'| {quadrant} | {count} | {fmt(ma)} | {fmt(sp_real)} | {fmt(sp_dd)} |'
        )

    # === Per-Quadrant Detail ===
    lines.append('\n## Per-Quadrant Asset Detail')
    for quadrant in QUADRANT_LABELS:
        stats = agg_scores['per_quadrant'].get(quadrant, {})
        if stats.get('count', 0) == 0:
            continue
        expected = QUADRANT_EXPECTATIONS.get(quadrant, {})
        lines.append(f'\n### {quadrant} (n={stats["count"]})')
        for asset_key, config in SCORING_ASSETS.items():
            accuracy = stats.get(f'{asset_key}_accuracy')
            if accuracy is None:
                continue
            direction = expected.get(asset_key, 'neutral')
            returns_parts = []
            for w in FORWARD_WINDOWS:
                avg = stats.get(f'{asset_key}_avg_{w}d')
                if avg is not None:
                    returns_parts.append(f'{w}d avg={avg}%')
            real_avg = stats.get('sp500_real_avg_90d') if asset_key == 'sp500' else None
            if real_avg is not None:
                returns_parts.append(f'real 90d avg={real_avg}%')
            returns_str = ', '.join(returns_parts) if returns_parts else '—'
            lines.append(f'- **{config["label"]}** (expect {direction}): accuracy={accuracy}% | {returns_str}')

    # === Economic Plausibility ===
    lines.append('\n## Economic Plausibility Checks')
    lines.append('')
    all_pass = plausibility.get('all_pass', False)
    lines.append(f'**Overall: {"PASS" if all_pass else "FAIL"}**')
    lines.append('')
    for check_name, check_data in plausibility.get('checks', {}).items():
        status = 'PASS' if check_data.get('pass') else 'FAIL'
        lines.append(f'- **{check_name}**: {status}')
        for k, v in check_data.items():
            if k != 'pass':
                lines.append(f'  - {k}: {v}')

    # === CPCV ===
    lines.append('\n## Combinatorial Purged Cross-Validation (CPCV)')
    lines.append('')
    if cpcv_result.get('pbo') is not None:
        pbo = cpcv_result['pbo']
        status = 'PASS' if pbo <= 0.5 else 'FAIL (likely overfit)'
        lines.append(f'- PBO (Probability of Backtest Overfitting): {pbo} ({status})')
        lines.append(f'- Number of paths tested: {cpcv_result["n_paths"]}')
        lines.append(f'- OOS mean accuracy: {cpcv_result["oos_mean"]}%')
        lines.append(f'- OOS std: {cpcv_result["oos_std"]}%')
        lines.append(f'- IS mean accuracy: {cpcv_result["is_mean"]}%')
    else:
        lines.append('- CPCV could not be computed (insufficient data)')

    # === DSR ===
    lines.append('\n## Deflated Sharpe Ratio (DSR)')
    lines.append('')
    if dsr_result.get('dsr') is not None:
        sig = 'SIGNIFICANT' if dsr_result['significant'] else 'NOT SIGNIFICANT'
        lines.append(f'- DSR z-score: {dsr_result["dsr"]}')
        lines.append(f'- p-value: {dsr_result["p_value"]} ({sig})')
        lines.append(f'- Observed Sharpe: {dsr_result["observed_sharpe"]}')
        lines.append(f'- Expected max Sharpe (null): {dsr_result["expected_max_sharpe"]}')
        lines.append(f'- Number of trials corrected for: {dsr_result["n_trials"]}')
    else:
        lines.append('- DSR could not be computed')

    # === Risk Filter Sensitivity ===
    lines.append('\n## Risk Filter Sensitivity Analysis')
    lines.append('')
    lines.append('| Configuration | Composite | Multi-Asset | WF Mean | WF Std | WF Sharpe | DD Order | Ret Order |')
    lines.append('|---------------|-----------|-------------|---------|--------|-----------|----------|-----------|')
    for s in sensitivity:
        if 'error' in s:
            lines.append(f'| {s["label"]} | ERROR: {s["error"]} |')
            continue
        comp = f'{s["composite_score"]}' if s.get('composite_score') is not None else '—'
        ma = f'{s["multi_asset_accuracy"]}%' if s.get('multi_asset_accuracy') is not None else '—'
        wf_m = f'{s["wf_mean"]}%' if s.get('wf_mean') is not None else '—'
        wf_s = f'{s["wf_std"]}%' if s.get('wf_std') is not None else '—'
        wf_sh = f'{s["wf_sharpe"]}' if s.get('wf_sharpe') is not None else '—'
        dd = 'PASS' if s.get('drawdown_ordering') else 'FAIL'
        ret = 'PASS' if s.get('real_return_ordering') else 'FAIL'
        lines.append(f'| {s["label"]} | {comp} | {ma} | {wf_m} | {wf_s} | {wf_sh} | {dd} | {ret} |')

    # Find winning config
    valid_configs = [s for s in sensitivity if 'error' not in s and s.get('wf_sharpe') is not None]
    if valid_configs:
        winner = max(valid_configs, key=lambda x: x['wf_sharpe'])
        lines.append(f'\n**Recommended configuration:** {winner["label"]}')
        lines.append(f'- Rationale: Highest walk-forward Sharpe ratio ({winner["wf_sharpe"]})')

    # === Final Recommendation ===
    lines.append('\n## Final Recommendation')
    lines.append('')

    passes_plausibility = plausibility.get('all_pass', False)
    passes_cpcv = cpcv_result.get('pbo') is not None and cpcv_result['pbo'] <= 0.5
    beats_baseline = composite is not None and composite > baseline_score

    if beats_baseline and passes_plausibility:
        lines.append(f'**PASS: Composite score {composite}/100 beats baseline {baseline_score}/100 by {composite - baseline_score:.1f} points.**')
        lines.append('')
        if passes_cpcv:
            lines.append('The result passes CPCV overfitting check. Phase 11 UI work can proceed.')
        else:
            lines.append('Note: CPCV flagged potential overfitting concerns. Proceed with caution.')
        if dsr_result.get('significant'):
            lines.append('DSR confirms statistical significance.')
        elif dsr_result.get('p_value') is not None:
            lines.append(f'DSR p-value {dsr_result["p_value"]} — review significance threshold.')
    else:
        lines.append(f'**FAIL: Composite score {composite}/100 does {"not beat" if not beats_baseline else "beats"} baseline {baseline_score}/100.**')
        if not passes_plausibility:
            lines.append('Economic plausibility checks failed.')
        lines.append('')
        lines.append('DO NOT proceed to Phase 11. Investigate and iterate on the conditions engine.')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('  Market Conditions Backtest (Quadrant-Led)')
    print('=' * 60)

    # Step 1: Load data
    histories = load_dimension_histories('2003-01-01')
    if 'quadrant' not in histories:
        print('ERROR: Cannot run backtest without quadrant history.')
        sys.exit(1)

    print('\nLoading scoring assets...')
    scoring_assets = load_scoring_assets()
    if not scoring_assets:
        print('ERROR: No scoring asset data available.')
        sys.exit(1)

    print('\nLoading CPI for real-return calculation...')
    cpi_series = load_cpi_series()
    if cpi_series is not None:
        print(f'  CPI: {cpi_series.index[0].strftime("%Y-%m-%d")} to {cpi_series.index[-1].strftime("%Y-%m-%d")} ({len(cpi_series)} points)')
    else:
        print('  WARNING: CPI data not available — S&P 500 will use nominal returns')

    # Step 2: Run full backtest
    print('\nRunning full backtest...')
    df = run_backtest(histories, scoring_assets, cpi_series)
    if df.empty:
        print('ERROR: No results generated.')
        sys.exit(1)
    print(f'  {len(df)} evaluation dates scored')

    # Save raw results
    csv_path = RESULTS_DIR / 'conditions_backtest_results.csv'
    df.to_csv(csv_path, index=False)
    print(f'  Raw results: {csv_path}')

    # Step 3: Aggregate scoring
    print('\nScoring results...')
    agg_scores = score_results(df)

    # Step 4: Walk-forward validation
    print('\nRunning walk-forward validation...')
    folds = generate_folds()
    wf_scores = score_walk_forward(df, folds)
    print(f'  Mean fold score: {wf_scores.get("mean")}%')
    print(f'  Std: {wf_scores.get("std")}%')
    print(f'  Sharpe: {wf_scores.get("sharpe")}')

    # Step 5: Economic plausibility
    print('\nChecking economic plausibility...')
    plausibility = check_plausibility(df)
    print(f'  All checks pass: {plausibility["all_pass"]}')

    # Step 6: Risk filter sensitivity analysis
    print('\nRunning risk filter sensitivity analysis...')
    sensitivity = run_risk_filter_sensitivity(histories, scoring_assets, cpi_series)

    valid_configs = [s for s in sensitivity if 'error' not in s and s.get('wf_sharpe') is not None]
    if valid_configs:
        winner = max(valid_configs, key=lambda x: x['wf_sharpe'])
        print(f'  Winner: {winner["label"]} (Sharpe={winner["wf_sharpe"]})')

    # Step 7: CPCV
    print('\nRunning CPCV (k=6, p=2, purge=3mo, embargo=1mo)...')
    cpcv_result = run_cpcv(df)
    print(f'  PBO: {cpcv_result.get("pbo")}')

    # Step 8: DSR
    print('\nComputing Deflated Sharpe Ratio...')
    n_trials = len(RISK_FILTER_CONFIGS)
    wf_sharpe = wf_scores.get('sharpe', 0.0)
    fold_scores_arr = np.array(wf_scores.get('fold_scores', []))

    if len(fold_scores_arr) > 1 and wf_sharpe is not None:
        all_sharpes = [s.get('wf_sharpe', 0.0) for s in sensitivity if s.get('wf_sharpe') is not None]
        std_sharpe = float(np.std(all_sharpes, ddof=1)) if len(all_sharpes) > 1 else 1.0
        skewness = float(pd.Series(fold_scores_arr).skew())
        kurtosis = float(pd.Series(fold_scores_arr).kurtosis()) + 3.0

        dsr_result = compute_dsr(
            observed_sharpe=wf_sharpe,
            n_trials=n_trials,
            n_observations=len(fold_scores_arr),
            std_sharpe=std_sharpe,
            skewness=skewness,
            kurtosis=kurtosis,
        )
    else:
        dsr_result = {'dsr': None, 'p_value': None, 'significant': None}

    print(f'  DSR z-score: {dsr_result.get("dsr")}')
    print(f'  p-value: {dsr_result.get("p_value")}')

    # Step 9: Generate report
    print('\nGenerating report...')
    report = generate_report(
        df, agg_scores, wf_scores, plausibility,
        cpcv_result, dsr_result, sensitivity,
    )

    report_path = RESULTS_DIR / 'conditions_backtest_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f'  Report: {report_path}')

    # Save structured results
    structured = {
        'overall': agg_scores.get('overall', {}),
        'walk_forward': wf_scores,
        'per_quadrant': agg_scores.get('per_quadrant', {}),
        'per_asset': agg_scores.get('per_asset', {}),
        'plausibility': plausibility,
        'cpcv': cpcv_result,
        'dsr': dsr_result,
        'sensitivity': sensitivity,
    }
    json_path = RESULTS_DIR / 'conditions_backtest_scores.json'
    with open(json_path, 'w') as f:
        json.dump(structured, f, indent=2, default=str)
    print(f'  Scores: {json_path}')

    # Print summary
    overall = agg_scores.get('overall', {})
    composite = overall.get('composite_score')
    baseline = 52.3
    print('\n' + '=' * 60)
    if composite is not None:
        delta = composite - baseline
        print(f'  COMPOSITE SCORE: {composite}/100 ({"+" if delta > 0 else ""}{delta:.1f} vs {baseline} baseline)')
    if 'multi_asset_accuracy' in overall:
        print(f'  Multi-asset accuracy: {overall["multi_asset_accuracy"]}%')
    if 'real_return_ordering_correct' in overall:
        ret = 'PASS' if overall['real_return_ordering_correct'] else 'FAIL'
        print(f'  Real return ordering (Goldilocks→Stagflation): {ret}')
    if 'drawdown_ordering_correct' in overall:
        dd = 'PASS' if overall['drawdown_ordering_correct'] else 'FAIL'
        print(f'  Drawdown ordering: {dd}')
    print(f'  Plausibility: {"PASS" if plausibility["all_pass"] else "FAIL"}')
    if cpcv_result.get('pbo') is not None:
        print(f'  CPCV PBO: {cpcv_result["pbo"]} ({"PASS" if cpcv_result["pbo"] <= 0.5 else "FAIL"})')
    if dsr_result.get('p_value') is not None:
        print(f'  DSR p-value: {dsr_result["p_value"]} ({"SIGNIFICANT" if dsr_result["significant"] else "NOT SIGNIFICANT"})')

    # Per-quadrant real returns
    real_returns_by_quad = overall.get('sp500_real_avg_90d_by_quadrant', {})
    if real_returns_by_quad:
        print('')
        print('  S&P 500 real 90d returns by quadrant:')
        for q in QUADRANT_LABELS:
            r = real_returns_by_quad.get(q)
            if r is not None:
                print(f'    {q}: {r}%')

    print('')
    for asset_key in SCORING_ASSETS:
        stats = agg_scores['per_asset'].get(asset_key, {})
        if stats:
            print(f'  {stats["label"]}: {stats["accuracy"]}% accurate ({stats["count"]} evals)')

    print('=' * 60)

    # Return composite for testing
    return composite


if __name__ == '__main__':
    main()
