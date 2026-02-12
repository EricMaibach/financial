# Market Signals Tracker

## 🚨 TRACKING HISTORIC MARKET DIVERGENCE 🚨

**Gold: ~$4,500** | **Credit Spreads: 276 bp** | **Divergence Gap: ~900 bp**

This tracker monitors one of the most extreme market divergences in financial history.

---

## 📊 **NEW: Comprehensive Market Divergence Tracker**

**For complete divergence tracking, use the new comprehensive tracker:**

### Quick Start

```bash
# Daily collection and analysis (recommended)
./run_daily.sh
```

See **[README_DIVERGENCE.md](README_DIVERGENCE.md)** for full documentation.

### What's New

- **Multi-asset tracking**: Credit, equity, gold, Bitcoin, volatility
- **Divergence analysis**: Quantifies the historic gold vs credit disconnect
- **Crisis scoring**: 0-100 warning score based on multiple indicators
- **Market breadth**: Track concentration risk (AI bubble)
- **Resolution monitoring**: See which way the divergence resolves

---

## 📈 Original Credit-Only Tracker (Legacy)

The original credit market tracker is still available below.

### Credit Market Signals Tracker

Automated daily collection of credit market indicators for historical analysis.

## Data Sources

The tracker collects the following signals:

1. **High-Yield Credit Spread** (FRED: BAMLH0A0HYM2)
   - ICE BofA US High Yield Index Option-Adjusted Spread

2. **Investment Grade Credit Spread** (FRED: BAMLC0A0CM)
   - ICE BofA US Corporate Index Option-Adjusted Spread

3. **CCC-Rated Bond Spread** (FRED: BAMLH0A3HYC)
   - ICE BofA CCC & Lower US High Yield Index Option-Adjusted Spread

4. **Leveraged Loan Proxy** (ETF: BKLN)
   - Invesco Senior Loan ETF price tracking

5. **Credit ETF Spreads vs Treasuries**
   - HYG (High Yield) vs IEF (7-10yr Treasury) spread
   - LQD (Investment Grade) vs IEF spread

## Setup

### Quick Setup (Recommended)

Run the automated setup script:

```bash
# First, install python3-venv if needed:
sudo apt install python3.13-venv

# Then run the setup script:
cd signaltrackers
./setup.sh
```

This will create a virtual environment, install dependencies, and create necessary directories.

### Manual Setup

#### 1. Create Virtual Environment (Linux/Mac)

```bash
# Install venv if not already installed (Ubuntu/Debian)
sudo apt install python3.13-venv

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** Always activate the virtual environment before running the scripts:
```bash
source venv/bin/activate
```

#### 2. Get FRED API Key

1. Go to [https://fred.stlouisfed.org/](https://fred.stlouisfed.org/)
2. Create a free account
3. Request an API key at [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)

#### 3. Set API Key

Set your FRED API key as an environment variable:

```bash
export FRED_API_KEY='your_api_key_here'
```

Or add it to your `.bashrc` or `.zshrc` for persistence:

```bash
echo "export FRED_API_KEY='your_api_key_here'" >> ~/.bashrc
source ~/.bashrc
```

## Email Configuration (Optional)

SignalTrackers supports email notifications for alerts and daily briefings. Email configuration is **optional** but required for alert notifications and automated briefings.

### Supported Email Providers

The application uses SMTP for email delivery. We recommend **Brevo (formerly Sendinblue)** for the free tier:
- **Free tier**: 300 emails/day (9,000/month)
- **Easy setup**: Simple SMTP configuration
- **Reliable**: High deliverability rates

### Setting Up Brevo

1. **Sign up** at [https://www.brevo.com](https://www.brevo.com)
2. **Navigate** to SMTP & API → SMTP
3. **Create** an SMTP key
4. **Verify** your sender email address

### Configure Environment Variables

Add to your `.env` file or environment:

```bash
# Email Configuration
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-brevo-smtp-key
MAIL_DEFAULT_SENDER=SignalTrackers <briefings@signaltrackers.com>
```

See `.env.example` for a complete configuration template.

### Test Email Configuration

Verify your email setup is working:

```bash
python scripts/test_email.py your-email@example.com
```

This sends a test email to verify:
- SMTP connection works
- Credentials are correct
- Email templates render properly
- Messages reach the inbox (not spam)

### Email Deliverability (Production)

For production deployments, configure DNS records for better deliverability:

**SPF Record** (add to your domain's DNS):
```
v=spf1 include:spf.brevo.com ~all
```

**DKIM**: Brevo provides DKIM records in the SMTP settings - add these to your DNS

**DMARC** (optional but recommended):
```
v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
```

### Alternative Email Providers

The application works with any SMTP provider:
- **SendGrid**: [https://sendgrid.com](https://sendgrid.com) (100 emails/day free)
- **Mailgun**: [https://www.mailgun.com](https://www.mailgun.com) (5,000 emails/month free for 3 months)
- **Amazon SES**: [https://aws.amazon.com/ses/](https://aws.amazon.com/ses/) (62,000 emails/month free with EC2)
- **Gmail SMTP**: Not recommended for production (low sending limits)

Just update the `MAIL_SERVER`, `MAIL_PORT`, and credentials accordingly.

## Usage

### Daily Collection

Run the script daily to collect and append new data:

```bash
python credit_signals.py
```

### First-Time Setup (Historical Data)

On first run, collect more historical data:

```bash
python credit_signals.py --lookback-days 365
```

### View Data Summary

See what data has been collected:

```bash
python credit_signals.py --summary
```

### Custom Data Directory

Store data in a different location:

```bash
python credit_signals.py --data-dir /path/to/data
```

### Pass API Key via Command Line

Instead of environment variable:

```bash
python credit_signals.py --fred-api-key YOUR_KEY_HERE
```

## Data Storage

Data is stored in CSV files in the `data/` directory (or custom directory):

- `high_yield_spread.csv` - High-yield credit spreads
- `investment_grade_spread.csv` - Investment grade spreads
- `ccc_spread.csv` - CCC-rated bond spreads
- `leveraged_loan_etf.csv` - BKLN ETF prices
- `high_yield_credit_etf.csv` - HYG ETF prices
- `investment_grade_credit_etf.csv` - LQD ETF prices
- `treasury_7_10yr_etf.csv` - IEF ETF prices
- `hyg_treasury_spread.csv` - Calculated HYG vs IEF spread
- `lqd_treasury_spread.csv` - Calculated LQD vs IEF spread

Each file contains:
- `date` - The observation date
- Value column (varies by file)

The script automatically:
- Avoids duplicate dates
- Appends only new data
- Sorts data by date

## Scheduling

### Linux/Mac (cron)

Add to your crontab to run daily at 6 PM:

```bash
crontab -e
```

Add this line (adjust path as needed):

```
0 18 * * * cd /home/eric/Documents/repos/financial/signaltrackers && source venv/bin/activate && python credit_signals.py >> logs/credit_signals.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at desired time
4. Action: Start a program
5. Program: `python`
6. Arguments: `credit_signals.py`
7. Start in: `C:\path\to\signaltrackers`

## Notes

- FRED data typically updates on business days
- ETF data only available on trading days
- The script handles missing data gracefully
- Spreads are stored in basis points (bp) for FRED data
- ETF spreads are calculated as price ratios (proxy for yield spreads)

## Troubleshooting

**No FRED data collected:**
- Verify your API key is set correctly
- Check you have internet connectivity
- Ensure the series IDs are valid

**No ETF data collected:**
- Ensure yfinance is installed: `pip install yfinance`
- Check ticker symbols are valid
- Verify market hours (data may not be available immediately)

**Duplicate data:**
- The script automatically prevents duplicates by date
- If you see duplicates, check the date format in your CSV files
