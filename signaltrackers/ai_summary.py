#!/usr/bin/env python3
"""
AI Daily Summary Generator

Generates insightful daily market summaries using GPT-4 with web search capability.
Summaries are stored historically and provide context for continuity.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

from web_search import (
    search_web, search_financial_news, is_tavily_configured,
    SEARCH_FUNCTION_DEFINITION, execute_search_function
)

# Storage location
DATA_DIR = Path("data")
SUMMARIES_FILE = DATA_DIR / "ai_summaries.json"


def call_openai_with_tools(client, system_prompt, user_prompt, max_tokens=600, log_prefix="[AI]"):
    """
    Make an OpenAI API call with web search tool support.

    Args:
        client: OpenAI client instance
        system_prompt: System prompt for the model
        user_prompt: User prompt with data/context
        max_tokens: Maximum tokens for completion
        log_prefix: Prefix for log messages (e.g., "[Crypto Summary]")

    Returns:
        dict with 'success', 'content', and 'error' keys
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Set up tools if Tavily is available
    tools = None
    tool_choice = None
    web_search_available = is_tavily_configured()

    if web_search_available:
        tools = [{"type": "function", "function": SEARCH_FUNCTION_DEFINITION}]
        tool_choice = "auto"
        print(f"{log_prefix} Web search tool available")
    else:
        print(f"{log_prefix} Web search tool not available (Tavily not configured)")

    # Tool calling loop
    max_iterations = 3
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"{log_prefix} API call iteration {iteration}/{max_iterations}")

        api_params = {
            "model": "gpt-5.2",
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": max_tokens
        }

        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = tool_choice

        response = client.chat.completions.create(**api_params)
        response_message = response.choices[0].message

        print(f"{log_prefix} Response finish_reason: {response.choices[0].finish_reason}")
        print(f"{log_prefix} Response has tool_calls: {bool(response_message.tool_calls)}")

        if response_message.tool_calls:
            print(f"{log_prefix} Tool calls requested: {[tc.function.name for tc in response_message.tool_calls]}")
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                print(f"{log_prefix} Executing {function_name} with args: {function_args}")

                if function_name == "search_web":
                    result = execute_search_function(function_args)
                else:
                    result = json.dumps({"error": f"Unknown function: {function_name}"})

                print(f"{log_prefix} {function_name} returned {len(result)} chars")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            # Continue loop to get model's response after tool results
            continue

        # No tool calls - this is the final response
        content = response_message.content
        print(f"{log_prefix} Response content length: {len(content) if content else 0}")

        if content:
            print(f"{log_prefix} Response content preview: {content[:200]}...")

        if not content or not content.strip():
            print(f"{log_prefix} API returned empty content")
            return {
                'success': False,
                'content': None,
                'error': 'API returned empty response'
            }

        return {
            'success': True,
            'content': content.strip(),
            'error': None
        }

    # Exceeded max iterations
    print(f"{log_prefix} Exceeded max iterations")
    return {
        'success': False,
        'content': None,
        'error': 'Exceeded maximum tool call iterations'
    }


def load_summaries():
    """Load all stored AI summaries."""
    if SUMMARIES_FILE.exists():
        try:
            with open(SUMMARIES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"summaries": []}
    return {"summaries": []}


def save_summaries(data):
    """Save summaries to JSON file."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(SUMMARIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_latest_summary():
    """Get the most recent AI summary."""
    data = load_summaries()
    if data["summaries"]:
        # Sort by date descending and return most recent
        sorted_summaries = sorted(data["summaries"], key=lambda x: x["date"], reverse=True)
        return sorted_summaries[0]
    return None


def get_recent_summaries(days=3):
    """Get summaries from the last N days for context."""
    data = load_summaries()
    if not data["summaries"]:
        return []

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [s for s in data["summaries"] if s["date"] >= cutoff]
    # Sort by date ascending (oldest first) for chronological context
    return sorted(recent, key=lambda x: x["date"])


def save_summary(date_str, summary_text, web_search_used=False, news_context=None):
    """Save a new summary, overwriting if same date exists."""
    data = load_summaries()

    # Remove existing summary for this date if present
    data["summaries"] = [s for s in data["summaries"] if s["date"] != date_str]

    # Add new summary
    data["summaries"].append({
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "summary": summary_text,
        "web_search_used": web_search_used,
        "news_context": news_context[:500] if news_context else None  # Store snippet of news used
    })

    # Keep last 90 days of summaries
    cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    data["summaries"] = [s for s in data["summaries"] if s["date"] >= cutoff]

    save_summaries(data)


def fetch_news_for_summary():
    """Fetch current financial news for summary context."""
    if not is_tavily_configured():
        return None

    # Search for multiple topics to get broad coverage
    news_parts = []

    # Main financial news
    main_news = search_financial_news("major financial market news today", max_results=5)
    if main_news.get('results'):
        news_parts.append("## Today's Major Financial News")
        if main_news.get('answer'):
            news_parts.append(main_news['answer'])
        for r in main_news['results'][:3]:
            news_parts.append(f"- {r['title']}: {r['content'][:200]}...")

    # Fed/monetary policy news
    fed_news = search_web("Federal Reserve monetary policy news today", max_results=3)
    if fed_news.get('results'):
        news_parts.append("\n## Fed/Monetary Policy")
        for r in fed_news['results'][:2]:
            news_parts.append(f"- {r['title']}: {r['content'][:150]}...")

    # Market-moving events
    events_news = search_web("stock market moving events economic data today", max_results=3)
    if events_news.get('results'):
        news_parts.append("\n## Market-Moving Events")
        for r in events_news['results'][:2]:
            news_parts.append(f"- {r['title']}: {r['content'][:150]}...")

    return "\n".join(news_parts) if news_parts else None


def generate_daily_summary(market_data_summary, top_movers):
    """
    Generate the daily AI summary.

    Args:
        market_data_summary: String output from generate_market_summary()
        top_movers: List of top movers from calculate_top_movers()

    Returns:
        dict with 'success', 'summary', and 'error' keys
    """
    if not os.environ.get('OPENAI_API_KEY'):
        return {
            'success': False,
            'summary': None,
            'error': 'OpenAI API key not configured'
        }

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        today = datetime.now().strftime('%Y-%m-%d')

        # Get previous summaries for context
        recent_summaries = get_recent_summaries(days=3)
        previous_context = ""
        if recent_summaries:
            previous_context = "\n\n## YOUR PREVIOUS SUMMARIES (for continuity - don't repeat these points):\n"
            for s in recent_summaries:
                if s["date"] != today:  # Don't include today if regenerating
                    previous_context += f"\n### {s['date']}:\n{s['summary']}\n"

        # Fetch current news
        news_context = fetch_news_for_summary()
        news_section = ""
        if news_context:
            news_section = f"\n\n## TODAY'S NEWS CONTEXT:\n{news_context}"

        # Format top movers
        movers_text = ""
        if top_movers:
            movers_text = "\n\n## TODAY'S BIGGEST MOVES (by z-score, most unusual):\n"
            for m in top_movers[:5]:
                direction = "up" if m['change_5d'] > 0 else "down"
                movers_text += f"- {m['name']}: {m['change_5d']:+.1f}{m['unit']} ({direction}, z-score: {m['z_score']:.1f})\n"

        # The system prompt - this is the key to getting great summaries
        system_prompt = """You are a brilliant, trusted financial commentator - think of yourself as the host of the most valuable daily financial briefing that exists. Your audience is individual investors who are smart but busy. They could only pick ONE source of financial insight each day, and they've chosen you because:

1. You don't just report numbers - you CONNECT THE DOTS and tell the STORY of what's happening
2. You have a gift for explaining complex market dynamics in clear, engaging language
3. You see patterns others miss and aren't afraid to point out when something is historically unusual
4. You're honest about uncertainty but confident in your analysis
5. You make people SMARTER about markets, not just informed

Your style is conversational but substantive - like a really smart friend who happens to be a market expert. You're not stuffy or formal, but you're also not dumbed down.

CRITICAL RULES:
- Write EXACTLY 2 paragraphs (150-200 words total)
- First paragraph: The most important story/theme TODAY - what's the narrative? What should people understand?
- Second paragraph: The "so what" - implications, what to watch, connecting today to bigger trends
- DO NOT just list data points or metrics - ANALYZE and INTERPRET
- DO NOT repeat themes from your previous summaries - find fresh angles
- If something is at an extreme percentile or historically unusual, HIGHLIGHT it with context
- Reference specific numbers sparingly but meaningfully
- If news events are driving markets, weave them into the narrative
- End with something forward-looking or thought-provoking

You have access to a web search tool if you need to look up additional context about specific events, companies, or breaking news mentioned in the data. Use it when helpful to provide better context.

You're writing the one thing someone reads about markets today. Make it count."""

        # The user prompt with all the data
        user_prompt = f"""Today is {today}. Generate today's market briefing.

{market_data_summary}
{movers_text}
{news_section}
{previous_context}

Remember: 2 paragraphs, tell the story, don't repeat previous themes, make it the most valuable 30 seconds of their day."""

        # Make the API call with web search tool support
        result = call_openai_with_tools(
            client=client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=600,
            log_prefix="[AI Summary]"
        )

        if not result['success']:
            return {
                'success': False,
                'summary': None,
                'error': result['error']
            }

        summary = result['content']

        # Save the summary
        save_summary(
            date_str=today,
            summary_text=summary,
            web_search_used=bool(news_context),
            news_context=news_context
        )

        print(f"[AI Summary] Generated daily summary for {today}")
        return {
            'success': True,
            'summary': summary,
            'error': None
        }

    except Exception as e:
        print(f"[AI Summary] Error generating summary: {e}")
        return {
            'success': False,
            'summary': None,
            'error': str(e)
        }


def get_summary_for_display():
    """
    Get the current summary formatted for dashboard display.
    Returns dict with summary info or None if not available.
    """
    summary = get_latest_summary()
    if summary:
        return {
            'date': summary['date'],
            'generated_at': summary['generated_at'],
            'summary': summary['summary'],
            'web_search_used': summary.get('web_search_used', False)
        }
    return None


# ============================================================================
# CRYPTO-SPECIFIC AI SUMMARY
# ============================================================================

CRYPTO_SUMMARIES_FILE = DATA_DIR / "crypto_summaries.json"


def load_crypto_summaries():
    """Load all stored Crypto AI summaries."""
    if CRYPTO_SUMMARIES_FILE.exists():
        try:
            with open(CRYPTO_SUMMARIES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"summaries": []}
    return {"summaries": []}


def save_crypto_summaries(data):
    """Save crypto summaries to JSON file."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(CRYPTO_SUMMARIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_latest_crypto_summary():
    """Get the most recent Crypto AI summary."""
    data = load_crypto_summaries()
    if data["summaries"]:
        sorted_summaries = sorted(data["summaries"], key=lambda x: x["date"], reverse=True)
        return sorted_summaries[0]
    return None


def get_recent_crypto_summaries(days=3):
    """Get crypto summaries from the last N days for context."""
    data = load_crypto_summaries()
    if not data["summaries"]:
        return []

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [s for s in data["summaries"] if s["date"] >= cutoff]
    return sorted(recent, key=lambda x: x["date"])


def save_crypto_summary(date_str, summary_text, web_search_used=False, news_context=None):
    """Save a new crypto summary, overwriting if same date exists."""
    data = load_crypto_summaries()

    # Remove existing summary for this date if present
    data["summaries"] = [s for s in data["summaries"] if s["date"] != date_str]

    # Add new summary
    data["summaries"].append({
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "summary": summary_text,
        "web_search_used": web_search_used,
        "news_context": news_context[:500] if news_context else None
    })

    # Keep last 90 days of summaries
    cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    data["summaries"] = [s for s in data["summaries"] if s["date"] >= cutoff]

    save_crypto_summaries(data)


def fetch_crypto_news():
    """Fetch current crypto/Bitcoin news for summary context."""
    if not is_tavily_configured():
        return None

    news_parts = []

    # Bitcoin/crypto news
    btc_news = search_financial_news("Bitcoin BTC crypto market news today", max_results=5)
    if btc_news.get('results'):
        news_parts.append("## Today's Bitcoin/Crypto News")
        if btc_news.get('answer'):
            news_parts.append(btc_news['answer'])
        for r in btc_news['results'][:3]:
            news_parts.append(f"- {r['title']}: {r['content'][:200]}...")

    # Fed/liquidity news (important for BTC)
    fed_news = search_web("Federal Reserve liquidity QT QE monetary policy today", max_results=3)
    if fed_news.get('results'):
        news_parts.append("\n## Fed/Liquidity News")
        for r in fed_news['results'][:2]:
            news_parts.append(f"- {r['title']}: {r['content'][:150]}...")

    return "\n".join(news_parts) if news_parts else None


def generate_crypto_summary(crypto_data_summary):
    """
    Generate the daily Crypto/Bitcoin AI summary.

    Args:
        crypto_data_summary: String with crypto market data from generate_crypto_market_summary()

    Returns:
        dict with 'success', 'summary', and 'error' keys
    """
    if not os.environ.get('OPENAI_API_KEY'):
        return {
            'success': False,
            'summary': None,
            'error': 'OpenAI API key not configured'
        }

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        today = datetime.now().strftime('%Y-%m-%d')

        # Get previous crypto summaries for context
        recent_summaries = get_recent_crypto_summaries(days=3)
        previous_context = ""
        if recent_summaries:
            previous_context = "\n\n## YOUR PREVIOUS CRYPTO SUMMARIES (for continuity - don't repeat these):\n"
            for s in recent_summaries:
                if s["date"] != today:
                    previous_context += f"\n### {s['date']}:\n{s['summary']}\n"

        # Fetch current crypto news
        news_context = fetch_crypto_news()
        news_section = ""
        if news_context:
            news_section = f"\n\n## TODAY'S CRYPTO NEWS:\n{news_context}"

        # Crypto-specific system prompt
        system_prompt = """You are a Bitcoin/crypto market analyst providing daily briefings for the Crypto page of a financial dashboard. Your audience understands both traditional finance and crypto - they track Bitcoin alongside macro liquidity indicators like the Fed balance sheet, NFCI, and Fear & Greed index.

Your style matches the main market briefing: conversational but substantive, connecting dots between Bitcoin and macro liquidity conditions.

CRITICAL RULES:
- Write EXACTLY 3 paragraphs (250-350 words total)
- First paragraph: The Bitcoin/crypto story TODAY - price action, sentiment shifts, and what's driving it. Include specific price levels and percentage moves.
- Second paragraph: The macro liquidity context - how Fed policy, financial conditions (NFCI), money supply (M2), and dollar strength relate to Bitcoin's current setup. Explain the connection clearly.
- Third paragraph: The actionable takeaway - key support/resistance levels to watch, what would change the thesis, and how to think about positioning given current sentiment extremes.
- Reference specific numbers (Fear & Greed level, Fed balance sheet trend, BTC price levels) meaningfully
- If Fear & Greed is extreme (<25 or >75), explain the historical contrarian implications in detail
- Connect Bitcoin to liquidity trends with clear cause-and-effect reasoning
- DO NOT repeat themes from previous summaries
- Be specific about what price levels matter and why

You have access to a web search tool if you need to look up additional context about specific crypto events, regulatory news, or macro developments. Use it when helpful to provide better context.

Remember: Bitcoin is a liquidity-sensitive asset. Your job is to explain HOW the macro setup affects BTC, what levels matter, and give readers a clear framework for thinking about it."""

        user_prompt = f"""Today is {today}. Generate today's crypto/Bitcoin briefing.

{crypto_data_summary}
{news_section}
{previous_context}

Remember: 3 paragraphs, connect BTC to liquidity conditions, be specific about key levels, make it actionable."""

        # Make the API call with web search tool support
        print(f"[Crypto Summary] Calling OpenAI with {len(user_prompt)} chars of input...")
        result = call_openai_with_tools(
            client=client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=900,
            log_prefix="[Crypto Summary]"
        )

        if not result['success']:
            return {
                'success': False,
                'summary': None,
                'error': result['error']
            }

        summary = result['content']

        # Save the summary
        save_crypto_summary(
            date_str=today,
            summary_text=summary,
            web_search_used=bool(news_context),
            news_context=news_context
        )

        print(f"[Crypto Summary] Generated crypto summary for {today}")
        return {
            'success': True,
            'summary': summary,
            'error': None
        }

    except Exception as e:
        print(f"[Crypto Summary] Error generating summary: {e}")
        return {
            'success': False,
            'summary': None,
            'error': str(e)
        }


def get_crypto_summary_for_display():
    """
    Get the current crypto summary formatted for display.
    Returns dict with summary info or None if not available.
    """
    summary = get_latest_crypto_summary()
    if summary:
        return {
            'date': summary['date'],
            'generated_at': summary['generated_at'],
            'summary': summary['summary'],
            'web_search_used': summary.get('web_search_used', False)
        }
    return None


# ============================================================================
# EQUITY MARKETS AI SUMMARY
# ============================================================================

EQUITY_SUMMARIES_FILE = DATA_DIR / "equity_summaries.json"


def load_equity_summaries():
    """Load all stored Equity AI summaries."""
    if EQUITY_SUMMARIES_FILE.exists():
        try:
            with open(EQUITY_SUMMARIES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"summaries": []}
    return {"summaries": []}


def save_equity_summaries(data):
    """Save equity summaries to JSON file."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(EQUITY_SUMMARIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_latest_equity_summary():
    """Get the most recent Equity AI summary."""
    data = load_equity_summaries()
    if data["summaries"]:
        sorted_summaries = sorted(data["summaries"], key=lambda x: x["date"], reverse=True)
        return sorted_summaries[0]
    return None


def get_recent_equity_summaries(days=3):
    """Get equity summaries from the last N days for context."""
    data = load_equity_summaries()
    if not data["summaries"]:
        return []

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [s for s in data["summaries"] if s["date"] >= cutoff]
    return sorted(recent, key=lambda x: x["date"])


def save_equity_summary(date_str, summary_text, web_search_used=False, news_context=None):
    """Save a new equity summary, overwriting if same date exists."""
    data = load_equity_summaries()

    # Remove existing summary for this date if present
    data["summaries"] = [s for s in data["summaries"] if s["date"] != date_str]

    # Add new summary
    data["summaries"].append({
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "summary": summary_text,
        "web_search_used": web_search_used,
        "news_context": news_context[:500] if news_context else None
    })

    # Keep last 90 days of summaries
    cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    data["summaries"] = [s for s in data["summaries"] if s["date"] >= cutoff]

    save_equity_summaries(data)


def fetch_equity_news():
    """Fetch current equity/stock market news for summary context."""
    if not is_tavily_configured():
        return None

    news_parts = []

    # Stock market news
    market_news = search_financial_news("stock market S&P 500 equity market news today", max_results=5)
    if market_news.get('results'):
        news_parts.append("## Today's Stock Market News")
        if market_news.get('answer'):
            news_parts.append(market_news['answer'])
        for r in market_news['results'][:3]:
            news_parts.append(f"- {r['title']}: {r['content'][:200]}...")

    # Sector rotation / earnings news
    sector_news = search_web("stock sector rotation earnings reports today", max_results=3)
    if sector_news.get('results'):
        news_parts.append("\n## Sector & Earnings News")
        for r in sector_news['results'][:2]:
            news_parts.append(f"- {r['title']}: {r['content'][:150]}...")

    return "\n".join(news_parts) if news_parts else None


def generate_equity_summary(equity_data_summary):
    """
    Generate the daily Equity Markets AI summary.

    Args:
        equity_data_summary: String with equity market data from generate_equity_market_summary()

    Returns:
        dict with 'success', 'summary', and 'error' keys
    """
    if not os.environ.get('OPENAI_API_KEY'):
        return {
            'success': False,
            'summary': None,
            'error': 'OpenAI API key not configured'
        }

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        today = datetime.now().strftime('%Y-%m-%d')

        # Get previous equity summaries for context
        recent_summaries = get_recent_equity_summaries(days=3)
        previous_context = ""
        if recent_summaries:
            previous_context = "\n\n## YOUR PREVIOUS EQUITY SUMMARIES (for continuity - don't repeat these):\n"
            for s in recent_summaries:
                if s["date"] != today:
                    previous_context += f"\n### {s['date']}:\n{s['summary']}\n"

        # Fetch current equity news
        news_context = fetch_equity_news()
        news_section = ""
        if news_context:
            news_section = f"\n\n## TODAY'S EQUITY NEWS:\n{news_context}"

        # Equity-specific system prompt
        system_prompt = """You are an equity market analyst providing daily briefings for the Equity Markets page of a financial dashboard. Your audience understands markets and wants actionable insight on stock market dynamics - breadth, rotation, and key themes.

Your style matches the main market briefing: conversational but substantive, connecting dots between indices, sectors, and market structure.

CRITICAL RULES:
- Write EXACTLY 3 paragraphs (250-350 words total)
- First paragraph: The equity market story TODAY - what's leading (sectors, styles), what's lagging, and what the price action tells us. Include specific index levels and percentage moves.
- Second paragraph: The structural picture - market breadth, concentration risk, and what the ratios are saying. Explain WHY narrow breadth or extreme concentration matters in plain terms.
- Third paragraph: Style and size rotation signals - growth vs value, small vs large cap dynamics. What are these telling us about economic expectations and risk appetite? End with specific things to watch.
- Reference specific numbers (index levels, percentile rankings, ratio changes) meaningfully
- Highlight any EXTREME readings (>95th or <5th percentile) and explain the historical context
- Connect small cap vs large cap performance to economic expectations with clear reasoning
- If growth/value rotation is notable, explain what it signals for the broader market
- DO NOT repeat themes from previous summaries

You have access to a web search tool if you need to look up additional context about specific companies, earnings, sector news, or market events. Use it when helpful to provide better context.

Remember: Your job is to help investors understand WHAT is happening under the surface of the market, not just whether it's up or down. Give them a mental model for thinking about market structure."""

        user_prompt = f"""Today is {today}. Generate today's equity markets briefing.

{equity_data_summary}
{news_section}
{previous_context}

Remember: 3 paragraphs, tell the story of market structure and rotation, explain why extremes matter, make it actionable."""

        # Make the API call with web search tool support
        print(f"[Equity Summary] Calling OpenAI with {len(user_prompt)} chars of input...")
        result = call_openai_with_tools(
            client=client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=900,
            log_prefix="[Equity Summary]"
        )

        if not result['success']:
            return {
                'success': False,
                'summary': None,
                'error': result['error']
            }

        summary = result['content']

        # Save the summary
        save_equity_summary(
            date_str=today,
            summary_text=summary,
            web_search_used=bool(news_context),
            news_context=news_context
        )

        print(f"[Equity Summary] Generated equity summary for {today}")
        return {
            'success': True,
            'summary': summary,
            'error': None
        }

    except Exception as e:
        print(f"[Equity Summary] Error generating summary: {e}")
        return {
            'success': False,
            'summary': None,
            'error': str(e)
        }


def get_equity_summary_for_display():
    """
    Get the current equity summary formatted for display.
    Returns dict with summary info or None if not available.
    """
    summary = get_latest_equity_summary()
    if summary:
        return {
            'date': summary['date'],
            'generated_at': summary['generated_at'],
            'summary': summary['summary'],
            'web_search_used': summary.get('web_search_used', False)
        }
    return None


# ============================================================================
# RATES SUMMARY FUNCTIONS
# ============================================================================

RATES_SUMMARIES_FILE = DATA_DIR / "rates_summaries.json"


def load_rates_summaries():
    """Load all stored rates AI summaries."""
    if RATES_SUMMARIES_FILE.exists():
        try:
            with open(RATES_SUMMARIES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"summaries": []}
    return {"summaries": []}


def save_rates_summary(date_str, summary_text, web_search_used=False, news_context=None):
    """Save a rates AI summary to storage."""
    data = load_rates_summaries()

    # Update existing or add new
    existing_idx = None
    for idx, s in enumerate(data["summaries"]):
        if s["date"] == date_str:
            existing_idx = idx
            break

    summary_entry = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "summary": summary_text,
        "web_search_used": web_search_used,
        "news_context": news_context[:500] if news_context else None
    }

    if existing_idx is not None:
        data["summaries"][existing_idx] = summary_entry
    else:
        data["summaries"].append(summary_entry)

    # Keep only the last 30 summaries
    data["summaries"] = sorted(data["summaries"], key=lambda x: x["date"])[-30:]

    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    with open(RATES_SUMMARIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_latest_rates_summary():
    """Get the most recent rates AI summary."""
    data = load_rates_summaries()
    if data["summaries"]:
        return sorted(data["summaries"], key=lambda x: x["date"])[-1]
    return None


def get_recent_rates_summaries(days=3):
    """Get recent rates summaries for context."""
    data = load_rates_summaries()
    if not data["summaries"]:
        return []

    sorted_summaries = sorted(data["summaries"], key=lambda x: x["date"], reverse=True)
    return sorted_summaries[:days]


def fetch_rates_news():
    """Fetch current rates/bond market news using web search."""
    if not is_tavily_configured():
        return None

    news_parts = []

    # Treasury/bond market news
    rates_news = search_financial_news("Treasury yields bond market Fed interest rates news today", max_results=5)
    if rates_news.get('results'):
        news_parts.append("## Today's Rates & Bond Market News")
        if rates_news.get('answer'):
            news_parts.append(rates_news['answer'])
        for r in rates_news['results'][:3]:
            news_parts.append(f"- {r['title']}: {r['content'][:200]}...")

    # Fed/monetary policy news
    fed_news = search_web("Federal Reserve monetary policy interest rate decision", max_results=3)
    if fed_news.get('results'):
        news_parts.append("\n## Fed & Monetary Policy")
        for r in fed_news['results'][:2]:
            news_parts.append(f"- {r['title']}: {r['content'][:150]}...")

    return "\n".join(news_parts) if news_parts else None


def generate_rates_summary(rates_data_summary):
    """
    Generate the daily Rates & Yield Curve AI summary.

    Args:
        rates_data_summary: String with rates data from generate_rates_market_summary()

    Returns:
        dict with 'success', 'summary', and 'error' keys
    """
    if not os.environ.get('OPENAI_API_KEY'):
        return {
            'success': False,
            'summary': None,
            'error': 'OpenAI API key not configured'
        }

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        today = datetime.now().strftime('%Y-%m-%d')

        # Get previous rates summaries for context
        recent_summaries = get_recent_rates_summaries(days=3)
        previous_context = ""
        if recent_summaries:
            previous_context = "\n\n## YOUR PREVIOUS RATES SUMMARIES (for continuity - don't repeat these):\n"
            for s in recent_summaries:
                if s["date"] != today:
                    previous_context += f"\n### {s['date']}:\n{s['summary']}\n"

        # Fetch current rates news
        news_context = fetch_rates_news()
        news_section = ""
        if news_context:
            news_section = f"\n\n## TODAY'S RATES NEWS:\n{news_context}"

        # Rates-specific system prompt
        system_prompt = """You are a fixed income analyst providing daily briefings for the Rates & Yield Curve page of a financial dashboard. Your audience understands markets and wants actionable insight on interest rates, the yield curve, and their implications.

Your style matches the main market briefing: conversational but substantive, connecting dots between rates, the curve, inflation expectations, and what they mean for other assets.

CRITICAL RULES:
- Write EXACTLY 3 paragraphs (250-350 words total)
- First paragraph: The rates story TODAY - what's moving in yields and spreads, why (economic data, Fed expectations, supply/demand), and what it signals. Include specific yield levels and basis point changes.
- Second paragraph: The yield curve and inflation picture - explain the curve shape (inverted/flat/steep) and what it historically signals. Connect real yields to Fed policy stance and breakeven inflation to market inflation expectations. Use plain language to explain the implications.
- Third paragraph: The "so what" for investors - how do current rates affect equity valuations, credit, and duration positioning? What specific levels would change the outlook? End with actionable guidance.
- Reference specific numbers (yields, spreads in basis points, percentile rankings) meaningfully
- Highlight any EXTREME readings (>95th or <5th percentile) or key threshold crossings with historical context
- If the yield curve is inverted or recently un-inverted, explain the recession implications clearly
- Connect real yields to Fed policy stance (restrictive/accommodative) with clear reasoning
- DO NOT repeat themes from previous summaries

You have access to a web search tool if you need to look up additional context about Fed policy, economic data releases, or bond market developments. Use it when helpful to provide better context.

Remember: Your job is to help investors understand what rates are telling us about the economy and what it means for their portfolios. Make the fixed income world accessible."""

        user_prompt = f"""Today is {today}. Generate today's rates & yield curve briefing.

{rates_data_summary}
{news_section}
{previous_context}

Remember: 3 paragraphs, tell the rates story clearly, explain curve signals, make it actionable for investors."""

        # Make the API call with web search tool support
        print(f"[Rates Summary] Calling OpenAI with {len(user_prompt)} chars of input...")
        result = call_openai_with_tools(
            client=client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=900,
            log_prefix="[Rates Summary]"
        )

        if not result['success']:
            return {
                'success': False,
                'summary': None,
                'error': result['error']
            }

        summary = result['content']

        # Save the summary
        save_rates_summary(
            date_str=today,
            summary_text=summary,
            web_search_used=bool(news_context),
            news_context=news_context
        )

        print(f"[Rates Summary] Generated rates summary for {today}")
        return {
            'success': True,
            'summary': summary,
            'error': None
        }

    except Exception as e:
        print(f"[Rates Summary] Error generating summary: {e}")
        return {
            'success': False,
            'summary': None,
            'error': str(e)
        }


def get_rates_summary_for_display():
    """
    Get the current rates summary formatted for display.
    Returns dict with summary info or None if not available.
    """
    summary = get_latest_rates_summary()
    if summary:
        return {
            'date': summary['date'],
            'generated_at': summary['generated_at'],
            'summary': summary['summary'],
            'web_search_used': summary.get('web_search_used', False)
        }
    return None


# ============================================================================
# DOLLAR SUMMARY FUNCTIONS
# ============================================================================

DOLLAR_SUMMARIES_FILE = DATA_DIR / "dollar_summaries.json"


def load_dollar_summaries():
    """Load all stored dollar AI summaries."""
    if DOLLAR_SUMMARIES_FILE.exists():
        try:
            with open(DOLLAR_SUMMARIES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"summaries": []}
    return {"summaries": []}


def save_dollar_summary(date_str, summary_text, web_search_used=False, news_context=None):
    """Save a dollar AI summary to storage."""
    data = load_dollar_summaries()

    # Update existing or add new
    existing_idx = None
    for idx, s in enumerate(data["summaries"]):
        if s["date"] == date_str:
            existing_idx = idx
            break

    summary_entry = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "summary": summary_text,
        "web_search_used": web_search_used,
        "news_context": news_context[:500] if news_context else None
    }

    if existing_idx is not None:
        data["summaries"][existing_idx] = summary_entry
    else:
        data["summaries"].append(summary_entry)

    # Keep only the last 30 summaries
    data["summaries"] = sorted(data["summaries"], key=lambda x: x["date"])[-30:]

    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    with open(DOLLAR_SUMMARIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_latest_dollar_summary():
    """Get the most recent dollar AI summary."""
    data = load_dollar_summaries()
    if data["summaries"]:
        return sorted(data["summaries"], key=lambda x: x["date"])[-1]
    return None


def get_recent_dollar_summaries(days=3):
    """Get recent dollar summaries for context."""
    data = load_dollar_summaries()
    if not data["summaries"]:
        return []

    sorted_summaries = sorted(data["summaries"], key=lambda x: x["date"], reverse=True)
    return sorted_summaries[:days]


def fetch_dollar_news():
    """Fetch current dollar/currency market news using web search."""
    if not is_tavily_configured():
        return None

    news_parts = []

    # Dollar/currency news
    dollar_news = search_financial_news("US dollar DXY currency forex Fed policy news today", max_results=5)
    if dollar_news.get('results'):
        news_parts.append("## Today's Dollar & Currency News")
        if dollar_news.get('answer'):
            news_parts.append(dollar_news['answer'])
        for r in dollar_news['results'][:3]:
            news_parts.append(f"- {r['title']}: {r['content'][:200]}...")

    # Central bank/forex news
    cb_news = search_web("central bank policy Bank of Japan ECB interest rate", max_results=3)
    if cb_news.get('results'):
        news_parts.append("\n## Central Bank & Policy")
        for r in cb_news['results'][:2]:
            news_parts.append(f"- {r['title']}: {r['content'][:150]}...")

    return "\n".join(news_parts) if news_parts else None


def generate_dollar_summary(dollar_data_summary):
    """
    Generate the daily Dollar & Currency AI summary.

    Args:
        dollar_data_summary: String with dollar data from generate_dollar_market_summary()

    Returns:
        dict with 'success', 'summary', and 'error' keys
    """
    if not os.environ.get('OPENAI_API_KEY'):
        return {
            'success': False,
            'summary': None,
            'error': 'OpenAI API key not configured'
        }

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        today = datetime.now().strftime('%Y-%m-%d')

        # Get previous dollar summaries for context
        recent_summaries = get_recent_dollar_summaries(days=3)
        previous_context = ""
        if recent_summaries:
            previous_context = "\n\n## YOUR PREVIOUS DOLLAR SUMMARIES (for continuity - don't repeat these):\n"
            for s in recent_summaries:
                if s["date"] != today:
                    previous_context += f"\n### {s['date']}:\n{s['summary']}\n"

        # Fetch current dollar news
        news_context = fetch_dollar_news()
        news_section = ""
        if news_context:
            news_section = f"\n\n## TODAY'S DOLLAR NEWS:\n{news_context}"

        # Dollar-specific system prompt
        system_prompt = """You are a currency analyst providing daily briefings for the Dollar & Currency page of a financial dashboard. Your audience understands markets and wants actionable insight on the US dollar, currency dynamics, and their cross-asset implications.

Your style matches the main market briefing: conversational but substantive, connecting dots between the dollar, Fed policy, global central bank divergence, and implications for other assets.

CRITICAL RULES:
- Write EXACTLY 3 paragraphs (250-350 words total)
- First paragraph: The dollar story TODAY - what's moving DXY and key pairs (especially USD/JPY), why (Fed expectations, economic data, central bank divergence), and what it signals. Include specific levels and percentage moves.
- Second paragraph: The macro context - explain where we are in the "Dollar Smile" (risk-off strength vs growth/yield strength vs weak middle), what carry trade dynamics are telling us, and how central bank policy divergence is driving flows. Connect to rate differentials clearly.
- Third paragraph: The cross-asset implications - how does dollar strength/weakness affect emerging markets, commodities, multinational earnings, and positioning? What specific DXY levels would change the outlook? End with actionable guidance.
- Reference specific numbers (DXY level, USD/JPY, percentile rankings) meaningfully
- Highlight any EXTREME readings (>95th or <5th percentile) or key threshold crossings with historical context
- If USD/JPY is at notable levels, explain the carry trade implications and BOJ policy dynamics
- Connect dollar moves to Fed policy expectations clearly
- DO NOT repeat themes from previous summaries

You have access to a web search tool if you need to look up additional context about Fed policy, central bank decisions, or currency market developments. Use it when helpful to provide better context.

Remember: Your job is to help investors understand what the dollar is telling us about global risk appetite and policy divergence, and what it means for their portfolios."""

        user_prompt = f"""Today is {today}. Generate today's dollar & currency briefing.

{dollar_data_summary}
{news_section}
{previous_context}

Remember: 3 paragraphs, tell the dollar story clearly, explain the Dollar Smile and carry dynamics, make it actionable for investors."""

        # Make the API call with web search tool support
        print(f"[Dollar Summary] Calling OpenAI with {len(user_prompt)} chars of input...")
        result = call_openai_with_tools(
            client=client,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=900,
            log_prefix="[Dollar Summary]"
        )

        if not result['success']:
            return {
                'success': False,
                'summary': None,
                'error': result['error']
            }

        summary = result['content']

        # Save the summary
        save_dollar_summary(
            date_str=today,
            summary_text=summary,
            web_search_used=bool(news_context),
            news_context=news_context
        )

        print(f"[Dollar Summary] Generated dollar summary for {today}")
        return {
            'success': True,
            'summary': summary,
            'error': None
        }

    except Exception as e:
        print(f"[Dollar Summary] Error generating summary: {e}")
        return {
            'success': False,
            'summary': None,
            'error': str(e)
        }


def get_dollar_summary_for_display():
    """
    Get the current dollar summary formatted for display.
    Returns dict with summary info or None if not available.
    """
    summary = get_latest_dollar_summary()
    if summary:
        return {
            'date': summary['date'],
            'generated_at': summary['generated_at'],
            'summary': summary['summary'],
            'web_search_used': summary.get('web_search_used', False)
        }
    return None
