# Conditions Strip Component — Quadrant Headline on Every Page

**Issue:** #322
**Feature:** 11.1 — Conditions Strip Component
**Created:** 2026-03-17
**Status:** Draft

---

## Overview

A reusable conditions strip component that replaces the current regime strip (`_regime_strip.html`) on every page. The quadrant is the headline with Liquidity, Risk, and Policy as supporting context. On the Crypto page, Liquidity leads instead of the quadrant.

**Replaces:** `_regime_strip.html` (current regime strip showing Bull/Bear/Neutral/Recession Watch)

---

## Design

### Desktop (768px+)

The strip displays all four dimensions inline in a single horizontal bar:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ● GOLDILOCKS     Liquidity: Expanding ↑ │ Risk: Calm │ Policy: Easing ↑ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Layout:**
- Full-width bar, same position as current regime strip (below navbar, above page content)
- Left: quadrant dot (colored) + quadrant name (uppercase, bold)
- Right: three supporting dimensions separated by `│` dividers
- Direction arrows (↑ / ↓ / →) shown for Liquidity and Policy when direction data is available
- Single line, no wrapping

### Crypto Page — Desktop (768px+)

Liquidity leads instead of the quadrant, because Bitcoin correlates with M2 (0.94), not growth/inflation:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ● LIQUIDITY: EXPANDING ↑     Goldilocks │ Risk: Calm │ Policy: Easing ↑ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Differences from standard strip:**
- Dot color uses Liquidity state color (not quadrant color)
- Lead label is "LIQUIDITY: [STATE]" instead of quadrant name
- Quadrant appears as a secondary item in the supporting dimensions list

### Mobile (<768px)

Collapsed by default, showing only the headline:

```
┌──────────────────────────────────────┐
│  ● GOLDILOCKS                     ▾  │
└──────────────────────────────────────┘
```

Tap ▾ to expand into a vertical list:

```
┌──────────────────────────────────────┐
│  ● GOLDILOCKS                     ▴  │
├──────────────────────────────────────┤
│  Liquidity    Expanding           ↑  │
│  Risk         Calm                   │
│  Policy       Easing              ↑  │
└──────────────────────────────────────┘
```

**Crypto page mobile:** Same expand pattern, but headline reads `● LIQUIDITY: EXPANDING ↑` and the expanded list shows Quadrant (Goldilocks) instead of Liquidity.

### Tablet (768px–1023px)

Same as desktop layout. The strip content is compact enough to fit at 768px.

---

## Quadrant Colors

| Quadrant | Dot + Text Color | CSS Custom Property |
|----------|-----------------|---------------------|
| **Goldilocks** | `#0D9488` (teal-600) | `--quadrant-goldilocks` |
| **Reflation** | `#1E40AF` (blue-800) | `--quadrant-reflation` |
| **Deflation Risk** | `#CA8A04` (amber-600) | `--quadrant-deflation` |
| **Stagflation** | `#DC2626` (red-600) | `--quadrant-stagflation` |

These map intentionally to the existing regime colors (Bull=green, Neutral=blue, Bear=amber, Recession=red) to ease the visual transition.

### Liquidity State Colors (Crypto Page Dot)

| State | Color |
|-------|-------|
| Strongly Expanding / Expanding | `#2563EB` (blue-600) |
| Neutral | `#64748B` (slate-500) |
| Contracting / Strongly Contracting | `#D97706` (amber-600) |

---

## Component Structure

### Template: `_conditions_strip.html`

Replaces `_regime_strip.html`. Included on every page via the same `{% include %}` pattern.

### Data Source

Reads from `market_conditions_cache.json` (injected via context processor, same pattern as current `macro_regime` injection in `dashboard.py`).

**Required fields from cache:**
- `dimensions.quadrant.state` — Goldilocks / Reflation / Stagflation / Deflation Risk
- `dimensions.liquidity.state` — Expanding / Neutral / Contracting / etc.
- `dimensions.risk.state` — Calm / Normal / Elevated / Stressed
- `dimensions.policy.stance` — Accommodative / Neutral / Restrictive
- `dimensions.policy.direction` — Easing / Paused / Tightening

### Display Labels

The strip uses simplified display labels for compactness:

| Dimension | Cache Value | Strip Display |
|-----------|------------|---------------|
| Liquidity | Strongly Expanding | Expanding ↑↑ |
| Liquidity | Expanding | Expanding ↑ |
| Liquidity | Neutral | Neutral |
| Liquidity | Contracting | Contracting ↓ |
| Liquidity | Strongly Contracting | Contracting ↓↓ |
| Risk | Calm | Calm |
| Risk | Normal | Normal |
| Risk | Elevated | Elevated |
| Risk | Stressed | Stressed |
| Policy | (any stance) + Easing | Easing ↑ |
| Policy | (any stance) + Paused | Paused |
| Policy | (any stance) + Tightening | Tightening ↓ |

**Note:** Policy shows direction (Easing/Paused/Tightening), not stance (Accommodative/Neutral/Restrictive), in the strip for brevity. The full stance + direction is shown on the homepage dimension card.

### Page-Level Configuration

Each page sets a `page_category` variable (existing pattern). The Crypto page additionally sets a flag that tells the strip to use the Liquidity-leads variant:

```jinja2
{% set page_category = 'Crypto' %}
{% set conditions_strip_liquidity_leads = true %}
{% include '_conditions_strip.html' %}
```

All other pages:
```jinja2
{% set page_category = 'Credit' %}
{% include '_conditions_strip.html' %}
```

---

## Accessibility

- `role="complementary"` with `aria-label="Market conditions for this page"` (same as current strip)
- Quadrant dot: `aria-hidden="true"` (decorative — color is not the only indicator)
- Quadrant name in text is always present (never rely on dot color alone)
- Mobile expand: `aria-expanded="false"` on toggle, `aria-controls` pointing to expand panel
- `aria-live="polite"` on the quadrant state for screen reader updates when data changes
- AAA contrast: all text colors meet 7:1 ratio on strip background
- Touch target: mobile toggle row is 44px min-height

---

## Graceful Degradation

If `market_conditions_cache.json` is missing or stale (>48 hours):
- Strip renders with neutral styling: `● CONDITIONS UNAVAILABLE` in `neutral-500`
- No supporting dimensions shown
- No expand on mobile (nothing to expand)
- Same pattern as current regime strip fallback

---

## CSS

**New file:** `static/css/components/conditions-strip.css`

**Key styles:**
- `.conditions-strip` — Full-width bar, `neutral-100` background, 1px bottom border `neutral-200`
- `.conditions-strip__quadrant` — Flex row, dot + name
- `.conditions-strip__dot` — 8px circle, quadrant color, `border-radius: 50%`
- `.conditions-strip__name` — `text-sm`, `font-weight: 700`, `text-transform: uppercase`, `letter-spacing: 0.05em`
- `.conditions-strip__dimensions` — Flex row, gap `space-3`, `text-sm`, `neutral-600`
- `.conditions-strip__separator` — 1px vertical line, `neutral-300`, 16px height
- `.conditions-strip__toggle` — Mobile only, 44px height, full-width tap target
- `.conditions-strip__expand` — Mobile only, max-height transition (screen reader safe)

**Quadrant color classes:**
- `.conditions-strip--goldilocks` — dot and name use `--quadrant-goldilocks`
- `.conditions-strip--reflation` — dot and name use `--quadrant-reflation`
- `.conditions-strip--deflation-risk` — dot and name use `--quadrant-deflation`
- `.conditions-strip--stagflation` — dot and name use `--quadrant-stagflation`

---

## Pages That Include the Strip

All pages that currently include `_regime_strip.html`:
- Homepage (`index.html`) — standard quadrant-leads variant
- Credit (`credit.html`)
- Rates (`rates.html`)
- Equities (`equity.html`)
- Dollar (`dollar.html`)
- Crypto (`crypto.html`) — **Liquidity-leads variant**
- Safe Havens (`safe_havens.html`)
- Property (`property.html`)
- Explorer (`explorer.html`)
- News (`news.html`)
- Portfolio (`portfolio.html`)

---

## Migration Notes

- `_regime_strip.html` is deleted after all pages switch to `_conditions_strip.html`
- The `category_regime_context` dict in `regime_config.py` is no longer used by the strip (context sentences move to category pages — see Feature #324)
- The `macro_regime` context processor continues to run in parallel during migration (Feature #326 removes it)
