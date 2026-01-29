"""
Kalshi Prediction Market Data Fetcher

Fetches prediction market data from Kalshi for macro/economic indicators.
No authentication required for public market data.

Key markets tracked:
- Fed funds rate predictions (kxfed series)
- Recession probability (kxrecssnber series)
- Rate cut count expectations (kxratecutcount series)
"""

import requests
from datetime import datetime, timedelta
from functools import lru_cache
import time

# Cache TTL in seconds (15 minutes)
CACHE_TTL = 900
_cache = {}
_cache_timestamps = {}


def _get_cached(key, fetcher):
    """Simple TTL cache wrapper."""
    now = time.time()
    if key in _cache and (now - _cache_timestamps.get(key, 0)) < CACHE_TTL:
        return _cache[key]

    result = fetcher()
    _cache[key] = result
    _cache_timestamps[key] = now
    return result


def get_next_fomc_month():
    """
    Get the next FOMC meeting month code.
    FOMC meets ~8 times per year. Returns format like '26jan', '26mar', etc.
    """
    # 2026 FOMC meeting months (approximate - meetings are roughly every 6-8 weeks)
    fomc_months = ['jan', 'mar', 'may', 'jun', 'jul', 'sep', 'nov', 'dec']

    now = datetime.now()
    year = now.year % 100  # Get 2-digit year

    # Find next meeting month
    for month in fomc_months:
        month_num = datetime.strptime(month, '%b').month
        meeting_date = datetime(now.year, month_num, 28)  # Approximate end of month
        if meeting_date > now:
            return f"{year}{month}"

    # If past all this year's meetings, return first of next year
    return f"{year + 1}jan"


def fetch_kalshi_market(ticker):
    """
    Fetch market data from Kalshi's public API.
    Returns market info including current prices.
    """
    try:
        # Kalshi public markets endpoint (no auth required)
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('market', {})
        elif response.status_code == 404:
            return None
        else:
            print(f"Kalshi API error for {ticker}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching Kalshi market {ticker}: {e}")
        return None


def fetch_fed_rate_prediction():
    """
    Fetch the next FOMC meeting Fed funds rate prediction.
    Returns probability distribution for rate outcomes.
    """
    def _fetch():
        next_meeting = get_next_fomc_month()
        ticker = f"KXFED-{next_meeting.upper()}"

        market = fetch_kalshi_market(ticker)
        if not market:
            # Try alternative ticker format
            ticker = f"kxfed-{next_meeting}"
            market = fetch_kalshi_market(ticker)

        if market:
            return {
                'ticker': ticker,
                'title': market.get('title', f'Fed Rate - {next_meeting}'),
                'subtitle': market.get('subtitle', ''),
                'yes_price': market.get('yes_bid', 0) / 100 if market.get('yes_bid') else None,
                'no_price': market.get('no_bid', 0) / 100 if market.get('no_bid') else None,
                'last_price': market.get('last_price', 0) / 100 if market.get('last_price') else None,
                'volume': market.get('volume', 0),
                'close_time': market.get('close_time'),
                'status': market.get('status'),
            }
        return None

    return _get_cached('fed_rate', _fetch)


def fetch_recession_probability():
    """
    Fetch recession probability for current year.
    Kalshi has markets like "Will NBER declare a recession in 2026?"
    """
    def _fetch():
        year = datetime.now().year % 100
        ticker = f"KXRECSSNBER-{year}"

        market = fetch_kalshi_market(ticker)
        if not market:
            # Try lowercase
            ticker = f"kxrecssnber-{year}"
            market = fetch_kalshi_market(ticker)

        if market:
            # yes_price represents probability of recession
            yes_price = market.get('last_price', 0)
            if yes_price:
                yes_price = yes_price / 100  # Convert cents to probability

            return {
                'ticker': ticker,
                'title': market.get('title', f'Recession in 20{year}'),
                'probability': yes_price,
                'volume': market.get('volume', 0),
                'close_time': market.get('close_time'),
                'status': market.get('status'),
            }
        return None

    return _get_cached('recession', _fetch)


def fetch_rate_cuts_expectation():
    """
    Fetch Fed large rate cut probability.
    KXLARGECUT-YY: Will the Fed cut rates more than 25bp this year?
    """
    def _fetch():
        year = datetime.now().year % 100
        ticker = f"KXLARGECUT-{year}"

        market = fetch_kalshi_market(ticker)

        if market:
            # last_price is in cents, convert to probability
            prob = market.get('last_price', 0) / 100 if market.get('last_price') else None
            return {
                'ticker': ticker,
                'title': market.get('title', f'Large Rate Cut in 20{year}'),
                'subtitle': f'{int(prob * 100)}% probability' if prob else '',
                'probability': prob,
                'volume': market.get('volume', 0),
                'close_time': market.get('close_time'),
                'status': market.get('status'),
            }
        return None

    return _get_cached('rate_cuts', _fetch)


def fetch_all_prediction_markets():
    """
    Fetch all tracked prediction markets.
    Returns a dict with all market data for dashboard display.

    Currently tracking:
    - Recession probability (KXRECSSNBER-YY)
    - Large Fed rate cut probability (KXLARGECUT-YY)
    """
    results = {
        'recession': None,
        'large_rate_cut': None,
        'last_updated': datetime.now().isoformat(),
    }

    # Fetch recession probability
    recession = fetch_recession_probability()
    if recession:
        results['recession'] = recession

    # Fetch large rate cut probability
    rate_cuts = fetch_rate_cuts_expectation()
    if rate_cuts:
        results['large_rate_cut'] = rate_cuts

    return results


def fetch_kalshi_events(category='economics'):
    """
    Fetch events from Kalshi in a given category.
    This provides a list of active markets.
    """
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/events"
        params = {
            'status': 'open',
            'limit': 50,
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])

            # Filter for economics-related events
            econ_keywords = ['fed', 'rate', 'recession', 'inflation', 'cpi', 'gdp', 'fomc']
            filtered = []
            for event in events:
                title_lower = event.get('title', '').lower()
                if any(kw in title_lower for kw in econ_keywords):
                    filtered.append(event)

            return filtered
        return []
    except Exception as e:
        print(f"Error fetching Kalshi events: {e}")
        return []


if __name__ == '__main__':
    # Test the fetchers
    print("Testing Kalshi data fetchers...\n")

    print("=== Fetching all prediction markets ===")
    data = fetch_all_prediction_markets()
    print(f"Last updated: {data['last_updated']}")

    if data['recession']:
        print(f"\nRecession Market:")
        print(f"  Title: {data['recession']['title']}")
        print(f"  Probability: {data['recession']['probability']:.1%}" if data['recession']['probability'] else "  Probability: N/A")

    if data['rate_cuts']:
        print(f"\nRate Cuts Market:")
        print(f"  Title: {data['rate_cuts']['title']}")

    print("\n=== Fetching economics events ===")
    events = fetch_kalshi_events()
    for event in events[:5]:
        print(f"  - {event.get('title')}")
