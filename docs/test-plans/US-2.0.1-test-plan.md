# Test Plan: US-2.0.1 - Market Conditions Progressive Disclosure

**Issue**: #36
**Feature**: Implement progressive disclosure for Market Conditions section
**Risk Level**: Medium (UI change affecting main dashboard page)
**Test Date**: 2026-02-13

---

## Summary
Testing progressive disclosure implementation for the Market Conditions section. This feature adds expand/collapse functionality to show/hide detailed market data. Primary risks include JavaScript errors, broken links in expanded state, poor UX due to jarring transitions, and accessibility failures.

---

## Test Cases

### 1. Functional Tests - Core Behavior

#### TC-1.1: Default Collapsed State on Page Load
**Priority**: P0 - Critical
**Steps**:
1. Clear browser cache
2. Navigate to homepage (/)
3. Observe Market Conditions section state

**Expected**:
- Section displays in collapsed state
- Summary widget is visible (6 status indicators + AI synthesis)
- "Show Details ↓" button is visible below summary
- Grid cards are NOT visible in DOM (display:none or hidden)
- No console errors

**Data to Validate**:
- Check computed style: `document.getElementById('market-conditions-grid').style.display === 'none'`

---

#### TC-1.2: Expand to Show Details
**Priority**: P0 - Critical
**Steps**:
1. Load homepage (collapsed state)
2. Click "Show Details ↓" button

**Expected**:
- Grid expands smoothly (~300ms transition)
- All 6 category cards become visible (Credit, Equities, Rates, Dollar, Gold, Commodities)
- Button text changes to "Hide Details ↑"
- No layout shift or visual glitches
- No console errors

---

#### TC-1.3: Collapse to Hide Details
**Priority**: P0 - Critical
**Steps**:
1. Load homepage and expand grid (from TC-1.2)
2. Click "Hide Details ↑" button

**Expected**:
- Grid collapses smoothly (~300ms transition)
- Only summary widget remains visible
- Button text changes back to "Show Details ↓"
- No layout shift or visual glitches
- No console errors

---

#### TC-1.4: Multiple Expand/Collapse Cycles
**Priority**: P1 - High
**Steps**:
1. Load homepage
2. Click expand button
3. Click collapse button
4. Repeat steps 2-3 five times rapidly

**Expected**:
- Each transition completes smoothly
- No animation stutter or timing issues
- State remains consistent
- No console errors or memory leaks
- Button text updates correctly each time

---

### 2. Functional Tests - Grid Links & Data

#### TC-2.1: View Links Work in Expanded State
**Priority**: P0 - Critical
**Steps**:
1. Load homepage and expand grid
2. Click each "View [Category] →" link:
   - View Credit →
   - View Equities →
   - View Rates →
   - View Dollar →
   - View Gold →
   - View Commodities →

**Expected**:
- Each link navigates to correct detail page
- No 404 errors
- Links are properly styled and clickable

---

#### TC-2.2: Data Loads Correctly in Grid
**Priority**: P1 - High
**Steps**:
1. Load homepage and expand grid
2. Inspect each category card for data population

**Expected**:
- Each card shows correct metrics
- Status indicators (up/down arrows, colors) display correctly
- Data matches what's shown in summary widget
- No "undefined" or "null" values visible

---

### 3. Edge Cases & Boundary Tests

#### TC-3.1: Rapid Click Spam Protection
**Priority**: P2 - Medium
**Steps**:
1. Load homepage
2. Click toggle button 20 times rapidly (stress test)

**Expected**:
- Animation doesn't break or get stuck
- Final state is deterministic (matches last click)
- No console errors
- No visual artifacts

---

#### TC-3.2: Page Load During Slow Network
**Priority**: P2 - Medium
**Steps**:
1. Open DevTools → Network tab
2. Set throttling to "Slow 3G"
3. Load homepage

**Expected**:
- Section still loads in collapsed state
- Summary widget appears before grid assets load
- Toggle button becomes interactive only after JS loads
- No FOUC (Flash of Unstyled Content)

---

#### TC-3.3: Missing/Failed Data Load
**Priority**: P2 - Medium
**Steps**:
1. Mock API failure for market data
2. Load homepage and expand grid

**Expected**:
- Grid structure still renders
- Graceful handling of missing data (placeholder or error message)
- Toggle button still works
- No JavaScript exceptions

---

### 4. Responsive & Cross-Browser Tests

#### TC-4.1: Mobile View (Portrait)
**Priority**: P1 - High
**Device**: iPhone 13 (390x844), Android Pixel 5 (393x851)
**Steps**:
1. Load homepage on mobile device
2. Tap "Show Details ↓" button
3. Scroll through expanded grid
4. Tap "Hide Details ↑" button

**Expected**:
- Touch tap triggers expand/collapse
- Grid cards stack vertically in mobile view
- Button remains accessible (not covered by keyboard or elements)
- Smooth scrolling behavior
- No horizontal scroll

---

#### TC-4.2: Tablet View (Portrait & Landscape)
**Priority**: P2 - Medium
**Device**: iPad Pro (1024x1366)
**Steps**:
1. Test in both portrait and landscape
2. Expand/collapse grid
3. Verify layout adapts correctly

**Expected**:
- Grid uses appropriate columns (2-3 depending on breakpoint)
- No awkward spacing or overflow
- Transition smooth on both orientations

---

#### TC-4.3: Cross-Browser Compatibility
**Priority**: P1 - High
**Browsers**: Chrome 120+, Firefox 120+, Safari 17+
**Steps**:
1. Test TC-1.1 through TC-1.4 on each browser
2. Verify CSS transitions work
3. Check button styling consistency

**Expected**:
- Identical behavior across all browsers
- CSS transitions render smoothly (no IE fallback needed)
- Bootstrap classes render correctly

---

### 5. Accessibility Tests

#### TC-5.1: Keyboard Navigation
**Priority**: P1 - High
**Steps**:
1. Load homepage
2. Use Tab key to navigate to toggle button
3. Press Enter to expand
4. Tab through grid cards and links
5. Tab back to toggle button
6. Press Enter to collapse

**Expected**:
- Button receives focus indicator
- Enter key triggers expand/collapse
- All grid links are keyboard accessible
- Focus order is logical
- No keyboard traps

---

#### TC-5.2: Screen Reader Compatibility
**Priority**: P2 - Medium
**Tools**: NVDA (Windows), VoiceOver (Mac)
**Steps**:
1. Load homepage with screen reader active
2. Navigate to Market Conditions section
3. Activate toggle button
4. Navigate through expanded grid

**Expected**:
- Button announces state ("Show Details" / "Hide Details")
- ARIA attributes present if needed (aria-expanded, aria-controls)
- Grid cards and links are properly announced
- No unlabeled buttons or links

---

#### TC-5.3: Focus Management
**Priority**: P2 - Medium
**Steps**:
1. Load homepage
2. Tab to toggle button and expand grid
3. Observe where focus goes after expansion
4. Collapse grid and observe focus

**Expected**:
- Focus remains on toggle button after expand
- No unexpected focus jumps
- Focus visible at all times

---

### 6. Performance Tests

#### TC-6.1: Animation Performance
**Priority**: P2 - Medium
**Steps**:
1. Load homepage
2. Open DevTools → Performance tab
3. Start recording
4. Expand/collapse grid 3 times
5. Stop recording and analyze

**Expected**:
- No significant frame drops (stay above 30fps)
- CSS transition completes in ~300ms
- No layout thrashing or reflows
- GPU acceleration used if possible

---

#### TC-6.2: Memory Leaks
**Priority**: P3 - Low
**Steps**:
1. Load homepage
2. Open DevTools → Memory tab
3. Take heap snapshot
4. Expand/collapse grid 50 times
5. Take another heap snapshot
6. Compare

**Expected**:
- No significant memory growth
- Event listeners properly cleaned up (if any)
- No detached DOM nodes accumulating

---

### 7. Security & Input Validation

#### TC-7.1: XSS Protection in Data Fields
**Priority**: P1 - High
**Steps**:
1. If data is dynamic, inject script tag in data source: `<script>alert('xss')</script>`
2. Load homepage and expand grid
3. Check if script executes

**Expected**:
- Script does NOT execute
- Data is properly escaped/sanitized
- HTML entities rendered as text

---

#### TC-7.2: DOM Manipulation Safety
**Priority**: P2 - Medium
**Steps**:
1. Open DevTools console
2. Attempt to manually trigger grid display: `document.getElementById('market-conditions-grid').style.display = 'block'`
3. Click toggle button

**Expected**:
- Manual manipulation doesn't break toggle logic
- State remains consistent with button text
- No console errors

---

## Test Execution Checklist

### Pre-Implementation (This Phase)
- [x] Test plan reviewed and approved
- [ ] Risk assessment completed

### Post-Implementation
- [ ] All P0 tests pass
- [ ] All P1 tests pass
- [ ] P2/P3 tests executed (document skips)
- [ ] No console errors in any test
- [ ] Cross-browser testing complete
- [ ] Mobile testing complete
- [ ] Accessibility spot-check complete

---

## Risk Assessment

### High Risk Areas
1. **JavaScript Toggle Logic**: Could fail silently if event listeners don't attach
2. **Data Loading**: Grid may not populate if existing JS has dependencies
3. **Layout Shift**: Poor transitions could cause jarring UX
4. **Mobile Touch**: Touch events might not trigger on all devices

### Mitigation Strategies
- Test toggle functionality extensively (TC-1.2 through TC-1.4)
- Verify data loads in expanded state (TC-2.2)
- Validate smooth transitions (TC-6.1)
- Test on real mobile devices, not just emulators (TC-4.1)

---

## Coverage Gaps

- **Load Testing**: Not testing with 100+ concurrent users (out of scope)
- **API Integration**: Assuming data endpoint is stable (tested separately)
- **Browser Versions**: Only testing latest versions, not legacy browsers
- **Automated E2E**: Manual testing only; no Selenium/Playwright tests planned

---

## Test Environment

- **Local Dev Server**: `python dashboard.py` running on localhost:5000
- **Browsers**: Chrome 120, Firefox 121, Safari 17.2
- **Mobile Devices**: Physical iPhone 13, Android Pixel 5
- **Screen Readers**: NVDA 2023.3, VoiceOver (macOS Sonoma)

---

## Exit Criteria

This test plan is considered complete when:
1. All P0 tests pass without errors
2. All P1 tests pass or have documented workarounds
3. P2 tests executed with results documented
4. No critical or high severity bugs found
5. Cross-browser compatibility verified
6. Mobile functionality verified on real devices
7. Basic accessibility compliance confirmed

---

## Notes for Engineer

- Pay special attention to the CSS transition timing (300ms)
- Ensure toggle button has proper Bootstrap classes for consistency
- Verify all existing grid IDs are preserved (they may be referenced by other JS)
- Consider adding data-testid attributes for future automated testing
- Animation should use CSS transitions (not JavaScript setTimeout)
