# Test Plan: US-2.1.1 - Remove Divergence Page

**Feature**: Remove standalone divergence page and update navigation
**Risk Level**: 🟡 Medium
**Impact**: Medium (affects navigation and bookmarked URLs)
**Test Execution Time**: ~30 minutes

---

## Summary & Risk Assessment

### What We're Testing
This feature removes the `/divergence` page and navigation item as part of repositioning from "divergence tracker" to "comprehensive macro platform". The removal must maintain backward compatibility for bookmarked URLs via 301 redirect, ensure homepage signal cards remain functional, and avoid breaking navigation.

### Overall Risk Assessment: MEDIUM 🟡

**Why Medium Risk:**
- ✅ **Low Code Complexity**: Simple route removal and redirect
- ⚠️ **Medium User Impact**: Users with bookmarks need seamless redirect
- ⚠️ **Navigation Changes**: Removing nav items can break layout/styling
- ✅ **Fallback Path**: Homepage signal cards still provide access to divergence_gap metric via /explorer

**Critical Risks:**
1. **Broken Bookmarks**: Users who bookmarked `/divergence` must land somewhere useful (mitigated by 301 redirect)
2. **Navigation Layout**: Removing nav item could break responsive design or alignment
3. **Orphaned Links**: Internal links to `/divergence` could create 404s if not updated
4. **Signal Card Breakage**: Homepage cards must still link to correct /explorer metrics

---

## Test Cases

### Category 1: Route Removal & Redirect (Critical Path)

#### TC-1.1: Redirect from /divergence to /credit
**Priority**: P0 - Critical
**Test Type**: Functional - HTTP Redirect
**Steps:**
1. Start the application: `python signaltrackers/dashboard.py`
2. Use curl to test redirect: `curl -I http://localhost:5001/divergence`
3. Alternatively, visit `http://localhost:5001/divergence` in browser

**Expected:**
- HTTP response code: `301 Moved Permanently`
- Location header: `/credit`
- Browser automatically redirects to `/credit` page
- No flash of error page or 404

**Why This Matters**: Users with bookmarks shouldn't hit 404s

---

#### TC-1.2: Direct access to /credit still works
**Priority**: P1 - High
**Test Type**: Functional - Baseline
**Steps:**
1. Visit `http://localhost:5001/credit` directly

**Expected:**
- Credit page loads normally
- No console errors
- All charts and data display correctly

**Why This Matters**: Redirect target must be functional

---

#### TC-1.3: Redirect preserves query parameters
**Priority**: P2 - Medium
**Test Type**: Edge Case - Query String Handling
**Steps:**
1. Visit `http://localhost:5001/divergence?foo=bar`

**Expected:**
- Redirects to `/credit` (query params likely not preserved for 301, which is acceptable)
- OR redirects to `/credit?foo=bar` (better UX, but not required)

**Why This Matters**: Some users may have bookmarks with query params

---

### Category 2: Navigation Updates

#### TC-2.1: Divergence link removed from main navigation
**Priority**: P0 - Critical
**Test Type**: Functional - UI
**Steps:**
1. Visit homepage: `http://localhost:5001/`
2. Inspect main navigation bar
3. Look for "Divergence" text in nav items

**Expected:**
- "Divergence" link is NOT visible in navigation
- Navigation displays: Home, Credit, Equity, Rates, Commodities, FX, Explorer (no Divergence)
- Navigation items are evenly spaced and properly aligned

**Why This Matters**: Core requirement of the story

---

#### TC-2.2: Navigation styling remains intact
**Priority**: P1 - High
**Test Type**: Visual - Layout
**Steps:**
1. Visit homepage and inspect navigation bar
2. Check navigation on desktop (1920px width)
3. Check navigation on tablet (768px width)
4. Check navigation on mobile (375px width)

**Expected:**
- No overlapping nav items
- No broken alignment or spacing
- Responsive collapse/hamburger menu works correctly
- No visual glitches or layout shifts

**Why This Matters**: Removing items can break CSS grid/flexbox layouts

---

#### TC-2.3: Mobile navigation updated
**Priority**: P1 - High
**Test Type**: Functional - Mobile
**Steps:**
1. Visit homepage on mobile viewport (375px width)
2. Open hamburger menu (if applicable)
3. Inspect nav items in mobile menu

**Expected:**
- "Divergence" is not present in mobile navigation
- Mobile menu opens/closes correctly
- All other nav items are accessible

**Why This Matters**: Mobile nav often has separate templates/logic

---

### Category 3: Homepage Signal Cards

#### TC-3.1: Three signal cards are visible on homepage
**Priority**: P0 - Critical
**Test Type**: Functional - UI
**Steps:**
1. Visit homepage: `http://localhost:5001/`
2. Scroll to signal cards section (around line 411-477 in index.html)

**Expected:**
- Exactly 3 signal cards are visible:
  1. Yield Curve Status
  2. VIX Term Structure
  3. Gold/Credit Divergence
- Each card displays: title, status, percentile, description
- Cards are properly styled and aligned

**Why This Matters**: Users need access to divergence data via homepage

---

#### TC-3.2: Yield Curve signal card links to /explorer
**Priority**: P0 - Critical
**Test Type**: Functional - Navigation
**Steps:**
1. Visit homepage
2. Click on "Yield Curve Status" signal card

**Expected:**
- Navigates to `/explorer?metric=yield_curve_10y2y` (or similar metric name)
- Explorer page loads with Yield Curve metric pre-selected
- Chart displays yield curve data

**Why This Matters**: Signal cards must be clickable and functional

---

#### TC-3.3: VIX Term Structure signal card links to /explorer
**Priority**: P0 - Critical
**Test Type**: Functional - Navigation
**Steps:**
1. Visit homepage
2. Click on "VIX Term Structure" signal card

**Expected:**
- Navigates to `/explorer?metric=vix_term_structure` (or similar metric name)
- Explorer page loads with VIX metric pre-selected
- Chart displays VIX data

---

#### TC-3.4: Gold/Credit Divergence signal card links to /explorer
**Priority**: P0 - Critical
**Test Type**: Functional - Navigation
**Steps:**
1. Visit homepage
2. Click on "Gold/Credit Divergence" signal card

**Expected:**
- Navigates to `/explorer?metric=divergence_gap` (or similar metric name)
- Explorer page loads with Divergence metric pre-selected
- Chart displays divergence gap data
- **This is the primary way users access divergence data now**

**Why This Matters**: Ensures users can still access divergence data after page removal

---

#### TC-3.5: Signal cards load data correctly
**Priority**: P1 - High
**Test Type**: Integration - Data Loading
**Steps:**
1. Visit homepage
2. Inspect each signal card for data display
3. Check browser console for errors

**Expected:**
- Each card shows current status (Inverted, Normal, Backwardation, etc.)
- Percentile value displays (e.g., "95th percentile")
- Description text appears
- No console errors related to data loading
- No "Loading..." or "Error" states

**Why This Matters**: Cards must show real data, not placeholders

---

### Category 4: Homepage Footer Link

#### TC-4.1: Footer link updated or removed
**Priority**: P1 - High
**Test Type**: Functional - Links
**Steps:**
1. Visit homepage
2. Scroll to bottom of signal cards section (around line 475)
3. Look for "View All Indicators →" or similar link

**Expected (Option A - Removed):**
- "View All Indicators →" link is NOT present
- No broken link or empty space

**Expected (Option B - Updated):**
- Link text changed to "Explore All Metrics →"
- Link points to `/explorer`
- Clicking link navigates to explorer page

**Why This Matters**: Old link may have pointed to /divergence

---

### Category 5: Code Cleanup & Orphaned References

#### TC-5.1: Search codebase for /divergence references
**Priority**: P1 - High
**Test Type**: Code Review
**Steps:**
1. Run: `grep -r "/divergence" signaltrackers/ --exclude-dir=_archive`
2. Review all matches

**Expected:**
- Only expected references remain:
  - The redirect route in `dashboard.py`
  - Comments explaining why redirect exists
  - `divergence_gap` metric references in data/CSV files are OK
- No internal links to `/divergence` in templates
- No hardcoded `/divergence` URLs in JavaScript

**Why This Matters**: Prevents internal 404s from stale links

---

#### TC-5.2: divergence.html template archived or deleted
**Priority**: P2 - Medium
**Test Type**: Code Review
**Steps:**
1. Check if `signaltrackers/templates/divergence.html` exists
2. If archived, check `signaltrackers/templates/_archive/divergence.html`

**Expected:**
- File moved to `_archive/` folder (preferred for git history)
- OR file deleted entirely (acceptable, recoverable from git)
- File is NOT in active templates directory

**Why This Matters**: Unused templates create confusion

---

#### TC-5.3: No orphaned CSS/JS for divergence page
**Priority**: P3 - Low
**Test Type**: Code Review
**Steps:**
1. Search for divergence-specific CSS: `grep -r "divergence" signaltrackers/static/css/`
2. Search for divergence-specific JS: `grep -r "divergence" signaltrackers/static/js/`

**Expected:**
- No CSS classes or IDs specific to divergence page (e.g., `.divergence-chart`)
- No JavaScript functions specific to divergence page
- Generic classes like `.signal-card` are fine (used across site)

**Why This Matters**: Reduces technical debt and confusion

---

### Category 6: Edge Cases & Security

#### TC-6.1: Redirect uses 301 (permanent), not 302 (temporary)
**Priority**: P1 - High
**Test Type**: Security/SEO - HTTP Headers
**Steps:**
1. Run: `curl -I http://localhost:5001/divergence`
2. Check HTTP status code

**Expected:**
- Status code is `301 Moved Permanently`
- NOT `302 Found` or `307 Temporary Redirect`

**Why This Matters**:
- 301 tells search engines the page is permanently gone
- 301 tells browsers to update bookmarks
- Better SEO and user experience

---

#### TC-6.2: Redirect is not an open redirect
**Priority**: P2 - Medium
**Test Type**: Security - Open Redirect
**Steps:**
1. Try to manipulate redirect: `http://localhost:5001/divergence?redirect=http://evil.com`
2. Try path traversal: `http://localhost:5001/divergence/../../../etc/passwd`

**Expected:**
- Always redirects to `/credit` (hardcoded target)
- No ability to redirect to external domains
- No path traversal vulnerabilities

**Why This Matters**: Open redirects are a security risk (phishing vector)

---

#### TC-6.3: All pages have no console errors
**Priority**: P1 - High
**Test Type**: Integration - Error Handling
**Steps:**
1. Visit each page: Home, Credit, Equity, Rates, Commodities, FX, Explorer
2. Open browser console (F12)
3. Look for JavaScript errors or 404s

**Expected:**
- No console errors on any page
- No 404 errors for missing resources (CSS, JS, images)
- No broken API calls

**Why This Matters**: Navigation changes can break shared layouts

---

### Category 7: Regression Testing

#### TC-7.1: All other pages still load correctly
**Priority**: P1 - High
**Test Type**: Regression - Baseline
**Steps:**
1. Visit each page: Home, Credit, Equity, Rates, Commodities, FX, Explorer
2. Verify page loads without errors

**Expected:**
- All pages load successfully
- No broken layouts or missing content
- No impact from removing divergence page

**Why This Matters**: Changes to base.html (nav) affect all pages

---

#### TC-7.2: Explorer page works independently
**Priority**: P0 - Critical
**Test Type**: Regression - Core Functionality
**Steps:**
1. Visit `/explorer` directly (without coming from signal card)
2. Select different metrics from dropdown
3. Verify charts render

**Expected:**
- Explorer page loads normally
- All metrics available in dropdown
- Charts render for each metric
- No dependency on divergence page

**Why This Matters**: Explorer is the new primary interface

---

## Recommended Tests to Write

### Unit Tests (Python)

```python
# tests/test_routes.py

def test_divergence_redirect_returns_301():
    """Test that /divergence redirects with permanent redirect code"""
    client = app.test_client()
    response = client.get('/divergence', follow_redirects=False)

    assert response.status_code == 301
    assert response.location.endswith('/credit')

def test_divergence_redirect_lands_on_credit():
    """Test that following redirect from /divergence lands on /credit page"""
    client = app.test_client()
    response = client.get('/divergence', follow_redirects=True)

    assert response.status_code == 200
    assert b'Credit' in response.data  # Check page title or content

def test_credit_page_still_accessible():
    """Test that /credit page loads directly without issues"""
    client = app.test_client()
    response = client.get('/credit')

    assert response.status_code == 200
```

### Integration Tests (Selenium/Playwright)

```python
# tests/test_integration.py

def test_homepage_signal_cards_visible(browser):
    """Test that 3 signal cards are visible on homepage"""
    browser.get('http://localhost:5001/')

    signal_cards = browser.find_elements_by_class_name('signal-card')
    assert len(signal_cards) == 3

    # Verify card titles
    card_titles = [card.find_element_by_tag_name('h3').text for card in signal_cards]
    assert 'Yield Curve' in ' '.join(card_titles)
    assert 'VIX' in ' '.join(card_titles)
    assert 'Divergence' in ' '.join(card_titles)

def test_divergence_signal_card_links_to_explorer(browser):
    """Test that clicking Gold/Credit Divergence card navigates to /explorer"""
    browser.get('http://localhost:5001/')

    # Find divergence signal card (might need to adjust selector)
    divergence_card = browser.find_element_by_xpath("//div[contains(text(), 'Divergence')]")
    divergence_card.click()

    # Wait for navigation
    browser.implicitly_wait(2)

    # Check URL contains /explorer and metric parameter
    assert '/explorer' in browser.current_url
    assert 'metric=divergence_gap' in browser.current_url

def test_navigation_does_not_show_divergence_link(browser):
    """Test that Divergence is not present in navigation"""
    browser.get('http://localhost:5001/')

    nav_links = browser.find_elements_by_css_selector('nav a')
    nav_texts = [link.text for link in nav_links]

    assert 'Divergence' not in nav_texts
    assert 'Credit' in nav_texts
    assert 'Explorer' in nav_texts
```

---

## Concerns & Risks

### 🔴 High Priority Concerns

1. **Signal Card Click Handlers**
   - **Risk**: Signal cards might not be clickable yet (implementation detail unclear from issue)
   - **Impact**: Users can't access divergence data via homepage
   - **Mitigation**: Test TC-3.2, TC-3.3, TC-3.4 thoroughly; add click handlers if missing

2. **Metric Name Mismatch**
   - **Risk**: Explorer might expect different metric names than signal cards provide
   - **Impact**: Clicking signal card lands on /explorer but shows wrong metric
   - **Mitigation**: Verify metric names in CSV files match URL parameters

### 🟡 Medium Priority Concerns

3. **Mobile Navigation Layout**
   - **Risk**: Removing nav item might break responsive design
   - **Impact**: Mobile users can't navigate site
   - **Mitigation**: Test TC-2.3 on multiple mobile viewports

4. **Hardcoded Links in Comments/Docs**
   - **Risk**: Developer documentation might still reference /divergence
   - **Impact**: Developer confusion, but no user impact
   - **Mitigation**: TC-5.1 should catch most cases

### 🟢 Low Priority Concerns

5. **SEO Impact**
   - **Risk**: Search engines might still index /divergence page
   - **Impact**: Users coming from Google land on redirect
   - **Mitigation**: 301 redirect handles this correctly

---

## Coverage Gaps

### What's Hard to Test (Manual Verification Required)

1. **Bookmark Behavior**: Can't easily test if browsers update bookmarks after 301 redirect
2. **SEO Crawlers**: Can't verify how search engines interpret 301 without production deploy
3. **Long-term Link Rot**: Can't verify no other sites link to /divergence

### What's Not Covered by This Test Plan

1. **Performance**: Not testing if removing page improves load times (negligible impact expected)
2. **Analytics**: Not verifying if analytics tracking updates (GA events might reference /divergence)
3. **A/B Testing**: Not testing user preference for old vs new navigation

---

## Test Execution Checklist

### Pre-Testing Setup
- [ ] Feature branch `feature/US-2.1.1` checked out
- [ ] Application running: `python signaltrackers/dashboard.py`
- [ ] Browser dev tools open (F12) for console monitoring

### Critical Path (Must Pass)
- [ ] TC-1.1: /divergence redirects to /credit with 301
- [ ] TC-1.2: /credit page loads correctly
- [ ] TC-2.1: Divergence link removed from navigation
- [ ] TC-3.1: Three signal cards visible on homepage
- [ ] TC-3.4: Gold/Credit Divergence card links to /explorer with correct metric
- [ ] TC-7.2: Explorer page works independently

### High Priority (Should Pass)
- [ ] TC-2.2: Navigation styling intact (desktop/mobile)
- [ ] TC-2.3: Mobile navigation updated
- [ ] TC-3.2: Yield Curve card links correctly
- [ ] TC-3.3: VIX card links correctly
- [ ] TC-3.5: Signal cards load real data
- [ ] TC-4.1: Footer link updated or removed
- [ ] TC-5.1: No orphaned /divergence references
- [ ] TC-6.1: Redirect uses 301 (not 302)
- [ ] TC-6.3: No console errors on any page
- [ ] TC-7.1: All other pages still load

### Medium Priority (Nice to Have)
- [ ] TC-1.3: Redirect handles query parameters gracefully
- [ ] TC-5.2: divergence.html archived or deleted
- [ ] TC-6.2: Redirect is not an open redirect

### Low Priority (Optional)
- [ ] TC-5.3: No orphaned CSS/JS

---

## Definition of Done (Testing Perspective)

- [ ] All P0 (Critical) tests pass
- [ ] All P1 (High) tests pass
- [ ] At least 80% of P2 (Medium) tests pass
- [ ] No new console errors introduced
- [ ] Test results documented in workflow log
- [ ] Any bugs found are filed in GitHub with `bug` label
- [ ] QA verdict (APPROVED or CHANGES_REQUESTED) posted to issue #79

---

## Test Results Template

```markdown
## QA Test Results - US-2.1.1

**Tested By**: Claude (QA Role)
**Date**: 2026-02-19
**Environment**: Local development (Python dashboard.py)

### Summary
[PASS/FAIL] - [X/Y] tests passed

### Critical Path Results
- [ ] TC-1.1: /divergence redirect - [PASS/FAIL] - Notes:
- [ ] TC-2.1: Navigation updated - [PASS/FAIL] - Notes:
- [ ] TC-3.4: Divergence card → Explorer - [PASS/FAIL] - Notes:

### Bugs Found
1. [Bug Title] - Severity: [High/Medium/Low] - Issue #[number]

### Overall Verdict
[APPROVED / CHANGES_REQUESTED]

[If CHANGES_REQUESTED: List specific issues that must be fixed]
```
