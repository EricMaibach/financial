"""
Layer 1 Alert Engine: Regime Transition Detection

Monitors CLI direction, yield curve slope (10Y-2Y), and financial conditions index (NFCI).
Fires when 2 or more of the 3 signals flip direction within a 30-day rolling window.

Output payload:
    {
        "layer": "Regime Transition",
        "signals_triggered": ["CLI", "yield curve (10Y-2Y)"],
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
    ("cli.csv", "cli", "CLI"),
    ("yield_curve_10y2y.csv", "yield_curve_10y2y", "yield curve (10Y-2Y)"),
    ("nfci.csv", "nfci", "financial conditions index (NFCI)"),
]

_SP500_CSV = "sp500_price.csv"
_SP500_COL = "sp500_price"


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


def _detect_direction_flip(series: pd.Series, window_days: int = 30) -> bool:
    """
    Return True if the signal's trend direction has reversed within the last window_days.

    Compares:
    - Recent direction:  (latest value) − (value ~window_days ago)
    - Prior direction:   (value ~window_days ago) − (value ~2*window_days ago)

    Returns True when the signs differ (direction has flipped).
    Consecutive identical values do NOT count as a flip.
    """
    if series is None or len(series) < 2:
        return False

    end_date = series.index[-1]
    mid_cutoff = end_date - timedelta(days=window_days)
    start_cutoff = end_date - timedelta(days=2 * window_days)

    recent_val = series.iloc[-1]

    # Value at or before the window boundary
    at_or_before_mid = series[series.index <= mid_cutoff]
    if at_or_before_mid.empty:
        return False
    mid_val = at_or_before_mid.iloc[-1]

    # Value at or before the 2x window boundary
    at_or_before_start = series[series.index <= start_cutoff]
    if at_or_before_start.empty:
        return False
    start_val = at_or_before_start.iloc[-1]

    recent_change = recent_val - mid_val
    prior_change = mid_val - start_val

    # Identical consecutive values → no directional information
    if recent_change == 0 or prior_change == 0:
        return False

    return (recent_change > 0) != (prior_change > 0)


def _count_historical_occurrences(
    window_days: int = 30,
    drawdown_threshold: float = 0.10,
    drawdown_horizon_days: int = 182,
    min_episode_gap_days: int = 60,
) -> tuple:
    """
    Scan the full historical record to count 2-of-3 signal flip episodes.

    Returns (n_drawdown, total_occurrences) where:
    - total_occurrences = number of distinct episodes where 2+ signals flipped
    - n_drawdown = subset of those episodes followed by an S&P 500 drawdown
                   >= drawdown_threshold within drawdown_horizon_days

    Episodes within min_episode_gap_days of each other are deduplicated.
    """
    signals_data = {}
    for csv_name, col_name, label in _SIGNALS:
        s = _load_signal(csv_name, col_name)
        if s is not None:
            signals_data[label] = s

    if len(signals_data) < 2:
        return 0, 0

    sp500 = _load_signal(_SP500_CSV, _SP500_COL)

    # Determine date range for scanning
    scan_start = max(s.index[0] for s in signals_data.values()) + timedelta(
        days=2 * window_days
    )
    scan_end = min(s.index[-1] for s in signals_data.values())

    if scan_start >= scan_end:
        return 0, 0

    total_occurrences = 0
    n_drawdown = 0
    last_episode_date = None

    # Advance month-by-month to keep complexity manageable
    scan_date = scan_start
    while scan_date <= scan_end:
        flipped_count = 0
        for label, series in signals_data.items():
            sub = series[series.index <= scan_date]
            if _detect_direction_flip(sub, window_days):
                flipped_count += 1

        if flipped_count >= 2:
            # Deduplicate: skip if too close to the last recorded episode
            if last_episode_date is None or (
                scan_date - last_episode_date
            ).days >= min_episode_gap_days:
                total_occurrences += 1
                last_episode_date = scan_date

                # Check for subsequent equity drawdown
                if sp500 is not None:
                    sp_at = sp500[sp500.index <= scan_date]
                    sp_after = sp500[
                        (sp500.index > scan_date)
                        & (sp500.index <= scan_date + timedelta(days=drawdown_horizon_days))
                    ]
                    if not sp_at.empty and not sp_after.empty:
                        entry_price = sp_at.iloc[-1]
                        min_price = sp_after.min()
                        if entry_price > 0 and (min_price / entry_price - 1) <= -drawdown_threshold:
                            n_drawdown += 1

        scan_date += timedelta(days=30)

    return n_drawdown, total_occurrences


def _build_context_sentence(
    signals_triggered: list,
    window_days: int,
    n_drawdown: int,
    total_occurrences: int,
) -> str:
    """Build a plain-language context sentence with historical occurrence data."""
    if len(signals_triggered) == 1:
        signals_str = signals_triggered[0]
        verb = "has shifted"
    elif len(signals_triggered) == 2:
        signals_str = f"{signals_triggered[0]} and {signals_triggered[1]}"
        verb = "have both shifted"
    else:
        signals_str = (
            ", ".join(signals_triggered[:-1]) + f", and {signals_triggered[-1]}"
        )
        verb = "have all shifted"

    return (
        f"{signals_str} {verb} in the last {window_days} days — "
        f"historically, regime transitions with this pattern have preceded "
        f"equity drawdowns within 3–6 months in "
        f"{n_drawdown} of {total_occurrences} occurrences."
    )


def check_regime_transition(window_days: int = 30) -> Optional[dict]:
    """
    Run the Layer 1 regime transition check.

    Returns an alert payload dict if 2+ of 3 signals have flipped direction
    within window_days, otherwise returns None.

    Payload keys: layer, signals_triggered, context_sentence, timestamp, severity
    """
    signals_triggered = []

    for csv_name, col_name, label in _SIGNALS:
        series = _load_signal(csv_name, col_name)
        if series is None:
            continue
        if _detect_direction_flip(series, window_days):
            signals_triggered.append(label)

    if len(signals_triggered) < 2:
        return None

    n_drawdown, total_occurrences = _count_historical_occurrences(window_days)
    context_sentence = _build_context_sentence(
        signals_triggered, window_days, n_drawdown, total_occurrences
    )

    return {
        "layer": "Regime Transition",
        "signals_triggered": signals_triggered,
        "context_sentence": context_sentence,
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "warning",
    }
