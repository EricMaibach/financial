# Design Spec: MacroClarity Rebrand

**Status:** Draft
**Date:** 2026-03-30

---

## Overview

Rebrand from **SignalTrackers** to **MacroClarity**. This spec covers the name change, logo integration, visual identity evolution, and typography refinement. The rebrand introduces an editorial, curated aesthetic while preserving the usability patterns and financial signal conventions that already work.

**Domain:** macroclarity.com

**Guiding principle:** Evolution, not revolution. The product's layout, responsive behavior, component patterns, and data visualization remain intact. What changes is the surface identity — name, logo, color temperature, typography pairing, and surface treatment.

---

## 1. Brand Identity

### Name
- **Product name:** MacroClarity
- **Tagline:** "Macro Finance Data & Analysis"
- **Alternate short tagline (for navbar):** "Macro Finance Data & Analysis"

### Logo

**Source file:** `docs/macroclarityrebrand/MacroClarityLogoOnly.svg`

The logomark is an angular **MC monogram** with an integrated upward arrow, rendered in a two-tone navy palette. Three color layers create depth:

| Layer | Color | Hex | Role |
|-------|-------|-----|------|
| Base (negative space) | White | `#fdfdfd` | Arrow cutout / internal detail |
| Primary body | Dark navy | `#09264c` | Main structure |
| Accent body | Medium navy | `#0e3a67` | Dimensional depth |

### Logo Usage

| Context | Format | Notes |
|---------|--------|-------|
| Navbar (desktop) | Icon + "MACROCLARITY" text | Icon ~28px height, text uses weight split: "MACRO" bold / "CLARITY" normal |
| Navbar (mobile) | Icon only | Icon ~24px height |
| Favicon (16x16, 32x32) | Icon only | May need simplified version at small sizes — test legibility |
| Apple touch icon (180x180) | Icon only | Full detail version |
| Email header | Icon + "MacroClarity" text | Inline with header background |
| Open Graph / social | Full lockup with tagline | 1200x630 recommended |

### Brand Text Treatment

When the product name appears as text (not the logo SVG), use this weight split:

```
MACRO  — font-weight: 700 (bold)
CLARITY — font-weight: 400 (normal)
```

All caps for the navbar brand. Title case ("MacroClarity") in body text, documentation, and conversational contexts.

---

## 2. Color System

### What Changes

#### New: Surface Tonal Hierarchy

Adopt the Macro-Architect's surface layering system. This replaces the current flat `neutral-50`/`neutral-100` approach with a warmer, blue-tinted surface scale that creates depth without borders.

```css
/* New surface tokens */
--surface:                 #f8f9ff;  /* Base canvas (replaces neutral-50) */
--surface-container-low:   #eff4ff;  /* Content groupings (replaces neutral-100) */
--surface-container-lowest: #ffffff; /* Floating cards, focus elements */
```

**Usage:**
- `surface` → Page background (the "floor")
- `surface-container-low` → Section groupings, sidebar backgrounds
- `surface-container-lowest` → Cards, modals, interactive elements that "float"

The subtle blue tint (`#f8f9ff` vs current `#FAFBFC`) warms the canvas and ties it to the navy brand palette.

#### New: Navy-Tinted Shadows

Replace pure-black shadows with navy-tinted shadows that feel more cohesive:

```css
/* Current */
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

/* New */
box-shadow: 0 2px 4px rgba(11, 28, 48, 0.06);
```

Shadow color base: `#0b1c30` (deep navy). Use lower opacity than current shadows — the tint adds richness without heaviness.

#### New: Primary Text Color

Shift primary text from pure near-black to a deep navy-charcoal:

```css
/* Current */
--neutral-800: #1A202C;  /* Primary text */
--neutral-900: #0F1419;  /* Maximum emphasis */

/* New */
--on-surface: #0b1c30;   /* Primary text — navy-charcoal depth */
```

This is a subtle shift that adds sophistication without reducing readability. Maintains WCAG AAA contrast on all surface colors.

#### Updated: Brand Colors

The logo introduces two new navy values that become the brand anchors:

```css
/* New brand palette (from logo) */
--brand-navy-dark:   #09264c;  /* Primary brand — logo dark */
--brand-navy-medium: #0e3a67;  /* Secondary brand — logo medium */

/* Existing (keep) */
--brand-blue-500:    #1E40AF;  /* Primary interactive — CTAs, links, active states */
--brand-indigo-500:  #4F46E5;  /* AI identity */
```

**Brand navy** is for identity (logo, navbar background, footer). **Brand blue** remains the interactive color (buttons, links, active states). Don't use navy for CTAs — it's too dark and reads as disabled.

### What Stays

- **Semantic signal colors** (success green, danger red, warning amber, info cyan) — unchanged. Red/green for financial gains/losses is a deeply ingrained convention. Never replace green with blue/teal for positive market movement.
- **Chart color palette** — unchanged. Already colorblind-friendly.
- **AI identity colors** (`--ai-color: #6366F1`, `--ai-accent: #F59E0B`) — unchanged.
- **Interactive state pattern** (default → hover/-600 → active/-700 → disabled/neutral-300) — unchanged.

### Surface Treatment: The "Tonal First" Rule

**Adopt** the Macro-Architect's principle of defining boundaries through background shifts rather than borders — but with a practical exception for data tables.

**For layout** (cards, sections, navigation):
- Define boundaries through surface-level contrast, not 1px borders
- Use `surface-container-lowest` cards floating on `surface` backgrounds
- If a border is needed for accessibility, use `rgba(198, 198, 205, 0.15)` ("ghost border")

**For data-dense components** (tables, comparison grids):
- Borders and zebra-striping are both permitted
- Readability trumps aesthetics in data tables
- Use `neutral-200` for table borders (consistent with current system)

---

## 3. Typography

### What Changes

#### New: Serif/Sans Pairing

Introduce **Noto Serif** as a display typeface for editorial warmth. Pair with **Inter** as the data/body typeface for precision.

```css
/* Display — "The Narrative" */
--font-display: 'Noto Serif', Georgia, 'Times New Roman', serif;

/* Interface — "The Data" */
--font-interface: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                  'Roboto', 'Helvetica Neue', Arial, sans-serif;

/* Monospace — unchanged */
--font-mono: 'SF Mono', 'Monaco', 'Cascadia Code', 'Consolas',
             'Courier New', monospace;
```

#### The "One Serif Hero" Rule

Each page gets **one** Noto Serif heading — the page title (H1). All other headings, body text, labels, and data use Inter. Overusing the serif makes the UI feel like a blog rather than a dashboard.

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Page title (H1) | Noto Serif | 700 | `--text-3xl` (30px), `--text-4xl` (36px) on desktop |
| Section heading (H2) | Inter | 600 | `--text-2xl` (24px) |
| Subsection heading (H3) | Inter | 600 | `--text-xl` (20px) |
| Body text | Inter | 400 | `--text-base` (16px) |
| Labels, captions | Inter | 400 | `--text-sm` (14px) |
| Table headers | Inter | 500, uppercase, 0.05em tracking | `--text-xs` (12px) |
| Numeric data (large) | Inter or Mono | 700, `font-variant-numeric: tabular-nums` | `--text-5xl` (48px) |

#### Font Loading

Both Noto Serif and Inter are Google Fonts. Load with `font-display: swap` to prevent invisible text during load:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Serif:wght@700&display=swap" rel="stylesheet">
```

Only load Noto Serif 700 (bold) — it's only used for H1 hero headings. Inter loads 400, 500, 600, 700.

### What Stays

- **Type scale** (major third / 1.250) — unchanged
- **Line heights** — unchanged
- **Responsive typography rules** — unchanged
- **Tabular numerals for financial data** — unchanged (now explicit: `font-variant-numeric: tabular-nums` on all numeric displays)

---

## 4. Component Updates

### Navbar

| Property | Current | New |
|----------|---------|-----|
| Background | `bg-dark` (Bootstrap) | `--brand-navy-dark` (`#09264c`) |
| Brand element | `bi-graph-up-arrow` icon + "SignalTrackers" | Logo icon SVG (24-28px) + HTML `<span>` "MACROCLARITY" with weight split (no lockup SVG needed — icon + styled text is more flexible and searchable) |
| Tagline | "Comprehensive macro intelligence for individual investors" | "Macro Finance Data & Analysis" |
| Shadow | `0 2px 4px rgba(0,0,0,0.1)` | `0 2px 4px rgba(11,28,48,0.06)` |
| Height, links, active states | unchanged | unchanged |

**Mobile navbar:** Logo icon only (no text). Hamburger menu unchanged.

### Footer

| Property | Current | New |
|----------|---------|-----|
| Background | `bg-dark` | `--brand-navy-dark` (`#09264c`) |
| Text | "SignalTrackers \| Macro Intelligence for Individual Investors \| Data updated daily" | "MacroClarity \| Macro Finance Data & Analysis \| Data updated daily" |

### Cards

Adopt floating card treatment:

```css
.card {
  background: var(--surface-container-lowest);  /* #ffffff */
  border: none;                                  /* Remove default border */
  border-radius: 0.75rem;                        /* 12px — softer than current */
  box-shadow: 0 2px 4px rgba(11, 28, 48, 0.06); /* Navy-tinted shadow */
}
```

Current cards use Bootstrap's default border + slight shadow. New cards float on the surface via shadow alone (tonal separation).

### Buttons

| Type | Current | New |
|------|---------|-----|
| Primary | `btn-primary` (Bootstrap blue) | `--brand-blue-500` (`#1E40AF`) — **unchanged** |
| Secondary | `btn-outline-secondary` | `--surface-container-low` background, `--on-surface` text, no border |
| Ghost/Tertiary | varies | Text-only, subtle underline on hover |

**Not adopted:** The Macro-Architect spec proposed pure black (`#000000`) gradient buttons. We keep brand-blue for primary CTAs — it's more inviting and consistent with the interactive color system.

### Page Backgrounds

```css
body {
  background-color: var(--surface);  /* #f8f9ff — blue-tinted canvas */
}
```

### Chatbot

| Property | Current | New |
|----------|---------|-----|
| Header text | "SignalTrackers AI" | "MacroClarity AI" |
| FAB color, panel styling | unchanged | unchanged |
| AI identity colors | unchanged | unchanged |

### Email Templates

| Property | Current | New |
|----------|---------|-----|
| Header background | `#1e3a5f` | `#09264c` (match logo dark navy) |
| Brand name | "SignalTrackers" | "MacroClarity" |
| Tagline | "Macro Financial Intelligence" | "Macro Finance Data & Analysis" |

---

## 5. Spacing

### Increased Section Spacing

Adopt generous whitespace between major page sections for an editorial, curated feel:

```css
/* Between major page sections */
margin-bottom: var(--space-12);  /* 48px — current */
/* Consider increasing to */
margin-bottom: var(--space-16);  /* 64px — more breathing room */
```

This is a judgment call per-page. Data-dense pages (Explorer, asset detail) may keep `space-12`. Overview pages (Dashboard, Pricing) benefit from `space-16`.

### Unchanged

- Component internal spacing — unchanged
- Card padding — unchanged
- Form field spacing — unchanged
- 4px baseline grid — unchanged

---

## 6. What We Are NOT Doing

Explicitly rejected from the Macro-Architect design system:

| Proposal | Reason for Rejection |
|----------|---------------------|
| Replace green with blue/teal for positive financial signals | Violates deeply ingrained financial convention. Users expect red/green for losses/gains. |
| Pure black (`#000000`) CTA buttons | Clashes with navy surface system. Reads as harsh. Brand-blue is more inviting. |
| Hard ban on all borders | Impractical for data tables. "Tonal first, borders as fallback" is the right balance. |
| Ghost borders at 15% opacity | Fails WCAG contrast requirements. If a border is needed, it must be visible. |
| Frosted glass / backdrop-blur system-wide | Performance concerns on lower-end devices. May use sparingly for chatbot panel only. |
| "Luxury/high-net-worth" positioning language | Our audience is financially literate non-professionals, not private banking clients. |
| Asymmetric layouts as a system rule | Selectively useful, not a system-wide requirement. Bootstrap grid stays. |

---

## 7. Text Replacement Map

Every instance of the old brand name that needs updating:

| File/Location | Current Text | New Text |
|---------------|-------------|----------|
| `base.html` — `<title>` | "SignalTrackers - Macro Intelligence Platform" | "MacroClarity - Macro Finance Data & Analysis" |
| `base.html` — navbar brand | `<i class="bi bi-graph-up-arrow"></i> SignalTrackers` | Logo SVG + "MACROCLARITY" (weight split) |
| `base.html` — navbar tagline | "Comprehensive macro intelligence for individual investors" | "Macro Finance Data & Analysis" |
| `base.html` — chatbot header | "SignalTrackers AI" | "MacroClarity AI" |
| `base.html` — footer | "SignalTrackers \| Macro Intelligence for Individual Investors \| Data updated daily" | "MacroClarity \| Macro Finance Data & Analysis \| Data updated daily" |
| `email/base_email.html` — header | "SignalTrackers" | "MacroClarity" |
| `email/base_email.html` — tagline | "Macro Financial Intelligence" | "Macro Finance Data & Analysis" |
| All page templates — `<title>` | "Page - SignalTrackers" | "Page - MacroClarity" |
| `auth/register.html` — hero | "Unlock the Full Power of SignalTrackers" | "Unlock the Full Power of MacroClarity" |
| `docs/design-system.md` | "SignalTrackers" references | "MacroClarity" |

---

## 8. Asset Checklist

Files to create or update for the rebrand:

| Asset | Status | Notes |
|-------|--------|-------|
| Logo SVG (icon only) | Done | `docs/macroclarityrebrand/MacroClarityLogoOnly.svg` |
| Logo SVG (icon + text lockup) | Not needed for implementation | Navbar uses icon SVG + HTML `<span>` text (more flexible, searchable). Lockup SVG only needed later for OG images / social cards if desired. |
| Favicon set (16x16, 32x32, ICO) | Needed | Generate from logo SVG, test legibility at small sizes |
| Apple touch icon (180x180 PNG) | Needed | |
| Open Graph image (1200x630) | Needed | Full lockup + tagline on brand navy background |
| Noto Serif + Inter font integration | Needed | Google Fonts link in `base.html` `<head>` |
| Updated `dashboard.css` variables | Needed | New surface tokens, shadow tints, brand navy values |
| Updated `design-system.md` | Needed | Reflect all changes in this spec |

---

## 9. Implementation Sequence

Suggested order for engineering implementation:

1. **Font loading** — Add Google Fonts link, define CSS custom properties for font families
2. **CSS variables** — Add surface tokens, brand navy, shadow tint, `--on-surface`
3. **Logo + favicon** — Place SVG assets in `static/img/`, generate favicon set
4. **Navbar** — Replace brand element (icon + text), update background color
5. **Footer** — Update text and background
6. **Page backgrounds** — Switch `body` background to `--surface`
7. **Card treatment** — Remove borders, add shadow, increase border-radius
8. **Typography** — Apply Noto Serif to H1 page titles, Inter to everything else
9. **Text replacement** — All "SignalTrackers" → "MacroClarity" across templates
10. **Email templates** — Update header, branding, colors
11. **Design system doc** — Update `docs/design-system.md` to reflect new system
