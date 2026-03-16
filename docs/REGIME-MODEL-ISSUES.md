# Macro Regime Model: Structural Issues & Opportunity

## Overview

Backtesting the current k-means regime classifier against 25 years of historical data (2000–2025) revealed structural limitations that cap its predictive accuracy. The composite score of **52.3/100** — barely above random — is not primarily a tuning problem. The model's assumptions about how asset classes behave in each regime are misaligned with how modern markets actually work.

This document catalogs the specific issues identified, the evidence from backtesting, and the opportunity to build a better model.

---

## Current Model

- **Method:** K-means clustering on 5 FRED indicators (HY spread, yield curve 10Y-2Y, NFCI, initial claims, fed funds rate)
- **Regimes:** Bull, Neutral, Bear, Recession Watch
- **Assumptions:** Each regime implies directional expectations for equities, bonds, and gold based on classical macro relationships

### Backtest Results (Baseline)

| Metric | Score |
|--------|-------|
| **Composite** | 52.3/100 |
| Multi-asset accuracy | 54.6% |
| S&P 500 accuracy | 55.0% |
| Treasuries (TLT) accuracy | 52.6% |
| Gold accuracy | 56.3% |

#### Per-Regime Breakdown

| Regime | Count | Accuracy | Key Problem |
|--------|-------|----------|-------------|
| Bull (n=81) | 26% | 45.2% | Treasuries and gold moved *opposite* to expectations (both rose) |
| Neutral (n=78) | 25% | 80.4% | Best performer — "neutral expects range-bound" is a forgiving bar |
| Bear (n=97) | 31% | 47.5% | S&P 500 rose 67% of the time during "Bear" classifications |
| Recession Watch (n=54) | 17% | 44.4% | All three assets underperformed expectations |

**Notable:** The model classified Bear regime 97 times (the most frequent), yet equities posted positive 90-day returns in two-thirds of those periods. This is not a calibration issue — it reflects a fundamental mismatch between the model's bear signal and actual market outcomes.

---

## Structural Issues

### 1. Central Bank Intervention Reverses Expected Outcomes

**The problem:** The model treats deteriorating macro indicators as bearish for risk assets, but post-2008 central banks respond to weakness with aggressive stimulus that *supports* risk assets. The worse the data, the stronger the policy response — and the better equities perform.

**Evidence:**
- Bear regime: S&P 500 averaged +1.96% over 90 days (positive, not negative)
- Recession Watch → Bear transition (2009-08-31): S&P 500 returned +7.81% over 90 days
- Bear → Recession Watch transition (2020-03-31): S&P 500 returned +18.64% over 90 days

**Why it matters:** The classical macro playbook assumed markets were driven by economic fundamentals. In the post-GFC era, the dominant driver is often the *anticipation* of policy response. A model that doesn't account for the central bank "put" will systematically misread risk environments.

### 2. Gold's Secular Uptrend Breaks Counter-Cyclical Assumptions

**The problem:** The model expects gold to decline in Bull regimes (risk-on) and rise in Bear/Recession Watch (risk-off). In reality, gold has risen in nearly all regimes over the past 25 years — driven by secular forces (central bank buying, de-dollarization, real yield suppression) that overwhelm cyclical macro signals.

**Evidence:**
- Bull regime: Gold expected negative, actual 90d avg = **+1.32%** (accuracy only 34.6%)
- Bear regime: Gold expected positive, actual 90d avg = **+3.72%** (accuracy 61.9% — one of the few regime calls that works)
- Recession Watch: Gold expected positive, actual 90d avg = **+2.94%** (accuracy only 46.3%)

Gold rose in 3 of 4 regimes, making the "expect negative in Bull" assumption consistently wrong. The model treats gold as a pure risk-off hedge, but gold has become a structural bid regardless of macro regime.

### 3. Stock-Bond Correlation Flip

**The problem:** The model assumes bonds rally when stocks fall (negative correlation) — the classic "flight to safety" trade. This relationship held from ~1998–2021 but broke down in 2022 when inflation forced the Fed to raise rates aggressively. Stocks and bonds fell together, violating the model's core diversification assumption.

**Evidence:**
- Bull → Bear transition (2022-03-31): S&P 500 returned **-15.42%** and Treasuries returned **-13.35%** — both fell sharply
- The model would have expected Treasuries to rally as a safe haven during equity weakness
- This simultaneous decline scored only 38% accuracy at that transition

**Why it matters:** In inflation-driven environments, the traditional stock-bond correlation inverts. The current model has no mechanism to distinguish between demand-driven downturns (where bonds rally) and inflation-driven downturns (where bonds fall alongside stocks). A 4-regime model that assumes bonds are always the hedge is structurally incomplete.

### 4. No Distinction Between Demand-Side and Supply/Inflation Crises

**The problem:** The model treats all bearish environments identically. But the macro playbook is completely different depending on the *cause* of the downturn:

| Crisis Type | Equities | Bonds | Gold | Fed Response |
|------------|----------|-------|------|-------------|
| Demand shock (2008, 2020) | Down | Up (flight to safety) | Up | Cut rates, QE |
| Inflation/supply shock (2022) | Down | Down (rates rising) | Up then mixed | Raise rates, QT |
| Stagflation (1970s-style) | Down | Down | Up | Conflicted |

The current model's 4 regimes (Bull/Neutral/Bear/Recession Watch) cannot distinguish these scenarios. Bear is Bear — whether it's a demand collapse or an inflation crisis — yet the correct portfolio positioning is opposite in each case.

**Evidence:** The model's Bear regime accuracy of 47.5% is a blended average of "sometimes right" (demand shocks where bonds rallied as expected) and "completely wrong" (inflation shocks where bonds fell alongside stocks).

---

## Bitcoin Exclusion

Backtesting initially included Bitcoin in the scoring model. It scored **34.8% accuracy** — worse than a coin flip — and was removed from the scoring framework.

Deep research confirmed Bitcoin is not meaningfully driven by macro regime state. Its primary drivers are:

1. **Global liquidity (M2 money supply):** ~0.94 correlation with a ~90-day lag (Lyn Alden research, Raoul Pal/Global Macro Investor)
2. **Halving supply cycles:** 4-year cycles dominating price structure (NY Fed Staff Report 1052)
3. **Idiosyncratic crypto market dynamics:** Exchange events, regulatory actions, adoption curves

The dashboard was providing incorrect regime guidance for crypto — telling users Bitcoin would "face outsized drawdown risk" in Bear and suffer "severe drawdowns" in Recession Watch, when the actual driver is liquidity conditions that don't map to macro regimes. This is tracked as **Bug #292** for correction in Phase 9.

Bitcoin may be evaluated by a future regime model if the model explicitly incorporates liquidity conditions, but it should not be scored against the current macro-regime framework.

---

## The Opportunity

The structural issues above are not unique to our implementation — they reflect real shifts in how markets function. This creates an opportunity: **a regime model that accounts for these realities would have a significant edge over classical macro frameworks.**

### What a Better Model Might Account For

1. **Central bank policy stance as a first-class input** — Not just the fed funds rate level, but the *direction* and *pace* of change. Markets price forward; a model that captures the transition from tightening to easing (or vice versa) would better anticipate regime shifts.

2. **Inflation regime as a separate dimension** — Instead of 4 regimes on a single bull-to-bear axis, the model could incorporate an inflation dimension: {low inflation, rising inflation, high inflation, falling inflation} × {expansion, contraction}. This would distinguish 2008-style crashes (buy bonds) from 2022-style crashes (avoid bonds).

3. **Adaptive asset expectations** — Rather than hardcoding "bonds rally in Bear," the model could learn time-varying relationships. The stock-bond correlation itself could be an input signal (when it flips positive, the regime playbook changes).

4. **Secular trend adjustment for gold** — Gold's structural bid (central bank buying, de-dollarization) could be accounted for by modeling gold relative to its own trend rather than assuming it behaves counter-cyclically.

5. **Liquidity conditions** — M2 growth rate, Fed balance sheet changes, and global liquidity proxies could improve the model's ability to predict risk asset behavior, especially for crypto and growth stocks.

### Implementation Path

The automated research loop documented in [REGIME-BACKTEST-STRATEGY.md](REGIME-BACKTEST-STRATEGY.md) is designed to systematically explore these improvements:

1. **Walk-forward expanding window** validation prevents overfitting to any single era
2. **CPCV + Deflated Sharpe Ratio** protects against multiple-hypothesis testing
3. **Standard method interface** allows testing fundamentally different approaches (supervised models, threshold-based rules, HMMs, ensemble methods) on equal footing
4. **Multi-asset scoring** evaluates whether the model actually predicts cross-asset behavior, not just equity direction

The baseline score of 52.3/100 is the bar to beat. Given the structural issues identified, there is meaningful room for improvement — particularly in Bear and Recession Watch regimes where accuracy is currently below 50%.

---

## Related Documents

- [REGIME-BACKTEST-STRATEGY.md](REGIME-BACKTEST-STRATEGY.md) — Full automated optimization strategy with implementation checklist
- [GitHub Bug #292](https://github.com/EricMaibach/financial/issues/292) — Incorrect crypto regime guidance in dashboard
- `signaltrackers/backtesting/results/backtest_report.md` — Full backtest results
- `signaltrackers/backtesting/regime_backtest.py` — Backtest implementation
- `signaltrackers/regime_detection.py` — Current k-means production classifier
- `signaltrackers/regime_config.py` — Regime metadata and expectations
