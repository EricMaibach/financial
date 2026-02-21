const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Mobile viewport
  await page.setViewportSize({ width: 375, height: 667 });

  // Go to explorer
  await page.goto('http://localhost:5000/explorer');

  // Wait for dropdown to be populated by JavaScript
  await page.waitForFunction(() => {
    const select = document.getElementById('metricSelector');
    return select && select.options.length > 1; // More than just "-- Choose a metric --"
  }, { timeout: 10000 });

  // Select the first metric (index 1, since 0 is the placeholder)
  await page.selectOption('#metricSelector', { index: 1 });

  // Wait for the chart to render
  // The page shows metricContent when content loads
  await page.waitForSelector('#metricContent', { state: 'visible', timeout: 10000 });

  // Wait a bit more for chart animation to complete
  await page.waitForTimeout(2000);

  // Take screenshot
  await page.screenshot({
    path: 'screenshots/explorer-with-metric-mobile.png',
    fullPage: true
  });

  console.log('Explorer screenshot saved!');

  // Also take desktop version for comparison
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.waitForTimeout(500); // Let layout adjust
  await page.screenshot({
    path: 'screenshots/explorer-with-metric-desktop.png',
    fullPage: true
  });

  console.log('Desktop version saved too!');

  await browser.close();
})();
