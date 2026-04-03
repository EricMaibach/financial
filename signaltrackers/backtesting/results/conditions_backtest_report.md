# Market Conditions Backtest Report (Quadrant-Led)

Generated: 2026-04-03 09:01:38
Evaluation period: 2005-01-31 to 2025-12-31
Total evaluations: 252
Baseline (k-means): 52.3/100

Scoring: S&P 500 uses real (inflation-adjusted) returns. Treasuries and Gold use nominal directional accuracy.

## Overall Composite Score: 27.8/100 (FAIL: -24.5 vs baseline)

Components:
- Multi-asset accuracy (50% weight): 55.5%
- Real return magnitude ordering Goldilocks→Stagflation (25% weight): FAIL
- Drawdown ordering Goldilocks→Stagflation (25% weight): FAIL

## Walk-Forward Validation

- Mean fold score: 54.4%
- Std deviation: 7.5%
- Sharpe-like ratio: 7.21
- Number of folds: 10

| Fold | Period | Evaluations | Score |
|------|--------|-------------|-------|
| 1 | 2005-01-01 to 2006-12-31 | 24 | 45.2% |
| 2 | 2007-01-01 to 2008-12-31 | 24 | 46.2% |
| 3 | 2009-01-01 to 2010-12-31 | 24 | 55.6% |
| 4 | 2011-01-01 to 2012-12-31 | 24 | 47.5% |
| 5 | 2013-01-01 to 2014-12-31 | 24 | 48.8% |
| 6 | 2015-01-01 to 2016-12-31 | 24 | 51.3% |
| 7 | 2017-01-01 to 2018-12-31 | 24 | 64.1% |
| 8 | 2019-01-01 to 2020-12-31 | 24 | 64.5% |
| 9 | 2021-01-01 to 2022-12-31 | 24 | 59.2% |
| 10 | 2023-01-01 to 2024-12-31 | 24 | 61.7% |

## Per-Asset Accuracy

| Asset | Weight | Accuracy | Evaluations |
|-------|--------|----------|-------------|
| S&P 500 | 38% | 50.0% | 252 |
| Treasuries (TLT) | 31% | 50.8% | 252 |
| Gold | 31% | 66.7% | 252 |

## Per-Quadrant Summary

| Quadrant | Count | Multi-Asset Accuracy | S&P 500 Real Avg 90d | S&P 500 Avg Max DD |
|----------|-------|---------------------|----------------------|-------------------|
| Goldilocks | 69 | 70.4% | 4.15% | -6.63% |
| Deflation Risk | 47 | 48.1% | 3.79% | -7.24% |
| Reflation | 45 | 56.0% | 0.48% | -8.43% |
| Stagflation | 91 | 47.7% | 0.61% | -7.23% |

## Per-Quadrant Asset Detail

### Goldilocks (n=69)
- **S&P 500** (expect positive): accuracy=79.7% | 30d avg=1.64%, 60d avg=3.2%, 90d avg=4.57%, real 90d avg=4.15%
- **Treasuries (TLT)** (expect positive): accuracy=56.5% | 30d avg=0.0%, 60d avg=0.34%, 90d avg=0.43%
- **Gold** (expect neutral): accuracy=73.2% | 30d avg=0.93%, 60d avg=2.29%, 90d avg=3.12%

### Deflation Risk (n=47)
- **S&P 500** (expect negative): accuracy=19.1% | 30d avg=1.33%, 60d avg=2.55%, 90d avg=4.04%, real 90d avg=3.79%
- **Treasuries (TLT)** (expect positive): accuracy=59.6% | 30d avg=0.27%, 60d avg=0.64%, 90d avg=0.88%
- **Gold** (expect neutral): accuracy=71.3% | 30d avg=1.38%, 60d avg=2.76%, 90d avg=3.94%

### Reflation (n=45)
- **S&P 500** (expect positive): accuracy=62.2% | 30d avg=0.53%, 60d avg=0.76%, 90d avg=1.31%, real 90d avg=0.48%
- **Treasuries (TLT)** (expect negative): accuracy=28.9% | 30d avg=1.16%, 60d avg=2.56%, 90d avg=4.02%
- **Gold** (expect positive): accuracy=75.6% | 30d avg=2.1%, 60d avg=4.52%, 90d avg=6.49%

### Stagflation (n=91)
- **S&P 500** (expect negative): accuracy=37.4% | 30d avg=0.46%, 60d avg=1.09%, 90d avg=1.55%, real 90d avg=0.61%
- **Treasuries (TLT)** (expect negative): accuracy=52.7% | 30d avg=-0.13%, 60d avg=0.01%, 90d avg=-0.15%
- **Gold** (expect positive): accuracy=54.9% | 30d avg=0.3%, 60d avg=0.69%, 90d avg=1.14%

## Economic Plausibility Checks

**Overall: FAIL**

- **march_2020_not_goldilocks**: FAIL
  - dominant_quadrant: Goldilocks
  - quadrants_found: ['Goldilocks']
  - quadrant_distribution: {'Goldilocks': 2}
- **2022_stagflation_present**: PASS
  - quadrants_found: ['Stagflation']
  - quadrant_distribution: {'Stagflation': 12}
- **quadrant_stability**: PASS
  - avg_duration_months: 7.2
  - total_transitions: 34
  - min_duration: 2
  - max_duration: 23

## Combinatorial Purged Cross-Validation (CPCV)

- PBO (Probability of Backtest Overfitting): 0.467 (PASS)
- Number of paths tested: 15
- OOS mean accuracy: 55.5%
- OOS std: 4.9%
- IS mean accuracy: 55.6%

## Deflated Sharpe Ratio (DSR)

- DSR z-score: 48.219
- p-value: 0.0 (SIGNIFICANT)
- Observed Sharpe: 7.21
- Expected max Sharpe (null): 0.3196
- Number of trials corrected for: 3

## Risk Filter Sensitivity Analysis

| Configuration | Composite | Multi-Asset | WF Mean | WF Std | WF Sharpe | DD Order | Ret Order |
|---------------|-----------|-------------|---------|--------|-----------|----------|-----------|
| No risk filter (quadrant only) | 27.8 | 55.5% | 54.4% | 7.5% | 7.21 | FAIL | FAIL |
| Stressed override (default) | 27.8 | 55.5% | 54.4% | 7.5% | 7.21 | FAIL | FAIL |
| Elevated+Stressed override | 27.2 | 54.4% | 53.6% | 6.9% | 7.73 | FAIL | FAIL |

**Recommended configuration:** Elevated+Stressed override
- Rationale: Highest walk-forward Sharpe ratio (7.73)

## Final Recommendation

**FAIL: Composite score 27.8/100 does not beat baseline 52.3/100.**
Economic plausibility checks failed.

DO NOT proceed to Phase 11. Investigate and iterate on the conditions engine.