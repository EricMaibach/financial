# Feature 3.1: Mobile-First Content Pages - Design Specification

**Feature:** #81
**Status:** Design Specification - Ready for PM Review
**Designer:** UI Designer
**Date:** 2026-02-20
**Version:** 1.0

---

## Overview

This specification defines the mobile-first redesign of content-heavy pages (Explorer and 6 asset class pages) to prioritize chart visibility and reduce scroll length on mobile devices while maintaining desktop excellence.

### Scope

**Pages to redesign:**
1. Explorer page (`/explorer`)
2. Credit page (`/credit`)
3. Rates page (`/rates`)
4. Dollar page (`/dollar`)
5. Equities page (`/equities`)
6. Crypto page (`/crypto`)
7. Safe Havens page (`/safe-havens`)

### Problem Statement

Current pages use desktop-first information hierarchy:
- Charts buried below extensive statistics sections (requiring 1500-2000px scroll on mobile)
- Primary content (visual data) treated as secondary
- Information overload prevents quick market checks on mobile
- Users must scroll extensively to see what they came for (the chart)

### Success Criteria (PM-Approved)

**Mobile (375px viewport):**
- ✓ Charts visible within first screen (no scrolling required)
- ✓ Total scroll length reduced by 50%+
- ✓ Statistics collapsed by default with clear expand affordance
- ✓ Full chart interactivity maintained (tap-based tooltips)
- ✓ Metric selector sticky/accessible without scrolling (Explorer page)
- ✓ Touch targets meet 44px minimum

**Tablet (768px viewport):**
- ✓ Hybrid approach: Chart prominent + 3-5 key stats visible
- ✓ Detailed metadata remains collapsed
- ✓ No loss of functionality

**Desktop (1920px viewport):**
- ✓ Maintain or improve current experience
- ✓ No regression in information density or functionality

---

## Design Principles

1. **Chart Prominence** - Visual data is the hero, not buried content
2. **Progressive Disclosure** - Show essentials first, details on demand
3. **Mobile-First, Desktop-Excellence** - Design for constraints, scale up with power
4. **Consistent Patterns** - All 7 pages use identical mobile layouts
5. **No Information Loss** - Everything accessible, just reordered by priority

**Design System Reference:** [docs/design-system.md](../design-system.md)

---

## Layout Specifications

### Mobile Layout (< 768px)

#### Visual Hierarchy (Top to Bottom)

```
┌─────────────────────────────┐
│ Navigation Bar (64px)       │ ← Existing nav
├─────────────────────────────┤
│ Page Title                  │ ← "Credit Markets" etc.
│ Last Updated: [time]        │ ← Context
├─────────────────────────────┤
│ [Metric Selector] (sticky)  │ ← Explorer only, 48px min-height
├─────────────────────────────┤
│                             │
│                             │
│    📊 CHART                 │ ← HERO ELEMENT
│    (Primary Focus)          │ ← 50-60% of viewport height
│    Interactive              │
│                             │
│                             │
├─────────────────────────────┤
│ Time Range Controls         │ ← Chart controls (1D, 1W, 1M, etc.)
├─────────────────────────────┤
│ ──── ⌄ Market Statistics ───│ ← COLLAPSED by default
├─────────────────────────────┤
│ ──── ⌄ About This Metric ───│ ← COLLAPSED by default
├─────────────────────────────┤
│ ──── ⌄ Related Indicators ───│ ← COLLAPSED (if applicable)
└─────────────────────────────┘

TOTAL HEIGHT: ~800-1000px (50-60% reduction vs. current ~2000px)
```

#### Detailed Component Breakdown

**1. Page Header**
```css
Height: Auto (min 80px)
Padding: var(--space-4) var(--space-4)
Background: white or var(--neutral-50)

Elements:
- H1: Page title (text-2xl on mobile, text-3xl on tablet+)
- Last Updated: text-sm, neutral-500
- Spacing: space-4 between elements
```

**2. Metric Selector (Explorer Page Only)**
```css
Position: Sticky
Top: 64px (below fixed nav)
Z-index: 100
Height: Min 48px (touch target)
Padding: var(--space-3) var(--space-4)
Background: white
Border-bottom: 1px solid var(--neutral-200)
Box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) (when stuck)

Behavior:
- Remains accessible at top of viewport
- User can change metrics without scrolling up
- Clear visual indication when sticky (subtle shadow)
```

**3. Chart Container (HERO ELEMENT)**
```css
Height: 50-60vh (viewport-relative for prominence)
Min-height: 300px (ensure usability)
Max-height: 400px (prevent overwhelming)
Padding: var(--space-4)
Background: white
Border: 1px solid var(--neutral-200)
Border-radius: 8px
Margin: var(--space-4)

Chart Behavior:
- Full interactivity maintained
- Tap for tooltip (not hover)
- Pinch to zoom (if applicable)
- Swipe for time navigation (optional enhancement)

Design System Reference: Chart colors from design-system.md Chart Colors
```

**4. Time Range Controls**
```css
Display: Flex
Justify-content: Center
Gap: var(--space-2)
Padding: var(--space-3) var(--space-4)
Background: white

Button specs:
- Min-height: 44px (touch target)
- Min-width: 60px
- Padding: var(--space-2) var(--space-3)
- Font-size: var(--text-sm)
- Border-radius: 6px
- Active state: brand-blue-500 background, white text
- Inactive: neutral-200 background, neutral-700 text
```

**5. Collapsible Sections (Progressive Disclosure)**

```
┌─────────────────────────────┐
│ ──── ⌄ Market Statistics ───│ ← Header (collapsed)
└─────────────────────────────┘

When expanded:
┌─────────────────────────────┐
│ ──── ⌃ Market Statistics ───│ ← Header (expanded)
├─────────────────────────────┤
│                             │
│ [Statistics Content]        │ ← All current stats
│ - Current Value             │
│ - Change (24h)              │
│ - Change (7d)               │
│ - etc.                      │
│                             │
└─────────────────────────────┘
```

**Collapsible Section Header:**
```css
Display: Flex
Align-items: Center
Justify-content: Space-between
Min-height: 56px (touch target)
Padding: var(--space-4)
Background: var(--neutral-50)
Border-top: 1px solid var(--neutral-200)
Border-bottom: 1px solid var(--neutral-200)
Cursor: Pointer

States:
- Default: Collapsed (chevron down ⌄)
- Hover: Background var(--neutral-100)
- Expanded: Chevron up (⌃), border-color var(--neutral-300)
- Active: Transform feedback (subtle press effect)

Typography:
- Font-size: var(--text-lg)
- Font-weight: 600
- Color: var(--neutral-700)
- Icon: 20px, neutral-500
```

**Collapsible Section Content:**
```css
Padding: var(--space-4)
Background: white
Animation: Slide down 250ms ease-out (expand)
           Slide up 200ms ease-in (collapse)
Max-height: None (content-driven)

Statistics Layout (within expanded section):
- Grid: 2 columns on mobile
- Gap: var(--space-4)
- Each stat: Label + Value + Change indicator
```

**6. Section Order (Collapsed State)**
```
Priority 1: ──── ⌄ Market Statistics ────
  (Current values, 24h changes, key metrics)

Priority 2: ──── ⌄ About This Metric ────
  (Description, interpretation, what it measures)

Priority 3: ──── ⌄ Related Indicators ────
  (Cross-references, correlated metrics)
```

---

### Tablet Layout (768px - 1023px)

#### Hybrid Approach

```
┌───────────────────────────────────────────┐
│ Navigation Bar (64px)                     │
├───────────────────────────────────────────┤
│ Page Title              Last Updated      │
├───────────────────────────────────────────┤
│ [Metric Selector] (Explorer only)         │
├────────────────────┬──────────────────────┤
│                    │ 📊 Key Stats (3-5)   │
│                    │                      │
│   📊 CHART         │ • Current Value      │
│   (Primary)        │ • 24h Change         │
│                    │ • 7d Change          │
│   ~60% width       │ • Volume (if appl.)  │
│                    │ • Market Cap         │
│                    │                      │
│                    │ ~40% width           │
├────────────────────┴──────────────────────┤
│ Time Range Controls (centered)            │
├───────────────────────────────────────────┤
│ ──── ⌄ About This Metric ──── (collapsed) │
├───────────────────────────────────────────┤
│ ──── ⌄ Additional Statistics ── (collapsed)│
└───────────────────────────────────────────┘
```

**Key Differences from Mobile:**
- **Chart + Key Stats side-by-side** (60/40 split)
- 3-5 most important statistics visible without expansion
- Detailed statistics still use progressive disclosure
- Chart maintains prominence but shares viewport
- Reduced scroll length vs. desktop, better than mobile

**Layout Specifications:**
```css
@media (min-width: 768px) {
  .content-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr; /* 60/40 split */
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .chart-container {
    height: 400px; /* Fixed height on tablet */
  }

  .key-stats-panel {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    padding: var(--space-5);
    background: white;
    border: 1px solid var(--neutral-200);
    border-radius: 8px;
  }

  .stat-card {
    /* Metric card from design system */
    border-left: 4px solid var(--info-600);
    padding: var(--space-3);
  }
}
```

---

### Desktop Layout (1024px+)

#### Maintain Current Excellence, Optimize Further

```
┌─────────────────────────────────────────────────────────┐
│ Navigation Bar (64px)                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Page Title                          Last Updated        │
│                                                         │
├────────────────────┬────────────────────────────────────┤
│                    │                                    │
│                    │  📊 Statistics Grid (expanded)     │
│   📊 CHART         │                                    │
│   (Primary)        │  ┌──────┬──────┬──────┬──────┐    │
│                    │  │ Stat │ Stat │ Stat │ Stat │    │
│   ~70% width       │  │  1   │  2   │  3   │  4   │    │
│   500-600px height │  └──────┴──────┴──────┴──────┘    │
│                    │  ┌──────┬──────┬──────┬──────┐    │
│                    │  │ Stat │ Stat │ Stat │ Stat │    │
│                    │  │  5   │  6   │  7   │  8   │    │
│                    │  └──────┴──────┴──────┴──────┘    │
│                    │                                    │
│                    │  ~30% width                        │
├────────────────────┴────────────────────────────────────┤
│ Time Range Controls (left-aligned or centered)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ About This Metric (expanded or collapsible)            │
│ [Full description, interpretation, methodology]         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Related Indicators / Additional Context                 │
└─────────────────────────────────────────────────────────┘
```

**Key Characteristics:**
- Chart remains primary but statistics fully visible (no scrolling for key info)
- Grid layout for statistics (4-column or adaptive)
- All content accessible with minimal scrolling
- Progressive disclosure optional (can show more by default)
- Optimized for power users doing deep analysis

**Layout Specifications:**
```css
@media (min-width: 1024px) {
  .content-grid {
    grid-template-columns: 2fr 1fr; /* 66/33 split */
    gap: var(--space-8);
    max-width: var(--container-xl); /* 1280px from design system */
    margin: 0 auto;
    padding: var(--space-8);
  }

  .chart-container {
    height: 500px; /* Larger chart for desktop */
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr); /* 2-column stats */
    gap: var(--space-4);
  }
}

@media (min-width: 1280px) {
  .content-grid {
    gap: var(--space-10);
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr); /* Keep 2-column */
    /* OR if more stats: repeat(3, 1fr) for 3-column */
  }
}
```

---

## Reusable Components

### 1. Collapsible Section Component

**Component Name:** `CollapsibleSection`

**Usage:**
```html
<div class="collapsible-section" data-collapsed="true">
  <button class="collapsible-section__header" aria-expanded="false">
    <h3 class="collapsible-section__title">Market Statistics</h3>
    <svg class="collapsible-section__icon" aria-hidden="true">
      <!-- Chevron icon -->
    </svg>
  </button>
  <div class="collapsible-section__content" hidden>
    <!-- Section content -->
  </div>
</div>
```

**Behavior:**
- Click/tap header to toggle
- Smooth expand/collapse animation (250ms)
- Chevron rotates 180° when expanded
- ARIA attributes for accessibility
- Keyboard support (Space/Enter to toggle)
- Remember state across page reloads (optional)

**CSS:**
```css
.collapsible-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 56px;
  padding: var(--space-4);
  background: var(--neutral-50);
  border: none;
  border-top: 1px solid var(--neutral-200);
  border-bottom: 1px solid var(--neutral-200);
  cursor: pointer;
  transition: background-color 150ms ease;
}

.collapsible-section__header:hover {
  background: var(--neutral-100);
}

.collapsible-section__header:focus {
  outline: 2px solid var(--brand-blue-500);
  outline-offset: 2px;
}

.collapsible-section__title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--neutral-700);
  margin: 0;
}

.collapsible-section__icon {
  width: 20px;
  height: 20px;
  color: var(--neutral-500);
  transition: transform 250ms ease;
}

.collapsible-section__header[aria-expanded="true"] .collapsible-section__icon {
  transform: rotate(180deg);
}

.collapsible-section__content {
  padding: var(--space-4);
  background: white;
  overflow: hidden;
  transition: max-height 250ms ease-out;
}

.collapsible-section__content[hidden] {
  display: none;
}
```

**JavaScript Behavior:**
```javascript
// Toggle on click
header.addEventListener('click', () => {
  const isExpanded = header.getAttribute('aria-expanded') === 'true';
  header.setAttribute('aria-expanded', !isExpanded);
  content.hidden = isExpanded;

  // Optional: Save state to localStorage
  localStorage.setItem(`section-${sectionId}`, !isExpanded);
});

// Keyboard support
header.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    header.click();
  }
});
```

### 2. Sticky Metric Selector (Explorer Page)

**Component Name:** `StickyMetricSelector`

**Usage:**
```html
<div class="sticky-selector" data-stuck="false">
  <label for="metricSelector" class="sticky-selector__label">
    Select Metric:
  </label>
  <select id="metricSelector" class="sticky-selector__dropdown">
    <option value="">-- Choose a metric --</option>
    <!-- Metric options -->
  </select>
</div>
```

**Behavior:**
- Becomes sticky after scrolling past page header
- Adds subtle shadow when stuck for visual feedback
- Remains accessible without scrolling to top
- Min 48px height for touch target compliance

**CSS:**
```css
.sticky-selector {
  position: sticky;
  top: 64px; /* Below fixed nav */
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 48px;
  padding: var(--space-3) var(--space-4);
  background: white;
  border-bottom: 1px solid var(--neutral-200);
  transition: box-shadow 200ms ease;
}

.sticky-selector[data-stuck="true"] {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.sticky-selector__dropdown {
  flex: 1;
  min-height: 44px; /* Touch target */
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-base);
  border: 1px solid var(--neutral-300);
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.sticky-selector__dropdown:focus {
  outline: none;
  border-color: var(--brand-blue-500);
  box-shadow: 0 0 0 3px var(--brand-blue-100);
}
```

**JavaScript Behavior:**
```javascript
// Detect when selector becomes stuck
const observer = new IntersectionObserver(
  ([e]) => {
    selector.setAttribute('data-stuck', e.intersectionRatio < 1);
  },
  { threshold: [1] }
);

observer.observe(selector);
```

### 3. Responsive Chart Container

**Component Name:** `ChartContainer`

**Responsive Sizing:**
```css
.chart-container {
  width: 100%;
  padding: var(--space-4);
  background: white;
  border: 1px solid var(--neutral-200);
  border-radius: 8px;
  margin: var(--space-4);
}

/* Mobile: Viewport-relative height for prominence */
@media (max-width: 767px) {
  .chart-container {
    height: 50vh; /* Prominent on mobile */
    min-height: 300px;
    max-height: 400px;
  }
}

/* Tablet: Fixed height */
@media (min-width: 768px) and (max-width: 1023px) {
  .chart-container {
    height: 400px;
  }
}

/* Desktop: Larger fixed height */
@media (min-width: 1024px) {
  .chart-container {
    height: 500px;
  }
}

/* Ensure chart responsiveness */
.chart-container canvas {
  max-width: 100%;
  max-height: 100%;
}
```

**Chart Interactivity (Mobile):**
- Tap for tooltip (not hover)
- Tooltip shows data point details
- Consider tap-and-hold for more info
- Pinch to zoom (optional enhancement)

---

## Responsive Breakpoints

Following design system breakpoints:

```css
/* Mobile-first base styles */
/* < 640px: Base mobile styles */

/* Large phones (landscape) */
@media (min-width: 640px) {
  /* Slightly larger spacing, still single column */
}

/* Tablets (portrait) */
@media (min-width: 768px) {
  /* Hybrid layout: Chart + key stats side-by-side */
  /* 3-5 key stats visible */
}

/* Tablets (landscape) / Small laptops */
@media (min-width: 1024px) {
  /* Desktop layout */
  /* Chart + stats grid */
  /* More information density */
}

/* Desktop */
@media (min-width: 1280px) {
  /* Enhanced desktop layout */
  /* Wider containers, more spacing */
}

/* Large desktop */
@media (min-width: 1536px) {
  /* Max container width, optimal spacing */
}
```

---

## Page-Specific Notes

### Explorer Page
- **Unique element:** Sticky metric selector
- **Chart updates:** On metric selection change
- **URL state:** Consider updating URL with selected metric (e.g., `/explorer?metric=vix`)

### Asset Class Pages (Credit, Rates, Dollar, Equities, Crypto, Safe Havens)
- **No metric selector** (fixed asset class)
- **Consistent layout:** All use same template
- **Section variations:** Some may have asset-specific sections (e.g., Crypto might have "Market Cap" section)

### Common Sections Across All Pages
1. **Market Statistics** (always present, collapsed on mobile)
2. **About This Metric/Asset** (always present, collapsed on mobile)
3. **Related Indicators** (optional, if present, collapsed on mobile)

---

## Design System Integration

### Colors
- Page background: `var(--neutral-50)`
- Card backgrounds: `white`
- Borders: `var(--neutral-200)`
- Text: `var(--neutral-600)` (body), `var(--neutral-700)` (headings)
- Interactive elements: `var(--brand-blue-500)`
- Chart colors: Use design system chart palette (colorblind-friendly)

### Typography
- Page title (H1): `var(--text-3xl)`, `font-weight: 700`, mobile: `var(--text-2xl)`
- Section headers (H2): `var(--text-xl)`, `font-weight: 600`
- Body text: `var(--text-base)`, `line-height: 1.6`
- Labels: `var(--text-sm)`, `color: var(--neutral-500)`

### Spacing
- Page padding: `var(--space-4)` mobile, `var(--space-8)` desktop
- Section spacing: `var(--space-6)` mobile, `var(--space-8)` desktop
- Component padding: `var(--space-4)` to `var(--space-6)`
- Grid gaps: `var(--space-4)` to `var(--space-6)`

### Components
- Collapsible sections: From design system progressive disclosure pattern
- Buttons: Design system button specs (44px min-height, proper states)
- Cards: Design system metric cards (4px semantic left border)

**Reference:** [docs/design-system.md](../design-system.md)

---

## Accessibility Requirements

### Touch Targets
- ✓ All interactive elements minimum 44px height
- ✓ Metric selector: 44-48px
- ✓ Collapsible section headers: 56px
- ✓ Time range buttons: 44px
- ✓ Adequate spacing between targets (8px minimum)

### Keyboard Navigation
- ✓ All interactive elements accessible via Tab
- ✓ Collapsible sections toggle with Space/Enter
- ✓ Dropdowns operable with keyboard
- ✓ Visible focus indicators (2px outline, brand-blue-500)

### Screen Readers
- ✓ Semantic HTML (`<section>`, `<article>`, `<aside>`)
- ✓ Proper heading hierarchy (H1 → H2 → H3)
- ✓ ARIA labels for icon-only buttons
- ✓ `aria-expanded` for collapsible sections
- ✓ Alt text for chart images (if applicable)
- ✓ Meaningful page titles

### Color Contrast
- ✓ All text meets WCAG 2.1 AA (4.5:1 minimum)
- ✓ UI elements meet 3:1 contrast
- ✓ Chart colors from colorblind-friendly palette
- ✓ Don't rely on color alone (use icons + color)

### Mobile-Specific
- ✓ No horizontal scrolling on any viewport
- ✓ Adequate spacing for "fat finger" tapping
- ✓ Tap tooltips (not hover-dependent)
- ✓ Pinch to zoom doesn't break layout

**Compliance:** WCAG 2.1 AA minimum

---

## Animation & Transitions

### Collapsible Sections
```css
Expand: 250ms ease-out
Collapse: 200ms ease-in
Max-height animation (smooth reveal)
```

### Sticky Elements
```css
Shadow transition: 200ms ease (when element becomes stuck)
```

### Buttons & Interactive Elements
```css
Hover/Active states: 150ms ease
Focus indicators: Instant (no delay)
```

### Chart Rendering
```css
Initial render: Fade in 300ms (optional)
Data updates: Smooth transitions (defer to chart library)
```

**Keep animations subtle and purposeful** - avoid gratuitous motion.

---

## Implementation Guidance

### Phase 1: Reusable Components (US-3.1.1)
**Goal:** Build foundational components used across all pages

1. **CollapsibleSection Component**
   - HTML structure
   - CSS styling
   - JavaScript toggle behavior
   - Keyboard accessibility
   - ARIA attributes

2. **StickyMetricSelector Component** (Explorer-specific)
   - Sticky positioning
   - Shadow effect on scroll
   - Touch-optimized dropdown

3. **ResponsiveChartContainer Component**
   - Viewport-relative sizing on mobile
   - Fixed sizing on tablet/desktop
   - Chart library integration (tap tooltips)

4. **KeyStatsPanel Component** (Tablet+)
   - Grid layout for statistics
   - Metric cards from design system

**Deliverable:** Reusable component library that can be applied to all 7 pages

### Phase 2: Explorer Page (US-3.1.2)
**Goal:** Implement mobile-first layout on Explorer page

1. Apply new layout structure
2. Integrate sticky metric selector
3. Make statistics collapsible by default
4. Test chart interactivity on mobile (tap tooltips)
5. Verify responsive breakpoints
6. Accessibility audit

**Test:** Playwright screenshots at 375px, 768px, 1920px
**Success:** Chart visible without scroll, 50%+ scroll reduction

### Phase 3: Asset Class Pages (US-3.1.3, US-3.1.4)
**Goal:** Apply proven pattern to remaining 6 pages

1. Credit & Rates pages (US-3.1.3)
2. Dollar, Equities, Crypto, Safe Havens pages (US-3.1.4)

Each page:
- Apply layout template
- Customize sections (if needed)
- Ensure consistency with Explorer
- Test responsiveness
- Accessibility audit

**Advantage:** Most work done in Phase 1, Phase 3 is primarily templating

### Technical Notes

**HTML Structure:**
```html
<main class="content-page">
  <header class="page-header">
    <h1>{{ page_title }}</h1>
    <span class="last-updated">{{ updated_time }}</span>
  </header>

  <!-- Explorer only -->
  <div class="sticky-selector" v-if="isExplorerPage">
    <select id="metricSelector">...</select>
  </div>

  <div class="content-grid">
    <!-- Mobile: Stacked, Tablet: Side-by-side, Desktop: Enhanced -->
    <div class="chart-container">
      <canvas id="chart"></canvas>
    </div>

    <!-- Tablet+: Key stats visible -->
    <aside class="key-stats-panel" v-if="viewportWidth >= 768">
      <!-- 3-5 key statistics -->
    </aside>
  </div>

  <div class="time-range-controls">
    <button>1D</button>
    <button>1W</button>
    <!-- etc -->
  </div>

  <!-- Progressive disclosure sections -->
  <div class="collapsible-section">
    <button class="collapsible-section__header">
      Market Statistics
    </button>
    <div class="collapsible-section__content" hidden>
      <!-- All statistics -->
    </div>
  </div>

  <div class="collapsible-section">
    <button class="collapsible-section__header">
      About This Metric
    </button>
    <div class="collapsible-section__content" hidden>
      <!-- Description -->
    </div>
  </div>
</main>
```

**CSS Architecture:**
- Mobile-first media queries
- CSS custom properties from design system
- BEM naming convention for components
- Utility classes for common patterns

**JavaScript:**
- Vanilla JS or framework (currently using Flask/Jinja2, likely vanilla JS)
- Progressive enhancement (works without JS, enhanced with JS)
- LocalStorage for section state (optional)
- IntersectionObserver for sticky element detection

**Testing:**
- Playwright screenshots at all breakpoints
- Manual testing on real devices (iPhone, iPad, Android)
- Keyboard navigation testing
- Screen reader testing (NVDA/JAWS)
- Color contrast validation

---

## Success Validation

### Playwright Screenshots
Create screenshots at these viewports for all 7 pages:
- Mobile: 375x667 (iPhone SE)
- Tablet: 768x1024 (iPad portrait)
- Desktop: 1920x1080

**Verify:**
- ✓ Chart visible in first screen on mobile (no scroll)
- ✓ Scroll length reduced by 50%+ vs. current
- ✓ Progressive disclosure working (sections collapsed)
- ✓ No horizontal scroll on any viewport

### Manual Testing Checklist
- [ ] All 7 pages use consistent mobile layout
- [ ] Charts visible without scrolling on mobile
- [ ] Collapsible sections work (click/tap to expand)
- [ ] Sticky selector works on Explorer (mobile)
- [ ] Chart tooltips work on tap (mobile)
- [ ] All interactive elements ≥44px touch target
- [ ] Keyboard navigation works (Tab, Space, Enter)
- [ ] No regressions on desktop
- [ ] Touch targets adequately spaced
- [ ] Color contrast meets WCAG AA
- [ ] Screen reader announces sections correctly

### Acceptance Criteria (from Feature #81)
- [x] All 7 pages redesigned for mobile-first ← This spec covers all
- [ ] Playwright screenshots demonstrate chart prominence ← Post-implementation
- [ ] Desktop experience maintained or improved ← Specified in desktop section
- [ ] Consistent mobile patterns across pages ← Reusable components ensure this
- [ ] No horizontal scrolling on any viewport ← Responsive design prevents this
- [ ] Touch targets meet 44px minimum ← All specs meet this standard

---

## Open Questions / Future Enhancements

### Potential Enhancements (Out of Scope for 3.1)
1. **Chart gestures:** Swipe between time ranges, pinch to zoom
2. **Section state persistence:** Remember user's expanded/collapsed preferences
3. **Lazy loading:** Load statistics only when section expanded (performance)
4. **Inline metric comparison:** Compare multiple metrics on one chart (Explorer)
5. **Export functionality:** Download chart as image/PDF
6. **Sharing:** Share specific metric view via URL

These can be considered for future features but are not required for Feature 3.1.

---

## Changelog

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-20 | Initial design specification based on PM requirements | UI Designer |

---

## Next Steps

1. **PM Review:** @pm please review this specification and approve
2. **Questions/Feedback:** Comment on issue #81 with any changes needed
3. **Approval:** PM approves spec, marks as ready for engineering
4. **Engineering Handoff:** @engineer receives spec for implementation
5. **User Stories:** PM creates detailed user stories referencing this spec
6. **Implementation:** Engineer builds according to spec
7. **Design Review:** Designer reviews implementation for compliance
8. **PM Validation:** PM validates against acceptance criteria

**Status:** ⏳ Awaiting PM Review

---

**Design System Reference:** [docs/design-system.md](../design-system.md)
**Feature Issue:** #81
**Related Feature:** #82 (Chatbot Mobile-First Redesign)
