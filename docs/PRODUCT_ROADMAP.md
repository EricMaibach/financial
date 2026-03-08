# SignalTrackers Product Roadmap

**Last updated:** 2026-03-08 (PM council run — 3 new issues from CEO-approved council discussions)

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
| Phase 4 | Mobile Polish + Core UX Wins | 13 stories (Feb 28, 2026) |
| Phase 5 | Macro Intelligence Layer | 9 stories (Feb 26, 2026) |
| Phase 6 | Advanced Intelligence & Sector Analysis | 6 stories (Feb 28, 2026) |

**Phase 5 highlights:** Macro Regime Score Panel (Feature 5.1, #138) and Multi-Model Recession Probability Sub-Panel (Feature 5.2, #146) — three recession models (NY Fed 12-month, Chauvet-Piger coincident, Richmond SOS weekly), all data free via FRED + Richmond Fed.

**Phase 6 highlights:** Regime Implications Panel (#145) — 5-level signal scale across 6 asset classes, static config from published research. Sector Management Tone Panel (#123) — SEC EDGAR 8-K ingestion, FinBERT NLP scoring, GICS sector aggregation (11 sectors), quarterly scheduling, /credit stub + nav parity.

**Total shipped:** 71 user stories across 6 phases.

---

## Phase 7: Credit Intelligence & Completion (in progress)
**Milestone goal:** Build out the credit detail page, integrate credit into the full AI briefing pipeline, and complete remaining market parity and UX gaps.

| Feature | Priority | Status |
|---------|----------|--------|
| #178 — Wire Macro Regime/Recession into AI Briefings & Chatbot | P2 | CLOSED ✅ (2026-03-04) |
| #171 — Homepage Section Quick-Nav | P2 | CLOSED ✅ (2026-03-05) |
| #183 — Homepage Narrative Cohesion — Full Redesign | P3 | IN PROGRESS (US-183.1 ✅; US-183.2 #185 `ready-for-implementation`) |
| #169 — Credit Market Detail Page | P2 | CLOSED ✅ (2026-03-06) |
| #208 — Refactor: Consolidate get_stats() / Fix Daily Briefing 52-Week Gap | P2 | CLOSED ✅ (2026-03-06) |
| #207 — Asset Detail Page Header — Shared Component Refactor | P3 | US-207.1 (#211) `ready-for-implementation` |
| #206 — Global Trade Pulse — FRED Trade Balance Indicator | P2 | CLOSED ✅ (2026-03-06) |
| #166 — ML Container Separation (FinBERT/torch) | P3 | `needs-human-decision` (architecture trigger escalated) |
| #218 — Multi-Model Trust Signal: Why We Use Three Models | P3 | `needs-test-plan` (approved from council: discussion #35, 2026-03-08) |
| #219 — Fix: Regime Thread Missing from Cross-Market and Prediction Sections | P3 | `needs-test-plan` (approved from council: discussion #36, 2026-03-08) |
| #220 — Bug: Portfolio AI Credit Spread Unit Conversion (HY/IG reads as ~3 bp instead of ~280 bp) | P1 | `needs-test-plan` (approved from council: discussion #37, 2026-03-08) |

### Active Story Pipeline

**WIP slot is open.** Next up in priority order:

1. **US-183.2** (#185) — `ready-for-pr` — P0 Critical, AI prompt anchoring (QA approved; Engineer needs to create PR)
2. **#220** — `needs-test-plan` — P1, Portfolio AI credit spread unit bug (two-line fix)
3. **US-207.1** (#211) — `ready-for-implementation` — P3, Asset detail header CSS refactor
4. **#218** — `needs-test-plan` — P3, Multi-Model Trust Signal explainer
5. **#219** — `needs-test-plan` — P3, Regime thread missing from Cross-Market/Prediction sections

### Phase 7 Feature Detail

- **Credit Market Detail Page** (#169, P2) — ✅ COMPLETE. Three credit spread intelligence requirements delivered: (1) HY/IG OAS percentile gauge vs. rolling 20-year history, (2) regime-conditioned interpretation block, (3) HY–IG differential sparkline. AI briefing integration complete — credit context now in chatbot and daily briefing pipeline.
- **Homepage Narrative Cohesion — Full Redesign** (#183, P3) — US-183.1 complete (reorder, visual threading, navbar pill, bridge sentences). US-183.2 (#185) AI prompt anchoring — `ready-for-implementation`, blocked on Feature #178 (now merged).
- **Refactor: Consolidate get_stats()** (#208, P2) — ✅ COMPLETE. Single `get_metric_stats(df)` at module level in `dashboard.py`; all 5 inline definitions replaced; daily briefing now includes 52-week range and distance-from-extreme context. Backend-only.
- **Asset Detail Page Header — Shared Component Refactor** (#207, P3) — Consolidate 6 duplicate page-header CSS blocks into a single shared `.asset-page-header` component. US-207.1 (#211) `ready-for-implementation`.
- **Global Trade Pulse — FRED Trade Balance Indicator** (#206, P2) — ✅ COMPLETE. Single-panel macro indicator showing US goods trade balance (BOPGSTB), YoY change, percentile framing, regime-conditioned interpretation. FRED-only scope; BDI deferred to Phase 9+. Follow-on: wire into AI Daily Briefing and Chatbot in Phase 8.
- **ML Container Separation** (#166, P3) — Extract FinBERT/torch from main app container. `needs-human-decision` — waiting on architecture decision (Redis queue vs. standalone cron vs. HTTP API).
- **Multi-Model Trust Signal** (#218, P3) — Persistent UI explainer on Recession Probability panel using the 2022–2024 yield curve false alarm as the canonical example of why multi-model synthesis outperforms any single indicator. Copy + small UI component only; no new backend. (Approved from council discussion #35, 2026-03-08)
- **Fix: Regime Thread Missing from Cross-Market and Prediction Sections** (#219, P3) — Add `regime-thread` class to `#signals-section` and `#prediction-section`. Two-line template change; all other homepage sections already have it. (Approved from council discussion #36, 2026-03-08)
- **Bug: Portfolio AI Credit Spread Unit Conversion** (#220, P1) — `generate_portfolio_market_context()` in `dashboard.py:3297-3304` formats HY/IG spreads without the `* 100` conversion, causing portfolio AI to see ~3 bp instead of ~280 bp. Silent accuracy failure in user-facing analysis. Two-line fix. (Approved from council discussion #37, 2026-03-08)

---

## What We Are NOT Building

These directions have been evaluated and dismissed. Do not re-propose without new evidence:

| Direction | Reason | Date |
|-----------|--------|------|
| Options flow + dark pool synthesis as primary signal | Dark pool prints lack reliable direction signal; options flow space has better-funded competitors; fundamental data quality issue would undermine user trust | 2026-02-23 |
| BDI (Baltic Dry Index) integration | Adds new data dependency while Phase 7 is in progress; FRED trade balance is sufficient to validate signal value first | 2026-03-06 |

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
