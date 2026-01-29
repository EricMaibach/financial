# Market Divergence Dashboard

A comprehensive web-based dashboard for tracking the historic market divergence between credit markets, safe havens, and equities.

## Features

### 📊 Main Dashboard
- **Crisis Warning Score** (0-100): Real-time calculation based on multiple indicators
- **Key Metrics Cards**: Divergence gap, HY spreads, gold price, VIX, Bitcoin, etc.
- **Divergence Gap Chart**: Visual tracking of the historic 900+ bp gap
- **Scenario Probabilities**: Updated probabilities for three possible outcomes
- **Market Regime Assessment**: Current state and what to watch

### 💰 Credit Markets Page
- Credit spread charts (HY, IG, CCC)
- Historical trends and analysis
- ETF performance tracking
- Warning levels and critical thresholds

### 📈 Equity Markets Page
- Stock indices performance (SPY, QQQ, IWM)
- Market breadth tracking
- Concentration risk monitoring

### 🏆 Safe Havens Page
- Gold tracking (currently at $4,145)
- Bitcoin crash analysis (24% from $120k peak)
- Gold vs Bitcoin divergence chart
- Leading indicator analysis

### 🎯 Scenarios Page
- Three scenario paths with probabilities
- **Scenario 1** (65-70%): Credit catches down to gold
- **Scenario 2** (25-30%): Messy middle
- **Scenario 3** (5-10%): Soft landing
- Quarterly timeline (Q1-Q4 2026)
- Black swan wildcards
- What to monitor for resolution

## Quick Start

### 1. Install Flask (if not already installed)

```bash
source venv/bin/activate
pip install flask
```

### 2. Start the Dashboard

```bash
./start_dashboard.sh
```

Or manually:

```bash
source venv/bin/activate
python dashboard.py
```

### 3. Access the Dashboard

Open your browser and go to:
```
http://localhost:5000
```

## Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| **Main Dashboard** | `/` | Overview, crisis score, key metrics |
| **Credit Markets** | `/credit` | Credit spreads, ETF performance |
| **Equity Markets** | `/equity` | Stock indices, market breadth |
| **Safe Havens** | `/safe-havens` | Gold, Bitcoin, divergence analysis |
| **Scenarios** | `/scenarios` | Future outlooks, timeline, wildcards |

## Key Metrics Displayed

### Crisis Warning Score
- **85-90/100**: EXTREME WARNING (current)
- Based on: Credit spreads, gold price, divergence gap, VIX, Bitcoin, market breadth

### Divergence Gap
- **917 bp**: Current gap between gold-implied spreads and actual spreads
- Gap widening = divergence getting worse
- Track for resolution signals

### Credit Spreads
- **HY: 276 bp** - Extremely tight (0th percentile)
- **IG: 79 bp** - Rock solid
- **CCC/HY: 3.14x** - Distressed lagging

### Safe Havens
- **Gold: $4,145** - 89th percentile, structural crisis signal
- **Bitcoin: $91,215** - Down 24% from $120k peak (liquidity warning)

## Auto-Refresh

The dashboard auto-refreshes data every 60 seconds to show the latest values from your collected CSV files.

## Data Sources

All data comes from your daily collection via `market_signals.py`:
- FRED credit spreads (requires API key)
- ETF prices via yfinance
- Calculated divergence metrics

## Customization

### Port Configuration

To run on a different port, edit `dashboard.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Styling

Edit `/static/css/dashboard.css` to customize colors, fonts, layout.

### Adding Charts

Charts use Chart.js. Add new charts in templates with:

```javascript
new Chart(ctx, {
    type: 'line',
    data: { ... },
    options: { ... }
});
```

## API Endpoints

The dashboard provides JSON APIs for programmatic access:

```
GET /api/dashboard           # Main dashboard data
GET /api/chart/divergence_gap    # Divergence gap chart data
GET /api/chart/credit_spreads    # Credit spreads chart data
GET /api/chart/gold_bitcoin      # Gold vs Bitcoin data
GET /api/chart/equity_indices    # Equity indices data
GET /api/chart/vix              # VIX data
```

Example:
```bash
curl http://localhost:5000/api/dashboard | python -m json.tool
```

## Production Deployment

### Using Gunicorn (Recommended)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 dashboard:app
```

### Using systemd Service

Create `/etc/systemd/system/market-dashboard.service`:

```ini
[Unit]
Description=Market Divergence Dashboard
After=network.target

[Service]
User=eric
WorkingDirectory=/home/eric/Documents/repos/financial/signaltrackers
Environment="PATH=/home/eric/Documents/repos/financial/signaltrackers/venv/bin"
ExecStart=/home/eric/Documents/repos/financial/signaltrackers/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 dashboard:app

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable market-dashboard
sudo systemctl start market-dashboard
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Dashboard Won't Start

1. Check Flask is installed:
   ```bash
   pip list | grep Flask
   ```

2. Check data directory exists:
   ```bash
   ls data/
   ```

3. Collect data first:
   ```bash
   python market_signals.py
   ```

### No Data Showing

1. Verify CSV files exist:
   ```bash
   ls -lh data/*.csv
   ```

2. Check for errors in browser console (F12)

3. Try API endpoint directly:
   ```bash
   curl http://localhost:5000/api/dashboard
   ```

### Port Already in Use

```bash
# Find what's using port 5000
lsof -i :5000

# Or use a different port
python dashboard.py  # Edit file to change port
```

## Daily Workflow

1. **Morning**: Run data collection
   ```bash
   ./run_daily.sh
   ```

2. **Start dashboard**:
   ```bash
   ./start_dashboard.sh
   ```

3. **Review**:
   - Check Crisis Warning Score
   - Review divergence gap trend
   - Watch for trigger events
   - Update positioning accordingly

## Mobile Access

The dashboard is responsive and works on mobile devices. Access via:
```
http://your-ip-address:5000
```

## Security Notes

- Dashboard runs on localhost by default (secure)
- For remote access, use SSH tunnel or VPN
- Don't expose to public internet without authentication
- Add authentication if needed (Flask-Login, etc.)

## Screenshots

(Add your own screenshots here after running)

## Updates & Maintenance

Dashboard automatically updates when you:
1. Run `market_signals.py` to collect new data
2. Refresh the browser page

No restart required - data is loaded from CSV files on each page load.

## Support

For issues or questions:
1. Check [README_DIVERGENCE.md](README_DIVERGENCE.md) for analysis details
2. Review [ANALYSIS_SUMMARY_2026-01-11.md](ANALYSIS_SUMMARY_2026-01-11.md)
3. Run `python comprehensive_report.py` for detailed analysis

---

**You're now tracking one of the most extreme market divergences in financial history with a real-time dashboard!**
