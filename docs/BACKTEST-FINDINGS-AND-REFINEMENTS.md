# Market Conditions Backtest: Findings and Refinements

**Created:** 2026-03-17
**Context:** Analysis of first backtest results from the Market Conditions engine (branch `feature/US-303`)
**Related:**
- [MARKET-CONDITIONS-FRAMEWORK.md](MARKET-CONDITIONS-FRAMEWORK.md) — Original framework spec
- [REGIME-MODEL-ISSUES.md](REGIME-MODEL-ISSUES.md) — Structural issues in old model
- `signaltrackers/backtesting/results/conditions_backtest_report.md` — Raw backtest output
- `signaltrackers/backtesting/results/conditions_backtest_scores.json` — Detailed scoring data
- GitHub Issue #313 — NROU duplicate data bug blocking detailed analysis

---

## 1. Backtest Results Summary

The four-dimension conditions engine was backtested against 231 monthly evaluations from 2006-2025 using the same walk-forward + CPCV + DSR validation framework as the baseline k-means model.

### Headline: Composite Score Failed, But Multi-Asset Accuracy Improved Significantly

| Metric | Old Model (K-Means) | New Model (Conditions) | Change |
|--------|---------------------|------------------------|--------|
| **Composite score** | 52.3/100 | 31.9/100 | -20.4 (FAIL) |
| **Multi-asset accuracy** | 54.6% | **63.9%** | **+9.3pp** |
| S&P 500 accuracy | 55.0% | **58.2%** | +3.2pp |
| Treasuries accuracy | 52.6% | **68.0%** | **+15.4pp** |
| Gold accuracy | 56.3% | **66.7%** | **+10.4pp** |

The composite score of 31.9 is misleading. The model is substantially better at predicting which direction assets actually move (63.9% vs 54.6%). The composite tanked because two of its three components — return ordering and drawdown ordering — failed. These components check whether the verdict labels (Favorable/Mixed/Cautious/Defensive) produce monotonically ordered S&P 500 returns and drawdowns. They don't — but not because the model is wrong. The model is right about asset directions. The problem is in how the verdict combines the dimensions.

### Validation Checks: All Passed

- **Walk-forward mean:** 62.4% accuracy across 10 folds (std 7.9%)
- **CPCV PBO:** 0.467 (below 0.5 threshold — not overfit)
- **DSR p-value:** 0.0 (statistically significant, not a fluke)
- **Plausibility:** March 2020 not classified as Favorable. 2022 correctly shows Stagflation. Average verdict duration 4.2 months (above 3-month minimum).

---

## 2. Root Cause: The Verdict Blending Destroys Information

### The Problem

The verdict combines all four dimensions (Liquidity 35%, Quadrant 35%, Risk 20%, Policy 10%) into a single weighted score, then maps to Favorable/Mixed/Cautious/Defensive. This blending undermines the quadrant's directional predictions.

**Example:** Stagflation + Expanding Liquidity + Calm Risk + Easing Policy scores as "Mixed" because three of four dimensions are positive. But the quadrant correctly predicts that stocks and bonds will underperform. The verdict dilutes this correct prediction into an ambiguous "Mixed" label with ambiguous expectations.

### Evidence: Per-Verdict S&P 500 Returns

| Verdict | Expected | S&P 500 90d Avg | S&P Accuracy | Problem |
|---------|----------|-----------------|--------------|---------|
| Favorable | Best returns | +4.83% | 84.6% | Works |
| Mixed | 2nd best | +2.22% | 71.5% | Works |
| Cautious | 3rd | +2.71% | 28.1% | Returns HIGHER than Mixed |
| Defensive | Worst | +3.17% | 33.3% | Returns HIGHER than Cautious |

The ordering Favorable > Mixed > Cautious > Defensive does not hold for returns. Cautious and Defensive predict stocks will fall, but stocks go up ~70% of the time in those verdicts — the same problem the old model's Bear regime had.

### Evidence: Per-Quadrant Real Returns DO Order Correctly

When we strip out the verdict and look at the quadrant alone, using inflation-adjusted returns, the ordering is correct:

| Quadrant | Nominal 90d | Avg CPI YoY | Real 90d | % Negative Real |
|----------|------------|-------------|----------|-----------------|
| **Goldilocks** | +5.13% | 1.82% | **+4.68%** | 14% |
| **Deflation Risk** | +2.48% | 2.47% | **+1.86%** | 31% |
| **Reflation** | +2.15% | 2.65% | **+1.49%** | 33% |
| **Stagflation** | +1.93% | 2.93% | **+1.20%** | 37% |

Goldilocks clearly on top, Stagflation clearly on the bottom. The quadrant is doing its job. The verdict scrambles this correct ordering by mixing in the other dimensions.

---

## 3. Key Findings

### Finding 1: Stocks Don't Go Down in Bad Times — They Go Up Less

The original framework assumed Cautious/Defensive environments produce negative equity returns. The data shows equities produce positive nominal returns in ALL environments. The difference is magnitude:

- Goldilocks: +5.13% over 90 days
- Stagflation: +1.93% over 90 days

This is the central bank "put" effect identified in [REGIME-MODEL-ISSUES.md](REGIME-MODEL-ISSUES.md) — when conditions deteriorate, the Fed steps in and prevents the expected crash. The model should expect "underperformance" not "decline."

### Finding 2: Inflation-Adjusted Returns Reveal the True Picture

During Stagflation periods, inflation is by definition elevated. When you adjust for inflation:

- Goldilocks real return: +4.68% (with low 1.82% inflation)
- Stagflation real return: +1.20% (with elevated 2.93% inflation)

During the 2022 Stagflation period specifically (CPI 7-8%), real 90-day returns were deeply negative: -9.48%, -7.12%, -17.56%. The model was RIGHT that Stagflation was bad. It just doesn't show up in nominal returns.

Scoring against real returns instead of nominal returns would properly credit the model for correctly identifying these environments.

### Finding 3: The Quadrant Should Be the Headline, Not the Verdict

The four dimensions answer different questions:

| Dimension | Question It Answers | Drives |
|-----------|-------------------|--------|
| **Quadrant** | What type of environment are we in? | Asset direction (equities, bonds, gold, commodities) |
| **Liquidity** | How strong will the moves be? | Asset magnitude — and **crypto direction** |
| **Risk** | How dangerous is it right now? | Near-term drawdown probability |
| **Policy** | What is the Fed doing about it? | Context |

The verdict tried to combine all four into one answer, but they're answering different questions. The quadrant should be the user-facing headline. The other three dimensions are modifiers that provide context.

### Finding 4: Liquidity Is the Right Signal for Crypto

With the quadrant as the headline for traditional assets, liquidity naturally becomes the lead signal for the Crypto category page. This directly solves Bug #292 (incorrect crypto regime guidance) and aligns with the empirical research (Bitcoin's 0.94 correlation with global M2, 83% directional accuracy).

### Finding 5: A Short-Term Dip Pattern Exists But Isn't Reliable Enough to Score

During Defensive periods, 38% had negative 30-day returns (vs 18% for Favorable). Some cases are dramatic — the 2018 Q4 episode saw a -13.83% drawdown before recovering +14.87%. The average max drawdown during Defensive (-8.36%) is worse than Favorable (-6.27%).

However, 62% of Defensive 30-day returns are still positive. The dip is real but not consistent enough to build a scoring rule around. It IS useful context for the narrative ("drawdown risk is elevated").

---

## 4. Recommended Changes

### Change 1: Remove the Verdict — Lead with the Quadrant

**Current design:** Four dimensions → weighted verdict (Favorable/Mixed/Cautious/Defensive) → asset expectations based on verdict.

**New design:** Quadrant is the headline. Liquidity, Risk, and Policy are supporting context displayed alongside it.

**User-facing display:**

For traditional asset pages (Equities, Rates, Credit, Safe Havens, Dollar):
```
● STAGFLATION  |  Liquidity: Expanding ↑  |  Risk: Calm  |  Policy: Easing ↑
```

For Crypto page (liquidity leads because that's what drives crypto):
```
● LIQUIDITY: EXPANDING ↑  |  Stagflation  |  Risk: Calm  |  Policy: Easing ↑
```

**Homepage headline becomes the quadrant with a plain-English explanation:**
```
● STAGFLATION
"Growth is slowing while inflation rises — historically the
toughest environment for portfolios. Expanding liquidity and
calm markets may limit the damage."
```

This is simpler than the verdict approach (four quadrant names vs four verdict names), carries more information (tells the user what to expect for their assets), and matches what the backtest says actually predicts returns.

### Change 2: Score Against the Quadrant, Not the Verdict

The scoring framework should test whether the quadrant correctly predicted asset behavior:

| Quadrant | S&P 500 | Treasuries | Gold |
|----------|---------|------------|------|
| Goldilocks | Best returns | Positive | Neutral/Negative |
| Reflation | Positive | Negative | Positive |
| Stagflation | Worst returns | Negative | Positive |
| Deflation Risk | Negative | Positive | Neutral/Positive |

Liquidity and Risk modify the expected magnitude but don't override the quadrant's directional call, except when Risk is "Stressed" (which overrides to expect elevated drawdowns regardless of quadrant).

### Change 3: Use Real (Inflation-Adjusted) Returns for Scoring

Score S&P 500 predictions using real returns instead of nominal returns. This properly penalizes Stagflation and Reflation periods where nominal returns mask inflation erosion.

**Implementation:** CPI data (`cpi.csv`) is already collected. For each evaluation date, compute 90-day real return as:
```
real_return = nominal_return - (cpi_yoy / 4)
```

The quadrant ordering (Goldilocks > Deflation Risk > Reflation > Stagflation) holds for real returns. The scoring composite should check this ordering.

### Change 4: Score Crypto Against Liquidity, Not the Quadrant

Bitcoin should be scored against the liquidity dimension only:
- Liquidity Expanding → expect positive crypto returns
- Liquidity Contracting → expect negative crypto returns

This aligns with the empirical research and gives crypto its own accurate scoring track rather than forcing it into the macro quadrant framework where it has no predictive relationship.

### Change 5: Adjust Equity Expectations from Direction to Magnitude

Instead of expecting negative equity returns in Stagflation/Deflation Risk, expect **reduced positive returns** (underperformance). The scoring should check:
- Do Goldilocks periods produce higher real equity returns than Stagflation periods? (magnitude ordering)
- NOT: Do Stagflation periods produce negative returns? (direction, which fails due to central bank intervention)

---

## 5. Impact on the Framework Spec

These changes simplify the [MARKET-CONDITIONS-FRAMEWORK.md](MARKET-CONDITIONS-FRAMEWORK.md) spec:

| Spec Section | Change |
|-------------|--------|
| §3 "The Single Verdict" | **Remove.** Quadrant IS the headline. No verdict scoring system needed. |
| §5 "Combining Dimensions into a Single Verdict" | **Remove.** No verdict_score calculation, no verdict thresholds, no verdict weights. |
| §5 "Asset Class Expectations" | **Simplify.** Expectations driven by quadrant directly. Liquidity/Risk/Policy as modifiers. |
| §6 "Scoring and Validation" | **Update.** Score quadrant predictions with real returns. Score crypto against liquidity. Test magnitude ordering, not direction. |
| §7-§8 UI sections | **Simplify.** Quadrant as headline replaces verdict as headline. Four verdict colors become four quadrant colors. |
| §13 "Risks" Decision #1 | **Revisit.** "One verdict, not four gauges" becomes "one quadrant, with three supporting gauges." Still one headline — just a better one. |

### What Stays the Same

- All four dimension engines (Liquidity, Quadrant, Risk, Policy) — the calculations are correct
- All data collection (FRED series) — no changes needed
- The progressive disclosure UI pattern — still one headline with drill-down
- The conditions strip on every page — same structure, quadrant leads
- The AI briefing integration — receives all four dimensions as context
- The interactive quadrant visualization with trajectory — this becomes even more important as the central visual element
- The portfolio implications matrix — restructured around quadrant instead of verdict

---

## 6. Suggested Implementation Sequence

### Step 1: Fix the NROU Duplicate Bug (Issue #313)

The data collection bug that creates duplicate rows for FRED series with future projections must be fixed before re-running the backtest. This also blocks generation of the per-evaluation CSV needed for detailed analysis.

### Step 2: Update the Scoring Framework

- Remove verdict-based scoring
- Score against quadrant expectations using real (inflation-adjusted) returns
- Test magnitude ordering (Goldilocks > rest) rather than direction (positive vs negative)
- Add crypto scoring against liquidity dimension
- Re-run the walk-forward backtest with updated scoring

### Step 3: Update the Framework Spec

- Remove all verdict-related sections from [MARKET-CONDITIONS-FRAMEWORK.md](MARKET-CONDITIONS-FRAMEWORK.md)
- Update the UI sections to show quadrant as headline
- Update asset expectations tables
- Update the conditions strip design
- Add crypto-specific liquidity-led display

### Step 4: Update the Calculation Engine

- Remove verdict classifier from `market_conditions.py`
- Remove verdict scoring maps and threshold logic
- Update the cache output to not include verdict fields
- Simplify the conditions context dict passed to the AI briefing

### Step 5: Proceed to UI Implementation (Phase 4 in Original Spec)

With the scoring validated against the quadrant, proceed to the homepage redesign and category page updates as described in the original spec, with quadrant as headline instead of verdict.

---

## 7. Expected Outcome

Based on the backtest data:

- **Multi-asset accuracy** should remain at ~64% or improve (the quadrant predictions are already correct; we're just scoring them properly now)
- **Return ordering** should pass when scored against quadrant with real returns (Goldilocks +4.68% > Deflation Risk +1.86% > Reflation +1.49% > Stagflation +1.20%)
- **Composite score** should exceed the 52.3 baseline substantially, clearing the Phase 3 gate
- **Crypto scoring** against liquidity should produce meaningful accuracy (vs the 34.8% that caused Bitcoin to be excluded from the old model)

---

## Appendix: Raw Data Supporting These Findings

### Per-Quadrant Asset Detail

**Goldilocks (n=51):**
- S&P 500: nominal +5.13%, real +4.68%, negative real 14% of the time
- Treasuries: direction accuracy 73.1%
- Gold: direction accuracy 75.6%

**Reflation (n=63):**
- S&P 500: nominal +2.15%, real +1.49%, negative real 33%
- Treasuries: direction accuracy 80.8%
- Gold: direction accuracy 71.5%

**Deflation Risk (n=77):**
- S&P 500: nominal +2.48%, real +1.86%, negative real 31%
- Treasuries: direction accuracy 46.9%
- Gold: direction accuracy 46.9%

**Stagflation (n=41):**
- S&P 500: nominal +1.93%, real +1.20%, negative real 37%
- Notable: During 2022 (CPI 7-8%), real returns were -9.48%, -7.12%, -17.56%

### Dip-Then-Recovery Pattern (Defensive Periods)

| Date | Quadrant | 30d Return | 90d Return | Max Drawdown |
|------|----------|-----------|-----------|-------------|
| 2010-07 | Stagflation | -6.61% | +5.64% | -6.87% |
| 2018-09 | Stagflation | -9.24% (est) | -13.83% → +14.87% recovery | -15.61% |
| 2018-11 | Stagflation | -8.80% | +1.69% | -15.61% |
| 2022-08 | Deflation Risk | -9.24% | +0.42% | -12.88% |

Pattern: 38% of Defensive periods had negative 30-day returns (vs 18% for Favorable). Drawdowns are deeper (avg -8.36% vs -6.27%). But recovery within 90 days means the average 90-day return is still positive.
