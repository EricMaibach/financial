# Market Conditions Backtest Report

Generated: 2026-03-17 08:09:19
Evaluation period: 2006-08-31 to 2025-10-31
Total evaluations: 231
Baseline (k-means): 52.3/100

## Overall Composite Score: 31.9/100 (FAIL: -20.4 vs baseline)

Components:
- Multi-asset accuracy (50% weight): 63.9%
- Drawdown ordering Favorable→Defensive (25% weight): FAIL
- S&P 500 return ordering Favorable→Defensive (25% weight): FAIL

## Walk-Forward Validation

- Mean fold score: 62.4%
- Std deviation: 7.9%
- Sharpe-like ratio: 7.86
- Number of folds: 10

| Fold | Period | Evaluations | Score |
|------|--------|-------------|-------|
| 1 | 2005-01-01 to 2006-12-31 | 5 | 50.0% |
| 2 | 2007-01-01 to 2008-12-31 | 24 | 62.2% |
| 3 | 2009-01-01 to 2010-12-31 | 24 | 62.6% |
| 4 | 2011-01-01 to 2012-12-31 | 24 | 72.3% |
| 5 | 2013-01-01 to 2014-12-31 | 24 | 65.5% |
| 6 | 2015-01-01 to 2016-12-31 | 24 | 53.5% |
| 7 | 2017-01-01 to 2018-12-31 | 24 | 73.8% |
| 8 | 2019-01-01 to 2020-12-31 | 24 | 69.0% |
| 9 | 2021-01-01 to 2022-12-31 | 24 | 55.6% |
| 10 | 2023-01-01 to 2024-12-31 | 24 | 59.6% |

## Per-Asset Accuracy

| Asset | Weight | Accuracy | Evaluations |
|-------|--------|----------|-------------|
| S&P 500 | 38% | 58.2% | 231 |
| Treasuries (TLT) | 31% | 68.0% | 231 |
| Gold | 31% | 66.7% | 231 |

## Per-Verdict Summary

| Verdict | Count | Multi-Asset Accuracy | S&P 500 Avg 90d | S&P 500 Avg Max DD |
|---------|-------|---------------------|-----------------|-------------------|
| Favorable | 39 | 78.2% | 4.83% | -6.27% |
| Mixed | 107 | 74.4% | 2.22% | -8.5% |
| Cautious | 64 | 39.8% | 2.71% | -6.41% |
| Defensive | 21 | 57.1% | 3.17% | -8.36% |

## Per-Verdict Asset Detail

### Favorable (n=39)
- **S&P 500**: accuracy=84.6% | 30d avg=2.77%, 60d avg=4.25%, 90d avg=4.83%
- **Treasuries (TLT)**: accuracy=73.1% | 30d avg=-0.07%, 60d avg=0.31%, 90d avg=1.12%
- **Gold**: accuracy=75.6% | 30d avg=-0.22%, 60d avg=0.18%, 90d avg=1.35%

### Mixed (n=107)
- **S&P 500**: accuracy=71.5% | 30d avg=0.31%, 60d avg=1.12%, 90d avg=2.22%
- **Treasuries (TLT)**: accuracy=80.8% | 30d avg=0.86%, 60d avg=1.72%, 90d avg=2.15%
- **Gold**: accuracy=71.5% | 30d avg=1.62%, 60d avg=3.22%, 90d avg=4.42%

### Cautious (n=64)
- **S&P 500**: accuracy=28.1% | 30d avg=1.1%, 60d avg=1.98%, 90d avg=2.71%
- **Treasuries (TLT)**: accuracy=46.9% | 30d avg=-0.67%, 60d avg=-0.57%, 90d avg=-1.15%
- **Gold**: accuracy=46.9% | 30d avg=0.14%, 60d avg=0.42%, 90d avg=0.71%

### Defensive (n=21)
- **S&P 500**: accuracy=33.3% | 30d avg=0.73%, 60d avg=1.67%, 90d avg=3.17%
- **Treasuries (TLT)**: accuracy=57.1% | 30d avg=0.32%, 60d avg=0.0%, 90d avg=0.98%
- **Gold**: accuracy=85.7% | 30d avg=1.19%, 60d avg=2.42%, 90d avg=4.01%

## Economic Plausibility Checks

**Overall: PASS**

- **march_2020_not_favorable**: PASS
  - dominant_verdict: Mixed
  - verdicts_found: ['Mixed', 'Favorable']
  - verdict_distribution: {'Mixed': 1, 'Favorable': 1}
- **2022_stagflation_present**: PASS
  - quadrants_found: ['Deflation Risk', 'Stagflation']
  - quadrant_distribution: {'Deflation Risk': 8, 'Stagflation': 4}
- **verdict_stability**: PASS
  - avg_duration_months: 4.2
  - total_transitions: 54
  - min_duration: 1
  - max_duration: 21

## Combinatorial Purged Cross-Validation (CPCV)

- PBO (Probability of Backtest Overfitting): 0.467 (PASS)
- Number of paths tested: 15
- OOS mean accuracy: 63.9%
- OOS std: 2.4%
- IS mean accuracy: 64.0%

## Deflated Sharpe Ratio (DSR)

- DSR z-score: 42.4204
- p-value: 0.0 (SIGNIFICANT)
- Observed Sharpe: 7.86
- Expected max Sharpe (null): 0.6858
- Number of trials corrected for: 7

## Weight Sensitivity Analysis

| Configuration | Composite | Multi-Asset | WF Mean | WF Std | WF Sharpe | DD Order | Ret Order |
|---------------|-----------|-------------|---------|--------|-----------|----------|-----------|
| Default (35/35/20/10) | 31.9 | 63.9% | 62.4% | 7.9% | 7.86 | FAIL | FAIL |
| Liquidity-heavy (40/30/20/10) | 31.9 | 63.7% | 62.3% | 7.9% | 7.89 | FAIL | FAIL |
| Quadrant-heavy (30/40/20/10) | 31.4 | 62.8% | 61.3% | 7.7% | 7.92 | FAIL | FAIL |
| Risk+Policy up (30/30/25/15) | 32.5 | 65.1% | 63.6% | 7.0% | 9.11 | FAIL | FAIL |
| Risk-heavy (25/25/30/20) | 32.4 | 64.8% | 65.9% | 8.1% | 8.11 | FAIL | FAIL |
| Macro-dominant (40/40/10/10) | 30.9 | 61.9% | 60.4% | 7.2% | 8.44 | FAIL | FAIL |
| Low-policy (35/35/25/5) | 31.2 | 62.4% | 61.1% | 7.7% | 7.98 | FAIL | FAIL |

**Recommended configuration:** Risk+Policy up (30/30/25/15)
- Rationale: Highest walk-forward Sharpe ratio (9.11)
- Weights: Liq=0.3, Quad=0.3, Risk=0.25, Policy=0.15

## Final Recommendation

**FAIL: Composite score 31.9/100 does not beat baseline 52.3/100.**

DO NOT proceed to Phase 11. Investigate and iterate on the conditions engine.