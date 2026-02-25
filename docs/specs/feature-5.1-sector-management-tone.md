# Sector Management Tone Panel — Design Spec

**Issue:** #123
**Feature:** Sector Management Tone Panel
**Created:** 2026-02-25
**Designer:** UI/UX Designer
**Status:** Draft

---

## Overview

A quarterly-updated panel showing aggregate management confidence tone across all 11 GICS sectors, derived from S&P 500 earnings call transcripts via SEC EDGAR and FinBERT sentiment scoring. This is a **macro-level leading indicator**, not a stock-picking signal.

**User problem:** Investors can observe current macro regime state, but have no way to see whether management teams across key sectors are becoming more or less confident in their forward language quarter-over-quarter. Sector-level earnings tone is a leading signal — management language shifts before sector data shifts.

**Design goal:** Surface sector-level confidence patterns alongside the macro regime card in a format that is instantly scannable, clearly educational (not trading signals), and deepens naturally for curious users via progressive disclosure.

---

## User Flow

1. User opens SignalTrackers homepage
2. Sees Macro Regime Card (Section 0 — existing)
3. Scrolls to new **Sector Management Tone** section (Section 1.5 — below Market Conditions)
4. At a glance: which sectors have positive vs. negative management tone this quarter
5. Optionally expands trend view: 4-quarter sparkline per sector
6. Educational context ("Updated quarterly · Aggregate management tone across S&P 500 companies") prevents misuse as a trading signal

---

## Placement

The Sector Management Tone panel is a new homepage section inserted **between** Section 1 (Market Conditions at a Glance) and the existing "What's Moving Today" section.

```
Section 0: Current Macro Regime          ← existing
Section 1: Market Conditions at a Glance ← existing
Section 1.5: Sector Management Tone      ← NEW
Section 2: What's Moving Today           ← existing (if present)
```

**Rationale:** The panel's quarterly cadence means it sits comfortably below real-time sections, but it's macro-level context that belongs before any "recent moves" snapshot.

---

## Wireframes

### Mobile (375px) — Collapsed by Default

```
┌─────────────────────────────────────────────────────┐
│  SECTOR MANAGEMENT TONE                             │
│  Updated quarterly · Q4 2025                        │
│ ─────────────── ⌄ Show Sectors ──────────────────── │  ← collapsed
└─────────────────────────────────────────────────────┘
```

### Mobile (375px) — Expanded

```
┌─────────────────────────────────────────────────────┐
│  SECTOR MANAGEMENT TONE                             │
│  Updated quarterly · Q4 2025                        │
│  Interpret alongside current macro regime ↑         │
│ ─────────────── ⌃ Hide Sectors ──────────────────── │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ ▲ Positive      │  │ ▲ Positive      │          │
│  │ Technology      │  │ Health Care     │          │
│  │ ● ● ● ▲         │  │ ● ● ▲ ▲         │          │
│  └─────────────────┘  └─────────────────┘          │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ ─ Neutral       │  │ ─ Neutral       │          │
│  │ Financials      │  │ Industrials     │          │
│  │ ▲ ● ● ─         │  │ ● ● ─ ─         │          │
│  └─────────────────┘  └─────────────────┘          │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ ▼ Negative      │  │ ▼ Negative      │          │
│  │ Real Estate     │  │ Utilities       │          │
│  │ ● ─ ▼ ▼         │  │ ─ ─ ▼ ▼         │          │
│  └─────────────────┘  └─────────────────┘          │
│  … (remaining 5 sectors, same grid) …              │
│                                                     │
│  ℹ Aggregate management tone from Q4 2025           │
│    earnings calls. Not individual stock analysis.  │
└─────────────────────────────────────────────────────┘
```

**Legend: sparkline dots**
- `▲` = Positive quarter (success-600)
- `●` = Neutral quarter (neutral-400)
- `▼` = Negative quarter (danger-600)

### Tablet (768px) — Expanded by Default

```
┌─────────────────────────────────────────────────────────────────┐
│ SECTOR MANAGEMENT TONE                        Updated · Q4 2025 │
│ Interpret alongside current macro regime ↑                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ▲ Positive   │  │ ▲ Positive   │  │ ▲ Positive   │          │
│  │ Technology   │  │ Health Care  │  │ Cons. Disc.  │          │
│  │ ● ● ● ▲      │  │ ● ● ▲ ▲      │  │ ● ▲ ▲ ▲      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ─ Neutral    │  │ ─ Neutral    │  │ ─ Neutral    │          │
│  │ Financials   │  │ Industrials  │  │ Materials    │          │
│  │ ▲ ● ● ─      │  │ ● ● ─ ─      │  │ ● ─ ─ ─      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ▼ Negative   │  │ ▼ Negative   │  │ ─ Neutral    │          │
│  │ Real Estate  │  │ Utilities    │  │ Energy       │          │
│  │ ● ─ ▼ ▼      │  │ ─ ─ ▼ ▼      │  │ ▲ ▲ ─ ─      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ ─ Neutral    │  │ ▲ Positive   │                            │
│  │ Cons. Staples│  │ Comm. Svcs   │                            │
│  │ ─ ─ ─ ─      │  │ ─ ● ▲ ▲      │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
│  ℹ Aggregate management tone from Q4 2025 earnings calls        │
│    (S&P 500 companies · SEC EDGAR 8-K filings · FinBERT).      │
│    Sector aggregates only — not individual stock analysis.     │
└─────────────────────────────────────────────────────────────────┘
```

### Desktop (1280px) — Expanded

- 4-column grid (3 rows: 4+4+3)
- All 11 sectors visible without scroll

---

## Component Specifications

### Sector Tone Panel (Container)

- Background: neutral-100
- Border: 1px solid neutral-200
- Border-radius: 12px
- Padding: 20px (mobile), 24px (desktop)
- `<section aria-label="Sector Management Tone">`

### Panel Header

**Row 1:**
- Left: "SECTOR MANAGEMENT TONE" — text-xs, neutral-500, uppercase, letter-spacing: 0.08em, weight 600
- Right: "Updated quarterly · Q{Q} {YEAR}" — text-xs, neutral-400

**Row 2 (below header, above collapse toggle on mobile):**
- "Interpret alongside current macro regime ↑" — text-xs, neutral-500, italic
- The ↑ is a link/anchor to `#macro-regime-section` (scrolls to regime card)
- Only visible when `macro_regime` data is available

**Progressive Disclosure Toggle (mobile only, hidden on tablet+):**
- Follows existing `─── ⌄ Show Sectors ───` pattern
- 56px min-height, neutral-50 bg, chevron rotates on expand
- Sections collapsed by default on mobile, expanded on tablet+

### Sector Card

Each of the 11 GICS sectors gets one card.

**Container:**
- Background: white
- Border: 1px solid neutral-200
- Border-radius: 8px
- Padding: 12px
- Min-height: 80px (ensures ≥44px touch target when tappable)
- No interactive behavior in MVP — cards are display-only (not links)

**Tone Indicator Row:**
- Left: Tone icon + tone label
  - Positive: `bi-arrow-up-short` (success-600) + "Positive" (success-700, text-sm, weight 600)
  - Neutral: `bi-dash` (neutral-400) + "Neutral" (neutral-500, text-sm, weight 500)
  - Negative: `bi-arrow-down-short` (danger-600) + "Negative" (danger-700, text-sm, weight 600)
- Both icon and text: always accompanied by text — never color alone

**Sector Name:**
- Font: text-base (16px), weight 600, neutral-700
- Full GICS sector name (no abbreviations in the card, max 18 chars — "Consumer Discretionary" truncates to "Cons. Discretionary" on mobile cards)
- Margin-top: 2px

**Trend Sparkline (4 quarters):**
- 4 colored dots in a row, representing Q(current-3), Q(current-2), Q(current-1), Q(current)
- Dot size: 8px circle
- Spacing: 4px between dots
- Colors: success-500 (positive), neutral-300 (neutral), danger-500 (negative)
- Each dot has `title="Q{N} {YEAR}: {tone}"` for hover tooltip
- `aria-label="Trend: [Q1 tone], [Q2 tone], [Q3 tone], [Q4 tone]"` on the trend container
- Margin-top: 8px

**Data Currency Label:**
- "Q{Q} {YEAR}" — text-xs, neutral-400
- Positioned inline with the sparkline row (right-aligned) OR below sector name

**Semantic Card Border (left border, matching tone):**
- Positive: 3px left border, success-500
- Neutral: 3px left border, neutral-300
- Negative: 3px left border, danger-500
- Same pattern as existing metric cards' semantic left border

### Tone States and Colors

| Tone | Score Range | Icon | Text Color | Left Border | Dot Color |
|------|-------------|------|------------|-------------|-----------|
| Positive | > +0.15 | `bi-arrow-up-short` | success-700 | success-500 | success-500 |
| Neutral | -0.15 to +0.15 | `bi-dash` | neutral-500 | neutral-300 | neutral-300 |
| Negative | < -0.15 | `bi-arrow-down-short` | danger-700 | danger-500 | danger-500 |

**Note:** Score thresholds (-0.15 / +0.15) are a design starting point. Backend/PM should validate against actual FinBERT score distribution — adjust if the neutral band is too wide or too narrow in practice.

### Educational Footer

Below the sector grid, inside the panel:
- Icon: `bi-info-circle` (neutral-400, text-sm)
- Text: "Aggregate management tone from Q{Q} {YEAR} earnings calls (S&P 500 companies, SEC EDGAR 8-K filings, FinBERT). Sector aggregates only — not individual stock analysis."
- Font: text-xs, neutral-400, line-height 1.5
- Separator: 1px neutral-200 hairline above (margin-top 16px)

---

## Grid Layout

| Breakpoint | Columns | Sectors/Row |
|------------|---------|-------------|
| 375px (mobile) | 2 | 2 |
| 640px (large phone) | 2 | 2 |
| 768px (tablet) | 3 | 3 |
| 1024px (desktop) | 4 | 4 (3 rows: 4+4+3) |
| 1280px+ | 4 | Same as 1024 |

**Mobile 2-col note:** 11 sectors = 5 complete rows + 1 lone card on row 6. The last card should be left-aligned, not centered or stretched.

---

## Sector Sort Order

Display sectors in **default sort order: by current tone strength** (most positive first → neutral → most negative). This maximizes at-a-glance usefulness.

If tone scores are equal within a tier, sort alphabetically within that tier.

**Rationale:** Random sector order makes the panel harder to scan. Sorted-by-tone lets users instantly see where management confidence is highest and lowest.

---

## Interaction Patterns

### Mobile Collapse/Expand

- Follows existing progressive disclosure pattern exactly (see design-system.md → Visual Standards → Progressive Disclosure)
- Toggle: `─── ⌄ Show Sectors ───` / `─── ⌃ Hide Sectors ───`
- 56px min-height, neutral-50 bg, chevron rotates 180° when expanded
- Max-height transition: 200ms ease-out (same as existing collapse pattern)
- Default state: **collapsed on mobile**, **expanded on tablet+**

### No Card Interactivity (MVP)

- Sector cards are display-only in MVP — no tap/click action
- Cards have no hover state
- Future consideration: tapping a sector card could link to a sector detail view (Phase 6+)

---

## Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| 375px | Collapsed by default; 2-column grid; sector names may truncate at 18 chars |
| 640px | Collapsed by default; 2-column grid |
| 768px | Expanded by default; 3-column grid; collapse toggle hidden |
| 1024px | Expanded; 4-column grid |
| 1280px+ | Same as 1024; max-width container constrains width |

---

## Accessibility Requirements

### Semantic Structure
- `<section aria-label="Sector Management Tone">` wraps the entire panel
- Section heading: `<h3>` with visually-hidden class (section title not displayed as large heading, matches existing section header pattern)

### Color Independence
- All three tone states distinguished by icon + text, not color alone:
  - Positive: upward arrow icon + "Positive" text
  - Neutral: dash icon + "Neutral" text
  - Negative: downward arrow icon + "Negative" text

### Sparkline Accessibility
- Trend sparkline container: `aria-label="Trend over last 4 quarters: {Q1 tone}, {Q2 tone}, {Q3 tone}, {Q4 tone}"`
- Individual dots: `aria-hidden="true"` (covered by container aria-label)
- Tooltip on each dot: title attribute for mouse users, aria-label for assistive tech

### Contrast
- Positive text (success-700 #15803D) on white: passes AAA (7.2:1)
- Negative text (danger-700 #B91C1C) on white: passes AAA (7.8:1)
- Neutral text (neutral-500 #697386) on white: passes AA (4.6:1)
- Body text (neutral-400 #9AA5B1) on white: 3.2:1 — only use at text-xs for labels; do not use for primary content

### Touch Targets
- Collapse toggle: 56px min-height (meets AAA target)
- No interactive card elements in MVP — no touch target requirements for cards
- "Interpret alongside macro regime ↑" link: ensure 44px touch target via padding

### Screen Readers
- Collapsed panel content is hidden with `hidden` attribute or `max-height:0` + `overflow:hidden` (consistent with existing collapse pattern in codebase)
- When collapsed, screen readers skip the sector grid (it is visually AND assistively hidden)

---

## Data Requirements

The backend must provide to the template:

```python
sector_management_tone = {
    "quarter": "Q4",           # Current quarter label
    "year": 2025,              # Current year
    "data_available": True,    # False shows a "data not yet available" state
    "sectors": [
        {
            "name": "Information Technology",  # Full GICS name
            "short_name": "Technology",         # Abbreviated for small cards
            "current_tone": "positive",         # "positive" | "neutral" | "negative"
            "current_score": 0.42,              # Raw FinBERT score (-1.0 to +1.0)
            "trend": [                          # Chronological, oldest first
                {"quarter": "Q1", "year": 2025, "tone": "neutral"},
                {"quarter": "Q2", "year": 2025, "tone": "neutral"},
                {"quarter": "Q3", "year": 2025, "tone": "positive"},
                {"quarter": "Q4", "year": 2025, "tone": "positive"},
            ]
        },
        # ... 10 more sectors
    ]
}
```

Backend sorts sectors by tone strength (positive first, then neutral, then negative) before passing to template, OR template receives unsorted data and sorts via Jinja2 filter.

**Empty state:** If `data_available = False` (e.g., first quarter of data collection, mid-quarter, or pipeline failure), display a placeholder card inside the panel:

```
┌─────────────────────────────────────────────────────┐
│  SECTOR MANAGEMENT TONE                             │
│  ─────────────────────────────────────────────────  │
│  ℹ Sector tone data will be available when          │
│    Q{N} {YEAR} earnings season completes.           │
│    (Typically 6–8 weeks after quarter end)          │
└─────────────────────────────────────────────────────┘
```

---

## Design System References

| Element | Design System Reference |
|---------|------------------------|
| Panel container | Component Library → Cards → Standard Card |
| Sector card left border | Component Library → Cards → Metric Card (semantic border) |
| Progressive disclosure toggle | Visual Standards → Progressive Disclosure |
| Typography | Typography → Type Scale |
| Spacing | Spacing System → 4px baseline grid |
| Colors | Semantic Colors (success/danger/neutral scale) |
| Section heading pattern | Visual Standards → Section Headers (matches existing `section-title` class) |

---

## Out of Scope (This Feature)

- **Interactive sector drill-down** — Tapping a sector card to see individual company breakdowns. Not aligned with macro-first scope. Phase 6+ consideration.
- **Real-time or monthly updates** — Data is quarterly only (aligned with earnings cycles). Do not add progress bars or real-time indicators.
- **Confidence/model score display** — The raw FinBERT score is used by the backend for tone classification but is not surfaced to users. Showing a decimal score ("0.42") provides false precision for a retail user audience.
- **Sector comparison charts** — Time-series charts showing multiple sectors on one axis. Too complex for MVP panel; design the card-based view first and validate user engagement before adding chart layer.
- **Notifications on tone change** — Future integration with alert system (Feature #109). Out of scope for this panel.

---

## Open Questions

1. **Trend history depth** — This spec designs for 4 quarters of history. If backend can only produce the current quarter initially (data pipeline starting fresh), the sparkline should gracefully show 1 dot with grey placeholders for missing quarters. PM/Engineer: confirm expected history depth at launch.

2. **Score thresholds for tone classification** — The ±0.15 threshold for neutral vs. positive/negative is a design starting point. Engineer/PM: validate against actual FinBERT score distribution once pipeline is running. If most scores cluster near 0, tighten the threshold. If scores spread widely, the current threshold may work.

3. **Panel placement on mobile** — Given the panel collapses on mobile, users must actively expand it. Is this acceptable for a feature the CEO considers a "leading indicator complement to regime detection"? Alternative: show a compact 2-sector summary strip (most positive + most negative) as the collapsed state. PM: preferred?

4. **Sector name display** — 11 GICS sector names range from 6 chars (Energy) to 22 chars (Consumer Discretionary). On mobile 2-col cards, long names need truncation or abbreviation. This spec uses `short_name` for mobile display (e.g., "Cons. Discretionary"). PM/Engineer: confirm short name mapping is acceptable.

5. **Regime integration depth** — Currently, the panel links to the regime card with a text note ("Interpret alongside current macro regime ↑"). Should the panel also show which sectors are particularly notable given the *current* regime? This would require backend to provide regime-sector relevance (similar to category_relevance in Feature 3.3). PM: defer to Phase 6, or include from the start?

---

*Spec complete. PM: Please review and approve to proceed to user story creation.*
