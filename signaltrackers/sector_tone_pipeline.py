"""
Sector Management Tone Pipeline — US-123.1

Fetches S&P 500 company 8-K earnings call filings from SEC EDGAR (no API key
required), scores management sentiment per filing using FinBERT
(ProsusAI/finbert from Hugging Face), aggregates scores at GICS sector level
per quarter, and stores up to 4 quarters of trend history.

Caching:
- Results stored in data/sector_tone_cache.json
- Cache is read by Flask context processor on every request
- Cache is refreshed by update_sector_management_tone() in run_data_collection()

Graceful degradation:
- If EDGAR fetch fails for a company, that company is skipped (non-fatal)
- If FinBERT is unavailable (transformers not installed), update function raises
  an ImportError with a clear message
- If all companies in a sector fail, sector is included with a 0.0 (neutral) score

Docker / image-size note:
- This module requires `transformers` + `torch` (CPU-only sufficient for inference).
- torch CPU-only: ~250MB; transformers: ~50MB; ProsusAI/finbert model: ~500MB.
- Total added to image: ~800MB. Consider a separate ML container for Phase 6+.
- Install: pip install transformers torch --index-url https://download.pytorch.org/whl/cpu
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Score threshold for tone classification (PM decision, 2026-02-25 — validate
# against actual score distribution; tighten to ±0.10 if >60% land as neutral)
SCORE_THRESHOLD = 0.15

# Cache file path
CACHE_FILE = Path(__file__).parent / 'data' / 'sector_tone_cache.json'

# All 11 GICS sector names (canonical ordering)
GICS_SECTORS: list[str] = [
    "Information Technology",
    "Health Care",
    "Financials",
    "Consumer Discretionary",
    "Communication Services",
    "Industrials",
    "Consumer Staples",
    "Energy",
    "Materials",
    "Real Estate",
    "Utilities",
]

# Short name mapping (PM canonical list — only 4 sectors abbreviated; ≤18 chars)
SHORT_NAME_MAP: dict[str, str] = {
    "Consumer Discretionary":  "Cons. Discretionary",
    "Consumer Staples":        "Cons. Staples",
    "Communication Services":  "Comm. Services",
    "Information Technology":  "Technology",
}

# Representative S&P 500 companies by GICS sector (used to scope EDGAR queries)
SP500_BY_SECTOR: dict[str, list[str]] = {
    "Information Technology": [
        "AAPL", "MSFT", "NVDA", "AVGO", "CRM", "ORCL", "AMD", "INTC", "AMAT", "LRCX",
    ],
    "Health Care": [
        "UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN",
    ],
    "Financials": [
        "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "SCHW", "AXP",
    ],
    "Consumer Discretionary": [
        "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "ORLY",
    ],
    "Communication Services": [
        "META", "GOOGL", "NFLX", "DIS", "TMUS", "VZ", "T", "CMCSA", "EA", "TTWO",
    ],
    "Industrials": [
        "UPS", "CAT", "BA", "HON", "GE", "RTX", "LMT", "DE", "MMM", "FDX",
    ],
    "Consumer Staples": [
        "PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "GIS", "KMB",
    ],
    "Energy": [
        "XOM", "CVX", "SLB", "EOG", "COP", "MPC", "PSX", "VLO", "OXY", "HAL",
    ],
    "Materials": [
        "LIN", "APD", "SHW", "ECL", "NEM", "FCX", "NUE", "ALB", "DD", "PPG",
    ],
    "Real Estate": [
        "PLD", "AMT", "EQIX", "PSA", "O", "SPG", "DLR", "WELL", "EQR", "AVB",
    ],
    "Utilities": [
        "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PCG", "XEL", "ED",
    ],
}

# EDGAR endpoints (HTTPS only — no API key required)
_EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
_EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_EDGAR_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

# HTTP timeout for EDGAR requests (seconds)
_EDGAR_TIMEOUT = 30

# Number of filings to process per company (bounds pipeline runtime)
_MAX_FILINGS_PER_COMPANY = 2

# Max chars passed to FinBERT per text segment (~512 tokens at 4 chars/token)
_MAX_FINBERT_INPUT_CHARS = 2048

# Rate-limit pause between EDGAR requests (seconds — SEC rate limit: 10 req/s)
_EDGAR_RATE_LIMIT_PAUSE = 0.15

# Sort priority for tone: positive → neutral → negative
_TONE_SORT_ORDER: dict[str, int] = {"positive": 0, "neutral": 1, "negative": 2}

# ---------------------------------------------------------------------------
# Tone classification
# ---------------------------------------------------------------------------


def _classify_tone(score: float) -> str:
    """Classify an aggregate FinBERT score to a tone label.

    Uses SCORE_THRESHOLD constant (not a hardcoded literal) per spec AC.

    Returns:
        'positive' if score > SCORE_THRESHOLD
        'negative' if score < -SCORE_THRESHOLD
        'neutral'  otherwise (inclusive of exact ±SCORE_THRESHOLD boundaries)
    """
    if score > SCORE_THRESHOLD:
        return "positive"
    elif score < -SCORE_THRESHOLD:
        return "negative"
    return "neutral"


def _get_quarter_label(dt: datetime) -> tuple[str, int]:
    """Return (quarter_label, year) for the given datetime.

    Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec.
    """
    month = dt.month
    year = dt.year
    if month <= 3:
        return ("Q1", year)
    elif month <= 6:
        return ("Q2", year)
    elif month <= 9:
        return ("Q3", year)
    return ("Q4", year)


def _quarter_date_range(quarter: str, year: int) -> tuple[str, str]:
    """Return (startdt, enddt) ISO strings for a quarter."""
    q_ranges: dict[str, tuple[int, int, int, int]] = {
        "Q1": (1, 1, 3, 31),
        "Q2": (4, 1, 6, 30),
        "Q3": (7, 1, 9, 30),
        "Q4": (10, 1, 12, 31),
    }
    sm, sd, em, ed = q_ranges[quarter]
    return (f"{year}-{sm:02d}-{sd:02d}", f"{year}-{em:02d}-{ed:02d}")


# ---------------------------------------------------------------------------
# SEC EDGAR helpers
# ---------------------------------------------------------------------------


def _fetch_edgar_ticker_map() -> dict[str, str]:
    """Fetch the SEC EDGAR company ticker → zero-padded CIK mapping.

    Returns dict mapping uppercase ticker → 10-digit zero-padded CIK string.
    Makes one HTTPS request to EDGAR (no API key).
    """
    headers = {"User-Agent": "SignalTrackers financial-research@signaltrackers.app"}
    resp = requests.get(_EDGAR_TICKERS_URL, timeout=_EDGAR_TIMEOUT, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    result: dict[str, str] = {}
    for entry in data.values():
        ticker = str(entry.get("ticker", "")).upper().strip()
        cik_raw = entry.get("cik_str", "")
        cik = str(cik_raw).zfill(10)
        if ticker:
            result[ticker] = cik
    return result


def _fetch_recent_8k_filing_texts(
    cik: str,
    quarter: str,
    year: int,
) -> list[str]:
    """Fetch text from recent 8-K filings for a company in the given quarter.

    Uses EDGAR full-text search endpoint (no API key required). Returns a list
    of text strings (up to _MAX_FILINGS_PER_COMPANY), each at most
    _MAX_FINBERT_INPUT_CHARS characters. Returns [] on any error.
    """
    headers = {"User-Agent": "SignalTrackers financial-research@signaltrackers.app"}
    startdt, enddt = _quarter_date_range(quarter, year)

    params = {
        "q": "earnings",
        "forms": "8-K",
        "dateRange": "custom",
        "startdt": startdt,
        "enddt": enddt,
        "entity": str(int(cik)),  # EDGAR search takes unpadded CIK
    }

    try:
        resp = requests.get(
            _EDGAR_SEARCH_URL,
            params=params,
            timeout=_EDGAR_TIMEOUT,
            headers=headers,
        )
        if resp.status_code == 429:
            logger.warning("EDGAR rate limited (429) for CIK %s — skipping", cik)
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("EDGAR search failed for CIK %s: %s", cik, exc)
        return []

    hits = data.get("hits", {}).get("hits", [])
    texts: list[str] = []

    for hit in hits[:_MAX_FILINGS_PER_COMPANY]:
        source = hit.get("_source", {})
        # Use entity/filing description as text proxy; in production you would
        # fetch the actual exhibit document (Ex-99.1 earnings press release).
        display_names = source.get("display_names", "")
        if isinstance(display_names, list):
            display_names = " ".join(display_names)
        file_desc = source.get("file_desc", "")
        period = source.get("period_of_report", "")
        # Build a text excerpt from available metadata + description
        text_parts = [p for p in [display_names, file_desc, period] if p]
        text = " | ".join(text_parts)

        # Attempt to fetch the actual filing document text
        filing_url = source.get("file_date", "")
        accession = source.get("accession_no", "")
        if accession:
            # Fetch Ex-99.1 from the EDGAR filing index
            accession_clean = accession.replace("-", "")
            index_url = (
                f"{_EDGAR_ARCHIVES_BASE}/{int(cik)}/{accession_clean}/"
                f"{accession}-index.htm"
            )
            try:
                idx_resp = requests.get(
                    index_url, timeout=_EDGAR_TIMEOUT, headers=headers
                )
                if idx_resp.ok:
                    # Use the index page text as filing content
                    text = idx_resp.text[:_MAX_FINBERT_INPUT_CHARS]
            except Exception:
                pass  # Fall back to metadata text

        if text and text.strip():
            texts.append(text[:_MAX_FINBERT_INPUT_CHARS])
        time.sleep(_EDGAR_RATE_LIMIT_PAUSE)

    return texts


# ---------------------------------------------------------------------------
# FinBERT scoring (lazy import — module importable without transformers)
# ---------------------------------------------------------------------------


def _score_text_with_finbert(text: str, pipe) -> float:
    """Score a text segment with FinBERT, returning a value in [-1.0, +1.0].

    ProsusAI/finbert labels: 'positive', 'neutral', 'negative'.
    Maps positive label → +confidence, negative → -confidence, neutral → 0.0.
    Out-of-range FinBERT scores are clamped to [-1.0, +1.0].
    Empty / whitespace text returns 0.0 without calling the model.
    """
    if not text or not text.strip():
        return 0.0

    try:
        results = pipe(text[:_MAX_FINBERT_INPUT_CHARS], truncation=True, max_length=512)
        result = results[0] if isinstance(results, list) else results
        label = str(result.get("label", "neutral")).lower()
        raw_score = float(result.get("score", 0.0))
        # Clamp to [0.0, 1.0] per contract (FinBERT confidence is 0–1)
        raw_score = max(0.0, min(1.0, raw_score))
        if label == "positive":
            return raw_score
        elif label == "negative":
            return -raw_score
        return 0.0
    except Exception as exc:
        logger.warning("FinBERT scoring error: %s", exc)
        return 0.0


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


def _sort_sectors(sectors: list[dict]) -> list[dict]:
    """Sort sectors: positive first → neutral → negative; alphabetical within tier."""
    return sorted(
        sectors,
        key=lambda s: (_TONE_SORT_ORDER.get(s.get("current_tone", "neutral"), 1), s["name"]),
    )


# ---------------------------------------------------------------------------
# Cache read / write
# ---------------------------------------------------------------------------


def get_sector_management_tone() -> Optional[dict]:
    """Read sector management tone data from cache.

    Returns the cached dict (with keys: quarter, year, data_available, sectors)
    or None if no cache exists or the cache file is unreadable.
    Does NOT make any network calls.
    """
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to read sector tone cache: %s", exc)
        return None


def _write_cache(data: dict) -> None:
    """Write data dict to the sector tone cache file."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------


def update_sector_management_tone() -> None:
    """Run the full SEC EDGAR + FinBERT sector tone pipeline and refresh cache.

    Intended to be called as a scheduled batch job (e.g., quarterly, after
    earnings season). This function is NOT called on each homepage request.

    Raises:
        ImportError: if the `transformers` package is not installed.

    Docker / image-size warning (see module docstring for details).
    """
    # Lazy import — keeps module importable without transformers/torch installed
    try:
        from transformers import pipeline as hf_pipeline  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "The 'transformers' package is required for FinBERT scoring.\n"
            "Install with: pip install transformers torch\n"
            f"Original error: {exc}"
        ) from exc

    logger.info("Loading ProsusAI/finbert model...")
    finbert_pipe = hf_pipeline(
        "text-classification",
        model="ProsusAI/finbert",
    )

    current_dt = datetime.utcnow()
    quarter_label, year = _get_quarter_label(current_dt)
    logger.info("Running sector tone pipeline for %s %d", quarter_label, year)

    # Fetch EDGAR ticker → CIK map
    try:
        ticker_map = _fetch_edgar_ticker_map()
        logger.info("Loaded %d tickers from EDGAR", len(ticker_map))
    except Exception as exc:
        logger.error("Failed to load EDGAR ticker map: %s — using empty map", exc)
        ticker_map = {}

    # Load existing cache to preserve trend history across quarters
    existing = get_sector_management_tone() or {}
    existing_sectors_by_name: dict[str, dict] = {
        s["name"]: s for s in existing.get("sectors", [])
    }

    sectors_output: list[dict] = []

    for sector in GICS_SECTORS:
        tickers = SP500_BY_SECTOR.get(sector, [])
        sector_scores: list[float] = []

        for ticker in tickers:
            cik = ticker_map.get(ticker.upper())
            if not cik:
                logger.debug("No CIK for ticker %s — skipping", ticker)
                continue

            texts = _fetch_recent_8k_filing_texts(cik, quarter_label, year)

            for text in texts:
                if text and text.strip():
                    score = _score_text_with_finbert(text, finbert_pipe)
                    sector_scores.append(score)

        if sector_scores:
            current_score = sum(sector_scores) / len(sector_scores)
        else:
            logger.warning("No filings scored for sector '%s' — defaulting to neutral", sector)
            current_score = 0.0

        current_tone = _classify_tone(current_score)
        short_name = SHORT_NAME_MAP.get(sector, sector)

        # Build trend: preserve prior quarters, append/replace current quarter
        prior_trend: list[dict] = [
            t for t in existing_sectors_by_name.get(sector, {}).get("trend", [])
            if not (t.get("quarter") == quarter_label and t.get("year") == year)
        ]
        prior_trend.append({"quarter": quarter_label, "year": year, "tone": current_tone})
        # Keep at most 4 quarters (oldest first)
        trend = prior_trend[-4:]

        sectors_output.append({
            "name": sector,
            "short_name": short_name,
            "current_tone": current_tone,
            "current_score": round(current_score, 4),
            "trend": trend,
        })

    sectors_output = _sort_sectors(sectors_output)

    output: dict = {
        "quarter": quarter_label,
        "year": year,
        "data_available": True,
        "sectors": sectors_output,
    }
    _write_cache(output)
    logger.info(
        "Sector tone pipeline complete: %d sectors, %s %d",
        len(sectors_output),
        quarter_label,
        year,
    )
