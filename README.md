# SignalTrackers

**Comprehensive macro intelligence for individual investors**

Stop reading dozens of financial sources daily. SignalTrackers synthesizes 50+ market indicators across all asset classes into clear, actionable intelligence - helping you understand market conditions at a glance.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 What is SignalTrackers?

SignalTrackers is a **macro financial dashboard** designed for individual investors with significant portfolios ($100K+) who want professional-grade market intelligence without the noise.

### The Problem
Individual investors face information overload:
- Dozens of financial sites to monitor daily
- Data without context or historical perspective
- No synthesis showing how signals relate to each other
- Unclear how market conditions affect *your* specific portfolio

### The Solution
SignalTrackers provides:
- **AI-powered briefings** that distill what matters from 50+ metrics
- **Personal context** - see how current conditions affect your portfolio
- **Historical perspective** - percentile rankings show where we are vs. 10+ years of data
- **Comprehensive coverage** - credit, equities, rates, crypto, currencies, safe havens

---

## ✨ Key Features

### 📊 Market Intelligence
- **50+ Macro Indicators**: Credit spreads, equity volatility, Treasury curves, currency flows, crypto sentiment, and more
- **Historical Context**: Every metric includes percentile rankings vs. 10+ years of data
- **AI Synthesis**: Daily briefings explain what's happening and why it matters
- **What's Moving Today**: Instant view of the biggest market shifts

### 💼 Portfolio Analysis
- **Personal Context**: See how current market conditions affect your specific holdings
- **Risk Assessment**: Understand your exposure to different market regimes
- **Template Library**: Quick setup with pre-built allocations (60/40, All Weather, etc.)

### 🔔 Smart Alerts
- **Custom Thresholds**: Get notified when metrics cross levels that matter to you
- **Email Delivery**: Daily briefings and alerts sent to your inbox
- **Flexible Scheduling**: Choose your briefing frequency and delivery times

### 🤖 AI-Powered Chat
- **Conversational Analysis**: Ask questions about market data in natural language
- **Historical Queries**: "What happened to VIX in March 2020?" or "Show me credit spreads during 2008"
- **Multi-Provider Support**: Choose between OpenAI and Anthropic Claude

---

## 🚀 Why SignalTrackers?

### Comprehensive, Not Niche
We track the full macro picture - not just one thesis or asset class. Our coverage spans:
- Credit markets (HY spreads, IG spreads, TED spread)
- Equity markets (VIX, sector performance, market breadth)
- Fixed income (yield curves, TIPS breakevens)
- Currencies (DXY, EM flows, crypto)
- Safe havens (gold, Treasuries, volatility)

### Signal Synthesis, Not Data Dump
Our AI briefings don't just list what happened - they explain:
- **What's significant** - Which moves are historically unusual?
- **What it means** - How do different signals relate to each other?
- **What to watch** - Where might conditions be shifting?

### Built for Individual Investors
Unlike institutional tools, SignalTrackers:
- Runs on your laptop - no subscriptions or data fees for core features
- Supports typical retail portfolios - stocks, bonds, ETFs
- Focuses on macro conditions - not trade signals or timing models
- Respects your time - briefings over real-time data feeds

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.11 or higher
- (Optional) API keys for AI providers (OpenAI or Anthropic Claude)
- (Optional) FRED API key for automatic data updates

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/EricMaibach/financial.git
   cd financial
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (see Configuration section)
   ```

3. **Install dependencies**
   ```bash
   cd signaltrackers
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   # Migrations will run automatically on first launch
   python dashboard.py
   ```

5. **Access the dashboard**
   ```
   Open http://localhost:5000 in your browser
   ```

### Configuration

Edit your `.env` file with the following:

#### Required (for multi-user mode)
- `SECRET_KEY` - Flask session secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `ENCRYPTION_KEY` - API key encryption (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)

#### Optional (but recommended)
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - For AI briefings and chat
- `FRED_API_KEY` - For automatic data updates ([get your key](https://fred.stlouisfed.org/docs/api/api_key.html))
- `TAVILY_API_KEY` - For web search in AI chat ([get your key](https://tavily.com/))

#### Email Alerts (optional)
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` - SMTP configuration for alerts
- We recommend [Brevo (Sendinblue)](https://www.brevo.com) - 300 emails/day free tier

See [`.env.example`](.env.example) for complete configuration options.

### Data Collection

SignalTrackers includes historical data for immediate use. To update with latest market data:

```bash
python signaltrackers/market_signals.py
```

Set up automated daily updates with cron:
```bash
0 18 * * 1-5 cd /path/to/signaltrackers && python market_signals.py
```

For detailed data collection setup, see [`signaltrackers/DATA_COLLECTION_GUIDE.md`](signaltrackers/DATA_COLLECTION_GUIDE.md).

---

## 📖 Documentation

- **[Dashboard Quick Start](signaltrackers/DASHBOARD_QUICKSTART.md)** - Get up and running fast
- **[Data Collection Guide](signaltrackers/DATA_COLLECTION_GUIDE.md)** - Setting up automated data updates
- **[Product Roadmap](docs/roles/pm-context.md)** - Vision and planned features
- **[Contributing Guide](CLAUDE.md)** - Development workflow and standards

---

## 🗺️ Product Vision

SignalTrackers aims to be the **go-to macro intelligence platform for individual investors**.

### What We Are
- A comprehensive market dashboard synthesizing 50+ indicators
- An AI-powered briefing service explaining what's happening
- A portfolio context tool showing how conditions affect your holdings

### What We're NOT
- ❌ A trading signal service (no "buy/sell" recommendations)
- ❌ A real-time trading platform (macro focus, daily updates)
- ❌ A single-thesis product (comprehensive coverage, not one narrative)

### Success Metrics
We measure success by:
- User perception: "comprehensive macro intelligence" vs. "niche tool"
- Signup → Active User conversion
- AI feature trial usage within first session
- Users with configured alerts

---

## 🤝 Contributing

We welcome contributions! SignalTrackers is actively developed and open to:
- Bug fixes and feature improvements
- New data sources or metrics
- UI/UX enhancements
- Documentation improvements

See [CLAUDE.md](CLAUDE.md) for development workflow, including:
- GitHub issue management
- Milestone-based planning
- PR submission process

---

## 📊 Project Status

**Current Version**: 2.0 (Phase 2: Consolidation & Templates)

**Recent Milestones**:
- ✅ Phase 1: Repositioning & Core Gaps - Homepage overhaul, comprehensive metric coverage
- 🔄 Phase 2: Consolidation & Templates - Streamlining pages, portfolio templates
- 📋 Phase 3: Onboarding & Trial - Hosted trial mode, setup wizard
- 📋 Phase 4: Mobile & Polish - Mobile experience, final polish

See [open issues](https://github.com/EricMaibach/financial/issues) for current work.

---

## 🔐 Security & Privacy

- **Local-first**: Runs on your machine - your portfolio data stays private
- **Encrypted credentials**: User API keys stored with Fernet encryption
- **No tracking**: No analytics, no data collection, no third-party tracking
- **Open source**: Audit the code yourself

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/EricMaibach/financial/issues)
- **Documentation**: See `docs/` directory for detailed guides
- **Questions**: Open a discussion or issue on GitHub

---

## 🌟 Why "SignalTrackers"?

The name reflects our philosophy: we **track signals** across the full macro landscape - not just one thesis, not just equities, not just credit. We synthesize diverse market indicators into clear intelligence, helping you separate signal from noise.

---

**Ready to get started?** Follow the [Quick Start](#-getting-started) guide above or check out the [Dashboard Quick Start](signaltrackers/DASHBOARD_QUICKSTART.md) for a detailed walkthrough.
