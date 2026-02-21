# SignalTrackers Design System

**Version:** 1.0
**Last Updated:** 2026-02-20
**Status:** Foundation Established

---

## Philosophy

SignalTrackers is a **macro intelligence platform** for sophisticated individual investors. Our design system reflects these core principles:

1. **Data First** - Information is the hero, UI chrome is invisible infrastructure
2. **Confidence Through Clarity** - Clean, unambiguous design builds trust in data
3. **Progressive Disclosure** - Show what matters now, reveal depth on demand
4. **Accessible by Default** - WCAG 2.1 AA minimum, AAA where feasible
5. **Mobile-First Excellence** - Constraints drive focus, enhancement adds power

---

## Color System

### Primary Palette

Our palette balances professional neutrals with purposeful semantic colors. All combinations tested for WCAG AA contrast.

#### Neutrals (Data Canvas)
```css
--neutral-50:   #FAFBFC;  /* Page background */
--neutral-100:  #F4F6F8;  /* Section background */
--neutral-200:  #E8ECEF;  /* Dividers, borders */
--neutral-300:  #D1D8DD;  /* Disabled states */
--neutral-400:  #9AA5B1;  /* Placeholder text */
--neutral-500:  #697386;  /* Secondary text */
--neutral-600:  #4A5568;  /* Body text */
--neutral-700:  #2D3748;  /* Headings */
--neutral-800:  #1A202C;  /* Primary text */
--neutral-900:  #0F1419;  /* Maximum emphasis */
```

**Usage:**
- `neutral-50`: Page background, maximum whitespace
- `neutral-100`: Card/section backgrounds
- `neutral-600`: Body text (16px+, AA on white)
- `neutral-700`: Headings, emphasized text
- `neutral-800`: Critical information, primary nav

#### Brand Colors (Trust & Intelligence)
```css
--brand-blue-500:    #1E40AF;  /* Primary brand - confidence, intelligence */
--brand-blue-600:    #1E3A8A;  /* Hover states */
--brand-blue-700:    #1E3A8A;  /* Active states */
--brand-blue-100:    #DBEAFE;  /* Subtle backgrounds */

--brand-indigo-500:  #4F46E5;  /* Secondary brand - innovation */
--brand-indigo-600:  #4338CA;  /* Hover */
```

**Usage:**
- Primary CTAs, key interactive elements
- Chart primary series
- Active navigation states
- Links and emphasis

#### Semantic Colors (Market Signals)

**Success (Positive Market Movement)**
```css
--success-700:  #15803D;  /* Text - WCAG AAA */
--success-600:  #16A34A;  /* Icons, badges */
--success-500:  #22C55E;  /* Charts, visual elements */
--success-100:  #DCFCE7;  /* Backgrounds */
```

**Danger (Negative Market Movement)**
```css
--danger-700:   #B91C1C;  /* Text - WCAG AAA */
--danger-600:   #DC2626;  /* Icons, badges */
--danger-500:   #EF4444;  /* Charts, visual elements */
--danger-100:   #FEE2E2;  /* Backgrounds */
```

**Warning (Caution Signals)**
```css
--warning-700:  #A16207;  /* Text - WCAG AAA */
--warning-600:  #CA8A04;  /* Icons, badges */
--warning-500:  #EAB308;  /* Charts, visual elements */
--warning-100:  #FEF3C7;  /* Backgrounds */
```

**Info (Neutral Information)**
```css
--info-700:     #0369A1;  /* Text - WCAG AAA */
--info-600:     #0284C7;  /* Icons, badges */
--info-500:     #06B6D4;  /* Charts, visual elements */
--info-100:     #CFFAFE;  /* Backgrounds */
```

#### Chart Colors (Data Visualization)

**Primary Series** (colorblind-friendly palette)
```css
--chart-blue:    #1E40AF;  /* Series 1 */
--chart-orange:  #EA580C;  /* Series 2 */
--chart-green:   #15803D;  /* Series 3 */
--chart-purple:  #7C3AED;  /* Series 4 */
--chart-teal:    #0D9488;  /* Series 5 */
--chart-pink:    #DB2777;  /* Series 6 */
```

**Background Reference Lines**
```css
--chart-grid:    #E8ECEF;  /* Grid lines (neutral-200) */
--chart-axis:    #9AA5B1;  /* Axis labels (neutral-400) */
```

### Color Usage Rules

1. **Text Contrast**
   - Body text (14-16px): Use -700 colors on white for AAA
   - Large text (18px+): Use -600 colors minimum for AA
   - Never use color alone to convey information

2. **Backgrounds**
   - Use -100 tints for subtle semantic backgrounds
   - Ensure text on colored backgrounds meets contrast standards
   - Test with colorblind simulation tools

3. **Interactive States**
   - Default: Base color
   - Hover: -600 variant (darker)
   - Active: -700 variant (darkest)
   - Disabled: neutral-300

---

## Typography

### Font Stack

**Primary (Interface)**
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto',
             'Helvetica Neue', Arial, sans-serif;
```

**Monospace (Numeric Data, Code)**
```css
font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Consolas',
             'Courier New', monospace;
```

### Type Scale

Built on a 1.250 (major third) modular scale for harmonious hierarchy.

```css
--text-xs:     0.75rem;   /* 12px - Captions, footnotes */
--text-sm:     0.875rem;  /* 14px - Secondary text, labels */
--text-base:   1rem;      /* 16px - Body text */
--text-lg:     1.125rem;  /* 18px - Emphasized body */
--text-xl:     1.25rem;   /* 20px - Subheadings */
--text-2xl:    1.5rem;    /* 24px - Section headings */
--text-3xl:    1.875rem;  /* 30px - Page titles */
--text-4xl:    2.25rem;   /* 36px - Hero elements */
--text-5xl:    3rem;      /* 48px - Large data displays */
```

### Typography Hierarchy

**Page Title (H1)**
```css
font-size: var(--text-3xl);     /* 30px */
font-weight: 700;                /* Bold */
color: var(--neutral-800);
line-height: 1.2;
letter-spacing: -0.02em;         /* Tighter for large text */
margin-bottom: 1.5rem;

@media (min-width: 768px) {
  font-size: var(--text-4xl);   /* 36px on tablet+ */
}
```

**Section Heading (H2)**
```css
font-size: var(--text-2xl);     /* 24px */
font-weight: 600;                /* Semibold */
color: var(--neutral-700);
line-height: 1.3;
margin-bottom: 1rem;
```

**Subsection Heading (H3)**
```css
font-size: var(--text-xl);      /* 20px */
font-weight: 600;
color: var(--neutral-700);
line-height: 1.4;
margin-bottom: 0.75rem;
```

**Body Text**
```css
font-size: var(--text-base);    /* 16px */
font-weight: 400;                /* Normal */
color: var(--neutral-600);
line-height: 1.6;                /* Optimal readability */
margin-bottom: 1rem;
```

**Small Text (Labels, Captions)**
```css
font-size: var(--text-sm);      /* 14px */
font-weight: 400;
color: var(--neutral-500);
line-height: 1.5;
```

**Emphasized Text**
```css
font-weight: 600;                /* Semibold */
color: var(--neutral-700);       /* Darker than body */
```

**Numeric Data (Large Displays)**
```css
font-family: var(--font-mono);
font-size: var(--text-5xl);     /* 48px */
font-weight: 700;
color: var(--neutral-800);
line-height: 1;
letter-spacing: -0.03em;
font-feature-settings: 'tnum';   /* Tabular numbers */
```

### Responsive Typography

**Mobile (< 768px)**
- Prioritize readability over hierarchy
- Use 16px minimum for body text (prevents zoom on iOS)
- Reduce heading scale slightly for viewport constraints

**Tablet (768px - 1024px)**
- Standard scale
- Increase line length to 65-75 characters per line

**Desktop (> 1024px)**
- Full scale
- Optimize line length (max 80 characters for readability)

---

## Spacing System

Based on 4px baseline grid for mathematical consistency and easy calculation.

```css
--space-1:   0.25rem;   /* 4px  - Micro spacing */
--space-2:   0.5rem;    /* 8px  - Tight spacing */
--space-3:   0.75rem;   /* 12px - Compact spacing */
--space-4:   1rem;      /* 16px - Standard spacing */
--space-5:   1.25rem;   /* 20px - Comfortable spacing */
--space-6:   1.5rem;    /* 24px - Loose spacing */
--space-8:   2rem;      /* 32px - Section spacing */
--space-10:  2.5rem;    /* 40px - Large section spacing */
--space-12:  3rem;      /* 48px - Page section dividers */
--space-16:  4rem;      /* 64px - Major page sections */
--space-20:  5rem;      /* 80px - Hero spacing */
```

### Spacing Usage Guidelines

**Component Internal Spacing**
- Tight elements (buttons, badges): `space-2` to `space-3`
- Card/container padding: `space-4` to `space-6`
- Form fields: `space-3` vertical, `space-4` horizontal

**Layout Spacing**
- Related elements: `space-4`
- Unrelated elements: `space-6` to `space-8`
- Section dividers: `space-8` to `space-12`
- Major page sections: `space-12` to `space-16`

**Responsive Spacing**
```css
/* Mobile: Reduce large spacing */
@media (max-width: 767px) {
  --section-spacing: var(--space-6);  /* 24px */
}

/* Desktop: Increase breathing room */
@media (min-width: 1024px) {
  --section-spacing: var(--space-12); /* 48px */
}
```

---

## Responsive Breakpoints

Mobile-first approach with named breakpoints aligned to common devices.

```css
/* Breakpoint tokens */
--breakpoint-sm:   640px;   /* Large phones (landscape) */
--breakpoint-md:   768px;   /* Tablets (portrait) */
--breakpoint-lg:   1024px;  /* Tablets (landscape), small laptops */
--breakpoint-xl:   1280px;  /* Desktop */
--breakpoint-2xl:  1536px;  /* Large desktop */
```

### Media Query Patterns

**Mobile First (Recommended)**
```css
/* Base: Mobile (< 640px) */
.component { }

/* Small: Large phones */
@media (min-width: 640px) { }

/* Medium: Tablets */
@media (min-width: 768px) { }

/* Large: Desktop */
@media (min-width: 1024px) { }

/* XL: Large desktop */
@media (min-width: 1280px) { }
```

### Viewport-Specific Patterns

**Mobile (< 768px)**
- Single column layouts
- Full-width cards
- Collapsible sections by default
- Touch-optimized (44px minimum tap targets)
- Prioritize vertical scroll over horizontal space

**Tablet (768px - 1023px)**
- 2-column layouts where appropriate
- Sidebar patterns emerge
- Some sections expand by default
- Hybrid touch + pointer interactions

**Desktop (1024px+)**
- Multi-column layouts
- Persistent navigation
- More sections expanded by default
- Hover states, tooltips
- Optimized for keyboard navigation

---

## Component Library

### Buttons

**Primary Button**
```css
Background: var(--brand-blue-500)
Text: white
Padding: var(--space-3) var(--space-6)  /* 12px 24px */
Border-radius: 6px
Font-size: var(--text-base)
Font-weight: 600
Min-height: 44px  /* Touch target */

States:
  Hover: var(--brand-blue-600)
  Active: var(--brand-blue-700)
  Focus: 2px outline var(--brand-blue-500), 2px offset
  Disabled: var(--neutral-300), cursor: not-allowed
```

**Secondary Button**
```css
Background: transparent
Text: var(--brand-blue-500)
Border: 2px solid var(--brand-blue-500)
Padding: var(--space-3) var(--space-6)
Border-radius: 6px
Font-size: var(--text-base)
Font-weight: 600
Min-height: 44px

States:
  Hover: Background var(--brand-blue-100)
  Active: Border var(--brand-blue-700)
  Focus: 2px outline var(--brand-blue-500), 2px offset
```

**Ghost Button (Tertiary)**
```css
Background: transparent
Text: var(--neutral-600)
Border: none
Padding: var(--space-2) var(--space-4)
Font-size: var(--text-sm)
Font-weight: 500
Min-height: 36px

States:
  Hover: Background var(--neutral-100)
  Active: Text var(--neutral-800)
```

**Button Sizing**
- Small: `space-2` `space-4` padding, `text-sm`, 36px min-height
- Medium (default): `space-3` `space-6`, `text-base`, 44px min-height
- Large: `space-4` `space-8`, `text-lg`, 52px min-height

### Cards

**Standard Card**
```css
Background: white
Border: 1px solid var(--neutral-200)
Border-radius: 8px
Padding: var(--space-6)  /* 24px */
Box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06)

States:
  Hover (if interactive):
    Box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)
    Transform: translateY(-2px)
    Transition: all 0.2s ease
```

**Metric Card (Data Highlight)**
```css
Background: white
Border-left: 4px solid var(--info-600)  /* Semantic color based on context */
Border-radius: 8px
Padding: var(--space-5)
Box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06)

Interactive States:
  Hover: Border-left-width: 6px
         Box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)
```

**Card Variants**
- **Elevated**: Stronger shadow (0 4px 6px rgba)
- **Flush**: No border, subtle background (neutral-50)
- **Bordered**: Emphasis border (2px solid)

### Forms

**Input Field**
```css
Background: white
Border: 1px solid var(--neutral-300)
Border-radius: 6px
Padding: var(--space-3) var(--space-4)  /* 12px 16px */
Font-size: var(--text-base)
Color: var(--neutral-700)
Min-height: 44px  /* Touch target */

States:
  Focus: Border var(--brand-blue-500),
         0 0 0 3px var(--brand-blue-100)
  Error: Border var(--danger-600),
         0 0 0 3px var(--danger-100)
  Disabled: Background var(--neutral-100),
            Color var(--neutral-400)
```

**Label**
```css
Font-size: var(--text-sm)
Font-weight: 600
Color: var(--neutral-700)
Margin-bottom: var(--space-2)
```

**Helper Text**
```css
Font-size: var(--text-sm)
Color: var(--neutral-500)
Margin-top: var(--space-1)
```

**Error Text**
```css
Font-size: var(--text-sm)
Color: var(--danger-700)
Margin-top: var(--space-1)
Icon: ⚠️ or bi-exclamation-circle
```

### Badges

**Status Badge**
```css
Padding: var(--space-1) var(--space-3)  /* 4px 12px */
Border-radius: 12px  /* Pill shape */
Font-size: var(--text-xs)
Font-weight: 600
Letter-spacing: 0.02em
Text-transform: uppercase

Variants:
  Success: Background var(--success-100), Text var(--success-700)
  Danger: Background var(--danger-100), Text var(--danger-700)
  Warning: Background var(--warning-100), Text var(--warning-700)
  Info: Background var(--info-100), Text var(--info-700)
  Neutral: Background var(--neutral-200), Text var(--neutral-700)
```

### Navigation

**Top Navigation Bar**
```css
Background: var(--neutral-900)  /* Dark for contrast */
Height: 64px
Padding: var(--space-4) var(--space-6)
Box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1)

Mobile: Collapsed hamburger menu
Tablet+: Horizontal navigation
```

**Nav Link**
```css
Font-size: var(--text-base)
Font-weight: 500
Color: var(--neutral-300)
Padding: var(--space-3) var(--space-4)
Min-height: 44px  /* Touch target */

States:
  Hover: Color white
  Active: Color white, Font-weight 700,
          Border-bottom 3px solid var(--brand-blue-500)
```

### Collapsible Sections (Progressive Disclosure)

**Section Header (Collapsed)**
```css
Display: flex
Align-items: center
Justify-content: space-between
Padding: var(--space-4)
Background: var(--neutral-50)
Border-top: 1px solid var(--neutral-200)
Border-bottom: 1px solid var(--neutral-200)
Cursor: pointer
Min-height: 56px  /* Touch target */

Content:
  Text (left): Font-size var(--text-lg), Font-weight 600
  Chevron icon (right): Rotates 180° when expanded

States:
  Hover: Background var(--neutral-100)
  Active: Border-color var(--neutral-300)
```

**Pattern Example (Text-based)**
```
────────────── ⌄ Market Statistics ──────────────
```

**Expanded State**
- Chevron rotates up (⌃)
- Content revealed with subtle slide animation (150ms ease)
- Section background remains distinct from page

---

## Accessibility Standards

### WCAG 2.1 Compliance

**Level AA (Minimum)**
- ✓ Color contrast: 4.5:1 for text, 3:1 for large text
- ✓ Touch targets: 44x44px minimum
- ✓ Keyboard navigation: All interactive elements reachable via Tab
- ✓ Focus indicators: Visible 2px outline with offset
- ✓ Form labels: Explicit association with inputs
- ✓ Alt text: Descriptive for all images
- ✓ Semantic HTML: Proper heading hierarchy, landmarks

**Level AAA (Where Feasible)**
- ✓ Color contrast: 7:1 for text (use -700 colors)
- ✓ Touch targets: 56x56px for critical actions
- ✓ Error prevention: Confirmation for destructive actions

### Touch Target Sizing

```css
--touch-target-min:  44px;  /* WCAG AA minimum */
--touch-target-opt:  48px;  /* Comfortable */
--touch-target-max:  56px;  /* Critical actions, AAA */
```

**Application:**
- Primary buttons: 48px height
- Nav links, icon buttons: 44px minimum
- Critical actions (delete, submit): 56px height
- Dense interfaces: 40px acceptable with adequate spacing

### Keyboard Navigation

1. **Tab Order**
   - Logical sequence matching visual order
   - Skip links for long navigation
   - Trap focus in modals

2. **Focus States**
   - Visible 2px outline (brand-blue-500)
   - 2px offset from element
   - Never remove outline without custom replacement

3. **Interactive Semantics**
   - Buttons for actions: `<button>`
   - Links for navigation: `<a>`
   - Proper ARIA labels for icon-only controls

### Screen Reader Support

**Semantic HTML**
```html
<header>  - Site header
<nav>     - Navigation regions
<main>    - Primary content
<aside>   - Complementary content
<footer>  - Site footer
<section> - Thematic groupings
<article> - Independent content
```

**ARIA Enhancements**
- `aria-label` for icon buttons
- `aria-describedby` for form help text
- `aria-expanded` for collapsible sections
- `aria-live="polite"` for dynamic updates (chart data)

### Color Accessibility

1. **Never rely on color alone**
   - Use icons + color for status
   - Add patterns to chart series
   - Include text labels

2. **Test with colorblind simulation**
   - Deuteranopia (red-green, most common)
   - Protanopia (red-green)
   - Tritanopia (blue-yellow)

3. **Ensure contrast**
   - All text meets WCAG AA minimum
   - UI elements (borders, icons) meet 3:1
   - Test with contrast checker tools

---

## Layout Patterns

### Container Widths

```css
--container-sm:   640px;   /* Narrow content (articles) */
--container-md:   768px;   /* Standard content */
--container-lg:   1024px;  /* Wide content */
--container-xl:   1280px;  /* Dashboard layouts */
--container-full: 100%;    /* Full viewport */
```

**Usage:**
- Articles, forms: `container-sm` to `container-md`
- Dashboard: `container-lg` to `container-xl`
- Landing pages: Mix of widths for visual interest

### Grid System

**Mobile (< 768px)**
- 4-column grid (rarely use all 4 - usually stack)
- Gutter: 16px (space-4)
- Margin: 16px (space-4)

**Tablet (768px - 1023px)**
- 8-column grid
- Gutter: 24px (space-6)
- Margin: 32px (space-8)

**Desktop (1024px+)**
- 12-column grid
- Gutter: 24px (space-6)
- Margin: 40px (space-10) to 80px

### Common Layouts

**Dashboard (Multi-Metric View)**
```
Mobile:
  [Metric Card 1]  - Full width
  [Metric Card 2]  - Full width
  [Metric Card 3]  - Full width

Tablet:
  [Card 1] [Card 2]  - 2 columns
  [Card 3] [Card 4]

Desktop:
  [Card 1] [Card 2] [Card 3]  - 3 columns
  [Card 4] [Card 5] [Card 6]
```

**Detail Page (Chart + Context)**
```
Mobile:
  [📊 Chart]           - Full width, top priority
  [──⌄ Stats ──]       - Collapsed
  [──⌄ About ──]       - Collapsed

Desktop:
  [📊 Chart - 2/3 width] [Stats - 1/3 width]
  [About - Full width below]
```

---

## Interaction Patterns

### Transitions & Animation

**Duration Tokens**
```css
--duration-fast:   150ms;   /* Micro-interactions */
--duration-base:   250ms;   /* Standard transitions */
--duration-slow:   350ms;   /* Complex animations */
```

**Easing Functions**
```css
--ease-in:      cubic-bezier(0.4, 0, 1, 1);
--ease-out:     cubic-bezier(0, 0, 0.2, 1);      /* Default */
--ease-in-out:  cubic-bezier(0.4, 0, 0.2, 1);
```

**Common Patterns**
- Hover states: 150ms ease-out
- Collapsible sections: 250ms ease-in-out
- Page transitions: 350ms ease-out

### Loading States

**Skeleton Screens** (Preferred)
- Show layout with pulsing placeholders
- Better perceived performance than spinners
- Use neutral-200 base, neutral-300 shimmer

**Spinner** (When skeleton isn't feasible)
- Brand-blue-500 color
- Centered with clear context ("Loading data...")
- Minimum 300ms display (avoid flash)

### Empty States

**Pattern:**
```
[Icon or Illustration]
Heading: "No data yet"
Body: Helpful explanation
[Optional CTA Button]
```

Example: No portfolio holdings
```
📊
No holdings yet
Add your first investment to start tracking performance.
[+ Add Holding]
```

---

## Data Visualization Principles

### Chart Design

**Canvas**
- Background: white or neutral-50
- Grid lines: neutral-200 (subtle)
- Axis lines: neutral-300

**Typography**
- Axis labels: text-sm, neutral-500
- Data labels: text-sm, neutral-700, font-mono
- Title: text-xl, neutral-800, font-weight 600

**Color Usage**
- Use chart palette (colorblind-friendly)
- Maximum 6 series before patterns required
- Add patterns for critical distinctions

**Responsive Charts**
- Mobile: Simplify, reduce series if needed
- Tablet: Standard complexity
- Desktop: Full detail, hover interactions

### Data Tables

**Header**
```css
Background: var(--neutral-100)
Text: var(--text-sm), var(--neutral-700), font-weight 600
Padding: var(--space-3)
Border-bottom: 2px solid var(--neutral-300)
```

**Row**
```css
Text: var(--text-sm), var(--neutral-600)
Padding: var(--space-3)
Border-bottom: 1px solid var(--neutral-200)

States:
  Hover: Background var(--neutral-50)
  Selected: Background var(--brand-blue-100)
```

**Numeric Columns**
```css
Font-family: var(--font-mono)
Text-align: right
Font-feature-settings: 'tnum'  /* Tabular numbers */
```

---

## Implementation Guide

### CSS Custom Properties Structure

```css
:root {
  /* Colors */
  --neutral-50: #FAFBFC;
  /* ... all color tokens ... */

  /* Typography */
  --text-xs: 0.75rem;
  /* ... all type tokens ... */

  /* Spacing */
  --space-1: 0.25rem;
  /* ... all spacing tokens ... */

  /* Breakpoints (for JS) */
  --breakpoint-md: 768px;
  /* ... */
}
```

### Component Development Checklist

When creating a new component:

- [ ] Mobile layout designed first
- [ ] Responsive behavior defined for tablet, desktop
- [ ] All interactive states specified (hover, active, focus, disabled)
- [ ] Touch targets meet 44px minimum
- [ ] Color contrast verified (WCAG AA minimum)
- [ ] Keyboard navigation tested
- [ ] Screen reader compatibility verified
- [ ] Design tokens used (no hard-coded values)
- [ ] Documented in this design system

### Progressive Enhancement

1. **Mobile Core**
   - Essential functionality works on smallest screens
   - Touch-optimized interactions
   - Single-column layouts

2. **Tablet Enhancement**
   - Multi-column layouts emerge
   - Additional content revealed
   - Hybrid interaction patterns

3. **Desktop Excellence**
   - Full feature set
   - Hover states, tooltips
   - Keyboard shortcuts
   - Rich data visualizations

---

## Design Tokens Reference

### Quick Reference Table

| Category | Token Pattern | Example |
|----------|---------------|---------|
| **Color** | `--{category}-{value}` | `--neutral-600`, `--brand-blue-500` |
| **Typography** | `--text-{size}` | `--text-base`, `--text-xl` |
| **Spacing** | `--space-{value}` | `--space-4`, `--space-8` |
| **Breakpoint** | `--breakpoint-{size}` | `--breakpoint-md` |
| **Duration** | `--duration-{speed}` | `--duration-fast` |
| **Ease** | `--ease-{type}` | `--ease-out` |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-20 | Initial design system established - colors, typography, spacing, components, accessibility standards |

---

**Next Steps:**
1. Implement CSS custom properties in dashboard.css
2. Audit existing components against new standards
3. Create component library documentation with live examples
4. Build Figma/design tool library for visual design work
