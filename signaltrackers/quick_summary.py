#!/usr/bin/env python3
"""Quick summary of credit market data"""

import pandas as pd
from pathlib import Path

data_dir = Path("data")

print("\n" + "="*70)
print("CREDIT MARKET SIGNALS SUMMARY")
print("="*70)

# High Yield Spread
hy_df = pd.read_csv(data_dir / "high_yield_spread.csv")
hy_start = hy_df.iloc[0]['high_yield_spread']
hy_current = hy_df.iloc[-1]['high_yield_spread']
hy_change = hy_current - hy_start

print(f"\n📊 HIGH-YIELD CREDIT SPREAD")
print(f"   Current: {hy_current:.2f}% ({int(hy_current*100)} bp)")
print(f"   30-day change: {hy_change:+.2f}% ({int(hy_change*100):+d} bp)")
print(f"   Trend: {'↓ TIGHTENING' if hy_change < 0 else '↑ WIDENING'}")
print(f"   Assessment: {'🟢 Very tight - strong credit' if hy_current < 3.0 else '⚠️ Elevated'}")

# Investment Grade Spread
ig_df = pd.read_csv(data_dir / "investment_grade_spread.csv")
ig_start = ig_df.iloc[0]['investment_grade_spread']
ig_current = ig_df.iloc[-1]['investment_grade_spread']
ig_change = ig_current - ig_start

print(f"\n📊 INVESTMENT GRADE SPREAD")
print(f"   Current: {ig_current:.2f}% ({int(ig_current*100)} bp)")
print(f"   30-day change: {ig_change:+.2f}% ({int(ig_change*100):+d} bp)")
print(f"   Trend: {'→ STABLE' if abs(ig_change) < 0.03 else ('↓ TIGHTENING' if ig_change < 0 else '↑ WIDENING')}")
print(f"   Assessment: {'🟢 Extremely tight - no stress' if ig_current < 1.0 else '⚠️ Elevated'}")

# CCC Spread
ccc_df = pd.read_csv(data_dir / "ccc_spread.csv")
ccc_start = ccc_df.iloc[0]['ccc_spread']
ccc_current = ccc_df.iloc[-1]['ccc_spread']
ccc_change = ccc_current - ccc_start

print(f"\n📊 CCC-RATED SPREAD")
print(f"   Current: {ccc_current:.2f}% ({int(ccc_current*100)} bp)")
print(f"   30-day change: {ccc_change:+.2f}% ({int(ccc_change*100):+d} bp)")
print(f"   Trend: {'↓ IMPROVING' if ccc_change < 0 else '↑ DETERIORATING'}")

# CCC/HY Ratio
ratio = ccc_current / hy_current
print(f"   CCC/HY Ratio: {ratio:.2f}x")
print(f"   Assessment: {'⚠️ Distressed lagging' if ratio > 3.0 else '🟢 Normal dispersion'}")

# Leveraged Loans
bkln_df = pd.read_csv(data_dir / "leveraged_loan_etf.csv")
bkln_start = bkln_df.iloc[0]['leveraged_loan_price']
bkln_current = bkln_df.iloc[-1]['leveraged_loan_price']
bkln_change_pct = ((bkln_current - bkln_start) / bkln_start) * 100

print(f"\n📊 LEVERAGED LOANS (BKLN)")
print(f"   Current: ${bkln_current:.2f}")
print(f"   30-day change: {bkln_change_pct:+.2f}%")
print(f"   Trend: {'↑ RISING' if bkln_change_pct > 0 else '↓ FALLING'}")
print(f"   Assessment: {'🟢 Strong performance' if bkln_change_pct > 0 else '🔴 Weakness'}")

# HYG ETF
hyg_df = pd.read_csv(data_dir / "high_yield_credit_etf.csv")
hyg_start = hyg_df.iloc[0]['high_yield_credit_price']
hyg_current = hyg_df.iloc[-1]['high_yield_credit_price']
hyg_change_pct = ((hyg_current - hyg_start) / hyg_start) * 100

print(f"\n📊 HIGH YIELD ETF (HYG)")
print(f"   Current: ${hyg_current:.2f}")
print(f"   30-day change: {hyg_change_pct:+.2f}%")
print(f"   Trend: {'↑ RISING' if hyg_change_pct > 0 else '↓ FALLING'}")

# LQD ETF
lqd_df = pd.read_csv(data_dir / "investment_grade_credit_etf.csv")
lqd_start = lqd_df.iloc[0]['investment_grade_credit_price']
lqd_current = lqd_df.iloc[-1]['investment_grade_credit_price']
lqd_change_pct = ((lqd_current - lqd_start) / lqd_start) * 100

print(f"\n📊 INVESTMENT GRADE ETF (LQD)")
print(f"   Current: ${lqd_current:.2f}")
print(f"   30-day change: {lqd_change_pct:+.2f}%")
print(f"   Trend: {'↑ RISING' if lqd_change_pct > 0 else '↓ FALLING'}")

# Overall Assessment
print(f"\n" + "="*70)
print("OVERALL MARKET ASSESSMENT")
print("="*70)

stress_score = 0
if hy_current > 5.0:
    stress_score += 3
elif hy_current > 4.0:
    stress_score += 2
elif hy_current > 3.0:
    stress_score += 1

if ig_current > 2.0:
    stress_score += 3
elif ig_current > 1.5:
    stress_score += 2
elif ig_current > 1.0:
    stress_score += 1

if ratio > 3.5:
    stress_score += 2
elif ratio > 3.0:
    stress_score += 1

if hy_change > 0.5:
    stress_score += 2
elif hy_change > 0.25:
    stress_score += 1

if stress_score == 0:
    status = "🟢 BENIGN - No stress detected"
    desc = "Credit markets are healthy with tight spreads and stable conditions."
elif stress_score <= 2:
    status = "🟡 WATCH - Minor concerns"
    desc = "Some metrics showing caution signals but overall market remains stable."
elif stress_score <= 4:
    status = "🟠 CAUTION - Elevated stress"
    desc = "Multiple indicators showing stress. Monitor closely."
else:
    status = "🔴 STRESS - Significant concerns"
    desc = "Credit markets under pressure. Risk-off conditions."

print(f"\nCredit Market Status: {status}")
print(f"\n{desc}")

print(f"\nKey Insights:")
print(f"  • Spreads are {'compressed' if hy_current < 3.5 else 'elevated'} - {'low' if hy_current < 3.5 else 'high'} default risk priced in")
print(f"  • Trend is {'positive (tightening)' if hy_change < -0.05 else ('negative (widening)' if hy_change > 0.05 else 'neutral (stable)')}")
print(f"  • Distressed debt is {'lagging broader HY' if ratio > 3.0 else 'in line with HY'}")
print(f"  • ETF flows are {'positive' if hyg_change_pct > 0 and lqd_change_pct > 0 else 'mixed'} - {'strong demand' if hyg_change_pct > 0 else 'outflows'}")

print(f"\n" + "="*70)
print(f"Data as of: {hy_df.iloc[-1]['date']}")
print(f"Full analysis: data/analysis_2026-01-10.md")
print("="*70 + "\n")
