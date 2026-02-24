# Feature 4.2: Chatbot Close vs. Minimize Button Behavior

**Issue:** #124
**Created:** 2026-02-24
**Status:** Draft
**Amends:** `docs/specs/feature-3.2-chatbot-mobile-redesign.md` (Section: Closing/Clearing the Chatbot)

---

## Overview

The chatbot header has two visually distinct controls (− and ×) that currently perform identical behavior (both minimize to the FAB). Distinct affordances must produce distinct outcomes. This spec establishes a **three-state model** that gives each button a clear, predictable role.

### The Problem

- Minimize (−) implies "shrink to taskbar" — accessible, compact, conversation persists
- Close (×) implies "dismiss this" — gone from view until user explicitly reopens
- Both doing the same thing erodes trust in the interface

### The Solution

Three chatbot states with clear visual distinction:

| State | How to Enter | Visual Result | Conversation |
|-------|-------------|---------------|--------------|
| Expanded | Tap FAB or Bottom Strip | Full panel visible | Active |
| Minimized | Tap − button | Compact bottom strip | Persists |
| Closed | Tap × button | FAB only (strip gone) | Persists |

---

## Three-State Model

### State 1: Expanded (unchanged from Feature 3.2)

Full panel open. No changes from existing spec.

### State 2: Minimized (via − button)

The panel collapses to a **compact bottom strip** — a slim, always-visible bar at the bottom of the viewport. This is the "chatbot is here, I'll use it again soon" state.

**Mobile (375px):**
```
┌─────────────────────────────────────┐
│  📊 Chart / page content            │
│                                     │
│                                     │
│                                     │
│                                     │
├─────────────────────────────────────┤
│ 💬  AI Chatbot              [3]  ▲  │ ← Bottom strip (48px)
└─────────────────────────────────────┘
```

**Tablet / Desktop (768px+):**
```
┌──────────────────────────┐
│  Page content            │
│                          │
│                          │
├────────────────┬─────────┤
│                │ 💬 AI Chatbot  [3]  ▲ │ ← Strip at panel base
└────────────────┴─────────────────────┘
                 ←── panel width ───→
```

#### Bottom Strip Specifications

- **Height:** 48px (touch-safe, exceeds 44px minimum)
- **Width:** Full viewport width on mobile; equal to panel width (360px tablet, 440px desktop) on tablet/desktop
- **Position:** `fixed; bottom: 0` — anchors to viewport bottom, no overlap with scrolling content
- **Background:** `neutral-800` (#1F2937) — dark, clearly distinct from the white panel and indigo FAB
- **Border:** 1px top border `neutral-600` (#4B5563)
- **Border radius:** None on mobile (full width flush to edges); 0 0 0 0 (square, it's flush to the bottom)

#### Bottom Strip Contents

Left-to-right layout:

1. **Chat icon** — 20px, white, `aria-hidden="true"`, left-padded 16px
2. **Label** — "AI Chatbot", `text-sm` (14px), 500 weight, white (#FFFFFF), margin-left 8px
3. **Unread badge** (when AI responds while minimized) — `danger-600` pill badge, same spec as FAB badge (see Feature 3.2 badge spec)
4. **Expand chevron (▲)** — rightmost, 24px, white, right-padded 16px, `aria-label="Expand chatbot"`

**Tap target:** Entire strip is tappable to expand (not just the chevron). The strip is a `<button>` with accessible label.

**FAB behavior when minimized:** The indigo FAB is **hidden** (`display: none`) when the chatbot is in the minimized (bottom strip) state. The strip IS the presence indicator and reopen trigger. No need for two triggers.

#### Unread Badge on Bottom Strip

When the AI responds while the chatbot is minimized:
- A badge appears on the right side of the label (before the expand chevron)
- Same spec as FAB badge: danger-600, white text, pill shape, count or "New"
- Clears when user expands the chatbot

---

### State 3: Closed (via × button)

The panel and the bottom strip are both hidden. **Only the floating trigger FAB remains** in the bottom-right corner. Conversation is preserved. The chatbot has low visual presence — it's out of the way until the user explicitly seeks it.

```
┌─────────────────────────────────────┐
│  📊 Chart / page content            │
│                                     │
│                              [💬]   │ ← FAB only (indigo, 64px)
└─────────────────────────────────────┘
  (No bottom strip)
```

**FAB behavior when closed:** The indigo FAB is visible (same as the existing "minimized" state in Feature 3.2). This is the same visual result as the current × behavior — the only change is that **the − button now produces the bottom strip state instead**.

**Reopening from closed:** User taps the FAB → panel expands with conversation restored. Panel goes directly to Expanded state (no bottom strip intermediate step).

---

## State Transitions

```
         ─── tap FAB or strip ───→
Closed                              Expanded
         ←── tap × button ──────
                                       ↕ tap − button / tap strip
                                    Minimized (Bottom Strip)
```

Full transition table:

| From | Action | To |
|------|--------|----|
| Closed | Tap FAB | Expanded |
| Minimized | Tap strip or ▲ | Expanded |
| Expanded | Tap − | Minimized (Bottom Strip) |
| Expanded | Tap × | Closed (FAB only) |
| Minimized | *(no direct × access)* | — |

**Note:** The × button is only accessible from the Expanded state (it lives in the panel header). There is no × on the bottom strip.

---

## Visual Design

### Bottom Strip Colors

| Element | Color Token | Hex |
|---------|------------|-----|
| Background | `neutral-800` | #1F2937 |
| Top border | `neutral-600` | #4B5563 |
| Icon + label | White | #FFFFFF |
| Expand chevron | White | #FFFFFF |
| Unread badge bg | `danger-600` | #DC2626 |
| Unread badge text | White | #FFFFFF |

**Contrast validation:**
- White on neutral-800: 14.7:1 (WCAG AAA ✅)
- danger-600 badge readable against neutral-800 background: distinct via color + number ✅

### Animation Sequences

**Minimize (panel → bottom strip):**
1. Panel slides down with `translateY(100%)` over 250ms ease-in-out
2. Simultaneously: Bottom strip fades in with `opacity: 0 → 1` over 200ms (starts at 50ms delay)
3. FAB fades out simultaneously with panel slide (opacity: 1 → 0, 150ms)
4. Result: Strip appears to "receive" the panel

**Close (panel → FAB only):**
1. Panel slides down with `translateY(100%)` over 250ms ease-in-out (same as current minimize)
2. FAB fades in with `opacity: 0 → 1` over 150ms (if not already visible)
3. No bottom strip

**Expand from bottom strip:**
1. Bottom strip fades out (opacity: 1 → 0, 150ms)
2. Panel slides up simultaneously (translateY: 100% → 0, 250ms)
3. Badge clears, focus moves to input field

---

## Wireframes

### Mobile — All Three States

```
CLOSED:                    MINIMIZED:                 EXPANDED:
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ Page content      │     │ Page content      │     │ Page content (50%)│
│                   │     │                   │     ├───────────────────┤
│                   │     │                   │     │━━━━━━━━━━━━━━━━━━│
│                   │     │                   │     │ AI Chatbot  [─][×]│
│            [💬]   │     ├───────────────────┤     ├───────────────────┤
│                   │     │💬 AI Chatbot [1] ▲│     │ Messages (scroll) │
└───────────────────┘     └───────────────────┘     ├───────────────────┤
                                                     │ Ask a question [↑]│
                                                     └───────────────────┘
```

### Tablet — Bottom Strip Position

```
MINIMIZED (768px+):
┌────────────────────┬────────────────────┐
│                    │                    │
│  Page content      │                    │
│                    │  (panel area,      │
│                    │   empty)           │
│                    │                    │
│             [💬]   ├────────────────────┤
└────────────────────│ 💬 AI Chatbot   ▲  │
                     └────────────────────┘
                      ←─── 360px ────────→
```

---

## Accessibility Requirements

### ARIA for Bottom Strip

```html
<button
  id="chatbot-strip"
  class="chatbot-strip"
  aria-label="AI Chatbot — tap to expand"
  aria-expanded="false"
  hidden>
  <svg aria-hidden="true" class="chatbot-strip-icon"><!-- chat icon --></svg>
  <span class="chatbot-strip-label">AI Chatbot</span>
  <span class="chatbot-strip-badge" aria-label="1 new message" hidden></span>
  <svg aria-hidden="true" class="chatbot-strip-chevron"><!-- ▲ --></svg>
</button>
```

### Updated FAB States

```html
<!-- In Closed state: FAB visible, strip hidden -->
<!-- In Minimized state: FAB hidden, strip visible -->
<!-- In Expanded state: both FAB and strip hidden; panel visible -->
```

### Screen Reader Announcements

| Action | Announcement |
|--------|-------------|
| Tap − to minimize | "AI Chatbot minimized" |
| Tap × to close | "AI Chatbot closed" |
| Tap strip to expand | "AI Chatbot opened" |
| Tap FAB to expand | "AI Chatbot opened" |

### Keyboard Navigation

- `Escape` when expanded: Minimize (−) behavior → goes to bottom strip state
- `Tab` order in bottom strip: Strip is a single tabbable button (all one target)
- Touch target: Full 48px strip height, full width ✅

---

## Responsive Behavior

| Breakpoint | Bottom Strip | FAB (Closed) |
|------------|-------------|--------------|
| Mobile (< 768px) | Full width, bottom: 0 | 64px, bottom-right: 16px |
| Tablet (768–1023px) | 360px wide, bottom-right (aligns with panel) | 64px, bottom-right: 16px |
| Desktop (≥ 1024px) | 440px wide, bottom-right (aligns with panel) | 64px, bottom-right: 16px |

On tablet/desktop, the strip is positioned so it aligns with the panel location (right side of viewport).

---

## Changes to Feature 3.2 Spec

This spec **amends** Feature 3.2. The following behavior changes:

| Element | Feature 3.2 (Old) | This Spec (New) |
|---------|-------------------|-----------------|
| − button | Minimizes to FAB | Minimizes to bottom strip |
| × button | Minimizes to FAB (same as −) | Closes to FAB only |
| Minimized visual | FAB in bottom-right | Bottom strip (48px, dark) |
| FAB role | Only visible thing when minimized | Only visible thing when CLOSED |
| `aria-label` on × | "Close and clear conversation" | "Close chatbot" |
| `aria-label` on − | "Minimize chatbot" | "Minimize chatbot" (unchanged) |

All other Feature 3.2 behavior (animations, conversation persistence, badge, clear conversation, performance banner, responsiveness) is unchanged.

---

## Implementation Notes

- Engineer: Add `chatbot-strip` element to HTML (alongside existing FAB and panel)
- Engineer: Add three-state management: `closed` | `minimized` | `expanded` — replaces binary open/closed
- Engineer: On − click: hide panel, hide FAB, show strip (transition as described)
- Engineer: On × click: hide panel, hide strip, show FAB (existing behavior)
- Engineer: On strip tap: hide strip, show panel, focus input (same as existing FAB tap when closed)
- Engineer: FAB tap when in `closed` state: existing open behavior
- CSS: Add `.chatbot-strip` component styles; update FAB visibility logic based on state
- No backend changes required; this is entirely a frontend state management change

---

## Design System References

- Colors: `neutral-800`, `neutral-600`, `danger-600` — see design-system.md
- Typography: `text-sm` (14px), weight 500 — see design-system.md
- Spacing: `space-4` (16px) padding — see design-system.md
- Touch targets: 48px minimum — see design-system.md Accessibility Standards
- Animations: 250ms ease-in-out — see Feature 3.2 spec
