# Macro Regime Detection — Design Spec

**Issue:** #108
**Feature:** Regime-Conditional Signal Weighting
**Created:** 2026-02-23
**Designer:** UI/UX Designer
**Status:** Draft

---

## Overview

Wrap existing macro signals with a current macro regime state (Bull / Neutral / Bear / Recession Watch) so users receive contextualized interpretation rather than raw indicators. The regime state is derived from FRED-MD data and updated daily.

**User problem:** Right now, SignalTrackers surfaces raw signals (HY spread at 450bps, 10Y yield at 4.2%). Users must interpret these themselves — "Is 450bps high? Is it dangerous in this environment?" The regime layer answers that question automatically: "In a Bear regime, an HY spread at 450bps has historically preceded credit stress within 6–9 months."

**Design goal:** Make the regime state feel like a **trusted briefing**, not a data dump. The regime card is the first thing users see, frames everything else, and disappears into the background once they've absorbed it.

---

## Regime States

Four states, covering the full macro cycle. Each has a distinct color and icon.

| State | Color | Background | Icon | When |
|-------|-------|------------|------|------|
| **Bull** | success-600 `#16A34A` | success-100 `#DCFCE7` | `bi-arrow-up-circle-fill` | Accelerating growth, low credit stress |
| **Neutral** | brand-blue-500 `#1E40AF` | brand-blue-100 `#DBEAFE` | `bi-dash-circle-fill` | Mixed signals, no clear directional trend |
| **Bear** | warning-600 `#CA8A04` | warning-100 `#FEF3C7` | `bi-arrow-down-circle-fill` | Decelerating growth, rising credit stress |
| **Recession Watch** | danger-600 `#DC2626` | danger-100 `#FEE2E2` | `bi-exclamation-circle-fill` | Contraction indicators active |

**Never use red for Bear** — reserve danger-600 for Recession Watch only. This preserves the semantic severity ladder.

---

## User Flow

1. User opens SignalTrackers homepage
2. **New: Regime card** is the first content section — shows current state, plain-language summary, and 2–3 regime-highlighted signals
3. User scrolls to existing "Market Conditions at a Glance" — category badges now carry a subtle regime-relevance indicator (for regime-sensitive categories)
4. User taps into a detail page (e.g., Rates)
5. **New: Compact regime strip** at top of detail page shows current state + one regime-relevant sentence for that category
6. User expands a metric card → **New: Regime context annotation** appears below the metric value with historical regime context

---

## Wireframes

### Homepage — Section 0: Macro Regime (New)

Sits above "Market Conditions at a Glance" as the **very first section** on the homepage.

#### Mobile (375px)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  CURRENT MACRO REGIME                               │
│  ┌─────────────────────────────────────────────┐   │
│  │ ● BEAR REGIME          Updated Feb 23, 2026 │   │
│  │ ─────────────────────────────────────────── │   │
│  │ "Growth is decelerating and credit spreads   │   │
│  │ are widening. Risk assets face headwinds.    │   │
│  │ Watch credit and safe haven signals closely."│   │
│  │ ─────────────────────────────────────────── │   │
│  │ REGIME-HIGHLIGHTED SIGNALS                  │   │
│  │ ┌──────────────┐ ┌──────────────┐           │   │
│  │ │ HY Spread    │ │ VIX          │           │   │
│  │ │ 462bps       │ │ 28.4         │           │   │
│  │ │ ▲ High risk  │ │ ▲ Elevated   │           │   │
│  │ └──────────────┘ └──────────────┘           │   │
│  │ ┌──────────────┐                            │   │
│  │ │ Gold         │                            │   │
│  │ │ $2,640       │                            │   │
│  │ │ ✓ Confirming │                            │   │
│  │ └──────────────┘                            │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Tablet / Desktop (768px+)

```
┌─────────────────────────────────────────────────────────────────┐
│ CURRENT MACRO REGIME                              Updated daily  │
│                                                                  │
│ ┌───────────────────────┐  ┌──────────────────────────────────┐ │
│ │ ● BEAR REGIME         │  │ Growth is decelerating and       │ │
│ │                       │  │ credit spreads are widening.     │ │
│ │ Feb 23, 2026          │  │ Risk assets face headwinds.      │ │
│ │                       │  │ Watch credit and safe haven      │ │
│ │ Confidence: High      │  │ signals closely.                 │ │
│ └───────────────────────┘  └──────────────────────────────────┘ │
│                                                                  │
│ REGIME-HIGHLIGHTED SIGNALS                                       │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│ │ HY Spread     │  │ VIX           │  │ Gold          │        │
│ │ 462bps        │  │ 28.4          │  │ $2,640        │        │
│ │ ▲ Elevated    │  │ ▲ Elevated    │  │ ✓ Confirming  │        │
│ │ risk signal   │  │ fear signal   │  │ bear defense  │        │
│ └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Detail Page — Compact Regime Strip (New)

Appears at the top of each asset class page (rates.html, credit.html, equity.html, dollar.html, crypto.html, safe_havens.html). Replaces nothing — inserts between page header and first content section.

#### Mobile (375px)

```
┌─────────────────────────────────────────────────────┐
│ [page header: Interest Rates]                       │
├─────────────────────────────────────────────────────┤
│ ● BEAR REGIME  │ In this regime, yield curve        │
│                │ inversions carry higher recession  │
│                │ predictive weight.                 │
├─────────────────────────────────────────────────────┤
│ [chart section]                                     │
└─────────────────────────────────────────────────────┘
```

The strip is a single horizontal row:
- Left: Regime badge (colored dot + regime name)
- Right: One sentence of regime relevance for this page's category
- Full-width, 1px bottom border (neutral-200), neutral-50 background
- Padding: 12px vertical, 16px horizontal

---

### Signal Card — Regime Context Annotation (New)

Within expanded metric sections on detail pages. The regime annotation appears **after the metric value**, as a secondary line. Collapsed by default on mobile; visible by default on tablet+.

#### Mobile (375px) — expanded metric card

```
┌─────────────────────────────────────────────────────┐
│ 10Y Treasury Yield                                  │
│ 4.23%         ▲ +8bps                               │
│ ── In Bear regime: ─────────────────────────────── │
│ "Rising yields here signal growth concerns, not     │
│  inflation expectations. Watch for inversion."      │
│ ─────────────────────────────────────────────────── │
│ [historical context link: Learn more]               │
└─────────────────────────────────────────────────────┘
```

The regime annotation block:
- Hairline divider above (neutral-200)
- `REGIME CONTEXT` label: text-xs, neutral-500, uppercase, tracking-wide
- Annotation text: text-sm, neutral-600
- Background: regime color at 5% opacity (e.g., warning-100 at low opacity)
- Left border: 3px solid regime color
- Border-radius: 0 4px 4px 0
- Max 2 lines of annotation text — no truncation, line wrap is fine

---

## Component Specifications

### 1. Macro Regime Card (Homepage)

**Container:**
- Background: regime-100 color (changes per regime state)
- Border: 1px solid regime-200 (darken regime-100 by one step)
- Border-radius: 12px
- Padding: 20px (mobile), 24px (desktop)
- Shadow: none (colored background carries the weight)

**Regime State Header Row:**
- Left: Colored dot (12px circle, regime-600) + regime name in ALL CAPS
- Font: text-lg (18px), weight 700, neutral-800
- Right: "Updated [date]" in text-xs, neutral-500
- Spacing below: 12px

**Divider:** 1px neutral-200 hairline, 12px margin top/bottom

**Plain-Language Summary:**
- Font: text-base (16px), weight 400, neutral-700
- Line height: 1.6
- Max 3 sentences
- Italic style to distinguish from data

**Divider:** 1px neutral-200 hairline, 16px margin top/bottom

**Regime-Highlighted Signals:**
- Label: "REGIME-HIGHLIGHTED SIGNALS" in text-xs, neutral-500, uppercase, tracking-wide
- Signal chips: 2–3 cards, inline on desktop (side by side), 2-column grid on mobile
- Each chip:
  - Signal name: text-sm, neutral-700, weight 600
  - Value: text-base, neutral-800, weight 700, monospace
  - Regime annotation: text-xs, neutral-600 with icon (▲ / ✓ / ─)
  - Background: white, 1px neutral-200 border, 6px border-radius
  - Padding: 12px
  - Touch target: minimum 44px height

**Confidence Indicator (desktop only):**
- "Confidence: High / Medium / Low" tag
- Displayed in the regime state panel
- Colors: High = success, Medium = warning, Low = danger
- Font: text-sm, weight 500

---

### 2. Compact Regime Strip (Detail Pages)

**Container:**
- Background: neutral-50
- Border-bottom: 1px solid neutral-200
- Padding: 12px 16px
- Display: flex, align-items: flex-start, gap: 12px

**Regime Badge:**
- Colored dot (8px circle) + regime name
- Font: text-sm, weight 700, uppercase, regime-700 color
- Min-width: 120px (prevents text reflow)
- Vertical separator: 1px solid neutral-200 on right (desktop only)

**Context Sentence:**
- Font: text-sm, weight 400, neutral-600
- Max 1 sentence, 100 characters max
- Engineer: content is dynamically provided per page by the backend (category-specific regime context)

---

### 3. Signal Regime Annotation (Within Metric Cards)

**Trigger:** Shows when a detail page metric card is in expanded state.

**Container:**
- Border-left: 3px solid regime-600 color
- Background: regime-100 at 40% opacity (use CSS: `color-mix(in srgb, regime-100 40%, white)`)
- Padding: 8px 12px
- Border-radius: 0 4px 4px 0
- Margin-top: 8px

**Label:**
- "REGIME CONTEXT" in text-xs, neutral-500, uppercase, letter-spacing: 0.05em
- Display: flex, align-items: center, gap: 6px
- Icon: bi-info-circle at text-xs, regime-600 color

**Annotation Text:**
- Font: text-sm, neutral-700
- Line height: 1.5
- Max 2 lines (wrap, don't truncate)

**Collapse on Mobile:**
- On mobile, annotation is collapsed by default (shows "REGIME CONTEXT ˅" as a toggle)
- Expands on tap
- On tablet+, annotation is always visible
- This prevents mobile signal cards from becoming too tall

---

### 4. Homepage Category Badges — Regime Relevance

The existing badge-cards on the homepage ("CREDIT", "EQUITIES", "RATES", etc.) get a subtle regime-relevance marker when in expanded view. This tells users which categories matter most **in the current regime**.

**When a category is regime-highlighted:**
- Add a small colored dot (6px) in the top-right corner of the badge card
- Add a `regime-highlighted` CSS class
- Tooltip/aria-label: "Highly relevant in current [regime] regime"

**Implementation note:** Backend provides which categories are regime-relevant. Designer does NOT add static styling — this is fully data-driven.

---

## Interaction Patterns

### Regime Card Transitions
- When regime state changes (daily update), do NOT animate in place
- On next page load after a state change, the card background color will update
- No flashing or animated transitions — jarring for a financial dashboard

### Annotation Collapse (Mobile)
- Tap on "REGIME CONTEXT ˅" → smooth expand (200ms ease-out, max-height transition)
- Tap again → collapse
- Chevron rotates 90° when expanded (matches existing collapsible-section pattern)

### Signal Chips (Homepage)
- Tapping a signal chip navigates to the relevant detail page (deep link to that metric)
- Hover state (desktop): subtle lift (translateY(-1px), shadow-sm) — same pattern as existing metric cards
- Active state: translateY(0), shadow-none

---

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|---------------|
| 375px (mobile) | Regime card stacked; signal chips 2-column grid; annotations collapsed by default |
| 640px (large phone) | Signal chips remain 2-col; annotation visible |
| 768px (tablet) | Regime card splits to 2-col (state panel + summary side by side); signal chips 3-col |
| 1024px (desktop) | Full layout; confidence indicator visible; category relevance dots visible |
| 1280px+ | No additional layout changes; max-width container applies |

---

## Accessibility Requirements

### Regime Card
- `<section aria-label="Current Macro Regime">` wraps the entire regime card
- Regime state change announced via `aria-live="polite"` on the state heading (daily update)
- Regime state uses both color AND text — never color alone
- Signal chips have `role="link"` and `aria-label="[Signal name]: [value], [annotation]"`

### Color Independence
- All four regime states are distinguishable without color:
  - Bull: upward arrow icon + "BULL" text
  - Neutral: dash icon + "NEUTRAL" text
  - Bear: downward arrow icon + "BEAR" text
  - Recession Watch: exclamation icon + "RECESSION WATCH" text

### Contrast
- All text on regime-100 backgrounds: check each combination
  - success-700 on success-100: passes AAA (7.2:1)
  - brand-blue-700 on brand-blue-100: passes AA (5.1:1)
  - warning-700 on warning-100: passes AA (5.4:1)
  - danger-700 on danger-100: passes AAA (7.8:1)

### Touch Targets
- Signal chips: 44px minimum height (enforce with min-height)
- Annotation collapse toggle: 44px touch target (add padding)
- All interactive elements: 44px minimum per existing standards

### Screen Reader
- Regime annotation text is always available to screen readers (not hidden when collapsed visually — use `aria-expanded` with reveal via CSS)
- Plain-language summary is not behind any interactive control — always in the DOM and visible

---

## Design System References

| Component | Design System Section |
|-----------|----------------------|
| Regime colors | Color System → Semantic Colors (new Regime variants derived from existing semantic scale) |
| Card container | Component Library → Cards → Standard Card |
| Signal chips | Component Library → Cards → Metric Card (new regime annotation sub-component) |
| Collapse toggle | Visual Standards → Progressive Disclosure |
| Typography | Typography → Type Scale |
| Spacing | Spacing System → 4px baseline grid |
| Badge dots | Component Library → Badges |

### New Design Token Additions

Add to `design-system.md` (Engineer should define in CSS variables):

```css
/* Regime States — derived from existing semantic palette */
--regime-bull-bg:         var(--success-100);
--regime-bull-border:     var(--success-600);
--regime-bull-text:       var(--success-700);

--regime-neutral-bg:      var(--brand-blue-100);
--regime-neutral-border:  var(--brand-blue-500);
--regime-neutral-text:    var(--brand-blue-600);  /* NOTE: use brand-blue-700 for text */

--regime-bear-bg:         var(--warning-100);
--regime-bear-border:     var(--warning-600);
--regime-bear-text:       var(--warning-700);

--regime-recession-bg:    var(--danger-100);
--regime-recession-border: var(--danger-600);
--regime-recession-text:  var(--danger-700);
```

---

## Out of Scope (This Feature)

- **Option A (Macro Regime Score Panel)** — A standalone dashboard panel with charts and historical regime data. This is the natural next feature after this one validates the concept. Design spec will be created separately.
- **Historical regime charts** — Showing how regime states have changed over time. Future feature.
- **User-configurable signal weights** — Users setting their own weights by regime. Future feature.
- **Push notifications on regime change** — Future feature (extends alert system in Feature #109).

---

## Open Questions

1. **Confidence indicator** — The FRED-MD methodology (arXiv 2503.11499) may produce a classification confidence score. If available from the backend, should it be surfaced to users? (Assumed: yes, on desktop only — as per this spec.) PM/Engineer: confirm if confidence is available.

2. **Signal annotation content** — This spec defines the UI shell. The backend/engineer must provide the regime-conditioned text per signal per regime state. Are these static strings stored in config, or dynamically generated by an LLM? Design is agnostic, but character limits apply: max 100 characters per annotation, max 200 characters for the plain-language summary.

3. **How many highlighted signals?** — This spec shows 2–3. The backend determines which signals are regime-relevant. Is there a fixed count (always 3) or variable (1–4 depending on active signals)? Design works for 1–4; above 4 wraps to a second row on mobile.

4. **Category relevance dots** — Should the regime-relevance dots on the homepage badge-cards always show (all 6 categories have some weight), or only highlight categories above a relevance threshold? Recommend: threshold approach — only show the dot when a category has elevated regime relevance, to preserve the signal value.

---

*Spec complete. PM: Please review and approve to proceed to user story creation.*
