# Market Divergence Tracker

## Overview

This tracker monitors one of the most extreme market divergences in financial history:

- **Gold at ~$4,500** - Pricing structural crisis / dollar debasement
- **Credit spreads at 276bp** - Pricing no stress / business as usual
- **Bitcoin weak** - Liquidity tight despite Fed easing
- **Stocks up but narrow** - AI bubble, concentration risk extreme

**The divergence gap: ~900+ basis points between what gold implies vs what credit prices**

This is unprecedented and will resolve - the question is how and when.

---

## Quick Start

### Daily Collection & Analysis

```bash
# Activate virtual environment
source venv/bin/activate

# Run complete daily collection and analysis
./run_daily.sh
```

Or run components separately:

```bash
# 1. Collect all market data
python market_signals.py

# 2. Run divergence analysis
python divergence_analysis.py
```

---

## What's Being Tracked

### Credit Markets
- High-yield spreads (FRED: BAMLH0A0HYM2)
- Investment grade spreads (FRED: BAMLC0A0CM)
- CCC-rated spreads (FRED: BAMLH0A3HYC)
- Credit ETFs: HYG, LQD, BKLN

### Equity Markets
- S&P 500 (SPY) - Cap-weighted
- S&P 500 Equal Weight (RSP) - Breadth indicator
- Small Caps (IWM) - Risk appetite
- Nasdaq (QQQ) - Tech/AI concentration

### Safe Havens & Alternatives
- Gold (GLD) - Systemic risk / currency fears
- Gold Miners (GDX) - Confirms gold move
- Silver (SLV) - Industrial + monetary metal
- Bitcoin (BTC-USD) - Liquidity / speculation gauge

### Volatility & Risk
- VIX - Equity market fear gauge
- Dollar Index (UUP) - Currency strength

### Fixed Income
- 7-10yr Treasuries (IEF) - Core reference
- 20yr Treasuries (TLT) - Long duration
- Short Treasuries (SHY) - Front end
- TIPS (TIP) - Inflation expectations

### Derived Metrics
- **Market Breadth Ratio (RSP/SPY)** - Concentration indicator
- **Gold/Silver Ratio** - Risk gauge
- **Real Yield Proxy (TIP/IEF)** - Inflation-adjusted yields
- **Credit ETF Spreads** - HYG & LQD vs Treasuries
- **Divergence Gap** - Gold-implied spread vs actual spread

---

## Understanding the Crisis Score

The divergence analysis calculates a **Crisis Warning Score (0-100)** based on:

### Scoring Components

| Component | Max Points | What It Measures |
|-----------|-----------|------------------|
| **Credit Spreads** | 25 | Extreme tightness = late cycle warning |
| **Gold Price** | 25 | Extreme levels = structural crisis signal |
| **Divergence Gap** | 25 | How far apart gold and credit are |
| **Market Structure** | 15 | Breadth, concentration risk |
| **Volatility** | 10 | Fear gauge / complacency |
| **Bitcoin** | 10 | Liquidity / speculation indicator |

### Score Interpretation

- **0-20**: Normal - No significant warnings
- **20-40**: Low Warning - Minor stress signals
- **40-60**: Moderate Warning - Notable concerns
- **60-75**: High Warning - Significant divergences
- **75-100**: Extreme Warning - Multiple severe signals

**Current typical score: 60-80** (High to Extreme Warning)

---

## Key Metrics Explained

### The Divergence Gap

**Most important metric for tracking resolution**

```
Gold-Implied Spread = What credit spreads SHOULD be based on gold price
Actual Spread = What credit spreads actually are
Divergence Gap = Gold-Implied - Actual

Current: ~900 bp gap
```

**What this means:**
- Gap >800 bp = UNPRECEDENTED divergence
- Gap >600 bp = Extreme divergence
- Gap >400 bp = Large divergence
- Gap >200 bp = Moderate divergence
- Gap <100 bp = Normal/converging

**Resolution tracking:**
- Gap widening = Divergence getting worse (gold rising faster than spreads)
- Gap stable = Markets in standoff
- Gap narrowing = Resolution beginning
  - Spreads widening (credit catching down to gold) 🔴
  - Gold falling (gold correcting to credit) 🟢
  - Both moving (meeting in middle) 🟡

### Market Breadth Ratio (RSP/SPY)

**Measures market concentration**

```
RSP/SPY Ratio = Equal-weight S&P / Cap-weight S&P
```

- **>100**: Equal-weight outperforming = broad rally, healthy
- **98-100**: Normal = reasonable participation
- **95-98**: Narrow rally = large caps leading
- **<95**: Very narrow = extreme concentration risk (AI bubble)

**Current: Likely <98** = Narrow rally, concentration risk

### CCC/HY Ratio

**Measures stress in distressed debt**

```
CCC Spread / HY Spread
```

- **<2.5x**: Distressed credits healthy
- **2.5-3.0x**: Normal dispersion
- **3.0-3.5x**: Distressed lagging
- **>3.5x**: Distressed credits under severe stress

**Current: ~3.14x** = Distressed lagging despite tight HY

### Bitcoin vs Gold

**Key liquidity indicator**

When both rise:
- ✅ Debasement fears + risk appetite
- ✅ "Everything rally"
- Interpretation: Broad liquidity

When gold rises, Bitcoin falls:
- 🔴 Safe haven demand but no risk appetite
- 🔴 Liquidity actually tight
- 🔴 "Digital gold" narrative failing
- **Current state**

---

## Warning Triggers

### Early Warnings (Watch For)

**Credit:**
- [ ] HY spreads break 350 bp (currently 276)
- [ ] IG spreads break 100 bp (currently 79)
- [ ] CCC/HY ratio >3.5x (currently 3.14)

**Equity:**
- [ ] Breadth ratio <95 (concentration extreme)
- [ ] VIX spikes >25 (fear returning)
- [ ] SPY down >5% in a week

**Gold/Bitcoin:**
- [ ] Gold breaks $5,000 (crisis escalating)
- [ ] Bitcoin continues falling (liquidity death)
- [ ] Gold falls <$4,000 (fears easing)

### Critical Warnings (Crisis Beginning)

- [ ] HY spreads >500 bp (major widening)
- [ ] Breadth ratio <90 (AI bubble bursting)
- [ ] VIX >30 (panic)
- [ ] Multiple 5%+ down days in stocks

### Crisis Mode (Full Breakdown)

- [ ] HY spreads >800 bp (crisis conditions)
- [ ] IG spreads >200 bp (IG stress)
- [ ] VIX >40 (extreme fear)
- [ ] Circuit breakers triggered

---

## Historical Context

### Why This Is Unprecedented

**Never before have we seen:**

1. Gold rally 125% (from $2,000 to $4,500) in 2-3 years
2. WHILE credit spreads at cycle lows (276 bp)
3. WHILE stocks making new highs (AI-driven)
4. WHILE Fed is easing (cuts started, QT ended)
5. WHILE Bitcoin is weak (down despite easing)

**Closest historical analogues:**

| Period | Gold | Credit | Stocks | Similarity | Key Difference |
|--------|------|--------|--------|------------|----------------|
| **1970s** | 🔴 Soared | 🔴 Wide | 🔴 Bear | Stagflation | Stocks were DOWN |
| **2008-11** | 🔴 Up 2.4x | 🔴 Blew out | 🔴 Crashed first | Financial crisis | Credit collapsed FIRST |
| **1999-2000** | 🟢 Flat | 🟢 Tight | 🔴 Bubble | Dot-com | Gold was WEAK |
| **NOW** | 🔴 $4,500 | 🟢 276bp | 🟡 Up (narrow) | **NONE** | **NO PRECEDENT** |

### What History Suggests

**Credit spreads are ALWAYS late to price systemic risk:**
- 2007: Tight until Aug 2007, then blew out
- 2000: Tight through 1999, widened in 2000-2002
- 1998: Tight, then LTCM crisis, then tight again

**Gold often leads by 6-24 months:**
- 2005-2007: Gold rallied before financial crisis
- 2009-2011: Gold rallied during recovery (debt fears)

**The divergence resolution window: 6-18 months**

---

## Most Likely Scenarios

### Scenario 1: "Credit Catches Down to Gold" (60% probability)

**Timeline:** 6-18 months

**What happens:**
1. Gold stays elevated or goes higher ($4,500-5,000+)
2. AI stock bubble peaks and rolls over (6-12 months)
3. Credit spreads start widening (HY: 350→600 bp)
4. Economic slowdown or recession emerges
5. Bitcoin stays weak or bottoms early
6. Resolution: Crisis or major reset by late 2026

**Catalysts:**
- AI earnings disappoint
- Geopolitical event
- Fed policy mistake
- Corporate refinancing stress

### Scenario 2: "Gold Corrects to Credit" (20% probability)

**Timeline:** 3-9 months

**What happens:**
1. Gold falls back to $3,000-3,500
2. Credit spreads stay tight
3. Soft landing achieved
4. AI boom has real productivity gains
5. Bitcoin recovers with gold
6. Resolution: Gold was wrong, bubble pops

**Catalysts:**
- De-escalation (geopolitics, trade)
- AI productivity boom validates valuations
- Fiscal situation better than feared

### Scenario 3: "Messy Middle / Both Right" (20% probability)

**Timeline:** 12-36 months

**What happens:**
1. Gold stays high, credit widens moderately (not catastrophically)
2. Stocks choppy, rolling bear market
3. No single crisis, but slow deterioration
4. Higher-for-longer grinds markets down
5. Bitcoin stays weak for years
6. Resolution: Slow grind, both partially right

---

## Daily Monitoring Routine

### What to Check Every Day

1. **Run the tracker:**
   ```bash
   ./run_daily.sh
   ```

2. **Review Crisis Score:**
   - Score increasing? = Getting worse
   - Score decreasing? = Resolving
   - Score >75? = High alert

3. **Check Divergence Gap:**
   - Gap widening? = Divergence worse
   - Gap narrowing? = Resolution starting
   - How is it narrowing? (Credit up or gold down?)

4. **Monitor Triggers:**
   - Any early warnings triggered?
   - Market breadth deteriorating?
   - VIX spiking?

5. **Watch for Catalysts:**
   - Fed announcements
   - Major economic data
   - Geopolitical events
   - Corporate earnings (especially AI/tech)

### Weekly Review

Compare week-over-week:
- Credit spread changes
- Gold price movement
- Divergence gap trend
- Market breadth trend
- Crisis score changes

### Monthly Analysis

Generate detailed report:
- Percentile analysis (where are we historically?)
- Correlation changes
- Resolution progress
- Updated probabilities

---

## Data Files Generated

All data stored in `data/` directory:

### Credit Spreads (FRED)
- `high_yield_spread.csv`
- `investment_grade_spread.csv`
- `ccc_spread.csv`

### Credit ETFs
- `leveraged_loan_price.csv` (BKLN)
- `high_yield_credit_price.csv` (HYG)
- `investment_grade_credit_price.csv` (LQD)

### Equity Indices
- `sp500_price.csv` (SPY)
- `sp500_equal_weight_price.csv` (RSP)
- `small_cap_price.csv` (IWM)
- `nasdaq_price.csv` (QQQ)

### Safe Havens
- `gold_price.csv` (GLD)
- `gold_miners_price.csv` (GDX)
- `silver_price.csv` (SLV)
- `bitcoin_price.csv` (BTC-USD)

### Other
- `vix_price.csv` (^VIX)
- `dollar_index_price.csv` (UUP)
- `treasury_7_10yr_price.csv` (IEF)
- `treasury_20yr_price.csv` (TLT)
- `treasury_short_price.csv` (SHY)
- `tips_inflation_price.csv` (TIP)
- `commodities_price.csv` (DBC)

### Derived Metrics
- `market_breadth_ratio.csv` (RSP/SPY)
- `gold_silver_ratio.csv` (GLD/SLV)
- `real_yield_proxy.csv` (TIP/IEF)
- `hyg_treasury_spread.csv`
- `lqd_treasury_spread.csv`

---

## Command Reference

### Data Collection

```bash
# Collect all data (30 days lookback for new files)
python market_signals.py

# Collect with custom lookback
python market_signals.py --lookback-days 90

# Show summary only (no collection)
python market_signals.py --summary

# Custom data directory
python market_signals.py --data-dir /path/to/data
```

### Analysis

```bash
# Run divergence analysis
python divergence_analysis.py

# Analysis uses default data directory 'data/'
# Make sure data is collected first
```

### Complete Daily Run

```bash
# Easiest - runs everything
./run_daily.sh
```

### Legacy Credit-Only Tracker

```bash
# Original credit-only tracker still works
python credit_signals.py
```

---

## Scheduling

### Linux/Mac Cron

Add to crontab to run daily at 6 PM:

```bash
crontab -e
```

Add:
```
0 18 * * * cd /home/eric/Documents/repos/financial/signaltrackers && ./run_daily.sh >> logs/daily_run.log 2>&1
```

Create logs directory:
```bash
mkdir -p logs
```

---

## Notes & Warnings

### Data Limitations

1. **Gold price from GLD ETF:**
   - GLD trades at ~1/10th spot gold price
   - We multiply by 10 for approximation
   - Not exact but close enough for analysis

2. **VIX data:**
   - Only available during market hours
   - May show stale data after hours

3. **Bitcoin:**
   - 24/7 trading = can be volatile
   - Weekend data may differ from Friday close

4. **FRED data:**
   - Updates on business days only
   - May lag by 1-2 days
   - Credit spreads are option-adjusted spreads (OAS)

### Interpretation Cautions

1. **Crisis score is relative:**
   - Based on current market structure
   - Not a prediction, a warning gauge
   - Use alongside other analysis

2. **Divergence can persist:**
   - "Markets can stay irrational longer than you can stay solvent"
   - Having warnings doesn't mean immediate crisis
   - Timeline is uncertain (6-24 month range)

3. **Historical analogues are imperfect:**
   - Current setup is truly unprecedented
   - Past patterns may not repeat
   - Multiple scenarios possible

4. **This is a monitoring tool:**
   - Not investment advice
   - Track, don't trade on signals alone
   - Use for situational awareness

---

## Support & Updates

### Files
- `market_signals.py` - Main data collection
- `divergence_analysis.py` - Analysis and scoring
- `credit_signals.py` - Legacy credit-only tracker
- `run_daily.sh` - Complete daily runner
- `setup.sh` - Initial setup script

### Getting Help

If you encounter issues:

1. Check FRED API key is set: `echo $FRED_API_KEY`
2. Verify virtual environment: `which python`
3. Check for errors in logs: `tail logs/daily_run.log`
4. Ensure yfinance working: `python -c "import yfinance; print('OK')"`

### Maintenance

**Monthly:**
- Review data quality
- Check for missing dates
- Verify calculations

**Quarterly:**
- Update crisis score thresholds if market regime changes
- Recalibrate gold-implied spread formula if relationship shifts
- Archive old analysis reports

---

## What Makes This Tracker Unique

1. **Tracks THE historic divergence** - Gold $4,500 vs 276bp spreads
2. **Multi-asset view** - Credit, equity, gold, Bitcoin, volatility
3. **Divergence scoring** - Quantifies how unprecedented this is
4. **Resolution tracking** - Monitors which way it's resolving
5. **Daily granularity** - Catches the turn when it happens
6. **Historical context** - Shows why this is different

**You're building a real-time record of one of the most extreme market setups in financial history.**

When this resolves, you'll have the data to see exactly how it happened.
