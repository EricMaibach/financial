# Alert Severity Design Tokens — CSS Component + Card Header Fix

**Issue:** #256
**Feature:** 9.5 — Alert Severity Design Tokens
**Created:** 2026-03-12
**Status:** Draft

---

## Overview

Extract the three hardcoded alert severity hex values from `settings_alerts.html` into named CSS custom properties, move badge styles into a shared component file, and fix the Smart Market Alerts card header color (currently `bg-danger`, which reads as an error/warning state for a settings panel).

This is a design-system consistency fix — **no new UI, no visual regression**. Badge colors remain identical; only the implementation source changes.

---

## Problem Statement

**Problem 1 — Hardcoded hex values:**
The three severity badge colors (`#6f42c1`, `#fd7e14`, `#dc3545`) are inline styles in `settings_alerts.html`. Any second engineer adding alerts to a new surface will guess or diverge. These must be named tokens.

**Problem 2 — Card header color:**
The Smart Market Alerts settings card uses `bg-danger text-white` (Bootstrap error red). This is a settings panel for a premium feature — it should feel authoritative and brand-adjacent, not broken/alerting.

---

## Token Definitions

### Alert Severity Tokens

| Token | Value | Semantic Meaning |
|-------|-------|-----------------|
| `--alert-l1-color` | `#6f42c1` | L1 — Critical/Priority (purple) |
| `--alert-l2-color` | `#fd7e14` | L2 — Important (orange) |
| `--alert-l3-color` | `#dc3545` | L3 — Standard (red) |

> **Note:** Values are unchanged from the current inline styles. Only the naming changes.

### Card Header Token

| Token | Value | Usage |
|-------|-------|-------|
| `--alert-header-bg` | `var(--brand-indigo-500)` → `#4F46E5` | Smart Market Alerts card header background |

**Rationale for indigo:** Brand indigo (`#4F46E5`) is the "innovation / intelligence" secondary brand color per the design system. Smart Market Alerts is the most AI-forward feature in settings — indigo correctly signals "smart premium feature" without the false-alarm connotation of Bootstrap red. It is clearly distinct from all semantic colors (success, danger, warning, info) and from `bg-danger`.

Text on indigo header: `color: white` — contrast ratio ≈ 8.5:1 (AAA ✓).

---

## File Specification

### New File: `static/css/components/alert-severity.css`

```css
/* ============================================================
   Alert Severity — Design Tokens + Badge Styles
   SignalTrackers Design System
   ============================================================ */

:root {
  /* Severity badge colors — established in Phase 8 */
  --alert-l1-color: #6f42c1;   /* L1 Critical — purple */
  --alert-l2-color: #fd7e14;   /* L2 Important — orange */
  --alert-l3-color: #dc3545;   /* L3 Standard — red */

  /* Smart Market Alerts card header */
  --alert-header-bg: #4F46E5;  /* brand-indigo-500 — premium/AI feature */
}

/* Severity badge base */
.alert-severity-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;   /* space-1 space-3 */
  border-radius: 12px;         /* pill shape */
  font-size: 0.75rem;          /* text-xs */
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: white;
}

.alert-severity-badge--l1 {
  background-color: var(--alert-l1-color);
}

.alert-severity-badge--l2 {
  background-color: var(--alert-l2-color);
}

.alert-severity-badge--l3 {
  background-color: var(--alert-l3-color);
}

/* Smart Market Alerts card header */
.alert-settings-header {
  background-color: var(--alert-header-bg);
  color: white;
}
```

### Changes to `settings_alerts.html`

- Replace inline `style="background-color: #6f42c1; color: white; ..."` badge styles with class `alert-severity-badge alert-severity-badge--l1`
- Replace `#fd7e14` badge styles → `alert-severity-badge alert-severity-badge--l2`
- Replace `#dc3545` badge styles → `alert-severity-badge alert-severity-badge--l3`
- Replace card header class `bg-danger text-white` → `alert-settings-header` (or add the class alongside removal of `bg-danger text-white`)
- Link the new CSS file in the template (or include in the base stylesheet if all pages need it)

---

## Design System Update

**Add to `docs/design-system.md`** under a new "Alert Severity" section within the Badge components or as a standalone "Feature-Specific Tokens" section:

```markdown
### Alert Severity Badges

Used on Smart Market Alerts settings and any future alert-adjacent surface.

| Token | Value | Semantic |
|-------|-------|---------|
| `--alert-l1-color` | `#6f42c1` | L1 Critical — purple |
| `--alert-l2-color` | `#fd7e14` | L2 Important — orange |
| `--alert-l3-color` | `#dc3545` | L3 Standard — red |
| `--alert-header-bg` | `#4F46E5` | Smart Alerts card header (brand-indigo-500) |

File: `static/css/components/alert-severity.css`

Badges use `.alert-severity-badge` base class + modifier `--l1`, `--l2`, `--l3`.
```

---

## Responsive Behavior

No responsive changes needed — badge styles are inline/compact and work identically across all breakpoints.

---

## Accessibility Requirements

- White text on `--alert-l1-color` (#6f42c1, purple): contrast ≈ 4.7:1 — AA ✓
- White text on `--alert-l2-color` (#fd7e14, orange): contrast ≈ 2.9:1 — **fails AA for text**

> **Important:** L2 orange badge has a known contrast issue. The current inline implementation has the same problem — this spec does not introduce a regression. However, the engineer should note this in implementation. A future fix would be: use dark text (`neutral-800`) on a light orange background (`warning-100`) instead of white text on orange. **Defer the contrast fix to a separate issue** — this feature's scope is token extraction only, not redesign.

- White text on `--alert-l3-color` (#dc3545, red): contrast ≈ 4.6:1 — AA ✓
- White text on `--alert-header-bg` (#4F46E5, indigo): contrast ≈ 8.5:1 — AAA ✓

---

## Wireframes

No layout changes. The only visible change is the card header color:

**Before (settings_alerts.html card header):**
```
┌─────────────────────────────────────┐
│  🔔 Smart Market Alerts  [bg-danger]│ ← Bootstrap error red — reads as broken
└─────────────────────────────────────┘
```

**After:**
```
┌─────────────────────────────────────┐
│  🔔 Smart Market Alerts [brand-ind]  │ ← Indigo — premium feature, AI-forward
└─────────────────────────────────────┘
```

Severity badges: identical appearance (same colors, same shape) — zero visual regression.

---

## Implementation Scope

- **1 new file:** `static/css/components/alert-severity.css`
- **1 file modified:** `signaltrackers/templates/settings_alerts.html` (replace inline styles + card header class)
- **1 file modified:** `docs/design-system.md` (add alert severity token documentation)
- **No Python changes**
- **No HTML structure changes** (only class/style attribute changes)

Engineer estimate: ~1 hour as noted in the feature issue.
