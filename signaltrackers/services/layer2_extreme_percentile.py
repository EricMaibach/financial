"""
Layer 2 Alert Engine: Extreme Percentile Detection

Fires when a tracked indicator crosses the 90th or 10th percentile on a
10-year rolling window AND has moved there from below the 70th percentile
within the last 90 days (momentum filter — prevents re-alerting on sustained
extreme readings).

Tracked indicators (minimum 5):
  - HY credit spreads
  - 10Y-2Y yield curve
  - VIX
  - ISM Manufacturing
  - Financial conditions index (NFCI)

Output payload (per triggered indicator):
    {
        "layer": "Extreme Percentile",
        "signals_triggered": ["HY credit spreads"],
        "current_percentile": 95.3,
        "context_sentence": "...",
        "timestamp": "2026-03-10T12:00:00",
        "severity": "warning"
    }
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")

# Signal definitions: (csv_filename, column_name, display_label)
_SIGNALS = [
    ("high_yield_spread.csv", "high_yield_spread", "HY credit spreads"),
    ("yield_curve_10y2y.csv", "yield_curve_10y2y", "10Y-2Y yield curve"),
    ("vix_price.csv", "vix_price", "VIX"),
    ("ism_manufacturing.csv", "ism_manufacturing", "ISM Manufacturing"),
    ("nfci.csv", "nfci", "financial conditions index (NFCI)"),
]

_EXTREME_HIGH_PCT = 90.0   # ≥ this → extreme high
_EXTREME_LOW_PCT = 10.0    # ≤ this → extreme low
_MOMENTUM_FILTER_PCT = 70.0  # indicator must have been ≤ this within momentum window
_MOMENTUM_DAYS = 90
_WINDOW_YEARS = 10
_MIN_EPISODE_GAP_DAYS = 60  # deduplicate historical episodes


def _load_signal(csv_name: str, col_name: str) -> Optional[pd.Series]:
    """Load a signal CSV and return a date-indexed Series, sorted ascending."""
    filepath = DATA_DIR / csv_name
    if not filepath.exists():
        return None
    try:
        df = pd.read_csv(filepath)
        if "date" not in df.columns or col_name not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=["date", col_name]).sort_values("date")
        return df.set_index("date")[col_name]
    except Exception as e:
        logger.warning("Failed to load signal %s: %s", csv_name, e)
        return None


def _calculate_percentile_10y(
    series: Optional[pd.Series], current_value: float
) -> Optional[float]:
    """
    Calculate percentile rank of current_value within a 10-year rolling window.

    Returns a float 0–100, or None if series is None/empty.
    Falls back to full history when fewer than 10 years of data are available.
    """
    if series is None or len(series) == 0:
        return None
    if len(series) == 1:
        return 100.0 if current_value >= series.iloc[0] else 0.0

    cutoff = pd.Timestamp.today() - pd.DateOffset(years=_WINDOW_YEARS)
    try:
        windowed = series[series.index >= cutoff]
        if len(windowed) < 2:
            windowed = series
    except TypeError:
        windowed = series

    count_below = (windowed < current_value).sum()
    return float(count_below / len(windowed) * 100)


def _passes_momentum_filter(series: pd.Series) -> bool:
    """
    Return True if the indicator was at or below the 70th-percentile threshold
    at any point within the last MOMENTUM_DAYS days.

    For each value in the lookback window, we compute its percentile using the
    full historical context available at that date (i.e. all data up to and
    including that date, windowed to 10 years).  If any value in the window
    has a percentile ≤ 70, the filter passes.

    This approach correctly handles the boundary (day-90 inclusive) and
    avoids false positives from quantile interpolation artefacts.
    """
    if series is None or len(series) < 2:
        return False

    end_date = series.index[-1]
    lookback_start = end_date - timedelta(days=_MOMENTUM_DAYS)

    window = series[
        (series.index >= lookback_start) & (series.index <= end_date)
    ]
    if window.empty:
        return False

    for idx, val in window.items():
        history_to_date = series[series.index <= idx]
        pct = _calculate_percentile_10y(history_to_date, val)
        if pct is not None and pct <= _MOMENTUM_FILTER_PCT:
            return True

    return False


def _count_historical_occurrences_extreme(
    series: pd.Series,
    extreme_high: bool,
) -> int:
    """
    Count distinct historical episodes where the indicator was at an extreme
    level (≥90th pct for high, ≤10th pct for low), deduplicating episodes
    within MIN_EPISODE_GAP_DAYS of each other.

    Uses the full historical distribution to define the extreme threshold
    (90th or 10th quantile of all available data).  This is a reasonable
    approximation for the context sentence — we avoid nested historical
    percentile computations for performance.
    """
    if series is None or len(series) < 2:
        return 0

    if extreme_high:
        threshold = series.quantile(0.90)
        in_extreme = series >= threshold
    else:
        threshold = series.quantile(0.10)
        in_extreme = series <= threshold

    count = 0
    last_episode_date = None

    for date, val in series.items():
        if not in_extreme[date]:
            continue
        if last_episode_date is None or (date - last_episode_date).days >= _MIN_EPISODE_GAP_DAYS:
            count += 1
            last_episode_date = date

    return count


def _build_context_sentence(label: str, current_percentile: float, occurrences: int) -> str:
    """Build a plain-language context sentence for a Layer 2 alert."""
    direction = "high" if current_percentile >= 50 else "low"
    return (
        f"{label} has reached a historically {direction} reading "
        f"({current_percentile:.1f}th percentile on a 10-year window) — "
        f"this extreme level has been reached {occurrences} time(s) "
        f"in the available historical record."
    )


def check_extreme_percentile() -> list:
    """
    Run the Layer 2 extreme percentile check across all tracked indicators.

    Returns a list of alert payload dicts (one per triggered indicator).
    Returns an empty list if no indicator triggers.

    Each payload has keys: layer, signals_triggered, current_percentile,
    context_sentence, timestamp, severity.
    """
    payloads = []

    for csv_name, col_name, label in _SIGNALS:
        series = _load_signal(csv_name, col_name)
        if series is None or len(series) == 0:
            continue

        current_value = series.iloc[-1]
        current_pct = _calculate_percentile_10y(series, current_value)
        if current_pct is None:
            continue

        # Check extreme thresholds (inclusive boundaries)
        is_high_extreme = current_pct >= _EXTREME_HIGH_PCT
        is_low_extreme = current_pct <= _EXTREME_LOW_PCT

        if not is_high_extreme and not is_low_extreme:
            continue

        # Momentum filter: indicator must have been ≤ 70th pct within last 90 days
        if not _passes_momentum_filter(series):
            continue

        occurrences = _count_historical_occurrences_extreme(series, extreme_high=is_high_extreme)
        context_sentence = _build_context_sentence(label, current_pct, occurrences)

        payloads.append({
            "layer": "Extreme Percentile",
            "signals_triggered": [label],
            "current_percentile": round(current_pct, 2),
            "context_sentence": context_sentence,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "warning",
        })

    return payloads
