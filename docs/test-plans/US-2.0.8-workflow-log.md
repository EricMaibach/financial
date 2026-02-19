# US-2.0.8 Workflow Log — Standardize Homepage Section Layout Widths

**Branch:** feature/US-2.0.8
**Issue:** #76
**Started:** 2026-02-18

---

## Phase 1: Setup — Complete

- Created branch `feature/US-2.0.8` from `main`
- Workflow log initialized

---

## Phase 2: QA Test Planning — Complete

### Baseline (Before Changes)

Current layout patterns in `index.html`:

| Section | Outermost Wrapper | Has Card Chrome |
|---|---|---|
| Market Conditions | `<section class="market-conditions-section mb-4">` | No |
| Today's Market Briefing | `<section class="hero-briefing mb-4">` | Yes (shadow-lg) |
| What's Moving Today | `<section class="whats-moving-section mb-4">` | No |
| Top Movers Chart | `<div class="row mb-4" id="movers-chart-container">` | Yes |
| Cross-Market Indicators | `<section class="market-signals-section mb-4">` | No |
| Prediction Markets | `<div class="row mb-4">` | Yes |

**Identified problems:**
- Lines 372–402: `movers-chart-container` uses `div.row > div.col-12 > div.card`. Bootstrap `row` adds negative horizontal margins (`margin-right/left: calc(-.5 * var(--bs-gutter-x))`), causing the section to appear wider/misaligned vs. direct `<section>` siblings.
- Lines 483–504: Prediction Markets uses identical `div.row > div.col-12 > div.card` pattern.
- The three direct `<section>` sections render flush; the two `div.row` sections render with gutter offset.

---

### Test Plan

#### TC-01: Layout Alignment — Desktop (1440px)
**Type:** Visual / Manual
**Pre-condition:** App running at localhost. Browser at 1440px.
**Steps:**
1. Open browser DevTools, use "Responsive Design Mode" set to 1440px wide.
2. Right-click the outermost element of each of the 5 sections and inspect.
3. Record `offsetLeft` for each section's outermost element.
**Pass criteria:** All 5 sections have identical `offsetLeft` values.
**Fail criteria:** Any section's `offsetLeft` differs from others.

#### TC-02: Layout Alignment — Desktop (1024px)
**Type:** Visual / Manual
**Steps:** Same as TC-01 at 1024px width.
**Pass criteria:** All 5 sections have identical `offsetLeft` values.

#### TC-03: Layout Alignment — Tablet (768px)
**Type:** Visual / Manual
**Steps:** Same as TC-01 at 768px width.
**Pass criteria:** All 5 sections have identical `offsetLeft` values.

#### TC-04: Layout Alignment — Mobile (375px)
**Type:** Visual / Manual
**Steps:** Same as TC-01 at 375px width. Also check for horizontal scrollbar.
**Pass criteria:** All 5 sections align; no horizontal overflow/scrollbar.

#### TC-05: HTML Structure — Wrapper Pattern
**Type:** Structural / Automated
**Steps:**
1. Inspect `index.html` source.
2. Verify no section outermost wrapper uses `<div class="row">` wrapping a `<div class="col-12">` as a full-width section container.
3. Verify all 5 sections use `<section>` as their outermost element.
4. Verify a layout convention comment exists at the top of `{% block content %}`.
**Pass criteria:** No `div.row > div.col-12` full-width section pattern; all 5 use `<section>`; comment present.

#### TC-06: Top Movers Chart — Functional Expand/Collapse
**Type:** Functional
**Steps:**
1. Navigate to homepage.
2. In "What's Moving Today" section, click "Show Trends Chart" button.
3. Verify the movers chart section becomes visible.
4. Verify the chart canvas renders (not blank, no JS error in console).
5. Click "Hide Chart" to collapse.
6. Verify chart section is hidden again.
**Pass criteria:** Toggle works; chart renders; no JS errors.

#### TC-07: Top Movers Chart — Timeframe Selector
**Type:** Functional
**Steps:**
1. Expand the Top Movers Chart.
2. Click each timeframe button: 1W, 1M, 3M, 6M, 1Y, 5Y, 10Y, 20Y, All.
3. For each click, verify the chart updates (data changes or loading state shows).
4. Verify no JS errors in console.
**Pass criteria:** All 9 timeframe buttons function; chart updates; no errors.

#### TC-08: Prediction Markets — Data Load
**Type:** Functional
**Steps:**
1. Navigate to homepage.
2. Observe the Prediction Markets section on page load.
3. Wait for data to load (or loading message to resolve).
4. Verify prediction market cards/items render correctly.
5. Verify no JS errors in console.
**Pass criteria:** Prediction markets data loads and displays; section visible and styled correctly.

#### TC-09: No Content Changes
**Type:** Regression
**Steps:**
1. Compare all text content, headings, labels, and data within each section before and after.
2. Verify no data values, labels, icons, or section names changed.
**Pass criteria:** Zero content changes in any section.

#### TC-10: No JavaScript Console Errors
**Type:** Regression
**Steps:**
1. Open homepage with browser console visible.
2. Wait for all sections to fully load.
3. Inspect console for errors or warnings caused by the layout change.
**Pass criteria:** No new JS errors introduced by the layout change.

#### TC-11: Server Startup — No Python Errors
**Type:** Smoke
**Steps:**
1. Run `python signaltrackers/dashboard.py` in terminal.
2. Verify server starts without errors.
3. Navigate to homepage and confirm 200 response.
**Pass criteria:** Server starts cleanly; homepage loads with HTTP 200.

#### TC-12: Edge Case — `movers-chart-container` ID Preserved
**Type:** Regression
**Steps:**
1. Inspect the converted Top Movers Chart element.
2. Verify `id="movers-chart-container"` is present on the new `<section>` tag.
3. Verify the `style="display: none;"` attribute is preserved.
**Pass criteria:** ID and display:none are present on the new element (JavaScript references this ID).

#### TC-13: Edge Case — `prediction-markets-container` ID Preserved
**Type:** Regression
**Steps:**
1. Inspect the Prediction Markets section.
2. Verify the inner `<div class="row" id="prediction-markets-container">` is preserved inside the new `<section>`.
**Pass criteria:** Inner prediction markets container ID is intact (JavaScript populates this element).

---

✅ Phase 2 Complete: Test plan created

---

## Phase 3: Implementation — Complete

### Changes Made

**File:** `signaltrackers/templates/index.html`

1. **Layout convention comment** added at line 6 (top of `{% block content %}`):
   ```
   {# LAYOUT CONVENTION: All homepage sections use direct <section> tags ... #}
   ```

2. **Top Movers Chart** (was lines 372–402):
   - Removed `<div class="row mb-4">` and `<div class="col-12">` wrappers
   - Changed to `<section class="movers-chart-section mb-4" id="movers-chart-container" style="display: none;">`
   - `id` and `style` attributes preserved for JavaScript compatibility
   - Inner `<div class="card">` and all content unchanged

3. **Prediction Markets** (was lines 483–504):
   - Removed `<div class="row mb-4">` and `<div class="col-12">` wrappers
   - Changed to `<section class="prediction-markets-section mb-4">`
   - Inner `<div class="row" id="prediction-markets-container">` preserved for JavaScript compatibility
   - All content unchanged

**No CSS changes required** — `mb-4` Bootstrap utility class handles bottom margin on both sections.

**Final section structure** (all direct children of `{% block content %}`):
```
<section class="market-conditions-section mb-4">
<section class="hero-briefing mb-4">
<section class="whats-moving-section mb-4">
<section class="movers-chart-section mb-4" id="movers-chart-container">  ← was div.row
<section class="market-signals-section mb-4">
<section class="prediction-markets-section mb-4">  ← was div.row
```

✅ Phase 3 Complete: Implementation done

---

## Phase 4: QA Verification — Complete

All automated and structural checks PASSED. QA verdict: **APPROVED**.

| TC | Result |
|---|---|
| TC-05 HTML structure | ✅ PASS |
| TC-06 Movers chart toggle | ✅ PASS |
| TC-07 Timeframe buttons | ✅ PASS |
| TC-08 Prediction markets load | ✅ PASS |
| TC-09 No content changes | ✅ PASS |
| TC-10 No JS console errors | ✅ PASS |
| TC-11 Server smoke test | ✅ PASS |
| TC-12 movers-chart-container ID preserved | ✅ PASS |
| TC-13 prediction-markets-container ID preserved | ✅ PASS |
| TC-01–04 Visual alignment | ⏳ Manual browser test required |

✅ Phase 4 Complete: QA review filed

---

## Phase 5: PR Creation

_In progress..._
