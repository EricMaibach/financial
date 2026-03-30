# Pricing & Checkout Flow Design Spec

**Issue:** #413
**Created:** 2026-03-29
**Status:** Draft

## Overview

The single conversion path from visitor to paying subscriber. A pricing/sales page communicates the value of subscribing at $19/mo, then hands off to Stripe Checkout for payment. The existing Phase 12 registration page evolves into this pricing page — same location in the information architecture, elevated purpose.

**User problem:** Anonymous visitors who've experienced AI features and hit their limits need a clear, low-friction path to become paid subscribers.

**Marketing line:** "Free gives you the macro picture. Paid makes it personal."

## User Flow

1. User arrives at `/pricing` — either directly (nav link) or via redirect from an AI limit
2. User reads value proposition and feature comparison
3. User clicks "Subscribe — $19/month" CTA
4. System creates a Stripe Checkout session and redirects to Stripe's hosted page
5. User completes payment on Stripe (email + card collected by Stripe)
6. Stripe redirects user back to app with success state
7. User receives "Set your password" email
8. User sets password and logs in for the first time

## Wireframes

### Mobile (375px)

```
┌─────────────────────────────┐
│  <navbar>                   │
├─────────────────────────────┤
│                             │
│  [graph-up-arrow icon]      │
│                             │
│  Unlock the Full Power of   │
│  SignalTrackers              │
│                             │
│  "Free gives you the macro  │
│   picture. Paid makes it    │
│   personal."                │
│                             │
│  ┌─ context banner ───────┐ │  ← Only if ?from= param
│  │ "Continue asking AI    │ │
│  │  about your portfolio" │ │
│  └────────────────────────┘ │
│                             │
│  ╔═══════════════════════╗  │
│  ║  $19 /month           ║  │
│  ║                       ║  │
│  ║  ✓ Unlimited AI chat  ║  │
│  ║  ✓ Portfolio tracking ║  │
│  ║  ✓ Daily briefing     ║  │
│  ║  ✓ Smart alerts       ║  │
│  ║                       ║  │
│  ║  [Subscribe — $19/mo] ║  │  ← Primary CTA, full width
│  ╚═══════════════════════╝  │
│                             │
│  ── What's included ──────  │
│                             │
│  FREE          │  PAID      │
│  ─────────────────────────  │
│  Dashboard ✓   │  ✓         │
│  Charts ✓      │  ✓         │
│  AI trial ✓    │  Unlimited │
│  Portfolio ✗   │  ✓         │
│  Briefing ✗    │  ✓         │
│  Alerts ✗      │  ✓         │
│                             │
│  Already have an account?   │
│  Login here                 │
│                             │
└─────────────────────────────┘
```

### Desktop (1024px+)

Two-column layout within a centered container (`col-lg-8`):

```
┌──────────────────────────────────────────────────────────────────┐
│  <navbar>                                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│              [graph-up-arrow icon]                                │
│              Unlock the Full Power of SignalTrackers              │
│              "Free gives you the macro picture.                   │
│               Paid makes it personal."                           │
│                                                                  │
│         ┌─ context banner (if ?from= param) ───────────────┐     │
│         │ "You were asking AI about credit markets —       │     │
│         │  subscribe to keep the conversation going."      │     │
│         └──────────────────────────────────────────────────┘     │
│                                                                  │
│    ┌─── Feature Comparison ───────┬─── Subscribe Card ─────┐     │
│    │                              │                        │     │
│    │  FREE          PAID          │  $19 /month            │     │
│    │  ──────────────────────      │                        │     │
│    │  Dashboard ✓    ✓            │  Everything you need   │     │
│    │  All charts ✓   ✓            │  for smarter macro     │     │
│    │  AI trial ✓     Unlimited    │  investing.            │     │
│    │  Portfolio ✗    ✓            │                        │     │
│    │  Briefing ✗     ✓            │  [Subscribe — $19/mo]  │     │
│    │  Alerts ✗       ✓            │                        │     │
│    │                              │  Cancel anytime.       │     │
│    └──────────────────────────────┴────────────────────────┘     │
│                                                                  │
│              Already have an account? Login here                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### Page Header (Value Proposition)

- **Icon:** `bi-graph-up-arrow` in `brand-blue-500`, decorative (`aria-hidden="true"`)
- **Heading:** H2, `text-3xl` (mobile) / `text-4xl` (desktop), `neutral-800`, `fw-bold`
- **Tagline:** `text-lg`, `neutral-500`, italic
- **Alignment:** Center-aligned, max-width `container-md` (768px)

### Context Banner

Shown only when `?from=` query parameter is present. Reflects what the user was doing when they hit the AI limit.

- **Container:** `brand-blue-100` background, `border-radius: 8px`, `space-4` padding
- **Icon:** `bi-info-circle` in `brand-blue-500`
- **Text:** `text-base`, `neutral-700`
- **Context messages by parameter:**
  - `?from=chatbot` → "You were chatting with your AI market analyst — subscribe to keep the conversation going."
  - `?from=portfolio-ai` → "You were getting AI insights on your portfolio — subscribe for unlimited analysis."
  - `?from=section-ai&section=credit` → "You were exploring credit market AI insights — subscribe to unlock all sections."
  - `?from=section-ai&section=equity` → (same pattern, swap section name)
  - No parameter → banner hidden

### Subscribe Card

The primary conversion element. Elevated card treatment.

- **Card:** White background, `border-radius: 8px`, `box-shadow: 0 4px 12px rgba(0,0,0,0.1)` (elevated)
- **Price:** `text-4xl`, `neutral-800`, `fw-bold`, monospace for the number. "$19" large, "/month" in `text-base`, `neutral-500`
- **Feature list:** Checkmark list with `bi-check-circle-fill` in `success-600`
  - "Unlimited AI-powered analysis" (50 chatbot/day, 10 portfolio/day, 25 section/day — feels unlimited)
  - "Portfolio tracking & insights"
  - "Daily market briefing email"
  - "Smart market alerts"
- **CTA button:** Large primary button (52px height, `text-lg`, `fw-bold`)
  - Label: "Subscribe — $19/month"
  - Full width on mobile, auto width on desktop (min 280px)
  - `brand-blue-500` background, standard hover/active states
- **Reassurance text:** Below CTA, `text-sm`, `neutral-500`: "Cancel anytime. No commitment."
- **States:**
  - Default: as described
  - Loading (after click): Button shows spinner, disabled, "Redirecting to checkout..."

### Feature Comparison Table

Simple two-column comparison. Not a complex matrix.

- **Layout:** Mobile: stacked rows with labels. Desktop: side-by-side table
- **Headers:** "Free" in `neutral-600`, "Paid" in `brand-blue-500`, `text-sm`, `fw-bold`, uppercase
- **Rows:**
  | Feature | Free | Paid |
  |---------|------|------|
  | Market dashboard | ✓ | ✓ |
  | All charts & data | ✓ | ✓ |
  | AI chat & analysis | Limited trial | Unlimited |
  | Portfolio tracking | — | ✓ |
  | Daily briefing email | — | ✓ |
  | Smart alerts | — | ✓ |
- **Check icon:** `bi-check-lg` in `success-600` for included, `bi-dash` in `neutral-300` for not included
- **"Unlimited" badge:** `success-100` background, `success-700` text, pill badge
- **"Limited trial" badge:** `warning-100` background, `warning-700` text, pill badge

### Login Link

- Below the main content, centered
- `text-sm`, `neutral-500` text with `brand-blue-500` link
- "Already have an account? [Login here]"

## Interaction Patterns

- **CTA click:** Creates Stripe Checkout session via POST/AJAX, then redirects. Button shows loading state immediately on click.
- **Success return:** After Stripe checkout completes, user returns to a `/pricing/success` or similar route showing a success state: "Welcome to SignalTrackers! Check your email to set your password."
- **Abandoned checkout:** User clicks browser back from Stripe → returns to pricing page, no state change.
- **Scroll behavior:** Page should fit above the fold on desktop. On mobile, CTA should be visible within first screenful (before comparison table).

## Success State (Post-Checkout Return)

```
┌─────────────────────────────┐
│                             │
│  [check-circle icon]        │
│                             │
│  Welcome to SignalTrackers! │
│                             │
│  Check your email to set    │
│  your password and start    │
│  exploring.                 │
│                             │
│  [Go to Dashboard]          │
│                             │
└─────────────────────────────┘
```

- **Icon:** `bi-check-circle-fill` in `success-600`, 48px
- **Heading:** H2, `neutral-800`
- **Body:** `text-base`, `neutral-600`
- **CTA:** Primary button → homepage

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|---------------|
| 375px (mobile) | Single column. Subscribe card → comparison table stacked vertically. CTA full-width. |
| 640px (sm) | Benefit badges go horizontal (flex-row) |
| 768px (md) | Feature comparison becomes a proper table |
| 1024px (lg) | Two-column layout: comparison left, subscribe card right. Card is sticky within viewport. |

## Accessibility Requirements

- Color contrast: All text meets 4.5:1 minimum. Check/dash icons paired with text labels (not color alone).
- Touch targets: CTA button 52px minimum height. Login link has adequate tap area.
- Keyboard navigation: Tab order: context banner → subscribe card CTA → comparison table → login link
- Screen reader: `aria-label` on CTA ("Subscribe to SignalTrackers for nineteen dollars per month"). Feature comparison table uses proper `<table>` with `<th>` headers. Context banner uses `role="status"`.
- Focus: Visible focus ring on all interactive elements per design system.

## Design System References

- Colors: `brand-blue-500` (CTA, accents), `success-600` (check icons), `neutral-*` (text hierarchy)
- Typography: `text-4xl` (price), `text-3xl`/`text-4xl` (heading), `text-base` (body), `text-sm` (captions)
- Components: Primary button (large variant, 52px), standard card (elevated variant), status badges (success, warning)
- Spacing: `space-6` card padding, `space-8` between sections, `space-12` page sections

## Navigation Changes

- Replace "Register" nav link with "Pricing" (same position in navbar)
- Route changes: `/register` redirects to `/pricing`
- Existing links to `/register` throughout the app should be updated to `/pricing`
