"""
Property Macro Interpretation Configuration (US-255.1)

Static interpretation texts for the property page interpretation block.
Keyed by hpi_trend.

HPI trend buckets (based on YoY % change in Case-Shiller HPI):
  'appreciating' — YoY HPI change >= +2%
  'flat'         — YoY HPI change between -2% and +2%
  'depreciating' — YoY HPI change <= -2%

Each text is 2–3 sentences written for a retail investor audience.
"""

PROPERTY_INTERPRETATIONS = {
    "appreciating": (
        "Property values are appreciating — home prices are rising on a year-over-year basis, "
        "reflecting demand strength relative to available supply. "
        "Rising home prices support consumer net worth and construction activity, though "
        "sustained appreciation compresses affordability and may eventually cool demand."
    ),
    "flat": (
        "Property values are stable — home prices are showing little net change year-over-year, "
        "suggesting balanced supply and demand conditions in the residential market. "
        "Flat appreciation is generally a sign of market equilibrium and poses minimal "
        "systemic risk to mortgage credit quality."
    ),
    "depreciating": (
        "Property values are declining — home prices are falling on a year-over-year basis, "
        "which can weaken consumer balance sheets via reduced home equity and raise default "
        "risk in the mortgage market. "
        "The depth and duration of the correction depend on underlying demand conditions, "
        "mortgage rate trends, and the broader economic environment."
    ),
}


def get_property_interpretation(_unused, hpi_yoy_pct):
    """Return the interpretation text for the given HPI YoY change.

    Args:
        _unused: ignored (kept for API compatibility)
        hpi_yoy_pct: float or None — Case-Shiller HPI year-over-year % change

    Returns:
        tuple: (interpretation_text, hpi_trend_bucket) where either may be None
    """
    if hpi_yoy_pct is None:
        return None, None

    if hpi_yoy_pct >= 2.0:
        hpi_trend = 'appreciating'
    elif hpi_yoy_pct <= -2.0:
        hpi_trend = 'depreciating'
    else:
        hpi_trend = 'flat'

    return PROPERTY_INTERPRETATIONS.get(hpi_trend), hpi_trend
