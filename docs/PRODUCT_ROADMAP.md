# SignalTrackers Product Roadmap

**Last updated:** 2026-02-25 (Feature 4.3 complete)

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

### Phase 3: Mobile-First Redesign (in progress)
**Milestone goal:** Pre-launch quality on mobile before adding acquisition features.

| Feature | Status |
|---------|--------|
| 3.1 — Mobile-first content pages (Credit, Rates, Dollar, Equities, Crypto, Safe Havens, Explorer) | Complete |
| 3.2 — Chatbot mobile-first redesign (bottom sheet, ≤50% viewport, full persistence) | Complete |
| 3.4 — Visible alert indicator in navbar (bell icon + unread badge, mobile + desktop) | Complete |

---

## Upcoming Priorities

### Phase 4: Mobile Polish + Core UX Wins
**Milestone goal:** Finish the mobile foundation; address UX debt before adding new features.

| Feature | Status |
|---------|--------|
| 4.1 — Macro Regime Detection: regime-conditional signal weighting (Bull/Neutral/Bear/Recession Watch, FRED-MD) | Complete |
| 4.2 — Fix chatbot close vs. minimize button behavior (− minimizes, × dismisses to floating trigger) | Complete |
| 4.3 — Replace native alert() dialogs in portfolio page with inline/toast error patterns | Complete |

### Phase 5: Macro Intelligence Layer
**Milestone goal:** Establish SignalTrackers as the leading macro regime tool for retail investors.

Planned work (ordered by dependency):
1. **Macro Regime Score Panel** — synthesized headline regime indicator updated daily, visible on dashboard. Logical follow-on now that signal weighting (Phase 4) has validated the approach.

---

## Strategic Backlog (approved, not yet scheduled)

These ideas are approved for exploration but do not have a milestone yet:

| Idea | Origin | Notes |
|------|--------|-------|
| PCR + GEX regime-conditioned indicators | Dismissed in council #104, reconsidering after macro regime foundation | Prerequisite: complete Phase 5 macro regime work first. Only using free OCC/Barchart data. |
| **Sector Management Tone Panel** — quarterly GICS sector-level earnings call sentiment from SEC EDGAR 8-K filings + FinBERT (open-source); 11 sectors, one score per sector per quarter, interpreted alongside macro regime state (#123, approved from council: discussion #121, 2026-02-24) | Research discussion #121 | Prerequisite: Phase 5 macro regime work must be in production. Significant NLP pipeline project (more complex than regime detection). Phase 6. |

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
| Phase 3 (current) | Mobile usability: no iOS Safari zoom, all touch targets ≥44px, chatbot functional on mobile |
| Phase 4 | Alert engagement: % users with active alerts; alert visibility without dropdown |
| Phase 5 | Regime accuracy: backtested signal performance in regime-conditioned vs. raw mode |

---

## Guiding Principles

1. **Free data first.** FRED, OCC, FRED-MD, Barchart — institutional methodology at retail cost.
2. **Interpretation over raw data.** Every indicator needs a plain-language context sentence.
3. **Mobile-first.** The majority of users will check signals on a phone.
4. **Approve sparingly.** Every feature becomes engineering work. We choose depth over breadth.
