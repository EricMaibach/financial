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

#### Database Migrations
- Use Alembic for database migrations
- Migration files located in `signaltrackers/migrations/versions/`
- Run migrations: `cd signaltrackers && source venv/bin/activate && flask --app dashboard db upgrade`
- Follow naming convention: `<revision>_<description>.py`

#### Deduplication Pattern
When preventing duplicate scheduled operations:
1. Add a tracking field to the model (e.g., `last_sent_date`)
2. Check field value in user's timezone before executing
3. Update field after successful execution
4. Always use user's timezone for date comparisons to handle day boundaries correctly

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

### Database Tables

#### AlertPreference Model
Location: `signaltrackers/models/alert.py`

Key fields for daily briefing deduplication:
- `last_briefing_sent_date` (Date, nullable) - Tracks last date briefing was sent to prevent duplicates
- `briefing_time` (Time) - User's preferred briefing time
- `briefing_timezone` (String) - User's timezone for accurate day boundary detection
- `daily_briefing_enabled` (Boolean) - Whether briefings are enabled
- `briefing_frequency` (String) - 'daily', 'weekly', or 'off'

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
- **Duplicate briefings**: When scheduler runs on intervals (not cron), always add deduplication tracking to prevent multiple sends during target window (fixed in issue #68)
- **Timezone handling**: Always use user's timezone for date comparisons when tracking "daily" operations to correctly handle day boundaries

---

## Key Files & Their Purpose

| File/Directory | Purpose |
|----------------|---------|
| `signaltrackers/dashboard.py` | Main Flask application entry point |
| `signaltrackers/market_signals.py` | Data collection for market metrics |
| `signaltrackers/jobs/email_jobs.py` | Scheduled jobs for sending briefing emails |
| `signaltrackers/services/briefing_email_service.py` | Daily briefing email generation and sending |
| `signaltrackers/models/alert.py` | AlertPreference and Alert database models |
| `signaltrackers/templates/` | Jinja2 HTML templates |
| `signaltrackers/static/` | CSS, JavaScript, images |
| `signaltrackers/data/` | CSV data files for metrics |
| `signaltrackers/migrations/versions/` | Alembic database migration files |
| `.env` | **NEVER COMMIT** - Contains API keys and secrets |
| `.env.example` | Template for environment variables |

---

## Session History

### 2026-02-12 (Session 2)
- **Fixed:** Issue #68 - Daily briefing duplicate emails
- **Changes:**
  - Added `last_briefing_sent_date` field to AlertPreference model
  - Implemented deduplication logic in `send_daily_briefing_to_user()`
  - Created database migration `f1a2b3c4d5e6_add_last_briefing_sent_date.py`
  - Ensures exactly one briefing per day per user
- **Technical Decision:** Use database-backed deduplication (not in-memory) to survive app restarts
- **Commit:** dd1b754

### 2026-02-12 (Session 1)
- **Created:** Initial engineer context file
- **Status:** Template created, to be populated as work progresses

---

*This file is the engineer's memory bank. Update it at the end of each session with important decisions, patterns, and lessons learned.*
