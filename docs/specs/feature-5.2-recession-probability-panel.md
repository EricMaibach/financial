# Recession Probability Panel — Design Spec

**Issue:** #146
**Feature:** Feature 5.2: Multi-Model Recession Probability Sub-Panel
**Created:** 2026-02-26
**Designer:** UI/UX Designer
**Status:** Draft

---

## Overview

Add a recession probability sub-panel directly below the Macro Regime Score Panel (Section 0 on the homepage). The panel displays three institutional models side-by-side with confidence bands — replacing the industry-standard single decontextualized number with an epistemically honest, labeled multi-model view.

**Key design principle:** The three-model display is the product's core differentiation. The design must communicate "these are three different methodologies measuring different things" — not "the answer is somewhere between these numbers." Model divergence is itself a signal worth surfacing.

**Integration:** Positioned as a new section immediately below the existing regime card, sharing visual language (regime border color, section header pattern). Not part of the regime card itself — a companion panel.

---

## User Flow

1. User opens SignalTrackers homepage
2. Section 0 shows Macro Regime Score (Bear / Bull / Neutral / etc.)
3. User scrolls slightly (or section is visible on tablet+)
4. Section 0.5 shows "Recession Probability" with a summary state label
5. On mobile: user taps header to expand the three-model detail
6. On tablet+: detail is always visible without interaction
7. User reads three models, understands prospective vs. current vs. weekly signals
8. If models diverge >15pp: divergence alert draws attention to the uncertainty signal

---

## Wireframes

### Mobile (375px) — Collapsed Default

```
┌──────────────────────────────────────────────────────┐
│ MACRO REGIME SCORE                    [section 0]    │
│ ┌────────────────────────────────────────────────┐   │
│ │  ● BEAR REGIME              ↘ Deteriorating    │   │
│ │  Confidence: High                              │   │
│ │  "Growth is decelerating..."                   │   │
│ │  [sparkline]  [signal chips]                   │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ 📊 RECESSION PROBABILITY         ⌄ Show detail │   │ ← collapsed
│ │ Low–Elevated · Models diverging               │   │
│ └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Mobile (375px) — Expanded

```
┌──────────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────────┐   │
│ │ 📊 RECESSION PROBABILITY         ⌃ Hide detail │   │
│ │                                                │   │
│ │  NY FED 12-MONTH LEADING                       │   │
│ │  Prospective Risk (12-mo ahead)                │   │
│ │                              28.9%  Elevated   │   │
│ │  Confidence range: 15.9% – 41.9%              │   │
│ │ ─────────────────────────────────────────────  │   │
│ │  CHAUVET-PIGER COINCIDENT                      │   │
│ │  Current Activity (real-time)                  │   │
│ │                               4.2%  Low        │   │
│ │ ─────────────────────────────────────────────  │   │
│ │  RICHMOND FED SOS INDICATOR                    │   │
│ │  Weekly Labor Signal                           │   │
│ │                               0.8%  Low        │   │
│ │ ─────────────────────────────────────────────  │   │
│ │ ⚠ Models diverge by 28pp                      │   │
│ │   Leading and coincident signals disagree —   │   │
│ │   spread itself signals elevated uncertainty. │   │
│ │ ─────────────────────────────────────────────  │   │
│ │  The NY Fed's leading model signals growing    │   │
│ │  12-month risk. Coincident indicators show     │   │
│ │  no current contraction.                       │   │
│ │                                                │   │
│ │  Data: FRED API · Richmond Fed                │   │
│ └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Tablet (768px) — Always Expanded, 3-Column

```
┌─────────────────────────────────────────────────────────────────┐
│ 📊 RECESSION PROBABILITY                                         │
│                                                                  │
│ ┌───────────────────┐  ┌───────────────────┐  ┌──────────────┐  │
│ │ NY Fed 12-Month   │  │ Chauvet-Piger     │  │ Richmond SOS │  │
│ │ Prospective Risk  │  │ Current Activity  │  │ Weekly Labor │  │
│ │                   │  │                   │  │              │  │
│ │     28.9%         │  │      4.2%         │  │    0.8%      │  │
│ │   Elevated        │  │      Low          │  │    Low       │  │
│ │                   │  │                   │  │              │  │
│ │ [confidence bar ] │  │ [confidence bar ] │  │ [prob bar  ] │  │
│ │ Range: 16–42%     │  │                   │  │              │  │
│ └───────────────────┘  └───────────────────┘  └──────────────┘  │
│                                                                  │
│ ⚠ Models diverge by 28pp — spread signals elevated uncertainty   │
│                                                                  │
│ The NY Fed's leading model signals growing 12-month risk.        │
│ Coincident indicators show no current contraction.              │
│                                          Data: FRED · Richmond  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Section Header

**Layout:** Standard SignalTrackers section header pattern (same as Section 0, Section 1, etc.)

- Icon: `bi-bar-chart-steps` (16px, brand-blue-500)
- Title: `<h3>` — "Recession Probability"
- Left border: 4px solid, using current regime border color token (`var(--regime-{state}-border)`) for visual continuity with Section 0
- Background: white (same as other sections)

**Mobile header summary row** (visible when collapsed):
- Summary text: `[lowest_risk_label]–[highest_risk_label] · [alignment_label]`
  - Examples: "Low · Models aligned", "Low–Elevated · Models diverging"
  - Font: text-sm (14px), neutral-600
- Expand/collapse toggle: standard progressive disclosure chevron (right-aligned), 44px tap target
- Collapse state: card shows header row only (~56px total)

**Tablet+:** No collapse toggle — full content always visible.

---

### Model Row (Mobile)

Each model is a labeled row within the expanded panel. Three rows stacked vertically, separated by `<hr class="regime-divider">`.

**Layout per model:**
```
[MODEL FULL NAME]
[Description label]              [Value]  [Risk Label]
[Confidence range text — NY Fed only]
```

**Elements:**
- **Model name:** text-xs (12px), uppercase, letter-spacing 0.05em, neutral-500 — matches sparkline label style
- **Description label:** text-sm (14px), neutral-600, italic
- **Probability value:** text-xl (20px), weight 700, color-coded (see color thresholds below)
- **Risk label:** text-xs (12px), weight 600, same color as probability value — always shown alongside color ("Low" / "Elevated" / "High")
- **Confidence range (NY Fed only):** text-xs (12px), neutral-500 — "Range: 15.9% – 41.9%"

**Color thresholds (probability value + risk label):**
| Range | Color | Label |
|-------|-------|-------|
| 0 – 14.9% | `#15803D` (success-700) | Low |
| 15 – 34.9% | `#B45309` (warning-700) | Elevated |
| ≥ 35% | `#B91C1C` (danger-700) | High |

Color is never used alone — the text label "Low / Elevated / High" always accompanies.

---

### Model Card (Tablet+ 3-Column Grid)

On 768px+, three cards laid out in a CSS grid (`grid-template-columns: repeat(3, 1fr)`, gap: 16px).

**Card structure:**
```
┌─────────────────────────┐
│ Model Short Name        │  ← text-xs, uppercase, neutral-500
│ Description             │  ← text-sm, neutral-600, italic
│                         │
│          28.9%          │  ← text-3xl (30px), weight 700, color-coded
│          Elevated       │  ← text-sm, weight 600, same color
│                         │
│ [──────[████]────────]  │  ← confidence bar (NY Fed) or probability bar
│ Range: 16% – 42%       │  ← text-xs, neutral-500 (NY Fed only)
│                         │
│ via FRED                │  ← text-xs, neutral-400
└─────────────────────────┘
```

**Card styling:**
- Border: 1px solid neutral-200
- Border-radius: 8px
- Padding: 16px
- No hover state (read-only data cards)

---

### Confidence/Probability Bar (Tablet+)

A horizontal track showing the probability value on a 0–50% scale (capped at 50% — fiscal stability signals rarely exceed this; values above 50% map to the right edge).

**Track:**
- Width: 100% (card width)
- Height: 8px
- Border-radius: 4px
- Background: neutral-100

**Filled region:**
- **For NY Fed (has confidence band):** filled segment from lower bound to upper bound of confidence interval, using the regime border color at 30% opacity
  - Example: 16%–42% range fills 32%–84% of the track (on a 0–50% scale)
- **For Chauvet-Piger and Richmond Fed (point estimate only):** filled from 0 to value position, neutral-300

**Point estimate marker:**
- 10×10px circle, centered on the value position
- Color: regime border color (matches Section 0 left border)
- Border: 2px white (creates separation from filled region)

**Scale:** 0–50% linear. Values above 50% pin to the right edge (treated as ≥50%). A small "50%" label appears at the right end if any value is ≥ 40%.

---

### Divergence Alert

Shown when the spread between the highest and lowest model values exceeds **15 percentage points**.

**Layout:**
- Mobile: full-width row between the last model row and the plain-language footer
- Tablet+: below the 3-column grid, above the plain-language footer
- Width: full panel width

**Styling:**
- Background: `#FEF3C7` (warning-100)
- Border: 1px solid `#FDE68A` (warning-200)
- Border-radius: 6px
- Padding: 12px 16px
- Icon: `bi-exclamation-triangle-fill`, `#B45309` (warning-700), 14px, `aria-hidden="true"`
- Text: "Models diverge by [X]pp — leading and coincident signals disagree. Spread itself signals elevated uncertainty."
  - Font: text-sm (14px), warning-700
  - "[X]pp" is the computed spread (max – min, rounded to 1 decimal)

**When no divergence:** Element is not rendered (no empty space).

---

### Plain-Language Footer

A 2–3 sentence interpretation block below the models/divergence alert.

**Styling:**
- Font: text-sm (14px), neutral-600
- Line-height: 1.6
- Top border: `<hr class="regime-divider">` separating from models above
- Margin-top: 12px

**Content:** Backend-generated interpretation. Spec guidance for backend:
- Lead with the highest-value model's signal
- Note if leading vs. coincident models agree or disagree
- Avoid absolute language ("will" → prefer "suggests", "indicates")

**Data source credit:**
- Font: text-xs (12px), neutral-400
- Alignment: right (tablet+), left (mobile)
- Text: "Data: FRED API · Richmond Fed · Updated [date]"

---

## Interaction Patterns

**Mobile expand/collapse:**
- Toggle element: the section header row (full width tap target, min-height: 44px)
- Chevron: rotates 0° (collapsed) → 180° (expanded), CSS `transform: rotate`, `transition: 0.2s ease`
- Content: `max-height` transition (same pattern as existing progressive disclosure)
- Default state: **collapsed** on mobile
- `aria-expanded` on the toggle button, `id` on the content div for `aria-controls`

**Tablet+:**
- No toggle — section content always rendered and visible
- No JS needed for display

**No interactive elements within the panel** — all data is read-only. No tooltips, no clickable models, no drill-down.

---

## Responsive Behavior

| Breakpoint | Layout | Collapse | Bar |
|------------|--------|----------|-----|
| 375px (mobile) | Stacked model rows | Collapsed by default | No (text range only) |
| 640px (large phone) | Same as mobile | Same | No |
| 768px (tablet) | 3-column card grid | Always expanded | Yes |
| 1024px+ | Same as tablet | Always expanded | Yes |

---

## CSS Classes

```css
/* Section wrapper */
.recession-panel { }
.recession-panel__header { }           /* section title row + mobile toggle */
.recession-panel__header--collapsed { } /* chevron state */
.recession-panel__content { }           /* collapsible region */

/* Model rows (mobile) */
.recession-model-row { }
.recession-model-name { }               /* text-xs uppercase label */
.recession-model-desc { }               /* italic description */
.recession-model-value { }              /* large probability number */
.recession-model-value--low { color: #15803D; }
.recession-model-value--elevated { color: #B45309; }
.recession-model-value--high { color: #B91C1C; }
.recession-model-risk-label { }         /* "Low / Elevated / High" */
.recession-model-range { }              /* "Range: X%–Y%" for NY Fed */

/* Model cards (tablet+) */
.recession-card-grid { }                /* CSS grid 3-col */
.recession-card { }
.recession-bar-track { }
.recession-bar-fill { }                 /* confidence band or point fill */
.recession-bar-marker { }               /* point estimate circle */

/* Divergence alert */
.recession-divergence-alert { }

/* Footer */
.recession-footer { }
.recession-source { }
```

---

## Accessibility Requirements

- Section header toggle uses `<button aria-expanded="false/true" aria-controls="recession-panel-content">`
- Probability values are text (never image/canvas) — accessible by default
- Risk label ("Low / Elevated / High") always accompanies color — no color-only information
- Divergence alert icon uses `aria-hidden="true"` (text carries meaning)
- Confidence bar (tablet+): decorative — `aria-hidden="true"` on the SVG; the "Range: X%–Y%" text beneath carries the information for screen readers
- No new interactive elements requiring keyboard navigation beyond the mobile expand/collapse toggle
- Mobile toggle: standard keyboard accessible button (Enter/Space to activate)

---

## Backend Data Requirements

The template receives a `recession_probability` context object:

| Field | Type | Description |
|-------|------|-------------|
| `recession_probability.ny_fed` | float | NY Fed 12-month probability (0.0–100.0) |
| `recession_probability.ny_fed_lower` | float | Lower bound of confidence interval |
| `recession_probability.ny_fed_upper` | float | Upper bound of confidence interval |
| `recession_probability.chauvet_piger` | float | Chauvet-Piger coincident probability (0.0–100.0) |
| `recession_probability.richmond_sos` | float | Richmond Fed SOS indicator probability (0.0–100.0) |
| `recession_probability.interpretation` | string | Backend-generated plain-language summary (2–3 sentences) |
| `recession_probability.updated` | string | Formatted update timestamp |
| `recession_probability.divergence_pp` | float | Max–min spread (pre-computed by backend) |

**Backend computes:**
- `divergence_pp` = max(ny_fed, chauvet_piger, richmond_sos) – min(...)
- Risk label for each value using the thresholds defined in this spec (<15% Low, 15-35% Elevated, ≥35% High)
- `interpretation` string using the guidance in the Plain-Language Footer section above

**Data sources:**
- NY Fed: FRED series `RECPROUSM156N` (monthly) — confidence bands per NY Fed methodology (±13pp at moderate readings)
- Chauvet-Piger: FRED series `RECPROUSM156N` companion or `JHGDPBRINDX`
- Richmond Fed SOS: Richmond Fed website direct download

**PM/Engineer: Confirm exact FRED series IDs for all three models.** The series IDs above are references, not guaranteed to be exact.

---

## Design System References

| Element | Reference |
|---------|-----------|
| Section border color | `var(--regime-{state}-border)` — matches current Section 0 regime |
| Section header | Standard h3 + bi-icon pattern (same as all other sections) |
| Model name labels | text-xs uppercase — matches sparkline label style from Feature 5.1 |
| Probability value | text-xl/text-3xl — numeric display |
| Color thresholds | success-700, warning-700, danger-700 (AAA contrast on white) |
| Dividers | `.regime-divider` (established in Feature 4.1) |
| Progressive disclosure | Existing chevron toggle pattern (established in Feature 3.1) |
| Divergence alert | warning-100/warning-700 (matches spec for warning states) |
| Card grid | 8px border-radius, neutral-200 border (standard card) |

---

## Out of Scope

- **Historical chart** — A time-series chart of model probabilities over time is a future enhancement.
- **Regime correlation** — Linking specific recession probability thresholds to regime state changes is out of scope.
- **Notification on threshold breach** — Alert when probability crosses a threshold is a future feature (relates to Feature 3.4 alert system).
- **Detail page placement** — Recession probability appears on the homepage only in this feature. If desired on detail pages, that is a future feature.
- **Model methodology tooltips** — Educational hover/tap explanations of each model's methodology. Keep the panel clean; methodology links can be added in a future enhancement.

---

## Open Questions

1. **FRED series IDs** — Confirm the exact series IDs for Chauvet-Piger and Richmond Fed SOS to ensure the backend team pulls the correct data. The NY Fed 12-month series is well-documented; the others need verification.

2. **Update frequency** — NY Fed data is monthly; Chauvet-Piger is approximately monthly; Richmond Fed SOS is weekly. The panel should show the last available value for each model with its update date. Should the panel show per-model update dates, or just a single "panel last updated" timestamp? Recommend: per-model update date (text-xs below the source credit).

3. **Divergence threshold** — This spec uses 15pp as the divergence alert threshold. PM/Engineer: Is this appropriate, or should it be higher (e.g., 20pp) to avoid alert fatigue during normal model divergence?

4. **Interpretation text ownership** — Should the `interpretation` string be entirely backend-generated (rules-based Jinja conditions), or should it use the LLM annotation approach established in Feature 4.1? Recommend: rules-based at launch (avoids LLM dependency), with LLM as a future enhancement.

5. **Mobile default state** — This spec defaults the mobile panel to collapsed. PM: Confirm whether collapsed default is correct, or whether this panel should be open by default (it is below the fold on most phones, so collapsed reduces initial page length).

---

*Spec complete. PM: Please review and approve to proceed to user story creation.*
