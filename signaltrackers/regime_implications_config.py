"""
Static configuration for the Regime Implications Panel (Feature 6.1 / US-145.1).

Historical asset class performance patterns across all 4 macro regime phases.
4 regimes × 6 asset classes.

Data sourced from published academic and institutional research:
- FRED-MD academic paper (Bok, Caratelli, Giannone, et al., 1960–2025)
- CFA Institute "Mind the Cycle" (November 2025)
- Fidelity Business Cycle Update methodology

No internal backtesting performed. All signals reflect historical pattern
averages and do not guarantee future performance.
"""

# ---------------------------------------------------------------------------
# Valid signal level strings (5-level scale)
# ---------------------------------------------------------------------------

VALID_SIGNALS = (
    'strong_outperform',
    'outperform',
    'neutral',
    'underperform',
    'strong_underperform',
)

# ---------------------------------------------------------------------------
# Mapping from regime engine state strings → data model keys
# Regime engine returns: 'Bull', 'Neutral', 'Bear', 'Recession Watch'
# Data model uses:       'bull', 'neutral', 'bear', 'recession_watch'
# ---------------------------------------------------------------------------

REGIME_STATE_TO_KEY = {
    'Bull': 'bull',
    'Neutral': 'neutral',
    'Bear': 'bear',
    'Recession Watch': 'recession_watch',
}

# ---------------------------------------------------------------------------
# Historical pattern data — 4 regimes × 6 asset classes
# ---------------------------------------------------------------------------

REGIME_IMPLICATIONS = {
    'bull': {
        'display_name': 'Bull Market',
        'asset_classes': [
            {
                'key': 'equities',
                'display_name': 'Equities',
                'signal': 'strong_outperform',
                'annotation': (
                    'Cyclicals and growth sectors historically lead in bull phases. '
                    'Broad market gains as earnings and economic activity expand.'
                ),
                'leading_sectors': ['Technology', 'Financials', 'Consumer Discretionary'],
                'lagging_sectors': ['Utilities', 'Consumer Staples'],
            },
            {
                'key': 'credit',
                'display_name': 'Credit',
                'signal': 'outperform',
                'annotation': (
                    'HY spreads tighten as economic conditions improve; '
                    'investment-grade in line with equities.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'rates',
                'display_name': 'Rates',
                'signal': 'underperform',
                'annotation': (
                    'Rising yields compress long-duration bond prices '
                    'in expanding economic conditions.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'safe_havens',
                'display_name': 'Safe Havens',
                'signal': 'strong_underperform',
                'annotation': (
                    'Gold and long-duration Treasuries trail as '
                    'risk-on assets dominate.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'crypto',
                'display_name': 'Crypto',
                'signal': 'outperform',
                'annotation': (
                    'Risk appetite supports crypto alongside equities in bull conditions. '
                    'Pattern based on 2010\u20132025 data.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'dollar',
                'display_name': 'Dollar',
                'signal': 'neutral',
                'annotation': (
                    'USD shows mixed behavior in bull markets; direction reflects US vs. global growth '
                    'differentials more than risk-on sentiment. Post-Bretton Woods data (1971\u20132025).'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
        ],
    },
    'neutral': {
        'display_name': 'Neutral',
        'asset_classes': [
            {
                'key': 'equities',
                'display_name': 'Equities',
                'signal': 'outperform',
                'annotation': (
                    'Returns moderate; sector leadership rotates toward quality and value '
                    'as the cycle matures.'
                ),
                'leading_sectors': ['Industrials', 'Technology', 'Healthcare'],
                'lagging_sectors': ['Energy', 'Materials'],
            },
            {
                'key': 'credit',
                'display_name': 'Credit',
                'signal': 'outperform',
                'annotation': (
                    'Investment-grade in line with equities; HY spreads stable '
                    'and carry-driven returns dominate.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'rates',
                'display_name': 'Rates',
                'signal': 'neutral',
                'annotation': (
                    'Yield curve flat; interest rate sensitivity modest. '
                    'Duration neutral or slightly short is favored.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'safe_havens',
                'display_name': 'Safe Havens',
                'signal': 'neutral',
                'annotation': (
                    'Gold demand limited; safe haven flows muted. '
                    'Preserves capital but offers little return alpha.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'crypto',
                'display_name': 'Crypto',
                'signal': 'neutral',
                'annotation': (
                    'Correlation with equities moderates; limited directional bias. '
                    'Pattern based on 2010\u20132025 data.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'dollar',
                'display_name': 'Dollar',
                'signal': 'neutral',
                'annotation': (
                    'No strong directional bias; dollar tracks Fed policy stance and global growth '
                    'differentials. Post-Bretton Woods data (1971\u20132025).'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
        ],
    },
    'bear': {
        'display_name': 'Bear Market',
        'asset_classes': [
            {
                'key': 'equities',
                'display_name': 'Equities',
                'signal': 'strong_underperform',
                'annotation': (
                    'Broad market declines as earnings expectations reset. '
                    'Defensive sectors offer relative protection.'
                ),
                'leading_sectors': ['Consumer Staples', 'Utilities', 'Healthcare'],
                'lagging_sectors': ['Technology', 'Consumer Discretionary', 'Financials'],
            },
            {
                'key': 'credit',
                'display_name': 'Credit',
                'signal': 'underperform',
                'annotation': (
                    'HY spreads widen sharply on rising default risk. '
                    'Duration risk elevated; quality migration accelerates.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'rates',
                'display_name': 'Rates',
                'signal': 'outperform',
                'annotation': (
                    'Flight-to-quality demand lifts long-duration Treasuries. '
                    'Yields fall as growth concerns mount.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'safe_havens',
                'display_name': 'Safe Havens',
                'signal': 'outperform',
                'annotation': (
                    'Gold and long-duration Treasuries provide capital preservation '
                    'as risk assets sell off.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'crypto',
                'display_name': 'Crypto',
                'signal': 'strong_underperform',
                'annotation': (
                    'High beta to equities; crypto sells off sharply in risk-off conditions. '
                    'Pattern based on 2010\u20132025 data.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'dollar',
                'display_name': 'Dollar',
                'signal': 'outperform',
                'annotation': (
                    'Flight-to-safety demand supports USD as risk assets sell off; DXY historically '
                    'strengthens in risk-off environments. Post-Bretton Woods data (1971\u20132025).'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
        ],
    },
    'recession_watch': {
        'display_name': 'Recession Watch',
        'asset_classes': [
            {
                'key': 'equities',
                'display_name': 'Equities',
                'signal': 'strong_underperform',
                'annotation': (
                    'Deep equity declines with broad sector losses. '
                    'Defensives least affected; cyclicals hit hardest.'
                ),
                'leading_sectors': ['Consumer Staples', 'Utilities'],
                'lagging_sectors': ['Financials', 'Industrials', 'Consumer Discretionary'],
            },
            {
                'key': 'credit',
                'display_name': 'Credit',
                'signal': 'strong_underperform',
                'annotation': (
                    'HY spreads blow out as default risk peaks. '
                    'Investment-grade spreads also widen; credit contraction weighs on growth.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'rates',
                'display_name': 'Rates',
                'signal': 'strong_outperform',
                'annotation': (
                    'Fed eases aggressively; long-duration Treasuries surge. '
                    'Rate-cut cycle historically delivers strongest fixed income returns.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'safe_havens',
                'display_name': 'Safe Havens',
                'signal': 'strong_outperform',
                'annotation': (
                    'Gold and Treasuries peak; maximum safe haven demand. '
                    'Both assets historically deliver during contraction phases.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'crypto',
                'display_name': 'Crypto',
                'signal': 'underperform',
                'annotation': (
                    'Risk-off sentiment weighs on crypto; correlates closely with equities. '
                    'Pattern based on 2010\u20132025 data.'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
            {
                'key': 'dollar',
                'display_name': 'Dollar',
                'signal': 'strong_outperform',
                'annotation': (
                    'Peak flight-to-USD demand as global safe haven; reserve currency premium '
                    'strengthens even as Fed eases. Post-Bretton Woods data (1971\u20132025).'
                ),
                'leading_sectors': None,
                'lagging_sectors': None,
            },
        ],
    },
}
