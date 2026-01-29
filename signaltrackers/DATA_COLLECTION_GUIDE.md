# Data Collection Guide

## Overview

You have two main data collection scripts:

| Script | Purpose | When to Use | Lookback Period |
|--------|---------|-------------|-----------------|
| **backfill_historical_data.sh** | One-time historical data collection | First setup or after gaps | 6 months (180 days) |
| **run_daily.sh** | Daily data updates | Every day | 30 days |

---

## First Time Setup (Backfill Historical Data)

### Run Once to Get 6 Months of History:

```bash
./backfill_historical_data.sh
```

**What it does:**
- Fetches 6 months (180 days) of data for all 30+ markets
- FRED credit spreads (HY, IG, CCC) - requires API key
- All ETF prices (gold, Bitcoin, stocks, etc.)
- Calculates derived metrics (divergence gap, breadth, etc.)
- Safely merges with any existing data (no duplicates)
- Takes 5-10 minutes to complete

**When to use:**
- ✅ First time running the tracker
- ✅ After a data gap (vacation, system down, etc.)
- ✅ Want to see longer historical trends in dashboard
- ✅ Need more data for better analysis

**Safe to run:**
- Won't create duplicate entries
- Won't overwrite existing data
- Won't affect daily run behavior

---

## Daily Updates (Run Daily)

### Run Every Day to Stay Current:

```bash
./run_daily.sh
```

**What it does:**
- Fetches last 30 days of data (to catch any missed days)
- Updates all 30+ markets
- Adds only new dates (no duplicates)
- Runs analysis and shows results
- Takes 1-2 minutes to complete

**When to use:**
- ✅ Every day (preferably after market close)
- ✅ When you want latest data
- ✅ Before checking the dashboard

**Schedule it:**
```bash
# Add to crontab for automatic daily runs
crontab -e

# Run daily at 6 PM
0 18 * * * cd /home/eric/Documents/repos/financial/signaltrackers && ./run_daily.sh >> logs/daily_run.log 2>&1
```

---

## How They Work Together

### Initial Setup:

```bash
# Step 1: Get 6 months of history (run once)
./backfill_historical_data.sh

# Step 2: Start using daily (run every day)
./run_daily.sh
```

### Daily Workflow:

```bash
# Every day
./run_daily.sh           # Updates data
./start_dashboard.sh     # View in browser
```

### After a Gap:

```bash
# If you missed several days/weeks
./backfill_historical_data.sh   # Re-backfill to catch up

# Then resume daily
./run_daily.sh
```

---

## Technical Details

### Backfill Script:

```bash
# Internally calls:
python market_signals.py --lookback-days 180
```

- **180 days** = approximately 6 months
- Fetches data from 180 days ago to today
- Merges with existing CSV files
- Only adds dates that don't already exist

### Daily Script:

```bash
# Internally calls:
python market_signals.py --lookback-days 30
python divergence_analysis.py
```

- **30 days** = safety buffer to catch missed days
- Fetches last month of data
- Updates only new dates
- Shows analysis after collection

### Why 30 Days for Daily Run?

- Catches any missed days if you skip a few days
- Handles weekends and holidays automatically
- FRED data sometimes has delays
- yfinance may have data gaps
- Better safe than missing data

---

## Data Storage

### CSV Files Location:
```
data/
├── high_yield_spread.csv        # FRED credit data
├── gold_price.csv               # ETF data
├── bitcoin_price.csv            # ETF data
├── divergence_gap.csv           # Calculated metrics
└── ... (30+ total files)
```

### How Duplicates are Prevented:

Both scripts use the same logic:
1. Read existing CSV file
2. Check which dates already exist
3. Only add rows for NEW dates
4. Sort by date
5. Save back to CSV

**This means you can safely run either script multiple times without creating duplicates.**

---

## Troubleshooting

### "No new data to append"

This is NORMAL and means:
- ✅ Data is already up to date
- ✅ No duplicates were created
- ✅ Everything is working correctly

Just means the dates you're trying to fetch already exist in your CSV files.

### Backfill takes a long time

Expected behavior:
- **FRED data:** 3 series × 180 days = can take 2-3 minutes
- **ETF data:** 25+ tickers × 180 days = can take 5-7 minutes
- **Total:** 5-10 minutes is normal

Be patient, especially if:
- First time running
- API rate limits (FRED)
- Network slow
- Many tickers to fetch

### Daily run is fast

Expected behavior:
- Already has most data
- Only fetching last 30 days
- Most dates already exist
- Takes 1-2 minutes

### Missing FRED data

If FRED API key not set:
```bash
# Set it first
export FRED_API_KEY='your_key_here'

# Add to .bashrc for persistence
echo "export FRED_API_KEY='your_key_here'" >> ~/.bashrc
source ~/.bashrc

# Then run backfill
./backfill_historical_data.sh
```

---

## Manual Data Collection

### Custom Lookback Period:

```bash
# Fetch 1 year of data
python market_signals.py --lookback-days 365

# Fetch 3 months
python market_signals.py --lookback-days 90

# Fetch just today
python market_signals.py --lookback-days 1
```

### Check What You Have:

```bash
# Show summary of all data files
python market_signals.py --summary

# Or manually
ls -lh data/
head data/high_yield_spread.csv
tail data/high_yield_spread.csv
```

### Data Quality Check:

```bash
# Run comprehensive analysis
python comprehensive_report.py

# Shows:
# - Data ranges for each file
# - Missing dates (if any)
# - Latest values
# - Historical percentiles
```

---

## Best Practices

### ✅ DO:

- Run backfill once when setting up
- Run daily updates every day
- Check dashboard regularly
- Set FRED API key before backfill
- Monitor logs for errors

### ❌ DON'T:

- Run backfill every day (unnecessary, slow)
- Worry about duplicates (automatically prevented)
- Delete data files (unless starting over)
- Skip daily updates for weeks (harder to catch up)

---

## Quick Reference

```bash
# FIRST TIME SETUP
./backfill_historical_data.sh    # Get 6 months of history

# DAILY USE
./run_daily.sh                   # Update with latest data
./start_dashboard.sh             # View in browser

# ANALYSIS
python comprehensive_report.py   # Detailed analysis
python divergence_analysis.py    # Crisis score

# CHECK DATA
python market_signals.py --summary
ls -lh data/

# EMERGENCY BACKFILL
./backfill_historical_data.sh    # If you missed days/weeks
```

---

## Example Timeline

### Day 1 (First Time Setup):
```bash
# Get 6 months of historical data
./backfill_historical_data.sh
# Takes: 5-10 minutes

# Check the dashboard
./start_dashboard.sh
# Now you have 6 months of charts!
```

### Day 2-365 (Daily Routine):
```bash
# Morning: Update data
./run_daily.sh
# Takes: 1-2 minutes

# Check dashboard
./start_dashboard.sh
# See latest metrics
```

### Day 100 (After missing a week):
```bash
# If you want to be extra safe
./backfill_historical_data.sh
# Re-fetches last 6 months, fills any gaps

# Or just run daily (30-day lookback catches the gap)
./run_daily.sh
# Takes: 1-2 minutes, fills the week you missed
```

---

## Summary

- **Backfill** = One-time, 6 months, 5-10 minutes, use for initial setup
- **Daily** = Every day, 30 days, 1-2 minutes, use for staying current
- **Both are safe** = No duplicates, merges intelligently
- **Both do the same thing** = Just different lookback periods

**You're all set!** Run the backfill once, then daily updates from there.
