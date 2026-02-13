#!/usr/bin/env python3
"""
Comprehensive Market Signals Tracker

Tracks the historic market divergence between:
- Credit markets (spreads, corporate debt)
- Equity markets (indices, breadth, volatility)
- Safe havens (Gold, Bitcoin)
- Currency & sovereign risk (Dollar, yields)

This tracker monitors one of the most extreme market divergences in financial history:
- Gold at $4,500+ (extreme structural concerns)
- Credit spreads at 276bp (extreme complacency)
- Bitcoin weak (liquidity tight)
- Stocks up but narrow (AI bubble)

Data is appended daily to CSV files for historical tracking.
"""

import os
import sys
from datetime import datetime, timedelta
import pytz
import pandas as pd
import requests
from pathlib import Path
import numpy as np
import time

# Optional imports with error handling
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    print("Warning: yfinance not installed. ETF data collection will be unavailable.")
    print("Install with: pip install yfinance")


class MarketSignalsTracker:
    """Comprehensive market signals tracker for divergence monitoring."""

    def __init__(self, data_dir="data", fred_api_key=None):
        """
        Initialize the tracker.

        Args:
            data_dir: Directory to store CSV files
            fred_api_key: FRED API key (can also be set via FRED_API_KEY env variable)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Get FRED API key from parameter or environment
        self.fred_api_key = fred_api_key or os.environ.get('FRED_API_KEY')
        if not self.fred_api_key:
            print("Warning: FRED_API_KEY not set. FRED data collection will be unavailable.")
            print("Get a free API key at: https://fred.stlouisfed.org/docs/api/api_key.html")
            print("Set it with: export FRED_API_KEY='your_key_here'")

        # FRED series IDs - Credit Spreads, Economic Indicators, and International Rates
        self.fred_series = {
            # Credit Spreads
            'high_yield_spread': 'BAMLH0A0HYM2',
            'investment_grade_spread': 'BAMLC0A0CM',
            'ccc_spread': 'BAMLH0A3HYC',
            # International Government Bond Yields (for carry trade and rate differential monitoring)
            'japan_10y_yield': 'IRLTLT01JPM156N',      # Japan 10-Year
            'germany_10y_yield': 'IRLTLT01DEM156N',    # Germany 10-Year (Bund)
            # Yield Curve (Recession Indicators)
            'yield_curve_10y2y': 'T10Y2Y',  # 10-Year Treasury Constant Maturity Minus 2-Year
            'yield_curve_10y3m': 'T10Y3M',  # 10-Year Treasury Constant Maturity Minus 3-Month
            # Labor Market
            'initial_claims': 'ICSA',  # Initial Jobless Claims (Weekly)
            'continuing_claims': 'CCSA',  # Continuing Claims (Insured Unemployment)
            # Economic Indicators
            'consumer_confidence': 'UMCSENT',  # University of Michigan Consumer Sentiment
            'm2_money_supply': 'M2SL',  # M2 Money Stock (Billions of Dollars)
            'cpi': 'CPIAUCSL',  # Consumer Price Index for All Urban Consumers
            # Fed Liquidity & Financial Conditions
            'fed_balance_sheet': 'WALCL',  # Federal Reserve Total Assets (Billions)
            'reverse_repo': 'RRPONTSYD',  # Overnight Reverse Repurchase Agreements (Billions)
            'nfci': 'NFCI',  # Chicago Fed National Financial Conditions Index
            # Real Yields & Inflation Expectations (Gold Drivers)
            'real_yield_10y': 'DFII10',  # 10-Year Real Interest Rate (TIPS yield)
            'breakeven_inflation_10y': 'T10YIE',  # 10-Year Breakeven Inflation Rate
            'treasury_10y': 'DGS10',  # 10-Year Treasury Constant Maturity Rate (nominal yield)
            # Federal Reserve Policy Rate
            'fed_funds_rate': 'FEDFUNDS'  # Effective Federal Funds Rate (Monthly)
        }

        # ETF tickers organized by category
        self.etf_tickers = {
            # Credit Markets
            'leveraged_loan': 'BKLN',
            'high_yield_credit': 'HYG',
            'investment_grade_credit': 'LQD',

            # Treasury/Safe Haven
            'treasury_7_10yr': 'IEF',
            'treasury_20yr': 'TLT',
            'treasury_short': 'SHY',
            'tips_inflation': 'TIP',

            # Equity Indices
            'sp500': 'SPY',
            'sp500_equal_weight': 'RSP',
            'small_cap': 'IWM',
            'nasdaq': 'QQQ',

            # Concentration/Style ETFs (AI/Tech concentration tracking)
            'semiconductor': 'SMH',      # VanEck Semiconductor ETF
            'tech_sector': 'XLK',        # Technology Select Sector SPDR
            'growth': 'IWF',             # iShares Russell 1000 Growth
            'value': 'IWD',              # iShares Russell 1000 Value

            # Key Sectors
            'financials_sector': 'XLF',  # Financial Select Sector SPDR
            'energy_sector': 'XLE',      # Energy Select Sector SPDR

            # Volatility
            'vix': '^VIX',

            # Precious Metals
            'gold': 'GLD',
            'gold_miners': 'GDX',
            'silver': 'SLV',

            # Crypto
            'bitcoin': 'BTC-USD',
            'ethereum': 'ETH-USD',

            # Currency
            'dollar_index': 'UUP',
            'usdjpy': 'JPY=X',            # USD/JPY exchange rate (yen carry trade)
            'eurusd': 'EURUSD=X',         # EUR/USD exchange rate

            # Commodities
            'commodities': 'DBC',
            'oil': 'USO'
        }

    def fetch_fred_data(self, series_id, start_date=None):
        """
        Fetch data from FRED API.

        Args:
            series_id: FRED series identifier
            start_date: Start date for data fetch (YYYY-MM-DD)

        Returns:
            DataFrame with date and value columns
        """
        if not self.fred_api_key:
            print(f"Skipping FRED series {series_id}: API key not available")
            return None

        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': self.fred_api_key,
            'file_type': 'json'
        }

        if start_date:
            params['observation_start'] = start_date

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'observations' not in data:
                print(f"No observations found for {series_id}")
                return None

            df = pd.DataFrame(data['observations'])
            df = df[['date', 'value']]
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna()

            return df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching FRED data for {series_id}: {e}")
            return None

    def fetch_etf_data(self, ticker, start_date=None, end_date=None):
        """
        Fetch ETF data using yfinance.

        Args:
            ticker: ETF ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with date and close price
        """
        if not YF_AVAILABLE:
            print(f"Skipping ETF {ticker}: yfinance not available")
            return None

        try:
            etf = yf.Ticker(ticker)

            if start_date:
                df = etf.history(start=start_date, end=end_date)
            else:
                df = etf.history(period="5d")

            if df.empty:
                print(f"No data returned for {ticker}")
                return None

            df = df[['Close']].copy()
            df.reset_index(inplace=True)
            df.columns = ['date', 'close']
            df['date'] = pd.to_datetime(df['date']).dt.date

            return df

        except Exception as e:
            print(f"Error fetching ETF data for {ticker}: {e}")
            return None

    def calculate_etf_spreads(self, credit_etf_data, treasury_etf_data):
        """Calculate spread between credit ETF and treasury ETF yields."""
        if credit_etf_data is None or treasury_etf_data is None:
            return None

        merged = pd.merge(
            credit_etf_data,
            treasury_etf_data,
            on='date',
            suffixes=('_credit', '_treasury')
        )

        # Simple ratio-based spread proxy
        merged['spread_proxy'] = (merged['close_credit'] / merged['close_treasury'] - 1) * 100

        return merged[['date', 'spread_proxy']]

    def get_last_date_in_file(self, filepath):
        """Get the last date in an existing CSV file."""
        if not filepath.exists():
            return None

        try:
            df = pd.read_csv(filepath)
            if df.empty:
                return None
            df['date'] = pd.to_datetime(df['date'])
            return df['date'].max()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None

    def append_to_csv(self, df, filepath, date_column='date'):
        """Append new data to CSV file, avoiding duplicates. Updates today's data if it exists."""
        if df is None or df.empty:
            print(f"No data to append to {filepath}")
            return

        df[date_column] = pd.to_datetime(df[date_column])
        today = pd.Timestamp.now().normalize()  # Today at midnight for comparison

        if filepath.exists():
            existing_df = pd.read_csv(filepath)
            existing_df[date_column] = pd.to_datetime(existing_df[date_column])

            # Separate today's data from historical data
            existing_historical = existing_df[existing_df[date_column].dt.normalize() < today]

            # Get new data that doesn't exist in historical records
            new_data = df[~df[date_column].isin(existing_historical[date_column])]

            if new_data.empty:
                print(f"No new data to append to {filepath.name}")
                return

            # Check if we're updating today's data
            today_in_new = new_data[new_data[date_column].dt.normalize() == today]
            today_in_existing = existing_df[existing_df[date_column].dt.normalize() == today]

            if not today_in_new.empty and not today_in_existing.empty:
                # We're updating today's data
                combined_df = pd.concat([existing_historical, new_data], ignore_index=True)
                combined_df = combined_df.sort_values(date_column)
                combined_df.to_csv(filepath, index=False)
                print(f"Updated today's data + added {len(new_data) - len(today_in_new)} new rows to {filepath.name}")
            else:
                # Normal append (no update needed)
                combined_df = pd.concat([existing_df, new_data], ignore_index=True)
                combined_df = combined_df.sort_values(date_column)
                combined_df.to_csv(filepath, index=False)
                print(f"Added {len(new_data)} new rows to {filepath.name}")
        else:
            df = df.sort_values(date_column)
            df.to_csv(filepath, index=False)
            print(f"Created {filepath.name} with {len(df)} rows")

    def collect_fred_signals(self, lookback_days=12775):
        """Collect all FRED-based credit signals.

        Args:
            lookback_days: Number of days to look back (default: 12775, ~35 years)
        """
        eastern = pytz.timezone('US/Eastern')
        print("\n=== Collecting FRED Credit Data ===")

        for signal_name, series_id in self.fred_series.items():
            print(f"\nFetching {signal_name} ({series_id})...")

            filepath = self.data_dir / f"{signal_name}.csv"
            last_date = self.get_last_date_in_file(filepath)

            # Always fetch based on lookback_days from today
            start_date = (datetime.now(eastern) - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

            if last_date:
                print(f"Last date in file: {last_date.date()}, fetching {lookback_days} days from {start_date}")
            else:
                print(f"No existing data, fetching {lookback_days} days from {start_date}")

            df = self.fetch_fred_data(series_id, start_date=start_date)

            if df is not None and not df.empty:
                df.columns = ['date', signal_name]
                self.append_to_csv(df, filepath)

    def collect_etf_signals(self, lookback_days=12775):
        """Collect all ETF-based signals.

        Args:
            lookback_days: Number of days to look back (default: 12775, ~35 years)
        """
        eastern = pytz.timezone('US/Eastern')
        print("\n=== Collecting Market ETF Data ===")

        for signal_name, ticker in self.etf_tickers.items():
            print(f"\nFetching {signal_name} ({ticker})...")

            filepath = self.data_dir / f"{signal_name}_price.csv"
            last_date = self.get_last_date_in_file(filepath)

            # Always fetch based on lookback_days from today
            start_date = (datetime.now(eastern) - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

            if last_date:
                print(f"Last date in file: {last_date.date()}, fetching {lookback_days} days from {start_date}")
            else:
                print(f"No existing data, fetching {lookback_days} days from {start_date}")

            df = self.fetch_etf_data(ticker, start_date=start_date)

            if df is not None and not df.empty:
                df.columns = ['date', f'{signal_name}_price']
                self.append_to_csv(df, filepath)

            # Add delay to avoid rate limiting
            time.sleep(2)

    def fetch_fear_greed_index(self):
        """
        Fetch Crypto Fear & Greed Index from Alternative.me API.

        Returns:
            DataFrame with date and fear_greed_index columns
        """
        url = 'https://api.alternative.me/fng/'
        # Fetch max available history (API provides up to ~2000 days)
        params = {'limit': 2000, 'format': 'json'}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data:
                print("No data found in Fear & Greed API response")
                return None

            records = []
            for item in data['data']:
                records.append({
                    'date': datetime.fromtimestamp(int(item['timestamp'])).strftime('%Y-%m-%d'),
                    'fear_greed_index': float(item['value'])
                })

            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            return df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Fear & Greed Index: {e}")
            return None

    def collect_fear_greed_index(self):
        """Collect Crypto Fear & Greed Index data."""
        print("\n=== Collecting Crypto Fear & Greed Index ===")

        filepath = self.data_dir / "fear_greed_index.csv"

        print("Fetching Fear & Greed Index from Alternative.me...")
        df = self.fetch_fear_greed_index()

        if df is not None and not df.empty:
            self.append_to_csv(df, filepath)
        else:
            print("Failed to fetch Fear & Greed Index data")

    def calculate_derived_metrics(self):
        """Calculate derived metrics like spreads and ratios."""
        print("\n=== Calculating Derived Metrics ===")

        # Credit ETF spreads vs treasuries
        treasury_file = self.data_dir / "treasury_7_10yr_price.csv"
        if treasury_file.exists():
            treasury_df = pd.read_csv(treasury_file)
            treasury_df.columns = ['date', 'close']

            # HYG vs IEF spread
            hyg_file = self.data_dir / "high_yield_credit_price.csv"
            if hyg_file.exists():
                hyg_df = pd.read_csv(hyg_file)
                hyg_df.columns = ['date', 'close']
                spread_df = self.calculate_etf_spreads(hyg_df, treasury_df)
                if spread_df is not None:
                    spread_df.columns = ['date', 'hyg_vs_ief_spread']
                    self.append_to_csv(spread_df, self.data_dir / "hyg_treasury_spread.csv")

            # LQD vs IEF spread
            lqd_file = self.data_dir / "investment_grade_credit_price.csv"
            if lqd_file.exists():
                lqd_df = pd.read_csv(lqd_file)
                lqd_df.columns = ['date', 'close']
                spread_df = self.calculate_etf_spreads(lqd_df, treasury_df)
                if spread_df is not None:
                    spread_df.columns = ['date', 'lqd_vs_ief_spread']
                    self.append_to_csv(spread_df, self.data_dir / "lqd_treasury_spread.csv")

        # Market breadth ratios
        print("\nCalculating market breadth ratios...")

        spy_file = self.data_dir / "sp500_price.csv"
        rsp_file = self.data_dir / "sp500_equal_weight_price.csv"
        iwm_file = self.data_dir / "small_cap_price.csv"
        qqq_file = self.data_dir / "nasdaq_price.csv"

        if spy_file.exists() and rsp_file.exists():
            spy_df = pd.read_csv(spy_file)
            rsp_df = pd.read_csv(rsp_file)
            spy_df.columns = ['date', 'spy']
            rsp_df.columns = ['date', 'rsp']

            merged = pd.merge(spy_df, rsp_df, on='date')
            merged['breadth_ratio'] = (merged['rsp'] / merged['spy']) * 100

            breadth_df = merged[['date', 'breadth_ratio']]
            self.append_to_csv(breadth_df, self.data_dir / "market_breadth_ratio.csv")
            print("Market breadth ratio (RSP/SPY) calculated")

        # Gold/Silver ratio
        gold_file = self.data_dir / "gold_price.csv"
        silver_file = self.data_dir / "silver_price.csv"

        if gold_file.exists() and silver_file.exists():
            gold_df = pd.read_csv(gold_file)
            silver_df = pd.read_csv(silver_file)
            gold_df.columns = ['date', 'gold']
            silver_df.columns = ['date', 'silver']

            merged = pd.merge(gold_df, silver_df, on='date')
            merged['gold_silver_ratio'] = merged['gold'] / merged['silver']

            ratio_df = merged[['date', 'gold_silver_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "gold_silver_ratio.csv")
            print("Gold/Silver ratio calculated")

        # Real yields (TIP vs IEF)
        tip_file = self.data_dir / "tips_inflation_price.csv"
        ief_file = self.data_dir / "treasury_7_10yr_price.csv"

        if tip_file.exists() and ief_file.exists():
            tip_df = pd.read_csv(tip_file)
            ief_df = pd.read_csv(ief_file)
            tip_df.columns = ['date', 'tip']
            ief_df.columns = ['date', 'ief']

            merged = pd.merge(tip_df, ief_df, on='date')
            merged['real_yield_proxy'] = (merged['tip'] / merged['ief'] - 1) * 100

            real_yield_df = merged[['date', 'real_yield_proxy']]
            self.append_to_csv(real_yield_df, self.data_dir / "real_yield_proxy.csv")
            print("Real yield proxy (TIP/IEF) calculated")

        # Market concentration ratios (AI/Tech tracking)
        print("\nCalculating market concentration ratios...")

        # SMH/SPY ratio - Semiconductor concentration
        smh_file = self.data_dir / "semiconductor_price.csv"
        if spy_file.exists() and smh_file.exists():
            spy_df = pd.read_csv(spy_file)
            smh_df = pd.read_csv(smh_file)
            spy_df.columns = ['date', 'spy']
            smh_df.columns = ['date', 'smh']

            merged = pd.merge(spy_df, smh_df, on='date')
            merged['smh_spy_ratio'] = (merged['smh'] / merged['spy']) * 100

            ratio_df = merged[['date', 'smh_spy_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "smh_spy_ratio.csv")
            print("SMH/SPY ratio (semiconductor concentration) calculated")

        # XLK/SPY ratio - Tech sector concentration
        xlk_file = self.data_dir / "tech_sector_price.csv"
        if spy_file.exists() and xlk_file.exists():
            spy_df = pd.read_csv(spy_file)
            xlk_df = pd.read_csv(xlk_file)
            spy_df.columns = ['date', 'spy']
            xlk_df.columns = ['date', 'xlk']

            merged = pd.merge(spy_df, xlk_df, on='date')
            merged['xlk_spy_ratio'] = (merged['xlk'] / merged['spy']) * 100

            ratio_df = merged[['date', 'xlk_spy_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "xlk_spy_ratio.csv")
            print("XLK/SPY ratio (tech sector concentration) calculated")

        # IWF/IWD ratio - Growth vs Value
        iwf_file = self.data_dir / "growth_price.csv"
        iwd_file = self.data_dir / "value_price.csv"
        if iwf_file.exists() and iwd_file.exists():
            iwf_df = pd.read_csv(iwf_file)
            iwd_df = pd.read_csv(iwd_file)
            iwf_df.columns = ['date', 'iwf']
            iwd_df.columns = ['date', 'iwd']

            merged = pd.merge(iwf_df, iwd_df, on='date')
            merged['growth_value_ratio'] = (merged['iwf'] / merged['iwd']) * 100

            ratio_df = merged[['date', 'growth_value_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "growth_value_ratio.csv")
            print("IWF/IWD ratio (growth vs value) calculated")

        # IWM/SPY ratio - Small Cap vs Large Cap
        if spy_file.exists() and iwm_file.exists():
            spy_df = pd.read_csv(spy_file)
            iwm_df = pd.read_csv(iwm_file)
            spy_df.columns = ['date', 'spy']
            iwm_df.columns = ['date', 'iwm']

            merged = pd.merge(spy_df, iwm_df, on='date')
            merged['iwm_spy_ratio'] = (merged['iwm'] / merged['spy']) * 100

            ratio_df = merged[['date', 'iwm_spy_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "iwm_spy_ratio.csv")
            print("IWM/SPY ratio (small cap vs large cap) calculated")

        # Bitcoin/Gold ratio - BTC priced in ounces of gold
        btc_file = self.data_dir / "bitcoin_price.csv"
        if btc_file.exists() and gold_file.exists():
            btc_df = pd.read_csv(btc_file)
            gold_df = pd.read_csv(gold_file)
            btc_df.columns = ['date', 'btc']
            gold_df.columns = ['date', 'gold']

            merged = pd.merge(btc_df, gold_df, on='date')
            merged['btc_gold_ratio'] = merged['btc'] / merged['gold']

            ratio_df = merged[['date', 'btc_gold_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "btc_gold_ratio.csv")
            print("BTC/Gold ratio (Bitcoin priced in gold ounces) calculated")

        # GDX/GLD ratio - Gold miners vs Gold (miner leverage indicator)
        gdx_file = self.data_dir / "gold_miners_price.csv"
        gld_file = self.data_dir / "gold_price.csv"
        if gdx_file.exists() and gld_file.exists():
            gdx_df = pd.read_csv(gdx_file)
            gld_df = pd.read_csv(gld_file)
            gdx_df.columns = ['date', 'gdx']
            gld_df.columns = ['date', 'gld']

            merged = pd.merge(gdx_df, gld_df, on='date')
            merged['gdx_gld_ratio'] = (merged['gdx'] / merged['gld']) * 100

            ratio_df = merged[['date', 'gdx_gld_ratio']]
            self.append_to_csv(ratio_df, self.data_dir / "gdx_gld_ratio.csv")
            print("GDX/GLD ratio (gold miners vs gold) calculated")

        # Rate Differentials (Currency/FX Drivers)
        print("\nCalculating rate differentials...")

        us_10y_file = self.data_dir / "treasury_10y.csv"
        japan_10y_file = self.data_dir / "japan_10y_yield.csv"
        germany_10y_file = self.data_dir / "germany_10y_yield.csv"

        # US-Japan 10Y Spread (carry trade driver)
        if us_10y_file.exists() and japan_10y_file.exists():
            us_df = pd.read_csv(us_10y_file)
            jp_df = pd.read_csv(japan_10y_file)
            us_df.columns = ['date', 'us_10y']
            jp_df.columns = ['date', 'jp_10y']

            merged = pd.merge(us_df, jp_df, on='date')
            merged['us_japan_10y_spread'] = merged['us_10y'] - merged['jp_10y']

            spread_df = merged[['date', 'us_japan_10y_spread']]
            self.append_to_csv(spread_df, self.data_dir / "us_japan_10y_spread.csv")
            print("US-Japan 10Y spread (carry trade driver) calculated")

        # US-Germany 10Y Spread (EUR/USD driver)
        if us_10y_file.exists() and germany_10y_file.exists():
            us_df = pd.read_csv(us_10y_file)
            de_df = pd.read_csv(germany_10y_file)
            us_df.columns = ['date', 'us_10y']
            de_df.columns = ['date', 'de_10y']

            merged = pd.merge(us_df, de_df, on='date')
            merged['us_germany_10y_spread'] = merged['us_10y'] - merged['de_10y']

            spread_df = merged[['date', 'us_germany_10y_spread']]
            self.append_to_csv(spread_df, self.data_dir / "us_germany_10y_spread.csv")
            print("US-Germany 10Y spread (EUR/USD driver) calculated")

    def run_daily_collection(self, lookback_days=12775):
        """Run the daily data collection process.

        Args:
            lookback_days: Number of days to look back (default: 12775, ~35 years)
        """
        eastern = pytz.timezone('US/Eastern')
        print(f"Market Signals Tracker - {datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')} ET")
        print(f"Data directory: {self.data_dir.absolute()}")

        self.collect_fred_signals(lookback_days=lookback_days)
        self.collect_etf_signals(lookback_days=lookback_days)
        self.collect_fear_greed_index()
        self.calculate_derived_metrics()

        print("\n=== Collection Complete ===")
        print(f"Data saved to: {self.data_dir.absolute()}")

    def show_summary(self):
        """Display a summary of collected data."""
        print("\n=== Data Summary ===")

        csv_files = sorted(self.data_dir.glob("*.csv"))

        if not csv_files:
            print("No data files found.")
            return

        for filepath in csv_files:
            try:
                df = pd.read_csv(filepath)
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    print(f"\n{filepath.name}:")
                    print(f"  Rows: {len(df)}")
                    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
                    if len(df.columns) > 1:
                        value_col = df.columns[1]
                        latest_value = df.iloc[-1][value_col]
                        print(f"  Latest value: {latest_value:.2f}" if isinstance(latest_value, (int, float)) else f"  Latest value: {latest_value}")
            except Exception as e:
                print(f"Error reading {filepath.name}: {e}")


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Collect comprehensive market signals for divergence monitoring.'
    )
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directory to store CSV files (default: data)'
    )
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=12775,  # 35 years
        help='Number of days to look back for data collection (default: 12775, ~35 years)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of collected data and exit'
    )
    parser.add_argument(
        '--fred-api-key',
        help='FRED API key (or set FRED_API_KEY environment variable)'
    )

    args = parser.parse_args()

    tracker = MarketSignalsTracker(
        data_dir=args.data_dir,
        fred_api_key=args.fred_api_key
    )

    if args.summary:
        tracker.show_summary()
    else:
        tracker.run_daily_collection(lookback_days=args.lookback_days)
        tracker.show_summary()


def get_latest_metrics():
    """
    Get latest values for all available metrics.

    Returns:
        dict: Dictionary mapping metric names to their latest data
              Format: {
                  'metric_name': {
                      'value': float,
                      'percentile': float,
                      'display_name': str,
                      'date': str
                  }
              }
    """
    from pathlib import Path
    import pandas as pd
    from metric_tools import calculate_percentile, METRIC_INFO

    data_dir = Path("data")
    metrics = {}

    if not data_dir.exists():
        return metrics

    # Load all CSV files
    for csv_file in data_dir.glob("*.csv"):
        metric_name = csv_file.stem  # filename without extension

        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                continue

            # us_recessions.csv has start_date/end_date, not date
            if metric_name != 'us_recessions':
                df['date'] = pd.to_datetime(df['date'])
            else:
                continue  # Skip us_recessions.csv in metric loading

            # Get the value column (second column)
            value_col = df.columns[1]

            # Get latest non-null value
            df_clean = df.dropna(subset=[value_col])
            if df_clean.empty:
                continue

            latest_row = df_clean.iloc[-1]
            latest_value = latest_row[value_col]
            latest_date = latest_row['date']

            # Calculate percentile
            all_values = df_clean[value_col].tolist()
            percentile = calculate_percentile(all_values, latest_value)

            # Get display name
            display_name = metric_name.replace('_', ' ').title()
            if metric_name in METRIC_INFO:
                display_name = METRIC_INFO[metric_name].get('description', display_name)

            metrics[metric_name] = {
                'value': latest_value,
                'percentile': percentile,
                'display_name': display_name,
                'date': latest_date.strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"Error loading {csv_file.name}: {e}")
            continue

    return metrics


def get_historical_metrics(days_ago=1):
    """
    Get metrics from N days ago.

    Args:
        days_ago: Number of days to look back

    Returns:
        dict: Metrics data structure (same format as get_latest_metrics)
    """
    from pathlib import Path
    import pandas as pd
    from datetime import datetime, timedelta
    from metric_tools import calculate_percentile, METRIC_INFO

    data_dir = Path("data")
    metrics = {}

    if not data_dir.exists():
        return metrics

    target_date = datetime.now() - timedelta(days=days_ago)

    # Load all CSV files
    for csv_file in data_dir.glob("*.csv"):
        metric_name = csv_file.stem

        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                continue

            # us_recessions.csv has start_date/end_date, not date
            if metric_name != 'us_recessions':
                df['date'] = pd.to_datetime(df['date'])
            else:
                continue  # Skip us_recessions.csv in metric loading

            # Get the value column (second column)
            value_col = df.columns[1]

            # Find the closest date to target_date
            df_clean = df.dropna(subset=[value_col])
            if df_clean.empty:
                continue

            # Filter to dates on or before target date
            df_before = df_clean[df_clean['date'] <= target_date]
            if df_before.empty:
                continue

            # Get the most recent row before/on target date
            historical_row = df_before.iloc[-1]
            historical_value = historical_row[value_col]
            historical_date = historical_row['date']

            # Calculate percentile using all historical data up to that point
            all_values = df_clean[df_clean['date'] <= historical_date][value_col].tolist()
            percentile = calculate_percentile(all_values, historical_value)

            # Get display name
            display_name = metric_name.replace('_', ' ').title()
            if metric_name in METRIC_INFO:
                display_name = METRIC_INFO[metric_name].get('description', display_name)

            metrics[metric_name] = {
                'value': historical_value,
                'percentile': percentile,
                'display_name': display_name,
                'date': historical_date.strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"Error loading {csv_file.name}: {e}")
            continue

    return metrics


if __name__ == '__main__':
    main()
