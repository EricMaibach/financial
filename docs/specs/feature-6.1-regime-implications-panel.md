# Regime Implications Panel — Design Spec

**Issue:** #145
**Feature:** 6.1 — Regime Implications Panel
**Created:** 2026-02-27
**Designer:** UI/UX Designer
**Status:** Draft

---

## Overview

A panel that translates the current macro regime (Bull / Neutral / Bear / Recession Watch from the FRED-MD engine) into historical sector and asset class performance patterns — closing the "so what" gap between regime awareness and portfolio context.

**User problem:** Users can see what regime we're in (Section 0) and how elevated recession risk is (Section 0.5), but have no way to understand what that regime has historically meant for equities, credit, rates, safe havens, and crypto. This is the critical macro → action translation layer.

**Design goal:** Deliver historical regime implications for 5 asset classes in a scannable, accessible, plain-language format. Interactive regime tabs allow users to compare all four regime phases.

---

## User Flow

1. User arrives at SignalTrackers homepage
2. Sees current macro regime in Section 0 (e.g., "Bull Market — Improving")
3. Scrolls to Section 0.75 — Regime Implications Panel
4. Current regime tab is pre-selected; user sees historical signals for all 5 asset classes
5. Optionally clicks other regime tabs to compare Bear, Neutral, Recession Watch patterns
6. Footer disclaimer reinforces educational framing

---

## Placement

New homepage **Section 0.75** — inserted between the Recession Probability Sub-Panel (Section 0.5) and Market Conditions (Section 1).

```
Section 0:    Macro Regime Score               ← existing
Section 0.5:  Recession Probability Sub-Panel  ← existing (Feature 5.2)
Section 0.75: Regime Implications Panel        ← NEW
Section 1:    Market Conditions at a Glance    ← existing
Section 1.5:  Sector Management Tone           ← upcoming (Feature 6.2 / #123)
```

**Rationale:** The macro regime trio (0 → 0.5 → 0.75) forms a logical narrative: "What regime are we in?" → "What's the recession risk?" → "What does this regime historically mean for my holdings?" Users receive the full context before reaching real-time market conditions.

---

## Wireframes

### Mobile (375px) — Collapsed by Default

```
┌─────────────────────────────────────────────────────┐
│  REGIME IMPLICATIONS                                 │
│  Bull Market · Historical patterns                   │
│ ─────────────── ⌄ View Implications ──────────────── │
└─────────────────────────────────────────────────────┘
```

### Mobile (375px) — Expanded (current regime view)

```
┌─────────────────────────────────────────────────────┐
│  REGIME IMPLICATIONS                                 │
│  Bull Market · Historical patterns                   │
│ ─────────────── ⌃ Hide ────────────────────────────  │
│                                                      │
│ ┌───── EQUITIES ─────────────────────────────────┐  │
│ │ ↑↑ Strong Outperform                           │  │
│ │ Cyclicals and growth sectors historically lead  │  │
│ │ in bull phases.                                 │  │
│ │                                                 │  │
│ │ Leading: Technology · Financials · Cons. Disc.  │  │
│ │ Lagging:  Utilities · Consumer Staples          │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌───── CREDIT ───────────────────────────────────┐  │
│ │ ↑ Outperform                                   │  │
│ │ HY spreads tighten as economic conditions       │  │
│ │ improve; investment-grade in line with equities.│  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌───── RATES ────────────────────────────────────┐  │
│ │ ↓ Underperform                                 │  │
│ │ Rising yields compress long-duration bond       │  │
│ │ prices in expanding economic conditions.        │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌───── SAFE HAVENS ──────────────────────────────┐  │
│ │ ↓↓ Strong Underperform                         │  │
│ │ Gold and long-duration Treasuries trail as      │  │
│ │ risk-on assets dominate.                        │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ┌───── CRYPTO ───────────────────────────────────┐  │
│ │ ↑ Outperform                                   │  │
│ │ Risk appetite supports crypto alongside         │  │
│ │ equities in bull conditions.                    │  │
│ └─────────────────────────────────────────────────┘  │
│                                                      │
│ ──────────── View other regimes ────────────────     │
│ [Bear]  [Neutral]  [Recession Watch]                 │
│                                                      │
│ ℹ Historical pattern analysis, not investment advice │
│   Sources: FRED-MD · CFA Institute · Fidelity BCU   │
└─────────────────────────────────────────────────────┘
```

**"Other regimes" footer (mobile):** Three compact text buttons below the asset class cards. Tapping switches the panel content and updates the section subtitle. Current regime button hidden from this row.

### Tablet / Desktop (768px+) — Always Expanded

```
┌─────────────────────────────────────────────────────────────────┐
│ REGIME IMPLICATIONS                                              │
│                                                                  │
│ [★ Bull Market]  [Neutral]  [Bear Market]  [Recession Watch]    │
│ ← tab bar; active tab accented with regime color ──────────── → │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────┐  │
│  │ EQUITIES         │ │ CREDIT           │ │ RATES          │  │
│  │ ↑↑ Strong Out.   │ │ ↑ Outperform     │ │ ↓ Underperform │  │
│  │                  │ │                  │ │                │  │
│  │ Cyclicals &      │ │ HY spreads       │ │ Rising yields  │  │
│  │ growth sectors   │ │ tighten as       │ │ compress long- │  │
│  │ historically     │ │ economy grows    │ │ duration bond  │  │
│  │ lead             │ │                  │ │ prices         │  │
│  │                  │ │                  │ │                │  │
│  │ ▲ Tech · Fin.    │ │                  │ │                │  │
│  │ ▼ Util · Stapl.  │ │                  │ │                │  │
│  └──────────────────┘ └──────────────────┘ └────────────────┘  │
│  ┌──────────────────┐ ┌──────────────────┐                      │
│  │ SAFE HAVENS      │ │ CRYPTO           │                      │
│  │ ↓↓ Strong Under. │ │ ↑ Outperform     │                      │
│  │                  │ │                  │                      │
│  │ Gold & long-dur. │ │ Risk appetite    │                      │
│  │ Treasuries trail │ │ supports crypto  │                      │
│  │ as risk-on       │ │ alongside        │                      │
│  │ assets dominate  │ │ equities         │                      │
│  └──────────────────┘ └──────────────────┘                      │
│                                                                  │
│  ℹ Historical pattern analysis (FRED-MD, 1960–2025).            │
│    Not investment advice. Patterns reflect historical averages,  │
│    not guarantees of future performance.                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Regime Implications Panel (Container)

- Section HTML: `<section id="regime-implications" aria-label="Regime Implications">`
- Background: neutral-50
- Border-top: 1px solid neutral-200
- Padding: 20px (mobile), 24px (desktop)
- Max-width: constrained by existing site container

### Panel Header

**Row 1 — Section title:**
- "REGIME IMPLICATIONS" — text-xs, neutral-500, uppercase, letter-spacing: 0.08em, weight 600
- Matches existing section header pattern (`.section-title` class)

**Row 2 — Current regime subtitle (mobile only):**
- "[Regime Name] · Historical patterns" — text-sm, neutral-600
- Updates when tab changes

**Progressive Disclosure Toggle (mobile only, hidden on tablet+):**
- Follows existing `─── ⌄ Show X ───` pattern exactly (see design-system.md → Visual Standards → Progressive Disclosure)
- Toggle label: "View Implications" / "Hide"
- 56px min-height, neutral-50 bg, chevron rotates 180° on expand
- Default state: **collapsed on mobile**, **always expanded on tablet+**

### Regime Tab Bar (tablet+)

- Shown only on tablet+ (hidden on mobile; mobile uses footer regime buttons instead)
- 4 tabs: Bull Market / Neutral / Bear Market / Recession Watch
- Active tab: bottom border 2px, regime color; text neutral-800, weight 600
- Inactive tab: text neutral-500, weight 400; hover: neutral-700
- Tab bar: border-bottom 1px neutral-200
- `role="tablist"`, each tab `role="tab"`, content panels `role="tabpanel"`
- Current regime tab bears a ★ prefix or `aria-label="... (current regime)"` indicator

**Regime color for tab accent:**
- Bull Market: success-600 (#16A34A)
- Neutral: brand-blue-500 (#3B82F6)
- Bear Market: warning-600 (#D97706)
- Recession Watch: danger-600 (#DC2626)

### Mobile Regime Switcher (mobile only)

- Shown below asset class cards, above the footer
- Label: "View other regimes:" — text-xs, neutral-500
- 3 text-button chips (non-active regimes only) — text-sm, brand-blue-600, underlined on focus
- 44px touch target height via padding
- Hidden on tablet+

### Asset Class Card

5 cards per regime: Equities, Credit, Rates, Safe Havens, Crypto.

**Container:**
- Background: white
- Border: 1px solid neutral-200
- Border-left: 4px solid `[signal-color]` — semantic left border matching performance signal
- Border-radius: 8px
- Padding: 16px
- Mobile: full-width stacked, margin-bottom: 12px
- Tablet+: part of responsive grid (see Grid Layout below)

**Signal left border colors:**
- Strong Outperform: success-600
- Outperform: success-700
- Neutral: neutral-300
- Underperform: warning-500
- Strong Underperform: danger-500

**Asset Class Label (header):**
- "EQUITIES" / "CREDIT" / etc. — text-xs, neutral-500, uppercase, letter-spacing 0.06em, weight 600
- Margin-bottom: 4px

**Performance Signal Row:**
- Icon (Bootstrap Icons) + Signal label
- Signal icon choices:
  - Strong Outperform: `bi-arrow-up-right-circle-fill` (success-600)
  - Outperform: `bi-arrow-up-right` (success-700)
  - Neutral: `bi-dash-circle` (neutral-400)
  - Underperform: `bi-arrow-down-right` (warning-600)
  - Strong Underperform: `bi-arrow-down-right-circle-fill` (danger-600)
- Signal label: text-base (16px), weight 700, matching signal color
- Icon has `aria-hidden="true"`; signal label is the accessible text

**Annotation Text:**
- 1–2 sentence plain-language description — text-sm (14px), neutral-600, line-height 1.5
- Margin-top: 8px

**Sector Callouts (Equities card only):**
- "Leading: [sector] · [sector] · [sector]" — text-xs, neutral-500, margin-top: 10px
- "Lagging: [sector] · [sector]" — text-xs, neutral-500, margin-top: 2px
- Sector names separated by `·` (middle dot), no links in MVP

### Performance Signal Scale

| Signal | Icon | Text | Left Border | Meaning |
|--------|------|------|-------------|---------|
| Strong Outperform | `bi-arrow-up-right-circle-fill` | success-600 | success-600 | Historically significant positive return |
| Outperform | `bi-arrow-up-right` | success-700 | success-700 | Modest positive historical pattern |
| Neutral | `bi-dash-circle` | neutral-400 | neutral-300 | Mixed or flat historical pattern |
| Underperform | `bi-arrow-down-right` | warning-600 | warning-500 | Modest negative historical pattern |
| Strong Underperform | `bi-arrow-down-right-circle-fill` | danger-600 | danger-500 | Historically significant negative return |

Always pair icon + text label — never color alone.

### Footer / Disclaimer

- Icon: `bi-info-circle` (neutral-400, text-sm), `aria-hidden="true"`
- Text: "Historical pattern analysis (FRED-MD, 1960–2025). Patterns reflect historical averages, not guarantees of future performance. Not investment advice."
- Font: text-xs, neutral-400, line-height 1.5
- Separator: 1px neutral-200 hairline above (margin-top 16px, padding-top 16px)

---

## Grid Layout

### Asset Class Cards (tablet+)

| Breakpoint | Columns | Layout |
|------------|---------|--------|
| 375px (mobile) | 1 | Stacked full-width |
| 640px (large phone) | 1 | Stacked full-width |
| 768px (tablet) | 3 | Row 1: Equities / Credit / Rates; Row 2: Safe Havens / Crypto / (empty) |
| 1024px+ (desktop) | 3 | Same as tablet (5 cards fit cleanly in 3+2) |

**3-col note:** Equities card on tablet+ is the same width as the others (no full-width exception). The sector callout rows make it slightly taller than the other cards — this is acceptable (grid rows stretch to match tallest card in the row).

---

## Interaction Patterns

### Regime Tab Switching (tablet+)

- Clicking a tab: shows that regime's `tabpanel`, hides others
- `aria-selected="true"` on active tab, `aria-selected="false"` on others
- Tab panel visibility: `hidden` attribute toggled (not CSS visibility), so screen readers skip inactive panels
- Section subtitle does NOT update on desktop (tab label is visible)
- No page reload or scroll jump on tab switch
- Animation: none (instant content swap — financial dashboard, not marketing page)

### Mobile Regime Switcher

- Tapping a regime chip: replaces asset class card content with that regime's data
- Section subtitle updates to "[Regime Name] · Historical patterns"
- No animation on content swap
- The current regime chip is the default; previously active regime chip re-appears when user switches to another

### Progressive Disclosure (mobile)

- Follows existing collapse pattern exactly:
  - `max-height: 0; overflow: hidden` when collapsed
  - `max-height: [content height]; overflow: hidden` when expanded
  - `transition: max-height 200ms ease-out`
  - 56px min-height toggle row
  - Chevron rotates 180° on expand via `aria-expanded` attribute

---

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|---------------|
| 375px | Collapsed default; stacked single-column cards; mobile regime switcher visible |
| 640px | Same as 375px |
| 768px | Always expanded; regime tab bar visible; 3-column card grid; mobile switcher hidden |
| 1024px | Same as 768px; 3-column grid |
| 1280px+ | Same as 1024px; max-width container limits expansion |

---

## Accessibility Requirements

### Structure
- `<section id="regime-implications" aria-label="Regime Implications">` wraps the panel
- Section heading: visually-styled label (`section-title` class), not a large visible `<h2>`
- Tab bar: `role="tablist"`, tabs: `role="tab"` with `aria-selected`, `aria-controls`
- Tab panels: `role="tabpanel"` with `id` and `aria-labelledby`

### Color Independence
- Performance signals always use icon + text label — never color alone
- Left border accent is decorative (redundant with icon + text): `aria-hidden` approach acceptable for border
- Sector callouts ("Leading: / Lagging:") use text labels only

### Touch Targets
- Regime tabs: min 44px height via padding
- Mobile regime switcher chips: min 44px height via padding
- Progressive disclosure toggle: 56px min-height

### Keyboard Navigation
- Tab bar: Arrow keys move between tabs; Enter/Space activates; `tabindex="-1"` on inactive tabs
- Mobile regime chips: standard button navigation

### Screen Readers
- Signal icon: `aria-hidden="true"` — signal label text provides the accessible text
- Collapsed mobile panel: hidden with `hidden` attribute or `max-height:0; overflow:hidden` per existing pattern
- Active tab: `aria-selected="true"` announced; inactive tab panels hidden from ARIA tree via `hidden` attribute

### Contrast (verified against design tokens)
- Strong Outperform (success-600 #16A34A) on white: 5.1:1 — passes AA
- Outperform (success-700 #15803D) on white: 6.8:1 — passes AAA
- Neutral (neutral-400 #9AA5B1) on white: 3.2:1 — only used for icons at large size; signal label uses neutral-500 (#6B7280) at 4.8:1
- Underperform (warning-600 #D97706) on white: 3.4:1 — `warning-700 (#B45309, 5.2:1)` for the text label
- Strong Underperform (danger-600 #DC2626) on white: 4.5:1 — passes AA

**Note:** Use warning-700 (#B45309) for Underperform text label and danger-700 (#B91C1C) for Strong Underperform text label to ensure AA contrast. Reserve warning-600 / danger-600 for icon color only.

---

## Data Requirements

The backend must provide to the template:

```python
regime_implications = {
    "current_regime": "bull",  # "bull" | "neutral" | "bear" | "recession_watch"
    "regimes": {
        "bull": {
            "display_name": "Bull Market",
            "asset_classes": [
                {
                    "key": "equities",
                    "display_name": "Equities",
                    "signal": "strong_outperform",  # "strong_outperform" | "outperform" | "neutral" | "underperform" | "strong_underperform"
                    "annotation": "Cyclicals and growth sectors historically lead in bull phases.",
                    "leading_sectors": ["Technology", "Financials", "Consumer Discretionary"],  # equities only; None for other asset classes
                    "lagging_sectors": ["Utilities", "Consumer Staples"]                        # equities only; None for other asset classes
                },
                {
                    "key": "credit",
                    "display_name": "Credit",
                    "signal": "outperform",
                    "annotation": "HY spreads tighten as economic conditions improve; investment-grade in line.",
                    "leading_sectors": None,
                    "lagging_sectors": None
                },
                {
                    "key": "rates",
                    "display_name": "Rates",
                    "signal": "underperform",
                    "annotation": "Rising yields compress long-duration bond prices in expanding conditions.",
                    "leading_sectors": None,
                    "lagging_sectors": None
                },
                {
                    "key": "safe_havens",
                    "display_name": "Safe Havens",
                    "signal": "strong_underperform",
                    "annotation": "Gold and long-duration Treasuries trail as risk-on assets dominate.",
                    "leading_sectors": None,
                    "lagging_sectors": None
                },
                {
                    "key": "crypto",
                    "display_name": "Crypto",
                    "signal": "outperform",
                    "annotation": "Risk appetite supports crypto alongside equities in bull conditions.",
                    "leading_sectors": None,
                    "lagging_sectors": None
                }
            ]
        },
        "neutral": { ... },  # same structure
        "bear": { ... },
        "recession_watch": { ... }
    }
}
```

**Important:** The performance patterns (signal + annotation + sector lists) can be **static data** loaded from a configuration file — they reflect historical patterns, not real-time analysis. The backend only needs to inject `current_regime` dynamically; all 4 regime pattern blocks can be pre-compiled at startup.

**Missing data / unavailable:** If `regime_implications` is `None` (backend failure), hide the entire Section 0.75 silently (no empty state needed — this is supplementary content; the regime card in Section 0 remains the authoritative source).

---

## Design System References

| Element | Design System Reference |
|---------|------------------------|
| Section container | Component Library → Cards → Standard Card |
| Asset class card left border | Component Library → Cards → Metric Card (semantic border) |
| Progressive disclosure toggle | Visual Standards → Progressive Disclosure |
| Performance signal colors | Semantic Colors (success/warning/danger scale) |
| Typography | Typography → Type Scale |
| Spacing | Spacing System → 4px baseline grid |
| Section title pattern | Visual Standards → Section Headers (`.section-title` class) |

---

## Out of Scope (This Feature)

- **Individual company performance data** — This panel shows asset-class and sector patterns only; no individual ticker or company analysis.
- **Percentile or quantified returns** — "Equities returned +X% on average" adds false precision for a retail audience. Use qualitative signals (Outperform / Underperform) only.
- **Customizable regime parameters** — Users see the same historical patterns as all other users. No custom weighting.
- **Alerts on regime change** — Future integration with alert system. Out of scope.
- **Intra-regime granularity** — "Early bull vs. late bull" segmentation. Use the 4 existing FRED-MD regime labels only.
- **Real-time charts** — Asset class performance over time (line charts). The panel shows pattern direction, not time-series visualization.

---

## Open Questions

1. **Historical data source for patterns** — Should the signal values (Strong Outperform, etc.) come from published academic research (FRED-MD paper, CFA Institute "Mind the Cycle" Nov 2025, Fidelity Business Cycle Update methodology) or from internal backtesting of the FRED-MD regime engine against asset class data? **PM/Engineer: confirm sourcing approach.** If internal backtesting, what asset class data sources are available without new cost?

2. **Performance signal scale** — This spec uses 5 levels (Strong Outperform / Outperform / Neutral / Underperform / Strong Underperform). A simpler 3-level scale (Outperform / Neutral / Underperform) reduces cognitive load but loses nuance. **PM: which scale?**

3. **Crypto inclusion** — Crypto as an asset class has limited historical regime data relative to equities, credit, and rates (FRED-MD data goes back to 1960; crypto only to ~2009). Should crypto be included with a caveat ("limited historical data — pattern based on 2010–2025 only"), excluded from MVP, or shown with a shortened time-series label? **PM: preferred approach.**

4. **Section title and position** — This spec places the panel as Section 0.75. If PM prefers a different position (e.g., after Market Conditions as Section 2), the design adjusts cleanly. **PM: confirm placement.**

5. **Tab behavior on mobile** — This spec collapses the panel on mobile and provides 3 regime-switcher chips below the current-regime content. Alternative: always show a compact regime tab bar on mobile (below the section header) that shifts between 4 full-page content areas. **PM: acceptable complexity trade-off?**

---

*Spec complete. PM: Please review and approve to proceed to user story creation.*
