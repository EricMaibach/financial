# QA Context

## Current State
- **Current User Story:** US-3.1.2 - Apply Mobile-First Layout to Explorer Page
- **Phase:** Test planning complete, awaiting implementation
- **Test Plan:** Comprehensive plan with 75+ test cases created and added to issue #84

## Active Issues
- US-3.1.2: Test plan created, ready for implementation phase
  - Critical focus: Mobile chart visibility, 50%+ scroll reduction, accessibility
  - Risk areas: Chart library tap tooltips, Safari sticky positioning, screen reader chart access

## Resolved (last 10)
_None yet in this workflow_

## Key Decisions

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
