"""
Credit Spread Interpretation Configuration (US-169.2)

Static interpretation texts for the credit page interpretation block.
Keyed by (regime_state, spread_bucket) tuples.

Note: regime_state is always None now (old regime system removed).
The 'unknown' fallback entries are used exclusively.

Spread buckets:
  'tight'  — HY OAS at or below 25th percentile of 20-year history
  'normal' — HY OAS between 25th and 75th percentile
  'wide'   — HY OAS above 75th percentile

Fallback key uses 'unknown' when regime data is unavailable.

Each text is 2–3 sentences written for a retail investor audience.
"""

CREDIT_INTERPRETATIONS = {
    # ─── Bull Regime ─────────────────────────────────────────────────────────
    ("Bull", "tight"): (
        "Credit conditions are unusually accommodative — HY spreads are in the bottom quartile "
        "of 20-year history, consistent with the elevated risk appetite typical of Bull regimes. "
        "Historically, spreads this tight in Bull markets have sustained for several more quarters "
        "before mean-reverting, but the cushion against a negative surprise is thin — "
        "consider trimming lower-quality credit exposure opportunistically."
    ),
    ("Bull", "normal"): (
        "Credit spreads are in their normal historical range and aligned with the constructive "
        "fundamentals typical of a Bull macro regime. Risk appetite is healthy but not extreme, "
        "making this a reasonable environment for balanced credit positioning with a modest tilt "
        "toward higher-quality high-yield names that benefit from economic expansion."
    ),
    ("Bull", "wide"): (
        "HY spreads are elevated relative to history despite a Bull macro regime — an unusual "
        "divergence that warrants attention. Credit markets may be pricing in sector-specific "
        "stress or risks not yet reflected in the broader macro picture. "
        "Watch for spread tightening as a confirmation signal before adding credit risk; "
        "sustained widening in a Bull regime has historically foreshadowed regime transitions."
    ),

    # ─── Neutral Regime ──────────────────────────────────────────────────────
    ("Neutral", "tight"): (
        "Credit spreads are tighter than historical norms in a Neutral macro regime, suggesting "
        "late-cycle complacency — the market is pricing in limited risk at a time when the "
        "macro outlook is genuinely uncertain. "
        "Consider favoring quality over yield: the spread cushion against a regime deterioration "
        "to Bear or Recession Watch is limited at these levels."
    ),
    ("Neutral", "normal"): (
        "Credit spreads are in line with their long-run median, consistent with the balanced "
        "conditions of a Neutral macro regime. Neither stress nor complacency dominates market "
        "pricing, making this a reasonable environment for maintaining diversified credit "
        "exposure near strategic weights while favoring BB-rated names with solid fundamentals."
    ),
    ("Neutral", "wide"): (
        "Spreads are running above historical norms in a Neutral regime, suggesting credit "
        "markets are more cautious than the macro picture warrants — or that pockets of "
        "sector stress are emerging ahead of a broader regime shift. "
        "Selectivity is rewarded: focus on higher-quality credit and avoid issuers with "
        "weak balance sheets or near-term refinancing needs."
    ),

    # ─── Bear Regime ─────────────────────────────────────────────────────────
    ("Bear", "tight"): (
        "Spreads are historically tight despite a Bear macro regime — a rare and potentially "
        "unstable combination. Tight credit pricing in a Bear environment typically reflects "
        "a lag rather than genuine credit health, and past divergences of this type have "
        "usually resolved via spread widening rather than regime improvement. "
        "Approach lower-quality credit with significant caution."
    ),
    ("Bear", "normal"): (
        "Credit spreads are at normal historical levels during a Bear regime — a mixed signal. "
        "While markets have not yet moved to stress territory, Bear regimes historically "
        "precede material spread widening by several months. "
        "Reducing high-yield exposure in favor of investment-grade and short-duration credit "
        "is consistent with typical Bear regime positioning."
    ),
    ("Bear", "wide"): (
        "Credit stress is elevated and consistent with a Bear macro regime — spreads are "
        "above the 75th percentile of 20-year history, reflecting rising default concern "
        "and tighter corporate financing conditions. "
        "Historically, spread peaks in Bear regimes have preceded equity market bottoms by "
        "2–6 months; focus on investment-grade, and avoid distressed names unless the "
        "risk-reward is explicitly priced into the position."
    ),

    # ─── Recession Watch Regime ───────────────────────────────────────────────
    ("Recession Watch", "tight"): (
        "Spreads are historically tight despite a Recession Watch macro signal — "
        "an unusual and potentially unstable divergence. "
        "Credit markets may not yet be pricing in the deteriorating fundamentals that "
        "could materialize if recession risk escalates. "
        "Capital preservation and duration management should take priority; "
        "do not rely on tight spreads as a signal of underlying credit health."
    ),
    ("Recession Watch", "normal"): (
        "Credit spreads at normal historical levels during a Recession Watch regime suggest "
        "markets are not yet fully pricing in recession risk. "
        "Historically, spreads have widened significantly once Recession Watch conditions "
        "have persisted for multiple quarters. "
        "Reducing high-yield exposure and moving up the credit quality stack is consistent "
        "with prudent Recession Watch positioning."
    ),
    ("Recession Watch", "wide"): (
        "Credit stress is significantly elevated, consistent with a Recession Watch regime. "
        "Spreads above the 75th percentile of 20-year history reflect rising default risk "
        "and tighter corporate financing — typical late-cycle stress dynamics. "
        "Capital preservation is the priority: focus on investment-grade or better, "
        "and consider increasing cash or short-duration instruments while awaiting "
        "clearer signs of spread normalization."
    ),

    # ─── Fallback (regime data unavailable) ──────────────────────────────────
    ("unknown", "tight"): (
        "Credit spreads are historically tight — in the bottom quartile of 20-year history. "
        "Tight spread environments reflect strong risk appetite and low perceived default risk, "
        "but they also reduce the cushion against negative surprises; "
        "spread normalization from these levels tends to be gradual in benign environments "
        "and rapid during stress episodes."
    ),
    ("unknown", "normal"): (
        "Credit spreads are within their normal historical range — between the 25th and 75th "
        "percentile of 20-year history. "
        "This represents balanced market pricing with neither stress nor complacency dominant. "
        "Credit allocations can remain near strategic weights in this environment."
    ),
    ("unknown", "wide"): (
        "Credit spreads are elevated relative to history — above the 75th percentile of "
        "20-year history. "
        "Wider spreads reflect elevated default concerns and tighter corporate financing conditions. "
        "Historically, spread widening at these levels has coincided with below-average earnings "
        "growth and above-average credit selection risk; exercise caution with lower-quality credits."
    ),
}


def get_credit_interpretation(regime_state, hy_percentile):
    """Return the interpretation text for the given regime state and HY percentile.

    Args:
        regime_state: str or None — e.g. 'Bull', 'Bear', 'Neutral', 'Recession Watch'
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

    if regime_state and regime_state not in ('Unknown', 'unknown'):
        key = (regime_state, spread_bucket)
    else:
        key = ('unknown', spread_bucket)

    return CREDIT_INTERPRETATIONS.get(key), spread_bucket
