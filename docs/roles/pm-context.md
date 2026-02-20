# SignalTrackers Product Roadmap

**Last Updated:** 2026-02-19
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

## Active Work

> **Features and tasks are tracked in GitHub Issues, organized by Milestones.**
>
> - **View issues:** `gh issue list`
> - **View milestones:** https://github.com/EricMaibach/financial/milestones
> - **View project board:** https://github.com/users/EricMaibach/projects/1

---

## Backlog (Future Consideration)

Items identified but not prioritized for current cycle:

| Feature | Notes | Priority |
|---------|-------|----------|
| Statistical Anomalies Dashboard | Identify statistically cheap/unusual assets with low media attention. Frame as educational context ("here's what's unusual, you decide") not trade signals. Leverages our percentile data uniquely. Strong differentiation potential. Needs legal review of framing. | Medium (Phase 5+) |
| Push notifications | Requires mobile app or PWA | Low |
| ADR/International stock support | Expand portfolio coverage | Low |
| Backtesting engine | Different product scope | Not planned |
| Real-time data | Cost vs. value for macro focus | Not planned |
| Options/derivatives in portfolio | Niche need, high complexity | Not planned |

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

1. **Prescriptive trade signals or "buy/sell" recommendations** - We provide context, data, and historical patterns but stop short of explicit recommendations. As the product evolves with more sophisticated analysis (percentiles, anomalies, patterns), we'll position as "maximum actionable intelligence within legal boundaries" rather than avoiding this space entirely. Key: educational framing, not advice.
2. **Real-time streaming data** - Cost/complexity vs. macro user needs
3. **"Balanced" thesis presentation** - We report data objectively; we don't need to artificially balance every metric
4. **Options/derivatives portfolio support** - Serves <15% of users, high complexity
5. **Mobile native app** - Web responsive is sufficient for now
6. **Backtesting engine** - Different product entirely

---

## Key Decisions

### Feature 2.1: Remove Divergence Page, Don't Replace (Feb 2026)
**Decision**: Kill the standalone divergence page entirely. Do NOT create a replacement "signals page."

**Context**:
- Original plan was to transform `/divergence` into comprehensive `/signals` page with 7+ indicators
- PM analysis showed this would violate "synthesis over data dump" principle
- Homepage already shows 3 key signal cards; asset class pages provide deep dives
- Creating signals page risks becoming a "ghost page" that adds complexity without clear value

**Rationale**:
- Simpler information architecture: Homepage → Asset Classes → Explorer
- Aligns with product vision (synthesis, not more dashboards)
- De-emphasizes divergence without giving cross-market signals MORE prominence
- Users who want signal details can use /explorer or asset class pages

**Implementation**:
- Remove `/divergence` route and navigation item
- Redirect `/divergence` → `/credit` (backward compatibility)
- Keep 3 signal cards on homepage (Yield Curve, VIX, Gold/Credit)
- Each card links to /explorer for that specific metric
- Update or remove "View All Indicators →" link on homepage

### UX Pattern: Progressive Disclosure (Feb 2026)
**Decision**: Establish divider/chevron expansion control as the standard pattern for progressive disclosure across the app.

**Context**:
- US-2.0.3 implemented a refined expansion control for Market Conditions section
- Pattern uses horizontal divider lines with centered chevron/text: `─────────── ⌄ Show Details ───────────`
- More subtle and elegant than traditional buttons

**Impact**:
- US-2.0.2 (What's Moving Today) updated to follow same pattern for consistency
- Future sections using progressive disclosure should use this pattern
- Engineers may extract to reusable CSS classes (`.expansion-control`, `.expansion-button`)

**Rationale**:
- Visual consistency across homepage sections
- Reduces cognitive load (same interaction pattern everywhere)
- Subtle styling doesn't compete with content
- Establishes scalable design system

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
| 2026-02-10 | Migrated features to GitHub Issues; slimmed doc to strategy only | PM |
| 2026-02-15 | Established divider/chevron as standard progressive disclosure pattern; updated US-2.0.2 | PM |
| 2026-02-19 | Feature 2.0 Homepage Streamlining marked COMPLETE; homepage reduced from 10→5 sections | PM |
| 2026-02-19 | Feature 2.1 rescoped: Remove divergence page entirely (don't replace with signals page) | PM |
| 2026-02-19 | Updated "What We're NOT Building" - refined trade signals positioning for future features | PM |
| 2026-02-19 | Added "Statistical Anomalies Dashboard" to backlog for future consideration (Phase 5+) | PM |

---

*This document contains product strategy and vision. For active work items, see GitHub Issues and Milestones.*
