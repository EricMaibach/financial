# SignalTrackers Product Roadmap

**Last updated:** 2026-03-06 (PM Council: 3 features created from council discussions #29, #30, #31)

---

## Product Vision

SignalTrackers is a macro financial dashboard for individual investors — the only tool that combines macro regime detection, technical signals, and plain-language interpretation in one place.

**The problem we solve:** Retail investors are forced to maintain 4–6 fragmented subscriptions (TradingView for charts, Koyfin for fundamentals, MacroMicro for data, SentimenTrader for sentiment) because no single platform covers the full stack. SignalTrackers closes this gap, starting with the macro layer.

**What makes us different:**
- Macro-first: regime context drives signal interpretation, not the other way around
- Plain-language synthesis: data means nothing without explanation (only 62% of investors understand how rates affect bonds)
- Retail-priced: institutional-grade methodology using free/public data (FRED, OCC, FRED-MD)

---

## North Star Metric

Investors who use SignalTrackers as their primary macro intelligence tool — replacing at least one paid subscription.

---

## Current Release State

### Phases 1–6: Complete

| Phase | Title | Shipped |
|-------|-------|---------|
| Phase 1 | Repositioning & Core Gaps | 16 stories |
| Phase 2 | Consolidation & Templates | 13 stories |
| Phase 3 | Mobile-First Redesign | 14 stories (Feb 23, 2026) |
| Phase 4 | Mobile Polish + Core UX Wins | 13 stories (Feb 25, 2026) |
| Phase 5 | Macro Intelligence Layer | 9 stories (Feb 26, 2026) |
| Phase 6 | Advanced Intelligence & Sector Analysis | 6 stories (Feb 28, 2026) |

**Phase 5 highlights:** Macro Regime Score Panel (Feature 5.1, #138) and Multi-Model Recession Probability Sub-Panel (Feature 5.2, #146) — three recession models (NY Fed 12-month, Chauvet-Piger coincident, Richmond SOS weekly), all data free via FRED + Richmond Fed.

**Phase 6 highlights:** Regime Implications Panel (#145) — 5-level signal scale across 6 asset classes, static config from published research. Sector Management Tone Panel (#123) — SEC EDGAR 8-K ingestion, FinBERT NLP scoring, GICS sector aggregation (11 sectors), quarterly scheduling, /credit stub + nav parity.

**Total shipped:** 71 user stories across 6 phases.

---

## Phase 7: Credit Intelligence & Completion (upcoming)
**Milestone goal:** Build out the credit detail page, integrate credit into the full AI briefing pipeline, and complete remaining market parity and UX gaps.

| Feature | Priority | Status |
|---------|----------|--------|
| #178 — Wire Macro Regime/Recession into AI Briefings & Chatbot | P2 | Complete |
| #169 — Credit Market Detail Page | P2 | Backlog |
| #173 — Rename "Additional Charts" sections (quick-win) | P3 | Backlog (user-story, needs-test-plan) |
| #174 — Bug: regime/recession cache ordering fix | P1 | Backlog (prerequisite for #11 wiring) |
| #175 — Bug: FRED incremental fetching (35yr → targeted) | P2 | Backlog |
| #186 — Bug: Dollar briefing missing from automated daily refresh | P2 | Backlog |
| #166 — ML Container Separation (FinBERT/torch) | P3 | Backlog |
| #171 — Homepage Section Quick-Nav | P2 | Backlog |
| #207 — Asset Detail Page Header — Shared Component Refactor | P3 | Backlog |
| #208 — Refactor: Consolidate get_stats() and Fix Daily Briefing 52-Week Context Gap | P2 | Backlog |

- **Homepage Section Quick-Nav** (#171) — Sticky/floating quick-nav so returning users can jump to any homepage section in ≤1 tap on mobile and desktop; section IDs already in HTML, frontend-only work (#171, approved from council: discussion #15, 2026-02-28)
- **"Additional Charts" rename** (#173) — Rename collapsible section headers on Equities, Rates, Safe Havens, and Crypto detail pages to descriptive labels (e.g., "Yield Curve & Real Yields") — text change only, four files; standalone P3 quick-win to complete before credit page work begins (#173, approved from council: discussion #20, 2026-03-01)
- **Bug: cache ordering fix** (#174, P1) — Move `update_macro_regime()` and `update_recession_probability()` to run before AI briefing generation in `run_data_collection()` — prerequisite for wiring regime/recession state into daily briefings (discussion #21, 2026-03-01)
- **Bug: FRED incremental fetching** (#175, P2) — Replace 35-year full-history FRED fetch on every daily refresh with targeted start-date using `get_last_date_in_file()` output; prevents rate-limit issues as series list grows with Phase 7 credit data (discussion #21, 2026-03-01)
- **Credit Market Detail Page** (#169, P2) — Updated 2026-03-01: now includes three credit spread intelligence requirements as core: (1) HY/IG OAS percentile gauge vs. rolling 20-year history, (2) regime-conditioned interpretation block, (3) HY–IG differential sparkline. All use existing FRED data (approved from council: discussion #19, 2026-03-01)
- **Bug: Dollar briefing missing from automated daily refresh** (#186, P2) — `run_data_collection()` generates crypto/equity/rates briefings but skips the dollar briefing entirely; `generate_daily_summary()` checks for same-day dollar briefing and injects it as synthesis context — so the dollar context is never available in automated runs. Fix: add ~10-line step to `run_data_collection()` mirroring existing briefing pattern (#186, approved from council: discussion #26, 2026-03-03)
- **Asset Detail Page Header — Shared Component Refactor** (#207, P3) — Consolidate 6 duplicate page-header CSS blocks into a single shared `.asset-page-header` component in `static/css/components/asset-page-header.css`, update all 6 templates, document in design system. Timing: after US-169.3 merges (#207, approved from council: discussion #30, 2026-03-06)
- **Refactor: Consolidate get_stats() and Fix Daily Briefing 52-Week Context Gap** (#208, P2) — Extract single module-level `get_metric_stats(df)` in `dashboard.py`; replace all 5 inline definitions; update daily briefing format strings to include 52-week range and distance-from-extreme context (#208, approved from council: discussion #31, 2026-03-06)

---

## Strategic Backlog (approved, not yet scheduled)

These ideas are approved for exploration but have not been assigned to a milestone:

| Idea | Origin | Notes |
|------|--------|-------|
| PCR + GEX regime-conditioned indicators | Dismissed in council #104, reconsidering after macro regime foundation | Prerequisite: complete Phase 5 macro regime work first. Only using free OCC/Barchart data. |
| Global Trade Pulse — FRED Trade Balance Indicator | Council discussion #29 | Single-panel macro indicator: US goods trade balance (BOPGSTB), YoY change, percentile framing, regime-conditioned interpretation. FRED-only scope; BDI integration deferred to Phase 9+. (#206, approved 2026-03-06) |

---

## What We Are NOT Building

These directions have been evaluated and dismissed. Do not re-propose without new evidence:

| Direction | Reason | Date |
|-----------|--------|------|
| Options flow + dark pool synthesis as primary signal | Dark pool prints lack reliable direction signal; options flow space has better-funded competitors; fundamental data quality issue would undermine user trust | 2026-02-23 |

---

## Success Metrics by Phase

| Phase | Key Metric |
|-------|-----------|
| Phase 3 | Mobile usability: no iOS Safari zoom, all touch targets ≥44px, chatbot functional on mobile |
| Phase 4 | Alert engagement: % users with active alerts; alert visibility without dropdown |
| Phase 5 | Regime accuracy: backtested signal performance in regime-conditioned vs. raw mode |
| Phase 6 | Regime → action gap: users who view Regime Implications Panel after checking regime score |

---

## Guiding Principles

1. **Free data first.** FRED, OCC, FRED-MD, Barchart — institutional methodology at retail cost.
2. **Interpretation over raw data.** Every indicator needs a plain-language context sentence.
3. **Mobile-first.** The majority of users will check signals on a phone.
4. **Approve sparingly.** Every feature becomes engineering work. We choose depth over breadth.
