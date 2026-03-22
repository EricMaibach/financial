# Phase 12: AI Foundation & Metering

**Goal:** Remove BYOK, let anyone experience AI within budget, measure everything, protect costs.

**Phase state:** IDEATING (pending PM breakdown into features and stories)

---

## Context

Phase 11 shipped the Market Conditions Engine and deprecated the old regime system. The product is feature-complete for a free dashboard — macro conditions, recession modeling, credit intelligence, sector sentiment, portfolio tracking, AI chatbot, news pipeline.

The next priority is monetization. Phase 12 lays the foundation: remove the bring-your-own-key requirement so anyone can use AI features, add metering to understand real usage patterns, and protect costs with rate limiting. Usage data collected here directly informs pricing decisions for Phase 13 (Stripe integration and payment tiers).

### What This Phase Does NOT Include

- Stripe or payment processing
- Subscription tiers or pricing page
- Paywall modals or upgrade flows
- Daily briefing email gating
- Conversion optimization

All of that is Phase 13, informed by the usage data we collect in Phase 12.

---

## Work Items

### 1. Remove BYOK System

**What:** Eliminate the bring-your-own-key system entirely. All AI features (chatbot, section AI buttons, sentence drill-in, portfolio AI analysis) run on the system API key.

**Why:** BYOK was a stopgap. Users shouldn't need their own OpenAI/Anthropic account to use our product. Removing it simplifies the codebase and is a prerequisite for metered access.

**Scope:**
- Remove encrypted API key storage from `UserSettings` model (Fernet-encrypted fields)
- Remove API key configuration UI from the settings page
- Remove `get_user_ai_client()` path in `ai_service.py` — all calls use `get_system_ai_client()`
- Remove `check_user_ai_configured()` checks and related frontend conditional logic
- Update all AI routes to use system client instead of per-user client
- Clean up related imports, templates, and JavaScript
- Database migration to drop encrypted key columns

### 2. Anonymous AI Access

**What:** Allow users who are not logged in to use AI features, within rate limits.

**Why:** The "aha moment" — getting a personalized AI answer about market data — is what converts visitors to signups. Putting a login wall before that moment weakens conversion.

**Scope:**
- Remove `@login_required` from AI routes: `/api/chatbot`, portfolio AI analysis endpoint, section AI button endpoints
- Ensure AI routes handle both authenticated and anonymous users
- Anonymous users identified by session cookie for rate limiting purposes
- Portfolio features that require saved data (portfolio allocations) still require `@login_required` — only the AI interaction layer opens up

### 3. Per-Session Rate Limiting (Anonymous)

**What:** Each anonymous user gets a lifetime AI budget tracked by session cookie. Once used, AI is done — sign up to continue.

**Limits (starting values, configurable):**
- Chatbot messages: ~5 total (lifetime per session)
- Portfolio AI analyses: ~2 total (lifetime per session)

**Why lifetime, not daily:** A daily reset lets someone use free AI indefinitely without signing up. Lifetime turns anonymous AI into a trial experience — a taste of the product, not an ongoing free tier. The free tier is the dashboard without AI. AI is the premium hook.

**Behavior when limit hit:** AI routes return a structured response (not an error) that the frontend handles as a redirect to the signup page. See item 5.

**Tracking:** Session cookie. Someone clearing cookies or using incognito gets a fresh session — acceptable at this stage since the global daily cap (item 4) is the real cost protection.

### 4. Global Daily Anonymous Cap

**What:** A single counter tracking total anonymous AI calls across all anonymous users per day. Configurable limit. When hit, all anonymous AI calls redirect to signup until midnight reset.

**Starting limit:** ~100 total anonymous AI calls per day (adjust based on observed usage and cost).

**Why:** Per-session limits prevent one person from draining the budget. The global cap prevents aggregate anonymous usage from creating runaway API costs. This is the circuit breaker.

**Implementation notes:**
- One counter, simple increment. Chatbot message = 1 call. Portfolio analysis = 1 call. Section AI button = 1 call.
- Resets at midnight (server time or UTC — pick one and be consistent).
- Configurable via environment variable or app config so it can be adjusted without a deploy.

### 5. Graceful Redirect Flow

**What:** When an anonymous user hits their per-session limit, the global daily cap, or clicks an AI feature with no remaining budget, the experience is a smooth redirect to the signup page — never an error message.

**Scope:**
- AI routes return a structured JSON response indicating the limit type (personal limit, global limit)
- Frontend JavaScript handles these responses: shows a brief message ("You've used your free AI messages for today") and redirects or shows a modal pointing to signup
- The redirect carries context about what the user was trying to do (e.g., `?from=chatbot` or `?from=section-ai&section=credit`) so the signup page can show relevant copy

### 6. Signup Page Enhancement

**What:** Enhance the existing registration page to serve as the landing page for AI redirect flows. Foundation for a future sales/pricing page.

**Scope:**
- Add context-aware copy above the registration form based on the `from` parameter:
  - From chatbot: "Sign up to continue asking questions about your market data"
  - From section AI: "Sign up to get AI analysis of [section name]"
  - Default: "Sign up for full access to AI-powered market intelligence"
- Brief feature list: what registered users get (more AI messages, portfolio tracking, alerts)
- Keep the existing form fields and validation — no changes to the registration flow itself
- Clean, simple design — this is not a full sales page yet (that's Phase 13)

### 7. Usage Metering (Registered Users)

**What:** Database model tracking every AI interaction for registered users. No enforcement yet — purely measurement.

**Why:** We need real usage data to set pricing for Phase 13. How many chatbot messages does an engaged user send per day? Per month? How token-heavy are portfolio analyses vs chatbot messages? This data answers those questions.

**Data model (per interaction):**
- User ID
- Interaction type (chatbot, portfolio_analysis, section_ai, sentence_drill_in)
- Timestamp
- Token count (input tokens, output tokens, cache read/creation tokens if available)
- Model used
- Estimated cost (calculated from token count — approximate is fine)

**Scope:**
- New database model and migration
- Logging hook in AI service layer — every AI call records a metering row
- No UI for users (they don't see this data yet — that's Phase 13)
- Admin analytics page uses this data (see item 9)

### 8. Per-User Rate Limiting (Registered Users)

**What:** Daily limits for registered users. Generous — the goal is cost protection, not restriction.

**Starting limits (configurable):**
- Chatbot messages: ~25 per day
- Portfolio AI analyses: ~5 per day

**Behavior when limit hit:** Same graceful pattern as anonymous limits, but the message says "You've reached your daily limit. Resets tomorrow." No signup redirect — they already have an account. (In Phase 13, this becomes an upgrade prompt.)

**Why:** Even without paid tiers, we need a ceiling on per-user usage to prevent any single registered user from generating outsized API costs.

### 9. Admin Role & Usage Analytics

**What:** Admin-only dashboard for monitoring AI usage across the platform.

**Admin access:** Uses the existing `is_admin` boolean on the User model. Admin users set manually via direct database update — no admin management UI needed.

**Scope:**
- `@admin_required` decorator that checks `current_user.is_admin`, returns 403 if not
- Admin analytics page at `/admin/usage` (or similar) showing:
  - Daily AI call volume (total, anonymous vs registered breakdown)
  - Token consumption and estimated cost
  - Per-user breakdown (top users by call count and token usage)
  - Global anonymous cap status (calls used today / limit)
  - Trend over time (daily totals for the past 30 days)
- Simple, functional design — data tables and basic charts. No need for a polished admin UI.

---

## Architecture Notes

### System AI Key

After BYOK removal, all AI calls use the system key configured in `.env` (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`). The `AI_PROVIDER` environment variable determines which provider is used.

**Cost implications:** Every AI interaction now costs us money. The three-layer cost protection (per-session anonymous limits, global daily cap, per-user registered limits) is critical. Monitor costs closely via the admin dashboard after launch.

### Rate Limit Configuration

All rate limits should be configurable without code changes — either via environment variables or a config table. Starting values are conservative estimates; we'll adjust based on observed usage.

| Limit | Starting Value | Configurable Via |
|-------|---------------|-----------------|
| Anonymous chatbot (lifetime per session) | 5 | App config |
| Anonymous portfolio AI (lifetime per session) | 2 | App config |
| Global anonymous calls/day | 100 | App config / env var |
| Registered chatbot/day | 25 | App config |
| Registered portfolio AI/day | 5 | App config |

### Database Changes

- Drop: Encrypted API key columns from `UserSettings` (or deprecate the model entirely if no other fields remain)
- Add: `AIUsage` model for metering (item 7)
- Add: Anonymous usage tracking (may be in-memory/Redis or a lightweight DB table)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Anonymous → signup conversion | Baseline measurement (no target yet — this is our first data) |
| Daily anonymous AI calls | Understand organic demand level |
| Registered user AI usage | Average calls per user per day/month — informs tier pricing |
| Cost per user per month | Key input for Phase 13 pricing |
| Global cap hit frequency | If hitting daily, raise limit or reconsider pricing model |
| Zero error states for AI access | No user should ever see an error when clicking an AI button — always a graceful redirect or a working response |

---

## Phase 13 Preview (Not In Scope)

Phase 13 uses the usage data collected here to implement:
- Stripe integration (checkout, webhooks, customer portal)
- Subscription tiers (Starter $19/mo, Pro $39/mo — pricing validated by Phase 12 data)
- Pricing/sales page (evolves from the signup page built here)
- Paywall modals and upgrade prompts when hitting limits
- Daily briefing email gated to paid tier
- Free trial flow (14-day, credit card required)
- Usage dashboard for users (messages remaining, etc.)
