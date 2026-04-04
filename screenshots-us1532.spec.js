/**
 * US-15.3.2: Inflation Component Signal Visibility screenshots
 *
 * Takes screenshots showing:
 * 1. Component signals collapsed (default) — desktop + mobile
 * 2. Component signals expanded with divergent data — desktop + mobile
 * 3. Component signals expanded with uniform data (all rising) — desktop + mobile
 *
 * Uses docker exec to modify root-owned JSON inside the container.
 */
const { test } = require('@playwright/test');
const { execSync } = require('child_process');
const path = require('path');

const CONTAINER = 'signaltrackers-dev';
const JSON_FILE = '/app/data/market_conditions_history.json';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots', 'us1532');

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

// Divergent data: realized rising, market falling, consumer rising
const DIVERGENT_COMPONENTS = {
  inflation_components: {
    CPIAUCSL: { direction: 'rising', z_score: 0.45, raw_value: 3.2 },
    PCEPILFE: { direction: 'rising', z_score: 0.32, raw_value: 2.8 },
    MEDCPIM158SFRBCLE: { direction: 'falling', z_score: -0.12, raw_value: 2.4 },
    T10YIE: { direction: 'falling', z_score: -0.28, raw_value: 2.3 },
    T5YIFR: { direction: 'falling', z_score: -0.15, raw_value: 2.2 },
    MICH: { direction: 'rising', z_score: 0.55, raw_value: 4.1 },
  },
  inflation_breadth: 3,
  inflation_breadth_total: 6,
};

// Uniform data: all rising
const UNIFORM_COMPONENTS = {
  inflation_components: {
    CPIAUCSL: { direction: 'rising', z_score: 0.65, raw_value: 3.5 },
    PCEPILFE: { direction: 'rising', z_score: 0.52, raw_value: 3.0 },
    MEDCPIM158SFRBCLE: { direction: 'rising', z_score: 0.38, raw_value: 2.9 },
    T10YIE: { direction: 'rising', z_score: 0.42, raw_value: 2.7 },
    T5YIFR: { direction: 'rising', z_score: 0.35, raw_value: 2.5 },
    MICH: { direction: 'rising', z_score: 0.48, raw_value: 3.8 },
  },
  inflation_breadth: 6,
  inflation_breadth_total: 6,
};

test.describe('US-15.3.2 Component Signal Visibility', () => {

  test.beforeAll(() => {
    // Ensure screenshot directory exists
    execSync(`mkdir -p ${SCREENSHOT_DIR}`);
  });

  test('Collapsed — divergent — desktop', async ({ page }) => {
    updateConditionsData(DIVERGENT_COMPONENTS);
    await page.setViewportSize(DESKTOP);
    await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
    await page.waitForSelector('.inflation-components');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'collapsed-divergent-desktop.png'),
      fullPage: true,
    });
  });

  test('Collapsed — divergent — mobile', async ({ page }) => {
    updateConditionsData(DIVERGENT_COMPONENTS);
    await page.setViewportSize(MOBILE);
    await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
    await page.waitForSelector('.inflation-components');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'collapsed-divergent-mobile.png'),
      fullPage: true,
    });
  });

  test('Expanded — divergent — desktop', async ({ page }) => {
    updateConditionsData(DIVERGENT_COMPONENTS);
    await page.setViewportSize(DESKTOP);
    await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
    await page.click('#inflation-components-toggle');
    await page.waitForSelector('.inflation-components--expanded');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'expanded-divergent-desktop.png'),
      fullPage: true,
    });
  });

  test('Expanded — divergent — mobile', async ({ page }) => {
    updateConditionsData(DIVERGENT_COMPONENTS);
    await page.setViewportSize(MOBILE);
    await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
    await page.click('#inflation-components-toggle');
    await page.waitForSelector('.inflation-components--expanded');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'expanded-divergent-mobile.png'),
      fullPage: true,
    });
  });

  test('Expanded — uniform (all rising) — desktop', async ({ page }) => {
    updateConditionsData(UNIFORM_COMPONENTS);
    await page.setViewportSize(DESKTOP);
    await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
    await page.click('#inflation-components-toggle');
    await page.waitForSelector('.inflation-components--expanded');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'expanded-uniform-desktop.png'),
      fullPage: true,
    });
  });

  test('Expanded — uniform (all rising) — mobile', async ({ page }) => {
    updateConditionsData(UNIFORM_COMPONENTS);
    await page.setViewportSize(MOBILE);
    await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
    await page.click('#inflation-components-toggle');
    await page.waitForSelector('.inflation-components--expanded');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'expanded-uniform-mobile.png'),
      fullPage: true,
    });
  });
});
