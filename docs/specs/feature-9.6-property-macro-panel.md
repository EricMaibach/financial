# Property Macro Panel — Residential & Farmland Indicators

**Issue:** #255
**Feature:** 9.6 — Property Macro Panel
**Created:** 2026-03-12
**Status:** Draft

---

## Overview

A dedicated property macro panel providing regime-contextualized residential real estate and farmland indicators using FRED and USDA NASS data. Real estate is a major asset class influencing inflation, credit conditions, and consumer balance sheets — currently absent from the dashboard.

**Scope:** Tier 1 only (required). Tier 2 (Zillow ZORI/ZHVI ratio, REIT ETF proxies) is at engineer's discretion if effort fits.

---

## Placement Decision: Dedicated Page vs. Homepage Section

**Decision: Dedicated page at `/property`**

**Rationale:**
- 4+ data series (Case-Shiller HPI, CPI Rent, Vacancy Rate, USDA Farmland $/acre) is too much for a homepage section without severely compressing each metric
- The data is low-frequency (monthly/annual), making it more appropriate as a reference page than a daily-glance section
- The pattern set by Credit, Equity, Rates, Dollar, Crypto, Safe Havens pages is well-established and directly applicable
- Users who want real estate context will navigate there deliberately, not scroll past it on the homepage
- A homepage teaser widget (§1.X) can surface a single "Property Macro" headline metric to drive navigation — see "Homepage Teaser" section below

**Navigation:** Add `Property` link to the top navbar after Safe Havens.

---

## Navigation Integration

**Route:** `/property`
**Nav label:** `Property`
**Nav icon:** `bi-house-door` (Bootstrap icon — consistent with icon set in use)

Mobile: collapses into hamburger (existing pattern).
Desktop: standard navbar link.

**Category color for page header:**
```css
--category-property: #8B5CF6;  /* violet-500 — distinct from all 6 existing asset colors */
```

Existing category colors for reference: Credit `#dc3545`, Equity `#0d6efd`, Rates `#0d6efd`, Dollar `#0dcaf0`, Crypto `#ffc107`, Safe Havens `#198754`. Violet is the only unused high-saturation color that is colorblind-distinguishable from all six.

---

## Page Header

Follows the `asset-page-header` component pattern from Feature 8.1:

```html
<header class="asset-page-header">
  <h1 class="asset-page-header__title">
    <i class="bi bi-house-door" style="color: var(--category-color);" aria-hidden="true"></i>
    Property Macro
  </h1>
  <p class="asset-page-header__description">
    Residential real estate and farmland macro indicators — regime-contextualized
  </p>
  <p class="asset-page-header__updated">
    Last Updated: <span id="last-updated-time">…</span>
  </p>
</header>
```

Per-page `:root` block:
```css
:root {
  --category-color: #8B5CF6;  /* violet — property */
}
```

---

## Page Layout

### Mobile (375px)

```
┌─────────────────────────────────┐
│ [navbar]                        │
├─────────────────────────────────┤
│ 🏠 Property Macro               │ ← page header component
│ Residential & farmland macro... │
│ Last Updated: Jan 2026          │
├─────────────────────────────────┤
│ ─── ⌄ Residential Housing ────  │ ← collapsed section (mobile default)
├─────────────────────────────────┤
│ ─── ⌄ Rental Market ──────────  │ ← collapsed section
├─────────────────────────────────┤
│ ─── ⌄ Farmland ───────────────  │ ← collapsed section
├─────────────────────────────────┤
│ [regime interpretation block]   │ ← always visible (like Trade Pulse)
└─────────────────────────────────┘
```

### Tablet (768px+)

```
┌──────────────────────────────────────────────────────┐
│ [navbar]                                              │
├──────────────────────────────────────────────────────┤
│ 🏠 Property Macro                    Jan 2026         │
├──────────────────────────────────────────────────────┤
│ [Residential Housing — expanded]                      │
│ [Case-Shiller HPI] [CPI Rent]  ← 2-col metric cards  │
├──────────────────────────────────────────────────────┤
│ [Rental Market — expanded]                            │
│ [Vacancy Rate]  ← 1 metric card                       │
├──────────────────────────────────────────────────────┤
│ [Farmland — expanded]                                 │
│ [USDA Farmland $/acre]  ← 1 metric card               │
├──────────────────────────────────────────────────────┤
│ [Regime interpretation block]                         │
└──────────────────────────────────────────────────────┘
```

### Desktop (1024px+)

```
┌──────────────────────────────────────────────────────┐
│  [chart area — 2/3 width] │ [Regime interp — 1/3]    │
│  [metric cards below]     │                           │
└──────────────────────────────────────────────────────┘
```

If charting is implemented for a metric (e.g., Case-Shiller HPI time series), use the chart + sidebar layout pattern from the asset detail pages. If charts are deferred to a future story, use the metric card grid only.

---

## Metric Specifications

### Section 1: Residential Housing

**Data:** Case-Shiller National HPI (FRED `CSUSHPISA`)

```
┌─────────────────────────────────────────┐
│ CASE-SHILLER HPI (NATIONAL)             │ ← text-xs, uppercase, neutral-500
│                                         │
│  324.5                                  │ ← current index value, text-4xl font-mono
│  ▲ +4.2% YoY                           │ ← YoY change badge (success/danger)
│                                         │
│  [■■■■■■■□□□] 72nd percentile          │ ← percentile bar (see Trade Pulse pattern)
│  Strong appreciation vs. 10-yr history  │ ← 1-line interpretation label
│                                         │
│  Jan 2026 · Preliminary                 │ ← text-xs, neutral-400
└─────────────────────────────────────────┘
```

**Data:** CPI Rent of Primary Residence (FRED `CUUR0000SEHA`)

```
┌─────────────────────────────────────────┐
│ CPI RENT (PRIMARY RESIDENCE)            │
│                                         │
│  +3.8%                                  │ ← YoY % change (primary metric)
│  ▲ vs. +4.1% prior month               │ ← MoM direction
│                                         │
│  [■■■■■□□□□□] 54th percentile          │
│  Elevated — above historical median     │
│                                         │
│  Jan 2026                               │
└─────────────────────────────────────────┘
```

### Section 2: Rental Market

**Data:** Rental Vacancy Rate (FRED `RRVRUSQ156N`)

```
┌─────────────────────────────────────────┐
│ RENTAL VACANCY RATE                     │
│                                         │
│  6.2%                                   │ ← current rate, text-4xl font-mono
│  ▼ Tightening (was 6.8% prior qtr)     │ ← direction note
│                                         │
│  [■■□□□□□□□□] 22nd percentile          │ ← tight market = low vacancies
│  Tight rental supply                    │
│                                         │
│  Q4 2025 · Quarterly                    │ ← cadence note
└─────────────────────────────────────────┘
```

Note on vacancy rate percentile: lower vacancy = tighter market. The percentile bar direction is: higher percentile = looser/buyer's market. Engineer should clarify in display whether the current value is "historically tight" or "historically loose" — the label below the bar handles this.

### Section 3: Farmland

**Data:** USDA NASS Farmland $/acre (farm real estate, cropland, pasture)

```
┌─────────────────────────────────────────┐
│ USDA FARMLAND ($/ACRE)                  │
│                                         │
│  Farm RE:  $4,080                       │ ← all-land average
│  Cropland: $5,460                       │ ← highest-value category
│  Pasture:  $1,650                       │
│                                         │
│  ▲ +5.1% YoY (Farm RE)                 │ ← YoY for primary metric
│                                         │
│  2025 · Annual                          │ ← annual cadence
└─────────────────────────────────────────┘
```

Farmland $/acre is annual — no percentile bar (insufficient data points for a meaningful percentile). Display the three values in a compact 3-row list. No chart unless historical series is long enough (NASS goes back to 1970 — engineer discretion on whether to chart it).

---

## Regime Interpretation Block

Follows the **identical pattern** as the Credit page interpretation block and Trade Pulse: 4px left border, lightbulb icon, uppercase label, body text.

```css
/* Reuse existing interpretation block pattern */
border-left: 4px solid var(--category-color);  /* violet for property */
background: var(--neutral-50);
border-radius: 0 8px 8px 0;
padding: var(--space-4) var(--space-5);
```

**Label:** `PROPERTY MACRO OUTLOOK`
**Icon:** `bi-lightbulb` (matches other interpretation blocks, `aria-hidden`)

**Copy matrix:** Engineer to define a config dict (same pattern as `credit_interpretation_config.py`) with combinations of:
- Macro regime (bull / neutral / bear / recession_watch)
- HPI trend (appreciating / flat / depreciating)
- Rental market tightness (tight / loose)

Minimum viable: 4 regime × 2 HPI direction = 8 combinations. See Trade Pulse for the 16-combination precedent.

---

## Percentile Bar

Reuse the Trade Pulse percentile bar component (8px tall, 5-zone color, `role="progressbar"`):

| Percentile | Zone Color | Label |
|------------|------------|-------|
| 0–20 | danger-600 | Historically low |
| 21–40 | warning-600 | Below average |
| 41–60 | neutral-400 | Near average |
| 61–80 | info-600 | Above average |
| 81–100 | success-600 | Historically high |

Accessibility: `role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100" aria-label="{metric} at {pct}th percentile"`

---

## Homepage Teaser Widget (Optional — Single Story)

A small "Property Macro" teaser in the homepage evidence tier (§1.X) — one metric card showing Case-Shiller HPI with a link to `/property` for full detail. This is optional and can be a separate user story.

```
┌─────────────────────────────────────┐
│ PROPERTY MACRO         → Full View  │ ← link to /property
│ Case-Shiller HPI: 324.5 ▲ +4.2%   │
│ Rental vacancy tight · Jan 2026     │
└─────────────────────────────────────┘
```

If the homepage teaser story is included, it belongs in the homepage evidence tier between §1 Market Conditions and §1.3 Trade Pulse (or after §1.3).

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| 375px | Single column; all 3 sections collapsed by default; interpretation block always visible |
| 768px | All 3 sections expanded; metric cards 2-col within each section (except farmland: 1 card with 3-row list) |
| 1024px+ | 2/3 + 1/3 layout if chart exists; 3-col metric grid if chart-less |

---

## Accessibility Requirements

- Page title: `<title>Property Macro — SignalTrackers</title>`
- Page follows `asset-page-header` accessibility pattern (aria-hidden on decorative icon)
- Collapsible sections: `aria-expanded` on toggle, `aria-controls` referencing content div
- Percentile bar: `role="progressbar"` with aria values (see above)
- Farmland data table alternative: if displayed as a 3-row list, use `<dl>` (definition list) with `<dt>` for label and `<dd>` for value
- Color contrast: violet `--category-color` (#8B5CF6) on white = 3.1:1 — meets 3:1 for large text/UI elements ✓; do NOT use violet for body text (use neutral-600 instead)

---

## Design System References

- Colors: `--category-property: #8B5CF6` (new token); neutral scale; semantic success/danger/warning for directional badges
- Typography: text-xs labels, text-4xl metric values (font-mono), text-sm body
- Components: asset-page-header, interpretation block pattern (Trade Pulse), percentile bar (Trade Pulse), collapsible section pattern, metric card (4px left border)
- Pattern reference: `docs/specs/feature-8.2-global-trade-pulse.md` — closest structural precedent

---

## Implementation Notes

- New template: `signaltrackers/templates/property.html` — extend `base.html`, link `asset-page-header.css`
- New CSS: `signaltrackers/static/css/property.css` (per-page, same as credit.css pattern)
- Backend: New route `/property` in Flask app; new data config dict for interpretation copy
- USDA NASS API: requires free registration — `USDA_NASS_API_KEY` must be added to `.env.example`; ask user to add to `.env`
- FRED series: reuse existing FRED integration; add 3 new series (`CSUSHPISA`, `CUUR0000SEHA`, `RRVRUSQ156N`)
- Tier 2: Zillow ZORI/ZHVI (free CSV) and REIT ETF proxies via yfinance — at engineer's discretion

**Story split (suggested by PM):**
- US-255.1: Backend data pipeline (FRED + NASS integration, interpretation config)
- US-255.2: Property page frontend (template, metric cards, percentile bars, collapsible sections)
- US-255.3 (optional): Homepage teaser widget at §1.X
