# Test Plan: US-3.1.3 - Apply Mobile-First Layout to Credit & Rates Pages

**User Story:** #85
**QA Engineer:** Claude QA
**Created:** 2026-02-20
**Risk Assessment:** MEDIUM-HIGH (UI/UX changes across 2 critical asset pages)

---

## Executive Summary

This test plan validates mobile-first redesign for Credit and Rates pages, ensuring charts are visible without scrolling on mobile while maintaining desktop excellence. Pattern must match validated Explorer page (US-3.1.2).

**Critical Success Factors:**
- ✓ Charts visible in first screen on mobile (both pages)
- ✓ 50%+ scroll reduction in collapsed state
- ✓ Collapsible sections functional on mobile
- ✓ Consistent with Explorer page pattern
- ✓ No desktop regression

**Total Test Cases:** 82
**Must-Pass (P0):** 18
**Should-Pass (P1):** 14

---

## 1. Functional Testing

### 1.1 Mobile Layout (< 768px) - Credit Page

**Test Case 1.1.1: Visual Hierarchy (P0)**
- **Given:** User opens `/credit` on mobile (375px)
- **When:** Page loads
- **Then:**
  - Navigation bar visible at top
  - Page title "Credit Markets" + Last Updated displayed
  - Chart visible without scrolling (50-60vh, 300-400px)
  - Time range controls below chart
  - All sections below are collapsed by default

**Test Case 1.1.2: Chart Prominence (P0)**
- **Given:** Credit page loaded on mobile
- **When:** Measuring chart dimensions
- **Then:**
  - Chart height = 50vh (min 300px, max 400px)
  - Chart width = 100% viewport width (minus padding)
  - Chart visible above fold (no scroll needed)
  - No metric selector present (fixed asset class)

**Test Case 1.1.3: Progressive Disclosure - Collapsed State (P0)**
- **Given:** Credit page loaded on mobile
- **When:** Inspecting collapsible sections
- **Then:**
  - "Market Statistics" section collapsed by default
  - "About This Asset Class" section collapsed by default
  - Any credit-specific sections (e.g., "Spread Analysis") collapsed
  - Clear expand affordance visible (divider/chevron)

**Test Case 1.1.4: Progressive Disclosure - Expansion (P1)**
- **Given:** Credit page with collapsed sections
- **When:** User taps "Market Statistics" header
- **Then:**
  - Section expands with smooth animation
  - Statistics content revealed
  - Chevron rotates to indicate expanded state
  - Other sections remain collapsed

**Test Case 1.1.5: Progressive Disclosure - Collapse (P1)**
- **Given:** Expanded "Market Statistics" section
- **When:** User taps header again
- **Then:**
  - Section collapses with smooth animation
  - Content hidden
  - Chevron returns to collapsed state

**Test Case 1.1.6: Scroll Reduction (P0)**
- **Given:** Credit page on mobile with all sections collapsed
- **When:** Measuring total page height
- **Then:**
  - Total height ≤ 1000px
  - 50%+ reduction vs. current state (baseline: ~2000px)
  - User can see chart without any scrolling

**Test Case 1.1.7: Chart Interactivity (P1)**
- **Given:** Credit page chart on mobile
- **When:** User taps chart data point
- **Then:**
  - Tooltip displays with data values
  - Tap target ≥ 44px (accessibility)
  - Tooltip doesn't obscure chart
  - Touch interaction feels responsive

**Test Case 1.1.8: Time Range Controls (P1)**
- **Given:** Credit page chart on mobile
- **When:** User changes time range (1M → 1Y)
- **Then:**
  - Chart updates with new data
  - Loading state shown during fetch
  - Chart remains visible (no scroll jump)
  - Time range button shows selected state

### 1.2 Mobile Layout (< 768px) - Rates Page

**Test Case 1.2.1: Visual Hierarchy (P0)**
- **Given:** User opens `/rates` on mobile (375px)
- **When:** Page loads
- **Then:**
  - Navigation bar visible at top
  - Page title "Interest Rates" + Last Updated displayed
  - Chart visible without scrolling (50-60vh, 300-400px)
  - Time range controls below chart
  - All sections below are collapsed by default

**Test Case 1.2.2: Chart Prominence (P0)**
- **Given:** Rates page loaded on mobile
- **When:** Measuring chart dimensions
- **Then:**
  - Chart height = 50vh (min 300px, max 400px)
  - Chart width = 100% viewport width (minus padding)
  - Chart visible above fold (no scroll needed)
  - No metric selector present (fixed asset class)

**Test Case 1.2.3: Progressive Disclosure - Collapsed State (P0)**
- **Given:** Rates page loaded on mobile
- **When:** Inspecting collapsible sections
- **Then:**
  - "Market Statistics" section collapsed by default
  - "About This Asset Class" section collapsed by default
  - Any rates-specific sections (e.g., "Yield Curve Analysis") collapsed
  - Clear expand affordance visible (divider/chevron)

**Test Case 1.2.4: Progressive Disclosure - Expansion (P1)**
- **Given:** Rates page with collapsed sections
- **When:** User taps section header
- **Then:**
  - Section expands smoothly
  - Content revealed
  - Chevron indicates expansion

**Test Case 1.2.5: Scroll Reduction (P0)**
- **Given:** Rates page on mobile with all sections collapsed
- **When:** Measuring total page height
- **Then:**
  - Total height ≤ 1000px
  - 50%+ reduction vs. current state
  - Chart visible without scrolling

**Test Case 1.2.6: Chart Interactivity (P1)**
- **Given:** Rates page chart on mobile
- **When:** User taps chart
- **Then:**
  - Tooltip displays correctly
  - Touch targets adequate (≥ 44px)
  - Responsive interaction

### 1.3 Tablet Layout (768px - 1023px) - Both Pages

**Test Case 1.3.1: Hybrid Layout - Credit Page (P0)**
- **Given:** Credit page on tablet (768px)
- **When:** Page loads
- **Then:**
  - Chart and key stats side-by-side (60/40 split)
  - Chart height = 400px fixed
  - 3-5 key statistics visible without expansion
  - Detailed statistics remain collapsed
  - No horizontal scroll

**Test Case 1.3.2: Hybrid Layout - Rates Page (P0)**
- **Given:** Rates page on tablet (768px)
- **When:** Page loads
- **Then:**
  - Chart and key stats side-by-side (60/40 split)
  - Chart height = 400px fixed
  - 3-5 key statistics visible
  - Detailed stats collapsed

**Test Case 1.3.3: Responsive Breakpoint Transition (P1)**
- **Given:** Credit page on mobile (375px)
- **When:** Viewport resized to 768px (tablet)
- **Then:**
  - Layout transitions to side-by-side grid
  - Chart resizes from 50vh to 400px height
  - Key stats panel appears
  - No content jump or flash

**Test Case 1.3.4: Key Stats Panel Content (P2)**
- **Given:** Rates page on tablet
- **When:** Viewing key stats panel
- **Then:**
  - 3-5 most important metrics shown
  - Metrics have clear labels and values
  - Values formatted appropriately (%, decimals)
  - Panel doesn't overflow

### 1.4 Desktop Layout (1024px+) - Both Pages

**Test Case 1.4.1: Enhanced Layout - Credit Page (P0)**
- **Given:** Credit page on desktop (1920px)
- **When:** Page loads
- **Then:**
  - Chart + stats grid side-by-side (66/33 split)
  - Chart height = 500px
  - All key statistics visible (no collapse needed)
  - Chart quality maintained (no pixelation)

**Test Case 1.4.2: Enhanced Layout - Rates Page (P0)**
- **Given:** Rates page on desktop (1920px)
- **When:** Page loads
- **Then:**
  - Chart + stats grid side-by-side (66/33 split)
  - Chart height = 500px
  - All key statistics visible

**Test Case 1.4.3: No Desktop Regression (P0)**
- **Given:** Desktop user familiar with current layout
- **When:** Comparing new vs. old desktop layout
- **Then:**
  - All information still accessible
  - Chart quality equal or better
  - Stats layout equal or better
  - No loss of functionality

**Test Case 1.4.4: Wide Screen Optimization (P2)**
- **Given:** Credit page on ultrawide monitor (2560px)
- **When:** Page loads
- **Then:**
  - Content doesn't stretch awkwardly
  - Chart maintains aspect ratio
  - Max-width constraints prevent over-stretching
  - Layout remains readable

---

## 2. Integration Testing

**Test Case 2.1: CollapsibleSection Component Integration (P1)**
- **Given:** Mobile Credit page using CollapsibleSection component
- **When:** User expands/collapses sections
- **Then:**
  - Component state managed correctly
  - Multiple sections can be expanded simultaneously
  - Section state persists during page interaction
  - No console errors

**Test Case 2.2: ChartContainer Component Integration (P1)**
- **Given:** Both pages use ChartContainer component
- **When:** Chart renders
- **Then:**
  - Container applies correct responsive sizing
  - Chart library initialized properly
  - Time range controls interact with chart
  - No memory leaks on chart re-render

**Test Case 2.3: KeyStatsPanel Component Integration (P1)**
- **Given:** Tablet/desktop layout with KeyStatsPanel
- **When:** Page loads
- **Then:**
  - Panel receives correct data
  - Stats formatted consistently
  - Panel responsive to viewport changes

**Test Case 2.4: Cross-Component State Management (P1)**
- **Given:** User interacts with chart time range
- **When:** Time range changes
- **Then:**
  - Chart updates
  - Stats panel updates (if time-dependent)
  - Collapsible sections maintain state
  - No UI flicker or state desync

---

## 3. Edge Cases

**Test Case 3.1: Viewport Extremes - Small (P1)**
- **Given:** Credit page on 320px viewport (iPhone SE)
- **When:** Page loads
- **Then:**
  - Layout doesn't break
  - Chart min-height (300px) enforced
  - Touch targets still ≥ 44px
  - No horizontal scroll

**Test Case 3.2: Viewport Extremes - Large (P2)**
- **Given:** Rates page on 3840px viewport (4K)
- **When:** Page loads
- **Then:**
  - Max-width constraints applied
  - Chart doesn't pixelate
  - Layout remains centered and readable

**Test Case 3.3: Missing Data (P1)**
- **Given:** Chart data fails to load
- **When:** Page renders
- **Then:**
  - Error message displayed in chart area
  - Layout doesn't collapse
  - Other sections still accessible
  - Retry option provided

**Test Case 3.4: Slow Network (P2)**
- **Given:** User on 3G network
- **When:** Loading Credit page
- **Then:**
  - Loading skeleton shown
  - Chart loads progressively
  - Page remains interactive during load
  - Timeout handled gracefully (30s)

**Test Case 3.5: Very Long Statistics List (P2)**
- **Given:** Credit page with 20+ statistics
- **When:** User expands "Market Statistics" section
- **Then:**
  - Section expands without breaking layout
  - Scroll is smooth
  - Performance remains acceptable

**Test Case 3.6: Rapid Viewport Resize (P2)**
- **Given:** User resizing browser rapidly
- **When:** Crossing breakpoints (mobile ↔ tablet ↔ desktop)
- **Then:**
  - Layout transitions smoothly
  - No chart re-render flickering
  - Debounced resize handlers prevent thrashing

**Test Case 3.7: Empty Last Updated Timestamp (P2)**
- **Given:** Last Updated value is null/empty
- **When:** Page loads
- **Then:**
  - Graceful fallback displayed ("Data as of: Unknown")
  - Layout doesn't break
  - No console errors

**Test Case 3.8: Browser Back/Forward Navigation (P2)**
- **Given:** User navigates Credit → Rates → Browser Back
- **When:** Returning to Credit page
- **Then:**
  - Page state restored correctly
  - Section collapse states preserved (if cached)
  - Chart doesn't re-fetch unnecessarily

---

## 4. Security Testing

**Test Case 4.1: XSS Prevention - Page Title (P0)**
- **Given:** Malicious script in page title data
- **When:** Rendering "Credit Markets" title
- **Then:**
  - Script tags escaped/sanitized
  - No JavaScript execution
  - Content displayed as plain text

**Test Case 4.2: XSS Prevention - Statistics Content (P0)**
- **Given:** Malicious script in statistics data
- **When:** Rendering Market Statistics section
- **Then:**
  - Content properly escaped
  - No script execution
  - HTML entities rendered safely

**Test Case 4.3: SQL Injection - Time Range Query (P1)**
- **Given:** User manipulates time range parameter in URL
- **When:** Backend fetches chart data
- **Then:**
  - Query parameters validated/sanitized
  - No SQL injection possible
  - Invalid input rejected with error

**Test Case 4.4: CSRF Protection (P2)**
- **Given:** User submits form/action on page
- **When:** Request sent to backend
- **Then:**
  - CSRF token validated
  - Unauthorized requests rejected
  - Token rotation on sensitive actions

---

## 5. Performance Testing

**Test Case 5.1: Page Load Performance - Mobile (P0)**
- **Given:** Credit page on mobile 3G network
- **When:** Measuring performance metrics
- **Then:**
  - LCP (Largest Contentful Paint) < 2.5s
  - FID (First Input Delay) < 100ms
  - CLS (Cumulative Layout Shift) < 0.1
  - Page fully interactive < 5s

**Test Case 5.2: Page Load Performance - Desktop (P1)**
- **Given:** Rates page on desktop broadband
- **When:** Measuring performance metrics
- **Then:**
  - LCP < 1.5s
  - FID < 50ms
  - CLS < 0.1

**Test Case 5.3: Animation Performance (P1)**
- **Given:** User expands collapsible section on mobile
- **When:** Measuring animation frame rate
- **Then:**
  - Animation runs at 60fps
  - No jank or stutter
  - Uses CSS transitions (not JavaScript animation)

**Test Case 5.4: Chart Render Time (P1)**
- **Given:** Chart data loaded (100 data points)
- **When:** Chart renders
- **Then:**
  - Render completes < 500ms
  - Re-render on resize < 200ms
  - No memory leaks on multiple re-renders

**Test Case 5.5: Memory Usage (P2)**
- **Given:** User navigates between Credit and Rates pages 10 times
- **When:** Monitoring memory usage
- **Then:**
  - No memory leaks
  - Heap size stable after garbage collection
  - Event listeners cleaned up properly

---

## 6. Accessibility Testing (WCAG 2.1 AA)

### 6.1 Keyboard Navigation

**Test Case 6.1.1: Tab Order - Mobile (P0)**
- **Given:** Credit page on mobile
- **When:** User navigates with Tab key
- **Then:**
  - Focus order: Nav → Title → Chart → Time Range → Sections
  - All interactive elements reachable
  - Focus indicator visible (outline)
  - No keyboard traps

**Test Case 6.1.2: Collapsible Section Keyboard Control (P0)**
- **Given:** Collapsed section on mobile
- **When:** User focuses section header and presses Enter/Space
- **Then:**
  - Section expands
  - Focus remains on header
  - ARIA attributes updated (aria-expanded="true")

**Test Case 6.1.3: Chart Keyboard Navigation (P1)**
- **Given:** Chart has focus
- **When:** User presses arrow keys
- **Then:**
  - Data points navigable with keyboard
  - Tooltip displayed for focused point
  - Escape key closes tooltip

### 6.2 Screen Reader Support

**Test Case 6.2.1: Page Structure Semantics (P0)**
- **Given:** NVDA screen reader on Credit page
- **When:** User navigates by headings
- **Then:**
  - Page title = h1
  - Section headers = h2
  - Proper heading hierarchy (no skipped levels)
  - Landmark roles used (main, nav, article)

**Test Case 6.2.2: Collapsible Section Announcements (P0)**
- **Given:** Screen reader user on collapsed section
- **When:** User activates section header
- **Then:**
  - Announces "expanded" or "collapsed" state
  - ARIA attributes present (aria-expanded, aria-controls)
  - Content revealed is announced

**Test Case 6.2.3: Chart Alternative Text (P0)**
- **Given:** Chart element on page
- **When:** Screen reader encounters chart
- **Then:**
  - Descriptive alt text or aria-label present
  - Data summary table provided (if complex chart)
  - Screen reader can access key data points

**Test Case 6.2.4: Dynamic Content Announcements (P1)**
- **Given:** User changes time range on chart
- **When:** Chart updates
- **Then:**
  - ARIA live region announces "Chart updated"
  - Screen reader notified of change
  - User understands new state

### 6.3 Visual Accessibility

**Test Case 6.3.1: Color Contrast - Text (P0)**
- **Given:** Page content on mobile
- **When:** Testing with WebAIM Contrast Checker
- **Then:**
  - All text has ≥ 4.5:1 contrast ratio (normal text)
  - Large text (18pt+) has ≥ 3:1 contrast ratio
  - Chart data labels meet contrast requirements

**Test Case 6.3.2: Color Contrast - Interactive Elements (P0)**
- **Given:** Buttons, links, section headers
- **When:** Testing contrast
- **Then:**
  - Interactive elements ≥ 3:1 contrast with background
  - Focus indicators ≥ 3:1 contrast
  - Disabled elements excluded from requirement

**Test Case 6.3.3: Touch Target Size (P0)**
- **Given:** Mobile page with interactive elements
- **When:** Measuring touch targets
- **Then:**
  - All tap targets ≥ 44x44px
  - Adequate spacing between targets (8px minimum)
  - Chart data points have 44px touch targets

**Test Case 6.3.4: Zoom & Reflow (P1)**
- **Given:** Page zoomed to 200%
- **When:** User navigates
- **Then:**
  - Content reflows without horizontal scroll
  - No content clipped or obscured
  - Text remains readable

**Test Case 6.3.5: Focus Indicators (P0)**
- **Given:** User navigates with keyboard
- **When:** Elements receive focus
- **Then:**
  - Visible focus indicator (outline or border)
  - Focus indicator ≥ 2px width
  - Focus indicator doesn't rely on color alone

### 6.4 ARIA & Semantic HTML

**Test Case 6.4.1: ARIA Roles & Attributes (P1)**
- **Given:** Collapsible sections on page
- **When:** Inspecting HTML
- **Then:**
  - aria-expanded on section headers
  - aria-controls linking header to content
  - role="button" on clickable headers (if not <button>)
  - Valid ARIA relationships

**Test Case 6.4.2: Form Labels (P1)**
- **Given:** Time range controls
- **When:** Inspecting HTML
- **Then:**
  - All inputs have associated <label> or aria-label
  - Labels descriptive and unique
  - Required fields marked with aria-required

---

## 7. Cross-Browser & Device Testing

**Test Case 7.1: Chrome Mobile (P0)**
- **Given:** Credit page on Android Chrome
- **When:** Testing full user flow
- **Then:**
  - Layout renders correctly
  - Touch interactions work
  - Chart tooltips functional

**Test Case 7.2: Safari iOS (P0)**
- **Given:** Rates page on iPhone Safari
- **When:** Testing layout and interactions
- **Then:**
  - Sticky positioning works (known Safari bugs)
  - Touch events fire correctly
  - No unexpected scrolling behavior

**Test Case 7.3: Desktop Chrome (P1)**
- **Given:** Both pages on desktop Chrome
- **When:** Testing full feature set
- **Then:**
  - All functionality works
  - Layout matches design spec
  - Performance acceptable

**Test Case 7.4: Desktop Safari (P1)**
- **Given:** Both pages on macOS Safari
- **When:** Testing
- **Then:**
  - CSS Grid/Flexbox renders correctly
  - Chart library compatible
  - No vendor-prefix issues

**Test Case 7.5: Desktop Firefox (P2)**
- **Given:** Both pages on Firefox
- **When:** Testing
- **Then:**
  - Layout consistent
  - Chart interactions work
  - No Firefox-specific bugs

---

## 8. Visual Regression Testing

**Test Case 8.1: Mobile Screenshot - Credit Page (P0)**
- **Given:** Playwright test at 375x667 viewport
- **When:** Capturing Credit page screenshot
- **Then:**
  - Chart visible in first screen
  - All sections collapsed
  - Matches design spec baseline

**Test Case 8.2: Mobile Screenshot - Rates Page (P0)**
- **Given:** Playwright test at 375x667 viewport
- **When:** Capturing Rates page screenshot
- **Then:**
  - Chart visible in first screen
  - Layout matches design spec

**Test Case 8.3: Tablet Screenshot - Both Pages (P1)**
- **Given:** Playwright test at 768x1024 viewport
- **When:** Capturing screenshots
- **Then:**
  - Side-by-side layout visible
  - Chart + key stats grid renders correctly
  - Matches design spec

**Test Case 8.4: Desktop Screenshot - Both Pages (P1)**
- **Given:** Playwright test at 1920x1080 viewport
- **When:** Capturing screenshots
- **Then:**
  - Enhanced layout visible
  - All statistics shown
  - Matches design spec

---

## 9. Consistency with Explorer Page

**Test Case 9.1: Component Reuse (P0)**
- **Given:** Credit and Rates pages implementation
- **When:** Reviewing code
- **Then:**
  - Same CollapsibleSection component as Explorer
  - Same ChartContainer component as Explorer
  - Same KeyStatsPanel component as Explorer
  - Consistent CSS classes and naming

**Test Case 9.2: Responsive Breakpoints (P0)**
- **Given:** All three pages (Explorer, Credit, Rates)
- **When:** Testing breakpoints
- **Then:**
  - Mobile: < 768px (all three)
  - Tablet: 768-1023px (all three)
  - Desktop: 1024px+ (all three)
  - Identical breakpoint values

**Test Case 9.3: Progressive Disclosure Pattern (P0)**
- **Given:** Mobile view of all three pages
- **When:** Testing collapsible sections
- **Then:**
  - Same interaction pattern (tap header to expand)
  - Same animation timing
  - Same visual affordance (chevron/divider)
  - Consistent ARIA attributes

**Test Case 9.4: Chart Sizing Consistency (P1)**
- **Given:** Charts on all three pages
- **When:** Comparing dimensions
- **Then:**
  - Mobile: 50vh (min 300px, max 400px) - all three
  - Tablet: 400px - all three
  - Desktop: 500px - all three

---

## Test Execution Strategy

### Automated Testing
1. **Playwright Visual Regression:**
   - Run `screenshots.spec.js` for all pages
   - Capture at 375px, 768px, 1920px viewports
   - Compare against design spec baselines

2. **Lighthouse Audits:**
   - Performance score ≥ 90
   - Accessibility score = 100
   - Best Practices score ≥ 95

3. **Unit Tests:**
   - Component-level tests for CollapsibleSection, ChartContainer, KeyStatsPanel
   - State management tests

### Manual Testing
1. **Real Device Testing:**
   - iPhone 12 (iOS Safari)
   - Samsung Galaxy S21 (Android Chrome)
   - iPad Pro (Safari)

2. **Screen Reader Testing:**
   - NVDA (Windows)
   - VoiceOver (macOS/iOS)

3. **Exploratory Testing:**
   - Edge cases not covered by automated tests
   - User flow validation

---

## Pass/Fail Criteria

### P0 Tests (Must Pass - 18 total)
All P0 tests must pass for approval. Any P0 failure blocks release.

### P1 Tests (Should Pass - 14 total)
At least 90% of P1 tests should pass. Failures require documented workaround or follow-up issue.

### P2 Tests (Nice to Have - 12 total)
No minimum pass rate. Failures logged for future improvement.

---

## Risk Areas

1. **Safari iOS Sticky Positioning:** Known Safari bugs with sticky elements. Test early on real device.
2. **Chart Touch Interactions:** Chart library may need modification for 44px touch targets.
3. **Performance on Low-End Devices:** Test on older Android devices (2019 models).
4. **Screen Reader Chart Access:** Complex charts may need data table alternatives.

---

## Tools Required

- Playwright (visual regression)
- Lighthouse CLI (performance + accessibility)
- WebAIM Contrast Checker (color contrast)
- NVDA (Windows screen reader)
- VoiceOver (macOS/iOS screen reader)
- Chrome DevTools (performance profiling)
- Real devices: iPhone, Android phone, iPad

---

## Definition of Done

- [ ] All 18 P0 tests pass
- [ ] ≥ 90% of P1 tests pass
- [ ] Playwright screenshots captured and verified
- [ ] Lighthouse accessibility score = 100
- [ ] Real device testing complete (iOS + Android)
- [ ] Screen reader testing complete (NVDA + VoiceOver)
- [ ] No P0 bugs remaining
- [ ] All P1 bugs have documented workarounds or follow-up issues
