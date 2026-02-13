#!/usr/bin/env python3
"""
Export market data summary for AI analysis.
Generates a comprehensive markdown file with all metrics and trends.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import pytz
import json

DATA_DIR = Path("data")
OUTPUT_FILE = "market_data_summary_for_ai.md"

def load_csv_safely(filename):
    """Load CSV file and return DataFrame, or None if not found."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            df = pd.read_csv(filepath)
            # us_recessions.csv has start_date/end_date, not date
            if filename != 'us_recessions.csv':
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

def calculate_divergence_gap(gold_df, hy_df):
    """Calculate the divergence gap between gold-implied and actual spreads."""
    if gold_df is None or hy_df is None:
        return None

    merged = pd.merge(gold_df, hy_df, on='date', how='inner')

    # Calculate gold-implied spread
    gold_prices = merged['gold_price'].values
    hy_spreads = merged['high_yield_spread'].values * 100  # Convert to bp

    gold_implied = ((gold_prices / 200) ** 1.5) * 400
    divergence = gold_implied - hy_spreads

    merged['divergence_gap'] = divergence

    return calculate_stats(merged, 'divergence_gap')

def generate_markdown_summary():
    """Generate comprehensive markdown summary of all market data."""

    output = []

    eastern = pytz.timezone('US/Eastern')
    # Header
    output.append("# MACRO FINANCIAL DATA SUMMARY")
    output.append(f"**Generated:** {datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')} ET")
    output.append("")
    output.append("This document contains a comprehensive summary of all tracked market metrics,")
    output.append("optimized for AI analysis. All data includes current values, trends, and recent history.")
    output.append("")
    output.append("---")
    output.append("")

    # Table of Contents
    output.append("## TABLE OF CONTENTS")
    output.append("1. [Credit Markets](#credit-markets)")
    output.append("2. [Equity Markets](#equity-markets)")
    output.append("3. [Safe Haven Assets](#safe-haven-assets)")
    output.append("4. [Fixed Income](#fixed-income)")
    output.append("5. [Commodities](#commodities)")
    output.append("6. [Market Breadth & Ratios](#market-breadth--ratios)")
    output.append("7. [Divergence Metrics](#divergence-metrics)")
    output.append("8. [Raw Data (JSON)](#raw-data-json)")
    output.append("")
    output.append("---")
    output.append("")

    # Collect all data
    all_stats = {}

    # Load all metrics
    metrics = {
        'divergence': {
            'gold_price': ('gold_price.csv', 'gold_price'),
            'high_yield_spread': ('high_yield_spread.csv', 'high_yield_spread'),
        },
        'credit': {
            'high_yield_spread': ('high_yield_spread.csv', 'high_yield_spread'),
            'investment_grade_spread': ('investment_grade_spread.csv', 'investment_grade_spread'),
            'ccc_spread': ('ccc_spread.csv', 'ccc_spread'),
            'high_yield_credit_price': ('high_yield_credit_price.csv', 'high_yield_credit_price'),
            'investment_grade_credit_price': ('investment_grade_credit_price.csv', 'investment_grade_credit_price'),
            'leveraged_loan_price': ('leveraged_loan_price.csv', 'leveraged_loan_price'),
        },
        'equity': {
            'sp500_price': ('sp500_price.csv', 'sp500_price'),
            'nasdaq_price': ('nasdaq_price.csv', 'nasdaq_price'),
            'small_cap_price': ('small_cap_price.csv', 'small_cap_price'),
            'sp500_equal_weight_price': ('sp500_equal_weight_price.csv', 'sp500_equal_weight_price'),
            'vix_price': ('vix_price.csv', 'vix_price'),
        },
        'safe_havens': {
            'gold_price': ('gold_price.csv', 'gold_price'),
            'bitcoin_price': ('bitcoin_price.csv', 'bitcoin_price'),
            'gold_miners_price': ('gold_miners_price.csv', 'gold_miners_price'),
            'silver_price': ('silver_price.csv', 'silver_price'),
        },
        'fixed_income': {
            'treasury_7_10yr_price': ('treasury_7_10yr_price.csv', 'treasury_7_10yr_price'),
            'treasury_20yr_price': ('treasury_20yr_price.csv', 'treasury_20yr_price'),
            'treasury_short_price': ('treasury_short_price.csv', 'treasury_short_price'),
            'tips_inflation_price': ('tips_inflation_price.csv', 'tips_inflation_price'),
        },
        'commodities': {
            'oil_price': ('oil_price.csv', 'oil_price'),
            'commodities_price': ('commodities_price.csv', 'commodities_price'),
            'dollar_index_price': ('dollar_index_price.csv', 'dollar_index_price'),
        },
        'ratios': {
            'market_breadth_ratio': ('market_breadth_ratio.csv', 'breadth_ratio'),
            'gold_silver_ratio': ('gold_silver_ratio.csv', 'gold_silver_ratio'),
            'real_yield_proxy': ('real_yield_proxy.csv', 'real_yield_proxy'),
            'hyg_treasury_spread': ('hyg_treasury_spread.csv', 'hyg_vs_ief_spread'),
            'lqd_treasury_spread': ('lqd_treasury_spread.csv', 'lqd_vs_ief_spread'),
        }
    }

    # Calculate divergence gap (will be added after other categories)
    gold_df = load_csv_safely('gold_price.csv')
    hy_df = load_csv_safely('high_yield_spread.csv')
    divergence_stats = calculate_divergence_gap(gold_df, hy_df)

    # Process each category
    for category, category_metrics in metrics.items():
        if category == 'divergence':
            continue  # Already handled

        category_name = category.replace('_', ' ').title()
        output.append(f"## {category_name.upper()}")
        output.append("")

        for metric_name, (filename, column) in category_metrics.items():
            df = load_csv_safely(filename)
            stats = calculate_stats(df, column)

            if stats:
                all_stats[metric_name] = stats

                display_name = metric_name.replace('_', ' ').title()
                output.append(f"### {display_name}")

                # Determine unit
                unit = ""
                if 'spread' in metric_name:
                    unit = " bp"
                elif 'price' in metric_name and 'vix' not in metric_name:
                    unit = ""
                    if 'bitcoin' in metric_name or 'gold' in metric_name or 'sp500' in metric_name:
                        stats['current'] = stats['current']

                output.append(f"- **Current:** {stats['current']:.2f}{unit}")
                if 'change_1d' in stats:
                    output.append(f"- **1-Day Change:** {stats['change_1d']:+.2f}{unit} ({stats['change_1d_pct']:+.2f}%)")
                if 'change_10d' in stats:
                    output.append(f"- **10-Day Change:** {stats['change_10d']:+.2f}{unit} ({stats['change_10d_pct']:+.2f}%)")
                if 'change_30d' in stats:
                    output.append(f"- **30-Day Change:** {stats['change_30d']:+.2f}{unit} ({stats['change_30d_pct']:+.2f}%)")
                output.append(f"- **Range:** {stats['min']:.2f} - {stats['max']:.2f}{unit}")
                output.append(f"- **Mean:** {stats['mean']:.2f}{unit} | **Median:** {stats['median']:.2f}{unit}")
                output.append(f"- **Data Points:** {stats['count']} ({stats['first_date']} to {stats['last_date']})")
                output.append("")

        output.append("")

    # DIVERGENCE METRICS (added after other categories)
    output.append("## DIVERGENCE METRICS")
    output.append("")
    output.append("### Divergence Gap (Gold-Implied Spread vs Actual HY Spread)")
    if divergence_stats:
        output.append(f"- **Current:** {divergence_stats['current']:.1f} bp")
        output.append(f"- **1-Day Change:** {divergence_stats.get('change_1d', 0):+.1f} bp ({divergence_stats.get('change_1d_pct', 0):+.2f}%)")
        output.append(f"- **5-Day Change:** {divergence_stats.get('change_5d', 0):+.1f} bp ({divergence_stats.get('change_5d_pct', 0):+.2f}%)")
        output.append(f"- **10-Day Change:** {divergence_stats.get('change_10d', 0):+.1f} bp ({divergence_stats.get('change_10d_pct', 0):+.2f}%)")
        output.append(f"- **30-Day Change:** {divergence_stats.get('change_30d', 0):+.1f} bp ({divergence_stats.get('change_30d_pct', 0):+.2f}%)")
        output.append(f"- **Range:** {divergence_stats['min']:.1f} - {divergence_stats['max']:.1f} bp")
        output.append(f"- **Mean:** {divergence_stats['mean']:.1f} bp")
        output.append("")
        output.append("**Recent 10 Days:**")
        output.append("```")
        output.append("Date       | Divergence Gap (bp)")
        output.append("-----------|-------------------")
        for item in divergence_stats['recent_data']:
            output.append(f"{item['date']} | {item['value']:.1f}")
        output.append("```")
        output.append("")
        all_stats['divergence_gap'] = divergence_stats
    output.append("")

    # RAW DATA (JSON)
    output.append("## RAW DATA (JSON)")
    output.append("")
    output.append("Complete dataset in JSON format for programmatic analysis:")
    output.append("")
    output.append("```json")
    output.append(json.dumps(all_stats, indent=2))
    output.append("```")
    output.append("")

    return "\n".join(output)

def main():
    """Generate and save the AI summary."""
    print("=" * 80)
    print("GENERATING AI-OPTIMIZED MARKET DATA SUMMARY")
    print("=" * 80)
    print("")

    print("Reading CSV files...")
    summary = generate_markdown_summary()

    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        f.write(summary)

    print("")
    print("✅ Summary generated successfully!")
    print("")
    print(f"File: {OUTPUT_FILE}")
    print(f"Size: {len(summary):,} characters")
    print("")
    print("You can now:")
    print("  1. Copy the entire file content")
    print("  2. Paste into Claude, ChatGPT, or Grok")
    print("  3. Ask for analysis of the market conditions")
    print("")
    print("Example prompt:")
    print('  "Analyze this market data and tell me what\'s happening,')
    print('   what scenarios are most likely, and what to watch for."')
    print("")

if __name__ == "__main__":
    main()
