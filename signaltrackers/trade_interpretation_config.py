"""
Trade Balance Interpretation Configuration (US-206.1)

Regime-conditioned interpretation texts for the Global Trade Pulse homepage panel.
Keyed by (regime_state, trade_condition) tuples.

Regime states match regime_detection.py output:
  'Bull', 'Neutral', 'Bear', 'Recession Watch'

Trade conditions:
  'widening_deficit'   — current value negative, YoY change negative (deficit growing)
  'narrowing_deficit'  — current value negative, YoY change positive (deficit shrinking)
  'widening_surplus'   — current value positive, YoY change positive (surplus growing)
  'narrowing_surplus'  — current value positive, YoY change negative (surplus shrinking)

Fallback key ('unknown', condition) used when regime data is unavailable.
Each entry is a dict with 'label' (uppercase header) and 'body' (1-2 sentence copy).
"""

TRADE_INTERPRETATIONS = {
    # ─── Bull (Expansion) Regime ──────────────────────────────────────────────
    ("Bull", "widening_deficit"): {
        "label": "EXPANSION REGIME \u00b7 WIDENING DEFICIT",
        "body": (
            "Trade volumes are growing but the goods deficit is widening — a typical pattern "
            "in expansion as US import demand rises faster than exports. Watch for USD softness "
            "if the deficit widens materially."
        ),
    },
    ("Bull", "narrowing_deficit"): {
        "label": "EXPANSION REGIME \u00b7 NARROWING DEFICIT",
        "body": (
            "Trade conditions are improving alongside the expansion — a narrowing goods deficit "
            "reduces external drag and supports the USD. This is a constructive signal for the "
            "macro backdrop."
        ),
    },
    ("Bull", "widening_surplus"): {
        "label": "EXPANSION REGIME \u00b7 WIDENING SURPLUS",
        "body": (
            "The goods trade balance is improving materially in an expansion — export demand is "
            "strong. This is a positive signal for trade-sensitive sectors and USD stability."
        ),
    },
    ("Bull", "narrowing_surplus"): {
        "label": "EXPANSION REGIME \u00b7 NARROWING SURPLUS",
        "body": (
            "Export surplus is narrowing in an expansion phase — import demand is picking up, "
            "which is consistent with strong domestic consumption. Monitor for future current "
            "account pressure."
        ),
    },

    # ─── Bear (Contraction) Regime ────────────────────────────────────────────
    ("Bear", "widening_deficit"): {
        "label": "CONTRACTION REGIME \u00b7 WIDENING DEFICIT",
        "body": (
            "Trade volumes are contracting and the goods deficit is widening — a pressure pattern "
            "that adds headwinds for the USD and may weigh on export-sensitive sectors in an "
            "already-weak macro environment."
        ),
    },
    ("Bear", "narrowing_deficit"): {
        "label": "CONTRACTION REGIME \u00b7 NARROWING DEFICIT",
        "body": (
            "The goods deficit is narrowing in a contraction — typically because import demand is "
            "falling faster than export weakness. This may provide modest USD support but reflects "
            "weak domestic demand, not trade strength."
        ),
    },
    ("Bear", "widening_surplus"): {
        "label": "CONTRACTION REGIME \u00b7 IMPROVING BALANCE",
        "body": (
            "Trade balance is improving in a contraction — falling imports are reducing the "
            "deficit. This provides some buffer for the USD but the signal reflects demand "
            "weakness, not export-driven strength."
        ),
    },
    ("Bear", "narrowing_surplus"): {
        "label": "CONTRACTION REGIME \u00b7 MIXED SIGNAL",
        "body": (
            "Export surplus is narrowing as the contraction weighs on global trade. External "
            "demand is softening — watch for further deterioration in export-heavy sectors."
        ),
    },

    # ─── Neutral Regime ──────────────────────────────────────────────────────
    ("Neutral", "widening_deficit"): {
        "label": "NEUTRAL REGIME \u00b7 WIDENING DEFICIT",
        "body": (
            "The goods trade deficit is widening in a neutral macro environment — modest negative "
            "signal for the USD and external balance. No immediate implication for domestic growth."
        ),
    },
    ("Neutral", "narrowing_deficit"): {
        "label": "NEUTRAL REGIME \u00b7 NARROWING DEFICIT",
        "body": (
            "Trade balance is improving slightly in a neutral regime — a positive but non-decisive "
            "signal. External drag on growth is easing gradually."
        ),
    },
    ("Neutral", "widening_surplus"): {
        "label": "NEUTRAL REGIME \u00b7 WIDENING SURPLUS",
        "body": (
            "Trade balance is strengthening in a neutral regime — modest positive for USD and "
            "reduced external drag. Not a regime-moving signal on its own."
        ),
    },
    ("Neutral", "narrowing_surplus"): {
        "label": "NEUTRAL REGIME \u00b7 STABLE TRADE",
        "body": (
            "Trade balance is relatively stable in a neutral macro environment. No significant "
            "trade flow signal at this time."
        ),
    },

    # ─── Recession Watch Regime ───────────────────────────────────────────────
    ("Recession Watch", "widening_deficit"): {
        "label": "RECESSION WATCH \u00b7 WIDENING DEFICIT",
        "body": (
            "Trade conditions are deteriorating alongside elevated recession risk. A widening "
            "goods deficit in a recession-watch environment adds external pressure — this "
            "combination has historically preceded USD stress and tightening financial conditions."
        ),
    },
    ("Recession Watch", "narrowing_deficit"): {
        "label": "RECESSION WATCH \u00b7 NARROWING DEFICIT",
        "body": (
            "The goods deficit is narrowing in a recession-watch environment — likely reflecting "
            "falling import demand as businesses and consumers pull back. This is a defensive, "
            "not constructive, signal."
        ),
    },
    ("Recession Watch", "widening_surplus"): {
        "label": "RECESSION WATCH \u00b7 IMPROVING BALANCE",
        "body": (
            "Trade balance is improving as import demand contracts in a recession-watch "
            "environment. The improvement is driven by weakness, not export strength — "
            "treat cautiously."
        ),
    },
    ("Recession Watch", "narrowing_surplus"): {
        "label": "RECESSION WATCH \u00b7 WEAKENING TRADE",
        "body": (
            "Export surplus is narrowing as global demand softens — a leading indicator of "
            "further trade deterioration consistent with elevated recession risk."
        ),
    },
}

# Fallback entries for all conditions when regime data is unavailable
for _condition in ("widening_deficit", "narrowing_deficit", "widening_surplus", "narrowing_surplus"):
    TRADE_INTERPRETATIONS[("unknown", _condition)] = {
        "label": "TRADE BALANCE",
        "body": None,  # Filled by get_trade_interpretation using percentile fallback
    }


def get_trade_interpretation(regime_state, trade_condition, trade_percentile=None):
    """Return the interpretation label and body for the given regime and trade condition.

    Args:
        regime_state: str or None — e.g. 'Bull', 'Bear', 'Neutral', 'Recession Watch'
        trade_condition: str or None — one of the four trade condition constants
        trade_percentile: float or None — used for fallback copy when regime unavailable

    Returns:
        tuple: (label, body) where either may be None
    """
    if trade_condition is None:
        return None, None

    if regime_state and regime_state not in ('Unknown', 'unknown', ''):
        key = (regime_state, trade_condition)
    else:
        key = ('unknown', trade_condition)

    entry = TRADE_INTERPRETATIONS.get(key)
    if entry is None:
        return None, None

    label = entry['label']
    body = entry['body']

    # Fallback body when regime is unknown — use percentile-based generic text
    if body is None and trade_percentile is not None:
        pct_int = int(round(trade_percentile))
        body = (
            f"US goods trade balance is at the {pct_int}th percentile of the past 10 years. "
            "A reading below the 33rd percentile indicates below-average trade flow conditions."
        )
    elif body is None:
        return None, None

    return label, body
