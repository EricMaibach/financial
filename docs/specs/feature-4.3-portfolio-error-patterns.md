# Feature 4.3: Portfolio Page Error Patterns

**Issue:** #125
**Created:** 2026-02-24
**Status:** Draft

---

## Overview

The portfolio page currently uses native browser `alert()` dialogs for all 6 validation and API error states. These OS-level popups are visually inconsistent, blocking, and mobile-disruptive. This spec replaces all 6 callsites with design-system-consistent patterns that are non-blocking, contextual, and accessible.

### Two Error Pattern Types

| Pattern | When to Use | Where it Appears |
|---------|-------------|-----------------|
| **Inline field error** | Form validation failures (missing/invalid input) | Below the invalid field |
| **Modal error banner** | API/network failures (server errors, network down) | Top of the modal, above the form |

---

## Pattern 1: Inline Field Error

Used for the 2 form validation callsites:
- "Please fill in all required fields"
- "Symbol is required for this asset type"

### Wireframe

```
┌─────────────────────────────────────────────────────┐
│ Add Holding                                    [×]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Asset Type *                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │ Stocks                               ▼      │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Symbol *                                           │
│  ┌─────────────────────────────────────────────┐   │  ← red border (focus/error state)
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│  ⚠ Symbol is required for this asset type          │  ← inline error (new)
│                                                     │
│  Quantity *                                         │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│  ⚠ Please fill in all required fields               │  ← inline error (new)
│                                                     │
│  [Cancel]                         [Save Holding]   │
└─────────────────────────────────────────────────────┘
```

### Inline Error Specifications

**Error text element:**
- Tag: `<p>` or `<span>` below the relevant `<input>` or `<select>`
- Class: `.form-error-message` (consistent with auth forms)
- Color: `danger-600` (#DC2626)
- Font: `text-sm` (14px), weight 400
- Icon: `⚠` warning symbol prefix (plain unicode or SVG icon), `aria-hidden="true"`, followed by space and error text
- Margin-top: `space-1` (4px) — tight to the field
- Display: hidden by default (`display: none`); visible when field fails validation

**Invalid field highlight:**
- Input border: `danger-600` (#DC2626), 1px → 2px on error
- No background color change (border is sufficient signal)
- Error persists until user corrects the field and triggers revalidation (or successful save)

**Multiple field errors:**
- Each field shows its own inline error independently
- There is NO summary banner for validation errors (inline is sufficient)
- Error for "Please fill in all required fields" maps to the first empty required field that was left blank — error text appears below the first invalid field detected, or the submit button if multiple fields are empty

**Accessibility:**
- Each error `<span>` linked to its field via `aria-describedby`
- Example: `<input id="symbol-input" aria-describedby="symbol-error" aria-invalid="true">`
- Example: `<span id="symbol-error" class="form-error-message" role="alert">⚠ Symbol is required for this asset type</span>`
- `role="alert"` causes screen readers to announce the error immediately on appearance

---

## Pattern 2: Modal Error Banner

Used for the 4 API/network failure callsites:
- "Error: [message]" (save API error)
- "Error: [message]" (delete API error)
- "Failed to save holding"
- "Failed to delete holding"

### Wireframe

```
┌─────────────────────────────────────────────────────┐
│ Add Holding                                    [×]  │
├─────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────┐   │  ← error banner (new)
│ │ ⚠  Could not save holding — please try again  │   │
│ └───────────────────────────────────────────────┘   │
│                                                     │
│  Asset Type *                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │ Stocks                               ▼      │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [Cancel]                         [Save Holding]   │
└─────────────────────────────────────────────────────┘
```

### Modal Error Banner Specifications

**Container:**
- Position: First element inside `.modal-body`, above all form fields
- Visibility: Hidden by default; shown on API/network error
- Margin-bottom: `space-4` (16px) — separates banner from form fields
- Display: Removed from DOM / `display: none` when not shown (avoids empty space)

**Banner appearance:**
- Background: `danger-100` (#FEE2E2) — light red, consistent with semantic danger-100 token
- Border: 1px solid `danger-300` (#FCA5A5) — slightly darker border for definition
- Border-radius: 8px (consistent with performance banner in chatbot spec)
- Padding: `space-3` vertical (12px), `space-4` horizontal (16px)
- Layout: Flexbox row, `align-items: flex-start`

**Banner contents:**
- Warning icon (⚠ or filled warning SVG): `danger-600` (#DC2626), 18px, `aria-hidden="true"`, margin-right `space-2` (8px), top-aligned
- Error message text: `danger-700` (#B91C1C), `text-sm` (14px), line-height 1.5
- No dismiss (×) button on modal error banners — banners auto-clear on next successful save

**Contrast validation:**
- danger-700 on danger-100: passes 4.5:1 ✅

**Error message copy:**
| Callsite | Displayed Message |
|----------|------------------|
| Save API error | "Could not save holding — please try again" |
| Delete API error | "Could not delete holding — please try again" |
| Network failure (save) | "Could not save holding — check your connection" |
| Network failure (delete) | "Could not delete holding — check your connection" |

**Rationale:** Messages are human-readable and actionable. Raw "Error: [message]" strings from the backend are not user-appropriate. Messages never expose technical error details.

**Accessibility:**
- Banner element: `role="alert"` (triggers immediate screen reader announcement)
- Example: `<div class="modal-error-banner" role="alert" hidden>...</div>`
- When displayed, screen readers announce: "Could not save holding — please try again"

---

## Pattern Comparison (Old vs New)

| Callsite | Old (alert) | New Pattern |
|----------|------------|-------------|
| Validation: required fields | `alert("Please fill in all required fields")` | Inline error below first empty required field |
| Validation: symbol required | `alert("Symbol is required for this asset type")` | Inline error below symbol input |
| Save API error | `alert("Error: " + message)` | Modal error banner: "Could not save holding" |
| Delete API error | `alert("Error: " + message)` | Modal error banner: "Could not delete holding" |
| Save network failure | `alert("Failed to save holding")` | Modal error banner: "Could not save holding — check your connection" |
| Delete network failure | `alert("Failed to delete holding")` | Modal error banner: "Could not delete holding — check your connection" |

---

## Error State Behavior

### Inline Validation

- **When triggered:** On form submit attempt (not on every keystroke)
- **When cleared:** When the field value changes AND is now valid, OR on successful save
- **Multiple errors at once:** Each field shows its own error simultaneously
- **Re-validate on change:** After a failed submit, re-validate each field as user types (so errors clear as they're fixed)

### API Error Banner

- **When triggered:** On fetch/XHR failure or non-2xx response from save/delete endpoint
- **When cleared:** Automatically removed when user successfully saves/deletes, OR when user manually closes the modal
- **One banner per modal:** Only one banner shown at a time; new errors replace previous banner text
- **Does not block form:** User can still edit fields and retry while banner is visible

---

## Component HTML Pattern

### Inline Field Error

```html
<!-- Example: Symbol field with error state -->
<div class="mb-3">
  <label for="symbol-input" class="form-label">Symbol *</label>
  <input
    type="text"
    id="symbol-input"
    class="form-control form-control--error"
    aria-describedby="symbol-error"
    aria-invalid="true">
  <span
    id="symbol-error"
    class="form-error-message"
    role="alert">
    <span aria-hidden="true">⚠ </span>Symbol is required for this asset type
  </span>
</div>
```

### Modal Error Banner

```html
<!-- Inside .modal-body, first child -->
<div
  class="modal-error-banner"
  role="alert"
  hidden>
  <svg class="modal-error-icon" aria-hidden="true"><!-- warning icon --></svg>
  <p class="modal-error-text">Could not save holding — please try again</p>
</div>
```

---

## CSS Tokens (Reference)

```
Inline error text:    danger-600 (#DC2626), text-sm (14px)
Invalid field border: danger-600 (#DC2626), 2px
Banner background:    danger-100 (#FEE2E2)
Banner border:        danger-300 (#FCA5A5)
Banner text:          danger-700 (#B91C1C)
Banner icon:          danger-600 (#DC2626)
```

---

## Responsive Behavior

Both patterns work within the Bootstrap modal. No special responsive behavior needed:

- **Mobile:** Modal is full-width; both inline errors and banner display within the modal scroll area
- **Tablet/Desktop:** Modal has max-width (Bootstrap default); patterns scale naturally
- Error text wraps gracefully at narrow widths (no fixed widths on error elements)
- Touch-friendly: No extra interaction required — errors are visible without tapping

---

## Accessibility Requirements

- Color contrast: danger-700 on danger-100 ≥ 4.5:1 ✅
- Color contrast: danger-600 on white (inline error) ≥ 4.5:1 ✅
- Never color alone: Warning icon (⚠) accompanies all error text
- Screen reader: `role="alert"` on all error elements for immediate announcement
- `aria-invalid="true"` on fields with inline errors
- `aria-describedby` links each field to its error element

---

## Design System References

- Colors: `danger-600`, `danger-700`, `danger-100`, `danger-300` — see design-system.md Color System
- Typography: `text-sm` (14px) — see design-system.md Typography Scale
- Spacing: `space-1` (4px), `space-2` (8px), `space-3` (12px), `space-4` (16px) — see design-system.md Spacing
- Form accessibility patterns: WCAG 2.1 AA — see design-system.md Accessibility Standards
- Reference pattern: Auth form inline validation (existing, same pattern to reuse)
- Reference pattern: Chatbot error messages (existing in-component styling for API errors)
