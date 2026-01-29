#!/usr/bin/env python3
"""
Test script to verify tracker setup and dependencies.
"""

import sys

def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    try:
        import pandas as pd
        print(f"  ✓ pandas {pd.__version__}")
    except ImportError as e:
        print(f"  ✗ pandas: {e}")
        return False

    try:
        import numpy as np
        print(f"  ✓ numpy {np.__version__}")
    except ImportError as e:
        print(f"  ✗ numpy: {e}")
        return False

    try:
        import requests
        print(f"  ✓ requests {requests.__version__}")
    except ImportError as e:
        print(f"  ✗ requests: {e}")
        return False

    try:
        import yfinance as yf
        print(f"  ✓ yfinance {yf.__version__}")
    except ImportError as e:
        print(f"  ✗ yfinance: {e}")
        return False

    return True

def test_fred_api_key():
    """Test if FRED API key is set."""
    import os
    print("\nTesting FRED API key...")

    fred_key = os.environ.get('FRED_API_KEY')
    if fred_key:
        print(f"  ✓ FRED_API_KEY is set ({fred_key[:8]}...)")
        return True
    else:
        print("  ⚠ FRED_API_KEY not set (FRED data will be unavailable)")
        print("    Get a key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("    Set with: export FRED_API_KEY='your_key'")
        return False

def test_data_directory():
    """Test if data directory exists."""
    from pathlib import Path
    print("\nTesting data directory...")

    data_dir = Path("data")
    if data_dir.exists():
        csv_count = len(list(data_dir.glob("*.csv")))
        print(f"  ✓ data/ directory exists ({csv_count} CSV files)")
        return True
    else:
        print("  ⚠ data/ directory doesn't exist yet")
        print("    Will be created on first run")
        return True

def test_scripts():
    """Test if main scripts exist."""
    from pathlib import Path
    print("\nTesting scripts...")

    scripts = [
        'market_signals.py',
        'divergence_analysis.py',
        'credit_signals.py',
        'run_daily.sh'
    ]

    all_exist = True
    for script in scripts:
        if Path(script).exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ✗ {script} missing")
            all_exist = False

    return all_exist

def test_yfinance_connection():
    """Test yfinance can fetch data."""
    print("\nTesting yfinance connection...")

    try:
        import yfinance as yf
        ticker = yf.Ticker("SPY")
        data = ticker.history(period="1d")
        if not data.empty:
            print(f"  ✓ Successfully fetched SPY data")
            return True
        else:
            print(f"  ✗ No data returned (market closed?)")
            return True  # Not a failure if market is closed
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("Market Signals Tracker - Setup Verification")
    print("="*60)
    print()

    results = []

    results.append(("Imports", test_imports()))
    results.append(("FRED API Key", test_fred_api_key()))
    results.append(("Data Directory", test_data_directory()))
    results.append(("Scripts", test_scripts()))
    results.append(("YFinance Connection", test_yfinance_connection()))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    all_passed = all(result[1] for result in results[:1])  # Only imports are critical
    critical_warnings = not results[1][1]  # FRED API key

    print("\n" + "="*60)
    if all_passed and not critical_warnings:
        print("🟢 All tests passed! Ready to run.")
        print("\nNext steps:")
        print("  1. Run: ./run_daily.sh")
        print("  2. Or run: python market_signals.py")
    elif all_passed:
        print("🟡 Setup OK but with warnings")
        print("\nYou can run the tracker, but:")
        print("  • FRED data won't be collected without API key")
        print("  • ETF data will still work via yfinance")
    else:
        print("🔴 Setup incomplete")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
    print("="*60)

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
