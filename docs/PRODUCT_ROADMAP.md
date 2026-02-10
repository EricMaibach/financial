# SignalTrackers Product Roadmap

**Last Updated:** 2026-02-09
**Status:** Active Development
**Target Audience:** Individual investors with $100K+ portfolios

---

## Product Vision

SignalTrackers is a **comprehensive macro intelligence platform** for individual investors who want to understand market conditions without reading dozens of financial sources daily.

### Core Value Proposition
- **Synthesis over data dump:** AI-powered briefings distill what matters
- **Personal context:** Portfolio analysis against current market conditions
- **Historical perspective:** Percentile rankings show where we are historically
- **Broad coverage:** Credit, equities, rates, crypto, currencies, safe havens

### What We Are NOT
- A trading signal service
- A single-thesis product (e.g., "gold vs credit")
- A real-time trading platform
- A replacement for financial advisors

---

## Current State Assessment

Based on independent product review (February 2026):

| Criteria | Score | Notes |
|----------|-------|-------|
| Feature completeness | 7/10 | Missing alerts, onboarding friction |
| Ease of use | 6/10 | API key setup is a barrier |
| Data quality | 8/10 | 50+ metrics, 10+ years history |
| AI integration | 8/10 | Dual provider support, good synthesis |
| Design/UX | 6/10 | Functional but not polished |
| **Overall** | **7.5/10** | |

### Key Problem Identified
The product has been perceived as narrowly focused on gold/credit divergence. This is a **positioning failure**, not a feature issue. We track 50+ metrics across all asset classes, but one metric became our perceived identity.

---

## Prioritized Roadmap

### Phase 1: Repositioning & Core Gaps (Weeks 1-5)

#### 1.1 Homepage & Positioning Overhaul
**Priority:** CRITICAL
**Status:** [x] ✅ COMPLETE (2026-02-09)
**Effort:** 2 weeks

**Problem:** Divergence metric dominates, creating single-thesis perception.

**Deliverables:**
- [x] Redesign homepage to lead with "Today's Market Briefing"
- [x] Add balanced metric grid: Credit | Equities | Rates | Safe Havens | Crypto | Dollar
- [x] Create "What's Moving Today" section (top movers across ALL categories)
- [x] Move divergence to "Signals" section (one of several)
- [x] Update tagline: "Comprehensive macro intelligence for individual investors"
- [x] Remove hero messaging about gold vs. credit

**Files to Modify:**
- `signaltrackers/templates/index.html`
- `signaltrackers/templates/base.html` (navigation)
- `signaltrackers/static/css/` (styling updates)
- `signaltrackers/dashboard.py` (new API endpoints if needed)

---

#### 1.2 Market Conditions Summary Card
**Priority:** HIGH
**Status:** [ ] Not Started
**Effort:** 1 week

**Problem:** Users want quick "what should I know" without reading multiple briefings.

**Deliverables:**
- [ ] New homepage widget: "Market Conditions at a Glance"
- [ ] Status indicators for each dimension:
  - Credit: Tight / Normal / Stressed / Crisis
  - Equities: Risk-On / Neutral / Risk-Off
  - Rates: Rising / Stable / Falling / Inverted
  - Volatility: Calm / Elevated / Spiking
  - Dollar: Strong / Neutral / Weak
  - Liquidity: Expanding / Stable / Contracting
- [ ] One-sentence AI synthesis
- [ ] Click-through to detailed views

**Files to Modify:**
- `signaltrackers/templates/index.html`
- `signaltrackers/dashboard.py` (aggregation endpoint)
- `signaltrackers/static/js/dashboard.js`

---

#### 1.3 Alert System
**Priority:** HIGH
**Status:** [ ] Not Started
**Effort:** 2-3 weeks

**Problem:** Monitoring tool with no notifications. Users must manually check.

**Deliverables:**
- [ ] Database model for user alert preferences
- [ ] Alert threshold settings in user Settings page
- [ ] Pre-configured "smart alerts":
  - [ ] VIX spike (>25, >30)
  - [ ] Credit spreads widening (>50bp weekly move)
  - [ ] Yield curve inversion/un-inversion
  - [ ] Equity breadth deterioration
  - [ ] Significant moves in any tracked metric
- [ ] Email notification system (using Flask-Mail or similar)
- [ ] Daily briefing email option
- [ ] Background job to check thresholds (integrate with APScheduler)
- [ ] Alert history page

**New Files:**
- `signaltrackers/models/alert.py`
- `signaltrackers/services/email_service.py`
- `signaltrackers/templates/alerts.html`
- `signaltrackers/templates/settings_alerts.html`

**Files to Modify:**
- `signaltrackers/dashboard.py` (new routes)
- `signaltrackers/extensions.py` (email setup)
- `signaltrackers/requirements.txt` (Flask-Mail)

---

### Phase 2: Consolidation & Templates (Weeks 6-7)

#### 2.1 Signals Page Consolidation
**Priority:** MEDIUM-HIGH
**Status:** [ ] Not Started
**Effort:** 1-2 weeks

**Problem:** Divergence has its own nav item, implying outsized importance.

**Deliverables:**
- [ ] New unified "Signals" page replacing standalone Divergence page
- [ ] Track ALL cross-market signals:
  - Gold/Credit Divergence
  - Yield Curve Status
  - Breadth vs. Index (concentration)
  - VIX Term Structure
  - Credit ETF vs. Index spread
  - Bitcoin vs. Liquidity
  - Dollar vs. Equities correlation
- [ ] Each signal shows: Current state, percentile, trend, "What This Means"
- [ ] Update navigation to consolidate

**Files to Modify:**
- `signaltrackers/templates/base.html` (navigation)
- `signaltrackers/templates/divergence.html` → rename/refactor to `signals.html`
- `signaltrackers/dashboard.py` (routes)

---

#### 2.2 Portfolio Templates
**Priority:** MEDIUM
**Status:** [ ] Not Started
**Effort:** 1 week

**Problem:** Empty portfolio page has no quick-start option.

**Deliverables:**
- [ ] "Start from Template" button on empty portfolio
- [ ] Template options:
  - 60/40 Traditional (60% SPY, 40% AGG)
  - All-Weather (30% stocks, 40% long bonds, 15% intermediate, 7.5% gold, 7.5% commodities)
  - Tech Growth (50% QQQ, 20% SMH, 15% individual tech, 15% cash)
  - Dividend Income (40% VYM, 30% SCHD, 20% bonds, 10% REITs)
  - Defensive (40% stocks, 30% bonds, 15% gold, 15% cash)
- [ ] "Analyze This Template" instant AI feedback
- [ ] Modify and save as personal portfolio

**New Files:**
- `signaltrackers/portfolio_templates.py` (template definitions)

**Files to Modify:**
- `signaltrackers/templates/portfolio.html`
- `signaltrackers/dashboard.py`
- `signaltrackers/static/js/portfolio.js`

---

### Phase 3: Onboarding & Trial (Week 8)

#### 3.1 Hosted Trial Mode
**Priority:** MEDIUM
**Status:** [ ] Not Started
**Effort:** 1 week

**Problem:** AI features require user API key, creating signup friction.

**Deliverables:**
- [ ] Track AI usage credits per user (new field in user model)
- [ ] 10 free AI interactions for new users
- [ ] System API key fallback for trial users
- [ ] Clear messaging when credits exhausted
- [ ] "Add your API key to continue" upgrade prompt

**Files to Modify:**
- `signaltrackers/models/user.py` (add credits field)
- `signaltrackers/services/ai_service.py` (credit checking)
- `signaltrackers/dashboard.py` (credit deduction)
- `signaltrackers/templates/settings.html` (credits display)

---

#### 3.2 Onboarding Wizard
**Priority:** MEDIUM
**Status:** [ ] Not Started
**Effort:** 1 week

**Problem:** Users drop off between registration and first value.

**Deliverables:**
- [ ] Post-registration wizard flow:
  - Step 1: Investment style (Conservative / Balanced / Growth / Macro-aware)
  - Step 2: Start with template or build own?
  - Step 3: Enable AI features? (trial credits explanation)
  - Step 4: Set up alerts? (quick defaults)
- [ ] Progress indicator
- [ ] Skip option on every step
- [ ] Track onboarding completion

**New Files:**
- `signaltrackers/templates/onboarding/` (wizard steps)

**Files to Modify:**
- `signaltrackers/dashboard.py` (onboarding routes)
- `signaltrackers/models/user.py` (onboarding_complete flag)

---

### Phase 4: Mobile & Polish (Weeks 9-10)

#### 4.1 Mobile Experience Improvements
**Priority:** MEDIUM
**Status:** [ ] Not Started
**Effort:** 2 weeks

**Problem:** Mobile is "adequate" but our users check on phones.

**Deliverables:**
- [ ] Collapsible metric cards (show value + change, expand for details)
- [ ] Bottom navigation bar for mobile
- [ ] "Today's Briefing" prominent on mobile homepage
- [ ] Touch-optimized chart interactions
- [ ] Portfolio entry form redesigned for mobile
- [ ] Responsive testing across devices

**Files to Modify:**
- `signaltrackers/static/css/` (responsive styles)
- `signaltrackers/templates/*.html` (responsive markup)
- `signaltrackers/static/js/` (touch interactions)

---

## Backlog (Future Consideration)

Items identified but not prioritized for current cycle:

| Feature | Notes | Priority |
|---------|-------|----------|
| Push notifications | Requires mobile app or PWA | Low |
| ADR/International stock support | Expand portfolio coverage | Low |
| Backtesting engine | Different product scope | Not planned |
| Real-time data | Cost vs. value for macro focus | Not planned |
| Options/derivatives in portfolio | Niche need, high complexity | Not planned |
| Trade signals | Liability concerns, out of scope | Not planned |

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| User perception: "comprehensive" vs "niche" | ~30% / 70% | 70% / 30% | User survey |
| Signup → Active User conversion | ~30% | 55% | Analytics |
| Pages visited per session | 2-3 | 4-5 | Analytics |
| Users with alerts configured | 0% | 50% | Database query |
| Mobile session duration | Baseline TBD | +25% | Analytics |
| AI feature usage (trial users) | 0 | 80% try within first session | Analytics |

---

## What We're NOT Building

Explicitly out of scope to maintain focus:

1. **Trade signals or "buy/sell" recommendations** - Liability, different product
2. **Real-time streaming data** - Cost/complexity vs. macro user needs
3. **"Balanced" thesis presentation** - We report data objectively; we don't need to artificially balance every metric
4. **Options/derivatives portfolio support** - Serves <15% of users, high complexity
5. **Mobile native app** - Web responsive is sufficient for now
6. **Backtesting engine** - Different product entirely

---

## Technical Debt & Cleanup

Items to address alongside feature work:

- [ ] Remove/rename `README_DIVERGENCE.md` (reinforces old positioning)
- [ ] Audit AI prompts for thesis-specific language
- [ ] Review homepage template for divergence-heavy content
- [ ] Update any marketing copy in templates

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-09 | Initial roadmap created | PM |
| 2026-02-09 | Phase 1.1 Homepage Overhaul marked COMPLETE | PM |

---

*This document is the source of truth for product direction. Update as items are completed or priorities shift.*
