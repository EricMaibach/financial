#!/bin/bash
# Daily runner for comprehensive market signals tracking

set -e

echo "=========================================="
echo "Daily Market Signals Collection"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo

# Check if we're in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the comprehensive tracker
echo "Collecting market data..."
python market_signals.py

echo
echo "=========================================="
echo "Running Divergence Analysis..."
echo "=========================================="
echo

# Run divergence analysis
python divergence_analysis.py

echo
echo "=========================================="
echo "Collection and Analysis Complete!"
echo "=========================================="
echo
