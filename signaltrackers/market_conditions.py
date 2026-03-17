"""
Market Conditions Engine — four-dimension framework.

Computes the four dimensions used by the Market Conditions Framework:
  1. Global Liquidity (35% of verdict weight)
  2. Growth × Inflation Quadrant (35% of verdict weight)
  3. Risk Regime (20% of verdict weight)
  4. Policy Stance (10% of verdict weight)

Runs alongside the existing regime_detection.py system — no replacement yet.

Reference: docs/MARKET-CONDITIONS-FRAMEWORK.md, Sections 4-5
"""

import json
import os
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class LiquidityResult:
    """Output of the Global Liquidity engine."""
    state: str          # Strongly Expanding / Expanding / Neutral / Contracting / Strongly Contracting
    score: float        # Raw z-score composite
    fed_nl_yoy: Optional[float] = None
    ecb_yoy: Optional[float] = None
    boj_yoy: Optional[float] = None
    m2_yoy: Optional[float] = None
    as_of: Optional[str] = None  # Date string of evaluation


@dataclass
class QuadrantResult:
    """Output of the Growth×Inflation Quadrant engine."""
    quadrant: str          # Goldilocks / Reflation / Stagflation / Deflation Risk
    growth_composite: float
    inflation_composite: float
    raw_quadrant: str      # Before stability filter
    stable: bool           # Whether the stability filter confirms the quadrant
    as_of: Optional[str] = None


@dataclass
class RiskResult:
    """Output of the Risk Regime engine."""
    state: str             # Calm / Normal / Elevated / Stressed
    score: int             # Combined risk score (0-7)
    vix_score: int         # VIX level score (0-3)
    term_structure_score: int   # VIX term structure score (0-2)
    correlation_score: int      # Stock-bond correlation score (0-2)
    vix_level: Optional[float] = None
    vix_ratio: Optional[float] = None
    stock_bond_corr: Optional[float] = None
    as_of: Optional[str] = None


@dataclass
class PolicyResult:
    """Output of the Policy Stance engine."""
    stance: str            # Accommodative / Neutral / Restrictive
    direction: str         # Easing / Paused / Tightening
    taylor_gap: float      # Actual rate - Taylor prescribed rate
    taylor_prescribed: float
    actual_rate: float
    inflation_pct: Optional[float] = None
    output_gap: Optional[float] = None
    as_of: Optional[str] = None


# ---------------------------------------------------------------------------
# CSV loading helpers
# ---------------------------------------------------------------------------

def _load_csv(filename: str) -> Optional[pd.DataFrame]:
    """Load a CSV from the data directory, returning None if missing/empty."""
    path = os.path.join(DATA_DIR, f'{filename}.csv')
    if not os.path.exists(path):
        logger.warning('Data file not found: %s', path)
        return None
    try:
        df = pd.read_csv(path, parse_dates=['date'])
        if df.empty:
            return None
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception:
        logger.exception('Error loading %s', path)
        return None


def _to_series(df: Optional[pd.DataFrame], col: str) -> Optional[pd.Series]:
    """Extract a date-indexed numeric Series from a DataFrame."""
    if df is None or col not in df.columns:
        return None
    s = df.set_index('date')[col].dropna()
    if s.empty:
        return None
    return s


def _align_weekly(daily_series: pd.Series, weekly_index: pd.DatetimeIndex) -> pd.Series:
    """Forward-fill a daily series onto a weekly date index (no lookahead)."""
    combined = daily_series.reindex(daily_series.index.union(weekly_index))
    combined = combined.sort_index().ffill()
    return combined.reindex(weekly_index)


def _align_monthly(higher_freq: pd.Series, monthly_index: pd.DatetimeIndex) -> pd.Series:
    """Forward-fill a higher-frequency series onto a monthly date index."""
    combined = higher_freq.reindex(higher_freq.index.union(monthly_index))
    combined = combined.sort_index().ffill()
    return combined.reindex(monthly_index)


# ---------------------------------------------------------------------------
# Z-score helpers
# ---------------------------------------------------------------------------

def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    """Compute rolling z-score with a given window size."""
    roll_mean = series.rolling(window, min_periods=max(window // 2, 1)).mean()
    roll_std = series.rolling(window, min_periods=max(window // 2, 1)).std()
    # Avoid division by zero
    roll_std = roll_std.replace(0, np.nan)
    return (series - roll_mean) / roll_std


# ---------------------------------------------------------------------------
# Layer 1: Global Liquidity
# ---------------------------------------------------------------------------

def _compute_fed_net_liquidity() -> Optional[pd.Series]:
    """
    Fed Net Liquidity = WALCL - WDTGAL - (RRPONTSYD × 1000)

    WALCL and WDTGAL are in millions USD.
    RRPONTSYD is in billions USD — multiply by 1000 to align.
    """
    walcl_df = _load_csv('fed_balance_sheet')
    wdtgal_df = _load_csv('treasury_general_account')
    rrp_df = _load_csv('reverse_repo')

    walcl = _to_series(walcl_df, 'fed_balance_sheet')
    wdtgal = _to_series(wdtgal_df, 'treasury_general_account')
    rrp = _to_series(rrp_df, 'reverse_repo')

    if walcl is None or wdtgal is None or rrp is None:
        logger.warning('Missing data for Fed Net Liquidity calculation')
        return None

    # Align all to WALCL's weekly Wednesday index (the binding frequency)
    idx = walcl.index
    wdtgal_aligned = _align_weekly(wdtgal, idx)
    rrp_aligned = _align_weekly(rrp, idx)

    fed_nl = walcl - wdtgal_aligned - (rrp_aligned * 1000)
    return fed_nl.dropna()


def _compute_ecb_usd() -> Optional[pd.Series]:
    """ECB balance sheet in USD millions = ECBASSETSW × DEXUSEU."""
    ecb_df = _load_csv('ecb_total_assets')
    fx_df = _load_csv('fx_eur_usd')

    ecb = _to_series(ecb_df, 'ecb_total_assets')
    fx = _to_series(fx_df, 'fx_eur_usd')

    if ecb is None or fx is None:
        return None

    fx_aligned = _align_weekly(fx, ecb.index)
    return (ecb * fx_aligned).dropna()


def _compute_boj_usd() -> Optional[pd.Series]:
    """BOJ balance sheet in USD = (JPNASSETS × 100_000_000) / DEXJPUS."""
    boj_df = _load_csv('boj_total_assets')
    fx_df = _load_csv('fx_jpy_usd')

    boj = _to_series(boj_df, 'boj_total_assets')
    fx = _to_series(fx_df, 'fx_jpy_usd')

    if boj is None or fx is None:
        return None

    fx_aligned = _align_monthly(fx, boj.index)
    # JPNASSETS is in 100M JPY; DEXJPUS is JPY per USD
    boj_usd = (boj * 100_000_000) / fx_aligned
    return boj_usd.dropna()


def _yoy_change(series: pd.Series, periods: int) -> pd.Series:
    """Compute YoY rate of change: (current / prior) - 1."""
    return series / series.shift(periods) - 1


def _classify_liquidity(score: float) -> str:
    """Map liquidity z-score composite to classification label."""
    if score > 1.0:
        return 'Strongly Expanding'
    elif score > 0.5:
        return 'Expanding'
    elif score >= -0.5:
        return 'Neutral'
    elif score >= -1.0:
        return 'Contracting'
    else:
        return 'Strongly Contracting'


def compute_liquidity(as_of_date: Optional[str] = None) -> Optional[LiquidityResult]:
    """
    Compute the Global Liquidity dimension.

    Steps:
      1. Fed Net Liquidity (weekly) — YoY → z-score (260-week window)
      2. ECB USD (weekly) — YoY → z-score (260-week window)
      3. BOJ USD (monthly) — YoY → z-score (60-month window)
      4. US M2 (monthly) — YoY → z-score (60-month window)
      5. Weighted composite: Fed 40%, ECB 20%, BOJ 15%, M2 25%
      6. Classify: Strongly Expanding / Expanding / Neutral / Contracting / Strongly Contracting

    Args:
        as_of_date: Optional date string (YYYY-MM-DD). If None, uses latest available.

    Returns:
        LiquidityResult or None if insufficient data.
    """
    # --- Fed Net Liquidity (weekly) ---
    fed_nl = _compute_fed_net_liquidity()
    if fed_nl is None or len(fed_nl) < 53:
        logger.warning('Insufficient Fed Net Liquidity data')
        return None

    fed_nl_yoy = _yoy_change(fed_nl, 52)  # 52 weeks
    fed_z = _rolling_zscore(fed_nl_yoy, 260)  # 5 years of weeks

    # --- ECB in USD (weekly) ---
    ecb_usd = _compute_ecb_usd()
    ecb_z = None
    if ecb_usd is not None and len(ecb_usd) >= 53:
        ecb_yoy = _yoy_change(ecb_usd, 52)
        ecb_z = _rolling_zscore(ecb_yoy, 260)

    # --- BOJ in USD (monthly) ---
    boj_usd = _compute_boj_usd()
    boj_z = None
    if boj_usd is not None and len(boj_usd) >= 13:
        boj_yoy = _yoy_change(boj_usd, 12)
        boj_z = _rolling_zscore(boj_yoy, 60)

    # --- US M2 (monthly) ---
    m2_df = _load_csv('m2_money_supply')
    m2 = _to_series(m2_df, 'm2_money_supply')
    m2_z = None
    if m2 is not None and len(m2) >= 13:
        m2_yoy = _yoy_change(m2, 12)
        m2_z = _rolling_zscore(m2_yoy, 60)

    # --- Align everything to weekly Fed index and compute composite ---
    # Fed z-score is the anchor; align monthly series via forward-fill
    idx = fed_z.dropna().index
    if len(idx) == 0:
        return None

    # Determine as_of cutoff
    if as_of_date is not None:
        cutoff = pd.Timestamp(as_of_date)
        idx = idx[idx <= cutoff]
        if len(idx) == 0:
            return None

    # Build composite with available components
    composite = pd.Series(0.0, index=idx)
    total_weight = 0.0

    # Fed (40%)
    fed_aligned = fed_z.reindex(idx)
    mask = fed_aligned.notna()
    composite[mask] += 0.40 * fed_aligned[mask]
    total_weight_series = pd.Series(0.0, index=idx)
    total_weight_series[mask] += 0.40

    # ECB (20%)
    if ecb_z is not None:
        ecb_aligned = _align_weekly(ecb_z, idx)
        ecb_mask = ecb_aligned.notna()
        composite[ecb_mask] += 0.20 * ecb_aligned[ecb_mask]
        total_weight_series[ecb_mask] += 0.20

    # BOJ (15%)
    if boj_z is not None:
        boj_aligned = _align_weekly(boj_z, idx)
        boj_mask = boj_aligned.notna()
        composite[boj_mask] += 0.15 * boj_aligned[boj_mask]
        total_weight_series[boj_mask] += 0.15

    # M2 (25%)
    if m2_z is not None:
        m2_aligned = _align_weekly(m2_z, idx)
        m2_mask = m2_aligned.notna()
        composite[m2_mask] += 0.25 * m2_aligned[m2_mask]
        total_weight_series[m2_mask] += 0.25

    # Renormalize by actual weight available (handle missing components)
    total_weight_series = total_weight_series.replace(0, np.nan)
    composite = composite / total_weight_series

    # Get the evaluation point
    valid = composite.dropna()
    if len(valid) == 0:
        return None

    latest = valid.iloc[-1]
    eval_date = str(valid.index[-1].date())

    # Get component YoY values at evaluation date
    def _latest_val(s, idx_val):
        if s is None:
            return None
        aligned = s.reindex(s.index.union(pd.DatetimeIndex([idx_val]))).sort_index().ffill()
        val = aligned.get(idx_val)
        return float(val) if val is not None and not np.isnan(val) else None

    eval_ts = valid.index[-1]

    return LiquidityResult(
        state=_classify_liquidity(latest),
        score=float(latest),
        fed_nl_yoy=_latest_val(fed_nl_yoy, eval_ts),
        ecb_yoy=_latest_val(_yoy_change(ecb_usd, 52) if ecb_usd is not None else None, eval_ts),
        boj_yoy=_latest_val(_yoy_change(boj_usd, 12) if boj_usd is not None else None, eval_ts),
        m2_yoy=_latest_val(_yoy_change(m2, 12) if m2 is not None else None, eval_ts),
        as_of=eval_date,
    )


# ---------------------------------------------------------------------------
# Layer 2: Growth × Inflation Quadrant
# ---------------------------------------------------------------------------

def _compute_acceleration(series: pd.Series, period: int) -> pd.Series:
    """
    Compute acceleration: change in YoY rate of change.

    acceleration(t) = yoy(t) - yoy(t-1)

    This is the Hedgeye "second derivative" approach — detects inflection
    points earlier than level-based classification.
    """
    yoy_current = series / series.shift(period) - 1
    yoy_prior = series.shift(1) / series.shift(period + 1) - 1
    return yoy_current - yoy_prior


def _load_growth_signals() -> dict[str, Optional[pd.Series]]:
    """Load and compute z-scored acceleration for each growth indicator."""
    signals = {}

    # Initial Claims (ICSA) — weekly, INVERTED (falling = growth)
    icsa_df = _load_csv('initial_claims')
    icsa = _to_series(icsa_df, 'initial_claims')
    if icsa is not None and len(icsa) >= 54:
        accel = _compute_acceleration(icsa, 52)
        z = _rolling_zscore(accel, 260)
        signals['ICSA'] = -1 * z  # Inverted
    else:
        signals['ICSA'] = None

    # Yield Curve 10Y-2Y (T10Y2Y) — daily, direct
    # For spread data, use level change over 12 months (not acceleration of ratio)
    yc_df = _load_csv('yield_curve_10y2y')
    yc = _to_series(yc_df, 'yield_curve_10y2y')
    if yc is not None and len(yc) >= 253:
        level_change = yc.diff(252)  # ~12 months of trading days
        z = _rolling_zscore(level_change, 1260)  # 5 years of trading days
        signals['T10Y2Y'] = z
    else:
        signals['T10Y2Y'] = None

    # NFCI — weekly, INVERTED (falling NFCI = looser conditions = growth)
    nfci_df = _load_csv('nfci')
    nfci = _to_series(nfci_df, 'nfci')
    if nfci is not None and len(nfci) >= 54:
        accel = _compute_acceleration(nfci, 52)
        z = _rolling_zscore(accel, 260)
        signals['NFCI'] = -1 * z  # Inverted
    else:
        signals['NFCI'] = None

    # Industrial Production (INDPRO) — monthly, direct
    indpro_df = _load_csv('industrial_production')
    indpro = _to_series(indpro_df, 'industrial_production')
    if indpro is not None and len(indpro) >= 14:
        accel = _compute_acceleration(indpro, 12)
        z = _rolling_zscore(accel, 60)
        signals['INDPRO'] = z
    else:
        signals['INDPRO'] = None

    # Building Permits (PERMIT) — monthly, direct
    permit_df = _load_csv('building_permits')
    permit = _to_series(permit_df, 'building_permits')
    if permit is not None and len(permit) >= 14:
        accel = _compute_acceleration(permit, 12)
        z = _rolling_zscore(accel, 60)
        signals['PERMIT'] = z
    else:
        signals['PERMIT'] = None

    return signals


def _load_inflation_signals() -> dict[str, Optional[pd.Series]]:
    """Load and compute z-scored acceleration for each inflation indicator."""
    signals = {}

    # 10Y Breakeven (T10YIE) — daily, level change
    t10yie_df = _load_csv('breakeven_inflation_10y')
    t10yie = _to_series(t10yie_df, 'breakeven_inflation_10y')
    if t10yie is not None and len(t10yie) >= 253:
        level_change = t10yie.diff(252)
        z = _rolling_zscore(level_change, 1260)
        signals['T10YIE'] = z
    else:
        signals['T10YIE'] = None

    # 5Y Breakeven (T5YIE) — daily, level change
    t5yie_df = _load_csv('breakeven_inflation_5y')
    t5yie = _to_series(t5yie_df, 'breakeven_inflation_5y')
    if t5yie is not None and len(t5yie) >= 253:
        level_change = t5yie.diff(252)
        z = _rolling_zscore(level_change, 1260)
        signals['T5YIE'] = z
    else:
        signals['T5YIE'] = None

    # CPI (CPIAUCSL) — monthly, acceleration
    cpi_df = _load_csv('cpi')
    cpi = _to_series(cpi_df, 'cpi')
    if cpi is not None and len(cpi) >= 14:
        accel = _compute_acceleration(cpi, 12)
        z = _rolling_zscore(accel, 60)
        signals['CPIAUCSL'] = z
    else:
        signals['CPIAUCSL'] = None

    # Core PCE (PCEPILFE) — monthly, acceleration
    pce_df = _load_csv('core_pce_price_index')
    pce = _to_series(pce_df, 'core_pce_price_index')
    if pce is not None and len(pce) >= 14:
        accel = _compute_acceleration(pce, 12)
        z = _rolling_zscore(accel, 60)
        signals['PCEPILFE'] = z
    else:
        signals['PCEPILFE'] = None

    return signals


def _compute_monthly_composite(signals: dict[str, Optional[pd.Series]]) -> Optional[pd.Series]:
    """
    Compute equal-weight composite from mixed-frequency z-scored signals.

    Aligns all signals to a common monthly index via forward-fill.
    At each date, averages only the available (non-NaN) signals.
    """
    available = {k: v for k, v in signals.items() if v is not None and len(v) > 0}
    if not available:
        return None

    # Build a common monthly date range
    all_dates = set()
    for s in available.values():
        all_dates.update(s.index)

    if not all_dates:
        return None

    # Use a monthly frequency index spanning the full range
    min_date = min(all_dates)
    max_date = max(all_dates)

    # Resample all signals to monthly (end of month), forward-filling higher freq
    monthly_signals = {}
    for name, s in available.items():
        # Resample to month-end, taking the last available observation
        monthly = s.resample('ME').last()
        monthly_signals[name] = monthly

    # Combine into DataFrame and compute row-wise mean (ignoring NaN)
    combined = pd.DataFrame(monthly_signals)
    composite = combined.mean(axis=1)
    return composite.dropna()


def _apply_stability_filter(
    quadrant_series: pd.Series,
    required_consecutive: int = 2,
) -> pd.Series:
    """
    Apply quadrant stability filter: require N consecutive months in the
    same quadrant before recognizing a transition.

    Returns a Series of the same length with filtered quadrant labels.
    """
    if len(quadrant_series) == 0:
        return quadrant_series

    result = []
    current_stable = quadrant_series.iloc[0]
    consecutive_count = 1

    for i, q in enumerate(quadrant_series):
        if i == 0:
            result.append(current_stable)
            continue

        if q == current_stable:
            consecutive_count += 1
            result.append(current_stable)
        else:
            # New quadrant detected
            if consecutive_count == 0:
                # Already in transition
                if q == result[-1]:
                    # Same as last provisional — don't count
                    consecutive_count += 1
                else:
                    consecutive_count = 1
            else:
                consecutive_count = 1

            # Check if we've hit the threshold
            # Count backwards from current position
            count = 1
            for j in range(i - 1, max(i - required_consecutive, -1), -1):
                if quadrant_series.iloc[j] == q:
                    count += 1
                else:
                    break

            if count >= required_consecutive:
                current_stable = q
                consecutive_count = count

            result.append(current_stable)

    return pd.Series(result, index=quadrant_series.index)


def _classify_quadrant(growth: float, inflation: float) -> str:
    """Classify into one of four quadrants based on growth and inflation composites."""
    if growth > 0 and inflation <= 0:
        return 'Goldilocks'
    elif growth > 0 and inflation > 0:
        return 'Reflation'
    elif growth <= 0 and inflation > 0:
        return 'Stagflation'
    else:
        return 'Deflation Risk'


def compute_quadrant(as_of_date: Optional[str] = None) -> Optional[QuadrantResult]:
    """
    Compute the Growth × Inflation Quadrant dimension.

    Steps:
      1. Compute acceleration-based z-scores for 5 growth indicators
      2. Compute acceleration-based z-scores for 4 inflation indicators
      3. Equal-weight composites for growth and inflation
      4. Classify into quadrant
      5. Apply stability filter (2+ consecutive months)

    Args:
        as_of_date: Optional date string (YYYY-MM-DD). If None, uses latest.

    Returns:
        QuadrantResult or None if insufficient data.
    """
    growth_signals = _load_growth_signals()
    inflation_signals = _load_inflation_signals()

    growth_composite = _compute_monthly_composite(growth_signals)
    inflation_composite = _compute_monthly_composite(inflation_signals)

    if growth_composite is None or inflation_composite is None:
        logger.warning('Insufficient data for quadrant calculation')
        return None

    # Align growth and inflation to common dates
    common_idx = growth_composite.index.intersection(inflation_composite.index)
    if len(common_idx) == 0:
        return None

    growth_aligned = growth_composite.reindex(common_idx)
    inflation_aligned = inflation_composite.reindex(common_idx)

    # Classify each month into a raw quadrant
    raw_quadrants = pd.Series(
        [_classify_quadrant(g, i) for g, i in zip(growth_aligned, inflation_aligned)],
        index=common_idx,
    )

    # Apply stability filter
    stable_quadrants = _apply_stability_filter(raw_quadrants, required_consecutive=2)

    # Determine as_of cutoff
    if as_of_date is not None:
        cutoff = pd.Timestamp(as_of_date)
        mask = common_idx <= cutoff
        if not mask.any():
            return None
        common_idx = common_idx[mask]
        growth_aligned = growth_aligned.reindex(common_idx)
        inflation_aligned = inflation_aligned.reindex(common_idx)
        raw_quadrants = raw_quadrants.reindex(common_idx)
        stable_quadrants = stable_quadrants.reindex(common_idx)

    if len(common_idx) == 0:
        return None

    latest_idx = common_idx[-1]
    g_val = float(growth_aligned.iloc[-1])
    i_val = float(inflation_aligned.iloc[-1])
    raw_q = raw_quadrants.iloc[-1]
    stable_q = stable_quadrants.iloc[-1]

    return QuadrantResult(
        quadrant=stable_q,
        growth_composite=g_val,
        inflation_composite=i_val,
        raw_quadrant=raw_q,
        stable=(raw_q == stable_q),
        as_of=str(latest_idx.date()),
    )


# ---------------------------------------------------------------------------
# Full historical series (for backtesting / spot-checks)
# ---------------------------------------------------------------------------

def compute_liquidity_history(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Compute full liquidity history as a DataFrame.

    Returns DataFrame with columns: date, score, state
    """
    fed_nl = _compute_fed_net_liquidity()
    if fed_nl is None or len(fed_nl) < 53:
        return None

    fed_nl_yoy = _yoy_change(fed_nl, 52)
    fed_z = _rolling_zscore(fed_nl_yoy, 260)

    ecb_usd = _compute_ecb_usd()
    ecb_z = None
    if ecb_usd is not None and len(ecb_usd) >= 53:
        ecb_z = _rolling_zscore(_yoy_change(ecb_usd, 52), 260)

    boj_usd = _compute_boj_usd()
    boj_z = None
    if boj_usd is not None and len(boj_usd) >= 13:
        boj_z = _rolling_zscore(_yoy_change(boj_usd, 12), 60)

    m2_df = _load_csv('m2_money_supply')
    m2 = _to_series(m2_df, 'm2_money_supply')
    m2_z = None
    if m2 is not None and len(m2) >= 13:
        m2_z = _rolling_zscore(_yoy_change(m2, 12), 60)

    idx = fed_z.dropna().index
    if len(idx) == 0:
        return None

    if start_date:
        idx = idx[idx >= pd.Timestamp(start_date)]

    composite = pd.Series(0.0, index=idx)
    weights = pd.Series(0.0, index=idx)

    fed_aligned = fed_z.reindex(idx)
    mask = fed_aligned.notna()
    composite[mask] += 0.40 * fed_aligned[mask]
    weights[mask] += 0.40

    if ecb_z is not None:
        ecb_aligned = _align_weekly(ecb_z, idx)
        m = ecb_aligned.notna()
        composite[m] += 0.20 * ecb_aligned[m]
        weights[m] += 0.20

    if boj_z is not None:
        boj_aligned = _align_weekly(boj_z, idx)
        m = boj_aligned.notna()
        composite[m] += 0.15 * boj_aligned[m]
        weights[m] += 0.15

    if m2_z is not None:
        m2_aligned = _align_weekly(m2_z, idx)
        m = m2_aligned.notna()
        composite[m] += 0.25 * m2_aligned[m]
        weights[m] += 0.25

    weights = weights.replace(0, np.nan)
    composite = (composite / weights).dropna()

    result = pd.DataFrame({
        'date': composite.index,
        'score': composite.values,
        'state': [_classify_liquidity(s) for s in composite.values],
    })
    return result


def compute_quadrant_history(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Compute full quadrant history as a DataFrame.

    Returns DataFrame with columns: date, growth, inflation, raw_quadrant, quadrant
    """
    growth_signals = _load_growth_signals()
    inflation_signals = _load_inflation_signals()

    growth_composite = _compute_monthly_composite(growth_signals)
    inflation_composite = _compute_monthly_composite(inflation_signals)

    if growth_composite is None or inflation_composite is None:
        return None

    common_idx = growth_composite.index.intersection(inflation_composite.index)
    if len(common_idx) == 0:
        return None

    if start_date:
        common_idx = common_idx[common_idx >= pd.Timestamp(start_date)]

    growth_aligned = growth_composite.reindex(common_idx)
    inflation_aligned = inflation_composite.reindex(common_idx)

    raw_quadrants = pd.Series(
        [_classify_quadrant(g, i) for g, i in zip(growth_aligned, inflation_aligned)],
        index=common_idx,
    )
    stable_quadrants = _apply_stability_filter(raw_quadrants, required_consecutive=2)

    return pd.DataFrame({
        'date': common_idx,
        'growth': growth_aligned.values,
        'inflation': inflation_aligned.values,
        'raw_quadrant': raw_quadrants.values,
        'quadrant': stable_quadrants.values,
    })


# ---------------------------------------------------------------------------
# Layer 3: Risk Regime
# ---------------------------------------------------------------------------

def _score_vix_level(vix: float) -> int:
    """Map VIX level to score 0-3."""
    if vix < 15:
        return 0
    elif vix < 20:
        return 1
    elif vix < 30:
        return 2
    else:
        return 3


def _score_term_structure(ratio: float) -> int:
    """Map VIX/VIX3M ratio to score 0-2."""
    if ratio < 0.95:
        return 0  # Contango — calm
    elif ratio <= 1.05:
        return 1  # Flat — uncertain
    else:
        return 2  # Backwardation — stressed


def _score_stock_bond_corr(corr: float) -> int:
    """Map 63-day stock-bond rolling correlation to score 0-2."""
    if corr < -0.3:
        return 0  # Diversifying — bonds hedge stocks
    elif corr <= 0.3:
        return 1  # Transitional
    else:
        return 2  # Correlated — 2022-style


def _classify_risk(score: int) -> str:
    """Map combined risk score (0-7) to state label."""
    if score <= 1:
        return 'Calm'
    elif score <= 3:
        return 'Normal'
    elif score <= 5:
        return 'Elevated'
    else:
        return 'Stressed'


def _compute_stock_bond_correlation(window: int = 63) -> Optional[pd.Series]:
    """
    Compute rolling correlation between equity returns and approximate bond returns.

    Bond returns approximated via duration: -8.5 * daily yield change.
    Uses SPY for equity returns and DGS10 for 10Y yield.
    """
    # Load S&P 500 price (SPY from Yahoo)
    sp_df = _load_csv('sp500_price')
    sp = _to_series(sp_df, 'sp500_price')

    # Load 10Y Treasury yield (DGS10)
    t10_df = _load_csv('treasury_10y')
    t10 = _to_series(t10_df, 'treasury_10y')

    if sp is None or t10 is None:
        return None

    # Align to common dates
    common = sp.index.intersection(t10.index)
    if len(common) < window + 1:
        return None

    sp_aligned = sp.reindex(common)
    t10_aligned = t10.reindex(common)

    # Compute returns
    equity_returns = sp_aligned.pct_change()
    # Approximate bond returns: duration ~8.5 years × daily yield change (in decimal)
    bond_returns = -8.5 * t10_aligned.diff() / 100

    # 63-day rolling correlation
    rolling_corr = equity_returns.rolling(window, min_periods=window).corr(bond_returns)
    return rolling_corr.dropna()


def compute_risk(as_of_date: Optional[str] = None) -> Optional[RiskResult]:
    """
    Compute the Risk Regime dimension.

    Uses three sub-scores:
      1. VIX level (0-3)
      2. VIX term structure: VIX/VIX3M ratio (0-2)
      3. Stock-bond correlation: 63-day rolling (0-2)

    Combined score (0-7) → Calm / Normal / Elevated / Stressed

    Graceful degradation: if VIX3M unavailable, uses VIX level + correlation only.

    Args:
        as_of_date: Optional date string (YYYY-MM-DD). If None, uses latest.

    Returns:
        RiskResult or None if insufficient data.
    """
    # --- VIX level ---
    # Use Yahoo VIX data (vix_price.csv) — longer history than FRED VIXCLS
    vix_df = _load_csv('vix_price')
    vix_series = _to_series(vix_df, 'vix_price')

    if vix_series is None or len(vix_series) == 0:
        logger.warning('No VIX data available for risk calculation')
        return None

    # --- VIX 3-month (VIX3M / VXVCLS) for term structure ---
    vix3m_df = _load_csv('vix_3month')
    vix3m_series = _to_series(vix3m_df, 'vix_3month')

    # --- Stock-bond correlation ---
    corr_series = _compute_stock_bond_correlation(63)

    # Determine evaluation date
    if as_of_date is not None:
        cutoff = pd.Timestamp(as_of_date)
        vix_series = vix_series[vix_series.index <= cutoff]
        if vix3m_series is not None:
            vix3m_series = vix3m_series[vix3m_series.index <= cutoff]
        if corr_series is not None:
            corr_series = corr_series[corr_series.index <= cutoff]

    if len(vix_series) == 0:
        return None

    # Get latest VIX
    vix_val = float(vix_series.iloc[-1])
    eval_date = vix_series.index[-1]
    v_score = _score_vix_level(vix_val)

    # Term structure score
    ts_score = 0
    vix_ratio_val = None
    if vix3m_series is not None and len(vix3m_series) > 0:
        # Align VIX3M to VIX date
        vix3m_at_date = vix3m_series.reindex(
            vix3m_series.index.union(pd.DatetimeIndex([eval_date]))
        ).sort_index().ffill()
        vix3m_val = vix3m_at_date.get(eval_date)
        if vix3m_val is not None and not np.isnan(vix3m_val) and vix3m_val > 0:
            vix_ratio_val = vix_val / vix3m_val
            ts_score = _score_term_structure(vix_ratio_val)

    # Correlation score
    corr_score = 0
    corr_val = None
    if corr_series is not None and len(corr_series) > 0:
        # Get latest correlation at or before eval_date
        corr_at_date = corr_series.reindex(
            corr_series.index.union(pd.DatetimeIndex([eval_date]))
        ).sort_index().ffill()
        c = corr_at_date.get(eval_date)
        if c is not None and not np.isnan(c):
            corr_val = float(c)
            corr_score = _score_stock_bond_corr(corr_val)

    # Combined score
    combined = v_score + ts_score + corr_score

    return RiskResult(
        state=_classify_risk(combined),
        score=combined,
        vix_score=v_score,
        term_structure_score=ts_score,
        correlation_score=corr_score,
        vix_level=vix_val,
        vix_ratio=float(vix_ratio_val) if vix_ratio_val is not None else None,
        stock_bond_corr=corr_val,
        as_of=str(eval_date.date()),
    )


# ---------------------------------------------------------------------------
# Layer 4: Policy Stance
# ---------------------------------------------------------------------------

def _load_policy_rate() -> Optional[pd.Series]:
    """
    Load the effective policy rate.

    Uses DFEDTARU (Fed Funds Upper Target, daily) as primary source.
    Falls back to FEDFUNDS (effective rate, monthly) for pre-2009 periods.
    """
    # Try DFEDTARU first (daily, post-Dec 2008)
    target_df = _load_csv('fed_funds_upper_target')
    target = _to_series(target_df, 'fed_funds_upper_target')

    # FEDFUNDS as fallback (monthly, full history)
    ff_df = _load_csv('fed_funds_rate')
    ff = _to_series(ff_df, 'fed_funds_rate')

    if target is not None and ff is not None:
        # Combine: use FEDFUNDS before DFEDTARU starts, then DFEDTARU
        target_start = target.index.min()
        ff_before = ff[ff.index < target_start]
        # Forward-fill monthly FEDFUNDS to daily for alignment
        combined = pd.concat([ff_before, target]).sort_index()
        return combined
    elif target is not None:
        return target
    elif ff is not None:
        return ff
    else:
        return None


def _compute_taylor_rule(
    inflation_pct: pd.Series,
    output_gap: pd.Series,
) -> pd.Series:
    """
    Compute Taylor Rule prescribed rate.

    i = 1.0 + 1.5 * π + 0.5 * output_gap

    Where r* = 2%, π* = 2% (simplified Taylor 1993).
    """
    return 1.0 + 1.5 * inflation_pct + 0.5 * output_gap


def _classify_policy_stance(taylor_gap: float) -> str:
    """Classify Taylor gap into policy stance."""
    if taylor_gap > 1.0:
        return 'Restrictive'
    elif taylor_gap >= -0.5:
        return 'Neutral'
    else:
        return 'Accommodative'


def _classify_policy_direction(rate_change_3m: float) -> str:
    """Classify 3-month fed funds change into direction."""
    if rate_change_3m > 0.25:
        return 'Tightening'
    elif rate_change_3m < -0.25:
        return 'Easing'
    else:
        return 'Paused'


def compute_policy(as_of_date: Optional[str] = None) -> Optional[PolicyResult]:
    """
    Compute the Policy Stance dimension.

    Steps:
      1. Compute YoY Core PCE inflation (%)
      2. Compute output gap via Okun's Law: -2 × (UNRATE - NROU)
      3. Taylor Rule prescribed rate: i = 1.0 + 1.5π + 0.5(output_gap)
      4. Taylor gap = actual rate - prescribed rate
      5. Classify stance: Accommodative / Neutral / Restrictive
      6. Direction overlay: Easing / Paused / Tightening (3-month rate change)

    Args:
        as_of_date: Optional date string (YYYY-MM-DD). If None, uses latest.

    Returns:
        PolicyResult or None if insufficient data.
    """
    # --- Core PCE for inflation ---
    pce_df = _load_csv('core_pce_price_index')
    pce = _to_series(pce_df, 'core_pce_price_index')
    if pce is None or len(pce) < 13:
        logger.warning('Insufficient Core PCE data for policy calculation')
        return None

    # YoY inflation as percentage
    inflation_pct = ((pce / pce.shift(12)) - 1) * 100

    # --- Output gap via Okun's Law ---
    unrate_df = _load_csv('unemployment_rate')
    unrate = _to_series(unrate_df, 'unemployment_rate')

    nrou_df = _load_csv('natural_unemployment_rate')
    nrou = _to_series(nrou_df, 'natural_unemployment_rate')

    if unrate is None or nrou is None:
        logger.warning('Insufficient unemployment data for policy calculation')
        return None

    # NROU is quarterly — forward-fill to monthly to align with UNRATE
    nrou_monthly = nrou.resample('MS').ffill()
    # Align to UNRATE index
    common_idx = unrate.index.intersection(nrou_monthly.index)
    if len(common_idx) == 0:
        # Try forward-filling onto unrate's index
        nrou_aligned = _align_monthly(nrou_monthly, unrate.index)
        common_idx = unrate.index[nrou_aligned.notna()]
        if len(common_idx) == 0:
            return None
        unrate_aligned = unrate.reindex(common_idx)
        nrou_aligned = nrou_aligned.reindex(common_idx)
    else:
        unrate_aligned = unrate.reindex(common_idx)
        nrou_aligned = nrou_monthly.reindex(common_idx)

    output_gap = -2 * (unrate_aligned - nrou_aligned)

    # --- Align inflation and output gap ---
    inf_common = inflation_pct.dropna().index.intersection(output_gap.dropna().index)
    if len(inf_common) == 0:
        return None

    inflation_aligned = inflation_pct.reindex(inf_common)
    output_gap_aligned = output_gap.reindex(inf_common)

    # --- Taylor Rule ---
    taylor_prescribed = _compute_taylor_rule(inflation_aligned, output_gap_aligned)

    # --- Policy rate ---
    policy_rate = _load_policy_rate()
    if policy_rate is None:
        logger.warning('No policy rate data available')
        return None

    # Align policy rate to the monthly evaluation dates
    rate_aligned = _align_monthly(policy_rate, inf_common)

    # Apply as_of cutoff
    if as_of_date is not None:
        cutoff = pd.Timestamp(as_of_date)
        mask = inf_common <= cutoff
        if not mask.any():
            return None
        inf_common = inf_common[mask]
        inflation_aligned = inflation_aligned.reindex(inf_common)
        output_gap_aligned = output_gap_aligned.reindex(inf_common)
        taylor_prescribed = taylor_prescribed.reindex(inf_common)
        rate_aligned = rate_aligned.reindex(inf_common)

    # Find latest date where all components are available
    valid_mask = (
        inflation_aligned.notna()
        & output_gap_aligned.notna()
        & taylor_prescribed.notna()
        & rate_aligned.notna()
    )
    valid_dates = inf_common[valid_mask]
    if len(valid_dates) == 0:
        return None

    eval_date = valid_dates[-1]
    actual_rate = float(rate_aligned.loc[eval_date])
    prescribed = float(taylor_prescribed.loc[eval_date])
    gap = actual_rate - prescribed
    inf_val = float(inflation_aligned.loc[eval_date])
    og_val = float(output_gap_aligned.loc[eval_date])

    # --- Direction overlay (3-month rate change) ---
    # For monthly data, shift(3) = 3 months; for daily, shift(63) ≈ 3 months
    # Use the policy rate series directly for direction calculation
    if as_of_date is not None:
        rate_for_dir = policy_rate[policy_rate.index <= pd.Timestamp(as_of_date)]
    else:
        rate_for_dir = policy_rate

    if rate_for_dir is not None and len(rate_for_dir) > 63:
        latest_rate = float(rate_for_dir.iloc[-1])
        prior_rate = float(rate_for_dir.iloc[-64])  # ~3 months ago
        rate_change_3m = latest_rate - prior_rate
    elif rate_for_dir is not None and len(rate_for_dir) > 3:
        # Monthly fallback
        latest_rate = float(rate_for_dir.iloc[-1])
        prior_rate = float(rate_for_dir.iloc[-4])  # 3 months ago
        rate_change_3m = latest_rate - prior_rate
    else:
        rate_change_3m = 0.0

    direction = _classify_policy_direction(rate_change_3m)

    return PolicyResult(
        stance=_classify_policy_stance(gap),
        direction=direction,
        taylor_gap=gap,
        taylor_prescribed=prescribed,
        actual_rate=actual_rate,
        inflation_pct=inf_val,
        output_gap=og_val,
        as_of=str(eval_date.date()),
    )


# ---------------------------------------------------------------------------
# Risk history (for backtesting / spot-checks)
# ---------------------------------------------------------------------------

def compute_risk_history(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Compute full risk history as a DataFrame.

    Returns DataFrame with columns: date, vix_score, term_structure_score,
    correlation_score, score, state
    """
    # VIX level series
    vix_df = _load_csv('vix_price')
    vix_series = _to_series(vix_df, 'vix_price')
    if vix_series is None or len(vix_series) == 0:
        return None

    # VIX 3-month for term structure
    vix3m_df = _load_csv('vix_3month')
    vix3m_series = _to_series(vix3m_df, 'vix_3month')

    # Stock-bond correlation
    corr_series = _compute_stock_bond_correlation(63)

    # Build on VIX date index
    idx = vix_series.index
    if start_date:
        idx = idx[idx >= pd.Timestamp(start_date)]

    records = []
    for dt in idx:
        vix_val = float(vix_series.loc[dt])
        v_score = _score_vix_level(vix_val)

        # Term structure
        ts_score = 0
        if vix3m_series is not None and len(vix3m_series) > 0:
            v3m = vix3m_series.reindex(
                vix3m_series.index.union(pd.DatetimeIndex([dt]))
            ).sort_index().ffill()
            v3m_val = v3m.get(dt)
            if v3m_val is not None and not np.isnan(v3m_val) and v3m_val > 0:
                ts_score = _score_term_structure(vix_val / v3m_val)

        # Correlation
        c_score = 0
        if corr_series is not None and len(corr_series) > 0:
            c = corr_series.reindex(
                corr_series.index.union(pd.DatetimeIndex([dt]))
            ).sort_index().ffill()
            c_val = c.get(dt)
            if c_val is not None and not np.isnan(c_val):
                c_score = _score_stock_bond_corr(float(c_val))

        combined = v_score + ts_score + c_score
        records.append({
            'date': dt,
            'vix_score': v_score,
            'term_structure_score': ts_score,
            'correlation_score': c_score,
            'score': combined,
            'state': _classify_risk(combined),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Policy history (for backtesting / spot-checks)
# ---------------------------------------------------------------------------

def compute_policy_history(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Compute full policy history as a DataFrame.

    Returns DataFrame with columns: date, actual_rate, taylor_prescribed,
    taylor_gap, stance, direction
    """
    pce_df = _load_csv('core_pce_price_index')
    pce = _to_series(pce_df, 'core_pce_price_index')
    if pce is None or len(pce) < 13:
        return None

    inflation_pct = ((pce / pce.shift(12)) - 1) * 100

    unrate_df = _load_csv('unemployment_rate')
    unrate = _to_series(unrate_df, 'unemployment_rate')
    nrou_df = _load_csv('natural_unemployment_rate')
    nrou = _to_series(nrou_df, 'natural_unemployment_rate')

    if unrate is None or nrou is None:
        return None

    nrou_monthly = nrou.resample('MS').ffill()
    common_idx = unrate.index.intersection(nrou_monthly.index)
    if len(common_idx) == 0:
        nrou_aligned = _align_monthly(nrou_monthly, unrate.index)
        common_idx = unrate.index[nrou_aligned.notna()]
        if len(common_idx) == 0:
            return None
        unrate_aligned = unrate.reindex(common_idx)
        nrou_aligned = nrou_aligned.reindex(common_idx)
    else:
        unrate_aligned = unrate.reindex(common_idx)
        nrou_aligned = nrou_monthly.reindex(common_idx)

    output_gap = -2 * (unrate_aligned - nrou_aligned)

    inf_common = inflation_pct.dropna().index.intersection(output_gap.dropna().index)
    if len(inf_common) == 0:
        return None

    inflation_aligned = inflation_pct.reindex(inf_common)
    output_gap_aligned = output_gap.reindex(inf_common)
    taylor_prescribed = _compute_taylor_rule(inflation_aligned, output_gap_aligned)

    policy_rate = _load_policy_rate()
    if policy_rate is None:
        return None

    rate_aligned = _align_monthly(policy_rate, inf_common)

    if start_date:
        mask = inf_common >= pd.Timestamp(start_date)
        inf_common = inf_common[mask]

    records = []
    for dt in inf_common:
        prescribed = taylor_prescribed.get(dt)
        rate = rate_aligned.get(dt)
        if prescribed is None or rate is None or np.isnan(prescribed) or np.isnan(rate):
            continue

        gap = float(rate) - float(prescribed)

        # Direction: check 3-month rate change
        rate_before = policy_rate[policy_rate.index <= dt]
        if len(rate_before) > 63:
            rate_change = float(rate_before.iloc[-1]) - float(rate_before.iloc[-64])
        elif len(rate_before) > 3:
            rate_change = float(rate_before.iloc[-1]) - float(rate_before.iloc[-4])
        else:
            rate_change = 0.0

        records.append({
            'date': dt,
            'actual_rate': float(rate),
            'taylor_prescribed': float(prescribed),
            'taylor_gap': gap,
            'stance': _classify_policy_stance(gap),
            'direction': _classify_policy_direction(rate_change),
        })

    return pd.DataFrame(records) if records else None


# ---------------------------------------------------------------------------
# Section 5: Verdict Classifier
# ---------------------------------------------------------------------------

MARKET_CONDITIONS_CACHE_FILE = os.path.join(DATA_DIR, 'market_conditions_cache.json')

# Dimension → numeric score mapping (per framework spec Section 5)

_LIQUIDITY_SCORE_MAP = {
    'Strongly Expanding': 2.0,
    'Expanding': 1.0,
    'Neutral': 0.0,
    'Contracting': -1.0,
    'Strongly Contracting': -2.0,
}

_QUADRANT_SCORE_MAP = {
    'Goldilocks': 2.0,
    'Reflation': 1.0,
    'Deflation Risk': -1.0,
    'Stagflation': -2.0,
}

_RISK_SCORE_MAP = {
    'Calm': 1.0,
    'Normal': 0.0,
    'Elevated': -1.0,
    'Stressed': -2.0,
}

_POLICY_SCORE_MAP = {
    'Accommodative': 1.0,
    'Neutral': 0.0,
    'Restrictive': -1.0,
}

# Weights
_WEIGHT_LIQUIDITY = 0.35
_WEIGHT_QUADRANT = 0.35
_WEIGHT_RISK = 0.20
_WEIGHT_POLICY = 0.10


def _map_dimension_score(state: str, score_map: dict) -> Optional[float]:
    """Map a dimension state label to its numeric score."""
    return score_map.get(state)


def _compute_verdict_score(
    liquidity_mapped: float,
    quadrant_mapped: float,
    risk_mapped: float,
    policy_mapped: float,
) -> float:
    """Weighted composite of four dimension scores."""
    return (
        _WEIGHT_LIQUIDITY * liquidity_mapped
        + _WEIGHT_QUADRANT * quadrant_mapped
        + _WEIGHT_RISK * risk_mapped
        + _WEIGHT_POLICY * policy_mapped
    )


def _classify_verdict(score: float, risk_state: str) -> str:
    """
    Classify verdict from composite score.

    Override: Risk "Stressed" → always "Defensive".
    """
    if risk_state == 'Stressed':
        return 'Defensive'
    if score > 0.75:
        return 'Favorable'
    elif score > -0.25:
        return 'Mixed'
    elif score > -1.0:
        return 'Cautious'
    else:
        return 'Defensive'


# ---------------------------------------------------------------------------
# Section 5: Asset Class Expectations
# ---------------------------------------------------------------------------

# Quadrant → base expectations (direction for S&P 500, Treasuries, Gold)
_QUADRANT_EXPECTATIONS = {
    'Goldilocks': {
        'sp500': 'positive',
        'treasuries': 'positive',
        'gold': 'neutral',
    },
    'Reflation': {
        'sp500': 'positive',
        'treasuries': 'negative',
        'gold': 'positive',
    },
    'Stagflation': {
        'sp500': 'negative',
        'treasuries': 'negative',
        'gold': 'positive',
    },
    'Deflation Risk': {
        'sp500': 'negative',
        'treasuries': 'positive',
        'gold': 'neutral',
    },
}

# Liquidity overlay: modifies magnitude description, not direction
_LIQUIDITY_MAGNITUDE = {
    'Strongly Expanding': 'strong',
    'Expanding': 'moderate',
    'Neutral': 'baseline',
    'Contracting': 'reduced',
    'Strongly Contracting': 'weak',
}

# Risk overlay: modifies conviction
_RISK_CONVICTION = {
    'Calm': 'high',
    'Normal': 'standard',
    'Elevated': 'low',
    'Stressed': 'override',
}


def _build_asset_expectations(
    quadrant: str,
    liquidity_state: str,
    risk_state: str,
) -> List[Dict]:
    """
    Build asset class expectations from current conditions.

    Returns list of dicts with keys: asset, direction, magnitude, conviction.
    When Risk is Stressed, S&P 500 direction overridden to negative.
    """
    base = _QUADRANT_EXPECTATIONS.get(quadrant, _QUADRANT_EXPECTATIONS['Goldilocks'])
    magnitude = _LIQUIDITY_MAGNITUDE.get(liquidity_state, 'baseline')
    conviction = _RISK_CONVICTION.get(risk_state, 'standard')

    expectations = []
    for asset, direction in base.items():
        asset_dir = direction
        asset_mag = magnitude
        asset_conv = conviction

        # Stressed override: equities go negative regardless
        if risk_state == 'Stressed' and asset == 'sp500':
            asset_dir = 'negative'
            asset_conv = 'override'

        # Stressed override: reduce magnitude for all assets
        if risk_state == 'Stressed':
            asset_conv = 'override'
            if asset != 'gold':
                asset_mag = 'weak'

        expectations.append({
            'asset': asset,
            'direction': asset_dir,
            'magnitude': asset_mag,
            'conviction': asset_conv,
        })

    return expectations


# ---------------------------------------------------------------------------
# Verdict dataclass
# ---------------------------------------------------------------------------

@dataclass
class MarketConditionsResult:
    """Full market conditions verdict with all dimensions."""
    verdict: str               # Favorable / Mixed / Cautious / Defensive
    verdict_score: float       # Numeric composite score

    # Dimension states
    liquidity_state: str
    quadrant: str
    risk_state: str
    policy_stance: str
    policy_direction: str

    # Dimension mapped scores (-2 to +2)
    liquidity_mapped: float
    quadrant_mapped: float
    risk_mapped: float
    policy_mapped: float

    # Asset expectations
    asset_expectations: List[Dict]

    # Metadata
    as_of: Optional[str] = None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute_market_conditions(as_of_date: Optional[str] = None) -> Optional[MarketConditionsResult]:
    """
    Compute full market conditions: four dimensions → verdict → asset expectations.

    Returns MarketConditionsResult or None if insufficient data.
    Compatible with backtest interface via .verdict and .verdict_score.
    """
    liquidity = compute_liquidity(as_of_date)
    quadrant = compute_quadrant(as_of_date)
    risk = compute_risk(as_of_date)
    policy = compute_policy(as_of_date)

    # Require at least liquidity and quadrant (the two 35% weights)
    if liquidity is None or quadrant is None:
        logger.warning('Cannot compute verdict: missing liquidity or quadrant data')
        return None

    # Map dimension states to numeric scores
    liq_mapped = _map_dimension_score(liquidity.state, _LIQUIDITY_SCORE_MAP)
    quad_mapped = _map_dimension_score(quadrant.quadrant, _QUADRANT_SCORE_MAP)

    if liq_mapped is None or quad_mapped is None:
        logger.warning('Unknown dimension state: liquidity=%s quadrant=%s',
                        liquidity.state, quadrant.quadrant)
        return None

    # Risk and policy: graceful degradation if unavailable
    if risk is not None:
        risk_mapped = _map_dimension_score(risk.state, _RISK_SCORE_MAP)
        risk_state = risk.state
    else:
        risk_mapped = 0.0  # Neutral assumption
        risk_state = 'Normal'
        logger.info('Risk data unavailable; defaulting to Normal (0.0)')

    if policy is not None:
        pol_mapped = _map_dimension_score(policy.stance, _POLICY_SCORE_MAP)
        policy_stance = policy.stance
        policy_direction = policy.direction
    else:
        pol_mapped = 0.0  # Neutral assumption
        policy_stance = 'Neutral'
        policy_direction = 'Paused'
        logger.info('Policy data unavailable; defaulting to Neutral (0.0)')

    if risk_mapped is None:
        risk_mapped = 0.0
    if pol_mapped is None:
        pol_mapped = 0.0

    # Compute weighted composite
    v_score = _compute_verdict_score(liq_mapped, quad_mapped, risk_mapped, pol_mapped)

    # Classify verdict (with Stressed override)
    verdict = _classify_verdict(v_score, risk_state)

    # Build asset expectations
    expectations = _build_asset_expectations(
        quadrant.quadrant, liquidity.state, risk_state
    )

    # Determine as_of date
    dates = []
    for dim in [liquidity, quadrant, risk, policy]:
        if dim is not None and dim.as_of:
            dates.append(dim.as_of)
    as_of = max(dates) if dates else (as_of_date or None)

    return MarketConditionsResult(
        verdict=verdict,
        verdict_score=round(v_score, 4),
        liquidity_state=liquidity.state,
        quadrant=quadrant.quadrant,
        risk_state=risk_state,
        policy_stance=policy_stance,
        policy_direction=policy_direction,
        liquidity_mapped=liq_mapped,
        quadrant_mapped=quad_mapped,
        risk_mapped=risk_mapped,
        policy_mapped=pol_mapped,
        asset_expectations=expectations,
        as_of=as_of,
    )


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def update_market_conditions_cache() -> Optional[dict]:
    """
    Compute current market conditions and write to cache file.

    Called by run_data_collection() alongside update_macro_regime().
    Returns the cache dict, or None on failure.
    """
    logger.info('Computing market conditions for cache update...')

    try:
        result = compute_market_conditions()
        if result is None:
            logger.warning('Market conditions computation returned None; skipping cache update')
            return None

        cache_data = {
            'verdict': result.verdict,
            'verdict_score': result.verdict_score,
            'dimensions': {
                'liquidity': {
                    'state': result.liquidity_state,
                    'mapped_score': result.liquidity_mapped,
                },
                'quadrant': {
                    'state': result.quadrant,
                    'mapped_score': result.quadrant_mapped,
                },
                'risk': {
                    'state': result.risk_state,
                    'mapped_score': result.risk_mapped,
                },
                'policy': {
                    'stance': result.policy_stance,
                    'direction': result.policy_direction,
                    'mapped_score': result.policy_mapped,
                },
            },
            'asset_expectations': result.asset_expectations,
            'as_of': result.as_of,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }

        os.makedirs(os.path.dirname(MARKET_CONDITIONS_CACHE_FILE), exist_ok=True)
        with open(MARKET_CONDITIONS_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)

        logger.info('Market conditions cache updated: verdict=%s score=%.4f',
                     result.verdict, result.verdict_score)
        return cache_data

    except Exception:
        logger.exception('Error updating market conditions cache')
        return None


def get_market_conditions() -> Optional[dict]:
    """Read market conditions from cache file."""
    if not os.path.exists(MARKET_CONDITIONS_CACHE_FILE):
        return None
    try:
        with open(MARKET_CONDITIONS_CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        logger.exception('Error reading market conditions cache')
        return None
