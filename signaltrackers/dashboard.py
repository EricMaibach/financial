#!/usr/bin/env python3
"""
Market Divergence Dashboard
A comprehensive web dashboard for tracking the historic market divergence.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import subprocess
import threading
import os
import atexit
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from kalshi_data import fetch_all_prediction_markets
from web_search import SEARCH_FUNCTION_DEFINITION, execute_search_function, is_tavily_configured
from ai_summary import (
    generate_daily_summary, get_summary_for_display, get_latest_summary,
    generate_crypto_summary, get_crypto_summary_for_display,
    generate_equity_summary, get_equity_summary_for_display,
    generate_rates_summary, get_rates_summary_for_display,
    generate_dollar_summary, get_dollar_summary_for_display
)
from metric_tools import (
    LIST_METRICS_FUNCTION,
    GET_METRIC_FUNCTION,
    execute_metric_function
)
from portfolio import (
    load_portfolio, save_portfolio, add_allocation, update_allocation,
    delete_allocation, validate_allocation_total, validate_symbol,
    get_portfolio_with_prices, get_portfolio_summary_for_ai,
    # Database-backed functions for multi-user mode
    db_load_portfolio, db_add_allocation, db_update_allocation,
    db_delete_allocation, db_validate_allocation_total,
    db_get_portfolio_with_prices, db_get_portfolio_summary_for_ai
)
from config import get_config
from extensions import init_extensions, db, limiter, csrf
from models import User, UserSettings

app = Flask(__name__)

# Load configuration
app.config.from_object(get_config())

# Initialize extensions (database, login manager, CSRF, rate limiting)
init_extensions(app)

# Initialize OpenAI client (only if API key is available)
openai_api_key = os.environ.get('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Track data reload status
reload_status = {
    'in_progress': False,
    'last_reload': None,
    'error': None
}

DATA_DIR = Path("data")

# Background scheduler for automatic data refresh
scheduler = None


def init_scheduler():
    """Initialize background scheduler for automatic data refresh."""
    global scheduler

    scheduler = BackgroundScheduler()

    # Daily refresh at 5:30 PM Eastern, Monday-Friday
    eastern = pytz.timezone('US/Eastern')
    scheduler.add_job(
        scheduled_data_refresh,
        CronTrigger(hour=17, minute=30, day_of_week='mon-fri', timezone=eastern),
        id='daily_refresh',
        replace_existing=True,
        name='Daily Data Refresh'
    )

    scheduler.start()
    print(f"Scheduler started. Next refresh: {scheduler.get_job('daily_refresh').next_run_time}")

    # Ensure scheduler shuts down on exit
    atexit.register(lambda: scheduler.shutdown() if scheduler else None)

    return scheduler


def scheduled_data_refresh():
    """Background job to refresh all data and AI briefings."""
    print(f"[{datetime.now()}] Starting scheduled data refresh...")

    # Use the existing run_data_collection function
    # which handles all data collection and AI summary generation
    run_data_collection()

    print(f"[{datetime.now()}] Scheduled data refresh completed.")


def get_scheduler_status():
    """Get current scheduler status for API endpoint."""
    if scheduler is None:
        return {
            'enabled': False,
            'message': 'Scheduler not initialized'
        }

    job = scheduler.get_job('daily_refresh')
    if job:
        return {
            'enabled': True,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'job_name': job.name,
            'schedule': 'Daily at 5:30 PM Eastern (Mon-Fri)'
        }

    return {
        'enabled': True,
        'next_run': None,
        'message': 'No scheduled job found'
    }


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
    'iwm_spy_ratio': {
        'what': 'Russell 2000 Small Cap (IWM) divided by S&P 500 (SPY), scaled to 100. Measures small cap vs large cap relative performance.',
        'why': 'Small caps are more economically sensitive. Rising ratio = risk appetite, economic optimism. Falling ratio = flight to quality, economic concern.',
        'watch': 'Low ratio = large caps dominating (current environment). Rising ratio = small cap rotation, often bullish for broader economy. Watch for divergence from SPY.'
    },
    'financials_sector_price': {
        'what': 'Financial Select Sector ETF (XLF) - tracks major banks, insurance, and financial services companies.',
        'why': 'Banks are sensitive to yield curve, credit conditions, and economic health. Often leads the market during recoveries.',
        'watch': 'Strength = economic optimism, steepening yield curve. Weakness = credit concerns, recession fears. Compare to broader market for rotation signals.'
    },
    'energy_sector_price': {
        'what': 'Energy Select Sector ETF (XLE) - tracks major oil, gas, and energy equipment companies.',
        'why': 'Energy sector performance reflects oil prices and inflation expectations. Counter-cyclical to tech in some environments.',
        'watch': 'Strength = inflation hedge, commodity cycle. Weakness = deflation fears or oversupply. Often moves opposite to growth stocks.'
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
    },
    'yield_curve_10y2y': {
        'what': '10-Year Treasury yield minus 2-Year Treasury yield. The classic yield curve spread used to predict recessions.',
        'why': 'When short-term rates exceed long-term rates (inversion), it signals markets expect economic weakness ahead. Has preceded every US recession since 1970.',
        'watch': 'Positive spread = normal (economy healthy). Negative (inverted) = recession warning (typically 12-18 months ahead). Re-steepening after inversion often signals recession is imminent.'
    },
    'yield_curve_10y3m': {
        'what': '10-Year Treasury yield minus 3-Month Treasury yield. The Fed\'s preferred yield curve measure for recession prediction.',
        'why': 'More directly reflects Fed policy vs market expectations. 3-month rate is tightly tied to Fed Funds rate, while 10-year reflects growth/inflation expectations.',
        'watch': 'Inversion here is considered more significant by economists. Extended inversion (>3 months) is a stronger recession signal than brief inversions.'
    },
    'initial_claims': {
        'what': 'Weekly count of new unemployment insurance filings. Leading indicator of labor market health.',
        'why': 'First signal of labor market stress. Rising claims = companies laying off workers. Tends to spike quickly at recession onset.',
        'watch': 'Current healthy range: 200-250k. Warning zone: 250-300k. Recession signal: >300k sustained. Crisis: >400k. Watch for trend, not single weeks.'
    },
    'continuing_claims': {
        'what': 'Total number of people receiving unemployment benefits. Lagging confirmation of labor market conditions.',
        'why': 'Shows how long people stay unemployed. Rising continuing claims = harder to find new jobs = weakening economy.',
        'watch': 'Confirms initial claims trends. Sustained rise indicates recession has begun. Watch for divergence from initial claims (longer unemployment duration).'
    },
    'fed_balance_sheet': {
        'what': 'Total assets held by the Federal Reserve in billions of dollars. Includes Treasury securities, mortgage-backed securities, and other assets acquired through QE programs.',
        'why': 'Primary measure of Fed liquidity injection. Balance sheet expansion (QE) = adding liquidity = bullish for risk assets. Quantitative tightening (QT) = draining liquidity = headwind for markets.',
        'watch': 'Peak was ~$9 trillion in 2022. Currently shrinking via QT. Sharp expansion = crisis response. Correlation with Bitcoin and risk assets is strong.'
    },
    'reverse_repo': {
        'what': 'Overnight Reverse Repurchase Agreement Facility usage in billions. Money market funds park excess cash at the Fed overnight.',
        'why': 'Measures excess liquidity in the system. High RRP = too much cash chasing too few safe assets. Declining RRP = liquidity being absorbed by Treasury issuance or markets.',
        'watch': 'Peak was ~$2.5 trillion. Declining = liquidity draining from system. Near zero = potential liquidity stress. Rapid drop can signal tightening conditions.'
    },
    'nfci': {
        'what': 'Chicago Fed National Financial Conditions Index. Weighted average of 105 financial indicators including risk, credit, and leverage measures.',
        'why': 'Comprehensive measure of financial stress. Negative values = loose conditions (below average tightness). Positive values = tight conditions (stress building).',
        'watch': 'Zero = average conditions. >0.5 = tightening, watch for stress. <-0.5 = very loose, risk-on. Spikes precede or coincide with market stress events.'
    },
    'fear_greed_index': {
        'what': 'Alternative.me Crypto Fear & Greed Index (0-100 scale). Composite of volatility, momentum, social media, surveys, and dominance metrics.',
        'why': 'Sentiment indicator for crypto markets. Extreme fear often marks bottoms, extreme greed marks tops. Contrarian signal.',
        'watch': '0-25 = Extreme Fear (potential buying opportunity). 26-46 = Fear. 47-54 = Neutral. 55-75 = Greed. 76-100 = Extreme Greed (potential top).'
    },
    'btc_gold_ratio': {
        'what': 'Bitcoin price divided by gold price (ounces of gold per BTC). Measures Bitcoin\'s value relative to the traditional store of value.',
        'why': 'Compares two competing store-of-value assets. Rising ratio = Bitcoin outperforming gold. Falling ratio = gold outperforming Bitcoin.',
        'watch': 'Ratio expansion during risk-on periods, contraction during risk-off. Track alongside Fed liquidity - both assets respond to monetary policy.'
    },
    'real_yield_10y': {
        'what': '10-Year Treasury Inflation-Protected Securities (TIPS) yield. Represents the real (inflation-adjusted) return on 10-year government bonds.',
        'why': 'Key driver of gold prices - gold has strong inverse correlation with real yields. When real yields fall, gold becomes more attractive.',
        'watch': 'Rising real yields = headwind for gold. Falling real yields = tailwind for gold. Watch for Fed policy shifts affecting real rates.'
    },
    'breakeven_inflation_10y': {
        'what': '10-Year breakeven inflation rate (nominal Treasury yield minus TIPS yield). Market\'s expectation for average inflation over next 10 years.',
        'why': 'Measures inflation expectations. Higher breakevens = market expects more inflation, which can support gold prices.',
        'watch': 'Rising breakevens often coincide with gold rallies. Track alongside CPI and Fed inflation targets (2%).'
    },
    'gdx_gld_ratio': {
        'what': 'Gold miners ETF (GDX) divided by gold price ETF (GLD). Measures how miners are performing relative to gold itself.',
        'why': 'Miners have leverage to gold moves. When miners lead gold higher, it\'s bullish. When miners lag, it can signal exhaustion.',
        'watch': 'Rising ratio = miners outperforming (bullish), falling ratio = miners lagging (bearish divergence). Miners often lead gold at turning points.'
    },
    'treasury_10y': {
        'what': '10-Year Treasury Constant Maturity Rate (DGS10). The nominal yield on 10-year US government bonds.',
        'why': 'Benchmark risk-free rate for the US. Nominal yield = Real yield + Breakeven inflation. Key reference for all financial assets.',
        'watch': 'Rising yields can pressure gold and growth stocks. Compare to real yields to understand inflation expectations.'
    },
    'eurusd_price': {
        'what': 'EUR/USD exchange rate - how many US Dollars per 1 Euro. The most traded currency pair in the world.',
        'why': 'Primary gauge of dollar strength vs Europe. Driven by Fed/ECB policy divergence, growth differentials, and risk appetite. EUR is ~57% of DXY.',
        'watch': 'Rising EUR/USD = dollar weakening vs euro. Above 1.10 = euro strength. Below 1.05 = dollar strength. Rate differentials (US-Germany 10Y) are key driver.'
    },
    'germany_10y_yield': {
        'what': 'Germany 10-Year Government Bond (Bund) yield. The benchmark risk-free rate for the Eurozone.',
        'why': 'ECB policy gauge. Germany/US rate differential drives EUR/USD. Rising Bund yields = ECB tightening, supports euro. Falling = ECB dovish, weakens euro.',
        'watch': 'Negative yields (pre-2022) = extreme monetary accommodation. Positive and rising = policy normalization. Compare to US 10Y for rate differential.'
    },
    'us_japan_10y_spread': {
        'what': 'US 10-Year Treasury yield minus Japan 10-Year Government Bond yield. The rate differential that drives the yen carry trade.',
        'why': 'The carry trade: borrow cheap in yen, invest in higher-yielding USD assets. Wider spread = more incentive for carry trade = yen weakness, supports USD/JPY.',
        'watch': 'Spread >3% = strong carry trade incentive. Spread narrowing (Japan yields rising or US falling) = carry unwind risk, supports yen. BOJ policy is key.'
    },
    'us_germany_10y_spread': {
        'what': 'US 10-Year Treasury yield minus Germany 10-Year Bund yield. The rate differential that drives EUR/USD flows.',
        'why': 'Wider spread = US yields more attractive = capital flows to USD = EUR/USD falls. Narrowing spread = euro support as European yields become more competitive.',
        'watch': 'Spread >1.5% typically supports dollar. Spread narrowing often coincides with EUR/USD strength. Watch Fed vs ECB policy trajectory.'
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
        'high_yield_spread': {'display': 'abs', 'unit': 'bp', 'name': 'HY Spread', 'link': '/explorer?metric=high_yield_spread', 'multiplier': 100},
        'investment_grade_spread': {'display': 'abs', 'unit': 'bp', 'name': 'IG Spread', 'link': '/explorer?metric=investment_grade_spread', 'multiplier': 100},
        'ccc_spread': {'display': 'abs', 'unit': 'bp', 'name': 'CCC Spread', 'link': '/explorer?metric=ccc_spread', 'multiplier': 100},

        # Prices - use % change
        'gold_price': {'display': 'pct', 'unit': '%', 'name': 'Gold', 'link': '/explorer?metric=gold_price'},
        'silver_price': {'display': 'pct', 'unit': '%', 'name': 'Silver', 'link': '/explorer?metric=silver_price'},
        'bitcoin_price': {'display': 'pct', 'unit': '%', 'name': 'Bitcoin', 'link': '/explorer?metric=bitcoin_price'},
        'sp500_price': {'display': 'pct', 'unit': '%', 'name': 'S&P 500', 'link': '/explorer?metric=sp500_price'},
        'nasdaq_price': {'display': 'pct', 'unit': '%', 'name': 'Nasdaq', 'link': '/explorer?metric=nasdaq_price'},
        'vix_price': {'display': 'pct', 'unit': '%', 'name': 'VIX', 'link': '/explorer?metric=vix_price'},
        'oil_price': {'display': 'pct', 'unit': '%', 'name': 'Oil', 'link': '/explorer?metric=oil_price'},
        'commodities_price': {'display': 'pct', 'unit': '%', 'name': 'Commodities', 'link': '/explorer?metric=commodities_price'},
        'gold_miners_price': {'display': 'pct', 'unit': '%', 'name': 'Gold Miners', 'link': '/explorer?metric=gold_miners_price'},
        'small_cap_price': {'display': 'pct', 'unit': '%', 'name': 'Small Caps', 'link': '/explorer?metric=small_cap_price'},
        'tech_sector_price': {'display': 'pct', 'unit': '%', 'name': 'Tech Sector', 'link': '/explorer?metric=tech_sector_price'},
        'semiconductor_price': {'display': 'pct', 'unit': '%', 'name': 'Semiconductors', 'link': '/explorer?metric=semiconductor_price'},
        'financials_sector_price': {'display': 'pct', 'unit': '%', 'name': 'Financials', 'link': '/explorer?metric=financials_sector_price'},
        'energy_sector_price': {'display': 'pct', 'unit': '%', 'name': 'Energy', 'link': '/explorer?metric=energy_sector_price'},
        'treasury_20yr_price': {'display': 'pct', 'unit': '%', 'name': 'Treasury 20Y', 'link': '/explorer?metric=treasury_20yr_price'},
        'dollar_index_price': {'display': 'pct', 'unit': '%', 'name': 'Dollar Index', 'link': '/explorer?metric=dollar_index_price'},
        'usdjpy_price': {'display': 'pct', 'unit': '%', 'name': 'USD/JPY', 'link': '/explorer?metric=usdjpy_price'},

        # Ratios - use % change
        'gold_silver_ratio': {'display': 'pct', 'unit': '%', 'name': 'Gold/Silver Ratio', 'link': '/explorer?metric=gold_silver_ratio'},
        'smh_spy_ratio': {'display': 'pct', 'unit': '%', 'name': 'Semiconductor/SPY', 'link': '/explorer?metric=smh_spy_ratio'},
        'xlk_spy_ratio': {'display': 'pct', 'unit': '%', 'name': 'Tech/SPY', 'link': '/explorer?metric=xlk_spy_ratio'},
        'growth_value_ratio': {'display': 'pct', 'unit': '%', 'name': 'Growth/Value', 'link': '/explorer?metric=growth_value_ratio'},
        'iwm_spy_ratio': {'display': 'pct', 'unit': '%', 'name': 'Small/Large Cap', 'link': '/explorer?metric=iwm_spy_ratio'},
        'market_breadth_ratio': {'display': 'pct', 'unit': '%', 'name': 'Market Breadth', 'link': '/explorer?metric=market_breadth_ratio'},

        # Yields - use absolute change
        'japan_10y_yield': {'display': 'abs', 'unit': '%', 'name': 'Japan 10Y Yield', 'link': '/explorer?metric=japan_10y_yield', 'multiplier': 1},
        'real_yield_proxy': {'display': 'pct', 'unit': '%', 'name': 'Real Yield Proxy', 'link': '/explorer?metric=real_yield_proxy'},
        'treasury_10y': {'display': 'abs', 'unit': '%', 'name': '10Y Treasury', 'link': '/explorer?metric=treasury_10y', 'multiplier': 1},

        # ETF spreads
        'hyg_treasury_spread': {'display': 'pct', 'unit': '%', 'name': 'HYG-Treasury Spread', 'link': '/explorer?metric=hyg_treasury_spread'},
        'lqd_treasury_spread': {'display': 'pct', 'unit': '%', 'name': 'LQD-Treasury Spread', 'link': '/explorer?metric=lqd_treasury_spread'},

        # Economic Indicators - use % change
        'consumer_confidence': {'display': 'pct', 'unit': '%', 'name': 'Consumer Confidence', 'link': '/explorer?metric=consumer_confidence'},
        'm2_money_supply': {'display': 'pct', 'unit': '%', 'name': 'M2 Money Supply', 'link': '/explorer?metric=m2_money_supply'},
        'cpi': {'display': 'pct', 'unit': '%', 'name': 'CPI (Inflation)', 'link': '/explorer?metric=cpi'},

        # Yield Curve - use absolute change (spread in %)
        'yield_curve_10y2y': {'display': 'abs', 'unit': '%', 'name': '10Y-2Y Yield Curve', 'link': '/explorer?metric=yield_curve_10y2y', 'multiplier': 1},
        'yield_curve_10y3m': {'display': 'abs', 'unit': '%', 'name': '10Y-3M Yield Curve', 'link': '/explorer?metric=yield_curve_10y3m', 'multiplier': 1},

        # Labor Market - use % change
        'initial_claims': {'display': 'pct', 'unit': '%', 'name': 'Initial Claims', 'link': '/explorer?metric=initial_claims'},
        'continuing_claims': {'display': 'pct', 'unit': '%', 'name': 'Continuing Claims', 'link': '/explorer?metric=continuing_claims'},

        # Fed Liquidity & Financial Conditions - use % change
        'fed_balance_sheet': {'display': 'pct', 'unit': '%', 'name': 'Fed Balance Sheet', 'link': '/explorer?metric=fed_balance_sheet'},
        'reverse_repo': {'display': 'pct', 'unit': '%', 'name': 'Reverse Repo', 'link': '/explorer?metric=reverse_repo'},
        'nfci': {'display': 'abs', 'unit': 'index', 'name': 'NFCI', 'link': '/explorer?metric=nfci', 'multiplier': 1},

        # Crypto Sentiment
        'fear_greed_index': {'display': 'abs', 'unit': 'pts', 'name': 'Crypto Fear/Greed', 'link': '/explorer?metric=fear_greed_index', 'multiplier': 1},
        'btc_gold_ratio': {'display': 'pct', 'unit': '%', 'name': 'BTC/Gold Ratio', 'link': '/explorer?metric=btc_gold_ratio'},

        # Real Yields & Inflation (Gold Drivers)
        'real_yield_10y': {'display': 'abs', 'unit': '%', 'name': '10Y Real Yield', 'link': '/explorer?metric=real_yield_10y', 'multiplier': 1},
        'breakeven_inflation_10y': {'display': 'abs', 'unit': '%', 'name': '10Y Breakeven', 'link': '/explorer?metric=breakeven_inflation_10y', 'multiplier': 1},
        'gdx_gld_ratio': {'display': 'pct', 'unit': '%', 'name': 'GDX/GLD Ratio', 'link': '/explorer?metric=gdx_gld_ratio'},
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
                    'link': '/explorer?metric=divergence_gap',
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


# =============================================================================
# Authentication Routes
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('This account has been deactivated.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=bool(remember))
            user.update_last_login()
            db.session.commit()

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))

        flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        # Validation
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        elif len(username) > 80:
            errors.append('Username must be less than 80 characters.')
        elif User.query.filter_by(username=username).first():
            errors.append('Username already exists.')

        if not email:
            errors.append('Email is required.')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        elif not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter.')
        elif not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one number.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)

        # Create default settings
        settings = UserSettings(user=user, ai_provider='openai')

        db.session.add(user)
        db.session.add(settings)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    """Log out current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# =============================================================================
# Page Routes
# =============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/credit')
def credit():
    """Credit markets page - redirects to rates (credit merged into rates)."""
    return redirect('/rates')


@app.route('/equity')
def equity():
    """Equity markets page."""
    return render_template('equity.html')


@app.route('/safe-havens')
def safe_havens():
    """Safe havens page."""
    return render_template('safe_havens.html')


@app.route('/divergence')
def divergence():
    """Divergence gap analysis page."""
    return render_template('divergence.html')


@app.route('/crypto')
def crypto():
    """Crypto/Bitcoin analysis page."""
    return render_template('crypto.html')


@app.route('/rates')
def rates():
    """Rates & Yield Curve page."""
    return render_template('rates.html')


@app.route('/dollar')
def dollar():
    """Dollar & Currency page."""
    return render_template('dollar.html')


@app.route('/portfolio')
@login_required
def portfolio():
    """Personal portfolio tracking page."""
    return render_template('portfolio.html')


@app.route('/settings')
@login_required
def settings():
    """User settings page."""
    from services.ai_service import check_user_ai_configured
    return render_template('settings.html', check_user_ai_configured=check_user_ai_configured)


@app.route('/settings/api-keys', methods=['POST'])
@login_required
def settings_update_api_keys():
    """Update user's AI API keys."""
    ai_provider = request.form.get('ai_provider', 'openai')
    openai_key = request.form.get('openai_key', '').strip()
    anthropic_key = request.form.get('anthropic_key', '').strip()

    # Validate provider
    if ai_provider not in ['openai', 'anthropic']:
        ai_provider = 'openai'

    # Get or create user settings
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user=current_user)
        db.session.add(settings)

    # Update provider
    settings.ai_provider = ai_provider

    # Update keys only if provided (don't clear existing keys if empty)
    if openai_key:
        try:
            settings.set_openai_key(openai_key)
        except Exception as e:
            flash(f'Error saving OpenAI key: {e}', 'danger')
            return redirect(url_for('settings'))

    if anthropic_key:
        try:
            settings.set_anthropic_key(anthropic_key)
        except Exception as e:
            flash(f'Error saving Anthropic key: {e}', 'danger')
            return redirect(url_for('settings'))

    db.session.commit()
    flash('Settings saved successfully!', 'success')
    return redirect(url_for('settings'))


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
    """Redirect old metric detail URLs to the explorer page."""
    # Map old friendly names to the actual metric names used by explorer
    metric_map = {
        'divergence_gap': 'divergence_gap',
        'hy_spread': 'high_yield_spread',
        'ig_spread': 'investment_grade_spread',
        'ccc_spread': 'ccc_spread',
        'gold_price': 'gold_price',
        'bitcoin_price': 'bitcoin_price',
        'vix': 'vix_price',
        'sp500': 'sp500_price',
        'market_breadth': 'market_breadth_ratio'
    }

    # Get the actual metric name for explorer
    explorer_metric = metric_map.get(metric_name, metric_name)
    return redirect(f'/explorer?metric={explorer_metric}')


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

    # Add calculated metrics first (not stored as CSV files)
    calculated_metrics = [
        {'value': 'divergence_gap', 'label': 'Divergence Gap', 'filename': None, 'calculated': True},
    ]
    metrics.extend(calculated_metrics)

    # Add CSV-based metrics
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

    # Metric name aliases - map common/short names to actual CSV file names
    metric_aliases = {
        'cpi_yoy': 'cpi',
        'hy_spread': 'high_yield_spread',
        'ig_spread': 'investment_grade_spread',
        'vix': 'vix_price',
        'sp500': 'sp500_price',
        'market_breadth': 'market_breadth_ratio',
    }

    # Apply alias if one exists
    metric_name = metric_aliases.get(metric_name, metric_name)

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

        # Generate AI summary after successful data reload
        print("Generating AI daily summary...")
        try:
            market_summary = generate_market_summary()
            top_movers = calculate_top_movers(5)
            result = generate_daily_summary(market_summary, top_movers)
            if result['success']:
                print("AI summary generated successfully!")
            else:
                print(f"AI summary generation failed: {result['error']}")
        except Exception as summary_error:
            print(f"AI summary error (non-fatal): {summary_error}")

        # Generate Crypto AI summary
        print("Generating Crypto AI summary...")
        try:
            crypto_summary_data = generate_crypto_market_summary()
            crypto_result = generate_crypto_summary(crypto_summary_data)
            if crypto_result['success']:
                print("Crypto AI summary generated successfully!")
            else:
                print(f"Crypto AI summary generation failed: {crypto_result['error']}")
        except Exception as crypto_summary_error:
            print(f"Crypto AI summary error (non-fatal): {crypto_summary_error}")

        # Generate Equity AI summary
        print("Generating Equity Markets AI summary...")
        try:
            equity_summary_data = generate_equity_market_summary()
            equity_result = generate_equity_summary(equity_summary_data)
            if equity_result['success']:
                print("Equity AI summary generated successfully!")
            else:
                print(f"Equity AI summary generation failed: {equity_result['error']}")
        except Exception as equity_summary_error:
            print(f"Equity AI summary error (non-fatal): {equity_summary_error}")

        # Generate Rates AI summary
        print("Generating Rates & Yield Curve AI summary...")
        try:
            rates_summary_data = generate_rates_market_summary()
            rates_result = generate_rates_summary(rates_summary_data)
            if rates_result['success']:
                print("Rates AI summary generated successfully!")
            else:
                print(f"Rates AI summary generation failed: {rates_result['error']}")
        except Exception as rates_summary_error:
            print(f"Rates AI summary error (non-fatal): {rates_summary_error}")

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


@app.route('/api/scheduler-status')
def api_scheduler_status():
    """Get current scheduler status including next refresh time."""
    status = get_scheduler_status()
    status['last_reload'] = reload_status['last_reload']
    return jsonify(status)


@app.route('/api/prediction-markets')
def api_prediction_markets():
    """Get prediction market data from Kalshi."""
    try:
        data = fetch_all_prediction_markets()
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching prediction markets: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-summary')
def api_ai_summary():
    """Get the current AI-generated daily summary."""
    summary = get_summary_for_display()
    if summary:
        return jsonify(summary)
    return jsonify({
        'error': 'No summary available',
        'message': 'Run a data reload to generate a summary'
    }), 404


@app.route('/api/ai-summary/generate', methods=['POST'])
def api_generate_summary():
    """Manually trigger AI summary generation."""
    try:
        market_summary = generate_market_summary()
        top_movers = calculate_top_movers(5)
        result = generate_daily_summary(market_summary, top_movers)

        if result['success']:
            return jsonify({
                'status': 'success',
                'summary': result['summary']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/crypto-summary')
def api_crypto_summary():
    """Get the current AI-generated crypto/Bitcoin summary."""
    summary = get_crypto_summary_for_display()
    if summary:
        return jsonify(summary)
    return jsonify({
        'error': 'No crypto summary available',
        'message': 'Run a data reload to generate a summary'
    }), 404


@app.route('/api/crypto-summary/generate', methods=['POST'])
def api_generate_crypto_summary():
    """Manually trigger crypto AI summary generation."""
    try:
        crypto_summary_data = generate_crypto_market_summary()
        result = generate_crypto_summary(crypto_summary_data)

        if result['success']:
            return jsonify({
                'status': 'success',
                'summary': result['summary']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/equity-summary')
def api_equity_summary():
    """Get the current AI-generated equity markets summary."""
    summary = get_equity_summary_for_display()
    if summary:
        return jsonify(summary)
    return jsonify({
        'error': 'No equity summary available',
        'message': 'Run a data reload to generate a summary'
    }), 404


@app.route('/api/equity-summary/generate', methods=['POST'])
def api_generate_equity_summary():
    """Manually trigger equity AI summary generation."""
    try:
        equity_summary_data = generate_equity_market_summary()
        result = generate_equity_summary(equity_summary_data)

        if result['success']:
            return jsonify({
                'status': 'success',
                'summary': result['summary']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/rates-summary')
def api_rates_summary():
    """Get the current AI-generated rates & yield curve summary."""
    summary = get_rates_summary_for_display()
    if summary:
        return jsonify(summary)
    return jsonify({
        'error': 'No rates summary available',
        'message': 'Run a data reload to generate a summary'
    }), 404


@app.route('/api/rates-summary/generate', methods=['POST'])
def api_generate_rates_summary():
    """Manually trigger rates AI summary generation."""
    try:
        rates_summary_data = generate_rates_market_summary()
        result = generate_rates_summary(rates_summary_data)

        if result['success']:
            return jsonify({
                'status': 'success',
                'summary': result['summary']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/dollar-summary')
def api_dollar_summary():
    """Get the current dollar AI summary."""
    summary = get_dollar_summary_for_display()
    if summary:
        return jsonify(summary)
    return jsonify({
        'error': 'No dollar summary available',
        'message': 'Run a data reload to generate a summary'
    }), 404


@app.route('/api/dollar-summary/generate', methods=['POST'])
def api_generate_dollar_summary():
    """Manually trigger dollar AI summary generation."""
    try:
        dollar_summary_data = generate_dollar_market_summary()
        result = generate_dollar_summary(dollar_summary_data)

        if result['success']:
            return jsonify({
                'status': 'success',
                'summary': result['summary']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# Portfolio API Endpoints
# ============================================================================

@app.route('/api/portfolio')
@login_required
def api_portfolio_get():
    """Get all portfolio allocations with current prices for current user."""
    try:
        portfolio_data = db_get_portfolio_with_prices(current_user.id)
        return jsonify(portfolio_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio', methods=['POST'])
@csrf.exempt
@login_required
def api_portfolio_add():
    """Add a new allocation to the portfolio."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        asset_type = data.get('asset_type')
        symbol = data.get('symbol')
        name = data.get('name')
        percentage = data.get('percentage')

        if not asset_type or not name or percentage is None:
            return jsonify({'error': 'Missing required fields: asset_type, name, percentage'}), 400

        try:
            percentage = float(percentage)
        except (ValueError, TypeError):
            return jsonify({'error': 'Percentage must be a number'}), 400

        result = db_add_allocation(current_user.id, asset_type, symbol, name, percentage)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/<allocation_id>', methods=['PUT'])
@csrf.exempt
@login_required
def api_portfolio_update(allocation_id):
    """Update an existing allocation."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        percentage = data.get('percentage')
        name = data.get('name')
        symbol = data.get('symbol')

        if percentage is not None:
            try:
                percentage = float(percentage)
            except (ValueError, TypeError):
                return jsonify({'error': 'Percentage must be a number'}), 400

        result = db_update_allocation(current_user.id, allocation_id, percentage=percentage, name=name, symbol=symbol)

        if 'error' in result:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/<allocation_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def api_portfolio_delete(allocation_id):
    """Delete an allocation from current user's portfolio."""
    try:
        result = db_delete_allocation(current_user.id, allocation_id)

        if 'error' in result:
            return jsonify(result), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/validate')
@login_required
def api_portfolio_validate():
    """Validate current user's portfolio allocation total."""
    try:
        result = db_validate_allocation_total(current_user.id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/validate-symbol/<symbol>')
def api_portfolio_validate_symbol(symbol):
    """Validate a ticker symbol and get info."""
    try:
        result = validate_symbol(symbol)
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/summary')
@login_required
def api_portfolio_summary():
    """Get the current portfolio AI summary."""
    from ai_summary import get_portfolio_summary_for_display
    summary = get_portfolio_summary_for_display()
    if summary:
        return jsonify(summary)
    return jsonify({
        'error': 'No portfolio summary available',
        'message': 'Click refresh to generate an AI analysis'
    }), 404


@app.route('/api/portfolio/summary/generate', methods=['POST'])
@csrf.exempt
@login_required
def api_generate_portfolio_summary():
    """Manually trigger portfolio AI summary generation for current user."""
    from ai_summary import generate_portfolio_summary
    from services.ai_service import get_user_ai_client, AIServiceError

    try:
        # Get user's AI client for this request
        try:
            user_client, provider = get_user_ai_client()
        except AIServiceError as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 400

        # Get current user's portfolio data for AI
        portfolio_data = db_get_portfolio_summary_for_ai(current_user.id)

        if 'error' in portfolio_data:
            return jsonify({
                'status': 'error',
                'error': portfolio_data['error']
            }), 500

        if not portfolio_data.get('holdings'):
            return jsonify({
                'status': 'error',
                'error': 'No holdings in portfolio. Add some allocations first.'
            }), 400

        # Generate market summary for context
        market_summary = generate_portfolio_market_context()

        # Generate AI summary using user's API key
        result = generate_portfolio_summary(portfolio_data, market_summary, user_client=user_client)

        if result['success']:
            return jsonify({
                'status': 'success',
                'summary': result['summary']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


def generate_portfolio_market_context():
    """Generate market context for portfolio AI analysis."""
    from ai_summary import (
        get_latest_summary, get_latest_crypto_summary,
        get_latest_equity_summary, get_latest_rates_summary,
        get_latest_dollar_summary
    )

    context_parts = []

    # Get all AI briefings from today
    briefings = []

    general = get_latest_summary()
    if general:
        briefings.append(f"**General Market Briefing:**\n{general.get('summary', 'N/A')}")

    crypto = get_latest_crypto_summary()
    if crypto:
        briefings.append(f"**Crypto Briefing:**\n{crypto.get('summary', 'N/A')}")

    equity = get_latest_equity_summary()
    if equity:
        briefings.append(f"**Equity Briefing:**\n{equity.get('summary', 'N/A')}")

    rates = get_latest_rates_summary()
    if rates:
        briefings.append(f"**Rates Briefing:**\n{rates.get('summary', 'N/A')}")

    dollar = get_latest_dollar_summary()
    if dollar:
        briefings.append(f"**Dollar Briefing:**\n{dollar.get('summary', 'N/A')}")

    if briefings:
        context_parts.append("## Today's AI Briefings\n" + "\n\n".join(briefings))

    # Get key market metrics
    try:
        metrics_summary = []

        # Credit spreads
        hy_df = load_csv_data('high_yield_spread.csv')
        if hy_df is not None and not hy_df.empty:
            hy_val = hy_df.iloc[-1][hy_df.columns[1]]
            metrics_summary.append(f"- HY Spread: {hy_val:.0f} bp")

        ig_df = load_csv_data('investment_grade_spread.csv')
        if ig_df is not None and not ig_df.empty:
            ig_val = ig_df.iloc[-1][ig_df.columns[1]]
            metrics_summary.append(f"- IG Spread: {ig_val:.0f} bp")

        # VIX
        vix_df = load_csv_data('vix_price.csv')
        if vix_df is not None and not vix_df.empty:
            vix_val = vix_df.iloc[-1][vix_df.columns[1]]
            metrics_summary.append(f"- VIX: {vix_val:.1f}")

        # Gold
        gold_df = load_csv_data('gold_price.csv')
        if gold_df is not None and not gold_df.empty:
            gold_val = gold_df.iloc[-1][gold_df.columns[1]] * 10
            metrics_summary.append(f"- Gold: ${gold_val:.0f}")

        # Bitcoin
        btc_df = load_csv_data('bitcoin_price.csv')
        if btc_df is not None and not btc_df.empty:
            btc_val = btc_df.iloc[-1][btc_df.columns[1]]
            metrics_summary.append(f"- Bitcoin: ${btc_val:,.0f}")

        # S&P 500
        spy_df = load_csv_data('sp500_price.csv')
        if spy_df is not None and not spy_df.empty:
            spy_val = spy_df.iloc[-1][spy_df.columns[1]]
            metrics_summary.append(f"- S&P 500 (SPY): ${spy_val:.2f}")

        # Yield curve
        yc_df = load_csv_data('yield_curve_10y2y.csv')
        if yc_df is not None and not yc_df.empty:
            yc_val = yc_df.iloc[-1][yc_df.columns[1]]
            metrics_summary.append(f"- 10Y-2Y Yield Curve: {yc_val:.2f}%")

        # DXY
        dxy_df = load_csv_data('dxy.csv')
        if dxy_df is not None and not dxy_df.empty:
            dxy_val = dxy_df.iloc[-1][dxy_df.columns[1]]
            metrics_summary.append(f"- DXY: {dxy_val:.1f}")

        if metrics_summary:
            context_parts.append("## Current Key Metrics\n" + "\n".join(metrics_summary))

    except Exception as e:
        print(f"Error generating market metrics context: {e}")

    return "\n\n".join(context_parts)


@app.route('/api/debug/web-search-status')
def api_debug_web_search():
    """Debug endpoint to check web search configuration."""
    from web_search import TAVILY_API_KEY
    return jsonify({
        'tavily_configured': is_tavily_configured(),
        'tavily_api_key_in_module': bool(TAVILY_API_KEY),
        'tavily_api_key_in_environ': bool(os.environ.get('TAVILY_API_KEY')),
        'tavily_api_key_preview': os.environ.get('TAVILY_API_KEY', '')[:8] + '...' if os.environ.get('TAVILY_API_KEY') else None
    })


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

        # Yield Curve
        yield_curve_10y2y_df = load_csv_data('yield_curve_10y2y.csv')
        yield_curve_10y3m_df = load_csv_data('yield_curve_10y3m.csv')

        # Labor Market
        initial_claims_df = load_csv_data('initial_claims.csv')
        continuing_claims_df = load_csv_data('continuing_claims.csv')

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

        # Yield Curve (Recession Indicators)
        summary_parts.append("## YIELD CURVE (Recession Indicators)")
        if yield_curve_10y2y_df is not None:
            stats = get_stats(yield_curve_10y2y_df)
            if stats:
                status = "INVERTED" if stats['current'] < 0 else "Normal"
                summary_parts.append(f"10Y-2Y Spread: {stats['current']:.2f}% [{status}] ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d']:+.2f}%")
        if yield_curve_10y3m_df is not None:
            stats = get_stats(yield_curve_10y3m_df)
            if stats:
                status = "INVERTED" if stats['current'] < 0 else "Normal"
                summary_parts.append(f"10Y-3M Spread: {stats['current']:.2f}% [{status}] ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d']:+.2f}%")
        summary_parts.append("  (Negative = inverted yield curve, historically precedes recessions by 12-18 months)")
        summary_parts.append("")

        # Labor Market
        summary_parts.append("## LABOR MARKET (Weekly Data)")
        if initial_claims_df is not None:
            stats = get_stats(initial_claims_df)
            if stats:
                level = "Low" if stats['current'] < 250 else "Elevated" if stats['current'] > 300 else "Normal"
                summary_parts.append(f"Initial Claims: {stats['current']:.0f}k [{level}] ({stats['percentile']:.1f}th %ile) | 5d: {stats['change_5d']:+.0f}k")
        if continuing_claims_df is not None:
            stats = get_stats(continuing_claims_df)
            if stats:
                summary_parts.append(f"Continuing Claims: {stats['current']:.0f}k ({stats['percentile']:.1f}th %ile) | 30d: {stats['change_30d']:+.0f}k")
        summary_parts.append("  (Rising claims = labor market weakening; Initial >300k = warning, >400k = recession signal)")
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


def generate_crypto_market_summary():
    """Generate a crypto-focused market data summary for the Crypto AI briefing."""
    try:
        summary_parts = []
        summary_parts.append("# CRYPTO/BITCOIN MARKET DATA SUMMARY")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append("")

        def get_stats(df):
            if df is None or len(df) < 2:
                return None
            col = [c for c in df.columns if c != 'date'][0]
            current = df.iloc[-1][col]
            values = df[col].dropna().tolist()
            percentile = sum(1 for v in values if v <= current) / len(values) * 100

            change_1d = current - df.iloc[-2][col] if len(df) > 1 else 0
            change_5d = current - df.iloc[-6][col] if len(df) > 5 else 0
            change_30d = current - df.iloc[-31][col] if len(df) > 30 else 0

            pct_change_5d = ((current / df.iloc[-6][col]) - 1) * 100 if len(df) > 5 and df.iloc[-6][col] != 0 else 0
            pct_change_30d = ((current / df.iloc[-31][col]) - 1) * 100 if len(df) > 30 and df.iloc[-31][col] != 0 else 0

            high_52w = df[col].tail(252).max() if len(df) > 252 else df[col].max()
            low_52w = df[col].tail(252).min() if len(df) > 252 else df[col].min()

            return {
                'current': current,
                'percentile': percentile,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_30d': change_30d,
                'pct_change_5d': pct_change_5d,
                'pct_change_30d': pct_change_30d,
                'high_52w': high_52w,
                'low_52w': low_52w
            }

        # Load crypto-relevant metrics
        bitcoin_df = load_csv_data('bitcoin_price.csv')
        gold_df = load_csv_data('gold_price.csv')
        btc_gold_ratio_df = load_csv_data('btc_gold_ratio.csv')
        fear_greed_df = load_csv_data('fear_greed_index.csv')
        fed_balance_df = load_csv_data('fed_balance_sheet.csv')
        reverse_repo_df = load_csv_data('reverse_repo.csv')
        nfci_df = load_csv_data('nfci.csv')
        m2_df = load_csv_data('m2_money_supply.csv')
        vix_df = load_csv_data('vix_price.csv')
        dxy_df = load_csv_data('dollar_index_price.csv')
        sp500_df = load_csv_data('sp500_price.csv')
        nasdaq_df = load_csv_data('nasdaq_price.csv')

        # Bitcoin Section
        summary_parts.append("## BITCOIN")
        if bitcoin_df is not None:
            stats = get_stats(bitcoin_df)
            if stats:
                summary_parts.append(f"Price: ${stats['current']:,.0f} ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day: {stats['pct_change_5d']:+.1f}% | 30-day: {stats['pct_change_30d']:+.1f}%")
                summary_parts.append(f"  52-week range: ${stats['low_52w']:,.0f} - ${stats['high_52w']:,.0f}")

                # Distance from 52w high/low
                dist_from_high = ((stats['current'] / stats['high_52w']) - 1) * 100
                dist_from_low = ((stats['current'] / stats['low_52w']) - 1) * 100
                summary_parts.append(f"  Distance from 52w high: {dist_from_high:.1f}% | from low: +{dist_from_low:.1f}%")
        summary_parts.append("")

        # Fear & Greed Index
        summary_parts.append("## CRYPTO SENTIMENT")
        if fear_greed_df is not None:
            stats = get_stats(fear_greed_df)
            if stats:
                # Interpret the level
                level = stats['current']
                if level <= 25:
                    interpretation = "EXTREME FEAR (historically good buying zone)"
                elif level <= 46:
                    interpretation = "Fear"
                elif level <= 54:
                    interpretation = "Neutral"
                elif level <= 75:
                    interpretation = "Greed"
                else:
                    interpretation = "EXTREME GREED (historically poor time to buy)"

                summary_parts.append(f"Fear & Greed Index: {level:.0f}/100 [{interpretation}]")
                summary_parts.append(f"  5-day change: {stats['change_5d']:+.0f} pts | 30-day: {stats['change_30d']:+.0f} pts")
                summary_parts.append(f"  Historical context: {stats['percentile']:.1f}th percentile")

                # Key levels
                summary_parts.append("  KEY LEVELS: <25 = extreme fear (contrarian buy), >75 = extreme greed (caution)")
        summary_parts.append("")

        # BTC/Gold Ratio
        summary_parts.append("## BTC/GOLD RATIO")
        if btc_gold_ratio_df is not None:
            stats = get_stats(btc_gold_ratio_df)
            if stats:
                summary_parts.append(f"BTC priced in gold: {stats['current']:.1f} oz ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.1f}%")
                summary_parts.append("  (Rising = BTC outperforming gold, risk-on; Falling = gold outperforming, risk-off)")
        summary_parts.append("")

        # Liquidity Indicators
        summary_parts.append("## LIQUIDITY INDICATORS (Key BTC Drivers)")

        if fed_balance_df is not None:
            stats = get_stats(fed_balance_df)
            if stats:
                trend = "EXPANDING (bullish for BTC)" if stats['change_30d'] > 0 else "SHRINKING (headwind for BTC)"
                summary_parts.append(f"Fed Balance Sheet: ${stats['current']/1000:.2f} trillion [{trend}]")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.2f}%")

        if reverse_repo_df is not None:
            stats = get_stats(reverse_repo_df)
            if stats:
                trend = "Rising (liquidity parking at Fed)" if stats['change_30d'] > 0 else "Declining (liquidity entering markets)"
                summary_parts.append(f"Reverse Repo (RRP): ${stats['current']:.0f}B [{trend}]")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.1f}%")

        if nfci_df is not None:
            stats = get_stats(nfci_df)
            if stats:
                if stats['current'] > 0.5:
                    condition = "TIGHT (bearish for risk assets)"
                elif stats['current'] > 0:
                    condition = "Tightening"
                elif stats['current'] > -0.5:
                    condition = "Loose (bullish for risk assets)"
                else:
                    condition = "VERY LOOSE (bullish for risk assets)"
                summary_parts.append(f"NFCI (Financial Conditions): {stats['current']:.2f} [{condition}]")
                summary_parts.append(f"  30-day change: {stats['change_30d']:+.2f}")
                summary_parts.append("  (Negative = loose conditions favor BTC; Positive = tight conditions = headwind)")

        if m2_df is not None:
            stats = get_stats(m2_df)
            if stats:
                # Calculate YoY change
                if len(m2_df) > 12:
                    yoy = ((stats['current'] / m2_df.iloc[-13][[c for c in m2_df.columns if c != 'date'][0]]) - 1) * 100
                else:
                    yoy = 0
                summary_parts.append(f"M2 Money Supply: ${stats['current']/1000:.1f} trillion | YoY: {yoy:+.1f}%")
                summary_parts.append("  (BTC correlates ~0.7-0.8 with global M2)")
        summary_parts.append("")

        # Risk Context
        summary_parts.append("## RISK CONTEXT")
        if vix_df is not None:
            stats = get_stats(vix_df)
            if stats:
                level = "HIGH FEAR" if stats['current'] > 30 else "Elevated" if stats['current'] > 20 else "Low"
                summary_parts.append(f"VIX: {stats['current']:.1f} [{level}] | 5d: {stats['pct_change_5d']:+.1f}%")

        if dxy_df is not None:
            stats = get_stats(dxy_df)
            if stats:
                trend = "Strengthening (BTC headwind)" if stats['change_30d'] > 0 else "Weakening (BTC tailwind)"
                summary_parts.append(f"Dollar Index (DXY): {stats['current']:.2f} [{trend}] | 30d: {stats['pct_change_30d']:+.1f}%")

        if sp500_df is not None:
            stats = get_stats(sp500_df)
            if stats:
                summary_parts.append(f"S&P 500: {stats['current']:,.0f} | 30d: {stats['pct_change_30d']:+.1f}%")

        if nasdaq_df is not None:
            stats = get_stats(nasdaq_df)
            if stats:
                summary_parts.append(f"Nasdaq 100: {stats['current']:,.0f} | 30d: {stats['pct_change_30d']:+.1f}%")
        summary_parts.append("")

        # Key Insights
        summary_parts.append("## KEY RELATIONSHIPS TO MONITOR")
        summary_parts.append("- Fed Balance Sheet expanding + NFCI negative = bullish liquidity setup for BTC")
        summary_parts.append("- Fear & Greed <25 + Fed not tightening = historical buying opportunity")
        summary_parts.append("- BTC/Gold ratio falling while gold rises = risk-off rotation")
        summary_parts.append("- VIX spiking + NFCI positive = expect BTC volatility/downside")
        summary_parts.append("")

        return "\n".join(summary_parts)

    except Exception as e:
        print(f"Error generating crypto market summary: {e}")
        return "Crypto market data summary unavailable."


def generate_equity_market_summary():
    """Generate an equity-focused market data summary for the Equity AI briefing."""
    try:
        summary_parts = []
        summary_parts.append("# EQUITY MARKETS DATA SUMMARY")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append("")

        def get_stats(df):
            if df is None or len(df) < 2:
                return None
            col = [c for c in df.columns if c != 'date'][0]
            current = df.iloc[-1][col]
            values = df[col].dropna().tolist()
            percentile = sum(1 for v in values if v <= current) / len(values) * 100

            change_1d = current - df.iloc[-2][col] if len(df) > 1 else 0
            change_5d = current - df.iloc[-6][col] if len(df) > 5 else 0
            change_30d = current - df.iloc[-31][col] if len(df) > 30 else 0

            pct_change_5d = ((current / df.iloc[-6][col]) - 1) * 100 if len(df) > 5 and df.iloc[-6][col] != 0 else 0
            pct_change_30d = ((current / df.iloc[-31][col]) - 1) * 100 if len(df) > 30 and df.iloc[-31][col] != 0 else 0

            high_52w = df[col].tail(252).max() if len(df) > 252 else df[col].max()
            low_52w = df[col].tail(252).min() if len(df) > 252 else df[col].min()

            return {
                'current': current,
                'percentile': percentile,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_30d': change_30d,
                'pct_change_5d': pct_change_5d,
                'pct_change_30d': pct_change_30d,
                'high_52w': high_52w,
                'low_52w': low_52w
            }

        # Load equity-relevant metrics
        sp500_df = load_csv_data('sp500_price.csv')
        nasdaq_df = load_csv_data('nasdaq_price.csv')
        small_cap_df = load_csv_data('small_cap_price.csv')
        vix_df = load_csv_data('vix_price.csv')
        breadth_df = load_csv_data('market_breadth_ratio.csv')
        smh_spy_df = load_csv_data('smh_spy_ratio.csv')
        growth_value_df = load_csv_data('growth_value_ratio.csv')
        iwm_spy_df = load_csv_data('iwm_spy_ratio.csv')
        financials_df = load_csv_data('financials_sector_price.csv')
        energy_df = load_csv_data('energy_sector_price.csv')
        semi_df = load_csv_data('semiconductor_price.csv')

        # Core Indices Section
        summary_parts.append("## CORE INDICES")
        if sp500_df is not None:
            stats = get_stats(sp500_df)
            if stats:
                summary_parts.append(f"S&P 500: {stats['current']:,.0f} ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day: {stats['pct_change_5d']:+.1f}% | 30-day: {stats['pct_change_30d']:+.1f}%")

        if nasdaq_df is not None:
            stats = get_stats(nasdaq_df)
            if stats:
                summary_parts.append(f"Nasdaq 100: {stats['current']:,.0f} ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day: {stats['pct_change_5d']:+.1f}% | 30-day: {stats['pct_change_30d']:+.1f}%")

        if small_cap_df is not None:
            stats = get_stats(small_cap_df)
            if stats:
                summary_parts.append(f"Russell 2000 (Small Caps): ${stats['current']:,.2f} ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day: {stats['pct_change_5d']:+.1f}% | 30-day: {stats['pct_change_30d']:+.1f}%")
        summary_parts.append("")

        # VIX Section
        summary_parts.append("## VOLATILITY")
        if vix_df is not None:
            stats = get_stats(vix_df)
            if stats:
                if stats['current'] < 15:
                    level = "LOW (complacency)"
                elif stats['current'] < 20:
                    level = "Normal"
                elif stats['current'] < 30:
                    level = "Elevated"
                else:
                    level = "HIGH FEAR"
                summary_parts.append(f"VIX: {stats['current']:.1f} [{level}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day: {stats['pct_change_5d']:+.1f}% | 30-day: {stats['pct_change_30d']:+.1f}%")
                summary_parts.append("  KEY LEVELS: <15 = complacent, 15-20 = normal, 20-30 = elevated, >30 = fear")
        summary_parts.append("")

        # Market Structure Section
        summary_parts.append("## MARKET STRUCTURE (Breadth & Concentration)")
        if breadth_df is not None:
            stats = get_stats(breadth_df)
            if stats:
                if stats['percentile'] < 20:
                    condition = "VERY NARROW (concentrated)"
                elif stats['percentile'] < 40:
                    condition = "Narrow"
                elif stats['percentile'] < 60:
                    condition = "Normal"
                elif stats['percentile'] < 80:
                    condition = "Broad"
                else:
                    condition = "VERY BROAD (healthy)"
                summary_parts.append(f"Market Breadth (RSP/SPY): {stats['current']:.2f} [{condition}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.1f}%")
                summary_parts.append("  (Low = few stocks driving gains; High = broad participation)")

        if smh_spy_df is not None:
            stats = get_stats(smh_spy_df)
            if stats:
                if stats['percentile'] > 90:
                    level = "EXTREME concentration"
                elif stats['percentile'] > 75:
                    level = "High concentration"
                else:
                    level = "Normal"
                summary_parts.append(f"Semiconductor/SPY Ratio: {stats['current']:.1f} [{level}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.1f}%")
                summary_parts.append("  (Proxy for AI/Mag 7 concentration)")
        summary_parts.append("")

        # Style Rotation Section
        summary_parts.append("## STYLE & SIZE ROTATION")
        if growth_value_df is not None:
            stats = get_stats(growth_value_df)
            if stats:
                if stats['percentile'] > 80:
                    bias = "Strong GROWTH leadership"
                elif stats['percentile'] > 60:
                    bias = "Growth favored"
                elif stats['percentile'] > 40:
                    bias = "Balanced"
                elif stats['percentile'] > 20:
                    bias = "Value favored"
                else:
                    bias = "Strong VALUE leadership"
                summary_parts.append(f"Growth/Value Ratio: {stats['current']:.1f} [{bias}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.1f}%")

        if iwm_spy_df is not None:
            stats = get_stats(iwm_spy_df)
            if stats:
                if stats['percentile'] > 70:
                    bias = "Small caps leading (risk-on)"
                elif stats['percentile'] > 40:
                    bias = "Balanced"
                else:
                    bias = "Large caps leading (quality flight)"
                summary_parts.append(f"Small Cap/Large Cap Ratio: {stats['current']:.1f} [{bias}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.1f}%")
        summary_parts.append("")

        # Key Sectors Section
        summary_parts.append("## KEY SECTORS")
        if semi_df is not None:
            stats = get_stats(semi_df)
            if stats:
                summary_parts.append(f"Semiconductors (SMH): ${stats['current']:,.2f} | 5d: {stats['pct_change_5d']:+.1f}% | 30d: {stats['pct_change_30d']:+.1f}%")

        if financials_df is not None:
            stats = get_stats(financials_df)
            if stats:
                summary_parts.append(f"Financials (XLF): ${stats['current']:,.2f} | 5d: {stats['pct_change_5d']:+.1f}% | 30d: {stats['pct_change_30d']:+.1f}%")

        if energy_df is not None:
            stats = get_stats(energy_df)
            if stats:
                summary_parts.append(f"Energy (XLE): ${stats['current']:,.2f} | 5d: {stats['pct_change_5d']:+.1f}% | 30d: {stats['pct_change_30d']:+.1f}%")
        summary_parts.append("")

        # Key Insights
        summary_parts.append("## KEY RELATIONSHIPS TO MONITOR")
        summary_parts.append("- Breadth low + indices high = fragile rally dependent on few stocks")
        summary_parts.append("- Small caps leading = risk appetite, economic optimism")
        summary_parts.append("- Growth/Value ratio falling = potential rotation to defensives")
        summary_parts.append("- VIX <15 with indices at highs = complacency (watch for reversal)")
        summary_parts.append("")

        return "\n".join(summary_parts)

    except Exception as e:
        print(f"Error generating equity market summary: {e}")
        return "Equity market data summary unavailable."


def generate_rates_market_summary():
    """Generate a rates-focused market data summary for the Rates AI briefing."""
    try:
        summary_parts = []
        summary_parts.append("# RATES & YIELD CURVE DATA SUMMARY")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append("")

        def get_stats(df):
            if df is None or len(df) < 2:
                return None
            col = [c for c in df.columns if c != 'date'][0]
            current = df.iloc[-1][col]
            values = df[col].dropna().tolist()
            percentile = sum(1 for v in values if v <= current) / len(values) * 100

            change_1d = current - df.iloc[-2][col] if len(df) > 1 else 0
            change_5d = current - df.iloc[-6][col] if len(df) > 5 else 0
            change_30d = current - df.iloc[-31][col] if len(df) > 30 else 0

            pct_change_5d = ((current / df.iloc[-6][col]) - 1) * 100 if len(df) > 5 and df.iloc[-6][col] != 0 else 0
            pct_change_30d = ((current / df.iloc[-31][col]) - 1) * 100 if len(df) > 30 and df.iloc[-31][col] != 0 else 0

            high_52w = df[col].tail(252).max() if len(df) > 252 else df[col].max()
            low_52w = df[col].tail(252).min() if len(df) > 252 else df[col].min()

            return {
                'current': current,
                'percentile': percentile,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_30d': change_30d,
                'pct_change_5d': pct_change_5d,
                'pct_change_30d': pct_change_30d,
                'high_52w': high_52w,
                'low_52w': low_52w
            }

        # Load rates-relevant metrics
        treasury_10y_df = load_csv_data('treasury_10y.csv')
        yield_curve_10y2y_df = load_csv_data('yield_curve_10y2y.csv')
        yield_curve_10y3m_df = load_csv_data('yield_curve_10y3m.csv')
        real_yield_df = load_csv_data('real_yield_10y.csv')
        breakeven_df = load_csv_data('breakeven_inflation_10y.csv')
        cpi_df = load_csv_data('cpi_yoy.csv')
        fed_funds_df = load_csv_data('fed_funds_rate.csv')
        sp500_df = load_csv_data('sp500_price.csv')
        gold_df = load_csv_data('gold_price.csv')

        # Treasury Yields Section
        summary_parts.append("## TREASURY YIELDS")
        if treasury_10y_df is not None:
            stats = get_stats(treasury_10y_df)
            if stats:
                if stats['current'] > 4.5:
                    level = "ELEVATED (restrictive)"
                elif stats['current'] > 3.5:
                    level = "Normal"
                else:
                    level = "LOW (accommodative)"
                summary_parts.append(f"10-Year Treasury: {stats['current']:.2f}% [{level}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']*100:+.0f} bps")
                summary_parts.append(f"  52-week range: {stats['low_52w']:.2f}% - {stats['high_52w']:.2f}%")
                summary_parts.append("  KEY LEVELS: 4.0% (psychological), 5.0% (restrictive)")
        summary_parts.append("")

        # Yield Curve Section
        summary_parts.append("## YIELD CURVE (Recession Indicator)")
        if yield_curve_10y2y_df is not None:
            stats = get_stats(yield_curve_10y2y_df)
            if stats:
                spread_bps = stats['current'] * 100
                if stats['current'] < 0:
                    status = "INVERTED (recession warning)"
                elif stats['current'] < 0.25:
                    status = "Flat"
                else:
                    status = "Normal (positive slope)"
                summary_parts.append(f"10Y-2Y Spread: {spread_bps:.0f} bps [{status}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']*100:+.0f} bps")

        if yield_curve_10y3m_df is not None:
            stats = get_stats(yield_curve_10y3m_df)
            if stats:
                spread_bps = stats['current'] * 100
                if stats['current'] < 0:
                    status = "INVERTED"
                elif stats['current'] < 0.25:
                    status = "Flat"
                else:
                    status = "Normal"
                summary_parts.append(f"10Y-3M Spread (Fed's preferred): {spread_bps:.0f} bps [{status}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']*100:+.0f} bps")
        summary_parts.append("  CONTEXT: Inversion has preceded every US recession since 1970 (6-18 month lead)")
        summary_parts.append("")

        # Real Yields Section
        summary_parts.append("## REAL YIELDS & INFLATION")
        if real_yield_df is not None:
            stats = get_stats(real_yield_df)
            if stats:
                if stats['current'] > 2:
                    policy = "RESTRICTIVE"
                elif stats['current'] > 0.5:
                    policy = "Tight"
                elif stats['current'] > 0:
                    policy = "Neutral"
                else:
                    policy = "ACCOMMODATIVE"
                summary_parts.append(f"10Y Real Yield (TIPS): {stats['current']:.2f}% [{policy}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']*100:+.0f} bps")
                summary_parts.append("  (Real yield = nominal yield minus inflation expectations)")

        if breakeven_df is not None:
            stats = get_stats(breakeven_df)
            if stats:
                if stats['current'] > 2.5:
                    expectation = "Above target (inflation concerns)"
                elif stats['current'] >= 2.0:
                    expectation = "At Fed target"
                else:
                    expectation = "Below target"
                summary_parts.append(f"10Y Breakeven Inflation: {stats['current']:.2f}% [{expectation}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']*100:+.0f} bps")
                summary_parts.append("  (Market's 10-year inflation forecast)")

        if cpi_df is not None:
            stats = get_stats(cpi_df)
            if stats:
                summary_parts.append(f"CPI (YoY): {stats['current']:.1f}%")
        summary_parts.append("")

        # Fed Policy Section
        summary_parts.append("## FED POLICY")
        if fed_funds_df is not None:
            stats = get_stats(fed_funds_df)
            if stats:
                summary_parts.append(f"Fed Funds Rate: {stats['current']:.2f}%")
                if treasury_10y_df is not None:
                    t10y_stats = get_stats(treasury_10y_df)
                    if t10y_stats:
                        term_premium = t10y_stats['current'] - stats['current']
                        summary_parts.append(f"  Term Premium (10Y - Fed Funds): {term_premium:.2f}%")
        summary_parts.append("")

        # Cross-Asset Context
        summary_parts.append("## RATES IMPACT ON OTHER ASSETS")
        if sp500_df is not None and treasury_10y_df is not None:
            sp_stats = get_stats(sp500_df)
            t10y_stats = get_stats(treasury_10y_df)
            if sp_stats and t10y_stats:
                # Equity risk premium approximation (rough)
                earnings_yield = 100 / 20  # Assume ~20x P/E
                erp = earnings_yield - t10y_stats['current']
                summary_parts.append(f"S&P 500 Equity Risk Premium (est): {erp:.1f}%")
                summary_parts.append("  (Higher rates compress equity valuations)")

        if gold_df is not None and real_yield_df is not None:
            gold_stats = get_stats(gold_df)
            ry_stats = get_stats(real_yield_df)
            if gold_stats and ry_stats:
                summary_parts.append(f"Gold vs Real Yields: Gold {gold_stats['pct_change_30d']:+.1f}% (30d) | Real yield {ry_stats['change_30d']*100:+.0f} bps")
                summary_parts.append("  (Gold typically inversely correlated with real yields)")
        summary_parts.append("")

        # Credit Spreads Section
        summary_parts.append("## CREDIT SPREADS (Risk Appetite)")
        hy_spread_df = load_csv_data('hy_spread.csv')
        ig_spread_df = load_csv_data('ig_spread.csv')
        ccc_spread_df = load_csv_data('ccc_spread.csv')

        if hy_spread_df is not None:
            stats = get_stats(hy_spread_df)
            if stats:
                if stats['current'] > 500:
                    status = "STRESS (significant risk aversion)"
                elif stats['current'] > 350:
                    status = "Elevated"
                elif stats['current'] > 300:
                    status = "Normal"
                else:
                    status = "TIGHT (complacency)"
                summary_parts.append(f"High-Yield Spread: {stats['current']:.0f} bp [{status}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']:+.0f} bp")
                summary_parts.append("  KEY LEVELS: 300bp (first warning), 500bp (stress), 800bp (crisis)")

        if ig_spread_df is not None:
            stats = get_stats(ig_spread_df)
            if stats:
                if stats['current'] > 150:
                    status = "STRESS"
                elif stats['current'] > 120:
                    status = "Elevated"
                elif stats['current'] > 100:
                    status = "Normal"
                else:
                    status = "Tight"
                summary_parts.append(f"Investment Grade Spread: {stats['current']:.0f} bp [{status}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  30-day change: {stats['change_30d']:+.0f} bp")

        if ccc_spread_df is not None and hy_spread_df is not None:
            ccc_stats = get_stats(ccc_spread_df)
            hy_stats = get_stats(hy_spread_df)
            if ccc_stats and hy_stats and hy_stats['current'] > 0:
                ccc_hy_ratio = ccc_stats['current'] / hy_stats['current']
                if ccc_hy_ratio > 3.5:
                    ratio_status = "DISTRESSED (quality bifurcation)"
                elif ccc_hy_ratio > 3.0:
                    ratio_status = "Elevated"
                else:
                    ratio_status = "Normal"
                summary_parts.append(f"CCC/HY Ratio: {ccc_hy_ratio:.2f}x [{ratio_status}]")
                summary_parts.append("  (Higher ratio = market discriminating against lowest quality)")
        summary_parts.append("  CONTEXT: Tight spreads = complacency, historically precedes sharp widening")
        summary_parts.append("")

        # Key Insights
        summary_parts.append("## KEY RELATIONSHIPS TO MONITOR")
        summary_parts.append("- Inverted curve + steepening = recession typically imminent")
        summary_parts.append("- Rising real yields = headwind for growth stocks and gold")
        summary_parts.append("- Breakevens > 2.5% = inflation expectations unanchored")
        summary_parts.append("- 10Y above 5% = significant equity valuation pressure")
        summary_parts.append("- Credit spreads widening while equities rise = divergence warning")
        summary_parts.append("- HY spreads at extremes (<300bp or >500bp) often precede regime change")
        summary_parts.append("")

        return "\n".join(summary_parts)

    except Exception as e:
        print(f"Error generating rates market summary: {e}")
        return "Rates market data summary unavailable."


def generate_dollar_market_summary():
    """Generate a dollar-focused market data summary for the Dollar AI briefing."""
    try:
        summary_parts = []
        summary_parts.append("# DOLLAR & CURRENCY DATA SUMMARY")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append("")

        def get_stats(df):
            if df is None or len(df) < 2:
                return None
            col = [c for c in df.columns if c != 'date'][0]
            current = df.iloc[-1][col]
            values = df[col].dropna().tolist()
            percentile = sum(1 for v in values if v <= current) / len(values) * 100

            change_1d = current - df.iloc[-2][col] if len(df) > 1 else 0
            change_5d = current - df.iloc[-6][col] if len(df) > 5 else 0
            change_30d = current - df.iloc[-31][col] if len(df) > 30 else 0

            pct_change_5d = ((current / df.iloc[-6][col]) - 1) * 100 if len(df) > 5 and df.iloc[-6][col] != 0 else 0
            pct_change_30d = ((current / df.iloc[-31][col]) - 1) * 100 if len(df) > 30 and df.iloc[-31][col] != 0 else 0

            high_52w = df[col].tail(252).max() if len(df) > 252 else df[col].max()
            low_52w = df[col].tail(252).min() if len(df) > 252 else df[col].min()

            return {
                'current': current,
                'percentile': percentile,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_30d': change_30d,
                'pct_change_5d': pct_change_5d,
                'pct_change_30d': pct_change_30d,
                'high_52w': high_52w,
                'low_52w': low_52w
            }

        # Load dollar-relevant metrics
        dxy_df = load_csv_data('dollar_index_price.csv')
        usdjpy_df = load_csv_data('usdjpy_price.csv')
        treasury_10y_df = load_csv_data('treasury_10y.csv')
        fed_funds_df = load_csv_data('fed_funds_rate.csv')
        gold_df = load_csv_data('gold_price.csv')
        sp500_df = load_csv_data('sp500_price.csv')
        bitcoin_df = load_csv_data('bitcoin_price.csv')
        vix_df = load_csv_data('vix_price.csv')

        # Dollar Index Section
        summary_parts.append("## US DOLLAR INDEX (DXY)")
        if dxy_df is not None:
            stats = get_stats(dxy_df)
            if stats:
                # Dollar Smile framework interpretation
                if stats['current'] > 105:
                    level = "STRONG (risk-off or yield advantage)"
                elif stats['current'] > 100:
                    level = "Firm"
                elif stats['current'] > 95:
                    level = "Neutral"
                else:
                    level = "WEAK (risk-on or policy concerns)"
                summary_parts.append(f"DXY: {stats['current']:.2f} [{level}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day change: {stats['pct_change_5d']:+.2f}%")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.2f}%")
                summary_parts.append(f"  52-week range: {stats['low_52w']:.2f} - {stats['high_52w']:.2f}")
                summary_parts.append("  KEY LEVELS: 100 (psychological), 105 (strong dollar), 95 (weak dollar)")
        summary_parts.append("")

        # USD/JPY Section (Carry Trade Indicator)
        summary_parts.append("## USD/JPY (Carry Trade Barometer)")
        if usdjpy_df is not None:
            stats = get_stats(usdjpy_df)
            if stats:
                # Carry trade dynamics
                if stats['current'] > 150:
                    status = "EXTENDED (carry trade stress risk)"
                elif stats['current'] > 145:
                    status = "Elevated (BOJ intervention zone)"
                elif stats['current'] > 140:
                    status = "Normal carry trade range"
                else:
                    status = "Yen strength (carry unwind risk)"
                summary_parts.append(f"USD/JPY: {stats['current']:.2f} [{status}] ({stats['percentile']:.1f}th %ile)")
                summary_parts.append(f"  5-day change: {stats['pct_change_5d']:+.2f}%")
                summary_parts.append(f"  30-day change: {stats['pct_change_30d']:+.2f}%")
                summary_parts.append(f"  52-week range: {stats['low_52w']:.2f} - {stats['high_52w']:.2f}")
                summary_parts.append("  CONTEXT: Japan's ultra-low rates make JPY funding currency for global carry trades")
                summary_parts.append("  KEY LEVELS: 150 (BOJ red line), 145 (intervention risk), 140 (support)")
        summary_parts.append("")

        # Dollar Smile Framework
        summary_parts.append("## DOLLAR SMILE FRAMEWORK")
        summary_parts.append("The 'Dollar Smile' describes three regimes where USD strengthens:")
        summary_parts.append("  LEFT SIDE: Risk-off panic (flight to safety → USD bid)")
        summary_parts.append("  MIDDLE: Weak dollar (calm markets, relative growth elsewhere)")
        summary_parts.append("  RIGHT SIDE: US growth/yield advantage (risk-on but US outperforms)")
        summary_parts.append("")

        # Rate Differentials
        summary_parts.append("## RATE DIFFERENTIALS (Dollar Driver)")
        if treasury_10y_df is not None:
            stats = get_stats(treasury_10y_df)
            if stats:
                summary_parts.append(f"US 10Y Treasury: {stats['current']:.2f}%")
                summary_parts.append(f"  30-day change: {stats['change_30d']*100:+.0f} bps")
                summary_parts.append("  (Higher US rates typically support USD)")

        if fed_funds_df is not None:
            stats = get_stats(fed_funds_df)
            if stats:
                summary_parts.append(f"Fed Funds Rate: {stats['current']:.2f}%")
                summary_parts.append("  CONTEXT: Rate differential vs ECB/BOJ drives FX flows")
        summary_parts.append("")

        # Cross-Asset Context
        summary_parts.append("## DOLLAR IMPACT ON OTHER ASSETS")
        if gold_df is not None and dxy_df is not None:
            gold_stats = get_stats(gold_df)
            dxy_stats = get_stats(dxy_df)
            if gold_stats and dxy_stats:
                summary_parts.append(f"Gold: ${gold_stats['current']:.2f} ({gold_stats['pct_change_30d']:+.1f}% 30d) vs DXY {dxy_stats['pct_change_30d']:+.1f}%")
                summary_parts.append("  (Gold typically inversely correlated with USD)")

        if sp500_df is not None:
            stats = get_stats(sp500_df)
            if stats:
                summary_parts.append(f"S&P 500: {stats['current']:.2f} ({stats['pct_change_30d']:+.1f}% 30d)")
                summary_parts.append("  (Strong dollar headwind for multinational earnings)")

        if bitcoin_df is not None:
            stats = get_stats(bitcoin_df)
            if stats:
                summary_parts.append(f"Bitcoin: ${stats['current']:,.0f} ({stats['pct_change_30d']:+.1f}% 30d)")
                summary_parts.append("  (Crypto sensitive to dollar liquidity conditions)")
        summary_parts.append("")

        # Risk Sentiment
        summary_parts.append("## RISK SENTIMENT CONTEXT")
        if vix_df is not None:
            stats = get_stats(vix_df)
            if stats:
                if stats['current'] > 25:
                    regime = "RISK-OFF (supports USD safe-haven bid)"
                elif stats['current'] > 18:
                    regime = "Elevated uncertainty"
                else:
                    regime = "Risk-on (may weaken USD)"
                summary_parts.append(f"VIX: {stats['current']:.2f} [{regime}]")
        summary_parts.append("")

        # Key Insights
        summary_parts.append("## KEY RELATIONSHIPS TO MONITOR")
        summary_parts.append("- DXY > 105 with VIX > 25 = risk-off dollar strength (left side of smile)")
        summary_parts.append("- DXY > 105 with VIX < 18 = yield/growth advantage (right side of smile)")
        summary_parts.append("- USD/JPY > 150 = BOJ intervention risk, carry trade stress")
        summary_parts.append("- DXY falling while VIX low = middle of smile (dollar weakness)")
        summary_parts.append("- Sharp yen strength = carry trade unwind, risk-off signal")
        summary_parts.append("- Dollar strength headwind for EM assets, commodities, multinational earnings")
        summary_parts.append("")

        return "\n".join(summary_parts)

    except Exception as e:
        print(f"Error generating dollar market summary: {e}")
        return "Dollar market data summary unavailable."


@app.route('/api/chat', methods=['POST'])
@csrf.exempt  # API endpoint uses login_required for auth
@limiter.limit("10 per minute")
@login_required
def api_chat():
    """Handle chat messages with user's API key, with web search capability."""
    from services.ai_service import get_user_ai_client, AIServiceError

    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])  # Get conversation history

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Get user's AI client
        try:
            user_client, provider = get_user_ai_client()
        except AIServiceError as e:
            return jsonify({'error': str(e)}), 400

        # Currently chatbot only supports OpenAI due to tool calling
        if provider != 'openai':
            return jsonify({
                'error': 'Chatbot currently requires OpenAI. Please configure an OpenAI API key in Settings.'
            }), 400

        # Check if web search is available
        web_search_available = is_tavily_configured()
        print(f"[CHAT] Web search available: {web_search_available}")

        # Build system message - now tool-based, not data-dump
        system_message = """You are a financial markets expert assistant with access to real-time market data through tools.

AVAILABLE TOOLS:
1. **list_available_metrics** - Discover all available market data series (credit spreads, equities, safe havens, etc.)
2. **get_metric_data** - Fetch detailed data for any metric (current value, percentile, historical stats, recent changes)
3. **search_web** - Search for current news, market commentary, or recent events (if configured)

HOW TO USE TOOLS EFFECTIVELY:
- When users ask about specific metrics, USE get_metric_data to fetch current data rather than guessing
- When users ask "what data do you have?" or ask about a metric you're unsure of, USE list_available_metrics first
- Only search the web for news/current events - use metric tools for market data

KEY CONTEXT:
- This dashboard tracks a wide range of financial market data: credit spreads, equities, safe havens, yield curves, economic indicators, and more
- The divergence_gap metric compares gold-implied spreads vs actual HY spreads - one of many useful cross-market comparisons
- Use percentiles to contextualize whether current values are historically high/low
- Yield curve metrics (10y2y, 10y3m) are important recession indicators
- Credit spreads (HY, IG, CCC) reflect market stress levels
- Historical recession data is available to correlate with other indicators

YOUR ROLE:
- Help users understand what the numbers mean and their implications
- Fetch specific data when asked about metrics (don't make up numbers!)
- Explain market dynamics, risks, and historical context
- Be objective and data-driven
- Don't give specific investment advice (no "you should buy/sell X")
- Be conversational and educational

IMPORTANT: When answering questions about specific metrics, ALWAYS use the tools to get current data. Don't rely on potentially stale information."""

        # Build messages array: system message + conversation history + current message
        messages = [{"role": "system", "content": system_message}]

        # Add conversation history (excluding the current message which is already in history)
        # The history includes the current user message, so we add all but the last one
        for msg in conversation_history[:-1] if conversation_history else []:
            if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                messages.append({"role": msg['role'], "content": msg['content']})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Build API call parameters
        api_params = {
            "model": "gpt-5.2",
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": 800
        }

        # Add function calling tools - metric tools always available, web search if configured
        tools = [
            {"type": "function", "function": LIST_METRICS_FUNCTION},
            {"type": "function", "function": GET_METRIC_FUNCTION}
        ]
        if web_search_available:
            tools.append({"type": "function", "function": SEARCH_FUNCTION_DEFINITION})

        api_params["tools"] = tools
        api_params["tool_choice"] = "auto"

        # API call with tool calling loop (handles multiple rounds of tool calls)
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        ai_message = None

        print(f"[CHAT] Starting chat request for message: {user_message[:100]}...")
        print(f"[CHAT] Using model: {api_params['model']}")
        print(f"[CHAT] Web search enabled: {web_search_available}")
        print(f"[CHAT] Conversation history length: {len(conversation_history)}")

        while iteration < max_iterations:
            iteration += 1
            print(f"[CHAT] API call iteration {iteration}/{max_iterations}")

            response = user_client.chat.completions.create(**api_params)
            response_message = response.choices[0].message

            # Log full response details
            print(f"[CHAT] Response finish_reason: {response.choices[0].finish_reason}")
            print(f"[CHAT] Response message role: {response_message.role}")
            print(f"[CHAT] Response message content type: {type(response_message.content)}")
            print(f"[CHAT] Response message content: {repr(response_message.content)[:200] if response_message.content else 'None'}")
            print(f"[CHAT] Response has tool_calls: {bool(response_message.tool_calls)}")

            # Check for refusal (some models have this)
            if hasattr(response_message, 'refusal') and response_message.refusal:
                print(f"[CHAT] Model refused: {response_message.refusal}")

            if response_message.tool_calls:
                print(f"[CHAT] Tool calls requested: {[tc.function.name for tc in response_message.tool_calls]}")
                # Process each tool call
                messages.append(response_message)

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    print(f"[CHAT] Executing {function_name} with args: {function_args}")

                    # Route to appropriate function handler
                    if function_name == "search_web":
                        result = execute_search_function(function_args)
                    elif function_name in ["list_available_metrics", "get_metric_data"]:
                        result = execute_metric_function(function_name, function_args)
                    else:
                        result = json.dumps({"error": f"Unknown function: {function_name}"})

                    print(f"[CHAT] {function_name} returned {len(result)} chars")

                    # Add function result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result
                    })

                # Update api_params messages for next iteration
                api_params["messages"] = messages
                api_params["max_completion_tokens"] = 1000  # Allow longer response with tool results
            else:
                # No more tool calls - we have the final response
                ai_message = response_message.content
                print(f"[CHAT] Final response - content is {'present' if ai_message else 'EMPTY/NONE'}")
                if ai_message:
                    print(f"[CHAT] Response preview: {ai_message[:200]}...")
                break

        print(f"[CHAT] Loop completed after {iteration} iterations")

        # Handle case where we exhausted iterations or got None content
        if ai_message is None or ai_message.strip() == "":
            print(f"[CHAT] ERROR: Model returned empty content after {iteration} iterations")
            print(f"[CHAT] Attempting retry without tools...")

            # Retry without tools - simpler request
            try:
                retry_params = {
                    "model": "gpt-5.2",
                    "messages": [
                        {"role": "system", "content": "You are a helpful financial markets assistant. Answer the user's question concisely."},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7,
                    "max_completion_tokens": 500
                }
                retry_response = user_client.chat.completions.create(**retry_params)
                retry_content = retry_response.choices[0].message.content
                print(f"[CHAT] Retry finish_reason: {retry_response.choices[0].finish_reason}")
                print(f"[CHAT] Retry content: {repr(retry_content)[:200] if retry_content else 'None'}")

                if retry_content and retry_content.strip():
                    ai_message = retry_content
                    print(f"[CHAT] Retry successful!")
                else:
                    print(f"[CHAT] Retry also returned empty content!")
                    ai_message = "I apologize, but the AI service is returning empty responses. This appears to be a temporary issue with the GPT-5.2 model. Please try again in a moment."
            except Exception as retry_error:
                print(f"[CHAT] Retry failed with error: {retry_error}")
                ai_message = f"I apologize, but I wasn't able to generate a response. Error details: Model returned empty content."
        else:
            # Filter out any reasoning artifacts that might leak through
            import re
            lines = ai_message.split('\n')
            filtered_lines = []
            for line in lines:
                # Skip lines that look like internal reasoning
                if re.match(r'^(Need |Oops |Let me |I should |Thinking:|<think>|</think>)', line.strip()):
                    print(f"[CHAT] Filtering out reasoning artifact: {line[:50]}")
                    continue
                filtered_lines.append(line)
            ai_message = '\n'.join(filtered_lines).strip()

            # If filtering removed everything, use fallback
            if not ai_message:
                print(f"[CHAT] WARNING: All content was filtered as reasoning artifacts")
                ai_message = "I apologize, but I wasn't able to generate a response. Please try asking your question again."

        return jsonify({
            'message': ai_message,
            'timestamp': datetime.now().isoformat(),
            'web_search_enabled': web_search_available
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Initialize the scheduler for automatic daily refresh
    init_scheduler()

    # Run Flask app
    # Note: For production, use Gunicorn with --preload flag:
    # gunicorn -w 1 --preload dashboard:app
    app.run(debug=True, host='0.0.0.0', port=5000)
