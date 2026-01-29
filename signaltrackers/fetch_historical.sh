#!/bin/bash
cd /home/eric/Documents/repos/financial/signaltrackers
source venv/bin/activate

echo "===== Fetching historical market data ====="
echo "This will take about 10-15 minutes with delays to avoid rate limiting"
echo ""

# Run market signals with 20 years (ETFs don't have 35 years of data)
python market_signals.py --lookback-days 7300

echo ""
echo "===== Market signals complete, waiting 30 seconds before credit signals ====="
sleep 30

# Run credit signals
python credit_signals.py --lookback-days 7300

echo ""
echo "===== Complete! ====="
