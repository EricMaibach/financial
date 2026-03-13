#!/usr/bin/env python3
"""
Daily macro news pipeline.

Fetches news across six market topic areas via Tavily, stores full article
content keyed by date, and generates a single cross-market AI summary.

Usage:
    from news_pipeline import run_news_pipeline, get_stored_news

    run_news_pipeline()          # fetch + store + summarize
    data = get_stored_news()     # read stored data for today (or recent)
"""

import json
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pytz
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / 'data'
NEWS_CACHE_FILE = DATA_DIR / 'news_data.json'

RETENTION_DAYS = 90

# ---------------------------------------------------------------------------
# Topic queries
# ---------------------------------------------------------------------------
TOPIC_QUERIES = [
    ('macro',   'macroeconomic news today federal reserve GDP inflation employment'),
    ('crypto',  'cryptocurrency Bitcoin Ethereum crypto market news today'),
    ('equity',  'stock market equity S&P 500 earnings news today'),
    ('rates',   'interest rates treasury yields bond market news today'),
    ('dollar',  'US dollar DXY currency forex news today'),
    ('credit',  'credit markets corporate bonds spreads high yield news today'),
]

TAVILY_API_URL = 'https://api.tavily.com/search'

# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def _fetch_topic(api_key: str, topic: str, query: str) -> list[dict]:
    """Fetch articles for one topic. Returns list of article dicts."""
    try:
        payload = {
            'api_key': api_key,
            'query': query,
            'search_depth': 'advanced',
            'max_results': 7,
            'include_raw_content': True,
            'include_answer': False,
        }
        resp = requests.post(TAVILY_API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning('[news_pipeline] Tavily fetch failed for topic=%s: %s', topic, exc)
        return []

    articles = []
    for item in data.get('results', []):
        url = item.get('url', '')
        try:
            domain = urlparse(url).netloc.lstrip('www.')
        except Exception:
            domain = ''
        raw = item.get('raw_content') or item.get('content', '')
        articles.append({
            'headline': item.get('title', ''),
            'url': url,
            'source': domain,
            'timestamp': datetime.now(tz=pytz.utc).isoformat(),
            'raw_content': raw,
            'topic': topic,
        })
    return articles


# ---------------------------------------------------------------------------
# AI summarization
# ---------------------------------------------------------------------------

def _generate_cross_market_summary(articles: list[dict]) -> str | None:
    """
    Generate a single cross-market prose summary from all articles.
    Returns the summary string, or None if AI is unavailable.
    """
    # Build article digest for the prompt (cap per-article length to save tokens)
    digest_parts = []
    for art in articles[:40]:  # max 40 articles
        content_snippet = (art['raw_content'] or '')[:600]
        digest_parts.append(
            f"[{art['topic'].upper()}] {art['headline']}\n"
            f"Source: {art['source']}\n"
            f"{content_snippet}"
        )
    digest = '\n\n---\n\n'.join(digest_parts)

    system_prompt = (
        "You are a senior macro analyst writing a daily market briefing for sophisticated investors. "
        "Write a comprehensive cross-market summary of today's news in 3-5 prose paragraphs. "
        "Do NOT use bullet points or headers. Write in flowing, analytical prose. "
        "Cover the major themes across macro, equities, rates, credit, crypto, and currencies. "
        "Focus on what matters most and how the pieces connect. Be direct and authoritative."
    )
    user_prompt = (
        f"Today's date: {date.today().isoformat()}\n\n"
        f"Here are today's key articles across all market areas:\n\n{digest}\n\n"
        "Write your cross-market summary now."
    )

    # Try Anthropic first, fall back to OpenAI
    provider = os.environ.get('AI_PROVIDER', 'openai').lower()

    if provider == 'anthropic':
        return _summarize_with_anthropic(system_prompt, user_prompt)
    else:
        return _summarize_with_openai(system_prompt, user_prompt)


def _summarize_with_openai(system_prompt: str, user_prompt: str) -> str | None:
    try:
        from openai import OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return None
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model='gpt-5.2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_completion_tokens=1200,
            temperature=0.6,
        )
        content = resp.choices[0].message.content
        return content.strip() if content else None
    except Exception as exc:
        logger.warning('[news_pipeline] OpenAI summarization failed: %s', exc)
        return None


def _summarize_with_anthropic(system_prompt: str, user_prompt: str) -> str | None:
    try:
        import anthropic as anthropic_lib
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return None
        client = anthropic_lib.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model='claude-opus-4-6',
            max_tokens=1200,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_prompt}],
        )
        content = msg.content[0].text if msg.content else None
        return content.strip() if content else None
    except Exception as exc:
        logger.warning('[news_pipeline] Anthropic summarization failed: %s', exc)
        return None


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if not NEWS_CACHE_FILE.exists():
        return {}
    try:
        with open(NEWS_CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(NEWS_CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _prune(data: dict) -> dict:
    """Remove entries older than RETENTION_DAYS."""
    cutoff = (date.today() - timedelta(days=RETENTION_DAYS)).isoformat()
    return {k: v for k, v in data.items() if k >= cutoff}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_news_pipeline() -> bool:
    """
    Fetch daily macro news, store articles, and generate a cross-market summary.

    Returns True on success, False if Tavily is unavailable.
    Failures in individual topic fetches or summarization are non-fatal.
    """
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        logger.info('[news_pipeline] TAVILY_API_KEY not set — skipping news pipeline')
        return False

    today = date.today().isoformat()
    logger.info('[news_pipeline] Starting news pipeline for %s', today)

    # Fetch all topic areas
    all_articles = []
    for topic, query in TOPIC_QUERIES:
        logger.info('[news_pipeline] Fetching topic: %s', topic)
        articles = _fetch_topic(api_key, topic, query)
        all_articles.extend(articles)
        logger.info('[news_pipeline] Got %d articles for topic %s', len(articles), topic)

    logger.info('[news_pipeline] Total articles fetched: %d', len(all_articles))

    # Generate cross-market AI summary
    logger.info('[news_pipeline] Generating cross-market summary...')
    summary = _generate_cross_market_summary(all_articles) if all_articles else None
    if summary:
        logger.info('[news_pipeline] Summary generated (%d chars)', len(summary))
    else:
        logger.warning('[news_pipeline] Summary generation failed or returned empty')

    # Build record
    eastern = pytz.timezone('US/Eastern')
    record = {
        'date': today,
        'fetched_at': datetime.now(eastern).isoformat(),
        'articles': all_articles,
        'summary': summary,
    }

    # Load, update, prune, save
    cache = _load_cache()
    cache[today] = record
    cache = _prune(cache)
    _save_cache(cache)

    logger.info('[news_pipeline] News pipeline complete for %s', today)
    return True


def get_stored_news(max_stale_days: int = 7) -> dict | None:
    """
    Return stored news data.

    Checks today's record first. If absent, returns the most recent record
    within max_stale_days. Returns None if no suitable record exists or if
    the storage file is missing/malformed.

    Args:
        max_stale_days: How many days old the most recent record may be.

    Returns:
        dict with keys 'date', 'fetched_at', 'articles', 'summary', or None.
    """
    try:
        cache = _load_cache()
    except Exception:
        return None

    if not cache:
        return None

    today = date.today().isoformat()

    # Prefer today's record
    if today in cache:
        return cache[today]

    # Fall back to most recent within stale window
    cutoff = (date.today() - timedelta(days=max_stale_days)).isoformat()
    candidates = {k: v for k, v in cache.items() if k >= cutoff}
    if not candidates:
        return None

    most_recent_key = max(candidates.keys())
    return candidates[most_recent_key]
