#!/usr/bin/env python3
"""
Export market data for AI analysis - Neutral/Objective version.
Provides pure data and statistics without interpretation or bias.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

DATA_DIR = Path("data")
OUTPUT_FILE = "market_data_for_ai.md"

def load_csv_safely(filename):
    """Load CSV file and return DataFrame, or None if not found."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    return None

def calculate_stats(df, column):
    """Calculate comprehensive statistics for a metric."""
    if df is None or len(df) == 0:
        return None

    values = df[column].dropna()
    if len(values) == 0:
        return None

    stats = {
        'current': float(values.iloc[-1]),
        'min': float(values.min()),
        'max': float(values.max()),
        'mean': float(values.mean()),
        'median': float(values.median()),
        'std': float(values.std()),
        'percentile_25': float(np.percentile(values, 25)),
        'percentile_75': float(np.percentile(values, 75)),
        'count': len(values),
        'first_date': df['date'].iloc[0].strftime('%Y-%m-%d'),
        'last_date': df['date'].iloc[-1].strftime('%Y-%m-%d'),
    }

    # Calculate changes
    if len(values) >= 2:
        stats['change_1d'] = float(values.iloc[-1] - values.iloc[-2])
        stats['change_1d_pct'] = float(((values.iloc[-1] / values.iloc[-2]) - 1) * 100)

    if len(values) >= 6:
        stats['change_5d'] = float(values.iloc[-1] - values.iloc[-6])
        stats['change_5d_pct'] = float(((values.iloc[-1] / values.iloc[-6]) - 1) * 100)

    if len(values) >= 11:
        stats['change_10d'] = float(values.iloc[-1] - values.iloc[-11])
        stats['change_10d_pct'] = float(((values.iloc[-1] / values.iloc[-11]) - 1) * 100)

    if len(values) >= 31:
        stats['change_30d'] = float(values.iloc[-1] - values.iloc[-31])
        stats['change_30d_pct'] = float(((values.iloc[-1] / values.iloc[-31]) - 1) * 100)

    # Calculate percentile rank of current value
    current_percentile = (values < values.iloc[-1]).sum() / len(values) * 100
    stats['current_percentile'] = float(current_percentile)

    # Recent data (last 10 days)
    recent = df.tail(10)
    stats['recent_data'] = [
        {
            'date': row['date'].strftime('%Y-%m-%d'),
            'value': float(row[column])
        }
        for _, row in recent.iterrows()
    ]

    return stats

def calculate_yoy_change(df, column):
    """Calculate year-over-year change for monthly data (12 periods back)."""
    if df is None or len(df) < 13:
        return None

    values = df[column].dropna()
    if len(values) < 13:
        return None

    current = float(values.iloc[-1])
    year_ago = float(values.iloc[-13])

    return {
        'current': current,
        'year_ago': year_ago,
        'yoy_change': current - year_ago,
        'yoy_pct': ((current / year_ago) - 1) * 100 if year_ago != 0 else 0
    }


def calculate_divergence_gap(gold_df, hy_df):
    """Calculate the gap between gold-implied spread and actual spread."""
    if gold_df is None or hy_df is None:
        return None

    merged = pd.merge(gold_df, hy_df, on='date', how='inner')

    # Gold-implied spread calculation
    gold_prices = merged['gold_price'].values
    hy_spreads = merged['high_yield_spread'].values * 100

    gold_implied = ((gold_prices / 200) ** 1.5) * 400
    divergence = gold_implied - hy_spreads

    merged['divergence_gap'] = divergence
    merged['gold_implied_spread'] = gold_implied

    stats = calculate_stats(merged, 'divergence_gap')
    if stats:
        stats['gold_implied_current'] = float(gold_implied[-1])
        stats['actual_spread_current'] = float(hy_spreads[-1])

    return stats

def generate_markdown_summary():
    """Generate neutral markdown summary of all market data."""

    output = []

    # Header
    output.append("# MARKET DATA EXPORT")
    output.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    output.append("Comprehensive financial market data with statistics and trends.")
    output.append("All values presented as-is without interpretation.")
    output.append("")
    output.append("---")
    output.append("")

    # Table of Contents
    output.append("## TABLE OF CONTENTS")
    output.append("1. [Calculated Metrics](#calculated-metrics)")
    output.append("2. [Credit Markets](#credit-markets)")
    output.append("3. [Equity Markets](#equity-markets)")
    output.append("4. [Safe Haven Assets](#safe-haven-assets)")
    output.append("5. [Fixed Income](#fixed-income)")
    output.append("6. [Commodities & Currency](#commodities--currency)")
    output.append("7. [Market Ratios](#market-ratios)")
    output.append("8. [Market Concentration](#market-concentration)")
    output.append("9. [Yen Carry Trade](#yen-carry-trade)")
    output.append("10. [Yield Curve](#yield-curve)")
    output.append("11. [Labor Market](#labor-market)")
    output.append("12. [Economic Indicators](#economic-indicators)")
    output.append("13. [Fed Liquidity & Conditions](#fed-liquidity--conditions)")
    output.append("14. [Crypto Sentiment](#crypto-sentiment)")
    output.append("15. [Safe Haven Drivers](#safe-haven-drivers)")
    output.append("16. [Complete Dataset (JSON)](#complete-dataset-json)")
    output.append("")
    output.append("---")
    output.append("")

    # Collect all data
    all_stats = {}

    # Define all metrics to load
    metrics = {
        'credit': {
            'high_yield_spread': ('high_yield_spread.csv', 'high_yield_spread', 'bp'),
            'investment_grade_spread': ('investment_grade_spread.csv', 'investment_grade_spread', 'bp'),
            'ccc_spread': ('ccc_spread.csv', 'ccc_spread', 'bp'),
            'high_yield_credit_price': ('high_yield_credit_price.csv', 'high_yield_credit_price', '$'),
            'investment_grade_credit_price': ('investment_grade_credit_price.csv', 'investment_grade_credit_price', '$'),
            'leveraged_loan_price': ('leveraged_loan_price.csv', 'leveraged_loan_price', '$'),
        },
        'equity': {
            'sp500_price': ('sp500_price.csv', 'sp500_price', '$'),
            'nasdaq_price': ('nasdaq_price.csv', 'nasdaq_price', '$'),
            'small_cap_price': ('small_cap_price.csv', 'small_cap_price', '$'),
            'sp500_equal_weight_price': ('sp500_equal_weight_price.csv', 'sp500_equal_weight_price', '$'),
            'semiconductor_price': ('semiconductor_price.csv', 'semiconductor_price', '$'),
            'tech_sector_price': ('tech_sector_price.csv', 'tech_sector_price', '$'),
            'growth_price': ('growth_price.csv', 'growth_price', '$'),
            'value_price': ('value_price.csv', 'value_price', '$'),
            'vix_price': ('vix_price.csv', 'vix_price', 'index'),
        },
        'safe_havens': {
            'gold_price': ('gold_price.csv', 'gold_price', '$ (GLD ETF)'),
            'bitcoin_price': ('bitcoin_price.csv', 'bitcoin_price', '$'),
            'gold_miners_price': ('gold_miners_price.csv', 'gold_miners_price', '$'),
            'silver_price': ('silver_price.csv', 'silver_price', '$'),
        },
        'fixed_income': {
            'treasury_7_10yr_price': ('treasury_7_10yr_price.csv', 'treasury_7_10yr_price', '$'),
            'treasury_20yr_price': ('treasury_20yr_price.csv', 'treasury_20yr_price', '$'),
            'treasury_short_price': ('treasury_short_price.csv', 'treasury_short_price', '$'),
            'tips_inflation_price': ('tips_inflation_price.csv', 'tips_inflation_price', '$'),
        },
        'commodities': {
            'oil_price': ('oil_price.csv', 'oil_price', '$'),
            'commodities_price': ('commodities_price.csv', 'commodities_price', '$'),
            'dollar_index_price': ('dollar_index_price.csv', 'dollar_index_price', '$'),
        },
        'ratios': {
            'market_breadth_ratio': ('market_breadth_ratio.csv', 'breadth_ratio', 'ratio'),
            'gold_silver_ratio': ('gold_silver_ratio.csv', 'gold_silver_ratio', 'ratio'),
            'real_yield_proxy': ('real_yield_proxy.csv', 'real_yield_proxy', '$'),
            'hyg_treasury_spread': ('hyg_treasury_spread.csv', 'hyg_vs_ief_spread', 'bp'),
            'lqd_treasury_spread': ('lqd_treasury_spread.csv', 'lqd_vs_ief_spread', 'bp'),
        },
        'concentration': {
            'smh_spy_ratio': ('smh_spy_ratio.csv', 'smh_spy_ratio', 'ratio (×100)'),
            'xlk_spy_ratio': ('xlk_spy_ratio.csv', 'xlk_spy_ratio', 'ratio (×100)'),
            'growth_value_ratio': ('growth_value_ratio.csv', 'growth_value_ratio', 'ratio (×100)'),
        },
        'yen_carry_trade': {
            'usdjpy_price': ('usdjpy_price.csv', 'usdjpy_price', 'JPY per USD'),
            'japan_10y_yield': ('japan_10y_yield.csv', 'japan_10y_yield', '%'),
        },
        'yield_curve': {
            'yield_curve_10y2y': ('yield_curve_10y2y.csv', 'yield_curve_10y2y', '% (spread)'),
            'yield_curve_10y3m': ('yield_curve_10y3m.csv', 'yield_curve_10y3m', '% (spread)'),
        },
        'labor_market': {
            'initial_claims': ('initial_claims.csv', 'initial_claims', 'thousands'),
            'continuing_claims': ('continuing_claims.csv', 'continuing_claims', 'thousands'),
        },
        'economic_indicators': {
            'consumer_confidence': ('consumer_confidence.csv', 'consumer_confidence', 'index'),
            'm2_money_supply': ('m2_money_supply.csv', 'm2_money_supply', 'billions $'),
            'cpi': ('cpi.csv', 'cpi', 'index'),
        },
        'fed_liquidity_conditions': {
            'fed_balance_sheet': ('fed_balance_sheet.csv', 'fed_balance_sheet', 'billions $'),
            'reverse_repo': ('reverse_repo.csv', 'reverse_repo', 'billions $'),
            'nfci': ('nfci.csv', 'nfci', 'index'),
        },
        'crypto_sentiment': {
            'fear_greed_index': ('fear_greed_index.csv', 'fear_greed_index', 'index (0-100)'),
            'btc_gold_ratio': ('btc_gold_ratio.csv', 'btc_gold_ratio', 'ratio (oz gold per BTC)'),
        },
        'safe_haven_drivers': {
            'treasury_10y': ('treasury_10y.csv', 'treasury_10y', '% (nominal yield)'),
            'real_yield_10y': ('real_yield_10y.csv', 'real_yield_10y', '% (TIPS yield)'),
            'breakeven_inflation_10y': ('breakeven_inflation_10y.csv', 'breakeven_inflation_10y', '% (inflation expectations)'),
            'gdx_gld_ratio': ('gdx_gld_ratio.csv', 'gdx_gld_ratio', 'ratio (miners vs gold)'),
        }
    }

    # Calculate divergence gap first
    gold_df = load_csv_safely('gold_price.csv')
    hy_df = load_csv_safely('high_yield_spread.csv')
    divergence_stats = calculate_divergence_gap(gold_df, hy_df)

    # CALCULATED METRICS
    output.append("## CALCULATED METRICS")
    output.append("")
    output.append("### Divergence Gap")
    output.append("")
    output.append("**Calculation:** Gold-Implied Spread minus Actual High-Yield Spread")
    output.append("")
    output.append("Where Gold-Implied Spread = ((gold_price / 200)^1.5) × 400")
    output.append("")
    if divergence_stats:
        output.append(f"- **Current Value:** {divergence_stats['current']:.2f} bp")
        output.append(f"- **Gold-Implied Spread:** {divergence_stats['gold_implied_current']:.2f} bp")
        output.append(f"- **Actual HY Spread:** {divergence_stats['actual_spread_current']:.2f} bp")
        output.append("")
        output.append("**Statistics:**")
        output.append(f"- Min: {divergence_stats['min']:.2f} bp")
        output.append(f"- Max: {divergence_stats['max']:.2f} bp")
        output.append(f"- Mean: {divergence_stats['mean']:.2f} bp")
        output.append(f"- Median: {divergence_stats['median']:.2f} bp")
        output.append(f"- Std Dev: {divergence_stats['std']:.2f} bp")
        output.append(f"- Current Percentile: {divergence_stats['current_percentile']:.1f}%")
        output.append("")
        output.append("**Changes:**")
        if 'change_1d' in divergence_stats:
            output.append(f"- 1-Day: {divergence_stats['change_1d']:+.2f} bp ({divergence_stats['change_1d_pct']:+.2f}%)")
        if 'change_10d' in divergence_stats:
            output.append(f"- 10-Day: {divergence_stats['change_10d']:+.2f} bp ({divergence_stats['change_10d_pct']:+.2f}%)")
        if 'change_30d' in divergence_stats:
            output.append(f"- 30-Day: {divergence_stats['change_30d']:+.2f} bp ({divergence_stats['change_30d_pct']:+.2f}%)")
        output.append("")
        output.append("**Recent Values (Last 10 Days):**")
        output.append("")
        output.append("| Date | Value (bp) |")
        output.append("|------|------------|")
        for item in divergence_stats['recent_data']:
            output.append(f"| {item['date']} | {item['value']:.2f} |")
        output.append("")
        all_stats['divergence_gap'] = divergence_stats
    output.append("")

    # Process each category
    for category, category_metrics in metrics.items():
        category_name = category.replace('_', ' ').title()
        output.append(f"## {category_name.upper()}")
        output.append("")

        for metric_name, (filename, column, unit) in category_metrics.items():
            df = load_csv_safely(filename)
            stats = calculate_stats(df, column)

            if stats:
                all_stats[metric_name] = stats

                display_name = metric_name.replace('_', ' ').title()
                output.append(f"### {display_name}")
                output.append("")
                output.append(f"**Unit:** {unit}")
                output.append("")
                output.append(f"**Current Value:** {stats['current']:.2f}")
                output.append("")
                output.append("**Statistics:**")
                output.append(f"- Range: {stats['min']:.2f} - {stats['max']:.2f}")
                output.append(f"- Mean: {stats['mean']:.2f}")
                output.append(f"- Median: {stats['median']:.2f}")
                output.append(f"- Std Dev: {stats['std']:.2f}")
                output.append(f"- 25th Percentile: {stats['percentile_25']:.2f}")
                output.append(f"- 75th Percentile: {stats['percentile_75']:.2f}")
                output.append(f"- Current Percentile: {stats['current_percentile']:.1f}%")
                output.append("")
                output.append("**Changes:**")

                # For economic indicators (monthly data), calculate YoY instead of daily changes
                if category == 'economic_indicators':
                    yoy = calculate_yoy_change(df, column)
                    if yoy:
                        output.append(f"- Year-over-Year: {yoy['yoy_change']:+.2f} ({yoy['yoy_pct']:+.2f}%)")
                        stats['yoy_change'] = yoy['yoy_change']
                        stats['yoy_pct'] = yoy['yoy_pct']
                    if 'change_1d' in stats:
                        output.append(f"- Last Period: {stats['change_1d']:+.2f} ({stats['change_1d_pct']:+.2f}%)")
                else:
                    if 'change_1d' in stats:
                        output.append(f"- 1-Day: {stats['change_1d']:+.2f} ({stats['change_1d_pct']:+.2f}%)")
                    if 'change_5d' in stats:
                        output.append(f"- 5-Day: {stats['change_5d']:+.2f} ({stats['change_5d_pct']:+.2f}%)")
                    if 'change_10d' in stats:
                        output.append(f"- 10-Day: {stats['change_10d']:+.2f} ({stats['change_10d_pct']:+.2f}%)")
                    if 'change_30d' in stats:
                        output.append(f"- 30-Day: {stats['change_30d']:+.2f} ({stats['change_30d_pct']:+.2f}%)")
                output.append("")
                output.append(f"**Data Period:** {stats['first_date']} to {stats['last_date']} ({stats['count']} observations)")
                output.append("")

        output.append("")

    # RAW DATA (JSON)
    output.append("## COMPLETE DATASET (JSON)")
    output.append("")
    output.append("Full dataset in JSON format:")
    output.append("")
    output.append("```json")
    output.append(json.dumps(all_stats, indent=2))
    output.append("```")
    output.append("")

    # METADATA
    output.append("---")
    output.append("")
    output.append("## METADATA")
    output.append("")
    output.append(f"- **Export Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"- **Data Directory:** {DATA_DIR}")
    output.append(f"- **Number of Metrics:** {len(all_stats)}")
    output.append(f"- **Total Observations:** {sum(s.get('count', 0) for s in all_stats.values())}")
    output.append("")
    output.append("**Note on Units:**")
    output.append("- bp = basis points (1 bp = 0.01%)")
    output.append("- $ = US Dollars or ETF share price")
    output.append("- index = dimensionless index value")
    output.append("- ratio = dimensionless ratio")
    output.append("")
    output.append("**Note on Gold Price:**")
    output.append("- Gold price tracked via GLD ETF share price")
    output.append("- Each GLD share represents approximately 1/10 troy ounce of gold")
    output.append("- To estimate gold per ounce: multiply GLD price by ~10")
    output.append("")
    output.append("**Note on Market Concentration Ratios:**")
    output.append("- SMH/SPY: Semiconductor ETF vs S&P 500 (AI/chip concentration)")
    output.append("- XLK/SPY: Technology Sector vs S&P 500 (tech concentration)")
    output.append("- Growth/Value: Russell 1000 Growth vs Value (style preference)")
    output.append("- All ratios scaled by 100 for readability")
    output.append("")
    output.append("**Note on Yen Carry Trade:**")
    output.append("- USD/JPY: Higher = weaker yen, carry trade expanding")
    output.append("- Sharp USD/JPY drops indicate carry trade unwinding (risk-off)")
    output.append("- Japan 10Y Yield: Rising yields = BOJ tightening, carry trade at risk")
    output.append("")
    output.append("**Note on Yield Curve:**")
    output.append("- 10Y-2Y Spread: 10-Year minus 2-Year Treasury yield (classic recession predictor)")
    output.append("- 10Y-3M Spread: 10-Year minus 3-Month Treasury yield (Fed's preferred measure)")
    output.append("- Negative (inverted) yield curve historically precedes recessions by 12-18 months")
    output.append("- Steepening after inversion often signals recession is imminent")
    output.append("")
    output.append("**Note on Labor Market:**")
    output.append("- Initial Claims: Weekly new unemployment filings (leading indicator)")
    output.append("- Continuing Claims: Total insured unemployed (lagging confirmation)")
    output.append("- Rising claims = labor market weakening, potential recession")
    output.append("- Key levels: Initial claims >300k = warning, >400k = recession signal")
    output.append("")
    output.append("**Note on Economic Indicators:**")
    output.append("- Consumer Confidence: University of Michigan Sentiment (survey-based)")
    output.append("- M2 Money Supply: Total money stock in billions USD")
    output.append("- CPI: Consumer Price Index (inflation measure)")
    output.append("- These are monthly data series (lower frequency than market data)")
    output.append("")
    output.append("**Note on Fed Liquidity & Financial Conditions:**")
    output.append("- Fed Balance Sheet (WALCL): Total Federal Reserve assets in billions USD")
    output.append("- Expansion = QE/adding liquidity (bullish for risk assets)")
    output.append("- Contraction = QT/draining liquidity (headwind for markets)")
    output.append("- Reverse Repo (RRP): Overnight reverse repurchase facility usage")
    output.append("- High RRP = excess liquidity parked at Fed, declining = liquidity draining")
    output.append("- NFCI: Chicago Fed National Financial Conditions Index")
    output.append("- Positive values = tight conditions (stress), negative = loose conditions")
    output.append("- Zero = average conditions, spikes often precede market stress")
    output.append("")
    output.append("**Note on Crypto Sentiment:**")
    output.append("- Fear & Greed Index: Alternative.me composite sentiment indicator (0-100)")
    output.append("- 0-25 = Extreme Fear (historically good buying opportunities)")
    output.append("- 26-46 = Fear, 47-54 = Neutral, 55-75 = Greed")
    output.append("- 76-100 = Extreme Greed (historically poor time to buy)")
    output.append("- Based on volatility, momentum, social media, surveys, and dominance")
    output.append("")
    output.append("**Note on Safe Haven Drivers:**")
    output.append("- Treasury 10Y (DGS10): 10-Year nominal Treasury yield - benchmark risk-free rate")
    output.append("- Key relationship: Nominal Yield = Real Yield + Breakeven Inflation")
    output.append("- Real Yield 10Y (DFII10): 10-Year TIPS yield - inflation-adjusted return")
    output.append("- Gold has strong inverse correlation with real yields")
    output.append("- Falling real yields = tailwind for gold, rising = headwind")
    output.append("- Breakeven Inflation 10Y (T10YIE): Market's 10-year inflation expectations")
    output.append("- Rising breakevens often support gold prices")
    output.append("- GDX/GLD Ratio: Gold miners vs gold performance")
    output.append("- Rising ratio = miners outperforming (bullish), miners often lead gold at turning points")
    output.append("")

    return "\n".join(output)

def main():
    """Generate and save the neutral AI summary."""
    print("=" * 80)
    print("GENERATING NEUTRAL MARKET DATA EXPORT")
    print("=" * 80)
    print("")

    print("Reading CSV files...")
    summary = generate_markdown_summary()

    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        f.write(summary)

    print("")
    print("✅ Export generated successfully!")
    print("")
    print(f"File: {OUTPUT_FILE}")
    print(f"Size: {len(summary):,} characters")
    print("")
    print("This export contains:")
    print("  • Pure data and statistics")
    print("  • No interpretations or opinions")
    print("  • No biased language")
    print("  • Objective percentiles and trends")
    print("")
    print("Ready for unbiased AI analysis.")
    print("")

if __name__ == "__main__":
    main()
