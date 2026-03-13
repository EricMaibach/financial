"""
Property Macro Interpretation Configuration (US-255.1)

Static interpretation texts for the property page's regime-conditioned
interpretation block. Keyed by (regime_state, hpi_trend) tuples.

Regime states match regime_detection.py output:
  'Bull', 'Neutral', 'Bear', 'Recession Watch'

HPI trend buckets (based on YoY % change in Case-Shiller HPI):
  'appreciating' — YoY HPI change >= +2%
  'flat'         — YoY HPI change between -2% and +2%
  'depreciating' — YoY HPI change <= -2%

Fallback key uses 'unknown' when regime data is unavailable.

Each text is 2–3 sentences written for a retail investor audience.
"""

PROPERTY_INTERPRETATIONS = {
    # ─── Bull Regime ─────────────────────────────────────────────────────────
    ("Bull", "appreciating"): (
        "Property values are rising in an already-expansionary macro environment — a combination "
        "that historically sustains real estate momentum as strong employment and income growth "
        "support buyer demand. Rental markets typically tighten alongside rising home prices, "
        "compressing vacancy rates and supporting landlord pricing power. "
        "Watch for affordability constraints as a leading indicator of demand cooling."
    ),
    ("Bull", "flat"): (
        "Home prices are stable despite a Bull macro regime, suggesting supply and demand are "
        "broadly balanced — a healthier dynamic than the frothy appreciation seen in prior cycles. "
        "Flat appreciation in a Bull environment often reflects normalization after a strong run "
        "rather than weakness, and is consistent with sustained rental demand at current rents."
    ),
    ("Bull", "depreciating"): (
        "Home prices are declining even as the broader economy is in expansion — an unusual "
        "divergence that typically reflects local oversupply, affordability exhaustion, or "
        "rising mortgage rates compressing buying power. "
        "Bull regime fundamentals (strong employment, consumer confidence) tend to put a floor "
        "under price declines, but sustained depreciation warrants monitoring for broader "
        "credit contagion via mortgage markets."
    ),

    # ─── Neutral Regime ──────────────────────────────────────────────────────
    ("Neutral", "appreciating"): (
        "Property values are appreciating during a Neutral macro regime — moderate economic "
        "conditions are supporting real estate demand without generating the exuberance of a "
        "Bull market. This is typically a stable environment for existing homeowners, though "
        "rising prices erode affordability for first-time buyers over time. "
        "Monitor rental vacancy trends as a leading signal of demand durability."
    ),
    ("Neutral", "flat"): (
        "Property values are flat in a Neutral macro regime — a balanced outcome consistent "
        "with neither strong cyclical tailwinds nor recessionary headwinds. "
        "Flat appreciation preserves real estate wealth in real terms (assuming inflation is low) "
        "and keeps rental markets in equilibrium; no significant directional tilt is warranted."
    ),
    ("Neutral", "depreciating"): (
        "Home prices are declining in a Neutral macro regime — a signal that housing-specific "
        "headwinds (affordability, oversupply, or rate sensitivity) are outweighing the "
        "stable macro backdrop. "
        "Neutral regimes rarely produce deep housing corrections without additional macro "
        "deterioration, but declining prices can weaken consumer balance sheets and dampen "
        "spending via the wealth effect."
    ),

    # ─── Bear Regime ─────────────────────────────────────────────────────────
    ("Bear", "appreciating"): (
        "Property values continue to appreciate despite a Bear macro regime — a divergence "
        "that reflects either lagged housing market data (real estate responds slowly to macro "
        "shifts) or genuine supply-side constraints protecting prices. "
        "Bear regimes historically pressure housing demand as employment uncertainty reduces "
        "buyer confidence; appreciation in this context is likely to slow or reverse as "
        "deteriorating conditions eventually feed through."
    ),
    ("Bear", "flat"): (
        "Home prices are holding flat in a Bear macro regime — resilience likely driven by "
        "low inventory or seller reluctance rather than strong buyer demand. "
        "Bear environments historically precede housing price corrections by several quarters "
        "as unemployment rises and mortgage delinquencies increase; "
        "flat prices should not be interpreted as a signal of underlying market health."
    ),
    ("Bear", "depreciating"): (
        "Property values are declining in a Bear macro regime — the typical outcome as rising "
        "unemployment, tightening credit standards, and weakening consumer confidence converge "
        "to reduce housing demand. "
        "Historically, Bear-regime housing corrections have lasted 4–8 quarters; "
        "REIT valuations and mortgage credit quality are the key metrics to monitor as "
        "lagging indicators of the correction's depth."
    ),

    # ─── Recession Watch Regime ───────────────────────────────────────────────
    ("Recession Watch", "appreciating"): (
        "Property values are still rising despite a Recession Watch signal — likely reflecting "
        "housing market inertia rather than fundamental strength. "
        "Recession Watch conditions historically precede housing price peaks by 2–4 quarters, "
        "as the full impact of tightening credit, rising defaults, and employment weakness "
        "takes time to reach transaction prices. "
        "Use this window to assess liquidity and leverage in any real estate exposure."
    ),
    ("Recession Watch", "flat"): (
        "Property values are flat under a Recession Watch regime — a fragile equilibrium "
        "that may reflect buyers and sellers at an impasse rather than genuine market balance. "
        "If recession risk escalates, historical patterns suggest prices follow the broader "
        "economy down with a 1–3 quarter lag; "
        "preserving real estate liquidity and avoiding leveraged property positions is prudent."
    ),
    ("Recession Watch", "depreciating"): (
        "Home prices are declining in a Recession Watch regime — the highest-risk combination "
        "for property holders, as falling values compound mortgage credit stress and can "
        "trigger a feedback loop of foreclosures and further price pressure. "
        "This environment historically calls for maximum caution on real estate exposure; "
        "focus on liquid assets and avoid extending leverage into property markets "
        "until the macro regime stabilizes."
    ),

    # ─── Fallback (regime data unavailable) ──────────────────────────────────
    ("unknown", "appreciating"): (
        "Property values are appreciating — home prices are rising on a year-over-year basis, "
        "reflecting demand strength relative to available supply. "
        "Rising home prices support consumer net worth and construction activity, though "
        "sustained appreciation compresses affordability and may eventually cool demand."
    ),
    ("unknown", "flat"): (
        "Property values are stable — home prices are showing little net change year-over-year, "
        "suggesting balanced supply and demand conditions in the residential market. "
        "Flat appreciation is generally a sign of market equilibrium and poses minimal "
        "systemic risk to mortgage credit quality."
    ),
    ("unknown", "depreciating"): (
        "Property values are declining — home prices are falling on a year-over-year basis, "
        "which can weaken consumer balance sheets via reduced home equity and raise default "
        "risk in the mortgage market. "
        "The depth and duration of the correction depend on underlying demand conditions, "
        "mortgage rate trends, and the broader economic environment."
    ),
}


def get_property_interpretation(regime_state, hpi_yoy_pct):
    """Return the interpretation text for the given regime state and HPI YoY change.

    Args:
        regime_state: str or None — e.g. 'Bull', 'Bear', 'Neutral', 'Recession Watch'
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

    if regime_state and regime_state not in ('Unknown', 'unknown'):
        key = (regime_state, hpi_trend)
    else:
        key = ('unknown', hpi_trend)

    return PROPERTY_INTERPRETATIONS.get(key), hpi_trend
