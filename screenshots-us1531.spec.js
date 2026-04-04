/**
 * US-15.3.1: Graduated Confidence Display & Breadth Indicator screenshots
 *
 * Takes screenshots showing:
 * 1. Transition Watch state with high breadth (5/6) - desktop + mobile
 * 2. Transition Watch state with low breadth (3/6) - desktop + mobile
 * 3. Confirmed state with high breadth (6/6) - desktop + mobile
 * 4. Conditions strip on non-homepage showing breadth pill + transition watch - desktop + mobile
 *
 * Uses docker exec to modify root-owned JSON inside the container.
 */
const { test } = require('@playwright/test');
const { execSync } = require('child_process');
const path = require('path');

const CONTAINER = 'signaltrackers-dev';
const JSON_FILE = '/app/data/market_conditions_history.json';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots', 'us1531');

// Viewports
const DESKTOP = { width: 1920, height: 1080 };
const MOBILE = { width: 375, height: 667 };

function dockerExecPython(script) {
  execSync(`docker exec ${CONTAINER} python3 -c "${script}"`, { stdio: 'pipe' });
}

function updateConditionsData(overrides) {
  const overridesJson = JSON.stringify(overrides).replace(/"/g, '\\"');
  dockerExecPython(`
import json
with open('${JSON_FILE}') as f:
    d = json.load(f)
dates = sorted(d.keys())
latest = dates[-1]
overrides = json.loads('${overridesJson}')
d[latest]['dimensions']['quadrant'].update(overrides)
with open('${JSON_FILE}', 'w') as f:
    json.dump(d, f, indent=2)
`);
}

function removeTransitionWatch() {
  dockerExecPython(`
import json
with open('${JSON_FILE}') as f:
    d = json.load(f)
dates = sorted(d.keys())
latest = dates[-1]
d[latest]['dimensions']['quadrant'].pop('transition_watch', None)
with open('${JSON_FILE}', 'w') as f:
    json.dump(d, f, indent=2)
`);
}

function restoreConditionsData() {
  dockerExecPython(`
import json
with open('${JSON_FILE}') as f:
    d = json.load(f)
dates = sorted(d.keys())
latest = dates[-1]
d[latest]['dimensions']['quadrant'] = {'state': 'Goldilocks'}
with open('${JSON_FILE}', 'w') as f:
    json.dump(d, f, indent=2)
`);
}

test.afterAll(() => {
  restoreConditionsData();
});

// Serialize tests to avoid data races
test.describe.configure({ mode: 'serial' });

async function reloadAndWait(page, url) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
}

test.describe('US-15.3.1: Transition Watch + Breadth Screenshots', () => {

  // Scenario 1: Transition Watch with HIGH breadth (5/6) — shifting toward Stagflation
  test('transition-watch-high-breadth-desktop', async ({ page }) => {
    updateConditionsData({
      state: 'Goldilocks',
      transition_watch: { direction: 'Stagflation', month: 1 },
      inflation_breadth: 5,
      inflation_breadth_total: 6
    });
    await page.setViewportSize(DESKTOP);
    await reloadAndWait(page, 'http://localhost:5000/');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'transition-watch-high-breadth-desktop.png'),
      fullPage: true
    });
  });

  test('transition-watch-high-breadth-mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE);
    await reloadAndWait(page, 'http://localhost:5000/');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'transition-watch-high-breadth-mobile.png'),
      fullPage: true
    });
  });

  // Scenario 2: Transition Watch with LOW breadth (3/6) — shifting toward Reflation
  test('transition-watch-low-breadth-desktop', async ({ page }) => {
    updateConditionsData({
      state: 'Goldilocks',
      transition_watch: { direction: 'Reflation', month: 1 },
      inflation_breadth: 3,
      inflation_breadth_total: 6
    });
    await page.setViewportSize(DESKTOP);
    await reloadAndWait(page, 'http://localhost:5000/');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'transition-watch-low-breadth-desktop.png'),
      fullPage: true
    });
  });

  test('transition-watch-low-breadth-mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE);
    await reloadAndWait(page, 'http://localhost:5000/');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'transition-watch-low-breadth-mobile.png'),
      fullPage: true
    });
  });

  // Scenario 3: Confirmed state with HIGH breadth (6/6) — no transition watch
  test('confirmed-high-breadth-desktop', async ({ page }) => {
    updateConditionsData({
      state: 'Goldilocks',
      inflation_breadth: 6,
      inflation_breadth_total: 6
    });
    removeTransitionWatch();
    await page.setViewportSize(DESKTOP);
    await reloadAndWait(page, 'http://localhost:5000/');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'confirmed-high-breadth-desktop.png'),
      fullPage: true
    });
  });

  test('confirmed-high-breadth-mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE);
    await reloadAndWait(page, 'http://localhost:5000/');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'confirmed-high-breadth-mobile.png'),
      fullPage: true
    });
  });

  // Scenario 4: Conditions strip on non-homepage — transition watch + breadth pill
  test('strip-transition-watch-desktop', async ({ page }) => {
    updateConditionsData({
      state: 'Goldilocks',
      transition_watch: { direction: 'Stagflation', month: 1 },
      inflation_breadth: 5,
      inflation_breadth_total: 6
    });
    await page.setViewportSize(DESKTOP);
    await reloadAndWait(page, 'http://localhost:5000/equity');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'strip-transition-desktop.png'),
      fullPage: true
    });
  });

  test('strip-transition-watch-mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE);
    await reloadAndWait(page, 'http://localhost:5000/equity');

    // Expand the conditions strip to show breadth row + transition watch row
    const expandBtn = page.locator('#conditions-strip-toggle');
    if (await expandBtn.isVisible()) {
      await expandBtn.click();
      await page.waitForTimeout(300);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'strip-transition-mobile.png'),
      fullPage: true
    });
  });
});
