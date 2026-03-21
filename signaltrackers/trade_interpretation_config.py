"""
Trade Balance Interpretation Configuration (US-206.1)

Interpretation texts for the Global Trade Pulse homepage panel.
Keyed by trade_condition.

Trade conditions:
  'widening_deficit'   — current value negative, YoY change negative (deficit growing)
  'narrowing_deficit'  — current value negative, YoY change positive (deficit shrinking)
  'widening_surplus'   — current value positive, YoY change positive (surplus growing)
  'narrowing_surplus'  — current value positive, YoY change negative (surplus shrinking)

Each entry is a dict with 'label' (uppercase header) and 'body' (1-2 sentence copy).
"""

TRADE_INTERPRETATIONS = {
    "widening_deficit": {
        "label": "TRADE BALANCE",
        "body": None,  # Filled by get_trade_interpretation using percentile fallback
    },
    "narrowing_deficit": {
        "label": "TRADE BALANCE",
        "body": None,
    },
    "widening_surplus": {
        "label": "TRADE BALANCE",
        "body": None,
    },
    "narrowing_surplus": {
        "label": "TRADE BALANCE",
        "body": None,
    },
}


def get_trade_interpretation(_unused, trade_condition, trade_percentile=None):
    """Return the interpretation label and body for the given trade condition.

    Args:
        _unused: ignored (kept for API compatibility)
        trade_condition: str or None — one of the four trade condition constants
        trade_percentile: float or None — used for fallback copy

    Returns:
        tuple: (label, body) where either may be None
    """
    if trade_condition is None:
        return None, None

    entry = TRADE_INTERPRETATIONS.get(trade_condition)
    if entry is None:
        return None, None

    label = entry['label']
    body = entry['body']

    # Percentile-based generic text
    if body is None and trade_percentile is not None:
        pct_int = int(round(trade_percentile))
        body = (
            f"US goods trade balance is at the {pct_int}th percentile of the past 10 years. "
            "A reading below the 33rd percentile indicates below-average trade flow conditions."
        )
    elif body is None:
        return None, None

    return label, body
