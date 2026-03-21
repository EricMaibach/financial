"""Market Conditions configuration — quadrant × liquidity context sentences
and signal annotations (US-324.1).

Provides CATEGORY_CONDITIONS_CONTEXT and SIGNAL_CONDITIONS_ANNOTATIONS
with quadrant × liquidity context sentences.
"""

# ---------------------------------------------------------------------------
# Liquidity state simplification
# ---------------------------------------------------------------------------
# The 5 liquidity states map to 3 for context sentence lookup:
#   Strongly Expanding / Expanding → 'Expanding'
#   Neutral                        → 'Neutral'
#   Contracting / Strongly Contracting → 'Contracting'

LIQUIDITY_STATE_SIMPLIFIED = {
    'Strongly Expanding': 'Expanding',
    'Expanding': 'Expanding',
    'Neutral': 'Neutral',
    'Contracting': 'Contracting',
    'Strongly Contracting': 'Contracting',
}


def get_simplified_liquidity(liquidity_state):
    """Return simplified liquidity state for context lookup."""
    return LIQUIDITY_STATE_SIMPLIFIED.get(liquidity_state, 'Neutral')


# ---------------------------------------------------------------------------
# Category context sentences — 7 categories × 4 quadrants × 3 liquidity = 84
# ---------------------------------------------------------------------------

CATEGORY_CONDITIONS_CONTEXT = {
    'Credit': {
        ('Goldilocks', 'Expanding'): 'Credit spreads historically tighten further in Goldilocks with expanding liquidity \u2014 carry trades supported.',
        ('Goldilocks', 'Neutral'): 'Goldilocks conditions support credit; spreads should remain well-behaved.',
        ('Goldilocks', 'Contracting'): 'Goldilocks supports credit quality, but contracting liquidity may limit spread compression.',
        ('Reflation', 'Expanding'): 'Rising inflation pressures credit quality, but expanding liquidity provides a cushion.',
        ('Reflation', 'Neutral'): 'Rising inflation creates headwinds for lower-quality credit; favor investment grade.',
        ('Reflation', 'Contracting'): 'Tightening liquidity and rising inflation create headwinds for lower-quality credit.',
        ('Stagflation', 'Expanding'): "Stagflation is historically tough for credit \u2014 expanding liquidity may cushion but doesn\u2019t fix fundamentals.",
        ('Stagflation', 'Neutral'): 'Stagflation is the worst environment for credit \u2014 expect spread widening.',
        ('Stagflation', 'Contracting'): 'Severe credit stress likely. Spreads at current levels may underestimate risk.',
        ('Deflation Risk', 'Expanding'): 'Flight to quality benefits high-grade credit; expanding liquidity limits systemic risk.',
        ('Deflation Risk', 'Neutral'): 'Flight to quality underway; focus on investment-grade credit, avoid high-yield.',
        ('Deflation Risk', 'Contracting'): 'Credit contraction underway. Focus on balance sheet quality and short duration.',
    },
    'Rates': {
        ('Goldilocks', 'Expanding'): 'Falling inflation supports bonds; expanding liquidity adds a tailwind to duration.',
        ('Goldilocks', 'Neutral'): 'Goldilocks supports bonds as inflation cools; duration is rewarded.',
        ('Goldilocks', 'Contracting'): 'Inflation cooling supports bonds, but liquidity contraction may limit gains.',
        ('Reflation', 'Expanding'): 'Rising inflation pressures bonds; expanding liquidity creates cross-currents in rates.',
        ('Reflation', 'Neutral'): 'Rising inflation is a headwind for bonds; shorter duration reduces risk.',
        ('Reflation', 'Contracting'): 'Rising inflation and contracting liquidity both weigh on bonds \u2014 shorten duration.',
        ('Stagflation', 'Expanding'): 'Stagflation puts bonds under pressure from inflation; expanding liquidity partially offsets.',
        ('Stagflation', 'Neutral'): 'Bonds struggle in stagflation \u2014 rising inflation and slowing growth create uncertainty.',
        ('Stagflation', 'Contracting'): 'Worst case for bonds: rising inflation meets contracting liquidity. Minimize duration.',
        ('Deflation Risk', 'Expanding'): 'Deflation risk drives flight to safety; bonds rally as rate cuts are priced in.',
        ('Deflation Risk', 'Neutral'): 'Falling inflation and slowing growth support long bonds; rate cuts likely ahead.',
        ('Deflation Risk', 'Contracting'): 'Flight to safety bid supports Treasuries despite liquidity contraction.',
    },
    'Equities': {
        ('Goldilocks', 'Expanding'): 'Best environment for equities: accelerating growth, cooling inflation, expanding liquidity.',
        ('Goldilocks', 'Neutral'): 'Goldilocks favors equities broadly; growth stocks and tech historically outperform.',
        ('Goldilocks', 'Contracting'): 'Growth and inflation favor equities, but contracting liquidity may cap upside.',
        ('Reflation', 'Expanding'): 'Growth and liquidity support equities; watch for inflation eroding real returns.',
        ('Reflation', 'Neutral'): 'Equities benefit from growth; cyclicals and commodities-linked sectors outperform.',
        ('Reflation', 'Contracting'): 'Rising inflation with tightening liquidity creates rotation risk \u2014 favor pricing power.',
        ('Stagflation', 'Expanding'): "Stagflation is tough for equities; expanding liquidity may cushion but doesn\u2019t reverse headwinds.",
        ('Stagflation', 'Neutral'): 'Worst quadrant for equity real returns \u2014 defensive sectors and pricing power outperform.',
        ('Stagflation', 'Contracting'): 'Maximum headwinds for equities: slowing growth, rising inflation, tight liquidity.',
        ('Deflation Risk', 'Expanding'): 'Equities face growth headwinds, but expanding liquidity signals policy response \u2014 watch for reversal.',
        ('Deflation Risk', 'Neutral'): 'Slowing growth weighs on equities; defensive positioning and quality factors favored.',
        ('Deflation Risk', 'Contracting'): 'Growth slowing with tight liquidity \u2014 risk of accelerating drawdowns. Preserve capital.',
    },
    'Dollar': {
        ('Goldilocks', 'Expanding'): 'Risk-on flows and expanding liquidity typically weaken the dollar; EM assets benefit.',
        ('Goldilocks', 'Neutral'): 'Dollar range-bound in Goldilocks; no strong directional catalyst.',
        ('Goldilocks', 'Contracting'): 'Contracting liquidity supports the dollar despite favorable growth conditions.',
        ('Reflation', 'Expanding'): 'Rising inflation and loose liquidity weaken dollar purchasing power; commodities benefit.',
        ('Reflation', 'Neutral'): 'Dollar mixed in reflation \u2014 inflation weakens, but rate hike expectations support.',
        ('Reflation', 'Contracting'): 'Rate hike expectations from inflation plus tight liquidity support a stronger dollar.',
        ('Stagflation', 'Expanding'): 'Dollar weakens as stagflation erodes confidence; liquidity flows seek alternatives.',
        ('Stagflation', 'Neutral'): 'Dollar direction depends on whether markets price growth weakness or inflation first.',
        ('Stagflation', 'Contracting'): 'Safe-haven dollar demand competes with stagflation erosion \u2014 volatile, range-bound.',
        ('Deflation Risk', 'Expanding'): 'Policy response (liquidity expansion) fights deflationary dollar strength \u2014 watch Fed actions.',
        ('Deflation Risk', 'Neutral'): 'Dollar strengthens on safe-haven demand; EM and carry trades face pressure.',
        ('Deflation Risk', 'Contracting'): 'Strong dollar safe-haven bid; global dollar shortage risk for EM borrowers.',
    },
    'Crypto': {
        ('Goldilocks', 'Expanding'): 'Expanding liquidity is the primary crypto driver \u2014 historically favorable with ~90-day lag.',
        ('Goldilocks', 'Neutral'): 'Liquidity neutral; crypto direction depends on cycle-specific factors, not macro quadrant.',
        ('Goldilocks', 'Contracting'): 'Contracting liquidity is a headwind for crypto regardless of favorable macro conditions.',
        ('Reflation', 'Expanding'): 'Expanding liquidity supports crypto; Bitcoin correlates 0.94 with M2, not growth/inflation.',
        ('Reflation', 'Neutral'): 'Liquidity neutral; crypto may benefit from inflation hedge narrative but primary driver is flat.',
        ('Reflation', 'Contracting'): 'Contracting liquidity weighs on crypto despite reflation narrative \u2014 M2 matters more than CPI.',
        ('Stagflation', 'Expanding'): 'Expanding liquidity supports crypto even in stagflation \u2014 the M2 correlation dominates.',
        ('Stagflation', 'Neutral'): 'Liquidity flat in stagflation; crypto driven by halving cycle and institutional flows.',
        ('Stagflation', 'Contracting'): 'Contracting liquidity in stagflation is the worst combination for crypto risk assets.',
        ('Deflation Risk', 'Expanding'): 'Policy-driven liquidity expansion (QE) historically triggers strong crypto recoveries.',
        ('Deflation Risk', 'Neutral'): 'Liquidity neutral with deflation risk; crypto volatile but watch for policy response pivot.',
        ('Deflation Risk', 'Contracting'): 'Contracting liquidity in deflation \u2014 maximum headwind for crypto. Watch for QE pivot.',
    },
    'Safe Havens': {
        ('Goldilocks', 'Expanding'): 'Safe havens underperform in Goldilocks; gold neutral, Treasuries supported by falling inflation.',
        ('Goldilocks', 'Neutral'): 'Safe havens are secondary in Goldilocks; hold for diversification, not returns.',
        ('Goldilocks', 'Contracting'): 'Goldilocks limits safe haven demand, but liquidity contraction adds a hedge rationale.',
        ('Reflation', 'Expanding'): 'Gold benefits from inflation + liquidity expansion; Treasuries struggle with rising rates.',
        ('Reflation', 'Neutral'): 'Gold outperforms on inflation hedge; Treasuries underperform. Mixed safe haven picture.',
        ('Reflation', 'Contracting'): 'Gold mixed (inflation bullish, liquidity bearish); Treasuries face dual headwinds.',
        ('Stagflation', 'Expanding'): 'Gold shines in stagflation \u2014 best quadrant historically. Expanding liquidity amplifies.',
        ('Stagflation', 'Neutral'): 'Gold is the primary safe haven in stagflation; Treasuries hurt by rising inflation.',
        ('Stagflation', 'Contracting'): 'Gold remains best haven in stagflation but liquidity headwind limits upside.',
        ('Deflation Risk', 'Expanding'): 'Treasuries rally on flight to safety; gold mixed \u2014 benefits from uncertainty, hurt by deflation.',
        ('Deflation Risk', 'Neutral'): 'Flight to safety drives Treasuries higher; gold benefits from uncertainty premium.',
        ('Deflation Risk', 'Contracting'): 'Maximum flight to safety \u2014 Treasuries are the primary safe haven. Gold secondary.',
    },
    'Property': {
        ('Goldilocks', 'Expanding'): 'Best environment for property: growth supports rents, expanding liquidity supports prices.',
        ('Goldilocks', 'Neutral'): 'Goldilocks supports property fundamentals; low rates and growth favor housing.',
        ('Goldilocks', 'Contracting'): 'Growth supports property fundamentals but tightening liquidity may slow price appreciation.',
        ('Reflation', 'Expanding'): 'Property benefits from inflation hedging; expanding liquidity supports mortgage availability.',
        ('Reflation', 'Neutral'): 'Rising inflation supports property as a real asset; watch mortgage rate pressure.',
        ('Reflation', 'Contracting'): 'Inflation supports property values but tightening liquidity restricts mortgage access.',
        ('Stagflation', 'Expanding'): 'Property fundamentals challenged by slowing growth; expanding liquidity partially offsets.',
        ('Stagflation', 'Neutral'): 'Slowing growth weakens rental demand; rising inflation supports real asset valuations.',
        ('Stagflation', 'Contracting'): 'Tough environment for property: slowing growth, rising costs, tight financing.',
        ('Deflation Risk', 'Expanding'): 'Deflation risk threatens property values; policy response (rate cuts) supports housing.',
        ('Deflation Risk', 'Neutral'): 'Falling prices and slowing growth pressure property; watch for policy pivot.',
        ('Deflation Risk', 'Contracting'): 'Maximum property headwinds: falling demand, tight credit, deflationary pressure.',
    },
}


def get_category_conditions_context(category, quadrant, liquidity_state):
    """Look up the context sentence for a category given quadrant and liquidity.

    Args:
        category: One of 'Credit', 'Rates', 'Equities', 'Dollar', 'Crypto',
                  'Safe Havens', 'Property'.
        quadrant: One of 'Goldilocks', 'Reflation', 'Stagflation', 'Deflation Risk'.
        liquidity_state: Raw 5-state liquidity string (simplified internally).

    Returns:
        Context sentence string, or empty string if not found.
    """
    simplified_liq = get_simplified_liquidity(liquidity_state)
    return CATEGORY_CONDITIONS_CONTEXT.get(category, {}).get(
        (quadrant, simplified_liq), ''
    )


# ---------------------------------------------------------------------------
# Signal annotations — 18 signals × 4 quadrants = 72
# ---------------------------------------------------------------------------

SIGNAL_CONDITIONS_ANNOTATIONS = {
    'high_yield_spread': {
        'Goldilocks': '\u2713 Tight spreads expected in Goldilocks; carry trade supported.',
        'Reflation': '\u2500 Growth supports credit, but rising inflation pressures margins.',
        'Stagflation': '\u25b2 Spreads typically widen in stagflation; default risk rises.',
        'Deflation Risk': '\u25b2 Flight to quality widens HY spreads; avoid lower-rated credit.',
    },
    'investment_grade_spread': {
        'Goldilocks': '\u2713 IG spreads tight; investment-grade credit well-supported.',
        'Reflation': '\u2500 IG credit stable; inflation risk mostly in lower quality.',
        'Stagflation': '\u25b2 IG spreads widening; even quality credit faces pressure.',
        'Deflation Risk': '\u2713 IG benefits from flight to quality; relative safe haven.',
    },
    'ccc_spread': {
        'Goldilocks': '\u2713 CCC spreads tight; risk appetite elevated in Goldilocks.',
        'Reflation': '\u2500 CCC credit mixed; growth helps, inflation hurts margins.',
        'Stagflation': '\u25b2 CCC spreads widen sharply; highest default risk segment.',
        'Deflation Risk': '\u25b2 Avoid CCC credit in deflation risk; defaults accelerate.',
    },
    'yield_curve_10y2y': {
        'Goldilocks': '\u2713 Steepening curve confirms accelerating growth outlook.',
        'Reflation': '\u2500 Curve shape depends on whether Fed is behind inflation.',
        'Stagflation': '\u25b2 Curve inversion risk as Fed fights inflation into slowdown.',
        'Deflation Risk': '\u25b2 Inversion deepening; growth deceleration confirmed.',
    },
    'yield_curve_10y3m': {
        'Goldilocks': '\u2713 Positive slope confirms expansion; growth leading indicator.',
        'Reflation': '\u2500 Slope depends on short-end rate expectations.',
        'Stagflation': '\u25b2 Inversion likely as Fed tightens into slowdown.',
        'Deflation Risk': '\u25b2 Deep inversion; recession probability elevated.',
    },
    'treasury_10y': {
        'Goldilocks': '\u2500 Yields stable-to-falling as inflation cools; duration rewarded.',
        'Reflation': '\u25b2 Rising yields reflect inflation expectations; duration penalized.',
        'Stagflation': '\u25b2 Yields volatile \u2014 inflation pushes up, growth fears pull down.',
        'Deflation Risk': '\u2713 Yields fall on flight to safety and rate cut expectations.',
    },
    'nfci': {
        'Goldilocks': '\u2713 Loose conditions support Goldilocks; risk assets benefit.',
        'Reflation': '\u2500 Conditions tightening as Fed responds to inflation.',
        'Stagflation': '\u25b2 Tightening conditions amplify stagflation pain.',
        'Deflation Risk': '\u25b2 Tight conditions accelerate growth slowdown.',
    },
    'initial_claims': {
        'Goldilocks': '\u2713 Low claims confirm healthy labor market and growth.',
        'Reflation': '\u2713 Low claims; labor market tight \u2014 inflation pressure.',
        'Stagflation': '\u25b2 Rising claims signal growth deceleration is hitting jobs.',
        'Deflation Risk': '\u25b2 Rising claims confirm growth slowdown is broadening.',
    },
    'continuing_claims': {
        'Goldilocks': '\u2713 Low continuing claims; labor market absorbing workers.',
        'Reflation': '\u2713 Low claims; tight labor market fueling wage inflation.',
        'Stagflation': '\u25b2 Rising continuing claims; re-employment getting harder.',
        'Deflation Risk': '\u25b2 Elevated claims; labor market deterioration underway.',
    },
    'consumer_confidence': {
        'Goldilocks': '\u2713 High confidence supports consumer spending and growth.',
        'Reflation': '\u2500 Confidence mixed; growth helps but inflation erodes sentiment.',
        'Stagflation': '\u25b2 Falling confidence; inflation and job fears compound.',
        'Deflation Risk': '\u25b2 Low confidence; spending pullback likely.',
    },
    'vix': {
        'Goldilocks': '\u2713 Low VIX consistent with Goldilocks calm; complacency risk.',
        'Reflation': '\u2500 VIX normal; markets pricing growth over inflation risk.',
        'Stagflation': '\u25b2 Elevated VIX expected; stagflation uncertainty.',
        'Deflation Risk': '\u25b2 VIX spikes on growth fears; hedging demand elevated.',
    },
    'gold': {
        'Goldilocks': '\u2500 Gold neutral-to-weak in Goldilocks; risk assets preferred.',
        'Reflation': '\u2713 Gold benefits from inflation hedge demand.',
        'Stagflation': '\u2713 Gold outperforms in stagflation \u2014 best quadrant for gold.',
        'Deflation Risk': '\u2500 Gold mixed; uncertainty supports, deflation headwind.',
    },
    'real_yield_10y': {
        'Goldilocks': '\u2500 Real yields stable; no strong directional signal.',
        'Reflation': '\u25b2 Rising real yields constrain gold and growth multiples.',
        'Stagflation': '\u2500 Real yields volatile; depends on inflation vs. growth pricing.',
        'Deflation Risk': '\u2713 Falling real yields support gold and long-duration assets.',
    },
    'breakeven_inflation_10y': {
        'Goldilocks': '\u2713 Breakevens falling confirms inflation deceleration.',
        'Reflation': '\u25b2 Rising breakevens signal accelerating inflation expectations.',
        'Stagflation': '\u25b2 Elevated breakevens confirm sticky inflation despite slowdown.',
        'Deflation Risk': '\u2713 Falling breakevens confirm disinflation / deflation risk.',
    },
    'sp500': {
        'Goldilocks': '\u2713 Equities favored in Goldilocks; best real return quadrant.',
        'Reflation': '\u2713 Equities benefit from growth; real returns moderate.',
        'Stagflation': '\u25b2 Worst quadrant for equity real returns historically.',
        'Deflation Risk': '\u25b2 Growth slowdown weighs on equities; watch policy response.',
    },
    'fed_funds_rate': {
        'Goldilocks': '\u2500 Rate level less important than direction in Goldilocks.',
        'Reflation': '\u25b2 Rate hikes expected as Fed fights rising inflation.',
        'Stagflation': '\u25b2 Fed trapped \u2014 hiking into slowdown historically ends badly.',
        'Deflation Risk': '\u2713 Rate cuts expected or underway; watch pace and market response.',
    },
    'fed_balance_sheet': {
        'Goldilocks': '\u2500 Balance sheet stable; no active QE/QT signal.',
        'Reflation': '\u25b2 QT likely as Fed fights inflation; liquidity withdrawal.',
        'Stagflation': '\u2500 Fed policy uncertain; balance sheet direction a key variable.',
        'Deflation Risk': '\u2713 QE restart likely; liquidity injection supports recovery.',
    },
    'm2_money_supply': {
        'Goldilocks': '\u2713 M2 growth supports Goldilocks conditions.',
        'Reflation': '\u25b2 M2 growth may fuel further inflation.',
        'Stagflation': '\u2500 M2 direction is a key variable in resolving stagflation.',
        'Deflation Risk': '\u25b2 Contracting M2 deepens deflation risk.',
    },
    'dollar_index': {
        'Goldilocks': '\u2500 Dollar range-bound in Goldilocks; risk-on flows mild headwind.',
        'Reflation': '\u2500 Dollar mixed; inflation weakens but rate expectations support.',
        'Stagflation': '\u2500 Dollar direction depends on growth vs. inflation pricing.',
        'Deflation Risk': '\u25b2 Dollar strengthens on safe-haven demand; EM pressure.',
    },
}
