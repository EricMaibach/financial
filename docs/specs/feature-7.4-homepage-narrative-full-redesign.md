# Homepage Narrative Cohesion — Full Redesign

**Issue:** #183
**Created:** 2026-03-03
**Supersedes:** `docs/specs/feature-7.3-homepage-narrative-cohesion.md` (Feature #179 — conservative scope, closed)
**Status:** Draft

---

## Overview

Transform the SignalTrackers homepage from a collection of independent data sections into a cohesive, regime-conditioned investment story. The page already has the right content — §0 through §3 contain everything needed. This redesign adds the structural, visual, and textual connective tissue that makes the regime narrative continuous from top to bottom.

Six approaches are in scope:

| # | Approach | Type | Dependencies |
|---|----------|------|-------------|
| 1 | Structural page reorder | HTML only | None |
| 2 | Visual regime threading — left-border accent across all sections | CSS + template | None |
| 3 | Persistent regime pill in navbar | CSS + template (`base.html`) | None |
| 4 | Regime-anchored AI synthesis — §1 and §2 (prompt changes) | Backend only | Feature #178 (depends on Bug #174) |
| 5 | Regime bridge sentences — §1.5 and §2 (template) | Template | None |
| 6 | What's Moving context note — §3 (template) | Template | None |

Approaches 1–3 and 5–6 are independent and can be implemented in a single story or sequenced. Approach 4 is blocked on Feature #178 and is a pure backend story with no UI spec required beyond the prompt text defined below.

---

## User Flow (Post-Redesign)

1. User loads homepage — §0 delivers the regime verdict with the full `.regime-card` treatment
2. §0.5 Recession Probability corroborates the verdict with the existing regime color bar
3. §0.75 Regime Implications follows immediately — implications of the regime for asset classes
4. *(NEW — §1.5 promoted to sit here)* Sector Tone appears as the second dimension of implications — how the regime is expressed in sector management behavior
5. §1 Market Conditions follows — raw market evidence the regime interpretation is built on; a subtle left-border accent and (if #178 is complete) a regime-anchored AI synthesis sentence orient the user
6. §2 Today's Briefing — a regime bridge sentence appears before the briefing content; the AI text (if #178 is complete) opens with a regime anchor
7. §3 What's Moving — a static regime context note under the section header frames the movers list
8. A user who enters mid-scroll at any section sees the regime color thread in the left border and reads regime context in the prose — no scrollback required to orient themselves

---

## Approach 1: Structural Page Reorder

### Designer Assessment

**Recommendation: Implement the reorder.** The current order places §1 Market Conditions (evidence) before §0.75 Regime Implications (interpretation) — a story inversion that makes users build their own context. The proposed VERDICT → IMPLICATIONS → EVIDENCE → TODAY arc resolves this cleanly and matches how a skilled analyst would actually narrate the macro picture.

The key design call is where to place §1.5 Sector Tone. Moving it up alongside §0.75 Regime Implications is correct — both sections are *interpretations of regime meaning*, not raw data. The combined Implications block (§0.75 + §1.5) tells the user what the regime means, before §1 Market Conditions shows them the data underneath.

**Variation considered:** Keeping §1.5 in its current position (after §1) and only moving §0.75 up before §1. Rejected — §1.5 Sector Tone is explicitly an interpretation ("management tone" is a forward-looking assessment, not a raw signal). It belongs with implications, not evidence.

### New Section Order

| Position | Section | Role | Template Lines (current) |
|----------|---------|------|--------------------------|
| 1 | §0 — Macro Regime Score | VERDICT | 14–153 |
| 2 | §0.5 — Recession Probability | CORROBORATING VERDICT | 158–324 |
| 3 | §0.75 — Regime Implications | IMPLICATIONS — asset classes | 329–441 |
| 4 | §1.5 — Sector Tone *(moved up)* | IMPLICATIONS — sectors | currently 725–825 |
| 5 | §1 — Market Conditions *(moved down)* | EVIDENCE | currently 445–721 |
| 6 | §2 — Today's Briefing | SYNTHESIS | 829–882 |
| 7 | §3 — What's Moving | REAL-TIME SIGNAL | 885–910 |

### Implementation

Cut the entire `<section aria-label="Sector Management Tone"...>` block (lines 725–825) from its current position and insert it immediately after `</section>` at line 441 (end of §0.75 Regime Implications). The `<section class="market-conditions-section"...>` block then sits below it.

No CSS changes are required for the reorder itself. No JavaScript changes required.

**Mobile wireframe — new order:**
```
┌─────────────────────────────────────┐
│ MACRO REGIME SCORE                  │  ← §0 VERDICT (unchanged)
├─────────────────────────────────────┤
│ RECESSION PROBABILITY               │  ← §0.5 VERDICT (unchanged)
├─────────────────────────────────────┤
│ REGIME IMPLICATIONS                 │  ← §0.75 IMPLICATIONS (unchanged)
├─────────────────────────────────────┤
│ SECTOR MANAGEMENT TONE  ← MOVED UP │  ← §1.5 IMPLICATIONS (moved from below §1)
├─────────────────────────────────────┤
│ MARKET CONDITIONS AT A GLANCE      │  ← §1 EVIDENCE (moved down)
├─────────────────────────────────────┤
│ TODAY'S MARKET BRIEFING            │  ← §2 SYNTHESIS (unchanged)
├─────────────────────────────────────┤
│ WHAT'S MOVING TODAY                │  ← §3 SIGNAL (unchanged)
└─────────────────────────────────────┘
```

---

## New Component: `.regime-pill`

A shared inline badge component used in three places: bridge sentences (Approaches 5–6), the navbar (Approach 3), and optionally section headers. This is a new design system component.

### Specification

```
Padding: 2px 8px (space-0.5 / space-2)
Border-radius: 10px  (pill shape)
Font-size: var(--text-xs)  (12px)
Font-weight: 700
Letter-spacing: 0.05em
Text-transform: uppercase
Display: inline-block
Vertical-align: baseline  (for inline-text usage)
```

**Color variants** (using existing regime CSS variables from `regime-card.css`):

| Class | Background | Text |
|-------|------------|------|
| `.regime-pill--bull` | `var(--regime-bull-border)` #16A34A | white |
| `.regime-pill--neutral` | `var(--regime-neutral-border)` #1E40AF | white |
| `.regime-pill--bear` | `var(--regime-bear-border)` #CA8A04 | white |
| `.regime-pill--recession` | `var(--regime-recession-border)` #DC2626 | white |

**Contrast check:**
- Bull (#16A34A on white): 3.1:1 — only used on dark navbar (white text on green: 3.1:1 — acceptable for badge/large text); for inline text context, the surrounding sentence provides context
- Bear (#CA8A04 on white): 3.1:1 — badge text is white on #CA8A04: 3.1:1 — same note
- White text on all variants on dark bg: all pass 4.5:1

**Note on inline text contrast:** The `.regime-pill` is used as a design accent within sentences where the surrounding text provides semantic context. It is never the sole conveyor of information — the regime name is always in the text before or after. Therefore the 3:1 large-text threshold applies (WCAG 1.4.11 non-text contrast), which all variants pass.

**Accessible markup pattern:**
```html
<span class="regime-pill regime-pill--{{ macro_regime.css_class | replace('regime-', '') }}"
      aria-label="Current regime: {{ macro_regime.state | title }}">
  {{ macro_regime.state | upper }}
</span>
```

**New CSS file:** `signaltrackers/static/css/components/regime-pill.css`
Link in `base.html` alongside existing component stylesheets.

---

## Approach 2: Visual Regime Threading — Section Left-Border Accent

### Designer Assessment

Of three options (left-border accent, section-header tint, full section background tint), **left-border accent is the right call.** It:
- Follows the existing metric card pattern (4px semantic left border)
- Is subtle enough not to overpower section content
- Is immediately recognizable as a design motif (repeats §0's card border color)
- Does not require wrapping sections in additional markup — applies to existing `<section>` tags

**Rejected: section-header tint.** Applied to the `.section-header` row, it would interfere with the neutral-50 background that creates visual rhythm. The header tint would also look disconnected from the rest of the section content below it.

**Rejected: full background tint.** Too heavy — the `-100` tints would compete with card backgrounds inside sections and create visual noise.

### CSS Specification

New CSS class: `.regime-thread` applied to all `<section>` elements below §0. Combines with the regime modifier class (`regime-bull`, `regime-neutral`, `regime-bear`, `regime-recession`) that the engineer adds to each section via Jinja2.

```css
/* regime-thread.css — new file */

/* Base thread class: adds left-border regime accent to homepage sections */
.regime-thread {
  border-left: 4px solid transparent;  /* fallback: no accent if no regime */
  padding-left: var(--space-4);         /* 16px — indent content from border */
  transition: border-color 0.3s ease;
}

/* Regime color assignments */
.regime-thread.regime-bull       { border-left-color: var(--regime-bull-border); }
.regime-thread.regime-neutral    { border-left-color: var(--regime-neutral-border); }
.regime-thread.regime-bear       { border-left-color: var(--regime-bear-border); }
.regime-thread.regime-recession  { border-left-color: var(--regime-recession-border); }
```

**Sections that receive `.regime-thread`** (all sections below §0):
- §0.5 — `#recession-panel-section`
- §0.75 — `#regime-implications`
- §1.5 — `#sector-tone-section` (after reorder)
- §1 — `#market-conditions`
- §2 — `.hero-briefing`
- §3 — `.whats-moving-section`

**Template pattern** (applied to each section `<section>` tag):
```jinja2
<section id="recession-panel-section"
         class="mb-4 regime-thread{% if macro_regime %} {{ macro_regime.css_class }}{% endif %}">
```

**Note on §0 (Macro Regime Score):** §0 already has the full `.regime-card` treatment with background, border, and text colors. Do NOT add `.regime-thread` to §0 — it would double-apply border styling and create visual conflict.

### Mobile / Responsive Behavior

The 4px left border is visible at all breakpoints. On mobile, the `padding-left: var(--space-4)` adds 16px left indent to the section content — verify this doesn't conflict with the existing section container padding in `dashboard.css`. If the section already has left padding, engineer should apply `padding-left` only if not already set, or add the 4px border without padding (the border itself provides visual separation without requiring content indent on mobile).

**Fallback:** If `macro_regime` is None (data unavailable), the `regime-thread` class applies with `border-left-color: transparent` — no visible border, no visual artifact.

---

## Approach 3: Persistent Regime Pill in Navbar

### Designer Assessment

The navbar (`base.html`) currently has: brand logo + tagline (left), nav links (collapsible), right-side controls (last-updated, bell, user menu). The regime pill must be visible on mobile (not inside the collapse) and on desktop.

**Recommended placement:** Inside the `navbar-brand-container` div, after the tagline `<span>`. This keeps it paired with the brand identity area, is always visible regardless of collapse state, and works at all breakpoints.

**Mobile behavior:** The brand container is always visible. The regime pill sits after the tagline (which hides on mobile via `d-none d-md-inline`). On mobile (< 768px), the pill appears directly after the brand name. On desktop, it appears after the tagline.

### Wireframes

**Desktop (1280px):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ↗ SignalTrackers  Comprehensive macro intelligence...  [BEAR]  Dashboard... │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Mobile (375px, collapsed):**
```
┌─────────────────────────────────────┐
│ ↗ SignalTrackers  [BEAR]      [≡]   │
└─────────────────────────────────────┘
```

### Template Pattern (`base.html`)

Insert inside `navbar-brand-container`, after the tagline `<span>`:
```jinja2
{% if macro_regime %}
<span class="navbar-regime-pill regime-pill regime-pill--{{ macro_regime.css_class | replace('regime-', '') }}"
      aria-label="Current macro regime: {{ macro_regime.state | title }}">
  {{ macro_regime.state | upper }}
</span>
{% endif %}
```

### CSS Specification

Add to `regime-pill.css`:
```css
/* Navbar placement variant — slight vertical offset for alignment in navbar */
.navbar-regime-pill {
  margin-left: var(--space-3);  /* 12px gap from brand/tagline */
  vertical-align: middle;
}
```

**Note on `macro_regime` availability in `base.html`:** `macro_regime` is currently passed to the homepage view context only. The engineer must check if it's available in the base template context (passed via `g` object, context processor, or similar). If not, the engineer needs to either:
- Add `macro_regime` to a context processor so it's available on all pages, OR
- Render the regime pill only on pages where it's available (homepage only), OR
- Use a lightweight data attribute + JavaScript to populate the pill after load

**Designer preference:** Option 1 (context processor) is cleanest — regime state changes infrequently and the data is already computed. If the engineer determines this is too costly, fallback to homepage-only rendering is acceptable. Leave this decision to the engineer.

---

## Approach 4: Regime-Anchored AI Synthesis (Backend Only — No New UI)

**Depends on Feature #178 (Macro Regime wired into AI context).**

No UI spec required. This is a prompt change in the backend generation code. The engineer modifies the AI prompt strings:

**§1 Market Conditions synthesis prompt addition:**
> "Begin your synthesis by explicitly naming the current macro regime (`{macro_regime}`) and in one sentence explaining whether current market conditions are consistent with or diverging from what is historically typical for this regime. Then proceed with your standard market conditions summary."

**§2 Today's Briefing prompt addition:**
> "Open your briefing by naming the current macro regime (`{macro_regime}`) and in one sentence explaining what it means for investors today. Then proceed with your standard briefing content."

**Fallback:** If `macro_regime` is None or "Unknown", omit the prompt addition — the generated text remains regime-agnostic.

**Design constraint for both:** The synthesis/briefing text is rendered as plain prose in existing HTML containers (`#market-synthesis-text`, `#briefing-narrative`). No markup changes to these containers are needed. The regime reference must appear in the first sentence of the generated text.

---

## Approach 5: Regime Bridge Sentences — §1.5 and §2 (Template Changes)

### Component Reuse

Bridge sentences use the new `.regime-pill` component (Approach 2 spec above) inline in prose.

**CSS class for the bridge sentence container:**
```css
/* In regime-pill.css or a new narrative-bridge.css */
.narrative-bridge {
  font-size: var(--text-sm);   /* 14px */
  color: var(--neutral-500);
  line-height: 1.6;
  margin-bottom: var(--space-4);  /* 16px before first content element */
}
```

### §1.5 — Sector Tone Bridge Sentence

**Placement:** After the existing regime link `<p>` (line 738–741 in current template), before the mobile toggle button. After the section reorder, §1.5 sits after §0.75 — the regime link `<a>` pointing up to `#macro-regime-section` should be **removed** (it was navigational scaffolding for when §0.75 was far above; now §0.75 is immediately above §1.5). Replace the regime link with the bridge sentence.

**Wireframe — Mobile (375px, after reorder):**
```
┌─────────────────────────────────────┐
│ 🏢 Sector Management Tone  Q4 2025  │  ← existing section header
├─────────────────────────────────────┤
│ In a [BEAR] regime, defensive        │  ← NEW bridge sentence (replaces regime link)
│ positioning and cash flow quality   │
│ tend to hold up better. See how     │
│ tone has shifted:                   │
├─────────────────────────────────────┤
│ ─────── ⌄ Show Sectors ─────────    │  ← existing toggle (mobile only)
├─────────────────────────────────────┤
│ (sector card grid)                  │
└─────────────────────────────────────┘
```

**Wireframe — Tablet+ (768px+):**
```
┌───────────────────────────────────────────────────────┐
│ 🏢 Sector Management Tone            Updated quarterly │
│ In a [BEAR] regime, defensive positioning and cash     │
│ flow quality tend to hold up better. See how tone      │
│ has shifted:                                           │
├───────────────────────────────────────────────────────┤
│ [sector card grid — expanded]                          │
└───────────────────────────────────────────────────────┘
```

**Template pattern:**
```jinja2
{% if macro_regime %}
<p class="narrative-bridge">
  In a <span class="regime-pill regime-pill--{{ macro_regime.css_class | replace('regime-', '') }}"
             aria-label="Current regime: {{ macro_regime.state | title }}">{{ macro_regime.state | upper }}</span>
  regime, {{ sector_tone_bridge[macro_regime.state] }}
</p>
{% endif %}
```

**Static copy dict** (`sector_tone_bridge` — defined in `views.py`):

| Regime state key | Bridge text |
|-----------------|-------------|
| `bull` | sector momentum typically confirms the regime. See how this quarter's tone aligns: |
| `neutral` | sector signals diverge — watch for emerging conviction in either direction: |
| `bear` | defensive positioning and cash flow quality tend to hold up better. See how tone has shifted: |
| `recession_watch` | significant sector deterioration is common. Earnings guidance and credit spreads deserve close attention: |

---

### §2 — Today's Briefing Regime Anchor

Two changes: a visual regime line before the briefing content, and (blocked on #178) a prompt addition.

**Change: Visual regime anchor line** (template-only, no backend):

**Placement:** After the `.section-header` row, before `<div class="briefing-content">`.

**Wireframe — Mobile and Desktop:**
```
┌─────────────────────────────────────┐
│ 📰 Today's Market Briefing   [date] │  ← existing header
├─────────────────────────────────────┤
│ Current regime: [BEAR]              │  ← NEW anchor line (template only)
├─────────────────────────────────────┤
│ [loading skeleton / briefing text]  │  ← existing briefing content
└─────────────────────────────────────┘
```

**Template pattern:**
```jinja2
{% if macro_regime %}
<p class="narrative-bridge narrative-bridge--compact">
  Current regime:
  <span class="regime-pill regime-pill--{{ macro_regime.css_class | replace('regime-', '') }}"
        aria-label="Current regime: {{ macro_regime.state | title }}">{{ macro_regime.state | upper }}</span>
</p>
{% endif %}
```

Additional CSS for the compact variant:
```css
.narrative-bridge--compact {
  margin-bottom: var(--space-3);  /* 12px — tighter than standard bridge */
}
```

**Note:** The §2 change is intentionally minimal — a one-line label + pill. The heavier narrative work is done by the AI prompt (Approach 4). The visual anchor is the template-level minimum that works even when #178 is not yet complete.

---

## Approach 6: What's Moving Context Note — §3 (Template Change)

### Specification

**Placement:** Inside `.whats-moving-section`, after the `.section-header` div (line 886–890), before the movers list/chart container.

**Wireframe — Mobile:**
```
┌─────────────────────────────────────┐
│ ⚡ What's Moving Today    [control] │  ← existing section header
│ In Bear regimes, defensive rotation │  ← NEW context note (plain text, no pill)
│ and breadth deterioration are key   │
│ warning signals. Cash flow quality  │
│ and dividend safety take precedence.│
├─────────────────────────────────────┤
│ [movers list]                       │
└─────────────────────────────────────┘
```

**Template pattern:**
```jinja2
{% if macro_regime %}
<p class="narrative-bridge narrative-bridge--whats-moving">
  {{ whats_moving_context[macro_regime.state] }}
</p>
{% endif %}
```

Additional CSS:
```css
.narrative-bridge--whats-moving {
  margin-top: var(--space-2);   /* 8px above */
  margin-bottom: var(--space-4); /* 16px below, before movers list */
}
```

**Design decision: no regime pill in §3.** Keep §3 lighter — no badge pill in the context note, plain text only. The regime name is written out in the copy itself ("In Bear regimes..."). This prevents visual overload — every other section now has a pill, §3 uses prose instead for variety.

**Static copy dict** (`whats_moving_context` — defined in `views.py`):

| Regime state key | Context note |
|-----------------|-------------|
| `bull` | In Bull regimes, momentum leaders often widen their lead. Watch for broad participation across sectors as a confirmation signal. |
| `neutral` | In Neutral regimes, cross-sector dispersion creates selective opportunities. Focus on relative strength rather than broad market direction. |
| `bear` | In Bear regimes, defensive rotation and breadth deterioration are key warning signals. Cash flow quality and dividend safety take precedence. |
| `recession_watch` | In Recession Watch regimes, capital preservation matters most. Watch for credit spread widening and earnings guidance cuts as leading signals. |

---

## Responsive Behavior Summary

| Approach | Mobile (375px) | Tablet (768px+) | Desktop (1280px+) |
|----------|---------------|-----------------|-------------------|
| 1. Page reorder | Same order | Same order | Same order |
| 2. Left-border thread | 4px left border on all sections | Same | Same |
| 3. Navbar pill | Shows next to brand (always visible) | Shows after tagline | Shows after tagline |
| 5. Bridge sentences | Block text, wraps | Block text | Block text |
| 6. Context note | Block text | Block text | Block text |

No new breakpoint behavior required — all changes are additive inline/block elements.

---

## Accessibility Requirements

- **`.regime-pill` badges**: Always include `aria-label="Current regime: [name]"` when used without surrounding text context (navbar). In bridge sentences, surrounding prose provides context — `aria-label` still recommended for explicit screen reader clarity.
- **Left-border thread**: Decorative — no ARIA needed. The `border-left-color` is not conveying critical information alone (regime is also visible in §0 and in prose).
- **Navbar regime pill**: Include `aria-label="Current macro regime: [name]"` for screen readers who may not visit §0.
- **Bridge sentences and context notes**: Plain `<p>` — no special ARIA.
- **Color contrast**: `--neutral-500` (bridge/context text) on white: 4.6:1 — passes AA. Regime pill: white on regime border colors — see note in component spec above (3:1 for badge/large text, passes 1.4.11).
- **Keyboard navigation**: No new interactive elements — no keyboard impact.
- **Touch targets**: No new interactive elements.

---

## Copy Tone Guidelines

All bridge sentences and context notes follow:
- **Factual, not alarmist** — describe historical patterns, not predictions
- **"Historically," "tend to," "watch for"** framing — avoids implying certainty
- **Second-person aware** — "watch for" not "you should"
- **Consistent with §0.75 Regime Implications panel tone** — complementary, not redundant

---

## New Files

| File | Action | Contents |
|------|--------|----------|
| `signaltrackers/static/css/components/regime-pill.css` | Create | `.regime-pill` component + `.navbar-regime-pill` variant |
| `signaltrackers/static/css/components/regime-thread.css` | Create | `.regime-thread` section left-border accent |
| `signaltrackers/static/css/components/narrative-bridge.css` | Create | `.narrative-bridge` and variants |

Link all three in `base.html` alongside existing component stylesheet links.

---

## Files Engineer Will Modify

| File | Change |
|------|--------|
| `signaltrackers/templates/index.html` | Section reorder (Approach 1); add `.regime-thread` class to sections (Approach 2); add bridge sentences §1.5 + §2 (Approach 5); add §3 context note (Approach 6) |
| `signaltrackers/templates/base.html` | Add navbar regime pill (Approach 3) |
| `signaltrackers/views.py` | Add `sector_tone_bridge` and `whats_moving_context` static dicts; if Approach 3 needs context processor, update there; if Approach 4 (blocked on #178), update AI prompt strings |

---

## Design System References

- Regime color variables: `--regime-bull-border`, `--regime-bear-border`, `--regime-neutral-border`, `--regime-recession-border` (in `regime-card.css`)
- Text sizes: `--text-xs` (12px for pill), `--text-sm` (14px for bridge text)
- Colors: `--neutral-500` for bridge text
- Spacing: `--space-2` (8px), `--space-3` (12px), `--space-4` (16px)
- Regime CSS class values: `regime-bull`, `regime-neutral`, `regime-bear`, `regime-recession`
- `macro_regime.state` values: `bull`, `neutral`, `bear`, `recession_watch`
- `macro_regime.css_class` values: `regime-bull`, `regime-neutral`, `regime-bear`, `regime-recession`

---

## Implementation Sequencing Recommendation

All independent approaches (1–3, 5–6) can be implemented in a single user story. Suggested sequence within that story:

1. Create CSS files (regime-pill, regime-thread, narrative-bridge)
2. Page reorder (Approach 1)
3. Add `.regime-thread` classes to sections (Approach 2)
4. Add navbar pill in `base.html` (Approach 3)
5. Add §1.5 bridge sentence — remove existing regime link, add bridge (Approach 5a)
6. Add §2 regime anchor line (Approach 5b)
7. Add §3 context note (Approach 6)
8. Add Python dicts to `views.py` (or wherever view context is built)

Approach 4 (AI prompts) is a separate story, blocked on Feature #178.

---

## Success Criteria Cross-Check

| Criterion (from issue) | Covered by |
|------------------------|-----------|
| Mid-scroll user identifies regime without scrolling to §0 | Approach 2 (visual thread) + Approach 3 (navbar pill) + Approaches 5–6 (bridge text) |
| Page order follows VERDICT → IMPLICATIONS → EVIDENCE → TODAY | Approach 1 |
| Regime color present in every section below §0 | Approach 2 |
| Navbar shows current regime at all times | Approach 3 |
| §2 Briefing text opens with regime name and meaning | Approach 4 (blocked on #178) |
| §1.5, §2, §3 all have visible regime context before content | Approach 5 (§1.5, §2) + Approach 6 (§3) |
| Designer spec validated before implementation begins | This document |
