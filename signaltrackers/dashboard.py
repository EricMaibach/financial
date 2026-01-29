#!/usr/bin/env python3
"""
Market Divergence Dashboard
A comprehensive web dashboard for tracking the historic market divergence.
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import subprocess
import threading
import os
from openai import OpenAI
from kalshi_data import fetch_all_prediction_markets

app = Flask(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Track data reload status
reload_status = {
    'in_progress': False,
    'last_reload': None,
    'error': None
}

DATA_DIR = Path("data")

# Metric descriptions for educational purposes
METRIC_DESCRIPTIONS = {
    'divergence_gap': {
        'what': 'The gap between what gold prices are "saying" credit spreads should be versus what they actually are. Calculated as: Gold-Implied Spread minus Actual HY Spread.',
        'why': 'A massive divergence indicates one of these markets is catastrophically wrong. When safe havens (gold) are pricing extreme crisis while credit markets remain calm, a major dislocation is likely.',
        'watch': 'Gap >900 bp is unprecedented. Watch for: (1) Gap widening = crisis building, (2) Gap narrowing via credit widening = crisis arriving, (3) Gap narrowing via gold falling = false alarm resolving.'
    },
    'high_yield_spread': {
        'what': 'The yield premium investors demand to hold junk bonds (BB-rated or below) versus Treasury bonds. Measured in basis points (100 bp = 1%).',
        'why': 'Primary gauge of credit market stress. When spreads are tight (<300 bp), markets see low default risk. When spreads blow out (>500 bp), credit crisis is underway.',
        'watch': 'Current: 276 bp (7th percentile - extremely tight). Key levels: >300 bp = early warning, >400 bp = deteriorating, >500 bp = crisis mode, >800 bp = severe crisis.'
    },
    'investment_grade_spread': {
        'what': 'Yield premium on investment-grade corporate bonds (BBB to AAA-rated) versus Treasuries. Lower risk than high-yield.',
        'why': 'Reflects stress in higher-quality corporate credit. Tends to lead high-yield spreads by a few weeks when widening.',
        'watch': 'Current: 79 bp (extremely tight). Key levels: >100 bp = caution, >150 bp = stress building, >200 bp = crisis.'
    },
    'ccc_spread': {
        'what': 'Spread on CCC-rated bonds - the most distressed segment of the high-yield market (one step above default).',
        'why': 'Leading indicator of default risk. CCC/HY ratio shows if distressed credits are lagging or leading the broader market.',
        'watch': 'CCC/HY ratio: 3.14x (normal range: 2.5-4x). Rising ratio = distressed credits under pressure first. Falling ratio = broad HY catching down.'
    },
    'gold_price': {
        'what': 'Price of gold per troy ounce (tracking via GLD ETF). Primary safe-haven asset.',
        'why': 'Gold rises when investors fear currency debasement, geopolitical risk, or structural economic crisis. At $4,145 (89th percentile), gold is pricing extreme crisis.',
        'watch': 'Key levels: >$4,000 = crisis signal, >$4,500 = severe crisis, >$5,000 = panic. Below $4,000 = fears moderating.'
    },
    'bitcoin_price': {
        'what': 'Price of Bitcoin in USD. Risk asset and liquidity gauge.',
        'why': 'Bitcoin crashed 24% from $120k peak 3 months ago - major liquidity warning. Acts as early warning for risk asset stress.',
        'watch': 'Peak: $120k, Current: ~$91k. Further crashes = liquidity crisis deepening. Recovery toward $100k+ = risk appetite returning.'
    },
    'vix_price': {
        'what': 'CBOE Volatility Index - measures expected S&P 500 volatility over next 30 days. Known as the "fear gauge".',
        'why': 'Low VIX (14-15) despite other warning signs = dangerous complacency. VIX spike typically precedes or coincides with equity selloffs.',
        'watch': 'Current: 14.49 (low). Key levels: >20 = fear rising, >25 = significant stress, >30 = crisis mode, >40 = panic.'
    },
    'sp500_price': {
        'what': 'S&P 500 index tracking 500 largest US stocks (via SPY ETF).',
        'why': 'Benchmark for US equity market. Currently near all-time highs while credit spreads are tight and gold is screaming - unprecedented divergence.',
        'watch': 'Watch for: 5-10% drawdown = early weakness, 15-20% = correction, >20% = bear market.'
    },
    'market_breadth_ratio': {
        'what': 'Equal-weight S&P 500 (RSP) divided by market-cap-weight S&P 500 (SPY). Measures market concentration.',
        'why': 'Low ratio = narrow market rally driven by few mega-cap stocks. High concentration = fragile market vulnerable to rotation.',
        'watch': 'Current: Very narrow rally. Ratio falling = concentration increasing (risk). Ratio rising = broadening (healthier).'
    },
    'nasdaq_price': {
        'what': 'Nasdaq 100 index - tech-heavy index of 100 largest non-financial stocks (via QQQ ETF).',
        'why': 'Heavily weighted to mega-cap tech (Mag 7). Performance gap vs S&P 500 shows tech leadership or stress.',
        'watch': 'Outperformance = tech leadership continues. Underperformance = rotation or tech stress.'
    },
    'small_cap_price': {
        'what': 'Russell 2000 small-cap index (via IWM ETF).',
        'why': 'Small caps typically underperform in late cycle or when credit conditions tighten. Leading indicator of economic stress.',
        'watch': 'Underperformance vs large caps = economic stress signal. Outperformance = broadening rally.'
    },
    'leveraged_loan_price': {
        'what': 'Price of leveraged loan ETF (BKLN) - floating-rate senior secured loans to sub-investment grade companies.',
        'why': 'Senior in capital structure, so less risky than high-yield bonds. Price stability suggests loan market is calm despite warnings.',
        'watch': 'Price stability = loan market comfortable. Sharp decline = credit stress spreading to senior secured debt.'
    },
    'high_yield_credit_price': {
        'what': 'Price of high-yield bond ETF (HYG) - junk bond market proxy.',
        'why': 'Price reflects both spread changes and Treasury moves. Falling price = credit stress or rising rates.',
        'watch': 'Stable/rising price = credit markets calm. Sharp decline = spreads widening or credit stress.'
    },
    'investment_grade_credit_price': {
        'what': 'Price of investment-grade corporate bond ETF (LQD).',
        'why': 'Higher quality than HYG. Price decline = either IG spreads widening or Treasury yields rising.',
        'watch': 'Watch for divergence from HYG. LQD declining while HYG stable = quality flight.'
    },
    'treasury_7_10yr_price': {
        'what': 'Price of 7-10 year Treasury ETF (IEF) - medium-term US government bonds.',
        'why': 'Safe haven during equity stress. Price rises (yields fall) when investors flee to safety.',
        'watch': 'Rising price = safety bid. Falling price = rising yields or inflation fears.'
    },
    'treasury_20yr_price': {
        'what': 'Price of 20+ year Treasury ETF (TLT) - long-term US government bonds.',
        'why': 'Most sensitive to interest rate changes. Large price moves signal major shifts in rate expectations.',
        'watch': 'Rising sharply = flight to safety or recession fears. Falling = inflation concerns or Fed hawkishness.'
    },
    'treasury_short_price': {
        'what': 'Price of short-term Treasury ETF (SHY) - 1-3 year US government bonds.',
        'why': 'Anchored to Fed policy. Minimal volatility. Price reflects front-end rate expectations.',
        'watch': 'Relatively stable. Large moves = major Fed policy shift.'
    },
    'tips_inflation_price': {
        'what': 'Treasury Inflation-Protected Securities (TIP) - bonds that adjust for inflation.',
        'why': 'Real yield gauge. TIPS outperform when inflation expectations rise.',
        'watch': 'Outperforming nominal Treasuries = inflation concerns. Underperforming = deflation fears.'
    },
    'gold_miners_price': {
        'what': 'Gold mining stocks ETF (GDX) - levered play on gold prices.',
        'why': 'Typically outperform physical gold in bull markets due to operating leverage. Underperformance = margin pressure.',
        'watch': 'Outperforming gold = strong gold bull market. Lagging gold = margin or execution concerns.'
    },
    'silver_price': {
        'what': 'Silver price (via SLV ETF) - both industrial metal and monetary metal.',
        'why': 'More volatile than gold. Outperformance = risk appetite in precious metals. Underperformance = defensive gold positioning.',
        'watch': 'Gold/Silver ratio: High ratio = defensive, low ratio = aggressive.'
    },
    'dollar_index_price': {
        'what': 'US Dollar Index (via UUP ETF) - dollar strength vs basket of currencies.',
        'why': 'Strong dollar = global USD shortage or flight to safety. Weak dollar = risk-on or inflation fears.',
        'watch': 'Rising with gold = extreme crisis. Falling with gold rising = currency debasement fears.'
    },
    'commodities_price': {
        'what': 'Broad commodity index (DBC) - oil, metals, agriculture.',
        'why': 'Inflation gauge and economic activity indicator. Rising = growth or inflation. Falling = recession fears.',
        'watch': 'Divergence from equities = economic stress signal.'
    },
    'oil_price': {
        'what': 'Crude oil price (via USO ETF).',
        'why': 'Key inflation and economic activity indicator. Crash = recession fears. Spike = inflation/supply shock.',
        'watch': 'Sharp decline with equities = recession signal. Rising with falling equities = stagflation risk.'
    },
    'lqd_treasury_spread': {
        'what': 'Spread between LQD (investment-grade credit) yield and Treasury yield.',
        'why': 'Alternative measure of IG credit stress. Widening = IG credit stress building.',
        'watch': 'Watch for divergence from official IG spread data.'
    },
    'hyg_treasury_spread': {
        'what': 'Spread between HYG (high-yield credit) yield and Treasury yield.',
        'why': 'Market-based measure of HY credit risk using ETF yields.',
        'watch': 'Should track official HY spread. Divergence = ETF-specific flows or technical factors.'
    },
    'real_yield_proxy': {
        'what': 'Approximation of real yields using TIP (inflation-protected bonds).',
        'why': 'Real yields determine discount rate for growth stocks. Negative real yields = bullish for long-duration assets.',
        'watch': 'Rising real yields = pressure on growth stocks and gold. Falling = support for risk assets.'
    },
    'gold_silver_ratio': {
        'what': 'Gold price divided by silver price.',
        'why': 'High ratio (>80) = defensive positioning, fear. Low ratio (<70) = risk appetite in precious metals.',
        'watch': 'Current ratio tells you if gold move is fear-driven (high ratio) or inflation-driven (low ratio).'
    },
    'smh_spy_ratio': {
        'what': 'Semiconductor ETF (SMH) price divided by S&P 500 (SPY) price, scaled to 100. Measures semiconductor sector concentration.',
        'why': 'Semiconductors are at the heart of the AI boom. Rising ratio = semiconductor outperformance and increasing AI/tech concentration risk.',
        'watch': 'High and rising ratio = AI bubble concerns. Sharp decline = potential tech/AI selloff beginning. Compare to 2000 tech bubble.'
    },
    'xlk_spy_ratio': {
        'what': 'Technology Sector ETF (XLK) price divided by S&P 500 (SPY) price, scaled to 100. Measures tech sector weight in the market.',
        'why': 'Tech sector dominance indicator. When tech becomes too large a portion of the index, market becomes vulnerable to tech-specific risks.',
        'watch': 'Ratio >35 historically signals excessive tech concentration. Rising ratio = tech leadership. Falling ratio = rotation away from tech.'
    },
    'growth_value_ratio': {
        'what': 'Russell 1000 Growth (IWF) divided by Russell 1000 Value (IWD), scaled to 100. Measures growth vs value style preference.',
        'why': 'Growth stocks (including AI/tech) outperform when investors chase future earnings. Extreme growth outperformance often precedes corrections.',
        'watch': 'High ratio = growth bubble territory, similar to late 1990s. Falling ratio = value rotation, often signals economic slowdown fears.'
    },
    'usdjpy_price': {
        'what': 'USD/JPY exchange rate - how many Japanese Yen per 1 US Dollar.',
        'why': 'Critical for monitoring the yen carry trade. Investors borrow cheap yen to invest in higher-yielding assets. When yen strengthens (USD/JPY falls), carry trades unwind violently.',
        'watch': 'Rising USD/JPY = yen weakening, carry trade expanding. Sharp USD/JPY drop = carry trade unwinding, risk-off. Key levels: <140 = potential crisis, >155 = extreme yen weakness.'
    },
    'japan_10y_yield': {
        'what': 'Japan 10-Year Government Bond (JGB) yield. The benchmark interest rate for yen-denominated borrowing.',
        'why': 'Ultra-low Japanese rates enable the carry trade. When BOJ allows yields to rise, it signals potential end of easy money and triggers global risk-off.',
        'watch': 'Near-zero yields = carry trade intact. Rising yields (>0.5%) = BOJ tightening, carry trade at risk. BOJ yield curve control changes are major market events.'
    },
    'consumer_confidence': {
        'what': 'University of Michigan Consumer Sentiment Index. Survey-based measure of how optimistic consumers feel about the economy.',
        'why': 'Leading indicator of consumer spending, which drives ~70% of US GDP. Falling confidence often precedes recessions. Divergence from markets = warning sign.',
        'watch': 'Index <70 = recession territory. Index >100 = strong optimism. Sharp drops (>10 points) historically precede economic downturns. Compare to market levels for divergence signals.'
    },
    'm2_money_supply': {
        'what': 'M2 Money Stock - includes cash, checking deposits, savings deposits, and money market funds. Measures total "spendable" money in the economy.',
        'why': 'Tracks Fed liquidity injections/withdrawals. Rapid M2 growth = potential inflation. M2 contraction (rare) = deflationary pressure. Current cycle unprecedented.',
        'watch': 'YoY growth >10% = inflationary. YoY contraction = highly unusual, last seen in Great Depression. M2/GDP ratio shows excess liquidity relative to economy size.'
    },
    'cpi': {
        'what': 'Consumer Price Index for All Urban Consumers - measures average change in prices paid by consumers for goods and services.',
        'why': 'Primary inflation gauge used by Fed for policy decisions. High CPI = Fed tightening. Low/negative CPI = deflation risk and potential easing.',
        'watch': 'Fed target is ~2% YoY. >3% = elevated inflation. >5% = high inflation requiring aggressive response. Negative readings = deflation, major crisis signal.'
    }
}


def load_csv_data(filename):
    """Load CSV file and return as DataFrame."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return None


def calculate_returns(df, column, periods=[1, 5, 20]):
    """Calculate returns over multiple periods."""
    if df is None or len(df) < 2:
        return {}

    returns = {}
    for period in periods:
        if len(df) > period:
            current = df.iloc[-1][column]
            past = df.iloc[-(period+1)][column]
            returns[f'{period}d'] = ((current / past) - 1) * 100
    return returns


def calculate_top_movers(num_movers=5):
    """
    Calculate top movers based on z-score of 5-day changes.
    Returns metrics with most unusual moves relative to their historical volatility.
    """
    import os
    import numpy as np

    movers = []

    # Define which metrics use absolute change vs % change for display
    # Also define friendly names and explorer links
    metric_config = {
        # Spreads - use absolute bp change
        'high_yield_spread': {'display': 'abs', 'unit': 'bp', 'name': 'HY Spread', 'link': '/metric/hy_spread', 'multiplier': 100},
        'investment_grade_spread': {'display': 'abs', 'unit': 'bp', 'name': 'IG Spread', 'link': '/explorer?metric=investment_grade_spread', 'multiplier': 100},
        'ccc_spread': {'display': 'abs', 'unit': 'bp', 'name': 'CCC Spread', 'link': '/explorer?metric=ccc_spread', 'multiplier': 100},

        # Prices - use % change
        'gold_price': {'display': 'pct', 'unit': '%', 'name': 'Gold', 'link': '/metric/gold_price'},
        'silver_price': {'display': 'pct', 'unit': '%', 'name': 'Silver', 'link': '/explorer?metric=silver_price'},
        'bitcoin_price': {'display': 'pct', 'unit': '%', 'name': 'Bitcoin', 'link': '/metric/bitcoin_price'},
        'sp500_price': {'display': 'pct', 'unit': '%', 'name': 'S&P 500', 'link': '/metric/sp500'},
        'nasdaq_price': {'display': 'pct', 'unit': '%', 'name': 'Nasdaq', 'link': '/explorer?metric=nasdaq_price'},
        'vix_price': {'display': 'pct', 'unit': '%', 'name': 'VIX', 'link': '/metric/vix'},
        'oil_price': {'display': 'pct', 'unit': '%', 'name': 'Oil', 'link': '/explorer?metric=oil_price'},
        'commodities_price': {'display': 'pct', 'unit': '%', 'name': 'Commodities', 'link': '/explorer?metric=commodities_price'},
        'gold_miners_price': {'display': 'pct', 'unit': '%', 'name': 'Gold Miners', 'link': '/explorer?metric=gold_miners_price'},
        'small_cap_price': {'display': 'pct', 'unit': '%', 'name': 'Small Caps', 'link': '/explorer?metric=small_cap_price'},
        'tech_sector_price': {'display': 'pct', 'unit': '%', 'name': 'Tech Sector', 'link': '/explorer?metric=tech_sector_price'},
        'semiconductor_price': {'display': 'pct', 'unit': '%', 'name': 'Semiconductors', 'link': '/explorer?metric=semiconductor_price'},
        'treasury_20yr_price': {'display': 'pct', 'unit': '%', 'name': 'Treasury 20Y', 'link': '/explorer?metric=treasury_20yr_price'},
        'dollar_index_price': {'display': 'pct', 'unit': '%', 'name': 'Dollar Index', 'link': '/explorer?metric=dollar_index_price'},
        'usdjpy_price': {'display': 'pct', 'unit': '%', 'name': 'USD/JPY', 'link': '/explorer?metric=usdjpy_price'},

        # Ratios - use % change
        'gold_silver_ratio': {'display': 'pct', 'unit': '%', 'name': 'Gold/Silver Ratio', 'link': '/explorer?metric=gold_silver_ratio'},
        'smh_spy_ratio': {'display': 'pct', 'unit': '%', 'name': 'Semiconductor/SPY', 'link': '/explorer?metric=smh_spy_ratio'},
        'xlk_spy_ratio': {'display': 'pct', 'unit': '%', 'name': 'Tech/SPY', 'link': '/explorer?metric=xlk_spy_ratio'},
        'growth_value_ratio': {'display': 'pct', 'unit': '%', 'name': 'Growth/Value', 'link': '/explorer?metric=growth_value_ratio'},
        'market_breadth_ratio': {'display': 'pct', 'unit': '%', 'name': 'Market Breadth', 'link': '/explorer?metric=market_breadth_ratio'},

        # Yields - use absolute change
        'japan_10y_yield': {'display': 'abs', 'unit': '%', 'name': 'Japan 10Y Yield', 'link': '/explorer?metric=japan_10y_yield', 'multiplier': 1},
        'real_yield_proxy': {'display': 'pct', 'unit': '%', 'name': 'Real Yield Proxy', 'link': '/explorer?metric=real_yield_proxy'},

        # ETF spreads
        'hyg_treasury_spread': {'display': 'pct', 'unit': '%', 'name': 'HYG-Treasury Spread', 'link': '/explorer?metric=hyg_treasury_spread'},
        'lqd_treasury_spread': {'display': 'pct', 'unit': '%', 'name': 'LQD-Treasury Spread', 'link': '/explorer?metric=lqd_treasury_spread'},

        # Economic Indicators - use % change
        'consumer_confidence': {'display': 'pct', 'unit': '%', 'name': 'Consumer Confidence', 'link': '/explorer?metric=consumer_confidence'},
        'm2_money_supply': {'display': 'pct', 'unit': '%', 'name': 'M2 Money Supply', 'link': '/explorer?metric=m2_money_supply'},
        'cpi': {'display': 'pct', 'unit': '%', 'name': 'CPI (Inflation)', 'link': '/explorer?metric=cpi'},
    }

    # Process each metric file
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f != 'us_recessions.csv']

    for filename in csv_files:
        metric_name = filename.replace('.csv', '')
        config = metric_config.get(metric_name)

        # Skip metrics not in our config (like etf duplicates)
        if not config:
            continue

        df = load_csv_data(filename)
        if df is None or len(df) < 60:  # Need enough history for z-score
            continue

        col = df.columns[1]  # Data column
        multiplier = config.get('multiplier', 1)

        # Calculate 5-day changes for z-score
        if config['display'] == 'pct':
            # Percent change
            df['change_5d'] = df[col].pct_change(5) * 100
        else:
            # Absolute change (for spreads)
            df['change_5d'] = (df[col] - df[col].shift(5)) * multiplier

        # Calculate z-score using rolling std of 5-day changes (60-day window)
        df['rolling_std'] = df['change_5d'].rolling(60).std()
        df['rolling_mean'] = df['change_5d'].rolling(60).mean()

        # Get current values
        if len(df) < 65:  # Not enough data for z-score
            continue

        current_change = df['change_5d'].iloc[-1]
        rolling_std = df['rolling_std'].iloc[-1]
        rolling_mean = df['rolling_mean'].iloc[-1]

        if pd.isna(current_change) or pd.isna(rolling_std) or rolling_std == 0:
            continue

        z_score = (current_change - rolling_mean) / rolling_std

        movers.append({
            'metric': metric_name,
            'name': config['name'],
            'link': config['link'],
            'change_5d': round(current_change, 2),
            'z_score': round(z_score, 2),
            'unit': config['unit'],
            'display_type': config['display']
        })

    # Add calculated metrics (divergence gap, CCC/HY ratio)
    # Divergence Gap
    gold_df = load_csv_data('gold_price.csv')
    hy_df = load_csv_data('high_yield_spread.csv')

    if gold_df is not None and hy_df is not None and len(gold_df) > 65 and len(hy_df) > 65:
        # Calculate divergence gap series
        merged = pd.merge(gold_df, hy_df, on='date', suffixes=('_gold', '_hy'))
        merged['gold_price'] = merged[merged.columns[1]] * 10
        merged['hy_spread'] = merged[merged.columns[2]] * 100
        merged['gold_implied'] = ((merged['gold_price'] / 2000) ** 1.5) * 400
        merged['divergence_gap'] = merged['gold_implied'] - merged['hy_spread']

        merged['change_5d'] = merged['divergence_gap'] - merged['divergence_gap'].shift(5)
        merged['rolling_std'] = merged['change_5d'].rolling(60).std()
        merged['rolling_mean'] = merged['change_5d'].rolling(60).mean()

        if len(merged) > 65:
            current_change = merged['change_5d'].iloc[-1]
            rolling_std = merged['rolling_std'].iloc[-1]
            rolling_mean = merged['rolling_mean'].iloc[-1]

            if not pd.isna(current_change) and not pd.isna(rolling_std) and rolling_std > 0:
                z_score = (current_change - rolling_mean) / rolling_std
                movers.append({
                    'metric': 'divergence_gap',
                    'name': 'Divergence Gap',
                    'link': '/metric/divergence_gap',
                    'change_5d': round(current_change, 0),
                    'z_score': round(z_score, 2),
                    'unit': 'bp',
                    'display_type': 'abs'
                })

    # Sort by absolute z-score and return top N
    movers.sort(key=lambda x: abs(x['z_score']), reverse=True)
    return movers[:num_movers]


def calculate_crisis_score():
    """Calculate comprehensive crisis warning score."""
    score = 0
    warnings = []

    # Load data
    hy_df = load_csv_data('high_yield_spread.csv')
    ig_df = load_csv_data('investment_grade_spread.csv')
    gold_df = load_csv_data('gold_price.csv')
    vix_df = load_csv_data('vix_price.csv')
    btc_df = load_csv_data('bitcoin_price.csv')
    breadth_df = load_csv_data('market_breadth_ratio.csv')

    # Credit spreads (0-25 points)
    if hy_df is not None:
        hy_current = hy_df.iloc[-1][hy_df.columns[1]] * 100
        if hy_current < 250:
            score += 15
            warnings.append(f"HY spreads extremely tight ({hy_current:.0f} bp)")
        elif hy_current < 300:
            score += 10
            warnings.append(f"HY spreads very tight ({hy_current:.0f} bp)")

    if ig_df is not None:
        ig_current = ig_df.iloc[-1][ig_df.columns[1]] * 100
        if ig_current < 80:
            score += 10
            warnings.append(f"IG spreads extremely tight ({ig_current:.0f} bp)")

    # Gold (0-25 points)
    if gold_df is not None:
        gold_price = gold_df.iloc[-1][gold_df.columns[1]] * 10
        if gold_price > 4500:
            score += 25
            warnings.append(f"Gold EXTREME (${gold_price:.0f})")
        elif gold_price > 4000:
            score += 20
            warnings.append(f"Gold very elevated (${gold_price:.0f})")
        elif gold_price > 3500:
            score += 15
            warnings.append(f"Gold elevated (${gold_price:.0f})")

    # Divergence gap (0-25 points)
    if gold_df is not None and hy_df is not None:
        gold_price = gold_df.iloc[-1][gold_df.columns[1]] * 10
        hy_current = hy_df.iloc[-1][hy_df.columns[1]] * 100
        gold_implied = ((gold_price / 2000) ** 1.5) * 400
        divergence_gap = gold_implied - hy_current

        if divergence_gap > 800:
            score += 25
            warnings.append(f"EXTREME divergence gap ({divergence_gap:.0f} bp)")
        elif divergence_gap > 600:
            score += 20
            warnings.append(f"Very large divergence gap ({divergence_gap:.0f} bp)")
        elif divergence_gap > 400:
            score += 15
            warnings.append(f"Large divergence gap ({divergence_gap:.0f} bp)")

    # Market breadth (0-15 points)
    if breadth_df is not None and len(breadth_df) > 0:
        breadth = breadth_df.iloc[-1][breadth_df.columns[1]]
        if breadth < 95:
            score += 10
            warnings.append("Market breadth weak - narrow rally")

    # VIX (0-10 points)
    if vix_df is not None:
        vix_current = vix_df.iloc[-1][vix_df.columns[1]]
        if vix_current > 30:
            score += 10
            warnings.append(f"VIX elevated ({vix_current:.1f})")
        elif vix_current < 15 and score > 30:
            score += 5
            warnings.append(f"VIX low despite warnings ({vix_current:.1f}) - complacency")

    # Bitcoin (0-10 points)
    if btc_df is not None and len(btc_df) > 20:
        btc_returns = calculate_returns(btc_df, btc_df.columns[1], [20])
        if '20d' in btc_returns:
            if btc_returns['20d'] < -10:
                score += 10
                warnings.append(f"Bitcoin weak ({btc_returns['20d']:.1f}% 30d)")
            elif btc_returns['20d'] < -5:
                score += 5
                warnings.append(f"Bitcoin declining ({btc_returns['20d']:.1f}% 30d)")

    return min(score, 100), warnings


def get_dashboard_data():
    """Get all dashboard data."""
    data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'metrics': {},
        'charts': {},
        'warnings': []
    }

    # Calculate crisis score
    crisis_score, warnings = calculate_crisis_score()
    data['metrics']['crisis_score'] = crisis_score
    data['warnings'] = warnings

    # Load key metrics
    hy_df = load_csv_data('high_yield_spread.csv')
    ig_df = load_csv_data('investment_grade_spread.csv')
    ccc_df = load_csv_data('ccc_spread.csv')
    gold_df = load_csv_data('gold_price.csv')
    btc_df = load_csv_data('bitcoin_price.csv')
    spy_df = load_csv_data('sp500_price.csv')
    vix_df = load_csv_data('vix_price.csv')

    # HY Spreads
    if hy_df is not None:
        hy_current = hy_df.iloc[-1][hy_df.columns[1]] * 100
        hy_change_30d = (hy_df.iloc[-1][hy_df.columns[1]] - hy_df.iloc[max(0, len(hy_df)-21)][hy_df.columns[1]]) * 100
        hy_change_5d = (hy_df.iloc[-1][hy_df.columns[1]] - hy_df.iloc[max(0, len(hy_df)-6)][hy_df.columns[1]]) * 100
        data['metrics']['hy_spread'] = {
            'current': round(hy_current, 0),
            'change_5d': round(hy_change_5d, 0),
            'change_30d': round(hy_change_30d, 0),
            'status': 'tight' if hy_current < 300 else 'normal' if hy_current < 600 else 'wide'
        }

    # Gold
    if gold_df is not None:
        gold_price = gold_df.iloc[-1][gold_df.columns[1]] * 10
        gold_returns = calculate_returns(gold_df, gold_df.columns[1], [5, 20])
        data['metrics']['gold'] = {
            'price': round(gold_price, 0),
            'change_5d': round(gold_returns.get('5d', 0), 2),
            'change_30d': round(gold_returns.get('20d', 0), 2)
        }

    # Bitcoin
    if btc_df is not None:
        btc_price = btc_df.iloc[-1][btc_df.columns[1]]
        btc_returns = calculate_returns(btc_df, btc_df.columns[1], [5, 20])

        # Calculate peak and decline
        btc_peak = btc_df[btc_df.columns[1]].max()
        btc_decline = ((btc_price / btc_peak) - 1) * 100

        data['metrics']['bitcoin'] = {
            'price': round(btc_price, 0),
            'peak': round(btc_peak, 0),
            'decline_from_peak': round(btc_decline, 1),
            'change_5d': round(btc_returns.get('5d', 0), 2),
            'change_30d': round(btc_returns.get('20d', 0), 2)
        }

    # Divergence Gap
    if gold_df is not None and hy_df is not None:
        gold_price = gold_df.iloc[-1][gold_df.columns[1]] * 10
        hy_current = hy_df.iloc[-1][hy_df.columns[1]] * 100
        gold_implied = ((gold_price / 2000) ** 1.5) * 400
        divergence_gap = gold_implied - hy_current

        # Calculate 5d and 30d changes for divergence gap
        gap_5d_ago = None
        gap_30d_ago = None
        if len(gold_df) > 5 and len(hy_df) > 5:
            gold_5d = gold_df.iloc[-6][gold_df.columns[1]] * 10
            hy_5d = hy_df.iloc[-6][hy_df.columns[1]] * 100
            implied_5d = ((gold_5d / 2000) ** 1.5) * 400
            gap_5d_ago = implied_5d - hy_5d
        if len(gold_df) > 20 and len(hy_df) > 20:
            gold_30d = gold_df.iloc[-21][gold_df.columns[1]] * 10
            hy_30d = hy_df.iloc[-21][hy_df.columns[1]] * 100
            implied_30d = ((gold_30d / 2000) ** 1.5) * 400
            gap_30d_ago = implied_30d - hy_30d

        data['metrics']['divergence'] = {
            'gap': round(divergence_gap, 0),
            'gold_implied_spread': round(gold_implied, 0),
            'actual_spread': round(hy_current, 0),
            'gap_change_5d': round(divergence_gap - gap_5d_ago, 0) if gap_5d_ago is not None else 0,
            'gap_change_30d': round(divergence_gap - gap_30d_ago, 0) if gap_30d_ago is not None else 0
        }

    # VIX
    if vix_df is not None:
        vix_current = vix_df.iloc[-1][vix_df.columns[1]]
        vix_returns = calculate_returns(vix_df, vix_df.columns[1], [5, 20])
        data['metrics']['vix'] = {
            'current': round(vix_current, 2),
            'change_5d': round(vix_returns.get('5d', 0), 2),
            'change_30d': round(vix_returns.get('20d', 0), 2),
            'status': 'low' if vix_current < 16 else 'normal' if vix_current < 25 else 'elevated'
        }

    # CCC/HY Ratio
    if ccc_df is not None and hy_df is not None:
        ccc_current = ccc_df.iloc[-1][ccc_df.columns[1]] * 100
        hy_current = hy_df.iloc[-1][hy_df.columns[1]] * 100
        ratio = ccc_current / hy_current

        # Calculate 5d and 30d changes for ratio
        ratio_5d_ago = None
        ratio_30d_ago = None
        if len(ccc_df) > 5 and len(hy_df) > 5:
            ccc_5d = ccc_df.iloc[-6][ccc_df.columns[1]] * 100
            hy_5d = hy_df.iloc[-6][hy_df.columns[1]] * 100
            ratio_5d_ago = ccc_5d / hy_5d if hy_5d > 0 else None
        if len(ccc_df) > 20 and len(hy_df) > 20:
            ccc_30d = ccc_df.iloc[-21][ccc_df.columns[1]] * 100
            hy_30d = hy_df.iloc[-21][hy_df.columns[1]] * 100
            ratio_30d_ago = ccc_30d / hy_30d if hy_30d > 0 else None

        data['metrics']['ccc_hy_ratio'] = {
            'current': round(ratio, 2),
            'change_5d': round(ratio - ratio_5d_ago, 2) if ratio_5d_ago else 0,
            'change_30d': round(ratio - ratio_30d_ago, 2) if ratio_30d_ago else 0
        }

    # SPY
    if spy_df is not None:
        spy_price = spy_df.iloc[-1][spy_df.columns[1]]
        spy_returns = calculate_returns(spy_df, spy_df.columns[1], [5, 20])
        data['metrics']['spy'] = {
            'price': round(spy_price, 2),
            'change_5d': round(spy_returns.get('5d', 0), 2),
            'change_30d': round(spy_returns.get('20d', 0), 2)
        }

    # Market Concentration Ratios
    smh_spy_df = load_csv_data('smh_spy_ratio.csv')
    xlk_spy_df = load_csv_data('xlk_spy_ratio.csv')
    growth_value_df = load_csv_data('growth_value_ratio.csv')

    concentration_metrics = {}

    if smh_spy_df is not None and len(smh_spy_df) > 0:
        smh_spy_current = smh_spy_df.iloc[-1][smh_spy_df.columns[1]]
        smh_spy_returns = calculate_returns(smh_spy_df, smh_spy_df.columns[1], [5, 20])
        # Calculate percentile
        all_values = smh_spy_df[smh_spy_df.columns[1]].dropna()
        percentile = (all_values < smh_spy_current).sum() / len(all_values) * 100
        concentration_metrics['smh_spy'] = {
            'current': round(smh_spy_current, 2),
            'change_5d': round(smh_spy_returns.get('5d', 0), 2),
            'change_30d': round(smh_spy_returns.get('20d', 0), 2),
            'percentile': round(percentile, 1),
            'label': 'Semiconductor/SPY'
        }

    if xlk_spy_df is not None and len(xlk_spy_df) > 0:
        xlk_spy_current = xlk_spy_df.iloc[-1][xlk_spy_df.columns[1]]
        xlk_spy_returns = calculate_returns(xlk_spy_df, xlk_spy_df.columns[1], [5, 20])
        all_values = xlk_spy_df[xlk_spy_df.columns[1]].dropna()
        percentile = (all_values < xlk_spy_current).sum() / len(all_values) * 100
        concentration_metrics['xlk_spy'] = {
            'current': round(xlk_spy_current, 2),
            'change_5d': round(xlk_spy_returns.get('5d', 0), 2),
            'change_30d': round(xlk_spy_returns.get('20d', 0), 2),
            'percentile': round(percentile, 1),
            'label': 'Tech Sector/SPY'
        }

    if growth_value_df is not None and len(growth_value_df) > 0:
        gv_current = growth_value_df.iloc[-1][growth_value_df.columns[1]]
        gv_returns = calculate_returns(growth_value_df, growth_value_df.columns[1], [5, 20])
        all_values = growth_value_df[growth_value_df.columns[1]].dropna()
        percentile = (all_values < gv_current).sum() / len(all_values) * 100
        concentration_metrics['growth_value'] = {
            'current': round(gv_current, 2),
            'change_5d': round(gv_returns.get('5d', 0), 2),
            'change_30d': round(gv_returns.get('20d', 0), 2),
            'percentile': round(percentile, 1),
            'label': 'Growth/Value'
        }

    if concentration_metrics:
        data['metrics']['concentration'] = concentration_metrics

    # Yen Carry Trade Metrics
    usdjpy_df = load_csv_data('usdjpy_price.csv')
    japan_10y_df = load_csv_data('japan_10y_yield.csv')

    carry_trade_metrics = {}

    if usdjpy_df is not None and len(usdjpy_df) > 0:
        usdjpy_current = usdjpy_df.iloc[-1][usdjpy_df.columns[1]]
        usdjpy_returns = calculate_returns(usdjpy_df, usdjpy_df.columns[1], [5, 20])
        all_values = usdjpy_df[usdjpy_df.columns[1]].dropna()
        percentile = (all_values < usdjpy_current).sum() / len(all_values) * 100
        carry_trade_metrics['usdjpy'] = {
            'current': round(usdjpy_current, 2),
            'change_5d': round(usdjpy_returns.get('5d', 0), 2),
            'change_30d': round(usdjpy_returns.get('20d', 0), 2),
            'percentile': round(percentile, 1),
            'label': 'USD/JPY'
        }

    if japan_10y_df is not None and len(japan_10y_df) > 0:
        japan_10y_current = japan_10y_df.iloc[-1][japan_10y_df.columns[1]]
        japan_10y_returns = calculate_returns(japan_10y_df, japan_10y_df.columns[1], [5, 20])
        all_values = japan_10y_df[japan_10y_df.columns[1]].dropna()
        percentile = (all_values < japan_10y_current).sum() / len(all_values) * 100
        carry_trade_metrics['japan_10y'] = {
            'current': round(japan_10y_current, 2),
            'change_5d': round(japan_10y_returns.get('5d', 0), 2),
            'change_30d': round(japan_10y_returns.get('20d', 0), 2),
            'percentile': round(percentile, 1),
            'label': 'Japan 10Y Yield'
        }

    if carry_trade_metrics:
        data['metrics']['carry_trade'] = carry_trade_metrics

    # Economic Indicators
    consumer_confidence_df = load_csv_data('consumer_confidence.csv')
    m2_df = load_csv_data('m2_money_supply.csv')
    cpi_df = load_csv_data('cpi.csv')

    economic_indicators = {}

    if consumer_confidence_df is not None and len(consumer_confidence_df) > 0:
        cc_current = consumer_confidence_df.iloc[-1][consumer_confidence_df.columns[1]]
        cc_returns = calculate_returns(consumer_confidence_df, consumer_confidence_df.columns[1], [20])
        all_values = consumer_confidence_df[consumer_confidence_df.columns[1]].dropna()
        percentile = (all_values < cc_current).sum() / len(all_values) * 100
        economic_indicators['consumer_confidence'] = {
            'current': round(cc_current, 1),
            'change_30d': round(cc_returns.get('20d', 0), 2),
            'percentile': round(percentile, 1),
            'label': 'Consumer Confidence'
        }

    if m2_df is not None and len(m2_df) > 12:
        m2_current = m2_df.iloc[-1][m2_df.columns[1]]
        # Calculate YoY change (M2 is monthly, so 12 periods back)
        if len(m2_df) > 12:
            m2_year_ago = m2_df.iloc[-13][m2_df.columns[1]]
            m2_yoy = ((m2_current / m2_year_ago) - 1) * 100
        else:
            m2_yoy = 0
        all_values = m2_df[m2_df.columns[1]].dropna()
        percentile = (all_values < m2_current).sum() / len(all_values) * 100
        economic_indicators['m2_money_supply'] = {
            'current': round(m2_current / 1000, 2),  # Convert to trillions
            'yoy_change': round(m2_yoy, 1),
            'percentile': round(percentile, 1),
            'label': 'M2 Money Supply'
        }

    if cpi_df is not None and len(cpi_df) > 12:
        cpi_current = cpi_df.iloc[-1][cpi_df.columns[1]]
        # Calculate YoY change (CPI is monthly, so 12 periods back)
        if len(cpi_df) > 12:
            cpi_year_ago = cpi_df.iloc[-13][cpi_df.columns[1]]
            cpi_yoy = ((cpi_current / cpi_year_ago) - 1) * 100
        else:
            cpi_yoy = 0
        all_values = cpi_df[cpi_df.columns[1]].dropna()
        percentile = (all_values < cpi_current).sum() / len(all_values) * 100
        economic_indicators['cpi'] = {
            'current': round(cpi_current, 1),
            'yoy_change': round(cpi_yoy, 1),
            'percentile': round(percentile, 1),
            'label': 'CPI'
        }

    if economic_indicators:
        data['metrics']['economic_indicators'] = economic_indicators

    # Calculate top movers
    data['top_movers'] = calculate_top_movers(5)

    return data


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/credit')
def credit():
    """Credit markets page."""
    return render_template('credit.html')


@app.route('/equity')
def equity():
    """Equity markets page."""
    return render_template('equity.html')


@app.route('/safe-havens')
def safe_havens():
    """Safe havens page."""
    return render_template('safe_havens.html')


@app.route('/scenarios')
def scenarios():
    """Scenarios page."""
    return render_template('scenarios.html')


@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data."""
    return jsonify(get_dashboard_data())


@app.route('/api/chart/<chart_type>')
def api_chart(chart_type):
    """API endpoint for chart data."""

    if chart_type == 'divergence_gap':
        hy_df = load_csv_data('high_yield_spread.csv')
        gold_df = load_csv_data('gold_price.csv')

        if hy_df is not None and gold_df is not None:
            # Merge on date
            merged = pd.merge(hy_df, gold_df, on='date', how='inner')

            dates = merged['date'].dt.strftime('%Y-%m-%d').tolist()
            hy_spreads = (merged[hy_df.columns[1]] * 100).tolist()
            gold_prices = (merged[gold_df.columns[1]] * 10).tolist()
            gold_implied = [((g / 2000) ** 1.5) * 400 for g in gold_prices]
            divergence = [impl - actual for impl, actual in zip(gold_implied, hy_spreads)]

            return jsonify({
                'dates': dates,
                'actual_spread': hy_spreads,
                'implied_spread': gold_implied,
                'divergence_gap': divergence
            })

    elif chart_type == 'credit_spreads':
        hy_df = load_csv_data('high_yield_spread.csv')
        ig_df = load_csv_data('investment_grade_spread.csv')
        ccc_df = load_csv_data('ccc_spread.csv')

        if hy_df is not None:
            dates = hy_df['date'].dt.strftime('%Y-%m-%d').tolist()
            hy_data = (hy_df[hy_df.columns[1]] * 100).tolist()

            result = {
                'dates': dates,
                'hy_spread': hy_data
            }

            if ig_df is not None:
                ig_data = (ig_df[ig_df.columns[1]] * 100).tolist()
                result['ig_spread'] = ig_data

            if ccc_df is not None:
                ccc_data = (ccc_df[ccc_df.columns[1]] * 100).tolist()
                result['ccc_spread'] = ccc_data

            return jsonify(result)

    elif chart_type == 'gold_bitcoin':
        gold_df = load_csv_data('gold_price.csv')
        btc_df = load_csv_data('bitcoin_price.csv')

        if gold_df is not None and btc_df is not None:
            # Merge on date
            merged = pd.merge(gold_df, btc_df, on='date', how='inner')

            dates = merged['date'].dt.strftime('%Y-%m-%d').tolist()
            gold_data = (merged[gold_df.columns[1]] * 10).tolist()
            btc_data = merged[btc_df.columns[1]].tolist()

            return jsonify({
                'dates': dates,
                'gold': gold_data,
                'bitcoin': btc_data
            })

    elif chart_type == 'equity_indices':
        spy_df = load_csv_data('sp500_price.csv')
        qqq_df = load_csv_data('nasdaq_price.csv')
        iwm_df = load_csv_data('small_cap_price.csv')

        if spy_df is not None:
            dates = spy_df['date'].dt.strftime('%Y-%m-%d').tolist()

            result = {'dates': dates}

            if spy_df is not None:
                result['spy'] = spy_df[spy_df.columns[1]].tolist()
            if qqq_df is not None:
                result['qqq'] = qqq_df[qqq_df.columns[1]].tolist()
            if iwm_df is not None:
                result['iwm'] = iwm_df[iwm_df.columns[1]].tolist()

            return jsonify(result)

    elif chart_type == 'vix':
        vix_df = load_csv_data('vix_price.csv')

        if vix_df is not None:
            dates = vix_df['date'].dt.strftime('%Y-%m-%d').tolist()
            vix_data = vix_df[vix_df.columns[1]].tolist()

            return jsonify({
                'dates': dates,
                'vix': vix_data
            })

    return jsonify({'error': 'Chart type not found'}), 404


@app.route('/metric/<metric_name>')
def metric_detail(metric_name):
    """Individual metric detail page."""
    # Map friendly names to CSV filenames
    metric_map = {
        'divergence_gap': {'file': 'divergence_gap', 'title': 'Divergence Gap', 'unit': 'bp'},
        'hy_spread': {'file': 'high_yield_spread', 'title': 'High Yield Credit Spread', 'unit': 'bp'},
        'ig_spread': {'file': 'investment_grade_spread', 'title': 'Investment Grade Spread', 'unit': 'bp'},
        'ccc_spread': {'file': 'ccc_spread', 'title': 'CCC-Rated Spread', 'unit': 'bp'},
        'gold_price': {'file': 'gold_price', 'title': 'Gold Price', 'unit': '$'},
        'bitcoin_price': {'file': 'bitcoin_price', 'title': 'Bitcoin Price', 'unit': '$'},
        'vix': {'file': 'vix_price', 'title': 'VIX (Volatility Index)', 'unit': ''},
        'sp500': {'file': 'sp500_price', 'title': 'S&P 500', 'unit': '$'},
        'market_breadth': {'file': 'market_breadth_ratio', 'title': 'Market Breadth (RSP/SPY)', 'unit': ''}
    }

    if metric_name in metric_map:
        metric_info = metric_map[metric_name]
        return render_template('metric_detail.html',
                             metric_name=metric_name,
                             metric_file=metric_info['file'],
                             metric_title=metric_info['title'],
                             metric_unit=metric_info['unit'])
    else:
        return "Metric not found", 404


@app.route('/explorer')
def explorer():
    """Metric explorer page with dropdown selector."""
    return render_template('explorer.html')


@app.route('/api/metrics/description/<metric_name>')
def api_metric_description(metric_name):
    """API endpoint to get description for a specific metric."""
    if metric_name in METRIC_DESCRIPTIONS:
        return jsonify(METRIC_DESCRIPTIONS[metric_name])
    return jsonify({'error': 'Description not available'}), 404


@app.route('/api/metrics/list')
def api_metrics_list():
    """API endpoint to list all available metrics."""
    import os

    metrics = []
    csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])

    for filename in csv_files:
        metric_name = filename.replace('.csv', '')
        # Create friendly name from filename
        friendly_name = metric_name.replace('_', ' ').title()
        metrics.append({
            'value': metric_name,
            'label': friendly_name,
            'filename': filename
        })

    return jsonify(metrics)


@app.route('/api/recessions')
def api_recessions():
    """API endpoint to get US recession periods for chart shading."""
    filepath = DATA_DIR / 'us_recessions.csv'
    if filepath.exists():
        df = pd.read_csv(filepath)
        recessions = []
        for _, row in df.iterrows():
            recessions.append({
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'name': row['name'],
                'duration_months': int(row['duration_months']) if pd.notna(row['duration_months']) else None
            })
        return jsonify(recessions)
    return jsonify([])


@app.route('/api/metrics/<metric_name>')
def api_metric_data(metric_name):
    """API endpoint to get data for a specific metric."""

    # Special handling for divergence_gap (calculated metric)
    if metric_name == 'divergence_gap':
        gold_df = load_csv_data('gold_price.csv')
        hy_df = load_csv_data('high_yield_spread.csv')

        if gold_df is not None and hy_df is not None:
            # Merge on date
            merged = pd.merge(gold_df, hy_df, on='date', how='inner')

            # Calculate gold-implied spread and divergence gap
            gold_prices = merged['gold_price'].values
            hy_spreads = merged['high_yield_spread'].values * 100  # Convert to bp

            gold_implied = ((gold_prices / 200) ** 1.5) * 400
            divergence = gold_implied - hy_spreads

            dates = merged['date'].dt.strftime('%Y-%m-%d').tolist()
            values = divergence.tolist()

            # Calculate stats
            current_value = values[-1] if values else None
            min_value = min(values) if values else None
            max_value = max(values) if values else None
            avg_value = sum(values) / len(values) if values else None

            # Calculate change
            change_1d = None
            change_30d = None
            if len(values) >= 2:
                change_1d = values[-1] - values[-2]
            if len(values) >= 30:
                change_30d = values[-1] - values[-30]

            return jsonify({
                'dates': dates,
                'values': values,
                'column_name': 'divergence_gap',
                'stats': {
                    'current': current_value,
                    'min': min_value,
                    'max': max_value,
                    'average': avg_value,
                    'change_1d': change_1d,
                    'change_30d': change_30d
                }
            })

    # Try loading with .csv extension if not present
    filename = metric_name if metric_name.endswith('.csv') else f"{metric_name}.csv"
    df = load_csv_data(filename)

    if df is not None and len(df) > 0:
        dates = df['date'].dt.strftime('%Y-%m-%d').tolist()

        # Get the value column (second column, typically)
        value_column = df.columns[1]
        values = df[value_column].tolist()

        # Calculate stats
        current_value = values[-1] if values else None
        min_value = min(values) if values else None
        max_value = max(values) if values else None
        avg_value = sum(values) / len(values) if values else None

        # Calculate change
        change_1d = None
        change_30d = None
        if len(values) >= 2:
            change_1d = values[-1] - values[-2]
        if len(values) >= 30:
            change_30d = values[-1] - values[-30]

        return jsonify({
            'dates': dates,
            'values': values,
            'column_name': value_column,
            'stats': {
                'current': current_value,
                'min': min_value,
                'max': max_value,
                'average': avg_value,
                'change_1d': change_1d,
                'change_30d': change_30d
            }
        })

    return jsonify({'error': 'Metric not found or no data available'}), 404


def run_data_collection():
    """Run the data collection scripts in the background."""
    global reload_status

    try:
        reload_status['in_progress'] = True
        reload_status['error'] = None

        # Run market_signals.py (default 30-day lookback)
        print("Running market_signals.py...")
        result1 = subprocess.run(
            ['python', 'market_signals.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result1.returncode != 0:
            raise Exception(f"market_signals.py failed: {result1.stderr}")

        # Run divergence_analysis.py
        print("Running divergence_analysis.py...")
        result2 = subprocess.run(
            ['python', 'divergence_analysis.py'],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result2.returncode != 0:
            raise Exception(f"divergence_analysis.py failed: {result2.stderr}")

        reload_status['last_reload'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("Data reload completed successfully!")

    except Exception as e:
        reload_status['error'] = str(e)
        print(f"Data reload error: {e}")

    finally:
        reload_status['in_progress'] = False


@app.route('/api/reload-data', methods=['POST'])
def api_reload_data():
    """Trigger data reload in background."""
    global reload_status

    if reload_status['in_progress']:
        return jsonify({
            'status': 'already_running',
            'message': 'Data reload is already in progress'
        }), 409

    # Start data collection in background thread
    thread = threading.Thread(target=run_data_collection)
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'started',
        'message': 'Data reload started'
    })


@app.route('/api/reload-status')
def api_reload_status():
    """Get current reload status."""
    return jsonify({
        'in_progress': reload_status['in_progress'],
        'last_reload': reload_status['last_reload'],
        'error': reload_status['error']
    })


@app.route('/api/prediction-markets')
def api_prediction_markets():
    """Get prediction market data from Kalshi."""
    try:
        data = fetch_all_prediction_markets()
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching prediction markets: {e}")
        return jsonify({'error': str(e)}), 500


def generate_market_summary():
    """Generate a comprehensive market data summary for AI context."""
    try:
        summary_parts = []
        summary_parts.append("# CURRENT MARKET DATA SUMMARY")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append("")

        # Load all key metrics
        divergence_df = load_csv_data('divergence_gap.csv')
        hy_spread_df = load_csv_data('high_yield_spread.csv')
        ig_spread_df = load_csv_data('investment_grade_spread.csv')
        ccc_spread_df = load_csv_data('ccc_spread.csv')
        gold_df = load_csv_data('gold_price.csv')
        silver_df = load_csv_data('silver_price.csv')
        vix_df = load_csv_data('vix_price.csv')
        sp500_df = load_csv_data('sp500_price.csv')
        bitcoin_df = load_csv_data('bitcoin_price.csv')

        # Market Concentration
        smh_spy_df = load_csv_data('smh_spy_ratio.csv')
        xlk_spy_df = load_csv_data('xlk_spy_ratio.csv')
        growth_value_df = load_csv_data('growth_value_ratio.csv')
        breadth_df = load_csv_data('market_breadth_ratio.csv')

        # Yen Carry Trade
        usdjpy_df = load_csv_data('usdjpy_price.csv')
        japan_10y_df = load_csv_data('japan_10y_yield.csv')

        # Economic Indicators
        consumer_confidence_df = load_csv_data('consumer_confidence.csv')
        m2_df = load_csv_data('m2_money_supply.csv')
        cpi_df = load_csv_data('cpi.csv')

        # Helper function to get current value and stats
        def get_stats(df):
            if df is None or len(df) == 0:
                return None
            values = df[df.columns[1]].dropna()
            if len(values) == 0:
                return None
            return {
                'current': float(values.iloc[-1]),
                'min': float(values.min()),
                'max': float(values.max()),
                'mean': float(values.mean()),
                'change_1d': float(values.iloc[-1] - values.iloc[-2]) if len(values) >= 2 else 0,
                'change_1d_pct': float(((values.iloc[-1] / values.iloc[-2]) - 1) * 100) if len(values) >= 2 else 0,
                'change_5d': float(values.iloc[-1] - values.iloc[-6]) if len(values) >= 6 else 0,
                'change_5d_pct': float(((values.iloc[-1] / values.iloc[-6]) - 1) * 100) if len(values) >= 6 else 0,
                'change_30d': float(values.iloc[-1] - values.iloc[-31]) if len(values) >= 31 else 0,
                'change_30d_pct': float(((values.iloc[-1] / values.iloc[-31]) - 1) * 100) if len(values) >= 31 else 0,
                'percentile': float((values < values.iloc[-1]).sum() / len(values) * 100)
            }

        # Helper for YoY change (for monthly data)
        def get_yoy(df):
            if df is None or len(df) < 13:
                return None
            values = df[df.columns[1]].dropna()
            if len(values) < 13:
                return None
            current = float(values.iloc[-1])
            year_ago = float(values.iloc[-13])
            return ((current / year_ago) - 1) * 100 if year_ago != 0 else 0

        # Divergence Gap
        if divergence_df is not None:
            stats = get_stats(divergence_df)
            if stats:
                summary_parts.append("## DIVERGENCE GAP (Gold-Implied Spread minus Actual HY Spread)")
                summary_parts.append(f"Current: {stats['current']:.0f} bp ({stats['percentile']:.1f}th percentile)")
                summary_parts.append(f"5-Day Change: {stats['change_5d']:+.0f} bp | 30-Day Change: {stats['change_30d']:+.0f} bp")
                summary_parts.append(f"Historical Range: {stats['min']:.0f} - {stats['max']:.0f} bp")
                summary_parts.append("")

        # Credit Spreads Section
        summary_parts.append("## CREDIT SPREADS")
        if hy_spread_df is not None:
            stats = get_stats(hy_spread_df)
            if stats:
                summary_parts.append(f"High Yield (HY): {stats['current']*100:.0f} bp ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if ig_spread_df is not None:
            stats = get_stats(ig_spread_df)
            if stats:
                summary_parts.append(f"Investment Grade (IG): {stats['current']*100:.0f} bp ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if ccc_spread_df is not None:
            stats = get_stats(ccc_spread_df)
            if stats:
                summary_parts.append(f"CCC-rated: {stats['current']*100:.0f} bp ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        summary_parts.append("")

        # Safe Havens Section
        summary_parts.append("## SAFE HAVEN ASSETS")
        if gold_df is not None:
            stats = get_stats(gold_df)
            if stats:
                summary_parts.append(f"Gold (GLD×10): ${stats['current']*10:,.0f}/oz equiv ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if silver_df is not None:
            stats = get_stats(silver_df)
            if stats:
                summary_parts.append(f"Silver (SLV): ${stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if bitcoin_df is not None:
            stats = get_stats(bitcoin_df)
            if stats:
                summary_parts.append(f"Bitcoin: ${stats['current']:,.0f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        summary_parts.append("")

        # Equity Markets
        summary_parts.append("## EQUITY MARKETS")
        if sp500_df is not None:
            stats = get_stats(sp500_df)
            if stats:
                summary_parts.append(f"S&P 500: ${stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if vix_df is not None:
            stats = get_stats(vix_df)
            if stats:
                summary_parts.append(f"VIX (Fear Index): {stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        summary_parts.append("")

        # Market Concentration
        summary_parts.append("## MARKET CONCENTRATION (Higher = More AI/Tech Concentration)")
        if smh_spy_df is not None:
            stats = get_stats(smh_spy_df)
            if stats:
                summary_parts.append(f"Semiconductor/SPY: {stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if xlk_spy_df is not None:
            stats = get_stats(xlk_spy_df)
            if stats:
                summary_parts.append(f"Tech Sector/SPY: {stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if growth_value_df is not None:
            stats = get_stats(growth_value_df)
            if stats:
                summary_parts.append(f"Growth/Value: {stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        if breadth_df is not None:
            stats = get_stats(breadth_df)
            if stats:
                summary_parts.append(f"Market Breadth (SPY/RSP): {stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
        summary_parts.append("")

        # Yen Carry Trade
        summary_parts.append("## YEN CARRY TRADE MONITOR")
        if usdjpy_df is not None:
            stats = get_stats(usdjpy_df)
            if stats:
                summary_parts.append(f"USD/JPY: {stats['current']:.2f} ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d_pct']:+.1f}%")
                summary_parts.append("  (Lower = stronger yen = carry trade unwinding risk)")
        if japan_10y_df is not None:
            stats = get_stats(japan_10y_df)
            if stats:
                summary_parts.append(f"Japan 10Y Yield: {stats['current']:.2f}% ({stats['percentile']:.1f}th %ile)")
                summary_parts.append("  (Rising yields = BOJ tightening = carry trade at risk)")
        summary_parts.append("")

        # Economic Indicators
        summary_parts.append("## ECONOMIC INDICATORS (Monthly Data)")
        if consumer_confidence_df is not None:
            stats = get_stats(consumer_confidence_df)
            if stats:
                summary_parts.append(f"Consumer Confidence (UMich): {stats['current']:.1f} ({stats['percentile']:.1f}th %ile)")
                summary_parts.append("  (<70 = recession territory, >100 = strong optimism)")
        if m2_df is not None:
            stats = get_stats(m2_df)
            yoy = get_yoy(m2_df)
            if stats:
                summary_parts.append(f"M2 Money Supply: ${stats['current']/1000:.2f} trillion | YoY: {yoy:+.1f}%")
                summary_parts.append("  (Negative YoY = highly unusual, deflationary)")
        if cpi_df is not None:
            stats = get_stats(cpi_df)
            yoy = get_yoy(cpi_df)
            if stats:
                summary_parts.append(f"CPI Index: {stats['current']:.1f} | YoY Inflation: {yoy:+.1f}%")
                summary_parts.append("  (Fed target ~2%, >5% = high inflation)")
        summary_parts.append("")

        # Prediction Markets
        try:
            prediction_data = fetch_all_prediction_markets()
            summary_parts.append("## PREDICTION MARKETS (Kalshi)")
            if prediction_data.get('recession') and prediction_data['recession'].get('probability'):
                prob = prediction_data['recession']['probability'] * 100
                summary_parts.append(f"Recession Probability (2026): {prob:.0f}%")
            if prediction_data.get('large_rate_cut') and prediction_data['large_rate_cut'].get('probability'):
                prob = prediction_data['large_rate_cut']['probability'] * 100
                summary_parts.append(f"Large Fed Rate Cut (>25bp) Probability: {prob:.0f}%")
            summary_parts.append("")
        except Exception:
            pass  # Skip prediction markets if unavailable

        return "\n".join(summary_parts)

    except Exception as e:
        print(f"Error generating market summary: {e}")
        return "Market data summary unavailable."


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat messages with OpenAI API."""
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Check if OpenAI API key is configured
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({
                'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'
            }), 500

        # Generate market data summary for context
        market_summary = generate_market_summary()

        # System message with context
        system_message = f"""You are a financial markets expert assistant helping users understand market divergence data.

You have access to current market data showing an unprecedented divergence between safe havens (gold) and credit markets.

CURRENT MARKET DATA:
{market_summary}

KEY CONTEXT:
- The "Divergence Gap" measures the difference between what gold prices imply credit spreads should be versus actual spreads
- A large divergence suggests one market is catastrophically wrong
- Gold at 90+ percentile = pricing in crisis
- Credit spreads at <10 percentile = pricing in no risk
- This setup is historically unprecedented

YOUR ROLE:
- Help users understand what the numbers mean
- Explain market dynamics and risks
- Answer questions about specific metrics
- Provide context about historical precedents
- Discuss possible scenarios and outcomes
- Be objective and data-driven
- Don't give specific investment advice (no "you should buy/sell X")
- Be conversational and helpful

Be concise but thorough. Focus on education and understanding."""

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=800
        )

        ai_message = response.choices[0].message.content

        return jsonify({
            'message': ai_message,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
