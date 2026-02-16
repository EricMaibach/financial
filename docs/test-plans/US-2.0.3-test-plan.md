# Test Plan: US-2.0.3 - Refine Market Conditions Widget Expansion UX

**Issue**: #72
**Feature**: Market Conditions widget expansion with refined UX
**Risk Level**: MEDIUM (UI/UX change to homepage, high visibility)

## Overview
This feature refines the Market Conditions section expansion UX by:
- Converting 6 summary badges into detailed cards in the same grid positions
- Using a subtle horizontal divider control (not a prominent button)
- Ensuring AI synthesis is always visible
- Providing smooth, natural animations

---

## Test Categories

### 1. Functional Testing (Happy Path)

#### TC-1.1: Default Collapsed State
**Given**: User loads the homepage
**When**: Page finishes loading
**Then**:
- [ ] AI synthesis text is visible
- [ ] 6 badge cards are displayed in a 2x3 grid
- [ ] Badge labels match: CREDIT, STOCKS, BONDS, COMMODITIES, CURRENCIES, VOLATILITY
- [ ] Each badge shows a status (e.g., CALM, ELEVATED, etc.)
- [ ] Expansion control shows "⌄ Show Details"
- [ ] Detail cards are hidden (display: none)
- [ ] aria-expanded="false" on control button

#### TC-1.2: Expand to Detail Cards
**Given**: User is viewing collapsed state
**When**: User clicks expansion control
**Then**:
- [ ] Badges disappear (display: none)
- [ ] Detail cards appear (display: grid) in 2x3 grid
- [ ] Cards appear in same positions as badges (Credit top-left, Stocks top-middle, etc.)
- [ ] Each card shows metrics and "View [Category] →" link
- [ ] Expansion control shows "⌃ Hide Details"
- [ ] aria-expanded="true" on control button
- [ ] AI synthesis remains visible throughout
- [ ] Transition is smooth (~350ms)

#### TC-1.3: Collapse Back to Badges
**Given**: User is viewing expanded state
**When**: User clicks expansion control
**Then**:
- [ ] Detail cards disappear (display: none)
- [ ] Badges reappear (display: grid) in 2x3 grid
- [ ] Expansion control shows "⌄ Show Details"
- [ ] aria-expanded="false" on control button
- [ ] AI synthesis remains visible throughout
- [ ] Transition is smooth (~350ms)

#### TC-1.4: Navigation Links Work in Expanded State
**Given**: User is viewing expanded state
**When**: User clicks "View Credit →" link
**Then**:
- [ ] User navigates to Credit detail page
- [ ] No JavaScript errors occur
- [ ] (Repeat for all 6 category links)

---

### 2. Visual & Layout Testing

#### TC-2.1: Grid Layout Integrity
**Given**: User views collapsed state
**Then**:
- [ ] 6 badges arranged in 2 rows, 3 columns
- [ ] Consistent spacing between badges (~1rem)
- [ ] Badges aligned properly (no offset)

**Given**: User views expanded state
**Then**:
- [ ] 6 cards arranged in 2 rows, 3 columns
- [ ] Consistent spacing between cards (~1.5rem)
- [ ] Cards aligned properly (no offset)

#### TC-2.2: Badge-to-Card Position Mapping
**Given**: User views collapsed then expanded state
**Then**:
- [ ] Credit badge (top-left) → Credit card (top-left)
- [ ] Stocks badge (top-middle) → Stocks card (top-middle)
- [ ] Bonds badge (top-right) → Bonds card (top-right)
- [ ] Commodities badge (bottom-left) → Commodities card (bottom-left)
- [ ] Currencies badge (bottom-middle) → Currencies card (bottom-middle)
- [ ] Volatility badge (bottom-right) → Volatility card (bottom-right)

#### TC-2.3: Expansion Control Styling
**Given**: User views the expansion control
**Then**:
- [ ] Control spans full section width
- [ ] Horizontal divider lines are light gray (#dee2e6)
- [ ] Button text is muted gray (#6c757d)
- [ ] Text size is ~0.9rem
- [ ] Chevron direction matches state (⌄ collapsed, ⌃ expanded)

**Given**: User hovers over control
**Then**:
- [ ] Text color darkens slightly (#495057)
- [ ] Cursor changes to pointer
- [ ] No other visual changes (no background, border, etc.)

#### TC-2.4: AI Synthesis Visibility
**Given**: User views collapsed state
**Then**: AI synthesis is visible above badges

**Given**: User views expanded state
**Then**: AI synthesis is visible above cards

**Given**: User toggles multiple times
**Then**: AI synthesis never disappears or moves

---

### 3. Animation & Transition Testing

#### TC-3.1: Expansion Animation Smoothness
**Given**: User clicks to expand
**Then**:
- [ ] Transition duration is ~350ms
- [ ] Easing function is ease-in-out
- [ ] No visible flickering or flashing
- [ ] No layout shift in other page sections
- [ ] Animation feels natural ("widgets growing")

#### TC-3.2: Collapse Animation Smoothness
**Given**: User clicks to collapse
**Then**:
- [ ] Transition duration is ~350ms
- [ ] Easing function is ease-in-out
- [ ] No visible flickering or flashing
- [ ] No layout shift in other page sections
- [ ] Animation feels natural ("widgets shrinking")

#### TC-3.3: Animation Performance
**Given**: User toggles expansion
**Then**:
- [ ] Animation runs at ~60fps (no jank)
- [ ] CPU usage stays reasonable
- [ ] No memory leaks after multiple toggles

---

### 4. Edge Cases & Error Handling

#### TC-4.1: Rapid Toggle Clicks
**Given**: User clicks expansion control very rapidly (5+ clicks in 1 second)
**Then**:
- [ ] Animation completes properly each time
- [ ] No state desync (badges/cards match control text)
- [ ] aria-expanded attribute stays in sync
- [ ] No JavaScript errors

#### TC-4.2: Missing Data Scenarios
**Given**: One or more badges have missing data (null status, missing label)
**Then**:
- [ ] Page doesn't crash
- [ ] Other badges/cards render normally
- [ ] Missing data shows fallback or blank (not "undefined" or "null")

#### TC-4.3: Long AI Synthesis Text
**Given**: AI synthesis text is very long (500+ characters)
**Then**:
- [ ] Text wraps properly (doesn't overflow container)
- [ ] Layout doesn't break
- [ ] Expansion control remains positioned correctly

#### TC-4.4: Browser Window Resize During Transition
**Given**: User clicks expand and immediately resizes browser window
**Then**:
- [ ] Animation completes without visual glitches
- [ ] Responsive layout adjusts correctly
- [ ] No layout shift issues

#### TC-4.5: Page Reload State
**Given**: User expands detail cards
**When**: User reloads page
**Then**:
- [ ] Page returns to default collapsed state (badges visible)
- [ ] No broken state or console errors

#### TC-4.6: JavaScript Disabled
**Given**: User has JavaScript disabled
**Then**:
- [ ] Badges are visible (default state)
- [ ] Expansion control doesn't work (expected)
- [ ] Page content is still accessible
- [ ] No broken layout

---

### 5. Accessibility Testing

#### TC-5.1: Keyboard Navigation
**Given**: User navigates with keyboard only
**When**: User tabs to expansion control
**Then**:
- [ ] Control receives visible focus indicator
- [ ] Pressing Enter toggles expansion
- [ ] Focus remains on control after toggle
- [ ] No keyboard traps

#### TC-5.2: Screen Reader Compatibility
**Given**: User uses a screen reader (NVDA, JAWS, VoiceOver)
**Then**:
- [ ] Expansion control is announced as a button
- [ ] aria-expanded state is announced ("collapsed" or "expanded")
- [ ] State change is announced when toggled
- [ ] Badge/card content is readable

#### TC-5.3: Touch Device Accessibility
**Given**: User uses a touch device (phone, tablet)
**Then**:
- [ ] Tapping expansion control toggles state
- [ ] Tap target is large enough (44x44px minimum)
- [ ] No unintended double-tap zoom

---

### 6. Responsive Design Testing

#### TC-6.1: Desktop View (≥992px)
**Given**: User views on desktop
**Then**:
- [ ] Badges/cards displayed in 2x3 grid
- [ ] Proper spacing and alignment
- [ ] Expansion control spans full width
- [ ] All content readable and accessible

#### TC-6.2: Tablet View (768px - 991px)
**Given**: User views on tablet
**Then**:
- [ ] Badges/cards displayed in 2x3 grid (or 2x2 if too narrow)
- [ ] Proper spacing and alignment
- [ ] Expansion control spans full width
- [ ] Touch interaction works

#### TC-6.3: Mobile View (≤767px)
**Given**: User views on mobile
**Then**:
- [ ] Badges/cards displayed in 2x2 grid (6 items, wrapped)
- [ ] Cards don't overflow screen width
- [ ] Text remains readable
- [ ] Expansion control works with touch
- [ ] Animation remains smooth

---

### 7. Browser Compatibility Testing

#### TC-7.1: Chrome
**Given**: User views in Chrome (latest version)
**Then**: All functionality works as expected

#### TC-7.2: Firefox
**Given**: User views in Firefox (latest version)
**Then**: All functionality works as expected

#### TC-7.3: Safari
**Given**: User views in Safari (latest version)
**Then**: All functionality works as expected

#### TC-7.4: Mobile Safari (iOS)
**Given**: User views in Mobile Safari
**Then**: Touch interactions and animations work smoothly

#### TC-7.5: Chrome Mobile (Android)
**Given**: User views in Chrome Mobile
**Then**: Touch interactions and animations work smoothly

---

### 8. Integration Testing

#### TC-8.1: No Impact on Other Sections
**Given**: User toggles Market Conditions expansion
**Then**:
- [ ] Other page sections don't move or shift
- [ ] Navigation, footer, other widgets unaffected
- [ ] Page scroll position remains stable

#### TC-8.2: Data Loading Integration
**Given**: Market Conditions data loads from backend
**Then**:
- [ ] Badges display correct status data
- [ ] Cards display correct metrics data
- [ ] No "loading" flicker after page load
- [ ] Data format matches expectations

#### TC-8.3: Link Navigation Integration
**Given**: User clicks "View Credit →" in expanded card
**Then**:
- [ ] Navigates to correct detail page (e.g., `/credit`)
- [ ] Detail page loads correctly
- [ ] Browser back button returns to homepage
- [ ] Homepage state resets to collapsed

---

### 9. Security Testing

#### TC-9.1: XSS in AI Synthesis
**Given**: AI synthesis contains malicious script (e.g., `<script>alert('XSS')</script>`)
**Then**:
- [ ] Script is escaped and not executed
- [ ] Text is displayed safely (HTML-encoded)
- [ ] No JavaScript execution occurs

#### TC-9.2: XSS in Badge/Card Data
**Given**: Badge status or card metric contains malicious content
**Then**:
- [ ] Content is escaped and not executed
- [ ] No XSS vulnerability exists

#### TC-9.3: CSRF Protection (if applicable)
**Given**: Expansion state is saved to backend (if implemented)
**Then**:
- [ ] CSRF token is validated
- [ ] Unauthorized requests are blocked

---

### 10. Performance Testing

#### TC-10.1: Animation Frame Rate
**Given**: User toggles expansion on mid-range device
**Then**:
- [ ] Animation runs at ~60fps
- [ ] No visible stuttering or lag
- [ ] Smooth visual transition

#### TC-10.2: DOM Manipulation Efficiency
**Given**: User toggles expansion multiple times
**Then**:
- [ ] No excessive DOM reflows
- [ ] No memory leaks (check DevTools)
- [ ] Page remains responsive

#### TC-10.3: Large Dataset Performance
**Given**: Detail cards contain large amounts of data (many metrics)
**Then**:
- [ ] Page loads without lag
- [ ] Expansion transition remains smooth
- [ ] No performance degradation

---

## Risks & Concerns

### High Risk
1. **Animation jank on mobile devices**: CSS transitions may not be smooth on older/low-end phones
   - **Mitigation**: Test on actual devices, consider `will-change` CSS property
2. **State desync with rapid clicks**: JavaScript toggle logic could get out of sync
   - **Mitigation**: Debounce or disable button during animation
3. **Regression on existing functionality**: Refactoring could break current working features
   - **Mitigation**: Test all existing Market Conditions features thoroughly

### Medium Risk
1. **Browser compatibility issues**: Different browsers may render animations differently
   - **Mitigation**: Test on Chrome, Firefox, Safari before release
2. **Responsive layout edge cases**: Unusual screen sizes (very narrow, very wide) may break layout
   - **Mitigation**: Test at multiple viewport widths

### Low Risk
1. **Accessibility gaps**: Screen reader announcements may not be perfect
   - **Mitigation**: Manual screen reader testing

---

## Coverage Gaps

1. **Visual regression testing**: No automated way to detect subtle CSS changes
   - **Recommendation**: Manual visual review, screenshot comparison
2. **Performance testing**: No load testing for concurrent users
   - **Recommendation**: Monitor analytics post-release
3. **User acceptance testing**: No real user feedback on "natural feel" of animation
   - **Recommendation**: Internal team review before release

---

## Test Execution Order

1. **Phase 1 - Functional Tests**: TC-1.1 to TC-1.4 (verify basic functionality)
2. **Phase 2 - Visual Tests**: TC-2.1 to TC-2.4 (verify layout and styling)
3. **Phase 3 - Animation Tests**: TC-3.1 to TC-3.3 (verify smoothness)
4. **Phase 4 - Edge Cases**: TC-4.1 to TC-4.6 (verify robustness)
5. **Phase 5 - Accessibility**: TC-5.1 to TC-5.3 (verify a11y compliance)
6. **Phase 6 - Responsive**: TC-6.1 to TC-6.3 (verify mobile/tablet)
7. **Phase 7 - Browser Compat**: TC-7.1 to TC-7.5 (verify cross-browser)
8. **Phase 8 - Integration**: TC-8.1 to TC-8.3 (verify no regressions)
9. **Phase 9 - Security**: TC-9.1 to TC-9.3 (verify security)
10. **Phase 10 - Performance**: TC-10.1 to TC-10.3 (verify speed)

---

## Definition of Done (Testing Perspective)

- [ ] All Phase 1-8 tests pass (Phases 9-10 are advisory)
- [ ] No critical or high-severity bugs found
- [ ] Animation feels natural and smooth (subjective, but important)
- [ ] No console errors or warnings
- [ ] Accessibility standards met (WCAG 2.1 Level AA)
- [ ] Works on Chrome, Firefox, Safari
- [ ] Works on mobile devices (iOS, Android)
- [ ] Code review completed by QA

---

## Automated Test Recommendations

While manual testing covers the UX aspects, here are automated tests that should be written:

### JavaScript Unit Tests
```javascript
describe('Market Conditions Expansion', () => {
  test('should toggle from collapsed to expanded state', () => {
    // Test aria-expanded attribute changes
    // Test display style changes
    // Test button text changes
  });

  test('should toggle from expanded to collapsed state', () => {
    // Verify reverse transition
  });

  test('should maintain state consistency during rapid clicks', () => {
    // Click multiple times rapidly
    // Verify final state matches aria-expanded
  });
});
```

### Integration Tests (Playwright/Cypress)
```javascript
test('User can expand and collapse Market Conditions widgets', async () => {
  await page.goto('/');

  // Verify collapsed state
  await expect(page.locator('#market-badges')).toBeVisible();
  await expect(page.locator('#market-cards')).not.toBeVisible();

  // Click expand
  await page.click('#market-toggle');

  // Verify expanded state
  await expect(page.locator('#market-badges')).not.toBeVisible();
  await expect(page.locator('#market-cards')).toBeVisible();

  // Click collapse
  await page.click('#market-toggle');

  // Verify collapsed state again
  await expect(page.locator('#market-badges')).toBeVisible();
  await expect(page.locator('#market-cards')).not.toBeVisible();
});
```

---

**Prepared by**: QA Test Engineer
**Date**: 2026-02-15
**Status**: Ready for Implementation
