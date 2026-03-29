# Phase 13: Stripe & Subscriptions

**Goal:** Ship payments. One price, one conversion path, minimal complexity. Start making money.

**Phase state:** IDEATING (pending PM breakdown into features and stories)

---

## Context

Phase 12 shipped the AI foundation: BYOK removed, anonymous AI trial with lifetime session limits, usage metering, admin analytics, and cost protection via global daily caps. The product is now a fully functional free dashboard with a built-in AI trial experience.

Phase 13 closes the loop: add Stripe so people can pay. Every design decision in this phase optimizes for simplicity — one tier, one price, one conversion path. We can add complexity later when we have real usage data and paying users telling us what they need.

### Key Decisions Made

These decisions were made by the CEO and founder on 2026-03-29. They are final for Phase 13 scope — do not re-open without new evidence.

1. **Single pricing tier: $19/mo.** No Pro tier at launch. A second tier gets added later when usage data reveals a natural breakpoint between normal and power users.

2. **No free registered tier.** Registration = payment. There are exactly two user states: anonymous (no account) and paid subscriber (has account). There is no "free account" in between.

3. **No free trial.** The Phase 12 anonymous AI experience IS the trial. Users get ~5 chatbot messages and ~2 portfolio analyses per session (lifetime, not daily). Adding a formal 14-day trial on top of this is redundant complexity.

4. **Stripe code lives in the public repo.** All secrets (API keys, webhook secrets) are in `.env` (gitignored). The code itself follows standard Stripe patterns that are publicly documented. Webhook signature verification handles security. The portfolio value of visible payment infrastructure is a net positive.

5. **Billing module stays in main app.** Code lives in `signaltrackers/billing/` — architecturally separated but same repo, same deploy. No separate private repo.

6. **All rate limits must be config-driven.** Limits are adjustable without code changes (env vars or app config). This applies to both existing Phase 12 limits and new paid tier limits.

---

## The Two User States

### Anonymous (No Account)

Everything the product offers today, minus AI beyond the trial:

- Full dashboard: market conditions engine, recession models, credit intelligence, sector sentiment, news, charts
- Limited AI trial (Phase 12 lifetime session limits): ~5 chatbot messages, ~2 portfolio AI analyses per session
- No portfolio tracking (requires account)
- No daily briefing email
- No alerts

### Paid Subscriber ($19/mo)

Full product experience:

- Everything anonymous users get, without AI limits constraining them
- AI chatbot: 50 messages/day
- Portfolio AI analysis: 10/day
- Section AI / drill-in: 25/day
- Daily briefing email
- Portfolio tracking and alerts
- Subscription management (cancel, update payment method, billing history)

**Limit philosophy:** These limits should feel unlimited to a normal retail investor. They exist to prevent abuse and protect API costs, not to constrain usage. If users regularly hit these ceilings, that's the signal to introduce a Pro tier at a higher price.

**Starting daily limits (configurable):**

| Feature | Paid Limit | Anonymous Limit (Phase 12) |
|---------|-----------|---------------------------|
| Chatbot messages | 50/day | ~5 lifetime per session |
| Portfolio AI analyses | 10/day | ~2 lifetime per session |
| Section AI / drill-in | 25/day | Shares anonymous chatbot budget |
| Daily briefing email | 1/day | None |

---

## Conversion Funnel

This is the single path from visitor to paying customer:

```
1. Visitor lands on site
   → Full dashboard visible, no account needed

2. Visitor clicks an AI feature (chatbot, section AI button, drill-in)
   → AI works. Visitor gets their "aha moment."

3. Visitor uses up their anonymous AI budget
   → Graceful redirect: "Want more? Subscribe for $19/mo."
   → Context-aware: message reflects what they were trying to do

4. Visitor clicks "Subscribe"
   → Stripe Checkout session → payment → account created → redirected back

5. Paid subscriber
   → Full AI unlocked, daily briefing email starts, portfolio available
```

Phase 12 already built steps 1–3. Phase 13 builds steps 3.5–5 (the upgrade prompt, Stripe checkout, and post-payment experience).

---

## Work Items

### 1. Stripe Integration

**What:** Core Stripe infrastructure — API client, checkout sessions, webhook handling, subscription lifecycle management.

**Scope:**
- Stripe Python SDK integration in `signaltrackers/billing/`
- Stripe Checkout for subscription creation (hosted checkout page — don't build a custom payment form)
- Webhook endpoint to handle Stripe events:
  - `checkout.session.completed` — activate subscription, create/upgrade user
  - `invoice.paid` — record successful renewal
  - `invoice.payment_failed` — handle failed payment (grace period, then downgrade)
  - `customer.subscription.deleted` — handle cancellation
  - `customer.subscription.updated` — handle plan changes (future-proofing)
- Webhook signature verification (critical for security, especially in a public repo)
- Stripe Customer ID stored on User model
- Subscription status tracking (active, past_due, canceled, etc.)

**Environment variables (add to `.env.example`):**
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID` (the $19/mo price ID created in Stripe Dashboard)

### 2. Registration = Payment Flow

**What:** Merge the existing registration flow into Stripe Checkout. Signing up creates a Stripe subscription and a user account in one step.

**Scope:**
- Replace or redirect the existing `/register` route to go through Stripe Checkout
- Stripe Checkout collects email + payment → webhook creates the user account
- Password setup: either collected during checkout (custom fields) or via a "set your password" email after payment
- Post-checkout redirect back to the app with the user logged in
- Handle edge cases: user closes checkout mid-flow, payment fails, duplicate emails

**Important:** The existing registration page from Phase 12 has context-aware copy (e.g., "Sign up to continue asking questions about your market data"). This context should carry through to the pricing page or pre-checkout flow so the user still sees relevant messaging.

### 3. Pricing / Sales Page

**What:** A single page that communicates the value of subscribing and has one clear call-to-action.

**Scope:**
- Route: `/pricing` or `/subscribe`
- Single tier displayed: $19/mo
- Clear value proposition: what you get as a subscriber vs. what's free
- Feature comparison (free vs. paid) — keep it simple, not a complex feature matrix
- One CTA button: "Subscribe — $19/month" → initiates Stripe Checkout
- Context-aware: if redirected from an AI limit, show messaging about what they were doing
- Mobile-responsive
- This page evolves from the Phase 12 signup page enhancement — build on that foundation

**Marketing line to use:** "Free gives you the macro picture. Paid makes it personal."

### 4. Upgrade Prompts

**What:** When an anonymous user hits their AI limit, redirect them to the pricing page with contextual messaging.

**Scope:**
- Update Phase 12's graceful redirect flow to point to the pricing page instead of the registration page
- Context parameter carries through: `?from=chatbot`, `?from=section-ai&section=credit`, etc.
- The pricing page renders context-aware copy based on this parameter
- Chatbot: when limit is hit, show an inline message with a link to subscribe (not just a redirect)
- Section AI buttons: disable with a "Subscribe to unlock" tooltip after limit reached

**Phase 12 foundation:** The redirect infrastructure already exists (item 5 from Phase 12). This work updates the destination and enhances the messaging.

### 5. Daily Briefing Email Gating

**What:** Gate the daily briefing email to paid subscribers only.

**Scope:**
- Daily briefing email scheduler checks subscription status before sending
- Only users with `subscription_status = 'active'` receive the email
- Include an unsubscribe link in every email (required by law)
- When a subscription is canceled, stop sending emails
- The email itself should include a small "Powered by SignalTrackers" footer with a link to the site

**Note:** The daily briefing email pipeline already exists. This work adds the subscriber gate and ensures the email content is up to date with all current signal categories.

### 6. Subscription Management

**What:** Let subscribers manage their subscription — cancel, update payment, view billing history.

**Scope:**
- Account settings page at `/account` or `/settings`
- "Manage Subscription" button → Stripe Customer Portal (use Stripe's hosted portal, don't build custom)
- Stripe Customer Portal handles: cancel subscription, update payment method, view invoices, update billing info
- Display current plan status on the account page (active, past_due, canceling at period end)
- Handle cancellation gracefully: access continues until end of billing period, then downgrade to anonymous experience

### 7. Paid Tier Rate Limiting

**What:** Enforce daily AI limits for paid subscribers. Follows the same pattern as Phase 12's anonymous and registered limits.

**Scope:**
- Paid subscribers get daily limits (see table above): 50 chatbot, 10 portfolio AI, 25 section AI
- All limits configurable via app config / env vars — no hardcoded values
- When a paid user hits a limit: "You've reached your daily limit. Resets tomorrow." (Not a paywall — they already pay)
- Phase 12 usage metering continues tracking all calls for analytics
- Admin dashboard shows paid user usage patterns alongside anonymous usage

**Note:** Phase 12 built per-user rate limiting for "registered users" at 25 chatbot / 5 portfolio AI per day. This work either updates those limits for the paid tier or replaces the registered-user concept entirely since registration now equals payment.

---

## Architecture Notes

### Billing Module Structure

All Stripe-related code lives in `signaltrackers/billing/`:

```
signaltrackers/billing/
├── __init__.py
├── stripe_client.py      # Stripe SDK setup, helper functions
├── webhooks.py            # Webhook endpoint and event handlers
├── checkout.py            # Checkout session creation, redirect logic
├── models.py              # Subscription model, billing-related DB fields
└── config.py              # Rate limits, price IDs, configurable values
```

This is a suggested structure — the engineer should adapt based on the existing codebase patterns.

### User Model Changes

The User model needs:
- `stripe_customer_id` — links to Stripe Customer object
- `subscription_status` — enum: active, past_due, canceled, none
- `subscription_end_date` — when current period ends (for grace period on cancellation)
- Remove or repurpose Phase 12's "registered free" rate limit fields if they exist

### Rate Limit Configuration

All limits in one place, easily adjustable:

```
# .env or app config
PAID_DAILY_CHATBOT_LIMIT=50
PAID_DAILY_PORTFOLIO_AI_LIMIT=10
PAID_DAILY_SECTION_AI_LIMIT=25

# Phase 12 limits (already exist)
ANON_SESSION_CHATBOT_LIMIT=5
ANON_SESSION_PORTFOLIO_AI_LIMIT=2
ANON_GLOBAL_DAILY_CAP=100
```

### Stripe Checkout vs. Custom Form

Use **Stripe Checkout** (Stripe's hosted payment page), not a custom payment form. Reasons:
- PCI compliance handled entirely by Stripe — no card data touches our server
- Mobile-optimized out of the box
- Handles 3D Secure, Apple Pay, Google Pay automatically
- Less code to write and maintain
- Especially important in a public repo — no custom payment form code to scrutinize

### Webhook Security

Even though the code is in a public repo, webhook security is handled by:
- Stripe webhook signature verification on every incoming webhook (using `STRIPE_WEBHOOK_SECRET` from `.env`)
- Endpoint URL is configured in Stripe Dashboard, not in code
- Signature verification rejects any request not signed by Stripe — knowing the endpoint URL is useless without the secret

---

## What This Phase Does NOT Include

- Multiple pricing tiers (Pro tier added later based on usage data)
- Annual billing option (add later if warranted)
- Free registered accounts (registration = payment)
- Free trial (anonymous AI experience is the trial)
- Usage dashboard for subscribers ("messages remaining" UI — defer unless trivial)
- Referral programs, discount codes, or promotional pricing
- Mobile app or desktop app payment flows

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Checkout completion rate | Baseline measurement — first real conversion data |
| Anonymous → subscriber conversion | Track: AI limit hit → pricing page → checkout → paid |
| Monthly recurring revenue (MRR) | Any amount > $0 is a milestone |
| Churn rate | Baseline measurement |
| Failed payment recovery | Stripe handles retry logic — monitor success rate |
| Webhook reliability | 100% of Stripe events processed successfully |
| Zero payment errors | No user should hit an error during checkout flow |

---

## Dependencies

- **Phase 12 (complete):** Anonymous AI trial, rate limiting, usage metering, graceful redirect flow, signup page enhancement
- **Stripe account:** Needs to be set up in Stripe Dashboard with product/price configured before implementation
- **Domain/DNS:** Stripe Checkout needs a return URL — confirm the production URL is ready
- **.env setup:** Stripe keys need to be added to the production environment

---

## Post-Phase 13: What Comes Next

With payments live, the priority sequence becomes:
1. **Soft launch** — get the product in front of real users
2. **Monitor** — usage patterns, conversion rates, churn, costs
3. **Iterate pricing** — adjust limits, consider Pro tier if power users emerge
4. **Distribution** — SEO, Product Hunt, content marketing (no distribution until money can change hands)
