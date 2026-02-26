"""
Recession Probability Module — US-146.1

Fetches and processes three institutional recession probability models:
1. NY Fed 12-month leading model (yield-curve based, direct XLS from newyorkfed.org)
2. Chauvet-Piger coincident model (FRED RECPROUSM156N)
3. Richmond Fed SOS Indicator (direct XLSX from richmondfed.org)

NOTE: NY Fed yield-curve model is NOT on FRED — it is fetched directly from the NY Fed
as an XLS file. See Bug #153 for the fix to add _fetch_ny_fed_direct().

Caching:
- Results stored in data/recession_probability_cache.json
- Cache is read by Flask context processor on every request
- Cache is refreshed by calling update_recession_probability() in run_data_collection()

Graceful degradation:
- If any individual model fetch fails, it is omitted and others still render.
- If all models fail, get_recession_probability() returns None.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_FILE = Path(__file__).parent / 'data' / 'recession_probability_cache.json'

# FRED API key sourced from environment (same as market_signals.py)
_FRED_API_KEY = os.environ.get('FRED_API_KEY')

# FRED series IDs
# NOTE: RECPROUSM156N is "Smoothed U.S. Recession Probabilities" (Chauvet-Piger coincident model).
# The NY Fed 12-month leading model is a separate series; confirm the correct ID.
# Per spec: NY Fed uses RECPROUSM156N. Chauvet-Piger uses the series below.
NY_FED_SERIES = 'RECPROUSM156N'    # NY Fed 12-month leading (spec recommendation — confirm)
CHAUVET_PIGER_SERIES = 'RECPROUSM156N'  # Chauvet-Piger coincident (same series per spec; update when confirmed)

# Richmond Fed SOS Indicator public data URL (confirmed live, HTTP 200 — Bug #154 fix)
_RICHMOND_SOS_URL = (
    'https://www.richmondfed.org/-/media/RichmondFedOrg/assets/data/sos_recession_indicator.xlsx'
)

# Confidence interval: NY Fed applies ±13pp at moderate readings (per NY Fed methodology docs)
_NY_FED_CI_WIDTH = 13.0

# Divergence alert threshold (pp): alert shown when max–min spread ≥ this value
DIVERGENCE_THRESHOLD = 15.0

# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

def _risk_label(value: float) -> str:
    """Map a probability value (0–100) to a risk label per spec thresholds."""
    if value < 15.0:
        return 'Low'
    elif value < 35.0:
        return 'Elevated'
    else:
        return 'High'


def _risk_css_class(value: float) -> str:
    """Map a probability value to CSS modifier class (for recession-model-value)."""
    label = _risk_label(value)
    return label.lower()  # 'low' | 'elevated' | 'high'


# ---------------------------------------------------------------------------
# FRED data fetcher
# ---------------------------------------------------------------------------

def _fetch_fred_latest(series_id: str) -> tuple[Optional[float], Optional[str]]:
    """
    Fetch the latest non-null observation from a FRED series.

    Returns:
        (value, date_str) — e.g. (28.9, '2025-12-01') — or (None, None) on failure.
    """
    if not _FRED_API_KEY:
        logger.warning('FRED_API_KEY not set — skipping series %s', series_id)
        return None, None

    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': _FRED_API_KEY,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 10,  # Fetch last 10; iterate to find first non-null
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        observations = resp.json().get('observations', [])
        for obs in observations:
            raw = obs.get('value', '.')
            if raw in ('.', ''):
                continue
            try:
                return float(raw), obs.get('date', '')
            except (ValueError, TypeError):
                continue
        logger.warning('No valid observations found for FRED series %s', series_id)
        return None, None

    except requests.exceptions.RequestException as exc:
        logger.warning('FRED fetch failed for %s: %s', series_id, exc)
        return None, None
    except Exception as exc:
        logger.warning('Unexpected error fetching FRED series %s: %s', series_id, exc)
        return None, None


# ---------------------------------------------------------------------------
# Richmond Fed SOS fetcher
# ---------------------------------------------------------------------------

def _fetch_richmond_sos() -> tuple[Optional[float], Optional[str]]:
    """
    Fetch the latest Richmond Fed SOS Indicator value.

    The Richmond Fed SOS is a weekly labor/stress indicator published as an XLSX file.

    File layout (Bug #154 confirmed):
        Column 0: Date (Excel serial integer — e.g. 46060 → 2026-02-07)
        Column 1: SOS indicator (float, the actual value to use)
        Column 2: Recession Threshold (constant 0.2 — do NOT use this column)

    Returns:
        (value, date_str) — or (None, None) on failure.
    """
    try:
        resp = requests.get(_RICHMOND_SOS_URL, timeout=10)
        resp.raise_for_status()

        try:
            import pandas as pd
            from io import BytesIO
            df = pd.read_excel(BytesIO(resp.content), header=0)
            # File has 3 columns: Date (serial int), SOS indicator, Recession Threshold
            if df.empty:
                return None, None
            df = df.dropna(subset=[df.columns[1]])  # Drop rows where SOS indicator is null
            if df.empty:
                return None, None
            last_row = df.iloc[-1]
            # Column 0 is an Excel serial integer — convert to ISO date string
            date_serial = int(last_row.iloc[0])
            date_val = (datetime(1899, 12, 31) + timedelta(days=date_serial - 1)).strftime('%Y-%m-%d')
            prob_val = float(last_row.iloc[1])  # SOS indicator (not Recession Threshold constant)
            return prob_val, date_val
        except Exception:
            pass

        logger.warning('Richmond Fed SOS: could not parse response')
        return None, None

    except requests.exceptions.RequestException as exc:
        logger.warning('Richmond Fed SOS fetch failed: %s', exc)
        return None, None
    except Exception as exc:
        logger.warning('Unexpected error fetching Richmond Fed SOS: %s', exc)
        return None, None


# ---------------------------------------------------------------------------
# Interpretation string builder
# ---------------------------------------------------------------------------

def _build_interpretation(models: dict) -> str:
    """
    Build a rules-based 2–3 sentence plain-language interpretation.

    Args:
        models: dict with keys 'ny_fed', 'chauvet_piger', 'richmond_sos' (floats or None)

    Returns:
        2–3 sentence string per spec guidance.
    """
    available = {k: v for k, v in models.items() if v is not None}
    if not available:
        return 'Recession probability data is currently unavailable.'

    values = list(available.values())
    model_names = {
        'ny_fed': 'NY Fed\u2019s 12-month leading model',
        'chauvet_piger': 'Chauvet-Piger coincident model',
        'richmond_sos': 'Richmond Fed SOS Indicator',
    }

    # Find highest-value model to lead with
    highest_key = max(available, key=lambda k: available[k])
    highest_val = available[highest_key]
    highest_label = _risk_label(highest_val)
    highest_name = model_names[highest_key]

    # Sentence 1: Lead with highest-value model signal
    if highest_label == 'High':
        s1 = f'The {highest_name} signals high recession risk at {highest_val:.1f}%.'
    elif highest_label == 'Elevated':
        s1 = (
            f'The {highest_name} suggests elevated recession risk at {highest_val:.1f}%,'
            f' indicating growing near-term uncertainty.'
        )
    else:
        s1 = (
            f'The {highest_name} indicates low recession risk at {highest_val:.1f}%,'
            f' consistent with continued expansion.'
        )

    # Sentence 2: Note agreement or disagreement between leading and coincident models
    if 'ny_fed' in available and 'chauvet_piger' in available:
        spread = abs(available['ny_fed'] - available['chauvet_piger'])
        if spread >= DIVERGENCE_THRESHOLD:
            s2 = (
                f'Coincident indicators diverge from the leading model by {spread:.0f}pp \u2014'
                f' a spread that itself signals elevated uncertainty about the near-term outlook.'
            )
        else:
            if available['ny_fed'] < 15.0 and available['chauvet_piger'] < 15.0:
                s2 = 'Leading and coincident indicators agree: current and forward-looking signals show low recession risk.'
            else:
                s2 = 'Leading and coincident indicators are broadly aligned, suggesting a consistent near-term signal.'
    elif len(available) >= 2:
        # Two or more models, but not NY Fed + Chauvet-Piger pair specifically
        all_labels = [_risk_label(v) for v in available.values()]
        if len(set(all_labels)) == 1:
            s2 = f'Available models are broadly aligned at the {all_labels[0].lower()} risk level.'
        else:
            s2 = 'Available models show divergent signals; monitor developments across sources for confirmation.'
    else:
        s2 = ''

    parts = [s for s in [s1, s2] if s]
    return ' '.join(parts)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> Optional[dict]:
    """Return cached recession probability dict, or None if cache doesn't exist."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as exc:
        logger.warning('Failed to read recession probability cache: %s', exc)
    return None


def _save_cache(data: dict) -> None:
    """Persist recession probability dict to cache file."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, default=str, indent=2)
    except Exception as exc:
        logger.warning('Failed to write recession probability cache: %s', exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_recession_probability() -> Optional[dict]:
    """
    Return the cached recession probability data.

    Returns None if no cache exists or cache is corrupted.
    Called by the Flask context processor on every request.
    """
    return _load_cache()


def update_recession_probability() -> None:
    """
    Fetch latest data from all three model sources, compute derived fields,
    and write to the cache file.

    Called once per daily data refresh cycle (run_data_collection).
    Errors from individual model fetches are non-fatal (graceful degradation).
    """
    updated_at = datetime.now(timezone.utc).isoformat()

    # Fetch individual models
    ny_fed_val, ny_fed_date = _fetch_fred_latest(NY_FED_SERIES)
    cp_val, cp_date = _fetch_fred_latest(CHAUVET_PIGER_SERIES)
    sos_val, sos_date = _fetch_richmond_sos()

    # At least one model must be available
    available_models = {
        k: v for k, v in [
            ('ny_fed', ny_fed_val),
            ('chauvet_piger', cp_val),
            ('richmond_sos', sos_val),
        ] if v is not None
    }

    if not available_models:
        logger.warning('No recession probability model data available — skipping cache update')
        return

    # NY Fed confidence interval (±13pp, clamped to [0, 100])
    ny_fed_lower = None
    ny_fed_upper = None
    if ny_fed_val is not None:
        ny_fed_lower = round(max(0.0, ny_fed_val - _NY_FED_CI_WIDTH), 1)
        ny_fed_upper = round(min(100.0, ny_fed_val + _NY_FED_CI_WIDTH), 1)

    # Divergence (max–min across all available models)
    all_values = list(available_models.values())
    divergence_pp = round(max(all_values) - min(all_values), 1) if len(all_values) >= 2 else 0.0

    # Interpretation string
    interpretation = _build_interpretation({
        'ny_fed': ny_fed_val,
        'chauvet_piger': cp_val,
        'richmond_sos': sos_val,
    })

    # Formatted update timestamp (e.g. "Feb 26, 2026")
    try:
        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        updated_display = dt.strftime('%b %-d, %Y')
    except (ValueError, AttributeError):
        updated_display = ''

    data = {
        'updated_at': updated_at,
        'updated': updated_display,
    }

    # Per-model fields (only include models where data is available)
    if ny_fed_val is not None:
        data['ny_fed'] = round(ny_fed_val, 1)
        data['ny_fed_lower'] = ny_fed_lower
        data['ny_fed_upper'] = ny_fed_upper
        data['ny_fed_date'] = ny_fed_date or ''
        data['ny_fed_risk'] = _risk_label(ny_fed_val)
        data['ny_fed_css'] = _risk_css_class(ny_fed_val)

    if cp_val is not None:
        data['chauvet_piger'] = round(cp_val, 1)
        data['chauvet_piger_date'] = cp_date or ''
        data['chauvet_piger_risk'] = _risk_label(cp_val)
        data['chauvet_piger_css'] = _risk_css_class(cp_val)

    if sos_val is not None:
        data['richmond_sos'] = round(sos_val, 1)
        data['richmond_sos_date'] = sos_date or ''
        data['richmond_sos_risk'] = _risk_label(sos_val)
        data['richmond_sos_css'] = _risk_css_class(sos_val)

    data['divergence_pp'] = divergence_pp
    data['interpretation'] = interpretation

    # Mobile summary: e.g. "Low–Elevated · Models diverging"
    risk_labels = [_risk_label(v) for v in all_values]
    unique_labels = sorted(set(risk_labels), key=['Low', 'Elevated', 'High'].index)
    risk_summary = '\u2013'.join(unique_labels) if len(unique_labels) > 1 else unique_labels[0]
    alignment = 'Models diverging' if divergence_pp >= DIVERGENCE_THRESHOLD else 'Models aligned'
    data['mobile_summary'] = f'{risk_summary} \u00b7 {alignment}'

    _save_cache(data)
    logger.info(
        'Recession probability updated: ny_fed=%s chauvet_piger=%s richmond_sos=%s divergence=%.1fpp',
        ny_fed_val, cp_val, sos_val, divergence_pp,
    )
