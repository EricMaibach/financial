# QA Context

## Current State
- **Current User Story:** US-3.1.4 - Apply Mobile-First Layout to Dollar, Equities, Crypto, Safe Havens Pages
- **Phase:** Test planning complete, ready for implementation
- **Test Plan:** Comprehensive plan with 56 test cases created and added to issue #86

## Active Issues
- US-3.1.4: Test plan created, ready for implementation phase
  - Critical focus: Mobile chart visibility on 4 pages (Dollar, Equities, Crypto, Safe Havens), 50%+ scroll reduction, consistency with Explorer/Credit/Rates
  - Risk areas: Safari iOS sticky positioning, chart touch targets (44px), consistency drift across 4 pages, performance on low-end devices, page-specific sections breaking layout
  - Scope: 4 pages (largest batch yet), completes Feature 3.1 (all 7 content pages)
  - Unique challenge: Each page has custom sections (Currency Pairs, Market Indices, On-Chain Metrics, Bonds) that must use collapsible pattern

## Resolved (last 10)
- US-3.1.3: Test plan created (82 test cases), handed off to implementation (2026-02-21)

## Key Decisions

### US-3.1.4 Testing Approach
1. **Automated-first strategy:** Playwright for visual regression at 3 viewports (375px, 768px, 1920px) for ALL 4 pages
2. **12 screenshots total:** 4 pages × 3 viewports = comprehensive visual validation
3. **Real device testing required:** iOS Safari and Android Chrome for touch interactions on all 4 pages
4. **Accessibility non-negotiable:** All P0 a11y tests must pass (touch targets, keyboard nav, screen readers) on all 4 pages
5. **Performance baseline:** LCP < 2.5s on 3G, animations at 60fps, tested on all 4 pages
6. **Consistency validation critical:** Must match Explorer/Credit/Rates pattern - all 7 pages identical layout
7. **Page-specific section handling:** Each page has custom sections (Currency Pairs, Market Indices, On-Chain Metrics, Bonds) that must use CollapsibleSection component
8. **Feature 3.1 completion:** This completes the entire feature - all 7 content pages mobile-first

### Risk Mitigation - US-3.1.4
- Test Safari iOS sticky positioning early (known Safari bugs may affect all 4 pages)
- Validate chart touch targets early (may need chart library modification for 44px on all pages)
- Test on older Android devices (2019 models) for performance validation
- Provide chart data alternatives for screen readers (WCAG compliance on all 4 pages)
- Ensure all pages use identical components (CollapsibleSection, ChartContainer, KeyStatsPanel)
- Visual diff all 4 pages against Explorer/Credit/Rates to catch consistency drift
- Test all custom sections (Dollar: Currency Pairs, Equities: Market Indices, Crypto: On-Chain Metrics, Safe Havens: Bonds) at all viewports
- Use component reuse to prevent pattern deviations (copy-paste template structure)

### US-3.1.3 Testing Approach
1. **Automated-first strategy:** Playwright for visual regression at 3 viewports (375px, 768px, 1920px) for BOTH pages
2. **Real device testing required:** iOS Safari and Android Chrome for touch interactions
3. **Accessibility non-negotiable:** All P0 a11y tests must pass (touch targets, keyboard nav, screen readers)
4. **Performance baseline:** LCP < 2.5s on 3G, animations at 60fps
5. **Consistency validation:** Must match Explorer page pattern (US-3.1.2) for design system coherence
6. **Dual-page testing:** Both Credit and Rates pages tested identically to ensure pattern consistency

### Risk Mitigation - US-3.1.3
- Test Safari iOS sticky positioning early (known Safari bugs)
- Validate chart touch targets early (may need chart library modification for 44px)
- Test on older Android devices (2019 models) for performance validation
- Provide chart data alternatives for screen readers (WCAG compliance)
- Ensure both pages use identical components (CollapsibleSection, ChartContainer, KeyStatsPanel)

### US-3.1.2 Testing Approach
1. **Automated-first strategy:** Playwright for visual regression at 3 viewports (375px, 768px, 1920px)
2. **Real device testing required:** iOS Safari and Android Chrome for touch interactions
3. **Accessibility non-negotiable:** All P0 a11y tests must pass (touch targets, keyboard nav, screen readers)
4. **Performance baseline:** LCP < 2.5s on 3G, animations at 60fps
5. **Security testing:** XSS and SQL injection tests for metric selector critical

### Risk Mitigation
- Test chart tap tooltips early (may need chart library modification)
- Use real iOS devices for sticky positioning validation (Safari bugs)
- Provide chart data alternatives for screen readers (WCAG compliance)

## Coverage Summary

### US-3.1.4 Test Coverage
**Total Test Cases:** 56

**By Category:**
- Functional (Mobile): 10 test cases (all 4 pages: visual hierarchy, chart prominence, scroll reduction)
- Functional (Tablet): 4 test cases (hybrid layout for all 4 pages)
- Functional (Desktop): 1 test case (enhanced layout for all 4 pages)
- Consistency: 4 test cases (critical - all 7 content pages must match pattern)
- Page-Specific: 4 test cases (custom sections: Currency Pairs, Market Indices, On-Chain Metrics, Bonds)
- Integration: 4 test cases (component interactions, state management)
- Edge Cases: 4 test cases (viewport extremes, missing data, slow network, rapid resize)
- Security: 4 test cases (XSS, SQL injection, CSRF, validation)
- Performance: 4 test cases (page load, render time, animations, memory)
- Accessibility: 6 test cases (WCAG 2.1 AA compliance)
- Cross-Browser: 5 test cases (Chrome, Safari, Firefox, Edge, mobile)
- Visual Regression: 4 test cases (12 Playwright screenshots: 4 pages × 3 viewports)

**By Priority:**
- P0 (Critical): 23 test cases (must pass 100% for approval)
- P1 (High): 18 test cases (should pass 90%+ threshold)
- P2 (Medium): 15 test cases (should pass 80%+)

**Tools:**
- Playwright (visual regression, 12 screenshots)
- Lighthouse (performance + accessibility on all 4 pages)
- WebAIM Contrast Checker (color contrast)
- NVDA/VoiceOver (screen readers)
- Chrome DevTools (performance profiling)
- Real devices: iPhone, Android, iPad

**Unique Challenges:**
- 4 pages (largest batch) increases consistency risk
- Each page has custom sections requiring validation
- Completes Feature 3.1 - final validation of pattern across all 7 pages
- 12 total screenshots vs. 6 in US-3.1.3 (doubled workload)

### US-3.1.3 Test Coverage
**Total Test Cases:** 82

**By Category:**
- Functional: 28 test cases (mobile/tablet/desktop layouts for Credit & Rates pages)
- Integration: 4 test cases (component interactions, state management)
- Edge Cases: 8 test cases (viewport extremes, missing data, slow network, rapid resize)
- Security: 4 test cases (XSS, SQL injection, CSRF, validation)
- Performance: 5 test cases (page load, render time, animations, memory)
- Accessibility: 18 test cases (WCAG 2.1 AA compliance)
- Cross-Browser: 5 test cases (Chrome, Safari, Firefox, Edge, mobile)
- Visual Regression: 4 test cases (Playwright screenshots for both pages)
- Consistency: 4 test cases (matching Explorer page pattern)

**By Priority:**
- P0 (Critical): 18 test cases (must pass for approval)
- P1 (High): 14 test cases (should pass, 90% threshold)
- P2 (Medium): 12 test cases (nice to have)

**Tools:**
- Playwright (visual regression)
- Lighthouse (performance + accessibility)
- WebAIM Contrast Checker (color contrast)
- NVDA/VoiceOver (screen readers)
- Chrome DevTools (performance profiling)
- Real devices: iPhone, Android, iPad

### US-3.1.2 Test Coverage
**Total Test Cases:** 75+

**By Category:**
- Functional: 24 test cases (mobile/tablet/desktop layouts, interactivity)
- Integration: 4 test cases (component interactions, state management)
- Edge Cases: 8 test cases (viewport extremes, missing data, slow network)
- Security: 4 test cases (XSS, SQL injection, CSRF, validation)
- Performance: 5 test cases (page load, render time, animations, memory)
- Accessibility: 18 test cases (WCAG 2.1 AA compliance)
- Cross-Browser: 5 test cases (Chrome, Safari, Firefox, Edge, mobile)
- Visual Regression: 4 test cases (Playwright screenshots)

**By Priority:**
- P0 (Critical): 15 test cases (must pass for approval)
- P1 (High): 12 test cases (should pass for quality)
- P2 (Medium): 8 test cases (nice to have)
- P3 (Low): 1 test case (optional)

**Tools:**
- Playwright (visual regression)
- Lighthouse (performance + accessibility)
- WebAIM Contrast Checker (color contrast)
- NVDA/VoiceOver (screen readers)
- Chrome DevTools (performance profiling)

### Coverage Gaps (Acknowledged)
- Load testing (high concurrent users) - out of scope
- Internationalization/RTL - not tested
- Offline mode - not applicable
- Print styles - low priority for mobile
