#!/bin/bash
# Start the Market Divergence Dashboard

set -e

echo "=========================================="
echo "Market Divergence Dashboard"
echo "=========================================="
echo

# Check if we're in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Flask not found. Installing dependencies..."
    pip install flask
fi

# Run data collection first
echo "Running data collection..."
python market_signals.py

echo
echo "=========================================="
echo "Starting Dashboard Server..."
echo "=========================================="
echo
echo "Dashboard will be available at:"
echo "  http://localhost:5000"
echo
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo

# Start the dashboard
python dashboard.py
