#!/bin/bash
# Setup script for Credit Signals Tracker

set -e

echo "Setting up Credit Signals Tracker..."
echo

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    if ! python3 -m venv venv 2>/dev/null; then
        echo
        echo "❌ Error: Failed to create virtual environment"
        echo
        echo "You need to install python3-venv first:"
        echo "  sudo apt install python3.13-venv"
        echo
        echo "Or try with your Python version:"
        echo "  sudo apt install python3-venv"
        echo
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Verify venv was created successfully
if [ ! -f "venv/bin/activate" ]; then
    echo
    echo "❌ Error: Virtual environment is incomplete"
    echo "Try removing it and running setup again:"
    echo "  rm -rf venv"
    echo "  ./setup.sh"
    exit 1
fi

# Activate and install dependencies
echo
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create data directory
mkdir -p data
mkdir -p logs
echo "✓ Directories created"

echo
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo
echo "Next steps:"
echo
echo "1. Get a free FRED API key from:"
echo "   https://fred.stlouisfed.org/docs/api/api_key.html"
echo
echo "2. Set your API key:"
echo "   export FRED_API_KEY='your_key_here'"
echo
echo "3. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo
echo "4. Run the collector:"
echo "   python credit_signals.py"
echo
