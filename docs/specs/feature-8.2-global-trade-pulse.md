# Global Trade Pulse — Design Spec

**Issue:** #206
**Feature:** 8.2 — Global Trade Pulse (FRED Trade Balance Indicator)
**Created:** 2026-03-06
**Status:** Draft

---

## Overview

A new homepage macro panel displaying the US goods trade balance (FRED BOPGSTB series) with YoY change, a historical percentile ranking, and a regime-conditioned plain-language interpretation block. Global trade flows lead economic activity and moved independently of equity markets during the 2025 tariff shock — this closes a real signal gap in the platform.

Scope: FRED-only. No BDI or non-FRED data integration in this feature.

---

## Placement

**Homepage — Section 1.3**, inserted between §1 Market Conditions and §1.5 Sector Tone.

```
§0    Macro Regime Score
§0.5  Recession Probability
§0.75 Regime Implications
§1    Market Conditions at a Glance    ← existing
§1.3  Global Trade Pulse               ← NEW (this feature)
§1.5  Sector Management Tone          ← existing
§2    Today's Briefing
§3    What's Moving
```

**Rationale:** Trade balance is macro-level evidence — it belongs in the evidence tier alongside Market Conditions, not in the interpretation tier. The §1 Market Conditions section already covers equity, rates, and credit signals; Global Trade Pulse adds the trade flow dimension. Placing it after §1 and before §1.5 (Sector Tone) preserves the EVIDENCE → SECTOR IMPLICATIONS reading order.

**Section nav registration:** Engineer must add a new pill (`Trade`) to the desktop quick-nav strip and mobile bottom sheet in `index.html`, with `data-target="#trade-pulse-section"` and a matching `id="trade-pulse-section"` on the new `<section>` element.

---

## User Flow

1. User has absorbed the current regime verdict (§0) and recession risk (§0.5)
2. User scrolls to §1 Market Conditions — sees equity, rates, credit signal summary
3. User scrolls to §1.3 Global Trade Pulse — sees current trade balance value and YoY direction at a glance
4. Percentile badge contextualizes the reading ("33rd percentile — weaker than usual")
5. Regime-conditioned interpretation block provides the plain-language "so what" in 1–2 sentences anchored to the current macro regime
6. User understands whether trade flow corroborates or diverges from the equity/credit signal in §1

---

## Data Points to Display

| Element | Source | Notes |
|---------|---------|-------|
| Current value (USD billions) | FRED BOPGSTB | Monthly — display as "−$XX.Xb" or "+$XX.Xb" |
| YoY change (% or absolute) | Derived | Current month vs. same month prior year |
| Historical percentile | Derived (rolling window) | Engineer to define window — suggest 10 years (120 months) |
| Interpretation text | Backend config | Regime-conditioned, see copy spec below |
| Data freshness | FRED publication date | Display as "Last Updated: {date}" |

> **Data note:** BOPGSTB is monthly and is typically revised. Engineer should display the most recent available value and note if it is preliminary. Display month/year of the reading (e.g., "Jan 2026"), not just a relative date.

---

## Wireframes

### Mobile (375px) — Collapsed Default

```
┌──────────────────────────────────────────────────┐
│  GLOBAL TRADE PULSE                              │
│  US Goods Trade Balance                         │
│  ─────────── ⌄ View Trade Data ─────────────── │
└──────────────────────────────────────────────────┘
```

Follows the standard collapsible-section pattern used by all other homepage sections. Collapsed by default on mobile (375px). Expanded by default on tablet+ (768px+).

### Mobile (375px) — Expanded

```
┌──────────────────────────────────────────────────┐
│  GLOBAL TRADE PULSE                              │
│  US Goods Trade Balance (FRED BOPGSTB)          │
│  ─────────── ⌃ Hide ────────────────────────── │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  −$XX.Xb            ↓ YoY                 │  │
│  │  Jan 2026        −$X.Xb vs. Jan 2025       │  │
│  │                                            │  │
│  │  Percentile: [══════════░░░░░] 33rd pct.   │  │
│  │  Weaker than 67% of months (10-year range) │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ 💡  CONTRACTION REGIME · WIDENING DEFICIT  │  │
│  │  Trade volumes are contracting — consistent│  │
│  │  with the current Contraction regime. A    │  │
│  │  widening deficit adds headwinds for USD   │  │
│  │  and may pressure export-sensitive sectors.│  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Last Updated: Jan 2026 (FRED BOPGSTB)          │
└──────────────────────────────────────────────────┘
```

### Tablet (768px) — Expanded (default)

```
┌──────────────────────────────────────────────────────────────────────┐
│  GLOBAL TRADE PULSE · US Goods Trade Balance (FRED BOPGSTB)         │
│ ─────────────────────────────────────────────────────── ⌃ Hide ────  │
│                                                                      │
│  ┌────────────────────────────────┐  ┌────────────────────────────┐  │
│  │  −$XX.Xb                      │  │  Percentile                │  │
│  │  Jan 2026                     │  │  [══════░░░░░░] 33rd        │  │
│  │  ↓ −$X.Xb vs. Jan 2025        │  │  Weaker than 67%           │  │
│  │                               │  │  of months (10-yr range)   │  │
│  └────────────────────────────────┘  └────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ 💡 CONTRACTION REGIME · WIDENING DEFICIT                     │    │
│  │ Trade volumes are contracting — consistent with the current  │    │
│  │ Contraction regime. A widening deficit adds headwinds for USD │    │
│  │ and may pressure export-sensitive sectors.                   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Last Updated: Jan 2026 (FRED BOPGSTB)                              │
└──────────────────────────────────────────────────────────────────────┘
```

### Desktop (1280px)

Same as tablet layout but inside the standard container-xl max-width. The current value + percentile panel sits in a 2-column grid (1fr 1fr or a natural flex row). No widescreen-specific changes beyond the container width constraint.

---

## Component Anatomy

### 1. Metric Panel

Displays the current value, reading period, and YoY change as a single prominent data block.

```
Structure:
  [Large numeric] — current value: font-mono, text-3xl on tablet+ / text-2xl on mobile
  [Period label]  — "Jan 2026": text-sm, neutral-500
  [YoY badge]     — icon + amount: icon is ↑ (success-600) or ↓ (danger-600) + text-sm value

Color rules:
  Positive trade balance (surplus): success-600 for YoY badge and arrow icon
  Negative trade balance (deficit): danger-600 for YoY badge and arrow icon
  Never use color alone — always pair icon + text label
  Numeric value itself: neutral-800 always (the sign conveys direction; color is on the change badge)
```

### 2. Percentile Bar

Visualizes where the current reading falls in the historical distribution.

```
Structure:
  Label row: "Percentile" (text-sm, neutral-500) + value (text-sm, font-weight 600, neutral-700)
  Bar:        Full-width progress bar
              Background: neutral-200
              Fill:        Semantic color (see rules below)
              Height:      8px
              Border-radius: 4px
  Footer:    "Weaker / Stronger than X% of months (10-year range)" — text-xs, neutral-500

Percentile color rules:
  0–25th pct  (severe contraction):  danger-600 fill
  26–40th pct (below average):       warning-600 fill
  41–60th pct (neutral):             neutral-400 fill
  61–75th pct (above average):       info-600 fill
  76–100th pct (strong expansion):   success-600 fill

Language: "Weaker than X% of months" when below 50th pct; "Stronger than X% of months" when above.
Note: never color alone — percentile number and text label always accompany the bar.
```

### 3. Regime-Conditioned Interpretation Block

Follows the Credit page `credit-interpretation-block` UX pattern exactly. Uses a 4px left border with the panel's category color, a lightbulb icon, an uppercase regime context label, and 1–2 sentences of plain-language interpretation.

```
Structure:
  Left border:  4px solid var(--category-trade) [new token, see below]
  Background:   var(--neutral-50)
  Border-radius: 0 6px 6px 0
  Padding:      space-4 space-5

  Header row:
    Icon:  bi-lightbulb-fill, color: var(--category-trade), text-sm
    Label: text-xs, font-weight 700, uppercase, letter-spacing 0.05em, neutral-500
           Format: "{REGIME NAME} REGIME · {CONDITION LABEL}"
           e.g.: "CONTRACTION REGIME · WIDENING DEFICIT"

  Body:
    font-size: text-sm
    line-height: 1.65
    color: neutral-700
    1–2 sentences of plain-language interpretation
```

**Category color token:** `--category-trade: #0D9488` (chart-teal from design system). Teal is distinct from all 6 existing asset page category colors and is on the colorblind-friendly chart palette. This token is added to the section's `:root` or inline on the panel element.

### 4. Data Freshness Line

```
Text: "Last Updated: {Month Year} (FRED BOPGSTB)"
Style: text-xs, neutral-400, align: left on mobile, right on desktop
```

---

## Regime-Conditioned Copy Spec

The interpretation block text must be authored per regime state. The backend should select from a config dict keyed by regime + trade_condition (widening deficit / narrowing deficit / narrowing surplus / widening surplus).

### States and Copy

**Expansion Regime**

| Trade Condition | Label | Copy |
|-----------------|-------|------|
| Widening deficit | EXPANSION REGIME · WIDENING DEFICIT | "Trade volumes are growing but the goods deficit is widening — a typical pattern in expansion as US import demand rises faster than exports. Watch for USD softness if the deficit widens materially." |
| Narrowing deficit | EXPANSION REGIME · NARROWING DEFICIT | "Trade conditions are improving alongside the expansion — a narrowing goods deficit reduces external drag and supports the USD. This is a constructive signal for the macro backdrop." |
| Widening surplus | EXPANSION REGIME · WIDENING SURPLUS | "The goods trade balance is improving materially in an expansion — export demand is strong. This is a positive signal for trade-sensitive sectors and USD stability." |
| Narrowing surplus | EXPANSION REGIME · NARROWING SURPLUS | "Export surplus is narrowing in an expansion phase — import demand is picking up, which is consistent with strong domestic consumption. Monitor for future current account pressure." |

**Contraction Regime**

| Trade Condition | Label | Copy |
|-----------------|-------|------|
| Widening deficit | CONTRACTION REGIME · WIDENING DEFICIT | "Trade volumes are contracting and the goods deficit is widening — a pressure pattern that adds headwinds for the USD and may weigh on export-sensitive sectors in an already-weak macro environment." |
| Narrowing deficit | CONTRACTION REGIME · NARROWING DEFICIT | "The goods deficit is narrowing in a contraction — typically because import demand is falling faster than export weakness. This may provide modest USD support but reflects weak domestic demand, not trade strength." |
| Widening surplus | CONTRACTION REGIME · IMPROVING BALANCE | "Trade balance is improving in a contraction — falling imports are reducing the deficit. This provides some buffer for the USD but the signal reflects demand weakness, not export-driven strength." |
| Narrowing surplus | CONTRACTION REGIME · MIXED SIGNAL | "Export surplus is narrowing as the contraction weighs on global trade. External demand is softening — watch for further deterioration in export-heavy sectors." |

**Neutral Regime**

| Trade Condition | Label | Copy |
|-----------------|-------|------|
| Widening deficit | NEUTRAL REGIME · WIDENING DEFICIT | "The goods trade deficit is widening in a neutral macro environment — modest negative signal for the USD and external balance. No immediate implication for domestic growth." |
| Narrowing deficit | NEUTRAL REGIME · NARROWING DEFICIT | "Trade balance is improving slightly in a neutral regime — a positive but non-decisive signal. External drag on growth is easing gradually." |
| Widening surplus | NEUTRAL REGIME · WIDENING SURPLUS | "Trade balance is strengthening in a neutral regime — modest positive for USD and reduced external drag. Not a regime-moving signal on its own." |
| Narrowing surplus | NEUTRAL REGIME · STABLE TRADE | "Trade balance is relatively stable in a neutral macro environment. No significant trade flow signal at this time." |

**Recession Watch Regime**

| Trade Condition | Label | Copy |
|-----------------|-------|------|
| Widening deficit | RECESSION WATCH · WIDENING DEFICIT | "Trade conditions are deteriorating alongside elevated recession risk. A widening goods deficit in a recession-watch environment adds external pressure — this combination has historically preceded USD stress and tightening financial conditions." |
| Narrowing deficit | RECESSION WATCH · NARROWING DEFICIT | "The goods deficit is narrowing in a recession-watch environment — likely reflecting falling import demand as businesses and consumers pull back. This is a defensive, not constructive, signal." |
| Widening surplus | RECESSION WATCH · IMPROVING BALANCE | "Trade balance is improving as import demand contracts in a recession-watch environment. The improvement is driven by weakness, not export strength — treat cautiously." |
| Narrowing surplus | RECESSION WATCH · WEAKENING TRADE | "Export surplus is narrowing as global demand softens — a leading indicator of further trade deterioration consistent with elevated recession risk." |

> **Fallback copy:** If regime is unavailable: "US goods trade balance is at the {Nth} percentile of the past 10 years. A reading below the 33rd percentile indicates below-average trade flow conditions."

---

## Collapsible Section Integration

Uses the standard `.collapsible-section` / `.collapsible-section__header` / `.collapsible-section__content` pattern established across the homepage.

```html
<section id="trade-pulse-section" class="mb-4 regime-thread{% if macro_regime %} {{ macro_regime.css_class }}{% endif %}" aria-label="Global Trade Pulse">
    <div class="section-header mb-3">
        <h2 class="section-header__title">Global Trade Pulse</h2>
        <span class="section-header__subtitle">US Goods Trade Balance (FRED BOPGSTB)</span>
    </div>
    <!-- Metric panel + percentile bar + interpretation block -->
</section>
```

The `.regime-thread` class means the section will automatically receive the 4px left-border regime color accent when the regime CSS class is present (following Approach 2 of Feature #183 / US-183.1).

---

## Mobile Behavior

- **Collapsed by default** at 375px (follows homepage pattern for all non-hero sections)
- **Expanded by default** at 768px+
- Tap target for collapse toggle: 56px min-height (standard section header)
- All tap targets within expanded panel: 44px minimum
- Text sizes do not scale below 16px (iOS zoom prevention)
- Percentile bar scales to full width of panel at all breakpoints

---

## Quick-Nav Integration

The section must be added to both the desktop sticky pill strip and the mobile bottom sheet in `index.html`.

| Element | Value |
|---------|-------|
| Desktop pill label | `Trade` |
| Mobile sheet label | `Trade` |
| `data-target` | `#trade-pulse-section` |
| Section `id` | `trade-pulse-section` |
| Position in list | After `Markets` (#market-conditions), before `Sectors` (#sector-tone-section) |

---

## Accessibility

- `<section aria-label="Global Trade Pulse">` as the landmark
- Collapsible toggle: `aria-expanded` on the button element
- Percentile bar: `role="progressbar"` with `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="Trade balance at Nth percentile of 10-year range"`
- YoY change icon: `aria-hidden="true"` (direction communicated by text label)
- Interpretation icon: `aria-hidden="true"`
- Interpretation block: no special ARIA needed — it is static, not live-updating

---

## Design Tokens Used

| Token | Value | Purpose |
|-------|-------|---------|
| `--category-trade` | `#0D9488` (chart-teal) | Left border and icon accent on interpretation block |
| `--neutral-50` | `#FAFBFC` | Interpretation block background |
| `--neutral-200` | `#E8ECEF` | Percentile bar background track |
| `--neutral-400` | `#9AA5B1` | Neutral percentile fill |
| `--neutral-500` | `#697386` | Percentile label, updated timestamp |
| `--neutral-700` | `#2D3748` | Interpretation body text |
| `--neutral-800` | `#1A202C` | Large numeric value |
| `--success-600` | `#16A34A` | Positive YoY arrow and high percentile fill |
| `--danger-600` | `#DC2626` | Negative YoY arrow and low percentile fill |
| `--warning-600` | `#CA8A04` | Below-average percentile fill |
| `--info-600` | `#0284C7` | Above-average percentile fill |
| `--text-2xl` | 24px | Current value (mobile) |
| `--text-3xl` | 30px | Current value (tablet+) |
| `--text-sm` | 14px | Labels, YoY change, interpretation body |
| `--text-xs` | 12px | Interpretation block header label, data freshness |

---

## Out of Scope

- BDI (Baltic Dry Index) integration — explicitly deferred by CEO to Phase 9+
- Historical chart / sparkline for BOPGSTB — FRED data is monthly; a sparkline may be added in a future story if signal value is confirmed
- New detail page for trade — panel lives on the homepage macro section only
- Non-FRED data sources

---

## Design Review Criteria

When Engineer submits for design review, provide screenshots at 375px (mobile collapsed), 375px (mobile expanded), 768px, and 1280px showing the full panel including the interpretation block. Verify:

1. Left border color matches `--category-trade` (teal)
2. Large numeric value is font-mono, appropriately sized
3. Percentile bar fills correctly and is readable at all widths
4. Interpretation block structure matches Credit page pattern (icon + uppercase label + body text)
5. Section collapses/expands correctly on mobile
6. Quick-nav pill `Trade` appears and scrolls correctly
