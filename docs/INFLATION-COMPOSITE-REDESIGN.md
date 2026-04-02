# Inflation Composite Redesign

**Created:** 2026-04-01
**Authors:** Eric + Claude (research collaboration)
**Status:** Proposal — awaiting PM review for feature/story breakdown
**Related Docs:**
- [MARKET-CONDITIONS-FRAMEWORK.md](MARKET-CONDITIONS-FRAMEWORK.md) — Current quadrant engine design
- [REGIME-MODEL-ISSUES.md](REGIME-MODEL-ISSUES.md) — Structural issues in the regime model
- [BACKTEST-FINDINGS-AND-REFINEMENTS.md](BACKTEST-FINDINGS-AND-REFINEMENTS.md) — Backtest results

---

## 1. Problem Statement

The inflation composite in the Market Conditions quadrant engine is producing misleading results. As of April 1, 2026, the dashboard classifies the current environment as **"Deflation Risk"** while the consensus macro narrative — supported by PPI at 3.4%, Core PCE at 3.06%, consumer expectations at 3.8-5.2%, an oil shock, and accelerating tariff pass-through — points toward **stagflation**.

This is not a cosmetic issue. The quadrant classification drives asset expectations and the AI briefing narrative. A wrong classification means wrong guidance for users.

### Root Causes

Investigation identified two categories of issues: **methodology problems** and **data gaps**.

---

## 2. Methodology Issues

### 2.1 Acceleration (Second Derivative) as Primary Classifier

**Current behavior:** The inflation composite uses acceleration — the change in the YoY rate of change — as the basis for quadrant classification. A positive composite means inflation is accelerating; negative means decelerating.

**The problem:** Inflation can be high and steadily rising, but if it rises at a constant rate, acceleration is zero. The system classifies this as neutral when every major practitioner framework (Bridgewater, Gavekal, Hedgeye) would classify it as "rising inflation."

**What practitioners do:** Most four-quadrant macro frameworks classify based on **direction of the YoY rate** (first derivative) — is inflation going up or down? Acceleration (second derivative) is used as a secondary early-warning signal for regime transitions, not as the primary classifier.

**Proposed fix:** Use direction of YoY rate as the primary quadrant classifier. Retain acceleration as a secondary signal that can flag upcoming transitions before the YoY direction confirms them.

### 2.2 Z-Score Normalization Window Too Long

**Current behavior:** Inflation signals are z-scored against a 5-year (60-month / 1260-trading-day) rolling window.

**The problem:** The 5-year window (2021-2026) includes the massive 2022-2023 inflation surge, when CPI hit 9%+ and acceleration values were extreme. Current moderate acceleration (+0.05% for CPI) gets z-scored against that period and looks deeply negative — even though inflation is objectively above target and mildly re-accelerating.

**Evidence:** BIS research and practitioner consensus confirm that long windows include the prior regime in the normalization, suppressing signals at turning points. Practitioners use 12-24 month windows for regime detection.

**Proposed fix:** Shorten the z-score window from 60 months to 24 months for regime detection purposes. Optionally retain the 5-year window as a secondary "how unusual is this historically?" context signal.

### 2.3 Monthly Resampling Discards Intra-Month Signals

**Current behavior:** Daily breakeven data is resampled to month-end via `resample('ME').last()`. April's breakeven signal won't enter the composite until April 30.

**The problem:** Market-implied inflation expectations can shift dramatically within a month (the 5Y breakeven hit 2.66% on March 18 then fell to 2.54% by month-end). The month-end snapshot misses this volatility entirely.

**Proposed fix:** Evaluate whether a mid-month or rolling-window approach for daily signals would improve responsiveness without introducing noise. At minimum, surface the daily signals as separate intra-month indicators alongside the monthly composite.

### 2.4 Two-Month Stability Filter Delays Regime Detection

**Current behavior:** The quadrant label won't change until the new quadrant persists for 2 consecutive months.

**The problem:** This adds 1-2 months of lag on top of the data and calculation lag. The BIS uses 5 consecutive quarters for central bank policy (far too slow for investment dashboards). Practitioner consensus for dashboards is that 2 months is a reasonable minimum, but a graduated approach is better.

**Proposed fix:** Replace the binary 2-month filter with a graduated confidence display:
- Month 1 in new quadrant: Display as "Transition Watch — signals shifting toward [X]"
- Month 2 in new quadrant: Display as confirmed regime transition

This gives users early warning while maintaining the confirmation gate.

### 2.5 No Component Visibility

**Current behavior:** Individual signal z-scores are computed but discarded. Only the blended composite is stored in `market_conditions_history.json`.

**The problem:** When signals diverge — e.g., breakevens are flat while realized inflation is rising — the composite averages them into a meaningless middle. There is no way to see what's driving the score or detect divergences.

**Proposed fix:** Store individual signal values alongside the composite. Surface them in the UI or at minimum make them available for debugging and the AI briefing.

### 2.6 Inflation Breadth Signal

**Current behavior:** None. The system only produces a single composite score.

**The problem:** When 5 out of 6 indicators point toward rising inflation but one disagrees, the breadth of agreement is itself a strong signal. The Federal Reserve (FEDS Notes, December 2024) publishes research showing that broad-based inflation pressure (high breadth) is more persistent than narrow-based pressure.

**Proposed fix:** Add an inflation breadth metric: count how many of the inflation indicators agree on direction. Display alongside the composite to indicate confidence.

---

## 3. Data Gaps

### 3.1 Current Inflation Indicators (4)

| # | Indicator | FRED ID | Frequency | Role |
|---|-----------|---------|-----------|------|
| 1 | CPI All Items | `CPIAUCSL` | Monthly | Realized headline inflation |
| 2 | Core PCE | `PCEPILFE` | Monthly | Fed's preferred realized gauge |
| 3 | 10Y Breakeven | `T10YIE` | Daily | Market inflation expectations |
| 4 | 5Y Breakeven | `T5YIE` | Daily | Market inflation expectations (shorter horizon) |

**Problem with current set:** The 5Y and 10Y breakevens are ~0.95 correlated — effectively double-counting the same market signal. There are no consumer expectations, no noise-filtered trend measures, and no way to detect expectations unanchoring.

### 3.2 Proposed Inflation Indicators (6)

| # | Indicator | FRED ID | Frequency | Have It? | Role |
|---|-----------|---------|-----------|----------|------|
| 1 | CPI All Items | `CPIAUCSL` | Monthly | Yes | Realized headline inflation |
| 2 | Core PCE | `PCEPILFE` | Monthly | Yes | Fed's preferred realized gauge |
| 3 | 10Y Breakeven | `T10YIE` | Daily | Yes | Market inflation expectations |
| 4 | Cleveland Fed Median CPI | `MEDCPIM158SFRBCLE` | Monthly | **No** | Best noise-filtered CPI trend signal (Cleveland Fed research) |
| 5 | 5Y5Y Forward Expectations | `T5YIFR` | Daily | **No** | Fed's preferred long-run expectations gauge; replaces 5Y Breakeven with a better signal that strips near-term noise |
| 6 | Michigan 1-Year Expectations | `MICH` | Monthly | **No** | Consumer inflation expectations; captures expectations-unanchoring risk that market-based measures miss |

### 3.3 Why These Specific Additions

**Cleveland Fed Median CPI** replaces noise with signal. It strips the 49.5% most extreme price changes from each tail of the CPI distribution. Cleveland Fed research shows it is a better predictor of the inflation trend than headline CPI, Core CPI, or Core PCE. It releases the same day as CPI (no additional lag).

**5Y5Y Forward Expectations** replaces the 5Y Breakeven. It isolates where markets expect inflation 5-10 years from now by stripping out near-term noise embedded in the 5Y breakeven. It's the measure the Fed itself watches most closely for expectations anchoring. Daily frequency, available on FRED.

**Michigan 1-Year Expectations** adds a dimension the current system completely lacks: what consumers expect. As of March 2026, Michigan expectations are 3.8% while market breakevens are ~2.3%. That 150bp divergence is a critical signal of potential expectations unanchoring — the Fed's worst-case scenario. This indicator would have caught the current stagflation concern weeks ago.

### 3.4 What We Considered But Excluded

The following indicators were researched and intentionally excluded:

| Indicator | Why Excluded |
|-----------|-------------|
| **PPI Final Demand** (`PPIFIS`) | Leading indicator, but relationship with CPI has weakened and is structurally unstable (Stock-Watson 2007). Better suited as a separate dashboard signal than a composite input. |
| **Import Price Index** (`IR`) | Captures tariff pass-through but relationship with CPI is episodic. Same recommendation as PPI. |
| **Oil / Gas prices** (`DCOILWTICO`, `GASREGW`) | Already embedded in CPI — including alongside CPI is double-counting. The Cleveland Fed uses these to *forecast* CPI, not as components *alongside* CPI. |
| **Dallas Fed Trimmed Mean PCE** | Valuable but highly correlated with Median CPI and Core PCE. Adding it would triple-count the "realized trend" dimension. |
| **Atlanta Fed Sticky-Price CPI** | Useful for persistence analysis but adds complexity with marginal gain at 6 indicators. Could be added later. |
| **Atlanta Fed Wage Growth Tracker** | Important macro signal but measures a different construct (labor market) than inflation itself. Better suited to the growth composite or a separate wage dimension. |
| **ECI / Average Hourly Earnings** | Same reasoning as wage tracker — labor market signal, not inflation signal. |
| **Cleveland Fed Inflation Nowcast** | Not available on FRED. Would require web scraping or custom API integration. |

### 3.5 Dimensional Coverage

The proposed 6 indicators cover three distinct dimensions of inflation:

**Realized Trend (3 indicators):**
- CPI All Items — headline, includes food/energy
- Core PCE — ex food/energy, Fed's preferred
- Cleveland Fed Median CPI — noise-filtered trend

**Market Expectations (2 indicators):**
- 10Y Breakeven — medium-term market expectations
- 5Y5Y Forward — long-run expectations (anchoring signal)

**Consumer Expectations (1 indicator):**
- Michigan 1-Year — consumer sentiment on inflation direction

This ensures that a divergence between what's happening (realized), what markets expect (breakevens/forwards), and what consumers expect (surveys) becomes visible rather than averaged away.

---

## 4. Research Basis

This proposal is grounded in the following research:

**On parsimony:**
- Stock & Watson (2007, 2016): Simple inflation models consistently beat complex ones. Inflation forecasting relationships are structurally unstable — more indicators does not mean better predictions.
- Cleveland Fed: Naive forecasts from Median CPI outperform Phillips curve regressions across most horizons.
- Atlanta Fed: Explicitly chose NOT to collapse 9 measures into a single number. Divergences between measures are informative.

**On the four-quadrant framework:**
- Bridgewater, Gavekal, Hedgeye, 42 Macro all use direction of YoY rate (first derivative) for regime classification, not acceleration (second derivative).
- BIS Papers No. 133 (2023): Low-inflation regimes are self-stabilizing; high-inflation regimes are self-reinforcing. Detection asymmetry matters.
- CFA Institute (2025): Markets react to changes in trajectory, not just levels. Monitoring the transition itself is a signal.

**On z-score windows:**
- BIS: Uses 5-year average as reference but with fixed absolute thresholds, not z-scores.
- EIB Working Paper 2019/11: Cut-off points for growth and inflation change over time; fixed long windows miss this.
- Hall (2024, Journal of Forecasting): Varying-length windows outperform fixed-length windows specifically during regime transitions.

**On expectations:**
- Fed Board Index of Common Inflation Expectations: Long-run expectations (TIPS, Michigan 5-10Y) dominate the common factor.
- Richmond Fed: Survey-based expectations generate best forecasts vs. term structure models.
- Michigan consumer expectations systematically overpredict but capture directional shifts early.

**On oil/commodity double-counting:**
- CME Group: Commodities make up ~36% of CPI variance. Including oil alongside CPI double-counts.
- Cleveland Fed nowcaster: Uses oil/gas as inputs to *forecast* CPI, not alongside CPI.
- IMF: 10% oil increase raises headline CPI ~0.4% including second-round effects.

---

## 5. Implementation Scope

### 5.1 Data Collection (New FRED Series)

Add 3 new FRED series to the data collection pipeline in `market_signals.py`:
- `MEDCPIM158SFRBCLE` — Cleveland Fed Median CPI (monthly)
- `T5YIFR` — 5-Year, 5-Year Forward Inflation Expectation Rate (daily)
- `MICH` — University of Michigan 1-Year Inflation Expectations (monthly)

Remove collection of `T5YIE` from the inflation composite inputs (may retain for other dashboard uses).

All three are available via the existing FRED API infrastructure. No new vendors or paid subscriptions.

### 5.2 Calculation Engine Changes (`market_conditions.py`)

1. **Update `_load_inflation_signals()`** — Replace T5YIE with T5YIFR and MICH; add Median CPI
2. **Add YoY direction classification** — New function to compute whether YoY rate is rising or falling for each indicator; use as primary quadrant classifier
3. **Retain acceleration as secondary signal** — Keep current `_compute_acceleration()` for transition early-warning
4. **Shorten z-score window** — Change from 60-month/1260-day to 24-month/504-day
5. **Add inflation breadth calculation** — Count directional agreement across indicators
6. **Store component-level data** — Write individual signal values to `market_conditions_history.json`
7. **Graduate the stability filter** — Add "Transition Watch" state for month 1 of a new quadrant

### 5.3 UI Changes

1. **Graduated confidence display** — Show "Transition Watch" vs. confirmed quadrant
2. **Component visibility** — Surface individual inflation signal states (optional, could be debug-only initially)
3. **Breadth indicator** — Display inflation breadth alongside quadrant (e.g., "5/6 indicators agree")

### 5.4 Testing

1. Update existing tests in `test_us2941_market_conditions.py` for new signal set
2. Add tests for YoY direction classification
3. Add tests for breadth calculation
4. Add tests for graduated stability filter
5. Backtest the new composite against historical data to verify improvement over current approach

### 5.5 Documentation

1. Update `MARKET-CONDITIONS-FRAMEWORK.md` Section 5 with new methodology
2. Update `conditions_config.py` if quadrant context sentences need adjustment for transition states

---

## 6. What This Does NOT Change

- **Growth composite** — No changes to the growth dimension
- **Liquidity, Risk, Policy dimensions** — Unchanged
- **Asset expectations logic** — Quadrant-to-asset mapping stays the same (but should produce better results with accurate quadrant classification)
- **AI briefing integration** — Consumes the quadrant output; no changes needed unless we surface component signals to the briefing
- **Other FRED data collection** — Existing series unaffected; only adding 3 new ones

---

## 7. Success Criteria

1. The inflation composite correctly identifies the current environment as trending toward stagflation (or at minimum, not "Deflation Risk") given: CPI 2.4% and rising, Core PCE 3.06%, consumer expectations at 3.8%, oil shock in progress
2. Regime transitions are detected within 1 month instead of 2-3 months
3. Individual component signals are visible for divergence analysis
4. Backtest composite score improves over current 4-indicator acceleration-only approach
5. No regression in stable-period classification accuracy (Goldilocks periods should still be correctly identified)
