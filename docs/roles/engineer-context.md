# Engineer Context & Memory Bank

**Last Updated:** 2026-02-12
**Project:** SignalTrackers - Macro Financial Dashboard

---

## Architectural Decisions

### Tech Stack
- **Backend:** Python 3.x, Flask
- **Frontend:** Jinja2 templates, vanilla JavaScript (minimal), CSS
- **Data Storage:** CSV files for historical metrics
- **AI Providers:** OpenAI and Anthropic (dual support)
- **Deployment:** TBD

### Key Design Principles
1. Simple over clever - maintainability matters
2. Progressive enhancement for frontend
3. Support multiple AI providers (no vendor lock-in)
4. CSV-based data storage for simplicity and transparency
5. Environment-based configuration (never commit secrets)

---

## Code Patterns & Conventions

### Flask Application Structure
- Main entry point: `signaltrackers/dashboard.py`
- Templates: `signaltrackers/templates/`
- Static assets: `signaltrackers/static/`
- Data collection: `signaltrackers/market_signals.py`

### Common Patterns
- (To be documented as patterns emerge)

### Naming Conventions
- (To be documented as patterns emerge)

---

## Environment Variables

**CRITICAL:** Never edit `.env` directly. Only update `.env.example` and ask user to update their `.env`.

### Current Variables
- See `.env.example` for complete list
- AI API keys (OpenAI, Anthropic)
- Configuration flags for AI provider selection

---

## External Services & APIs

### Market Data Sources
- (To be documented as integrations are built)

### AI Integration
- **OpenAI:** GPT models for AI summaries
- **Anthropic:** Claude models for AI summaries
- Both providers supported, user-configurable

---

## Data Model

### CSV Data Files
Location: `signaltrackers/data/`

- (Document schemas as files are created/modified)

---

## Known Issues & Technical Debt

### Current Technical Debt
- (Document as discovered)

### Security Considerations
- `.env` file excluded from git (contains API keys)
- Input validation needed at all user input points
- Template output escaping for XSS prevention

---

## Performance Considerations

### Current Performance Notes
- (Document performance bottlenecks, optimizations, caching strategies)

### Monitoring & Logging
- (Document logging patterns, monitoring setup)

---

## Testing Strategy

### Manual Testing Checklist
1. Run `python signaltrackers/dashboard.py`
2. Test in browser at http://localhost:5000
3. Verify mobile responsiveness
4. Test error cases

### Test Data
- (Document test data sources, fixtures)

---

## Deployment & Operations

### Running Locally
```bash
cd signaltrackers
python dashboard.py
```

### Data Collection
```bash
python signaltrackers/market_signals.py
```

### Environment Setup
- Python 3.x required
- Dependencies: (document as added)
- API keys required: OpenAI and/or Anthropic

---

## Common Gotchas & Lessons Learned

### Lessons from Development
- **AI summaries**: Eastern Time display preferred over UTC (fixed in issue #60)
- **Briefing frequency**: 15-minute interval for daily briefings (fixed in issue #64)
- (Add more as discovered)

---

## Key Files & Their Purpose

| File/Directory | Purpose |
|----------------|---------|
| `signaltrackers/dashboard.py` | Main Flask application entry point |
| `signaltrackers/market_signals.py` | Data collection for market metrics |
| `signaltrackers/templates/` | Jinja2 HTML templates |
| `signaltrackers/static/` | CSS, JavaScript, images |
| `signaltrackers/data/` | CSV data files for metrics |
| `.env` | **NEVER COMMIT** - Contains API keys and secrets |
| `.env.example` | Template for environment variables |

---

## Session History

### 2026-02-12
- **Created:** Initial engineer context file
- **Status:** Template created, to be populated as work progresses

---

*This file is the engineer's memory bank. Update it at the end of each session with important decisions, patterns, and lessons learned.*
