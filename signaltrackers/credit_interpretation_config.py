"""
Credit Spread Interpretation Configuration (US-169.2)

Static interpretation texts for the credit page interpretation block.
Keyed by spread_bucket.

Spread buckets:
  'tight'  — HY OAS at or below 25th percentile of 20-year history
  'normal' — HY OAS between 25th and 75th percentile
  'wide'   — HY OAS above 75th percentile

Each text is 2–3 sentences written for a retail investor audience.
"""

CREDIT_INTERPRETATIONS = {
    "tight": (
        "Credit spreads are historically tight — in the bottom quartile of 20-year history. "
        "Tight spread environments reflect strong risk appetite and low perceived default risk, "
        "but they also reduce the cushion against negative surprises; "
        "spread normalization from these levels tends to be gradual in benign environments "
        "and rapid during stress episodes."
    ),
    "normal": (
        "Credit spreads are within their normal historical range — between the 25th and 75th "
        "percentile of 20-year history. "
        "This represents balanced market pricing with neither stress nor complacency dominant. "
        "Credit allocations can remain near strategic weights in this environment."
    ),
    "wide": (
        "Credit spreads are elevated relative to history — above the 75th percentile of "
        "20-year history. "
        "Wider spreads reflect elevated default concerns and tighter corporate financing conditions. "
        "Historically, spread widening at these levels has coincided with below-average earnings "
        "growth and above-average credit selection risk; exercise caution with lower-quality credits."
    ),
}


def get_credit_interpretation(_unused, hy_percentile):
    """Return the interpretation text for the given HY percentile.

    Args:
        _unused: ignored (kept for API compatibility)
        hy_percentile: float or None — HY OAS percentile (0–100)

    Returns:
        tuple: (interpretation_text, spread_bucket) where either may be None
    """
    if hy_percentile is None:
        return None, None

    if hy_percentile <= 25:
        spread_bucket = 'tight'
    elif hy_percentile <= 75:
        spread_bucket = 'normal'
    else:
        spread_bucket = 'wide'

    return CREDIT_INTERPRETATIONS.get(spread_bucket), spread_bucket
