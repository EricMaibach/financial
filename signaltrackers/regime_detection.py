"""
Macro regime detection engine.

Derives the current Bull / Neutral / Bear / Recession Watch macro regime
state from FRED economic data using a modified k-means clustering approach
inspired by Oliveira et al. (arXiv 2503.11499).

Data sourcing priority:
1. Read from local CSV files (populated by market_signals.py daily run)
2. Fetch from FRED API directly if CSV files are unavailable
3. Fall back to rule-based classification if no data can be obtained

Caching:
- Result is stored in data/macro_regime_cache.json after each calculation
- Cache is read by the Flask context processor on every request
- Cache is refreshed by calling update_macro_regime() in run_data_collection()
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from regime_config import (
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_LOW_THRESHOLD,
    REGIME_CLASSIFICATION_FEATURES,
    REGIME_METADATA,
    VALID_REGIMES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_FILE = Path(__file__).parent / 'data' / 'macro_regime_cache.json'
DATA_DIR = Path(__file__).parent / 'data'

# Number of months of history to use for k-means fitting
HISTORY_MONTHS = 60  # 5 years

# Feature column names used in the model (order matters for centroid mapping)
_FEATURES = list(REGIME_CLASSIFICATION_FEATURES.keys())

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _load_cache() -> Optional[dict]:
    """Return cached regime dict, or None if cache doesn't exist."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as exc:
        logger.warning('Failed to read regime cache: %s', exc)
    return None


def _save_cache(regime_dict: dict) -> None:
    """Persist regime dict to cache file."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(regime_dict, f, default=str, indent=2)
    except Exception as exc:
        logger.warning('Failed to write regime cache: %s', exc)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_csv_series(metric_key: str) -> Optional[pd.Series]:
    """
    Load a time series from an existing CSV data file.

    Returns a pandas Series indexed by date, or None if the file doesn't
    exist or can't be read.
    """
    csv_path = DATA_DIR / f'{metric_key}.csv'
    if not csv_path.exists():
        return None
    try:
        df = pd.read_csv(csv_path)
        if df.empty or len(df.columns) < 2:
            return None
        df['date'] = pd.to_datetime(df['date'])
        value_col = df.columns[1]
        df = df.dropna(subset=[value_col]).set_index('date')
        return df[value_col].astype(float)
    except Exception as exc:
        logger.warning('Failed to read CSV for %s: %s', metric_key, exc)
        return None


def _fetch_fred_series(fred_series_id: str, fred_api_key: str) -> Optional[pd.Series]:
    """Fetch a FRED series via API. Returns Series indexed by date or None."""
    import requests

    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': fred_series_id,
        'api_key': fred_api_key,
        'file_type': 'json',
        'observation_start': '2000-01-01',
        'sort_order': 'asc',
        'units': 'lin',
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        obs = data.get('observations', [])
        if not obs:
            return None
        rows = [
            (o['date'], float(o['value']))
            for o in obs
            if o['value'] != '.'
        ]
        if not rows:
            return None
        dates, values = zip(*rows)
        return pd.Series(values, index=pd.to_datetime(dates), dtype=float)
    except Exception as exc:
        logger.warning('FRED fetch failed for %s: %s', fred_series_id, exc)
        return None


def _load_feature_data() -> Optional[pd.DataFrame]:
    """
    Build a DataFrame of feature columns, sourced from CSV files first
    and FRED API as fallback.

    Returns a monthly-resampled DataFrame, or None if insufficient data.
    """
    fred_api_key = os.environ.get('FRED_API_KEY', '')
    series_map: dict[str, pd.Series] = {}

    for metric_key, fred_id in REGIME_CLASSIFICATION_FEATURES.items():
        # Try local CSV first
        series = _load_csv_series(metric_key)
        if series is None or len(series) < 12:
            # Fall back to FRED API
            if fred_api_key:
                series = _fetch_fred_series(fred_id, fred_api_key)
            else:
                logger.warning(
                    'No local data for %s and FRED_API_KEY not set; skipping.',
                    metric_key,
                )
        if series is not None and not series.empty:
            series_map[metric_key] = series

    if len(series_map) < 2:
        logger.warning('Insufficient feature data for regime classification.')
        return None

    # Align to monthly frequency (end of month)
    df = pd.DataFrame(series_map)
    df = df.resample('ME').last()
    df = df.dropna(how='all')
    return df


# ---------------------------------------------------------------------------
# Rule-based fallback classifier
# ---------------------------------------------------------------------------


def _rule_based_regime(latest: dict) -> str:
    """
    Simple threshold-based regime classification.

    Used when there is insufficient historical data for k-means.
    """
    hy = latest.get('high_yield_spread', None)
    curve = latest.get('yield_curve_10y2y', None)
    nfci = latest.get('nfci', None)
    claims = latest.get('initial_claims', None)

    stress_score = 0

    if hy is not None:
        if hy > 600:
            stress_score += 3
        elif hy > 450:
            stress_score += 2
        elif hy > 300:
            stress_score += 1

    if curve is not None:
        if curve < -0.5:
            stress_score += 3
        elif curve < 0:
            stress_score += 1

    if nfci is not None:
        if nfci > 0.5:
            stress_score += 2
        elif nfci > 0:
            stress_score += 1

    if claims is not None:
        # Claims > 300k is elevated; >400k is severe
        if claims > 400:
            stress_score += 2
        elif claims > 300:
            stress_score += 1

    if stress_score >= 7:
        return 'Recession Watch'
    elif stress_score >= 4:
        return 'Bear'
    elif stress_score >= 2:
        return 'Neutral'
    else:
        return 'Bull'


# ---------------------------------------------------------------------------
# K-means classification
# ---------------------------------------------------------------------------


def _kmeans_regime(df: pd.DataFrame) -> tuple[str, str]:
    """
    Classify the most recent data point using k-means clustering (k=4).

    Returns (regime_name, confidence_level).

    Cluster-to-regime mapping is determined by sorting cluster centroids
    by a macro stress composite score:
        stress = HY_spread_norm + (-yield_curve_norm) + NFCI_norm + claims_norm

    Highest stress centroid → Recession Watch, then Bear, Neutral, Bull.
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    # Use available columns only
    available = [col for col in _FEATURES if col in df.columns]
    df_feat = df[available].copy()

    # Use at most HISTORY_MONTHS of monthly data
    if len(df_feat) > HISTORY_MONTHS:
        df_feat = df_feat.iloc[-HISTORY_MONTHS:]

    # Forward-fill then back-fill to handle gaps in monthly data
    df_feat = df_feat.ffill().bfill()

    # Drop rows with any remaining NaN (strict: need all features)
    df_clean = df_feat.dropna()

    if len(df_clean) < 24:  # Need at least 2 years to fit meaningfully
        return 'Neutral', None  # Fallback

    # Normalise features
    scaler = StandardScaler()
    X = scaler.fit_transform(df_clean.values)

    # Fit k-means with k=4 and a fixed random seed for reproducibility
    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    kmeans.fit(X)

    # Map clusters to regime names via stress score of centroids
    centroids = kmeans.cluster_centers_  # shape (4, n_features)
    stress_scores = _centroid_stress_scores(centroids, available)
    # Sort cluster indices by ascending stress → [0=lowest=Bull, 3=highest=Recession]
    sorted_clusters = np.argsort(stress_scores)  # ascending
    regime_labels = ['Bull', 'Neutral', 'Bear', 'Recession Watch']
    cluster_to_regime = {
        sorted_clusters[i]: regime_labels[i]
        for i in range(n_clusters)
    }

    # Classify the most recent data point
    latest_raw = df_feat.iloc[-1:].ffill().bfill().dropna()
    if latest_raw.empty:
        return 'Neutral', None

    latest_scaled = scaler.transform(latest_raw.values)
    predicted_cluster = kmeans.predict(latest_scaled)[0]
    regime = cluster_to_regime[predicted_cluster]

    # Confidence: distance from assigned centroid vs. average intra-cluster distance
    centroid_dist = np.linalg.norm(latest_scaled - kmeans.cluster_centers_[predicted_cluster])
    # Approximate typical distance as sqrt of per-cluster inertia / cluster count
    cluster_mask = kmeans.labels_ == predicted_cluster
    cluster_points = X[cluster_mask]
    if len(cluster_points) > 1:
        avg_dist = np.mean(
            np.linalg.norm(cluster_points - kmeans.cluster_centers_[predicted_cluster], axis=1)
        )
    else:
        avg_dist = centroid_dist  # edge case

    if avg_dist > 0:
        ratio = centroid_dist / avg_dist
    else:
        ratio = 1.0

    if ratio <= CONFIDENCE_LOW_THRESHOLD:
        confidence = 'High'
    elif ratio <= CONFIDENCE_HIGH_THRESHOLD:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    return regime, confidence


def _centroid_stress_scores(centroids: np.ndarray, features: list[str]) -> np.ndarray:
    """
    Compute a macro stress score for each k-means centroid.

    Score = HY_norm + (-yield_curve_norm) + NFCI_norm + claims_norm
    Higher score → higher stress → closer to Recession Watch.
    """
    scores = np.zeros(len(centroids))
    feature_weights = {
        'high_yield_spread': +1.5,   # Higher spread = more stress
        'yield_curve_10y2y': -1.5,   # More negative curve = more stress
        'nfci': +1.0,                # Higher NFCI = tighter conditions = stress
        'initial_claims': +1.0,      # More claims = weaker labor = stress
        'fed_funds_rate': +0.5,      # Higher rates = more restrictive (mild weight)
    }
    for i, feature in enumerate(features):
        weight = feature_weights.get(feature, 0.0)
        if weight != 0.0:
            scores += weight * centroids[:, i]
    return scores


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_macro_regime() -> Optional[dict]:
    """
    Return the current macro regime from cache.

    Returns a dict with keys:
        - state: str — one of VALID_REGIMES
        - updated_at: str — ISO 8601 timestamp
        - confidence: str|None — 'High', 'Medium', 'Low', or None
    Or None if no cache exists.
    """
    return _load_cache()


def update_macro_regime() -> Optional[dict]:
    """
    Run regime classification and update the cache.

    Called by run_data_collection() after daily market data is refreshed.
    Returns the new regime dict, or None on failure.
    """
    logger.info('Running macro regime classification...')

    try:
        df = _load_feature_data()

        if df is None or df.empty:
            # No data available — try rule-based with whatever is in cache
            logger.warning('No feature data for regime classification; skipping update.')
            return None

        # Try k-means first; fall back to rule-based if sklearn is unavailable
        try:
            regime_name, confidence = _kmeans_regime(df)
        except ImportError:
            logger.warning('scikit-learn not available; using rule-based regime classification.')
            latest_vals = {}
            for col in _FEATURES:
                if col in df.columns:
                    series = df[col].dropna()
                    if not series.empty:
                        latest_vals[col] = float(series.iloc[-1])
            regime_name = _rule_based_regime(latest_vals)
            confidence = None

        assert regime_name in VALID_REGIMES, f'Invalid regime: {regime_name}'

        regime_dict = {
            'state': regime_name,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'confidence': confidence,
        }
        _save_cache(regime_dict)
        logger.info('Macro regime updated: %s (confidence: %s)', regime_name, confidence)
        return regime_dict

    except Exception as exc:
        logger.error('Regime classification failed: %s', exc, exc_info=True)
        return None


def get_regime_config() -> dict:
    """
    Return the full static config for all regimes.

    Convenience accessor so templates/tests can import a single module.
    """
    from regime_config import (
        CATEGORY_REGIME_CONTEXT,
        REGIME_CATEGORY_RELEVANCE,
        SIGNAL_REGIME_ANNOTATIONS,
    )
    return {
        'REGIME_METADATA': REGIME_METADATA,
        'CATEGORY_REGIME_CONTEXT': CATEGORY_REGIME_CONTEXT,
        'SIGNAL_REGIME_ANNOTATIONS': SIGNAL_REGIME_ANNOTATIONS,
        'REGIME_CATEGORY_RELEVANCE': REGIME_CATEGORY_RELEVANCE,
        'VALID_REGIMES': VALID_REGIMES,
    }
