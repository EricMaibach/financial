# AI Briefing Feed Review

**Date:** 2026-02-10
**Purpose:** Evaluate AI briefing context/prompts for lingering niche bias (gold/credit divergence) and ensure alignment with comprehensive macro financial dashboard positioning.

---

## Executive Summary

The AI briefing **system prompts are clean** - they don't emphasize any niche area and are appropriately positioned for a comprehensive macro dashboard. However, the **data context being fed to the AI** has remnants of the previous niche focus that should be adjusted.

**Key Finding:** The Divergence Gap metric is given undue prominence in the data feeds, appearing first and with special treatment. This can inadvertently lead the AI to emphasize it over other equally important macro indicators.

---

## Issues Identified

### Issue 1: Divergence Gap Positioned First in Market Summary

**Location:** `dashboard.py:2438-2446` in `generate_market_summary()`

**Problem:** The Divergence Gap is the **first metric** in the data summary, appearing before Credit Spreads, Safe Havens, Equities, and all other categories. This positional prominence signals to the AI that it's the most important metric.

**Current Code:**
```python
# Divergence Gap  <-- FIRST SECTION
if divergence_df is not None:
    stats = get_stats(divergence_df)
    if stats:
        summary_parts.append("## DIVERGENCE GAP (Gold-Implied Spread minus Actual HY Spread)")
        ...

# Credit Spreads Section  <-- Second
summary_parts.append("## CREDIT SPREADS")
```

**Recommendation:** Move Divergence Gap to be one metric among many, not the lead. Position it after core macro indicators like Credit Spreads, Equity Markets, and Safe Havens.

---

### Issue 2: Export File Header References "Divergence"

**Location:** `export_for_ai.py:103`

**Problem:** The file header says "# MARKET DIVERGENCE DATA SUMMARY" which frames the entire export around the divergence theme rather than comprehensive macro data.

**Current Code:**
```python
output.append("# MARKET DIVERGENCE DATA SUMMARY")
```

**Recommendation:** Change to neutral header like "# MARKET DATA SUMMARY" or "# MACRO FINANCIAL DATA SUMMARY"

---

### Issue 3: Table of Contents Prioritizes Divergence

**Location:** `export_for_ai.py:114`

**Problem:** Table of Contents lists "Key Divergence Metrics" as item #1, reinforcing the niche focus.

**Current Code:**
```python
output.append("1. [Key Divergence Metrics](#key-divergence-metrics)")
output.append("2. [Credit Markets](#credit-markets)")
```

**Recommendation:** Reorder to put Credit Markets, Equity Markets, or a more neutral category first.

---

## What's Already Working Well

The **system prompts** in `ai_summary.py` are well-written for a comprehensive macro platform:

| Briefing | System Prompt Assessment |
|----------|--------------------------|
| Daily Market Summary | Generic "financial commentator" - no niche bias |
| Crypto | Focus on liquidity/macro - appropriate |
| Equity | Focus on breadth/rotation - appropriate |
| Rates | Focus on yield curve/Fed policy - appropriate |
| Dollar | Focus on Dollar Smile/carry - appropriate |
| Portfolio | References all briefings - comprehensive |

**No changes needed to system prompts.**

---

## Recommended Changes

### Change 1: Reorder Data Sections in `generate_market_summary()`

**File:** `dashboard.py`
**Lines:** ~2438-2590

**Before (Current Order):**
1. Divergence Gap ← Too prominent
2. Credit Spreads
3. Safe Havens
4. Equity Markets
5. Market Concentration
6. Yen Carry Trade
7. Yield Curve
8. Labor Market
9. Economic Indicators
10. Prediction Markets

**After (Recommended Order):**
1. Credit Spreads ← Lead with core risk indicator
2. Equity Markets
3. Safe Havens
4. Market Concentration
5. Yield Curve
6. Yen Carry Trade
7. Labor Market
8. Economic Indicators
9. Divergence Gap ← Move to end as one of many indicators
10. Prediction Markets

---

### Change 2: Update Export File Header

**File:** `export_for_ai.py`
**Line:** 103

**Before:**
```python
output.append("# MARKET DIVERGENCE DATA SUMMARY")
```

**After:**
```python
output.append("# MACRO FINANCIAL DATA SUMMARY")
```

---

### Change 3: Reorder Table of Contents in Export

**File:** `export_for_ai.py`
**Lines:** 114-121

**Before:**
```python
output.append("1. [Key Divergence Metrics](#key-divergence-metrics)")
output.append("2. [Credit Markets](#credit-markets)")
```

**After:**
```python
output.append("1. [Credit Markets](#credit-markets)")
output.append("2. [Equity Markets](#equity-markets)")
...
output.append("7. [Divergence Metrics](#divergence-metrics)")  # Renamed and repositioned
```

---

## Summary of Changes

| File | Change | Impact |
|------|--------|--------|
| `dashboard.py` | Move Divergence Gap section from first to near-last | AI won't treat it as primary metric |
| `export_for_ai.py` | Change header from "MARKET DIVERGENCE" to "MACRO FINANCIAL" | Neutral framing |
| `export_for_ai.py` | Reorder TOC to put Credit/Equity first | Proper prioritization |

---

## Files That Would Be Modified

1. **`dashboard.py`** - Reorder sections in `generate_market_summary()` (~lines 2438-2590)
2. **`export_for_ai.py`** - Update header (line 103) and TOC order (lines 114-121)

---

## Next Steps

**Awaiting approval before making any code changes.**

These are minimal, targeted changes that reposition existing content without adding new features or changing the AI's tone.

---

*Document generated as part of Issue #2: AI briefing feed review*
