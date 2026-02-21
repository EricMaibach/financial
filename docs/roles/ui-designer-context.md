# UI/UX Designer Context

**Last Updated:** 2026-02-20
**Product:** SignalTrackers - Macro Intelligence Platform
**Target Users:** Individual investors with $100K+ portfolios

---

## Design System

**Primary Reference:** [docs/design-system.md](../design-system.md)

The complete design system has been established with:
- Color palette (neutrals, brand, semantic, charts)
- Typography scale and hierarchy
- Spacing system (4px baseline grid)
- Responsive breakpoints (640px, 768px, 1024px, 1280px, 1536px)
- Component specifications
- Accessibility standards (WCAG 2.1 AA+)

### Key Design Tokens (Quick Reference)

**Colors**
- Neutrals: 50-900 scale, body text uses neutral-600+
- Brand: blue-500 (primary), indigo-500 (secondary)
- Semantic: success/danger/warning/info in 100/600/700 variants
- Charts: 6-color colorblind-friendly palette

**Typography**
- Scale: xs(12px) → 5xl(48px), 1.250 ratio
- Body: 16px (text-base), line-height 1.6
- Headings: 600-700 weight, neutral-700/800 color

**Spacing**
- 4px baseline grid: space-1(4px) → space-20(80px)
- Component padding: space-4 to space-6
- Section spacing: space-8 to space-12

**Breakpoints**
- sm: 640px (large phones)
- md: 768px (tablets)
- lg: 1024px (desktop)
- xl: 1280px (large desktop)

---

## Mobile Patterns

### Current Findings (Feb 2026)

**Content-Heavy Pages Issue (IN PROGRESS - Feature 3.1 #81)**
- Explorer and Asset Class pages suffer from desktop-first information hierarchy
- Charts buried below extensive statistics sections on mobile
- Example: Explorer page requires ~2000px scroll to reach chart
- **Design Spec:** [docs/specs/feature-3.1-mobile-content-pages.md](../specs/feature-3.1-mobile-content-pages.md)
- **Status:** Spec complete, awaiting PM approval

**Pages Being Redesigned (Feature 3.1):**
- Explorer page (metric analysis)
- Credit, Rates, Dollar, Equities, Crypto, Safe Havens (asset class pages)

**Chatbot Mobile UX Issue (Feature 3.2 #82)**
- Chatbot takes 90%+ of mobile viewport when expanded
- Obscures page content including charts users are asking about
- Users lose context during AI interactions
- **Design Spec:** [docs/specs/feature-3.2-chatbot-mobile-redesign.md](../specs/feature-3.2-chatbot-mobile-redesign.md)
- **Status:** ✅ APPROVED - Spec finalized and ready for engineering implementation
- **PM Approval:** 2026-02-20

**Pages Working Adequately:**
- Homepage (recent streamlining)
- Portfolio/Login pages (simple forms)

---

## Component Library

**Primary Reference:** [docs/design-system.md](../design-system.md#component-library)

Established components:
- **Buttons**: Primary, Secondary, Ghost (3 sizes, all states)
- **Cards**: Standard, Metric (with semantic border), Elevated
- **Forms**: Input fields, labels, helper/error text
- **Badges**: Status badges with semantic colors (also notification badges on FABs)
- **Navigation**: Top nav, nav links with active states
- **Collapsible Sections**: Progressive disclosure pattern
- **Bottom Sheet** (Mobile): Panel slides up from bottom, 40-50% viewport, used for chatbot
- **FAB** (Floating Action Button): 64px circular button, fixed position, indigo brand color

All components meet 44px minimum touch targets and WCAG 2.1 AA contrast.

---

## Visual Standards

### Established Patterns

**Progressive Disclosure** (Feb 2026)
- Pattern: Horizontal divider with centered chevron/text
- Example: `─────────── ⌄ Show Details ───────────`
- Usage: Market Conditions, What's Moving Today sections
- Implementation: 56px min-height, neutral-50 background, chevron rotates 180° when expanded
- Rationale: Reduces cognitive load, consistent interaction
- **Status**: Specified in design system

**Card Hierarchy** (Feb 2026)
- Standard cards: 1px border, subtle shadow
- Metric cards: 4px semantic left border (info-600, success-600, danger-600)
- Interactive cards: Hover lift effect (translateY(-2px), enhanced shadow)
- **Status**: Specified in design system

**Data Visualization** (Feb 2026)
- Colorblind-friendly palette: 6 colors maximum before patterns required
- Grid lines: neutral-200 (subtle, not dominant)
- Tabular numbers: Monospace font with 'tnum' feature
- **Status**: Principles documented in design system

---

## Accessibility Standards

**Primary Reference:** [docs/design-system.md](../design-system.md#accessibility-standards)

### WCAG 2.1 AA Compliance (Minimum)
- ✓ Color contrast: 4.5:1 for text, 3:1 for UI elements
- ✓ Touch targets: 44px minimum (48px optimal, 56px for critical actions)
- ✓ Keyboard navigation: All interactive elements via Tab, visible 2px focus outline
- ✓ Semantic HTML: Proper heading hierarchy, landmark regions
- ✓ Form accessibility: Explicit labels, helper text, error messages

### AAA Where Feasible
- Text contrast: 7:1 (using -700 color variants)
- Touch targets: 56px for destructive actions
- Error prevention: Confirmation for critical actions

### Color Independence
- Never rely on color alone
- Use icons + color for status
- Add patterns to charts for colorblind accessibility
- Test with deuteranopia, protanopia, tritanopia simulations

---

## Design Decisions

### Color Palette Selection (Feb 2026)
- **Decision**: Professional neutrals with purposeful semantic colors
- **Rationale**: Financial platform requires trust and clarity; colorful brand palettes distract from data
- **Outcome**: Neutral-heavy palette (50-900 scale) with semantic colors for market signals
- **Reference**: design-system.md - Color System

### Typography: System Font Stack (Feb 2026)
- **Decision**: Use system fonts (-apple-system, Segoe UI, Roboto) rather than web fonts
- **Rationale**: Faster load times, native feel, excellent readability
- **Outcome**: Professional appearance without font loading delays
- **Reference**: design-system.md - Typography

### Mobile-First Breakpoints (Feb 2026)
- **Decision**: 640px, 768px, 1024px, 1280px, 1536px breakpoints
- **Rationale**: Align with common device sizes; mobile-first progressive enhancement
- **Outcome**: Clear breakpoint strategy for responsive development
- **Reference**: design-system.md - Responsive Breakpoints

### 4px Spacing System (Feb 2026)
- **Decision**: 4px baseline grid (space-1 through space-20)
- **Rationale**: Mathematically consistent, easy calculation, aligns with 8pt grid systems
- **Outcome**: Predictable spacing relationships across all components
- **Reference**: design-system.md - Spacing System

### Bottom Sheet Pattern for Mobile Overlays (Feb 2026)
- **Decision**: Use bottom sheet pattern for chatbot (slides up from bottom, 40-50% viewport)
- **Rationale**: Preserves context (page content visible above), familiar mobile pattern (Google Maps, Uber), touch-optimized
- **Outcome**: Chatbot usable on mobile while maintaining chart visibility
- **Reference**: docs/specs/feature-3.2-chatbot-mobile-redesign.md
- **Pattern**: Mobile uses bottom sheet, tablet/desktop use side panel (responsive adaptation)

---

## Changelog

| Date | Change | Designer |
|------|--------|----------|
| 2026-02-20 | UI Designer role established | PM |
| 2026-02-20 | Identified mobile-first redesign needed for content-heavy pages | PM |
| 2026-02-20 | **Design system v1.0 established** - Complete color, typography, spacing, component, and accessibility standards documented | UI Designer |
| 2026-02-20 | **Collaboration workflow documented** - PM → Designer → Engineer handoff process added to CLAUDE.md | UI Designer |
| 2026-02-20 | **Feature 3.1 design spec created** - Comprehensive mobile-first redesign spec for 7 content pages | UI Designer |
| 2026-02-20 | **Chatbot mobile UX identified** - Analyzed screenshots, identified critical UX failure, PM created Feature 3.2 | UI Designer |
| 2026-02-20 | **Feature 3.2 design spec created** - Bottom sheet pattern with complete component spec, accessibility requirements, and implementation guidance | UI Designer |
| 2026-02-20 | **Feature 3.2 spec approved by PM** - All open questions answered, spec updated with final decisions, ready for engineering | UI Designer |

---

*This document contains design system decisions and accumulated design knowledge. Update after each significant design session.*
