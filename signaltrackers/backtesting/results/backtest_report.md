# Macro Regime Backtest Report

Generated: 2026-03-16 08:15:06
Evaluation period: 2000-01-31 to 2025-10-31
Total evaluations: 310

## Overall Composite Score: 52.3/100

Components:
- Multi-asset accuracy (50% weight): 54.6%
- Drawdown ordering Bull→Recession Watch (25% weight): PASS
- S&P 500 return ordering Bull→Recession Watch (25% weight): FAIL

## Per-Asset Accuracy

How often each asset moved in the direction the regime predicted.

| Asset | Weight | Accuracy | Evaluations |
|-------|--------|----------|-------------|
| S&P 500 | 38% | 55.0% | 310 |
| Treasuries (TLT) | 31% | 52.6% | 310 |
| Gold | 31% | 56.3% | 310 |

## Per-Regime Summary

| Regime | Count | Multi-Asset Accuracy | S&P 500 Avg 90d | S&P 500 Avg Max DD |
|--------|-------|---------------------|-----------------|-------------------|
| Bull | 81 | 45.2% | 3.14% | -6.3% |
| Neutral | 78 | 80.4% | 3.4% | -6.49% |
| Bear | 97 | 47.5% | 1.96% | -8.07% |
| Recession Watch | 54 | 44.4% | -0.26% | -11.02% |

## Per-Regime Asset Detail

### Bull (n=81)
- **S&P 500** (expect positive): accuracy=69.1% | 30d avg=1.06%, 60d avg=2.03%, 90d avg=3.14%
- **Treasuries (TLT)** (expect negative): accuracy=27.2% | 30d avg=0.76%, 60d avg=1.75%, 90d avg=2.51%
- **Gold** (expect negative): accuracy=34.6% | 30d avg=0.52%, 60d avg=1.04%, 90d avg=1.32%
- **S&P 500 Max Drawdown (90d)**: avg=-6.3%, worst=-17.07%

### Neutral (n=78)
- **S&P 500** (expect neutral): accuracy=75.0% | 30d avg=1.22%, 60d avg=2.48%, 90d avg=3.4%
- **Treasuries (TLT)** (expect neutral): accuracy=88.5% | 30d avg=-0.18%, 60d avg=-0.28%, 90d avg=-0.3%
- **Gold** (expect neutral): accuracy=78.8% | 30d avg=0.54%, 60d avg=1.07%, 90d avg=1.61%
- **S&P 500 Max Drawdown (90d)**: avg=-6.49%, worst=-27.66%

### Bear (n=97)
- **S&P 500** (expect negative): accuracy=33.0% | 30d avg=0.47%, 60d avg=1.09%, 90d avg=1.96%
- **Treasuries (TLT)** (expect positive): accuracy=50.5% | 30d avg=0.18%, 60d avg=0.51%, 90d avg=0.72%
- **Gold** (expect positive): accuracy=61.9% | 30d avg=0.91%, 60d avg=2.25%, 90d avg=3.72%
- **S&P 500 Max Drawdown (90d)**: avg=-8.07%, worst=-33.72%

### Recession Watch (n=54)
- **S&P 500** (expect negative): accuracy=44.4% | 30d avg=0.17%, 60d avg=0.15%, 90d avg=-0.26%
- **Treasuries (TLT)** (expect positive): accuracy=42.6% | 30d avg=0.2%, 60d avg=0.75%, 90d avg=0.99%
- **Gold** (expect positive): accuracy=46.3% | 30d avg=1.07%, 60d avg=2.03%, 90d avg=2.94%
- **S&P 500 Max Drawdown (90d)**: avg=-11.02%, worst=-40.71%

## Confidence Level Performance

| Confidence | Count | Multi-Asset Accuracy |
|------------|-------|---------------------|
| Medium | 207 | 53.5% |
| Low | 103 | 57.0% |

## Regime Transitions (25 total)

Transition directional accuracy: 52.0%
(When shifting bearish, did S&P 500 decline? When shifting bullish, did it rise?)

| Date | From | To | Score | S&P 500 90d | Treasuries (TLT) 90d | Gold 90d |
|------|------|----|-------|------------|------------|------------|
| 2001-04-30 | Recession Watch | Bear | 38% | -4.32% | 0.00% | 0.00% |
| 2001-09-30 | Bear | Neutral | 81% | 10.00% | 0.00% | 0.00% |
| 2003-06-30 | Neutral | Bull | 69% | 3.78% | -4.97% | 0.00% |
| 2005-05-31 | Bull | Neutral | 100% | 2.26% | 0.65% | 4.61% |
| 2006-05-31 | Neutral | Bear | 31% | 2.86% | 5.99% | -5.12% |
| 2007-08-31 | Bear | Recession Watch | 62% | 0.20% | 8.03% | 17.68% |
| 2009-08-31 | Recession Watch | Bear | 62% | 7.81% | 0.99% | 23.81% |
| 2009-11-30 | Bear | Neutral | 84% | 2.32% | -4.20% | -5.37% |
| 2009-12-31 | Neutral | Bull | 38% | 5.42% | 0.24% | 1.53% |
| 2012-05-31 | Bull | Neutral | 66% | 8.19% | -1.19% | 5.92% |
| 2013-11-30 | Neutral | Bull | 38% | 3.75% | 5.68% | 8.54% |
| 2014-12-31 | Bull | Bear | 62% | 0.88% | 4.20% | 0.07% |
| 2016-01-31 | Bear | Recession Watch | 62% | 7.95% | 1.51% | 14.06% |
| 2017-02-28 | Recession Watch | Bear | 62% | 2.57% | 2.56% | 0.76% |
| 2017-04-30 | Bear | Neutral | 100% | 3.89% | 2.87% | 0.90% |
| 2018-04-30 | Neutral | Bear | 31% | 6.31% | 0.64% | -7.18% |
| 2019-01-31 | Bear | Neutral | 81% | 8.58% | 2.47% | -3.49% |
| 2019-03-31 | Neutral | Bear | 62% | 3.94% | 6.98% | 7.48% |
| 2020-03-31 | Bear | Recession Watch | 62% | 18.64% | 0.26% | 12.55% |
| 2020-05-31 | Recession Watch | Neutral | 66% | 14.82% | 0.17% | 12.94% |
| 2020-10-31 | Neutral | Bear | 0% | 12.55% | -3.95% | -2.98% |
| 2020-11-30 | Bear | Bull | 100% | 8.06% | -11.46% | -3.08% |
| 2022-03-31 | Bull | Bear | 38% | -15.42% | -13.35% | -6.18% |
| 2025-03-31 | Bear | Neutral | 66% | 10.78% | -1.98% | 5.79% |
| 2025-10-31 | Neutral | Bear | 31% | 2.06% | -1.88% | 34.71% |