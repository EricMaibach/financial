# Portfolio Real Estate Categories Design Spec

**Issue:** #238
**Created:** 2026-03-10
**Status:** Draft

## Overview

Add farmland, commercial real estate, and residential real estate as portfolio asset types using the existing percentage-based entry model. No new entry flow, no dollar values. These types slot into the existing `<select>` alongside Gold, Crypto, and Cash — no symbols, name pre-filled.

## User Flow

1. User clicks "Add Holding"
2. User selects one of the three new real estate types from the asset type picker
3. Name field auto-populates (e.g., "Farmland"); user may edit
4. Symbol field is hidden (no ticker needed)
5. User enters allocation percentage and saves
6. Real estate types appear in the holdings table, both charts, and the new Real Estate summary card

## Wireframes

### Summary Cards Row — Before (4 cards)
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ TOTAL ALLOC  │ │ HOLDINGS     │ │ EQUITIES     │ │ ALTERNATIVES │
│ 82%          │ │ 7            │ │ 40%          │ │ 30%          │
│ Incomplete   │ │ positions    │ │ Stocks/ETFs  │ │ Gold, Crypto │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Summary Cards Row — After (5 cards)
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ TOTAL ALLOC  │ │ HOLDINGS     │ │ EQUITIES     │ │ ALTERNATIVES │
│ 82%          │ │ 7            │ │ 40%          │ │ 20%          │
│ Incomplete   │ │ positions    │ │ Stocks/ETFs  │ │ Gold, Crypto │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
┌──────────────────────┐
│ REAL ESTATE          │
│ 22%                  │
│ Farm 12% · Comm 5% · │
│ Resid 5%             │
└──────────────────────┘
```
At `xl` (1280px+): first 4 cards on row 1, Real Estate card on row 2 (col-xl-3, left-aligned).
At `md` (768px): 2 per row (col-md-6), 3 rows.
At `sm` (375px): stacked 1 per row.

### Asset Type Picker — Add Holding Modal
```
Asset Type  ▼
─────────────────────
  Stock
  ETF
  Mutual Fund
  Crypto (Bitcoin)
  Gold
  Cash
  Savings Account
  Money Market
  ─────────────────   ← visual separator via <optgroup>
  Farmland
  Commercial Real Estate
  Residential Real Estate
  ─────────────────
  Other
```

### Holdings Table Badge
Real estate entries display with a `bg-secondary` badge (same as all other types):
```
│ My Farmland    │ Farmland  │ -  │ 12%  │ -  │ -  │ ✏ 🗑 │
│ Commercial Bldg│ Comm. RE  │ -  │  5%  │ -  │ -  │ ✏ 🗑 │
```
Price and Change columns show `-` (no ticker data — same behavior as Gold/Cash).

## Component Specifications

### Asset Type Picker — New Options

Add three new `<option>` elements inside the existing `<select id="asset-type">`, grouped after Money Market and before Other using an `<optgroup label="Real Estate">`:

| `value` | Display Label |
|---------|---------------|
| `farmland` | Farmland |
| `commercial_real_estate` | Commercial Real Estate |
| `residential_real_estate` | Residential Real Estate |

**Name auto-fill** (same pattern as crypto/gold/cash): when these types are selected, populate `#holding-name` with the default label:
- `farmland` → `"Farmland"`
- `commercial_real_estate` → `"Commercial Real Estate"`
- `residential_real_estate` → `"Residential Real Estate"`

**Symbol field:** hidden for all three (same as crypto/gold/cash — not in `SYMBOL_REQUIRED` array).

### Real Estate Summary Card

New 5th summary metric card. HTML structure matches existing metric cards exactly:

```html
<div class="col-xl-3 col-md-6 mb-3">
  <div class="card metric-card">
    <div class="card-body">
      <h6 class="text-muted">REAL ESTATE</h6>
      <h2 class="mb-0" id="real-estate-pct">0%</h2>
      <small class="text-muted" id="real-estate-breakdown">
        No real estate holdings
      </small>
    </div>
  </div>
</div>
```

When holdings exist, the breakdown subtitle shows each sub-type that has a non-zero allocation:
- **All three present:** `"Farm 12% · Comm 5% · Resid 5%"`
- **Two present:** `"Farm 12% · Resid 10%"`
- **One present:** `"Farmland 22%"`
- **None:** `"No real estate holdings"`

Use `·` (middle dot `\u00B7`) as the separator. Abbreviations:
- farmland → `"Farm"`
- commercial_real_estate → `"Comm"`
- residential_real_estate → `"Resid"`
- When only one type present, use the full label: `"Farmland"`, `"Commercial RE"`, `"Residential RE"`

No border-left variant needed (no semantic state). The card uses the same unstyled `card metric-card` as Holdings Count.

### Alternatives Summary Card — Updated Subtitle

The `<small class="text-muted">` subtitle in the existing Alternatives card remains `"Gold, Crypto"`. Real estate is intentionally excluded — it surfaces in its own card. No change to the Alternatives card computation.

### Chart Colors — Asset Class Chart

Add three new entries to the existing `typeColors` object in `updateAssetClassChart()`:

| Asset Type | Color | Rationale |
|-----------|-------|-----------|
| `farmland` | `#7B9E5A` | Muted sage green — evokes agricultural land; distinct from Bootstrap success green (#198754) and mint (#20c997) |
| `commercial_real_estate` | `#607D8B` | Blue-gray slate — urban, professional; distinct from all existing blues and grays |
| `residential_real_estate` | `#E07B39` | Warm amber — evokes residential warmth; lighter/more golden than gold's orange (#fd7e14) |

These three colors are also visually distinct under deuteranopia simulation (green-blind users see the amber as warm and the slate as cool blue-gray).

### `formatAssetType()` — Display Labels

Add to the existing `labels` map:
- `'farmland'` → `'Farmland'`
- `'commercial_real_estate'` → `'Comm. RE'`
- `'residential_real_estate'` → `'Residential RE'`

### `updateUI()` — Real Estate Calculation

Add alongside existing equities/alternatives calculations:

```javascript
const realEstatePct = (breakdown.farmland || 0)
    + (breakdown.commercial_real_estate || 0)
    + (breakdown.residential_real_estate || 0);
```

Drive `#real-estate-pct` with `realEstatePct.toFixed(1) + '%'` and build the breakdown subtitle string as described in the Real Estate Summary Card spec above.

## Interaction Patterns

- **Selecting a real estate type:** Symbol group hides instantly (same as gold/cash). Name field pre-populates. User can edit name freely.
- **Saving:** Identical flow to any other non-symbol asset type.
- **Charts:** Both doughnut charts update automatically when holdings change — no special behavior for real estate types.
- **Price / Change columns:** Real estate holdings show `–` for price and change (no live price data available). Identical to Gold and Cash behavior.

## Responsive Behavior

| Breakpoint | Summary Row | Modal |
|------------|-------------|-------|
| 375px | 1 card per row (col-md-6 = full-width at xs) | Full-width modal, stacked fields |
| 768px (md) | 2 cards per row | Centered modal |
| 1280px (xl) | 4 cards row 1 + Real Estate card row 2 | Centered modal |

The 5-card layout at xl (4+1 wrap) is intentional and matches Bootstrap's standard grid behavior. No custom CSS required.

## Accessibility Requirements

- Asset type `<optgroup label="Real Estate">` provides keyboard users a clear group structure in the select
- No color-only communication: chart legend always shows label + color swatch
- New summary card uses same `h6 + h2 + small` structure as existing cards — screen readers announce naturally
- `aria-hidden="true"` not needed on summary cards (no decorative icons)

## Backend Notes (for Engineer)

- Three new asset type values must be recognized by the `/api/portfolio` endpoints
- `type_breakdown` response dict should include the new keys when holdings exist
- AI analysis prompt should list real estate types as percentage holdings (same as all other assets)
- No real estate market data, cap rate tracking, or property value fields — percentage only

## Design System References

- Colors: see Chart Colors section above — new values extend the `typeColors` object; not added to `design-system.md` (these are portfolio JS chart colors, not global design tokens)
- Typography: `h6.text-muted` uppercase label + `h2` value + `small.text-muted` subtitle — matches existing metric cards exactly
- Components: `card metric-card` (existing pattern in `dashboard.css`)
- Spacing: `col-xl-3 col-md-6 mb-3` — consistent with all 4 existing summary cards
