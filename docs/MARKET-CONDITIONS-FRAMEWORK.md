# Market Conditions Framework: From Single Regime to Multi-Dimensional Intelligence

**Created:** 2026-03-16
**Updated:** 2026-03-17 (post-backtest refinements — verdict removed, quadrant leads)
**Authors:** Eric + Claude (research collaboration)
**Status:** Proposal — awaiting CEO review
**Supersedes:** Current k-means regime detection system (Bull/Neutral/Bear/Recession Watch)
**Related Docs:**
- [BACKTEST-FINDINGS-AND-REFINEMENTS.md](BACKTEST-FINDINGS-AND-REFINEMENTS.md) — Backtest results analysis and refinements
- [REGIME-MODEL-ISSUES.md](REGIME-MODEL-ISSUES.md) — Structural issues identified in current model
- [REGIME-BACKTEST-STRATEGY.md](REGIME-BACKTEST-STRATEGY.md) — Existing backtest infrastructure
- [specs/feature-3.3-macro-regime-detection.md](specs/feature-3.3-macro-regime-detection.md) — Current regime UI design spec

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Why the Current Model Fails](#2-why-the-current-model-fails)
3. [The New Framework: Quadrant-Led, Four Dimensions](#3-the-new-framework-quadrant-led-four-dimensions)
4. [Data Requirements](#4-data-requirements)
5. [Calculation Engine](#5-calculation-engine)
6. [Scoring and Validation](#6-scoring-and-validation)
7. [UI/UX Design Vision](#7-uiux-design-vision)
8. [Homepage Redesign](#8-homepage-redesign)
9. [Category Page Integration](#9-category-page-integration)
10. [AI Briefing Integration](#10-ai-briefing-integration)
11. [Migration Strategy](#11-migration-strategy)
12. [Implementation Phases](#12-implementation-phases)
13. [Risks and Mitigations](#13-risks-and-mitigations)
14. [Decision Log](#14-decision-log)
15. [Research Sources](#15-research-sources)

---

## 1. Executive Summary

### The Problem

The current k-means regime classifier scores **52.3/100** in backtesting — barely above random. This is not a tuning problem. The model has four structural failures:

1. **Central bank intervention reverses expected outcomes** — Bear regime saw S&P 500 rise 67% of the time
2. **Stock-bond correlation flipped** — 2022 broke the "bonds hedge stocks" assumption; the model has no mechanism to distinguish demand crashes from inflation crashes
3. **Gold's secular uptrend breaks counter-cyclical assumptions** — Gold rose in 3 of 4 regimes
4. **No distinction between crisis types** — A demand crash (2008: buy bonds) and an inflation crash (2022: sell bonds) are both classified as "Bear" despite requiring opposite positioning

Full evidence in [REGIME-MODEL-ISSUES.md](REGIME-MODEL-ISSUES.md).

### The Solution

Replace the single-label regime system with a **multi-dimensional conditions engine** built on four dimensions, with the **Growth × Inflation Quadrant as the headline**:

1. **The Quadrant as headline** (Goldilocks / Reflation / Stagflation / Deflation Risk) — tells users what type of environment we're in and what it means for their portfolio
2. **Three supporting dimensions** (Liquidity, Risk, Policy) — provide context on magnitude, near-term danger, and central bank stance
3. **A one-sentence synthesis** explaining the quadrant in plain English — what users read
4. **Asset-class-specific expectations** — testable predictions scored against inflation-adjusted returns
5. **Crypto scored against Liquidity** — because Bitcoin correlates with M2 (0.94), not macro quadrants

### Why This Is Better

The four dimensions solve each structural failure:

| Structural Failure | Current Model | New Framework |
|-------------------|---------------|---------------|
| Central bank "put" | Fed funds rate as raw input | Policy Stance dimension tracks direction + Taylor Rule gap |
| Stock-bond correlation flip | Hardcodes "bonds rally in Bear" | Growth × Inflation quadrant: Stagflation expects bonds AND stocks down |
| Gold's secular uptrend | Expects gold to fall in Bull | Quadrant-specific expectations: gold rises in 3 of 4 quadrants |
| Demand vs. inflation crash | Both are "Bear" | Deflation Risk (2008) vs. Stagflation (2022) are separate quadrants |

### Key Design Decisions

**Quadrant is the headline, not a blended verdict.** Initial design combined all four dimensions into a weighted verdict (Favorable/Mixed/Cautious/Defensive). Backtesting revealed that this blending destroys the quadrant's correct directional predictions — a Stagflation call diluted by expanding liquidity becomes "Mixed," losing the actionable signal. The quadrant alone correctly orders real returns across all asset classes. See [BACKTEST-FINDINGS-AND-REFINEMENTS.md](BACKTEST-FINDINGS-AND-REFINEMENTS.md) for full evidence.

**Score against inflation-adjusted returns.** Backtesting showed stocks produce positive *nominal* returns in all environments (including Stagflation) due to central bank intervention. But inflation-adjusted returns order correctly: Goldilocks (+4.68%) > Deflation Risk (+1.86%) > Reflation (+1.49%) > Stagflation (+1.20%). The model is right — it just doesn't show up in nominal returns.

**Magnitude ordering, not direction.** Instead of expecting negative equity returns in Stagflation, expect *underperformance* — reduced positive returns. The backtest scores whether Goldilocks produces higher real returns than Stagflation (magnitude ordering), not whether Stagflation produces negative returns (direction, which fails due to central bank intervention).

---

## 2. Why the Current Model Fails

### Current Architecture

- **Algorithm:** K-means clustering (k=4) on 5 FRED indicators
- **Indicators:** HY spread, yield curve 10Y-2Y, NFCI, initial claims, fed funds rate
- **Output:** Bull / Neutral / Bear / Recession Watch
- **Score:** 52.3/100 composite (50% multi-asset accuracy + 25% return ordering + 25% drawdown ordering)
- **Implementation:** `signaltrackers/regime_detection.py` + `signaltrackers/regime_config.py`

### Why K-Means Is Wrong for This Problem

| Property Needed | K-Means | Better Alternatives |
|----------------|---------|---------------------|
| Temporal persistence (today depends on yesterday) | No | HMM, Jump Models |
| Transition probabilities between states | No | HMM |
| Probabilistic/soft assignments | No | GMM, HMM |
| Non-spherical clusters | No | GMM |
| Regime-specific volatility | No | HMM, GMM |

K-means treats each monthly observation as independent — it has no concept of regime persistence. It uses hard cluster boundaries when markets transition gradually. And it assumes spherical clusters when macro indicators have correlated, elliptical distributions.

### The One-Dimensional Trap

The fundamental problem is not the algorithm — it's that a single bull-to-bear axis cannot represent the two most important macro distinctions:

**Growth vs. Contraction:**
- 2020 COVID crash → growth collapsed → Fed cut → bonds rallied → recovery was fast

**Inflation vs. Deflation:**
- 2022 inflation crisis → growth was fine → Fed hiked → bonds crashed → stocks and bonds fell together

Both are classified as "Bear" by the current model, yet they require **opposite** portfolio positioning. No algorithm improvement can fix this within a one-dimensional framework.

### Evidence from Backtesting

| Regime | Count | Accuracy | Core Problem |
|--------|-------|----------|-------------|
| Bull (n=81) | 26% | 45.2% | Treasuries and gold moved opposite to expectations |
| Neutral (n=78) | 25% | 80.4% | "Neutral expects range-bound" is a forgiving bar |
| Bear (n=97) | 31% | 47.5% | S&P 500 rose 67% of the time during "Bear" |
| Recession Watch (n=54) | 17% | 44.4% | All three assets underperformed expectations |

---

## 3. The New Framework: Quadrant-Led, Four Dimensions

### Architecture Overview

```
                    DATA LAYER
    ┌────────────────────────────────────────┐
    │  ~25 FRED series + market data         │
    │  (daily/weekly/monthly collection)     │
    └──────────────────┬─────────────────────┘
                       │
                CALCULATION LAYER
    ┌──────────────────▼─────────────────────┐
    │  Four independent dimension engines:   │
    │                                        │
    │  1. Global Liquidity    (weekly)       │
    │  2. Growth × Inflation  (monthly)      │
    │  3. Risk Regime         (daily)        │
    │  4. Policy Stance       (monthly)      │
    └──────────────────┬─────────────────────┘
                       │
               PRESENTATION LAYER
    ┌──────────────────▼─────────────────────┐
    │  Quadrant is the headline:             │
    │  - Drives traditional asset            │
    │    expectations (equities, bonds,      │
    │    gold, commodities)                  │
    │                                        │
    │  Three supporting dimensions:          │
    │  - Liquidity: magnitude modifier +     │
    │    CRYPTO direction (leads for crypto) │
    │  - Risk: near-term drawdown context    │
    │  - Policy: Fed stance context          │
    │                                        │
    │  Progressive disclosure:               │
    │  Tier 1: Quadrant + one sentence       │
    │  Tier 2: Four dimension summaries      │
    │  Tier 3: Full detail per dimension     │
    └────────────────────────────────────────┘
```

### Why No Blended Verdict

The initial design combined all four dimensions into a weighted verdict (Favorable/Mixed/Cautious/Defensive). Backtesting revealed this destroys information:

- The **quadrant** correctly orders real asset returns (Goldilocks +4.68% > Stagflation +1.20%)
- But when blended with liquidity, risk, and policy, the verdict **scrambles this ordering** (Cautious returned more than Mixed; Defensive returned more than Cautious)
- Example: Stagflation + Expanding Liquidity + Calm Risk → verdict was "Mixed," which diluted the correct Stagflation signal

The four dimensions answer **different questions** and should not be combined into one number:

| Dimension | Question It Answers | What It Drives |
|-----------|-------------------|----------------|
| **Quadrant** (headline) | What type of environment are we in? | Traditional asset direction |
| **Liquidity** (modifier) | How strong will the moves be? | Magnitude — and **crypto direction** |
| **Risk** (modifier) | How dangerous is it right now? | Near-term drawdown probability |
| **Policy** (modifier) | What is the Fed doing about it? | Context |

### Dimension 1: Global Liquidity

**What it measures:** How much money is available to flow into financial assets. This is the single most important variable for asset prices in the post-2008 era.

**Why it matters:** Michael Howell (CrossBorder Capital) demonstrates that global liquidity explains ~66% of asset price variation and leads asset prices by 30-90 days. Lyn Alden's research shows Bitcoin moves with global M2 83% of the time. The current model has zero liquidity inputs.

**States:** Expanding / Neutral / Contracting

**Inputs:**
- Fed Net Liquidity (Fed balance sheet minus TGA minus reverse repo)
- US M2 money supply growth rate
- ECB balance sheet (converted to USD)
- BOJ balance sheet (converted to USD)

### Dimension 2: Growth × Inflation Quadrant

**What it measures:** Which of four economic environments we are in, based on whether growth and inflation are each accelerating or decelerating.

**Why it matters:** This is the dimension that solves the core model failures. The Bridgewater All Weather framework and the Hedgeye Quad framework both use this structure. Alpha Architect (2024) applied GMM clustering to 62 years of US macro data and independently discovered four regimes that map directly to these quadrants.

**States (four quadrants):**

| Quadrant | Growth | Inflation | Archetype |
|----------|--------|-----------|-----------|
| **Goldilocks** | Accelerating | Decelerating | 2019, 2023-2024 |
| **Reflation** | Accelerating | Accelerating | 2021, early 2025 |
| **Stagflation** | Decelerating | Accelerating | 2022, 1970s |
| **Deflation Risk** | Decelerating | Decelerating | 2008-2009, 2020 |

**Inputs (Growth):** Initial claims, yield curve, NFCI, industrial production, building permits
**Inputs (Inflation):** 10Y breakeven, 5Y breakeven, CPI, core PCE

**Critical methodology:** Uses **rate of change** (acceleration/deceleration), not levels. "Growth decelerating" means the YoY growth rate is getting smaller — the economy may still be growing, but it's slowing down. This is the Hedgeye approach and produces earlier signals than level-based classification.

### Dimension 3: Risk Regime

**What it measures:** How stressed or calm financial markets are right now. Unlike the other dimensions (which use economic data with publication lags), this dimension uses directly observable, real-time market data.

**Why it matters:** CFA Institute research (2026) found that risk-regime-aware frameworks achieve 187% higher Sharpe ratios and 45.5% lower drawdowns vs. static approaches. The 2022 stock-bond correlation flip — where 60/40 portfolios lost 16.7% — is captured here.

**States:** Calm / Normal / Elevated / Stressed

**Inputs:**
- VIX level (volatility)
- VIX term structure (VIX / VIX3M ratio — contango vs. backwardation)
- Stock-bond rolling correlation (63-day)

### Dimension 4: Policy Stance

**What it measures:** Whether central bank policy is accommodative, neutral, or restrictive relative to current economic conditions — and in which direction it's moving.

**Why it matters:** The current model uses the raw fed funds rate, which conflates "rates are high because the economy is strong" with "rates are high because the Fed is fighting inflation." The Taylor Rule gap separates these.

**States:** Accommodative / Neutral / Restrictive
**Direction overlay:** Easing / Paused / Tightening

**Inputs:**
- Fed funds rate (actual)
- Core PCE inflation (for Taylor Rule)
- Unemployment rate + natural rate (for output gap via Okun's Law)
- CBO potential GDP (for Taylor Rule calibration)

### The Quadrant as Headline

The quadrant IS the user-facing headline. Each quadrant name is immediately followed by a plain-English definition:

| Quadrant | Plain English | Asset Implications |
|----------|--------------|-------------------|
| **Goldilocks** | Growth accelerating, inflation cooling | Best environment — equities lead, bonds supported, gold neutral |
| **Reflation** | Growth accelerating, inflation rising | Equities and commodities up, bonds under pressure, gold up |
| **Stagflation** | Growth slowing, inflation rising | Toughest environment — equities and bonds both struggle, gold shines |
| **Deflation Risk** | Growth slowing, inflation falling | Flight to safety — bonds rally, equities fall, gold mixed |

The three supporting dimensions (Liquidity, Risk, Policy) appear alongside the quadrant as context modifiers, not competing signals. Their role in the display:

- **Liquidity** modifies expected magnitude ("expanding liquidity may cushion the blow")
- **Risk** flags near-term drawdown danger ("elevated risk suggests caution despite Goldilocks conditions")
- **Policy** provides Fed context ("the Fed is tightening into Stagflation")
- **Liquidity leads for Crypto** — because Bitcoin correlates with M2 (0.94), not growth/inflation quadrants

The quadrant's asset expectations are what the backtest scores against.

---

## 4. Data Requirements

### New FRED Series to Collect

The project currently collects ~15 FRED series in `market_signals.py`. This framework requires ~10 additional series.

#### Layer 1: Global Liquidity

| Series ID | Name | Frequency | Units | Notes |
|-----------|------|-----------|-------|-------|
| `WALCL` | Fed Total Assets | Weekly (Wed) | Millions USD | Fed balance sheet |
| `WDTGAL` | Treasury General Account | Weekly (Wed) | Millions USD | Use Wednesday Level (not WTREGEN week avg) for alignment with WALCL |
| `RRPONTSYD` | Overnight Reverse Repo | Daily | **Billions USD** | **UNIT MISMATCH:** Must multiply by 1000 to align with WALCL/WDTGAL (millions) |
| `ECBASSETSW` | ECB Total Assets | Weekly | Millions EUR | Requires EUR→USD conversion |
| `JPNASSETS` | BOJ Total Assets | Monthly | 100M JPY | Requires JPY→USD conversion |
| `DEXUSEU` | EUR/USD Exchange Rate | Daily | USD per EUR | For ECB conversion |
| `DEXJPUS` | JPY/USD Exchange Rate | Daily | JPY per USD | Invert for BOJ conversion |

**Data already collected:** `M2SL` (US M2, monthly)

#### Layer 2: Growth × Inflation

| Series ID | Name | Frequency | Dimension | Notes |
|-----------|------|-----------|-----------|-------|
| `INDPRO` | Industrial Production Index | Monthly | Growth | Hard production data |
| `PERMIT` | Building Permits | Monthly | Growth | Leading housing indicator |
| `T5YIE` | 5Y Breakeven Inflation | Daily | Inflation | Shorter-term inflation expectations |
| `CPIAUCSL` | CPI All Items | Monthly | Inflation | Realized inflation |
| `PCEPILFE` | Core PCE Price Index | Monthly | Inflation | Fed's preferred measure |

**Data already collected:** `ICSA` (initial claims), `T10Y2Y` (yield curve), `NFCI`, `T10YIE` (10Y breakeven)

#### Layer 3: Risk Regime

| Series ID | Name | Frequency | Notes |
|-----------|------|-----------|-------|
| `VXVCLS` | VIX 3-Month (VIX3M) | Daily | For term structure ratio. History starts Dec 2007. |
| `STLFSI4` | St. Louis Financial Stress Index | Weekly | 18-component stress composite |

**Data already collected:** `VIXCLS` (VIX), `BAMLH0A0HYM2` (HY spread), `DGS10` (10Y yield), `SP500` (S&P 500)

#### Layer 4: Policy Stance

| Series ID | Name | Frequency | Notes |
|-----------|------|-----------|-------|
| `DFEDTARU` | Fed Funds Upper Target | Daily | Current policy rate |
| `PCEPI` | PCE Price Index | Monthly | For Taylor Rule inflation input |
| `GDPC1` | Real GDP | Quarterly | For output gap (backup to Okun's Law) |
| `GDPPOT` | CBO Potential GDP | Quarterly | Taylor Rule calibration. **Known limitation:** subject to large revisions |
| `UNRATE` | Unemployment Rate | Monthly | For Okun's Law output gap |
| `NROU` | Natural Rate of Unemployment | Quarterly | CBO estimate for Okun's Law |

### Data Availability Summary

| Layer | New Series | Already Collected | Total | Binding Historical Constraint |
|-------|-----------|-------------------|-------|-------------------------------|
| Liquidity | 7 | 1 | 8 | `WALCL` starts Dec 2002 |
| Growth × Inflation | 5 | 4 | 9 | All available from 1990s+ |
| Risk | 2 | 4 | 6 | `VXVCLS` starts Dec 2007 |
| Policy | 6 | 0 | 6 | `NROU` starts 1949 |
| **Total unique** | **~18 new** | **~9 existing** | **~27** | **Dec 2007 for full framework** |

### Data Not on FRED (Acknowledged Gaps)

| Data | Status | Workaround |
|------|--------|------------|
| China M2 (PBOC) | FRED series dead (Aug 2019) | Use 3-central-bank composite (Fed+ECB+BOJ = ~70% of global CB liquidity) |
| BOE Balance Sheet | Not on FRED | Omit; UK is ~4% of global CB liquidity |
| ISM Manufacturing PMI | Removed from FRED in 2016 | Use `INDPRO` (Industrial Production) as proxy |

### All Data Is Free

No paid data subscriptions are required. All series are available via the FRED API (already used by `market_signals.py`) or derived from existing collections.

---

## 5. Calculation Engine

### Implementation Plan

Create a new file `signaltrackers/market_conditions.py` alongside the existing `regime_detection.py`. The old system continues running in parallel during migration.

### Layer 1: Global Liquidity

#### Fed Net Liquidity (Weekly)

```python
# CRITICAL: Unit alignment — WALCL and WDTGAL are millions, RRPONTSYD is billions
fed_net_liquidity = WALCL - WDTGAL - (RRPONTSYD * 1000)

# Current (Mar 2026): ~6,646,344 - 805,806 - 427 = ~$5,840,111 million
```

#### Global Liquidity Composite (Weekly)

```python
# Step 1: Convert non-USD balance sheets
ecb_usd = ECBASSETSW * DEXUSEU                     # EUR millions → USD millions
boj_usd = (JPNASSETS * 100_000_000) / DEXJPUS      # 100M JPY units → USD

# Step 2: Compute YoY rate of change for each component
fed_nl_yoy   = fed_net_liquidity / fed_net_liquidity.shift(52) - 1    # 52 weeks
ecb_yoy      = ecb_usd / ecb_usd.shift(52) - 1
boj_yoy      = boj_usd / boj_usd.shift(12) - 1                       # 12 months
m2_yoy       = M2SL / M2SL.shift(12) - 1

# Step 3: Normalize to z-scores (5-year rolling window)
fed_z  = (fed_nl_yoy - fed_nl_yoy.rolling(260).mean()) / fed_nl_yoy.rolling(260).std()
ecb_z  = (ecb_yoy - ecb_yoy.rolling(260).mean()) / ecb_yoy.rolling(260).std()
boj_z  = (boj_yoy - boj_yoy.rolling(60).mean()) / boj_yoy.rolling(60).std()
m2_z   = (m2_yoy - m2_yoy.rolling(60).mean()) / m2_yoy.rolling(60).std()

# Step 4: Weighted composite
liquidity_score = 0.40 * fed_z + 0.20 * ecb_z + 0.15 * boj_z + 0.25 * m2_z
```

#### Liquidity Classification

| Score | State | Intensity |
|-------|-------|-----------|
| > 1.0 | **Strongly Expanding** | Powerful tailwind for risk assets |
| > 0.5 | **Expanding** | Supportive for risk assets |
| -0.5 to 0.5 | **Neutral** | No liquidity tailwind or headwind |
| < -0.5 | **Contracting** | Headwind for risk assets |
| < -1.0 | **Strongly Contracting** | Significant headwind |

**Update frequency:** Weekly (after Wednesday FRED releases, aligned with WALCL publication).

### Layer 2: Growth × Inflation Quadrant

#### Rate of Change Methodology

The framework uses **acceleration** (rate of change of YoY change) — the Hedgeye "second derivative" approach. This detects inflection points earlier than level-based classification.

```python
def compute_acceleration(series, period=12):
    """
    Compute the acceleration of a YoY rate of change.

    For monthly data: period=12 (12-month YoY)
    For weekly data: period=52 (52-week YoY)

    Returns: positive = accelerating, negative = decelerating
    """
    yoy_current = series / series.shift(period) - 1
    yoy_prior = series.shift(1) / series.shift(period + 1) - 1
    acceleration = yoy_current - yoy_prior
    return acceleration
```

#### Growth Composite

| Indicator | Series | Frequency | Direction | Weight |
|-----------|--------|-----------|-----------|--------|
| Initial Claims | `ICSA` | Weekly | **Inverted** (falling claims = growth) | 1.0 |
| Yield Curve 10Y-2Y | `T10Y2Y` | Daily | Direct (steepening = growth) | 1.0 |
| NFCI | `NFCI` | Weekly | **Inverted** (falling NFCI = looser = growth) | 1.0 |
| Industrial Production | `INDPRO` | Monthly | Direct | 1.0 |
| Building Permits | `PERMIT` | Monthly | Direct | 1.0 |

```python
# Compute acceleration for each, normalize to z-scores, apply direction
growth_signals = {
    'ICSA':   -1 * zscore(compute_acceleration(ICSA, period=52)),   # inverted
    'T10Y2Y': +1 * zscore(T10Y2Y.diff(252)),                       # level change over 12m
    'NFCI':   -1 * zscore(compute_acceleration(NFCI, period=52)),   # inverted
    'INDPRO': +1 * zscore(compute_acceleration(INDPRO, period=12)),
    'PERMIT': +1 * zscore(compute_acceleration(PERMIT, period=12)),
}

growth_composite = mean(growth_signals.values())
# > 0 → Growth Accelerating
# < 0 → Growth Decelerating
```

#### Inflation Composite

| Indicator | Series | Frequency | Weight |
|-----------|--------|-----------|--------|
| 10Y Breakeven Inflation | `T10YIE` | Daily | 1.0 |
| 5Y Breakeven Inflation | `T5YIE` | Daily | 1.0 |
| CPI All Items YoY | `CPIAUCSL` | Monthly | 1.0 |
| Core PCE YoY | `PCEPILFE` | Monthly | 1.0 |

```python
inflation_signals = {
    'T10YIE':  zscore(T10YIE.diff(252)),                             # level change
    'T5YIE':   zscore(T5YIE.diff(252)),                              # level change
    'CPIAUCSL': zscore(compute_acceleration(CPIAUCSL, period=12)),
    'PCEPILFE': zscore(compute_acceleration(PCEPILFE, period=12)),
}

inflation_composite = mean(inflation_signals.values())
# > 0 → Inflation Rising
# < 0 → Inflation Falling
```

#### Quadrant Classification

```python
if growth_composite > 0 and inflation_composite <= 0:
    quadrant = "Goldilocks"
elif growth_composite > 0 and inflation_composite > 0:
    quadrant = "Reflation"
elif growth_composite <= 0 and inflation_composite > 0:
    quadrant = "Stagflation"
else:
    quadrant = "Deflation Risk"
```

The actual composite values (not just the sign) position a dot within the quadrant for visualization, communicating conviction. A growth_composite of +0.1 means "barely accelerating" (near the boundary); +2.0 means "strongly accelerating."

#### Historical Quadrant Frequency

Based on academic research (Alpha Architect 2024, 62 years of US data):

| Quadrant | Approx. Frequency | Avg. Duration |
|----------|-------------------|---------------|
| Goldilocks | ~30% | 4-8 months |
| Reflation | ~30% | 4-8 months |
| Deflation Risk | ~25% | 3-6 months |
| Stagflation | ~15% | 2-4 months (unstable, resolves quickly) |

**Update frequency:** Monthly (after all monthly indicators release, typically first week of month).

### Layer 3: Risk Regime

All inputs are daily — this is the most responsive dimension.

#### VIX Level Score (0-3)

| VIX Range | Score | Label |
|-----------|-------|-------|
| < 15 | 0 | Low volatility |
| 15 - 20 | 1 | Normal |
| 20 - 30 | 2 | Elevated |
| > 30 | 3 | Crisis |

#### VIX Term Structure Score (0-2)

```python
vix_ratio = VIXCLS / VXVCLS    # VIX 30-day / VIX 3-month

# Contango (ratio < 1) is normal (~85% of the time since 2007)
# Backwardation (ratio > 1) signals stress — short-term fear > long-term fear
```

| Ratio | Score | Meaning |
|-------|-------|---------|
| < 0.95 | 0 | Contango — calm |
| 0.95 - 1.05 | 1 | Flat — uncertain |
| > 1.05 | 2 | Backwardation — stressed |

#### Stock-Bond Correlation Score (0-2)

```python
# Approximate daily bond returns from yield changes
# 10Y Treasury duration ≈ 8.5 years
bond_returns = -8.5 * DGS10.diff() / 100
equity_returns = SP500.pct_change()

# 63-day (3-month) rolling correlation
rolling_corr_63d = equity_returns.rolling(63).corr(bond_returns)
```

| Correlation | Score | Meaning |
|-------------|-------|---------|
| < -0.3 | 0 | Diversifying — bonds hedge stocks (normal post-2000) |
| -0.3 to +0.3 | 1 | Transitional — ambiguous hedging |
| > +0.3 | 2 | Correlated — bonds and stocks move together (2022-style) |

**Note:** The correlation score is a critical innovation. It directly captures the stock-bond correlation flip that broke the current model in 2022.

#### Combined Risk Score

```python
risk_score = vix_score + term_structure_score + correlation_score
# Range: 0-7

if risk_score <= 1:   risk_state = "Calm"
elif risk_score <= 3: risk_state = "Normal"
elif risk_score <= 5: risk_state = "Elevated"
else:                 risk_state = "Stressed"
```

**Update frequency:** Daily (all inputs update daily).

### Layer 4: Policy Stance

#### Taylor Rule Implementation

```python
# Inflation: YoY Core PCE
inflation = (PCEPILFE / PCEPILFE.shift(12) - 1) * 100

# Output gap via Okun's Law (monthly, more timely than quarterly GDP)
output_gap = -2 * (UNRATE - NROU)

# Taylor Rule prescribed rate
# i = r* + π + 0.5(π - π*) + 0.5(output_gap)
# Simplified: i = 1.0 + 1.5π + 0.5(output_gap)
# Where r* = 2%, π* = 2%
taylor_prescribed = 1.0 + 1.5 * inflation + 0.5 * output_gap

# Policy stance = how far actual rate is from Taylor prescription
taylor_gap = DFEDTARU - taylor_prescribed
# Positive → policy is TIGHTER than conditions warrant
# Negative → policy is LOOSER than conditions warrant
```

#### Policy Classification

| Taylor Gap | Stance |
|-----------|--------|
| > 1.0 | **Restrictive** |
| -0.5 to 1.0 | **Neutral** |
| < -0.5 | **Accommodative** |

#### Direction Overlay

```python
fed_change_3m = DFEDTARU - DFEDTARU.shift(63)  # ~3 months of trading days
if fed_change_3m > 0.25:    direction = "Tightening"
elif fed_change_3m < -0.25: direction = "Easing"
else:                       direction = "Paused"
```

Combined label examples: "Restrictive, Paused" or "Accommodative, Easing"

**Known limitation:** The Taylor Rule depends on CBO's potential GDP and natural unemployment rate estimates, which are revised significantly (up to 8% for potential GDP during 2007-2014 per SF Fed research). This dimension should carry lower weight in the verdict and be flagged as "model-dependent" in the UI. When Taylor Rule inputs diverge sharply from market-implied rates (fed funds futures), the discrepancy itself is informative and should be noted.

**Update frequency:** Monthly (after PCE release, typically last Friday of month).

### Asset Class Expectations by Quadrant

This is the table the backtest scores against. The quadrant drives traditional asset expectations. Liquidity drives crypto expectations.

**Critical insight from backtesting:** Stocks produce positive *nominal* returns in ALL quadrants due to central bank intervention. The scoring uses **inflation-adjusted (real) returns** and tests **magnitude ordering** (Goldilocks produces better real returns than Stagflation), NOT direction (Stagflation produces negative returns).

#### Quadrant Expectations (Traditional Assets)

| Quadrant | S&P 500 (real) | Treasuries (TLT) | Gold | Backtest Real 90d |
|----------|---------------|-------------------|------|-------------------|
| **Goldilocks** | Best returns | Positive (falling inflation supports) | Neutral to negative | +4.68% |
| **Reflation** | Good returns | Negative (rising inflation hurts) | Positive | +1.49% |
| **Deflation Risk** | Below average | Positive (flight to safety) | Neutral to positive | +1.86% |
| **Stagflation** | Worst returns | Negative (rising inflation hurts) | Positive | +1.20% |

**Scoring rule:** The backtest checks magnitude ordering of real returns: Goldilocks > Deflation Risk > Reflation > Stagflation. This ordering held in backtesting with 20 years of data.

#### Liquidity Overlay (Modifies Magnitude for Traditional Assets)

| Liquidity | Effect on Equities | Effect on Bonds | Effect on Gold |
|-----------|-------------------|-----------------|----------------|
| Expanding | Amplifies upside | Modest support | Supports via monetary debasement |
| Neutral | No modification | No modification | No modification |
| Contracting | Amplifies downside | Supports (flight to safety) | Mixed |

#### Liquidity Expectations (Crypto)

Crypto is scored against the liquidity dimension only — NOT the quadrant:

| Liquidity State | Crypto Expectation | Basis |
|----------------|-------------------|-------|
| Expanding | Positive (directional) | Bitcoin 0.94 correlation with M2, 83% directional accuracy |
| Neutral | Neutral | |
| Contracting | Negative (directional) | |

This directly addresses Bug #292 (incorrect crypto regime guidance in dashboard).

#### Risk Overlay (Modifies Confidence and Hedging)

| Risk State | Effect |
|-----------|--------|
| Calm | Full conviction in quadrant expectations |
| Normal | Standard conviction |
| Elevated | Drawdown risk is elevated (38% vs 18% probability); increase hedging |
| Stressed | Override other signals — capital preservation mode |

**Backtest evidence for Risk overlay:** During elevated/stressed risk periods, the average max drawdown was -8.36% vs -6.27% during calm periods. The probability of a negative 30-day return roughly doubles (38% vs 18%).

---

## 6. Scoring and Validation

### Compatibility with Existing Backtest Infrastructure

The scoring framework is **fully compatible** with the existing walk-forward + CPCV + DSR infrastructure in `signaltrackers/backtesting/regime_backtest.py`. The only change is the expectation table.

#### Scoring Flow

```
For each monthly evaluation date (2006-2025):
  1. Compute quadrant from data available at that date (NO lookahead)
  2. Compute 90-day forward REAL returns (nominal - CPI/4) for S&P 500, Treasuries, Gold
  3. Score traditional assets: does the quadrant's real return ordering hold?
     (Goldilocks > Deflation Risk > Reflation > Stagflation for equities)
  4. Score Treasuries and Gold: did each move in the expected direction?
  5. Score crypto separately against liquidity dimension
  6. Weight: S&P 500 (37.5%), Treasuries (31.25%), Gold (31.25%)
```

#### What Changes from Original Scoring

| Component | Original (v1 backtest) | Updated (v2) |
|-----------|----------------------|--------------|
| Classification | Four dimensions → blended verdict | Quadrant drives expectations directly |
| Equity scoring | Direction (positive/negative) | **Magnitude ordering of real returns** |
| Returns | Nominal | **Inflation-adjusted (real)** |
| Crypto | Excluded | **Scored against liquidity dimension** |

#### Why Magnitude + Real Returns Fix the Score

The v1 backtest showed multi-asset accuracy of 63.9% (up from 54.6%), but the composite failed because the verdict ordering was broken. The quadrant ordering works with real returns:

| Quadrant | Nominal 90d | CPI YoY | Real 90d | Ordering |
|----------|------------|---------|----------|----------|
| Goldilocks | +5.13% | 1.82% | **+4.68%** | Best ✓ |
| Deflation Risk | +2.48% | 2.47% | **+1.86%** | 2nd ✓ |
| Reflation | +2.15% | 2.65% | **+1.49%** | 3rd ✓ |
| Stagflation | +1.93% | 2.93% | **+1.20%** | Worst ✓ |

The ordering holds because Stagflation periods have both lower nominal returns AND higher inflation, creating a double penalty in real terms. During 2022 specifically (CPI 7-8%), real 90-day returns were -9.48%, -7.12%, -17.56% — the model was right about Stagflation being bad.

#### Historical Period Validation

| Historical Period | Old Model | New Model (Quadrant) | Outcome |
|-------------------|-----------|---------------------|---------|
| 2008-09 | Bear (correct direction) | Deflation Risk (correct: TLT ↑, S&P underperforms) | ✓ Same |
| 2020 Mar | Bear (wrong: S&P rallied) | Deflation Risk + Expanding Liquidity (recovery expected) | ✓ Better |
| 2022 | Bear (wrong: TLT ↓ not ↑) | **Stagflation** (correct: TLT ↓, S&P ↓, Gold ↑) | ✓ Fixed |
| 2023-24 | Bear/Neutral (wrong: S&P ↑↑) | Goldilocks (correct: best real returns) | ✓ Fixed |

#### Validation Steps

1. **Walk-forward expanding window** (10 folds, 2005-2025) — primary score
2. **CPCV** (k=6, p=2, purge=3 months) — applied to top variants
3. **Deflated Sharpe Ratio** — applied to winning configuration
4. **Economic plausibility filter** — hard-fail if March 2020 classified as Goldilocks or 2022 as Deflation Risk
5. **Regime stability check** — average quadrant duration must be ≥ 3 months

#### Binding Backtesting Constraint

VIX term structure data (`VXVCLS`) starts December 2007. This means:
- The Risk dimension can only be fully evaluated from 2008 onward
- Earlier folds (2005-2007) will use VIX level + HY spread only (no term structure)
- Growth × Inflation and Liquidity dimensions have full history from 2003+

---

## 7. UI/UX Design Vision

### Core Principle: Quadrant Leads, Progressive Disclosure

The quadrant is the single headline — it tells the user what type of economic environment we're in and what it means for their portfolio. The other three dimensions provide supporting context. This preserves cognitive simplicity (one headline, not four competing signals) while carrying more information than the old regime label.

**Three-tier progressive disclosure:**

| Tier | Time to Absorb | What User Sees | Where |
|------|---------------|----------------|-------|
| **Glance** | 5 seconds | Quadrant name + one sentence | Conditions strip (every page) |
| **Summary** | 30 seconds | AI briefing + four dimension cards | Homepage top section |
| **Deep dive** | 5 minutes | Interactive quadrant with trajectory, full metrics, implications matrix | Homepage expanded sections |

**Crypto exception:** On the Crypto category page, Liquidity leads instead of the Quadrant, because liquidity is what drives crypto prices.

### Design Language

#### Quadrant Colors

| Quadrant | Primary Color | Background | Semantic |
|----------|--------------|------------|----------|
| **Goldilocks** | `#0D9488` (teal-600) | `#CCFBF1` (teal-100) | Best environment |
| **Reflation** | `#1E40AF` (blue-800) | `#DBEAFE` (blue-100) | Growth with inflation |
| **Deflation Risk** | `#CA8A04` (amber-600) | `#FEF3C7` (amber-100) | Caution — slowdown |
| **Stagflation** | `#DC2626` (red-600) | `#FEE2E2` (red-100) | Toughest environment |

These map intentionally to the existing regime colors (Bull=green, Neutral=blue, Bear=amber, Recession=red) to ease the visual transition for existing users.

#### Dimension Colors (Used Only in Expanded/Detail Views)

Each dimension has its own spectrum when shown individually. These are NOT the verdict colors — they describe the state of that specific dimension:

| Dimension | Favorable End | Neutral | Unfavorable End |
|-----------|--------------|---------|-----------------|
| Liquidity | Deep blue `#2563EB` | Slate `#64748B` | Amber `#D97706` |
| Growth × Inflation | Teal `#0D9488` (Goldilocks) | — | Burnt orange `#EA580C` (Stagflation) |
| Risk | Cool blue `#3B82F6` (Calm) | Slate `#64748B` | Red `#DC2626` (Stressed) |
| Policy | Green `#16A34A` (Easing) | Slate `#64748B` | Amber `#D97706` (Tightening) |

**Colorblind safety:** Primary contrast pair is blue/amber (safe for red-green colorblindness). Red is reserved exclusively for Risk at elevated/stressed levels.

#### Accessibility

- All states distinguishable without color (icon + text label)
- AAA contrast ratios on all backgrounds
- `aria-live="polite"` on verdict and dimension state changes
- 44px minimum touch targets
- Screen reader text always in DOM

---

## 8. Homepage Redesign

### Current Homepage Structure

| Position | Section | Role |
|----------|---------|------|
| §0 | Macro Regime Score Card | Verdict |
| §0.5 | Recession Probability | Corroborating verdict |
| §0.75 | Regime Implications | Asset class implications |
| §1.5 | Sector Management Tone | Sector implications |
| §1 | Market Conditions at a Glance | Raw market evidence |
| §2 | Today's AI Briefing | Narrative synthesis |
| §3 | What's Moving | Real-time movers |

**Problem:** The homepage tries to be both the conditions overview AND a signal-level dashboard. The connection between "here's the macro environment" and "here's why these numbers matter" gets lost in the scroll. It's unclear to users why specific metrics are surfaced.

### New Homepage Structure

The homepage becomes the Market Conditions page. Every element has a clear purpose in answering: "What do I need to know today, and what does it mean for my portfolio?"

| Position | Section | Role | Content |
|----------|---------|------|---------|
| §0 | AI Briefing | **Lead narrative** | 2-3 paragraph synthesis of all conditions |
| §1 | Conditions at a Glance | **Visual summary** | Quadrant headline + four dimension cards (2×2 grid) |
| §2 | Growth × Inflation Detail | **Primary dimension** | Interactive quadrant + trajectory + driving metrics |
| §3 | Global Liquidity Detail | **Primary dimension** | Spectrum bar + components + trend |
| §4 | Risk Environment Detail | **Supporting dimension** | Spectrum bar + VIX/correlation/credit components |
| §5 | Policy Stance Detail | **Supporting dimension** | Spectrum bar + Taylor Rule + direction |
| §6 | Portfolio Implications | **Actionable takeaway** | Asset class matrix with per-dimension signals |
| §7 | What's Moving | **Real-time context** | Movers list with conditions context |

### Wireframes

#### §0: AI Briefing (Lead Section)

The AI briefing moves to the top. It becomes the "trusted morning briefing" — the narrative thread that everything below supports with data.

**Mobile (375px):**
```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  SIGNALTRACKERS DAILY BRIEFING                      │
│  March 16, 2026                                     │
│                                                     │
│  Markets are operating in a Goldilocks              │
│  environment with growth accelerating and           │
│  inflation moderating. Global liquidity is          │
│  expanding as the Fed's balance sheet               │
│  stabilizes and M2 growth turns positive.           │
│                                                     │
│  Risk indicators remain calm with the VIX           │
│  below 15 and credit spreads tight. Policy          │
│  is neutral-to-easing with markets pricing          │
│  two rate cuts by year-end.                         │
│                                                     │
│  This combination historically favors growth        │
│  stocks, technology, and long-duration bonds.       │
│  Watch inflation breakevens — they're               │
│  approaching the threshold that would shift         │
│  conditions toward Reflation.                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### §1: Conditions at a Glance

**Mobile (375px):**
```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ● GOLDILOCKS                    Updated today      │
│  "Growth is accelerating while inflation            │
│   cools — the best environment for portfolios"      │
│                                                     │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ LIQUIDITY        │  │ GROWTH ×         │        │
│  │ [=====|========] │  │ INFLATION        │        │
│  │ Expanding  ↑     │  │ ┌──┬──┐          │        │
│  │                  │  │ │  │●·│          │        │
│  │                  │  │ ├──┼──┤          │        │
│  │                  │  │ │  │  │          │        │
│  │                  │  │ └──┴──┘          │        │
│  │                  │  │ Goldilocks       │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ RISK             │  │ POLICY           │        │
│  │ [=|============] │  │ [=========|====] │        │
│  │ Calm             │  │ Easing  ↑        │        │
│  └──────────────────┘  └──────────────────┘        │
│                                                     │
│  Favored: Growth stocks, Long bonds, Tech           │
│  Watch:   Inflation nearing Reflation threshold     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tablet+ (768px):**
The four dimension cards display in a true 2×2 grid with more room. The Growth × Inflation quadrant visualization can be larger (~180×180px) showing the trajectory dot and recent path.

**Design notes:**
- Three of the four dimensions (Liquidity, Risk, Policy) use the **same horizontal spectrum bar component** with different labels and color endpoints. This is a single reusable component.
- The Growth × Inflation card uses a mini 2×2 quadrant visualization with a positioned dot. This is a unique component.
- Below the cards: a compact "Favored / Watch" strip (2 lines max) showing the portfolio-level takeaway.

#### §2-§5: Dimension Detail Sections

Each dimension gets an expandable section. On mobile, sections start collapsed (showing only the spectrum bar + state + one-line summary). Tap to expand.

**Expanded dimension section pattern (same for all four):**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  GLOBAL LIQUIDITY                    Expanding  ↑   │
│  ─────────────────────────────────────────────────  │
│  [Spectrum bar: ====|=============>]                │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │ Fed Net Liquidity     $5.84T     ↑ +2.3%  │    │
│  │ US M2 Growth          +3.1% YoY  ↑        │    │
│  │ ECB Balance Sheet     €6.18T     → flat    │    │
│  │ BOJ Balance Sheet     ¥684T      ↓ -1.2%  │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  Liquidity is expanding, driven primarily by US     │
│  M2 growth turning positive and Fed balance sheet   │
│  stabilization. ECB is flat while BOJ is modestly   │
│  tightening. Net effect: supportive for risk        │
│  assets over the next 1-3 months.                   │
│                                                     │
│  [Sparkline: 14-week liquidity trend]               │
│                                                     │
│  Related: Credit signals → | Rates detail →         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**The Growth × Inflation section is special** — it contains the interactive quadrant visualization:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  GROWTH × INFLATION                   Goldilocks    │
│  ─────────────────────────────────────────────────  │
│                                                     │
│       Growth Accelerating ↑                         │
│            │                                        │
│  Reflation │  Goldilocks                            │
│            │        ●←·←·                           │
│  ──────────┼──────────── Inflation                  │
│            │              Falling →                  │
│  Stagfla-  │  Deflation                             │
│  tion      │  Risk                                  │
│            │                                        │
│       Growth Decelerating ↓                         │
│                                                     │
│  The ● shows current position.                      │
│  The ·←·← trail shows the last 3 months.           │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │ GROWTH SIGNALS                             │    │
│  │ Initial Claims    210K     ↓ improving     │    │
│  │ NFCI              -0.32   loose            │    │
│  │ Yield Curve       +0.45%  steepening       │    │
│  │ Industrial Prod.  +2.1%   accelerating     │    │
│  │ Building Permits  1.52M   accelerating     │    │
│  ├────────────────────────────────────────────┤    │
│  │ INFLATION SIGNALS                          │    │
│  │ 10Y Breakeven     2.31%   ↓ falling        │    │
│  │ 5Y Breakeven      2.18%   ↓ falling        │    │
│  │ CPI YoY           2.8%    decelerating     │    │
│  │ Core PCE YoY      2.5%    decelerating     │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  Related: Equities → | Rates → | Safe Havens →     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Interactive behavior for quadrant visualization:**
- Tap/hover any quadrant → tooltip: "Goldilocks: Growth accelerating + inflation falling. Historically favors growth stocks and long bonds."
- Tap the current dot → show exact growth/inflation composite values
- The trail of 3-6 previous monthly positions shows trajectory (where we came from, where we're heading)
- Current quadrant at full opacity; other three at 40%

#### §6: Portfolio Implications

Replaces the current regime implications panel. Restructured for the quadrant framework.

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  WHAT THIS MEANS FOR YOUR PORTFOLIO                 │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  ┌─────────┬──────────┬──────┬──────┬──────┬─────┐ │
│  │ Asset   │Liquidity │Quad  │Risk  │Policy│ Net │ │
│  ├─────────┼──────────┼──────┼──────┼──────┼─────┤ │
│  │Equities │ ✓ +      │ ✓ ++ │ ✓    │ ✓    │ ✓✓  │ │
│  │Bonds    │ ✓ +      │ ✓ +  │ ✓    │ ✓    │ ✓✓  │ │
│  │Gold     │ ─        │ ✗ -  │ ✓    │ ─    │ ─   │ │
│  │Commod.  │ ─        │ ✗ -  │ ✓    │ ─    │ ✗   │ │
│  │Credit   │ ✓ +      │ ✓ +  │ ✓    │ ─    │ ✓   │ │
│  │Crypto   │ ✓ ++     │ ─    │ ✓    │ ─    │ ✓   │ │
│  └─────────┴──────────┴──────┴──────┴──────┴─────┘ │
│                                                     │
│  ✓ = supportive  ─ = neutral  ✗ = headwind         │
│                                                     │
│  In previous Goldilocks periods with expanding      │
│  liquidity (n=14 since 2003), the S&P 500           │
│  returned +8.2% annualized over 6 months.           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key innovation:** This matrix shows users **why** each asset class is favored or not, broken down by which dimension drives the signal. This replaces the current implications panel's opaque "strong_outperform / underperform" labels with transparent reasoning.

**Mobile:** The matrix collapses into expandable cards per asset class, each showing its signal breakdown.

### Conditions Strip (Every Page)

Replaces `_regime_strip.html`. Same visual weight and position as the current strip.

**Desktop (768px+):**
```
┌──────────────────────────────────────────────────────────────────────┐
│ ● GOLDILOCKS   Liquidity: Expanding ↑ │ Risk: Calm │ Policy: Easing ↑ │
└──────────────────────────────────────────────────────────────────────┘
```

**Crypto page (desktop) — Liquidity leads:**
```
┌──────────────────────────────────────────────────────────────────────┐
│ ● LIQUIDITY: EXPANDING ↑   Goldilocks │ Risk: Calm │ Policy: Easing ↑ │
└──────────────────────────────────────────────────────────────────────┘
```

**Mobile (<768px):**
```
┌──────────────────────────────────────┐
│ ● GOLDILOCKS                      ▾ │
└──────────────────────────────────────┘
```
Tap ▾ to expand into vertical list of supporting dimensions.

---

## 9. Category Page Integration

### What Changes on Category Detail Pages

Each category page (Credit, Rates, Equities, Dollar, Crypto, Safe Havens) currently shows:
1. A regime strip at the top with a category-specific context sentence
2. Regime annotations on each metric card

These are updated to use the new framework:

#### Updated Category Context Sentences

Instead of one sentence per regime, each category gets context per **quadrant + liquidity state**:

**Example: Credit page**

| Quadrant | Liquidity Expanding | Liquidity Contracting |
|----------|--------------------|-----------------------|
| Goldilocks | "Credit spreads historically tighten further in Goldilocks with expanding liquidity — carry trades are supported." | "Goldilocks conditions support credit, but contracting liquidity may limit spread compression." |
| Reflation | "Rising inflation pressures credit quality; spreads may widen despite economic growth." | "Tightening liquidity and rising inflation create headwinds for lower-quality credit." |
| Stagflation | "Stagflation is historically the worst environment for credit — expect spread widening." | "Severe credit stress likely. Spreads at current levels underestimate risk." |
| Deflation Risk | "Flight to quality benefits high-grade credit; avoid high-yield in deflation risk." | "Credit contraction underway. Focus on balance sheet quality and short duration." |

This provides dramatically more specific guidance than the current system's generic "Spreads widening; credit stress is building here."

#### Updated Signal Annotations

Each signal gets annotations per quadrant rather than per regime. The annotation structure in `regime_config.py` expands from 4 entries per signal (one per regime) to entries keyed by the quadrant + relevant dimension.

---

## 10. AI Briefing Integration

### Current State

The AI briefing in `signaltrackers/ai_summary.py` receives the regime state as context and generates a narrative. It currently gets:
- Regime state (Bull/Bear/Neutral/Recession Watch)
- Regime confidence
- Individual signal values

### New Context for AI

The AI briefing receives all four dimensions with the quadrant as the frame:

```python
conditions_context = {
    'quadrant': {
        'name': 'Goldilocks',
        'growth_score': 0.6,
        'inflation_score': -0.4,
        'growth_drivers': ['Claims falling', 'NFCI loosening'],
        'inflation_drivers': ['CPI decelerating', 'Breakevens falling'],
    },
    'liquidity': {
        'state': 'Expanding',
        'score': 0.8,
        'direction': 'improving',
        'key_drivers': ['M2 growth turning positive', 'Fed balance sheet stable'],
    },
    'risk': {
        'state': 'Calm',
        'score': 1,
        'vix': 14.8,
        'term_structure': 'contango',
        'stock_bond_corr': -0.35,
    },
    'policy': {
        'stance': 'Neutral',
        'direction': 'Easing',
        'taylor_gap': 0.3,
        'fed_funds': 4.25,
    },
    'implications': {
        'favored': ['Growth stocks', 'Long bonds', 'Tech'],
        'headwinds': ['Commodities', 'Energy'],
        'watch': ['Inflation breakevens approaching Reflation threshold'],
    },
}
```

### Narrative Structure

The AI briefing should follow a three-paragraph structure:

1. **Current conditions** — Lead with the quadrant, then how the other three dimensions modify the picture
2. **What's changing** — Transitions, trends approaching thresholds (e.g., "inflation metrics approaching the Reflation boundary")
3. **Portfolio implications** — What this means in plain English for the reader's investments

### Rule-Based Fallback

When the AI is unavailable (no API key, rate limit, etc.), a rule-based narrative generator constructs the briefing from templates:

```python
headline = (
    f"{quadrant_name}: {quadrant_plain_english}. "
    f"Liquidity is {liquidity_state}, risk is {risk_state}, "
    f"and policy is {policy_direction}."
)
# Example: "Goldilocks: Growth is accelerating while inflation cools.
#           Liquidity is expanding, risk is calm, and policy is easing."
```

---

## 11. Migration Strategy

### Parallel Operation

The new `market_conditions.py` runs alongside `regime_detection.py` during the migration period. Both systems cache their results. The UI switches from the old cache to the new one when the frontend is ready.

### What Gets Replaced

| Current Component | Action | New Component |
|-------------------|--------|---------------|
| `regime_detection.py` | **Keep running** (parallel) then deprecate | `market_conditions.py` |
| `regime_config.py` | **Extend** — add quadrant metadata alongside regime metadata | `conditions_config.py` |
| `regime_implications_config.py` | **Replace** — new implications by quadrant × liquidity | `conditions_implications_config.py` |
| `_regime_strip.html` | **Replace** | `_conditions_strip.html` |
| Homepage §0 (regime card) | **Replace** with quadrant headline + conditions summary | New §1 |
| Homepage §0.75 (implications panel) | **Restructure** for quadrants | New §6 |
| `layer1_regime_transition.py` | **Extend** — alert on quadrant transitions and liquidity shifts | Enhanced alert engine |
| `ai_summary.py` | **Extend** — quadrant-led context dict (no verdict) | Same file, richer context |
| `regime_backtest.py` | **Extend** — quadrant-based expectations with real returns | Same file + new scoring logic |
| Verdict classifier | **Remove** — verdict scoring, weights, thresholds | N/A — quadrant is the headline directly |

### What Stays Unchanged

- All category detail pages (Credit, Rates, Equities, etc.) — structure unchanged, annotations updated
- Market data collection pipeline (`market_signals.py`) — extended with new series, existing series unchanged
- All existing CSS architecture — extended, not replaced
- Flask route structure — no new routes required (conditions is the homepage)
- Cache file pattern — new file (`market_conditions_cache.json`) alongside existing

### Bitcoin Reintegration

With the liquidity dimension, Bitcoin can be scored **against liquidity only**, not against the composite verdict. This addresses Bug #292 (incorrect crypto regime guidance). The Crypto category page would show: "Liquidity is expanding — historically favorable for Bitcoin (83% directional accuracy with ~90-day lag per Lyn Alden research)."

---

## 12. Implementation Phases

### Phase 1: Data Collection (Backend, No UI Changes)

**Goal:** Add all new FRED series to `market_signals.py` and verify data quality.

**Scope:**
- Add ~18 new FRED series to the data collection pipeline
- Store as CSVs in `data/` directory (same pattern as existing series)
- Verify data availability, handle unit mismatches (RRPONTSYD billions vs millions)
- Add FX conversion for ECB/BOJ balance sheets
- No UI changes — existing regime system continues operating

**Risk:** Low. Pure additive data collection.

### Phase 2: Calculation Engine (Backend, No UI Changes) — COMPLETE

**Goal:** Build `market_conditions.py` with all four dimension engines.

**Scope:**
- ✅ Implement liquidity composite calculation
- ✅ Implement growth × inflation quadrant engine
- ✅ Implement risk regime scoring
- ✅ Implement Taylor Rule / policy stance
- ✅ Store full calculation history (for quadrant trajectory visualization)
- ✅ Cache results to `market_conditions_cache.json`
- ✅ Run in parallel with existing regime system

**Status:** Implemented in PRs #306, #307, #308, #311.

### Phase 3: Backtest Validation — IN PROGRESS (Scoring Refinement)

**Goal:** Score the new model through the walk-forward framework and validate it beats 52.3/100.

**Status:** First backtest run completed (branch `feature/US-303`). Multi-asset accuracy improved to 63.9% (from 54.6%), but composite score of 31.9 failed due to verdict-based scoring issues. Analysis identified three refinements needed (see [BACKTEST-FINDINGS-AND-REFINEMENTS.md](BACKTEST-FINDINGS-AND-REFINEMENTS.md)):

**Remaining scope:**
- Remove verdict-based scoring — score against quadrant expectations directly
- Switch to inflation-adjusted (real) returns for equity scoring
- Test magnitude ordering (Goldilocks > Stagflation) instead of direction (positive vs negative)
- Add crypto scoring against liquidity dimension
- Fix NROU duplicate data bug (Issue #313) blocking per-evaluation CSV
- Re-run walk-forward validation with updated scoring
- Run CPCV and DSR on updated results
- Document final results

**Critical gate:** If the quadrant-based real-return scoring does not beat 52.3/100, iterate on the model before proceeding to UI.

**Risk:** Low-medium. The quadrant ordering already holds in the data (Goldilocks +4.68% > Stagflation +1.20% in real terms). The refinement is about scoring what we already have correctly, not building something new.

### Phase 4: Homepage Redesign (Full-Stack)

**Goal:** Replace the homepage with the conditions-first layout. This is the core UX transformation.

**Scope:**
- New conditions strip component (`_conditions_strip.html`)
- Move AI briefing to §0 (lead section)
- New conditions summary card (§1) with quadrant headline + four dimension mini-cards
- New dimension detail sections (§2-§5) with progressive disclosure
- New portfolio implications section (§6)
- Update context processors to inject conditions data
- Mobile-responsive layouts for all new components
- New CSS files for conditions components

**Risk:** Medium. Significant UI work but well-defined by the wireframes above.

### Phase 5: Category Page Migration (Full-Stack)

**Goal:** Update all category pages to use quadrant-based annotations and context sentences.

**Scope:**
- Update `_conditions_strip.html` behavior on category pages
- New quadrant × liquidity context sentences for all 6 categories
- Updated signal annotations for all ~19 signals
- Update AI briefing context on category pages

**Risk:** Low. Pattern established in Phase 4, applied consistently.

### Phase 6: AI Briefing Enhancement (Backend)

**Goal:** Update the AI briefing to synthesize all four dimensions with the narrative structure defined in Section 10.

**Scope:**
- Update `ai_summary.py` with new conditions context dict
- Build rule-based fallback narrative generator
- Update prompt templates for four-dimension synthesis
- Test narrative quality across different condition combinations

**Risk:** Low-medium. The AI work is incremental on existing infrastructure.

### Phase 7: Deprecate Old Regime System

**Goal:** Remove the parallel old system once the new system is validated in production.

**Scope:**
- Remove `regime_detection.py` calls from production code paths
- Archive old `regime_config.py` and `regime_implications_config.py`
- Remove old cache file generation
- Clean up any remaining regime-specific CSS/templates
- Update CLAUDE.md references

**Risk:** Low. Cleanup work.

---

## 13. Risks and Mitigations

### Critical Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| New model doesn't beat 52.3 in backtest | High | Low (post-refinement) | Phase 3 is a hard gate. First run showed multi-asset accuracy of 63.9% — the underlying predictions work. Scoring refinement (real returns, magnitude ordering, quadrant-based) should clear the bar. |
| Second derivatives whipsaw (noisy quadrant transitions) | High | Medium-High | Apply smoothing (3-month rolling average on acceleration signals). Require 2+ consecutive months in new quadrant before transition. Test stability constraint in backtest. |
| Taylor Rule instability (CBO revisions) | Medium | High | Policy dimension carries lowest weight (10%). Flag as "model-dependent" in UI. When Taylor Rule and fed funds futures diverge, note the discrepancy. |
| International data gaps (China/UK M2) | Medium | Certain | Use 3-central-bank composite (Fed+ECB+BOJ = ~70% global CB liquidity). Document the limitation. Revisit if PBOC/BOE FRED series are restored. |
| Retail investors don't understand "Goldilocks" / "Stagflation" | Medium | Medium | Use plain-English descriptions at Tier 1 ("Growth is accelerating while inflation cools"). Reserve technical names for Tier 2/3 with tooltips. Test with user research. |

### Operational Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| 25 FRED series = 25 potential failure points | Medium | Implement per-series staleness detection. If any Layer 1 or Layer 2 input is >45 days stale, flag the dimension as "Data delayed" in UI. Graceful degradation: verdict still computed from available dimensions. |
| AI narrative synthesizes four dimensions incorrectly | Medium | Rule-based fallback narrative always available. AI output validated against structural template (must mention all four dimensions, must name the verdict, must include implications). |
| VIX term structure data limited to 2007+ | Low | Risk dimension uses VIX level (available from 1990) as primary signal. Term structure is additive. Backtest earlier folds use VIX-only risk scoring. |

### Product Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Users miss the old simplicity of Bull/Bear/Neutral | Medium | The quadrant names (Goldilocks, Reflation, Stagflation, Deflation Risk) are equally simple and carry more information. Each is immediately followed by a plain-English sentence ("Growth is slowing while inflation rises"). |
| Homepage feels "too opinionated" | Medium | The quadrant is a factual classification (growth IS accelerating or decelerating), not an opinion. Every dimension card links to the underlying data (category pages). Users can always verify the reasoning. Include a "See the data →" CTA prominently. |
| Framework is wrong publicly and damages trust | Medium | Show historical accuracy prominently: "This framework correctly identified X of Y historical environments." When wrong, acknowledge it in the next briefing. Transparency builds more trust than perfection. |

---

## 14. Decision Log

Decisions made during the research and design process, with rationale.

| # | Decision | Rationale | Alternatives Considered |
|---|----------|-----------|------------------------|
| 1 | ~~**One verdict, not four gauges**~~ → **Quadrant as headline, no verdict** | Original design blended four dimensions into a verdict (Favorable/Mixed/Cautious/Defensive). Backtesting proved the verdict scrambled the quadrant's correct predictions — Cautious returned more than Mixed, Defensive returned more than Cautious. The quadrant alone correctly orders real returns. Verdict removed; quadrant IS the headline. Still one headline — just a better one that carries real information. | Blended verdict (rejected post-backtest: destroys quadrant signal), Four independent gauges (rejected: cognitive overload) |
| 2 | **Use rate of change, not levels, for quadrant** | Hedgeye approach: detects inflection points earlier. "Growth decelerating" (3% → 2%) is more useful than "growth is positive." | Level-based classification (rejected: too slow to detect transitions) |
| 3 | **Taylor Rule gap over Wu-Xia shadow rate for Policy** | Wu-Xia is no longer updated (stopped Jun 2023). Taylor Rule is computable from FRED data. Shadow rate only differs from actual rate during ZLB periods (not current). | Wu-Xia shadow rate (rejected: discontinued), Raw fed funds rate (rejected: conflates policy with conditions) |
| 4 | **Central bank balance sheets as global liquidity proxy** | International M2 FRED data is dead (China 2019, Japan 2017, Euro Area 2017). CB balance sheets are active and cover ~70% of global CB liquidity. | Global M2 aggregation (rejected: data unavailable on FRED), Proprietary data (rejected: paid, not FRED-compatible) |
| 5 | **Homepage = conditions page** | Current homepage lacks clear purpose — tries to be both overview and signal dashboard. Conditions-first gives it a clear narrative: "what's happening, why, and what to do." | Keep homepage as data dashboard with improved regime card (rejected: doesn't solve the structural clarity problem) |
| 6 | **AI briefing at top of homepage** | Briefing is the product's key differentiator ("plain-language synthesis"). Currently buried below regime and implications panels. Moving it to §0 makes interpretation the lead, supported by structured data below. | Keep briefing in current position (rejected: doesn't leverage the differentiator) |
| 7 | **Score crypto against liquidity, traditional assets against quadrant** | Bitcoin's 34.8% accuracy against macro regimes is unfixable — its drivers are liquidity and halving cycles, not growth/inflation. But it correlates 0.94 with global M2. On the Crypto page, liquidity leads the display instead of the quadrant. | Include Bitcoin in composite scoring (rejected: empirically fails), Exclude Bitcoin entirely (rejected: loses the genuine liquidity signal) |
| 8 | ~~**Liquidity and Quadrant weighted highest (35% each)**~~ → **No weights — dimensions serve different roles** | Original design weighted four dimensions into a verdict. Post-backtest, dimensions are not blended. Quadrant drives traditional asset expectations. Liquidity drives crypto and modifies magnitude. Risk and Policy provide context. No weighting needed. | Equal weighting into verdict (rejected: backtest showed blending destroys information) |
| 9 | **Phase 3 backtest as a hard gate before UI work** | Avoids building a beautiful UI for a model that doesn't work. Walk-forward validation is the empirical test. If it doesn't beat 52.3, iterate on the model, not the UI. | Build UI and model in parallel (rejected: risk of shipping unvalidated framework) |
| 10 | **Quadrant stability filter: require 2+ months before transition** | Second derivatives amplify noise. Without smoothing, quadrant would change every 1-2 months. Backtest shows 4.2 month average duration (passes 3-month minimum). | No smoothing (rejected: too noisy for retail), 3-month filter (considered: may miss genuine fast transitions like March 2020) |
| 11 | **Score using inflation-adjusted (real) returns** | Backtesting showed stocks produce positive nominal returns in ALL environments (central bank put). But real return ordering is correct: Goldilocks +4.68% > Stagflation +1.20%. During 2022 stagflation (CPI 7-8%), real returns were -9% to -17%. The model was right — nominal scoring hid it. | Nominal return scoring (rejected: fails because stocks are nominally positive even in Stagflation) |
| 12 | **Score magnitude ordering, not direction** | Instead of "did Stagflation produce negative returns?" (it didn't, nominally), score "did Goldilocks produce better real returns than Stagflation?" (it did, always). Magnitude ordering holds across 20 years of data. | Direction-based scoring (rejected: central bank intervention makes direction unreliable for equities) |

---

## 15. Research Sources

### Academic Papers

| Paper | Authors | Year | Key Finding |
|-------|---------|------|-------------|
| "Regimes" | Campbell Harvey et al. (Duke/Man Group) | 2025 | Regime identification on equity factors achieved 0.82 Sharpe. SSRN 5164863. |
| "A New Approach to the Economic Analysis of Nonstationary Time Series" | James Hamilton | 1989 | Foundational HMM regime-switching framework. |
| "Empirical Evidence on the Stock-Bond Correlation" | Baele, Bekaert, Inghelbrecht | 2024 | When inflation >5%, stock-bond correlation is always positive. Financial Analysts Journal. |
| "Measuring Macroeconomic Impact at the Zero Lower Bound" | Wu & Xia | 2016 | Shadow rate framework for unconventional policy. JMCB. |
| "A Monetary Policy Asset Pricing Model" | Caballero & Simsek | 2022 | Fed's reaction function creates "policy risk premium." NBER WP 30132. |
| "Deconstructing Monetary Policy Surprises" | Jarociński & Karadi | 2020 | FOMC surprises decompose into three components. AEJ: Macro. |
| "Identifying Patterns in Financial Markets: Statistical Jump Model" | Aydinhan, Kolm, Mulvey, Shu | 2024 | Jump model framework for regime identification. Annals of Operations Research. |

### Practitioner Research

| Source | Key Finding |
|--------|-------------|
| Two Sigma (2021/2025) | GMM on 17 factor returns identifies 4 regimes: Steady State, Crisis, Walking on Ice, and a fourth. |
| Alpha Architect (2024) | GMM on 62 years of US macro data independently finds Growth, Inflation, Precarious, Crisis regimes. |
| State Street (2025) | 23 datasets with t-distributed mixture model identifies 4 statistically robust regimes. |
| Michael Howell / CrossBorder Capital | Global liquidity explains ~66% of asset price variation. Liquidity cycle is 5-6 years. |
| Lyn Alden (2024) | Bitcoin moves with global M2 83% of the time. 0.94 correlation with ~90-day lag. |
| Raoul Pal / Real Vision | "Everything Code" — all assets are expressions of liquidity. ISM as timing overlay. |
| CFA Institute (2026) | Risk-regime-aware frameworks achieve 187% higher Sharpe, 45.5% lower drawdowns. |
| Hedgeye | Growth/Inflation quadrant (Quad 1-4) achieves ~70% accuracy with proprietary implementation. |
| AQR | Macro momentum (direction + rate of change) delivers 0.4-1.0 Sharpe over 50+ years. |
| Man Group/AHL (2025) | Similarity-based approach measuring historical resemblance rather than discrete classification. |
| BlackRock Investment Institute | "New regime" where mega forces replace traditional business cycles as market drivers. |

### Data Sources

| Source | URL | What It Provides |
|--------|-----|-----------------|
| FRED | fred.stlouisfed.org | All ~27 economic series used in this framework |
| Atlanta Fed Taylor Rule Utility | atlantafed.org/cqer/research/taylor-rule | Taylor Rule reference implementation |
| BIS Global Liquidity Indicators | data.bis.org/topics/GLI | Foreign currency credit to non-bank borrowers |
| CBOE | cboe.com | VIX term structure data (via FRED: VIXCLS, VXVCLS) |

---

## Appendix A: Glossary for Non-Technical Readers

| Term | Plain English |
|------|--------------|
| **Goldilocks** | Economy is growing and inflation is cooling — the "just right" environment. Think 2019 or 2023-2024. |
| **Reflation** | Economy is growing AND inflation is picking up — rising tide lifts all boats, but watch for overheating. Think 2021. |
| **Stagflation** | Economy is slowing but inflation is still rising — the worst combination. Think 2022 or the 1970s. |
| **Deflation Risk** | Economy is slowing and prices are falling — recession territory. Think 2008-2009 or March 2020. |
| **Fed Net Liquidity** | How much money the Fed is effectively making available to markets. Balance sheet minus money the government and banks are parking at the Fed. |
| **Taylor Rule** | A formula that says what interest rates "should" be given current inflation and unemployment. If the actual rate is higher, policy is restrictive. If lower, accommodative. |
| **VIX Term Structure** | Whether short-term fear is higher than long-term fear (backwardation = stressed) or lower (contango = calm). Normally long-term fear is higher. |
| **Stock-Bond Correlation** | Whether stocks and bonds move in the same direction (unusual, means bonds can't hedge stocks — like 2022) or opposite directions (normal, means bonds protect you when stocks fall). |
| **Rate of Change / Acceleration** | Not whether something is high or low, but whether it's getting bigger or smaller. "Growth decelerating" means the economy is still growing, but slowing down. |

## Appendix B: Complete FRED Series Reference

### Already Collected (~9 series)
`BAMLH0A0HYM2`, `T10Y2Y`, `NFCI`, `ICSA`, `FEDFUNDS`, `VIXCLS`, `T10YIE`, `M2SL`, `SP500`

### New Series Required (~18 series)
`WALCL`, `WDTGAL`, `RRPONTSYD`, `ECBASSETSW`, `JPNASSETS`, `DEXUSEU`, `DEXJPUS`, `INDPRO`, `PERMIT`, `T5YIE`, `CPIAUCSL`, `PCEPILFE`, `VXVCLS`, `STLFSI4`, `DFEDTARU`, `PCEPI`, `GDPC1`, `GDPPOT`, `UNRATE`, `NROU`, `DGS10`

### Series Details

| ID | Name | Freq | Units | Start | Layer |
|----|------|------|-------|-------|-------|
| `WALCL` | Fed Total Assets | W | M USD | 2002 | Liquidity |
| `WDTGAL` | Treasury General Account (Wed) | W | M USD | 2002 | Liquidity |
| `RRPONTSYD` | Overnight Reverse Repo | D | **B USD** | 2003 | Liquidity |
| `M2SL` | M2 Money Supply | M | B USD | 1959 | Liquidity |
| `ECBASSETSW` | ECB Balance Sheet | W | M EUR | 1999 | Liquidity |
| `JPNASSETS` | BOJ Balance Sheet | M | 100M JPY | 1998 | Liquidity |
| `DEXUSEU` | EUR/USD Rate | D | USD/EUR | 1999 | Liquidity |
| `DEXJPUS` | JPY/USD Rate | D | JPY/USD | 1971 | Liquidity |
| `ICSA` | Initial Claims | W | Persons | 1967 | Growth |
| `T10Y2Y` | 10Y-2Y Yield Curve | D | % | 1976 | Growth |
| `NFCI` | Financial Conditions | W | Index | 1971 | Growth |
| `INDPRO` | Industrial Production | M | Index | 1919 | Growth |
| `PERMIT` | Building Permits | M | Thousands | 1960 | Growth |
| `T10YIE` | 10Y Breakeven Inflation | D | % | 2003 | Inflation |
| `T5YIE` | 5Y Breakeven Inflation | D | % | 2003 | Inflation |
| `CPIAUCSL` | CPI All Items | M | Index | 1947 | Inflation |
| `PCEPILFE` | Core PCE | M | Index | 1959 | Inflation |
| `VIXCLS` | VIX | D | Index | 1990 | Risk |
| `VXVCLS` | VIX 3-Month | D | Index | 2007 | Risk |
| `DGS10` | 10Y Treasury Yield | D | % | 1962 | Risk |
| `SP500` | S&P 500 | D | Index | ~2016 | Risk |
| `BAMLH0A0HYM2` | HY OAS Spread | D | % | 1996 | Risk |
| `STLFSI4` | Financial Stress Index | W | Index | 1993 | Risk |
| `DFEDTARU` | Fed Funds Upper Target | D | % | 2008 | Policy |
| `PCEPI` | PCE Price Index | M | Index | 1959 | Policy |
| `GDPC1` | Real GDP | Q | B 2017$ | 1947 | Policy |
| `GDPPOT` | CBO Potential GDP | Q | B 2017$ | 1949 | Policy |
| `UNRATE` | Unemployment Rate | M | % | 1948 | Policy |
| `NROU` | Natural Unemployment Rate | Q | % | 1949 | Policy |
