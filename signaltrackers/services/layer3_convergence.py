"""
Layer 3 Alert Engine: Multi-Signal Convergence

Fires when 3 or more tracked indicators simultaneously sit in stress territory
(>75th percentile or <25th percentile) AND all agree on the same direction
(all risk-off or all risk-on).

Uses the same 5 indicators as Layer 2 (10-year rolling percentile window).

Output payload:
    {
        "layer": "Multi-Signal Convergence",
        "signals_triggered": ["HY credit spreads", "VIX", "financial conditions index (NFCI)"],
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

from services.layer2_extreme_percentile import (
    _SIGNALS,
    _MIN_EPISODE_GAP_DAYS,
    _WINDOW_YEARS,
    _load_signal,
    _calculate_percentile_10y,
)

logger = logging.getLogger(__name__)

_STRESS_HIGH_PCT = 75.0  # >75th = risk-off
_STRESS_LOW_PCT = 25.0   # <25th = risk-on
_MIN_CONVERGENCE = 3     # minimum number of agreeing signals to fire


def _count_historical_convergence_occurrences(signal_configs: list) -> int:
    """
    Count distinct historical months where 3+ tracked indicators were
    simultaneously in the same stress direction (>75th or <25th pct).

    Uses monthly sampling for performance; deduplicates episodes within
    MIN_EPISODE_GAP_DAYS of each other.

    Returns total episode count.
    """
    loaded = []
    for csv_name, col_name, label in signal_configs:
        s = _load_signal(csv_name, col_name)
        if s is not None:
            loaded.append((label, s))

    if len(loaded) < _MIN_CONVERGENCE:
        return 0

    # Determine scannable date range
    scan_start = max(s.index[0] for _, s in loaded) + timedelta(days=60)
    scan_end = min(s.index[-1] for _, s in loaded)

    if scan_start >= scan_end:
        return 0

    count = 0
    last_episode_date = None
    scan_date = scan_start

    while scan_date <= scan_end:
        risk_off = []
        risk_on = []

        for label, series in loaded:
            sub = series[series.index <= scan_date]
            if sub.empty:
                continue
            current_value = sub.iloc[-1]
            pct = _calculate_percentile_10y(sub, current_value)
            if pct is None:
                continue
            if pct > _STRESS_HIGH_PCT:
                risk_off.append(label)
            elif pct < _STRESS_LOW_PCT:
                risk_on.append(label)

        triggered = risk_off if len(risk_off) >= _MIN_CONVERGENCE else (
            risk_on if len(risk_on) >= _MIN_CONVERGENCE else []
        )

        if triggered:
            if last_episode_date is None or (scan_date - last_episode_date).days >= _MIN_EPISODE_GAP_DAYS:
                count += 1
                last_episode_date = scan_date

        scan_date += timedelta(days=30)

    return count


def _build_context_sentence(signals: list, direction: str, occurrences: int) -> str:
    """Build a plain-language context sentence for a Layer 3 alert."""
    if len(signals) == 1:
        signals_str = signals[0]
    elif len(signals) == 2:
        signals_str = f"{signals[0]} and {signals[1]}"
    else:
        signals_str = ", ".join(signals[:-1]) + f", and {signals[-1]}"

    return (
        f"{len(signals)} indicators simultaneously in {direction} stress territory: "
        f"{signals_str}. "
        f"Historically, this convergence pattern has occurred "
        f"{occurrences} time(s) in the available record."
    )


def check_convergence(signal_configs: Optional[list] = None) -> Optional[dict]:
    """
    Run the Layer 3 multi-signal convergence check.

    Returns an alert payload dict if 3+ indicators agree on direction,
    otherwise returns None.

    Args:
        signal_configs: list of (csv_name, col_name, label) tuples.
                        Defaults to the standard 5 Layer 2/3 indicators.

    Payload keys: layer, signals_triggered, context_sentence, timestamp, severity
    """
    if signal_configs is None:
        signal_configs = list(_SIGNALS)

    risk_off = []
    risk_on = []

    for csv_name, col_name, label in signal_configs:
        series = _load_signal(csv_name, col_name)
        if series is None or len(series) == 0:
            continue

        current_value = series.iloc[-1]
        pct = _calculate_percentile_10y(series, current_value)
        if pct is None:
            continue

        if pct > _STRESS_HIGH_PCT:
            risk_off.append(label)
        elif pct < _STRESS_LOW_PCT:
            risk_on.append(label)

    # Determine if convergence threshold is met
    if len(risk_off) >= _MIN_CONVERGENCE:
        triggered = risk_off
        direction = "risk-off"
    elif len(risk_on) >= _MIN_CONVERGENCE:
        triggered = risk_on
        direction = "risk-on"
    else:
        return None

    occurrences = _count_historical_convergence_occurrences(signal_configs)
    context_sentence = _build_context_sentence(triggered, direction, occurrences)

    return {
        "layer": "Multi-Signal Convergence",
        "signals_triggered": triggered,
        "context_sentence": context_sentence,
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "warning",
    }
