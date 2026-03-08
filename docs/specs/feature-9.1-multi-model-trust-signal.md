# Multi-Model Trust Signal Design Spec

**Issue:** #218
**Feature:** Feature 9.1: Multi-Model Trust Signal — Why We Use Three Models
**Created:** 2026-03-08
**Status:** Draft

---

## Overview

Add a persistent, low-profile explainer callout at the bottom of the Recession Probability panel (§0.5) that frames SignalTrackers' multi-model architecture using the 2022–2024 yield curve false alarm as the canonical concrete example.

**Design constraint:** No new CSS files. Component is implemented entirely with Bootstrap utility classes and existing design system classes already loaded on the page.

**Key design principle:** This is a methodology note — supplementary context, not primary data. It must be clearly secondary in visual weight to the model values and interpretation text above it. Investors should encounter the data first, then find the framing below.

---

## User Flow

1. User opens SignalTrackers homepage
2. §0.5 Recession Probability panel renders — model values, divergence alert (if applicable), plain-language footer are the primary content
3. After reading the panel data, user notices the "WHY THREE MODELS?" callout at the bottom
4. User reads 2–3 sentence explanation anchored to the 2022 yield curve false alarm
5. User gains confidence in the multi-model approach — understands that divergence between models is itself informative

---

## Wireframes

### Mobile (375px)

```
┌────────────────────────────────────────────────────────┐
│ 📊 RECESSION PROBABILITY                      ⌄        │
│                                                        │
│  NY FED 12-MONTH LEADING                              │
│  Prospective Risk (12-mo ahead)        28.9% Elevated │
│  Range: 15.9% – 41.9%                                 │
│ ─────────────────────────────────────────────────────  │
│  CHAUVET-PIGER COINCIDENT                             │
│  Current Activity (real-time)           4.2% Low      │
│ ─────────────────────────────────────────────────────  │
│  RICHMOND FED SOS INDICATOR                           │
│  Weekly Labor Signal                    0.8% Low      │
│ ─────────────────────────────────────────────────────  │
│ ⚠ Models diverge by 28pp ...                          │
│ ─────────────────────────────────────────────────────  │
│  [plain-language footer text]                         │
│                          Data: FRED API · Richmond... │
│ ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌  │
│ ┌────────────────────────────────────────────────┐    │
│ │ ⓘ WHY THREE MODELS?                            │    │
│ │ Single indicators fail in practice. The yield  │    │
│ │ curve inverted in 2022 and held through 2024 — │    │
│ │ a textbook recession signal — while the        │    │
│ │ expansion continued. Three methodologically    │    │
│ │ distinct models are more reliable than any     │    │
│ │ one, and divergence between them is itself the │    │
│ │ signal.                                        │    │
│ └────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

### Tablet / Desktop (768px+)

Same callout block, full panel width. Rendering is identical — no layout change at larger breakpoints. The 3-column model card grid above renders normally; the callout sits below it as a full-width strip, after the data source credit.

```
┌──────────────────────────────────────────────────────────────┐
│ [3-column model card grid]                                   │
│                                                              │
│ ⚠ Models diverge by 28pp — ...                              │
│                                                              │
│ [plain-language footer]           Data: FRED · Richmond...  │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ ┌──────────────────────────────────────────────────────┐    │
│ │ ⓘ WHY THREE MODELS?                                  │    │
│ │ Single indicators fail in practice. The yield curve  │    │
│ │ inverted in 2022 and held through 2024 — a textbook  │    │
│ │ recession signal — while the expansion continued.    │    │
│ │ Three methodologically distinct models are more      │    │
│ │ reliable than any one, and divergence between them   │    │
│ │ is itself the signal.                                │    │
│ └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Specification

### Multi-Model Trust Signal Callout

**Placement:** Last element within `#recession-panel-content`, immediately after `.recession-source`. Separated from the source line by an `<hr class="regime-divider">`.

**Persistent:** Always rendered. Not collapsible. Not conditional on any data state.

**Implementation — HTML using existing classes only:**

```html
<hr class="regime-divider">
<div class="bg-light border-start border-2 border-secondary rounded-2 p-3 mt-2">
  <p class="text-xs text-uppercase fw-semibold text-secondary mb-1">
    <i class="bi bi-info-circle me-1" aria-hidden="true"></i>Why three models?
  </p>
  <p class="small text-muted mb-0">
    Single indicators fail in practice. The yield curve inverted in 2022 and held through
    2024 — a textbook recession signal — while the expansion continued. Three
    methodologically distinct models are more reliable than any one, and when they diverge,
    the disagreement is itself the signal.
  </p>
</div>
```

**Visual properties (derived from Bootstrap utilities + existing classes):**

| Property | Value | Source |
|----------|-------|--------|
| Background | `#F4F6F8` (neutral-100 equivalent) | Bootstrap `bg-light` |
| Left border | 4px solid, `--bs-secondary` (~neutral-500) | Bootstrap `border-start border-2 border-secondary` |
| Border radius | 8px | Bootstrap `rounded-2` |
| Padding | 16px | Bootstrap `p-3` |
| Label font | 12px, uppercase, 600 weight, neutral-500 | `text-xs text-uppercase fw-semibold text-secondary` |
| Label icon | `bi-info-circle`, 12px, decorative | `aria-hidden="true"` |
| Body font | 14px, neutral-600 | Bootstrap `small text-muted` |
| Body line-height | 1.6 | Inherited from global body style |
| Top margin | 8px | Bootstrap `mt-2` |

**Copy (static — no backend data required):**

- **Label:** "Why three models?"
- **Body:** "Single indicators fail in practice. The yield curve inverted in 2022 and held through 2024 — a textbook recession signal — while the expansion continued. Three methodologically distinct models are more reliable than any one, and when they diverge, the disagreement is itself the signal."

Copy is hardcoded in the template. No backend variable needed.

---

## Interaction Patterns

None. The callout is purely informational:
- No expand/collapse toggle
- No hover states
- No clickable elements
- No JS required

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| 375px | Full-width callout, stacked below data source line |
| 768px+ | Same — full-width, no layout change |

No responsive variants needed. The callout is full-width at all breakpoints.

---

## Accessibility Requirements

- `<i class="bi bi-info-circle" aria-hidden="true">` — decorative icon, text carries meaning
- No interactive elements — no ARIA roles, aria-expanded, or aria-controls needed
- Color contrast: `text-muted` (neutral-600) on `bg-light` (neutral-100) — passes WCAG AA (5.5:1)
- No information conveyed by color alone — label text always present alongside border

---

## Implementation Notes

**Files to modify:**
- `signaltrackers/templates/index.html` — add the callout block inside `#recession-panel-content`, after `.recession-source`

**Files NOT modified:**
- No CSS files added or changed
- No Python/backend files added or changed
- No new context variables

**What to look for in the template:**
```html
<div class="recession-source">
    Data: FRED API · Richmond Fed · Updated {{ recession_probability.updated }}
</div>
<!-- INSERT CALLOUT BLOCK HERE -->
```

Then close `</div>{# /.recession-panel__content #}` as normal.

---

## Design System References

| Element | Reference |
|---------|-----------|
| Background | Bootstrap `bg-light` ≈ neutral-100 |
| Left border accent | Bootstrap `border-secondary` ≈ neutral-500 |
| Label style | `text-xs text-uppercase fw-semibold` — matches existing model name labels in this panel |
| Body text | Bootstrap `small text-muted` — matches data source credit style |
| Divider | `.regime-divider` `<hr>` — already used within this panel |
| Icon | `bi-info-circle` — Bootstrap Icons, already loaded |
| Border radius | Bootstrap `rounded-2` — matches existing card radius |

---

## Out of Scope

- **Historical accuracy / backtesting panel** — explicitly deferred to Phase 8+ per CEO decision. Do NOT include.
- **Tooltip or modal with extended methodology** — keep it static and simple.
- **Collapsible behavior** — the copy is short enough (~55 words) that it does not need progressive disclosure.
- **Link to external model documentation** — no external links in this feature.
- **Placement on detail pages** — homepage only.

---

*Spec complete. PM: Please review and approve to proceed to user story creation.*
