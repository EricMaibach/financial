"""
Market Conditions Engine — four-dimension framework.

Computes the four dimensions used by the Market Conditions Framework:
  1. Global Liquidity
  2. Growth × Inflation Quadrant (headline classification)
  3. Risk Regime
  4. Policy Stance

The Quadrant is the headline classification — no blended verdict.
Three supporting dimensions (Liquidity, Risk, Policy) provide context.

Reference: docs/MARKET-CONDITIONS-FRAMEWORK.md, Sections 3-5
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
    inflation_breadth: Optional[int] = None        # Count of indicators agreeing on majority direction
    inflation_breadth_total: Optional[int] = None   # Total indicators available
    inflation_components: Optional[dict] = None     # Per-indicator detail: {name: {direction, z_score, raw_value}}
    transition_watch: Optional[dict] = None         # None if confirmed; {direction: str, month: int} if in transition


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


def _expanding_zscore(series: pd.Series, min_periods: int = 12) -> pd.Series:
    """
    Compute expanding z-score against the full available history.

    Used for rate-based inflation series (breakevens, survey expectations)
    where the level itself IS the inflation signal. Z-scoring against the
    full history answers "is this rate high or low relative to historical
    norms?" — appropriate for expectation indicators whose absolute level
    matters more than short-term momentum.
    """
    exp_mean = series.expanding(min_periods=min_periods).mean()
    exp_std = series.expanding(min_periods=min_periods).std()
    exp_std = exp_std.replace(0, np.nan)
    return (series - exp_mean) / exp_std


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

    Retained as a secondary early-warning signal for regime transitions.
    The primary classifier is now YoY direction (see _compute_yoy_direction).
    """
    yoy_current = series / series.shift(period) - 1
    yoy_prior = series.shift(1) / series.shift(period + 1) - 1
    return yoy_current - yoy_prior


def _compute_yoy_direction(series: pd.Series, period: int) -> pd.Series:
    """
    Compute YoY rate direction for index-level series (e.g. CPI, Core PCE).

    Uses percentage change: series / series.shift(period) - 1.
    This converts a price index into a YoY inflation rate — positive means
    inflation is rising year-over-year.

    Only valid for index-level series. For rate-based series (breakevens,
    survey expectations, median CPI), use _compute_rate_momentum instead.
    """
    return series / series.shift(period) - 1


def _compute_rate_momentum(series: pd.Series, period: int) -> pd.Series:
    """
    Compute YoY momentum for rate-based series (e.g. breakevens, Michigan).

    Uses simple difference: series - series.shift(period).
    Rate-based series are already expressed as percentages, so their level
    IS the inflation signal. The difference tells us whether the rate is
    rising or falling — positive means inflation expectations are increasing.

    Using percentage change on rates would give "change in the rate of change"
    (essentially acceleration), which defeats the purpose of using direction
    as the primary classifier.
    """
    return series.diff(period)


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
    """
    Load and compute z-scored inflation signals for each indicator.

    Two signal types based on the nature of each series:

    - **Index-level series** (CPI, Core PCE): Compute YoY rate direction
      (first derivative) and z-score against a 24-month rolling window.
      This measures whether the realized inflation rate is rising or falling
      relative to recent history.

    - **Rate-based series** (Median CPI, breakevens, forwards, Michigan):
      Z-score the raw level against an expanding (full-history) window.
      These series are already expressed as inflation rates/percentages;
      their level IS the inflation signal. The expanding z-score measures
      whether the rate is high or low relative to historical norms —
      appropriate for expectation indicators where an elevated level signals
      inflationary pressure regardless of short-term momentum.

    6 indicators across 3 dimensions:
      Realized Trend: CPI, Core PCE, Median CPI
      Market Expectations: 10Y Breakeven, 5Y5Y Forward
      Consumer Expectations: Michigan 1-Year
    """
    signals = {}

    # --- Realized Trend (monthly) ---

    # CPI (CPIAUCSL) — price index, YoY direction z-scored over 24 months
    cpi_df = _load_csv('cpi')
    cpi = _to_series(cpi_df, 'cpi')
    if cpi is not None and len(cpi) >= 13:
        yoy = _compute_yoy_direction(cpi, 12)
        z = _rolling_zscore(yoy, 24)
        signals['CPIAUCSL'] = z
    else:
        signals['CPIAUCSL'] = None

    # Core PCE (PCEPILFE) — price index, YoY direction z-scored over 24 months
    pce_df = _load_csv('core_pce_price_index')
    pce = _to_series(pce_df, 'core_pce_price_index')
    if pce is not None and len(pce) >= 13:
        yoy = _compute_yoy_direction(pce, 12)
        z = _rolling_zscore(yoy, 24)
        signals['PCEPILFE'] = z
    else:
        signals['PCEPILFE'] = None

    # Cleveland Fed Median CPI (MEDCPIM158SFRBCLE) — rate-based (YoY %)
    # Level z-scored against full history: "is this inflation rate
    # historically high or low?"
    med_df = _load_csv('median_cpi')
    med = _to_series(med_df, 'median_cpi')
    if med is not None and len(med) >= 13:
        z = _expanding_zscore(med)
        signals['MEDCPIM158SFRBCLE'] = z
    else:
        signals['MEDCPIM158SFRBCLE'] = None

    # --- Market Expectations (daily) ---

    # 10Y Breakeven (T10YIE) — rate-based (%)
    # Level z-scored against full history: "are inflation expectations
    # elevated relative to historical norms?"
    t10yie_df = _load_csv('breakeven_inflation_10y')
    t10yie = _to_series(t10yie_df, 'breakeven_inflation_10y')
    if t10yie is not None and len(t10yie) >= 253:
        z = _expanding_zscore(t10yie)
        signals['T10YIE'] = z
    else:
        signals['T10YIE'] = None

    # 5Y5Y Forward (T5YIFR) — rate-based (%)
    # Level z-scored against full history
    fwd_df = _load_csv('inflation_expectations_5y5y')
    fwd = _to_series(fwd_df, 'inflation_expectations_5y5y')
    if fwd is not None and len(fwd) >= 253:
        z = _expanding_zscore(fwd)
        signals['T5YIFR'] = z
    else:
        signals['T5YIFR'] = None

    # --- Consumer Expectations (monthly) ---

    # Michigan 1-Year Expectations (MICH) — rate-based (%)
    # Level z-scored against full history: "are consumer expectations
    # elevated relative to historical norms?"
    mich_df = _load_csv('michigan_inflation_expectations')
    mich = _to_series(mich_df, 'michigan_inflation_expectations')
    if mich is not None and len(mich) >= 13:
        z = _expanding_zscore(mich)
        signals['MICH'] = z
    else:
        signals['MICH'] = None

    return signals


def _load_inflation_raw_values() -> dict[str, Optional[dict]]:
    """Load raw values and direction labels for each inflation indicator.

    Returns a dict mapping indicator name to {raw_value, direction} for the
    latest available observation, or None if the indicator is unavailable.
    Used for component-level storage in market_conditions_history.json.
    """
    raw = {}

    # --- Realized Trend (index-level: direction = YoY rate direction) ---

    cpi_df = _load_csv('cpi')
    cpi = _to_series(cpi_df, 'cpi')
    if cpi is not None and len(cpi) >= 13:
        yoy = _compute_yoy_direction(cpi, 12)
        yoy_clean = yoy.dropna()
        if len(yoy_clean) > 0:
            latest = float(yoy_clean.iloc[-1])
            raw['CPIAUCSL'] = {
                'raw_value': round(latest, 6),
                'direction': 'rising' if latest > 0 else 'falling',
            }
    if 'CPIAUCSL' not in raw:
        raw['CPIAUCSL'] = None

    pce_df = _load_csv('core_pce_price_index')
    pce = _to_series(pce_df, 'core_pce_price_index')
    if pce is not None and len(pce) >= 13:
        yoy = _compute_yoy_direction(pce, 12)
        yoy_clean = yoy.dropna()
        if len(yoy_clean) > 0:
            latest = float(yoy_clean.iloc[-1])
            raw['PCEPILFE'] = {
                'raw_value': round(latest, 6),
                'direction': 'rising' if latest > 0 else 'falling',
            }
    if 'PCEPILFE' not in raw:
        raw['PCEPILFE'] = None

    # --- Rate-based series: direction = above/below expanding mean ---

    for csv_name, col_name, key in [
        ('median_cpi', 'median_cpi', 'MEDCPIM158SFRBCLE'),
        ('breakeven_inflation_10y', 'breakeven_inflation_10y', 'T10YIE'),
        ('inflation_expectations_5y5y', 'inflation_expectations_5y5y', 'T5YIFR'),
        ('michigan_inflation_expectations', 'michigan_inflation_expectations', 'MICH'),
    ]:
        df = _load_csv(csv_name)
        s = _to_series(df, col_name)
        min_len = 253 if key in ('T10YIE', 'T5YIFR') else 13
        if s is not None and len(s) >= min_len:
            exp_mean = s.expanding(min_periods=12).mean()
            latest_val = float(s.iloc[-1])
            latest_mean = float(exp_mean.iloc[-1])
            raw[key] = {
                'raw_value': round(latest_val, 4),
                'direction': 'rising' if latest_val > latest_mean else 'falling',
            }
        else:
            raw[key] = None

    return raw


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


# Dimensional grouping for inflation indicators.
# Equal weight per dimension (1/3 each) prevents any single dimension
# from dominating the composite — e.g., 3 realized indicators don't
# get 3x the voice of 1 consumer indicator.
_INFLATION_DIMENSIONS = {
    'realized': ['CPIAUCSL', 'PCEPILFE', 'MEDCPIM158SFRBCLE'],
    'market': ['T10YIE', 'T5YIFR'],
    'consumer': ['MICH'],
}


# Daily signals that should use rolling smoothing before monthly resampling
# to preserve intra-month responsiveness without noise.
_DAILY_SIGNALS = {'T10YIE', 'T5YIFR'}
_DAILY_SMOOTHING_WINDOW = 20  # ~1 trading month


def _compute_inflation_composite(
    signals: dict[str, Optional[pd.Series]],
) -> Optional[pd.Series]:
    """
    Compute dimensionally-weighted inflation composite.

    Groups 6 inflation indicators into 3 dimensions (realized trend,
    market expectations, consumer expectations), computes a per-dimension
    average, then averages the dimensions with equal weight.

    Each signal is forward-filled by 1 month after monthly resampling to
    handle publication lag within a dimension. At the cross-dimension level,
    forward-fill extends to 2 months because monthly FRED indicators
    (CPI, PCE, Median CPI, Michigan) publish with ~1-month lag, creating
    a 2-month-end gap relative to daily market signals early in each month.

    Daily signals (T10YIE, T5YIFR) use a 20-day rolling mean before
    monthly resampling to preserve intra-month responsiveness without
    introducing daily noise.
    """
    # Step 1: Build per-dimension composites
    dim_composites = {}
    for dim_name, indicator_keys in _INFLATION_DIMENSIONS.items():
        dim_signals = {
            k: signals[k]
            for k in indicator_keys
            if signals.get(k) is not None and len(signals[k]) > 0
        }
        if not dim_signals:
            continue

        # Resample each to monthly, forward-fill 1 month for publication lag
        monthly = {}
        for name, s in dim_signals.items():
            if name in _DAILY_SIGNALS:
                # Daily signals: smooth with rolling mean before resampling
                # to capture intra-month movements without daily noise
                smoothed = s.rolling(_DAILY_SMOOTHING_WINDOW, min_periods=5).mean()
                m = smoothed.resample('ME').last()
            else:
                m = s.resample('ME').last()
            monthly[name] = m

        # Combine into DataFrame (auto-aligns to union of date indices),
        # then forward-fill each column by 1 period
        combined = pd.DataFrame(monthly)
        combined = combined.ffill(limit=1)
        dim_avg = combined.mean(axis=1).dropna()

        if len(dim_avg) > 0:
            dim_composites[dim_name] = dim_avg

    if not dim_composites:
        return None

    # Step 2: Equal-weight average of dimensional composites
    dim_df = pd.DataFrame(dim_composites)
    dim_df = dim_df.ffill(limit=2)  # Bridge 2-month gap: monthly FRED data lags ~1 month
    composite = dim_df.mean(axis=1)
    return composite.dropna()


def _compute_inflation_breadth(
    signals: dict[str, Optional[pd.Series]],
) -> tuple[Optional[int], Optional[int]]:
    """
    Compute inflation breadth: count of indicators agreeing on majority direction.

    For each indicator, determine direction at the latest month-end:
    - Positive z-score → rising inflation signal
    - Negative z-score → falling inflation signal

    Breadth = count of indicators agreeing with the majority direction.

    Returns:
        (breadth_count, total_indicators) or (None, None) if no data.
    """
    directions = []
    for dim_name, indicator_keys in _INFLATION_DIMENSIONS.items():
        for key in indicator_keys:
            s = signals.get(key)
            if s is None or len(s) == 0:
                continue
            if key in _DAILY_SIGNALS:
                smoothed = s.rolling(_DAILY_SMOOTHING_WINDOW, min_periods=5).mean()
                monthly = smoothed.resample('ME').last().dropna()
            else:
                monthly = s.resample('ME').last().dropna()
            # Forward-fill 1 period for publication lag
            monthly = monthly.ffill(limit=1)
            if len(monthly) == 0:
                continue
            latest_z = float(monthly.iloc[-1])
            directions.append('rising' if latest_z > 0 else 'falling')

    if not directions:
        return None, None

    rising_count = sum(1 for d in directions if d == 'rising')
    falling_count = len(directions) - rising_count
    breadth = max(rising_count, falling_count)
    return breadth, len(directions)


def _compute_inflation_components(
    signals: dict[str, Optional[pd.Series]],
    raw_values: dict[str, Optional[dict]],
) -> dict:
    """
    Build per-indicator component data for storage and briefing.

    Returns a dict keyed by indicator name with direction, z_score, and
    raw_value for each available indicator. Missing indicators have None.
    """
    components = {}
    all_keys = [k for keys in _INFLATION_DIMENSIONS.values() for k in keys]

    for key in all_keys:
        s = signals.get(key)
        rv = raw_values.get(key)

        if s is None or len(s) == 0:
            components[key] = None
            continue

        if key in _DAILY_SIGNALS:
            smoothed = s.rolling(_DAILY_SMOOTHING_WINDOW, min_periods=5).mean()
            monthly = smoothed.resample('ME').last().dropna()
        else:
            monthly = s.resample('ME').last().dropna()
        monthly = monthly.ffill(limit=1)

        if len(monthly) == 0:
            components[key] = None
            continue

        latest_z = float(monthly.iloc[-1])
        comp = {
            'z_score': round(latest_z, 4),
            'direction': 'rising' if latest_z > 0 else 'falling',
        }
        if rv is not None:
            comp['raw_value'] = rv.get('raw_value')
        else:
            comp['raw_value'] = None

        components[key] = comp

    return components


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


def _apply_graduated_stability_filter(
    quadrant_series: pd.Series,
    required_consecutive: int = 2,
) -> tuple:
    """Apply graduated stability filter with transition watch state.

    Instead of silently suppressing month-1 transitions, this filter reports
    them as "Transition Watch" — an early warning that signals are shifting.

    Returns:
        (stable_series, transition_watch_series)
        - stable_series: pd.Series of confirmed quadrant labels (same as binary filter)
        - transition_watch_series: pd.Series of dicts or None per time step.
          None = confirmed; {'direction': str, 'month': int} = watching.
    """
    if len(quadrant_series) == 0:
        return quadrant_series, pd.Series([], dtype=object)

    stable_result = []
    watch_result = []
    current_stable = quadrant_series.iloc[0]

    for i, q in enumerate(quadrant_series):
        if i == 0:
            # First data point is always confirmed
            stable_result.append(current_stable)
            watch_result.append(None)
            continue

        if q == current_stable:
            # Same as confirmed — no transition
            stable_result.append(current_stable)
            watch_result.append(None)
        else:
            # New quadrant detected — count consecutive months backward
            count = 1
            for j in range(i - 1, max(i - required_consecutive, -1), -1):
                if quadrant_series.iloc[j] == q:
                    count += 1
                else:
                    break

            if count >= required_consecutive:
                # Threshold met — confirm transition
                current_stable = q
                stable_result.append(current_stable)
                watch_result.append(None)
            else:
                # Not yet confirmed — transition watch
                stable_result.append(current_stable)
                watch_result.append({'direction': q, 'month': count})

    return (
        pd.Series(stable_result, index=quadrant_series.index),
        pd.Series(watch_result, index=quadrant_series.index),
    )


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
      2. Compute z-scored inflation signals (direction for indices,
         expanding level for rate-based series)
      3. Equal-weight growth composite; dimensionally-weighted inflation
         composite (realized/market/consumer each 1/3)
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
    inflation_composite = _compute_inflation_composite(inflation_signals)

    if growth_composite is None or inflation_composite is None:
        logger.warning('Insufficient data for quadrant calculation')
        return None

    # Compute inflation breadth and component data
    breadth, breadth_total = _compute_inflation_breadth(inflation_signals)
    raw_values = _load_inflation_raw_values()
    components = _compute_inflation_components(inflation_signals, raw_values)

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

    # Apply graduated stability filter (transition watch for early warning)
    stable_quadrants, watch_series = _apply_graduated_stability_filter(
        raw_quadrants, required_consecutive=2,
    )

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
        watch_series = watch_series.reindex(common_idx)

    if len(common_idx) == 0:
        return None

    latest_idx = common_idx[-1]
    g_val = float(growth_aligned.iloc[-1])
    i_val = float(inflation_aligned.iloc[-1])
    raw_q = raw_quadrants.iloc[-1]
    stable_q = stable_quadrants.iloc[-1]
    tw = watch_series.iloc[-1]  # None or {'direction': str, 'month': int}

    return QuadrantResult(
        quadrant=stable_q,
        growth_composite=g_val,
        inflation_composite=i_val,
        raw_quadrant=raw_q,
        stable=(raw_q == stable_q),
        as_of=str(latest_idx.date()),
        inflation_breadth=breadth,
        inflation_breadth_total=breadth_total,
        inflation_components=components,
        transition_watch=tw,
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
    stable_quadrants, watch_series = _apply_graduated_stability_filter(
        raw_quadrants, required_consecutive=2,
    )

    return pd.DataFrame({
        'date': common_idx,
        'growth': growth_aligned.values,
        'inflation': inflation_aligned.values,
        'raw_quadrant': raw_quadrants.values,
        'quadrant': stable_quadrants.values,
        'transition_watch': watch_series.values,
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

    # NROU is quarterly — deduplicate (FRED sometimes has duplicate dates),
    # then forward-fill to monthly to align with UNRATE
    nrou = nrou[~nrou.index.duplicated(keep='last')]
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
# Cache file paths
# ---------------------------------------------------------------------------

MARKET_CONDITIONS_CACHE_FILE = os.path.join(DATA_DIR, 'market_conditions_cache.json')
MARKET_CONDITIONS_HISTORY_FILE = os.path.join(DATA_DIR, 'market_conditions_history.json')


# ---------------------------------------------------------------------------
# Section 5: Asset Class Expectations
# ---------------------------------------------------------------------------

# Quadrant → base expectations (direction for each asset class)
_QUADRANT_EXPECTATIONS = {
    'Goldilocks': {
        'sp500': 'positive',
        'treasuries': 'positive',
        'gold': 'neutral',
        'credit': 'positive',
        'commodities': 'neutral',
    },
    'Reflation': {
        'sp500': 'positive',
        'treasuries': 'negative',
        'gold': 'positive',
        'credit': 'neutral',
        'commodities': 'positive',
    },
    'Stagflation': {
        'sp500': 'negative',
        'treasuries': 'negative',
        'gold': 'positive',
        'credit': 'negative',
        'commodities': 'positive',
    },
    'Deflation Risk': {
        'sp500': 'negative',
        'treasuries': 'positive',
        'gold': 'neutral',
        'credit': 'negative',
        'commodities': 'negative',
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

    # Bitcoin/crypto: liquidity-driven (primary signal per framework §8 §6)
    btc_direction_map = {
        'Strongly Expanding': 'positive',
        'Expanding': 'positive',
        'Neutral': 'neutral',
        'Contracting': 'negative',
        'Strongly Contracting': 'negative',
    }
    btc_dir = btc_direction_map.get(liquidity_state, 'neutral')
    btc_mag = magnitude
    btc_conv = conviction
    if risk_state == 'Stressed':
        btc_conv = 'override'
        btc_mag = 'weak'
    expectations.append({
        'asset': 'bitcoin',
        'direction': btc_dir,
        'magnitude': btc_mag,
        'conviction': btc_conv,
    })

    return expectations


# Per-dimension signal breakdown for the implications matrix (§2 homepage)
# Maps each (asset, dimension) → signal: 'strong_support', 'support', 'neutral',
# 'headwind', 'strong_headwind'

# Quadrant signal per asset class
_QUADRANT_SIGNAL = {
    'Goldilocks': {
        'sp500': 'support', 'treasuries': 'support', 'gold': 'headwind',
        'credit': 'support', 'commodities': 'headwind', 'bitcoin': 'neutral',
    },
    'Reflation': {
        'sp500': 'support', 'treasuries': 'headwind', 'gold': 'support',
        'credit': 'neutral', 'commodities': 'support', 'bitcoin': 'neutral',
    },
    'Stagflation': {
        'sp500': 'headwind', 'treasuries': 'headwind', 'gold': 'support',
        'credit': 'headwind', 'commodities': 'support', 'bitcoin': 'neutral',
    },
    'Deflation Risk': {
        'sp500': 'headwind', 'treasuries': 'support', 'gold': 'neutral',
        'credit': 'headwind', 'commodities': 'headwind', 'bitcoin': 'neutral',
    },
}

# Liquidity signal per asset class (expanding = support for risk assets)
_LIQUIDITY_SIGNAL = {
    'positive': {  # Expanding / Strongly Expanding
        'sp500': 'support', 'treasuries': 'support', 'gold': 'neutral',
        'credit': 'support', 'commodities': 'neutral', 'bitcoin': 'strong_support',
    },
    'neutral': {
        'sp500': 'neutral', 'treasuries': 'neutral', 'gold': 'neutral',
        'credit': 'neutral', 'commodities': 'neutral', 'bitcoin': 'neutral',
    },
    'negative': {  # Contracting / Strongly Contracting
        'sp500': 'headwind', 'treasuries': 'neutral', 'gold': 'neutral',
        'credit': 'headwind', 'commodities': 'neutral', 'bitcoin': 'headwind',
    },
}

# Risk signal (Calm = support for risk assets, Stressed = headwind)
_RISK_SIGNAL = {
    'Calm': {
        'sp500': 'support', 'treasuries': 'neutral', 'gold': 'neutral',
        'credit': 'support', 'commodities': 'neutral', 'bitcoin': 'support',
    },
    'Normal': {
        'sp500': 'neutral', 'treasuries': 'neutral', 'gold': 'neutral',
        'credit': 'neutral', 'commodities': 'neutral', 'bitcoin': 'neutral',
    },
    'Elevated': {
        'sp500': 'headwind', 'treasuries': 'support', 'gold': 'support',
        'credit': 'headwind', 'commodities': 'neutral', 'bitcoin': 'headwind',
    },
    'Stressed': {
        'sp500': 'strong_headwind', 'treasuries': 'support', 'gold': 'strong_support',
        'credit': 'strong_headwind', 'commodities': 'neutral', 'bitcoin': 'strong_headwind',
    },
}

# Policy signal (Easing = support for duration-sensitive assets)
_POLICY_SIGNAL = {
    'Easing': {
        'sp500': 'support', 'treasuries': 'support', 'gold': 'neutral',
        'credit': 'neutral', 'commodities': 'neutral', 'bitcoin': 'neutral',
    },
    'Paused': {
        'sp500': 'neutral', 'treasuries': 'neutral', 'gold': 'neutral',
        'credit': 'neutral', 'commodities': 'neutral', 'bitcoin': 'neutral',
    },
    'Tightening': {
        'sp500': 'headwind', 'treasuries': 'headwind', 'gold': 'neutral',
        'credit': 'headwind', 'commodities': 'neutral', 'bitcoin': 'neutral',
    },
}

# Signal strength ordering for overall computation
_SIGNAL_RANK = {
    'strong_support': 2, 'support': 1, 'neutral': 0,
    'headwind': -1, 'strong_headwind': -2,
}


def build_implications_matrix(
    quadrant: str,
    liquidity_state: str,
    risk_state: str,
    policy_direction: str,
) -> List[Dict]:
    """Build per-dimension signal matrix for the portfolio implications table.

    Returns a list of dicts, one per asset, each with:
      asset, label, link, overall, quad, liq, risk, policy, why
    """
    # Map liquidity state to simplified direction
    liq_dir = 'neutral'
    if liquidity_state in ('Expanding', 'Strongly Expanding'):
        liq_dir = 'positive'
    elif liquidity_state in ('Contracting', 'Strongly Contracting'):
        liq_dir = 'negative'

    quad_signals = _QUADRANT_SIGNAL.get(quadrant, _QUADRANT_SIGNAL['Goldilocks'])
    liq_signals = _LIQUIDITY_SIGNAL.get(liq_dir, _LIQUIDITY_SIGNAL['neutral'])
    risk_signals = _RISK_SIGNAL.get(risk_state, _RISK_SIGNAL['Normal'])
    policy_signals = _POLICY_SIGNAL.get(policy_direction, _POLICY_SIGNAL['Paused'])

    assets = [
        ('sp500', 'Equities', '/equity'),
        ('treasuries', 'Bonds', '/rates'),
        ('gold', 'Gold', '/safe-havens'),
        ('bitcoin', 'Crypto', '/crypto'),
        ('credit', 'Credit', '/credit'),
        ('commodities', 'Commod.', '/equity'),
    ]

    rows = []
    for asset_key, label, link in assets:
        q = quad_signals.get(asset_key, 'neutral')
        l = liq_signals.get(asset_key, 'neutral')
        r = risk_signals.get(asset_key, 'neutral')
        p = policy_signals.get(asset_key, 'neutral')

        # Compute overall from average of dimension ranks
        dims = [q, l, r, p]
        avg_rank = sum(_SIGNAL_RANK.get(d, 0) for d in dims) / len(dims)
        if avg_rank >= 1.5:
            overall = 'strong_support'
        elif avg_rank >= 0.5:
            overall = 'support'
        elif avg_rank > -0.5:
            overall = 'neutral'
        elif avg_rank > -1.5:
            overall = 'headwind'
        else:
            overall = 'strong_headwind'

        # Build "why" for mobile: list dominant dimensions
        why_parts = []
        if _SIGNAL_RANK.get(q, 0) >= 1:
            why_parts.append('Quad')
        if _SIGNAL_RANK.get(l, 0) >= 1:
            why_parts.append('Liq')
        if _SIGNAL_RANK.get(r, 0) >= 1:
            why_parts.append('Risk')
        if _SIGNAL_RANK.get(p, 0) >= 1:
            why_parts.append('Pol')
        why = '+'.join(why_parts) if why_parts else ''

        rows.append({
            'asset': asset_key,
            'label': label,
            'link': link,
            'overall': overall,
            'quad': q,
            'liq': l,
            'risk': r,
            'policy': p,
            'why': why,
        })

    return rows


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class MarketConditionsResult:
    """Full market conditions result — quadrant is the headline classification."""

    # Headline: the Growth×Inflation quadrant drives asset expectations
    quadrant: str              # Goldilocks / Reflation / Stagflation / Deflation Risk

    # Supporting dimension states
    liquidity_state: str
    risk_state: str
    policy_stance: str
    policy_direction: str

    # Asset expectations (driven by quadrant + dimension overlays)
    asset_expectations: List[Dict]

    # Metadata
    as_of: Optional[str] = None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute_market_conditions(as_of_date: Optional[str] = None) -> Optional[MarketConditionsResult]:
    """
    Compute full market conditions: four dimensions → quadrant headline → asset expectations.

    Returns MarketConditionsResult or None if insufficient data.
    The quadrant (Growth×Inflation) is the headline classification.
    """
    liquidity = compute_liquidity(as_of_date)
    quadrant = compute_quadrant(as_of_date)
    risk = compute_risk(as_of_date)
    policy = compute_policy(as_of_date)

    # Require at least liquidity and quadrant
    if liquidity is None or quadrant is None:
        logger.warning('Cannot compute market conditions: missing liquidity or quadrant data')
        return None

    # Risk and policy: graceful degradation if unavailable
    if risk is not None:
        risk_state = risk.state
    else:
        risk_state = 'Normal'
        logger.info('Risk data unavailable; defaulting to Normal')

    if policy is not None:
        policy_stance = policy.stance
        policy_direction = policy.direction
    else:
        policy_stance = 'Neutral'
        policy_direction = 'Paused'
        logger.info('Policy data unavailable; defaulting to Neutral')

    # Build asset expectations (quadrant-driven with dimension overlays)
    expectations = _build_asset_expectations(
        quadrant.quadrant, liquidity.state, risk_state
    )

    # Determine as_of date.
    # Use the explicit backtest date if provided; otherwise use today's date.
    # Do NOT use max(dimension dates) — quarterly FRED series (NROU, GDPPOT)
    # have forward-looking observation dates that would key history entries
    # in the future, causing overwrites and lost daily snapshots.
    if as_of_date is not None:
        as_of = as_of_date
    else:
        from datetime import date as _date
        as_of = str(_date.today())

    return MarketConditionsResult(
        quadrant=quadrant.quadrant,
        liquidity_state=liquidity.state,
        risk_state=risk_state,
        policy_stance=policy_stance,
        policy_direction=policy_direction,
        asset_expectations=expectations,
        as_of=as_of,
    )


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def update_market_conditions_cache() -> Optional[dict]:
    """
    Compute current market conditions and write to cache file.

    Called by run_data_collection() during the daily refresh.
    Returns the cache dict, or None on failure.
    """
    logger.info('Computing market conditions for cache update...')

    try:
        # Compute individual dimensions for detailed cache data (US-323.1)
        liquidity = compute_liquidity()
        quadrant_result = compute_quadrant()
        risk = compute_risk()
        policy = compute_policy()

        if liquidity is None or quadrant_result is None:
            logger.warning('Market conditions computation returned None; skipping cache update')
            return None

        risk_state = risk.state if risk else 'Normal'
        policy_stance = policy.stance if policy else 'Neutral'
        policy_direction = policy.direction if policy else 'Paused'

        expectations = _build_asset_expectations(
            quadrant_result.quadrant, liquidity.state, risk_state
        )

        from datetime import date as _date
        import calendar
        today = _date.today()
        # Key by month-end date so daily updates overwrite within the same
        # month, matching the backfill cadence (QA issue #1 on bug #337).
        month_end = _date(today.year, today.month,
                          calendar.monthrange(today.year, today.month)[1])
        as_of = str(month_end)

        cache_data = {
            'quadrant': quadrant_result.quadrant,
            'dimensions': {
                'liquidity': {
                    'state': liquidity.state,
                    'score': round(liquidity.score, 4) if liquidity.score is not None else None,
                },
                'quadrant': {
                    'state': quadrant_result.quadrant,
                    'growth_composite': round(quadrant_result.growth_composite, 4),
                    'inflation_composite': round(quadrant_result.inflation_composite, 4),
                    'inflation_breadth': quadrant_result.inflation_breadth,
                    'inflation_breadth_total': quadrant_result.inflation_breadth_total,
                    'inflation_components': quadrant_result.inflation_components,
                    'transition_watch': quadrant_result.transition_watch,
                },
                'risk': {
                    'state': risk_state,
                    'score': risk.score if risk else None,
                    'vix_level': round(risk.vix_level, 2) if risk and risk.vix_level else None,
                    'vix_ratio': round(risk.vix_ratio, 4) if risk and risk.vix_ratio else None,
                    'stock_bond_corr': round(risk.stock_bond_corr, 4) if risk and risk.stock_bond_corr else None,
                },
                'policy': {
                    'stance': policy_stance,
                    'direction': policy_direction,
                    'taylor_gap': round(policy.taylor_gap, 4) if policy else None,
                    'actual_rate': round(policy.actual_rate, 4) if policy else None,
                    'taylor_prescribed': round(policy.taylor_prescribed, 4) if policy else None,
                },
            },
            'asset_expectations': expectations,
            'as_of': as_of,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }

        logger.info('Market conditions computed: quadrant=%s',
                     quadrant_result.quadrant)

        # Write to daily history (single source of truth — bug #337)
        _append_conditions_history(cache_data)

        # Backfill 12 months of history if sparse (bug #337)
        _backfill_history_if_needed()

        return cache_data

    except Exception:
        logger.exception('Error updating market conditions cache')
        return None


def get_market_conditions() -> Optional[dict]:
    """Read the latest market conditions from the history file.

    Returns the most recent entry in the same shape that consumers expect
    (quadrant, dimensions, asset_expectations, as_of, updated_at).
    Falls back to the legacy cache file if the history file is empty.
    """
    history = _load_conditions_history()
    if history:
        latest_date = max(history.keys())
        entry = history[latest_date]
        # Reconstruct the flat cache shape expected by callers
        return {
            'quadrant': entry.get('quadrant'),
            'dimensions': entry.get('dimensions', {}),
            'asset_expectations': entry.get('asset_expectations', []),
            'as_of': latest_date,
            'updated_at': entry.get('updated_at', ''),
        }

    # Legacy fallback: read old cache file if it exists
    if os.path.exists(MARKET_CONDITIONS_CACHE_FILE):
        try:
            with open(MARKET_CONDITIONS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            logger.exception('Error reading legacy market conditions cache')
    return None


# ---------------------------------------------------------------------------
# Market Conditions History (append-only, one entry per day)
# ---------------------------------------------------------------------------


def _load_conditions_history() -> dict:
    """Load the daily market conditions history from file.

    Returns a dict mapping ISO date strings to snapshot dicts.
    """
    try:
        if os.path.exists(MARKET_CONDITIONS_HISTORY_FILE):
            with open(MARKET_CONDITIONS_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as exc:
        logger.warning('Failed to read market conditions history: %s', exc)
    return {}


def _save_conditions_history(history: dict) -> None:
    """Persist the daily market conditions history to file."""
    try:
        os.makedirs(os.path.dirname(MARKET_CONDITIONS_HISTORY_FILE), exist_ok=True)
        with open(MARKET_CONDITIONS_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as exc:
        logger.warning('Failed to write market conditions history: %s', exc)


def _append_conditions_history(cache_data: dict) -> None:
    """Append a snapshot to the conditions history file.

    Keyed by the as_of date (month-end). Daily runs within the same month
    overwrite the same entry (idempotent). No pruning — all history retained.
    """
    as_of = cache_data.get('as_of')
    if not as_of:
        return

    history = _load_conditions_history()

    # Extract growth/inflation composite scores from dimensions for quadrant
    # trajectory visualisation (bug #337)
    dims = cache_data.get('dimensions', {})
    quad_dims = dims.get('quadrant', {})

    entry = {
        'quadrant': cache_data['quadrant'],
        'growth_score': quad_dims.get('growth_composite'),
        'inflation_score': quad_dims.get('inflation_composite'),
        'raw_quadrant': quad_dims.get('state', cache_data.get('quadrant')),
        'transition_watch': quad_dims.get('transition_watch'),
        'dimensions': dims,
        'asset_expectations': cache_data.get('asset_expectations', []),
        'updated_at': cache_data.get('updated_at'),
    }

    history[as_of] = entry
    _save_conditions_history(history)
    logger.info('Market conditions history updated for %s (%d total entries)',
                as_of, len(history))


def _backfill_history_if_needed(min_entries: int = 12) -> None:
    """Backfill history from computed dimension histories if sparse.

    When the history file has fewer than *min_entries*, compute 12 months
    of monthly snapshots using the *_history() functions and prepend them.
    Existing entries are never overwritten.
    """
    history = _load_conditions_history()
    if len(history) >= min_entries:
        return

    logger.info('History has %d entries (< %d); backfilling...', len(history), min_entries)

    try:
        from datetime import date as _date
        # 12 months ago
        today = _date.today()
        start = _date(today.year - 1, today.month, today.day).isoformat()

        quad_hist = compute_quadrant_history(start_date=start)
        liq_hist = compute_liquidity_history(start_date=start)
        risk_hist = compute_risk_history(start_date=start)
        policy_hist = compute_policy_history(start_date=start)

        if quad_hist is None or len(quad_hist) == 0:
            logger.warning('Cannot backfill: quadrant history unavailable')
            return

        # Use end-of-month dates from quadrant history (monthly cadence)
        quad_hist = quad_hist.copy()
        quad_hist['month'] = quad_hist['date'].dt.to_period('M')
        monthly = quad_hist.groupby('month').last().reset_index()

        added = 0
        for _, row in monthly.iterrows():
            dt_str = str(row['date'].date())
            if dt_str in history:
                continue  # never overwrite existing entries

            dims = {
                'quadrant': {
                    'state': row['quadrant'],
                    'growth_composite': round(float(row['growth']), 4),
                    'inflation_composite': round(float(row['inflation']), 4),
                },
            }

            # Liquidity — find closest date
            if liq_hist is not None and len(liq_hist) > 0:
                liq_row = liq_hist.iloc[(liq_hist['date'] - row['date']).abs().argsort()[:1]]
                dims['liquidity'] = {
                    'state': str(liq_row.iloc[0]['state']),
                    'score': round(float(liq_row.iloc[0]['score']), 4),
                }

            # Risk — find closest date
            if risk_hist is not None and len(risk_hist) > 0:
                risk_row = risk_hist.iloc[(risk_hist['date'] - row['date']).abs().argsort()[:1]]
                dims['risk'] = {
                    'state': str(risk_row.iloc[0]['state']),
                    'score': int(risk_row.iloc[0]['score']),
                }

            # Policy — find closest date
            if policy_hist is not None and len(policy_hist) > 0:
                pol_row = policy_hist.iloc[(policy_hist['date'] - row['date']).abs().argsort()[:1]]
                dims['policy'] = {
                    'stance': str(pol_row.iloc[0]['stance']),
                    'direction': str(pol_row.iloc[0]['direction']),
                }

            history[dt_str] = {
                'quadrant': row['quadrant'],
                'growth_score': round(float(row['growth']), 4),
                'inflation_score': round(float(row['inflation']), 4),
                'raw_quadrant': row.get('raw_quadrant', row['quadrant']),
                'dimensions': dims,
            }
            added += 1

        if added > 0:
            _save_conditions_history(history)
            logger.info('Backfilled %d monthly entries into conditions history', added)

    except Exception:
        logger.exception('Error during history backfill')


def get_conditions_history() -> dict:
    """Read the full market conditions history.

    Returns a dict mapping ISO date strings to snapshot dicts.
    """
    return _load_conditions_history()
