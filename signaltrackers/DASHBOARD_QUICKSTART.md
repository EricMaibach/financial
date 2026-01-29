# Dashboard Quick Start Guide

## 🚀 Start the Dashboard in 3 Steps

### Step 1: Open Terminal and Navigate

```bash
cd /home/eric/Documents/repos/financial/signaltrackers
```

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 3: Start the Dashboard

```bash
./start_dashboard.sh
```

Or manually:

```bash
python dashboard.py
```

### Step 4: Open Your Browser

Go to:
```
http://localhost:5000
```

---

## 📊 What You'll See

### Main Dashboard (/)
- **Crisis Warning Score**: 85-90/100 (EXTREME WARNING)
- **Divergence Gap**: 917 bp (unprecedented)
- **Key Metrics**: HY spreads (276 bp), Gold ($4,145), Bitcoin ($91k), VIX (14.49)
- **Live Chart**: Divergence gap over time
- **Scenario Probabilities**: Updated with Bitcoin crash context

### Credit Markets (/credit)
- Credit spread charts (HY, IG, CCC)
- Historical trends
- Warning levels

### Equity Markets (/equity)
- SPY, QQQ, IWM performance
- Market breadth tracking

### Safe Havens (/safe-havens)
- Gold tracking
- Bitcoin crash analysis (24% from $120k)
- Gold vs Bitcoin divergence

### Scenarios (/scenarios)
- Three resolution paths
- Quarterly timeline (Q1-Q4 2026)
- Black swan wildcards
- What to monitor

---

## 🔄 Daily Workflow

**Morning Routine:**

1. Collect latest data:
   ```bash
   ./run_daily.sh
   ```

2. Start dashboard:
   ```bash
   ./start_dashboard.sh
   ```

3. Review in browser:
   - Crisis score trending
   - Divergence gap movement
   - Any trigger events

4. Take action based on alerts

---

## ⚙️ Troubleshooting

### Dashboard won't start?

```bash
# Check if Flask installed
pip list | grep Flask

# If not, install it
pip install flask
```

### No data showing?

```bash
# Collect data first
python market_signals.py

# Check CSV files exist
ls -lh data/
```

### Port 5000 in use?

```bash
# Find what's using it
lsof -i :5000

# Kill it or change port in dashboard.py
```

---

## 📱 Access from Other Devices

### On Same Network:

1. Find your IP address:
   ```bash
   hostname -I
   ```

2. Access from phone/tablet:
   ```
   http://YOUR-IP:5000
   ```

### Via SSH Tunnel (Remote):

```bash
ssh -L 5000:localhost:5000 eric@your-server
```

Then access `http://localhost:5000` on your local machine.

---

## 🎯 Key Features

✅ **Real-time updates**: Auto-refresh every 60 seconds
✅ **Responsive design**: Works on mobile/tablet
✅ **Interactive charts**: Hover for details
✅ **Crisis scoring**: Automated warning system
✅ **Scenario tracking**: Monitor resolution probabilities
✅ **Historical data**: All charts show trends

---

## 📈 Most Important Metrics to Watch

1. **Divergence Gap**
   - Currently: 917 bp
   - Watch for: Widening (worse) or narrowing (resolving)

2. **HY Credit Spreads**
   - Currently: 276 bp
   - Critical level: >300 bp (first warning)

3. **Crisis Warning Score**
   - Currently: 85-90/100
   - Watch for: Trending up or down

4. **VIX**
   - Currently: 14.49
   - Critical level: >20 (fear returning)

---

## 🔔 Alert Levels

### 🔴 Critical (Immediate Action)
- HY spreads >350 bp
- VIX >25
- Divergence gap >1,000 bp
- Gold >$4,500

### 🟡 Warning (Increased Monitoring)
- HY spreads >300 bp
- VIX >20
- Bitcoin falls further
- Market breadth deteriorating

### 🟢 Resolution (Divergence Closing)
- Gap narrowing to <600 bp
- Either credit widens OR gold falls
- Direction indicates which scenario

---

## 💡 Pro Tips

1. **Bookmark the dashboard**: Add to favorites for quick access

2. **Set up dual monitors**: Dashboard on one screen, trading/research on another

3. **Check before market open**: Review overnight changes

4. **Watch scenario page**: Timeline shows expected progression

5. **Use API endpoints**: Integrate data into your own tools
   ```bash
   curl http://localhost:5000/api/dashboard | python -m json.tool
   ```

---

## 🛑 Stopping the Dashboard

Press `Ctrl+C` in the terminal where it's running.

Or if running in background:
```bash
pkill -f dashboard.py
```

---

## 📚 More Information

- Full documentation: [DASHBOARD_README.md](DASHBOARD_README.md)
- Analysis details: [README_DIVERGENCE.md](README_DIVERGENCE.md)
- Latest analysis: [ANALYSIS_SUMMARY_2026-01-11.md](ANALYSIS_SUMMARY_2026-01-11.md)

---

**Happy tracking! You're now monitoring one of the most extreme market divergences in financial history with a real-time dashboard.**
