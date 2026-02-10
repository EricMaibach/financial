# Phase 1.1: Homepage Overhaul Feature Specification

**Document Version:** 1.1
**Created:** 2026-02-09
**Status:** ✅ COMPLETE
**Completed:** 2026-02-09
**Estimated Effort:** 2 weeks
**Priority:** CRITICAL

---

## Executive Summary

The homepage overhaul addresses a critical positioning failure: SignalTrackers is perceived as a single-thesis "gold vs. credit" tool despite tracking 50+ metrics across all asset classes. This feature redesigns the homepage to communicate our value proposition as a **comprehensive macro intelligence platform**.

---

## Problem Statement

### Current State Issues

1. **Divergence Dominance:** The current homepage emphasizes the gold/credit divergence metric, creating a narrow "single thesis" perception
2. **Scattered Information:** Key metrics are not organized by asset class, making it hard for users to quickly assess market conditions
3. **Buried Value:** The AI-powered daily briefing exists but doesn't command attention as the primary value proposition
4. **Inconsistent Messaging:** Hero content and navigation reinforce the divergence focus
5. **No Quick Movers View:** Users can't quickly see what's moving unusually across ALL categories

### User Impact

- **30% of users perceive SignalTrackers as "comprehensive"** (target: 70%)
- Users visit only 2-3 pages per session (target: 4-5)
- New users don't immediately understand the breadth of coverage

---

## Goals & Success Metrics

| Goal | Metric | Baseline | Target |
|------|--------|----------|--------|
| Reposition as comprehensive platform | User survey: "comprehensive" perception | 30% | 70% |
| Increase engagement | Pages visited per session | 2-3 | 4-5 |
| Showcase AI value | Users reading daily briefing | ~40% | 80% |
| Surface all asset classes | Time to find non-divergence metrics | >30 sec | <10 sec |

---

## Design Specification

### New Homepage Layout (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NAVIGATION BAR                                                          │
│  [Logo] Dashboard | Markets | Signals | Explorer | Portfolio | [User]    │
│  New tagline: "Comprehensive macro intelligence for individual investors"│
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SECTION 1: TODAY'S MARKET BRIEFING (HERO)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ 📊 Today's Market Briefing                          Feb 9, 2026    ││
│  │ ─────────────────────────────────────────────────────────────────  ││
│  │ [AI-generated 2-3 paragraph synthesis of market conditions]        ││
│  │                                                                     ││
│  │ Key Points:                                                         ││
│  │ • Credit markets showing stress signals...                          ││
│  │ • Equities diverging from fundamentals...                           ││
│  │ • Safe haven demand elevated...                                     ││
│  │                                                                     ││
│  │ [Regenerate Briefing]                      Generated: 8:30 AM ET   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SECTION 2: WHAT'S MOVING TODAY                                         │
│  ┌────────────┬────────────┬────────────┬────────────┬────────────────┐│
│  │ #1         │ #2         │ #3         │ #4         │ #5             ││
│  │ VIX        │ Gold       │ BTC        │ HY Spread  │ 10Y Yield      ││
│  │ ▲ +15.2%   │ ▲ +2.1%    │ ▼ -4.3%    │ ▲ +18bp    │ ▲ +8bp         ││
│  │ z: 2.4     │ z: 1.8     │ z: 1.6     │ z: 1.5     │ z: 1.4         ││
│  │ [UNUSUAL]  │ [ELEVATED] │ [ELEVATED] │ [UNUSUAL]  │ [NOTABLE]      ││
│  └────────────┴────────────┴────────────┴────────────┴────────────────┘│
│  Ranked by statistical significance (z-score) across all 50+ metrics   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SECTION 3: MARKET CONDITIONS GRID                                      │
│  ┌─────────────────┬─────────────────┬─────────────────────────────────┐│
│  │ CREDIT          │ EQUITIES        │ RATES                           ││
│  │ ────────────    │ ────────────    │ ────────────                    ││
│  │ HY Spread: 385bp│ S&P 500: 5,124  │ 10Y: 4.25%                      ││
│  │ IG Spread: 95bp │ Russell: 2,089  │ 2Y: 4.15%                       ││
│  │ CCC Ratio: 0.45 │ VIX: 18.5       │ Curve: +10bp                    ││
│  │ Status: STRESSED│ Status: RISK-ON │ Status: INVERTED                ││
│  │ [View Credit →] │ [View Equities→]│ [View Rates →]                  ││
│  ├─────────────────┼─────────────────┼─────────────────────────────────┤│
│  │ SAFE HAVENS     │ CRYPTO          │ DOLLAR                          ││
│  │ ────────────    │ ────────────    │ ────────────                    ││
│  │ Gold: $2,145    │ Bitcoin: $67,234│ DXY: 103.5                      ││
│  │ Silver: $25.80  │ ETH: $3,456     │ EUR/USD: 1.085                  ││
│  │ TLT: $92.50     │ BTC Dom: 52%    │ USD/JPY: 148.2                  ││
│  │ Status: ELEVATED│ Status: NEUTRAL │ Status: STRONG                  ││
│  │ [View Havens →] │ [View Crypto →] │ [View Dollar →]                 ││
│  └─────────────────┴─────────────────┴─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SECTION 4: MARKET SIGNALS (formerly Divergence)                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Active Signals                                                     │  │
│  │ ┌─────────────────┬─────────────────┬─────────────────┐           │  │
│  │ │ Gold/Credit     │ Yield Curve     │ VIX Term        │           │  │
│  │ │ Divergence      │ Inversion       │ Structure       │           │  │
│  │ │ ⚠️ ELEVATED     │ ⚠️ INVERTED     │ ✓ NORMAL        │           │  │
│  │ │ 78th percentile │ 95th percentile │ 45th percentile │           │  │
│  │ └─────────────────┴─────────────────┴─────────────────┘           │  │
│  │ [View All Signals →]                                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SECTION 5: ADDITIONAL INSIGHTS                                         │
│  ┌────────────────────────┬────────────────────────────────────────────┐│
│  │ MARKET CONCENTRATION   │ PREDICTION MARKETS                         ││
│  │ Tech/SPY: 32% (⚠️)    │ Recession 2026: 35%                        ││
│  │ Semis/SPY: 8% (⚠️)    │ Fed Cut >25bp: 62%                         ││
│  └────────────────────────┴────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  FLOATING AI CHAT (unchanged)                                           │
│  [💬 Ask about markets]                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Section Specifications

### Section 1: Today's Market Briefing (Hero)

**Purpose:** Lead with AI-powered synthesis to showcase primary value proposition

**Requirements:**
- Full-width card with prominent styling (gradient header or border)
- Large typography for briefing text (18px body, 24px heading)
- Structured format with:
  - 2-3 paragraph narrative summary
  - Bulleted "Key Points" (3-5 items)
  - Clear attribution: "AI-generated based on current market data"
- Timestamp showing when briefing was generated
- "Regenerate Briefing" button (rate-limited, 1 per hour for free users)
- Loading skeleton state while briefing generates
- Fallback message if AI unavailable: "Market briefing generating... Check back shortly."

**Data Source:** `/api/ai-summary` endpoint (existing)

**Visual Design:**
- Primary color accent (blue gradient header)
- Card shadow for elevation
- Readable line height (1.6)
- Icon: 📊 or chart icon

---

### Section 2: What's Moving Today

**Purpose:** Surface unusual movements across ALL asset classes, not just divergence

**Requirements:**
- Horizontal card row showing top 5 movers
- Each card displays:
  - Metric name
  - Current value
  - Change (5-day, with direction arrow)
  - Z-score (statistical significance)
  - Severity badge: UNUSUAL (z>2), ELEVATED (z>1.5), NOTABLE (z>1)
- Ranked by absolute z-score (largest deviations first)
- Click on card navigates to metric detail page
- Responsive: wraps to 2 rows on mobile

**Data Source:** `/api/dashboard` endpoint → `top_movers` array (existing)

**Visual Design:**
- Horizontal scroll on mobile
- Color-coded by direction (green up, red down) AND severity
- Pulse animation on z-score > 2.5

---

### Section 3: Market Conditions Grid

**Purpose:** Provide balanced coverage of ALL major asset classes at a glance

**Requirements:**
- 6 equal-sized category cards in 3x2 grid (2x3 on mobile)
- Categories:
  1. **CREDIT** - HY Spread, IG Spread, CCC/HY Ratio
  2. **EQUITIES** - S&P 500, Russell 2000, VIX
  3. **RATES** - 10Y Yield, 2Y Yield, Curve Spread
  4. **SAFE HAVENS** - Gold, Silver, TLT (Long Treasuries)
  5. **CRYPTO** - Bitcoin, Ethereum, BTC Dominance
  6. **DOLLAR** - DXY, EUR/USD, USD/JPY

- Each card shows:
  - Category header with icon
  - 3 key metrics with current values
  - Status indicator: Risk level/condition (e.g., "STRESSED", "ELEVATED", "NORMAL")
  - "View [Category] →" link to detailed page

**Status Determination Logic:**

| Category | Status | Criteria |
|----------|--------|----------|
| Credit | CRISIS | HY Spread > 600bp |
| Credit | STRESSED | HY Spread > 400bp |
| Credit | TIGHT | HY Spread < 300bp |
| Credit | NORMAL | Otherwise |
| Equities | RISK-OFF | VIX > 25 |
| Equities | CAUTIOUS | VIX > 20 |
| Equities | RISK-ON | VIX < 15 |
| Equities | NEUTRAL | Otherwise |
| Rates | INVERTED | 10Y - 2Y < 0 |
| Rates | STEEP | 10Y - 2Y > 100bp |
| Rates | FLAT | 10Y - 2Y < 25bp |
| Rates | NORMAL | Otherwise |
| Safe Havens | ELEVATED | Gold 30-day return > 5% |
| Safe Havens | FLIGHT | Gold + TLT both up > 3% in 5 days |
| Safe Havens | NORMAL | Otherwise |
| Crypto | RISK-ON | BTC up > 10% in 30 days |
| Crypto | RISK-OFF | BTC down > 10% in 30 days |
| Crypto | NEUTRAL | Otherwise |
| Dollar | STRONG | DXY > 105 |
| Dollar | WEAK | DXY < 100 |
| Dollar | NEUTRAL | Otherwise |

**Data Source:** `/api/dashboard` endpoint (existing, may need aggregation)

**Visual Design:**
- Consistent card heights
- Category-specific accent colors:
  - Credit: Red
  - Equities: Blue
  - Rates: Purple
  - Safe Havens: Gold
  - Crypto: Orange
  - Dollar: Green
- Status badge with appropriate color (danger/warning/success/secondary)

---

### Section 4: Market Signals

**Purpose:** Reposition divergence as ONE of several cross-market signals

**Requirements:**
- Compact section showing 3 key signals with current status
- Signals to display:
  1. **Gold/Credit Divergence** - Existing metric, renamed
  2. **Yield Curve Status** - 10Y-2Y spread, inversion flag
  3. **VIX Term Structure** - Contango/backwardation indicator
- Each signal shows:
  - Signal name
  - Current status (icon + label)
  - Percentile ranking
- "View All Signals →" link to future unified Signals page (Phase 2.1)
- Note: This section prepares for Phase 2.1's full Signals page

**Data Source:** `/api/dashboard` endpoint (existing divergence data + new calculations)

**Visual Design:**
- Horizontal layout with 3 equal cards
- Muted styling compared to hero sections (secondary importance)
- Warning icons for elevated signals

---

### Section 5: Additional Insights

**Purpose:** Retain valuable concentration and prediction market data in secondary position

**Requirements:**
- Compact 2-column layout
- Left: Market Concentration metrics (Tech/SPY, Semis/SPY ratios)
- Right: Prediction Markets (Recession, Fed actions)
- Existing functionality preserved, just repositioned lower

**Data Source:** Existing endpoints

---

## Navigation Updates

### Current Navigation:
```
Dashboard | Equity Markets | Safe Havens | Crypto | Rates | Dollar | Divergence | Explorer | Portfolio
```

### New Navigation:
```
Dashboard | Markets ▼ | Signals | Explorer | Portfolio
                │
                └── Equity Markets
                    Safe Havens
                    Crypto
                    Rates
                    Dollar
```

**Changes:**
1. Consolidate asset class pages under "Markets" dropdown
2. Replace "Divergence" with "Signals" (links to divergence page initially, then to unified signals page in Phase 2.1)
3. Keep Explorer and Portfolio as top-level items

---

## Messaging Updates

### Tagline Changes

| Location | Current | New |
|----------|---------|-----|
| `base.html` navbar | (none or implicit) | "Comprehensive macro intelligence for individual investors" |
| `index.html` hero | "Real-time tracking of credit markets, equities, safe havens, and economic indicators" | "Your daily macro intelligence briefing" |
| Browser title | "Financial Markets Dashboard" | "SignalTrackers - Macro Intelligence Platform" |

### Content to Remove/Demote
- Any hero messaging specifically about gold vs. credit divergence
- Prominent "Crisis Warning" scores that imply single-thesis monitoring
- "Gold-Implied Spread" as a primary metric (move to Signals section)

---

## Technical Implementation

### Files to Modify

| File | Changes |
|------|---------|
| `signaltrackers/templates/index.html` | Complete restructure per layout spec |
| `signaltrackers/templates/base.html` | Navigation updates, tagline addition |
| `signaltrackers/static/css/dashboard.css` | New section styles, grid layouts, status badges |
| `signaltrackers/static/js/dashboard.js` | Status calculation logic, new data bindings |
| `signaltrackers/dashboard.py` | New aggregation endpoint for market conditions (optional) |

### New CSS Classes Needed

```css
.hero-briefing         /* Full-width briefing card */
.briefing-content      /* Briefing text styling */
.movers-row            /* Horizontal movers cards */
.mover-card            /* Individual mover card */
.market-grid           /* 6-card asset class grid */
.market-card           /* Individual asset class card */
.status-badge          /* Dynamic status indicator */
.status-crisis         /* Red */
.status-stressed       /* Orange */
.status-elevated       /* Yellow */
.status-normal         /* Green */
.status-neutral        /* Gray */
.signals-section       /* Signals preview area */
.signal-card           /* Individual signal card */
.category-credit       /* Red accent */
.category-equities     /* Blue accent */
.category-rates        /* Purple accent */
.category-havens       /* Gold accent */
.category-crypto       /* Orange accent */
.category-dollar       /* Green accent */
```

### API Considerations

The existing `/api/dashboard` endpoint returns sufficient data for most requirements. Consider:

1. **Optional Enhancement:** Add `/api/market-conditions` endpoint that returns pre-calculated status for each category
2. **AI Briefing:** Ensure `/api/ai-summary` returns structured data (narrative + key_points array) if not already

---

## User Stories

This feature is broken into the following user stories for implementation:

| Story ID | Title | Effort | Status |
|----------|-------|--------|--------|
| 1.1.1 | Market Briefing Hero Section | 2-3 days | ✅ Complete |
| 1.1.2 | Balanced Asset Class Metric Grid | 2-3 days | ✅ Complete |
| 1.1.3 | What's Moving Today Section | 1-2 days | ✅ Complete |
| 1.1.4 | Reposition Divergence to Signals Section | 1-2 days | ✅ Complete |
| 1.1.5 | Brand Messaging and Navigation Update | 1 day | ✅ Complete |

See individual user story documents for detailed acceptance criteria.

---

## Out of Scope

The following are explicitly NOT part of Phase 1.1:

- Unified Signals page (Phase 2.1)
- Market Conditions Summary Card with AI synthesis (Phase 1.2)
- Alert system (Phase 1.3)
- Mobile-specific redesign (Phase 4.1)
- Backend API restructuring

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Users miss divergence metric after repositioning | Medium | Clear "Signals" navigation, prominent in signals section |
| Layout complexity on mobile | Medium | Design mobile-first, test on multiple devices |
| AI briefing load time | Low | Loading skeleton, caching, pre-generation on schedule |
| Scope creep | High | Strict adherence to this spec, defer enhancements |

---

## Appendix: Current vs. New Information Architecture

### Current Homepage Sections (order):
1. Header with title
2. Daily Market Briefing (exists but not hero)
3. Top Movers (5 Day)
4. Top Movers Chart
5. Key Metrics Row 1 (HY Spread, Gold, VIX, Bitcoin)
6. Key Metrics Row 2 (S&P 500, CCC Ratio, Gold-Implied Spread)
7. AI/Tech Concentration
8. Yen Carry Trade
9. Economic Indicators
10. Prediction Markets

### New Homepage Sections (order):
1. **TODAY'S MARKET BRIEFING** (promoted to hero)
2. **WHAT'S MOVING TODAY** (renamed, enhanced)
3. **MARKET CONDITIONS GRID** (new, balanced)
4. **MARKET SIGNALS** (divergence repositioned)
5. **ADDITIONAL INSIGHTS** (concentration + predictions, demoted)

---

*This document serves as the authoritative specification for Phase 1.1. All implementation should reference this document.*
