"""
Static configuration for macro regime detection.

Stores regime metadata, plain-language summaries, category context sentences,
signal annotations, and highlighted signal definitions for all four regime states.

All strings are constrained to character limits per design spec:
- Plain-language summaries: max 200 chars
- Category context sentences: max 100 chars per category × regime
- Signal annotations: max 100 chars per signal × regime
"""

# ---------------------------------------------------------------------------
# Regime metadata: icons, colors, summaries
# ---------------------------------------------------------------------------

REGIME_METADATA = {
    'Bull': {
        'icon': 'bi-arrow-up-circle-fill',
        'css_class': 'regime-bull',
        # Summary: max 200 chars
        'summary': (
            'Growth is accelerating and credit markets are calm. '
            'Risk assets are broadly supported. Momentum favors equities and credit.'
        ),
        # Highlighted signals (2-3): signal keys matching CSV filenames / metric keys
        'highlighted_signals': ['sp500', 'high_yield_spread', 'initial_claims'],
    },
    'Neutral': {
        'icon': 'bi-dash-circle-fill',
        'css_class': 'regime-neutral',
        'summary': (
            'Mixed macro signals with no clear directional trend. '
            'Credit and growth indicators are balanced. Selective positioning is warranted.'
        ),
        'highlighted_signals': ['yield_curve_10y2y', 'nfci', 'initial_claims'],
    },
    'Bear': {
        'icon': 'bi-arrow-down-circle-fill',
        'css_class': 'regime-bear',
        'summary': (
            'Growth is decelerating and credit spreads are widening. '
            'Risk assets face headwinds. Watch credit and safe haven signals closely.'
        ),
        'highlighted_signals': ['high_yield_spread', 'vix', 'gold'],
    },
    'Recession Watch': {
        'icon': 'bi-exclamation-circle-fill',
        'css_class': 'regime-recession',
        'summary': (
            'Contraction indicators are active. Credit stress is elevated '
            'and labor markets are weakening. Defensive positioning is prudent.'
        ),
        'highlighted_signals': ['high_yield_spread', 'yield_curve_10y2y', 'initial_claims'],
    },
}

# ---------------------------------------------------------------------------
# Category context sentences for the compact regime strip on detail pages.
# 6 categories × 4 regimes = 24 strings. Max 100 chars each.
# ---------------------------------------------------------------------------

CATEGORY_REGIME_CONTEXT = {
    'Credit': {
        'Bull': 'Spreads are tight; credit is a carry trade in this regime.',
        'Neutral': 'Spreads near historic median; selective credit is viable.',
        'Bear': 'Spreads widening; credit stress is building here.',
        'Recession Watch': 'Spreads at distress levels; avoid lower-rated credit.',
    },
    'Rates': {
        'Bull': 'Curve steepening; duration risk is elevated.',
        'Neutral': 'Curve mixed; duration calls depend on inflation data.',
        'Bear': 'Yield curve inversions carry higher recession predictive weight.',
        'Recession Watch': 'Front-end rates may fall; long-duration bonds attract safety bids.',
    },
    'Equities': {
        'Bull': 'Breadth and momentum favor equities broadly.',
        'Neutral': 'Rotation between sectors; earnings quality matters most.',
        'Bear': 'Multiple compression underway; focus on earnings resilience.',
        'Recession Watch': 'Defensive sectors outperform; avoid cyclicals and small caps.',
    },
    'Dollar': {
        'Bull': 'Risk-on flows weaken the dollar; EM assets benefit.',
        'Neutral': 'Dollar range-bound; watch Fed signals for direction.',
        'Bear': 'Dollar may strengthen as a haven; watch carry unwinds.',
        'Recession Watch': 'Safe-haven dollar demand typically spikes in contraction.',
    },
    'Crypto': {
        'Bull': 'Risk-on regime supports crypto; beta to equities is high.',
        'Neutral': 'Crypto follows equities; no regime-specific edge here.',
        'Bear': 'Liquidity tightens; crypto faces outsized drawdown risk.',
        'Recession Watch': 'Crypto is a high-risk asset; severe drawdowns are likely.',
    },
    'Safe Havens': {
        'Bull': 'Gold and bonds underperform as risk appetite dominates.',
        'Neutral': 'Safe havens are range-bound; hedge selectively.',
        'Bear': 'Gold and long-duration bonds outperform; hedge here.',
        'Recession Watch': 'Safe havens are primary defense; overweight gold and Treasuries.',
    },
}

# ---------------------------------------------------------------------------
# Signal regime annotations: brief text shown on expanded metric cards.
# Max 100 chars each.
# ---------------------------------------------------------------------------

SIGNAL_REGIME_ANNOTATIONS = {
    'high_yield_spread': {
        'Bull': '▲ Tight spreads confirm risk-on sentiment.',
        'Neutral': '─ Spreads near median; no strong credit signal.',
        'Bear': '▲ Widening spreads signal rising default risk.',
        'Recession Watch': '▲ Distress-level spreads; credit crisis risk is elevated.',
    },
    'investment_grade_spread': {
        'Bull': '✓ IG spreads tight; investment-grade credit supported.',
        'Neutral': '─ IG spreads near median; carry trade viable.',
        'Bear': '▲ IG spreads widening; quality credit under pressure.',
        'Recession Watch': '▲ IG spreads at stress levels; quality flight underway.',
    },
    'ccc_spread': {
        'Bull': '✓ CCC spreads tight; risk appetite is elevated.',
        'Neutral': '─ CCC spreads near median; selective risk taking.',
        'Bear': '▲ CCC spreads widening; high default risk ahead.',
        'Recession Watch': '▲ CCC spreads at extreme levels; avoid distressed credit.',
    },
    'yield_curve_10y2y': {
        'Bull': '▲ Steepening curve supports growth outlook.',
        'Neutral': '─ Flat curve; mixed growth vs inflation signals.',
        'Bear': '▲ Inversion deepening; recession risk rising.',
        'Recession Watch': '▲ Deeply inverted; contraction historically follows.',
    },
    'yield_curve_10y3m': {
        'Bull': '✓ Positive slope confirms expansion continues.',
        'Neutral': '─ Slope near flat; watch for inversion.',
        'Bear': '▲ Inversion signals growth concerns ahead.',
        'Recession Watch': '▲ Deep inversion; historically high recession probability.',
    },
    'treasury_10y': {
        'Bull': '▲ Rising yields reflect strong growth expectations.',
        'Neutral': '─ Yields stable; inflation and growth in balance.',
        'Bear': '▲ Rising yields here signal growth concerns, not inflation.',
        'Recession Watch': '✓ Falling yields reflect flight to safety and rate cut bets.',
    },
    'nfci': {
        'Bull': '✓ Loose financial conditions fuel risk asset demand.',
        'Neutral': '─ Financial conditions near neutral; no directional edge.',
        'Bear': '▲ Tightening conditions restrict credit and growth.',
        'Recession Watch': '▲ Severely tight; systemic risk is elevated.',
    },
    'initial_claims': {
        'Bull': '✓ Low claims confirm healthy labor market.',
        'Neutral': '─ Claims near trend; labor market stable.',
        'Bear': '▲ Rising claims signal labor market softening.',
        'Recession Watch': '▲ Spiking claims; labor market contraction underway.',
    },
    'continuing_claims': {
        'Bull': '✓ Low continuing claims; job-finders market persists.',
        'Neutral': '─ Continuing claims stable; no labor market alarm.',
        'Bear': '▲ Continuing claims rising; re-employment harder.',
        'Recession Watch': '▲ Elevated continuing claims; broad job losses underway.',
    },
    'consumer_confidence': {
        'Bull': '✓ High consumer confidence supports spending growth.',
        'Neutral': '─ Consumer confidence near historic median.',
        'Bear': '▲ Fading confidence signals spending pullback ahead.',
        'Recession Watch': '▲ Low confidence; demand destruction risk is high.',
    },
    'vix': {
        'Bull': '✓ Low VIX reflects market complacency.',
        'Neutral': '─ VIX in normal range; no elevated fear.',
        'Bear': '▲ Elevated VIX signals investor anxiety.',
        'Recession Watch': '▲ Extreme VIX; capitulation conditions possible.',
    },
    'gold': {
        'Bull': '─ Gold underperforms in risk-on regimes.',
        'Neutral': '─ Gold range-bound without a clear regime catalyst.',
        'Bear': '✓ Gold outperforms as a defensive hedge here.',
        'Recession Watch': '✓ Gold confirming flight-to-safety demand.',
    },
    'real_yield_10y': {
        'Bull': '▲ Rising real yields constrain gold and credit multiples.',
        'Neutral': '─ Real yields near neutral; balanced macro backdrop.',
        'Bear': '✓ Falling real yields support gold and duration.',
        'Recession Watch': '✓ Deeply negative real yields favor gold and long bonds.',
    },
    'breakeven_inflation_10y': {
        'Bull': '▲ Rising breakevens reflect growth-driven inflation expectations.',
        'Neutral': '─ Breakevens anchored near Fed target.',
        'Bear': '─ Breakevens falling; disinflation risk building.',
        'Recession Watch': '─ Breakevens collapsing; deflation risk elevated.',
    },
    'sp500': {
        'Bull': '✓ Equities in uptrend; momentum is your friend.',
        'Neutral': '─ Equities range-bound; sector rotation active.',
        'Bear': '▲ Equities correcting; downside risk elevated.',
        'Recession Watch': '▲ Deep drawdowns possible; preserve capital.',
    },
    'fed_funds_rate': {
        'Bull': '▲ Accommodative rate supports risk appetite.',
        'Neutral': '─ Rates near neutral; Fed in wait-and-see mode.',
        'Bear': '▲ Restrictive rate weighs on growth and credit.',
        'Recession Watch': '✓ Rate cuts incoming or underway; watch pace.',
    },
    'fed_balance_sheet': {
        'Bull': '✓ Expanding balance sheet adds liquidity to markets.',
        'Neutral': '─ Balance sheet stable; QE/QT roughly balanced.',
        'Bear': '▲ Shrinking balance sheet removes market liquidity.',
        'Recession Watch': '✓ Expect QE restart; liquidity injection likely.',
    },
    'm2_money_supply': {
        'Bull': '✓ Expanding M2 supports asset prices and growth.',
        'Neutral': '─ M2 growth near trend; liquidity conditions normal.',
        'Bear': '▲ Slowing M2 growth signals tightening liquidity.',
        'Recession Watch': '▲ Contracting M2 historically precedes deep recessions.',
    },
    'dollar_index': {
        'Bull': '─ Weak dollar supports EM and commodities.',
        'Neutral': '─ Dollar near fair value; no regime-driven signal.',
        'Bear': '▲ Strengthening dollar tightens global financial conditions.',
        'Recession Watch': '▲ Dollar safe-haven bid; EM assets face pressure.',
    },
}

# ---------------------------------------------------------------------------
# Category regime relevance: which categories are elevated in each regime.
# Only categories in this list get the regime-relevance dot on badge-cards.
# ---------------------------------------------------------------------------

REGIME_CATEGORY_RELEVANCE = {
    'Bull': ['Equities', 'Credit'],
    'Neutral': ['Rates', 'Equities'],
    'Bear': ['Credit', 'Rates', 'Safe Havens'],
    'Recession Watch': ['Credit', 'Rates', 'Safe Havens', 'Equities'],
}

# ---------------------------------------------------------------------------
# FRED series used for regime classification
# These must match the series IDs in market_signals.py
# ---------------------------------------------------------------------------

REGIME_CLASSIFICATION_FEATURES = {
    # Key: local CSV filename stem / metric key
    # Value: FRED series ID
    'high_yield_spread': 'BAMLH0A0HYM2',
    'yield_curve_10y2y': 'T10Y2Y',
    'nfci': 'NFCI',
    'initial_claims': 'ICSA',
    'fed_funds_rate': 'FEDFUNDS',
}

# Valid regime state names
VALID_REGIMES = ('Bull', 'Neutral', 'Bear', 'Recession Watch')

# Confidence thresholds (as fraction of median intra-cluster distance)
# Below LOW_THRESHOLD: High confidence; above HIGH_THRESHOLD: Low confidence
CONFIDENCE_LOW_THRESHOLD = 0.5
CONFIDENCE_HIGH_THRESHOLD = 1.5
