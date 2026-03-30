# Upgrade Prompts Design Spec

**Issue:** #414
**Created:** 2026-03-29
**Status:** Draft

## Overview

When anonymous users exhaust their AI trial budget, guide them to the pricing page with context-aware, inline messaging. Phase 12 built the redirect infrastructure — this feature updates the destination from `/register` to `/pricing` and enhances the in-context messaging to feel helpful rather than jarring.

**User problem:** The moment a user hits their AI limit is the highest-intent moment in the funnel. The transition from "free trial exhausted" to "here's how to continue" must feel like a helpful suggestion, not a paywall slap.

**Design principle:** Inline messages first, redirect second. Show the user what happened and give them a choice, rather than hard-redirecting away from what they were doing.

## User Flows

### Chatbot Limit Flow
1. User sends a message in the chatbot
2. System detects session limit reached
3. Chatbot displays an inline upgrade message in the chat thread (not a redirect)
4. User clicks subscribe link → navigates to `/pricing?from=chatbot`

### Section AI Limit Flow
1. User clicks a Section AI / drill-in button
2. System detects session limit reached
3. Button becomes disabled with upgrade tooltip
4. User clicks disabled button → navigates to `/pricing?from=section-ai&section={name}`

### Portfolio AI Limit Flow
1. User triggers portfolio AI analysis
2. System detects session limit reached
3. Portfolio AI area shows inline upgrade message
4. User clicks subscribe link → navigates to `/pricing?from=portfolio-ai`

### Global Daily Cap Flow
1. Any AI request is made
2. System detects global anonymous daily cap reached
3. Response includes redirect URL to `/pricing` (existing Phase 12 behavior, updated destination)

## Wireframes

### Chatbot Inline Upgrade Message

```
┌─ Chat thread ──────────────────────┐
│                                    │
│  [User message bubble]             │
│  "What's the outlook for credit?"  │
│                                    │
│  ┌─ Upgrade message ────────────┐  │
│  │ ✦ You've used your free AI   │  │
│  │   messages for this session. │  │
│  │                              │  │
│  │   Subscribe for unlimited    │  │
│  │   AI-powered market          │  │
│  │   analysis.                  │  │
│  │                              │  │
│  │   [Subscribe — $19/mo →]     │  │
│  └──────────────────────────────┘  │
│                                    │
│  ┌──────────────────────────────┐  │
│  │  Message input (disabled)    │  │
│  │  "Subscribe to continue..." │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

### Section AI Disabled Button State

```
Before limit:
  [✦ Ask AI about this signal]     ← Active, brand-blue

After limit:
  [✦ Ask AI — Subscribe to unlock] ← Disabled, neutral-300
                                      Tooltip on hover/tap:
                                      "Free AI trial used.
                                       Subscribe for $19/mo →"
```

### Portfolio AI Inline Upgrade Message

```
┌─ Portfolio Analysis Area ──────────┐
│                                    │
│  ┌─ Upgrade card ───────────────┐  │
│  │  ✦ AI Portfolio Analysis     │  │
│  │                              │  │
│  │  You've used your free       │  │
│  │  portfolio analysis for this │  │
│  │  session.                    │  │
│  │                              │  │
│  │  Subscribe to get unlimited  │  │
│  │  AI insights on your         │  │
│  │  portfolio.                  │  │
│  │                              │  │
│  │  [Subscribe — $19/mo →]      │  │
│  └──────────────────────────────┘  │
│                                    │
└────────────────────────────────────┘
```

## Component Specifications

### Chatbot Upgrade Message

Appears as a system message in the chat thread, visually distinct from AI responses.

- **Container:** `brand-blue-100` background, `border-radius: 8px`, `space-4` padding, `space-3` margin-top
- **Icon:** AI sparkle mark (✦) in `--ai-color` (#6366F1)
- **Heading:** "You've used your free AI messages for this session." — `text-sm`, `neutral-700`, `fw-semibold`
- **Body:** "Subscribe for unlimited AI-powered market analysis." — `text-sm`, `neutral-600`
- **CTA link:** "Subscribe — $19/mo →" — `text-sm`, `fw-semibold`, `brand-blue-500`, inline link (not a button — lighter touch)
- **Behavior:** Message appended to chat thread, scrolled into view. Cannot be dismissed. Input field becomes disabled.

### Disabled Chat Input

When the chatbot limit is reached, the input field shows a disabled state.

- **Input:** Disabled, `neutral-100` background, `neutral-400` placeholder text
- **Placeholder:** "Subscribe to continue chatting..."
- **Send button:** Disabled, `neutral-300` background

### Section AI Disabled Button

- **Default state (before limit):** Primary button per design system, with AI sparkle icon
- **Disabled state (after limit):**
  - Background: `neutral-300`
  - Text: `neutral-500`
  - Label: "✦ Ask AI — Subscribe to unlock"
  - Cursor: `pointer` (not `not-allowed` — clicking navigates to pricing)
  - On click: Navigate to `/pricing?from=section-ai&section={category}`
- **Tooltip (desktop hover):**
  - `neutral-900` background, white text, `border-radius: 6px`, `text-sm`
  - Content: "Free AI trial used. Subscribe for $19/mo →"
  - Arrow pointing to button
- **Mobile tap:** No tooltip — button click navigates directly to pricing

### Portfolio AI Upgrade Card

Replaces the analysis area content when limit is reached.

- **Card:** Standard card (white background, `neutral-200` border, `border-radius: 8px`)
- **Border-left:** 4px solid `--ai-color` (#6366F1) — metric card variant
- **Icon:** AI sparkle mark (✦) in `--ai-color`, 24px
- **Heading:** "AI Portfolio Analysis" — `text-lg`, `neutral-700`, `fw-semibold`
- **Body:** "You've used your free portfolio analysis for this session. Subscribe to get unlimited AI insights on your portfolio." — `text-base`, `neutral-600`
- **CTA:** Small primary button: "Subscribe — $19/mo →"
- **Padding:** `space-5`

### Rate Limit Response Updates

The existing rate limit response payloads need updated URLs and messaging:

| Field | Phase 12 Value | Phase 13 Value |
|-------|---------------|----------------|
| `signup_url` | `/register` | `/pricing` |
| `message` (session limit) | "...Create a free account to get higher limits..." | "You've used your free AI trial. Subscribe for $19/mo for unlimited access." |
| `message` (global daily cap) | "...Create a free account to get guaranteed access..." | "Free AI features have reached their daily limit. Subscribe for guaranteed access." |

## Interaction Patterns

- **Chatbot message append:** Upgrade message appears as the last message in the thread, with a subtle fade-in (250ms ease-out). No bounce or attention-grabbing animation — it should feel like a natural system message.
- **Input disable:** Happens simultaneously with the upgrade message. Transition: opacity from 1.0 to 0.7, 150ms.
- **Section AI button transition:** When limit is detected, button transitions from active to disabled state with a 150ms color fade. No jarring flash.
- **No modal/overlay:** Upgrade prompts are always inline. Never interrupt with a modal or overlay.

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|---------------|
| 375px (mobile) | All upgrade messages full-width within their containers. CTA links are full-width blocks. |
| 768px (md) | Chatbot upgrade message max-width 80% of chat area. Portfolio card inline. |
| 1024px (lg) | Section AI buttons show hover tooltips. |

## Accessibility Requirements

- Color contrast: All upgrade text meets 4.5:1 on their respective backgrounds. Disabled button text (neutral-500 on neutral-300) exceeds 3:1 for UI components.
- Touch targets: CTA links minimum 44px tap height. Disabled section AI buttons maintain 44px touch target.
- Keyboard navigation: Upgrade message CTA links are focusable and reachable via Tab. Disabled input has `aria-disabled="true"`.
- Screen reader: Upgrade message container has `role="alert"` so it's announced. Disabled buttons have `aria-label` explaining why disabled: "AI trial used. Subscribe to unlock."
- Tooltip: Desktop tooltips triggered on focus as well as hover.

## Design System References

- Colors: `brand-blue-100` (message backgrounds), `--ai-color` #6366F1 (sparkle icons), `neutral-300` (disabled states), `success-600` (included checks on pricing page via ?from= flow)
- Typography: `text-sm` (chat messages), `text-base` (portfolio card body), `text-lg` (card heading)
- Components: Standard card (metric variant with left border), ghost links, disabled button state
- Spacing: `space-4` message padding, `space-3` element gaps, `space-5` card padding

## Copy Guidelines

Tone is conversational and helpful. Acknowledge what happened, offer the solution.

- **Do:** "You've used your free AI messages" (acknowledge), "Subscribe for unlimited access" (solution)
- **Don't:** "Upgrade required" (demanding), "Buy premium" (salesy), "Limit reached" (cold/technical)
- Always include the price in the CTA to set expectations: "Subscribe — $19/mo"
- Use "→" arrow in CTA text to suggest forward motion
