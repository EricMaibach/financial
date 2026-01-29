#!/bin/bash
# One-time backfill of 6 months of historical data
# This script is safe to run - it won't create duplicates

set -e

echo "=========================================="
echo "Historical Data Backfill"
echo "=========================================="
echo
echo "This will fetch 6 months (180 days) of historical data"
echo "for all tracked markets and indicators."
echo
echo "⚠️  Note: This may take 5-10 minutes to complete"
echo "    FRED API has rate limits"
echo "    yfinance needs to fetch data for 25+ tickers"
echo
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Backfill cancelled."
    exit 1
fi

echo
echo "Starting backfill..."
echo

# Check if we're in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check for FRED API key
if [ -z "$FRED_API_KEY" ]; then
    echo
    echo "⚠️  WARNING: FRED_API_KEY not set"
    echo "    Credit spread data (HY, IG, CCC) will not be collected"
    echo
    echo "To collect FRED data, set your API key:"
    echo "    export FRED_API_KEY='your_key_here'"
    echo
    read -p "Continue without FRED data? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        echo "Backfill cancelled. Set FRED_API_KEY and run again."
        exit 1
    fi
fi

echo
echo "=========================================="
echo "Fetching 6 months of historical data..."
echo "=========================================="
echo

# Run market_signals.py with 180 day lookback
# This will:
# - Fetch 6 months of data from FRED (if API key set)
# - Fetch 6 months of ETF data from yfinance
# - Calculate all derived metrics
# - Merge with existing data (no duplicates)
# - Sort by date

python market_signals.py --lookback-days 180

echo
echo "=========================================="
echo "Backfill Complete!"
echo "=========================================="
echo

# Show summary
python market_signals.py --summary

echo
echo "✅ Historical data backfill successful!"
echo
echo "You can now:"
echo "  1. Start the dashboard: ./start_dashboard.sh"
echo "  2. Run analysis: python comprehensive_report.py"
echo "  3. Daily updates: ./run_daily.sh (uses 30-day lookback)"
echo
echo "The backfill is complete. Future runs of ./run_daily.sh"
echo "will only fetch recent data (30 days) to stay current."
echo
