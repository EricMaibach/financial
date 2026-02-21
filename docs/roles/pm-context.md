# SignalTrackers Product Roadmap

**Last Updated:** 2026-02-20
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

### Phase 3: Mobile-First Redesign - 7/12 Complete (58%)

**✅ COMPLETED (Feb 21, 2026):**
- **Feature 3.1: Mobile-First Content Pages** (#81)
  - All 7 content pages (Explorer + 6 asset classes) redesigned mobile-first
  - Charts visible without scrolling on mobile
  - 50%+ scroll reduction achieved on all pages
  - Design review: 5/5 Excellent rating
  - QA validation: 21/21 tests passed, 0 issues
  - **Major milestone** - Product's analytical core now mobile-excellent

**🔄 IN PROGRESS:**
- **Feature 3.2: Chatbot Mobile-First Redesign** (#82)
  - Status: Ready for engineering implementation
  - Design spec: Approved (docs/specs/feature-3.2-chatbot-mobile-redesign.md)
  - User stories: US-3.2.1 through US-3.2.4 created and approved
  - Priority: P1 (critical mobile UX issue - chatbot blocks 90%+ of viewport)
  - Next: Engineer to start US-3.2.1 implementation

**📋 TECHNICAL DEBT (P2):**
- Bug #55: Update deprecated Anthropic API parameter (thinking.type)
- Bug #56: Verify Anthropic model name (claude-opus-4-6 validity)
- Both: < 2 hours total effort, non-blocking

**Priority recommendation:** Complete Feature 3.2 (mobile-first momentum), then address bugs.

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

### Completed Phase 2 Decisions (Feb 2026)
**Feature 2.1**: Divergence page removed entirely (no replacement signals page) - Simpler IA, aligns with synthesis principle
**Feature 2.2**: Portfolio Templates cancelled - Templates don't serve actual user needs (existing portfolios, not allocating new capital)
**UX Pattern**: Divider/chevron established as standard progressive disclosure pattern - Visual consistency across app

### Phase 3 Pivot: Mobile-First, Pre-Launch Focus (Feb 2026)
**Decision**: Rescope Phase 3 from "Onboarding & Trial" to "Mobile-First Redesign" with pre-launch quality focus.

**Context**:
- Original Phase 3: Hosted Trial Mode, Onboarding Wizard
- Product not yet launched, no users to onboard
- Current assessment: Product is 7.5/10 - good, not great
- Target users ($100K+ portfolios) likely check markets on mobile throughout the day
- Mobile session duration is a key success metric (+25% target)
- Original Phase 4 had mobile improvements, but too late in roadmap

**Rationale**:
- **Onboarding is premature** - Can't optimize acquisition before product is ready to launch
- **Mobile is architectural** - Desktop-first assumptions baked into current design; every new feature built on this foundation creates more retrofit work
- **User behavior** - Investors check markets on mobile during trading hours, commutes, throughout the day
- **Cost of delay** - Building more desktop-first features before fixing mobile foundation is technical debt
- **Pre-launch quality** - Focus should be on making the product excellent, not on growth features

**New Phase 3 Focus:**
1. **Mobile-First Redesign** - Redesign layouts and components mobile-first, scale up to desktop
2. **Responsive excellence** - Mobile-first does NOT mean mobile-only; power users still need excellent desktop experience
3. **Pre-launch polish** - Ensure product is truly ready for users before building onboarding/acquisition features

**Design Philosophy:**
- Design for mobile constraints first (small screens, touch, limited attention)
- Scale up to tablet and desktop with progressive enhancement
- Desktop experience should be excellent for power users (deep analysis, multiple charts, etc.)
- Mobile-first is a design approach, not a device limitation

**Outcome**:
- Phase 3 Features (Hosted Trial, Onboarding Wizard) moved to future consideration
- Feature 4.1 (Mobile Experience Improvements) being rescoped into comprehensive mobile-first redesign
- New Phase 3 will focus on mobile-first architecture before adding more features
- Phase 3 milestone renamed from "Onboarding & Trial" to "Mobile-First Redesign"

### Feature 3.1 Scope: One Feature for Content Pages (Feb 2026)
**Decision**: Create one cohesive Feature 3.1 covering all content-heavy pages, rather than separate features per page type.

**Context**:
- Playwright screenshot analysis revealed content-heavy pages suffer from desktop-first information hierarchy
- Explorer page: Chart buried at bottom after 15+ sections of statistics (poor mobile UX)
- Asset class pages: Extremely long vertical scrolls, dense content stacked vertically
- Homepage and simple pages are adequate; problem is specific to content-heavy analytical pages

**Pages in scope:**
- Explorer page (metric analysis with charts)
- 6 Asset class pages (Credit, Rates, Dollar, Equities, Crypto, Safe Havens)

**Pages out of scope:**
- Homepage (already decent, recent streamlining work)
- Portfolio/Login pages (simple forms work fine)

**One Feature vs. Multiple:**
- Considered separating Explorer vs. Asset pages as different features
- Decided on ONE feature to ensure consistent mobile patterns across all content pages
- Tracking granularity maintained via user stories (US-3.1.1 through US-3.1.4)

**Rationale**:
- All affected pages share the same problem: desktop-first hierarchy with buried charts
- Solution requires consistent mobile-first patterns (chart prominence, progressive disclosure)
- One feature enforces architectural coherence and prevents inconsistent mobile UX
- User stories provide granular tracking while maintaining design system consistency

**Outcome**:
- Feature 3.1 "Mobile-First Content Pages" created (Issue #81, P0 priority)
- Scope: 7 pages total (Explorer + 6 asset class pages)
- Success metric: Charts visible within first screen on mobile, 50%+ scroll reduction
- Will be broken into 4 user stories for incremental delivery

### Feature 3.1 Design Decisions (Feb 2026)
**Context**: UI Designer reviewed Feature 3.1 and asked clarifying questions about mobile UX patterns.

**Decisions made:**
1. **Statistics collapsed by default on mobile** - Chart gets prominence, stats accessible via expansion control
2. **Full chart interactivity maintained** - Tap-based tooltips for mobile, no functionality removed
3. **Sticky metric selector on Explorer** - Always accessible for quick metric switching
4. **Hybrid tablet approach (768px)** - Chart + key stats visible, detailed metadata collapsed

**Status**: ✅ Design spec approved, user stories created, ready for engineering

**User Stories Created:**
- US-3.1.1 (Issue #83): Build reusable mobile-first components
- US-3.1.2 (Issue #84): Apply to Explorer page (validate pattern)
- US-3.1.3 (Issue #85): Apply to Credit & Rates pages
- US-3.1.4 (Issue #86): Apply to Dollar, Equities, Crypto, Safe Havens pages (completes feature)

**Design Specification:** `docs/specs/feature-3.1-mobile-content-pages.md` (approved)

### Feature 3.2: Chatbot Mobile UX (Feb 2026)
**Decision**: Create separate feature for chatbot mobile-first redesign.

**Context**:
- UI Designer identified critical mobile UX issue during Feature 3.1 review
- Chatbot currently takes 90%+ of mobile viewport when expanded
- Completely obscures charts/data users are asking questions about
- Users lose context - can't see data while using AI assistant

**Rationale**:
- Different component with different interaction patterns (overlay vs. page layout)
- Can be designed/implemented independently from Feature 3.1
- Potentially quick win to improve mobile chatbot usage
- Both features part of Phase 3 mobile-first focus

**Outcome**:
- Feature 3.2 "Chatbot Mobile-First Redesign" created (Issue #82, P1 priority)
- Success criteria: ≤50% viewport on mobile, users can see data while chatbot is open
- Added to Phase 3 milestone

**Design Decisions (Feb 2026):**
UI Designer reviewed Feature 3.2 and asked 6 product questions. PM decisions:

1. **Default state:** Floating button only (minimized, non-intrusive)
2. **Panel pattern:** Two-state toggle (minimized ↔ half-screen) - simpler for MVP
3. **Conversation persistence:** Full persistence (critical for AI value proposition)
4. **Notifications:** Badge indicator on floating button when minimized
5. **Input:** Text-only for MVP, quick suggestion chips for future
6. **Multi-turn scroll:** Scrollable message area within fixed panel height

**Pattern approved:** Bottom sheet (slides up from bottom, 40-50% viewport, page remains visible)

**Final Product Decisions (Feb 2026):**
UI Designer created comprehensive spec and asked 5 implementation questions. PM decisions:

1. **Close button**: X minimizes (not clears), separate "Clear conversation" link with confirmation
2. **Context awareness**: Include for MVP if technically simple (<1hr), else defer
3. **Quick suggestions**: Defer to post-MVP (data-driven based on usage patterns)
4. **Voice input**: Defer to post-MVP (significant complexity, not critical)
5. **Conversation limits**: Soft limit at 30 messages with gentle performance nudge

**Status:** ✅ Design spec approved, user stories created, ready for engineering

**User Stories Created:**
- US-3.2.1 (Issue #90): Build core chatbot widget (mobile bottom sheet)
- US-3.2.2 (Issue #91): Implement message interaction and AI integration
- US-3.2.3 (Issue #92): Add persistence, notifications, and polish features
- US-3.2.4 (Issue #93): Implement responsive tablet/desktop layouts (completes feature)

**Design Specification:** `docs/specs/feature-3.2-chatbot-mobile-redesign.md` (approved)

---

## Technical Debt & Cleanup

**Active Technical Debt:**
- [ ] **Bug #55** (P2): Update deprecated `thinking.type=enabled` → `adaptive` in ai_summary.py - Affects AI performance
- [ ] **Bug #56** (P2): Verify/update Anthropic model name `claude-opus-4-6` - Potential API errors

**Deferred Cleanup:**
- [ ] Remove/rename `README_DIVERGENCE.md` (reinforces old positioning)
- [ ] Audit AI prompts for thesis-specific language
- [ ] Review homepage template for divergence-heavy content

---

## Recent Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-21 | **Feature 3.1 COMPLETE** - All 7 content pages mobile-first (5/5 design, 21/21 QA, 0 issues) - Major milestone | PM |
| 2026-02-21 | Phase 3 progress: 7/12 complete (58%) - Feature 3.1 done, Feature 3.2 ready for engineering | PM |
| 2026-02-21 | Bugs #55 and #56 identified (Anthropic API issues) - Triaged as P2, defer until after Feature 3.2 | PM |
| 2026-02-21 | User stories created for Feature 3.2: US-3.2.1 (#90), US-3.2.2 (#91), US-3.2.3 (#92), US-3.2.4 (#93) | PM |
| 2026-02-20 | Feature 3.2 design spec approved - bottom sheet pattern, two-state toggle, full persistence | PM |
| 2026-02-20 | Feature 3.1 design spec approved - stats collapsed by default, chart prominence on mobile | PM |
| 2026-02-20 | Phase 3 rescoped to "Mobile-First Redesign" (was "Onboarding & Trial") - pre-launch focus shift | PM |
| 2026-02-20 | Phase 2 complete (13/13 issues) - Feature 2.2 cancelled (templates don't serve user needs) | PM |
| 2026-02-19 | Feature 2.0 Homepage Streamlining COMPLETE - homepage reduced from 10→5 sections | PM |
| 2026-02-15 | Established divider/chevron as standard progressive disclosure pattern | PM |

**Earlier milestones:** Phase 1 Complete (Feb 9), Phase 2 Complete (Feb 20), divergence page removed, portfolio templates cancelled

---

*This document contains product strategy and vision. For active work items, see GitHub Issues and Milestones.*
