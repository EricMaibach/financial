# Homepage Section Quick-Nav Design Spec

**Issue:** #171
**Created:** 2026-03-04
**Status:** Draft

## Overview

The homepage has grown to 9 named sections across ~1200px+ of content. Returning users — our most valuable cohort — scroll linearly past regime/recession panels to reach the live signal layer they actually came for. This feature adds a context-aware quick-nav:

- **Mobile (< 768px):** Floating action button (bottom-right) that opens a section list on tap
- **Desktop (768px+):** Sticky horizontal pill row below the top navbar with active-section tracking

Both patterns allow any section to be reached in ≤1 tap/click from anywhere on the page.

---

## Section Inventory

The quick-nav covers all 9 current major sections (in scroll order after US-183.1 reorder):

| # | Display Label | Current Section ID | Status |
|---|---------------|-------------------|--------|
| 1 | Regime | `macro-regime-section` | ✅ Exists |
| 2 | Recession | `recession-panel-section` | ✅ Exists |
| 3 | Implications | `regime-implications` | ✅ Exists |
| 4 | Sectors | `sector-tone-section` | ✅ Exists |
| 5 | Markets | `market-conditions` | ✅ Exists |
| 6 | Briefing | *(no section-level ID)* | ⚠️ Engineer must add `id="briefing-section"` to `<section class="hero-briefing">` |
| 7 | Movers | *(no section-level ID)* | ⚠️ Engineer must add `id="movers-section"` to `<section class="whats-moving-section">` |
| 8 | Signals | *(no section-level ID)* | ⚠️ Engineer must add `id="signals-section"` to `<section class="market-signals-section">` |
| 9 | Prediction | *(no section-level ID)* | ⚠️ Engineer must add `id="prediction-section"` to `<section class="prediction-markets-section">` |

> **Note to Engineer:** The issue description states "section IDs already exist" but 4 sections are missing IDs at the `<section>` element level. Please add the IDs listed above — this is the only template change needed beyond the nav components themselves.

---

## User Flows

### Mobile Flow
1. User opens homepage; FAB visible at bottom-right (always present while scrolling)
2. User taps FAB
3. Section list bottom sheet slides up (smooth, 250ms ease-out)
4. User taps a section name (44px min-height tap targets)
5. Bottom sheet closes + page smooth-scrolls to target section
6. FAB remains visible for subsequent jumps

### Desktop Flow
1. User opens homepage; sticky pill row renders below navbar
2. As user scrolls, active pill updates to reflect the section nearest top of viewport
3. User clicks any pill → smooth scroll to that section
4. Active pill updates immediately on click; also tracks natural scrolling

---

## Wireframes

### Mobile: Floating Action Button (375px)

```
┌─────────────────────────┐
│ [Regime section content]│
│                         │
│                         │
│                         │
│                         │
│              ┌──────┐   │
│              │ ≡ §  │   │  ← FAB: 48×48px circle, bottom:80px, right:16px
│              └──────┘   │
└─────────────────────────┘
```

### Mobile: Bottom Sheet (open state, 375px)

```
┌─────────────────────────┐
│░░░░ backdrop ░░░░░░░░░░░│  ← rgba(0,0,0,0.4)
│░░░░░░░░░░░░░░░░░░░░░░░░░│
├─────────────────────────┤  ← 12px border-radius top corners
│ ── Jump to Section  ×   │  ← handle bar + title + close button
├─────────────────────────┤
│ ● Regime                │  ← 48px min-height, left-border active indicator
│   Recession             │
│   Implications          │
│   Sectors               │
│   Markets               │
│   Briefing              │
│   Movers                │
│   Signals               │
│   Prediction            │
└─────────────────────────┘
```

### Desktop: Sticky Pill Row (768px+)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Top Navbar — 64px]                                                  │
├──────────────────────────────────────────────────────────────────────┤
│  Regime │ Recession │ Implications │ Sectors │ [Markets] │ Briefing… │  ← sticky strip, 48px height
├──────────────────────────────────────────────────────────────────────┤
│  [Homepage content scrolls below]                                     │
└──────────────────────────────────────────────────────────────────────┘
```
*Active pill shown with filled background. Strip scrolls horizontally on overflow (tablet).*

---

## Component Specifications

### A. Desktop Sticky Strip (`.section-quick-nav`)

**Container:**
```
Position: sticky
Top: 64px  (navbar height)
Z-index: 100  (above page content, below chatbot/modals at 1040+)
Background: white
Border-bottom: 1px solid var(--neutral-200)
Box-shadow: 0 2px 4px rgba(0,0,0,0.06)
Height: 48px
Overflow-x: auto
Scrollbar-width: none  (hidden scrollbar, touch-scrollable on small tablets)
```

**Inner layout:**
```
Display: flex
Align-items: center
Padding: var(--space-2) var(--space-4)  (8px 16px)
Gap: var(--space-2)  (8px)
White-space: nowrap
```

**Individual Pill (`.section-quick-nav__pill`):**
```
Padding: var(--space-1) var(--space-3)  (4px 12px)
Border-radius: 20px  (full pill shape)
Font-size: var(--text-sm)  (14px)
Font-weight: 500
Min-height: 36px
Cursor: pointer
Transition: all 150ms ease-out

Default state:
  Background: var(--neutral-100)
  Color: var(--neutral-600)

Hover state:
  Background: var(--neutral-200)
  Color: var(--neutral-700)

Active state (.is-active):
  Background: var(--brand-blue-100)
  Color: var(--brand-blue-500)
  Font-weight: 600

Focus:
  Outline: 2px solid var(--brand-blue-500)
  Outline-offset: 2px
```

### B. Mobile FAB (`.section-quick-nav-fab`)

```
Position: fixed
Bottom: 80px
Right: var(--space-4)  (16px)
Z-index: 200  (above sticky strip if visible; strip is hidden on mobile anyway)
Width: 48px
Height: 48px
Border-radius: 50%
Background: white
Border: 1.5px solid var(--brand-blue-500)
Color: var(--brand-blue-500)
Box-shadow: 0 4px 12px rgba(0,0,0,0.15)
Cursor: pointer
Transition: box-shadow 150ms ease-out

Hover/focus:
  Box-shadow: 0 6px 16px rgba(0,0,0,0.2)
  Background: var(--brand-blue-100)

Active:
  Transform: scale(0.96)

Icon: bi-list-ul (Bootstrap Icons), 20px
```

> **Safe area:** Engineer should apply `bottom: max(80px, calc(16px + env(safe-area-inset-bottom)))` to handle iOS home bar environments.

### C. Mobile Bottom Sheet (`.section-quick-nav-sheet`)

**Backdrop:**
```
Position: fixed, inset: 0
Background: rgba(0, 0, 0, 0.4)
Z-index: 300
Transition: opacity 250ms ease-out
```

**Sheet panel:**
```
Position: fixed
Bottom: 0
Left: 0, Right: 0
Max-height: 65vh
Border-radius: 12px 12px 0 0
Background: white
Z-index: 301
Transition: transform 250ms ease-out
Transform: translateY(100%) → translateY(0) on open
```

**Sheet header:**
```
Display: flex
Align-items: center
Justify-content: space-between
Padding: var(--space-4)
Border-bottom: 1px solid var(--neutral-200)
```

Handle bar (decorative):
```
Width: 40px, Height: 4px
Background: var(--neutral-300)
Border-radius: 2px
Margin: var(--space-2) auto var(--space-3)
```

Title:
```
Font-size: var(--text-base), Font-weight: 600, Color: var(--neutral-700)
Text: "Jump to Section"
```

Close button (×):
```
Min-height: 44px, Min-width: 44px
Background: transparent, Border: none
Color: var(--neutral-500)
Font-size: var(--text-xl)
```

**Section list:**
```
Overflow-y: auto
Padding: var(--space-2) 0
```

List item (`.section-quick-nav-sheet__item`):
```
Display: flex
Align-items: center
Min-height: 48px
Padding: var(--space-3) var(--space-5)  (12px 20px)
Font-size: var(--text-base)
Color: var(--neutral-700)
Background: transparent
Border: none
Width: 100%
Text-align: left
Transition: background 150ms ease-out
Cursor: pointer

Hover / focus:
  Background: var(--neutral-100)

Active section (.is-active):
  Color: var(--brand-blue-500)
  Font-weight: 600
  Border-left: 3px solid var(--brand-blue-500)
  Padding-left: calc(var(--space-5) - 3px)  (compensate for border)
```

---

## Interaction Patterns

### Scroll-to-Section Behavior
- Smooth scroll: `behavior: 'smooth'` (native CSS `scroll-behavior: smooth` on `html`)
- Scroll offset: account for sticky strip height (48px) + navbar height (64px) = 112px
  - Implementation: Use `scrollIntoView` with a 112px negative margin offset, or manually calculate `element.offsetTop - 112`
- On mobile: no sticky strip is visible, so offset is navbar height only (64px)

### Active Section Tracking (Desktop)
- Use `IntersectionObserver` on all 9 section elements
- Options: `{ rootMargin: '-64px 0px -70% 0px', threshold: 0 }`
  - This marks a section active when it enters the top 30% of the viewport (below the navbar)
- When multiple sections intersect, the topmost one wins
- When no section is in view (e.g., user is below all sections — unlikely), keep last active
- On page load, mark the first section (Regime) as active

### Bottom Sheet Behavior
- Open: FAB tap → backdrop fades in (150ms) + sheet slides up (250ms)
- Close: tap backdrop, tap × button, or tap any section item
- Keyboard: Escape closes the sheet
- Scroll lock: `body { overflow: hidden }` while sheet is open (prevent background scroll)
- After navigation: restore body scroll, then smooth-scroll

---

## Responsive Behavior

| Breakpoint | Component | Behavior |
|------------|-----------|----------|
| 375px (mobile) | FAB | Visible, bottom-right fixed |
| 375px (mobile) | Sticky strip | Hidden (`display: none`) |
| 640px (mobile) | FAB | Visible |
| 640px (mobile) | Sticky strip | Hidden |
| 768px (tablet) | FAB | Hidden (`display: none`) |
| 768px (tablet) | Sticky strip | Visible, scrollable horizontally (overflow-x: auto) |
| 1024px (desktop) | FAB | Hidden |
| 1024px (desktop) | Sticky strip | Visible, all 9 pills likely fit (horizontal scroll still available as fallback) |
| 1280px (desktop) | Sticky strip | All pills fit comfortably without scrolling |

---

## CSS File

New file: `signaltrackers/static/css/section-quick-nav.css`

Include in `base.html` with other component CSS files.

---

## Accessibility Requirements

**Desktop Sticky Strip:**
- Element: `<nav aria-label="Page sections">`
- Pills: `<button>` elements (not `<a>` — no URL change)
- Active pill: `aria-current="true"` on the active button
- Focus style: 2px solid brand-blue-500 outline, 2px offset

**Mobile FAB:**
- `aria-label="Jump to section"` on the FAB button
- `aria-expanded="true"/"false"` to reflect sheet state
- `aria-controls="section-quick-nav-sheet"`

**Mobile Bottom Sheet:**
- `role="dialog"` on the sheet panel
- `aria-modal="true"`
- `aria-labelledby="section-nav-sheet-title"` (pointing to "Jump to Section" heading)
- Focus trap: Tab/Shift+Tab cycles within the sheet while open
- On open: move focus to the first section item (or close button)
- On close: return focus to the FAB button
- Escape key: closes the sheet

**Smooth scroll:**
- Respect `prefers-reduced-motion`: when set, use instant scroll (`behavior: 'auto'`)
  ```css
  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
  }
  ```

---

## Design System References

- **Colors:** `--brand-blue-500` (active), `--neutral-100/200/600/700` (default states) — see design-system.md § Color System
- **Typography:** `--text-sm` for pills (14px), `--text-base` for sheet items — see design-system.md § Typography
- **Spacing:** `--space-1` through `--space-5` — see design-system.md § Spacing System
- **Navigation component:** Top Navigation Bar reference (64px height) — see design-system.md § Navigation
- **Touch targets:** 48px FAB, 44px pills (desktop), 48px sheet items (mobile) — see design-system.md § Touch Target Sizing

---

## Implementation Notes for Engineer

1. **Add section IDs** to the 4 missing sections before wiring nav links (see Section Inventory table above)
2. **Placement of sticky strip:** Render inside `base.html` immediately after the `<nav class="navbar">` so it sticks below the navbar. Must be outside `{% block content %}` to appear on all pages (but should only render on the homepage — wrap with a template conditional or inject from `index.html` via `{% block extra_nav %}`)
3. **Z-index ladder:** Chatbot sits at 1040+; sticky strip at 100; FAB at 200; sheet at 300. Do not conflict with existing z-index values.
4. **IntersectionObserver fallback:** If observer isn't supported, skip active tracking — pills still function as scroll links
5. **JS file:** New `section-quick-nav.js` or inline in `index.html` `extra_js` block
6. **No backend changes required**
