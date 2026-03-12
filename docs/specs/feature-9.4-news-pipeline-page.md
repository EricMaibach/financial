# Persistent News Pipeline — News Page Design Spec

**Issue:** #259
**Feature:** 9.4 — Persistent News Pipeline (News Page)
**Created:** 2026-03-12
**Status:** Draft

---

## Overview

A dedicated `/news` page that surfaces the daily aggregate AI news summary and source articles for macro/financial news fetched via Tavily. The pipeline backend is entirely out of scope for this spec — this spec covers only the `/news` page UI and its navigation integration.

The news page serves sophisticated investors who want to understand what happened in macro markets today. The primary content is a single synthesized narrative (not a list of bullets), giving users a coherent "what happened" read before drilling into source articles.

---

## Navigation Integration

**Add "News" to the top navbar** between existing nav items. Suggested position: after "Home", before asset pages (Credit, Equity, etc.) — it's top-of-funnel context that makes all the asset pages more meaningful.

**Nav link label:** `News`
**Nav link icon (optional):** `bi-newspaper` (consistent with Bootstrap icon set already in use)
**Route:** `/news`

Mobile: The nav link collapses into the hamburger menu (existing pattern — no new work).
Desktop: Standard navbar link with hover/active states per design system.

---

## User Flow

1. User has read the AI daily briefing on the homepage or wants broader context
2. User clicks "News" in the navbar
3. Page loads: they see the AI-synthesized narrative at the top (primary focus)
4. They read the coherent macro narrative — this is the value
5. Below, they see the source list — headline + link — to read any individual article
6. On mobile, sources are stacked vertically; on desktop, sources use a 2-column grid

---

## Page Layout

### Mobile (375px) — Primary Design

```
┌─────────────────────────────────┐
│ [navbar]                        │
├─────────────────────────────────┤
│ 📰 Today's Macro News           │ ← H1, text-2xl, neutral-800
│ [date: March 12, 2026]          │ ← text-sm, neutral-500
├─────────────────────────────────┤
│ ┌─────────────────────────────┐ │
│ │ AI SUMMARY                  │ │ ← uppercase label, text-xs, neutral-500
│ │                             │ │
│ │ [synthesized narrative      │ │ ← text-base, neutral-600, lh 1.6
│ │  paragraph(s) here — full   │ │
│ │  coherent AI text, no       │ │
│ │  truncation]                │ │
│ │                             │ │
│ │ ──────────────────────────  │ │
│ │ Generated from X sources    │ │ ← text-xs, neutral-400
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ SOURCES (X)                     │ ← section label, text-sm, font-weight 600
│                                 │
│ ┌─────────────────────────────┐ │
│ │ [Source headline text]   →  │ │ ← link, text-sm, neutral-700
│ │ reuters.com · 2h ago        │ │ ← text-xs, neutral-400
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ [Source headline text]   →  │ │
│ │ ft.com · 4h ago             │ │
│ └─────────────────────────────┘ │
│ [... more source cards]         │
└─────────────────────────────────┘
```

### Desktop (1024px+)

```
┌──────────────────────────────────────────────────────────┐
│ [navbar]                                                  │
├──────────────────────────────────────────────────────────┤
│  📰 Today's Macro News               March 12, 2026      │
├───────────────────────┬──────────────────────────────────┤
│                       │                                  │
│  AI SUMMARY           │  SOURCES (X)                     │
│                       │                                  │
│  [synthesized         │  [Source 1 headline]          →  │
│   narrative text,     │  reuters.com · 2h ago            │
│   lh 1.6, max-width   │                                  │
│   65ch for readab-    │  [Source 2 headline]          →  │
│   ility]              │  ft.com · 4h ago                 │
│                       │                                  │
│                       │  [Source 3 headline]          →  │
│                       │  wsj.com · 5h ago                │
│                       │                                  │
│  Generated from       │  [Source 4 headline]          →  │
│  X sources            │  bloomberg.com · 6h ago          │
│                       │                                  │
└───────────────────────┴──────────────────────────────────┘
```

**Desktop layout:** 2/3 width left column (AI summary) + 1/3 width right column (sources). Sources use single-column list on the right, not a grid — this avoids visual competition with the summary.

---

## Component Specifications

### Page Header

```
Element: <h1> with inline icon
Icon: bi-newspaper (aria-hidden="true")
Text: "Today's Macro News"
Date: <p class="text-sm text-neutral-500"> — "March 12, 2026" format
Layout: icon + title on one line, date below on mobile; title + date on same row on desktop (justify-content: space-between)
```

### AI Summary Card

A card with a distinctive left border to signal "AI-generated content" — matches the interpretation block pattern used in Trade Pulse and Credit page.

```css
/* Component: .news-summary-card */
background: white;
border: 1px solid var(--neutral-200);
border-left: 4px solid var(--brand-indigo-500);  /* indigo = AI/intelligence */
border-radius: 8px;
padding: var(--space-6);
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
```

**Header within card:**
- Label: `AI SUMMARY` — text-xs, font-weight 600, letter-spacing 0.08em, neutral-500, uppercase
- Optionally prefix label with `✦` (AI sparkle mark, from the AI icon system in Feature #258, if available) or `bi-stars`

**Body text:**
- Full narrative, no truncation — `text-base`, `neutral-600`, `line-height: 1.6`
- Do NOT display as bullet list — the backend produces a coherent paragraph; display it as-is

**Footer within card:**
- "Generated from X sources" — text-xs, neutral-400, italic
- Bottom of card, separated by a 1px neutral-200 rule

### Source List

Each source is a clickable card that opens the article URL in a new tab.

```
Element: <a href="{url}" target="_blank" rel="noopener noreferrer">
```

**Source card:**
```css
display: flex;
justify-content: space-between;
align-items: flex-start;
padding: var(--space-4);
border: 1px solid var(--neutral-200);
border-radius: 8px;
background: white;
margin-bottom: var(--space-3);
text-decoration: none;
transition: all 150ms ease-out;

/* Hover */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
border-color: var(--neutral-300);
transform: translateY(-1px);
```

**Source card content:**
- Left: headline text (`text-sm`, `neutral-700`, `font-weight: 500`)
- Below headline: domain + relative time (`text-xs`, `neutral-400`) — extract domain from URL (e.g., `reuters.com`); time relative if same day, else date
- Right: `→` arrow icon (`bi-arrow-up-right`, `neutral-400`, decorative, `aria-hidden`)

**Section label above sources:**
- `SOURCES (X)` — text-sm, font-weight 600, neutral-700, uppercase, margin-bottom space-4

---

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|---------------|
| 375px | Single column: summary full-width, sources stacked below |
| 768px | Single column still; source cards slightly wider padding |
| 1024px+ | Two-column: summary left 2/3, sources right 1/3, sticky (position: sticky, top: 80px) summary if content is short |

**Source card grid on desktop:** Single column list in the right panel (not a 2-col grid). The right panel is already 1/3 width — a 2-col grid inside would be too dense.

---

## Empty States

### No Data Fetched Yet

Shown when the pipeline has never run (fresh install).

```
[bi-newspaper icon, 48px, neutral-300]

No news yet
The daily macro news pipeline hasn't run yet.
Check back tomorrow morning.
```

### API Unavailable (Last Known Summary Shown)

When Tavily is down but a prior summary exists, show the last stored summary with a stale-data notice at the top:

```
┌──────────────────────────────────────────────────────┐
│ ⚠ Showing news from March 11, 2026 — today's fetch   │
│   is unavailable.                                    │  ← warning-100 bg, warning-700 text
└──────────────────────────────────────────────────────┘
[rest of page with prior summary]
```

### API Unavailable (No Prior Data)

```
[bi-wifi-off icon, 48px, neutral-300]

News unavailable
We couldn't fetch today's news and have no prior summary to display.
The pipeline will retry automatically tomorrow.
```

---

## Accessibility Requirements

- Page title: `<title>News — SignalTrackers</title>`
- `<h1>` for page heading, `<h2>` for "AI Summary" and "Sources" sections (use visually hidden `<h2>` if label styling differs)
- Source links: `aria-label="Read: {headline} (opens in new tab)"` — screen readers need the "opens in new tab" warning
- AI summary card: `role="region" aria-label="AI-generated news summary"`
- Color contrast: all body text uses neutral-600 or darker (passes AA)
- Touch targets: source cards have min-height 56px (AAA, because these are primary interactive elements on the page)

---

## Design System References

- Colors: neutral-50/200/400/500/600/700, brand-indigo-500 (AI left border), warning-100/700 (stale notice)
- Typography: text-xs, text-sm, text-base; neutral color scale for hierarchy
- Spacing: space-3, space-4, space-6 (card padding)
- Components: Card pattern (1px border, 8px radius, subtle shadow), metric card left border pattern
- Interpretation block pattern: same left-border treatment as `credit-interpretation-block`

---

## Implementation Notes

- News page is a new route — engineer adds `/news` to routing
- Template: `signaltrackers/templates/news.html` — extend `base.html`
- Backend passes: `summary_text` (string), `sources` (list of `{headline, url, timestamp}`), `summary_date` (date), `is_stale` (bool), `stale_date` (date or None)
- Domain extraction from URL can be done in Jinja2 or Python — keep it simple (`urlparse(url).netloc`)
- CSS: new `static/css/news.css` (or add to a shared page CSS if pattern already exists)
- No new JavaScript needed — static render
