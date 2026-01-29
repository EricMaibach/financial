#!/usr/bin/env python3
"""
Example analysis script showing how to use the collected credit signals data.

This demonstrates:
- Loading the collected data
- Combining multiple signals
- Basic trend analysis
- Visualization
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def load_all_signals(data_dir="data"):
    """
    Load all collected signals into a single DataFrame.

    Args:
        data_dir: Directory containing CSV files

    Returns:
        DataFrame with all signals merged by date
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        print(f"Data directory not found: {data_path}")
        return None

    # Dictionary to store all dataframes
    signals = {}

    # Load FRED spreads
    fred_files = {
        'high_yield_spread.csv': 'hy_spread',
        'investment_grade_spread.csv': 'ig_spread',
        'ccc_spread.csv': 'ccc_spread'
    }

    for filename, column_name in fred_files.items():
        filepath = data_path / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            df.columns = ['date', column_name]
            signals[column_name] = df

    # Load ETF prices
    etf_files = {
        'leveraged_loan_etf.csv': 'bkln_price',
        'high_yield_credit_etf.csv': 'hyg_price',
        'investment_grade_credit_etf.csv': 'lqd_price',
        'treasury_7_10yr_etf.csv': 'ief_price'
    }

    for filename, column_name in etf_files.items():
        filepath = data_path / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            df.columns = ['date', column_name]
            signals[column_name] = df

    # Load calculated spreads
    spread_files = {
        'hyg_treasury_spread.csv': 'hyg_ief_spread',
        'lqd_treasury_spread.csv': 'lqd_ief_spread'
    }

    for filename, column_name in spread_files.items():
        filepath = data_path / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            df.columns = ['date', column_name]
            signals[column_name] = df

    if not signals:
        print("No signal files found")
        return None

    # Merge all signals on date
    combined_df = None
    for signal_name, df in signals.items():
        if combined_df is None:
            combined_df = df
        else:
            combined_df = pd.merge(combined_df, df, on='date', how='outer')

    combined_df = combined_df.sort_values('date')

    return combined_df


def calculate_spread_changes(df, periods=[1, 5, 20]):
    """
    Calculate changes in spreads over different periods.

    Args:
        df: DataFrame with spread data
        periods: List of periods (in days) to calculate changes

    Returns:
        DataFrame with additional change columns
    """
    spread_columns = [col for col in df.columns if 'spread' in col.lower()]

    for col in spread_columns:
        for period in periods:
            change_col = f"{col}_change_{period}d"
            df[change_col] = df[col].diff(period)

    return df


def print_latest_signals(df):
    """Print the most recent signal values."""
    if df is None or df.empty:
        print("No data available")
        return

    latest = df.iloc[-1]

    print("\n" + "=" * 60)
    print(f"Latest Credit Market Signals - {latest['date'].date()}")
    print("=" * 60)

    if 'hy_spread' in df.columns:
        print(f"\nHigh-Yield Spread:        {latest['hy_spread']:.2f} bp")

    if 'ig_spread' in df.columns:
        print(f"Investment Grade Spread:  {latest['ig_spread']:.2f} bp")

    if 'ccc_spread' in df.columns:
        print(f"CCC-Rated Spread:         {latest['ccc_spread']:.2f} bp")

    if 'bkln_price' in df.columns:
        print(f"\nBKLN (Lev Loan) Price:    ${latest['bkln_price']:.2f}")

    if 'hyg_ief_spread' in df.columns:
        print(f"\nHYG vs IEF Spread:        {latest['hyg_ief_spread']:.2f}%")

    if 'lqd_ief_spread' in df.columns:
        print(f"LQD vs IEF Spread:        {latest['lqd_ief_spread']:.2f}%")

    print("\n" + "=" * 60)


def plot_spread_trends(df, days=90):
    """
    Plot credit spread trends.

    Args:
        df: DataFrame with spread data
        days: Number of recent days to plot
    """
    if df is None or df.empty:
        print("No data available for plotting")
        return

    # Filter to recent days
    recent_df = df.tail(days)

    # Create subplots
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # Plot FRED spreads
    ax1 = axes[0]
    if 'hy_spread' in recent_df.columns:
        ax1.plot(recent_df['date'], recent_df['hy_spread'], label='High Yield', linewidth=2)
    if 'ig_spread' in recent_df.columns:
        ax1.plot(recent_df['date'], recent_df['ig_spread'], label='Investment Grade', linewidth=2)
    if 'ccc_spread' in recent_df.columns:
        ax1.plot(recent_df['date'], recent_df['ccc_spread'], label='CCC Rated', linewidth=2)

    ax1.set_title('Credit Spreads (FRED Data)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Spread (bp)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot ETF prices
    ax2 = axes[1]
    if 'bkln_price' in recent_df.columns:
        ax2.plot(recent_df['date'], recent_df['bkln_price'], label='BKLN (Lev Loans)', linewidth=2)
    if 'hyg_price' in recent_df.columns:
        ax2_twin = ax2.twinx()
        ax2_twin.plot(recent_df['date'], recent_df['hyg_price'], label='HYG (High Yield)',
                      linewidth=2, color='orange', alpha=0.7)
        ax2_twin.set_ylabel('HYG Price ($)', fontsize=12)
        ax2_twin.legend(loc='upper right')

    ax2.set_title('Credit ETF Prices', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('BKLN Price ($)', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('credit_signals_plot.png', dpi=150, bbox_inches='tight')
    print("\nPlot saved to: credit_signals_plot.png")
    plt.show()


def analyze_stress_indicators(df):
    """
    Analyze indicators of credit market stress.

    Args:
        df: DataFrame with spread data
    """
    if df is None or df.empty:
        print("No data available")
        return

    print("\n" + "=" * 60)
    print("Credit Market Stress Analysis")
    print("=" * 60)

    latest = df.iloc[-1]

    # Calculate percentiles (relative to historical data)
    if 'hy_spread' in df.columns:
        hy_percentile = (df['hy_spread'] < latest['hy_spread']).sum() / len(df) * 100
        print(f"\nHigh-Yield Spread Percentile: {hy_percentile:.1f}%")
        if hy_percentile > 90:
            print("  ⚠️  ELEVATED - High yield spreads in top 10% of range")
        elif hy_percentile < 10:
            print("  ℹ️  LOW - High yield spreads in bottom 10% of range")

    if 'ccc_spread' in df.columns and 'hy_spread' in df.columns:
        ccc_hy_ratio = latest['ccc_spread'] / latest['hy_spread']
        print(f"\nCCC/HY Spread Ratio: {ccc_hy_ratio:.2f}")
        if ccc_hy_ratio > 2.5:
            print("  ⚠️  ELEVATED - CCC spreads widening relative to broader HY")

    # Check for recent spread widening
    if 'hy_spread' in df.columns and len(df) > 20:
        recent_20d = df.tail(20)
        spread_change = latest['hy_spread'] - recent_20d['hy_spread'].iloc[0]
        print(f"\n20-Day HY Spread Change: {spread_change:+.2f} bp")
        if spread_change > 50:
            print("  ⚠️  WARNING - Significant spread widening detected")
        elif spread_change < -50:
            print("  ✓ Spreads tightening significantly")

    print("\n" + "=" * 60)


def main():
    """Main analysis function."""
    print("Loading credit signals data...")

    df = load_all_signals()

    if df is None or df.empty:
        print("\nNo data found. Run credit_signals.py first to collect data.")
        return

    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Calculate spread changes
    df = calculate_spread_changes(df)

    # Print latest signals
    print_latest_signals(df)

    # Analyze stress indicators
    analyze_stress_indicators(df)

    # Plot trends
    try:
        plot_spread_trends(df, days=90)
    except Exception as e:
        print(f"\nNote: Could not create plot: {e}")
        print("Install matplotlib for visualization: pip install matplotlib")


if __name__ == '__main__':
    main()
