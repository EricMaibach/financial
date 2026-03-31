# Phase 13: Access Control & Launch Prep

**Goal:** Ship a free public site with invite-only registration for AI features. Validate traction before monetization.

**Phase state:** BUILDING

---

## Context

Phase 12 shipped the AI foundation: BYOK removal, anonymous AI trial with session limits, usage metering, admin analytics. The original Phase 13 plan was Stripe integration and a $19/mo subscription tier.

After strategic review (2026-03-30), we're changing direction. The product hasn't validated market demand yet. Building payment infrastructure before knowing if anyone wants the product is premature. The new priority is: get live, see who shows up, learn what they care about.

### Strategic Decisions (2026-03-30)

- **Monetization paused.** No Stripe checkout, no pricing page, no subscription management. Revisit when traction data exists.
- **Free public site.** Full dashboard, all charts, data exploration, daily briefing — no account required.
- **Invite-only registration.** AI features (chatbot, section AI, drill-in, portfolio AI, daily briefing email) require a registered account. Registration requires an invite code.
- **Anonymous AI trial removed.** The Phase 12 anonymous AI trial (lifetime session limits) is turned off. Anonymous visitors see the dashboard and read the daily briefing. They do not interact with AI. This eliminates the primary variable cost for unregistered traffic.
- **Stripe development stopped.** PR #425 (US-13.1.4) stays open but unmerged — it changes access control to require paid subscriptions, which conflicts with the invite-only model. Merged Stripe code (US-13.1.1, 13.1.2, 13.1.3) remains in the codebase dormant. No harm, no cost, ready if needed later.

### What Changed From the Original Phase 13

| Original Plan | New Plan |
|---------------|----------|
| Stripe checkout + webhooks | Shelved (foundation code already merged) |
| $19/mo subscription tier | Shelved |
| Pricing/sales page | Not needed |
| Upgrade prompts (anonymous → paid) | Not needed |
| Daily briefing email gating (paid only) | Gated to registered users (invite-only) |
| Subscription management (cancel, billing) | Not needed |
| Free anonymous AI trial as conversion funnel | Removed entirely |

---

## Work Items

### 1. Invite Code on Registration

**What:** Add an invite code field to the registration form. Registration fails without a valid code.

**Why:** Controls who gets an account (and therefore AI access) without payment infrastructure. Lets Eric selectively onboard users for feedback and testing.

**Scope:**
- Add invite code configuration (environment variable or app config) — a simple string comparison, not a database of codes
- Add invite code field to the registration form
- Validate invite code server-side on registration submission
- Clear error message for invalid code: "Registration is currently invite-only. Contact us for access." (or similar)
- Admin can change the code via config without a deploy

**What this does NOT include:**
- Per-user invite codes or tracking who used which code
- Invite code expiration or usage limits
- Self-service invite generation

Keep it simple. One code, one config value.

### 2. Remove Anonymous AI Trial

**What:** Remove the Phase 12 anonymous AI trial experience. Anonymous users cannot use AI features.

**Why:** Every anonymous AI call is a cost with no conversion path (no payment flow exists). The daily briefing on the homepage demonstrates AI quality without interactive AI access. The free experience is the dashboard — AI is for registered users.

**Scope:**
- Re-add `@login_required` (or equivalent) to AI routes: chatbot, section AI buttons, sentence drill-in, portfolio AI analysis
- Remove or hide AI interaction UI elements for anonymous users (chatbot launcher, section AI buttons, drill-in highlights)
- The daily briefing text on the homepage remains visible to everyone (it's pre-generated, fixed daily cost regardless of traffic)
- Remove the anonymous-to-signup redirect flow (Phase 12 item 5) — anonymous users simply don't see AI buttons
- Keep the Phase 12 rate limiting infrastructure intact for registered users (daily limits still apply to invited users for cost protection)

**Important:** The `anonymous_rate_limit` decorator, session tracking, and global daily cap code can remain in the codebase — just not triggered if anonymous users never reach AI routes. No need to delete working code.

### 3. Update Registration Flow Messaging

**What:** Update the signup page to reflect invite-only access.

**Scope:**
- Registration page messaging: "MacroClarity is currently in private beta. Enter your invite code to create an account."
- Remove any Phase 12 context-aware signup copy that referenced AI trial limits or upgrade paths
- Simple, clean form: email, password, invite code

### 4. Shelve Remaining Stripe Issues

**What:** Close or defer all open Phase 13 Stripe-related issues with a clear note.

**GitHub issues to shelve:**
- #421 (US-13.1.4: Subscription Lifecycle Access Control) — PR #425 stays open, unmerged
- #417 (Daily Briefing Email Gating) — defer; email gating changes to invite-only instead of paid-only
- #416 (Subscription Management) — defer
- #415 (Paid Tier Rate Limits) — defer
- #414 (Upgrade Prompts) — defer
- #413 (Pricing & Checkout Flow) — defer
- #412 (Stripe Integration feature) — defer; sub-stories 13.1.1–13.1.3 already merged

**Label:** Add a `deferred` label (or similar) so these are clearly paused, not abandoned.

**Comment on each:** "Deferred per strategic review 2026-03-30. Monetization paused pending traction validation. Stripe foundation code (13.1.1–13.1.3) remains merged and ready. Will revisit when usage data supports pricing decisions."

### 5. Verify Existing Access Model Works

**What:** Confirm that the current `is_authenticated` access model (without PR #425's `has_paid_access` changes) works correctly for invite-only users.

**Verify:**
- Registered users (via invite code) bypass anonymous rate limits and get full AI access
- Registered user daily limits (Phase 12) still apply for cost protection
- Admin analytics page still tracks usage correctly
- No leftover Stripe-specific UI or messaging visible to registered users
- Anonymous users see the full dashboard but no AI interaction elements

---

## What Stays Free (No Account)

- Full macro dashboard — all charts, all data
- Market conditions engine — quadrant, liquidity, risk, policy
- Recession probability models
- Credit intelligence, sector sentiment, news
- Daily AI briefing (read-only on homepage)
- All data exploration pages
- Property macro indicators

## What Requires Registration (Invite-Only)

- AI chatbot
- Section AI / drill-in
- Portfolio tracking and portfolio AI analysis
- Daily briefing email (delivered to inbox)
- Personalized features (saved portfolio, alert preferences)

---

## Phase Sequence

| Phase | Title | Focus |
|-------|-------|-------|
| **13** | **Access Control & Launch Prep** | Invite code, remove anonymous AI, shelve Stripe |
| **14** | **MacroClarity Rebrand** | Full rebrand: templates, CSS, AI prompts, emails, meta/SEO, favicon |
| **15** | **Public Deployment** | DNS → macroclarity.com, production config, SSL, monitoring |
| **16+** | **Traction & Learning** | SEO, content, observe usage, decide on monetization |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Phase 13 shipped | Invite-only registration working, anonymous AI removed |
| Site stable for public traffic | Dashboard loads reliably with no AI cost from anonymous visitors |
| Invited user feedback | Qualitative — do invited users find the briefing + AI valuable? |
| Cost baseline | Understand monthly cost with 0 paying users and N invited users |

---

## Engineering Direction: Code Hygiene & Future-Proof Architecture

The Phase 12 and 13.1.x code was built with clean module separation. The goal of this phase is to **layer access control on top of existing infrastructure**, not rip anything out. This preserves a clean pivot path back to paid subscriptions when traction data supports it.

### Principle: Layer, Don't Delete

All Phase 12 rate limiting and Phase 13 Stripe code stays in place. It is well-isolated and costs nothing at runtime when not triggered. Removing it creates unnecessary merge conflicts and re-implementation work when monetization returns.

### Implementation Guidelines for Stories

**1. Decorator Stacking (AI Route Protection)**

Add `@login_required` **before** the existing `@anonymous_rate_limit` decorator on AI routes. Do not replace the rate limit decorator.

```python
# Correct — layered, reversible
@login_required
@anonymous_rate_limit(CATEGORY_CHATBOT)
def api_chatbot():
    ...

# Wrong — deletes infrastructure you'll need later
@login_required
def api_chatbot():
    ...
```

When `@login_required` blocks anonymous users, they never reach `@anonymous_rate_limit` — it becomes a passive no-op. Registered users still get daily limit protection from the subscriber layer. To re-enable anonymous AI later, remove `@login_required` and the anonymous rate limiting activates again with zero code changes.

**2. UI Element Hiding (Templates & JS)**

Use template conditionals to hide AI interaction elements for anonymous users. Do not delete the template markup or JS.

```jinja
{# Correct — hidden, not deleted #}
{% if current_user.is_authenticated %}
  <button class="chatbot-launcher">...</button>
{% endif %}
```

The chatbot JS, section AI button code, and drill-in toolbar all stay in the static assets. They simply aren't rendered for anonymous visitors. This avoids re-implementing frontend features on pivot-back.

**3. Rate Limit Messages — Config-Driven Copy**

Add a `SITE_MODE` config value (`invite_only`, `paid`, `open`) to control user-facing rate limit and access control messages. The rate limiting logic stays identical — only the response copy changes.

| SITE_MODE | Rate limit message | Signup prompt |
|-----------|-------------------|---------------|
| `invite_only` | "You've reached your daily limit. Limits reset at midnight UTC." | "Registration is invite-only. Contact us for access." |
| `paid` | "Subscribe to get guaranteed access and higher limits." | "Sign up for a free trial." |
| `open` | "You've reached the free limit for this feature." | "Create an account for higher limits." |

This prevents messaging slop (e.g., invited beta users seeing "Subscribe to get guaranteed access" when there's nothing to subscribe to).

**4. Registered User Daily Limits**

In invite-only mode, registered users (who have no subscription) should get the subscriber-tier daily limits for cost protection — not fall through to the anonymous path. The `check_subscriber_daily_limit()` function currently gates on `has_paid_access`; in invite-only mode, skip that gate so all authenticated users get daily limits tracked via `ai_usage_records`.

This is a small conditional change, not a rewrite:
```python
# If site is invite-only, all authenticated users get subscriber limits
if site_mode != 'invite_only':
    if hasattr(current_user, 'has_paid_access') and not current_user.has_paid_access:
        return None
```

**5. What Stays Untouched**

| Component | Location | Why |
|-----------|----------|-----|
| Billing module | `signaltrackers/billing/` | Gracefully degrades when Stripe keys absent. Zero cost. |
| Stripe webhook route | `dashboard.py` `/webhook/stripe` | Returns 200 to any valid Stripe request. Harmless. |
| User model subscription fields | `models/user.py` | Empty columns, no schema migration needed on pivot-back. |
| `ai_usage_records` table | DB | Still actively used for metering invited users. |
| Anonymous rate limit code | `services/rate_limiting.py` | Passive no-op behind `@login_required`. Activates on pivot-back. |
| PR #425 | GitHub | Stays open, unmerged. Contains `has_paid_access` gating for paid mode. |
| Phase 13 Stripe tests | `tests/` | Pass in both modes (Stripe tests verify graceful degradation). |

**6. What Gets Modified (Minimal Surface)**

| Change | Scope |
|--------|-------|
| Add `@login_required` to ~10 AI routes | One decorator per route |
| Add invite code field to registration | One form field, one config value, one validation check |
| Add `SITE_MODE` config | One env var, message lookup table |
| Template conditionals for AI UI elements | `{% if %}` wrappers in ~4 templates |
| Update registration page copy | Template text changes |
| Adjust `check_subscriber_daily_limit` for invite-only | One conditional branch |

---

## Decisions for PM

1. **Milestone:** Rename the existing "Phase 13 — Stripe & Subscriptions" milestone to "Phase 13 — Access Control & Launch Prep" (or create new and migrate).
2. **Existing closed stories (13.1.1–13.1.3):** Leave closed. That work is done and merged. It just sits dormant.
3. **PR #425:** Leave open, do not merge. Add a comment explaining the deferral.
4. **New stories:** Break work items 1–5 above into user stories following the standard workflow (QA test plan → Engineer implement → Designer review → QA test → PR).
5. **Feature issues:** Create a single feature issue for the access control work, or reuse #412 (Stripe Integration) with updated scope — PM's call on cleanliness vs. history preservation.
