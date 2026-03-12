# SignalTrackers Product Roadmap

**Last updated:** 2026-03-12 (Phase transition: IDEATING → BUILDING — human approved scope for Phase 9; all 5 issues approved)

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

## Active Phase
**Phase:** Phase 9 — Depth & Polish
**State:** BUILDING

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
| Phase 7 | Credit Intelligence & Completion | Mar 10, 2026 |

**Phase 5 highlights:** Macro Regime Score Panel (Feature 5.1, #138) and Multi-Model Recession Probability Sub-Panel (Feature 5.2, #146) — three recession models (NY Fed 12-month, Chauvet-Piger coincident, Richmond SOS weekly), all data free via FRED + Richmond Fed.

**Phase 6 highlights:** Regime Implications Panel (#145) — 5-level signal scale across 6 asset classes, static config from published research. Sector Management Tone Panel (#123) — SEC EDGAR 8-K ingestion, FinBERT NLP scoring, GICS sector aggregation (11 sectors), quarterly scheduling, /credit stub + nav parity.

**Total shipped:** 71+ user stories across 7 phases.

---

## Phase 7: Credit Intelligence & Completion ✅ COMPLETE
**Milestone goal:** Build out the credit detail page, integrate credit into the full AI briefing pipeline, and complete remaining market parity and UX gaps.

| Feature | Priority | Status |
|---------|----------|--------|
| #178 — Wire Macro Regime/Recession into AI Briefings & Chatbot | P2 | CLOSED ✅ (2026-03-04) |
| #171 — Homepage Section Quick-Nav | P2 | CLOSED ✅ (2026-03-05) |
| #183 — Homepage Narrative Cohesion — Full Redesign | P3 | CLOSED ✅ (2026-03-09) |
| #169 — Credit Market Detail Page | P2 | CLOSED ✅ (2026-03-06) |
| #208 — Refactor: Consolidate get_stats() / Fix Daily Briefing 52-Week Gap | P2 | CLOSED ✅ (2026-03-06) |
| #207 — Asset Detail Page Header — Shared Component Refactor | P3 | CLOSED ✅ (2026-03-09) |
| #206 — Global Trade Pulse — FRED Trade Balance Indicator | P2 | CLOSED ✅ (2026-03-06) |
| #166 — ML Container Separation (FinBERT/torch) | P3 | `needs-human-decision` (architecture trigger escalated) |
| #218 — Multi-Model Trust Signal: Why We Use Three Models | P3 | CLOSED ✅ (2026-03-10) |
| #232 — Bug: Richmond Fed SOS Indicator missing — openpyxl not installed | P1 | CLOSED ✅ (2026-03-10) |
| #219 — Fix: Regime Thread Missing from Cross-Market and Prediction Sections | P3 | CLOSED ✅ (2026-03-09) |
| #220 — Bug: Portfolio AI Credit Spread Unit Conversion (HY/IG reads as ~3 bp instead of ~280 bp) | P1 | CLOSED ✅ |
| #223 — Bug: market_signals.py crashes on empty FRED observations | P0 | CLOSED ✅ |
| #224 — Bug: Sector tone pipeline all Neutral — EDGAR fetch broken | P1 | CLOSED ✅ (2026-03-09) |

### Phase 7 Feature Detail

- **Credit Market Detail Page** (#169, P2) — ✅ COMPLETE. Three credit spread intelligence requirements delivered: (1) HY/IG OAS percentile gauge vs. rolling 20-year history, (2) regime-conditioned interpretation block, (3) HY–IG differential sparkline. AI briefing integration complete — credit context now in chatbot and daily briefing pipeline.
- **Homepage Narrative Cohesion — Full Redesign** (#183, P3) — ✅ COMPLETE. US-183.1: structural reorder (VERDICT→IMPLICATIONS→EVIDENCE→TODAY arc), visual regime threading (left-border accent), navbar regime pill, bridge sentences for §1.5/§2/§3. US-183.2: AI prompt anchoring — §1 Market Conditions and §2 Today's Briefing open with explicit regime context.
- **Refactor: Consolidate get_stats()** (#208, P2) — ✅ COMPLETE. Single `get_metric_stats(df)` at module level in `dashboard.py`; all 5 inline definitions replaced; daily briefing now includes 52-week range and distance-from-extreme context. Backend-only.
- **Asset Detail Page Header — Shared Component Refactor** (#207, P3) — ✅ COMPLETE. Consolidated 6 duplicate page-header CSS blocks into a single shared `.asset-page-header` component in `static/css/components/asset-page-header.css`. CSS custom property for category color accent. All 6 templates updated, per-page blocks removed, component documented in `docs/design-system.md`.
- **Global Trade Pulse — FRED Trade Balance Indicator** (#206, P2) — ✅ COMPLETE. Single-panel macro indicator showing US goods trade balance (BOPGSTB), YoY change, percentile framing, regime-conditioned interpretation. FRED-only scope; BDI deferred to Phase 9+. Follow-on: wire into AI Daily Briefing and Chatbot in Phase 8.
- **ML Container Separation** (#166, P3) — Extract FinBERT/torch from main app container. `needs-human-decision` — waiting on architecture decision (Redis queue vs. standalone cron vs. HTTP API).
- **Multi-Model Trust Signal** (#218, P3) — ✅ COMPLETE. Persistent UI explainer on Recession Probability panel using the 2022–2024 yield curve false alarm as the canonical example of why multi-model synthesis outperforms any single indicator. Copy + small UI component only; no new backend.
- **Fix: Regime Thread Missing from Cross-Market and Prediction Sections** (#219, P3) — ✅ COMPLETE. Added `regime-thread` class to `#signals-section` and `#prediction-section`. Regime-colored left border now renders consistently across all homepage sections.
- **Bug: Portfolio AI Credit Spread Unit Conversion** (#220, P1) — `generate_portfolio_market_context()` in `dashboard.py:3297-3304` formats HY/IG spreads without the `* 100` conversion, causing portfolio AI to see ~3 bp instead of ~280 bp. Silent accuracy failure in user-facing analysis. Two-line fix. (Approved from council discussion #37, 2026-03-08)
- **Bug: Richmond Fed SOS Indicator missing — openpyxl not installed** (#232, P1) — ✅ COMPLETE. `openpyxl` was absent from `requirements.txt`; `_fetch_richmond_sos()` silently returned `(None, None)`, causing the third recession model to not render. Fix: add `openpyxl>=3.0.0`. PR #234 merged.

---

## Phase 8: Signal Quality & Portfolio Foundation ✅ COMPLETE
**Milestone goal:** Deepen the quality and accuracy of the AI intelligence layer, fix the alert experience, and lay the foundation for real estate portfolio coverage.

*Phase 8 is a refinement phase — depth over breadth. We have added significant surface area across Phases 5–7. This phase makes what we have genuinely excellent before expanding further.*

### Hard Requirements

These are confirmed scope — no council research needed on direction.

| Requirement | Notes |
|-------------|-------|
| Daily Briefing Email audit & refresh | A lot has changed since the email was last updated: homepage redesign, regime detection, global trade pulse, new credit metrics. Audit the template, AI prompts, and data feeding the email. Bring it current. |
| Wire Global Trade Pulse into AI Daily Briefing & Chatbot | Carried forward from Phase 7 (#206). BOPGSTB panel ships without AI integration — Phase 8 closes that gap. |
| Property investment categories — value tracking | Add farmland, commercial rental property, and residential rental property as portfolio asset categories. At minimum: manual value entry, included in portfolio totals and AI recommendations. AI can reason meaningfully about these assets with values alone. |
| AI briefing prompt refresh | Audit all AI prompts against current signal coverage. Ensure regime, credit, global trade, and recession probability context is consistently included. Low-effort, high-impact. |

### Council Research Focus

These are open questions. Council researches and proposes — CEO approves/dismisses — PM creates Feature Issues.

| Topic | Council | Question |
|-------|---------|----------|
| Smart Market Alerts replacement | Researcher | Find an innovative, rare-signal alert approach — something that fires infrequently but with genuine conviction (e.g., multi-signal convergence at extremes, regime change triggers). If nothing compelling surfaces, recommend removing the feature. Do not propose incremental threshold tweaks. |
| AI briefing data quality | Engineer Council | What pre-processing, cross-signal correlation, or lightweight ML approaches could meaningfully improve LLM inputs? Look at: anomaly detection on individual metrics, convergence signals (multiple indicators stressed simultaneously), historical similarity matching. Propose what's achievable without major new dependencies. |
| Portfolio UX & analysis depth | Designer + Engineer Council | How should the portfolio section evolve? What analysis improvements are achievable given the value-tracking foundation? |
| Property macro data sources | Researcher + Engineer Council | Are there reliable public data sources for commercial cap rates, farmland price indexes, or residential rental yields? If yes, propose Phase 9 integration approach. If not, confirm value-tracking-only scope is correct. |

### Phase 8 Active Work

**Feature #237**: Smart Market Alerts — 3-Layer Architecture Replacement (P2) — CLOSED ✅ (2026-03-11)
- US-237.1 (#241): Layer 1 Regime Transition Detection — CLOSED ✅
- US-237.2 (#242): Layers 2 & 3 Extreme Percentile + Multi-Signal Convergence — CLOSED ✅
- US-237.3 (#243): Integration, Rate-Limiting (≤5/week), Display Update — CLOSED ✅

**Feature #238**: Portfolio Real Estate Categories — UX Design + Implementation (P2) — CLOSED ✅ (2026-03-11)
- US-238.1 (#245): Backend (API + breakdown + AI) — CLOSED ✅
- US-238.2 (#246): Frontend (picker, colors, labels) — CLOSED ✅
- US-238.3 (#247): UI (Real Estate summary card) — CLOSED ✅

**Bug #239**: Chatbot metrics silently broken — METRIC_INFO filename mismatches (P1) — CLOSED ✅ (PR #240 merged 2026-03-10)

### Success Metrics

| Metric | Target |
|--------|--------|
| Daily briefing email — content accuracy | Covers all major signal categories now in the product |
| Alert signal quality | Either: alerts fire ≤2x/week and are actionable, or feature is removed |
| Portfolio — property category adoption | Real estate categories available and included in AI portfolio analysis |

---

## Phase 9: Depth & Polish (planned)

**Milestone goal:** Build on Phase 8 council findings, deepen portfolio analysis, and address UX polish backlog.

*Scope is intentionally open — defined by what Phase 8 council surfaces. Known candidates below.*

### Planned Work

- **Property Macro Panel — Residential & Farmland Indicators** — Case-Shiller HPI, CPI Rent trend, rental vacancy rate, and USDA NASS farmland $/acre; all regime-contextualized, FRED/NASS only, no new paid data sources. Tier 2 (Zillow rent-to-price ratio, REIT-implied CRE proxies) at engineer's discretion. (#255, approved from council discussion #49, 2026-03-11)
- **Alert Severity Design Tokens — CSS Component + Card Header Fix** — Extract three alert severity hex values to named CSS tokens (--alert-l1/2/3-color), shared component file, design-system doc update; fix Smart Market Alerts card header from bg-danger to neutral/brand-adjacent color. (#256, approved from council discussion #50, 2026-03-11)
- **Bug: Credit briefing excluded from daily synthesis and portfolio context** — Wire get_latest_credit_summary() into both generate_daily_summary() and generate_portfolio_market_context(), matching existing pattern for crypto/equity/rates/dollar. ~10 lines, mechanical wiring only. (#257, P1, approved from council discussion #51, 2026-03-11)

### Remaining Candidates (Feature Issues pending)

| Candidate | Depends On |
|-----------|-----------|
| Alert replacement implementation | Phase 8 Researcher finding something worth building |
| AI briefing data pre-processing | Phase 8 Engineer Council proposal approved by CEO |
| Portfolio UX polish | Phase 8 Designer Council findings |
| General UX polish | Designer Council backlog items |
| BDI (Baltic Dry Index) integration | Re-evaluate after FRED trade balance signal validated in Phase 7/8 |
| Persistent news pipeline + news page | (#259, needs-human-approval) Feature A: scheduled fetch+store + AI-summarized news page; summaries feed AI briefings and chatbot. Feature B (deferred): custom RSS/feed management. Requires Tavily API. |
| Contextual AI entry points | (#258, needs-human-approval) Part 1: section-level AI icon → opens chatbot pre-loaded with section data. Part 2: sentence-level drill-in from AI briefings (requires design spec). Both require design spec. |

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
