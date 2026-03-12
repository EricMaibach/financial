# Contextual AI Entry Points Design Spec

**Issue:** #258
**Created:** 2026-03-12
**Status:** Ready for PM Approval

---

## Overview

Add contextual AI entry points so users can instantly drill into any dashboard section or AI briefing sentence for deeper explanation — without navigating away or starting a blank chatbot session.

This feature has two distinct parts:
- **Part 1 — Section-Level AI Icon:** Ghost pill buttons in section headers that open the chatbot pre-loaded with that section's data and context.
- **Part 2 — Sentence-Level Drill-In:** Users can tap/select sentences in the AI daily briefing to explore any specific claim or data point with the chatbot.

Design decisions for both parts were pre-approved in Discussion #45 (2026-03-11).

---

## AI Icon System (Shared Across Both Parts)

### Concept

Chart bars + ascending trend line + 4-pointed sparkle. The chart elements communicate financial context; the sparkle is the AI signature. This replaces `bi-robot` everywhere in the app.

### New CSS Tokens (add to design-system.md and root stylesheet)

```css
--ai-color:  #6366F1;  /* indigo-500 — AI identity, matches chatbot FAB */
--ai-accent: #F59E0B;  /* amber-500 — sparkle mark, warm contrast to cool indigo */
```

### Icon Family

| Variant | Size | Usage | Description |
|---------|------|-------|-------------|
| `ai-icon--full` | 64px | Design references only | 4 bars (indigo-300→600 gradient) + dark trend line + amber sparkle |
| `ai-icon--compact` | 24px | Section AI buttons, chatbot FAB | 3 bars + amber sparkle, no trend line (illegible at 24px) |
| `ai-icon--mark` | 16px | Inline badge, chatbot panel header | Sparkle only |

### SVG Assets

Store as static files in `static/img/` or inline in templates (engineer's choice).

**Full (64px, light background):**
```svg
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="8"  y="38" width="7" height="10" rx="1.5" fill="#A5B4FC"/>
  <rect x="19" y="30" width="7" height="18" rx="1.5" fill="#818CF8"/>
  <rect x="30" y="22" width="7" height="26" rx="1.5" fill="#6366F1"/>
  <rect x="41" y="16" width="7" height="32" rx="1.5" fill="#4F46E5"/>
  <polyline points="11,40 22,31 33,24 44,18 54,12" fill="none" stroke="#1E1B4B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M54,6 L55.5,10.5 L60,12 L55.5,13.5 L54,18 L52.5,13.5 L48,12 L52.5,10.5 Z" fill="#F59E0B"/>
</svg>
```

**Compact (24px, colored, light background — section buttons):**
```svg
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="2"  y="14" width="4" height="8"  rx="1" fill="#A5B4FC"/>
  <rect x="8"  y="10" width="4" height="12" rx="1" fill="#818CF8"/>
  <rect x="14" y="6"  width="4" height="16" rx="1" fill="#6366F1"/>
  <path d="M21,2 L22,4.5 L24.5,5.5 L22,6.5 L21,9 L20,6.5 L17.5,5.5 L20,4.5 Z" fill="#F59E0B"/>
</svg>
```

**Compact (24px, white-on-indigo — chatbot FAB background):**
```svg
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="2"  y="14" width="4" height="8"  rx="1" fill="rgba(255,255,255,0.6)"/>
  <rect x="8"  y="10" width="4" height="12" rx="1" fill="rgba(255,255,255,0.8)"/>
  <rect x="14" y="6"  width="4" height="16" rx="1" fill="#ffffff"/>
  <path d="M21,2 L22,4.5 L24.5,5.5 L22,6.5 L21,9 L20,6.5 L17.5,5.5 L20,4.5 Z" fill="#F59E0B"/>
</svg>
```

**Mark (16px, sparkle only — inline badge):**
```svg
<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
  <path d="M8,1 L9.2,5.2 L13.5,6.5 L9.2,7.8 L8,12 L6.8,7.8 L2.5,6.5 L6.8,5.2 Z" fill="#6366F1"/>
</svg>
```

### Existing App — Icon Migration

Replace `bi-robot` in these locations:

| Location | Old | New |
|----------|-----|-----|
| Chatbot FAB button | `bi-robot` | 24px compact SVG, white-on-indigo treatment |
| Chatbot panel header | `bi-robot` | 16px mark + "SignalTrackers AI" label |
| AI provenance badge (`index.html:1096`) | `bi-robot` | 16px mark + "AI-generated" label |

---

## Part 1 — Section-Level AI Entry Points

### User Flow

1. User sees a ghost pill button labeled `✦ AI` right-aligned in each major dashboard section header
2. User taps/clicks the button
3. Chatbot opens (same behavior as FAB click)
4. Chatbot is pre-loaded with that section's current data and opens with a section-specific explanation — not a blank prompt

### Section AI Button Specification

**Appearance:**
- Ghost/outline pill button (no fill at rest, light border)
- 24px colored compact AI icon (indigo bars + amber sparkle) + `AI` text label
- Border: `1px solid var(--ai-color)` at rest
- Text: `var(--ai-color)` (#6366F1)
- Hover: light indigo fill `rgba(99, 102, 241, 0.08)`, border stays
- Active: slightly deeper fill `rgba(99, 102, 241, 0.16)`

**Size:**
- Height: 32px desktop / 36px mobile (meets 44px touch target with 4px vertical margin padding on parent)
- Minimum touch target: 44px (ensure via padding or wrapper)
- Padding: 6px 12px

**Placement:**
- Right-aligned inside the section header row
- On desktop: floated right with `float: right` or flex `justify-content: space-between` on header row
- On mobile: same row as section title — pill should never push title to second line (engineer: use `flex-wrap: nowrap` and truncate title if needed, or break to small breakpoints)

**Label:**
```html
<button class="btn ai-section-btn" aria-label="Ask AI about [Section Name]">
  <!-- 24px compact SVG inline -->
  <span aria-hidden="true">AI</span>
</button>
```

**Accessibility:**
- `aria-label="Ask AI about Macro Regime Score"` (or relevant section name)
- Icon SVG: `aria-hidden="true"` (decorative, button label is sufficient)
- Keyboard-accessible: standard button, Tab-focusable
- Focus outline: 2px solid `var(--ai-color)`, 2px offset

### Sections to Add AI Buttons

Every major homepage section and asset page:

| Section | Section ID | Chatbot Context |
|---------|------------|-----------------|
| Macro Regime Score | existing | Regime score, state, drivers |
| AI Market Briefing | existing | Current briefing text |
| Sector Tone | `#sector-tone-section` | All sector sentiment data |
| Market Conditions | existing | Key macro signals |
| What's Moving | `#movers-section` | Top movers data |
| Signals | `#signals-section` | Signal indicators |
| Recession Probability | existing | Model outputs, divergence |
| Global Trade Pulse | `#trade-pulse-section` | Trade balance, regime |
| Regime Implications | existing | Implications panel |

Asset pages (credit, equity, rates, dollar, crypto, safe-havens): add AI button to each page's asset header.

### Chatbot Pre-Load Behavior

When a section AI button is clicked:
1. Chatbot opens (same animation as FAB)
2. System prompt is injected with section context (engineer defines the context shape)
3. Chatbot immediately shows an explanatory opening message — not a blank prompt
4. Visual distinction between pre-loaded openings and blank openings is **not needed** — keep it simple

**Engineer note:** The `chatbot.js` already supports programmatic open. Engineer must define the API for passing section ID + data snapshot to the chatbot on open. Context injection goes into the system prompt; the AI's opening message should reference current data values (e.g., "You're looking at the Macro Regime Score — currently 62/100 (Risk-Off)...").

---

## Part 2 — Sentence-Level Drill-In (AI Briefing)

### User Flow

**Desktop:**
1. User reads AI daily briefing text
2. User selects any text (same as copy action)
3. Small floating pill appears 8px above selection: `[📋 Copy]  [✦ Ask AI]`
4. Clicking Copy: works normally (copies to clipboard)
5. Clicking Ask AI: sends selected text to chatbot as pre-loaded context, chatbot opens

**Mobile:**
1. User reads AI daily briefing text
2. User taps any sentence
3. 200ms amber background tint (`var(--ai-accent)`) confirms the tap
4. Confirm pill appears near tap point: `[✦ Ask AI about this]`
5. Tapping the pill opens chatbot with that sentence as context
6. Tapping elsewhere dismisses the confirm pill

### Interaction Details

**Desktop selection toolbar:**
```
╭────────────────────────────╮
│  📋 Copy   │   ✦ Ask AI   │
╰────────────────────────────╯
```
- Toolbar: white card, 1px neutral-200 border, 4px border-radius, subtle shadow
- Positioned: 8px above selection midpoint; shifts left/right to stay in viewport
- Disappears on: deselection, scroll, Escape key
- Copy button: plain text, `neutral-600`
- Ask AI button: `var(--ai-color)`, 16px mark icon + "Ask AI" label
- Divider: 1px `neutral-200` between the two buttons

**Mobile sentence tap:**
- Sentences wrapped in `<span class="ai-sentence">` by JavaScript at page load
- At-rest: no visual indicator (zero noise)
- On tap: `background-color: rgba(245, 158, 11, 0.2)` (amber-500 at 20% opacity), 4px border-radius — lasts 200ms then fades
- Confirm pill: white card, same styling as desktop toolbar, appears within 8px of tap point (centered horizontally), arrow indicator pointing at source sentence
- Pill content: `[✦ Ask AI about this]` — single button, full width
- Dismiss: tap outside → 150ms fade out

**Discoverability hint (always visible, below briefing block):**
```
Desktop:  ✦ Select any text to ask AI for more detail
Mobile:   ✦ Tap any sentence to explore with AI
```
- Rendered as a single line below the briefing card, outside the card border
- Style: `font-size: 12px; color: var(--neutral-500); margin-top: 8px;`
- 16px mark icon (sparkle, `var(--ai-accent)`) + hint text
- `pointer-coarse` media query controls which copy shows:
  ```css
  .ai-briefing-hint--desktop { display: block; }
  .ai-briefing-hint--mobile  { display: none;  }
  @media (pointer: coarse) {
    .ai-briefing-hint--desktop { display: none;  }
    .ai-briefing-hint--mobile  { display: block; }
  }
  ```

### Sentence Wrapping — Engineer Flag

**This must be decided before implementation begins.**

The JS that wraps `<span class="ai-sentence">` elements must handle:
- Abbreviations: U.S., vs., e.g., i.e., Fed., Jan., Feb.
- Dollar/percent numbers: $1.2T, 3.4%, +12bps
- Quoted sentences: "The Fed will..." — should be one unit
- Ellipsis: "..." is not a sentence boundary

**Options:**
1. **Regex** — simpler, faster; acceptable false-positive rate for financial prose
2. **NLP sentence tokenizer** (e.g., `compromise.js` or a Rust WASM tokenizer) — more accurate, adds bundle weight

Engineer must choose and document the decision in the implementation PR. Either approach is acceptable — the decision is theirs to make.

### Interaction Patterns Explicitly Rejected

Do not implement these (pre-decided):
- Inline `✦` icons at sentence ends — too noisy in dense financial prose
- Long-press on mobile — conflicts with OS native text selection
- Dotted underlines on all sentences — makes prose feel like a hyperlink list
- "Explore mode" toggle — friction kills discoverability

---

## Wireframes

### Section AI Button — Desktop Header Row

```
┌──────────────────────────────────────────────────────┐
│  MACRO REGIME SCORE                    [✦ AI]  ▼     │
├──────────────────────────────────────────────────────┤
│  ...section content...                               │
└──────────────────────────────────────────────────────┘
```

### Section AI Button — Mobile Header Row

```
┌────────────────────────────┐
│  MACRO REGIME SCORE [✦ AI] │ ← same row, flex layout
├────────────────────────────┤
│  ...section content...     │
└────────────────────────────┘
```

### Sentence Drill-In — Desktop (selection active)

```
                ╭────────────────────╮
                │ 📋 Copy │ ✦ Ask AI │
                ╰────────────────────╯
  ...the Fed is likely to hold rates steady through Q2,
  [as inflation remains above target]  ← selected text
  driven by services inflation in shelter and healthcare...
```

### Sentence Drill-In — Mobile (after tap)

```
  ...the Fed is likely to hold rates steady through Q2,
  [as inflation remains above target ← amber flash]
  driven by services inflation...

         ╭──────────────────────────╮
         │  ✦ Ask AI about this     │
         ╰──────────────────────────╯
```

### Discoverability Hint

```
  └─────────────────────────────────────────────────────┘
  ✦ Select any text to ask AI for more detail              ← below card, muted
```

---

## Responsive Behavior

| Breakpoint | Section AI Buttons | Sentence Drill-In |
|------------|-------------------|-------------------|
| 375px (mobile) | Ghost pill in header row; 36px height; 44px touch target | Two-step tap → amber flash → confirm pill |
| 768px (tablet) | Same as mobile but slightly more whitespace | Desktop selection toolbar |
| 1280px (desktop) | Same; full-width section headers give ample room for right-aligned button | Desktop selection toolbar |

---

## Accessibility Requirements

**Section AI Buttons:**
- `aria-label="Ask AI about [Section Name]"` on every button
- SVG icons: `aria-hidden="true"`
- Keyboard: Tab to button, Enter/Space to activate
- Focus: `outline: 2px solid var(--ai-color); outline-offset: 2px`

**Sentence Drill-In:**
- Desktop toolbar: `role="toolbar"`, Copy and Ask AI as `<button>` elements
- Mobile confirm pill: `role="dialog"` or `role="tooltip"` (engineer's choice), focusable, Escape dismisses
- Screen reader: announce toolbar via `aria-live` region when it appears? (optional — engineer judgment)
- Amber flash: visual-only affordance; does not need to be announced

**General:**
- Color contrast: `--ai-color` (#6366F1) on white = 4.54:1 ✅ (passes AA)
- `--ai-accent` (#F59E0B) on white = 2.93:1 — use only for decorative sparkle, never as sole text color

---

## Design System References

- New tokens: `--ai-color: #6366F1`, `--ai-accent: #F59E0B` (add to design-system.md Color System section)
- Typography: `font-size: 12px` (xs) for hint text, `neutral-500` color
- Spacing: 8px gaps within toolbar, 8px offset for floating toolbar above selection
- Touch targets: 44px minimum (section AI buttons, mobile confirm pill)
- Ghost button pattern: consistent with existing `.btn-outline-*` usage in app

---

## Implementation Notes

### User Story Split (recommended)

| Story | Scope |
|-------|-------|
| US-258.1 | AI icon migration — replace `bi-robot` in FAB, chatbot header, provenance badge; introduce SVG assets and CSS tokens |
| US-258.2 | Section AI buttons — add ghost pill to all major section headers; wire up chatbot pre-load with section context |
| US-258.3 | Sentence drill-in desktop — selection toolbar with Copy + Ask AI |
| US-258.4 | Sentence drill-in mobile — sentence wrapping, amber tap, confirm pill; includes engineer decision on sentence tokenizer |

Stories US-258.1 → US-258.2 must be completed in order (icon assets needed by buttons). US-258.3 and US-258.4 can be developed in parallel after US-258.2.
