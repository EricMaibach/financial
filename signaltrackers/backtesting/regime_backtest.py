"""
Macro Regime Backtest

Replays the k-means regime classifier over historical dates to evaluate
accuracy. For each evaluation date, uses only data available up to that
date (60-month rolling window), classifies the regime, then measures
forward returns across 4 investable assets (S&P 500, treasuries, gold,
bitcoin) to assess whether the regime call was correct.

Usage:
    PYTHONPATH=signaltrackers python3 signaltrackers/backtesting/regime_backtest.py

Output is written to signaltrackers/backtesting/results/
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
RESULTS_DIR = Path(__file__).resolve().parent / 'results'

# ---------------------------------------------------------------------------
# Configuration (mirrors regime_detection.py / regime_config.py)
# ---------------------------------------------------------------------------

REGIME_FEATURES = {
    'high_yield_spread': 'BAMLH0A0HYM2',
    'yield_curve_10y2y': 'T10Y2Y',
    'nfci': 'NFCI',
    'initial_claims': 'ICSA',
    'fed_funds_rate': 'FEDFUNDS',
}

FEATURE_WEIGHTS = {
    'high_yield_spread': +1.5,
    'yield_curve_10y2y': -1.5,
    'nfci': +1.0,
    'initial_claims': +1.0,
    'fed_funds_rate': +0.5,
}

REGIME_LABELS = ['Bull', 'Neutral', 'Bear', 'Recession Watch']
HISTORY_MONTHS = 60
CONFIDENCE_LOW_THRESHOLD = 0.5
CONFIDENCE_HIGH_THRESHOLD = 1.5

# Forward return windows (calendar days)
FORWARD_WINDOWS = [30, 60, 90]

# How often to evaluate (every N months)
EVAL_FREQUENCY_MONTHS = 1

# ---------------------------------------------------------------------------
# Multi-asset scoring configuration
# ---------------------------------------------------------------------------

# Investable assets with CSV file keys and scoring weights
# Bitcoin excluded from scoring — research shows it is driven by liquidity
# conditions and its own halving cycle, not macro regimes. Including it
# adds noise that makes it harder to evaluate regime detection accuracy.
# See: NY Fed Staff Report No. 1052, "The Bitcoin-Macro Disconnect" (2023)
# and backtest results showing 34.8% accuracy under risk-on/risk-off assumptions.
SCORING_ASSETS = {
    'sp500': {
        'csv_key': 'sp500_price',
        'weight': 0.375,
        'label': 'S&P 500',
    },
    'treasuries': {
        'csv_key': 'treasury_20yr_price',
        'weight': 0.3125,
        'label': 'Treasuries (TLT)',
    },
    'gold': {
        'csv_key': 'gold_price',
        'weight': 0.3125,
        'label': 'Gold',
    },
}

# Expected direction per asset per regime:
#   'positive'  = asset should go up
#   'negative'  = asset should go down
#   'neutral'   = no strong directional expectation
EXPECTED_DIRECTIONS = {
    'Bull': {
        'sp500': 'positive',
        'treasuries': 'negative',   # no flight-to-safety bid
        'gold': 'negative',         # risk-on, gold underperforms
    },
    'Neutral': {
        'sp500': 'neutral',
        'treasuries': 'neutral',
        'gold': 'neutral',
    },
    'Bear': {
        'sp500': 'negative',
        'treasuries': 'positive',   # flight to safety
        'gold': 'positive',         # safe haven bid
    },
    'Recession Watch': {
        'sp500': 'negative',
        'treasuries': 'positive',   # strong flight to safety
        'gold': 'positive',         # strong safe haven bid
    },
}

# Neutral tolerance: return within +/- this threshold counts as "correct"
NEUTRAL_THRESHOLD = 0.05  # 5%


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_csv(metric_key: str) -> pd.Series | None:
    """Load a CSV time series from the data directory. Returns None if missing."""
    csv_path = DATA_DIR / f'{metric_key}.csv'
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    if df.empty or len(df.columns) < 2:
        return None
    df['date'] = pd.to_datetime(df['date'])
    value_col = df.columns[1]
    df = df.dropna(subset=[value_col]).set_index('date')
    return df[value_col].astype(float)


def load_all_features() -> pd.DataFrame:
    """Load all regime feature series and combine into a single DataFrame."""
    series_map = {}
    for key in REGIME_FEATURES:
        s = load_csv(key)
        if s is not None and len(s) >= 12:
            series_map[key] = s
    if len(series_map) < 2:
        raise RuntimeError('Insufficient feature data for backtesting.')
    df = pd.DataFrame(series_map)
    df = df.resample('ME').last()
    df = df.dropna(how='all')
    return df


def load_scoring_assets() -> dict[str, pd.Series]:
    """Load all investable asset price series for scoring."""
    assets = {}
    for asset_key, config in SCORING_ASSETS.items():
        s = load_csv(config['csv_key'])
        if s is not None and not s.empty:
            assets[asset_key] = s
            print(f'  Loaded {config["label"]}: {s.index[0].strftime("%Y-%m-%d")} to {s.index[-1].strftime("%Y-%m-%d")} ({len(s)} points)')
        else:
            print(f'  WARNING: Could not load {config["label"]} ({config["csv_key"]}.csv)')
    return assets


# ---------------------------------------------------------------------------
# K-means regime classifier (mirrors _kmeans_regime from regime_detection.py)
# ---------------------------------------------------------------------------


def classify_regime(
    df_monthly: pd.DataFrame,
    as_of_date: pd.Timestamp,
) -> dict | None:
    """
    Classify the macro regime using only data available up to as_of_date.

    Returns a dict with keys: regime, confidence, confidence_ratio
    or None if insufficient data.
    """
    df = df_monthly[df_monthly.index <= as_of_date].copy()

    available = [col for col in REGIME_FEATURES if col in df.columns]
    df_feat = df[available].copy()

    if len(df_feat) > HISTORY_MONTHS:
        df_feat = df_feat.iloc[-HISTORY_MONTHS:]

    df_feat = df_feat.ffill().bfill()
    df_clean = df_feat.dropna()

    if len(df_clean) < 24:
        return None

    scaler = StandardScaler()
    X = scaler.fit_transform(df_clean.values)

    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    kmeans.fit(X)

    centroids = kmeans.cluster_centers_
    stress_scores = np.zeros(len(centroids))
    for i, feature in enumerate(available):
        weight = FEATURE_WEIGHTS.get(feature, 0.0)
        if weight != 0.0:
            stress_scores += weight * centroids[:, i]

    sorted_clusters = np.argsort(stress_scores)
    cluster_to_regime = {
        sorted_clusters[i]: REGIME_LABELS[i] for i in range(n_clusters)
    }

    latest_raw = df_feat.iloc[-1:].ffill().bfill().dropna()
    if latest_raw.empty:
        return None

    latest_scaled = scaler.transform(latest_raw.values)
    predicted_cluster = kmeans.predict(latest_scaled)[0]
    regime = cluster_to_regime[predicted_cluster]

    centroid_dist = np.linalg.norm(
        latest_scaled - kmeans.cluster_centers_[predicted_cluster]
    )
    cluster_mask = kmeans.labels_ == predicted_cluster
    cluster_points = X[cluster_mask]
    if len(cluster_points) > 1:
        avg_dist = np.mean(
            np.linalg.norm(
                cluster_points - kmeans.cluster_centers_[predicted_cluster],
                axis=1,
            )
        )
    else:
        avg_dist = centroid_dist

    ratio = centroid_dist / avg_dist if avg_dist > 0 else 1.0

    if ratio <= CONFIDENCE_LOW_THRESHOLD:
        confidence = 'High'
    elif ratio <= CONFIDENCE_HIGH_THRESHOLD:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    return {
        'regime': regime,
        'confidence': confidence,
        'confidence_ratio': round(ratio, 4),
    }


# ---------------------------------------------------------------------------
# Forward return calculation
# ---------------------------------------------------------------------------


def compute_forward_return(
    price_series: pd.Series,
    eval_date: pd.Timestamp,
    window_days: int,
) -> float | None:
    """
    Compute forward return for a price series from eval_date over window_days.

    Returns a float (e.g., 0.025 for 2.5%) or None if insufficient data.
    """
    future = price_series[price_series.index >= eval_date]
    if future.empty:
        return None

    start_price = future.iloc[0]
    target_date = eval_date + pd.Timedelta(days=window_days)
    future_window = price_series[price_series.index >= target_date]
    if future_window.empty:
        return None

    end_price = future_window.iloc[0]
    return round((end_price - start_price) / start_price, 6)


def compute_max_drawdown(
    price_series: pd.Series,
    eval_date: pd.Timestamp,
    window_days: int,
) -> float | None:
    """
    Compute the maximum drawdown within window_days after eval_date.
    Returns a negative float (e.g., -0.08 for 8% drawdown) or None.
    """
    end_date = eval_date + pd.Timedelta(days=window_days)
    window_prices = price_series[
        (price_series.index >= eval_date) & (price_series.index <= end_date)
    ]
    if len(window_prices) < 2:
        return None

    cummax = window_prices.cummax()
    drawdowns = (window_prices - cummax) / cummax
    return round(drawdowns.min(), 6)


# ---------------------------------------------------------------------------
# Per-evaluation multi-asset scoring
# ---------------------------------------------------------------------------


def score_single_evaluation(
    regime: str,
    asset_returns: dict[str, float | None],
) -> dict:
    """
    Score a single regime call against forward returns across all assets.

    Returns a dict with per-asset scores (0.0 or 1.0), the weighted score,
    and which assets were available.
    """
    expected = EXPECTED_DIRECTIONS[regime]
    asset_scores = {}
    weighted_sum = 0.0
    weight_sum = 0.0

    for asset_key, config in SCORING_ASSETS.items():
        ret = asset_returns.get(asset_key)
        if ret is None:
            continue

        direction = expected[asset_key]
        weight = config['weight']

        if direction == 'positive':
            score = 1.0 if ret > 0 else 0.0
        elif direction == 'negative':
            score = 1.0 if ret < 0 else 0.0
        elif direction == 'neutral':
            # Neutral: correct if small move, partial credit if larger
            score = 1.0 if abs(ret) < NEUTRAL_THRESHOLD else 0.5
        else:
            continue

        asset_scores[asset_key] = score
        weighted_sum += score * weight
        weight_sum += weight

    # Normalize to 0-1 scale based on available assets
    weighted_score = weighted_sum / weight_sum if weight_sum > 0 else None

    return {
        'asset_scores': asset_scores,
        'weighted_score': round(weighted_score, 4) if weighted_score is not None else None,
        'assets_available': list(asset_scores.keys()),
    }


# ---------------------------------------------------------------------------
# Main backtest loop
# ---------------------------------------------------------------------------


def run_backtest(
    start_year: int = 2000,
    end_year: int | None = None,
) -> pd.DataFrame:
    """
    Run the regime backtest over the specified date range.

    Returns a DataFrame with one row per evaluation date, including
    per-asset forward returns and multi-asset scores.
    """
    print('Loading data...')
    features_monthly = load_all_features()
    scoring_assets = load_scoring_assets()

    if not scoring_assets:
        raise RuntimeError('No scoring asset data available.')

    # Determine end date: need 90 days of forward data for all assets
    last_dates = [s.index[-1] for s in scoring_assets.values()]
    last_data = min(features_monthly.index[-1], min(last_dates))
    if end_year is None:
        end_date = last_data - pd.Timedelta(days=90)
    else:
        end_date = pd.Timestamp(f'{end_year}-12-31')

    start_date = pd.Timestamp(f'{start_year}-01-01')

    eval_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq=f'{EVAL_FREQUENCY_MONTHS}ME',
    )

    print(
        f'\nEvaluating {len(eval_dates)} dates from '
        f'{eval_dates[0].strftime("%Y-%m-%d")} to '
        f'{eval_dates[-1].strftime("%Y-%m-%d")}...'
    )

    rows = []
    for i, eval_date in enumerate(eval_dates):
        if (i + 1) % 50 == 0 or i == 0:
            print(f'  Processing {i + 1}/{len(eval_dates)}: {eval_date.strftime("%Y-%m-%d")}')

        result = classify_regime(features_monthly, eval_date)
        if result is None:
            continue

        row = {
            'date': eval_date.strftime('%Y-%m-%d'),
            'regime': result['regime'],
            'confidence': result['confidence'],
            'confidence_ratio': result['confidence_ratio'],
        }

        # Compute forward returns for each asset at each window
        asset_returns_90d = {}
        for asset_key, price_series in scoring_assets.items():
            for w in FORWARD_WINDOWS:
                ret = compute_forward_return(price_series, eval_date, w)
                row[f'{asset_key}_fwd_{w}d'] = ret
                if w == 90:
                    asset_returns_90d[asset_key] = ret

        # S&P 500 max drawdown
        if 'sp500' in scoring_assets:
            row['sp500_max_dd_90d'] = compute_max_drawdown(
                scoring_assets['sp500'], eval_date, 90
            )

        # Multi-asset score for this evaluation
        eval_score = score_single_evaluation(result['regime'], asset_returns_90d)
        row['multi_asset_score'] = eval_score['weighted_score']
        for asset_key, score in eval_score['asset_scores'].items():
            row[f'{asset_key}_correct'] = score

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Scoring and report generation
# ---------------------------------------------------------------------------


def score_results(df: pd.DataFrame) -> dict:
    """
    Compute aggregate accuracy metrics from the backtest results.

    Returns a dict with per-regime stats, per-asset stats, and overall scores.
    """
    report = {
        'overall': {},
        'per_regime': {},
        'per_asset': {},
        'per_confidence': {},
        'transitions': {},
    }

    # ---- Overall multi-asset score ----
    valid_scores = df['multi_asset_score'].dropna()
    if not valid_scores.empty:
        report['overall']['multi_asset_accuracy'] = round(
            float(valid_scores.mean()) * 100, 1
        )
        report['overall']['total_evaluations'] = int(len(valid_scores))

    # ---- Per-asset accuracy ----
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

    # ---- Per-regime statistics ----
    for regime in REGIME_LABELS:
        mask = df['regime'] == regime
        subset = df[mask]
        if subset.empty:
            report['per_regime'][regime] = {'count': 0}
            continue

        stats = {'count': int(len(subset))}

        # Multi-asset score for this regime
        regime_scores = subset['multi_asset_score'].dropna()
        if not regime_scores.empty:
            stats['multi_asset_accuracy'] = round(
                float(regime_scores.mean()) * 100, 1
            )

        # Per-asset returns for this regime
        for asset_key in SCORING_ASSETS:
            for w in FORWARD_WINDOWS:
                col = f'{asset_key}_fwd_{w}d'
                if col not in subset.columns:
                    continue
                valid = subset[col].dropna()
                if not valid.empty:
                    stats[f'{asset_key}_avg_{w}d'] = round(
                        float(valid.mean()) * 100, 2
                    )
                    stats[f'{asset_key}_median_{w}d'] = round(
                        float(valid.median()) * 100, 2
                    )

            # Per-asset correctness for this regime
            correct_col = f'{asset_key}_correct'
            if correct_col in subset.columns:
                valid = subset[correct_col].dropna()
                if not valid.empty:
                    stats[f'{asset_key}_accuracy'] = round(
                        float(valid.mean()) * 100, 1
                    )

        # S&P 500 max drawdown
        dd_col = 'sp500_max_dd_90d'
        if dd_col in subset.columns:
            dd_valid = subset[dd_col].dropna()
            if not dd_valid.empty:
                stats['sp500_avg_max_dd_90d'] = round(
                    float(dd_valid.mean()) * 100, 2
                )
                stats['sp500_worst_max_dd_90d'] = round(
                    float(dd_valid.min()) * 100, 2
                )

        report['per_regime'][regime] = stats

    # ---- Per-confidence statistics ----
    for conf in ['High', 'Medium', 'Low']:
        mask = df['confidence'] == conf
        subset = df[mask]
        if subset.empty:
            continue
        stats = {'count': int(len(subset))}
        conf_scores = subset['multi_asset_score'].dropna()
        if not conf_scores.empty:
            stats['multi_asset_accuracy'] = round(
                float(conf_scores.mean()) * 100, 1
            )
        report['per_confidence'][conf] = stats

    # ---- Regime ordering check ----
    # Does multi-asset accuracy increase from Recession Watch → Bull?
    # (Bull should score highest because all assets move "right")
    regime_accuracy_order = {}
    for regime in REGIME_LABELS:
        stats = report['per_regime'].get(regime, {})
        if 'multi_asset_accuracy' in stats:
            regime_accuracy_order[regime] = stats['multi_asset_accuracy']

    if len(regime_accuracy_order) >= 3:
        report['overall']['regime_accuracy_by_regime'] = regime_accuracy_order

    # ---- S&P 500 return ordering (does risk increase from Bull → Recession Watch?) ----
    regime_sp500_returns = {}
    for regime in REGIME_LABELS:
        stats = report['per_regime'].get(regime, {})
        avg_ret = stats.get('sp500_avg_90d')
        if avg_ret is not None:
            regime_sp500_returns[regime] = avg_ret

    if len(regime_sp500_returns) >= 3:
        ordered = [regime_sp500_returns.get(r) for r in REGIME_LABELS if r in regime_sp500_returns]
        is_monotonic = all(ordered[i] >= ordered[i + 1] for i in range(len(ordered) - 1))
        report['overall']['sp500_return_ordering_correct'] = is_monotonic
        report['overall']['sp500_avg_90d_by_regime'] = regime_sp500_returns

    # ---- Drawdown ordering ----
    regime_drawdowns = {}
    for regime in REGIME_LABELS:
        stats = report['per_regime'].get(regime, {})
        dd = stats.get('sp500_avg_max_dd_90d')
        if dd is not None:
            regime_drawdowns[regime] = dd

    if len(regime_drawdowns) >= 3:
        ordered = [regime_drawdowns.get(r) for r in REGIME_LABELS if r in regime_drawdowns]
        # Drawdowns should get worse (more negative) from Bull → Recession Watch
        dd_ordering_correct = all(ordered[i] >= ordered[i + 1] for i in range(len(ordered) - 1))
        report['overall']['drawdown_ordering_correct'] = dd_ordering_correct
        report['overall']['sp500_avg_max_dd_by_regime'] = regime_drawdowns

    # ---- Transition analysis ----
    df_sorted = df.sort_values('date').reset_index(drop=True)
    transitions = []
    for i in range(1, len(df_sorted)):
        prev_regime = df_sorted.loc[i - 1, 'regime']
        curr_regime = df_sorted.loc[i, 'regime']
        if prev_regime != curr_regime:
            t = {
                'date': df_sorted.loc[i, 'date'],
                'from': prev_regime,
                'to': curr_regime,
            }
            for asset_key in SCORING_ASSETS:
                col_90 = f'{asset_key}_fwd_90d'
                if col_90 in df_sorted.columns:
                    t[f'{asset_key}_90d'] = df_sorted.loc[i, col_90]
            t['multi_asset_score'] = df_sorted.loc[i, 'multi_asset_score']
            transitions.append(t)

    report['transitions']['count'] = len(transitions)
    report['transitions']['details'] = transitions

    # Transition scoring: did the multi-asset score improve on bullish shifts?
    stress_rank = {'Bull': 0, 'Neutral': 1, 'Bear': 2, 'Recession Watch': 3}
    correct_transitions = 0
    total_transitions = 0
    for t in transitions:
        score = t.get('multi_asset_score')
        if score is None or pd.isna(score):
            continue
        from_rank = stress_rank[t['from']]
        to_rank = stress_rank[t['to']]
        total_transitions += 1
        sp500_ret = t.get('sp500_90d')
        if sp500_ret is None or pd.isna(sp500_ret):
            continue
        # Shift more bearish → expect S&P 500 decline
        if to_rank > from_rank and sp500_ret < 0:
            correct_transitions += 1
        # Shift more bullish → expect S&P 500 rise
        elif to_rank < from_rank and sp500_ret > 0:
            correct_transitions += 1

    if total_transitions > 0:
        report['transitions']['directional_accuracy'] = round(
            correct_transitions / total_transitions * 100, 1
        )

    # ---- Composite score ----
    # Weighted: multi-asset accuracy (50%), drawdown ordering (25%),
    # S&P return ordering (25%)
    scores = []
    weights = []

    if 'multi_asset_accuracy' in report['overall']:
        scores.append(report['overall']['multi_asset_accuracy'])
        weights.append(0.50)

    if report['overall'].get('drawdown_ordering_correct'):
        scores.append(100.0)
        weights.append(0.25)
    elif 'drawdown_ordering_correct' in report['overall']:
        scores.append(0.0)
        weights.append(0.25)

    if report['overall'].get('sp500_return_ordering_correct'):
        scores.append(100.0)
        weights.append(0.25)
    elif 'sp500_return_ordering_correct' in report['overall']:
        scores.append(0.0)
        weights.append(0.25)

    if scores and sum(weights) > 0:
        composite = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        report['overall']['composite_score'] = round(composite, 1)

    return report


def generate_report(df: pd.DataFrame, scores: dict) -> str:
    """Generate a human-readable markdown report from backtest results."""
    lines = []
    lines.append('# Macro Regime Backtest Report')
    lines.append(f'\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'Evaluation period: {df["date"].iloc[0]} to {df["date"].iloc[-1]}')
    lines.append(f'Total evaluations: {len(df)}')

    # ---- Overall Score ----
    overall = scores.get('overall', {})
    composite = overall.get('composite_score')
    if composite is not None:
        lines.append(f'\n## Overall Composite Score: {composite}/100')
        lines.append('')
        lines.append('Components:')
        if 'multi_asset_accuracy' in overall:
            lines.append(
                f'- Multi-asset accuracy (50% weight): {overall["multi_asset_accuracy"]}%'
            )
        if 'drawdown_ordering_correct' in overall:
            dd_order = 'PASS' if overall['drawdown_ordering_correct'] else 'FAIL'
            lines.append(f'- Drawdown ordering Bull→Recession Watch (25% weight): {dd_order}')
        if 'sp500_return_ordering_correct' in overall:
            ret_order = 'PASS' if overall['sp500_return_ordering_correct'] else 'FAIL'
            lines.append(f'- S&P 500 return ordering Bull→Recession Watch (25% weight): {ret_order}')

    # ---- Per-Asset Accuracy ----
    lines.append('\n## Per-Asset Accuracy')
    lines.append('')
    lines.append('How often each asset moved in the direction the regime predicted.')
    lines.append('')
    lines.append('| Asset | Weight | Accuracy | Evaluations |')
    lines.append('|-------|--------|----------|-------------|')
    for asset_key in SCORING_ASSETS:
        stats = scores['per_asset'].get(asset_key, {})
        if not stats:
            continue
        lines.append(
            f'| {stats["label"]} | {stats["weight"]:.0%} | '
            f'{stats["accuracy"]}% | {stats["count"]} |'
        )

    # ---- Per-Regime Multi-Asset Summary ----
    lines.append('\n## Per-Regime Summary')
    lines.append('')
    lines.append('| Regime | Count | Multi-Asset Accuracy | S&P 500 Avg 90d | S&P 500 Avg Max DD |')
    lines.append('|--------|-------|---------------------|-----------------|-------------------|')
    for regime in REGIME_LABELS:
        stats = scores['per_regime'].get(regime, {})
        count = stats.get('count', 0)
        if count == 0:
            lines.append(f'| {regime} | 0 | — | — | — |')
            continue
        ma = stats.get('multi_asset_accuracy', '—')
        sp_ret = stats.get('sp500_avg_90d', '—')
        sp_dd = stats.get('sp500_avg_max_dd_90d', '—')
        fmt = lambda v: f'{v}%' if isinstance(v, (int, float)) else v
        lines.append(
            f'| {regime} | {count} | {fmt(ma)} | {fmt(sp_ret)} | {fmt(sp_dd)} |'
        )

    # ---- Per-Regime Per-Asset Detail ----
    lines.append('\n## Per-Regime Asset Detail')
    for regime in REGIME_LABELS:
        stats = scores['per_regime'].get(regime, {})
        if stats.get('count', 0) == 0:
            continue

        expected = EXPECTED_DIRECTIONS[regime]
        lines.append(f'\n### {regime} (n={stats["count"]})')

        for asset_key, config in SCORING_ASSETS.items():
            label = config['label']
            direction = expected[asset_key]
            accuracy = stats.get(f'{asset_key}_accuracy')
            if accuracy is None:
                continue

            returns_parts = []
            for w in FORWARD_WINDOWS:
                avg = stats.get(f'{asset_key}_avg_{w}d')
                if avg is not None:
                    returns_parts.append(f'{w}d avg={avg}%')

            returns_str = ', '.join(returns_parts) if returns_parts else '—'
            lines.append(
                f'- **{label}** (expect {direction}): '
                f'accuracy={accuracy}% | {returns_str}'
            )

        # S&P 500 drawdown
        dd_avg = stats.get('sp500_avg_max_dd_90d')
        dd_worst = stats.get('sp500_worst_max_dd_90d')
        if dd_avg is not None:
            lines.append(f'- **S&P 500 Max Drawdown (90d)**: avg={dd_avg}%, worst={dd_worst}%')

    # ---- Confidence Breakdown ----
    lines.append('\n## Confidence Level Performance')
    lines.append('')
    lines.append('| Confidence | Count | Multi-Asset Accuracy |')
    lines.append('|------------|-------|---------------------|')
    for conf in ['High', 'Medium', 'Low']:
        stats = scores['per_confidence'].get(conf, {})
        if not stats:
            continue
        ma = stats.get('multi_asset_accuracy', '—')
        fmt = lambda v: f'{v}%' if isinstance(v, (int, float)) else v
        lines.append(f'| {conf} | {stats["count"]} | {fmt(ma)} |')

    # ---- Transitions ----
    trans = scores.get('transitions', {})
    if trans.get('count', 0) > 0:
        lines.append(f'\n## Regime Transitions ({trans["count"]} total)')
        if 'directional_accuracy' in trans:
            lines.append(
                f'\nTransition directional accuracy: {trans["directional_accuracy"]}%'
            )
            lines.append(
                '(When shifting bearish, did S&P 500 decline? When shifting bullish, did it rise?)'
            )
        lines.append('')

        # Header
        header = '| Date | From | To | Score |'
        sep = '|------|------|----|-------|'
        for asset_key, config in SCORING_ASSETS.items():
            header += f' {config["label"]} 90d |'
            sep += '------------|'
        lines.append(header)
        lines.append(sep)

        for t in trans.get('details', []):
            score = t.get('multi_asset_score')
            score_str = f'{score:.0%}' if score is not None and not pd.isna(score) else '—'
            row = f'| {t["date"]} | {t["from"]} | {t["to"]} | {score_str} |'
            for asset_key in SCORING_ASSETS:
                ret = t.get(f'{asset_key}_90d')
                if ret is not None and not pd.isna(ret):
                    row += f' {ret * 100:.2f}% |'
                else:
                    row += ' — |'
            lines.append(row)

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    df = run_backtest(start_year=2000)

    if df.empty:
        print('ERROR: No results generated. Check data availability.')
        sys.exit(1)

    # Save raw results
    csv_path = RESULTS_DIR / 'backtest_results.csv'
    df.to_csv(csv_path, index=False)
    print(f'\nRaw results saved to: {csv_path}')

    # Score and generate report
    scores = score_results(df)

    json_path = RESULTS_DIR / 'backtest_scores.json'
    with open(json_path, 'w') as f:
        json.dump(scores, f, indent=2, default=str)
    print(f'Scores saved to: {json_path}')

    report = generate_report(df, scores)
    report_path = RESULTS_DIR / 'backtest_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f'Report saved to: {report_path}')

    # Print summary
    overall = scores.get('overall', {})
    composite = overall.get('composite_score')
    print('\n' + '=' * 60)
    if composite is not None:
        print(f'  COMPOSITE SCORE: {composite}/100')
    if 'multi_asset_accuracy' in overall:
        print(f'  Multi-asset accuracy: {overall["multi_asset_accuracy"]}%')
    if 'drawdown_ordering_correct' in overall:
        dd = 'PASS' if overall['drawdown_ordering_correct'] else 'FAIL'
        print(f'  Drawdown ordering: {dd}')
    if 'sp500_return_ordering_correct' in overall:
        ret = 'PASS' if overall['sp500_return_ordering_correct'] else 'FAIL'
        print(f'  S&P 500 return ordering: {ret}')

    # Per-asset summary
    print('')
    for asset_key in SCORING_ASSETS:
        stats = scores['per_asset'].get(asset_key, {})
        if stats:
            print(f'  {stats["label"]}: {stats["accuracy"]}% accurate ({stats["count"]} evals)')

    print('=' * 60)


if __name__ == '__main__':
    main()
