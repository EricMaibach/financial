"""
Bitcoin / Liquidity Dimension Validation — Walk-Forward Backtest

Tests whether the Liquidity dimension (Expanding/Neutral/Contracting) predicts
Bitcoin 90-day forward returns.  This is SEPARATE from the main composite
backtest — Bitcoin is orthogonal to the Growth×Inflation quadrant but
correlates 0.94 with global M2 (~90-day lag, per Lyn Alden research).

The result informs how Phase 11 presents conditions context on the crypto page:
  - Strong accuracy → "Liquidity is expanding — historically favorable for Bitcoin (X% accuracy)"
  - Weak accuracy → honest acknowledgment of limited macro signal

Usage:
    PYTHONPATH=signaltrackers python3 signaltrackers/backtesting/bitcoin_liquidity_backtest.py

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

from signaltrackers.backtesting.regime_backtest import (
    load_csv,
    compute_forward_return,
    NEUTRAL_THRESHOLD,
)
from signaltrackers.market_conditions import compute_liquidity_history

warnings.filterwarnings('ignore', category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(__file__).resolve().parent / 'results'

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FORWARD_WINDOW = 90  # 90-day forward returns (matches M2 lag hypothesis)
EVAL_FREQUENCY_MONTHS = 1  # Monthly evaluation dates

# Bitcoin data starts Sep 2014; liquidity history starts earlier.
# Use 2014 as start year for the validation window.
FOLD_START_YEAR = 2014
FOLD_END_YEAR = 2025
FOLD_TEST_MONTHS = 24  # 2-year test windows (same as main backtest)

# ---------------------------------------------------------------------------
# Liquidity → Bitcoin directional expectations
# ---------------------------------------------------------------------------

# Expanding liquidity → historically favorable for Bitcoin (risk-on + M2 correlation)
# Contracting liquidity → historically unfavorable
# Neutral → no strong directional signal
LIQUIDITY_EXPECTATIONS = {
    'Strongly Expanding': 'positive',
    'Expanding': 'positive',
    'Neutral': 'neutral',
    'Contracting': 'negative',
    'Strongly Contracting': 'negative',
}

# Simplified 3-bucket grouping for reporting
LIQUIDITY_BUCKETS = {
    'Strongly Expanding': 'Expanding',
    'Expanding': 'Expanding',
    'Neutral': 'Neutral',
    'Contracting': 'Contracting',
    'Strongly Contracting': 'Contracting',
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_bitcoin_price() -> Optional[pd.Series]:
    """Load Bitcoin daily price series."""
    return load_csv('bitcoin_price')


# ---------------------------------------------------------------------------
# Walk-forward fold generation
# ---------------------------------------------------------------------------


def generate_folds(
    start_year: int = FOLD_START_YEAR,
    end_year: int = FOLD_END_YEAR,
    test_months: int = FOLD_TEST_MONTHS,
) -> list[dict]:
    """
    Generate walk-forward expanding window folds.

    Same methodology as the main conditions backtest.
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


# ---------------------------------------------------------------------------
# Core backtest
# ---------------------------------------------------------------------------


def run_bitcoin_liquidity_backtest(
    liquidity_history: pd.DataFrame,
    bitcoin_price: pd.Series,
    start_year: int = FOLD_START_YEAR,
    end_year: int = FOLD_END_YEAR,
) -> pd.DataFrame:
    """
    Run the Bitcoin / Liquidity validation over monthly evaluation dates.

    For each evaluation date:
      1. Get the liquidity state (point-in-time, no lookahead)
      2. Map to expected Bitcoin direction
      3. Compute 90-day forward Bitcoin return
      4. Score directional accuracy

    Returns DataFrame with one row per evaluation date.
    """
    # Need 90 days of forward data
    last_btc_date = bitcoin_price.index[-1]
    end_date = min(
        pd.Timestamp(f'{end_year}-12-31'),
        last_btc_date - pd.Timedelta(days=FORWARD_WINDOW),
    )

    # Bitcoin reliable data starts mid-Sep 2014
    btc_start = bitcoin_price.index[0]
    start_date = max(pd.Timestamp(f'{start_year}-01-01'), btc_start)

    eval_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq=f'{EVAL_FREQUENCY_MONTHS}ME',
    )

    rows = []
    for eval_date in eval_dates:
        # Get liquidity state at eval_date (no lookahead)
        mask = liquidity_history['date'] <= eval_date
        subset = liquidity_history[mask]
        if subset.empty:
            continue

        liq_row = subset.iloc[-1]
        liq_state = liq_row['state']
        liq_score = liq_row['score']

        # Map to 3-bucket
        liq_bucket = LIQUIDITY_BUCKETS.get(liq_state, 'Neutral')
        expected_direction = LIQUIDITY_EXPECTATIONS.get(liq_state, 'neutral')

        # Forward returns at multiple windows for context
        fwd_90d = compute_forward_return(bitcoin_price, eval_date, 90)
        fwd_30d = compute_forward_return(bitcoin_price, eval_date, 30)
        fwd_60d = compute_forward_return(bitcoin_price, eval_date, 60)

        if fwd_90d is None:
            continue

        # Score directional accuracy
        if expected_direction == 'positive':
            correct = 1.0 if fwd_90d > 0 else 0.0
        elif expected_direction == 'negative':
            correct = 1.0 if fwd_90d < 0 else 0.0
        elif expected_direction == 'neutral':
            correct = 1.0 if abs(fwd_90d) < NEUTRAL_THRESHOLD else 0.5
        else:
            correct = 0.5

        rows.append({
            'date': eval_date.strftime('%Y-%m-%d'),
            'liquidity_state': liq_state,
            'liquidity_bucket': liq_bucket,
            'liquidity_score': round(liq_score, 4),
            'expected_direction': expected_direction,
            'btc_fwd_30d': fwd_30d,
            'btc_fwd_60d': fwd_60d,
            'btc_fwd_90d': fwd_90d,
            'correct': correct,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_results(df: pd.DataFrame) -> dict:
    """Compute aggregate accuracy metrics per liquidity state."""
    report = {
        'overall': {},
        'per_state': {},
        'per_bucket': {},
    }

    # Overall accuracy
    valid = df['correct'].dropna()
    if not valid.empty:
        report['overall']['accuracy'] = round(float(valid.mean()) * 100, 1)
        report['overall']['total_evaluations'] = int(len(valid))
        report['overall']['correct_count'] = int(valid.sum())

    # Per liquidity state (5-state)
    for state in LIQUIDITY_EXPECTATIONS:
        mask = df['liquidity_state'] == state
        subset = df[mask]
        if subset.empty:
            report['per_state'][state] = {'count': 0}
            continue

        state_correct = subset['correct'].dropna()
        stats = {
            'count': int(len(subset)),
            'expected_direction': LIQUIDITY_EXPECTATIONS[state],
        }
        if not state_correct.empty:
            stats['accuracy'] = round(float(state_correct.mean()) * 100, 1)
            stats['correct_count'] = int(state_correct.sum())

        # Average forward returns
        for w in [30, 60, 90]:
            col = f'btc_fwd_{w}d'
            if col in subset.columns:
                fwd_valid = subset[col].dropna()
                if not fwd_valid.empty:
                    stats[f'avg_fwd_{w}d'] = round(float(fwd_valid.mean()) * 100, 2)
                    stats[f'median_fwd_{w}d'] = round(float(fwd_valid.median()) * 100, 2)

        report['per_state'][state] = stats

    # Per bucket (3-bucket: Expanding/Neutral/Contracting)
    for bucket in ['Expanding', 'Neutral', 'Contracting']:
        mask = df['liquidity_bucket'] == bucket
        subset = df[mask]
        if subset.empty:
            report['per_bucket'][bucket] = {'count': 0}
            continue

        bucket_correct = subset['correct'].dropna()
        stats = {'count': int(len(subset))}
        if not bucket_correct.empty:
            stats['accuracy'] = round(float(bucket_correct.mean()) * 100, 1)
            stats['correct_count'] = int(bucket_correct.sum())

        # Average 90d forward returns
        fwd_valid = subset['btc_fwd_90d'].dropna()
        if not fwd_valid.empty:
            stats['avg_fwd_90d'] = round(float(fwd_valid.mean()) * 100, 2)
            stats['median_fwd_90d'] = round(float(fwd_valid.median()) * 100, 2)
            stats['pct_positive'] = round(
                float((fwd_valid > 0).mean()) * 100, 1
            )

        report['per_bucket'][bucket] = stats

    # Return magnitude ordering: Expanding > Neutral > Contracting
    bucket_returns = {}
    for bucket in ['Expanding', 'Neutral', 'Contracting']:
        avg = report['per_bucket'].get(bucket, {}).get('avg_fwd_90d')
        if avg is not None:
            bucket_returns[bucket] = avg
    if len(bucket_returns) >= 2:
        ordered_vals = [bucket_returns.get(b) for b in ['Expanding', 'Neutral', 'Contracting'] if b in bucket_returns]
        report['overall']['return_ordering_correct'] = all(
            ordered_vals[i] >= ordered_vals[i + 1]
            for i in range(len(ordered_vals) - 1)
        )
        report['overall']['avg_fwd_90d_by_bucket'] = bucket_returns

    return report


def score_walk_forward(
    df: pd.DataFrame,
    folds: list[dict],
) -> dict:
    """Score each walk-forward fold. Same structure as main backtest."""
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

        valid_scores = fold_df['correct'].dropna()
        if valid_scores.empty:
            continue

        fold_score = float(valid_scores.mean()) * 100
        fold_scores.append(fold_score)

        # Per-bucket counts
        bucket_counts = fold_df['liquidity_bucket'].value_counts().to_dict()

        fold_details.append({
            'fold': fold['fold'],
            'test_start': fold['test_start'].strftime('%Y-%m-%d'),
            'test_end': fold['test_end'].strftime('%Y-%m-%d'),
            'evaluations': int(len(valid_scores)),
            'score': round(fold_score, 1),
            'bucket_counts': bucket_counts,
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
# CPCV — Combinatorial Purged Cross-Validation
# ---------------------------------------------------------------------------


def run_cpcv(
    df: pd.DataFrame,
    k: int = 6,
    p: int = 2,
    purge_months: int = 3,
    embargo_months: int = 1,
) -> dict:
    """Run CPCV on the Bitcoin/Liquidity validation results."""
    df_sorted = df.sort_values('date').reset_index(drop=True)
    dates = pd.to_datetime(df_sorted['date'])
    n = len(df_sorted)

    if n < k:
        return {'pbo': None, 'n_paths': 0}

    group_size = n // k
    groups = []
    for i in range(k):
        start_idx = i * group_size
        end_idx = start_idx + group_size if i < k - 1 else n
        groups.append(list(range(start_idx, end_idx)))

    test_combos = list(combinations(range(k), p))

    oos_scores = []
    is_scores = []

    for combo in test_combos:
        test_indices = set()
        for g in combo:
            test_indices.update(groups[g])

        train_indices = set(range(n)) - test_indices

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
            if (test_start - pd.Timedelta(days=purge_days)) <= obs_date < test_start:
                continue
            if test_end < obs_date <= (test_end + pd.Timedelta(days=embargo_days)):
                continue
            purged_train.add(idx)

        test_df = df_sorted.iloc[sorted(test_indices)]
        test_scores = test_df['correct'].dropna()
        if test_scores.empty:
            continue
        oos_score = float(test_scores.mean())

        train_df = df_sorted.iloc[sorted(purged_train)]
        train_scores = train_df['correct'].dropna()
        if train_scores.empty:
            continue
        is_score = float(train_scores.mean())

        oos_scores.append(oos_score)
        is_scores.append(is_score)

    if not oos_scores:
        return {'pbo': None, 'n_paths': 0}

    n_overfit = sum(1 for oos, ins in zip(oos_scores, is_scores) if oos < ins)
    pbo = n_overfit / len(oos_scores)

    return {
        'pbo': round(pbo, 3),
        'n_paths': len(oos_scores),
        'oos_mean': round(float(np.mean(oos_scores)) * 100, 1),
        'oos_std': round(float(np.std(oos_scores)) * 100, 1),
        'is_mean': round(float(np.mean(is_scores)) * 100, 1),
    }


# ---------------------------------------------------------------------------
# Plausibility checks
# ---------------------------------------------------------------------------


def check_plausibility(df: pd.DataFrame) -> dict:
    """
    Economic plausibility checks specific to Bitcoin/Liquidity.

    1. 2020-2021 liquidity expansion should predict bullish Bitcoin (expected: yes)
    2. 2022 liquidity contraction should predict bearish Bitcoin (expected: yes)
    """
    checks = {}

    # Check 1: During 2020-2021 expansion, model should predict bullish
    expansion_period = df[
        (df['date'] >= '2020-06-01') & (df['date'] <= '2021-12-31')
    ]
    if not expansion_period.empty:
        expanding_evals = expansion_period[
            expansion_period['liquidity_bucket'] == 'Expanding'
        ]
        expanding_pct = len(expanding_evals) / len(expansion_period)
        checks['2020_2021_liquidity_expansion'] = {
            'pass': bool(expanding_pct > 0.5),
            'expanding_pct': round(expanding_pct * 100, 1),
            'expanding_count': int(len(expanding_evals)),
            'total_count': int(len(expansion_period)),
            'note': 'Majority of evals should classify as Expanding during 2020-2021 QE',
        }
    else:
        checks['2020_2021_liquidity_expansion'] = {
            'pass': True,
            'note': 'No evaluation dates in range',
        }

    # Check 2: During 2022, model should see contraction
    contraction_period = df[
        (df['date'] >= '2022-01-01') & (df['date'] <= '2022-12-31')
    ]
    if not contraction_period.empty:
        contracting_evals = contraction_period[
            contraction_period['liquidity_bucket'] == 'Contracting'
        ]
        contracting_pct = len(contracting_evals) / len(contraction_period)
        checks['2022_liquidity_contraction'] = {
            'pass': bool(contracting_pct > 0.3),  # At least 30% contracting
            'contracting_pct': round(contracting_pct * 100, 1),
            'contracting_count': int(len(contracting_evals)),
            'total_count': int(len(contraction_period)),
            'note': 'Contraction should be present during 2022 QT',
        }
    else:
        checks['2022_liquidity_contraction'] = {
            'pass': True,
            'note': 'No evaluation dates in range',
        }

    # Check 3: Expanding avg return > Contracting avg return
    expanding_df = df[df['liquidity_bucket'] == 'Expanding']
    contracting_df = df[df['liquidity_bucket'] == 'Contracting']
    if not expanding_df.empty and not contracting_df.empty:
        exp_avg = expanding_df['btc_fwd_90d'].dropna().mean()
        con_avg = contracting_df['btc_fwd_90d'].dropna().mean()
        checks['expanding_beats_contracting_returns'] = {
            'pass': bool(exp_avg > con_avg),
            'expanding_avg_90d': round(float(exp_avg) * 100, 2),
            'contracting_avg_90d': round(float(con_avg) * 100, 2),
            'note': 'Expanding liquidity should yield higher Bitcoin returns than Contracting',
        }

    all_pass = all(c.get('pass', False) for c in checks.values())
    return {
        'all_pass': all_pass,
        'checks': checks,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_report(
    df: pd.DataFrame,
    agg_scores: dict,
    wf_scores: dict,
    plausibility: dict,
    cpcv_result: dict,
    baseline_accuracy: float = 34.8,
) -> str:
    """Generate comprehensive markdown backtest report for Bitcoin/Liquidity."""
    lines = []
    lines.append('# Bitcoin / Liquidity Dimension Validation Report')
    lines.append(f'\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'Evaluation period: {df["date"].iloc[0]} to {df["date"].iloc[-1]}')
    lines.append(f'Total evaluations: {len(df)}')
    lines.append(f'Baseline (old regime model crypto accuracy): {baseline_accuracy}%')
    lines.append('')
    lines.append('This validation is SEPARATE from the main composite backtest.')
    lines.append('Bitcoin correlates 0.94 with global M2 (~90-day lag). This tests')
    lines.append('whether the Liquidity dimension predicts Bitcoin 90-day forward returns.')

    # === Overall Accuracy ===
    overall = agg_scores.get('overall', {})
    accuracy = overall.get('accuracy')
    if accuracy is not None:
        delta = accuracy - baseline_accuracy
        status = 'ABOVE' if delta > 0 else 'BELOW'
        lines.append(f'\n## Overall Accuracy: {accuracy}% ({status} baseline: {"+" if delta > 0 else ""}{delta:.1f}pp)')
    else:
        lines.append('\n## Overall Accuracy: N/A')

    # === Per-Bucket Breakdown ===
    lines.append('\n## Per-Liquidity-State Accuracy (3-bucket)')
    lines.append('')
    lines.append('| Liquidity State | Count | Accuracy | Avg 90d Return | Median 90d Return | % Positive |')
    lines.append('|-----------------|-------|----------|----------------|-------------------|------------|')
    for bucket in ['Expanding', 'Neutral', 'Contracting']:
        stats = agg_scores['per_bucket'].get(bucket, {})
        count = stats.get('count', 0)
        if count == 0:
            lines.append(f'| {bucket} | 0 | — | — | — | — |')
            continue
        acc = f'{stats.get("accuracy", "—")}%' if 'accuracy' in stats else '—'
        avg = f'{stats.get("avg_fwd_90d", "—")}%' if 'avg_fwd_90d' in stats else '—'
        med = f'{stats.get("median_fwd_90d", "—")}%' if 'median_fwd_90d' in stats else '—'
        pct = f'{stats.get("pct_positive", "—")}%' if 'pct_positive' in stats else '—'
        lines.append(f'| {bucket} | {count} | {acc} | {avg} | {med} | {pct} |')

    # Return ordering
    ordering = overall.get('return_ordering_correct')
    if ordering is not None:
        lines.append(f'\nReturn magnitude ordering (Expanding > Neutral > Contracting): **{"PASS" if ordering else "FAIL"}**')
        by_bucket = overall.get('avg_fwd_90d_by_bucket', {})
        if by_bucket:
            for b in ['Expanding', 'Neutral', 'Contracting']:
                if b in by_bucket:
                    lines.append(f'  - {b}: {by_bucket[b]}%')

    # === Per-State Detail (5-state) ===
    lines.append('\n## Per-Liquidity-State Detail (5-state)')
    lines.append('')
    lines.append('| State | Expected | Count | Accuracy | Avg 30d | Avg 60d | Avg 90d |')
    lines.append('|-------|----------|-------|----------|---------|---------|---------|')
    for state in ['Strongly Expanding', 'Expanding', 'Neutral', 'Contracting', 'Strongly Contracting']:
        stats = agg_scores['per_state'].get(state, {})
        count = stats.get('count', 0)
        if count == 0:
            lines.append(f'| {state} | {LIQUIDITY_EXPECTATIONS[state]} | 0 | — | — | — | — |')
            continue
        exp = stats.get('expected_direction', '—')
        acc = f'{stats.get("accuracy", "—")}%' if 'accuracy' in stats else '—'
        a30 = f'{stats.get("avg_fwd_30d", "—")}%' if 'avg_fwd_30d' in stats else '—'
        a60 = f'{stats.get("avg_fwd_60d", "—")}%' if 'avg_fwd_60d' in stats else '—'
        a90 = f'{stats.get("avg_fwd_90d", "—")}%' if 'avg_fwd_90d' in stats else '—'
        lines.append(f'| {state} | {exp} | {count} | {acc} | {a30} | {a60} | {a90} |')

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

    # === Recommendation ===
    lines.append('\n## Recommendation for Phase 11 Crypto Page')
    lines.append('')

    if accuracy is not None:
        meaningful_improvement = accuracy > baseline_accuracy + 5  # > 5pp improvement
        above_50 = accuracy > 50.0

        if meaningful_improvement and above_50:
            lines.append(f'**STRONG SIGNAL: {accuracy}% accuracy (vs {baseline_accuracy}% old regime model)**')
            lines.append('')
            lines.append('The Liquidity dimension provides a meaningful predictive signal for Bitcoin.')
            lines.append('Recommended crypto page guidance:')
            lines.append(f'> "Liquidity is [state] — historically [favorable/unfavorable] for Bitcoin ({accuracy:.0f}% accuracy)"')
            lines.append('')
            lines.append('This is a substantial improvement over the current regime-based crypto context.')
        elif above_50:
            lines.append(f'**MODERATE SIGNAL: {accuracy}% accuracy (vs {baseline_accuracy}% old regime model)**')
            lines.append('')
            lines.append('The Liquidity dimension provides some predictive signal for Bitcoin,')
            lines.append('better than the old regime model but not overwhelmingly strong.')
            lines.append('Recommended crypto page guidance:')
            lines.append('> "Liquidity conditions may [favor/not favor] Bitcoin — signal is moderate"')
        else:
            lines.append(f'**WEAK SIGNAL: {accuracy}% accuracy (vs {baseline_accuracy}% old regime model)**')
            lines.append('')
            lines.append('The Liquidity dimension does not reliably predict Bitcoin direction.')
            lines.append('Recommended crypto page guidance:')
            lines.append('> "Macro conditions have limited predictive value for Bitcoin direction"')

        # Per-state recommendations
        lines.append('\n### Per-State Signal Strength')
        for bucket in ['Expanding', 'Neutral', 'Contracting']:
            stats = agg_scores['per_bucket'].get(bucket, {})
            bucket_acc = stats.get('accuracy')
            bucket_count = stats.get('count', 0)
            if bucket_acc is not None and bucket_count >= 5:
                strength = 'strong' if bucket_acc >= 60 else ('moderate' if bucket_acc >= 50 else 'weak')
                lines.append(f'- **{bucket}** (n={bucket_count}): {bucket_acc}% accuracy — {strength} signal')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('  Bitcoin / Liquidity Dimension Validation')
    print('=' * 60)

    # Step 1: Load data
    print('\nLoading liquidity history...')
    liq_history = compute_liquidity_history('2010-01-01')
    if liq_history is None or liq_history.empty:
        print('ERROR: Cannot compute liquidity history.')
        sys.exit(1)
    print(f'  Liquidity: {len(liq_history)} points, '
          f'{liq_history["date"].iloc[0].strftime("%Y-%m-%d")} to '
          f'{liq_history["date"].iloc[-1].strftime("%Y-%m-%d")}')

    print('\nLoading Bitcoin price data...')
    btc_price = load_bitcoin_price()
    if btc_price is None or btc_price.empty:
        print('ERROR: No Bitcoin price data available (bitcoin_price.csv).')
        sys.exit(1)
    print(f'  Bitcoin: {len(btc_price)} points, '
          f'{btc_price.index[0].strftime("%Y-%m-%d")} to '
          f'{btc_price.index[-1].strftime("%Y-%m-%d")}')

    # Step 2: Run backtest
    print('\nRunning Bitcoin/Liquidity backtest...')
    df = run_bitcoin_liquidity_backtest(liq_history, btc_price)
    if df.empty:
        print('ERROR: No results generated.')
        sys.exit(1)
    print(f'  {len(df)} evaluation dates scored')

    # Save raw results
    csv_path = RESULTS_DIR / 'bitcoin_liquidity_results.csv'
    df.to_csv(csv_path, index=False)
    print(f'  Raw results: {csv_path}')

    # Step 3: Aggregate scoring
    print('\nScoring results...')
    agg_scores = score_results(df)
    overall = agg_scores.get('overall', {})
    accuracy = overall.get('accuracy')
    print(f'  Overall accuracy: {accuracy}%')

    # Step 4: Walk-forward validation
    print('\nRunning walk-forward validation...')
    folds = generate_folds()
    wf_scores = score_walk_forward(df, folds)
    print(f'  Mean fold score: {wf_scores.get("mean")}%')
    print(f'  Std: {wf_scores.get("std")}%')
    print(f'  Sharpe: {wf_scores.get("sharpe")}')

    # Step 5: CPCV
    print('\nRunning CPCV (k=6, p=2, purge=3mo, embargo=1mo)...')
    cpcv_result = run_cpcv(df)
    print(f'  PBO: {cpcv_result.get("pbo")}')

    # Step 6: Economic plausibility
    print('\nChecking economic plausibility...')
    plausibility = check_plausibility(df)
    print(f'  All checks pass: {plausibility["all_pass"]}')

    # Step 7: Generate report
    print('\nGenerating report...')
    report = generate_report(
        df, agg_scores, wf_scores, plausibility, cpcv_result,
    )

    report_path = RESULTS_DIR / 'bitcoin_liquidity_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f'  Report: {report_path}')

    # Save structured results
    structured = {
        'overall': overall,
        'walk_forward': wf_scores,
        'per_state': agg_scores.get('per_state', {}),
        'per_bucket': agg_scores.get('per_bucket', {}),
        'plausibility': plausibility,
        'cpcv': cpcv_result,
    }
    json_path = RESULTS_DIR / 'bitcoin_liquidity_scores.json'
    with open(json_path, 'w') as f:
        json.dump(structured, f, indent=2, default=str)
    print(f'  Scores: {json_path}')

    # Print summary
    print('\n' + '=' * 60)
    baseline = 34.8
    if accuracy is not None:
        delta = accuracy - baseline
        print(f'  ACCURACY: {accuracy}% ({"+" if delta > 0 else ""}{delta:.1f}pp vs {baseline}% old regime)')
    print('')
    for bucket in ['Expanding', 'Neutral', 'Contracting']:
        stats = agg_scores['per_bucket'].get(bucket, {})
        if stats.get('count', 0) > 0:
            acc = stats.get('accuracy', '—')
            avg = stats.get('avg_fwd_90d', '—')
            print(f'  {bucket}: {acc}% accurate, avg 90d return={avg}%')
    print('')
    if plausibility['all_pass']:
        print('  Plausibility: PASS')
    else:
        print('  Plausibility: FAIL')
    if cpcv_result.get('pbo') is not None:
        print(f'  CPCV PBO: {cpcv_result["pbo"]} ({"PASS" if cpcv_result["pbo"] <= 0.5 else "FAIL"})')
    print('=' * 60)

    return accuracy


if __name__ == '__main__':
    main()
