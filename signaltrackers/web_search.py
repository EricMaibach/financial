#!/usr/bin/env python3
"""
Web search integration using Tavily API.
Provides web search capabilities for the ChatGPT chatbot.
"""

import os
import requests
from datetime import datetime

# Tavily API configuration
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')
TAVILY_API_URL = 'https://api.tavily.com/search'


def search_web(query, search_depth='basic', max_results=5, include_domains=None, exclude_domains=None):
    """
    Search the web using Tavily API.

    Args:
        query: Search query string
        search_depth: 'basic' or 'advanced' (advanced costs more credits)
        max_results: Maximum number of results to return (1-10)
        include_domains: List of domains to include (optional)
        exclude_domains: List of domains to exclude (optional)

    Returns:
        dict with search results or error
    """
    # Always get fresh API key from environment
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        return {
            'error': 'TAVILY_API_KEY not configured',
            'results': []
        }

    try:
        payload = {
            'api_key': api_key,
            'query': query,
            'search_depth': search_depth,
            'max_results': min(max_results, 10),
            'include_answer': True,  # Get AI-generated answer summary
            'include_raw_content': False,  # Don't need full page content
        }

        if include_domains:
            payload['include_domains'] = include_domains
        if exclude_domains:
            payload['exclude_domains'] = exclude_domains

        response = requests.post(TAVILY_API_URL, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Format results for easy consumption
        results = []
        for item in data.get('results', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': item.get('content', ''),
                'score': item.get('score', 0)
            })

        return {
            'query': query,
            'answer': data.get('answer'),  # AI-generated summary if available
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        return {
            'error': f'Search request failed: {str(e)}',
            'results': []
        }
    except Exception as e:
        return {
            'error': f'Search error: {str(e)}',
            'results': []
        }


def search_financial_news(query, max_results=5):
    """
    Search for financial news, prioritizing financial news sources.

    Args:
        query: Search query string
        max_results: Maximum number of results

    Returns:
        dict with search results
    """
    # Prioritize financial news domains
    financial_domains = [
        'reuters.com',
        'bloomberg.com',
        'wsj.com',
        'ft.com',
        'cnbc.com',
        'marketwatch.com',
        'finance.yahoo.com',
        'seekingalpha.com',
        'zerohedge.com',
        'federalreserve.gov'
    ]

    return search_web(
        query=query,
        search_depth='basic',
        max_results=max_results,
        include_domains=financial_domains
    )


def format_search_results_for_context(search_results):
    """
    Format search results into a string suitable for LLM context.

    Args:
        search_results: Dict returned from search_web()

    Returns:
        Formatted string with search results
    """
    if search_results.get('error'):
        return f"Search error: {search_results['error']}"

    parts = []
    parts.append(f"Web Search Results for: \"{search_results.get('query', '')}\"")
    parts.append(f"Search Time: {search_results.get('timestamp', 'Unknown')}")
    parts.append("")

    # Include AI-generated answer if available
    if search_results.get('answer'):
        parts.append("Summary:")
        parts.append(search_results['answer'])
        parts.append("")

    # Include individual results
    parts.append("Sources:")
    for i, result in enumerate(search_results.get('results', []), 1):
        parts.append(f"\n{i}. {result['title']}")
        parts.append(f"   URL: {result['url']}")
        if result.get('content'):
            # Truncate content if too long
            content = result['content'][:500] + '...' if len(result['content']) > 500 else result['content']
            parts.append(f"   {content}")

    return "\n".join(parts)


# OpenAI function definition for function calling
SEARCH_FUNCTION_DEFINITION = {
    "name": "search_web",
    "description": "Search the internet for current information, news, or data. Use this when you need up-to-date information that may not be in your training data, such as recent news, current events, specific company announcements, or real-time market commentary.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Be specific and include relevant keywords."
            },
            "search_type": {
                "type": "string",
                "enum": ["general", "financial_news"],
                "description": "Type of search: 'general' for broad web search, 'financial_news' to prioritize financial news sources like Reuters, Bloomberg, WSJ, etc."
            }
        },
        "required": ["query"]
    }
}


def execute_search_function(function_args):
    """
    Execute the search function based on OpenAI function calling args.

    Args:
        function_args: Dict with 'query' and optionally 'search_type'

    Returns:
        Formatted string with search results
    """
    query = function_args.get('query', '')
    search_type = function_args.get('search_type', 'general')

    if search_type == 'financial_news':
        results = search_financial_news(query)
    else:
        results = search_web(query)

    return format_search_results_for_context(results)


def is_tavily_configured():
    """Check if Tavily API is configured. Always checks current env var."""
    return bool(os.environ.get('TAVILY_API_KEY'))
