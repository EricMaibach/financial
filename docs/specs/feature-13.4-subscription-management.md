# Subscription Management Design Spec

**Issue:** #416
**Created:** 2026-03-29
**Status:** Draft

## Overview

A simple account page that shows subscribers their current subscription status and provides a link to Stripe's hosted Customer Portal for managing payment, cancellation, and billing history. Stripe handles the complexity — our page is a lightweight status display and portal launcher.

**User problem:** Paying subscribers need to know their subscription status and have an obvious way to manage it (cancel, update payment, view invoices) without contacting support.

## User Flow

### View Account Status
1. Logged-in subscriber clicks "Account" in the navbar
2. Account page displays current subscription status, plan details, and billing period
3. User reads their status — no action needed

### Manage Subscription
1. User clicks "Manage Subscription" button on account page
2. System creates a Stripe Customer Portal session and redirects to Stripe's hosted portal
3. User manages their subscription (cancel, update payment, view invoices) on Stripe
4. Stripe redirects user back to account page

### Cancellation Flow
1. User cancels via Stripe Portal
2. Returns to account page → status shows "Canceling" with end date
3. Access continues until billing period ends
4. After end date, user is downgraded to anonymous experience

## Wireframes

### Mobile (375px) — Active Subscriber

```
┌─────────────────────────────┐
│  <navbar>                   │
├─────────────────────────────┤
│                             │
│  Account                    │
│                             │
│  ┌─ Subscription ─────────┐ │
│  │                        │ │
│  │  ● Active              │ │  ← Green dot + badge
│  │                        │ │
│  │  Plan: SignalTrackers   │ │
│  │  Price: $19/month       │ │
│  │  Next billing: Apr 29   │ │
│  │                        │ │
│  │  [Manage Subscription]  │ │  ← Secondary button → Stripe Portal
│  │                        │ │
│  └────────────────────────┘ │
│                             │
│  ┌─ Account Details ──────┐ │
│  │                        │ │
│  │  Email: user@email.com │ │
│  │  Username: johndoe     │ │
│  │  Member since: Mar 29  │ │
│  │                        │ │
│  │  [Change Password]     │ │  ← Ghost button
│  │                        │ │
│  └────────────────────────┘ │
│                             │
│  [Log Out]                  │  ← Danger ghost button
│                             │
└─────────────────────────────┘
```

### Mobile (375px) — Canceling (Grace Period)

```
┌─────────────────────────────┐
│                             │
│  ┌─ Subscription ─────────┐ │
│  │                        │ │
│  │  ◐ Canceling           │ │  ← Warning-amber dot + badge
│  │                        │ │
│  │  Your subscription     │ │
│  │  ends on Apr 29, 2026. │ │
│  │  You'll have full      │ │
│  │  access until then.    │ │
│  │                        │ │
│  │  [Resubscribe]         │ │  ← Primary button → Stripe Portal
│  │  [Manage Subscription] │ │  ← Ghost button → Stripe Portal
│  │                        │ │
│  └────────────────────────┘ │
│                             │
└─────────────────────────────┘
```

### Mobile (375px) — Past Due (Payment Failed)

```
┌─────────────────────────────┐
│                             │
│  ┌─ Subscription ─────────┐ │
│  │                        │ │
│  │  ⚠ Payment Issue       │ │  ← Danger-red dot + badge
│  │                        │ │
│  │  Your last payment     │ │
│  │  didn't go through.    │ │
│  │  Please update your    │ │
│  │  payment method to     │ │
│  │  keep your access.     │ │
│  │                        │ │
│  │  [Update Payment →]    │ │  ← Primary button → Stripe Portal
│  │                        │ │
│  └────────────────────────┘ │
│                             │
└─────────────────────────────┘
```

### Desktop (1024px+)

Centered single-column layout within `container-sm` (640px). Same card structure as mobile but with more breathing room.

```
┌──────────────────────────────────────────────────────────────────┐
│  <navbar>                                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                   Account                                        │
│                                                                  │
│         ┌─ Subscription ──────────────────────────────┐          │
│         │                                             │          │
│         │  ● Active              $19/month            │          │
│         │                                             │          │
│         │  Plan: SignalTrackers                        │          │
│         │  Next billing date: April 29, 2026          │          │
│         │                                             │          │
│         │                    [Manage Subscription]     │          │
│         └─────────────────────────────────────────────┘          │
│                                                                  │
│         ┌─ Account Details ───────────────────────────┐          │
│         │                                             │          │
│         │  Email        user@email.com                │          │
│         │  Username     johndoe                       │          │
│         │  Member since March 29, 2026                │          │
│         │                                             │          │
│         │                    [Change Password]         │          │
│         └─────────────────────────────────────────────┘          │
│                                                                  │
│                          [Log Out]                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### Subscription Status Card

The primary element on the account page.

- **Card:** Standard card, white background, `neutral-200` border, `border-radius: 8px`, `space-6` padding
- **Status indicator:** Colored dot (8px circle) + status badge
  | Status | Dot Color | Badge | Badge Style |
  |--------|-----------|-------|-------------|
  | Active | `success-600` | "Active" | `success-100` bg, `success-700` text |
  | Past Due | `danger-600` | "Payment Issue" | `danger-100` bg, `danger-700` text |
  | Canceling | `warning-600` | "Canceling" | `warning-100` bg, `warning-700` text |
- **Plan name:** "SignalTrackers" — `text-base`, `neutral-700`
- **Price:** "$19/month" — `text-base`, `neutral-700`, `fw-semibold`. Displayed on same line as status badge on desktop.
- **Billing date:** "Next billing date: [date]" — `text-sm`, `neutral-500`
- **Cancellation end date:** "Your subscription ends on [date]. You'll have full access until then." — `text-base`, `neutral-600`
- **Past due message:** "Your last payment didn't go through. Please update your payment method to keep your access." — `text-base`, `danger-700`

### Manage Subscription Button

- **Active state:** Secondary button per design system (outlined, `brand-blue-500`)
- **Canceling state:** Two buttons:
  - "Resubscribe" — Primary button (`brand-blue-500` background)
  - "Manage Subscription" — Ghost button
- **Past due state:** "Update Payment →" — Primary button
- **Behavior:** POST to create Stripe Portal session, then redirect. Button shows loading state on click.
- **Min-width:** 200px on desktop, full-width on mobile

### Account Details Card

- **Card:** Standard card, same styling as subscription card
- **Fields:** Label-value pairs in a definition list (`<dl>`)
  - Label: `text-sm`, `neutral-500`, `fw-semibold`, uppercase
  - Value: `text-base`, `neutral-700`
- **Fields shown:**
  - Email
  - Username
  - Member since (date user account was created)
- **Change Password:** Ghost button, bottom of card

### Log Out Button

- **Style:** Ghost button with `danger-600` text color
- **Position:** Below account details card, centered
- **Size:** Standard (44px min-height)

## Interaction Patterns

- **Portal redirect:** On "Manage Subscription" click, button shows spinner + "Redirecting..." text. Server creates portal session and returns redirect URL. Browser navigates to Stripe.
- **Portal return:** After Stripe Portal actions, user returns to `/account`. Page loads fresh data reflecting any changes made in the portal.
- **No inline editing:** Account details (email, username) are read-only on this page. Password change navigates to a separate flow.
- **Status refresh:** When page loads, subscription status is fetched fresh from the database (which is kept in sync by Stripe webhooks).

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|---------------|
| 375px (mobile) | Full-width cards, stacked vertically. Buttons full-width. Status badge wraps below status dot if needed. |
| 640px (sm) | Status badge and price on same line. Buttons auto-width. |
| 768px (md) | Cards within centered container (max-width 640px). More padding. |
| 1024px (lg) | Same as md — this page doesn't need wide layout. |

## Accessibility Requirements

- Color contrast: Status badges use high-contrast color pairs (e.g., `success-700` on `success-100` = 4.8:1). Past due message in `danger-700` on white background.
- Touch targets: All buttons 44px minimum height. Log out button has adequate spacing from other elements.
- Keyboard navigation: Tab order: subscription card actions → account details → change password → log out. Focus trapped appropriately during loading states.
- Screen reader: Status badge has `aria-label` ("Subscription status: Active"). Dates use `<time>` element with `datetime` attribute. Definition list for account details provides proper semantics. Loading state announced via `aria-live="polite"`.

## Design System References

- Colors: `success-*` (active status), `warning-*` (canceling), `danger-*` (past due), `neutral-*` (text hierarchy)
- Typography: `text-base` (body), `text-sm` (labels, captions), `text-lg` (page heading)
- Components: Standard card, secondary button, ghost button, status badges
- Spacing: `space-6` card padding, `space-8` between cards, `space-4` within card sections

## Navigation Changes

- Add "Account" link to navbar for logged-in users (replaces or supplements "Settings" if it exists)
- Route: `/account`
- Only visible to authenticated users
- Position: Right side of navbar, near user menu / logout
