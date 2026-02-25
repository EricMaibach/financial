# Macro Regime Score Panel — Design Spec

**Issue:** #138
**Feature:** Feature 5.1: Macro Regime Score Panel
**Created:** 2026-02-25
**Designer:** UI/UX Designer
**Status:** Draft

---

## Overview

Enhance the existing Section 0 regime card (built in Feature 4.1) with two missing capabilities: **trend direction** (improving / stable / deteriorating) and a **confidence sparkline** (14-day historical confidence trend). Also fix the existing gap where confidence is hidden on mobile.

**What Feature 4.1 built:** Regime label, plain-language summary, highlighted signal chips, confidence (desktop-only), detail page strips, signal annotations.

**What Feature 5.1 adds:**
1. Trend direction indicator — visible on all breakpoints
2. 14-day confidence sparkline — inline SVG, server-rendered
3. Confidence label on mobile — fix existing `display:none` CSS

No new components need to be created from scratch — this spec extends the existing `regime-card` CSS and Jinja2 template. One new sub-section (the sparkline row) is added to the card.

---

## User Flow

1. User opens SignalTrackers homepage
2. Section 0 regime card is the first visible content (above the fold)
3. User sees: regime label + confidence + **trend direction** at a glance (Row 1–2, ~72px on mobile)
4. User reads plain-language summary
5. User notices **sparkline trend** below the summary — can see whether confidence has been climbing or falling
6. User taps signal chips to explore key drivers

---

## Wireframes

### Mobile (375px) — Enhanced Card Layout

```
┌──────────────────────────────────────────────────────┐
│ MACRO REGIME SCORE                    [section title] │
│ ┌────────────────────────────────────────────────┐   │
│ │ ● BEAR REGIME              Updated Feb 25, 2026 │   │
│ │ ↘ Deteriorating    Confidence: High             │   │ ← NEW row
│ │ ─────────────────────────────────────────────── │   │
│ │ "Growth is decelerating and credit spreads are  │   │
│ │  widening. Risk assets face headwinds. Watch    │   │
│ │  credit and safe haven signals closely."        │   │
│ │ ─────────────────────────────────────────────── │   │
│ │ 14-DAY CONFIDENCE TREND                         │   │ ← NEW row
│ │ [▁▂▃▄▅▆▇▇▇▆ sparkline line ──────────]         │   │
│ │ ─────────────────────────────────────────────── │   │
│ │ REGIME-HIGHLIGHTED SIGNALS                      │   │
│ │ ┌─────────────────┐  ┌─────────────────┐       │   │
│ │ │ HY Spread       │  │ VIX             │       │   │
│ │ │ 462bps          │  │ 28.4            │       │   │
│ │ │ ▲ Elevated risk │  │ ▲ Elevated fear │       │   │
│ │ └─────────────────┘  └─────────────────┘       │   │
│ └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**Mobile row heights (approximate):**
- Row 1 (state label + date): 36px
- Row 2 (trend direction + confidence): 28px  ← NEW
- Divider + summary: ~80px
- Divider + sparkline section: ~52px  ← NEW
- Divider + signal chips: ~120px
- **Total card: ~340px** — regime label visible within 64px of scroll start (above the fold ✅)

### Tablet / Desktop (768px+) — Enhanced State Panel

```
┌─────────────────────────────────────────────────────────────────┐
│ MACRO REGIME SCORE                                               │
│ ┌─────────────────────────┐  ┌──────────────────────────────┐   │
│ │ ● BEAR REGIME           │  │ Growth is decelerating and   │   │
│ │                         │  │ credit spreads are widening. │   │
│ │ Feb 25, 2026            │  │ Risk assets face headwinds.  │   │
│ │                         │  │ Watch credit and safe haven  │   │
│ │ Confidence: High        │  │ signals closely.             │   │
│ │ ↘ Deteriorating         │  └──────────────────────────────┘   │
│ │ [sparkline  ─────────]  │  ← sparkline inside state panel      │
│ └─────────────────────────┘                                      │
│                                                                  │
│ REGIME-HIGHLIGHTED SIGNALS                                       │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│ │ HY Spread     │  │ VIX           │  │ Gold          │        │
│ │ 462bps        │  │ 28.4          │  │ $2,640        │        │
│ └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Trend Direction Row (NEW — Mobile)

Renders as a new row between the state header row and the first divider on mobile.
On tablet+, integrates into the existing regime-state-panel (left column).

**Layout:** `display: flex; align-items: center; gap: 16px; margin-top: 8px`

**Trend Arrow sub-element (`.regime-trend-arrow`):**
- Icon: Bootstrap Icons
  - Improving: `bi-arrow-up-right`
  - Stable: `bi-arrow-right`
  - Deteriorating: `bi-arrow-down-right`
- Icon size: 0.875rem (14px)
- Icon color:
  - Improving: `#16A34A` (success-600)
  - Stable: `#6b7280` (neutral-500)
  - Deteriorating: `#DC2626` (danger-600)
- Label text alongside: "Improving" / "Stable" / "Deteriorating"
- Label font: text-sm (14px), weight 500, neutral-700
- Combined `aria-label="Trend: Deteriorating"` on the flex container

**Confidence sub-element (`.regime-trend-confidence`):**
- Text: "Confidence: High" (or Medium / Low)
- Font: text-sm (14px), weight 500
- Color:
  - High: success-700 `#15803D`
  - Medium: warning-700 `#A16207`
  - Low: danger-700 `#B91C1C`
- **Visible on all breakpoints** (removes current `display:none` on mobile)

**CSS class additions:**
```css
.regime-trend-row { }         /* new flex row below state header */
.regime-trend-arrow { }       /* icon + "Improving/Stable/Deteriorating" */
.regime-trend-arrow--improving { color: #16A34A; }
.regime-trend-arrow--stable    { color: #6b7280; }
.regime-trend-arrow--deteriorating { color: #DC2626; }
.regime-trend-confidence { }  /* "Confidence: High/Medium/Low" */
```

---

### 2. Confidence Sparkline (NEW)

An inline SVG polyline showing the last 14 days of regime confidence score (0–100 normalized).

**Where it renders:**
- Mobile: below the plain-language summary, in a new `.regime-sparkline-section` row
- Tablet+: inside `.regime-state-panel` below the trend direction row

**Dimensions:**
- Mobile: `width: 100%; height: 32px` (full card width, short)
- Desktop (inside state panel): `width: 100%; height: 36px`

**SVG implementation:**
- `<svg viewBox="0 0 100 32" preserveAspectRatio="none">` with `width/height` via CSS
- `<polyline>` connecting 14 data points, normalized to viewBox coordinates
- No axes, no labels, no grid
- Stroke: regime border color (e.g., `var(--regime-bear-border)`)
- Stroke-width: 2
- Fill: none
- `<title>14-day confidence trend</title>` for accessibility

**Backend provides:** `macro_regime.confidence_history` — a list of 14 floats (0.0–1.0), oldest first, representing daily confidence scores.

**Engineer renders** the polyline `points` attribute server-side:
```python
# Example: normalize list of floats to SVG viewBox(0,0,100,32)
# x: 0 to 100, distributed across 14 points
# y: inverted (0 = top, 32 = bottom in SVG)
```

**Sparkline section (mobile only block):**
- Section label: "14-DAY CONFIDENCE TREND" in text-xs, neutral-500, uppercase, letter-spacing: 0.05em
- Rendered as: label above, sparkline SVG below
- Container padding: 12px 0
- Separated from summary by `.regime-divider`
- Separated from signals by `.regime-divider`

**Fallback:** If `confidence_history` is empty or has fewer than 3 points, hide the sparkline section entirely (no empty space).

---

### 3. Section Title Update

Update the section title from "Current Macro Regime" to **"Macro Regime Score"** to align with the feature name and signal that this is now a synthesized score panel, not just a label.

- `<h3>` text: "Macro Regime Score"
- Icon: keep `bi-globe2` (established)
- No other changes to section header

---

### 4. Confidence on Mobile — Fix

Currently `.regime-confidence { display: none; }` hides confidence on mobile. Feature 5.1 requires it on all breakpoints.

**Remove the `display:none` default.** Instead, move confidence into the new `.regime-trend-row` (inline with trend direction), so it doesn't create a fourth row.

The existing `.regime-confidence { display: none; }` CSS is replaced by `.regime-trend-confidence { }` which is visible by default.

On tablet+, the confidence text moves into `.regime-state-panel` alongside the trend direction — same as it currently renders, just no longer hidden.

---

## Interaction Patterns

- **No animations on sparkline** — static SVG, no JavaScript transitions
- **Sparkline is not interactive** — no tooltips, no hover states (keeps mobile complexity low)
- **Trend direction does not expand** — read-only label, not a toggle
- **All existing interactions preserved** — signal chip hover/tap, annotation collapse on mobile remain unchanged

---

## Responsive Behavior

| Breakpoint | Trend Direction | Confidence | Sparkline | Placement |
|------------|----------------|-----------|-----------|-----------|
| 375px (mobile) | Row 2 below state header | Inline in Row 2 with trend | Full-width section below summary | New rows in card |
| 640px (large phone) | Same as mobile | Same | Same | Same |
| 768px (tablet) | Inside left state panel | Inside left state panel | Inside left state panel, full panel width | State panel |
| 1024px+ | Same as tablet | Same | Same | Same |

---

## Template Structure (Jinja2 Reference)

The existing `index.html` Section 0 block receives two additions:

**Addition 1 — Trend row** (after `.regime-state-row`, before mobile divider):

```html
{# NEW: Trend direction + confidence row #}
{% if macro_regime.trend %}
<div class="regime-trend-row">
  <span class="regime-trend-arrow regime-trend-arrow--{{ macro_regime.trend }}"
        aria-label="Trend: {{ macro_regime.trend | title }}">
    <i class="bi bi-arrow-{{ 'up-right' if macro_regime.trend == 'improving' else ('right' if macro_regime.trend == 'stable' else 'down-right') }}"
       aria-hidden="true"></i>
    {{ macro_regime.trend | title }}
  </span>
  {% if macro_regime.confidence %}
  <span class="regime-trend-confidence regime-confidence-{{ macro_regime.confidence | lower }}">
    Confidence: {{ macro_regime.confidence }}
  </span>
  {% endif %}
</div>
{% endif %}
```

**Addition 2 — Sparkline section** (mobile: after summary divider; desktop: inside state panel):

```html
{# NEW: 14-day sparkline section (mobile placement) #}
{% if macro_regime.confidence_history and macro_regime.confidence_history | length >= 3 %}
<hr class="regime-divider">
<div class="regime-sparkline-section">
  <div class="regime-sparkline-label">14-Day Confidence Trend</div>
  <svg class="regime-sparkline"
       viewBox="0 0 100 32"
       preserveAspectRatio="none"
       aria-label="14-day confidence trend"
       role="img">
    <title>14-day confidence trend</title>
    <polyline
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      points="{{ macro_regime.confidence_sparkline_points }}" />
  </svg>
</div>
{% endif %}
```

`confidence_sparkline_points` is a pre-computed string from the backend (e.g., `"0,24 7,22 14,20 21,18 28,16 35,14 ..."` for 14 points normalized to the viewBox).

---

## Backend Data Requirements

The existing `macro_regime` object (from `market_signals.py` / regime engine) needs two new fields:

| Field | Type | Description |
|-------|------|-------------|
| `macro_regime.trend` | string | `"improving"` / `"stable"` / `"deteriorating"` |
| `macro_regime.confidence_history` | list[float] | 14 daily confidence scores, 0.0–1.0, oldest first |
| `macro_regime.confidence_sparkline_points` | string | Pre-computed SVG polyline points string |

**PM/Engineer: Confirm availability of these fields.** If `confidence_history` is not yet tracked, the sparkline section simply doesn't render (Jinja2 `{% if %}` guard). Trend direction can be derived from comparing the last 3–5 confidence scores if needed.

---

## Accessibility Requirements

- Trend direction arrow uses `aria-label="Trend: Deteriorating"` — conveys meaning via text, not icon alone
- Sparkline uses `role="img"` + `<title>14-day confidence trend</title>` — descriptive but no data values (screen readers don't need the chart)
- Confidence label is always text (e.g., "Confidence: High"), not icon-only
- No new interactive controls added — no new tab stops, no new keyboard requirements
- Color is never used alone: trend uses icon + text; confidence uses text label

---

## Design System References

| Element | Reference |
|---------|-----------|
| Trend arrow colors | Semantic: success-600 (improving), neutral-500 (stable), danger-600 (deteriorating) |
| Confidence colors | Existing: `.regime-confidence-high/medium/low` |
| Sparkline stroke | Existing regime border tokens: `--regime-{state}-border` |
| Sparkline dimensions | Spacing system: 32px height = space-8 |
| Typography | text-xs for sparkline label, text-sm for trend/confidence |
| Spacing | 4px baseline grid, 8px margin-top for trend row, 12px for sparkline section |

---

## Out of Scope

- **Numeric score display** — Feature asked for label-based confidence ("high/medium/low"), not a 0–100 number. If a numeric score is desired, that's a future enhancement.
- **Interactive sparkline** — No tooltips or hover states on sparkline; static display only.
- **Regime history page** — A full historical view of past regime states is a future feature.
- **Regime change notification** — Alert when regime flips state is out of scope (relates to Feature 3.4 alert system).
- **Historical signal annotations** — Showing how signals evolved over time is out of scope.

---

## Open Questions

1. **Trend calculation** — How is "improving/stable/deteriorating" determined? Recommend: compare 3-day rolling average of confidence score vs. 10-day rolling average. If delta > +5%, "improving"; if delta < -5%, "deteriorating"; otherwise "stable." PM/Engineer: confirm threshold or provide alternate definition.

2. **Confidence history availability** — Is there an existing time-series store for daily confidence scores, or does the regime engine only compute the current day's value? If history is not available at launch, the sparkline section is hidden (graceful degradation is built into the spec).

3. **Confidence on mobile** — The existing spec (Feature 3.3) kept confidence desktop-only for space reasons. Feature 5.1 AC requires it everywhere. The design places it inline with trend direction to avoid adding a third row. PM/Engineer: confirm this compact treatment is acceptable.

4. **Section title** — This spec proposes renaming "Current Macro Regime" to "Macro Regime Score." If PM prefers to keep the original title, the section h3 text update is optional.

---

*Spec complete. PM: Please review and approve to proceed to user story creation.*
