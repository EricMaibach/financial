"""
Shared backtest utilities.

Common data loading and computation functions used by backtesting modules.
Extracted from a removed backtesting module during the conditions engine migration.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

# ---------------------------------------------------------------------------
# Multi-asset scoring configuration
# ---------------------------------------------------------------------------

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
# Forward return computation
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
