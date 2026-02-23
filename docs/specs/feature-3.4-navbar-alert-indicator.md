# Navbar Alert Indicator Design Spec

**Issue:** #109
**Feature:** 3.4 — Visible Alert Indicator in Navbar
**Created:** 2026-02-23
**Status:** Draft

## Overview

Add a persistent bell icon with unread-count badge to the top-level navbar so users can see unread alerts at a glance — without opening any dropdown. The indicator must be visible on all screen sizes, including the collapsed mobile navbar, and link directly to `/alerts`.

**Problem being solved:** Unread alerts currently appear as a badge inside the account dropdown, which requires two taps on mobile to discover. Time-sensitive macro alerts (VIX spikes, yield curve inversions, credit spread widening) are getting missed, eroding trust in the alert system.

**Backend context:** The `unread_alert_count` context variable is already provided to all templates — this is a template + CSS change only.

---

## User Flow

1. User receives a new alert (unread count > 0)
2. User loads any page — bell icon with badge is immediately visible in the navbar
3. User taps/clicks the bell icon
4. User is taken directly to `/alerts` page (no intermediate step)
5. After viewing alerts, unread count returns to 0 — badge disappears; bell remains

---

## Wireframes

### Mobile (collapsed navbar, ≤1023px)

The bell icon appears between the brand and the hamburger button — always visible without expanding the menu.

```
┌──────────────────────────────────────────────┐
│  ⟨⟩ SignalTrackers    🔔²    ≡               │
└──────────────────────────────────────────────┘
  ^brand                ^bell  ^hamburger
```

Where `²` is the unread badge. When 0 unread:

```
┌──────────────────────────────────────────────┐
│  ⟨⟩ SignalTrackers    🔔     ≡               │
└──────────────────────────────────────────────┘
```

### Desktop (expanded navbar, 1024px+)

Bell icon appears in the right-side nav group, before the account dropdown.

```
┌──────────────────────────────────────────────────────────────────┐
│  ⟨⟩ SignalTrackers   Dashboard  Markets ▾  Explorer   Portfolio  │
│                                              🕐 Loading  🔔²  👤 ▾│
└──────────────────────────────────────────────────────────────────┘
```

When 0 unread (badge hidden):
```
                                              🕐 Loading  🔔   👤 ▾
```

---

## Component Specifications

### Bell Icon Button

**Element:** `<a>` tag styled as a nav-link
**Target:** `/alerts`
**Icon:** `bi bi-bell` (Bootstrap Icons)
**Tooltip:** `title="View Alerts"` (browser tooltip on hover)

**States:**
| State | Appearance |
|-------|------------|
| Default (0 unread) | Bell icon at 75% white opacity (Bootstrap navbar-dark default) |
| Unread alerts (>0) | Bell icon at full white (100% opacity) to draw attention |
| Active (on /alerts page) | Full white + Bootstrap `active` class |
| Hover | Full white (100% opacity), 150ms transition |

**Always visible:** Must be placed **outside** the Bootstrap `.collapse.navbar-collapse` div so it renders in the always-visible navbar bar on mobile.

### Badge

The badge overlays the top-right corner of the bell icon.

**Visual spec:**
- Shape: Circle
- Size: 16px × 16px minimum (to meet touch/visual legibility threshold)
- Maximum: Cap display at 9+ for counts ≥ 10 (e.g., "9+")
- Background: `danger-600` (#DC2626)
- Text color: White (#FFFFFF)
- Font size: 10px, font-weight: 700
- Position: `top: -5px; right: -6px` (relative to bell icon wrapper)
- Border: `2px solid` navbar background color (creates visual separation between badge and navbar bg)
  - Mobile/desktop dark navbar: `2px solid #212529` (Bootstrap bg-dark)

**When to show:**
- `unread_alert_count > 0`: Badge visible
- `unread_alert_count === 0`: Badge hidden (`display: none` or conditional Jinja2)

**Count display:**
- 1–9: Show actual count
- 10+: Show "9+" (prevents badge from expanding and looking awkward)

**Example:**
```
    ●²   ← badge (16px danger circle, top-right)
   🔔    ← bell icon (Bootstrap Icons bi-bell)
```

### Bell Wrapper (positioning container)

The bell icon + badge need a relative-positioned wrapper for badge overlay:

```
.navbar-bell-btn {
  position: relative;   ← anchor for badge
  display: inline-flex;
  padding: (inherits nav-link padding)
}
.navbar-bell-badge {
  position: absolute;
  top: 5px;  right: 5px;  ← adjusted by engineer to suit actual icon dimensions
}
```

---

## Interaction Patterns

- **Click/tap:** Navigate to `/alerts` (standard link, no JavaScript needed)
- **No dropdown:** This is a direct link, not a dropdown trigger
- **No dismiss interaction:** Badge clears when backend marks alerts read on the alerts page
- **Hover (desktop):** 150ms opacity transition to full white

---

## Placement Details

### HTML Placement

The bell icon must be **outside** the `.collapse.navbar-collapse` div.

Recommended: Place a flex wrapper containing the bell (and keeping the hamburger toggler) between the brand container and the collapse div. This keeps mobile behavior correct.

Suggested structure (implementation detail for Engineer):
```
<nav>
  <div class="container-fluid">
    [brand]

    <!-- Always-visible right group (bell + toggler) -->
    <div class="d-flex align-items-center ms-auto me-0">
      {% if current_user.is_authenticated %}
      [bell icon]
      {% endif %}
      [hamburger toggler]
    </div>

    <!-- Collapsible nav (desktop) -->
    <div class="collapse navbar-collapse">
      [left nav links]
      [right nav: clock | account dropdown]
      <!-- Bell is NOT duplicated here -->
    </div>
  </div>
</nav>
```

On desktop (1024px+), the hamburger is hidden by Bootstrap by default, so the wrapper contains only the bell icon, which sits to the right of all the collapsed nav content.

On mobile, the wrapper renders between the brand and the hamburger: `[Brand] [Bell] [Hamburger]`.

### Visual Position

| Screen Size | Bell Position |
|------------|---------------|
| Mobile (≤1023px, collapsed) | Right of brand, left of hamburger |
| Desktop (1024px+, expanded) | Right nav group, between clock and account dropdown |

---

## Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| 0–1023px (mobile, collapsed nav) | Bell visible in top navbar bar between brand and hamburger |
| 1024px+ (desktop, expanded nav) | Bell visible in expanded right nav — hamburger hidden, bell remains |

**No breakpoint-based hiding/showing** — the bell is always visible at all viewport widths. One implementation, no `d-lg-none` / `d-none d-lg-flex` duplicates needed.

---

## Accessibility Requirements

- **Link label:** `aria-label="Alerts{% if unread_alert_count > 0 %}, {{ unread_alert_count }} unread{% endif %}"` on the `<a>` element
  - Screen readers announce: "Alerts, 3 unread" or just "Alerts"
- **Badge:** `aria-hidden="true"` — count is already in the aria-label, avoids double-announcement
- **Touch target:** The bell link's touch/click target must be ≥44×44px (wrap with padding to ensure this)
  - Recommended: `padding: 10px 12px` on the nav-link anchor
- **Keyboard navigation:** Bell icon participates in Tab order; must have visible focus ring (Bootstrap's default `outline` is acceptable in the navbar context)
- **Color independence:** Badge uses both color (danger red) AND a numeric label — not color-only

### Focus Indicator
Bootstrap's default focus outline is acceptable for the navbar dark context. Do not suppress `outline: none` on the bell link.

---

## Design System References

- **Danger color:** `danger-600` (#DC2626) — see [design-system.md — Semantic Colors](../design-system.md#semantic-colors-signal--status)
- **Typography:** Badge text at 10px/700 — smallest legible size at this scale
- **Spacing:** `space-1` (4px) padding around badge text; nav-link padding inherits Bootstrap defaults
- **Icon library:** Bootstrap Icons v1.x — `bi bi-bell` (matches all other navbar icons)
- **Touch targets:** 44px minimum — see [design-system.md — Accessibility Standards](../design-system.md#accessibility-standards)

---

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User not authenticated | Bell icon not rendered (alerts are user-specific) |
| 0 unread alerts | Bell visible, badge hidden |
| 1–9 unread alerts | Bell + badge with exact count |
| 10+ unread alerts | Bell + badge shows "9+" |
| On /alerts page | Bell has Bootstrap `active` class (full-white treatment) |
| Very small screen (320px) | Bell + hamburger fit; brand text may truncate (acceptable) |

---

## What This Spec Does NOT Cover

- Alert preview on hover/click (no dropdown menu — direct link only)
- Real-time badge updates via WebSocket (out of scope — badge reflects page-load count)
- Animated bell animation (out of scope — static icon is sufficient)
- The existing badge inside the account dropdown (keep as secondary reinforcement per issue #109)
