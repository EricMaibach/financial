# Asset Detail Page Header — Shared Component Spec

**Issue:** #207
**Feature:** 8.1 — Asset Detail Page Header Shared Component Refactor
**Created:** 2026-03-06
**Status:** Draft

---

## Overview

Six asset detail page templates (credit, equity, rates, dollar, crypto, safe_havens) each define an identical page-header CSS block. The only difference between them is the class name prefix (`.credit-header`, `.equity-header`, etc.). This creates guaranteed design drift as pages evolve independently — the Credit page is already more evolved than the others (regime interpretation block, AI briefing) and the rest will follow.

This spec defines a single shared `.asset-page-header` component to replace all six duplicate blocks. The component uses a CSS custom property (`--category-color`) for per-page accent color so the Engineer can set the correct brand color per template without forking the component rules.

---

## Problem Analysis

### Current Duplication (6 Identical Blocks)

All six templates define the following CSS identically, differing only in the class prefix:

```css
/* Current per-page pattern — repeated 6× with different prefix */
.{page}-header {
    padding: var(--space-4);           /* mobile */
    background: white;
    border-bottom: 1px solid var(--neutral-200);
}
.{page}-header__title {
    font-size: var(--text-2xl);        /* mobile */
    font-weight: 700;
    color: var(--neutral-800);
    margin: 0 0 var(--space-2) 0;
    display: flex;
    align-items: center;
    gap: var(--space-2);
}
.{page}-header__description {
    font-size: var(--text-sm);
    color: var(--neutral-600);
    margin: 0 0 var(--space-2) 0;
}
.{page}-header__updated {
    font-size: var(--text-sm);
    color: var(--neutral-500);
    margin: 0;
}
/* Tablet breakpoint */
@media (min-width: 768px) {
    .{page}-header          { padding: var(--space-6); }
    .{page}-header__title   { font-size: var(--text-3xl); }
}
```

### Current Category Color State

Only the Credit page currently defines a `--category-credit` CSS custom property. The other five pages use semantic colors from Bootstrap/the global token set but have no per-page category color token. The shared component introduces a standard `--category-color` pattern for all six pages.

| Page | Current Accent Color | Proposed `--category-color` Value |
|------|---------------------|----------------------------------|
| Credit | `--danger-600` (#dc3545) | `#dc3545` (danger-red) |
| Equity | `--brand-blue-500` (#0d6efd) | `#0d6efd` (brand blue) |
| Rates | `--brand-blue-500` (#0d6efd) | `#0d6efd` (brand blue, same as equity — rates and equity both use blue in current nav/icons) |
| Dollar | `--info-600` (#0dcaf0) | `#0dcaf0` (teal-info) |
| Crypto | `--warning-600` (#ffc107) | `#ffc107` (warning amber — crypto uses orange/amber indicators) |
| Safe Havens | `--success-600` (#198754) | `#198754` (success green — gold/safe havens use green) |

> **Note to Engineer:** These assignments follow the existing color usage in each template's icons and accent elements. Verify against actual `<i class="bi bi-... text-*">` color in each template header. If a page currently has no clear category accent, default to `--brand-blue-500` and note it in the PR.

---

## Shared Component Spec

### File Location

```
signaltrackers/static/css/components/asset-page-header.css
```

### BEM Class Names

| Class | Role |
|-------|------|
| `.asset-page-header` | Outer `<header>` wrapper |
| `.asset-page-header__title` | `<h1>` with icon and page name |
| `.asset-page-header__description` | Brief subtitle describing the page's data focus |
| `.asset-page-header__updated` | "Last Updated: …" timestamp line |

### CSS Specification

```css
/* ============================================================
   Asset Page Header — Shared Component
   Usage: <header class="asset-page-header"> on all 6 asset detail pages.
   Set --category-color on the page's :root or .asset-page-header
   to apply the correct per-page accent.
   ============================================================ */

.asset-page-header {
    padding: var(--space-4);
    background: white;
    border-bottom: 1px solid var(--neutral-200);
}

.asset-page-header__title {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--neutral-800);
    margin: 0 0 var(--space-2) 0;
    display: flex;
    align-items: center;
    gap: var(--space-2);
}

.asset-page-header__description {
    font-size: var(--text-sm);
    color: var(--neutral-600);
    margin: 0 0 var(--space-2) 0;
}

.asset-page-header__updated {
    font-size: var(--text-sm);
    color: var(--neutral-500);
    margin: 0;
}

/* Tablet and above */
@media (min-width: 768px) {
    .asset-page-header {
        padding: var(--space-6);
    }

    .asset-page-header__title {
        font-size: var(--text-3xl);
    }
}
```

### CSS Custom Property: `--category-color`

Each page sets `--category-color` in its own `:root` block (or inline on `.asset-page-header`). The shared component does **not** define a default for `--category-color` — it is a per-page override used by icon coloring, border accents, and the interpretation block. This follows the existing pattern established by `--category-credit` on the Credit page.

**Setting pattern (per template):**

```html
<style>
    :root {
        /* ... existing tokens ... */
        --category-color: #dc3545;  /* Set to the page's accent color */
    }
</style>
```

### HTML Template Pattern

```html
<header class="asset-page-header">
    <h1 class="asset-page-header__title">
        <i class="bi bi-{page-icon}" style="color: var(--category-color);"></i>
        {Page Title}
    </h1>
    <p class="asset-page-header__description">{Page subtitle}</p>
    <p class="asset-page-header__updated">Last Updated: <span id="last-updated-time">Loading...</span></p>
</header>
```

> **Note on icon coloring:** Currently each page uses Bootstrap utility classes like `text-danger`, `text-primary` for the header icon. After this refactor, icons in the header should use `style="color: var(--category-color);"` so the color derives from the token, not a hardcoded Bootstrap class. This is a minor template change that eliminates one more coupling point.

---

## Per-Page Migration Reference

| Template | Old Class | New Class | `--category-color` | Icon |
|----------|-----------|-----------|-------------------|------|
| `credit.html` | `.credit-header` | `.asset-page-header` | `#dc3545` | `bi-credit-card` |
| `equity.html` | `.equity-header` | `.asset-page-header` | `#0d6efd` | `bi-bar-chart-line` |
| `rates.html` | `.rates-header` | `.asset-page-header` | `#0d6efd` | *(verify current icon)* |
| `dollar.html` | `.dollar-header` | `.asset-page-header` | `#0dcaf0` | *(verify current icon)* |
| `crypto.html` | `.crypto-header` | `.asset-page-header` | `#ffc107` | *(verify current icon)* |
| `safe_havens.html` | `.safe-havens-header` | `.asset-page-header` | `#198754` | *(verify current icon)* |

---

## Design Decisions

### Why a CSS variable for category color, not a BEM modifier class?

A modifier class (`.asset-page-header--credit`) would require the Engineer to maintain a modifier class per page in the shared CSS file — recreating the same duplication problem at a different layer. The CSS custom property approach is simpler: the component defines the structure once; each page sets its own token. This also makes future per-page changes (e.g., a different shade for credit) a one-line change in the template, not a new modifier class.

### Why not a Jinja2 macro?

A Jinja macro is appropriate for repeated HTML structure with variable content. The header HTML is already short and clear — each template's title, description, and icon differ in ways that would make the macro call nearly as verbose as the raw HTML. The CSS consolidation is the real value; the HTML remains direct in each template.

### Zero visual regression requirement

This refactor is pure CSS class renaming. Users should see no visual change on any page. The acceptance test is visual equivalence across all 6 pages at 375px, 768px, and 1280px.

---

## Implementation Steps (for Engineer)

1. Create `signaltrackers/static/css/components/asset-page-header.css` with the CSS above
2. Add `--category-color` to `:root` in each of the 6 templates
3. In each template, replace `.{page}-header` references with `.asset-page-header` (HTML class attributes and any remaining CSS)
4. Remove the 6 duplicate per-page header CSS blocks from each template's `<style>` tag
5. Update icon color references from `text-danger` / `text-primary` etc. to `style="color: var(--category-color);"`
6. Link the new CSS file in each template (or via `base.html` if the component is always loaded)
7. Add the `asset-page-header.css` to the components directory (already the pattern for other shared components)
8. Remove the credit-specific `--category-credit` reference **only** where it was used solely for header styling; retain it everywhere it's used for non-header elements (interpretation block border, chart accents, etc.)

---

## Design System Documentation Entry

The following section must be added to `docs/design-system.md` under **Component Library**, after the existing Cards section:

---

**Asset Detail Page Header**

Canonical header for all 6 asset detail pages (Credit, Equity, Rates, Dollar, Crypto, Safe Havens).

```
File: static/css/components/asset-page-header.css

HTML:
<header class="asset-page-header">
  <h1 class="asset-page-header__title">
    <i class="bi bi-{icon}" style="color: var(--category-color);"></i>
    {Page Name}
  </h1>
  <p class="asset-page-header__description">{Subtitle}</p>
  <p class="asset-page-header__updated">Last Updated: <span id="last-updated-time">…</span></p>
</header>

Per-page setup: Each template sets --category-color in its :root block.

Mobile (default):  padding space-4; title text-2xl (24px)
Tablet+ (768px+):  padding space-6; title text-3xl (30px)
```

| Page | `--category-color` |
|------|--------------------|
| Credit | `#dc3545` (danger-red) |
| Equity | `#0d6efd` (brand-blue) |
| Rates | `#0d6efd` (brand-blue) |
| Dollar | `#0dcaf0` (teal-info) |
| Crypto | `#ffc107` (warning-amber) |
| Safe Havens | `#198754` (success-green) |

---

## Accessibility

- The `<header>` element is a landmark region — screen readers will announce "banner" or "header" when users navigate to it
- Title text meets WCAG AA contrast at all sizes (`--neutral-800` on white)
- Icon is decorative (conveys no unique information beyond the text title) — add `aria-hidden="true"` to the `<i>` element

---

## Design Review Criteria

When Engineer submits this for design review, provide screenshots at 375px, 768px, and 1280px for at least 2 pages (e.g., Credit and Equity) showing the header area. Visual equivalence to the current implementation is the pass criterion — no new visual design is expected.
