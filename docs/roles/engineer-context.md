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

### 2026-02-15 (Session 5)
- **Implemented:** Issue #72 (US-2.0.3) - Refine Market Conditions Widget Expansion UX
- **Changes:**
  - Replaced US-2.0.1 implementation with refined version
  - Created compact badge cards (6 cards in 2x3 grid) showing category name, icon, and status
  - Moved existing detailed cards into expandable state (hidden by default)
  - Added subtle horizontal divider expansion control with chevron icons
  - Implemented smooth CSS transitions (350ms ease-in-out) with opacity + height animations
  - AI synthesis now always visible above widgets (not hidden in either state)
  - Removed old `updateSummaryWidget()` function, replaced with `updateBadgeStatuses()`
  - Updated `loadMarketSynthesis()` to use new element ID: `market-synthesis-text`
- **Files Modified:**
  - `signaltrackers/templates/index.html` (replaced Market Conditions section)
  - `signaltrackers/static/css/dashboard.css` (added ~200 lines of CSS for badges, expansion control, animations, responsive design)
- **Technical Decisions:**
  - **Widget-level expansion:** All 6 widgets expand/collapse together (not individual expansion) to keep homepage simple and predictable
  - **Mutually exclusive states:** Badges OR cards visible, never both simultaneously, to avoid redundancy and visual clutter
  - **Subtle control design:** Horizontal divider with chevron (not prominent button) to feel like part of panel structure
  - **Natural positioning:** Badges expand into cards in same grid positions (Credit top-left → Credit card top-left) for visual continuity
  - **Always-visible synthesis:** AI market synthesis remains visible in both states to provide context
- **UX Pattern Established:**
  - Progressive disclosure for homepage widgets: compact summary by default, detailed view on demand
  - Expansion control should be subtle (divider + chevron) not prominent (bright button)
  - Use CSS opacity/visibility/height transitions for smooth animations (not just display switching)
  - Grid position mapping for expansion creates intuitive widget-grows-in-place feel
- **Accessibility:**
  - Added `aria-expanded` attribute to toggle button
  - Added `aria-label` for screen reader clarity
  - Keyboard accessible (tab + enter to toggle)
  - Focus visible on control
- **Responsive Design:**
  - Desktop: 2x3 grid for both badges and cards
  - Tablet: 2x3 grid (maintained)
  - Mobile: 2x2 grid for badges and cards (6 items wrap to 3 rows)
- **Bugs Fixed (post-PR feedback):**
  - Fixed missing animations (was using display switching, now uses opacity + visibility + height)
  - Fixed layout spacing issues (hidden elements were taking up space, now properly collapsed)
- **Commits:** 9b7aef7 (initial), e7f02fd (animation fix), bf96192 (spacing fix)
- **PR:** #73
- **Status:** Implementation complete with animation and spacing fixes, supersedes US-2.0.1

### 2026-02-13 (Session 4)
- **Implemented:** Issue #36 - US-2.0.1 Market Conditions Progressive Disclosure
- **Changes:**
  - Modified `signaltrackers/templates/index.html` to implement progressive disclosure pattern
    - Wrapped Market Conditions summary widget and grid in `.market-conditions-section` container
    - Added toggle button between summary and grid sections with "Show Details ↓" / "Hide Details ↑" labels
    - Grid hidden by default with `style="display:none"`
    - JavaScript toggle functionality to show/hide grid and swap button text on click
  - Modified `signaltrackers/static/css/dashboard.css`
    - Added `.market-conditions-section` container styles
    - Added `.market-conditions-grid-expandable` with 300ms CSS transition for smooth expand/collapse
    - Added toggle button hover effects (slight lift + shadow)
- **Technical Decision:** Progressive disclosure pattern for dashboard sections
  - Summary widget always visible (6 status indicators + AI synthesis)
  - Full detail view (6-card grid) collapsed by default to reduce visual overwhelm
  - Smooth CSS transitions (300ms ease-in-out) for better UX
  - Button text changes to clearly indicate current state and available action
- **Pattern Established:** Progressive disclosure implementation approach
  - Grid uses `display:none` when collapsed (removed from layout, not just visually hidden)
  - DOMContentLoaded event listener ensures safe DOM manipulation
  - Null checks on all DOM elements before attaching event listeners
  - Button state managed via inline `style.display` toggling for both grid and text spans
  - Transition applied via CSS `transition: all 0.3s ease-in-out` for smooth animation
- **Files Modified:**
  - `signaltrackers/templates/index.html` (lines 64-102, 165-372, 470-493)
  - `signaltrackers/static/css/dashboard.css` (lines 1236-1260 - added progressive disclosure section)
- **Testing Notes:**
  - Implementation verified through file inspection and code review
  - HTML structure validated: proper nesting, IDs present, default state correct
  - JavaScript logic validated: toggle works both ways, text swaps correctly
  - CSS transitions validated: 300ms timing matches specification
  - **Production server (Gunicorn) requires restart to pick up template changes**
- **Next Steps:**
  - Production server restart needed to see changes live
  - QA testing against test plan (docs/test-plans/US-2.0.1-test-plan.md)
  - Cross-browser and mobile testing per acceptance criteria
- **PR:** #71
- **Status:** Merged to main, superseded by US-2.0.3

### 2026-02-12 (Session 3)
- **Implemented:** Issue #69 - Include AI Market Briefing in Daily Email with Graceful Degradation
- **Changes:**
  - Modified `briefing_email_service.py` to remove blocking logic when AI briefing unavailable
  - Added conditional rendering in `daily_briefing.html` and `daily_briefing.txt` templates
  - Changed log level from warning to info when AI briefing is unavailable
  - **Bug Fix:** Fixed dictionary key mismatch (`'narrative'` → `'summary'`) causing empty AI content in emails
  - **Added:** `_extract_synthesis()` helper function to generate briefing one-liner from summary text
- **Technical Decision:** Graceful degradation pattern - email delivery continues even when optional AI features fail
- **Pattern Established:** When adding optional AI-powered features to emails:
  1. Never block email delivery on AI feature failure
  2. Use conditional template rendering (`{% if variable %}...{% endif %}`)
  3. Log at appropriate level (info for expected cases, warning for unexpected failures)
  4. Provide fallback values (None/empty dict) rather than early returns
- **Bug Discovered:** Email code used wrong dictionary keys ('narrative', 'one_liner') while AI summaries save with key 'summary'
  - Dashboard code was correct: `summary.get('summary', '')`
  - Email code was wrong: `summary.get('narrative', '')` → always returned empty string
  - Result: Emails showed headers but no AI content even when briefing existed
- **Commits:** 0212916 (graceful degradation), 5681319 (key mismatch fix)
- **PR:** #70

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
