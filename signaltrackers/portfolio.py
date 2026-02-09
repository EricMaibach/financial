#!/usr/bin/env python3
"""
Portfolio Management Module

Handles storage and retrieval of user portfolio allocations,
price fetching for various asset types, and portfolio analysis.

This module supports both:
- Database-backed storage (for multi-user mode via db_* functions)
- JSON file storage (legacy, for backward compatibility)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Optional imports with error handling
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    print("Warning: yfinance not installed. Stock/ETF price fetching will be unavailable.")

# Data directory setup
DATA_DIR = Path(__file__).parent / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"

# Database imports (optional - only available when Flask app is running)
try:
    from extensions import db
    from models.portfolio import PortfolioAllocation
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    db = None
    PortfolioAllocation = None

# Asset type categories
ASSET_TYPES = {
    'stock': {'symbol_required': True, 'data_source': 'yfinance'},
    'etf': {'symbol_required': True, 'data_source': 'yfinance'},
    'mutual_fund': {'symbol_required': True, 'data_source': 'yfinance'},
    'crypto': {'symbol_required': False, 'data_source': 'internal'},  # Uses bitcoin_price metric
    'gold': {'symbol_required': False, 'data_source': 'internal'},     # Uses gold_price metric
    'cash': {'symbol_required': False, 'data_source': None},
    'savings': {'symbol_required': False, 'data_source': None},
    'money_market': {'symbol_required': False, 'data_source': None},   # Money market funds/accounts
    'other': {'symbol_required': False, 'data_source': None},
}


def load_portfolio() -> Dict[str, Any]:
    """Load portfolio allocations from JSON file."""
    if not PORTFOLIO_FILE.exists():
        return {
            "allocations": [],
            "last_modified": None
        }

    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading portfolio: {e}")
        return {
            "allocations": [],
            "last_modified": None
        }


def save_portfolio(portfolio: Dict[str, Any]) -> bool:
    """Save portfolio allocations to JSON file."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        portfolio["last_modified"] = datetime.now().isoformat()
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(portfolio, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving portfolio: {e}")
        return False


def add_allocation(asset_type: str, symbol: Optional[str], name: str, percentage: float) -> Dict[str, Any]:
    """
    Add a new allocation to the portfolio.

    Args:
        asset_type: Type of asset (stock, etf, mutual_fund, crypto, gold, cash, savings, other)
        symbol: Ticker symbol (required for stocks/ETFs/mutual funds)
        name: Display name for the asset
        percentage: Allocation percentage (0-100)

    Returns:
        The newly created allocation dict, or error dict if validation fails
    """
    # Validate asset type
    if asset_type not in ASSET_TYPES:
        return {"error": f"Invalid asset type: {asset_type}"}

    # Validate symbol requirement
    if ASSET_TYPES[asset_type]['symbol_required'] and not symbol:
        return {"error": f"Symbol is required for {asset_type}"}

    # Validate percentage
    if percentage <= 0 or percentage > 100:
        return {"error": "Percentage must be between 0 and 100"}

    portfolio = load_portfolio()

    now = datetime.now().isoformat()
    allocation = {
        "id": str(uuid.uuid4()),
        "asset_type": asset_type,
        "symbol": symbol.upper() if symbol else None,
        "name": name,
        "percentage": round(percentage, 2),
        "added_at": now,
        "updated_at": now
    }

    portfolio["allocations"].append(allocation)
    save_portfolio(portfolio)

    return allocation


def update_allocation(allocation_id: str, percentage: Optional[float] = None,
                      name: Optional[str] = None, symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Update an existing allocation.

    Args:
        allocation_id: UUID of the allocation to update
        percentage: New percentage (optional)
        name: New name (optional)
        symbol: New symbol (optional)

    Returns:
        Updated allocation dict, or error dict if not found
    """
    portfolio = load_portfolio()

    for allocation in portfolio["allocations"]:
        if allocation["id"] == allocation_id:
            if percentage is not None:
                if percentage <= 0 or percentage > 100:
                    return {"error": "Percentage must be between 0 and 100"}
                allocation["percentage"] = round(percentage, 2)
            if name is not None:
                allocation["name"] = name
            if symbol is not None:
                allocation["symbol"] = symbol.upper() if symbol else None
            allocation["updated_at"] = datetime.now().isoformat()
            save_portfolio(portfolio)
            return allocation

    return {"error": f"Allocation not found: {allocation_id}"}


def delete_allocation(allocation_id: str) -> Dict[str, Any]:
    """
    Delete an allocation from the portfolio.

    Args:
        allocation_id: UUID of the allocation to delete

    Returns:
        Success message or error dict
    """
    portfolio = load_portfolio()

    original_count = len(portfolio["allocations"])
    portfolio["allocations"] = [a for a in portfolio["allocations"] if a["id"] != allocation_id]

    if len(portfolio["allocations"]) == original_count:
        return {"error": f"Allocation not found: {allocation_id}"}

    save_portfolio(portfolio)
    return {"success": True, "message": "Allocation deleted"}


def validate_allocation_total() -> Dict[str, Any]:
    """
    Check if allocations sum to approximately 100%.

    Returns:
        Dict with total percentage and validation status
    """
    portfolio = load_portfolio()
    total = sum(a["percentage"] for a in portfolio["allocations"])

    return {
        "total_percentage": round(total, 2),
        "is_valid": 95 <= total <= 105,  # Allow 5% tolerance
        "message": "Valid" if 95 <= total <= 105 else f"Total is {total:.1f}% (should be ~100%)"
    }


def fetch_asset_price(asset_type: str, symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch current price for an asset.

    Args:
        asset_type: Type of asset
        symbol: Ticker symbol (for stocks/ETFs/mutual funds)

    Returns:
        Dict with price info or error
    """
    config = ASSET_TYPES.get(asset_type)
    if not config:
        return {"error": f"Invalid asset type: {asset_type}"}

    # Handle internal data sources (gold, crypto)
    if config['data_source'] == 'internal':
        return _fetch_internal_price(asset_type)

    # Handle yfinance data sources
    if config['data_source'] == 'yfinance':
        if not symbol:
            return {"error": "Symbol required for this asset type"}
        return _fetch_yfinance_price(symbol)

    # No price data available (cash, savings, other)
    return {
        "price": None,
        "change_pct": None,
        "source": "none",
        "message": "No price data available for this asset type"
    }


def _fetch_internal_price(asset_type: str) -> Dict[str, Any]:
    """Fetch price from internal CSV data (gold, bitcoin)."""
    import pandas as pd

    if asset_type == 'gold':
        csv_file = DATA_DIR / 'gold_price.csv'
        if not csv_file.exists():
            return {"error": "Gold price data not available"}

        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                return {"error": "Gold price data is empty"}

            # Gold price in CSV is GLD ETF, multiply by 10 for approximate spot
            latest_price = float(df.iloc[-1][df.columns[1]]) * 10

            # Calculate change if we have enough data
            change_pct = None
            if len(df) > 1:
                prev_price = float(df.iloc[-2][df.columns[1]]) * 10
                change_pct = ((latest_price - prev_price) / prev_price) * 100

            return {
                "price": round(latest_price, 2),
                "change_pct": round(change_pct, 2) if change_pct else None,
                "source": "internal",
                "symbol": "GOLD"
            }
        except Exception as e:
            return {"error": f"Error fetching gold price: {e}"}

    elif asset_type == 'crypto':
        csv_file = DATA_DIR / 'bitcoin_price.csv'
        if not csv_file.exists():
            return {"error": "Bitcoin price data not available"}

        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                return {"error": "Bitcoin price data is empty"}

            latest_price = float(df.iloc[-1][df.columns[1]])

            # Calculate change if we have enough data
            change_pct = None
            if len(df) > 1:
                prev_price = float(df.iloc[-2][df.columns[1]])
                change_pct = ((latest_price - prev_price) / prev_price) * 100

            return {
                "price": round(latest_price, 2),
                "change_pct": round(change_pct, 2) if change_pct else None,
                "source": "internal",
                "symbol": "BTC"
            }
        except Exception as e:
            return {"error": f"Error fetching bitcoin price: {e}"}

    return {"error": f"Unknown internal asset type: {asset_type}"}


def _fetch_yfinance_price(symbol: str) -> Dict[str, Any]:
    """Fetch price from yfinance."""
    if not YF_AVAILABLE:
        return {"error": "yfinance not available"}

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")

        if hist.empty:
            return {"error": f"No data found for symbol: {symbol}"}

        latest_price = float(hist['Close'].iloc[-1])

        # Calculate change
        change_pct = None
        if len(hist) > 1:
            prev_price = float(hist['Close'].iloc[-2])
            change_pct = ((latest_price - prev_price) / prev_price) * 100

        return {
            "price": round(latest_price, 2),
            "change_pct": round(change_pct, 2) if change_pct else None,
            "source": "yfinance",
            "symbol": symbol.upper()
        }
    except Exception as e:
        return {"error": f"Error fetching price for {symbol}: {e}"}


def validate_symbol(symbol: str) -> Dict[str, Any]:
    """
    Validate a ticker symbol exists and get basic info.

    Args:
        symbol: Ticker symbol to validate

    Returns:
        Dict with symbol info or error
    """
    if not YF_AVAILABLE:
        return {"error": "yfinance not available for symbol validation"}

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Check if we got valid info
        if not info or info.get('regularMarketPrice') is None:
            # Try to get history as fallback
            hist = ticker.history(period="5d")
            if hist.empty:
                return {"error": f"Invalid symbol: {symbol}"}

            return {
                "valid": True,
                "symbol": symbol.upper(),
                "name": symbol.upper(),  # Use symbol as name fallback
                "type": "unknown"
            }

        return {
            "valid": True,
            "symbol": symbol.upper(),
            "name": info.get('shortName') or info.get('longName') or symbol.upper(),
            "type": info.get('quoteType', 'unknown').lower()
        }
    except Exception as e:
        return {"error": f"Error validating symbol {symbol}: {e}"}


def get_portfolio_with_prices() -> Dict[str, Any]:
    """
    Get portfolio allocations with current prices.

    Returns:
        Portfolio data with prices and performance info
    """
    portfolio = load_portfolio()
    allocations_with_prices = []

    for allocation in portfolio["allocations"]:
        alloc_data = allocation.copy()

        # Fetch price based on asset type
        price_info = fetch_asset_price(
            allocation["asset_type"],
            allocation.get("symbol")
        )

        alloc_data["price_info"] = price_info
        allocations_with_prices.append(alloc_data)

    # Calculate totals and breakdowns
    total_percentage = sum(a["percentage"] for a in portfolio["allocations"])

    # Asset type breakdown
    type_breakdown = {}
    for alloc in portfolio["allocations"]:
        atype = alloc["asset_type"]
        type_breakdown[atype] = type_breakdown.get(atype, 0) + alloc["percentage"]

    return {
        "allocations": allocations_with_prices,
        "total_percentage": round(total_percentage, 2),
        "is_valid": 95 <= total_percentage <= 105,
        "type_breakdown": type_breakdown,
        "last_modified": portfolio.get("last_modified")
    }


def get_portfolio_summary_for_ai() -> Dict[str, Any]:
    """
    Get portfolio data formatted for AI analysis.

    Returns:
        Dict with portfolio summary suitable for AI briefing generation
    """
    portfolio_data = get_portfolio_with_prices()

    # Build summary sections
    holdings_summary = []
    for alloc in portfolio_data["allocations"]:
        holding = {
            "name": alloc["name"],
            "type": alloc["asset_type"],
            "percentage": alloc["percentage"],
        }

        # Add price info if available
        price_info = alloc.get("price_info", {})
        if price_info.get("price"):
            holding["current_price"] = price_info["price"]
            if price_info.get("change_pct") is not None:
                holding["daily_change_pct"] = price_info["change_pct"]

        if alloc.get("symbol"):
            holding["symbol"] = alloc["symbol"]

        holdings_summary.append(holding)

    # Calculate risk metrics
    concentration_risk = []
    for alloc in portfolio_data["allocations"]:
        if alloc["percentage"] > 30:
            concentration_risk.append({
                "name": alloc["name"],
                "percentage": alloc["percentage"],
                "warning": "High concentration (>30%)"
            })

    # Asset class groupings for diversification analysis
    equity_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] in ['stock', 'etf', 'mutual_fund']
    )
    alternatives_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] in ['crypto', 'gold']
    )
    cash_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] in ['cash', 'savings', 'money_market']
    )
    other_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] == 'other'
    )

    return {
        "holdings": holdings_summary,
        "total_holdings": len(holdings_summary),
        "total_allocation_pct": portfolio_data["total_percentage"],
        "allocation_valid": portfolio_data["is_valid"],
        "type_breakdown": portfolio_data["type_breakdown"],
        "asset_class_breakdown": {
            "equities": round(equity_pct, 2),
            "alternatives": round(alternatives_pct, 2),
            "cash": round(cash_pct, 2),
            "other": round(other_pct, 2)
        },
        "concentration_warnings": concentration_risk,
        "last_modified": portfolio_data["last_modified"]
    }


# =============================================================================
# Database-Backed Portfolio Functions (Multi-User Mode)
# =============================================================================

def db_load_portfolio(user_id: str) -> Dict[str, Any]:
    """
    Load portfolio allocations from database for a specific user.

    Args:
        user_id: UUID of the user

    Returns:
        Portfolio data dict with allocations list
    """
    if not DB_AVAILABLE:
        return {"allocations": [], "last_modified": None, "error": "Database not available"}

    allocations = PortfolioAllocation.query.filter_by(user_id=user_id).all()

    alloc_list = [a.to_dict() for a in allocations]
    last_modified = max((a.updated_at for a in allocations), default=None)

    return {
        "allocations": alloc_list,
        "last_modified": last_modified.isoformat() if last_modified else None
    }


def db_add_allocation(user_id: str, asset_type: str, symbol: Optional[str],
                      name: str, percentage: float) -> Dict[str, Any]:
    """
    Add a new allocation to user's portfolio in database.

    Args:
        user_id: UUID of the user
        asset_type: Type of asset
        symbol: Ticker symbol (optional)
        name: Display name
        percentage: Allocation percentage

    Returns:
        The newly created allocation dict, or error dict
    """
    if not DB_AVAILABLE:
        return {"error": "Database not available"}

    # Validate asset type
    if asset_type not in ASSET_TYPES:
        return {"error": f"Invalid asset type: {asset_type}"}

    # Validate symbol requirement
    if ASSET_TYPES[asset_type]['symbol_required'] and not symbol:
        return {"error": f"Symbol is required for {asset_type}"}

    # Validate percentage
    if percentage <= 0 or percentage > 100:
        return {"error": "Percentage must be between 0 and 100"}

    allocation = PortfolioAllocation(
        user_id=user_id,
        asset_type=asset_type,
        symbol=symbol.upper() if symbol else None,
        name=name,
        percentage=round(percentage, 2)
    )

    db.session.add(allocation)
    db.session.commit()

    return allocation.to_dict()


def db_update_allocation(user_id: str, allocation_id: str,
                         percentage: Optional[float] = None,
                         name: Optional[str] = None,
                         symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Update an existing allocation in database.

    Args:
        user_id: UUID of the user (for ownership verification)
        allocation_id: UUID of the allocation
        percentage: New percentage (optional)
        name: New name (optional)
        symbol: New symbol (optional)

    Returns:
        Updated allocation dict, or error dict
    """
    if not DB_AVAILABLE:
        return {"error": "Database not available"}

    allocation = PortfolioAllocation.query.filter_by(
        id=allocation_id,
        user_id=user_id
    ).first()

    if not allocation:
        return {"error": f"Allocation not found: {allocation_id}"}

    if percentage is not None:
        if percentage <= 0 or percentage > 100:
            return {"error": "Percentage must be between 0 and 100"}
        allocation.percentage = round(percentage, 2)

    if name is not None:
        allocation.name = name

    if symbol is not None:
        allocation.symbol = symbol.upper() if symbol else None

    db.session.commit()

    return allocation.to_dict()


def db_delete_allocation(user_id: str, allocation_id: str) -> Dict[str, Any]:
    """
    Delete an allocation from user's portfolio.

    Args:
        user_id: UUID of the user (for ownership verification)
        allocation_id: UUID of the allocation

    Returns:
        Success message or error dict
    """
    if not DB_AVAILABLE:
        return {"error": "Database not available"}

    allocation = PortfolioAllocation.query.filter_by(
        id=allocation_id,
        user_id=user_id
    ).first()

    if not allocation:
        return {"error": f"Allocation not found: {allocation_id}"}

    db.session.delete(allocation)
    db.session.commit()

    return {"success": True, "message": "Allocation deleted"}


def db_validate_allocation_total(user_id: str) -> Dict[str, Any]:
    """
    Check if user's allocations sum to approximately 100%.

    Args:
        user_id: UUID of the user

    Returns:
        Dict with total percentage and validation status
    """
    if not DB_AVAILABLE:
        return {"error": "Database not available"}

    allocations = PortfolioAllocation.query.filter_by(user_id=user_id).all()
    total = sum(a.percentage for a in allocations)

    return {
        "total_percentage": round(total, 2),
        "is_valid": 95 <= total <= 105,
        "message": "Valid" if 95 <= total <= 105 else f"Total is {total:.1f}% (should be ~100%)"
    }


def db_get_portfolio_with_prices(user_id: str) -> Dict[str, Any]:
    """
    Get user's portfolio allocations with current prices.

    Args:
        user_id: UUID of the user

    Returns:
        Portfolio data with prices and performance info
    """
    if not DB_AVAILABLE:
        return {"allocations": [], "error": "Database not available"}

    allocations = PortfolioAllocation.query.filter_by(user_id=user_id).all()
    allocations_with_prices = []

    for allocation in allocations:
        alloc_data = allocation.to_dict()

        # Fetch price based on asset type
        price_info = fetch_asset_price(
            allocation.asset_type,
            allocation.symbol
        )

        alloc_data["price_info"] = price_info
        allocations_with_prices.append(alloc_data)

    # Calculate totals and breakdowns
    total_percentage = sum(a.percentage for a in allocations)

    # Asset type breakdown
    type_breakdown = {}
    for alloc in allocations:
        atype = alloc.asset_type
        type_breakdown[atype] = type_breakdown.get(atype, 0) + alloc.percentage

    last_modified = max((a.updated_at for a in allocations), default=None)

    return {
        "allocations": allocations_with_prices,
        "total_percentage": round(total_percentage, 2),
        "is_valid": 95 <= total_percentage <= 105,
        "type_breakdown": type_breakdown,
        "last_modified": last_modified.isoformat() if last_modified else None
    }


def db_get_portfolio_summary_for_ai(user_id: str) -> Dict[str, Any]:
    """
    Get user's portfolio data formatted for AI analysis.

    Args:
        user_id: UUID of the user

    Returns:
        Dict with portfolio summary suitable for AI briefing generation
    """
    portfolio_data = db_get_portfolio_with_prices(user_id)

    if "error" in portfolio_data:
        return portfolio_data

    # Build summary sections
    holdings_summary = []
    for alloc in portfolio_data["allocations"]:
        holding = {
            "name": alloc["name"],
            "type": alloc["asset_type"],
            "percentage": alloc["percentage"],
        }

        # Add price info if available
        price_info = alloc.get("price_info", {})
        if price_info.get("price"):
            holding["current_price"] = price_info["price"]
            if price_info.get("change_pct") is not None:
                holding["daily_change_pct"] = price_info["change_pct"]

        if alloc.get("symbol"):
            holding["symbol"] = alloc["symbol"]

        holdings_summary.append(holding)

    # Calculate risk metrics
    concentration_risk = []
    for alloc in portfolio_data["allocations"]:
        if alloc["percentage"] > 30:
            concentration_risk.append({
                "name": alloc["name"],
                "percentage": alloc["percentage"],
                "warning": "High concentration (>30%)"
            })

    # Asset class groupings for diversification analysis
    equity_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] in ['stock', 'etf', 'mutual_fund']
    )
    alternatives_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] in ['crypto', 'gold']
    )
    cash_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] in ['cash', 'savings', 'money_market']
    )
    other_pct = sum(
        a["percentage"] for a in portfolio_data["allocations"]
        if a["asset_type"] == 'other'
    )

    return {
        "holdings": holdings_summary,
        "total_holdings": len(holdings_summary),
        "total_allocation_pct": portfolio_data["total_percentage"],
        "allocation_valid": portfolio_data["is_valid"],
        "type_breakdown": portfolio_data["type_breakdown"],
        "asset_class_breakdown": {
            "equities": round(equity_pct, 2),
            "alternatives": round(alternatives_pct, 2),
            "cash": round(cash_pct, 2),
            "other": round(other_pct, 2)
        },
        "concentration_warnings": concentration_risk,
        "last_modified": portfolio_data["last_modified"]
    }


if __name__ == "__main__":
    # Test the module
    print("Portfolio Module Test")
    print("=" * 50)

    # Test loading
    portfolio = load_portfolio()
    print(f"Current allocations: {len(portfolio['allocations'])}")

    # Test validation
    validation = validate_allocation_total()
    print(f"Allocation total: {validation['total_percentage']}%")
    print(f"Valid: {validation['is_valid']}")

    # Test summary for AI
    summary = get_portfolio_summary_for_ai()
    print(f"\nPortfolio Summary for AI:")
    print(f"  Holdings: {summary['total_holdings']}")
    print(f"  Asset class breakdown: {summary['asset_class_breakdown']}")
