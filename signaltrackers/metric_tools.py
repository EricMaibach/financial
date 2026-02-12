#!/usr/bin/env python3
"""
Metric data tools for the AI chatbot.
Provides function calling tools to access market data on demand.
"""

import os
import json
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

# Function definitions for OpenAI function calling
LIST_METRICS_FUNCTION = {
    "name": "list_available_metrics",
    "description": "Get a list of all available market metrics/data series that can be queried. Returns metric IDs, friendly names, and brief descriptions. Use this first to discover what data is available before fetching specific metrics.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

GET_METRIC_FUNCTION = {
    "name": "get_metric_data",
    "description": "Get detailed data for a specific market metric. Returns current value, historical percentile, recent changes, min/max, and optionally the full historical time series. Use this when you need to analyze a specific indicator in depth.",
    "parameters": {
        "type": "object",
        "properties": {
            "metric_id": {
                "type": "string",
                "description": "The metric ID to fetch (e.g., 'gold_price', 'high_yield_spread', 'vix_price'). Use list_available_metrics first to see valid IDs."
            },
            "include_time_series": {
                "type": "boolean",
                "description": "Whether to include the full historical time series data. Default false for quick stats only, set true when you need to analyze historical patterns.",
                "default": False
            }
        },
        "required": ["metric_id"]
    }
}

# Metric descriptions for the list function
METRIC_INFO = {
    'divergence_gap': {
        'category': 'Divergence Analysis',
        'description': 'Gap between gold-implied credit spreads and actual spreads - key crisis indicator'
    },
    'high_yield_spread': {
        'category': 'Credit Markets',
        'description': 'Junk bond yield premium over Treasuries (basis points) - primary credit stress gauge'
    },
    'investment_grade_spread': {
        'category': 'Credit Markets',
        'description': 'Investment-grade corporate bond spread over Treasuries'
    },
    'ccc_spread': {
        'category': 'Credit Markets',
        'description': 'CCC-rated (near-default) bond spreads - extreme distress indicator'
    },
    'gold_price': {
        'category': 'Safe Havens',
        'description': 'Gold price per ounce (via GLD ETF) - crisis hedge and fear gauge'
    },
    'silver_price': {
        'category': 'Safe Havens',
        'description': 'Silver price (via SLV ETF) - industrial/precious metal'
    },
    'bitcoin_price': {
        'category': 'Risk Assets',
        'description': 'Bitcoin price - risk appetite and liquidity gauge'
    },
    'vix_price': {
        'category': 'Volatility',
        'description': 'VIX volatility index - equity market fear gauge'
    },
    'sp500_price': {
        'category': 'Equities',
        'description': 'S&P 500 index (via SPY ETF)'
    },
    'nasdaq_price': {
        'category': 'Equities',
        'description': 'Nasdaq 100 index (via QQQ ETF) - tech-heavy'
    },
    'russell2000_price': {
        'category': 'Equities',
        'description': 'Russell 2000 small-cap index (via IWM ETF)'
    },
    'treasury_10y_yield': {
        'category': 'Fixed Income',
        'description': '10-Year Treasury yield'
    },
    'treasury_2y_yield': {
        'category': 'Fixed Income',
        'description': '2-Year Treasury yield'
    },
    'yield_curve_10y2y': {
        'category': 'Yield Curve',
        'description': '10Y minus 2Y Treasury spread - recession predictor'
    },
    'yield_curve_10y3m': {
        'category': 'Yield Curve',
        'description': '10Y minus 3M Treasury spread - Fed\'s preferred measure'
    },
    'usdjpy_price': {
        'category': 'Yen Carry Trade',
        'description': 'USD/JPY exchange rate - carry trade indicator'
    },
    'japan_10y_yield': {
        'category': 'Yen Carry Trade',
        'description': 'Japan 10Y government bond yield - BOJ policy gauge'
    },
    'dxy_price': {
        'category': 'Currency',
        'description': 'US Dollar Index (DXY) - dollar strength'
    },
    'oil_price': {
        'category': 'Commodities',
        'description': 'Crude oil price (via USO ETF)'
    },
    'leveraged_loan_etf': {
        'category': 'Credit Markets',
        'description': 'Leveraged loan ETF (BKLN) - floating rate credit'
    },
    'market_breadth_ratio': {
        'category': 'Market Internals',
        'description': 'Equal-weight vs cap-weight S&P 500 ratio - concentration measure'
    },
    'qqq_spy_ratio': {
        'category': 'Market Ratios',
        'description': 'Nasdaq/S&P 500 ratio - tech leadership'
    },
    'initial_claims': {
        'category': 'Labor Market',
        'description': 'Weekly initial jobless claims - leading recession indicator'
    },
    'continuing_claims': {
        'category': 'Labor Market',
        'description': 'Continuing unemployment claims'
    },
    'consumer_confidence': {
        'category': 'Economic Indicators',
        'description': 'University of Michigan Consumer Sentiment'
    },
    'm2_money_supply': {
        'category': 'Economic Indicators',
        'description': 'M2 money supply - Fed liquidity measure'
    },
    'cpi': {
        'category': 'Economic Indicators',
        'description': 'Consumer Price Index - inflation measure'
    },
    'us_recessions': {
        'category': 'Economic History',
        'description': 'Historical US recession periods with dates, duration, and economic impact data'
    },
    'fed_balance_sheet': {
        'category': 'Fed Liquidity',
        'description': 'Federal Reserve total assets (billions) - QE/QT gauge, key liquidity indicator'
    },
    'reverse_repo': {
        'category': 'Fed Liquidity',
        'description': 'Overnight Reverse Repo Facility usage (billions) - excess liquidity measure'
    },
    'nfci': {
        'category': 'Financial Conditions',
        'description': 'Chicago Fed National Financial Conditions Index - comprehensive stress measure (positive=tight, negative=loose)'
    },
    'fear_greed_index': {
        'category': 'Crypto Sentiment',
        'description': 'Crypto Fear & Greed Index (0-100) - sentiment indicator (0=extreme fear, 100=extreme greed)'
    },
    'btc_gold_ratio': {
        'category': 'Crypto',
        'description': 'Bitcoin/Gold ratio - BTC priced in ounces of gold, compares two store-of-value assets'
    },
    'real_yield_10y': {
        'category': 'Safe Haven Drivers',
        'description': '10-Year TIPS yield (real yield) - key gold driver, gold has inverse correlation with real yields'
    },
    'breakeven_inflation_10y': {
        'category': 'Safe Haven Drivers',
        'description': '10-Year breakeven inflation rate - market inflation expectations, supports gold when rising'
    },
    'gdx_gld_ratio': {
        'category': 'Safe Haven Drivers',
        'description': 'Gold miners (GDX) vs gold (GLD) ratio - miners lead gold at turning points, rising = bullish'
    },
    'treasury_10y': {
        'category': 'Fixed Income',
        'description': '10-Year Treasury nominal yield (DGS10) - benchmark risk-free rate, nominal = real yield + breakeven inflation'
    }
}


def load_csv_data(filename):
    """Load CSV data from the data directory."""
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


def calculate_percentile(values, current_value):
    """Calculate historical percentile for a value (pure Python, no scipy)."""
    if not values or current_value is None:
        return None
    # Count how many values are less than or equal to current_value
    count_below_or_equal = sum(1 for v in values if v <= current_value)
    return float(count_below_or_equal / len(values) * 100)


def execute_list_metrics():
    """Execute the list_available_metrics function."""
    # Get actual available files
    available_files = set()
    if DATA_DIR.exists():
        available_files = {f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')}

    # Build response with available metrics
    metrics_by_category = {}

    for metric_id, info in METRIC_INFO.items():
        if metric_id in available_files or metric_id == 'divergence_gap':
            category = info['category']
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append({
                'id': metric_id,
                'description': info['description']
            })

    # Also add any metrics that exist but aren't in METRIC_INFO
    for metric_id in available_files:
        if metric_id not in METRIC_INFO:
            friendly_name = metric_id.replace('_', ' ').title()
            if 'Other' not in metrics_by_category:
                metrics_by_category['Other'] = []
            metrics_by_category['Other'].append({
                'id': metric_id,
                'description': friendly_name
            })

    return json.dumps({
        'metrics_by_category': metrics_by_category,
        'total_metrics': sum(len(m) for m in metrics_by_category.values()),
        'usage': 'Use get_metric_data with a metric id to fetch detailed data'
    }, indent=2)


def execute_get_metric_data(metric_id, include_time_series=False):
    """Execute the get_metric_data function."""

    # Special handling for divergence_gap (calculated metric)
    if metric_id == 'divergence_gap':
        return _get_divergence_gap_data(include_time_series)

    # Special handling for us_recessions (date range data, not time series)
    if metric_id == 'us_recessions':
        return _get_recession_data()

    # Try loading the metric
    filename = f"{metric_id}.csv"
    df = load_csv_data(filename)

    if df is None or len(df) == 0:
        return json.dumps({'error': f'Metric "{metric_id}" not found or no data available'})

    # Get value column
    value_column = df.columns[1]
    values = df[value_column].dropna().tolist()
    dates = df['date'].dt.strftime('%Y-%m-%d').tolist()

    if not values:
        return json.dumps({'error': f'No data available for "{metric_id}"'})

    current_value = values[-1]

    # Calculate statistics
    result = {
        'metric_id': metric_id,
        'friendly_name': metric_id.replace('_', ' ').title(),
        'current_value': round(current_value, 4) if current_value else None,
        'percentile': round(calculate_percentile(values, current_value), 1),
        'data_points': len(values),
        'date_range': {
            'start': dates[0] if dates else None,
            'end': dates[-1] if dates else None
        },
        'statistics': {
            'min': round(min(values), 4),
            'max': round(max(values), 4),
            'average': round(sum(values) / len(values), 4),
            'median': round(sorted(values)[len(values)//2], 4)
        },
        'recent_changes': {}
    }

    # Calculate changes
    if len(values) >= 2:
        result['recent_changes']['1_day'] = round(values[-1] - values[-2], 4)
        result['recent_changes']['1_day_pct'] = round(((values[-1] / values[-2]) - 1) * 100, 2) if values[-2] != 0 else None

    if len(values) >= 5:
        result['recent_changes']['5_day'] = round(values[-1] - values[-5], 4)
        result['recent_changes']['5_day_pct'] = round(((values[-1] / values[-5]) - 1) * 100, 2) if values[-5] != 0 else None

    if len(values) >= 30:
        result['recent_changes']['30_day'] = round(values[-1] - values[-30], 4)
        result['recent_changes']['30_day_pct'] = round(((values[-1] / values[-30]) - 1) * 100, 2) if values[-30] != 0 else None

    if len(values) >= 252:  # ~1 year of trading days
        result['recent_changes']['1_year'] = round(values[-1] - values[-252], 4)
        result['recent_changes']['1_year_pct'] = round(((values[-1] / values[-252]) - 1) * 100, 2) if values[-252] != 0 else None

    # Add description if available
    if metric_id in METRIC_INFO:
        result['description'] = METRIC_INFO[metric_id]['description']
        result['category'] = METRIC_INFO[metric_id]['category']

    # Include full time series if requested
    if include_time_series:
        result['time_series'] = {
            'dates': dates,
            'values': [round(v, 4) for v in values]
        }

    return json.dumps(result, indent=2)


def _get_divergence_gap_data(include_time_series=False):
    """Calculate and return divergence gap data."""
    gold_df = load_csv_data('gold_price.csv')
    hy_df = load_csv_data('high_yield_spread.csv')

    if gold_df is None or hy_df is None:
        return json.dumps({'error': 'Cannot calculate divergence gap - missing gold or high yield data'})

    # Merge on date
    merged = pd.merge(gold_df, hy_df, on='date', how='inner')

    if len(merged) == 0:
        return json.dumps({'error': 'No overlapping data for divergence gap calculation'})

    # Calculate gold-implied spread and divergence gap
    gold_prices = merged['gold_price'].values
    hy_spreads = merged['high_yield_spread'].values * 100  # Convert to bp

    gold_implied = ((gold_prices / 200) ** 1.5) * 400
    divergence = gold_implied - hy_spreads

    values = divergence.tolist()
    dates = merged['date'].dt.strftime('%Y-%m-%d').tolist()

    current_value = values[-1]

    result = {
        'metric_id': 'divergence_gap',
        'friendly_name': 'Divergence Gap',
        'description': 'Gap between gold-implied credit spreads and actual HY spreads (basis points). Positive = gold pricing more risk than credit markets.',
        'category': 'Divergence Analysis',
        'current_value': round(current_value, 1),
        'percentile': round(calculate_percentile(values, current_value), 1),
        'data_points': len(values),
        'date_range': {
            'start': dates[0],
            'end': dates[-1]
        },
        'statistics': {
            'min': round(min(values), 1),
            'max': round(max(values), 1),
            'average': round(sum(values) / len(values), 1)
        },
        'recent_changes': {},
        'interpretation': {
            'current_signal': 'EXTREME DIVERGENCE' if current_value > 900 else 'HIGH DIVERGENCE' if current_value > 600 else 'MODERATE DIVERGENCE' if current_value > 300 else 'NORMAL',
            'note': 'Gap >900 bp is unprecedented. Gold is pricing crisis while credit markets remain calm.'
        }
    }

    # Calculate changes
    if len(values) >= 2:
        result['recent_changes']['1_day'] = round(values[-1] - values[-2], 1)
    if len(values) >= 5:
        result['recent_changes']['5_day'] = round(values[-1] - values[-5], 1)
    if len(values) >= 30:
        result['recent_changes']['30_day'] = round(values[-1] - values[-30], 1)

    # Include full time series if requested
    if include_time_series:
        result['time_series'] = {
            'dates': dates,
            'values': [round(v, 1) for v in values]
        }

    return json.dumps(result, indent=2)


def _get_recession_data():
    """Return historical US recession data."""
    filepath = DATA_DIR / 'us_recessions.csv'
    if not filepath.exists():
        return json.dumps({'error': 'US recession data not available'})

    try:
        df = pd.read_csv(filepath)

        # Convert to list of recession periods
        recessions = []
        for _, row in df.iterrows():
            recession = {
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'duration_months': int(row['duration_months']) if pd.notna(row['duration_months']) else None,
                'name': row['name'] if pd.notna(row['name']) else None,
                'peak_unemployment_pct': float(row['peak_unemployment_pct']) if pd.notna(row.get('peak_unemployment_pct')) else None,
                'gdp_decline_pct': float(row['gdp_decline_pct']) if pd.notna(row.get('gdp_decline_pct')) else None,
                'notes': row['notes'] if pd.notna(row.get('notes')) else None
            }
            recessions.append(recession)

        # Get recent recessions (post-1945 are most relevant)
        modern_recessions = [r for r in recessions if r['start_date'] >= '1945-01-01']

        result = {
            'metric_id': 'us_recessions',
            'friendly_name': 'US Recession History',
            'description': 'Historical US recession periods from NBER. Useful for correlating with yield curve inversions and other indicators.',
            'category': 'Economic History',
            'total_recessions': len(recessions),
            'modern_recessions_count': len(modern_recessions),
            'date_range': {
                'earliest': recessions[0]['start_date'] if recessions else None,
                'latest': recessions[-1]['end_date'] if recessions else None
            },
            'modern_recessions': modern_recessions,  # Post-1945 recessions with full detail
            'all_recessions': recessions  # Full history back to 1857
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({'error': f'Error loading recession data: {str(e)}'})


def execute_metric_function(function_name, function_args):
    """Execute a metric function based on the function name and args."""
    if function_name == "list_available_metrics":
        return execute_list_metrics()
    elif function_name == "get_metric_data":
        metric_id = function_args.get('metric_id', '')
        include_time_series = function_args.get('include_time_series', False)
        return execute_get_metric_data(metric_id, include_time_series)
    else:
        return json.dumps({'error': f'Unknown function: {function_name}'})
