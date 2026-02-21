# Test Plan: US-3.1.4
**User Story:** Apply Mobile-First Layout to Dollar, Equities, Crypto, Safe Havens Pages
**Issue:** #86
**Created:** 2026-02-21
**QA Engineer:** QA Test Engineer

---

## Test Summary

### Scope
Apply proven mobile-first layout pattern from Explorer, Credit, and Rates pages to the remaining 4 asset class pages:
1. **Dollar page** (`/dollar`)
2. **Equities page** (`/equities`)
3. **Crypto page** (`/crypto`)
4. **Safe Havens page** (`/safe-havens`)

### Risk Assessment: **MEDIUM-HIGH**
- **4 pages to redesign** (vs. 2 in US-3.1.3, 1 in US-3.1.2)
- **Completes Feature 3.1** - final validation of pattern consistency across all 7 content pages
- **Mobile-first layout** - critical UX change affecting primary use case
- **Cross-page consistency** - must match Explorer, Credit, Rates exactly
- **Accessibility compliance** - WCAG 2.1 AA required for all pages

### Key Risk Areas
1. **Consistency drift** - 4 pages increase risk of subtle pattern deviations
2. **Page-specific sections** - Each asset class may have unique sections requiring custom handling
3. **Performance at scale** - Testing 4 pages with screenshots = 12 screenshots total
4. **Safari iOS sticky positioning** - Known Safari bugs may affect all 4 pages
5. **Chart touch targets** - 44px minimum may require chart library modifications on each page

### Design Spec Reference
[docs/specs/feature-3.1-mobile-content-pages.md](../specs/feature-3.1-mobile-content-pages.md)
- Mobile Layout: Lines 69-242
- Tablet Layout: Lines 245-313
- Desktop Layout: Lines 316-393
- Asset Class Page Notes: Lines 676-686

---

## Test Strategy

### Automated Testing
- **Playwright screenshots** at 3 viewports (375px, 768px, 1920px) for ALL 4 pages = **12 screenshots**
- **Visual regression** - Compare against Explorer/Credit/Rates pattern
- **Lighthouse audits** - Performance + Accessibility for all 4 pages

### Manual Testing
- **Real device testing** required: iOS Safari (iPhone), Android Chrome
- **Cross-browser testing**: Chrome, Safari, Firefox, Edge
- **Accessibility testing**: Keyboard nav, screen readers (NVDA/VoiceOver)

### Test Execution Order
1. **Functional tests** (P0) - Verify layouts work on all 4 pages
2. **Consistency tests** (P0) - Validate pattern matches Explorer/Credit/Rates
3. **Accessibility tests** (P0) - WCAG 2.1 AA compliance for all 4 pages
4. **Integration tests** (P1) - Component interactions
5. **Performance tests** (P1) - Page load, rendering
6. **Edge case tests** (P2) - Boundary conditions
7. **Cross-browser tests** (P2) - All browsers

### Pass/Fail Criteria
- **P0 tests:** 100% must pass (23 tests)
- **P1 tests:** 90%+ must pass (18 tests)
- **P2 tests:** 80%+ should pass (15 tests)
- **Total:** 56+ test cases covering all 4 pages

---

## Test Cases

### Category 1: Functional - Mobile Layout (< 768px)
**Priority:** P0
**Pages:** All 4 (Dollar, Equities, Crypto, Safe Havens)

#### TC-1.1: Visual Hierarchy - Dollar Page
**Given:** Dollar page loaded on mobile (375px viewport)
**When:** Page renders
**Then:**
- [ ] Visual hierarchy (top to bottom):
  1. Navigation bar (64px)
  2. Page title "Dollar Markets" + Last Updated timestamp
  3. Chart (HERO - 50-60vh, visible without scrolling)
  4. Time range controls
  5. Collapsible sections (collapsed by default)
- [ ] Chart visible within first screen without scrolling
- [ ] Total page height ≤ 1000px in collapsed state

**Test Data:** `/dollar` at 375x667px
**Expected Result:** ✅ Hierarchy matches spec, chart prominent

---

#### TC-1.2: Visual Hierarchy - Equities Page
**Given:** Equities page loaded on mobile (375px viewport)
**When:** Page renders
**Then:**
- [ ] Visual hierarchy matches TC-1.1 format
- [ ] Page title "Equities Markets" displayed correctly
- [ ] Chart visible without scrolling
- [ ] Total page height ≤ 1000px in collapsed state

**Test Data:** `/equities` at 375x667px
**Expected Result:** ✅ Hierarchy matches spec

---

#### TC-1.3: Visual Hierarchy - Crypto Page
**Given:** Crypto page loaded on mobile (375px viewport)
**When:** Page renders
**Then:**
- [ ] Visual hierarchy matches TC-1.1 format
- [ ] Page title "Crypto Markets" displayed correctly
- [ ] Chart visible without scrolling
- [ ] Total page height ≤ 1000px in collapsed state

**Test Data:** `/crypto` at 375x667px
**Expected Result:** ✅ Hierarchy matches spec

---

#### TC-1.4: Visual Hierarchy - Safe Havens Page
**Given:** Safe Havens page loaded on mobile (375px viewport)
**When:** Page renders
**Then:**
- [ ] Visual hierarchy matches TC-1.1 format
- [ ] Page title "Safe Haven Assets" displayed correctly
- [ ] Chart visible without scrolling
- [ ] Total page height ≤ 1000px in collapsed state

**Test Data:** `/safe-havens` at 375x667px
**Expected Result:** ✅ Hierarchy matches spec

---

#### TC-1.5: Chart Prominence - All Pages
**Priority:** P0
**Given:** Any asset page loaded on mobile
**When:** User views page
**Then:**
- [ ] Chart height: 50vh (min 300px, max 400px) on all 4 pages
- [ ] Chart visible within first screen on all 4 pages (no scrolling)
- [ ] Chart is primary visual element on all 4 pages
- [ ] No metric selector present (fixed asset class per page)

**Test Data:** All 4 pages at 375px
**Expected Result:** ✅ Charts prominent on all pages

---

#### TC-1.6: Progressive Disclosure - All Pages
**Priority:** P0
**Given:** Any asset page loaded on mobile
**When:** Page renders in collapsed state
**Then:**
- [ ] "Market Statistics" section collapsed by default on all 4 pages
- [ ] "About This Asset Class" section collapsed by default on all 4 pages
- [ ] Any asset-specific sections collapsed by default (e.g., Dollar: "Currency Pairs")
- [ ] Clear expand affordance (divider/chevron pattern) on all sections
- [ ] All pages use identical collapsible component

**Test Data:** All 4 pages at 375px
**Expected Result:** ✅ All sections collapsed, consistent pattern

---

#### TC-1.7: Scroll Reduction - Dollar Page
**Priority:** P0
**Given:** Dollar page on mobile (collapsed state)
**When:** Measure total page height
**Then:**
- [ ] Current page height (before redesign): ~2000px
- [ ] New page height (collapsed): ≤ 1000px
- [ ] Reduction: 50%+ vs. current state

**Test Data:** `/dollar` at 375px, DevTools height measurement
**Expected Result:** ✅ 50%+ scroll reduction achieved

---

#### TC-1.8: Scroll Reduction - Equities Page
**Priority:** P0
**Given:** Equities page on mobile (collapsed state)
**When:** Measure total page height
**Then:**
- [ ] Total height ≤ 1000px
- [ ] 50%+ reduction vs. current state

**Test Data:** `/equities` at 375px
**Expected Result:** ✅ 50%+ scroll reduction

---

#### TC-1.9: Scroll Reduction - Crypto Page
**Priority:** P0
**Given:** Crypto page on mobile (collapsed state)
**When:** Measure total page height
**Then:**
- [ ] Total height ≤ 1000px
- [ ] 50%+ reduction vs. current state

**Test Data:** `/crypto` at 375px
**Expected Result:** ✅ 50%+ scroll reduction

---

#### TC-1.10: Scroll Reduction - Safe Havens Page
**Priority:** P0
**Given:** Safe Havens page on mobile (collapsed state)
**When:** Measure total page height
**Then:**
- [ ] Total height ≤ 1000px
- [ ] 50%+ reduction vs. current state

**Test Data:** `/safe-havens` at 375px
**Expected Result:** ✅ 50%+ scroll reduction

---

### Category 2: Functional - Tablet Layout (768px - 1023px)
**Priority:** P1

#### TC-2.1: Hybrid Layout - Dollar Page
**Given:** Dollar page loaded on tablet (768px viewport)
**When:** Page renders
**Then:**
- [ ] Chart and key stats side-by-side (60/40 split)
- [ ] Chart height: 400px fixed
- [ ] 3-5 key statistics visible without expansion
- [ ] Detailed statistics remain collapsed
- [ ] Layout uses grid system (1.5fr 1fr)

**Test Data:** `/dollar` at 768x1024px
**Expected Result:** ✅ Hybrid layout working

---

#### TC-2.2: Hybrid Layout - Equities Page
**Given:** Equities page loaded on tablet
**When:** Page renders
**Then:**
- [ ] Chart + stats side-by-side (60/40 split)
- [ ] Chart height: 400px
- [ ] 3-5 key stats visible

**Test Data:** `/equities` at 768px
**Expected Result:** ✅ Hybrid layout working

---

#### TC-2.3: Hybrid Layout - Crypto Page
**Given:** Crypto page loaded on tablet
**When:** Page renders
**Then:**
- [ ] Chart + stats side-by-side (60/40 split)
- [ ] Chart height: 400px
- [ ] 3-5 key stats visible

**Test Data:** `/crypto` at 768px
**Expected Result:** ✅ Hybrid layout working

---

#### TC-2.4: Hybrid Layout - Safe Havens Page
**Given:** Safe Havens page loaded on tablet
**When:** Page renders
**Then:**
- [ ] Chart + stats side-by-side (60/40 split)
- [ ] Chart height: 400px
- [ ] 3-5 key stats visible

**Test Data:** `/safe-havens` at 768px
**Expected Result:** ✅ Hybrid layout working

---

### Category 3: Functional - Desktop Layout (1024px+)
**Priority:** P1

#### TC-3.1: Desktop Enhanced Layout - All Pages
**Given:** Any asset page loaded on desktop (1920px viewport)
**When:** Page renders
**Then:**
- [ ] Chart + stats grid side-by-side (66/33 split) on all 4 pages
- [ ] Chart height: 500px on all 4 pages
- [ ] All key statistics visible on all 4 pages
- [ ] No regression from current desktop experience on any page
- [ ] Grid uses 2fr 1fr column ratio

**Test Data:** All 4 pages at 1920x1080px
**Expected Result:** ✅ Desktop excellence maintained

---

### Category 4: Consistency Across All Asset Pages
**Priority:** P0 (Critical for Feature 3.1 completion)

#### TC-4.1: Component Consistency - All 7 Pages
**Given:** All 7 content pages (Explorer, Credit, Rates, Dollar, Equities, Crypto, Safe Havens)
**When:** Review implementation
**Then:**
- [ ] All 7 pages use identical CollapsibleSection component
- [ ] All 7 pages use identical ChartContainer component
- [ ] All 7 pages use identical responsive breakpoints (768px, 1024px)
- [ ] All 7 pages use identical progressive disclosure pattern
- [ ] All 7 pages use identical design system styling

**Test Data:** Visual inspection + code review
**Expected Result:** ✅ 100% component consistency

---

#### TC-4.2: Mobile Pattern Consistency - All 7 Pages
**Given:** All 7 pages loaded on mobile (375px)
**When:** Compare visual hierarchy
**Then:**
- [ ] All pages: Nav → Title → Chart → Time Controls → Collapsed Sections
- [ ] All pages: Chart at 50vh (min 300px, max 400px)
- [ ] All pages: Sections collapsed by default
- [ ] All pages: ≤ 1000px total height (collapsed)
- [ ] Visually indistinguishable patterns (except page titles/data)

**Test Data:** All 7 pages at 375px, side-by-side comparison
**Expected Result:** ✅ Perfect pattern consistency

---

#### TC-4.3: Tablet Pattern Consistency - All 7 Pages
**Given:** All 7 pages loaded on tablet (768px)
**When:** Compare layouts
**Then:**
- [ ] All pages: Chart + stats side-by-side (60/40 split)
- [ ] All pages: Chart height 400px
- [ ] All pages: 3-5 key stats visible
- [ ] Pattern identical across all 7 pages

**Test Data:** All 7 pages at 768px
**Expected Result:** ✅ Tablet consistency maintained

---

#### TC-4.4: Desktop Pattern Consistency - All 7 Pages
**Given:** All 7 pages loaded on desktop (1920px)
**When:** Compare layouts
**Then:**
- [ ] All pages: Chart + stats grid (66/33 split)
- [ ] All pages: Chart height 500px
- [ ] All pages: Same grid system, spacing, styles
- [ ] Pattern identical across all 7 pages

**Test Data:** All 7 pages at 1920px
**Expected Result:** ✅ Desktop consistency maintained

---

### Category 5: Page-Specific Customization
**Priority:** P1

#### TC-5.1: Dollar Page Custom Sections
**Given:** Dollar page loaded
**When:** Review page-specific sections
**Then:**
- [ ] Dollar-specific sections present (e.g., "DXY Analysis", "Currency Pairs")
- [ ] All custom sections use collapsible pattern on mobile
- [ ] Custom sections match design system styling
- [ ] Custom sections don't break layout on any viewport

**Test Data:** `/dollar` at all viewports
**Expected Result:** ✅ Dollar sections work correctly

---

#### TC-5.2: Equities Page Custom Sections
**Given:** Equities page loaded
**When:** Review page-specific sections
**Then:**
- [ ] Equity-specific sections present (e.g., "Market Indices", "Sector Performance")
- [ ] All custom sections use collapsible pattern on mobile
- [ ] Custom sections match design system styling

**Test Data:** `/equities` at all viewports
**Expected Result:** ✅ Equities sections work correctly

---

#### TC-5.3: Crypto Page Custom Sections
**Given:** Crypto page loaded
**When:** Review page-specific sections
**Then:**
- [ ] Crypto-specific sections present (e.g., "Market Cap", "On-Chain Metrics")
- [ ] All custom sections use collapsible pattern on mobile
- [ ] Custom sections match design system styling

**Test Data:** `/crypto` at all viewports
**Expected Result:** ✅ Crypto sections work correctly

---

#### TC-5.4: Safe Havens Page Custom Sections
**Given:** Safe Havens page loaded
**When:** Review page-specific sections
**Then:**
- [ ] Safe haven-specific sections present (e.g., "Gold/Silver Analysis", "Bonds")
- [ ] All custom sections use collapsible pattern on mobile
- [ ] Custom sections match design system styling

**Test Data:** `/safe-havens` at all viewports
**Expected Result:** ✅ Safe haven sections work correctly

---

### Category 6: Integration & Interactivity
**Priority:** P1

#### TC-6.1: Collapsible Section Interactions - All Pages
**Given:** Any asset page loaded
**When:** User taps/clicks collapsible section header
**Then:**
- [ ] Section expands smoothly (250ms animation) on all 4 pages
- [ ] Chevron rotates 180° on all 4 pages
- [ ] ARIA expanded state updates (aria-expanded="true")
- [ ] Section collapses on second tap (200ms animation)
- [ ] Keyboard support works (Space/Enter to toggle)

**Test Data:** All 4 pages, all viewports
**Expected Result:** ✅ Collapsible interactions work perfectly

---

#### TC-6.2: Chart Interactivity - Mobile
**Given:** Any asset page loaded on mobile
**When:** User taps chart data point
**Then:**
- [ ] Tooltip appears showing data details on all 4 pages
- [ ] Tooltip positioned correctly (not off-screen)
- [ ] Touch target ≥ 44px for tap detection
- [ ] No hover-dependent functionality

**Test Data:** All 4 pages, real iOS/Android devices
**Expected Result:** ✅ Chart tap tooltips work

---

#### TC-6.3: Time Range Controls - All Pages
**Given:** Any asset page loaded
**When:** User selects time range (1D, 1W, 1M, etc.)
**Then:**
- [ ] Chart updates with new time range data on all 4 pages
- [ ] Active button shows selected state (brand-blue-500 bg)
- [ ] Buttons meet 44px touch target minimum
- [ ] Controls work on mobile, tablet, desktop

**Test Data:** All 4 pages, all viewports
**Expected Result:** ✅ Time controls functional

---

#### TC-6.4: State Management
**Given:** User expands multiple sections
**When:** User navigates away and returns
**Then:**
- [ ] Sections return to default collapsed state (no state persistence)
- [ ] OR (if implemented) expanded state persists via localStorage
- [ ] No JavaScript errors on page load/navigation

**Test Data:** All 4 pages, browser navigation
**Expected Result:** ✅ State management correct

---

### Category 7: Edge Cases
**Priority:** P2

#### TC-7.1: Viewport Extremes
**Given:** Asset pages loaded at edge viewports
**When:** Test at 320px, 375px, 414px, 768px, 1024px, 1920px, 2560px
**Then:**
- [ ] No horizontal scrolling at any viewport on all 4 pages
- [ ] Chart renders correctly at all viewports
- [ ] Layout doesn't break at any breakpoint
- [ ] Touch targets remain ≥ 44px at all viewports

**Test Data:** All 4 pages, 7 viewports
**Expected Result:** ✅ Works at all viewport sizes

---

#### TC-7.2: Missing/Null Data
**Given:** Asset page with missing chart data
**When:** Page loads
**Then:**
- [ ] Graceful error message displayed
- [ ] Page layout doesn't break
- [ ] Collapsible sections still work
- [ ] No JavaScript errors in console

**Test Data:** Mock missing data scenario
**Expected Result:** ✅ Handles missing data gracefully

---

#### TC-7.3: Slow Network (3G)
**Given:** Asset page loaded on slow 3G connection
**When:** Measure load time
**Then:**
- [ ] Page renders skeleton/loading state
- [ ] LCP (Largest Contentful Paint) < 2.5s
- [ ] Chart loads progressively
- [ ] User can interact with page before full load

**Test Data:** Chrome DevTools 3G throttling, all 4 pages
**Expected Result:** ✅ Performance acceptable on slow network

---

#### TC-7.4: Rapid Viewport Resize
**Given:** Asset page loaded on desktop
**When:** User rapidly resizes browser window
**Then:**
- [ ] Layout adapts smoothly without breaking
- [ ] No content overflow or clipping
- [ ] Chart resizes correctly
- [ ] No JavaScript errors

**Test Data:** All 4 pages, manual resize testing
**Expected Result:** ✅ Handles resizing gracefully

---

### Category 8: Security
**Priority:** P1

#### TC-8.1: XSS Prevention - Page Titles
**Given:** Asset page templates
**When:** Review HTML output
**Then:**
- [ ] All user-supplied content properly escaped
- [ ] Page titles sanitized (Dollar, Equities, Crypto, Safe Havens)
- [ ] Section headers sanitized
- [ ] No inline JavaScript in templates

**Test Data:** Template code review
**Expected Result:** ✅ XSS protection in place

---

#### TC-8.2: SQL Injection - Chart Data
**Given:** Chart data fetched from database
**When:** Review data fetching code
**Then:**
- [ ] Parameterized queries used (no string concatenation)
- [ ] Input validation on any query parameters
- [ ] No direct SQL in templates

**Test Data:** Backend code review
**Expected Result:** ✅ SQL injection prevented

---

#### TC-8.3: CSRF Protection
**Given:** Any forms on asset pages (if applicable)
**When:** Submit form
**Then:**
- [ ] CSRF token present and validated
- [ ] POST requests protected
- [ ] Flask CSRF protection enabled

**Test Data:** Form submission testing
**Expected Result:** ✅ CSRF protection active

---

#### TC-8.4: Input Validation
**Given:** Any user inputs (time range selections, etc.)
**When:** User provides input
**Then:**
- [ ] Client-side validation present
- [ ] Server-side validation enforced
- [ ] Invalid inputs rejected gracefully
- [ ] No data type vulnerabilities

**Test Data:** Boundary value testing
**Expected Result:** ✅ Validation robust

---

### Category 9: Performance
**Priority:** P1

#### TC-9.1: Page Load Time - All Pages
**Given:** Asset pages loaded on 4G connection
**When:** Measure Lighthouse performance
**Then:**
- [ ] Performance score ≥ 90 on all 4 pages
- [ ] LCP < 2.5s on all 4 pages
- [ ] FID < 100ms
- [ ] CLS < 0.1

**Test Data:** Lighthouse audit, all 4 pages
**Expected Result:** ✅ Performance scores excellent

---

#### TC-9.2: Chart Render Time
**Given:** Asset page loaded
**When:** Chart renders
**Then:**
- [ ] Chart render time < 500ms on all 4 pages
- [ ] No frame drops during animation
- [ ] Smooth 60fps animations
- [ ] No jank during scrolling

**Test Data:** Chrome DevTools Performance profiler
**Expected Result:** ✅ Smooth rendering

---

#### TC-9.3: Animation Performance
**Given:** Collapsible sections on asset pages
**When:** User expands/collapses sections
**Then:**
- [ ] Animations run at 60fps on all 4 pages
- [ ] No layout thrashing
- [ ] GPU-accelerated transforms used
- [ ] Smooth on low-end devices (2019 Android)

**Test Data:** Chrome DevTools Performance panel
**Expected Result:** ✅ Animations performant

---

#### TC-9.4: Memory Usage
**Given:** User navigates between all 4 asset pages
**When:** Monitor memory usage
**Then:**
- [ ] No memory leaks detected
- [ ] Chart instances properly cleaned up on navigation
- [ ] Event listeners removed on page unload
- [ ] Heap size remains stable

**Test Data:** Chrome DevTools Memory profiler
**Expected Result:** ✅ No memory leaks

---

### Category 10: Accessibility (WCAG 2.1 AA)
**Priority:** P0

#### TC-10.1: Touch Targets - All Pages
**Given:** Asset pages on mobile
**When:** Measure interactive elements
**Then:**
- [ ] All buttons ≥ 44px height on all 4 pages
- [ ] Collapsible section headers ≥ 56px on all 4 pages
- [ ] Time range buttons ≥ 44px on all 4 pages
- [ ] Adequate spacing between targets (≥ 8px)

**Test Data:** DevTools element inspection, all 4 pages
**Expected Result:** ✅ All touch targets compliant

---

#### TC-10.2: Keyboard Navigation - All Pages
**Given:** Asset pages loaded
**When:** User navigates via keyboard only
**Then:**
- [ ] All interactive elements accessible via Tab on all 4 pages
- [ ] Collapsible sections toggle with Space/Enter
- [ ] Time range buttons selectable with Enter
- [ ] Visible focus indicators (2px outline, brand-blue-500)
- [ ] Logical tab order (top to bottom)

**Test Data:** Manual keyboard testing, all 4 pages
**Expected Result:** ✅ Full keyboard accessibility

---

#### TC-10.3: Screen Reader - All Pages
**Given:** Asset pages loaded with screen reader (NVDA/VoiceOver)
**When:** Screen reader navigates page
**Then:**
- [ ] Page titles announced correctly on all 4 pages
- [ ] Collapsible section states announced (expanded/collapsed)
- [ ] Chart data accessible (alt text or data table alternative)
- [ ] Semantic HTML structure (section, article, aside)
- [ ] Proper heading hierarchy (H1 → H2 → H3)

**Test Data:** NVDA (Windows), VoiceOver (iOS/Mac), all 4 pages
**Expected Result:** ✅ Screen reader compatible

---

#### TC-10.4: Color Contrast - All Pages
**Given:** Asset pages loaded
**When:** Check color contrast with WebAIM Contrast Checker
**Then:**
- [ ] All text meets 4.5:1 minimum (WCAG AA) on all 4 pages
- [ ] UI elements meet 3:1 contrast
- [ ] Chart colors from colorblind-friendly palette
- [ ] No information conveyed by color alone

**Test Data:** WebAIM Contrast Checker, all 4 pages
**Expected Result:** ✅ All contrast ratios compliant

---

#### TC-10.5: ARIA Attributes - All Pages
**Given:** Asset page HTML
**When:** Inspect ARIA attributes
**Then:**
- [ ] aria-expanded on collapsible headers (all 4 pages)
- [ ] aria-hidden on decorative icons
- [ ] aria-label on icon-only buttons
- [ ] Proper role attributes where needed
- [ ] No ARIA errors in accessibility tree

**Test Data:** axe DevTools audit, all 4 pages
**Expected Result:** ✅ ARIA correctly implemented

---

#### TC-10.6: Focus Management
**Given:** User expands collapsible section
**When:** Section expands
**Then:**
- [ ] Focus remains on header button on all 4 pages
- [ ] OR focus moves to expanded content (if appropriate)
- [ ] No focus traps
- [ ] Focus visible at all times

**Test Data:** Keyboard testing, all 4 pages
**Expected Result:** ✅ Focus management correct

---

### Category 11: Cross-Browser & Device Testing
**Priority:** P2

#### TC-11.1: Chrome Desktop - All Pages
**Given:** Asset pages loaded in Chrome (latest)
**When:** Test functionality
**Then:**
- [ ] All features work correctly on all 4 pages
- [ ] Layout renders correctly
- [ ] No console errors

**Test Data:** Chrome 120+, all 4 pages
**Expected Result:** ✅ Chrome fully supported

---

#### TC-11.2: Safari Desktop - All Pages
**Given:** Asset pages loaded in Safari (latest)
**When:** Test functionality
**Then:**
- [ ] All features work correctly on all 4 pages
- [ ] Sticky positioning works (check for Safari bugs)
- [ ] Layout renders correctly

**Test Data:** Safari 17+, all 4 pages
**Expected Result:** ✅ Safari fully supported

---

#### TC-11.3: Firefox Desktop - All Pages
**Given:** Asset pages loaded in Firefox (latest)
**When:** Test functionality
**Then:**
- [ ] All features work correctly on all 4 pages
- [ ] Layout renders correctly
- [ ] Animations smooth

**Test Data:** Firefox 120+, all 4 pages
**Expected Result:** ✅ Firefox fully supported

---

#### TC-11.4: iOS Safari Mobile - All Pages
**Given:** Asset pages loaded on iPhone (iOS Safari)
**When:** Test on real device
**Then:**
- [ ] Touch interactions work on all 4 pages
- [ ] Sticky positioning works correctly
- [ ] Chart tap tooltips functional
- [ ] No viewport zoom issues

**Test Data:** iPhone (iOS 16+), all 4 pages
**Expected Result:** ✅ iOS Safari fully supported

---

#### TC-11.5: Android Chrome Mobile - All Pages
**Given:** Asset pages loaded on Android (Chrome)
**When:** Test on real device
**Then:**
- [ ] Touch interactions work on all 4 pages
- [ ] Layout renders correctly
- [ ] Performance acceptable (2019 device)
- [ ] Chart interactions smooth

**Test Data:** Android device (2019+), all 4 pages
**Expected Result:** ✅ Android Chrome supported

---

### Category 12: Visual Regression (Playwright)
**Priority:** P0

#### TC-12.1: Playwright Screenshots - Dollar Page
**Given:** Dollar page loaded
**When:** Capture screenshots at 3 viewports
**Then:**
- [ ] Mobile (375x667): Chart visible, sections collapsed, ≤1000px height
- [ ] Tablet (768x1024): Hybrid layout, chart + stats side-by-side
- [ ] Desktop (1920x1080): Enhanced layout, chart + stats grid

**Test Data:** `/dollar`, Playwright screenshot script
**Expected Result:** ✅ Screenshots validate layouts

---

#### TC-12.2: Playwright Screenshots - Equities Page
**Given:** Equities page loaded
**When:** Capture screenshots at 3 viewports
**Then:**
- [ ] Mobile: Chart visible, sections collapsed
- [ ] Tablet: Hybrid layout
- [ ] Desktop: Enhanced layout

**Test Data:** `/equities`, Playwright
**Expected Result:** ✅ Screenshots validate layouts

---

#### TC-12.3: Playwright Screenshots - Crypto Page
**Given:** Crypto page loaded
**When:** Capture screenshots at 3 viewports
**Then:**
- [ ] Mobile: Chart visible, sections collapsed
- [ ] Tablet: Hybrid layout
- [ ] Desktop: Enhanced layout

**Test Data:** `/crypto`, Playwright
**Expected Result:** ✅ Screenshots validate layouts

---

#### TC-12.4: Playwright Screenshots - Safe Havens Page
**Given:** Safe Havens page loaded
**When:** Capture screenshots at 3 viewports
**Then:**
- [ ] Mobile: Chart visible, sections collapsed
- [ ] Tablet: Hybrid layout
- [ ] Desktop: Enhanced layout

**Test Data:** `/safe-havens`, Playwright
**Expected Result:** ✅ Screenshots validate layouts

---

## Test Execution Summary

### Total Test Cases: 56

**By Category:**
- Functional (Mobile): 10 test cases
- Functional (Tablet): 4 test cases
- Functional (Desktop): 1 test case
- Consistency: 4 test cases (critical for Feature 3.1)
- Page-Specific: 4 test cases
- Integration: 4 test cases
- Edge Cases: 4 test cases
- Security: 4 test cases
- Performance: 4 test cases
- Accessibility: 6 test cases
- Cross-Browser: 5 test cases
- Visual Regression: 4 test cases (12 screenshots total)

**By Priority:**
- **P0 (Critical):** 23 test cases - **Must pass 100% for approval**
- **P1 (High):** 18 test cases - **Should pass 90%+**
- **P2 (Medium):** 15 test cases - **Should pass 80%+**

### Testing Tools
- **Playwright** - Visual regression screenshots (12 total)
- **Lighthouse** - Performance + accessibility audits (4 pages)
- **WebAIM Contrast Checker** - Color contrast validation
- **NVDA/VoiceOver** - Screen reader testing
- **Chrome DevTools** - Performance profiling, memory analysis
- **Real Devices** - iPhone (iOS Safari), Android (Chrome)

### Estimated Test Execution Time
- **Automated tests:** 30 minutes (Playwright, Lighthouse)
- **Manual testing:** 3-4 hours (4 pages × 3 viewports × multiple browsers)
- **Accessibility testing:** 2 hours (keyboard nav, screen readers for 4 pages)
- **Performance testing:** 1 hour (profiling 4 pages)
- **Total:** ~7 hours for comprehensive testing

---

## Risk Mitigation Plan

### High-Risk Areas

**1. Safari iOS Sticky Positioning**
- **Risk:** Safari has known bugs with sticky positioning
- **Mitigation:**
  - Test early on real iOS devices
  - Have fallback: static positioning if sticky fails
  - Validate in Safari 16+ and Safari 17+

**2. Chart Touch Targets (44px minimum)**
- **Risk:** Chart library may not support 44px touch targets natively
- **Mitigation:**
  - Test chart interactions early
  - May need to modify chart library configuration
  - Overlay transparent touch targets if needed
  - Validate on real devices (fat finger testing)

**3. Consistency Drift Across 4 Pages**
- **Risk:** Implementing 4 pages increases chance of subtle deviations
- **Mitigation:**
  - Use identical components (CollapsibleSection, ChartContainer, KeyStatsPanel)
  - Copy-paste template structure, only change data/titles
  - Visual diff all 4 pages side-by-side
  - Automated screenshot comparison vs. Explorer/Credit/Rates

**4. Performance on Low-End Devices**
- **Risk:** 4 pages with charts + animations may be slow on older phones
- **Mitigation:**
  - Test on 2019 Android device (low-end baseline)
  - Use GPU-accelerated CSS transforms
  - Lazy load chart data if needed
  - Throttle resize events

**5. Page-Specific Sections Breaking Layout**
- **Risk:** Custom sections (Currency Pairs, On-Chain Metrics, etc.) may not fit pattern
- **Mitigation:**
  - Ensure all custom sections use CollapsibleSection component
  - Test each custom section at all viewports
  - Validate no content overflow or horizontal scroll

---

## Acceptance Criteria Validation

### From User Story #86

#### Mobile Layout (< 768px) - All 4 Pages ✅
- ✓ Visual hierarchy (Nav → Title → Chart → Controls → Collapsed Sections)
- ✓ Chart prominence (50-60vh, visible without scrolling)
- ✓ Progressive disclosure (sections collapsed by default)
- ✓ Scroll reduction (≤1000px total height, 50%+ reduction)

**Test Cases:** TC-1.1 through TC-1.10 validate these criteria

#### Tablet Layout (768px - 1023px) - All 4 Pages ✅
- ✓ Hybrid layout (chart + stats side-by-side, 60/40 split)
- ✓ 3-5 key stats visible without expansion
- ✓ Chart height: 400px fixed

**Test Cases:** TC-2.1 through TC-2.4 validate these criteria

#### Desktop Layout (1024px+) - All 4 Pages ✅
- ✓ Enhanced layout (chart + stats grid, 66/33 split)
- ✓ All key statistics visible
- ✓ Chart height: 500px
- ✓ No regression from current desktop experience

**Test Cases:** TC-3.1 validates these criteria

#### Consistency Across All Asset Pages ✅
- ✓ All 7 content pages use identical layout pattern
- ✓ Same component usage across all pages
- ✓ Same responsive breakpoints and behavior
- ✓ Same progressive disclosure interactions
- ✓ Consistent design system styling

**Test Cases:** TC-4.1 through TC-4.4 validate these criteria

#### Page-Specific Customization ✅
- ✓ Dollar-specific sections preserved and collapsible
- ✓ Equities-specific sections preserved and collapsible
- ✓ Crypto-specific sections preserved and collapsible
- ✓ Safe Havens-specific sections preserved and collapsible

**Test Cases:** TC-5.1 through TC-5.4 validate these criteria

#### Success Validation ✅
- ✓ Playwright screenshots (12 total: 4 pages × 3 viewports)
- ✓ Manual testing on real mobile devices
- ✓ Chart interactivity works on all pages
- ✓ Collapsible sections work on all pages
- ✓ Keyboard navigation verified
- ✓ No regressions on desktop
- ✓ Accessibility compliance (WCAG 2.1 AA)

**Test Cases:** TC-12.1 through TC-12.4 (screenshots), TC-10.1 through TC-10.6 (accessibility)

---

## Test Reporting

### Pass/Fail Tracking
After each test run, update this table:

| Category | Total | Passed | Failed | Pass % | Status |
|----------|-------|--------|--------|--------|--------|
| Functional (Mobile) | 10 | - | - | - | ⏳ |
| Functional (Tablet) | 4 | - | - | - | ⏳ |
| Functional (Desktop) | 1 | - | - | - | ⏳ |
| Consistency | 4 | - | - | - | ⏳ |
| Page-Specific | 4 | - | - | - | ⏳ |
| Integration | 4 | - | - | - | ⏳ |
| Edge Cases | 4 | - | - | - | ⏳ |
| Security | 4 | - | - | - | ⏳ |
| Performance | 4 | - | - | - | ⏳ |
| Accessibility | 6 | - | - | - | ⏳ |
| Cross-Browser | 5 | - | - | - | ⏳ |
| Visual Regression | 4 | - | - | - | ⏳ |
| **TOTAL** | **56** | **-** | **-** | **-** | **⏳** |

### Bug Severity Classification
If bugs found, classify as:
- **P0 (Blocker):** Prevents feature from working, must fix before approval
- **P1 (Critical):** Major functionality broken, should fix before approval
- **P2 (High):** Important issue, fix before release
- **P3 (Medium):** Minor issue, can fix post-release
- **P4 (Low):** Cosmetic issue, backlog

### Final Verdict
**APPROVED** ✅ if:
- All P0 tests pass (23/23)
- 90%+ P1 tests pass (16+/18)
- 80%+ P2 tests pass (12+/15)
- No P0 or P1 bugs found

**CHANGES REQUESTED** ⚠️ if:
- Any P0 tests fail
- < 90% P1 tests pass
- P0 or P1 bugs found

---

## Coverage Gaps (Acknowledged)

**Out of Scope for US-3.1.4:**
- Load testing (high concurrent users)
- Internationalization/RTL support
- Offline mode/PWA functionality
- Print styles
- Advanced chart features (export, sharing, annotations)
- Custom time range selection (date picker)
- Multi-metric comparison on single chart

These gaps are acceptable for Feature 3.1 and can be addressed in future features if needed.

---

## Next Steps

1. ✅ **Test plan created** - This document
2. ⏳ **Post to GitHub issue #86** - For PM/designer/engineer visibility
3. ⏳ **Engineer implements** - Following design spec
4. ⏳ **QA executes test plan** - Run all 56 test cases
5. ⏳ **Designer reviews** - Verify design compliance (screenshots)
6. ⏳ **QA reports results** - APPROVED or CHANGES_REQUESTED
7. ⏳ **Iterate if needed** - Fix issues, re-test (max 3 cycles)
8. ⏳ **Final approval** - All stakeholders sign off
9. ⏳ **PR merged** - Feature 3.1 complete!

---

**Test Plan Status:** ✅ Ready for Implementation
**Created By:** QA Test Engineer
**Date:** 2026-02-21
**Version:** 1.0
